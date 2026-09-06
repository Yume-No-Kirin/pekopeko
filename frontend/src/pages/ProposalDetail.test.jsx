import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import ProposalDetail from "./ProposalDetail.jsx";

function jsonResponse(status, body) {
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText: "",
    json: async () => body,
  };
}

function makeDetail({
  id = "p1",
  domain = "PERSONAL",
  proposalStatus = "PROPOSED",
  itemType = "assertion",
  epistemicStatus = "inferred",
  createdAt = "2026-08-25T14:23:45",
  validFrom = "2026-08-25T00:00:00",
  validUntil = null,
  sourceId = "src-a",
  extractionProvider = "ollama",
  provenanceExtra = {},
  body = "Contenu de test",
  originalFilename = "notes.md",
  contentHash = "abc123",
  ingestedAt = "2026-08-25T14:20:12",
  sourceBody = "# Source\n\nTexte source complet.",
  proposedPathSegments = [],
  entityType,
  startsAt,
  endsAt,
  relationshipType,
  endpoints,
} = {}) {
  return {
    id,
    domain,
    frontmatter: {
      id,
      domain,
      proposal_status: proposalStatus,
      proposed_item_type: itemType,
      epistemic_status: epistemicStatus,
      created_at: createdAt,
      valid_from: validFrom,
      valid_until: validUntil,
      provenance: { source_id: sourceId, extraction_provider: extractionProvider, ...provenanceExtra },
      proposed_path_segments: proposedPathSegments,
      entity_type: entityType,
      starts_at: startsAt,
      ends_at: endsAt,
      relationship_type: relationshipType,
      endpoints,
    },
    body,
    source_frontmatter: { original_filename: originalFilename, content_hash: contentHash, ingested_at: ingestedAt },
    source_body: sourceBody,
  };
}

// detailsById: { id: detail | [detail, detailAfterRefetch] }; ingestionsByDomain: { DOMAIN: [taskState, ...] };
// proposalsByDomain: { DOMAIN: [summary, ...] } (PROPOSED/assertion queue, same list
// returned regardless of status query param); proposalsByDomainAndStatus:
// { "DOMAIN:STATUS": [summary, ...] } overrides proposalsByDomain when a test needs
// PROPOSED and EDITED to differ (TASK-013 AC16); editShouldFail makes the /edit POST
// return a 400 instead of a success envelope.
function makeFetchMock({
  detailsById = {},
  ingestionsByDomain = {},
  proposalsByDomain = {},
  proposalsByDomainAndStatus = {},
  editShouldFail = false,
  organizationFoldersByDomain = {},
  acceptError = null,
} = {}) {
  return vi.fn((url, options = {}) => {
    const parsed = new URL(url);
    const path = parsed.pathname;
    const method = options.method || "GET";

    const foldersMatch = path.match(/^\/domains\/([A-Z]+)\/organization-folders$/);
    if (foldersMatch && method === "GET") {
      const segments_by_depth = organizationFoldersByDomain[foldersMatch[1]] || [];
      return Promise.resolve(jsonResponse(200, { segments_by_depth }));
    }

    const acceptMatch = path.match(/^\/domains\/([A-Z]+)\/proposals\/([^/]+)\/accept$/);
    if (acceptMatch && method === "POST") {
      if (acceptError) {
        return Promise.resolve(
          jsonResponse(acceptError.status, { error: { type: acceptError.type, message: acceptError.message } })
        );
      }
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

    const detailMatch = path.match(/^\/domains\/([A-Z]+)\/proposals\/([^/]+)$/);
    if (detailMatch && method === "GET") {
      const detail = detailsById[detailMatch[2]];
      if (!detail) {
        return Promise.resolve(jsonResponse(404, { error: { type: "ProposalNotFoundError", message: "not found" } }));
      }
      const resolved = Array.isArray(detail) ? (detail.length > 1 ? detail.shift() : detail[0]) : detail;
      return Promise.resolve(jsonResponse(200, resolved));
    }

    const listMatch = path.match(/^\/domains\/([A-Z]+)\/proposals$/);
    if (listMatch && method === "GET") {
      const domain = listMatch[1];
      const status = parsed.searchParams.get("status");
      // proposalsByDomain is a PROPOSED-only fixture from before TASK-013 added the
      // EDITED fan-out - only fall back to it for status=PROPOSED, or every fixture
      // using it would silently double its items once for each status queried.
      const items =
        proposalsByDomainAndStatus[`${domain}:${status}`] || (status === "PROPOSED" ? proposalsByDomain[domain] : null) || [];
      return Promise.resolve(jsonResponse(200, { items, total: items.length, limit: 500, offset: 0 }));
    }

    const ingestionsMatch = path.match(/^\/domains\/([A-Z]+)\/ingestions$/);
    if (ingestionsMatch && method === "GET") {
      const items = ingestionsByDomain[ingestionsMatch[1]] || [];
      return Promise.resolve(jsonResponse(200, { items, total: items.length, limit: 500, offset: 0 }));
    }

    return Promise.resolve(jsonResponse(404, { error: { type: "NotFound", message: "unhandled in test" } }));
  });
}

function renderDetailAtRoute(initialPath) {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        <Route path="/validation/:domain/:proposalId" element={<ProposalDetail />} />
        <Route path="/validation" element={<div data-testid="validation-page-marker" />} />
      </Routes>
    </MemoryRouter>
  );
}

describe("ProposalDetail", () => {
  beforeEach(() => {
    global.fetch = makeFetchMock();
  });

  it("AC1: renders status/domain/type/epistemic badges from a mocked ProposalDetail fixture", async () => {
    global.fetch = makeFetchMock({
      detailsById: { p1: makeDetail({ domain: "FICTION", epistemicStatus: "direct" }) },
    });
    renderDetailAtRoute("/validation/FICTION/p1");

    await screen.findByText("Contenu de test");
    expect(screen.getByText("À valider")).toBeInTheDocument();
    expect(screen.getByText("FICTION")).toBeInTheDocument();
    expect(screen.getByText("Assertion")).toBeInTheDocument();
    expect(screen.getByText("Direct")).toBeInTheDocument();
  });

  it("AC2: renders body read-only with no textarea or save button until Éditer is clicked", async () => {
    global.fetch = makeFetchMock({ detailsById: { p1: makeDetail({ body: "Le contenu complet de la note." }) } });
    renderDetailAtRoute("/validation/PERSONAL/p1");

    await screen.findByText("Le contenu complet de la note.");
    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
    expect(screen.queryByText(/Sauvegarder/)).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Éditer/ })).toBeInTheDocument();
  });

  it("AC3: renders source fields and full source_body with no truncation/expand-link", async () => {
    const fullSourceBody = "# Titre\n\nParagraphe complet de la source, sans troncature.";
    global.fetch = makeFetchMock({
      detailsById: {
        p1: makeDetail({
          originalFilename: "roman.md",
          contentHash: "hash-xyz",
          ingestedAt: "2026-08-25T14:20:12",
          sourceBody: fullSourceBody,
        }),
      },
    });
    renderDetailAtRoute("/validation/PERSONAL/p1");

    await screen.findByText("Contenu de test");
    expect(screen.getByText("roman.md")).toBeInTheDocument();
    expect(screen.getByText("hash-xyz")).toBeInTheDocument();
    expect(screen.getByText("2026-08-25T14:20:12")).toBeInTheDocument();
    expect(document.querySelector(".source-preview")).toHaveTextContent(
      fullSourceBody.replace(/\s+/g, " ").trim()
    );
    expect(screen.queryByText(/Voir le fichier source complet/)).not.toBeInTheDocument();
  });

  it("AC6: renders the matched ingestion task's events via the reused TaskEventLog", async () => {
    global.fetch = makeFetchMock({
      detailsById: { p1: makeDetail({ sourceId: "src-match" }) },
      ingestionsByDomain: {
        PERSONAL: [
          {
            task_id: "t1",
            source_path: "x.md",
            domain: "PERSONAL",
            status: "completed",
            started_at: "2026-08-25T09:00:00",
            completed_at: "2026-08-25T09:05:00",
            error: null,
            source_id: "src-match",
            proposal_ids: [],
            events: [{ timestamp: "2026-08-25T09:00:00", level: "info", message: "Démarrage de l'ingestion", details: null }],
          },
        ],
      },
    });
    renderDetailAtRoute("/validation/PERSONAL/p1");

    await screen.findByText("Contenu de test");
    expect(await screen.findByText("Démarrage de l'ingestion")).toBeInTheDocument();
  });

  it("AC7: renders the 'aucun journal disponible' fallback when no ingestion task matches", async () => {
    global.fetch = makeFetchMock({
      detailsById: { p1: makeDetail({ sourceId: "src-orphan" }) },
      ingestionsByDomain: { PERSONAL: [] },
    });
    renderDetailAtRoute("/validation/PERSONAL/p1");

    await screen.findByText("Contenu de test");
    expect(await screen.findByText(/aucun journal disponible/i)).toBeInTheDocument();
  });

  it("AC8: Précédent/Suivant are enabled/disabled at queue boundaries and navigate to the adjacent proposalId", async () => {
    const queue = ["p1", "p2", "p3"].map((id) => ({
      id,
      domain: "PERSONAL",
      proposal_status: "PROPOSED",
      proposed_item_type: "assertion",
      epistemic_status: "direct",
      created_at: `2026-08-25T0${id.slice(1)}:00:00`,
    }));
    global.fetch = makeFetchMock({
      detailsById: {
        p1: makeDetail({ id: "p1" }),
        p2: makeDetail({ id: "p2" }),
        p3: makeDetail({ id: "p3" }),
      },
      proposalsByDomain: { PERSONAL: queue },
    });
    const user = userEvent.setup();
    renderDetailAtRoute("/validation/PERSONAL/p1");

    await screen.findByText("Contenu de test");
    expect(screen.getByRole("button", { name: /Précédent/ })).toBeDisabled();
    expect(screen.getByRole("button", { name: /Suivant/ })).toBeEnabled();

    await user.click(screen.getByRole("button", { name: /Suivant/ }));
    await waitFor(() => expect(document.querySelector(".proposal-id")).toHaveTextContent("p2"));
    expect(screen.getByRole("button", { name: /Précédent/ })).toBeEnabled();
    expect(screen.getByRole("button", { name: /Suivant/ })).toBeEnabled();

    await user.click(screen.getByRole("button", { name: /Suivant/ }));
    await waitFor(() => expect(document.querySelector(".proposal-id")).toHaveTextContent("p3"));
    expect(screen.getByRole("button", { name: /Suivant/ })).toBeDisabled();
  });

  it("AC9: accepting calls POST accept with reviewer_id and redirects to /validation", async () => {
    global.fetch = makeFetchMock({ detailsById: { p1: makeDetail({ id: "p1" }) } });
    const user = userEvent.setup();
    renderDetailAtRoute("/validation/PERSONAL/p1");

    await screen.findByText("Contenu de test");
    global.fetch.mockClear();
    await user.click(screen.getByRole("button", { name: /Accepter/ }));

    const acceptCall = await waitFor(() =>
      global.fetch.mock.calls.find(([url]) => new URL(url).pathname.endsWith("/accept"))
    );
    expect(JSON.parse(acceptCall[1].body)).toEqual({ reviewer_id: "test-reviewer" });
    expect(await screen.findByTestId("validation-page-marker")).toBeInTheDocument();
  });

  it("AC9b: rejecting via the shared reason modal calls POST reject with the reason and redirects to /validation", async () => {
    global.fetch = makeFetchMock({ detailsById: { p1: makeDetail({ id: "p1" }) } });
    const user = userEvent.setup();
    renderDetailAtRoute("/validation/PERSONAL/p1");

    await screen.findByText("Contenu de test");
    await user.click(screen.getByRole("button", { name: /Rejeter/ }));
    expect(screen.getByRole("dialog")).toBeInTheDocument();

    await user.type(screen.getByLabelText(/Raison/), "Contenu erroné");
    global.fetch.mockClear();
    await user.click(screen.getByRole("button", { name: /Confirmer le rejet/ }));

    const rejectCall = await waitFor(() =>
      global.fetch.mock.calls.find(([url]) => new URL(url).pathname.endsWith("/reject"))
    );
    expect(JSON.parse(rejectCall[1].body)).toEqual({ reviewer_id: "test-reviewer", reason: "Contenu erroné" });
    expect(await screen.findByTestId("validation-page-marker")).toBeInTheDocument();
  });

  it("AC10: shows a loading state, then an error state on a failed fetch", async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve(jsonResponse(404, { error: { type: "ProposalNotFoundError", message: "Proposal not found" } }))
    );
    renderDetailAtRoute("/validation/PERSONAL/p1");

    expect(screen.getByText(/Chargement de la proposition/)).toBeInTheDocument();
    expect(await screen.findByRole("alert")).toHaveTextContent("Proposal not found");
  });

  it("TASK-013 AC10: clicking Éditer reveals a textarea, an epistemic-status select, and two validity inputs seeded from the current values", async () => {
    global.fetch = makeFetchMock({
      detailsById: {
        p1: makeDetail({ body: "Texte original", epistemicStatus: "uncertain", validFrom: "2026-01-01T00:00:00", validUntil: "2026-06-01T00:00:00" }),
      },
    });
    const user = userEvent.setup();
    renderDetailAtRoute("/validation/PERSONAL/p1");

    await screen.findByText("Texte original");
    await user.click(screen.getByRole("button", { name: /Éditer/ }));

    expect(screen.getByRole("textbox", { name: "Contenu de la proposition" })).toHaveValue("Texte original");
    expect(screen.getByRole("combobox")).toHaveValue("uncertain");
    expect(screen.getByDisplayValue("2026-01-01T00:00:00")).toBeInTheDocument();
    expect(screen.getByDisplayValue("2026-06-01T00:00:00")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Sauvegarder/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Annuler/ })).toBeInTheDocument();
  });

  it("TASK-013 AC11: entering edit mode hides Rejeter/Accepter/Éditer", async () => {
    global.fetch = makeFetchMock({ detailsById: { p1: makeDetail({ id: "p1" }) } });
    const user = userEvent.setup();
    renderDetailAtRoute("/validation/PERSONAL/p1");

    await screen.findByText("Contenu de test");
    await user.click(screen.getByRole("button", { name: /Éditer/ }));

    expect(screen.queryByRole("button", { name: /Rejeter/ })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Accepter/ })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Éditer/ })).not.toBeInTheDocument();
  });

  it("TASK-013 AC12: Sauvegarder calls editProposal with the draft, refetches, and exits edit mode", async () => {
    const initial = makeDetail({ id: "p1", proposalStatus: "PROPOSED", body: "Texte original" });
    const afterEdit = makeDetail({ id: "p1", proposalStatus: "EDITED", body: "Texte édité" });
    global.fetch = makeFetchMock({ detailsById: { p1: [initial, afterEdit] } });
    const user = userEvent.setup();
    renderDetailAtRoute("/validation/PERSONAL/p1");

    await screen.findByText("Texte original");
    await user.click(screen.getByRole("button", { name: /Éditer/ }));
    const textarea = screen.getByRole("textbox", { name: "Contenu de la proposition" });
    await user.clear(textarea);
    await user.type(textarea, "Texte édité");

    global.fetch.mockClear();
    await user.click(screen.getByRole("button", { name: /Sauvegarder/ }));

    const editCall = await waitFor(() =>
      global.fetch.mock.calls.find(([url]) => new URL(url).pathname.endsWith("/edit"))
    );
    expect(JSON.parse(editCall[1].body)).toEqual({
      reviewer_id: "test-reviewer",
      body: "Texte édité",
      field_updates: {
        epistemic_status: "inferred",
        valid_from: "2026-08-25T00:00:00",
        valid_until: null,
        proposed_path_segments: [],
      },
    });

    await screen.findByText("Texte édité");
    expect(screen.getByText("Éditée")).toBeInTheDocument();
    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
  });

  it("TASK-013 AC12b: a failed save keeps edit mode open with the draft intact and shows actionError", async () => {
    global.fetch = makeFetchMock({
      detailsById: { p1: makeDetail({ id: "p1", body: "Texte original" }) },
      editShouldFail: true,
    });
    const user = userEvent.setup();
    renderDetailAtRoute("/validation/PERSONAL/p1");

    await screen.findByText("Texte original");
    await user.click(screen.getByRole("button", { name: /Éditer/ }));
    const textarea = screen.getByRole("textbox", { name: "Contenu de la proposition" });
    await user.clear(textarea);
    await user.type(textarea, "Brouillon non sauvegardé");

    await user.click(screen.getByRole("button", { name: /Sauvegarder/ }));

    expect(await screen.findByRole("alert")).toHaveTextContent("edit rejected");
    expect(screen.getByRole("textbox", { name: "Contenu de la proposition" })).toHaveValue("Brouillon non sauvegardé");
    expect(screen.getByRole("button", { name: /Sauvegarder/ })).toBeInTheDocument();
  });

  it("TASK-013 AC13: Annuler exits edit mode and discards the draft without calling editProposal", async () => {
    global.fetch = makeFetchMock({ detailsById: { p1: makeDetail({ id: "p1", body: "Texte original" }) } });
    const user = userEvent.setup();
    renderDetailAtRoute("/validation/PERSONAL/p1");

    await screen.findByText("Texte original");
    await user.click(screen.getByRole("button", { name: /Éditer/ }));
    const textarea = screen.getByRole("textbox", { name: "Contenu de la proposition" });
    await user.clear(textarea);
    await user.type(textarea, "Brouillon jeté");

    global.fetch.mockClear();
    await user.click(screen.getByRole("button", { name: /Annuler/ }));

    expect(global.fetch.mock.calls.find(([url]) => new URL(url).pathname.endsWith("/edit"))).toBeUndefined();
    expect(await screen.findByText("Texte original")).toBeInTheDocument();
    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
  });

  it("TASK-013 AC15: Accepter/Rejeter still call acceptProposal/rejectProposal unchanged on an EDITED proposal", async () => {
    global.fetch = makeFetchMock({ detailsById: { p1: makeDetail({ id: "p1", proposalStatus: "EDITED" }) } });
    const user = userEvent.setup();
    renderDetailAtRoute("/validation/PERSONAL/p1");

    await screen.findByText("Contenu de test");
    global.fetch.mockClear();
    await user.click(screen.getByRole("button", { name: /Accepter/ }));

    const acceptCall = await waitFor(() =>
      global.fetch.mock.calls.find(([url]) => new URL(url).pathname.endsWith("/accept"))
    );
    expect(JSON.parse(acceptCall[1].body)).toEqual({ reviewer_id: "test-reviewer" });
  });

  it("TASK-013 AC16: merges PROPOSED and EDITED proposals into the Précédent/Suivant queue", async () => {
    global.fetch = makeFetchMock({
      detailsById: {
        p1: makeDetail({ id: "p1" }),
        p2: makeDetail({ id: "p2", proposalStatus: "EDITED" }),
      },
      proposalsByDomainAndStatus: {
        "PERSONAL:PROPOSED": [
          { id: "p1", domain: "PERSONAL", proposal_status: "PROPOSED", proposed_item_type: "assertion", epistemic_status: "direct", created_at: "2026-08-25T01:00:00" },
        ],
        "PERSONAL:EDITED": [
          { id: "p2", domain: "PERSONAL", proposal_status: "EDITED", proposed_item_type: "assertion", epistemic_status: "direct", created_at: "2026-08-25T02:00:00" },
        ],
      },
    });
    const user = userEvent.setup();
    renderDetailAtRoute("/validation/PERSONAL/p1");

    await screen.findByText("Contenu de test");
    expect(screen.getByRole("button", { name: /Suivant/ })).toBeEnabled();
    await user.click(screen.getByRole("button", { name: /Suivant/ }));
    await waitFor(() => expect(document.querySelector(".proposal-id")).toHaveTextContent("p2"));
  });

  it("TASK-014 AC18: outside edit mode renders proposed_path_segments read-only, including the empty-list case", async () => {
    global.fetch = makeFetchMock({
      detailsById: { p1: makeDetail({ id: "p1", proposedPathSegments: ["mythologie", "japonaise"] }) },
    });
    renderDetailAtRoute("/validation/PERSONAL/p1");

    await screen.findByText("Contenu de test");
    expect(screen.getByText("mythologie / japonaise")).toBeInTheDocument();
  });

  it("TASK-014 AC18: outside edit mode with no proposed_path_segments renders a placeholder without crashing", async () => {
    global.fetch = makeFetchMock({
      detailsById: { p1: makeDetail({ id: "p1", proposedPathSegments: [], validUntil: "2026-12-31T00:00:00" }) },
    });
    renderDetailAtRoute("/validation/PERSONAL/p1");

    await screen.findByText("Contenu de test");
    expect(screen.getByText("Dossier proposé")).toBeInTheDocument();
    expect(screen.getByText("—")).toBeInTheDocument();
  });

  it("TASK-014 AC17: entering edit mode seeds draftPathSegments and fetches organization folders", async () => {
    global.fetch = makeFetchMock({
      detailsById: { p1: makeDetail({ id: "p1", proposedPathSegments: ["mythologie"] }) },
      organizationFoldersByDomain: { PERSONAL: [["mythologie", "livres"]] },
    });
    const user = userEvent.setup();
    renderDetailAtRoute("/validation/PERSONAL/p1");

    await screen.findByText("Contenu de test");
    await user.click(screen.getByRole("button", { name: /Éditer/ }));

    const foldersCall = await waitFor(() =>
      global.fetch.mock.calls.find(([url]) => new URL(url).pathname.endsWith("/organization-folders"))
    );
    expect(foldersCall).toBeDefined();
    expect(screen.getByRole("button", { name: /mythologie/ })).toBeInTheDocument();
  });

  it("TASK-014 AC17: Sauvegarder includes proposed_path_segments in field_updates alongside the existing three fields", async () => {
    global.fetch = makeFetchMock({
      detailsById: { p1: makeDetail({ id: "p1", proposedPathSegments: ["mythologie"] }) },
    });
    const user = userEvent.setup();
    renderDetailAtRoute("/validation/PERSONAL/p1");

    await screen.findByText("Contenu de test");
    await user.click(screen.getByRole("button", { name: /Éditer/ }));
    await screen.findByRole("button", { name: /mythologie/ });

    global.fetch.mockClear();
    await user.click(screen.getByRole("button", { name: /Sauvegarder/ }));

    const editCall = await waitFor(() =>
      global.fetch.mock.calls.find(([url]) => new URL(url).pathname.endsWith("/edit"))
    );
    expect(JSON.parse(editCall[1].body).field_updates.proposed_path_segments).toEqual(["mythologie"]);
  });

  it("TASK-012: hides the Éditer button for entity/event/relationship proposals", async () => {
    global.fetch = makeFetchMock({
      detailsById: { p1: makeDetail({ id: "p1", itemType: "entity", entityType: "person" }) },
    });
    renderDetailAtRoute("/validation/PERSONAL/p1");

    await screen.findByText("Contenu de test");
    expect(screen.queryByRole("button", { name: /Éditer/ })).not.toBeInTheDocument();
  });

  it("TASK-012 AC14: renders EntityTypeBadge/EventTemporalRange metadata rows for entity/event proposals", async () => {
    global.fetch = makeFetchMock({
      detailsById: { p1: makeDetail({ id: "p1", itemType: "event", startsAt: "2026-08-01T10:00:00", endsAt: null }) },
    });
    renderDetailAtRoute("/validation/PERSONAL/p1");

    await screen.findByText("Contenu de test");
    expect(screen.getByText("2026-08-01T10:00:00 → non précisé")).toBeInTheDocument();
  });

  it("TASK-012 AC15: an unresolvable relationship endpoint (404) renders as a plain id", async () => {
    global.fetch = makeFetchMock({
      detailsById: {
        p1: makeDetail({
          id: "p1", itemType: "relationship", relationshipType: "attended", endpoints: ["already-canonical-id"],
        }),
      },
    });
    renderDetailAtRoute("/validation/PERSONAL/p1");

    await screen.findByText("Contenu de test");
    expect(await screen.findByText("already-canonical-id")).toBeInTheDocument();
  });

  it("TASK-012 AC16: Précédent/Suivant queue navigates across all 4 proposal types", async () => {
    const queue = [
      { id: "p1", domain: "PERSONAL", proposal_status: "PROPOSED", proposed_item_type: "assertion", epistemic_status: "direct", created_at: "2026-08-25T01:00:00" },
      { id: "p2", domain: "PERSONAL", proposal_status: "PROPOSED", proposed_item_type: "entity", epistemic_status: "direct", created_at: "2026-08-25T02:00:00" },
      { id: "p3", domain: "PERSONAL", proposal_status: "PROPOSED", proposed_item_type: "event", epistemic_status: "direct", created_at: "2026-08-25T03:00:00" },
      { id: "p4", domain: "PERSONAL", proposal_status: "PROPOSED", proposed_item_type: "relationship", epistemic_status: "direct", created_at: "2026-08-25T04:00:00" },
    ];
    global.fetch = makeFetchMock({
      detailsById: {
        p1: makeDetail({ id: "p1", itemType: "assertion" }),
        p2: makeDetail({ id: "p2", itemType: "entity", entityType: "person" }),
        p3: makeDetail({ id: "p3", itemType: "event", startsAt: "2026-08-01T10:00:00" }),
        p4: makeDetail({ id: "p4", itemType: "relationship", relationshipType: "attended", endpoints: [] }),
      },
      proposalsByDomain: { PERSONAL: queue },
    });
    const user = userEvent.setup();
    renderDetailAtRoute("/validation/PERSONAL/p1");

    await screen.findByText("Contenu de test");
    await user.click(screen.getByRole("button", { name: /Suivant/ }));
    await waitFor(() => expect(document.querySelector(".proposal-id")).toHaveTextContent("p2"));
    await user.click(screen.getByRole("button", { name: /Suivant/ }));
    await waitFor(() => expect(document.querySelector(".proposal-id")).toHaveTextContent("p3"));
    await user.click(screen.getByRole("button", { name: /Suivant/ }));
    await waitFor(() => expect(document.querySelector(".proposal-id")).toHaveTextContent("p4"));
    expect(screen.getByRole("button", { name: /Suivant/ })).toBeDisabled();
  });

  it("TASK-012 AC17: a 409 UnresolvedRelationshipEndpointError on accept surfaces via the existing actionError banner", async () => {
    global.fetch = makeFetchMock({
      detailsById: {
        p1: makeDetail({ id: "p1", itemType: "relationship", relationshipType: "attended", endpoints: [] }),
      },
      acceptError: {
        status: 409,
        type: "UnresolvedRelationshipEndpointError",
        message: "Endpoint(s) ['prop-x'] are not yet ACCEPTED proposals",
      },
    });
    const user = userEvent.setup();
    renderDetailAtRoute("/validation/PERSONAL/p1");

    await screen.findByText("Contenu de test");
    await user.click(screen.getByRole("button", { name: /Accepter/ }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Endpoint(s) ['prop-x'] are not yet ACCEPTED proposals");
  });

  it("TASK-012 AC18: resolving a relationship's endpoints fetches each unique id only once even if repeated", async () => {
    global.fetch = makeFetchMock({
      detailsById: {
        p1: makeDetail({
          id: "p1", itemType: "relationship", relationshipType: "attended", endpoints: ["e1", "e1", "e2"],
        }),
        e1: makeDetail({ id: "e1", itemType: "entity", entityType: "person", body: "Entity One" }),
        e2: makeDetail({ id: "e2", itemType: "entity", entityType: "place", body: "Entity Two" }),
      },
    });
    renderDetailAtRoute("/validation/PERSONAL/p1");

    // endpoints repeats "e1" - two <li> entries render its resolved label,
    // but the underlying id must be fetched only once (this test's point).
    await screen.findAllByText(/entity: Entity One/);
    expect(screen.getAllByText(/entity: Entity One/)).toHaveLength(2);
    expect(screen.getByText(/entity: Entity Two/)).toBeInTheDocument();
    const e1Calls = global.fetch.mock.calls.filter(([url]) => new URL(url).pathname === "/domains/PERSONAL/proposals/e1");
    expect(e1Calls).toHaveLength(1);
  });
});

// AC11 (no file under src/ modified) is not a runtime assertion this suite
// can make - verified via `git status --porcelain -- src/` per the ticket's
// verification pass.
