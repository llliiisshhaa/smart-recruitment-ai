import { apiClient } from './client.js';

export const jobsApi = {
  /**
   * List all job postings belonging to the authenticated recruiter.
   * Includes application_count and associated taxonomy skills.
   * @returns {Promise<Array<RecruiterJobResponse>>}
   */
  async getMyJobs() {
    const response = await apiClient.get('/jobs/mine');
    return response.data;
  },

  /**
   * Get job posting details by ID.
   * @param {number} jobId
   * @returns {Promise<RecruiterJobResponse>}
   */
  async getJobById(jobId) {
    const response = await apiClient.get(`/jobs/${jobId}`);
    return response.data;
  },

  /**
   * Create a new job opening.
   * @param {{
   *   title: string,
   *   description: string,
   *   min_experience_years: number,
   *   education?: string,
   *   skills: Array<{ skill_id: number, importance: 'required' | 'preferred' }>
   * }} payload
   * @returns {Promise<RecruiterJobResponse>}
   */
  async createJob(payload) {
    const response = await apiClient.post('/jobs', payload);
    return response.data;
  },

  /**
   * Update an existing job opening.
   * @param {number} jobId
   * @param {{
   *   title: string,
   *   description: string,
   *   min_experience_years: number,
   *   education?: string,
   *   skills: Array<{ skill_id: number, importance: 'required' | 'preferred' }>
   * }} payload
   * @returns {Promise<RecruiterJobResponse>}
   */
  async updateJob(jobId, payload) {
    const response = await apiClient.put(`/jobs/${jobId}`, payload);
    return response.data;
  },

  /**
   * Open or close a job opening.
   * @param {number} jobId
   * @param {'open' | 'closed'} status
   * @returns {Promise<RecruiterJobResponse>}
   */
  async updateJobStatus(jobId, status) {
    const response = await apiClient.patch(`/jobs/${jobId}/status`, { status });
    return response.data;
  },
};

