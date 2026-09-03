import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import IngestionLogs from "./IngestionLogs.jsx";

function jsonResponse(status, body) {
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText: "",
    json: async () => body,
  };
}

function makeTask(overrides = {}) {
  return {
    task_id: "ingest-1",
    source_path: "notes-lecture.md",
    domain: "PERSONAL",
    status: "completed",
    started_at: "2026-08-25T10:00:00",
    completed_at: "2026-08-25T10:05:00",
    error: null,
    source_id: "src-abc123",
    proposal_ids: ["p1", "p2"],
    events: [{ timestamp: "2026-08-25T10:00:00", level: "info", message: "Ingestion task started", details: null }],
    ...overrides,
  };
}

// ingestionsByDomain/extractionsByDomain: { DOMAIN: { items, total } }
// Slices by offset/limit like the real paginated endpoints do, so tests
// that page past a single fixture's length exercise realistic (possibly
// empty) subsequent pages instead of the same items coming back twice.
function makeFetchMock({ ingestionsByDomain = {}, extractionsByDomain = {} } = {}) {
  return vi.fn((url) => {
    const parsed = new URL(url);
    const path = parsed.pathname;
    const offset = Number(parsed.searchParams.get("offset") || 0);
    const limit = Number(parsed.searchParams.get("limit") || 10);

    const ingestMatch = path.match(/^\/domains\/([A-Z]+)\/ingestions$/);
    if (ingestMatch) {
      const page = ingestionsByDomain[ingestMatch[1]] || { items: [], total: 0 };
      return Promise.resolve(
        jsonResponse(200, { items: page.items.slice(offset, offset + limit), total: page.total, limit, offset })
      );
    }

    const extractMatch = path.match(/^\/domains\/([A-Z]+)\/extractions$/);
    if (extractMatch) {
      const page = extractionsByDomain[extractMatch[1]] || { items: [], total: 0 };
      return Promise.resolve(
        jsonResponse(200, { items: page.items.slice(offset, offset + limit), total: page.total, limit, offset })
      );
    }

    return Promise.resolve(jsonResponse(404, { error: { type: "NotFound", message: "unhandled in test" } }));
  });
}

describe("IngestionLogs", () => {
  beforeEach(() => {
    global.fetch = makeFetchMock();
  });

  it("AC1: renders merged ingestion + extraction rows across domains, each tagged with its type", async () => {
    global.fetch = makeFetchMock({
      ingestionsByDomain: {
        PERSONAL: { items: [makeTask({ task_id: "ingest-1", domain: "PERSONAL" })], total: 1 },
      },
      extractionsByDomain: {
        FICTION: { items: [makeTask({ task_id: "extract-1", domain: "FICTION", source_path: "roman.md" })], total: 1 },
      },
    });

    render(<IngestionLogs />);

    const ingestRow = (await screen.findByText("notes-lecture.md")).closest("tr");
    expect(within(ingestRow).getByText("ingestion")).toBeInTheDocument();
    expect(within(ingestRow).getByText("PERSONAL")).toBeInTheDocument();

    const extractRow = screen.getByText("roman.md").closest("tr");
    expect(within(extractRow).getByText("extraction")).toBeInTheDocument();
    expect(within(extractRow).getByText("FICTION")).toBeInTheDocument();
  });

  it("AC2: Status filter re-scopes the fetch, Period filter narrows the already-fetched rows client-side", async () => {
    global.fetch = makeFetchMock({
      ingestionsByDomain: {
        PERSONAL: {
          items: [
            makeTask({ task_id: "ingest-old", started_at: "2020-01-01T00:00:00", source_path: "vieux.md" }),
          ],
          total: 1,
        },
      },
    });

    const user = userEvent.setup();
    render(<IngestionLogs />);
    await screen.findByText("vieux.md");

    await user.selectOptions(screen.getByLabelText("Statut"), "failed");
    expect(global.fetch.mock.calls.some(([url]) => new URL(url).searchParams.get("status") === "failed")).toBe(true);

    await user.selectOptions(screen.getByLabelText("Statut"), "all");
    await screen.findByText("vieux.md");
    await user.selectOptions(screen.getByLabelText("Période"), "today");

    expect(screen.queryByText("vieux.md")).not.toBeInTheDocument();
  });

  it("AC3: a failed row's expanded detail shows both its error string and its full events sequence", async () => {
    global.fetch = makeFetchMock({
      ingestionsByDomain: {
        PERSONAL: {
          items: [
            makeTask({
              task_id: "ingest-failed",
              status: "failed",
              error: "Provider timeout",
              events: [
                { timestamp: "2026-08-25T10:00:00", level: "info", message: "Ingestion task started", details: null },
                { timestamp: "2026-08-25T10:00:05", level: "warning", message: "Provider extraction call failed", details: { error: "timeout" } },
              ],
            }),
          ],
          total: 1,
        },
      },
    });

    const user = userEvent.setup();
    render(<IngestionLogs />);

    const link = await screen.findByRole("link", { name: "Voir erreur" });
    await user.click(link);

    expect(screen.getByText(/Provider timeout/)).toBeInTheDocument();
    expect(screen.getByText("Ingestion task started")).toBeInTheDocument();
    expect(screen.getByText("Provider extraction call failed")).toBeInTheDocument();
  });

  it("AC4: a skipped_duplicate row's expanded detail surfaces the original source_id via its events entry", async () => {
    global.fetch = makeFetchMock({
      ingestionsByDomain: {
        PERSONAL: {
          items: [
            makeTask({
              task_id: "ingest-dup",
              status: "skipped_duplicate",
              events: [
                {
                  timestamp: "2026-08-25T10:00:00",
                  level: "info",
                  message: "Duplicate source detected, skipping ingestion",
                  details: { source_id: "src-original999" },
                },
              ],
            }),
          ],
          total: 1,
        },
      },
    });

    const user = userEvent.setup();
    render(<IngestionLogs />);

    const link = await screen.findByRole("link", { name: "Voir original" });
    await user.click(link);

    expect(screen.getByText(/src-original999/)).toBeInTheDocument();
  });

  it("AC5: pagination controls request the next page via limit/offset, and the count matches the merged total", async () => {
    const items = Array.from({ length: 10 }, (_, i) =>
      makeTask({ task_id: `ingest-${i}`, source_path: `note-${i}.md`, started_at: `2026-08-2${9 - (i % 9)}T10:00:00` })
    );
    global.fetch = makeFetchMock({
      ingestionsByDomain: { PERSONAL: { items, total: 25 } },
    });

    const user = userEvent.setup();
    render(<IngestionLogs />);

    expect(await screen.findByText("Affichage 1-10 sur 25")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Précédent/ })).toBeDisabled();

    global.fetch.mockClear();
    await user.click(screen.getByRole("button", { name: /Suivant/ }));

    expect(
      global.fetch.mock.calls.some(([url]) => new URL(url).searchParams.get("offset") === "10")
    ).toBe(true);
    expect(await screen.findByText("Affichage 11-20 sur 25")).toBeInTheDocument();
  });

  it("regression: paging never drops items that lost the merge on an earlier page (bug found in code review)", async () => {
    // FICTION has 12 items (f0 newest .. f11 oldest, one per hour from 12:00
    // down to 01:00); PERSONAL has 3 items slotted between FICTION's 7th and
    // 8th item (05:57-05:59, i.e. between f6's 06:00 and f7's 05:00). The
    // global top 10 is therefore f0-f6 + all 3 PERSONAL items - f7/f8/f9
    // (FICTION's own items ranked 8th-10th within its first fetched batch)
    // narrowly lose the page-0 merge. A naive "offset = page * PAGE_SIZE for
    // every source" re-fetch would ask FICTION for its items[10:20] on page
    // 1 and never see f7/f8/f9 again.
    const fictionItems = Array.from({ length: 12 }, (_, i) =>
      makeTask({
        task_id: `fiction-${i}`,
        domain: "FICTION",
        source_path: `f${i}.md`,
        started_at: `2026-08-25T${String(12 - i).padStart(2, "0")}:00:00`,
      })
    );
    const personalItems = Array.from({ length: 3 }, (_, i) =>
      makeTask({
        task_id: `personal-${i}`,
        domain: "PERSONAL",
        source_path: `p${i}.md`,
        started_at: `2026-08-25T05:5${9 - i}:00`,
      })
    );
    global.fetch = makeFetchMock({
      ingestionsByDomain: {
        FICTION: { items: fictionItems, total: 12 },
        PERSONAL: { items: personalItems, total: 3 },
      },
    });

    const user = userEvent.setup();
    render(<IngestionLogs />);

    expect(await screen.findByText("f0.md")).toBeInTheDocument();
    expect(screen.getByText("p0.md")).toBeInTheDocument();
    expect(screen.queryByText("f7.md")).not.toBeInTheDocument();
    expect(screen.queryByText("f8.md")).not.toBeInTheDocument();
    expect(screen.queryByText("f9.md")).not.toBeInTheDocument();
    expect(screen.getByText("Affichage 1-10 sur 15")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /Suivant/ }));

    expect(await screen.findByText("f7.md")).toBeInTheDocument();
    expect(screen.getByText("f8.md")).toBeInTheDocument();
    expect(screen.getByText("f9.md")).toBeInTheDocument();
    expect(screen.getByText("f10.md")).toBeInTheDocument();
    expect(screen.getByText("f11.md")).toBeInTheDocument();
    expect(screen.getByText("Affichage 11-15 sur 15")).toBeInTheDocument();
  });

  it("AC6: selecting a single domain issues fewer domain calls than 'tous les domaines'", async () => {
    global.fetch = makeFetchMock();
    const user = userEvent.setup();
    render(<IngestionLogs />);
    await screen.findByRole("table");

    global.fetch.mockClear();
    await user.selectOptions(screen.getByLabelText("Domaine"), "PERSONAL");

    const domainsQueried = new Set(
      global.fetch.mock.calls.map(([url]) => new URL(url).pathname.split("/")[2])
    );
    expect(domainsQueried.size).toBe(1);
    expect(domainsQueried.has("PERSONAL")).toBe(true);
  });

  it("AC7: every outgoing request carries X-API-Key", async () => {
    global.fetch = makeFetchMock({
      ingestionsByDomain: { PERSONAL: { items: [makeTask()], total: 1 } },
    });
    render(<IngestionLogs />);
    await screen.findByText("notes-lecture.md");

    expect(global.fetch.mock.calls.length).toBeGreaterThan(0);
    for (const [, options] of global.fetch.mock.calls) {
      expect(options.headers["X-API-Key"]).toBe("test-api-key");
    }
  });

  it("AC9: shows a loading state while requests are in flight, then an error state on failure", async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve(
        jsonResponse(401, { error: { type: "Unauthorized", message: "Missing or invalid X-API-Key header" } })
      )
    );

    render(<IngestionLogs />);
    expect(screen.getByText(/Chargement des tâches/)).toBeInTheDocument();

    expect(await screen.findByRole("alert")).toHaveTextContent("Missing or invalid X-API-Key header");
  });
});

// AC8 (Dashboard "Logs d'ingestion" card is available and navigates to
// /ingestion-logs) is covered in Dashboard.test.jsx, alongside the rest of
// that page's module-card assertions.
// AC10 (no file under src/ modified) is not a runtime assertion this suite
// can make - verified via `git status --porcelain -- src/` per the ticket's
// verification pass.
