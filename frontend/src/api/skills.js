import { apiClient } from './client.js';

export const skillsApi = {
  /**
   * Search standardized skills taxonomy.
   * @param {string} [query] - Optional name search term
   * @returns {Promise<Array<{ id: number, name: string, category: string }>>}
   */
  async searchSkills(query = '') {
    const params = query && query.trim() ? { q: query.trim() } : {};
    const response = await apiClient.get('/skills', { params });
    return response.data;
  },
};

