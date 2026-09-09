import { describe, it, expect, vi, beforeEach } from "vitest";
import { get, post, postForm, ApiError } from "./client.js";

describe("api client", () => {
  beforeEach(() => {
    global.fetch = vi.fn();
  });

  it("attaches the X-API-Key header on every outgoing request", async () => {
    global.fetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ ok: true }),
    });

    await get("/domains/PERSONAL/proposals");
    await post("/domains/PERSONAL/proposals/p1/accept", { reviewer_id: "cleo" });

    expect(global.fetch).toHaveBeenCalledTimes(2);
    for (const call of global.fetch.mock.calls) {
      const [, options] = call;
      expect(options.headers["X-API-Key"]).toBe("test-api-key");
    }
  });

  it("surfaces a non-2xx {error:{type,message}} envelope as a typed ApiError", async () => {
    global.fetch.mockResolvedValue({
      ok: false,
      status: 404,
      statusText: "Not Found",
      json: async () => ({
        error: { type: "ProposalNotFoundError", message: "Proposal 'x' not found" },
      }),
    });

    let caught;
    try {
      await get("/domains/PERSONAL/proposals/x");
    } catch (e) {
      caught = e;
    }

    expect(caught).toBeInstanceOf(ApiError);
    expect(caught).toMatchObject({
      name: "ApiError",
      type: "ProposalNotFoundError",
      message: "Proposal 'x' not found",
      status: 404,
    });
  });

  // TASK-009a: postForm - the first multipart request the frontend makes.

  it("postForm sends the FormData body with X-API-Key but no explicit Content-Type", async () => {
    global.fetch.mockResolvedValue({
      ok: true,
      status: 202,
      json: async () => ({ task_id: "ingest-1", status: "pending" }),
    });

    const formData = new FormData();
    formData.append("file", new File(["# Test"], "notes.md", { type: "text/markdown" }));

    const result = await postForm("/domains/PERSONAL/ingestions/upload", formData);

    expect(result).toEqual({ task_id: "ingest-1", status: "pending" });
    expect(global.fetch).toHaveBeenCalledTimes(1);
    const [, options] = global.fetch.mock.calls[0];
    expect(options.method).toBe("POST");
    expect(options.body).toBe(formData);
    expect(options.headers["X-API-Key"]).toBe("test-api-key");
    expect(options.headers["Content-Type"]).toBeUndefined();
  });

  it("postForm surfaces a non-2xx {error:{type,message}} envelope as a typed ApiError", async () => {
    global.fetch.mockResolvedValue({
      ok: false,
      status: 400,
      statusText: "Bad Request",
      json: async () => ({ error: { type: "ValueError", message: "Only .md files are supported" } }),
    });

    let caught;
    try {
      await postForm("/domains/PERSONAL/ingestions/upload", new FormData());
    } catch (e) {
      caught = e;
    }

    expect(caught).toBeInstanceOf(ApiError);
    expect(caught).toMatchObject({
      name: "ApiError",
      type: "ValueError",
      message: "Only .md files are supported",
      status: 400,
    });
  });
});
