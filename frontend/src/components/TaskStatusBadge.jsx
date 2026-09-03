const LABELS = {
  pending: "En attente",
  running: "En cours",
  completed: "Complété",
  failed: "Échoué",
  skipped_duplicate: "Doublon",
};

export default function TaskStatusBadge({ status }) {
  return <span className={`status-badge ${status}`}>{LABELS[status] || status}</span>;
}
