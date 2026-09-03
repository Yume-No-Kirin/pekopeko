import { Link } from "react-router-dom";

export default function ModuleCard({ title, description, status, to }) {
  // status="available" only counts as navigable if `to` is actually set - otherwise
  // fall through to the disabled render below rather than badging a dead-end "Disponible".
  const isAvailable = status === "available" && Boolean(to);
  const badge = (
    <span className={`module-badge ${isAvailable ? "available" : "coming-soon"}`}>
      {isAvailable ? "Disponible" : "À venir"}
    </span>
  );

  if (isAvailable) {
    return (
      <Link to={to} className="module-card">
        <div className="module-title">{title}</div>
        <div className="module-description">{description}</div>
        {badge}
      </Link>
    );
  }

  return (
    <div className="module-card disabled">
      <div className="module-title">{title}</div>
      <div className="module-description">{description}</div>
      {badge}
    </div>
  );
}
