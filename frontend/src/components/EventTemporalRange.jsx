export default function EventTemporalRange({ startsAt, endsAt }) {
  return (
    <span className="event-temporal-range">
      {startsAt || "non précisé"} → {endsAt || "non précisé"}
    </span>
  );
}
