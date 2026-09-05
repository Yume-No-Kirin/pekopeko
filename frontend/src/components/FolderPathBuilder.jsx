import { useRef, useState } from "react";

// Controlled port of the mockup's folder-path builder (toggleFolderDropdown/
// selectFolder/createNewFolder/addFolderSegment/updatePathData in
// pekopeko-proposal-detail.html) - React state + callbacks instead of DOM
// mutation, and a small inline input instead of window.prompt().
//
// Drag-to-reorder (TASK-014 amendment, 2026-09-05): a segment can be picked
// up with a long press (~400ms held still) then dragged to a new slot. This
// interaction has no mockup equivalent - both mockups only replace/append
// segments. A quick press-and-release, or a press that moves before the
// long-press threshold fires, is left alone and behaves exactly as before
// (opens/toggles the segment's dropdown).
const LONG_PRESS_MS = 400;
const MOVE_THRESHOLD_PX = 6;

function cleanSegmentName(raw) {
  return raw.trim().toLowerCase().replace(/\s+/g, "-");
}

export default function FolderPathBuilder({ segments, optionsByDepth, editable, onChange }) {
  const [openIndex, setOpenIndex] = useState(null);
  const [creatingIndex, setCreatingIndex] = useState(null);
  const [newNameDraft, setNewNameDraft] = useState("");
  const [order, setOrder] = useState(null); // array of original indices while a drag is in progress, else null
  const [dragPosition, setDragPosition] = useState(null); // position (in `order`) currently being dragged

  const segmentRefs = useRef([]);
  const dragInfo = useRef(null); // { position, startX, startY, timerId, armed, moved }
  const suppressNextClickRef = useRef(false);

  if (!editable) {
    return (
      <div className="folder-path-builder read-only">
        {segments && segments.length > 0 ? segments.join(" / ") : "—"}
      </div>
    );
  }

  const displaySegments = order ? order.map((i) => segments[i]) : segments;

  function closeAll() {
    setOpenIndex(null);
    setCreatingIndex(null);
    setNewNameDraft("");
  }

  function handleToggleDropdown(index) {
    if (openIndex === index) {
      closeAll();
    } else {
      setOpenIndex(index);
      setCreatingIndex(null);
      setNewNameDraft("");
    }
  }

  function handleSegmentClick(position) {
    if (suppressNextClickRef.current) {
      suppressNextClickRef.current = false;
      return;
    }
    handleToggleDropdown(position);
  }

  function handleSelectOption(index, value) {
    const updated = [...displaySegments];
    updated[index] = value;
    onChange(updated);
    closeAll();
  }

  function handleStartCreate(index) {
    setCreatingIndex(index);
    setNewNameDraft("");
  }

  function handleConfirmCreate() {
    const cleaned = cleanSegmentName(newNameDraft);
    if (!cleaned) return;
    const updated = [...displaySegments];
    if (creatingIndex === displaySegments.length) {
      updated.push(cleaned);
    } else {
      updated[creatingIndex] = cleaned;
    }
    onChange(updated);
    closeAll();
  }

  function findOverPosition(x, y) {
    for (let i = 0; i < segments.length; i++) {
      const el = segmentRefs.current[i];
      if (!el) continue;
      const rect = el.getBoundingClientRect();
      if (x >= rect.left && x <= rect.right && y >= rect.top && y <= rect.bottom) {
        return i;
      }
    }
    return null;
  }

  function handleSegmentPointerDown(e, position) {
    if (creatingIndex !== null) return;
    if (typeof e.currentTarget.setPointerCapture === "function") {
      e.currentTarget.setPointerCapture(e.pointerId);
    }
    const info = { position, startX: e.clientX, startY: e.clientY, armed: false, moved: false };
    dragInfo.current = info;
    info.timerId = setTimeout(() => {
      if (dragInfo.current === info) {
        // Long-press threshold reached: show the "this can be moved" cue
        // (tinted button + grabbing cursor, see .folder-segment.dragging)
        // right away, even before the pointer has actually moved.
        info.armed = true;
        setDragPosition(position);
      }
    }, LONG_PRESS_MS);
  }

  function handleSegmentPointerMove(e) {
    const info = dragInfo.current;
    if (!info) return;
    const dist = Math.hypot(e.clientX - info.startX, e.clientY - info.startY);

    if (!info.armed) {
      if (dist > MOVE_THRESHOLD_PX) {
        clearTimeout(info.timerId);
        dragInfo.current = null;
      }
      return;
    }

    if (!info.moved) {
      if (dist <= MOVE_THRESHOLD_PX) return;
      info.moved = true;
      closeAll();
      setOrder(segments.map((_, i) => i));
    }

    // Snapshot info.position now: it's a mutable ref field, and the
    // setOrder updater below only actually runs later (during React's
    // render phase, after info.position has already been reassigned a few
    // lines down) - reading info.position inside the updater itself would
    // silently use the wrong "from" index.
    const fromPosition = info.position;
    const overPosition = findOverPosition(e.clientX, e.clientY);
    if (overPosition === null || overPosition === fromPosition) return;
    setOrder((prevOrder) => {
      const base = prevOrder || segments.map((_, i) => i);
      const next = [...base];
      const [movedItem] = next.splice(fromPosition, 1);
      next.splice(overPosition, 0, movedItem);
      return next;
    });
    info.position = overPosition;
    setDragPosition(overPosition);
  }

  function handleSegmentPointerUp(e) {
    const info = dragInfo.current;
    dragInfo.current = null;
    if (info) {
      clearTimeout(info.timerId);
      if (typeof e.currentTarget.releasePointerCapture === "function") {
        e.currentTarget.releasePointerCapture(e.pointerId);
      }
    }
    if (info && info.armed && info.moved && order) {
      onChange(order.map((i) => segments[i]));
      suppressNextClickRef.current = true;
    }
    setOrder(null);
    setDragPosition(null);
  }

  function handleSegmentPointerCancel() {
    const info = dragInfo.current;
    dragInfo.current = null;
    if (info) clearTimeout(info.timerId);
    setOrder(null);
    setDragPosition(null);
  }

  return (
    <div className="folder-path-builder">
      {displaySegments.map((segment, index) => (
        <div
          className={`folder-segment${dragPosition === index ? " dragging" : ""}`}
          key={index}
          ref={(el) => (segmentRefs.current[index] = el)}
        >
          <button
            type="button"
            className={`folder-segment-btn${openIndex === index ? " active" : ""}`}
            onPointerDown={(e) => handleSegmentPointerDown(e, index)}
            onPointerMove={handleSegmentPointerMove}
            onPointerUp={handleSegmentPointerUp}
            onPointerCancel={handleSegmentPointerCancel}
            onClick={() => handleSegmentClick(index)}
          >
            {segment} <span>▼</span>
          </button>
          {openIndex === index && (
            <div className="folder-dropdown active">
              {(optionsByDepth[index] || []).map((option) => (
                <div
                  key={option}
                  className="folder-dropdown-item"
                  role="button"
                  tabIndex={0}
                  onClick={() => handleSelectOption(index, option)}
                >
                  {option}
                </div>
              ))}
              {creatingIndex === index ? (
                <div className="folder-dropdown-create-form">
                  <input
                    type="text"
                    aria-label="Nom du nouveau dossier"
                    value={newNameDraft}
                    onChange={(e) => setNewNameDraft(e.target.value)}
                  />
                  <button type="button" onClick={handleConfirmCreate}>Créer</button>
                  <button type="button" onClick={closeAll}>Annuler</button>
                </div>
              ) : (
                <div
                  className="folder-dropdown-item create-new"
                  role="button"
                  tabIndex={0}
                  onClick={() => handleStartCreate(index)}
                >
                  + Créer nouveau...
                </div>
              )}
            </div>
          )}
          {index < displaySegments.length - 1 && <span className="folder-separator">/</span>}
        </div>
      ))}
      {creatingIndex === displaySegments.length ? (
        <div className="folder-dropdown-create-form">
          <input
            type="text"
            aria-label="Nom du nouveau dossier"
            value={newNameDraft}
            onChange={(e) => setNewNameDraft(e.target.value)}
          />
          <button type="button" onClick={handleConfirmCreate}>Créer</button>
          <button type="button" onClick={closeAll}>Annuler</button>
        </div>
      ) : (
        <button type="button" className="folder-add-btn" onClick={() => handleStartCreate(displaySegments.length)}>
          + Ajouter
        </button>
      )}
    </div>
  );
}
