const BASELINE_FIELDS = [
  ["source_id", "ID Source"],
  ["extraction_provider", "Provider LLM"],
];

// TASK-001a additions - null/absent on a Proposal ingested before that
// ticket landed, so each row renders only when its own field is present
// (field-by-field, not all-or-nothing).
const OPTIONAL_FIELDS = [
  ["provider_model", "Modèle"],
  ["provider_temperature", "Température"],
  ["extraction_id", "Extraction ID"],
  ["extraction_duration_seconds", "Durée extraction"],
];

export default function ProvenanceSection({ provenance }) {
  return (
    <div className="section-card">
      <div className="section-header">
        <h2 className="card-section-title">Provenance & Extraction</h2>
      </div>
      <div className="section-content">
        <div className="metadata-table">
          {BASELINE_FIELDS.map(([field, label]) => (
            <div className="metadata-row" key={field}>
              <div className="metadata-label">{label}</div>
              <div className="metadata-value">{provenance[field]}</div>
            </div>
          ))}
          {OPTIONAL_FIELDS.map(([field, label]) =>
            provenance[field] === null || provenance[field] === undefined ? null : (
              <div className="metadata-row" key={field}>
                <div className="metadata-label">{label}</div>
                <div className="metadata-value">{provenance[field]}</div>
              </div>
            )
          )}
        </div>
      </div>
    </div>
  );
}
