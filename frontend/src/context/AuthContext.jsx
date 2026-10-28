import { useState, useEffect, useCallback } from 'react';
import { AuthContext } from './authContextInstance.js';
import { authApi } from '../api/auth.js';
import { TOKEN_STORAGE_KEY } from '../api/client.js';

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Logout handler
  const logout = useCallback(() => {
    try {
      localStorage.removeItem(TOKEN_STORAGE_KEY);
    } catch {
      // Ignore
    }
    setUser(null);
  }, []);

  // Fetch current user details with stored token
  const refreshUser = useCallback(async () => {
    try {
      const token = localStorage.getItem(TOKEN_STORAGE_KEY);
      if (!token) {
        setUser(null);
        return null;
      }
      const userData = await authApi.getMe();
      setUser(userData);
      return userData;
    } catch {
      // Invalid or expired token
      logout();
      return null;
    }
  }, [logout]);

  // Login handler
  const login = useCallback(async (credentials) => {
    const tokenResponse = await authApi.login(credentials);
    const token = tokenResponse.access_token;
    localStorage.setItem(TOKEN_STORAGE_KEY, token);
    const userData = await authApi.getMe();
    setUser(userData);
    return userData;
  }, []);

  // Register handler
  const register = useCallback(async (payload) => {
    const registeredUser = await authApi.register(payload);
    return registeredUser;
  }, []);

  // Initialize authentication on app mount
  useEffect(() => {
    let isMounted = true;

    async function initAuth() {
      try {
        const token = localStorage.getItem(TOKEN_STORAGE_KEY);
        if (token) {
          const userData = await authApi.getMe();
          if (isMounted) {
            setUser(userData);
          }
        } else {
          if (isMounted) {
            setUser(null);
          }
        }
      } catch {
        if (isMounted) {
          logout();
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    initAuth();

    // Listen to unauthorized events from axios interceptor
    const handleUnauthorized = () => {
      logout();
    };
    window.addEventListener('auth:unauthorized', handleUnauthorized);

    return () => {
      isMounted = false;
      window.removeEventListener('auth:unauthorized', handleUnauthorized);
    };
  }, [logout]);

  const value = {
    user,
    loading,
    isAuthenticated: Boolean(user),
    isCandidate: user?.role === 'candidate',
    login,
    register,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
