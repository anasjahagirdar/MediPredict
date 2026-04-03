import { Bell, Settings } from 'lucide-react';
import { useEffect, useMemo, useRef, useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';

import { useAuth } from '../context/AuthContext';
import '../styles/Navbar.css';


function Navbar() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    function handleOutsideClick(event) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target)
      ) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleOutsideClick);
    return () => {
      document.removeEventListener('mousedown', handleOutsideClick);
    };
  }, []);

  const initials = useMemo(() => {
    const first = user?.first_name?.[0] || user?.username?.[0] || 'M';
    const last = user?.last_name?.[0] || user?.username?.[1] || 'P';
    return `${first}${last}`.toUpperCase();
  }, [user]);

  const handleLogout = async () => {
    await logout();
    navigate('/login', { replace: true });
  };

  return (
    <header className="navbar">
      <div className="navbar__brand">MediPredict</div>

      <nav className="navbar__links">
        <NavLink
          to="/dashboard"
          className={({ isActive }) => `navbar__link ${isActive ? 'is-active' : ''}`}
        >
          My Health History
        </NavLink>
        <NavLink
          to="/analyze"
          className={({ isActive }) => `navbar__link ${isActive ? 'is-active' : ''}`}
        >
          Analyse Symptoms
        </NavLink>
      </nav>

      <div className="navbar__actions">
        <button className="navbar__icon-button" type="button" aria-label="Settings">
          <Settings size={18} />
        </button>
        <button className="navbar__icon-button" type="button" aria-label="Notifications">
          <Bell size={18} />
        </button>
        <div className="navbar__avatar-wrap" ref={dropdownRef}>
          <button
            className="navbar__avatar"
            type="button"
            onClick={() => setIsOpen((current) => !current)}
          >
            {initials}
          </button>
          {isOpen && (
            <div className="navbar__dropdown">
              <button type="button" onClick={handleLogout}>
                Sign Out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}


export default Navbar;
