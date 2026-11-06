import { apiClient } from './client.js';

export const healthApi = {
  /**
   * Check backend server and database connectivity status.
   */
  async checkHealth() {
    const response = await apiClient.get('/health');
    return response.data;
  },
};
