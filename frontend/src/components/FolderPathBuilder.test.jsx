import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, act } from "@testing-library/react";
import FolderPathBuilder from "./FolderPathBuilder.jsx";

describe("FolderPathBuilder", () => {
  it("TASK-014 AC14: read-only renders joined segment path as plain text with no interactive elements", () => {
    render(
      <FolderPathBuilder
        editable={false}
        segments={["mythologie", "japonaise"]}
        optionsByDepth={[]}
        onChange={() => {}}
      />
    );

    expect(screen.getByText("mythologie / japonaise")).toBeInTheDocument();
    expect(screen.queryAllByRole("button")).toHaveLength(0);
  });

  it("TASK-014 AC14/AC18: read-only with empty segments renders a placeholder without crashing", () => {
    render(<FolderPathBuilder editable={false} segments={[]} optionsByDepth={[]} onChange={() => {}} />);

    expect(screen.getByText("—")).toBeInTheDocument();
  });

  it("TASK-014 AC15: editable renders one clickable segment per entry and a trailing + Ajouter button", () => {
    render(
      <FolderPathBuilder
        editable={true}
        segments={["mythologie", "japonaise"]}
        optionsByDepth={[[], []]}
        onChange={() => {}}
      />
    );

    expect(screen.getByRole("button", { name: /mythologie/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /japonaise/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "+ Ajouter" })).toBeInTheDocument();
  });

  it("TASK-014 AC15: clicking a segment opens a dropdown of optionsByDepth[index] plus + Créer nouveau...", () => {
    render(
      <FolderPathBuilder
        editable={true}
        segments={["mythologie"]}
        optionsByDepth={[["livres", "histoire"]]}
        onChange={() => {}}
      />
    );

    fireEvent.click(screen.getByRole("button", { name: /mythologie/ }));

    expect(screen.getByText("livres")).toBeInTheDocument();
    expect(screen.getByText("histoire")).toBeInTheDocument();
    expect(screen.getByText("+ Créer nouveau...")).toBeInTheDocument();
  });

  it("TASK-014 AC16: selecting an existing dropdown option calls onChange with the updated segments array", () => {
    const onChange = vi.fn();
    render(
      <FolderPathBuilder
        editable={true}
        segments={["mythologie"]}
        optionsByDepth={[["livres", "histoire"]]}
        onChange={onChange}
      />
    );

    fireEvent.click(screen.getByRole("button", { name: /mythologie/ }));
    fireEvent.click(screen.getByText("livres"));

    expect(onChange).toHaveBeenCalledWith(["livres"]);
  });

  it("TASK-014 AC16: confirming + Créer nouveau... calls onChange with the cleaned new name", () => {
    const onChange = vi.fn();
    render(
      <FolderPathBuilder editable={true} segments={["mythologie"]} optionsByDepth={[[]]} onChange={onChange} />
    );

    fireEvent.click(screen.getByRole("button", { name: /mythologie/ }));
    fireEvent.click(screen.getByText("+ Créer nouveau..."));
    fireEvent.change(screen.getByLabelText("Nom du nouveau dossier"), { target: { value: " Nouveau Nom " } });
    fireEvent.click(screen.getByText("Créer"));

    expect(onChange).toHaveBeenCalledWith(["nouveau-nom"]);
  });

  it("TASK-014 AC16: + Ajouter then confirming the inline input calls onChange with the array extended by one entry", () => {
    const onChange = vi.fn();
    render(
      <FolderPathBuilder editable={true} segments={["mythologie"]} optionsByDepth={[[]]} onChange={onChange} />
    );

    fireEvent.click(screen.getByRole("button", { name: "+ Ajouter" }));
    fireEvent.change(screen.getByLabelText("Nom du nouveau dossier"), { target: { value: "Livres" } });
    fireEvent.click(screen.getByText("Créer"));

    expect(onChange).toHaveBeenCalledWith(["mythologie", "livres"]);
  });

  describe("TASK-014 amendment (2026-09-05): drag-to-reorder", () => {
    // jsdom has no PointerEvent constructor (https://github.com/jsdom/jsdom/issues/2527),
    // so testing-library's fireEvent.pointerDown/Move/Up silently fall back to a plain
    // Event and drop clientX/clientY/pointerId. Build the event by hand instead.
    function firePointer(el, type, { clientX, clientY, pointerId = 1 }) {
      const event = new Event(type, { bubbles: true, cancelable: true });
      Object.assign(event, { clientX, clientY, pointerId });
      fireEvent(el, event);
    }

    function mockSegmentRects(container) {
      // Lay out each .folder-segment as a 100px-wide slot side by side so
      // clientX alone determines which slot a point falls in.
      const segmentEls = container.querySelectorAll(".folder-segment");
      segmentEls.forEach((el, i) => {
        el.getBoundingClientRect = () => ({
          left: i * 100,
          right: i * 100 + 100,
          top: 0,
          bottom: 40,
          width: 100,
          height: 40,
        });
      });
    }

    it("a quick press-and-release with no movement still opens the dropdown (no regression on AC15)", () => {
      const onChange = vi.fn();
      const { container } = render(
        <FolderPathBuilder
          editable={true}
          segments={["mythologie", "japonaise"]}
          optionsByDepth={[["livres"], []]}
          onChange={onChange}
        />
      );
      mockSegmentRects(container);
      const btn = screen.getByRole("button", { name: /mythologie/ });

      firePointer(btn, "pointerdown", { clientX: 10, clientY: 10 });
      firePointer(btn, "pointerup", { clientX: 10, clientY: 10 });
      fireEvent.click(btn);

      expect(screen.getByText("livres")).toBeInTheDocument();
      expect(onChange).not.toHaveBeenCalled();
    });

    it("a long press held still (no drag yet) tints the segment and shows the grabbing cursor as soon as the threshold fires", () => {
      vi.useFakeTimers();
      const { container } = render(
        <FolderPathBuilder
          editable={true}
          segments={["mythologie", "japonaise"]}
          optionsByDepth={[["livres"], []]}
          onChange={() => {}}
        />
      );
      mockSegmentRects(container);
      const btn = screen.getByRole("button", { name: /mythologie/ });
      const segmentEl = btn.closest(".folder-segment");

      firePointer(btn, "pointerdown", { clientX: 10, clientY: 10 });
      expect(segmentEl).not.toHaveClass("dragging");

      // The timer callback calls setState outside of a React-managed event,
      // so (unlike the other tests here) nothing else flushes it before the
      // next assertion - wrap the advance in act() to flush it ourselves.
      act(() => {
        vi.advanceTimersByTime(500); // past the long-press threshold, pointer held still
      });
      expect(segmentEl).toHaveClass("dragging");

      firePointer(btn, "pointerup", { clientX: 10, clientY: 10 });
      expect(segmentEl).not.toHaveClass("dragging");
      vi.useRealTimers();
    });

    it("a long press followed by a drag past another segment reorders and calls onChange exactly once, without opening a dropdown", () => {
      vi.useFakeTimers();
      const onChange = vi.fn();
      const { container } = render(
        <FolderPathBuilder
          editable={true}
          segments={["mythologie", "japonaise", "creatures"]}
          optionsByDepth={[[], [], []]}
          onChange={onChange}
        />
      );
      mockSegmentRects(container);
      const btn = screen.getByRole("button", { name: /mythologie/ });

      firePointer(btn, "pointerdown", { clientX: 10, clientY: 10 });
      vi.advanceTimersByTime(500); // past the long-press threshold
      firePointer(btn, "pointermove", { clientX: 250, clientY: 10 }); // into the 3rd slot
      firePointer(btn, "pointerup", { clientX: 250, clientY: 10 });
      fireEvent.click(btn); // synthetic click the browser fires right after pointerup

      expect(onChange).toHaveBeenCalledTimes(1);
      expect(onChange).toHaveBeenCalledWith(["japonaise", "creatures", "mythologie"]);
      expect(screen.queryByText("+ Créer nouveau...")).not.toBeInTheDocument();
      vi.useRealTimers();
    });

    it("moving before the long-press threshold fires cancels the drag and behaves like a normal click", () => {
      vi.useFakeTimers();
      const onChange = vi.fn();
      const { container } = render(
        <FolderPathBuilder
          editable={true}
          segments={["mythologie", "japonaise"]}
          optionsByDepth={[["livres"], []]}
          onChange={onChange}
        />
      );
      mockSegmentRects(container);
      const btn = screen.getByRole("button", { name: /mythologie/ });

      firePointer(btn, "pointerdown", { clientX: 10, clientY: 10 });
      firePointer(btn, "pointermove", { clientX: 40, clientY: 10 }); // past the 6px threshold, before the timer fires
      vi.advanceTimersByTime(500);
      firePointer(btn, "pointerup", { clientX: 40, clientY: 10 });
      fireEvent.click(btn);

      expect(onChange).not.toHaveBeenCalled();
      expect(screen.getByText("livres")).toBeInTheDocument();
      vi.useRealTimers();
    });
  });
});
