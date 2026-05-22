import React, { useEffect, useState } from 'react';
import notesService from '../../services/notesService';
import '../styles/editLabelsModal.css';

export default function EditLabelsModal({ onClose, onLabelsSaved }) {
  const [labels, setLabels] = useState([]);
  const [newLabel, setNewLabel] = useState('');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const fetchLabels = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await notesService.getLabels();
      setLabels(response.data.payload || []);
    } catch (err) {
      setError('Failed to load labels.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLabels();
  }, []);

  const handleCreateLabel = async (e) => {
    e.preventDefault();

    const trimmed = newLabel.trim();
    if (!trimmed) {
      return;
    }

    if (labels.some((label) => label.name.toLowerCase() === trimmed.toLowerCase())) {
      setError('Label already exists.');
      return;
    }

    setSaving(true);
    setError('');

    try {
      await notesService.createLabel({ name: trimmed });
      setNewLabel('');
      await fetchLabels();
      if (onLabelsSaved) {
        onLabelsSaved();
      }
    } catch (err) {
      setError('Could not create label.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="edit-labels-overlay" onClick={onClose}>
      <div className="edit-labels-modal" onClick={(e) => e.stopPropagation()}>
        <div className="edit-labels-header">
          <h3>Edit labels</h3>
          <button type="button" className="edit-labels-close" onClick={onClose}>×</button>
        </div>

        <form className="edit-labels-form" onSubmit={handleCreateLabel}>
          <input
            type="text"
            placeholder="Create new label"
            value={newLabel}
            onChange={(e) => setNewLabel(e.target.value)}
            className="edit-labels-input"
          />
          <button type="submit" className="edit-labels-add" disabled={saving}>
            {saving ? 'Adding...' : 'Add'}
          </button>
        </form>

        {error && <p className="edit-labels-error">{error}</p>}

        <div className="edit-labels-list">
          {loading ? (
            <p className="edit-labels-empty">Loading labels...</p>
          ) : labels.length === 0 ? (
            <p className="edit-labels-empty">No labels yet</p>
          ) : (
            labels.map((label) => (
              <div key={label.id} className="edit-labels-item">
                <span>{label.name}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
