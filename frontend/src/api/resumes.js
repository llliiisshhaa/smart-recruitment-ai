import { apiClient } from './client.js';

export const resumesApi = {
  /**
   * List all resumes uploaded by the authenticated candidate.
   */
  async listResumes() {
    const response = await apiClient.get('/resumes');
    return response.data;
  },

  /**
   * Get specific resume details.
   * @param {number} id
   */
  async getResume(id) {
    const response = await apiClient.get(`/resumes/${id}`);
    return response.data;
  },

  /**
   * Upload a PDF or DOCX resume.
   * @param {File} file
   * @param {Function} [onUploadProgress]
   */
  async uploadResume(file, onUploadProgress) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post('/resumes', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress,
    });
    return response.data;
  },

  /**
   * Download a resume file as binary blob.
   * @param {number} id
   */
  async downloadResume(id) {
    const response = await apiClient.get(`/resumes/${id}/download`, {
      responseType: 'blob',
    });
    return response;
  },

  /**
   * Delete an uploaded resume and its database record.
   * @param {number} id
   */
  async deleteResume(id) {
    const response = await apiClient.delete(`/resumes/${id}`);
    return response.data;
  },
};
