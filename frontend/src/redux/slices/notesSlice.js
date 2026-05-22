import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  notes: [],
  loading: false,
  error: null,
};

const notesSlice = createSlice({
  name: 'notes',
  initialState,
  reducers: {
    setNotes(state, action) {
      state.notes = action.payload || [];
      state.loading = false;
      state.error = null;
    },
    addNote(state, action) {
      state.notes.unshift(action.payload);
    },
    updateNote(state, action) {
      const idx = state.notes.findIndex((n) => n.id === action.payload.id);
      if (idx >= 0) state.notes[idx] = { ...state.notes[idx], ...action.payload };
    },
    removeNote(state, action) {
      state.notes = state.notes.filter((n) => n.id !== action.payload);
    },
    setLoading(state, action) {
      state.loading = !!action.payload;
    },
    setError(state, action) {
      state.error = action.payload || null;
    },
  },
});

export const { setNotes, addNote, updateNote, removeNote, setLoading, setError } = notesSlice.actions;
export default notesSlice.reducer;
