import React, { useState } from 'react';
import '../styles/notes.css';
import notesService from '../../services/notesService';
import { FaArchive, FaThumbtack, FaTrash, FaUndoAlt, FaUsers } from 'react-icons/fa';

export default function NoteCard({
  note,
  onUpdate,
  onDelete,
  onStateChange,
  onClick,
  onManageCollaborators,
  currentView,
}) {
  const [loading, setLoading] = useState(false);
  const viewerAccess = note.viewer_access || 'owner';
  const isPinned = !!note.is_pinned;
  const isArchived = !!note.is_archived;
  const color = note.color || '#FFFFFF';

  const handlePin = async (e) => {
    e.stopPropagation();
    setLoading(true);

    try {
      const nextPinned = !isPinned;
      await notesService.updateNote(note.id, {
        is_pinned: nextPinned,
      });

      if (onStateChange) {
        onStateChange(note.id, { is_pinned: nextPinned });
      }

      onUpdate();

    } catch (err) {
      console.error('Failed to pin note', err);

    } finally {
      setLoading(false);
    }
  };

  const handleArchive = async (e) => {
    e.stopPropagation();
    setLoading(true);

    try {
      const nextArchived = !isArchived;
      await notesService.updateNote(note.id, {
        is_archived: nextArchived,
      });

      if (onStateChange) {
        onStateChange(note.id, { is_archived: nextArchived });
      }

      onUpdate();

    } catch (err) {
      console.error('Failed to archive note', err);

    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (e) => {
    e.stopPropagation();

    if (window.confirm('Move this note to trash?')) {
      setLoading(true);

      try {
        await notesService.deleteNote(note.id);

        onDelete(note.id);

      } catch (err) {
        console.error('Failed to delete note', err);

      } finally {
        setLoading(false);
      }
    }
  };

  return (
    <div
      className="note-card"
      style={{ backgroundColor: color }}
      onClick={currentView === 'trash' || viewerAccess === 'pending' ? undefined : onClick}
    >
      <div className="note-card-meta">
        {note.owner && (
          <span className="note-owner-chip">
            Owner: {note.owner.name || note.owner.email}
          </span>
        )}

        {viewerAccess && viewerAccess !== 'owner' && (
          <span className="note-access-chip">
            {viewerAccess === 'edit' ? 'Can edit' : 'Can view'}
          </span>
        )}

        {viewerAccess === 'owner' && (
          <span className="note-access-chip owner">Owner</span>
        )}

        {viewerAccess === 'pending' && (
          <span className="note-access-chip">Invitation pending</span>
        )}
      </div>

      {isPinned && (
        <span className="pinned-icon"><FaThumbtack /></span>
      )}

      <div className="note-card-header">
        <h3 className="note-card-title">
          {note.title}
        </h3>
      </div>

      <p className="note-card-content">
        {note.content}
      </p>

      {note.label_names &&
        note.label_names.length > 0 && (
        <div className="note-card-labels">
          {note.label_names
            .slice(0, 3)
            .map((label, idx) => (
            <span
              key={idx}
              className="note-label"
            >
              {label}
            </span>
          ))}
          {note.label_names.length > 3 && (
            <span className="note-label">
              +{note.label_names.length - 3}
            </span>
          )}
        </div>
      )}

      {note.collaborators && note.collaborators.length > 0 && (
        <div className="note-card-collaborators">
          {note.collaborators.slice(0, 2).map((user) => (
            <span key={user.id} className="note-collaborator-chip">
              {user.name || user.email} · {user.access_level === 'edit' ? 'edit' : 'view'}
            </span>
          ))}
          {note.collaborators.length > 2 && (
            <span className="note-collaborator-chip">
              +{note.collaborators.length - 2}
            </span>
          )}
        </div>
      )}

      <div className="note-card-footer">
        <small>{new Date(note.created_at).toLocaleDateString()}</small>

        <div className="note-actions">
          {currentView === 'shared' && viewerAccess === 'pending' ? (
            <>
              <button
                className="note-action-btn"
                onClick={async (e) => {
                  e.stopPropagation();
                  setLoading(true);
                  try {
                    await notesService.acceptNoteInvitation(note.invite_token);
                    onUpdate();
                  } catch (err) {
                    console.error('Failed to accept invitation', err);
                  } finally {
                    setLoading(false);
                  }
                }}
                disabled={loading}
                title="Accept invitation"
              >
                <FaUsers />
              </button>

              <button
                className="note-action-btn note-delete-btn"
                onClick={async (e) => {
                  e.stopPropagation();
                  setLoading(true);
                  try {
                    await notesService.declineNoteInvitation(note.invite_token);
                    onDelete(note.id);
                  } catch (err) {
                    console.error('Failed to decline invitation', err);
                  } finally {
                    setLoading(false);
                  }
                }}
                disabled={loading}
                title="Decline invitation"
              >
                <FaTrash />
              </button>
            </>
          ) : currentView === 'trash' ? (
            <>
              <button
                className="note-action-btn"
                onClick={async (e) => {
                  e.stopPropagation();
                  setLoading(true);
                  try {
                    await notesService.restoreNote(note.id);
                    onUpdate();
                  } catch (err) {
                    console.error('Failed to restore note', err);
                  } finally {
                    setLoading(false);
                  }
                }}
                disabled={loading}
                title="Restore"
              >
                <FaUndoAlt />
              </button>

              <button
                className="note-action-btn note-delete-btn"
                onClick={async (e) => {
                  e.stopPropagation();
                  if (!window.confirm('Permanently delete this note?')) return;

                  setLoading(true);
                  try {
                    await notesService.permanentDeleteNote(note.id);
                    onDelete(note.id);
                  } catch (err) {
                    console.error('Failed to permanently delete note', err);
                  } finally {
                    setLoading(false);
                  }
                }}
                disabled={loading}
                title="Permanently delete"
              >
                <FaTrash />
              </button>
            </>
          ) : (
            <>
              {(viewerAccess === 'owner' || viewerAccess === 'edit') && (
                <button
                  className="note-action-btn"
                  onClick={handlePin}
                  disabled={loading}
                  title={isPinned ? 'Unpin' : 'Pin'}
                >
                  <FaThumbtack style={{ opacity: isPinned ? 1 : 0.55 }} />
                </button>
              )}

              {(viewerAccess === 'owner' || viewerAccess === 'edit') && (
                <button
                  className="note-action-btn"
                  onClick={handleArchive}
                  disabled={loading}
                  title={isArchived ? 'Unarchive' : 'Archive'}
                >
                  <FaArchive />
                </button>
              )}

              <button
                className="note-action-btn"
                onClick={(e) => {
                  e.stopPropagation();
                  if (onManageCollaborators && viewerAccess === 'owner') {
                    onManageCollaborators(note);
                  }
                }}
                disabled={loading}
                title="Manage collaborators"
                style={{ opacity: viewerAccess === 'owner' ? 1 : 0.35 }}
              >
                <FaUsers />
              </button>

              {viewerAccess === 'owner' && (
                <button
                  className="note-action-btn note-delete-btn"
                  onClick={handleDelete}
                  disabled={loading}
                  title="Move to trash"
                >
                  <FaTrash />
                </button>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}