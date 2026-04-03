import { createContext, useContext, useEffect, useMemo, useState } from 'react';

import { loginUser, logoutUser, registerUser } from '../api/auth';


const AuthContext = createContext(null);
const ACCESS_KEY = 'medipredict_access';
const REFRESH_KEY = 'medipredict_refresh';


function decodeToken(token) {
  try {
    const payload = token.split('.')[1];
    const normalized = payload.replace(/-/g, '+').replace(/_/g, '/');
    const decoded = atob(normalized);
    return JSON.parse(decoded);
  } catch {
    return null;
  }
}


export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const accessToken = localStorage.getItem(ACCESS_KEY);

    if (!accessToken) {
      setIsLoading(false);
      return;
    }

    const payload = decodeToken(accessToken);
    if (!payload || (payload.exp && payload.exp * 1000 <= Date.now())) {
      localStorage.removeItem(ACCESS_KEY);
      localStorage.removeItem(REFRESH_KEY);
      setIsLoading(false);
      return;
    }

    setUser({
      id: payload.id,
      username: payload.username,
      first_name: payload.first_name || '',
      last_name: payload.last_name || '',
      email: payload.email || '',
    });
    setIsAuthenticated(true);
    setIsLoading(false);
  }, []);

  const login = async (username, password) => {
    const data = await loginUser({ username, password });
    localStorage.setItem(ACCESS_KEY, data.access);
    localStorage.setItem(REFRESH_KEY, data.refresh);
    setUser(data.user);
    setIsAuthenticated(true);
    return data;
  };

  const register = async (payload) => {
    const data = await registerUser(payload);
    return data;
  };

  const logout = async () => {
    const refresh = localStorage.getItem(REFRESH_KEY);

    try {
      if (refresh) {
        await logoutUser({ refresh });
      }
    } catch {
      // Ignore logout API failures and clear client state regardless.
    } finally {
      localStorage.removeItem(ACCESS_KEY);
      localStorage.removeItem(REFRESH_KEY);
      setUser(null);
      setIsAuthenticated(false);
    }
  };

  const value = useMemo(
    () => ({
      user,
      isAuthenticated,
      isLoading,
      login,
      logout,
      register,
    }),
    [user, isAuthenticated, isLoading]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}


export function useAuth() {
  return useContext(AuthContext);
}
