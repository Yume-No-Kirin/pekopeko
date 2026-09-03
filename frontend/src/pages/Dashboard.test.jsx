import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Routes, Route, useNavigate } from "react-router-dom";
import Dashboard from "./Dashboard.jsx";
import Settings from "./Settings.jsx";

function jsonResponse(status, body) {
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText: "",
    json: async () => body,
  };
}

function makeFetchMock({ ingestionsByDomain = {}, proposalsByDomain = {}, detailsById = {}, config = {} } = {}) {
  return vi.fn((url) => {
    const parsed = new URL(url);
    const path = parsed.pathname;
    const params = parsed.searchParams;

    const ingestionMatch = path.match(/^\/domains\/([A-Z]+)\/ingestions$/);
    if (ingestionMatch) {
      const domain = ingestionMatch[1];
      const status = params.get("status");
      const total = (ingestionsByDomain[domain] && ingestionsByDomain[domain][status]) || 0;
      return Promise.resolve(jsonResponse(200, { items: [], total, limit: 50, offset: 0 }));
    }

    const proposalsListMatch = path.match(/^\/domains\/([A-Z]+)\/proposals$/);
    if (proposalsListMatch) {
      const domain = proposalsListMatch[1];
      const status = params.get("status");
      const page = (proposalsByDomain[domain] && proposalsByDomain[domain][status]) || {
        items: [],
        total: 0,
      };
      return Promise.resolve(
        jsonResponse(200, { items: page.items, total: page.total, limit: 50, offset: 0 })
      );
    }

    const proposalDetailMatch = path.match(/^\/domains\/([A-Z]+)\/proposals\/([^/]+)$/);
    if (proposalDetailMatch) {
      const id = proposalDetailMatch[2];
      return Promise.resolve(
        jsonResponse(
          200,
          detailsById[id] || {
            id,
            domain: proposalDetailMatch[1],
            frontmatter: {},
            body: "",
            source_frontmatter: {},
            source_body: "",
          }
        )
      );
    }

    if (path === "/config") {
      return Promise.resolve(jsonResponse(200, config));
    }

    return Promise.resolve(jsonResponse(404, { error: { type: "NotFound", message: "unhandled in test" } }));
  });
}

function daysAgoIso(days) {
  return new Date(Date.now() - days * 24 * 60 * 60 * 1000).toISOString();
}

// Test-only harness: MemoryRouter's own history stack has no public "go back"
// handle, so this button drives real browser-back-equivalent navigation via
// useNavigate(-1) instead of the data-router APIs (which crash on jsdom's
// undici/AbortSignal realm mismatch).
function BackButton() {
  const navigate = useNavigate();
  return (
    <button type="button" onClick={() => navigate(-1)}>
      Back (test only)
    </button>
  );
}

function renderRoutedDashboard() {
  return render(
    <MemoryRouter initialEntries={["/"]}>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </MemoryRouter>
  );
}

describe("Dashboard", () => {
  beforeEach(() => {
    global.fetch = makeFetchMock();
  });

  it("navigates to Settings via the module card and back to Dashboard via browser back", async () => {
    global.fetch = makeFetchMock({
      config: {
        llm_provider: { active: "ollama" },
        default: { domain: "PERSONAL" },
        retrieval: { index_dir: "/idx" },
        task_state: { dir: "/state" },
      },
    });
    const user = userEvent.setup();
    render(
      <MemoryRouter initialEntries={["/"]}>
        <BackButton />
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </MemoryRouter>
    );

    expect(await screen.findByRole("heading", { name: "Dashboard" })).toBeInTheDocument();

    await user.click(screen.getByRole("link", { name: /Settings/ }));
    expect(await screen.findByRole("heading", { name: "Settings" })).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /Back/ }));
    expect(await screen.findByRole("heading", { name: "Dashboard" })).toBeInTheDocument();
  });

  it("sums 'Ingestions en cours' (pending+running) across all 5 domains", async () => {
    global.fetch = makeFetchMock({
      ingestionsByDomain: {
        PERSONAL: { pending: 1, running: 2 },
        FICTION: { pending: 3, running: 0 },
        LEARNING: { pending: 0, running: 1 },
        RESEARCH: { pending: 2, running: 2 },
        PUBLISHING: { pending: 0, running: 0 },
      },
    });
    renderRoutedDashboard();

    const value = await screen.findByText("11");
    expect(value.closest(".stat-card")).toHaveTextContent("Ingestions en cours");
  });

  it("sums 'Propositions en attente' across all 5 domains", async () => {
    global.fetch = makeFetchMock({
      proposalsByDomain: {
        PERSONAL: { PROPOSED: { items: [], total: 4 } },
        FICTION: { PROPOSED: { items: [], total: 1 } },
        LEARNING: { PROPOSED: { items: [], total: 0 } },
        RESEARCH: { PROPOSED: { items: [], total: 2 } },
        PUBLISHING: { PROPOSED: { items: [], total: 3 } },
      },
    });
    renderRoutedDashboard();

    const value = await screen.findByText("10");
    expect(value.closest(".stat-card")).toHaveTextContent("Propositions en attente");
  });

  it("sums 'Connaissances canoniques' (ACCEPTED totals) across all 5 domains", async () => {
    global.fetch = makeFetchMock({
      proposalsByDomain: {
        PERSONAL: { ACCEPTED: { items: [], total: 5 } },
        FICTION: { ACCEPTED: { items: [], total: 0 } },
        LEARNING: { ACCEPTED: { items: [], total: 7 } },
        RESEARCH: { ACCEPTED: { items: [], total: 0 } },
        PUBLISHING: { ACCEPTED: { items: [], total: 1 } },
      },
    });
    renderRoutedDashboard();

    const value = await screen.findByText("13");
    expect(value.closest(".stat-card")).toHaveTextContent("Connaissances canoniques");
  });

  it("computes 'Taux d'acceptation' from reviewed_at within the last 30 days only", async () => {
    global.fetch = makeFetchMock({
      proposalsByDomain: {
        PERSONAL: {
          ACCEPTED: { items: [{ id: "p1" }, { id: "p2" }], total: 2 },
          REJECTED: { items: [{ id: "r1" }], total: 1 },
        },
      },
      detailsById: {
        p1: { id: "p1", frontmatter: { reviewed_at: daysAgoIso(10) } },
        p2: { id: "p2", frontmatter: { reviewed_at: daysAgoIso(40) } },
        r1: { id: "r1", frontmatter: { reviewed_at: daysAgoIso(5) } },
      },
    });
    renderRoutedDashboard();

    // p1 (10d, recent) + r1 (5d, recent) count; p2 (40d) is excluded -> 1/(1+1) = 50%
    const value = await screen.findByText("50%");
    expect(value.closest(".stat-card")).toHaveTextContent("Taux d'acceptation");
  });

  it("renders '—' for the acceptance rate when there are no reviewed proposals in range", async () => {
    global.fetch = makeFetchMock();
    renderRoutedDashboard();

    const value = await screen.findByText("—");
    expect(value.closest(".stat-card")).toHaveTextContent("Taux d'acceptation");
  });

  it("renders Validation and Ingestion Logs as coming-soon and non-navigable, Settings as available", async () => {
    global.fetch = makeFetchMock();
    renderRoutedDashboard();
    await screen.findByRole("heading", { name: "Dashboard" });

    const validationCard = screen.getByText("Validation").closest(".module-card");
    expect(validationCard).toHaveClass("disabled");
    expect(validationCard.tagName).not.toBe("A");

    const ingestionLogsCard = screen.getByText("Logs d'ingestion").closest(".module-card");
    expect(ingestionLogsCard).toHaveClass("disabled");
    expect(ingestionLogsCard.tagName).not.toBe("A");

    const settingsCard = screen.getByText("Settings", { selector: ".module-title" }).closest(
      ".module-card"
    );
    expect(settingsCard).not.toHaveClass("disabled");
    expect(settingsCard).toHaveAttribute("href", "/settings");
  });

  it("shows a loading state while requests are in flight, then an error state on failure", async () => {
    let rejectFirstCall;
    global.fetch = vi.fn(() => {
      if (!rejectFirstCall) {
        rejectFirstCall = true;
        return Promise.resolve(
          jsonResponse(401, { error: { type: "Unauthorized", message: "Missing or invalid X-API-Key header" } })
        );
      }
      return Promise.resolve(jsonResponse(200, { items: [], total: 0, limit: 50, offset: 0 }));
    });

    renderRoutedDashboard();

    expect(screen.getByText(/Chargement des statistiques/)).toBeInTheDocument();

    expect(await screen.findByRole("alert")).toHaveTextContent("Missing or invalid X-API-Key header");
  });
});
