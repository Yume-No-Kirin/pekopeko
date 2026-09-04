import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import ProvenanceSection from "./ProvenanceSection.jsx";

describe("ProvenanceSection", () => {
  it("AC4: renders exactly the 2 baseline fields when TASK-001a's fields are absent", () => {
    render(<ProvenanceSection provenance={{ source_id: "src-a", extraction_provider: "ollama" }} />);

    expect(screen.getByText("src-a")).toBeInTheDocument();
    expect(screen.getByText("ollama")).toBeInTheDocument();
    expect(screen.queryByText("Modèle")).not.toBeInTheDocument();
    expect(screen.queryByText("Température")).not.toBeInTheDocument();
    expect(screen.queryByText("Extraction ID")).not.toBeInTheDocument();
    expect(screen.queryByText("Durée extraction")).not.toBeInTheDocument();
  });

  it("AC5: renders all 6 rows when TASK-001a's additional fields are present", () => {
    render(
      <ProvenanceSection
        provenance={{
          source_id: "src-a",
          extraction_provider: "ollama",
          provider_model: "llama3:8b-instruct",
          provider_temperature: 0.7,
          extraction_id: "extract-abc123",
          extraction_duration_seconds: 2.3,
        }}
      />
    );

    expect(screen.getByText("src-a")).toBeInTheDocument();
    expect(screen.getByText("ollama")).toBeInTheDocument();
    expect(screen.getByText("llama3:8b-instruct")).toBeInTheDocument();
    expect(screen.getByText("0.7")).toBeInTheDocument();
    expect(screen.getByText("extract-abc123")).toBeInTheDocument();
    expect(screen.getByText("2.3")).toBeInTheDocument();
  });
});
