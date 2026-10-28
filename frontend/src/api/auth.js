import { apiClient } from './client.js';

export const authApi = {
  /**
   * Register a new user account (candidate or recruiter).
   * @param {{ email: string, password: string, full_name: string, role: string }} payload
   */
  async register(payload) {
    const response = await apiClient.post('/auth/register', payload);
    return response.data;
  },

  /**
   * Authenticate a user and receive a JWT token.
   * @param {{ email: string, password: string }} credentials
   */
  async login(credentials) {
    const response = await apiClient.post('/auth/login', credentials);
    return response.data;
  },

  /**
   * Retrieve the currently authenticated user's profile and role.
   */
  async getMe() {
    const response = await apiClient.get('/auth/me');
    return response.data;
  },
};
