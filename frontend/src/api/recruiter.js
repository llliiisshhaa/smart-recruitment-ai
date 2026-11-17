import { apiClient } from './client.js';

export const recruiterApi = {
  /**
   * Fetch aggregated recruiter dashboard statistics.
   * Includes active/closed job counts, total applications, review status counts,
   * applications per job breakdown, and latest 5 recent applications.
   * Scoped strictly to the authenticated recruiter.
   * @returns {Promise<{
   *   active_jobs: number,
   *   closed_jobs: number,
   *   total_applications: number,
   *   awaiting_review: number,
   *   shortlisted: number,
   *   on_hold: number,
   *   rejected: number,
   *   applications_per_job: Array<{ job_id: number, title: string, count: number }>,
   *   recent_applications: Array<{ application_id: number, candidate_name: string, job_title: string, status: string, applied_at: string }>
   * }>}
   */
  async getStats() {
    const response = await apiClient.get('/recruiters/me/stats');
    return response.data;
  },

  /**
   * Fetch authenticated recruiter profile.
   */
  async getProfile() {
    const response = await apiClient.get('/recruiters/me');
    return response.data;
  },

  /**
   * Create or update recruiter company profile.
   * @param {{ company_name: string }} data
   */
  async updateProfile(data) {
    const response = await apiClient.put('/recruiters/me', data);
    return response.data;
  },

  /**
   * Fetch comprehensive applicant evaluation dossier.
   * Contact information is masked unless revealContact is explicitly set to true.
   * @param {number} applicationId
   * @param {boolean} [revealContact=false]
   * @returns {Promise<ApplicantDetailResponse>}
   */
  async getApplicationDetail(applicationId, revealContact = false) {
    const response = await apiClient.get(`/applications/${applicationId}`, {
      params: { reveal_contact: revealContact },
    });
    return response.data;
  },

  /**
   * Download the applicant's resume as a binary blob.
   * @param {number} applicationId
   * @returns {Promise<AxiosResponse<Blob>>}
   */
  async downloadApplicationResume(applicationId) {
    return apiClient.get(`/applications/${applicationId}/resume`, {
      responseType: 'blob',
    });
  },

  /**
   * Submit a recruiter review decision on an applicant.
   * @param {number} applicationId
   * @param {{ decision: 'shortlist' | 'hold' | 'reject', notes?: string }} payload
   * @returns {Promise<ReviewResponse>}
   */
  async submitReview(applicationId, payload) {
    const response = await apiClient.post(`/applications/${applicationId}/review`, payload);
    return response.data;
  },
};

