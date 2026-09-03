import { NavLink } from "react-router-dom";

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-logo">Pekopeko</div>
      </div>

      <nav className="sidebar-nav">
        <div className="nav-section">
          <div className="nav-section-title">Principal</div>
          <NavLink
            to="/"
            end
            className={({ isActive }) => `nav-item${isActive ? " active" : ""}`}
          >
            Dashboard
          </NavLink>
        </div>

        <div className="nav-section">
          <div className="nav-section-title">Modules actifs</div>
          <NavLink
            to="/settings"
            className={({ isActive }) => `nav-item${isActive ? " active" : ""}`}
          >
            Settings
          </NavLink>
          <NavLink
            to="/ingestion-logs"
            className={({ isActive }) => `nav-item${isActive ? " active" : ""}`}
          >
            Logs ingestion
          </NavLink>
          <NavLink
            to="/validation"
            className={({ isActive }) => `nav-item${isActive ? " active" : ""}`}
          >
            Validation
          </NavLink>
        </div>

        <div className="nav-section">
          <div className="nav-section-title">Modules à venir</div>
          <span className="nav-item disabled">Analytics</span>
          <span className="nav-item disabled">Export</span>
        </div>
      </nav>
    </aside>
  );
}
