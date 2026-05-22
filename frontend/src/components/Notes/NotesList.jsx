import React, { useCallback, useEffect, useState } from 'react';
import '../styles/notes.css';
import { FaArchive, FaInbox, FaTags, FaThumbtack, FaTrash, FaUsers } from 'react-icons/fa';
import NoteCard from './NoteCard';
import NoteForm from './NoteForm';
import NoteCollaboratorsModal from './NoteCollaboratorsModal';
import notesService from '../../services/notesService';
import CreateNoteBar from './CreateNoteBar';

export default function NotesList({ currentView = 'notes', searchQuery = '', labelsVersion = 0 }) {
  const [allNotes, setAllNotes] = useState(() => {
    try {
      const cached = sessionStorage.getItem('fundoo_notes_cache');
      return cached ? JSON.parse(cached) : [];
    } catch (err) {
      return [];
    }
  });
  const [filteredNotes, setFilteredNotes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [editingNote, setEditingNote] = useState(null);
  const [selectedLabel, setSelectedLabel] = useState('');
  const [labels, setLabels] = useState([]);
  const [collaboratorsNote, setCollaboratorsNote] = useState(null);

  useEffect(() => {
    fetchNotes();
    fetchLabels();
  }, []);

  useEffect(() => {
    fetchLabels();
  }, [labelsVersion]);

  const fetchNotes = async () => {
    setLoading(true);
    try {
      const response = await notesService.getNotes();
      const notesData = response.data.payload || [];
      const normalizedNotes = notesData || [];
      setAllNotes(normalizedNotes);
      sessionStorage.setItem('fundoo_notes_cache', JSON.stringify(normalizedNotes));
    } catch (err) {
      console.error('Failed to fetch notes', err);
      setAllNotes([]);
      sessionStorage.setItem('fundoo_notes_cache', JSON.stringify([]));
    } finally {
      setLoading(false);
    }
  };

  const updateNotesCache = (updater) => {
    setAllNotes((prev) => {
      const next = typeof updater === 'function' ? updater(prev) : updater;
      sessionStorage.setItem('fundoo_notes_cache', JSON.stringify(next));
      return next;
    });
  };

  const handleLocalNotePatch = (noteId, patch) => {
    updateNotesCache((prev) =>
      prev.map((note) => (note.id === noteId ? { ...note, ...patch } : note))
    );
  };

  const handleLocalNoteDelete = (noteId) => {
    updateNotesCache((prev) => prev.filter((note) => note.id !== noteId));
    fetchNotes();
  };

  const fetchLabels = async () => {
    try {
      const response = await notesService.getLabels();
      setLabels(response.data.payload || []);
    } catch (err) {
      console.error('Failed to fetch labels', err);
    }
  };

  const applyFilters = useCallback(() => {
    let filtered = allNotes;
    const isSharedNote = (note) => (note.share_state || 'private') !== 'private' || (note.collaborators?.length || 0) > 0;

    if (currentView === 'archive') {
      filtered = filtered.filter((note) => (note.is_archived || false) === true && !(note.is_deleted || false));
    } else if (currentView === 'notes') {
      filtered = filtered.filter(
        (note) => (note.viewer_access || 'owner') === 'owner' && (note.share_state || 'private') === 'private' && (note.is_archived || false) === false && !(note.is_deleted || false)
      );
    } else if (currentView === 'shared') {
      filtered = filtered.filter(
        (note) => isSharedNote(note) && (note.is_archived || false) === false && !(note.is_deleted || false)
      );
    } else if (currentView === 'trash') {
      filtered = filtered.filter((note) => (note.is_deleted || false) === true);
    } else if (currentView === 'labels') {
      filtered = filtered.filter(
        (note) => (note.viewer_access || 'owner') === 'owner' && (note.share_state || 'private') === 'private' && (note.is_archived || false) === false && !(note.is_deleted || false)
      );
    }

    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (note) =>
          note.title.toLowerCase().includes(query) ||
          note.content.toLowerCase().includes(query),
      );
    }

    if (selectedLabel && (currentView === 'notes' || currentView === 'labels')) {
      filtered = filtered.filter((note) =>
        note.label_ids?.includes(parseInt(selectedLabel, 10)),
      );
    }

    setFilteredNotes(filtered);
  }, [allNotes, searchQuery, selectedLabel, currentView]);

  useEffect(() => {
    applyFilters();
  }, [applyFilters]);

  const handleFormSuccess = () => {
    setShowForm(false);
    setEditingNote(null);
    fetchNotes();
  };

  const pinnedNotes = filteredNotes.filter((n) => !!n.is_pinned);
  const unpinnedNotes = filteredNotes.filter((n) => !n.is_pinned);

  return (
    <div className="notes-container">
      <div className="notes-header">
        {currentView === 'notes' && (
          <div className="notes-controls">
            <CreateNoteBar
              labels={labels}
              onCreate={async (noteData) => {
                try {
                  const response = await notesService.createNote(noteData);
                  const createdNote = response?.data?.payload;

                  if (createdNote && createdNote.id) {
                    updateNotesCache((prev) => [createdNote, ...prev]);
                  } else {
                    fetchNotes();
                  }
                } catch (err) {
                  console.error(err);
                }
              }}
            />

            <div className="filter-controls">
              <select
                value={selectedLabel}
                onChange={(e) => setSelectedLabel(e.target.value)}
                className="label-filter"
              >
                <option value="">All Labels</option>
                {labels.map((label) => (
                  <option key={label.id} value={label.id}>
                    {label.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
        )}

        {currentView === 'archive' && (
          <h2 className="notes-section-title"><FaArchive /> Archived Notes</h2>
        )}
        {currentView === 'shared' && (
          <h2 className="notes-section-title"><FaUsers /> Shared Notes</h2>
        )}
        {currentView === 'trash' && (
          <h2 className="notes-section-title"><FaTrash /> Trash</h2>
        )}
        {currentView === 'labels' && (
          <h2 className="notes-section-title"><FaTags /> Labels</h2>
        )}
      </div>

      {pinnedNotes.length > 0 && (
        <div className="notes-section">
          <h2 className="notes-section-title"><FaThumbtack /> Pinned</h2>
          <div className="notes-grid">
            {pinnedNotes.map((note) => (
              <NoteCard
                key={note.id}
                note={note}
                currentView={currentView}
                onUpdate={fetchNotes}
                onDelete={handleLocalNoteDelete}
                onStateChange={handleLocalNotePatch}
                onManageCollaborators={(selectedNote) => {
                  setCollaboratorsNote(selectedNote);
                }}
                onClick={() => {
                  setEditingNote(note);
                  setShowForm(true);
                }}
              />
            ))}
          </div>
        </div>
      )}

      {unpinnedNotes.length > 0 && (
        <div className="notes-section">
          {pinnedNotes.length > 0 && (
            <h2 className="notes-section-title">Others</h2>
          )}
          <div className="notes-grid">
            {unpinnedNotes.map((note) => (
              <NoteCard
                key={note.id}
                note={note}
                currentView={currentView}
                onUpdate={fetchNotes}
                onDelete={handleLocalNoteDelete}
                onStateChange={handleLocalNotePatch}
                onManageCollaborators={(selectedNote) => {
                  setCollaboratorsNote(selectedNote);
                }}
                onClick={() => {
                  setEditingNote(note);
                  setShowForm(true);
                }}
              />
            ))}
          </div>
        </div>
      )}

      {filteredNotes.length === 0 && !loading && (
        <div className="empty-state">
          {currentView === 'shared' ? (
            <>
              <p><FaInbox /> No shared notes yet</p>
              <p>Notes added by other people will appear here.</p>
            </>
          ) : currentView === 'trash' ? (
            <>
              <p><FaTrash /> Trash is empty</p>
              <p>Deleted notes will appear here until you restore or remove them permanently.</p>
            </>
          ) : (
            <>
              <p><FaInbox /> No notes yet</p>
              <p>Create your first note to get started!</p>
            </>
          )}
        </div>
      )}

      {loading && <div className="loading">Loading notes...</div>}

      {showForm && (
        <NoteForm
          onSuccess={handleFormSuccess}
          editingNote={editingNote}
          onCancel={() => {
            setShowForm(false);
            setEditingNote(null);
          }}
        />
      )}

      {collaboratorsNote && (
        <NoteCollaboratorsModal
          note={collaboratorsNote}
          onClose={() => setCollaboratorsNote(null)}
          onSaved={() => {
            fetchNotes();
          }}
        />
      )}
    </div>
  );
}
