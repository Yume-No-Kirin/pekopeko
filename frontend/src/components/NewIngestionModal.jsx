import { useEffect, useState } from "react";
import { DOMAINS } from "../api/domains.js";
import { startIngestionUpload } from "../api/tasks.js";
import { listContexts } from "../api/review.js";

// Structurally modeled on RejectReasonModal.jsx (.modal-overlay/.modal/
// .modal-header/.modal-body/.modal-actions, no new CSS). TASK-009a: closes
// the "+ Nouvelle ingestion" stub left by TASK-009.
export default function NewIngestionModal({ open, onCancel, onSuccess }) {
  const [file, setFile] = useState(null);
  const [fileError, setFileError] = useState(null);
  const [domain, setDomain] = useState(DOMAINS[0]);
  const [context, setContext] = useState("");
  const [contextOptions, setContextOptions] = useState([]);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    listContexts(domain)
      .then((result) => {
        if (!cancelled) setContextOptions(result.contexts || []);
      })
      .catch(() => {
        if (!cancelled) setContextOptions([]);
      });
    return () => {
      cancelled = true;
    };
  }, [domain, open]);

  if (!open) return null;

  function handleFileChange(e) {
    const selected = e.target.files[0] || null;
    if (selected && !selected.name.toLowerCase().endsWith(".md")) {
      setFile(null);
      setFileError("Seuls les fichiers .md sont acceptés.");
      return;
    }
    setFileError(null);
    setFile(selected);
  }

  function reset() {
    setFile(null);
    setFileError(null);
    setDomain(DOMAINS[0]);
    setContext("");
    setSubmitError(null);
  }

  function handleCancel() {
    reset();
    onCancel();
  }

  async function handleSubmit() {
    if (!file) return;
    setSubmitting(true);
    setSubmitError(null);
    try {
      const result = await startIngestionUpload(domain, file);
      const trimmedContext = context.trim() || null;
      const submittedDomain = domain;
      reset();
      setSubmitting(false);
      onSuccess({ taskId: result.task_id, domain: submittedDomain, context: trimmedContext });
    } catch (err) {
      setSubmitting(false);
      setSubmitError(err);
    }
  }

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true">
      <div className="modal">
        <div className="modal-header">Nouvelle ingestion</div>
        <div className="modal-body">
          {submitError && (
            <div className="validation-error" role="alert">
              {submitError.message}
            </div>
          )}

          <label className="filter-label" htmlFor="new-ingestion-file">
            Fichier (.md)
          </label>
          <input id="new-ingestion-file" type="file" accept=".md" onChange={handleFileChange} />
          {fileError && <p className="task-error">{fileError}</p>}

          <label className="filter-label" htmlFor="new-ingestion-domain">
            Domaine
          </label>
          <select
            id="new-ingestion-domain"
            className="filter-select"
            required
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
          >
            {DOMAINS.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>

          <label className="filter-label" htmlFor="new-ingestion-context">
            Contexte (optionnel)
          </label>
          <input
            id="new-ingestion-context"
            className="metadata-edit-input"
            type="text"
            list="new-ingestion-context-options"
            value={context}
            onChange={(e) => setContext(e.target.value)}
          />
          <datalist id="new-ingestion-context-options">
            {contextOptions.map((c) => (
              <option key={c} value={c} />
            ))}
          </datalist>
        </div>
        <div className="modal-actions">
          <button type="button" className="btn" onClick={handleCancel}>
            Annuler
          </button>
          <button
            type="button"
            className="btn btn-primary"
            disabled={!file || submitting}
            onClick={handleSubmit}
          >
            {submitting ? "Envoi…" : "Démarrer l'ingestion"}
          </button>
        </div>
      </div>
    </div>
  );
}
