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

function makeSummary({ id, domain = "PERSONAL", epistemicStatus = "direct", createdAt = "2026-08-25T10:00:00" }) {
  return {
    id,
    domain,
    proposal_status: "PROPOSED",
    proposed_item_type: "assertion",
    epistemic_status: epistemicStatus,
    created_at: createdAt,
  };
}

function makeDetail({ id, domain = "PERSONAL", sourceId, filename = "notes.md", body = "Contenu de test" }) {
  return {
    id,
    domain,
    frontmatter: { provenance: { source_id: sourceId, extraction_provider: "ollama" } },
    body,
    source_frontmatter: { original_filename: filename },
    source_body: "",
  };
}

// proposalsByDomain: { DOMAIN: [summary, ...] }; detailsById: { id: detail };
// ingestionsByDomain: { DOMAIN: [taskState, ...] }
function makeFetchMock({ proposalsByDomain = {}, detailsById = {}, ingestionsByDomain = {} } = {}) {
  return vi.fn((url, options = {}) => {
    const parsed = new URL(url);
    const path = parsed.pathname;
    const method = options.method || "GET";

    const proposalsListMatch = path.match(/^\/domains\/([A-Z]+)\/proposals$/);
    if (proposalsListMatch && method === "GET") {
      const items = proposalsByDomain[proposalsListMatch[1]] || [];
      return Promise.resolve(jsonResponse(200, { items, total: items.length, limit: 500, offset: 0 }));
    }

    const proposalDetailMatch = path.match(/^\/domains\/([A-Z]+)\/proposals\/([^/]+)$/);
    if (proposalDetailMatch && method === "GET") {
      const detail = detailsById[proposalDetailMatch[2]];
      if (!detail) {
        return Promise.resolve(jsonResponse(400, { error: { type: "ValidationError", message: "malformed" } }));
      }
      return Promise.resolve(jsonResponse(200, detail));
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

    expect(screen.getByText("Inféré")).toBeInTheDocument();
    expect(screen.getByText("Incertain")).toBeInTheDocument();
    expect(screen.getByText("Contesté")).toBeInTheDocument();
  });

  it("AC3: renders no folder-path column and no bulk-action button", async () => {
    global.fetch = makeFetchMock({
      proposalsByDomain: { PERSONAL: [makeSummary({ id: "p1" })] },
      detailsById: { p1: makeDetail({ id: "p1", sourceId: "src-a" }) },
    });

    renderValidation();
    await screen.findByText(/notes\.md/);

    expect(screen.queryByText(/Dossier proposé/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Tout accepter/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Tout rejeter/)).not.toBeInTheDocument();
    expect(screen.getAllByRole("columnheader")).toHaveLength(3);
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

  it("AC5: rejecting opens the shared reason modal; submitting calls POST reject with the entered reason", async () => {
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
      global.fetch.mock.calls.find(([url]) => new URL(url).pathname.endsWith("/reject"))
    );
    expect(JSON.parse(rejectCall[1].body)).toEqual({ reviewer_id: "test-reviewer", reason: "Pas assez fiable" });
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
      global.fetch.mock.calls.find(([url]) => new URL(url).pathname.endsWith("/reject"))
    );
    expect(JSON.parse(rejectCall[1].body)).toEqual({ reviewer_id: "test-reviewer", reason: null });
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
});

// AC9 (Dashboard "Validation" card is available and navigates to
// /validation) is covered in Dashboard.test.jsx, alongside the rest of that
// page's module-card assertions.
// AC11 (no file under src/ modified) is not a runtime assertion this suite
// can make - verified via `git status --porcelain -- src/` per the ticket's
// verification pass.
