import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import NewIngestionModal from "./NewIngestionModal.jsx";
import { startIngestionUpload } from "../api/tasks.js";
import { listContexts } from "../api/review.js";

vi.mock("../api/tasks.js", () => ({
  startIngestionUpload: vi.fn(),
}));
vi.mock("../api/review.js", () => ({
  listContexts: vi.fn(),
}));

function makeFile(name, content = "# Test") {
  return new File([content], name, { type: "text/markdown" });
}

describe("NewIngestionModal", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    listContexts.mockResolvedValue({ contexts: [] });
  });

  it("AC10: submit is disabled with no file selected", () => {
    render(<NewIngestionModal open={true} onCancel={() => {}} onSuccess={() => {}} />);

    expect(screen.getByRole("button", { name: /Démarrer l'ingestion/ })).toBeDisabled();
  });

  it("AC10: selecting a non-.md file shows an inline error and does not call startIngestionUpload", () => {
    // fireEvent.change (not userEvent.upload) - user-event v14 itself filters
    // a selection against the input's accept=".md" attribute, so it can never
    // deliver a non-matching file the way a real OS file picker override
    // could; this test exercises this component's own defense-in-depth
    // check, independent of the browser-level accept filter.
    render(<NewIngestionModal open={true} onCancel={() => {}} onSuccess={() => {}} />);

    fireEvent.change(screen.getByLabelText(/Fichier/), { target: { files: [makeFile("notes.txt")] } });

    expect(screen.getByText(/Seuls les fichiers \.md sont acceptés/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Démarrer l'ingestion/ })).toBeDisabled();
    expect(startIngestionUpload).not.toHaveBeenCalled();
  });

  it("AC11: selecting a domain fetches its context suggestions, changing domain re-fetches for the new one", async () => {
    listContexts.mockImplementation((domain) =>
      Promise.resolve({ contexts: domain === "PERSONAL" ? ["Livres"] : ["Mythologie japonaise"] })
    );
    const user = userEvent.setup();
    render(<NewIngestionModal open={true} onCancel={() => {}} onSuccess={() => {}} />);

    await waitFor(() => expect(listContexts).toHaveBeenCalledWith("PERSONAL"));

    await user.selectOptions(screen.getByLabelText("Domaine"), "FICTION");

    await waitFor(() => expect(listContexts).toHaveBeenCalledWith("FICTION"));
  });

  it("AC12: submit with a file and a domain (no context) calls startIngestionUpload once and reports a null context", async () => {
    startIngestionUpload.mockResolvedValue({ task_id: "ingest-1" });
    const onSuccess = vi.fn();
    const user = userEvent.setup();
    render(<NewIngestionModal open={true} onCancel={() => {}} onSuccess={onSuccess} />);

    const file = makeFile("notes.md");
    await user.upload(screen.getByLabelText(/Fichier/), file);
    await user.click(screen.getByRole("button", { name: /Démarrer l'ingestion/ }));

    await waitFor(() =>
      expect(onSuccess).toHaveBeenCalledWith({ taskId: "ingest-1", domain: "PERSONAL", context: null })
    );
    expect(startIngestionUpload).toHaveBeenCalledTimes(1);
    expect(startIngestionUpload).toHaveBeenCalledWith("PERSONAL", file);
  });

  it("submitting with a non-empty context reports the trimmed context string (feeds IngestionLogs' polling, AC13)", async () => {
    startIngestionUpload.mockResolvedValue({ task_id: "ingest-2" });
    const onSuccess = vi.fn();
    const user = userEvent.setup();
    render(<NewIngestionModal open={true} onCancel={() => {}} onSuccess={onSuccess} />);

    await user.upload(screen.getByLabelText(/Fichier/), makeFile("notes.md"));
    await user.type(screen.getByLabelText(/Contexte/), "  Mythologie japonaise  ");
    await user.click(screen.getByRole("button", { name: /Démarrer l'ingestion/ }));

    await waitFor(() =>
      expect(onSuccess).toHaveBeenCalledWith({
        taskId: "ingest-2",
        domain: "PERSONAL",
        context: "Mythologie japonaise",
      })
    );
  });

  it("does not render at all when open is false", () => {
    const { container } = render(<NewIngestionModal open={false} onCancel={() => {}} onSuccess={() => {}} />);
    expect(container).toBeEmptyDOMElement();
  });
});
