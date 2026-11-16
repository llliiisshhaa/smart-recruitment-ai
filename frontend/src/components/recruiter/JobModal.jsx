import { useState } from 'react';
import { jobsApi } from '../../api/jobs.js';
import { extractErrorMessage } from '../../api/client.js';
import { SkillPicker } from './SkillPicker.jsx';

/**
 * Inner form component initialized with job props directly.
 * Avoids cascading set-state-in-effect warnings.
 */
function JobForm({ job, isEditing, onClose, onSuccess }) {
  const [title, setTitle] = useState(job?.title || '');
  const [description, setDescription] = useState(job?.description || '');
  const [minExperience, setMinExperience] = useState(job?.min_experience_years ?? 0);
  const [education, setEducation] = useState(job?.education || '');
  const [skills, setSkills] = useState(
    (job?.skills || []).map((s) => ({
      skill_id: s.skill_id,
      name: s.name,
      category: s.category,
      importance: s.importance || 'required',
    }))
  );

  const [errors, setErrors] = useState({});
  const [apiError, setApiError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const validate = () => {
    const newErrors = {};

    const trimmedTitle = title.trim();
    if (!trimmedTitle) {
      newErrors.title = 'Job title is required.';
    } else if (trimmedTitle.length < 3 || trimmedTitle.length > 150) {
      newErrors.title = 'Job title must be between 3 and 150 characters.';
    }

    const trimmedDesc = description.trim();
    if (!trimmedDesc) {
      newErrors.description = 'Job description is required.';
    }

    const exp = Number(minExperience);
    if (isNaN(exp) || exp < 0 || exp > 40) {
      newErrors.minExperience = 'Experience must be between 0 and 40 years.';
    }

    if (education && education.trim().length > 255) {
      newErrors.education = 'Education requirement cannot exceed 255 characters.';
    }

    if (!skills || skills.length === 0) {
      newErrors.skills = 'Please add at least one technical or core skill.';
    } else {
      const hasRequired = skills.some((s) => s.importance === 'required');
      if (!hasRequired) {
        newErrors.skills = 'At least one skill must be marked as "Required".';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setApiError(null);

    if (!validate()) return;

    setIsSubmitting(true);

    const payload = {
      title: title.trim(),
      description: description.trim(),
      min_experience_years: Number(minExperience) || 0,
      education: education.trim() || null,
      skills: skills.map((s) => ({
        skill_id: s.skill_id,
        importance: s.importance,
      })),
    };

    try {
      let savedJob;
      if (isEditing) {
        savedJob = await jobsApi.updateJob(job.id, payload);
      } else {
        savedJob = await jobsApi.createJob(payload);
      }

      onSuccess(savedJob);
      onClose();
    } catch (err) {
      const errorMsg = extractErrorMessage(
        err,
        isEditing
          ? 'Failed to update job posting. Please verify inputs.'
          : 'Failed to create job posting. Please verify inputs.'
      );
      setApiError(errorMsg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {/* Global API Error Alert */}
      {apiError && (
        <div
          className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs text-rose-300 flex items-center gap-2"
          role="alert"
        >
          <svg className="w-4 h-4 shrink-0 text-rose-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>{apiError}</span>
        </div>
      )}

      {/* Job Title */}
      <div>
        <label htmlFor="job-title" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
          Job Title <span className="text-rose-400">*</span>
        </label>
        <input
          id="job-title"
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="e.g. Senior Python Backend Engineer"
          maxLength={150}
          className={`w-full px-4 py-2.5 bg-slate-950 border rounded-xl text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all ${
            errors.title ? 'border-rose-500' : 'border-slate-800'
          }`}
        />
        {errors.title && <p className="text-xs text-rose-400 mt-1">{errors.title}</p>}
      </div>

      {/* Experience & Education Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label htmlFor="job-exp" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
            Min Experience (Years) <span className="text-rose-400">*</span>
          </label>
          <input
            id="job-exp"
            type="number"
            min="0"
            max="40"
            value={minExperience}
            onChange={(e) => setMinExperience(e.target.value)}
            className={`w-full px-4 py-2.5 bg-slate-950 border rounded-xl text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all ${
              errors.minExperience ? 'border-rose-500' : 'border-slate-800'
            }`}
          />
          {errors.minExperience && (
            <p className="text-xs text-rose-400 mt-1">{errors.minExperience}</p>
          )}
        </div>

        <div>
          <label htmlFor="job-edu" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
            Education Requirement
          </label>
          <input
            id="job-edu"
            type="text"
            value={education}
            onChange={(e) => setEducation(e.target.value)}
            placeholder="e.g. Bachelor's in Computer Science"
            maxLength={255}
            className={`w-full px-4 py-2.5 bg-slate-950 border rounded-xl text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all ${
              errors.education ? 'border-rose-500' : 'border-slate-800'
            }`}
          />
          {errors.education && <p className="text-xs text-rose-400 mt-1">{errors.education}</p>}
        </div>
      </div>

      {/* Job Description */}
      <div>
        <label htmlFor="job-desc" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
          Job Description & Responsibilities <span className="text-rose-400">*</span>
        </label>
        <textarea
          id="job-desc"
          rows={4}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Outline the role expectations, key responsibilities, deliverables, and team dynamics..."
          className={`w-full px-4 py-2.5 bg-slate-950 border rounded-xl text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all resize-y ${
            errors.description ? 'border-rose-500' : 'border-slate-800'
          }`}
        />
        {errors.description && (
          <p className="text-xs text-rose-400 mt-1">{errors.description}</p>
        )}
      </div>

      {/* Reusable SkillPicker */}
      <SkillPicker
        selectedSkills={skills}
        onChange={setSkills}
        error={errors.skills}
      />

      {/* Form Actions */}
      <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
        <button
          type="button"
          onClick={onClose}
          disabled={isSubmitting}
          className="px-4 py-2 text-sm font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-xl transition-colors disabled:opacity-50 cursor-pointer"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={isSubmitting}
          className="px-5 py-2.5 text-sm font-semibold rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white shadow-lg shadow-indigo-600/25 transition-all disabled:opacity-50 flex items-center gap-2 cursor-pointer"
        >
          {isSubmitting ? (
            <>
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
              <span>{isEditing ? 'Saving Changes...' : 'Creating Job...'}</span>
            </>
          ) : (
            <span>{isEditing ? 'Save Changes' : 'Create Job Opening'}</span>
          )}
        </button>
      </div>
    </form>
  );
}

/**
 * Reusable modal container for creating and editing recruiter job postings.
 */
export function JobModal({ isOpen, job = null, onClose, onSuccess }) {
  if (!isOpen) return null;

  const isEditing = Boolean(job && job.id);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm overflow-y-auto animate-in fade-in"
      role="dialog"
      aria-modal="true"
      aria-labelledby="job-modal-title"
    >
      <div className="w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-2xl p-6 md:p-8 shadow-2xl my-8 relative">
        {/* Modal Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800 mb-6">
          <div>
            <h2 id="job-modal-title" className="text-xl font-bold text-white tracking-tight">
              {isEditing ? 'Edit Job Posting' : 'Create New Job Opening'}
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              {isEditing
                ? 'Update role specifications, requirements, and required technical skills.'
                : 'Define role details and key skill criteria to evaluate candidates.'}
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
            aria-label="Close modal"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Modal Form */}
        <JobForm
          key={job ? `edit-${job.id}` : 'create'}
          job={job}
          isEditing={isEditing}
          onClose={onClose}
          onSuccess={onSuccess}
        />
      </div>
    </div>
  );
}
