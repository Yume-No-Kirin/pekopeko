export const EPISTEMIC_STATUS_LABELS = {
  direct: "Direct",
  inferred: "Inféré",
  uncertain: "Incertain",
  contested: "Contesté",
};

export default function EpistemicStatusBadge({ status }) {
  return <span className={`epistemic-badge ${status}`}>{EPISTEMIC_STATUS_LABELS[status] || status}</span>;
}
