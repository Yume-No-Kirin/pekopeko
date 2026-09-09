import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, within, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import Validation from "./Validation.jsx";

function jsonResponse(status, body) {
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText: "",
    json: async () => body,
  };
}

function makeSummary({
  id,
  domain = "PERSONAL",
  epistemicStatus = "direct",
  createdAt = "2026-08-25T10:00:00",
  itemType = "assertion",
}) {
  return {
    id,
    domain,
    proposal_status: "PROPOSED",
    proposed_item_type: itemType,
    epistemic_status: epistemicStatus,
    created_at: createdAt,
  };
}

function makeDetail({
  id,
  domain = "PERSONAL",
  sourceId,
  filename = "notes.md",
  body = "Contenu de test",
  proposedPathSegments = [],
  context = null,
  itemType = "assertion",
  entityType,
  startsAt,
  endsAt,
  relationshipType,
  endpoints,
}) {
  return {
    id,
    domain,
    frontmatter: {
      proposed_item_type: itemType,
      provenance: { source_id: sourceId, extraction_provider: "ollama" },
      proposed_path_segments: proposedPathSegments,
      context,
      entity_type: entityType,
      starts_at: startsAt,
      ends_at: endsAt,
      relationship_type: relationshipType,
      endpoints,
    },
    body,
    source_frontmatter: { original_filename: filename },
    source_body: "",
  };
}

// proposalsByDomain: { DOMAIN: [summary, ...] } (same list returned regardless of the
// status query param); proposalsByDomainAndStatus: { "DOMAIN:STATUS": [summary, ...] }
// overrides proposalsByDomain when a test needs PROPOSED and EDITED to differ
// (TASK-013 AC16); detailsById: { id: detail }; ingestionsByDomain: { DOMAIN: [taskState, ...] };
// organizationFoldersByDomain: { DOMAIN: [[...], ...] } (segments_by_depth); editShouldFail
// makes the /edit POST return a 400 instead of a success envelope. acceptBatchFailIds/
// rejectBatchFailIds (TASK-015): proposal_ids in a batch request that should come back
// with status: "failed" instead of "accepted"/"rejected", simulating a partial failure.
function makeFetchMock({
  proposalsByDomain = {},
  proposalsByDomainAndStatus = {},
  detailsById = {},
  ingestionsByDomain = {},
  organizationFoldersByDomain = {},
  editShouldFail = false,
  acceptBatchFailIds = [],
  rejectBatchFailIds = [],
} = {}) {
  return vi.fn((url, options = {}) => {
    const parsed = new URL(url);
    const path = parsed.pathname;
    const method = options.method || "GET";

    const proposalsListMatch = path.match(/^\/domains\/([A-Z]+)\/proposals$/);
    if (proposalsListMatch && method === "GET") {
      const domain = proposalsListMatch[1];
      const status = parsed.searchParams.get("status");
      // proposalsByDomain is a PROPOSED-only fixture from before TASK-013 added the
      // EDITED fan-out - only fall back to it for status=PROPOSED, or every fixture
      // using it would silently double its items once for each status queried.
      const items =
        proposalsByDomainAndStatus[`${domain}:${status}`] || (status === "PROPOSED" ? proposalsByDomain[domain] : null) || [];
      return Promise.resolve(jsonResponse(200, { items, total: items.length, limit: 500, offset: 0 }));
    }

    const foldersMatch = path.match(/^\/domains\/([A-Z]+)\/organization-folders$/);
    if (foldersMatch && method === "GET") {
      const itemType = parsed.searchParams.get("item_type");
      const fixture = organizationFoldersByDomain[foldersMatch[1]];
      // Two supported fixture shapes: a flat segments_by_depth array (existing
      // tests - same options regardless of item_type), or a { itemType: [...] }
      // map (TASK-005a - lets a test differentiate options per proposed_item_type).
      const segments_by_depth = Array.isArray(fixture) ? fixture : (fixture && fixture[itemType]) || [];
      return Promise.resolve(jsonResponse(200, { segments_by_depth }));
    }

    const editMatch = path.match(/^\/domains\/([A-Z]+)\/proposals\/([^/]+)\/edit$/);
    if (editMatch && method === "POST") {
      if (editShouldFail) {
        return Promise.resolve(jsonResponse(400, { error: { type: "ValidationError", message: "edit rejected" } }));
      }
      return Promise.resolve(
        jsonResponse(200, {
          proposal_id: editMatch[2],
          edited_by: "test-reviewer",
          edited_at: "2026-09-04T00:00:00",
          archived_version_path: "/x/history/v1.md",
          archived_version: 1,
        })
      );
    }

    const proposalDetailMatch = path.match(/^\/domains\/([A-Z]+)\/proposals\/([^/]+)$/);
    if (proposalDetailMatch && method === "GET") {
      const detail = detailsById[proposalDetailMatch[2]];
      if (!detail) {
        return Promise.resolve(jsonResponse(400, { error: { type: "ValidationError", message: "malformed" } }));
      }
      return Promise.resolve(jsonResponse(200, detail));
    }

    const acceptBatchMatch = path.match(/^\/domains\/([A-Z]+)\/proposals\/accept-batch$/);
    if (acceptBatchMatch && method === "POST") {
      const body = JSON.parse(options.body);
      const results = body.proposal_ids.map((id) =>
        acceptBatchFailIds.includes(id)
          ? {
              proposal_id: id,
              status: "failed",
              error: {
                type: "UnresolvedRelationshipEndpointError",
                message: "Endpoint(s) [...] are not yet ACCEPTED proposals",
              },
            }
          : {
              proposal_id: id,
              assertion_id: "a1",
              assertion_path: "/x",
              reviewed_by: "test-reviewer",
              reviewed_at: "2026-09-03T00:00:00",
              status: "accepted",
            }
      );
      const failed_count = results.filter((r) => r.status === "failed").length;
      return Promise.resolve(
        jsonResponse(200, { results, succeeded_count: results.length - failed_count, failed_count })
      );
    }

    const rejectBatchMatch = path.match(/^\/domains\/([A-Z]+)\/proposals\/reject-batch$/);
    if (rejectBatchMatch && method === "POST") {
      const body = JSON.parse(options.body);
      const results = body.proposal_ids.map((id) =>
        rejectBatchFailIds.includes(id)
          ? {
              proposal_id: id,
              status: "failed",
              error: { type: "InvalidProposalStatusError", message: "not PROPOSED/EDITED" },
            }
          : {
              proposal_id: id,
              reviewed_by: "test-reviewer",
              reviewed_at: "2026-09-03T00:00:00",
              rejection_reason: body.reason,
              status: "rejected",
            }
      );
      const failed_count = results.filter((r) => r.status === "failed").length;
      return Promise.resolve(
        jsonResponse(200, { results, succeeded_count: results.length - failed_count, failed_count })
      );
    }

    const acceptMatch = path.match(/^\/domains\/([A-Z]+)\/proposals\/([^/]+)\/accept$/);
    if (acceptMatch && method === "POST") {
      return Promise.resolve(
        jsonResponse(200, {
          proposal_id: acceptMatch[2],
          assertion_id: "a1",
          assertion_path: "/x",
          reviewed_by: "test-reviewer",
          reviewed_at: "2026-09-03T00:00:00",
        })
      );
    }

    const rejectMatch = path.match(/^\/domains\/([A-Z]+)\/proposals\/([^/]+)\/reject$/);
    if (rejectMatch && method === "POST") {
      return Promise.resolve(
        jsonResponse(200, {
          proposal_id: rejectMatch[2],
          reviewed_by: "test-reviewer",
          reviewed_at: "2026-09-03T00:00:00",
          rejection_reason: null,
        })
      );
    }

    const ingestionsMatch = path.match(/^\/domains\/([A-Z]+)\/ingestions$/);
    if (ingestionsMatch && method === "GET") {
      const items = ingestionsByDomain[ingestionsMatch[1]] || [];
      return Promise.resolve(jsonResponse(200, { items, total: items.length, limit: 500, offset: 0 }));
    }

    return Promise.resolve(jsonResponse(404, { error: { type: "NotFound", message: "unhandled in test" } }));
  });
}

function renderValidation() {
  return render(
    <MemoryRouter>
      <Validation />
    </MemoryRouter>
  );
}

describe("Validation", () => {
  beforeEach(() => {
    global.fetch = makeFetchMock();
  });

  it("AC1: fetches proposals across domains, groups by source, and renders correct group/note counts", async () => {
    global.fetch = makeFetchMock({
      proposalsByDomain: {
        PERSONAL: [makeSummary({ id: "p1" }), makeSummary({ id: "p2" })],
        FICTION: [makeSummary({ id: "p3", domain: "FICTION" })],
      },
      detailsById: {
        p1: makeDetail({ id: "p1", sourceId: "src-a", filename: "notes-a.md", body: "Note A1" }),
        p2: makeDetail({ id: "p2", sourceId: "src-a", filename: "notes-a.md", body: "Note A2" }),
        p3: makeDetail({ id: "p3", domain: "FICTION", sourceId: "src-b", filename: "roman.md", body: "Note B1" }),
      },
    });

    renderValidation();

    await screen.findByText(/notes-a\.md/);
    expect(screen.getByText("Note A1")).toBeInTheDocument();
    expect(screen.getByText("Note A2")).toBeInTheDocument();
    expect(screen.getByText("2 notes proposées")).toBeInTheDocument();

    expect(screen.getByText(/roman\.md/)).toBeInTheDocument();
    expect(screen.getByText("Note B1")).toBeInTheDocument();
    expect(screen.getByText("1 notes proposées")).toBeInTheDocument();
  });

  it("AC2: renders all 4 real epistemic status values, not just the mockup's 2", async () => {
    global.fetch = makeFetchMock({
      proposalsByDomain: {
        PERSONAL: [
          makeSummary({ id: "p1", epistemicStatus: "direct" }),
          makeSummary({ id: "p2", epistemicStatus: "inferred" }),
          makeSummary({ id: "p3", epistemicStatus: "uncertain" }),
          makeSummary({ id: "p4", epistemicStatus: "contested" }),
        ],
      },
      detailsById: {
        p1: makeDetail({ id: "p1", sourceId: "src-a", body: "N1" }),
        p2: makeDetail({ id: "p2", sourceId: "src-a", body: "N2" }),
        p3: makeDetail({ id: "p3", sourceId: "src-a", body: "N3" }),
        p4: makeDetail({ id: "p4", sourceId: "src-a", body: "N4" }),
      },
    });

    renderValidation();
    await screen.findByText("Direct");

    // Scoped to the actual status badges (.epistemic-badge), not getByText,
    // since TASK-015's Statut épistémique filter <select> now also renders
    // "Inféré"/"Incertain"/"Contesté" as <option> text in the same DOM.
    const badgeTexts = Array.from(document.querySelectorAll(".epistemic-badge")).map((el) => el.textContent);
    expect(badgeTexts).toEqual(expect.arrayContaining(["Direct", "Inféré", "Incertain", "Contesté"]));
  });

  it("AC3 (TASK-014 AC19: folder-path column now present; TASK-015: bulk-action buttons now present)", async () => {
    global.fetch = makeFetchMock({
      proposalsByDomain: { PERSONAL: [makeSummary({ id: "p1" })] },
      detailsById: { p1: makeDetail({ id: "p1", sourceId: "src-a" }) },
    });

    renderValidation();
    await screen.findByText(/notes\.md/);

    expect(screen.getByRole("button", { name: /Tout accepter/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Tout rejeter/ })).toBeInTheDocument();
    expect(screen.getAllByRole("columnheader")).toHaveLength(5);
    expect(screen.getByRole("columnheader", { name: "Dossier proposé" })).toBeInTheDocument();
  });

  it("amends TASK-014 AC19: NoteRow renders proposed_path_segments editable, matching the mockup", async () => {
    global.fetch = makeFetchMock({
      proposalsByDomain: { PERSONAL: [makeSummary({ id: "p1" })] },
      detailsById: {
        p1: makeDetail({ id: "p1", sourceId: "src-a", proposedPathSegments: ["mythologie", "japonaise"] }),
      },
    });

    renderValidation();
    await screen.findByText(/notes\.md/);

    expect(screen.getByRole("button", { name: /mythologie/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /japonaise/ })).toBeInTheDocument();
    expect(document.querySelector(".folder-add-btn")).toBeInTheDocument();
  });

  it("editing a segment calls editProposal with the new path and updates the row without a full refetch", async () => {
    const user = userEvent.setup();
    global.fetch = makeFetchMock({
      proposalsByDomain: { PERSONAL: [makeSummary({ id: "p1" })] },
      detailsById: {
        p1: makeDetail({ id: "p1", sourceId: "src-a", proposedPathSegments: ["mythologie", "japonaise"] }),
      },
      organizationFoldersByDomain: { PERSONAL: [["mythologie", "geographie"], ["japonaise", "nordique"]] },
    });

    renderValidation();
    await screen.findByText(/notes\.md/);

    await user.click(screen.getByRole("button", { name: /japonaise/ }));
    await user.click(screen.getByText("nordique"));

    await waitFor(() => {
      expect(
        global.fetch.mock.calls.find(([url]) => new URL(url).pathname.endsWith("/edit"))
      ).toBeDefined();
    });

    const [, editOptions] = global.fetch.mock.calls.find(([url]) => new URL(url).pathname.endsWith("/edit"));
    const editBody = JSON.parse(editOptions.body);
    expect(editBody.field_updates.proposed_path_segments).toEqual(["mythologie", "nordique"]);

    expect(screen.getByRole("button", { name: /nordique/ })).toBeInTheDocument();
  });

  it("reverts the optimistic path update and surfaces actionError when editProposal fails", async () => {
    const user = userEvent.setup();
    global.fetch = makeFetchMock({
      proposalsByDomain: { PERSONAL: [makeSummary({ id: "p1" })] },
      detailsById: {
        p1: makeDetail({ id: "p1", sourceId: "src-a", proposedPathSegments: ["mythologie", "japonaise"] }),
      },
      organizationFoldersByDomain: { PERSONAL: [["mythologie"], ["japonaise", "nordique"]] },
      editShouldFail: true,
    });

    renderValidation();
    await screen.findByText(/notes\.md/);

    await user.click(screen.getByRole("button", { name: /japonaise/ }));
    await user.click(screen.getByText("nordique"));

    await screen.findByText(/Action impossible/);
    expect(screen.getByRole("button", { name: /japonaise/ })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /nordique/ })).not.toBeInTheDocument();
  });

  it("AC4: accepting a note calls POST accept with the configured reviewer_id and removes it from its group", async () => {
    global.fetch = makeFetchMock({
      proposalsByDomain: { PERSONAL: [makeSummary({ id: "p1" })] },
      detailsById: { p1: makeDetail({ id: "p1", sourceId: "src-a", body: "Contenu de test" }) },
    });
    const user = userEvent.setup();
    renderValidation();
    await screen.findByText("Contenu de test");

    global.fetch.mockClear();
    await user.click(screen.getByRole("button", { name: /Accepter/ }));

    const acceptCall = global.fetch.mock.calls.find(([url]) => new URL(url).pathname.endsWith("/accept"));
    expect(acceptCall).toBeDefined();
    expect(JSON.parse(acceptCall[1].body)).toEqual({ reviewer_id: "test-reviewer" });

    await waitFor(() => expect(screen.queryByText("Contenu de test")).not.toBeInTheDocument());
  });

  it("AC5 (TASK-015 item 10: individual reject now funnels through reject-batch with a 1-item id list): rejecting opens the shared reason modal; submitting calls POST reject-batch with the entered reason", async () => {
    global.fetch = makeFetchMock({
      proposalsByDomain: { PERSONAL: [makeSummary({ id: "p1" })] },
      detailsById: { p1: makeDetail({ id: "p1", sourceId: "src-a", body: "Contenu de test" }) },
    });
    const user = userEvent.setup();
    renderValidation();
    await screen.findByText("Contenu de test");

    await user.click(screen.getByRole("button", { name: /Rejeter/ }));
    expect(screen.getByRole("dialog")).toBeInTheDocument();

    await user.type(screen.getByLabelText(/Raison/), "Pas assez fiable");
    global.fetch.mockClear();
    await user.click(screen.getByRole("button", { name: /Confirmer le rejet/ }));

    const rejectCall = await waitFor(() =>
      global.fetch.mock.calls.find(([url]) => new URL(url).pathname.endsWith("/reject-batch"))
    );
    expect(JSON.parse(rejectCall[1].body)).toEqual({
      reviewer_id: "test-reviewer",
      proposal_ids: ["p1"],
      reason: "Pas assez fiable",
    });
  });

  it("AC5b: submitting the reject modal with a blank reason sends reason: null", async () => {
    global.fetch = makeFetchMock({
      proposalsByDomain: { PERSONAL: [makeSummary({ id: "p1" })] },
      detailsById: { p1: makeDetail({ id: "p1", sourceId: "src-a", body: "Contenu de test" }) },
    });
    const user = userEvent.setup();
    renderValidation();
    await screen.findByText("Contenu de test");

    await user.click(screen.getByRole("button", { name: /Rejeter/ }));
    global.fetch.mockClear();
    await user.click(screen.getByRole("button", { name: /Confirmer le rejet/ }));

    const rejectCall = await waitFor(() =>
      global.fetch.mock.calls.find(([url]) => new URL(url).pathname.endsWith("/reject-batch"))
    );
    expect(JSON.parse(rejectCall[1].body)).toEqual({
      reviewer_id: "test-reviewer",
      proposal_ids: ["p1"],
      reason: null,
    });
  });

  it("AC6: shows the joined ingestion task status badge when matched, renders cleanly with no badge when not matched", async () => {
    global.fetch = makeFetchMock({
      proposalsByDomain: {
        PERSONAL: [makeSummary({ id: "p1" }), makeSummary({ id: "p2" })],
      },
      detailsById: {
        p1: makeDetail({ id: "p1", sourceId: "src-matched", filename: "matched.md" }),
        p2: makeDetail({ id: "p2", sourceId: "src-orphan", filename: "orphan.md" }),
      },
      ingestionsByDomain: {
        PERSONAL: [
          {
            task_id: "ingest-1",
            source_path: "matched.md",
            domain: "PERSONAL",
            status: "completed",
            started_at: "2026-08-25T09:00:00",
            completed_at: "2026-08-25T09:05:00",
            error: null,
            source_id: "src-matched",
            proposal_ids: [],
            events: [],
          },
        ],
      },
    });

    renderValidation();
    await screen.findByText(/matched\.md/);

    const matchedHeader = screen.getByText(/matched\.md/).closest(".source-header-row");
    expect(within(matchedHeader).getByText("Complété")).toBeInTheDocument();

    const orphanHeader = screen.getByText(/orphan\.md/).closest(".source-header-row");
    expect(within(orphanHeader).queryByText(/Complété|En attente|En cours|Échoué|Doublon/)).not.toBeInTheDocument();
  });

  it("TASK-001d AC6: shows the most recent task's status when a source has multiple ingestion tasks, not the oldest", async () => {
    global.fetch = makeFetchMock({
      proposalsByDomain: {
        PERSONAL: [makeSummary({ id: "p1" })],
      },
      detailsById: {
        p1: makeDetail({ id: "p1", sourceId: "src-retried", filename: "retried.md" }),
      },
      ingestionsByDomain: {
        // Mirrors the real API's started_at-descending order (sort_by_recency):
        // the newer, completed task first, the older, failed one second - this
        // is the order that actually exercises the fix (the pre-fix code kept
        // whichever task was iterated last, so a fixture in the opposite,
        // "convenient" order would let the old bug pass by coincidence).
        PERSONAL: [
          {
            task_id: "ingest-2",
            source_path: "retried.md",
            domain: "PERSONAL",
            status: "completed",
            started_at: "2026-08-25T10:00:00",
            completed_at: "2026-08-25T10:05:00",
            error: null,
            source_id: "src-retried",
            proposal_ids: [],
            events: [],
          },
          {
            task_id: "ingest-1",
            source_path: "retried.md",
            domain: "PERSONAL",
            status: "failed",
            started_at: "2026-08-25T09:00:00",
            completed_at: "2026-08-25T09:01:00",
            error: "Provider failed",
            source_id: "src-retried",
            proposal_ids: [],
            events: [],
          },
        ],
      },
    });

    renderValidation();
    await screen.findByText(/retried\.md/);

    const header = screen.getByText(/retried\.md/).closest(".source-header-row");
    expect(within(header).getByText("Complété")).toBeInTheDocument();
    expect(within(header).queryByText("Échoué")).not.toBeInTheDocument();
  });

  it("AC7: domain filter re-scopes which domains are queried across all three fetch stages", async () => {
    global.fetch = makeFetchMock({
      proposalsByDomain: { PERSONAL: [makeSummary({ id: "p1" })] },
      detailsById: { p1: makeDetail({ id: "p1", sourceId: "src-a" }) },
    });
    const user = userEvent.setup();
    renderValidation();
    await screen.findByText(/notes\.md/);

    global.fetch.mockClear();
    await user.selectOptions(screen.getByLabelText("Domaine"), "PERSONAL");

    await waitFor(() => {
      const domainsQueried = new Set(
        global.fetch.mock.calls
          .filter(([url]) => /^\/domains\//.test(new URL(url).pathname))
          .map(([url]) => new URL(url).pathname.split("/")[2])
      );
      expect(domainsQueried.size).toBe(1);
      expect(domainsQueried.has("PERSONAL")).toBe(true);
    });
  });

  it("AC8: 'Détails' links to /validation/<domain>/<proposalId>", async () => {
    global.fetch = makeFetchMock({
      proposalsByDomain: { PERSONAL: [makeSummary({ id: "p1" })] },
      detailsById: { p1: makeDetail({ id: "p1", sourceId: "src-a" }) },
    });
    renderValidation();
    await screen.findByText(/notes\.md/);

    expect(screen.getByRole("link", { name: "Détails" })).toHaveAttribute("href", "/validation/PERSONAL/p1");
  });

  it("TASK-013 AC16: merges PROPOSED and EDITED proposals into the displayed queue", async () => {
    global.fetch = makeFetchMock({
      proposalsByDomainAndStatus: {
        "PERSONAL:PROPOSED": [makeSummary({ id: "p1" })],
        "PERSONAL:EDITED": [{ ...makeSummary({ id: "p2" }), proposal_status: "EDITED" }],
      },
      detailsById: {
        p1: makeDetail({ id: "p1", sourceId: "src-a", body: "Note proposée" }),
        p2: makeDetail({ id: "p2", sourceId: "src-a", body: "Note éditée" }),
      },
    });

    renderValidation();

    await screen.findByText("Note proposée");
    expect(screen.getByText("Note éditée")).toBeInTheDocument();
  });

  it("AC10: shows a loading state while requests are in flight, then an error state on failure", async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve(
        jsonResponse(401, { error: { type: "Unauthorized", message: "Missing or invalid X-API-Key header" } })
      )
    );

    renderValidation();
    expect(screen.getByText(/Chargement des propositions/)).toBeInTheDocument();

    expect(await screen.findByRole("alert")).toHaveTextContent("Missing or invalid X-API-Key header");
  });

  it("bonus: Prev/Next paginates whole groups without ever splitting one across pages", async () => {
    const groupAIds = Array.from({ length: 7 }, (_, i) => `a${i}`);
    const groupBIds = Array.from({ length: 6 }, (_, i) => `b${i}`);
    const detailsById = {};
    groupAIds.forEach((id) => {
      detailsById[id] = makeDetail({ id, sourceId: "src-a", filename: "source-a.md", body: `Note ${id}` });
    });
    groupBIds.forEach((id) => {
      detailsById[id] = makeDetail({ id, sourceId: "src-b", filename: "source-b.md", body: `Note ${id}` });
    });

    global.fetch = makeFetchMock({
      proposalsByDomain: {
        PERSONAL: [...groupAIds, ...groupBIds].map((id) => makeSummary({ id })),
      },
      detailsById,
    });

    const user = userEvent.setup();
    renderValidation();

    await screen.findByText(/source-a\.md/);
    expect(screen.queryByText(/source-b\.md/)).not.toBeInTheDocument();
    expect(screen.getByText("Affichage 1-7 notes sur 13 notes · 2 sources")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /Suivant/ }));

    expect(await screen.findByText(/source-b\.md/)).toBeInTheDocument();
    expect(screen.queryByText(/source-a\.md/)).not.toBeInTheDocument();
    expect(screen.getByText("Affichage 8-13 notes sur 13 notes · 2 sources")).toBeInTheDocument();
  });

  it("regression: accepting the last note on the last page falls back to the previous page instead of an empty state (bug found in code review)", async () => {
    // Group A alone already fills a page (10 notes = NOTES_PER_PAGE), so
    // group B stays isolated on its own page no matter how many of its
    // notes remain - only emptying it entirely collapses the page count.
    const groupAIds = Array.from({ length: 10 }, (_, i) => `a${i}`);
    const groupBIds = ["b0", "b1", "b2"];
    const detailsById = {};
    groupAIds.forEach((id) => {
      detailsById[id] = makeDetail({ id, sourceId: "src-a", filename: "source-a.md", body: `Note ${id}` });
    });
    groupBIds.forEach((id) => {
      detailsById[id] = makeDetail({ id, sourceId: "src-b", filename: "source-b.md", body: `Note ${id}` });
    });

    global.fetch = makeFetchMock({
      proposalsByDomain: {
        PERSONAL: [...groupAIds, ...groupBIds].map((id) => makeSummary({ id })),
      },
      detailsById,
    });

    const user = userEvent.setup();
    renderValidation();

    await screen.findByText(/source-a\.md/);
    await user.click(screen.getByRole("button", { name: /Suivant/ }));
    await screen.findByText(/source-b\.md/);

    for (const id of groupBIds) {
      await user.click(screen.getAllByRole("button", { name: /Accepter/ })[0]);
      await waitFor(() => expect(screen.queryByText(`Note ${id}`)).not.toBeInTheDocument());
    }

    // Group B is now empty and filtered out, collapsing 2 pages into 1 - the
    // stale `page` state (still 1) must not render an out-of-range slice.
    expect(await screen.findByText(/source-a\.md/)).toBeInTheDocument();
    expect(screen.queryByText("Aucune proposition")).not.toBeInTheDocument();
    expect(screen.getByText("Affichage 1-10 notes sur 10 notes · 1 sources")).toBeInTheDocument();
  });

  it("TASK-012 AC13/AC14/AC15, TASK-005a AC18: renders all 4 proposal types with type-specific fields, folder-path builder on every row", async () => {
    global.fetch = makeFetchMock({
      proposalsByDomain: {
        PERSONAL: [
          makeSummary({ id: "p-assert", itemType: "assertion" }),
          makeSummary({ id: "p-entity", itemType: "entity" }),
        ],
        FICTION: [
          makeSummary({ id: "p-event", domain: "FICTION", itemType: "event" }),
          makeSummary({ id: "p-rel", domain: "FICTION", itemType: "relationship" }),
        ],
      },
      detailsById: {
        "p-assert": makeDetail({ id: "p-assert", sourceId: "src-a", body: "Assertion body", itemType: "assertion" }),
        "p-entity": makeDetail({
          id: "p-entity", sourceId: "src-a", body: "Entity body", itemType: "entity", entityType: "person",
        }),
        "p-event": makeDetail({
          id: "p-event", domain: "FICTION", sourceId: "src-b", body: "Event body", itemType: "event",
          startsAt: "2026-08-01T10:00:00", endsAt: null,
        }),
        "p-rel": makeDetail({
          id: "p-rel", domain: "FICTION", sourceId: "src-b", body: "Relationship body", itemType: "relationship",
          relationshipType: "attended", endpoints: ["p-entity", "some-canonical-id"],
        }),
      },
    });

    renderValidation();

    await screen.findByText("Assertion body");
    expect(screen.getByText("Entity body")).toBeInTheDocument();
    expect(screen.getByText("Event body")).toBeInTheDocument();
    expect(screen.getByText("Relationship body")).toBeInTheDocument();

    // AC14: entity badge and event temporal range render; a null endsAt doesn't crash.
    expect(screen.getByText("person")).toBeInTheDocument();
    expect(screen.getByText("2026-08-01T10:00:00 → non précisé")).toBeInTheDocument();

    // AC15: an endpoint matching an already-fetched proposal resolves to a
    // label; one matching nothing fetched renders as a plain identifier.
    expect(screen.getByText(/entity: Entity body/)).toBeInTheDocument();
    expect(screen.getByText("some-canonical-id")).toBeInTheDocument();

    // TASK-005a AC18: every row, not just assertion, gets a folder-path builder.
    for (const text of ["Assertion body", "Entity body", "Event body", "Relationship body"]) {
      const row = screen.getByText(text).closest("tr");
      expect(row.querySelector(".folder-cell")).not.toBeEmptyDOMElement();
    }
  });

  it("TASK-005a AC18: each row's dropdown options come from its own item type's folder list, never another type's", async () => {
    const user = userEvent.setup();
    global.fetch = makeFetchMock({
      proposalsByDomain: {
        PERSONAL: [
          makeSummary({ id: "p-assert", itemType: "assertion" }),
          makeSummary({ id: "p-entity", itemType: "entity" }),
        ],
      },
      detailsById: {
        "p-assert": makeDetail({
          id: "p-assert", sourceId: "src-a", body: "Assertion body", itemType: "assertion",
          proposedPathSegments: ["existing"],
        }),
        "p-entity": makeDetail({
          id: "p-entity", sourceId: "src-a", body: "Entity body", itemType: "entity", entityType: "person",
          proposedPathSegments: ["existing"],
        }),
      },
      organizationFoldersByDomain: {
        PERSONAL: {
          assertion: [["mythologie"]],
          entity: [["personnages"]],
          event: [["guerre"]],
          relationship: [["famille"]],
        },
      },
    });

    renderValidation();
    await screen.findByText("Assertion body");

    const assertRow = screen.getByText("Assertion body").closest("tr");
    await user.click(within(assertRow).getByRole("button", { name: /existing/ }));
    expect(within(assertRow).getByText("mythologie")).toBeInTheDocument();
    expect(within(assertRow).queryByText("personnages")).not.toBeInTheDocument();

    const entityRow = screen.getByText("Entity body").closest("tr");
    await user.click(within(entityRow).getByRole("button", { name: /existing/ }));
    expect(within(entityRow).getByText("personnages")).toBeInTheDocument();
    expect(within(entityRow).queryByText("mythologie")).not.toBeInTheDocument();
  });

  it("TASK-014a AC13: NoteRow renders context read-only, for all 4 types, with no edit affordance", async () => {
    global.fetch = makeFetchMock({
      proposalsByDomain: {
        PERSONAL: [
          makeSummary({ id: "p-assert", itemType: "assertion" }),
          makeSummary({ id: "p-entity", itemType: "entity" }),
        ],
        FICTION: [
          makeSummary({ id: "p-event", domain: "FICTION", itemType: "event" }),
          makeSummary({ id: "p-rel", domain: "FICTION", itemType: "relationship" }),
        ],
      },
      detailsById: {
        "p-assert": makeDetail({
          id: "p-assert", sourceId: "src-a", body: "Assertion body", itemType: "assertion", context: "tatouages",
        }),
        "p-entity": makeDetail({
          id: "p-entity", sourceId: "src-a", body: "Entity body", itemType: "entity", entityType: "person",
          context: "tatouages",
        }),
        "p-event": makeDetail({
          id: "p-event", domain: "FICTION", sourceId: "src-b", body: "Event body", itemType: "event",
          startsAt: "2026-08-01T10:00:00", endsAt: null, context: null,
        }),
        "p-rel": makeDetail({
          id: "p-rel", domain: "FICTION", sourceId: "src-b", body: "Relationship body", itemType: "relationship",
          relationshipType: "attended", endpoints: [], context: "autre-roman",
        }),
      },
    });

    renderValidation();

    await screen.findByText("Assertion body");
    expect(screen.getByRole("columnheader", { name: "Contexte" })).toBeInTheDocument();
    expect(screen.getAllByText("tatouages")).toHaveLength(2);
    expect(screen.getByText("autre-roman")).toBeInTheDocument();
    const eventRow = screen.getByText("Event body").closest("tr");
    expect(within(eventRow).getByText("—")).toBeInTheDocument();

    // No edit affordance in the context cell of any row - it's plain text,
    // not a button/input.
    for (const text of ["Assertion body", "Entity body", "Event body", "Relationship body"]) {
      const row = screen.getByText(text).closest("tr");
      const contextCell = row.querySelector(".context-value").closest("td");
      expect(within(contextCell).queryByRole("button")).not.toBeInTheDocument();
      expect(within(contextCell).queryByRole("textbox")).not.toBeInTheDocument();
    }
  });

  it("TASK-005a AC19: a failed organization-folders fetch for one domain/type leaves the rest of the screen rendering, with that row's options degraded to []", async () => {
    global.fetch = vi.fn((url, options = {}) => {
      const parsed = new URL(url);
      const path = parsed.pathname;
      if (path === "/domains/PERSONAL/organization-folders" && parsed.searchParams.get("item_type") === "entity") {
        return Promise.reject(new Error("network error"));
      }
      return makeFetchMock({
        proposalsByDomain: { PERSONAL: [makeSummary({ id: "p-entity", itemType: "entity" })] },
        detailsById: {
          "p-entity": makeDetail({
            id: "p-entity", sourceId: "src-a", body: "Entity body", itemType: "entity", entityType: "person",
          }),
        },
      })(url, options);
    });

    renderValidation();

    await screen.findByText("Entity body");
    const entityRow = screen.getByText("Entity body").closest("tr");
    expect(entityRow.querySelector(".folder-cell")).not.toBeEmptyDOMElement();
    expect(entityRow.querySelector(".folder-add-btn")).toBeInTheDocument();
  });

  it("TASK-015 AC1: 'Tout accepter' issues exactly one accept-batch call with all N visible ids, and the whole group disappears", async () => {
    global.fetch = makeFetchMock({
      proposalsByDomain: {
        PERSONAL: [makeSummary({ id: "p1" }), makeSummary({ id: "p2" }), makeSummary({ id: "p3" })],
      },
      detailsById: {
        p1: makeDetail({ id: "p1", sourceId: "src-a", body: "Note 1" }),
        p2: makeDetail({ id: "p2", sourceId: "src-a", body: "Note 2" }),
        p3: makeDetail({ id: "p3", sourceId: "src-a", body: "Note 3" }),
      },
    });
    const user = userEvent.setup();
    renderValidation();
    await screen.findByText(/notes\.md/);

    global.fetch.mockClear();
    await user.click(screen.getByRole("button", { name: /Tout accepter/ }));

    const batchCalls = await waitFor(() => {
      const calls = global.fetch.mock.calls.filter(([url]) => new URL(url).pathname.endsWith("/accept-batch"));
      expect(calls.length).toBeGreaterThan(0);
      return calls;
    });
    expect(batchCalls).toHaveLength(1);
    expect(JSON.parse(batchCalls[0][1].body)).toEqual({ reviewer_id: "test-reviewer", proposal_ids: ["p1", "p2", "p3"] });

    await waitFor(() => expect(screen.queryByText(/notes\.md/)).not.toBeInTheDocument());
  });

  it("TASK-015 AC2: a partial-failure accept-batch keeps the failed note visible, removes the rest, and surfaces one banner message per failure", async () => {
    global.fetch = makeFetchMock({
      proposalsByDomain: { PERSONAL: [makeSummary({ id: "p1" }), makeSummary({ id: "p2" })] },
      detailsById: {
        p1: makeDetail({ id: "p1", sourceId: "src-a", body: "Note 1" }),
        p2: makeDetail({ id: "p2", sourceId: "src-a", body: "Note 2" }),
      },
      acceptBatchFailIds: ["p1"],
    });
    const user = userEvent.setup();
    renderValidation();
    await screen.findByText("Note 1");

    await user.click(screen.getByRole("button", { name: /Tout accepter/ }));

    await waitFor(() => expect(screen.queryByText("Note 2")).not.toBeInTheDocument());
    expect(screen.getByText("Note 1")).toBeInTheDocument();
    expect(screen.getByText(/1\/2 notes traitées, 1 échouée/)).toBeInTheDocument();
    expect(screen.getByText(/p1/)).toBeInTheDocument();
  });

  it("TASK-015 AC3: 'Tout rejeter' opens exactly one reason modal for the group; confirming sends every visible id plus the shared reason", async () => {
    global.fetch = makeFetchMock({
      proposalsByDomain: {
        PERSONAL: [makeSummary({ id: "p1" }), makeSummary({ id: "p2" }), makeSummary({ id: "p3" })],
      },
      detailsById: {
        p1: makeDetail({ id: "p1", sourceId: "src-a", body: "Note 1" }),
        p2: makeDetail({ id: "p2", sourceId: "src-a", body: "Note 2" }),
        p3: makeDetail({ id: "p3", sourceId: "src-a", body: "Note 3" }),
      },
    });
    const user = userEvent.setup();
    renderValidation();
    await screen.findByText(/notes\.md/);

    await user.click(screen.getByRole("button", { name: /Tout rejeter/ }));
    expect(screen.getAllByRole("dialog")).toHaveLength(1);

    await user.type(screen.getByLabelText(/Raison/), "Source peu fiable");
    global.fetch.mockClear();
    await user.click(screen.getByRole("button", { name: /Confirmer le rejet/ }));

    const rejectCall = await waitFor(() =>
      global.fetch.mock.calls.find(([url]) => new URL(url).pathname.endsWith("/reject-batch"))
    );
    expect(JSON.parse(rejectCall[1].body)).toEqual({
      reviewer_id: "test-reviewer",
      proposal_ids: ["p1", "p2", "p3"],
      reason: "Source peu fiable",
    });
  });

  it("TASK-015 AC4: Type de proposition filter hides notes of other types and restores them when reset to Tous", async () => {
    global.fetch = makeFetchMock({
      proposalsByDomain: {
        PERSONAL: [makeSummary({ id: "p-assert" }), makeSummary({ id: "p-entity" })],
      },
      detailsById: {
        "p-assert": makeDetail({ id: "p-assert", sourceId: "src-a", body: "Assertion body", itemType: "assertion" }),
        "p-entity": makeDetail({
          id: "p-entity", sourceId: "src-a", body: "Entity body", itemType: "entity", entityType: "person",
        }),
      },
    });
    const user = userEvent.setup();
    renderValidation();
    await screen.findByText("Assertion body");
    expect(screen.getByText("Entity body")).toBeInTheDocument();

    await user.selectOptions(screen.getByLabelText("Type de proposition"), "assertion");
    expect(screen.getByText("Assertion body")).toBeInTheDocument();
    expect(screen.queryByText("Entity body")).not.toBeInTheDocument();

    await user.selectOptions(screen.getByLabelText("Type de proposition"), "all");
    expect(screen.getByText("Assertion body")).toBeInTheDocument();
    expect(screen.getByText("Entity body")).toBeInTheDocument();
  });

  it("TASK-015 AC5: Statut épistémique filter composes with the Type filter (only the fully-matching note remains)", async () => {
    global.fetch = makeFetchMock({
      proposalsByDomain: {
        PERSONAL: [
          makeSummary({ id: "p1", itemType: "assertion", epistemicStatus: "direct" }),
          makeSummary({ id: "p2", itemType: "assertion", epistemicStatus: "inferred" }),
          makeSummary({ id: "p3", itemType: "entity", epistemicStatus: "direct" }),
        ],
      },
      detailsById: {
        p1: makeDetail({ id: "p1", sourceId: "src-a", body: "N1 body", itemType: "assertion" }),
        p2: makeDetail({ id: "p2", sourceId: "src-a", body: "N2 body", itemType: "assertion" }),
        p3: makeDetail({ id: "p3", sourceId: "src-a", body: "N3 body", itemType: "entity", entityType: "person" }),
      },
    });
    const user = userEvent.setup();
    renderValidation();
    await screen.findByText("N1 body");

    await user.selectOptions(screen.getByLabelText("Type de proposition"), "assertion");
    await user.selectOptions(screen.getByLabelText("Statut épistémique"), "direct");

    expect(screen.getByText("N1 body")).toBeInTheDocument();
    expect(screen.queryByText("N2 body")).not.toBeInTheDocument();
    expect(screen.queryByText("N3 body")).not.toBeInTheDocument();
  });

  it("TASK-015 AC6: the sort control reorders groups by their most recent note's created_at, both directions", async () => {
    global.fetch = makeFetchMock({
      proposalsByDomain: {
        PERSONAL: [
          makeSummary({ id: "n1", createdAt: "2026-01-01T00:00:00" }),
          makeSummary({ id: "n2", createdAt: "2026-03-01T00:00:00" }),
          makeSummary({ id: "n3", createdAt: "2026-02-01T00:00:00" }),
        ],
      },
      detailsById: {
        n1: makeDetail({ id: "n1", sourceId: "src-1", filename: "one.md", body: "Note 1" }),
        n2: makeDetail({ id: "n2", sourceId: "src-2", filename: "two.md", body: "Note 2" }),
        n3: makeDetail({ id: "n3", sourceId: "src-3", filename: "three.md", body: "Note 3" }),
      },
    });
    const user = userEvent.setup();
    renderValidation();
    await screen.findByText(/two\.md/);

    const filenamesInOrder = () =>
      Array.from(document.querySelectorAll(".source-file")).map((el) => el.textContent);

    expect(filenamesInOrder()).toEqual([
      expect.stringContaining("two.md"),
      expect.stringContaining("three.md"),
      expect.stringContaining("one.md"),
    ]);

    await user.selectOptions(screen.getByLabelText("Tri"), "oldest");

    expect(filenamesInOrder()).toEqual([
      expect.stringContaining("one.md"),
      expect.stringContaining("three.md"),
      expect.stringContaining("two.md"),
    ]);
  });

  it("TASK-015 AC7: a note filtered out by the Type filter is excluded from that group's next accept-batch call", async () => {
    global.fetch = makeFetchMock({
      proposalsByDomain: {
        PERSONAL: [makeSummary({ id: "p-assert" }), makeSummary({ id: "p-entity" })],
      },
      detailsById: {
        "p-assert": makeDetail({ id: "p-assert", sourceId: "src-a", body: "Assertion body", itemType: "assertion" }),
        "p-entity": makeDetail({
          id: "p-entity", sourceId: "src-a", body: "Entity body", itemType: "entity", entityType: "person",
        }),
      },
    });
    const user = userEvent.setup();
    renderValidation();
    await screen.findByText("Assertion body");

    await user.selectOptions(screen.getByLabelText("Type de proposition"), "assertion");
    global.fetch.mockClear();
    await user.click(screen.getByRole("button", { name: /Tout accepter/ }));

    const batchCall = await waitFor(() =>
      global.fetch.mock.calls.find(([url]) => new URL(url).pathname.endsWith("/accept-batch"))
    );
    expect(JSON.parse(batchCall[1].body).proposal_ids).toEqual(["p-assert"]);
  });

  it("TASK-015 AC9: individual accept still calls the pre-existing single-item /accept endpoint, never /accept-batch", async () => {
    global.fetch = makeFetchMock({
      proposalsByDomain: { PERSONAL: [makeSummary({ id: "p1" })] },
      detailsById: { p1: makeDetail({ id: "p1", sourceId: "src-a", body: "Contenu de test" }) },
    });
    const user = userEvent.setup();
    renderValidation();
    await screen.findByText("Contenu de test");

    global.fetch.mockClear();
    await user.click(screen.getByRole("button", { name: /^✓ Accepter$/ }));

    await waitFor(() => {
      expect(global.fetch.mock.calls.some(([url]) => new URL(url).pathname.endsWith("/accept"))).toBe(true);
    });
    expect(global.fetch.mock.calls.some(([url]) => new URL(url).pathname.endsWith("/accept-batch"))).toBe(false);
  });
});

// AC9 (Dashboard "Validation" card is available and navigates to
// /validation) is covered in Dashboard.test.jsx, alongside the rest of that
// page's module-card assertions.
// AC11 (no file under src/ modified) is not a runtime assertion this suite
// can make - verified via `git status --porcelain -- src/` per the ticket's
// verification pass.
