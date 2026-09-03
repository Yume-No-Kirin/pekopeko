import { useState } from "react";

// Not in any mockup - pekopeko-workflow.html's reject button has no
// confirmation step at all. New UI per TASK-010's own Scope, shared with
// TASK-011 for its own reject action.
export default function RejectReasonModal({ open, onCancel, onConfirm }) {
  const [reason, setReason] = useState("");

  if (!open) return null;

  function handleConfirm() {
    onConfirm(reason.trim());
    setReason("");
  }

  function handleCancel() {
    setReason("");
    onCancel();
  }

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true">
      <div className="modal">
        <div className="modal-header">Rejeter cette note</div>
        <div className="modal-body">
          <label className="filter-label" htmlFor="reject-reason">
            Raison (optionnelle)
          </label>
          <textarea
            id="reject-reason"
            className="modal-textarea"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
          />
        </div>
        <div className="modal-actions">
          <button type="button" className="btn" onClick={handleCancel}>
            Annuler
          </button>
          <button type="button" className="btn btn-primary" onClick={handleConfirm}>
            Confirmer le rejet
          </button>
        </div>
      </div>
    </div>
  );
}
