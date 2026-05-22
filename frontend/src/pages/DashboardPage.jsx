import React, { useState } from 'react';
import TopNavBar from '../components/Layout/TopNavBar';
import Sidebar from '../components/Layout/Sidebar';
import NotesList from '../components/Notes/NotesList';
import EditLabelsModal from '../components/Layout/EditLabelsModal';
import PendingInvitationsModal from '../components/Notes/PendingInvitationsModal';
import '../styles/dashboard.css';

export default function DashboardPage() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarHovered, setSidebarHovered] = useState(false);
  const [showLabelsModal, setShowLabelsModal] = useState(false);
  const [showInvitationsModal, setShowInvitationsModal] = useState(false);
  const [labelsVersion, setLabelsVersion] = useState(0);
  const [notesVersion, setNotesVersion] = useState(0);
  const [currentView, setCurrentView] = useState(
    sessionStorage.getItem('fundoo_current_view') || 'notes'
  ); // 'notes', 'archive', 'trash', 'labels'
  const [searchQuery, setSearchQuery] = useState(
    sessionStorage.getItem('fundoo_search_query') || ''
  );

  const handleSidebarToggle = () => {
    setSidebarOpen(!sidebarOpen);
  };

  const handleViewChange = (view) => {
    if (view === 'labels') {
      setShowLabelsModal(true);
      return;
    }

    setCurrentView(view);
    sessionStorage.setItem('fundoo_current_view', view);
  };

  const handleSearchChange = (value) => {
    setSearchQuery(value);
    sessionStorage.setItem('fundoo_search_query', value);
  };

  const handleSidebarItemClick = () => {
    setSidebarOpen(false);
    setSidebarHovered(false);
  };

  const handleLabelsSaved = () => {
    setLabelsVersion((prev) => prev + 1);
  };

  const isSidebarExpanded = sidebarOpen || (!sidebarOpen && sidebarHovered);

  return (
    <>
      <TopNavBar
        onSidebarToggle={handleSidebarToggle}
        searchQuery={searchQuery}
        onSearchChange={handleSearchChange}
        onInvitationsClick={() => setShowInvitationsModal(true)}
      />
      <div className="dashboard">
        <div
          className={`dashboard-sidebar ${isSidebarExpanded ? 'expanded' : 'closed'}`}
          onMouseEnter={() => {
            if (!sidebarOpen) {
              setSidebarHovered(true);
            }
          }}
          onMouseLeave={() => {
            if (!sidebarOpen) {
              setSidebarHovered(false);
            }
          }}
        >
          <Sidebar
            isOpen={isSidebarExpanded}
            currentView={currentView}
            onViewChange={handleViewChange}
            onItemClick={handleSidebarItemClick}
          />
        </div>
        <div className="dashboard-content">
          <NotesList
            currentView={currentView}
            searchQuery={searchQuery}
            labelsVersion={labelsVersion}
            key={notesVersion}
          />
        </div>
      </div>

      {showLabelsModal && (
        <EditLabelsModal
          onClose={() => setShowLabelsModal(false)}
          onLabelsSaved={handleLabelsSaved}
        />
      )}

      {showInvitationsModal && (
        <PendingInvitationsModal
          onClose={() => setShowInvitationsModal(false)}
          onInvitationHandled={() => {
            setNotesVersion((prev) => prev + 1);
          }}
        />
      )}
    </>
  );
}
