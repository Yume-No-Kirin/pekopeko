import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import Settings from "./Settings.jsx";

function jsonResponse(status, body) {
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText: "",
    json: async () => body,
  };
}

const MOCK_CONFIG = {
  llm_provider: { active: "ollama" },
  default: { domain: "PERSONAL" },
  retrieval: { index_dir: "/home/user/.pekopeko/retrieval_index" },
  task_state: { dir: "/home/user/.pekopeko/task_state" },
};

describe("Settings", () => {
  beforeEach(() => {
    global.fetch = vi.fn(() => Promise.resolve(jsonResponse(200, MOCK_CONFIG)));
  });

  it("renders the 4 fields from a mocked GET /config response", async () => {
    render(<Settings />);

    expect(await screen.findByText("ollama")).toBeInTheDocument();
    expect(screen.getByText("PERSONAL")).toBeInTheDocument();
    expect(screen.getByText("/home/user/.pekopeko/retrieval_index")).toBeInTheDocument();
    expect(screen.getByText("/home/user/.pekopeko/task_state")).toBeInTheDocument();
  });

  it("contains no editable input, no form, and issues no write request", async () => {
    const { container } = render(<Settings />);
    await screen.findByText("ollama");

    expect(container.querySelector("input, textarea, select, form, button")).toBeNull();

    for (const call of global.fetch.mock.calls) {
      const options = call[1] || {};
      expect((options.method || "GET").toUpperCase()).toBe("GET");
    }
  });

  it("names the config file path and states editing is manual", async () => {
    render(<Settings />);
    await screen.findByText("ollama");

    expect(screen.getByText(/~\/.pekopeko\/config\.yaml/)).toBeInTheDocument();
    expect(screen.getByText(/~\/.pekopeko\/.env/)).toBeInTheDocument();
    expect(screen.getByText(/manuellement/)).toBeInTheDocument();
  });
});
