import { Bell, FileText, History, Settings, Stethoscope } from 'lucide-react';
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
          <History size={16} />
          <span>My Health History</span>
        </NavLink>
        <NavLink
          to="/analyze"
          className={({ isActive }) => `navbar__link ${isActive ? 'is-active' : ''}`}
        >
          <Stethoscope size={16} />
          <span>Analyse Symptoms</span>
        </NavLink>
        <NavLink
          to="/reports"
          className={({ isActive }) => `navbar__link ${isActive ? 'is-active' : ''}`}
        >
          <FileText size={16} />
          <span>Reports</span>
        </NavLink>
      </nav>

      <div className="navbar__actions">
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