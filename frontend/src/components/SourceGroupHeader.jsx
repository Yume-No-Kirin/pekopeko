import TaskStatusBadge from "./TaskStatusBadge.jsx";

// No accept-all/reject-all here - bulk actions are a pre-existing deferral
// (TASK-015), not a cut made by this screen.
export default function SourceGroupHeader({ group, columnCount }) {
  return (
    <tr className="source-header-row">
      <td colSpan={columnCount}>
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
    </tr>
  );
}
