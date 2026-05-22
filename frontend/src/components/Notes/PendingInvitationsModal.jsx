import React, { useEffect, useState } from 'react';
import notesService from '../../services/notesService';
import '../styles/pendingInvitationsModal.css';
import { FaBell, FaCheck, FaTimes } from 'react-icons/fa';

export default function PendingInvitationsModal({ onClose, onInvitationHandled }) {
  const [invitations, setInvitations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [respondingId, setRespondingId] = useState(null);

  useEffect(() => {
    fetchPendingInvitations();
  }, []);

  const fetchPendingInvitations = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await notesService.getPendingInvitations();
      setInvitations(response.data.payload || []);
    } catch (err) {
      setError(err.response?.data?.payload?.detail || err.response?.data?.detail || 'Failed to load pending invitations.');
    } finally {
      setLoading(false);
    }
  };

  const handleRespond = async (inviteId, action) => {
    setRespondingId(inviteId);
    setError('');

    try {
      const response = await notesService.respondToInvitation(inviteId, action);

      // Remove the invitation from the list
      setInvitations((prev) => prev.filter((inv) => inv.invite_id !== inviteId));

      // Notify parent component to refresh data
      if (onInvitationHandled) {
        onInvitationHandled();
      }
    } catch (err) {
      console.error('Invitation response error:', err);
      const errorMessage = err.response?.data?.payload?.detail || err.response?.data?.detail || `Failed to ${action} invitation.`;
      setError(errorMessage);
    } finally {
      setRespondingId(null);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      year: date.getFullYear() !== new Date().getFullYear() ? 'numeric' : undefined
    });
  };

  const getAccessBadge = (level) => {
    if (level === 'edit') {
      return <span className="access-badge edit">Can Edit</span>;
    }
    return <span className="access-badge view">Can View</span>;
  };

  return (
    <div className="invitations-overlay" onClick={onClose}>
      <div className="invitations-modal" onClick={(e) => e.stopPropagation()}>
        <div className="invitations-header">
          <div className="invitations-title">
            <FaBell className="invitations-icon" />
            <h3>Pending Invitations</h3>
          </div>
          <button type="button" className="invitations-close" onClick={onClose}>
            ×
          </button>
        </div>

        <div className="invitations-content">
          {loading && <div className="invitations-empty">Loading invitations...</div>}

          {!loading && invitations.length === 0 && (
            <div className="invitations-empty">
              <p>No pending invitations</p>
            </div>
          )}

          {!loading && invitations.length > 0 && (
            <div className="invitations-list">
              {invitations.map((invite) => (
                <div key={invite.invite_id} className="invitation-item">
                  <div className="invitation-details">
                    <div className="invitation-note">
                      <h4 className="invitation-note-title">{invite.note_title}</h4>
                      <div className="invitation-meta">
                        <span className="invitation-owner">
                          From: <strong>{invite.invited_by_name || invite.invited_by_email}</strong>
                        </span>
                        <span className="invitation-date">{formatDate(invite.created_at)}</span>
                      </div>
                    </div>
                    <div className="invitation-access">
                      {getAccessBadge(invite.access_level)}
                    </div>
                  </div>

                  <div className="invitation-actions">
                    <button
                      type="button"
                      className="btn-accept"
                      onClick={() => handleRespond(invite.invite_id, 'accept')}
                      disabled={respondingId === invite.invite_id}
                    >
                      <FaCheck /> Accept
                    </button>
                    <button
                      type="button"
                      className="btn-decline"
                      onClick={() => handleRespond(invite.invite_id, 'decline')}
                      disabled={respondingId === invite.invite_id}
                    >
                      <FaTimes /> Decline
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {error && <div className="invitations-error">{error}</div>}
        </div>
      </div>
    </div>
  );
}
