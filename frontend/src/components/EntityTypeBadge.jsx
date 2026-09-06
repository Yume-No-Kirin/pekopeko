export default function EntityTypeBadge({ entityType }) {
  return (
    <span className={`entity-type-badge ${entityType || "unknown"}`}>
      {entityType || "non précisé"}
    </span>
  );
}
