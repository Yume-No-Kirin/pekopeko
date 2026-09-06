import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import EntityTypeBadge from "./EntityTypeBadge.jsx";

describe("EntityTypeBadge", () => {
  it("renders the entity_type value", () => {
    render(<EntityTypeBadge entityType="person" />);
    expect(screen.getByText("person")).toBeInTheDocument();
  });

  it("renders a placeholder without crashing when entity_type is null/missing", () => {
    render(<EntityTypeBadge entityType={null} />);
    expect(screen.getByText("non précisé")).toBeInTheDocument();
  });
});
