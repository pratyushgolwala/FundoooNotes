import React from 'react';
import '../styles/sidebar.css';
import { FaArchive, FaStickyNote, FaTags, FaTrash, FaUsers } from 'react-icons/fa';

export default function Sidebar({ isOpen, currentView, onViewChange, onItemClick }) {
  const menuItems = [
    { id: 'notes', icon: FaStickyNote, label: 'Notes' },
    { id: 'shared', icon: FaUsers, label: 'Shared notes' },
    { id: 'labels', icon: FaTags, label: 'Edit labels' },
    { id: 'archive', icon: FaArchive, label: 'Archive' },
    { id: 'trash', icon: FaTrash, label: 'Trash' },
  ];

  return (
    <nav className={`sidebar ${isOpen ? 'open' : 'closed'}`}>
      <div className="sidebar-menu">
        {menuItems.map((item) => (
          (() => {
            const Icon = item.icon;
            return (
          <button
            key={item.id}
            className={`sidebar-item ${item.id !== 'labels' && currentView === item.id ? 'active' : ''}`}
            onClick={() => {
              onViewChange(item.id);
              if (onItemClick) {
                onItemClick();
              }
            }}
            title={item.label}
          >
            <span className="sidebar-icon"><Icon /></span>
            <span className="sidebar-label">{item.label}</span>
          </button>
            );
          })()
        ))}
      </div>
    </nav>
  );
}
