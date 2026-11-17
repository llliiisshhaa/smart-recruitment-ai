import { apiClient } from './client.js';

export const jobsApi = {
  /**
   * Browse available open jobs for candidate.
   * Supports ?q= keyword search, limit, and offset pagination.
   * @param {{ q?: string, limit?: number, offset?: number }} [params]
   * @returns {Promise<{ items: Array<JobResponse>, total: number, limit: number, offset: number }>}
   */
  async browseJobs(params) {
    const response = await apiClient.get('/jobs', { params });
    return response.data;
  },

  /**
   * Apply to an open job opening with a selected resume.
   * @param {number} jobId
   * @param {{ resume_id: number }} payload
   * @returns {Promise<CandidateApplicationItem>}
   */
  async applyToJob(jobId, payload) {
    const response = await apiClient.post(`/jobs/${jobId}/apply`, payload);
    return response.data;
  },

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
   * List applicants for a job owned by the authenticated recruiter.
   * @param {number} jobId
   * @param {{ limit?: number, offset?: number }} [params]
   * @returns {Promise<{ items: Array<ApplicantSummaryItem>, total: number, limit: number, offset: number }>}
   */
  async getJobApplications(jobId, params) {
    const response = await apiClient.get(`/jobs/${jobId}/applications`, { params });
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

  /**
   * Stateless rule-based job description analyzer.
   * Suggests skills, experience, education, responsibilities, and flags potentially biased wording.
   * @param {{ title?: string, description: string }} payload
   * @returns {Promise<{
   *   skills: Array<{ skill_id: number, name: string, suggested_importance: 'required' | 'preferred', evidence_text: string }>,
   *   min_experience_years: number | null,
   *   education: string | null,
   *   responsibilities: Array<string>,
   *   fairness_warnings: Array<{ matched_phrase: string, category: string, suggested_rewrite: string }>,
   *   meta: Record<string, any>
   * }>}
   */
  async analyzeJobDescription(payload) {
    const response = await apiClient.post('/jobs/analyze', payload);
    return response.data;
  },
};

