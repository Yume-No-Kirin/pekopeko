import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import RelationshipEndpoints from "./RelationshipEndpoints.jsx";

describe("RelationshipEndpoints", () => {
  it("renders a resolved endpoint's label", () => {
    render(<RelationshipEndpoints endpoints={[{ id: "entity-1", label: "entity: Marie Dupont" }]} />);
    expect(screen.getByText("entity: Marie Dupont")).toBeInTheDocument();
  });

  it("renders the raw id when the endpoint's label is null (unresolved/404)", () => {
    render(<RelationshipEndpoints endpoints={[{ id: "some-canonical-id", label: null }]} />);
    expect(screen.getByText("some-canonical-id")).toBeInTheDocument();
  });

  it("renders one item per endpoint", () => {
    render(
      <RelationshipEndpoints
        endpoints={[
          { id: "e1", label: "entity: A" },
          { id: "e2", label: null },
        ]}
      />
    );
    expect(screen.getAllByRole("listitem")).toHaveLength(2);
  });
});
