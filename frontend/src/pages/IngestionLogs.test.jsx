import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, within, act, waitFor, fireEvent } from "@testing-library/react";
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
//
// TASK-009a additions: contextsByDomain ({ DOMAIN: [contexts] }) backs the
// modal's autocompletion fetch; uploadResult backs POST .../ingestions/upload;
// ingestionStatusSequence backs the single-task GET .../ingestions/<taskId>
// polled by IngestionLogs itself - one entry consumed per call, the last
// entry repeats once exhausted (so a one-element array behaves as "always
// this status").
function makeFetchMock({
  ingestionsByDomain = {},
  extractionsByDomain = {},
  contextsByDomain = {},
  uploadResult = { task_id: "ingest-new", status: "pending" },
  ingestionStatusSequence = [{ status: "completed", proposal_ids: [] }],
} = {}) {
  let singleIngestionCallCount = 0;
  return vi.fn((url, options = {}) => {
    const parsed = new URL(url);
    const path = parsed.pathname;
    const method = options.method || "GET";
    const offset = Number(parsed.searchParams.get("offset") || 0);
    const limit = Number(parsed.searchParams.get("limit") || 10);

    if (method === "POST" && /\/ingestions\/upload$/.test(path)) {
      return Promise.resolve(jsonResponse(202, uploadResult));
    }

    if (method === "POST" && /\/proposals\/[^/]+\/edit$/.test(path)) {
      return Promise.resolve(jsonResponse(200, { proposal_id: path.split("/").at(-2), edited_by: "cleo" }));
    }

    const contextsMatch = path.match(/^\/domains\/([A-Z]+)\/contexts$/);
    if (contextsMatch) {
      return Promise.resolve(jsonResponse(200, { contexts: contextsByDomain[contextsMatch[1]] || [] }));
    }

    const singleIngestionMatch = path.match(/^\/domains\/([A-Z]+)\/ingestions\/([^/]+)$/);
    if (method === "GET" && singleIngestionMatch) {
      const idx = Math.min(singleIngestionCallCount, ingestionStatusSequence.length - 1);
      singleIngestionCallCount += 1;
      return Promise.resolve(jsonResponse(200, ingestionStatusSequence[idx]));
    }

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

async function openModalAndFillFile(user, { context } = {}) {
  await user.click(screen.getByRole("button", { name: "+ Nouvelle ingestion" }));
  const file = new File(["# Test\n\nContent."], "notes.md", { type: "text/markdown" });
  await user.upload(screen.getByLabelText(/Fichier/), file);
  if (context) {
    await user.type(screen.getByLabelText(/Contexte/), context);
  }
}

// Under fake timers, screen.findByRole/waitFor's own internal setTimeout-based
// polling never fires unless the fake clock is advanced - rather than
// interleave timer advancement with those async queries (fragile), the
// AC13-15 tests below flush pending microtasks explicitly and then assert
// with synchronous get*/query* calls.
async function flushMicrotasks() {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(0);
  });
}

// @testing-library/user-event's realistic interaction machinery hangs
// indefinitely under vi.useFakeTimers() even with delay:null/advanceTimers
// set (its internal pointer-event sequencing never resolves) - the AC13-15
// tests below drive the same interactions with the lower-level, synchronous
// fireEvent instead, wrapped in flushMicrotasks() so React's own effects and
// the mocked fetch promises still get to resolve between steps.
async function openModalAndFillFileSync({ context } = {}) {
  fireEvent.click(screen.getByRole("button", { name: "+ Nouvelle ingestion" }));
  await flushMicrotasks();
  const file = new File(["# Test\n\nContent."], "notes.md", { type: "text/markdown" });
  fireEvent.change(screen.getByLabelText(/Fichier/), { target: { files: [file] } });
  if (context) {
    fireEvent.change(screen.getByLabelText(/Contexte/), { target: { value: context } });
  }
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

  // TASK-009a: "+ Nouvelle ingestion" button, modal wiring, and post-completion
  // context application via polling.

  it("AC12: successful submit with no context closes the modal and refreshes the list", async () => {
    global.fetch = makeFetchMock({ ingestionsByDomain: { PERSONAL: { items: [], total: 0 } } });
    const user = userEvent.setup();
    render(<IngestionLogs />);
    await screen.findByRole("table");

    await openModalAndFillFile(user);
    expect(screen.getByText("Nouvelle ingestion")).toBeInTheDocument();

    global.fetch.mockClear();
    await user.click(screen.getByRole("button", { name: /Démarrer l'ingestion/ }));

    await waitFor(() => expect(screen.queryByText("Nouvelle ingestion")).not.toBeInTheDocument());
    expect(
      global.fetch.mock.calls.some(([url]) => new URL(url).pathname === "/domains/PERSONAL/ingestions")
    ).toBe(true);
    // No context typed - no polling call for the new task should follow.
    expect(
      global.fetch.mock.calls.some(([url]) => new URL(url).pathname === "/domains/PERSONAL/ingestions/ingest-new")
    ).toBe(false);
  });

  it("AC13: submitting with a context polls until completed, then edits every resulting proposal with that context", async () => {
    vi.useFakeTimers();
    global.fetch = makeFetchMock({
      ingestionsByDomain: { PERSONAL: { items: [], total: 0 } },
      uploadResult: { task_id: "ingest-ctx", status: "pending" },
      ingestionStatusSequence: [{ status: "running" }, { status: "completed", proposal_ids: ["p1", "p2"] }],
    });

    render(<IngestionLogs />);
    await flushMicrotasks();
    await openModalAndFillFileSync({ context: "Mythologie japonaise" });

    global.fetch.mockClear();
    fireEvent.click(screen.getByRole("button", { name: /Démarrer l'ingestion/ }));
    await flushMicrotasks(); // handleSubmit resolves -> onSuccess -> 1st poll (running) -> setTimeout(2000) scheduled

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2000); // 2nd poll: completed -> fans out edits
    });

    const editCalls = global.fetch.mock.calls.filter(([url]) => new URL(url).pathname.endsWith("/edit"));
    expect(editCalls).toHaveLength(2);
    const editPaths = editCalls.map(([url]) => new URL(url).pathname).sort();
    expect(editPaths).toEqual(["/domains/PERSONAL/proposals/p1/edit", "/domains/PERSONAL/proposals/p2/edit"]);
    for (const [, options] of editCalls) {
      expect(JSON.parse(options.body).field_updates).toEqual({ context: "Mythologie japonaise" });
    }

    vi.useRealTimers();
  });

  it("AC14: gives up silently after the attempt cap if the task never reaches a terminal status", async () => {
    vi.useFakeTimers();
    global.fetch = makeFetchMock({
      ingestionsByDomain: { PERSONAL: { items: [], total: 0 } },
      uploadResult: { task_id: "ingest-stuck", status: "pending" },
      ingestionStatusSequence: [{ status: "running" }],
    });

    render(<IngestionLogs />);
    await flushMicrotasks();
    await openModalAndFillFileSync({ context: "Mythologie japonaise" });

    fireEvent.click(screen.getByRole("button", { name: /Démarrer l'ingestion/ }));
    await flushMicrotasks();
    await act(async () => {
      await vi.advanceTimersByTimeAsync(2000 * 65); // past the 60-attempt cap
    });

    const pollCalls = global.fetch.mock.calls.filter(
      ([url]) => new URL(url).pathname === "/domains/PERSONAL/ingestions/ingest-stuck"
    );
    expect(pollCalls).toHaveLength(60);
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();

    vi.useRealTimers();
  });

  it("AC15: unmounting mid-poll stops further getIngestion calls", async () => {
    vi.useFakeTimers();
    global.fetch = makeFetchMock({
      ingestionsByDomain: { PERSONAL: { items: [], total: 0 } },
      uploadResult: { task_id: "ingest-unmount", status: "pending" },
      ingestionStatusSequence: [{ status: "running" }],
    });

    const { unmount } = render(<IngestionLogs />);
    await flushMicrotasks();
    await openModalAndFillFileSync({ context: "Mythologie japonaise" });
    fireEvent.click(screen.getByRole("button", { name: /Démarrer l'ingestion/ }));
    await flushMicrotasks();

    const pollPath = "/domains/PERSONAL/ingestions/ingest-unmount";
    const callsBeforeUnmount = global.fetch.mock.calls.filter(([url]) => new URL(url).pathname === pollPath).length;
    expect(callsBeforeUnmount).toBeGreaterThanOrEqual(1);

    unmount();
    await act(async () => {
      await vi.advanceTimersByTimeAsync(2000 * 5);
    });

    const callsAfterUnmount = global.fetch.mock.calls.filter(([url]) => new URL(url).pathname === pollPath).length;
    expect(callsAfterUnmount).toBe(callsBeforeUnmount);

    vi.useRealTimers();
  });
});

// AC8 (Dashboard "Logs d'ingestion" card is available and navigates to
// /ingestion-logs) is covered in Dashboard.test.jsx, alongside the rest of
// that page's module-card assertions.
// AC10 (no file under src/ modified) is not a runtime assertion this suite
// can make - verified via `git status --porcelain -- src/` per the ticket's
// verification pass.
