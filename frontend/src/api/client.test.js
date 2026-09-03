import { describe, it, expect, vi, beforeEach } from "vitest";
import { get, post, ApiError } from "./client.js";

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
});
