import { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { jobsApi } from '../api/jobs.js';
import { extractErrorMessage } from '../api/client.js';
import { StatusBadge } from '../components/StatusBadge.jsx';
import { LoadingSpinner } from '../components/LoadingSpinner.jsx';
import { ApplyModal } from '../components/candidate/ApplyModal.jsx';

export function CandidateJobDetail() {
  const { jobId } = useParams();

  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [notFound, setNotFound] = useState(false);

  // Apply modal state
  const [applyModalOpen, setApplyModalOpen] = useState(false);

  const loadJob = useCallback(async (id) => {
    try {
      const data = await jobsApi.getJobById(Number(id));
      if (!data || data.status !== 'open') {
        setNotFound(true);
      } else {
        setJob(data);
        setNotFound(false);
      }
      setError(null);
    } catch (err) {
      if (err.response?.status === 404) {
        setNotFound(true);
      } else {
        setError(extractErrorMessage(err, 'Could not retrieve job posting details.'));
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!jobId) return;

    let isMounted = true;
    async function init() {
      try {
        const data = await jobsApi.getJobById(Number(jobId));
        if (!isMounted) return;
        if (!data || data.status !== 'open') {
          setNotFound(true);
        } else {
          setJob(data);
          setNotFound(false);
        }
      } catch (err) {
        if (!isMounted) return;
        if (err.response?.status === 404) {
          setNotFound(true);
        } else {
          setError(extractErrorMessage(err, 'Could not retrieve job posting details.'));
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    init();

    return () => {
      isMounted = false;
    };
  }, [jobId]);

  const handleRetry = () => {
    setLoading(true);
    setNotFound(false);
    setError(null);
    loadJob(jobId);
  };

  if (loading) {
    return <LoadingSpinner text="Loading job posting details..." />;
  }

  // Clean 404 / closed state
  if (notFound) {
    return (
      <div className="max-w-2xl mx-auto py-16 px-4 text-center">
        <div className="h-16 w-16 rounded-2xl bg-slate-800 text-slate-400 mx-auto flex items-center justify-center mb-4 border border-slate-700">
          <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h2 className="text-xl font-bold text-white mb-2">Job Not Found</h2>
        <p className="text-sm text-slate-400 mb-6 max-w-md mx-auto">
          The job posting you are looking for does not exist, has been closed, or is no longer accepting applications.
        </p>
        <Link
          to="/candidate/jobs"
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold shadow-md shadow-indigo-600/20 transition-all"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Browse Open Positions
        </Link>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="max-w-3xl mx-auto p-6 bg-slate-900 border border-slate-800 rounded-2xl space-y-4 text-center">
        <div className="text-rose-400 text-sm font-medium">{error}</div>
        <div className="flex items-center justify-center gap-3">
          <Link
            to="/candidate/jobs"
            className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 hover:text-white text-xs font-semibold"
          >
            &larr; Back to Jobs
          </Link>
          <button
            type="button"
            onClick={handleRetry}
            className="px-4 py-2 rounded-xl bg-indigo-600 text-white text-xs font-semibold hover:bg-indigo-500"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const requiredSkills = (job?.skills || []).filter((s) => s.importance === 'required');
  const preferredSkills = (job?.skills || []).filter((s) => s.importance === 'preferred');

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-in fade-in duration-200">
      {/* Top back navigation */}
      <div>
        <Link
          to="/candidate/jobs"
          className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-400 hover:text-indigo-400 transition-colors"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back to all jobs
        </Link>
      </div>

      {/* Main Job Card */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 md:p-8 shadow-xl space-y-6">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-4 pb-6 border-b border-slate-800">
          <div className="space-y-2">
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className="text-2xl md:text-3xl font-bold text-white tracking-tight">
                {job.title}
              </h1>
              <StatusBadge status={job.status} />
            </div>
            <div className="flex items-center gap-2 text-sm text-slate-400 flex-wrap">
              <span className="font-semibold text-slate-200">
                {job.company_name || 'Hiring Company'}
              </span>
              <span>&bull;</span>
              <span>
                Posted {new Date(job.created_at).toLocaleDateString()}
              </span>
            </div>
          </div>

          <button
            type="button"
            onClick={() => setApplyModalOpen(true)}
            className="self-start md:self-center px-6 py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-semibold text-sm shadow-lg shadow-indigo-600/25 transition-all flex items-center gap-2 shrink-0 cursor-pointer"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Apply for this Role
          </button>
        </div>

        {/* Quick Spec Metrics */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
          <div className="p-4 rounded-xl bg-slate-950/40 border border-slate-800">
            <p className="text-xs text-slate-400 uppercase tracking-wider font-medium">Experience</p>
            <p className="text-base font-semibold text-white mt-1">
              {job.min_experience_years === 0
                ? 'Entry Level / None required'
                : `${job.min_experience_years}+ years`}
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/40 border border-slate-800">
            <p className="text-xs text-slate-400 uppercase tracking-wider font-medium">Education</p>
            <p className="text-base font-semibold text-white mt-1 truncate">
              {job.education || 'Not specified'}
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/40 border border-slate-800 sm:col-span-2 md:col-span-1">
            <p className="text-xs text-slate-400 uppercase tracking-wider font-medium">Position Status</p>
            <p className="text-base font-semibold text-emerald-400 mt-1 capitalize">
              {job.status}
            </p>
          </div>
        </div>

        {/* Required Skills */}
        <div className="space-y-3">
          <h2 className="text-sm font-bold text-white uppercase tracking-wider">
            Required Skills ({requiredSkills.length})
          </h2>
          {requiredSkills.length === 0 ? (
            <p className="text-xs text-slate-400 italic">No mandatory skills specified.</p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {requiredSkills.map((s) => (
                <div
                  key={s.skill_id}
                  className="px-3 py-1.5 rounded-xl bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 text-xs font-medium flex items-center gap-2"
                >
                  <span className="h-1.5 w-1.5 rounded-full bg-indigo-400" />
                  <span className="font-semibold text-white">{s.name}</span>
                  <span className="text-[11px] text-indigo-400/80">({s.category})</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Preferred Skills */}
        {preferredSkills.length > 0 && (
          <div className="space-y-3">
            <h2 className="text-sm font-bold text-white uppercase tracking-wider">
              Preferred Skills ({preferredSkills.length})
            </h2>
            <div className="flex flex-wrap gap-2">
              {preferredSkills.map((s) => (
                <div
                  key={s.skill_id}
                  className="px-3 py-1.5 rounded-xl bg-slate-800 text-slate-300 border border-slate-700 text-xs font-medium flex items-center gap-2"
                >
                  <span className="h-1.5 w-1.5 rounded-full bg-slate-400" />
                  <span className="font-semibold text-white">{s.name}</span>
                  <span className="text-[11px] text-slate-400">({s.category})</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Job Description */}
        <div className="space-y-3 pt-2 border-t border-slate-800">
          <h2 className="text-sm font-bold text-white uppercase tracking-wider">
            Job Description & Responsibilities
          </h2>
          <div className="text-sm text-slate-300 leading-relaxed whitespace-pre-line bg-slate-950/20 p-5 rounded-2xl border border-slate-800/60">
            {job.description}
          </div>
        </div>

        {/* Bottom Apply CTA */}
        <div className="pt-4 border-t border-slate-800 flex items-center justify-between">
          <Link
            to="/candidate/jobs"
            className="text-xs text-slate-400 hover:text-white transition-colors"
          >
            &larr; Back to Open Jobs
          </Link>
          <button
            type="button"
            onClick={() => setApplyModalOpen(true)}
            className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs shadow-md shadow-indigo-600/20 transition-all cursor-pointer"
          >
            Apply for this Role
          </button>
        </div>
      </div>

      {/* Apply Modal */}
      <ApplyModal
        isOpen={applyModalOpen}
        onClose={() => setApplyModalOpen(false)}
        job={job}
      />
    </div>
  );
}
