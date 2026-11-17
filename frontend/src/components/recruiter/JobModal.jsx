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

  // Job description analyzer state
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analyzeError, setAnalyzeError] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [suggestedSkillsImportance, setSuggestedSkillsImportance] = useState({});

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

  const handleAnalyze = async () => {
    if (isAnalyzing || isSubmitting) return;
    if (description.trim().length < 30) return;

    setIsAnalyzing(true);
    setAnalyzeError(null);

    try {
      const data = await jobsApi.analyzeJobDescription({
        title: title.trim(),
        description: description.trim(),
      });
      setAnalysisResult(data);

      const initialImportance = {};
      (data.skills || []).forEach((s) => {
        initialImportance[s.skill_id] = s.suggested_importance || 'required';
      });
      setSuggestedSkillsImportance(initialImportance);
    } catch (err) {
      setAnalyzeError(
        extractErrorMessage(err, 'Failed to analyze job description. Please try again.')
      );
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleToggleSuggestedImportance = (skillId) => {
    setSuggestedSkillsImportance((prev) => ({
      ...prev,
      [skillId]: prev[skillId] === 'required' ? 'preferred' : 'required',
    }));
  };

  const handleAddSuggestedSkill = (suggestedSkill) => {
    if (skills.some((s) => s.skill_id === suggestedSkill.skill_id)) {
      return;
    }

    const importance =
      suggestedSkillsImportance[suggestedSkill.skill_id] ||
      suggestedSkill.suggested_importance ||
      'required';

    setSkills((prev) => [
      ...prev,
      {
        skill_id: suggestedSkill.skill_id,
        name: suggestedSkill.name,
        importance,
      },
    ]);

    if (errors.skills) {
      setErrors((prev) => ({ ...prev, skills: null }));
    }
  };

  const handleApplyExperience = (exp) => {
    if (exp !== null && exp !== undefined) {
      setMinExperience(exp);
      if (errors.minExperience) {
        setErrors((prev) => ({ ...prev, minExperience: null }));
      }
    }
  };

  const handleApplyEducation = (edu) => {
    if (edu) {
      setEducation(edu);
      if (errors.education) {
        setErrors((prev) => ({ ...prev, education: null }));
      }
    }
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
          className={`w-full px-4 py-2.5 bg-slate-950 border rounded-xl text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all ${errors.title ? 'border-rose-500' : 'border-slate-800'
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
            className={`w-full px-4 py-2.5 bg-slate-950 border rounded-xl text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all ${errors.minExperience ? 'border-rose-500' : 'border-slate-800'
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
            className={`w-full px-4 py-2.5 bg-slate-950 border rounded-xl text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all ${errors.education ? 'border-rose-500' : 'border-slate-800'
              }`}
          />
          {errors.education && <p className="text-xs text-rose-400 mt-1">{errors.education}</p>}
        </div>
      </div>

      {/* Job Description */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <label htmlFor="job-desc" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
            Job Description & Responsibilities <span className="text-rose-400">*</span>
          </label>
          <button
            type="button"
            onClick={handleAnalyze}
            disabled={description.trim().length < 30 || isAnalyzing || isSubmitting}
            className="inline-flex items-center gap-1.5 px-3 py-1 text-xs font-medium rounded-lg bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 hover:bg-indigo-500/20 hover:text-white transition-all disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
            title={description.trim().length < 30 ? 'Enter at least 30 characters to analyze' : 'Analyze job description for skill and requirement suggestions'}
          >
            {isAnalyzing ? (
              <>
                <span className="h-3 w-3 animate-spin rounded-full border-2 border-indigo-300 border-t-transparent" />
                <span>Analyzing...</span>
              </>
            ) : (
              <>
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                <span>Analyze description</span>
              </>
            )}
          </button>
        </div>
        <textarea
          id="job-desc"
          rows={4}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Outline the role expectations, key responsibilities, deliverables, and team dynamics..."
          className={`w-full px-4 py-2.5 bg-slate-950 border rounded-xl text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all resize-y ${errors.description ? 'border-rose-500' : 'border-slate-800'
            }`}
        />
        {errors.description && (
          <p className="text-xs text-rose-400 mt-1">{errors.description}</p>
        )}
      </div>

      {/* Analysis Error Alert */}
      {analyzeError && (
        <div
          className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs text-rose-300 flex items-center justify-between gap-2"
          role="alert"
        >
          <span>{analyzeError}</span>
          <button
            type="button"
            onClick={() => setAnalyzeError(null)}
            className="text-rose-400 hover:text-white text-sm font-bold"
          >
            &times;
          </button>
        </div>
      )}

      {/* Analysis Suggestions Panel */}
      {analysisResult && (
        <div className="p-4 rounded-xl bg-slate-950/80 border border-indigo-500/30 space-y-4">
          <div className="flex items-start justify-between gap-3 pb-3 border-b border-slate-800">
            <div>
              <div className="flex items-center gap-2">
                <span className="flex h-2 w-2 rounded-full bg-indigo-400" />
                <h3 className="text-sm font-semibold text-white">Analysis Suggestions</h3>
              </div>
              <p className="text-xs text-slate-400 italic mt-1">
                Suggestions are generated by rules, not by a model. Review before applying.
              </p>
            </div>
            <button
              type="button"
              onClick={() => setAnalysisResult(null)}
              className="text-xs text-slate-500 hover:text-slate-300 transition-colors cursor-pointer px-2 py-1 rounded hover:bg-slate-800"
              title="Dismiss suggestions"
            >
              Dismiss
            </button>
          </div>

          {/* Fairness warnings */}
          {analysisResult.fairness_warnings && analysisResult.fairness_warnings.length > 0 && (
            <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-xs text-amber-200 space-y-2">
              <div className="flex items-center gap-2 font-semibold text-amber-300">
                <svg className="w-4 h-4 text-amber-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <span>Potential Inclusivity Considerations ({analysisResult.fairness_warnings.length})</span>
              </div>
              <ul className="space-y-1.5 pl-5 list-disc text-amber-200/90">
                {analysisResult.fairness_warnings.map((w, idx) => (
                  <li key={idx} className="leading-relaxed">
                    <span className="font-semibold text-amber-100">&ldquo;{w.matched_phrase}&rdquo;</span>{' '}
                    <span className="text-amber-400/80 text-[11px] uppercase tracking-wider">[{w.category}]</span>
                    {w.suggested_rewrite && (
                      <span className="block text-amber-300/80 text-[11px] mt-0.5">
                        Suggested rewrite: {w.suggested_rewrite}
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Experience & Education Suggestions */}
          {(analysisResult.min_experience_years !== null || analysisResult.education) && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              {analysisResult.min_experience_years !== null && (
                <div className="p-3 bg-slate-900 border border-slate-800 rounded-lg flex items-center justify-between gap-2">
                  <div>
                    <span className="text-slate-400 block text-[11px]">Suggested Min Experience</span>
                    <span className="text-white font-medium">{analysisResult.min_experience_years} years</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleApplyExperience(analysisResult.min_experience_years)}
                    className="px-2.5 py-1 text-xs font-medium rounded-md bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 hover:text-white border border-indigo-500/30 transition-colors cursor-pointer"
                  >
                    Apply
                  </button>
                </div>
              )}

              {analysisResult.education && (
                <div className="p-3 bg-slate-900 border border-slate-800 rounded-lg flex items-center justify-between gap-2">
                  <div className="truncate">
                    <span className="text-slate-400 block text-[11px]">Suggested Education</span>
                    <span className="text-white font-medium truncate block">{analysisResult.education}</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleApplyEducation(analysisResult.education)}
                    className="px-2.5 py-1 text-xs font-medium rounded-md bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 hover:text-white border border-indigo-500/30 transition-colors cursor-pointer shrink-0"
                  >
                    Apply
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Suggested Skills */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Suggested Skills {analysisResult.skills ? `(${analysisResult.skills.length})` : ''}
              </span>
            </div>

            {(!analysisResult.skills || analysisResult.skills.length === 0) ? (
              <p className="text-xs text-slate-500 italic p-2 bg-slate-900 rounded border border-slate-800">
                No taxonomy skills matched in the description.
              </p>
            ) : (
              <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                {analysisResult.skills.map((s) => {
                  const isSelected = skills.some((sk) => sk.skill_id === s.skill_id);
                  const currentImportance =
                    suggestedSkillsImportance[s.skill_id] || s.suggested_importance || 'required';

                  return (
                    <div
                      key={s.skill_id}
                      className="p-2.5 bg-slate-900/90 border border-slate-800 rounded-lg space-y-1.5"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium text-white capitalize">{s.name}</span>
                          <button
                            type="button"
                            onClick={() => handleToggleSuggestedImportance(s.skill_id)}
                            disabled={isSelected}
                            className={`px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider rounded border transition-colors cursor-pointer ${currentImportance === 'required'
                                ? 'bg-rose-500/10 text-rose-300 border-rose-500/30'
                                : 'bg-slate-800 text-slate-300 border-slate-700'
                              } ${isSelected ? 'opacity-60 cursor-not-allowed' : ''}`}
                            title={isSelected ? 'Already added to job' : 'Toggle required/preferred'}
                          >
                            {currentImportance}
                          </button>
                        </div>

                        {isSelected ? (
                          <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
                            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                            Added
                          </span>
                        ) : (
                          <button
                            type="button"
                            onClick={() => handleAddSuggestedSkill(s)}
                            className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold rounded bg-indigo-600 hover:bg-indigo-500 text-white shadow-sm transition-colors cursor-pointer"
                          >
                            <span>Add</span>
                          </button>
                        )}
                      </div>

                      {s.evidence_text && (
                        <p className="text-[11px] text-slate-400 italic bg-slate-950/60 px-2 py-1 rounded border border-slate-800/80 leading-relaxed">
                          &ldquo;{s.evidence_text}&rdquo;
                        </p>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Extracted Responsibilities */}
          {analysisResult.responsibilities && analysisResult.responsibilities.length > 0 && (
            <div className="space-y-1.5 text-xs">
              <span className="text-slate-400 font-semibold block text-[11px] uppercase tracking-wider">
                Extracted Responsibilities ({analysisResult.responsibilities.length})
              </span>
              <ul className="space-y-1 pl-4 list-disc text-slate-300 bg-slate-900 p-2.5 rounded-lg border border-slate-800">
                {analysisResult.responsibilities.map((resp, idx) => (
                  <li key={idx} className="leading-relaxed">
                    {resp}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

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
      <div className="w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-2xl p-6 md:p-8 shadow-2xl my-8 relative max-h-[90vh] overflow-y-auto">
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
