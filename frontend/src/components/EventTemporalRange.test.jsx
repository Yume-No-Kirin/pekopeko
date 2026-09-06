import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import EventTemporalRange from "./EventTemporalRange.jsx";

describe("EventTemporalRange", () => {
  it("renders both bounds when present", () => {
    render(<EventTemporalRange startsAt="2026-08-01T10:00:00" endsAt="2026-08-01T12:00:00" />);
    expect(screen.getByText("2026-08-01T10:00:00 → 2026-08-01T12:00:00")).toBeInTheDocument();
  });

  it("renders a placeholder for a null endsAt without crashing", () => {
    render(<EventTemporalRange startsAt="2026-08-01T10:00:00" endsAt={null} />);
    expect(screen.getByText("2026-08-01T10:00:00 → non précisé")).toBeInTheDocument();
  });

  it("renders a placeholder for a null startsAt without crashing", () => {
    render(<EventTemporalRange startsAt={null} endsAt="2026-08-01T12:00:00" />);
    expect(screen.getByText("non précisé → 2026-08-01T12:00:00")).toBeInTheDocument();
  });
});
