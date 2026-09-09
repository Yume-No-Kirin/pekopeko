import { describe, it, expect, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import SourceGroupHeader from "./SourceGroupHeader.jsx";

function makeGroup(overrides = {}) {
  return {
    sourceId: "src-a8f3d2e1b4c5",
    domain: "PERSONAL",
    originalFilename: "notes.md",
    taskStatus: undefined,
    notes: [{ id: "p1" }, { id: "p2" }, { id: "p3" }],
    ...overrides,
  };
}

function renderInTable(ui) {
  return render(
    <table>
      <tbody>{ui}</tbody>
    </table>
  );
}

describe("SourceGroupHeader", () => {
  it("renders the source info block (filename, id, domain, notes count)", () => {
    const group = makeGroup();
    renderInTable(<SourceGroupHeader group={group} columnCount={5} onAcceptAll={() => {}} onRejectAll={() => {}} />);

    expect(screen.getByText(/notes\.md/)).toBeInTheDocument();
    expect(screen.getByText("src-a8f3d2e1b4c5")).toBeInTheDocument();
    expect(screen.getByText("PERSONAL")).toBeInTheDocument();
    expect(screen.getByText("3 notes proposées")).toBeInTheDocument();
  });

  it("renders no TaskStatusBadge when group.taskStatus is absent, one when present", () => {
    const { container, rerender } = renderInTable(
      <SourceGroupHeader group={makeGroup()} columnCount={5} onAcceptAll={() => {}} onRejectAll={() => {}} />
    );
    expect(container.querySelector(".status-badge")).not.toBeInTheDocument();

    rerender(
      <table>
        <tbody>
          <SourceGroupHeader
            group={makeGroup({ taskStatus: "completed" })}
            columnCount={5}
            onAcceptAll={() => {}}
            onRejectAll={() => {}}
          />
        </tbody>
      </table>
    );
    expect(container.querySelector(".status-badge")).toHaveTextContent("Complété");
  });

  it("renders 'Tout accepter' / 'Tout rejeter' buttons with the maquette's class names", () => {
    renderInTable(
      <SourceGroupHeader group={makeGroup()} columnCount={5} onAcceptAll={() => {}} onRejectAll={() => {}} />
    );

    const acceptBtn = screen.getByRole("button", { name: /Tout accepter/ });
    const rejectBtn = screen.getByRole("button", { name: /Tout rejeter/ });
    expect(acceptBtn.className).toContain("btn-small");
    expect(acceptBtn.className).toContain("accept-all");
    expect(rejectBtn.className).toContain("btn-small");
    expect(rejectBtn.className).toContain("reject-all");
  });

  it("clicking 'Tout accepter' calls onAcceptAll once with (domain, all note ids in order)", async () => {
    const onAcceptAll = vi.fn();
    const onRejectAll = vi.fn();
    renderInTable(
      <SourceGroupHeader group={makeGroup()} columnCount={5} onAcceptAll={onAcceptAll} onRejectAll={onRejectAll} />
    );

    await userEvent.click(screen.getByRole("button", { name: /Tout accepter/ }));

    expect(onAcceptAll).toHaveBeenCalledTimes(1);
    expect(onAcceptAll).toHaveBeenCalledWith("PERSONAL", ["p1", "p2", "p3"]);
    expect(onRejectAll).not.toHaveBeenCalled();
  });

  it("clicking 'Tout rejeter' calls onRejectAll once with (domain, all note ids in order)", async () => {
    const onAcceptAll = vi.fn();
    const onRejectAll = vi.fn();
    renderInTable(
      <SourceGroupHeader group={makeGroup()} columnCount={5} onAcceptAll={onAcceptAll} onRejectAll={onRejectAll} />
    );

    await userEvent.click(screen.getByRole("button", { name: /Tout rejeter/ }));

    expect(onRejectAll).toHaveBeenCalledTimes(1);
    expect(onRejectAll).toHaveBeenCalledWith("PERSONAL", ["p1", "p2", "p3"]);
    expect(onAcceptAll).not.toHaveBeenCalled();
  });

  it("info cell's colSpan is columnCount - 1, leaving the action cell its own column", () => {
    renderInTable(
      <SourceGroupHeader group={makeGroup()} columnCount={5} onAcceptAll={() => {}} onRejectAll={() => {}} />
    );

    const row = screen.getByText(/notes\.md/).closest("tr");
    const cells = within(row).getAllByRole("cell");
    expect(cells).toHaveLength(2);
    expect(cells[0]).toHaveAttribute("colspan", "4");
  });
});
