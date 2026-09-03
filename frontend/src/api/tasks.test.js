import { describe, it, expect, vi, beforeEach } from "vitest";
import { listIngestions, listExtractions } from "./tasks.js";

function jsonResponse(body) {
  return { ok: true, status: 200, json: async () => body };
}

describe("tasks api wrapper", () => {
  beforeEach(() => {
    global.fetch = vi.fn().mockResolvedValue(jsonResponse({ items: [], total: 0, limit: 10, offset: 0 }));
  });

  it("listIngestions builds the URL with status/limit/offset and returns the envelope", async () => {
    const envelope = { items: [{ task_id: "ingest-1" }], total: 1, limit: 10, offset: 0 };
    global.fetch.mockResolvedValue(jsonResponse(envelope));

    const result = await listIngestions("PERSONAL", { status: "failed", limit: 10, offset: 20 });

    const [url] = global.fetch.mock.calls[0];
    const parsed = new URL(url);
    expect(parsed.pathname).toBe("/domains/PERSONAL/ingestions");
    expect(parsed.searchParams.get("status")).toBe("failed");
    expect(parsed.searchParams.get("limit")).toBe("10");
    expect(parsed.searchParams.get("offset")).toBe("20");
    expect(result).toEqual(envelope);
  });

  it("listExtractions builds the URL with status/limit/offset and returns the envelope", async () => {
    const envelope = { items: [{ task_id: "extract-1" }], total: 1, limit: 10, offset: 0 };
    global.fetch.mockResolvedValue(jsonResponse(envelope));

    const result = await listExtractions("FICTION", { status: "completed", limit: 10, offset: 0 });

    const [url] = global.fetch.mock.calls[0];
    const parsed = new URL(url);
    expect(parsed.pathname).toBe("/domains/FICTION/extractions");
    expect(parsed.searchParams.get("status")).toBe("completed");
    expect(parsed.searchParams.get("limit")).toBe("10");
    expect(parsed.searchParams.get("offset")).toBe("0");
    expect(result).toEqual(envelope);
  });

  it("omits status/limit/offset from the query string when not given", async () => {
    await listIngestions("PERSONAL");

    const [url] = global.fetch.mock.calls[0];
    const parsed = new URL(url);
    expect(parsed.pathname).toBe("/domains/PERSONAL/ingestions");
    expect(parsed.search).toBe("");
  });
});
