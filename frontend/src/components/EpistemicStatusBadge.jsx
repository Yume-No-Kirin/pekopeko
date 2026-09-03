const LABELS = {
  direct: "Direct",
  inferred: "Inféré",
  uncertain: "Incertain",
  contested: "Contesté",
};

export default function EpistemicStatusBadge({ status }) {
  return <span className={`epistemic-badge ${status}`}>{LABELS[status] || status}</span>;
}
