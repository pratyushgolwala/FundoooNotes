import React, { useState, useContext } from 'react';
import '../styles/topnavbar.css';
import { AuthContext } from '../../context/AuthContext';
import { FaBars, FaCog, FaSlidersH, FaUserCircle, FaBell } from 'react-icons/fa';

export default function TopNavBar({ onSidebarToggle, searchQuery = '', onSearchChange, onInvitationsClick }) {
  const { logout, userId } = useContext(AuthContext);
  const [showMenu, setShowMenu] = useState(false);

  const handleLogout = () => {
    logout();
  };

  return (
    <header className="top-navbar">
      <div className="navbar-left">
        <button 
          className="navbar-toggle-btn"
          onClick={onSidebarToggle}
          title="Toggle sidebar"
        >
          <FaBars />
        </button>
        <div className="navbar-logo">FundooNotes</div>
        <div className="navbar-search">
          <input
            type="text"
            placeholder="Search notes"
            className="navbar-search-input"
            value={searchQuery}
            onChange={(e) => onSearchChange && onSearchChange(e.target.value)}
          />
        </div>
      </div>

      <div className="navbar-right">
        <button 
          className="navbar-icon-btn" 
          title="Invitations"
          onClick={onInvitationsClick}
        >
          <FaBell />
        </button>
        <button className="navbar-icon-btn" title="Settings"><FaCog /></button>
        <button className="navbar-icon-btn" title="View options"><FaSlidersH /></button>
        <div className="navbar-user-menu">
          <button
            className="navbar-user-avatar"
            onClick={() => setShowMenu(!showMenu)}
            title="Account"
          >
            <FaUserCircle />
          </button>

          {showMenu && (
            <div className="navbar-user-dropdown">
              <div className="navbar-user-info">
                <p>User ID: {userId}</p>
              </div>
              <button className="navbar-logout-btn" onClick={handleLogout}>
                Logout
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
