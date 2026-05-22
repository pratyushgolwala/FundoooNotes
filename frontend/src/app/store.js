import { configureStore } from '@reduxjs/toolkit';
import authReducer from '../redux/slices/authSlice';
import notesReducer from '../redux/slices/notesSlice';

const store = configureStore({
  reducer: {
    auth: authReducer,
    notes: notesReducer,
  },
});

export default store;
