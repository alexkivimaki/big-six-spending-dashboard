import { useEffect, useState } from "react";
import { Menu, X } from "lucide-react";
import { NavLink, useLocation } from "react-router-dom";

export function AppHeader() {
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);
  const [showMobileHamburger, setShowMobileHamburger] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return undefined;

    const mediaQuery = window.matchMedia("(max-width: 760px)");

    const updateMenuMode = () => {
      const shouldShowHamburger = mediaQuery.matches && window.scrollY > 80;
      setShowMobileHamburger(shouldShowHamburger);
      if (!shouldShowHamburger) {
        setMenuOpen(false);
      }
    };

    updateMenuMode();
    window.addEventListener("scroll", updateMenuMode, { passive: true });
    mediaQuery.addEventListener("change", updateMenuMode);

    return () => {
      window.removeEventListener("scroll", updateMenuMode);
      mediaQuery.removeEventListener("change", updateMenuMode);
    };
  }, []);

  useEffect(() => {
    setMenuOpen(false);
  }, [location.pathname, location.hash]);

  return (
    <header className="appHeader">
      <div className="appHeaderInner">
        <NavLink className="brandMark" to="/compare">
          <span className="brandText brandTextSolo">
            <strong>Football Finance</strong>
          </span>
        </NavLink>

        {!showMobileHamburger ? (
          <nav className="topNav topNavInline" aria-label="Primary">
            <NavLink className="topNavLink" to="/compare">
              Compare Clubs
            </NavLink>
            <NavLink className="topNavLink" to="/clubs">
              Club View
            </NavLink>
          </nav>
        ) : null}
      </div>

      {showMobileHamburger ? (
        <div className="appHeaderFloatingMenu">
          <button
            type="button"
            className="appHeaderMenuButton"
            aria-label={menuOpen ? "Close navigation menu" : "Open navigation menu"}
            aria-expanded={menuOpen}
            aria-controls="primary-navigation"
            onClick={() => setMenuOpen((open) => !open)}
          >
            {menuOpen ? <X size={18} /> : <Menu size={18} />}
          </button>

          {menuOpen ? (
            <nav id="primary-navigation" className="topNav topNavMenu" aria-label="Primary">
              <NavLink className="topNavLink" to="/compare" onClick={() => setMenuOpen(false)}>
                Compare Clubs
              </NavLink>
              <NavLink className="topNavLink" to="/clubs" onClick={() => setMenuOpen(false)}>
                Club View
              </NavLink>
            </nav>
          ) : null}
        </div>
      ) : null}
    </header>
  );
}
