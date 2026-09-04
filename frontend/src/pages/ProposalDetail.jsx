import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { listProposals, getProposal, acceptProposal, rejectProposal } from "../api/review.js";
import { listIngestions } from "../api/tasks.js";
import EpistemicStatusBadge from "../components/EpistemicStatusBadge.jsx";
import RejectReasonModal from "../components/RejectReasonModal.jsx";
import TaskEventLog from "../components/TaskEventLog.jsx";
import ProvenanceSection from "../components/ProvenanceSection.jsx";

const REVIEWER_ID = import.meta.env.VITE_REVIEWER_ID || "cleo";

const PROPOSAL_STATUS_LABELS = {
  PROPOSED: "À valider",
  ACCEPTED: "Acceptée",
  REJECTED: "Rejetée",
  EDITED: "Éditée",
};

function capitalize(value) {
  return value ? value.charAt(0).toUpperCase() + value.slice(1) : value;
}

export default function ProposalDetail() {
  const { domain, proposalId } = useParams();
  const navigate = useNavigate();

  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionError, setActionError] = useState(null);
  const [rejectOpen, setRejectOpen] = useState(false);
  const [ingestionTasks, setIngestionTasks] = useState([]);
  const [queue, setQueue] = useState([]);

  // Three independent fetches: the detail fetch is mandatory (its failure is
  // the page's error state); the ingestion-task list (Logs section) and the
  // PROPOSED/assertion queue (Précédent/Suivant) each degrade to an empty
  // list on failure rather than blocking the rest of the page - same
  // non-blocking-satellite posture the ticket asks for (TASK-001a/TASK-001b
  // aren't hard dependencies either).
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    setDetail(null);

    getProposal(domain, proposalId)
      .then((result) => {
        if (!cancelled) {
          setDetail(result);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err);
          setLoading(false);
        }
      });

    listIngestions(domain, { limit: 500, offset: 0 })
      .then((page) => {
        if (!cancelled) setIngestionTasks(page.items);
      })
      .catch(() => {
        if (!cancelled) setIngestionTasks([]);
      });

    listProposals(domain, { status: "PROPOSED", limit: 500, offset: 0 })
      .then((page) => {
        if (!cancelled) {
          setQueue(page.items.filter((item) => item.proposed_item_type === "assertion"));
        }
      })
      .catch(() => {
        if (!cancelled) setQueue([]);
      });

    return () => {
      cancelled = true;
    };
  }, [domain, proposalId]);

  async function handleAccept() {
    setActionError(null);
    try {
      await acceptProposal(domain, proposalId, REVIEWER_ID);
      navigate("/validation");
    } catch (err) {
      setActionError(err);
    }
  }

  async function handleRejectConfirm(reason) {
    setRejectOpen(false);
    setActionError(null);
    try {
      await rejectProposal(domain, proposalId, REVIEWER_ID, reason);
      navigate("/validation");
    } catch (err) {
      setActionError(err);
    }
  }

  const currentIndex = queue.findIndex((item) => item.id === proposalId);
  const hasPrev = currentIndex > 0;
  const hasNext = currentIndex >= 0 && currentIndex < queue.length - 1;

  function goToPrev() {
    navigate(`/validation/${domain}/${queue[currentIndex - 1].id}`);
  }

  function goToNext() {
    navigate(`/validation/${domain}/${queue[currentIndex + 1].id}`);
  }

  if (loading) {
    return (
      <>
        <header className="page-header">
          <h1 className="page-title">Revue de proposition</h1>
        </header>
        <div className="content-wrapper">
          <div className="validation-loading">Chargement de la proposition…</div>
        </div>
      </>
    );
  }

  if (error) {
    return (
      <>
        <header className="page-header">
          <h1 className="page-title">Revue de proposition</h1>
        </header>
        <div className="content-wrapper">
          <div className="validation-error" role="alert">
            Impossible de charger la proposition : {error.message}
          </div>
        </div>
      </>
    );
  }

  const { frontmatter, body, source_frontmatter: sourceFrontmatter, source_body: sourceBody } = detail;
  const ingestionTask = ingestionTasks.find((task) => task.source_id === frontmatter.provenance.source_id);

  return (
    <>
      <header className="page-header">
        <div className="breadcrumb">Dashboard / Validation / Détails</div>
        <h1 className="page-title">Revue de proposition</h1>
        <div className="proposal-id">{frontmatter.id}</div>
      </header>

      <div className="content-wrapper">
        {actionError && (
          <div className="validation-error" role="alert">
            Action impossible : {actionError.message}
          </div>
        )}

        <div className="status-bar">
          <div className="status-info">
            <span className={`proposal-status-badge ${frontmatter.proposal_status}`}>
              {PROPOSAL_STATUS_LABELS[frontmatter.proposal_status] || frontmatter.proposal_status}
            </span>
            <span className="domain-badge">{frontmatter.domain}</span>
            <span className="type-badge">{capitalize(frontmatter.proposed_item_type)}</span>
            <EpistemicStatusBadge status={frontmatter.epistemic_status} />
          </div>
          <div className="validation-actions">
            <div className="nav-buttons">
              <button type="button" className="btn btn-nav" disabled={!hasPrev} onClick={goToPrev}>
                ← Précédent
              </button>
            </div>
            <div className="action-buttons">
              <button type="button" className="btn btn-reject" onClick={() => setRejectOpen(true)}>
                ✕ Rejeter
              </button>
              <button type="button" className="btn btn-accept" onClick={handleAccept}>
                ✓ Accepter
              </button>
            </div>
            <div className="nav-buttons">
              <button type="button" className="btn btn-nav" disabled={!hasNext} onClick={goToNext}>
                Suivant →
              </button>
            </div>
          </div>
        </div>

        <div className="two-column">
          <div className="section-card">
            <div className="section-header">
              <h2 className="card-section-title">Contenu de la proposition</h2>
            </div>
            <div className="section-content">
              <div className="content-display">{body}</div>
            </div>
          </div>

          <div className="section-card">
            <div className="section-header">
              <h2 className="card-section-title">Métadonnées</h2>
            </div>
            <div className="section-content">
              <div className="metadata-table">
                <div className="metadata-row">
                  <div className="metadata-label">ID Proposition</div>
                  <div className="metadata-value"><code>{frontmatter.id}</code></div>
                </div>
                <div className="metadata-row">
                  <div className="metadata-label">Statut épistémique</div>
                  <div className="metadata-value">{frontmatter.epistemic_status}</div>
                </div>
                <div className="metadata-row">
                  <div className="metadata-label">Créé le</div>
                  <div className="metadata-value">{frontmatter.created_at}</div>
                </div>
                <div className="metadata-row">
                  <div className="metadata-label">Validité</div>
                  <div className="metadata-value">
                    De: {frontmatter.valid_from || "—"} · À: {frontmatter.valid_until || "—"}
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="section-card">
            <div className="section-header">
              <h2 className="card-section-title">Source originale</h2>
            </div>
            <div className="section-content">
              <div className="metadata-table">
                <div className="metadata-row">
                  <div className="metadata-label">Fichier</div>
                  <div className="metadata-value"><code>{sourceFrontmatter.original_filename}</code></div>
                </div>
                <div className="metadata-row">
                  <div className="metadata-label">Hash contenu</div>
                  <div className="metadata-value"><code>{sourceFrontmatter.content_hash}</code></div>
                </div>
                <div className="metadata-row">
                  <div className="metadata-label">Ingéré le</div>
                  <div className="metadata-value">{sourceFrontmatter.ingested_at}</div>
                </div>
              </div>
              <div className="source-preview">{sourceBody}</div>
            </div>
          </div>

          <ProvenanceSection provenance={frontmatter.provenance} />

          <div className="section-card logs-section">
            <div className="section-header">
              <h2 className="card-section-title">Logs d'ingestion complets</h2>
            </div>
            <div className="section-content">
              {ingestionTask && ingestionTask.events && ingestionTask.events.length > 0 ? (
                <TaskEventLog events={ingestionTask.events} />
              ) : (
                <p className="task-event-log-empty">Aucun journal disponible.</p>
              )}
            </div>
          </div>
        </div>
      </div>

      <RejectReasonModal
        open={rejectOpen}
        onCancel={() => setRejectOpen(false)}
        onConfirm={handleRejectConfirm}
      />
    </>
  );
}
