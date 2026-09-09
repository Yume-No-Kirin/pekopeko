import TaskStatusBadge from "./TaskStatusBadge.jsx";

// TASK-015: per-source-group bulk accept/reject, mirroring the maquette's
// .source-actions cell. `group.notes` is already the post-filter,
// post-pagination-page set (Validation.jsx's visibleGroups), so its ids are
// exactly what a bulk action for this group should act on - no separate
// "all ids" source needed.
export default function SourceGroupHeader({ group, columnCount, onAcceptAll, onRejectAll }) {
  const ids = group.notes.map((note) => note.id);

  return (
    <tr className="source-header-row">
      <td colSpan={columnCount - 1}>
        <div className="source-name">
          <div>
            <div className="source-file">📄 {group.originalFilename || group.sourceId}</div>
            <div className="source-id">{group.sourceId}</div>
          </div>
          <div className="source-meta">
            <span className="domain-badge">{group.domain}</span>
            {group.taskStatus && <TaskStatusBadge status={group.taskStatus} />}
            <span className="source-count">{group.notes.length} notes proposées</span>
          </div>
        </div>
      </td>
      <td>
        <div className="source-actions">
          <button type="button" className="btn-small accept-all" onClick={() => onAcceptAll(group.domain, ids)}>
            ✓ Tout accepter
          </button>
          <button type="button" className="btn-small reject-all" onClick={() => onRejectAll(group.domain, ids)}>
            ✕ Tout rejeter
          </button>
        </div>
      </td>
    </tr>
  );
}
