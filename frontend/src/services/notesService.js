import API from './api';

const notesService = {
  getNotes: (params = {}) => {
    // Make sure params are correct
    return API.get('/notes/', { params });
  },

  getNoteById: (id) => API.get(`/notes/${id}/`),

  createNote: (data) => {
    // Ensure required fields are present while preserving create-time flags.
    return API.post('/notes/', {
      title: data.title || 'Untitled',
      content: data.content || '',
      color: data.color || '#FFFFFF',
      label_ids: data.labels || [],
      is_pinned: !!data.is_pinned,
      is_archived: !!data.is_archived,
    });
  },

  updateNote: (id, data) => {
    const payload = {};

    if (data.title !== undefined) payload.title = data.title;
    if (data.content !== undefined) payload.content = data.content;
    if (data.color !== undefined) payload.color = data.color;
    if (data.labels !== undefined) payload.label_ids = data.labels;
    if (data.is_pinned !== undefined) payload.is_pinned = data.is_pinned;
    if (data.is_archived !== undefined) payload.is_archived = data.is_archived;

    return API.patch(`/notes/${id}/`, payload);
  },

  deleteNote: (id) => API.delete(`/notes/${id}/`),

  restoreNote: (id) => API.post(`/notes/${id}/restore/`),

  permanentDeleteNote: (id) => API.delete(`/notes/${id}/permanent-delete/`),

  getNoteCollaborators: (noteId) => API.get(`/notes/${noteId}/collaborators/`),

  addNoteCollaborator: (noteId, email, accessLevel = 'view') =>
    API.post(`/notes/${noteId}/collaborators/`, { email, access_level: accessLevel }),

  updateNoteCollaboratorAccess: (noteId, userId, accessLevel) =>
    API.patch(`/notes/${noteId}/collaborators/${userId}/`, { access_level: accessLevel }),

  removeNoteCollaborator: (noteId, userId) =>
    API.delete(`/notes/${noteId}/collaborators/${userId}/`),

  acceptNoteInvitation: (token) => API.post(`/notes/invitations/${token}/accept/`),

  declineNoteInvitation: (token) => API.post(`/notes/invitations/${token}/decline/`),

  // Hybrid approach: invitations managed in-app
  getPendingInvitations: () => API.get('/invitations/'),

  respondToInvitation: (inviteId, action) =>
    API.post('/invitations/', { invite_id: inviteId, action }),

  getLabels: () => API.get('/labels/'),

  createLabel: (data) => API.post('/labels/', data),
};

export default notesService;