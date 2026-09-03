import { Fragment, useEffect, useRef, useState } from "react";
import { listIngestions, listExtractions } from "../api/tasks.js";
import { DOMAINS } from "../api/domains.js";
import { PERIOD_OPTIONS, filterByPeriod } from "../utils/periodFilter.js";
import TaskStatusBadge from "../components/TaskStatusBadge.jsx";
import TaskEventLog from "../components/TaskEventLog.jsx";

const PAGE_SIZE = 10;

const STATUS_OPTIONS = [
  { value: "all", label: "Tous les statuts" },
  { value: "pending", label: "En attente" },
  { value: "running", label: "En cours" },
  { value: "completed", label: "Complété" },
  { value: "failed", label: "Échoué" },
  { value: "skipped_duplicate", label: "Doublon ignoré" },
];

function basename(path) {
  return path ? path.split(/[\\/]/).pop() : "";
}

function formatTimestamp(iso) {
  return iso ? iso.replace("T", " ").slice(0, 16) : "—";
}

function actionLabel(status) {
  if (status === "failed") return "Voir erreur";
  if (status === "skipped_duplicate") return "Voir original";
  return "Voir logs";
}

// Pagination strategy (per TASK-009): server-paginates each of the up to 10
// domain/type sources independently, then merges and re-sorts client-side -
// real server-side pagination per request, composed across the fixed
// 5-domain/2-type fan-out rather than one unbounded fetch sliced
// client-side.
//
// A naive version of this (re-requesting offset = page * PAGE_SIZE from
// every source on every page) drops items: whichever source loses the
// global sort-and-truncate on one page never gets a chance to surface its
// unfetched items on a later page, since its per-page offset keeps
// advancing regardless of what was actually shown. Instead, `pool` (keyed
// by domain:taskType) accumulates every item ever fetched for the current
// filters, and `ensurePoolDepth` only asks each source for enough items to
// guarantee the true top `requiredCount` across all sources is present in
// the pool - a source's rank inside its own list can never exceed its rank
// in the global merge, so once every source has contributed its own top
// `requiredCount` (or is exhausted), the global top `requiredCount` is
// provably complete. Nothing already fetched is ever discarded, so paging
// back and forth is also free of re-fetches.
async function ensurePoolDepth(pool, domains, status, requiredCount) {
  const fetches = [];
  for (const domain of domains) {
    for (const taskType of ["ingestion", "extraction"]) {
      const key = `${domain}:${taskType}`;
      const entry = pool.get(key) || { items: [], total: 0, exhausted: false };
      pool.set(key, entry);
      if (entry.exhausted || entry.items.length >= requiredCount) continue;

      const offset = entry.items.length;
      const limit = requiredCount - entry.items.length;
      const listFn = taskType === "ingestion" ? listIngestions : listExtractions;
      fetches.push(
        listFn(domain, { status, limit, offset }).then((r) => {
          entry.items = entry.items.concat(r.items.map((item) => ({ ...item, taskType })));
          entry.total = r.total;
          entry.exhausted = entry.items.length >= r.total;
        })
      );
    }
  }
  await Promise.all(fetches);
}

function mergedFromPool(pool) {
  const all = [];
  let total = 0;
  for (const entry of pool.values()) {
    all.push(...entry.items);
    total += entry.total;
  }
  all.sort((a, b) => (a.started_at < b.started_at ? 1 : a.started_at > b.started_at ? -1 : 0));
  return { all, total };
}

function TaskRow({ task, expanded, onToggle }) {
  return (
    <Fragment>
      <tr>
        <td>
          <div className="file-name">{basename(task.source_path)}</div>
          <div className="source-id">{task.source_id || "—"}</div>
        </td>
        <td>
          <span className="domain-badge">{task.domain}</span>
        </td>
        <td>
          <span className="task-type-badge">{task.taskType}</span>
        </td>
        <td>
          <TaskStatusBadge status={task.status} />
        </td>
        <td>{formatTimestamp(task.started_at)}</td>
        <td>{formatTimestamp(task.completed_at)}</td>
        <td>{task.proposal_ids.length}</td>
        <td>
          <a href="#" className="action-link" onClick={(e) => { e.preventDefault(); onToggle(task.task_id); }}>
            {actionLabel(task.status)}
          </a>
        </td>
      </tr>
      {expanded && (
        <tr>
          <td colSpan={8}>
            {task.status === "failed" && (
              <p className="task-error">Erreur : {task.error}</p>
            )}
            <TaskEventLog events={task.events} />
          </td>
        </tr>
      )}
    </Fragment>
  );
}

export default function IngestionLogs() {
  const [page, setPage] = useState(0);
  const [statusFilter, setStatusFilter] = useState("all");
  const [domainFilter, setDomainFilter] = useState("all");
  const [periodFilter, setPeriodFilter] = useState("all");
  const [refreshKey, setRefreshKey] = useState(0);
  const [expandedTaskId, setExpandedTaskId] = useState(null);
  const [pageData, setPageData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const poolRef = useRef(new Map());

  // A new set of filters invalidates every source's accumulated pool - a
  // page change alone does not, it only needs the pool deepened further.
  useEffect(() => {
    poolRef.current = new Map();
  }, [statusFilter, domainFilter, refreshKey]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    const domains = domainFilter === "all" ? DOMAINS : [domainFilter];
    const status = statusFilter === "all" ? undefined : statusFilter;
    const requiredCount = (page + 1) * PAGE_SIZE;
    ensurePoolDepth(poolRef.current, domains, status, requiredCount)
      .then(() => {
        if (cancelled) return;
        const { all, total } = mergedFromPool(poolRef.current);
        setPageData({ items: all.slice(page * PAGE_SIZE, requiredCount), total });
        setLoading(false);
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
  }, [page, statusFilter, domainFilter, refreshKey]);

  function handleStatusChange(e) {
    setStatusFilter(e.target.value);
    setPage(0);
  }

  function handleDomainChange(e) {
    setDomainFilter(e.target.value);
    setPage(0);
  }

  function handleToggleRow(taskId) {
    setExpandedTaskId((current) => (current === taskId ? null : taskId));
  }

  const items = pageData ? pageData.items : [];
  const total = pageData ? pageData.total : 0;
  const displayedItems = filterByPeriod(items, periodFilter, (item) => item.started_at);

  const rangeStart = total === 0 ? 0 : page * PAGE_SIZE + 1;
  const rangeEnd = Math.min((page + 1) * PAGE_SIZE, total);
  const hasNextPage = (page + 1) * PAGE_SIZE < total;

  return (
    <>
      <header className="page-header with-actions">
        <div className="header-left">
          <h1 className="page-title">Ingestion de données</h1>
          <p className="page-subtitle">Suivi des tâches d'ingestion et logs détaillés</p>
        </div>
        <div className="header-actions">
          <button type="button" className="btn" onClick={() => setRefreshKey((k) => k + 1)}>
            ↻ Rafraîchir
          </button>
        </div>
      </header>

      <div className="content-wrapper">
        {error && (
          <div className="ingestion-logs-error" role="alert">
            Impossible de charger les tâches : {error.message}
          </div>
        )}

        <div className="filters-bar">
          <div className="filter-group">
            <label className="filter-label" htmlFor="ingestion-status-filter">Statut</label>
            <select
              id="ingestion-status-filter"
              className="filter-select"
              value={statusFilter}
              onChange={handleStatusChange}
            >
              {STATUS_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label className="filter-label" htmlFor="ingestion-domain-filter">Domaine</label>
            <select
              id="ingestion-domain-filter"
              className="filter-select"
              value={domainFilter}
              onChange={handleDomainChange}
            >
              <option value="all">Tous les domaines</option>
              {DOMAINS.map((domain) => (
                <option key={domain} value={domain}>{domain}</option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label className="filter-label" htmlFor="ingestion-period-filter">Période</label>
            <select
              id="ingestion-period-filter"
              className="filter-select"
              value={periodFilter}
              onChange={(e) => setPeriodFilter(e.target.value)}
            >
              {PERIOD_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
        </div>

        {loading && !pageData && <div className="ingestion-logs-loading">Chargement des tâches…</div>}

        {pageData && !error && (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Source</th>
                  <th>Domaine</th>
                  <th>Type</th>
                  <th>Statut</th>
                  <th>Démarré</th>
                  <th>Complété</th>
                  <th>Propositions</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {displayedItems.length === 0 && (
                  <tr>
                    <td colSpan={8}>
                      <div className="empty-state">
                        <div className="empty-state-title">Aucune tâche</div>
                        <div className="empty-state-text">
                          Aucune tâche d'ingestion ou d'extraction ne correspond à ces filtres.
                        </div>
                      </div>
                    </td>
                  </tr>
                )}
                {displayedItems.map((task) => (
                  <TaskRow
                    key={`${task.taskType}-${task.task_id}`}
                    task={task}
                    expanded={expandedTaskId === task.task_id}
                    onToggle={handleToggleRow}
                  />
                ))}
              </tbody>
            </table>

            <div className="pagination">
              <div className="pagination-info">
                {total === 0 ? "Aucune tâche" : `Affichage ${rangeStart}-${rangeEnd} sur ${total}`}
              </div>
              <div className="pagination-controls">
                <button
                  type="button"
                  className="pagination-btn"
                  disabled={page === 0}
                  onClick={() => setPage((p) => p - 1)}
                >
                  ← Précédent
                </button>
                <button
                  type="button"
                  className="pagination-btn"
                  disabled={!hasNextPage}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Suivant →
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
