import React, { useEffect, useState } from 'react';
import notesService from '../../services/notesService';
import '../styles/noteCollaboratorsModal.css';

export default function NoteCollaboratorsModal({ note, onClose, onSaved }) {
  const [email, setEmail] = useState('');
  const [accessLevel, setAccessLevel] = useState('view');
  const [collaborators, setCollaborators] = useState(note?.collaborators || []);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  useEffect(() => {
    const fetchCollaborators = async () => {
      if (!note?.id) return;

      setLoading(true);
      setError('');

      try {
        const response = await notesService.getNoteCollaborators(note.id);
        setCollaborators(response.data.payload || []);
      } catch (err) {
        setError('Failed to load collaborators.');
      } finally {
        setLoading(false);
      }
    };

    fetchCollaborators();
  }, [note?.id]);

  const handleAddCollaborator = async (e) => {
    e.preventDefault();

    const trimmed = email.trim();
    if (!trimmed || !note?.id) {
      return;
    }

    setSaving(true);
    setError('');
    setNotice('');

    try {
      const response = await notesService.addNoteCollaborator(note.id, trimmed, accessLevel);
      const added = response?.data?.payload;

      if (added?.status === 'pending') {
        setNotice('Invitation sent. The collaborator can accept or decline from the email.');
      } else if (added?.id) {
        setCollaborators((prev) => {
          if (prev.some((user) => user.id === added.id)) {
            return prev;
          }
          return [...prev, added];
        });
      } else {
        const refreshed = await notesService.getNoteCollaborators(note.id);
        setCollaborators(refreshed.data.payload || []);
      }

      setEmail('');
      setAccessLevel('view');
      if (onSaved) {
        onSaved();
      }
    } catch (err) {
      setError(err.response?.data?.payload?.detail || err.response?.data?.detail || 'Could not add collaborator.');
    } finally {
      setSaving(false);
    }
  };

  const handleRemoveCollaborator = async (userId) => {
    if (!note?.id) return;

    setSaving(true);
    setError('');

    try {
      await notesService.removeNoteCollaborator(note.id, userId);
      setCollaborators((prev) => prev.filter((user) => user.id !== userId));
      if (onSaved) {
        onSaved();
      }
    } catch (err) {
      setError('Could not remove collaborator.');
    } finally {
      setSaving(false);
    }
  };

  const handleAccessChange = async (userId, nextAccess) => {
    if (!note?.id) return;

    setSaving(true);
    setError('');

    try {
      const response = await notesService.updateNoteCollaboratorAccess(note.id, userId, nextAccess);
      const updated = response?.data?.payload;

      if (updated?.id) {
        setCollaborators((prev) =>
          prev.map((user) => (user.id === userId ? { ...user, access_level: nextAccess } : user))
        );
      } else {
        const refreshed = await notesService.getNoteCollaborators(note.id);
        setCollaborators(refreshed.data.payload || []);
      }

      if (onSaved) {
        onSaved();
      }
    } catch (err) {
      setError('Could not update access level.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="note-collaborators-overlay" onClick={onClose}>
      <div className="note-collaborators-modal" onClick={(e) => e.stopPropagation()}>
        <div className="note-collaborators-header">
          <h3>Collaborators</h3>
          <button type="button" className="note-collaborators-close" onClick={onClose}>
            ×
          </button>
        </div>

        {note?.owner && (
          <div className="note-collaborators-owner">
            <span className="note-collaborators-owner-label">Owner</span>
            <div className="note-collaborators-owner-info">
              <strong>{note.owner.name}</strong>
              <span>{note.owner.email}</span>
            </div>
          </div>
        )}

        <form className="note-collaborators-form" onSubmit={handleAddCollaborator}>
          <input
            type="email"
            placeholder="Enter collaborator email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="note-collaborators-input"
          />
          <select
            className="note-collaborators-access"
            value={accessLevel}
            onChange={(e) => setAccessLevel(e.target.value)}
          >
            <option value="view">Can view</option>
            <option value="edit">Can edit</option>
          </select>
          <button type="submit" className="note-collaborators-add" disabled={saving}>
            {saving ? 'Adding...' : 'Add'}
          </button>
        </form>

        {error && <p className="note-collaborators-error">{error}</p>}
        {notice && <p className="note-collaborators-success">{notice}</p>}

        <div className="note-collaborators-list">
          {loading ? (
            <p className="note-collaborators-empty">Loading collaborators...</p>
          ) : collaborators.length === 0 ? (
            <p className="note-collaborators-empty">No collaborators yet</p>
          ) : (
            collaborators.map((user) => (
              <div key={user.id} className="note-collaborators-item">
                <div className="note-collaborators-user">
                  <strong>{user.name}</strong>
                  <span>{user.email}</span>
                </div>
                <div className="note-collaborators-actions">
                  <select
                    className="note-collaborators-access"
                    value={user.access_level || 'view'}
                    onChange={(e) => handleAccessChange(user.id, e.target.value)}
                    disabled={saving}
                  >
                    <option value="view">Can view</option>
                    <option value="edit">Can edit</option>
                  </select>
                  <button
                    type="button"
                    className="note-collaborators-remove"
                    onClick={() => handleRemoveCollaborator(user.id)}
                    disabled={saving}
                  >
                    Remove
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}