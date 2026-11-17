import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { candidateApi } from '../../api/candidate.js';
import { resumesApi } from '../../api/resumes.js';
import { jobsApi } from '../../api/jobs.js';
import { extractErrorMessage } from '../../api/client.js';
import { StatusBadge } from '../StatusBadge.jsx';
import { LoadingSpinner } from '../LoadingSpinner.jsx';

export function ApplyModal({ isOpen, onClose, job, onSuccess }) {
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState(null);
  const [profile, setProfile] = useState(null);
  const [resumes, setResumes] = useState([]);
  const [selectedResumeId, setSelectedResumeId] = useState(null);

  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);
  const [isDuplicateApp, setIsDuplicateApp] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(false);

  useEffect(() => {
    if (!isOpen) return;

    let isMounted = true;
    async function loadData() {
      try {
        const [profileData, resumesData] = await Promise.all([
          candidateApi.getProfile(),
          resumesApi.listResumes(),
        ]);

        if (!isMounted) return;

        setProfile(profileData);

        // Sort resumes: parsed ones first
        const sortedResumes = [...(resumesData || [])].sort((a, b) => {
          if (a.parse_status === 'parsed' && b.parse_status !== 'parsed') return -1;
          if (a.parse_status !== 'parsed' && b.parse_status === 'parsed') return 1;
          return 0;
        });

        setResumes(sortedResumes);

        if (sortedResumes.length > 0) {
          // Pre-select first parsed resume if present, or first resume
          setSelectedResumeId(sortedResumes[0].id);
        } else {
          setSelectedResumeId(null);
        }
      } catch (err) {
        if (isMounted) {
          setFetchError(extractErrorMessage(err, 'Failed to load candidate information.'));
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    loadData();

    return () => {
      isMounted = false;
    };
  }, [isOpen, job?.id]);

  const handleClose = () => {
    if (submitting) return;
    setSubmitError(null);
    setIsDuplicateApp(false);
    setSubmitSuccess(false);
    onClose();
  };

  if (!isOpen) return null;

  const hasConsent = Boolean(profile?.consent_given_at);
  const hasResumes = resumes.length > 0;
  const canSubmit = hasConsent && hasResumes && Boolean(selectedResumeId) && !submitting && !submitSuccess;

  const handleSubmit = async (e) => {
    e?.preventDefault();
    if (!canSubmit) return;

    setSubmitting(true);
    setSubmitError(null);
    setIsDuplicateApp(false);

    try {
      const application = await jobsApi.applyToJob(job.id, {
        resume_id: selectedResumeId,
      });

      setSubmitSuccess(true);
      if (onSuccess) {
        onSuccess(application);
      }

      // Briefly show confirmation then redirect to candidate applications
      setTimeout(() => {
        onClose();
        navigate('/candidate/applications');
      }, 1200);
    } catch (err) {
      if (err.response?.status === 409) {
        setIsDuplicateApp(true);
        setSubmitError('You have already applied to this job.');
      } else {
        setSubmitError(extractErrorMessage(err, 'Failed to submit application.'));
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in"
      role="dialog"
      aria-modal="true"
      aria-labelledby="apply-modal-title"
    >
      <div className="w-full max-w-lg bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl flex flex-col max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="p-6 border-b border-slate-800 flex items-start justify-between gap-4">
          <div>
            <h2 id="apply-modal-title" className="text-lg font-bold text-white tracking-tight">
              Apply for {job?.title || 'Position'}
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              {job?.company_name || 'Hiring Company'} &bull; Min {job?.min_experience_years || 0} years experience
            </p>
          </div>
          <button
            type="button"
            onClick={handleClose}
            disabled={submitting}
            className="text-slate-400 hover:text-white p-1.5 rounded-lg hover:bg-slate-800 transition-colors disabled:opacity-50"
            aria-label="Close dialog"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-5 flex-1">
          {loading ? (
            <div className="py-8">
              <LoadingSpinner text="Checking candidate profile and resumes..." />
            </div>
          ) : fetchError ? (
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-sm flex items-start justify-between gap-3">
              <span>{fetchError}</span>
              <button
                type="button"
                onClick={() => {
                  setLoading(true);
                  setFetchError(null);
                  Promise.all([candidateApi.getProfile(), resumesApi.listResumes()])
                    .then(([p, r]) => {
                      setProfile(p);
                      setResumes(r || []);
                    })
                    .catch((err) => setFetchError(extractErrorMessage(err)))
                    .finally(() => setLoading(false));
                }}
                className="text-xs font-semibold underline hover:text-white shrink-0"
              >
                Retry
              </button>
            </div>
          ) : (
            <>
              {/* Success Notification */}
              {submitSuccess && (
                <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-sm flex items-center gap-2">
                  <svg className="w-5 h-5 shrink-0 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span>Application submitted successfully! Redirecting to your applications...</span>
                </div>
              )}

              {/* Error Notification */}
              {submitError && (
                <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-sm flex flex-col gap-2">
                  <div className="flex items-start gap-2">
                    <svg className="w-5 h-5 shrink-0 text-rose-400 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span>{submitError}</span>
                  </div>
                  {isDuplicateApp && (
                    <Link
                      to="/candidate/applications"
                      onClick={onClose}
                      className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 underline ml-7"
                    >
                      View your existing application &rarr;
                    </Link>
                  )}
                </div>
              )}

              {/* Consent Guard */}
              {!hasConsent && (
                <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-200 text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="flex items-start gap-2.5">
                    <svg className="w-4 h-4 shrink-0 text-amber-400 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                    <div>
                      <p className="font-semibold text-white">Data Processing Consent Required</p>
                      <p className="text-amber-200/80 mt-0.5">
                        You must provide consent in your candidate profile before submitting applications.
                      </p>
                    </div>
                  </div>
                  <Link
                    to="/candidate/profile"
                    onClick={onClose}
                    className="px-3 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs shrink-0 transition-colors inline-block text-center"
                  >
                    Go to Profile &rarr;
                  </Link>
                </div>
              )}

              {/* Resumes Guard */}
              {!hasResumes && (
                <div className="p-4 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-200 text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="flex items-start gap-2.5">
                    <svg className="w-4 h-4 shrink-0 text-indigo-400 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <div>
                      <p className="font-semibold text-white">No Resumes Uploaded</p>
                      <p className="text-indigo-200/80 mt-0.5">
                        Please upload at least one resume document before applying for jobs.
                      </p>
                    </div>
                  </div>
                  <Link
                    to="/candidate/resumes"
                    onClick={onClose}
                    className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs shrink-0 transition-colors inline-block text-center"
                  >
                    Go to Resumes &rarr;
                  </Link>
                </div>
              )}

              {/* Resume Selection Section */}
              {hasResumes && (
                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                    Select Resume to Attach
                  </label>
                  <p className="text-xs text-slate-400 mb-3">
                    Choose which uploaded CV you want recruiters to review for this position.
                  </p>

                  <div className="space-y-2.5 max-h-56 overflow-y-auto pr-1">
                    {resumes.map((resume) => {
                      const isSelected = selectedResumeId === resume.id;
                      return (
                        <div
                          key={resume.id}
                          onClick={() => !submitting && setSelectedResumeId(resume.id)}
                          className={`p-3.5 rounded-xl border transition-all cursor-pointer flex items-center justify-between gap-3 ${
                            isSelected
                              ? 'bg-indigo-600/10 border-indigo-500 shadow-sm shadow-indigo-500/10'
                              : 'bg-slate-950/40 border-slate-800 hover:border-slate-700 hover:bg-slate-800/40'
                          }`}
                        >
                          <div className="flex items-center gap-3 min-w-0">
                            <input
                              type="radio"
                              name="selectedResume"
                              value={resume.id}
                              checked={isSelected}
                              onChange={() => setSelectedResumeId(resume.id)}
                              disabled={submitting}
                              className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-slate-700 bg-slate-900"
                            />
                            <div className="min-w-0">
                              <p className="text-sm font-medium text-white truncate">
                                {resume.original_filename}
                              </p>
                              <p className="text-[11px] text-slate-400">
                                Uploaded {new Date(resume.created_at).toLocaleDateString()}
                              </p>
                            </div>
                          </div>
                          <div className="shrink-0">
                            <StatusBadge status={resume.parse_status} />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer actions */}
        <div className="p-6 border-t border-slate-800 bg-slate-900/60 flex items-center justify-end gap-3">
          <button
            type="button"
            onClick={handleClose}
            disabled={submitting}
            className="px-4 py-2 text-sm font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-xl transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleSubmit}
            disabled={!canSubmit}
            className="px-5 py-2 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-500 rounded-xl shadow-lg shadow-indigo-600/25 transition-all disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {submitting ? (
              <>
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                <span>Submitting Application...</span>
              </>
            ) : submitSuccess ? (
              <span>Submitted</span>
            ) : (
              <span>Submit Application</span>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
