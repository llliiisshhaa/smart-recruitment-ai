import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { jobsApi } from '../api/jobs.js';
import { extractErrorMessage } from '../api/client.js';
import { StatusBadge } from '../components/StatusBadge.jsx';
import { ConfirmModal } from '../components/ConfirmModal.jsx';
import { JobModal } from '../components/recruiter/JobModal.jsx';

export function RecruiterJobs() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [successBanner, setSuccessBanner] = useState(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all'); // 'all' | 'open' | 'closed'

  // Modals state
  const [isJobModalOpen, setIsJobModalOpen] = useState(false);
  const [editingJob, setEditingJob] = useState(null);
  const [confirmState, setConfirmState] = useState({
    isOpen: false,
    job: null,
    action: 'close',
    isLoading: false,
  });

  // Initial fetch
  useEffect(() => {
    let isMounted = true;

    jobsApi
      .getMyJobs()
      .then((data) => {
        if (isMounted) {
          setJobs(data || []);
          setError(null);
        }
      })
      .catch((err) => {
        if (isMounted) {
          const msg = extractErrorMessage(
            err,
            'Failed to load your job postings. Please ensure the backend service is running.'
          );
          setError(msg);
        }
      })
      .finally(() => {
        if (isMounted) {
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  // Manual refresh handler
  const handleRefresh = async () => {
    setRefreshing(true);
    setError(null);

    try {
      const data = await jobsApi.getMyJobs();
      setJobs(data || []);
    } catch (err) {
      const msg = extractErrorMessage(err, 'Failed to refresh job postings.');
      setError(msg);
    } finally {
      setRefreshing(false);
    }
  };

  // Auto-dismiss success notification
  useEffect(() => {
    if (successBanner) {
      const timer = setTimeout(() => setSuccessBanner(null), 4000);
      return () => clearTimeout(timer);
    }
  }, [successBanner]);

  // Open Create Modal
  const handleOpenCreateModal = () => {
    setEditingJob(null);
    setIsJobModalOpen(true);
  };

  // Open Edit Modal
  const handleOpenEditModal = (job) => {
    setEditingJob(job);
    setIsJobModalOpen(true);
  };

  // Callback on successful create or update
  const handleJobSaved = (savedJob) => {
    setJobs((prevJobs) => {
      const exists = prevJobs.some((j) => j.id === savedJob.id);
      if (exists) {
        return prevJobs.map((j) => (j.id === savedJob.id ? savedJob : j));
      }
      return [savedJob, ...prevJobs];
    });

    const isEdit = Boolean(editingJob);
    setSuccessBanner(
      isEdit
        ? `Job opening "${savedJob.title}" updated successfully.`
        : `Job opening "${savedJob.title}" created and published successfully.`
    );
  };

  // Prompt confirmation for closing job
  const handlePromptStatusToggle = (job) => {
    if (job.status === 'open') {
      setConfirmState({
        isOpen: true,
        job,
        action: 'close',
        isLoading: false,
      });
    } else {
      // Reopening directly
      executeStatusChange(job, 'open');
    }
  };

  // Execute PATCH /jobs/:id/status
  const executeStatusChange = async (job, targetStatus) => {
    setConfirmState((prev) => ({ ...prev, isLoading: true }));
    setError(null);

    try {
      const updated = await jobsApi.updateJobStatus(job.id, targetStatus);
      setJobs((prev) => prev.map((j) => (j.id === updated.id ? updated : j)));
      setSuccessBanner(
        targetStatus === 'open'
          ? `Role "${updated.title}" reopened. Candidates can now submit applications.`
          : `Role "${updated.title}" closed. No new applications will be accepted.`
      );
      setConfirmState({ isOpen: false, job: null, action: 'close', isLoading: false });
    } catch (err) {
      const msg = extractErrorMessage(err, 'Failed to update job status.');
      setError(msg);
      setConfirmState((prev) => ({ ...prev, isLoading: false }));
    }
  };

  // Filter jobs based on search query and status tab
  const filteredJobs = jobs.filter((job) => {
    const matchesStatus =
      statusFilter === 'all' ? true : job.status === statusFilter;

    const query = searchQuery.trim().toLowerCase();
    if (!query) return matchesStatus;

    const matchesTitle = job.title?.toLowerCase().includes(query);
    const matchesDesc = job.description?.toLowerCase().includes(query);
    const matchesSkill = job.skills?.some((s) =>
      s.name?.toLowerCase().includes(query)
    );

    return matchesStatus && (matchesTitle || matchesDesc || matchesSkill);
  });

  const totalOpen = jobs.filter((j) => j.status === 'open').length;
  const totalClosed = jobs.filter((j) => j.status === 'closed').length;

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      {/* Header & Main Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
              Job Postings
            </h1>
            {!loading && (
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-slate-800 text-indigo-400 border border-slate-700">
                {jobs.length} {jobs.length === 1 ? 'Role' : 'Roles'}
              </span>
            )}
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Create and manage job openings, specify technical skill criteria, and review applicant counts.
          </p>
        </div>

        <div className="flex items-center gap-3 self-start sm:self-auto">
          {/* Refresh button */}
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition-colors disabled:opacity-50 flex items-center gap-2 cursor-pointer shadow-sm"
            title="Refresh job list"
          >
            <svg
              className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin text-indigo-400' : ''}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            <span>{refreshing ? 'Refreshing...' : 'Refresh'}</span>
          </button>

          {/* Post New Job Button */}
          <button
            onClick={handleOpenCreateModal}
            className="px-4 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/25 transition-all flex items-center gap-1.5 cursor-pointer"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            <span>Post New Job</span>
          </button>
        </div>
      </div>

      {/* Success Notification Banner */}
      {successBanner && (
        <div
          className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-300 flex items-center justify-between gap-3 animate-in fade-in"
          role="status"
        >
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4 shrink-0 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <span>{successBanner}</span>
          </div>
          <button
            onClick={() => setSuccessBanner(null)}
            className="text-emerald-400 hover:text-emerald-200"
          >
            &times;
          </button>
        </div>
      )}

      {/* Error Alert Banner */}
      {error && (
        <div
          className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs text-rose-300 flex items-center justify-between gap-3"
          role="alert"
        >
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4 shrink-0 text-rose-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>{error}</span>
          </div>
          <button
            onClick={handleRefresh}
            className="px-2.5 py-1 rounded bg-rose-500/20 hover:bg-rose-500/30 text-rose-200 font-semibold transition-colors"
          >
            Retry
          </button>
        </div>
      )}

      {/* Search and Status Filter Toolbar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-slate-900/60 p-3 rounded-2xl border border-slate-800">
        {/* Search Input */}
        <div className="relative flex-1 max-w-md">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by title, description, or skill..."
            className="w-full pl-9 pr-4 py-2 bg-slate-950 border border-slate-800 rounded-xl text-white placeholder-slate-500 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all"
          />
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-white"
            >
              &times;
            </button>
          )}
        </div>

        {/* Status Filter Tabs */}
        <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-xl border border-slate-800 shrink-0">
          <button
            onClick={() => setStatusFilter('all')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              statusFilter === 'all'
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-white hover:bg-slate-900'
            }`}
          >
            All ({jobs.length})
          </button>
          <button
            onClick={() => setStatusFilter('open')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              statusFilter === 'open'
                ? 'bg-emerald-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-white hover:bg-slate-900'
            }`}
          >
            Open ({totalOpen})
          </button>
          <button
            onClick={() => setStatusFilter('closed')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              statusFilter === 'closed'
                ? 'bg-slate-700 text-white shadow-sm'
                : 'text-slate-400 hover:text-white hover:bg-slate-900'
            }`}
          >
            Closed ({totalClosed})
          </button>
        </div>
      </div>

      {/* Loading Skeleton */}
      {loading ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 animate-pulse">
          {[1, 2, 3, 4].map((i) => (
            <div
              key={i}
              className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-lg space-y-4"
            >
              <div className="flex justify-between items-start">
                <div className="h-6 w-48 bg-slate-800 rounded-lg" />
                <div className="h-6 w-16 bg-slate-800 rounded-full" />
              </div>
              <div className="h-4 w-32 bg-slate-800/60 rounded" />
              <div className="h-12 w-full bg-slate-800/40 rounded-lg" />
              <div className="flex gap-2">
                <div className="h-6 w-20 bg-slate-800 rounded" />
                <div className="h-6 w-24 bg-slate-800 rounded" />
              </div>
              <div className="pt-4 border-t border-slate-800 flex justify-between">
                <div className="h-8 w-28 bg-slate-800 rounded-xl" />
                <div className="h-8 w-20 bg-slate-800 rounded-xl" />
              </div>
            </div>
          ))}
        </div>
      ) : filteredJobs.length === 0 ? (
        /* Empty State */
        <div className="flex flex-col items-center justify-center text-center p-10 md:p-14 border border-dashed border-slate-800 rounded-2xl bg-slate-950/40">
          <div className="h-14 w-14 rounded-2xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center mb-4">
            <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          </div>
          <h2 className="text-base font-bold text-white mb-1">
            {jobs.length === 0 ? 'No Job Openings Yet' : 'No Matching Jobs Found'}
          </h2>
          <p className="text-xs text-slate-400 max-w-sm mb-6">
            {jobs.length === 0
              ? 'You have not created any job postings yet. Publish your first opening to begin collecting candidate resumes.'
              : `No job postings match "${searchQuery}" under the "${statusFilter}" filter.`}
          </p>
          {jobs.length === 0 ? (
            <button
              onClick={handleOpenCreateModal}
              className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/25 transition-all inline-flex items-center gap-2 cursor-pointer"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              <span>Post Your First Job</span>
            </button>
          ) : (
            <button
              onClick={() => {
                setSearchQuery('');
                setStatusFilter('all');
              }}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition-colors"
            >
              Clear Filters
            </button>
          )}
        </div>
      ) : (
        /* Job Cards Grid */
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {filteredJobs.map((job) => {
            const requiredSkills = (job.skills || []).filter(
              (s) => s.importance === 'required'
            );
            const preferredSkills = (job.skills || []).filter(
              (s) => s.importance === 'preferred'
            );

            const postedDate = job.created_at
              ? new Date(job.created_at).toLocaleDateString(undefined, {
                  year: 'numeric',
                  month: 'short',
                  day: 'numeric',
                })
              : 'Recently';

            const appCount = job.application_count ?? 0;

            return (
              <div
                key={job.id}
                className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-lg hover:border-slate-700/80 transition-all flex flex-col justify-between group"
              >
                <div>
                  {/* Card Header: Title, Status, and Date */}
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <div className="min-w-0 flex-1">
                      <h2 className="text-lg font-bold text-white group-hover:text-indigo-300 transition-colors leading-snug">
                        {job.title}
                      </h2>
                      <p className="text-[11px] text-slate-400 mt-0.5">
                        Posted on {postedDate}
                      </p>
                    </div>
                    <StatusBadge status={job.status} />
                  </div>

                  {/* Requirements Pills */}
                  <div className="flex flex-wrap items-center gap-2 my-3">
                    {/* Minimum Experience */}
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-300 font-medium">
                      <svg className="w-3.5 h-3.5 text-indigo-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span>
                        {job.min_experience_years === 0
                          ? 'No experience required'
                          : `${job.min_experience_years}+ yrs exp`}
                      </span>
                    </span>

                    {/* Education */}
                    {job.education && (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-300 font-medium">
                        <svg className="w-3.5 h-3.5 text-indigo-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 14l9-5-9-5-9 5 9 5z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z" />
                        </svg>
                        <span className="truncate max-w-[180px]" title={job.education}>
                          {job.education}
                        </span>
                      </span>
                    )}

                    {/* Applicant Count Pill */}
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-xs text-indigo-300 font-semibold">
                      <svg className="w-3.5 h-3.5 text-indigo-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                      </svg>
                      <span>
                        {appCount} {appCount === 1 ? 'Applicant' : 'Applicants'}
                      </span>
                    </span>
                  </div>

                  {/* Description */}
                  <p className="text-xs text-slate-400 line-clamp-3 leading-relaxed mb-4">
                    {job.description}
                  </p>

                  {/* Skills Section */}
                  <div className="space-y-2 mb-4">
                    {/* Required Skills */}
                    {requiredSkills.length > 0 && (
                      <div className="flex flex-wrap items-center gap-1.5">
                        <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-wider mr-1">
                          Required:
                        </span>
                        {requiredSkills.map((s) => (
                          <span
                            key={s.skill_id}
                            className="inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-medium bg-indigo-500/10 text-indigo-300 border border-indigo-500/25"
                          >
                            {s.name}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Preferred Skills */}
                    {preferredSkills.length > 0 && (
                      <div className="flex flex-wrap items-center gap-1.5">
                        <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mr-1">
                          Preferred:
                        </span>
                        {preferredSkills.map((s) => (
                          <span
                            key={s.skill_id}
                            className="inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-medium bg-slate-800 text-slate-400 border border-slate-700/80"
                          >
                            {s.name}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                {/* Card Actions Footer */}
                <div className="pt-4 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-2">
                  {/* View Applicants button */}
                  <Link
                    to={`/recruiter/jobs/${job.id}/applications`}
                    className="px-3.5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/20 transition-all flex items-center gap-1.5"
                  >
                    <span>View Applicants</span>
                    <span className="px-1.5 py-0.2 rounded-full bg-indigo-800/80 text-[10px] font-bold">
                      {appCount}
                    </span>
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </Link>

                  <div className="flex items-center gap-2">
                    {/* Edit Job button */}
                    <button
                      onClick={() => handleOpenEditModal(job)}
                      className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition-colors flex items-center gap-1.5 cursor-pointer"
                      title="Edit job requirements"
                    >
                      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                      </svg>
                      <span>Edit</span>
                    </button>

                    {/* Status Toggle (Close / Reopen) */}
                    {job.status === 'open' ? (
                      <button
                        onClick={() => handlePromptStatusToggle(job)}
                        className="px-3 py-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/25 text-xs font-medium transition-colors cursor-pointer"
                        title="Close job role"
                      >
                        Close Role
                      </button>
                    ) : (
                      <button
                        onClick={() => handlePromptStatusToggle(job)}
                        className="px-3 py-1.5 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/25 text-xs font-medium transition-colors cursor-pointer"
                        title="Reopen job role"
                      >
                        Reopen Role
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Reusable Job Create / Edit Modal */}
      <JobModal
        isOpen={isJobModalOpen}
        job={editingJob}
        onClose={() => setIsJobModalOpen(false)}
        onSuccess={handleJobSaved}
      />

      {/* Close Confirmation Modal */}
      <ConfirmModal
        isOpen={confirmState.isOpen}
        title="Close Job Opening"
        message={`Are you sure you want to close "${confirmState.job?.title}"? Once closed, candidates will no longer be able to browse or submit applications for this role.`}
        confirmText="Yes, Close Job"
        cancelText="Keep Open"
        confirmVariant="danger"
        isLoading={confirmState.isLoading}
        onConfirm={() => executeStatusChange(confirmState.job, 'closed')}
        onCancel={() =>
          setConfirmState({ isOpen: false, job: null, action: 'close', isLoading: false })
        }
      />
    </div>
  );
}
