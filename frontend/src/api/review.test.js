import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  listProposals,
  getProposal,
  acceptProposal,
  rejectProposal,
  editProposal,
  listOrganizationFolders,
} from "./review.js";

function jsonResponse(body) {
  return { ok: true, status: 200, json: async () => body };
}

describe("review api wrapper", () => {
  beforeEach(() => {
    global.fetch = vi.fn().mockResolvedValue(jsonResponse({}));
  });

  it("listProposals builds the URL with status/limit/offset and returns the envelope", async () => {
    const envelope = { items: [{ id: "p1" }], total: 1, limit: 500, offset: 0 };
    global.fetch.mockResolvedValue(jsonResponse(envelope));

    const result = await listProposals("PERSONAL", { status: "PROPOSED", limit: 500, offset: 0 });

    const [url] = global.fetch.mock.calls[0];
    const parsed = new URL(url);
    expect(parsed.pathname).toBe("/domains/PERSONAL/proposals");
    expect(parsed.searchParams.get("status")).toBe("PROPOSED");
    expect(parsed.searchParams.get("limit")).toBe("500");
    expect(parsed.searchParams.get("offset")).toBe("0");
    expect(result).toEqual(envelope);
  });

  it("getProposal fetches the detail endpoint", async () => {
    const detail = { id: "p1", domain: "PERSONAL", frontmatter: {}, body: "text", source_frontmatter: {}, source_body: "" };
    global.fetch.mockResolvedValue(jsonResponse(detail));

    const result = await getProposal("PERSONAL", "p1");

    const [url] = global.fetch.mock.calls[0];
    expect(new URL(url).pathname).toBe("/domains/PERSONAL/proposals/p1");
    expect(result).toEqual(detail);
  });

  it("acceptProposal posts reviewer_id to the accept endpoint", async () => {
    await acceptProposal("PERSONAL", "p1", "cleo");

    const [url, options] = global.fetch.mock.calls[0];
    expect(new URL(url).pathname).toBe("/domains/PERSONAL/proposals/p1/accept");
    expect(JSON.parse(options.body)).toEqual({ reviewer_id: "cleo" });
  });

  it("rejectProposal posts reviewer_id and reason (or null) to the reject endpoint", async () => {
    await rejectProposal("PERSONAL", "p1", "cleo", "not accurate");

    const [url, options] = global.fetch.mock.calls[0];
    expect(new URL(url).pathname).toBe("/domains/PERSONAL/proposals/p1/reject");
    expect(JSON.parse(options.body)).toEqual({ reviewer_id: "cleo", reason: "not accurate" });
  });

  it("rejectProposal sends reason: null when no reason is given", async () => {
    await rejectProposal("PERSONAL", "p1", "cleo", "");

    const [, options] = global.fetch.mock.calls[0];
    expect(JSON.parse(options.body)).toEqual({ reviewer_id: "cleo", reason: null });
  });

  it("editProposal posts reviewer_id, body, and field_updates to the edit endpoint", async () => {
    await editProposal("PERSONAL", "p1", "cleo", {
      body: "New text",
      fieldUpdates: { epistemic_status: "inferred", valid_from: "2026-09-01T00:00:00", valid_until: null },
    });

    const [url, options] = global.fetch.mock.calls[0];
    expect(new URL(url).pathname).toBe("/domains/PERSONAL/proposals/p1/edit");
    expect(JSON.parse(options.body)).toEqual({
      reviewer_id: "cleo",
      body: "New text",
      field_updates: { epistemic_status: "inferred", valid_from: "2026-09-01T00:00:00", valid_until: null },
    });
  });

  it("editProposal sends body: null and field_updates: null when neither is given", async () => {
    await editProposal("PERSONAL", "p1", "cleo");

    const [, options] = global.fetch.mock.calls[0];
    expect(JSON.parse(options.body)).toEqual({ reviewer_id: "cleo", body: null, field_updates: null });
  });

  it("TASK-014 AC13: listOrganizationFolders GETs the organization-folders endpoint with item_type", async () => {
    const envelope = { segments_by_depth: [["mythologie", "livres"], ["japonaise"]] };
    global.fetch.mockResolvedValue(jsonResponse(envelope));

    const result = await listOrganizationFolders("PERSONAL", "assertion");

    const [url] = global.fetch.mock.calls[0];
    const parsed = new URL(url);
    expect(parsed.pathname).toBe("/domains/PERSONAL/organization-folders");
    expect(parsed.searchParams.get("item_type")).toBe("assertion");
    expect(result).toEqual(envelope);
  });
});
