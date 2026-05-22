import { createSlice } from '@reduxjs/toolkit';

function readInitial() {
  try {
    const accessToken = localStorage.getItem('access_token');
    const userId = localStorage.getItem('user_id');
    return {
      isAuthenticated: Boolean(accessToken),
      loading: false,
      userId: userId || null,
      accessToken: accessToken || null,
    };
  } catch (err) {
    return { isAuthenticated: false, loading: false, userId: null, accessToken: null };
  }
}

const authSlice = createSlice({
  name: 'auth',
  initialState: readInitial(),
  reducers: {
    loginSuccess(state, action) {
      state.isAuthenticated = true;
      state.accessToken = action.payload.accessToken || null;
      state.userId = action.payload.userId || null;
      state.loading = false;
    },
    logout(state) {
      state.isAuthenticated = false;
      state.accessToken = null;
      state.userId = null;
      state.loading = false;
    },
    setLoading(state, action) {
      state.loading = !!action.payload;
    },
  },
});

export const { loginSuccess, logout, setLoading } = authSlice.actions;
export default authSlice.reducer;
