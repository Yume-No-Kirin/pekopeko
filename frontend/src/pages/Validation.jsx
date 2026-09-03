import { Fragment, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listProposals, getProposal, acceptProposal, rejectProposal } from "../api/review.js";
import { listIngestions } from "../api/tasks.js";
import { DOMAINS } from "../api/domains.js";
import { PERIOD_OPTIONS, filterByPeriod } from "../utils/periodFilter.js";
import EpistemicStatusBadge from "../components/EpistemicStatusBadge.jsx";
import SourceGroupHeader from "../components/SourceGroupHeader.jsx";
import RejectReasonModal from "../components/RejectReasonModal.jsx";

const REVIEWER_ID = import.meta.env.VITE_REVIEWER_ID || "cleo";
const NOTES_PER_PAGE = 10;

// Fetches the full PROPOSED/assertion queue for the given domains (stage 1)
// and the originating ingestion tasks' status (stage 3) in parallel - stage
// 3 only depends on `domains`, not on stage 1's result, so there is no
// reason to wait for stage 1 (let alone the stage-2 detail fan-out below)
// before issuing it. Stage 2 (joining each proposal with its full
// ProposalDetail - a failed per-item fetch is dropped, not propagated,
// mirroring review/pipeline.py's list_proposals own "a single malformed
// proposal must not break the whole review queue") genuinely depends on
// stage 1's summaries, so it stays sequential after it. Everything is then
// grouped by provenance.source_id.
async function fetchGroups(domains) {
  const [proposalPages, taskPages] = await Promise.all([
    Promise.all(domains.map((domain) => listProposals(domain, { status: "PROPOSED", limit: 500, offset: 0 }))),
    Promise.all(domains.map((domain) => listIngestions(domain, { limit: 500, offset: 0 }))),
  ]);
  const summaries = proposalPages
    .flatMap((page) => page.items)
    .filter((item) => item.proposed_item_type === "assertion");

  const detailSettlements = await Promise.allSettled(
    summaries.map((summary) => getProposal(summary.domain, summary.id))
  );
  const notes = [];
  detailSettlements.forEach((settlement, i) => {
    if (settlement.status === "fulfilled") {
      notes.push({ ...summaries[i], detail: settlement.value });
    }
  });

  const taskStatusBySourceId = new Map();
  for (const page of taskPages) {
    for (const task of page.items) {
      // API returns each domain's tasks sorted started_at descending
      // (sort_by_recency), so the first task seen per source_id here is
      // always the most recent one - keep it, don't let an older task
      // overwrite it.
      if (task.source_id && !taskStatusBySourceId.has(task.source_id)) {
        taskStatusBySourceId.set(task.source_id, task.status);
      }
    }
  }

  const groupsByKey = new Map();
  for (const note of notes) {
    const sourceId = note.detail.frontmatter.provenance.source_id;
    const key = `${note.domain}:${sourceId}`;
    if (!groupsByKey.has(key)) {
      groupsByKey.set(key, {
        sourceId,
        domain: note.domain,
        originalFilename: note.detail.source_frontmatter.original_filename,
        taskStatus: taskStatusBySourceId.get(sourceId),
        notes: [],
      });
    }
    groupsByKey.get(key).notes.push(note);
  }

  return Array.from(groupsByKey.values());
}

// Packs whole groups into pages targeting ~NOTES_PER_PAGE notes each,
// without ever splitting a group across two pages (an over-sized group
// simply gets its own page).
function packGroupsIntoPages(groups, notesPerPage) {
  const pages = [];
  let current = [];
  let currentCount = 0;
  for (const group of groups) {
    if (currentCount > 0 && currentCount + group.notes.length > notesPerPage) {
      pages.push(current);
      current = [];
      currentCount = 0;
    }
    current.push(group);
    currentCount += group.notes.length;
  }
  if (current.length > 0) pages.push(current);
  return pages;
}

function NoteRow({ note, onAccept, onReject }) {
  return (
    <tr className="note-row">
      <td className="note-content-cell">
        <div className="note-content-display">{note.detail.body}</div>
      </td>
      <td>
        <EpistemicStatusBadge status={note.epistemic_status} />
      </td>
      <td>
        <div className="note-actions">
          <button type="button" className="btn-mini accept" onClick={() => onAccept(note.domain, note.id)}>
            ✓ Accepter
          </button>
          <button type="button" className="btn-mini reject" onClick={() => onReject(note.domain, note.id)}>
            ✕ Rejeter
          </button>
          <Link className="btn-mini detail" to={`/validation/${note.domain}/${note.id}`}>
            Détails
          </Link>
        </div>
      </td>
    </tr>
  );
}

export default function Validation() {
  const [domainFilter, setDomainFilter] = useState("all");
  const [periodFilter, setPeriodFilter] = useState("all");
  const [page, setPage] = useState(0);
  const [refreshKey, setRefreshKey] = useState(0);
  const [groups, setGroups] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionError, setActionError] = useState(null);
  const [rejectTarget, setRejectTarget] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    const domains = domainFilter === "all" ? DOMAINS : [domainFilter];
    fetchGroups(domains)
      .then((result) => {
        if (!cancelled) {
          setGroups(result);
          setPage(0);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err);
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [domainFilter, refreshKey]);

  function updateGroupsAfterRemoval(domain, proposalId) {
    setGroups((current) =>
      current
        .map((group) => {
          if (group.domain !== domain) return group;
          return { ...group, notes: group.notes.filter((note) => note.id !== proposalId) };
        })
        .filter((group) => group.notes.length > 0)
    );
  }

  async function handleAccept(domain, id) {
    setActionError(null);
    try {
      await acceptProposal(domain, id, REVIEWER_ID);
      updateGroupsAfterRemoval(domain, id);
    } catch (err) {
      setActionError(err);
    }
  }

  function handleRejectClick(domain, id) {
    setRejectTarget({ domain, id });
  }

  async function handleRejectConfirm(reason) {
    const target = rejectTarget;
    setRejectTarget(null);
    setActionError(null);
    try {
      await rejectProposal(target.domain, target.id, REVIEWER_ID, reason);
      updateGroupsAfterRemoval(target.domain, target.id);
    } catch (err) {
      setActionError(err);
    }
  }

  function handlePeriodChange(e) {
    setPeriodFilter(e.target.value);
    setPage(0);
  }

  const visibleGroups = groups
    ? groups
        .map((group) => ({ ...group, notes: filterByPeriod(group.notes, periodFilter, (note) => note.created_at) }))
        .filter((group) => group.notes.length > 0)
    : [];

  const pages = packGroupsIntoPages(visibleGroups, NOTES_PER_PAGE);
  // `page` state can outlive the page it points to (e.g. accepting/rejecting
  // the last note on the last page collapses `pages`) - clamp for every
  // read instead of trying to keep `page` itself perfectly in sync, so a
  // stale `page` never renders an out-of-range slice.
  const currentPage = Math.min(page, Math.max(pages.length - 1, 0));
  const currentPageGroups = pages[currentPage] || [];
  const totalNotes = visibleGroups.reduce((sum, g) => sum + g.notes.length, 0);
  const totalSources = visibleGroups.length;
  const notesBeforeCurrentPage = pages
    .slice(0, currentPage)
    .reduce((sum, p) => sum + p.reduce((s, g) => s + g.notes.length, 0), 0);
  const notesOnCurrentPage = currentPageGroups.reduce((s, g) => s + g.notes.length, 0);
  const rangeStart = totalNotes === 0 ? 0 : notesBeforeCurrentPage + 1;
  const rangeEnd = notesBeforeCurrentPage + notesOnCurrentPage;
  const hasNextPage = currentPage < pages.length - 1;

  return (
    <>
      <header className="page-header with-actions">
        <div className="header-left">
          <h1 className="page-title">Validation</h1>
          <p className="page-subtitle">Toutes les notes canoniques proposées, groupées par source</p>
        </div>
        <div className="header-actions">
          <button type="button" className="btn" onClick={() => setRefreshKey((k) => k + 1)}>
            ↻ Rafraîchir
          </button>
        </div>
      </header>

      <div className="content-wrapper">
        {error && (
          <div className="validation-error" role="alert">
            Impossible de charger les propositions : {error.message}
          </div>
        )}

        {actionError && (
          <div className="validation-error" role="alert">
            Action impossible : {actionError.message}
          </div>
        )}

        <div className="filters-bar">
          <div className="filter-group">
            <label className="filter-label" htmlFor="validation-domain-filter">Domaine</label>
            <select
              id="validation-domain-filter"
              className="filter-select"
              value={domainFilter}
              onChange={(e) => setDomainFilter(e.target.value)}
            >
              <option value="all">Tous les domaines</option>
              {DOMAINS.map((domain) => (
                <option key={domain} value={domain}>{domain}</option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label className="filter-label" htmlFor="validation-period-filter">Période</label>
            <select
              id="validation-period-filter"
              className="filter-select"
              value={periodFilter}
              onChange={handlePeriodChange}
            >
              {PERIOD_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
        </div>

        {loading && !groups && <div className="validation-loading">Chargement des propositions…</div>}

        {groups && !error && (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Contenu de la note</th>
                  <th>Type</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {currentPageGroups.length === 0 && (
                  <tr>
                    <td colSpan={3}>
                      <div className="empty-state">
                        <div className="empty-state-title">Aucune proposition</div>
                        <div className="empty-state-text">
                          Aucune note en attente de validation ne correspond à ces filtres.
                        </div>
                      </div>
                    </td>
                  </tr>
                )}
                {currentPageGroups.map((group) => (
                  <Fragment key={`${group.domain}:${group.sourceId}`}>
                    <SourceGroupHeader group={group} columnCount={3} />
                    {group.notes.map((note) => (
                      <NoteRow
                        key={`${note.domain}-${note.id}`}
                        note={note}
                        onAccept={handleAccept}
                        onReject={handleRejectClick}
                      />
                    ))}
                  </Fragment>
                ))}
              </tbody>
            </table>

            <div className="pagination">
              <div className="pagination-info">
                {totalNotes === 0
                  ? "Aucune note"
                  : `Affichage ${rangeStart}-${rangeEnd} notes sur ${totalNotes} notes · ${totalSources} sources`}
              </div>
              <div className="pagination-controls">
                <button
                  type="button"
                  className="pagination-btn"
                  disabled={currentPage === 0}
                  onClick={() => setPage(currentPage - 1)}
                >
                  ← Précédent
                </button>
                <button
                  type="button"
                  className="pagination-btn"
                  disabled={!hasNextPage}
                  onClick={() => setPage(currentPage + 1)}
                >
                  Suivant →
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      <RejectReasonModal
        open={rejectTarget !== null}
        onCancel={() => setRejectTarget(null)}
        onConfirm={handleRejectConfirm}
      />
    </>
  );
}
