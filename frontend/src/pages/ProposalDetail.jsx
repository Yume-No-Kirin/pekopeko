import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  listProposals,
  getProposal,
  acceptProposal,
  rejectProposal,
  editProposal,
  listOrganizationFolders,
} from "../api/review.js";
import { listIngestions } from "../api/tasks.js";
import EpistemicStatusBadge from "../components/EpistemicStatusBadge.jsx";
import RejectReasonModal from "../components/RejectReasonModal.jsx";
import TaskEventLog from "../components/TaskEventLog.jsx";
import ProvenanceSection from "../components/ProvenanceSection.jsx";
import FolderPathBuilder from "../components/FolderPathBuilder.jsx";
import EntityTypeBadge from "../components/EntityTypeBadge.jsx";
import EventTemporalRange from "../components/EventTemporalRange.jsx";
import RelationshipEndpoints from "../components/RelationshipEndpoints.jsx";

const REVIEWER_ID = import.meta.env.VITE_REVIEWER_ID || "cleo";

const PROPOSAL_STATUS_LABELS = {
  PROPOSED: "À valider",
  ACCEPTED: "Acceptée",
  REJECTED: "Rejetée",
  EDITED: "Éditée",
};

// Must match EpistemicStatusBadge.jsx's own label set.
const EPISTEMIC_STATUSES = ["direct", "inferred", "uncertain", "contested"];

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
  const [editing, setEditing] = useState(false);
  const [draftBody, setDraftBody] = useState("");
  const [draftEpistemicStatus, setDraftEpistemicStatus] = useState("");
  const [draftValidFrom, setDraftValidFrom] = useState("");
  const [draftValidUntil, setDraftValidUntil] = useState("");
  const [draftPathSegments, setDraftPathSegments] = useState([]);
  const [folderOptions, setFolderOptions] = useState([]);
  const [endpointLabels, setEndpointLabels] = useState({});
  const endpointCacheRef = useRef(new Map());

  // Three independent fetches: the detail fetch is mandatory (its failure is
  // the page's error state); the ingestion-task list (Logs section) and the
  // PROPOSED/EDITED queue (Précédent/Suivant, all 4 proposed_item_types
  // since TASK-012) each degrade to an empty list on failure rather than
  // blocking the rest of the page - same non-blocking-satellite posture the
  // ticket asks for (TASK-001a/TASK-001b aren't hard dependencies either).
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    setDetail(null);

    endpointCacheRef.current = new Map();
    setEndpointLabels({});

    getProposal(domain, proposalId)
      .then((result) => {
        if (!cancelled) {
          setDetail(result);
          setLoading(false);
          if (result.frontmatter.proposed_item_type === "relationship") {
            resolveEndpoints(result.frontmatter.endpoints || []);
          }
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

    Promise.all([
      listProposals(domain, { status: "PROPOSED", limit: 500, offset: 0 }),
      listProposals(domain, { status: "EDITED", limit: 500, offset: 0 }),
    ])
      .then(([proposedPage, editedPage]) => {
        if (!cancelled) {
          setQueue([...proposedPage.items, ...editedPage.items]);
        }
      })
      .catch(() => {
        if (!cancelled) setQueue([]);
      });

    // Resolves each relationship endpoint id to a display label via a
    // targeted getProposal call (no batch already in memory on this
    // single-proposal page, an explicit N+1 trade-off per TASK-012). The
    // promise is cached in endpointCacheRef *before* awaiting it, so two
    // endpoints that mutually reference each other's proposal_id never
    // trigger a second fetch for the same id. A 404 means "already
    // canonical" (plain id, no label); any other error degrades the same
    // way, matching this page's existing non-blocking-satellite fetches.
    function resolveEndpoints(ids) {
      for (const id of ids) {
        if (endpointCacheRef.current.has(id)) continue;
        const promise = getProposal(domain, id)
          .then((resolved) => `${resolved.frontmatter.proposed_item_type}: ${(resolved.body || "").slice(0, 60)}`)
          .catch(() => null);
        endpointCacheRef.current.set(id, promise);
      }
      Promise.all(ids.map((id) => endpointCacheRef.current.get(id))).then((labels) => {
        if (cancelled) return;
        const next = {};
        ids.forEach((id, i) => {
          next[id] = labels[i];
        });
        setEndpointLabels((current) => ({ ...current, ...next }));
      });
    }

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

  function handleEditToggle() {
    setDraftBody(body);
    setDraftEpistemicStatus(frontmatter.epistemic_status);
    setDraftValidFrom(frontmatter.valid_from || "");
    setDraftValidUntil(frontmatter.valid_until || "");
    setDraftPathSegments(frontmatter.proposed_path_segments || []);
    setActionError(null);
    setEditing(true);
    listOrganizationFolders(domain, "assertion")
      .then((result) => setFolderOptions(result.segments_by_depth || []))
      .catch(() => setFolderOptions([]));
  }

  function handleEditCancel() {
    setEditing(false);
  }

  async function handleEditSave() {
    setActionError(null);
    try {
      await editProposal(domain, proposalId, REVIEWER_ID, {
        body: draftBody,
        fieldUpdates: {
          epistemic_status: draftEpistemicStatus,
          valid_from: draftValidFrom || null,
          valid_until: draftValidUntil || null,
          proposed_path_segments: draftPathSegments,
        },
      });
      const refreshed = await getProposal(domain, proposalId);
      setDetail(refreshed);
      setEditing(false);
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
              {editing ? (
                <>
                  <button type="button" className="btn btn-small" onClick={handleEditCancel}>
                    Annuler
                  </button>
                  <button type="button" className="btn btn-small" onClick={handleEditSave}>
                    Sauvegarder
                  </button>
                </>
              ) : (
                <>
                  <button type="button" className="btn btn-reject" onClick={() => setRejectOpen(true)}>
                    ✕ Rejeter
                  </button>
                  <button type="button" className="btn btn-accept" onClick={handleAccept}>
                    ✓ Accepter
                  </button>
                  {frontmatter.proposed_item_type === "assertion" && (
                    <button type="button" className="btn btn-edit" onClick={handleEditToggle}>
                      ✎ Éditer
                    </button>
                  )}
                </>
              )}
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
              {editing ? (
                <textarea
                  className="content-textarea"
                  aria-label="Contenu de la proposition"
                  value={draftBody}
                  onChange={(e) => setDraftBody(e.target.value)}
                />
              ) : (
                <div className="content-display">{body}</div>
              )}
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
                  <div className="metadata-label">Créé le</div>
                  <div className="metadata-value">{frontmatter.created_at}</div>
                </div>
                {frontmatter.proposed_item_type === "assertion" && (
                  <>
                    <div className="metadata-row">
                      <div className="metadata-label">Statut épistémique</div>
                      <div className="metadata-value">
                        {editing ? (
                          <select
                            className="metadata-edit-select"
                            value={draftEpistemicStatus}
                            onChange={(e) => setDraftEpistemicStatus(e.target.value)}
                          >
                            {EPISTEMIC_STATUSES.map((status) => (
                              <option key={status} value={status}>{status}</option>
                            ))}
                          </select>
                        ) : (
                          frontmatter.epistemic_status
                        )}
                      </div>
                    </div>
                    <div className="metadata-row">
                      <div className="metadata-label">Validité</div>
                      <div className="metadata-value">
                        {editing ? (
                          <>
                            <input
                              type="text"
                              className="metadata-edit-input"
                              aria-label="Valide à partir de"
                              value={draftValidFrom}
                              onChange={(e) => setDraftValidFrom(e.target.value)}
                            />
                            {" · "}
                            <input
                              type="text"
                              className="metadata-edit-input"
                              aria-label="Valide jusqu'à"
                              value={draftValidUntil}
                              onChange={(e) => setDraftValidUntil(e.target.value)}
                            />
                          </>
                        ) : (
                          <>De: {frontmatter.valid_from || "—"} · À: {frontmatter.valid_until || "—"}</>
                        )}
                      </div>
                    </div>
                    <div className="metadata-row">
                      <div className="metadata-label">Dossier proposé</div>
                      <div className="metadata-value">
                        <FolderPathBuilder
                          segments={editing ? draftPathSegments : (frontmatter.proposed_path_segments || [])}
                          optionsByDepth={folderOptions}
                          editable={editing}
                          onChange={setDraftPathSegments}
                        />
                      </div>
                    </div>
                  </>
                )}
                {frontmatter.proposed_item_type === "entity" && (
                  <div className="metadata-row">
                    <div className="metadata-label">Type d'entité</div>
                    <div className="metadata-value">
                      <EntityTypeBadge entityType={frontmatter.entity_type} />
                    </div>
                  </div>
                )}
                {frontmatter.proposed_item_type === "event" && (
                  <div className="metadata-row">
                    <div className="metadata-label">Bornes temporelles</div>
                    <div className="metadata-value">
                      <EventTemporalRange startsAt={frontmatter.starts_at} endsAt={frontmatter.ends_at} />
                    </div>
                  </div>
                )}
                {frontmatter.proposed_item_type === "relationship" && (
                  <>
                    <div className="metadata-row">
                      <div className="metadata-label">Type de relation</div>
                      <div className="metadata-value">{frontmatter.relationship_type}</div>
                    </div>
                    <div className="metadata-row">
                      <div className="metadata-label">Endpoints</div>
                      <div className="metadata-value">
                        <RelationshipEndpoints
                          endpoints={(frontmatter.endpoints || []).map((id) => ({
                            id,
                            label: endpointLabels[id] ?? null,
                          }))}
                        />
                      </div>
                    </div>
                  </>
                )}
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
