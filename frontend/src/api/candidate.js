import { apiClient } from './client.js';

export const candidateApi = {
  /**
   * Get the candidate's profile details.
   */
  async getProfile() {
    const response = await apiClient.get('/candidates/me');
    return response.data;
  },

  /**
   * Update candidate profile information (phone, headline, location).
   * @param {{ phone?: string, headline?: string, location?: string }} data
   */
  async updateProfile(data) {
    const response = await apiClient.put('/candidates/me', data);
    return response.data;
  },

  /**
   * Record candidate consent for data and resume processing.
   */
  async giveConsent() {
    const response = await apiClient.post('/candidates/me/consent');
    return response.data;
  },

  /**
   * Fetch candidate's submitted job applications (if available).
   */
  async getMyApplications() {
    const response = await apiClient.get('/applications/mine');
    return response.data;
  },
};
