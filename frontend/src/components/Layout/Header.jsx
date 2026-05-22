import React, { useState, useContext } from 'react';
import '../styles/layout.css';
import { AuthContext } from '../../context/AuthContext';
import { FaBars, FaCog, FaSlidersH, FaUserCircle } from 'react-icons/fa';

export default function Header({ isOpen, setIsOpen }) {
  const { logout, userId } = useContext(AuthContext);
  const [showMenu, setShowMenu] = useState(false);

  const handleLogout = () => {
    logout();
  };

  return (
    <header className="app-header">
      <div className="header-left">
        <button 
          className="sidebar-toggle-btn"
          onClick={() => setIsOpen(!isOpen)}
          title={isOpen ? 'Close sidebar' : 'Open sidebar'}
        >
          <FaBars />
        </button>
        <div className="app-logo">Keep</div>
        <div className="search-bar">
          <input
            type="text"
            placeholder="Search notes"
            className="search-input"
          />
        </div>
      </div>

      <div className="header-right">
        <button className="header-icon-btn" title="Settings"><FaCog /></button>
        <button className="header-icon-btn" title="View options"><FaSlidersH /></button>
        <div className="user-menu">
          <button
            className="user-avatar"
            onClick={() => setShowMenu(!showMenu)}
            title="Account"
          >
            <FaUserCircle />
          </button>

          {showMenu && (
            <div className="user-dropdown">
              <div className="user-info">
                <p>User ID: {userId}</p>
              </div>
              <button className="logout-btn" onClick={handleLogout}>
                Logout
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
