export default function ContextValue({ value }) {
  return <span className="context-value">{value || "—"}</span>;
}
