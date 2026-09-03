function formatTimestamp(iso) {
  return iso ? iso.replace("T", " ").slice(0, 16) : "—";
}

// Generic over ingestion/extraction TaskEvent shape (TASK-001b) - reused
// verbatim by TASK-011's proposal detail log section.
export default function TaskEventLog({ events }) {
  if (!events || events.length === 0) {
    return <p className="task-event-log-empty">Aucun événement enregistré.</p>;
  }

  return (
    <ul className="task-event-log">
      {events.map((event, index) => (
        <li key={index} className="task-event">
          <span className="task-event-timestamp">{formatTimestamp(event.timestamp)}</span>
          <span className={`task-event-level ${event.level}`}>{event.level}</span>
          <span className="task-event-message">{event.message}</span>
          {event.details && (
            <span className="task-event-details">{JSON.stringify(event.details)}</span>
          )}
        </li>
      ))}
    </ul>
  );
}
