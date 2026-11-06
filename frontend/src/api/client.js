import axios from 'axios';

/**
 * Backend base URL configuration.
 * Reads from VITE_API_URL with a fallback to http://localhost:8000.
 */
const rawApiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
export const API_BASE_URL = rawApiUrl.replace(/\/+$/, '');

export const TOKEN_STORAGE_KEY = 'smart_recruitment_token';

/**
 * Security Note on Token Storage:
 * Storing JWT tokens in browser localStorage is used here for simple single-page
 * session persistence across page refreshes. While localStorage is susceptible to
 * Cross-Site Scripting (XSS) if untrusted scripts run in the origin, our application
 * mitigates this by avoiding dangerous innerHTML injections, enforcing strict Content
 * Security boundaries, sanitizing user inputs, and never logging tokens or passwords.
 */

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Accept': 'application/json',
  },
  timeout: 15000,
});

// Request interceptor to attach bearer token
apiClient.interceptors.request.use(
  (config) => {
    try {
      const token = localStorage.getItem(TOKEN_STORAGE_KEY);
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    } catch {
      // Storage access may fail in rare sandboxed environments
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle common error codes
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear token if expired or unauthorized
      try {
        localStorage.removeItem(TOKEN_STORAGE_KEY);
        // Dispatch custom event so AuthContext can handle logout cleanly
        window.dispatchEvent(new CustomEvent('auth:unauthorized'));
      } catch {
        // Ignore
      }
    }
    return Promise.reject(error);
  }
);

/**
 * Helper to extract human-readable error messages from FastAPI responses.
 */
export function extractErrorMessage(error, defaultMessage = 'An unexpected error occurred') {
  if (!error) return defaultMessage;

  const detail = error.response?.data?.detail;
  if (typeof detail === 'string') {
    return detail;
  }

  // Handle FastAPI Pydantic validation error lists: [{ loc: [...], msg: "..." }]
  if (Array.isArray(detail) && detail.length > 0) {
    return detail.map((err) => err.msg || JSON.stringify(err)).join('. ');
  }

  if (error.response?.data?.message) {
    return error.response.data.message;
  }

  if (error.message) {
    if (error.code === 'ERR_NETWORK') {
      return `Unable to connect to the backend server at ${API_BASE_URL}. Please ensure the server is running.`;
    }
    return error.message;
  }

  return defaultMessage;
}
