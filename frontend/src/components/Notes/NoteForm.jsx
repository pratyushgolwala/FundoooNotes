import React, { useState, useContext, useEffect } from 'react';
import '../styles/notes.css';
import notesService from '../../services/notesService';
import { AuthContext } from '../../context/AuthContext';

const COLORS = [
  '#FFFFFF', '#f28482', '#f4a261', '#f8f7a1',
  '#7bd051', '#80deea', '#4fc3f7', '#ab47bc',
  '#ef9a9a', '#ffcc80', '#fff59d', '#c5e1a5',
  '#80cbc4', '#81d4fa', '#b39ddb', '#f8bbd0'
];

export default function NoteForm({ onSuccess, editingNote = null, onCancel }) {
  const [formData, setFormData] = useState({
    title: editingNote?.title || '',
    content: editingNote?.content || '',
    color: editingNote?.color || '#FFFFFF',
    labels: editingNote?.label_ids || [],
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [labels, setLabels] = useState([]);
  const { userId } = useContext(AuthContext);

  useEffect(() => {
    fetchLabels();
  }, []);

  const fetchLabels = async () => {
    try {
      const response = await notesService.getLabels();
      setLabels(response.data.payload || []);
    } catch (err) {
      console.error('Failed to fetch labels', err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (editingNote) {
        await notesService.updateNote(editingNote.id, formData);
      } else {
        await notesService.createNote(formData);
      }
      onSuccess();
    } catch (err) {
      setError(err.response?.data?.payload?.detail || err.response?.data?.detail || 'Failed to save note');
    } finally {
      setLoading(false);
    }
  };

  const toggleLabel = (labelId) => {
    setFormData((prev) => ({
      ...prev,
      labels: prev.labels.includes(labelId)
        ? prev.labels.filter((id) => id !== labelId)
        : [...prev.labels, labelId],
    }));
  };

  return (
    <div className="note-form-overlay">
      <div className="note-form-container">
        <form onSubmit={handleSubmit} className="note-form">
          {error && <div className="form-error">{error}</div>}

          <div className="form-group">
            <input
              type="text"
              placeholder="Title"
              className="note-title-input"
              value={formData.title}
              onChange={(e) =>
                setFormData({ ...formData, title: e.target.value })
              }
              required
            />
          </div>

          <div className="form-group">
            <textarea
              placeholder="Take a note..."
              className="note-content-input"
              value={formData.content}
              onChange={(e) =>
                setFormData({ ...formData, content: e.target.value })
              }
              required
              rows="4"
            />
          </div>

          <div className="form-group">
            <label>Color:</label>
            <div className="color-picker">
              {COLORS.map((color) => (
                <button
                  key={color}
                  type="button"
                  className={`color-option ${
                    formData.color === color ? 'selected' : ''
                  }`}
                  style={{ backgroundColor: color }}
                  onClick={() => setFormData({ ...formData, color })}
                />
              ))}
            </div>
          </div>

          <div className="form-group">
            <label>Labels:</label>
            <div className="labels-grid">
              {labels.map((label) => (
                <label key={label.id} className="label-checkbox">
                  <input
                    type="checkbox"
                    checked={formData.labels.includes(label.id)}
                    onChange={() => toggleLabel(label.id)}
                  />
                  {label.name}
                </label>
              ))}
            </div>
          </div>

          <div className="form-actions">
            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? 'Saving...' : 'Save Note'}
            </button>
            {onCancel && (
              <button
                type="button"
                className="btn-secondary"
                onClick={onCancel}
              >
                Cancel
              </button>
            )}
          </div>
        </form>
      </div>
    </div>
  );
}
