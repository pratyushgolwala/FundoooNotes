import React, { createContext, useEffect, useMemo, useState } from 'react';

export const AuthContext = createContext({
  login: () => {},
  logout: () => {},
  isAuthenticated: false,
  loading: true,
  userId: null,
});

function readAuthState() {
  try {
    const accessToken = localStorage.getItem('access_token');
    const userId = localStorage.getItem('user_id');

    return {
      accessToken,
      userId,
      isAuthenticated: Boolean(accessToken),
    };
  } catch (error) {
    return {
      accessToken: null,
      userId: null,
      isAuthenticated: false,
    };
  }
}

export default function AuthProvider({ children }) {
  const [authState, setAuthState] = useState(() => readAuthState());
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setAuthState(readAuthState());
    setLoading(false);

    const handleStorageChange = () => {
      setAuthState(readAuthState());
    };

    window.addEventListener('storage', handleStorageChange);

    return () => {
      window.removeEventListener('storage', handleStorageChange);
    };
  }, []);

  const login = (accessToken, userId, refreshToken = null) => {
    if (accessToken) {
      localStorage.setItem('access_token', accessToken);
    }

    if (refreshToken) {
      localStorage.setItem('refresh_token', refreshToken);
    }

    if (userId !== undefined && userId !== null) {
      localStorage.setItem('user_id', String(userId));
    }

    setAuthState({
      accessToken,
      userId: userId !== undefined && userId !== null ? String(userId) : null,
      isAuthenticated: Boolean(accessToken),
    });
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_id');
    setAuthState({
      accessToken: null,
      userId: null,
      isAuthenticated: false,
    });
  };

  const value = useMemo(
    () => ({
      login,
      logout,
      isAuthenticated: authState.isAuthenticated,
      loading,
      userId: authState.userId,
    }),
    [authState.isAuthenticated, authState.userId, loading]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}