import React, { useState, useRef, useEffect } from "react";
import "../styles/CreateNoteBar.css";
import { FaArchive, FaPalette, FaTags, FaThumbtack } from 'react-icons/fa';

export default function CreateNoteBar({ onCreate, labels = [] }) {
  const [expanded, setExpanded] = useState(false);
  const [showColorPicker, setShowColorPicker] = useState(false);
  const [showLabelPicker, setShowLabelPicker] = useState(false);
  const colorPickerRef = useRef(null);
  const labelPickerRef = useRef(null);

  const [note, setNote] = useState({
    title: "",
    content: "",
    color: "#ffffff",
    is_pinned: false,
    is_archived: false,
    labels: [],
  });

  // Close pickers when clicking outside.
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (colorPickerRef.current && !colorPickerRef.current.contains(e.target)) {
        setShowColorPicker(false);
      }
      if (labelPickerRef.current && !labelPickerRef.current.contains(e.target)) {
        setShowLabelPicker(false);
      }
    };

    if (showColorPicker || showLabelPicker) {
      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [showColorPicker, showLabelPicker]);

  const handleSubmit = () => {
    if (!note.title && !note.content) return;

    onCreate(note);

    setNote({
      title: "",
      content: "",
      color: "#ffffff",
      is_pinned: false,
      is_archived: false,
      labels: [],
    });

    setExpanded(false);
    setShowColorPicker(false);
    setShowLabelPicker(false);
  };

  const toggleLabel = (labelId) => {
    setNote((prev) => {
      const nextLabels = prev.labels.includes(labelId)
        ? prev.labels.filter((id) => id !== labelId)
        : [...prev.labels, labelId];

      return {
        ...prev,
        labels: nextLabels,
      };
    });
  };

  const colors = [
    "#ffffff",
    "#f28482",
    "#f4a460",
    "#f9f871",
    "#a6d48f",
    "#8ec6d6",
    "#98b3d9",
    "#e6a8d7",
    "#d3d3d3",
    "#1e1e1e",
  ];

  return (
    <div
      className={`create-note-bar ${expanded ? "expanded" : ""}`}
      style={{ backgroundColor: note.color }}
      onClick={() => setExpanded(true)}
    >
      {expanded && (
        <input
          type="text"
          placeholder="Title"
          value={note.title}
          onChange={(e) =>
            setNote({ ...note, title: e.target.value })
          }
          className="note-title-input"
          onClick={(e) => e.stopPropagation()}
        />
      )}

      <textarea
        placeholder="Take a note..."
        value={note.content}
        onChange={(e) =>
          setNote({ ...note, content: e.target.value })
        }
        className="note-content-input"
        onClick={(e) => e.stopPropagation()}
      />

      {expanded && (
        <div className="note-toolbar">
          <div className="toolbar-left">
            {/* Pin Button with State Indicator */}
            <button
              className={`toolbar-btn ${note.is_pinned ? "active" : ""}`}
              onClick={(e) => {
                e.stopPropagation();
                setNote({ ...note, is_pinned: !note.is_pinned });
              }}
              title={note.is_pinned ? "Unpinned this note" : "Pin this note"}
              aria-label="Pin note"
            >
              <FaThumbtack style={{ opacity: note.is_pinned ? 1 : 0.55 }} />
            </button>

            {/* Color Picker Toggle */}
            <div className="color-picker-wrapper" ref={colorPickerRef}>
              <button
                className="toolbar-btn color-toggle-btn"
                onClick={(e) => {
                  e.stopPropagation();
                  setShowColorPicker(!showColorPicker);
                  setShowLabelPicker(false);
                }}
                title="Change color"
                aria-label="Toggle color picker"
              >
                <FaPalette />
              </button>

              {showColorPicker && (
                <div className="color-picker-dropdown" onClick={(e) => e.stopPropagation()}>
                  {colors.map((color) => (
                    <button
                      key={color}
                      className={`color-circle ${note.color === color ? "selected" : ""}`}
                      style={{ backgroundColor: color }}
                      onClick={(e) => {
                        e.stopPropagation();
                        setNote({ ...note, color });
                        setShowColorPicker(false);
                      }}
                      title={`Color: ${color}`}
                      aria-label={`Select color ${color}`}
                    />
                  ))}
                </div>
              )}
            </div>

            {/* Labels Button */}
            <div className="label-picker-wrapper" ref={labelPickerRef}>
              <button
                className={`toolbar-btn ${note.labels.length > 0 ? "active" : ""}`}
                onClick={(e) => {
                  e.stopPropagation();
                  setShowLabelPicker(!showLabelPicker);
                  setShowColorPicker(false);
                }}
                title="Add labels"
                aria-label="Add labels"
              >
                <FaTags />
              </button>

              {showLabelPicker && (
                <div className="label-picker-dropdown" onClick={(e) => e.stopPropagation()}>
                  {labels.length === 0 ? (
                    <p className="label-picker-empty">No labels found</p>
                  ) : (
                    labels.map((label) => {
                      const selected = note.labels.includes(label.id);
                      return (
                        <label key={label.id} className="label-picker-item">
                          <input
                            type="checkbox"
                            checked={selected}
                            onChange={() => toggleLabel(label.id)}
                          />
                          <span>{label.name}</span>
                        </label>
                      );
                    })
                  )}
                </div>
              )}
            </div>

            {/* Archive Button with State Indicator */}
            <button
              className={`toolbar-btn ${note.is_archived ? "active" : ""}`}
              onClick={(e) => {
                e.stopPropagation();
                setNote({ ...note, is_archived: !note.is_archived });
              }}
              title={note.is_archived ? "Unarchive" : "Archive"}
              aria-label="Archive note"
            >
              <FaArchive />
            </button>
          </div>

          {note.labels.length > 0 && (
            <div className="selected-labels">
              {labels
                .filter((label) => note.labels.includes(label.id))
                .map((label) => (
                  <span key={label.id} className="selected-label-chip">
                    {label.name}
                  </span>
                ))}
            </div>
          )}

          <button
            className="close-btn"
            onClick={(e) => {
              e.stopPropagation();
              handleSubmit();
            }}
          >
            Save
          </button>
        </div>
      )}
    </div>
  );
}