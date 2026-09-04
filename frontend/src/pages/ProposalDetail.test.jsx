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
    },
    body,
    source_frontmatter: { original_filename: originalFilename, content_hash: contentHash, ingested_at: ingestedAt },
    source_body: sourceBody,
  };
}

// detailsById: { id: detail }; ingestionsByDomain: { DOMAIN: [taskState, ...] };
// proposalsByDomain: { DOMAIN: [summary, ...] } (PROPOSED/assertion queue).
function makeFetchMock({ detailsById = {}, ingestionsByDomain = {}, proposalsByDomain = {} } = {}) {
  return vi.fn((url, options = {}) => {
    const parsed = new URL(url);
    const path = parsed.pathname;
    const method = options.method || "GET";

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

    const detailMatch = path.match(/^\/domains\/([A-Z]+)\/proposals\/([^/]+)$/);
    if (detailMatch && method === "GET") {
      const detail = detailsById[detailMatch[2]];
      if (!detail) {
        return Promise.resolve(jsonResponse(404, { error: { type: "ProposalNotFoundError", message: "not found" } }));
      }
      return Promise.resolve(jsonResponse(200, detail));
    }

    const listMatch = path.match(/^\/domains\/([A-Z]+)\/proposals$/);
    if (listMatch && method === "GET") {
      const items = proposalsByDomain[listMatch[1]] || [];
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

  it("AC2: renders body read-only with no textarea, save button, or edit-toggle control", async () => {
    global.fetch = makeFetchMock({ detailsById: { p1: makeDetail({ body: "Le contenu complet de la note." }) } });
    renderDetailAtRoute("/validation/PERSONAL/p1");

    await screen.findByText("Le contenu complet de la note.");
    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
    expect(screen.queryByText(/Sauvegarder/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Éditer/)).not.toBeInTheDocument();
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
});

// AC11 (no file under src/ modified) is not a runtime assertion this suite
// can make - verified via `git status --porcelain -- src/` per the ticket's
// verification pass.
