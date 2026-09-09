import { Fragment, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  listProposals,
  getProposal,
  acceptProposal,
  rejectProposal,
  editProposal,
  listOrganizationFolders,
  acceptProposalsBatch,
  rejectProposalsBatch,
} from "../api/review.js";
import { listIngestions } from "../api/tasks.js";
import { DOMAINS } from "../api/domains.js";
import { PERIOD_OPTIONS, filterByPeriod } from "../utils/periodFilter.js";
import EpistemicStatusBadge, { EPISTEMIC_STATUS_LABELS } from "../components/EpistemicStatusBadge.jsx";
import SourceGroupHeader from "../components/SourceGroupHeader.jsx";
import RejectReasonModal from "../components/RejectReasonModal.jsx";
import FolderPathBuilder from "../components/FolderPathBuilder.jsx";
import ContextValue from "../components/ContextValue.jsx";
import EntityTypeBadge from "../components/EntityTypeBadge.jsx";
import EventTemporalRange from "../components/EventTemporalRange.jsx";
import RelationshipEndpoints from "../components/RelationshipEndpoints.jsx";

const REVIEWER_ID = import.meta.env.VITE_REVIEWER_ID || "cleo";
const NOTES_PER_PAGE = 10;

const PROPOSED_ITEM_TYPE_OPTIONS = [
  { value: "all", label: "Tous" },
  { value: "assertion", label: "Assertion" },
  { value: "entity", label: "Entité" },
  { value: "event", label: "Événement" },
  { value: "relationship", label: "Relation" },
];

const EPISTEMIC_STATUS_OPTIONS = [
  { value: "all", label: "Tous" },
  ...Object.entries(EPISTEMIC_STATUS_LABELS).map(([value, label]) => ({ value, label })),
];

const SORT_OPTIONS = [
  { value: "recent", label: "Plus récent d'abord" },
  { value: "oldest", label: "Plus ancien d'abord" },
];

// Most recent created_at across a group's (already filtered) notes - the
// sort control's own comparison key. -Infinity for an empty group so it
// never crashes Math.max (packGroupsIntoPages/visibleGroups always drop
// empty groups before this would matter, but keeping the helper total).
function groupMostRecentCreatedAt(group) {
  return group.notes.reduce((max, note) => Math.max(max, new Date(note.created_at).getTime()), -Infinity);
}

// Resolves a relationship endpoint id to a display label using only detail
// data already fetched for other reasons (no new backend read endpoint,
// TASK-012's explicit V1 scope decision): an id not present in `detailsById`
// (not in the current PROPOSED/EDITED queue - already canonical, or outside
// this view) resolves to `null`, rendered as a plain id by
// RelationshipEndpoints.
function resolveEndpointLabel(id, detailsById) {
  const detail = detailsById.get(id);
  if (!detail) return null;
  const excerpt = (detail.body || "").slice(0, 60);
  return `${detail.frontmatter.proposed_item_type}: ${excerpt}`;
}

// Fetches the full PROPOSED/EDITED queue for the given domains (stage 1,
// all 4 proposed_item_types since TASK-012) and the originating ingestion
// tasks' status (stage 3) in parallel - stage 3 only depends on `domains`,
// not on stage 1's result, so there is no reason to wait for stage 1 (let
// alone the stage-2 detail fan-out below) before issuing it. Stage 2
// (joining each proposal with its full ProposalDetail - a failed per-item
// fetch is dropped, not propagated, mirroring review/pipeline.py's
// list_proposals own "a single malformed proposal must not break the whole
// review queue") genuinely depends on stage 1's summaries, so it stays
// sequential after it. Everything is then grouped by provenance.source_id.
// The same stage-2 details also become `detailsById`, reused (TASK-012) to
// resolve relationship endpoint labels without any extra fetch.
async function fetchGroups(domains) {
  const [proposedPages, editedPages, taskPages] = await Promise.all([
    Promise.all(domains.map((domain) => listProposals(domain, { status: "PROPOSED", limit: 500, offset: 0 }))),
    Promise.all(domains.map((domain) => listProposals(domain, { status: "EDITED", limit: 500, offset: 0 }))),
    Promise.all(domains.map((domain) => listIngestions(domain, { limit: 500, offset: 0 }))),
  ]);
  const summaries = [...proposedPages, ...editedPages].flatMap((page) => page.items);

  const detailSettlements = await Promise.allSettled(
    summaries.map((summary) => getProposal(summary.domain, summary.id))
  );
  const notes = [];
  const detailsById = new Map();
  detailSettlements.forEach((settlement, i) => {
    if (settlement.status === "fulfilled") {
      notes.push({ ...summaries[i], detail: settlement.value });
      detailsById.set(summaries[i].id, settlement.value);
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

  return { groups: Array.from(groupsByKey.values()), detailsById };
}

const ORGANIZATION_ITEM_TYPES = ["assertion", "entity", "event", "relationship"];

// Four organization-folders fetches per visible domain, one per proposed_item_type
// (TASK-005a: ADI-012 adoption widens this beyond assertion-only) - each
// (domain, itemType) pair degrades independently to no suggested options on
// failure, rather than blocking the table, same non-blocking-satellite posture as
// the rest of this fetch. Result is keyed by domain, then by item type.
async function fetchFolderOptionsByDomain(domains) {
  const entries = await Promise.all(
    domains.map(async (domain) => {
      const byType = await Promise.all(
        ORGANIZATION_ITEM_TYPES.map((itemType) =>
          listOrganizationFolders(domain, itemType)
            .then((result) => [itemType, result.segments_by_depth || []])
            .catch(() => [itemType, []])
        )
      );
      return [domain, Object.fromEntries(byType)];
    })
  );
  return Object.fromEntries(entries);
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

function NoteRow({ note, folderOptions, detailsById, onAccept, onReject, onPathChange }) {
  const itemType = note.detail.frontmatter.proposed_item_type;
  const resolvedEndpoints =
    itemType === "relationship"
      ? (note.detail.frontmatter.endpoints || []).map((id) => ({
          id,
          label: resolveEndpointLabel(id, detailsById),
        }))
      : [];

  return (
    <tr className="note-row">
      <td className="note-content-cell">
        <div className="note-content-display">{note.detail.body}</div>
      </td>
      <td>
        <EpistemicStatusBadge status={note.epistemic_status} />
        {itemType === "entity" && <EntityTypeBadge entityType={note.detail.frontmatter.entity_type} />}
        {itemType === "event" && (
          <EventTemporalRange
            startsAt={note.detail.frontmatter.starts_at}
            endsAt={note.detail.frontmatter.ends_at}
          />
        )}
        {itemType === "relationship" && <RelationshipEndpoints endpoints={resolvedEndpoints} />}
      </td>
      <td className="folder-cell">
        <FolderPathBuilder
          editable={true}
          segments={note.detail.frontmatter.proposed_path_segments || []}
          optionsByDepth={(folderOptions && folderOptions[itemType]) || []}
          onChange={(segments) => onPathChange(note.domain, note.id, segments)}
        />
      </td>
      <td>
        <ContextValue value={note.detail.frontmatter.context} />
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
  const [typeFilter, setTypeFilter] = useState("all");
  const [epistemicFilter, setEpistemicFilter] = useState("all");
  const [sortOrder, setSortOrder] = useState("recent");
  const [page, setPage] = useState(0);
  const [refreshKey, setRefreshKey] = useState(0);
  const [groups, setGroups] = useState(null);
  const [detailsById, setDetailsById] = useState(new Map());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionError, setActionError] = useState(null);
  const [rejectTarget, setRejectTarget] = useState(null);
  const [folderOptionsByDomain, setFolderOptionsByDomain] = useState({});

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    const domains = domainFilter === "all" ? DOMAINS : [domainFilter];
    fetchGroups(domains)
      .then((result) => {
        if (!cancelled) {
          setGroups(result.groups);
          setDetailsById(result.detailsById);
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
    fetchFolderOptionsByDomain(domains).then((result) => {
      if (!cancelled) setFolderOptionsByDomain(result);
    });
    return () => {
      cancelled = true;
    };
  }, [domainFilter, refreshKey]);

  function updateGroupsAfterRemoval(domain, proposalIds) {
    const idsToRemove = new Set(Array.isArray(proposalIds) ? proposalIds : [proposalIds]);
    setGroups((current) =>
      current
        .map((group) => {
          if (group.domain !== domain) return group;
          return { ...group, notes: group.notes.filter((note) => !idsToRemove.has(note.id)) };
        })
        .filter((group) => group.notes.length > 0)
    );
  }

  // Shared by handleAcceptAll and handleRejectConfirm (batch endpoints - see
  // api/review.js's acceptProposalsBatch/rejectProposalsBatch): removes every
  // non-"failed" result's note from state, and - if at least one item failed
  // - surfaces a dedicated banner listing one message per failure rather than
  // silently dropping it (TASK-015 item 11). This actionError shape
  // ({batch: true, ...}) is distinct from the plain Error object the
  // non-batch action handlers below set, so the render below can branch on it.
  function applyBatchResponse(domain, response) {
    const succeededIds = response.results.filter((r) => r.status !== "failed").map((r) => r.proposal_id);
    if (succeededIds.length > 0) updateGroupsAfterRemoval(domain, succeededIds);

    const failures = response.results.filter((r) => r.status === "failed");
    setActionError(
      failures.length > 0
        ? { batch: true, succeededCount: response.succeeded_count, failedCount: response.failed_count, failures }
        : null
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

  async function handleAcceptAll(domain, ids) {
    setActionError(null);
    try {
      const response = await acceptProposalsBatch(domain, ids, REVIEWER_ID);
      applyBatchResponse(domain, response);
    } catch (err) {
      setActionError(err);
    }
  }

  function setNotePathSegments(domain, proposalId, segments) {
    setGroups((current) =>
      current.map((group) => {
        if (group.domain !== domain) return group;
        return {
          ...group,
          notes: group.notes.map((note) =>
            note.id === proposalId
              ? { ...note, detail: { ...note.detail, frontmatter: { ...note.detail.frontmatter, proposed_path_segments: segments } } }
              : note
          ),
        };
      })
    );
  }

  async function handlePathChange(domain, id, newSegments) {
    const note = groups.flatMap((g) => g.notes).find((n) => n.domain === domain && n.id === id);
    const previousSegments = note ? note.detail.frontmatter.proposed_path_segments || [] : [];
    setActionError(null);
    setNotePathSegments(domain, id, newSegments);
    try {
      await editProposal(domain, id, REVIEWER_ID, { fieldUpdates: { proposed_path_segments: newSegments } });
    } catch (err) {
      setNotePathSegments(domain, id, previousSegments);
      setActionError(err);
    }
  }

  // rejectTarget is {domain, ids} for both paths: a single-note reject
  // (ids: [id]) and a group-level "Tout rejeter" (ids: the group's full
  // visible id list) - both share the one RejectReasonModal/handler below,
  // generalized onto the batch endpoint (TASK-015 item 10).
  function handleRejectClick(domain, id) {
    setRejectTarget({ domain, ids: [id] });
  }

  function handleRejectAllClick(domain, ids) {
    setRejectTarget({ domain, ids });
  }

  async function handleRejectConfirm(reason) {
    const target = rejectTarget;
    setRejectTarget(null);
    setActionError(null);
    try {
      const response = await rejectProposalsBatch(target.domain, target.ids, REVIEWER_ID, reason);
      applyBatchResponse(target.domain, response);
    } catch (err) {
      setActionError(err);
    }
  }

  function handlePeriodChange(e) {
    setPeriodFilter(e.target.value);
    setPage(0);
  }

  function handleTypeFilterChange(e) {
    setTypeFilter(e.target.value);
    setPage(0);
  }

  function handleEpistemicFilterChange(e) {
    setEpistemicFilter(e.target.value);
    setPage(0);
  }

  function handleSortOrderChange(e) {
    setSortOrder(e.target.value);
    setPage(0);
  }

  const visibleGroups = groups
    ? groups
        .map((group) => ({
          ...group,
          notes: filterByPeriod(group.notes, periodFilter, (note) => note.created_at)
            .filter((note) => typeFilter === "all" || note.detail.frontmatter.proposed_item_type === typeFilter)
            .filter((note) => epistemicFilter === "all" || note.epistemic_status === epistemicFilter),
        }))
        .filter((group) => group.notes.length > 0)
        .sort((a, b) => {
          const diff = groupMostRecentCreatedAt(b) - groupMostRecentCreatedAt(a);
          return sortOrder === "recent" ? diff : -diff;
        })
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

        {actionError && actionError.batch && (
          <div className="validation-error" role="alert">
            <div>
              {`${actionError.succeededCount}/${actionError.succeededCount + actionError.failedCount} notes traitées, ${actionError.failedCount} échouée(s) :`}
            </div>
            <ul>
              {actionError.failures.map((failure) => (
                <li key={failure.proposal_id}>{`${failure.proposal_id} — ${failure.error.message}`}</li>
              ))}
            </ul>
          </div>
        )}

        {actionError && !actionError.batch && (
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

          <div className="filter-group">
            <label className="filter-label" htmlFor="validation-type-filter">Type de proposition</label>
            <select
              id="validation-type-filter"
              className="filter-select"
              value={typeFilter}
              onChange={handleTypeFilterChange}
            >
              {PROPOSED_ITEM_TYPE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label className="filter-label" htmlFor="validation-epistemic-filter">Statut épistémique</label>
            <select
              id="validation-epistemic-filter"
              className="filter-select"
              value={epistemicFilter}
              onChange={handleEpistemicFilterChange}
            >
              {EPISTEMIC_STATUS_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label className="filter-label" htmlFor="validation-sort-order">Tri</label>
            <select
              id="validation-sort-order"
              className="filter-select"
              value={sortOrder}
              onChange={handleSortOrderChange}
            >
              {SORT_OPTIONS.map((opt) => (
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
                  <th>Dossier proposé</th>
                  <th>Contexte</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {currentPageGroups.length === 0 && (
                  <tr>
                    <td colSpan={5}>
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
                    <SourceGroupHeader
                      group={group}
                      columnCount={5}
                      onAcceptAll={handleAcceptAll}
                      onRejectAll={handleRejectAllClick}
                    />
                    {group.notes.map((note) => (
                      <NoteRow
                        key={`${note.domain}-${note.id}`}
                        note={note}
                        folderOptions={folderOptionsByDomain[note.domain]}
                        detailsById={detailsById}
                        onAccept={handleAccept}
                        onReject={handleRejectClick}
                        onPathChange={handlePathChange}
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
