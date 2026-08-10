import { NavLink } from "react-router-dom";

export function AppHeader() {
  return (
    <header className="appHeader">
      <div className="appHeaderInner">
        <NavLink className="brandMark" to="/compare">
          <span className="brandSquare">B6</span>
          <span className="brandText">
            <strong>Big Six Spending Dashboard</strong>
            <small>Football finance beta</small>
          </span>
        </NavLink>

        <nav className="topNav" aria-label="Primary">
          <NavLink className="topNavLink" to="/compare">
            Compare
          </NavLink>
          <NavLink className="topNavLink" to="/clubs">
            Clubs
          </NavLink>
        </nav>
      </div>
    </header>
  );
}
