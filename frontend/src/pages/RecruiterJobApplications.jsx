import { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { jobsApi } from '../api/jobs.js';
import { extractErrorMessage } from '../api/client.js';
import { StatusBadge } from '../components/StatusBadge.jsx';

const PAGE_SIZE = 20;

export function RecruiterJobApplications() {
  const { jobId } = useParams();

  const [job, setJob] = useState(null);
  const [applications, setApplications] = useState([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);

  // Client-side filters
  const [statusFilter, setStatusFilter] = useState('all'); // 'all' | 'applied' | 'reviewed'
  const [decisionFilter, setDecisionFilter] = useState('all'); // 'all' | 'shortlist' | 'hold' | 'reject' | 'none'

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [notFound, setNotFound] = useState(false);

  const loadData = useCallback(async (currentJobId, currentOffset) => {
    try {
      const [jobData, appsData] = await Promise.all([
        jobsApi.getJobById(Number(currentJobId)),
        jobsApi.getJobApplications(Number(currentJobId), {
          limit: PAGE_SIZE,
          offset: currentOffset,
        }),
      ]);

      setJob(jobData);
      setApplications(appsData?.items || []);
      setTotal(appsData?.total || 0);
      setError(null);
      setNotFound(false);
    } catch (err) {
      if (err.response?.status === 404) {
        setNotFound(true);
      } else {
        setError(extractErrorMessage(err, 'Failed to load applicants for this job opening.'));
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let isMounted = true;

    async function init() {
      try {
        const [jobData, appsData] = await Promise.all([
          jobsApi.getJobById(Number(jobId)),
          jobsApi.getJobApplications(Number(jobId), {
            limit: PAGE_SIZE,
            offset,
          }),
        ]);

        if (!isMounted) return;

        setJob(jobData);
        setApplications(appsData?.items || []);
        setTotal(appsData?.total || 0);
        setError(null);
        setNotFound(false);
      } catch (err) {
        if (!isMounted) return;
        if (err.response?.status === 404) {
          setNotFound(true);
        } else {
          setError(extractErrorMessage(err, 'Failed to load applicants for this job opening.'));
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
  }, [jobId, offset]);

  const handleRetry = () => {
    setLoading(true);
    setNotFound(false);
    setError(null);
    loadData(jobId, offset);
  };

  const handlePrevPage = () => {
    if (offset >= PAGE_SIZE) {
      setLoading(true);
      setOffset(offset - PAGE_SIZE);
    }
  };

  const handleNextPage = () => {
    if (offset + PAGE_SIZE < total) {
      setLoading(true);
      setOffset(offset + PAGE_SIZE);
    }
  };

  // Client-side filtering on current page items
  const filteredApplicants = applications.filter((app) => {
    // 1. Status filter
    if (statusFilter !== 'all') {
      const normalizedStatus = (app.status || '').toLowerCase().trim();
      if (statusFilter === 'applied') {
        if (normalizedStatus !== 'applied' && normalizedStatus !== 'awaiting_review') {
          return false;
        }
      } else if (statusFilter === 'reviewed') {
        if (normalizedStatus !== 'reviewed') {
          return false;
        }
      }
    }

    // 2. Decision filter
    if (decisionFilter !== 'all') {
      const decision = (app.latest_review_decision || '').toLowerCase().trim();
      if (decisionFilter === 'none') {
        if (decision) return false;
      } else {
        if (decision !== decisionFilter) return false;
      }
    }

    return true;
  });

  const totalPages = Math.ceil(total / PAGE_SIZE);
  const currentPage = Math.floor(offset / PAGE_SIZE) + 1;
  const isFilterActive = statusFilter !== 'all' || decisionFilter !== 'all';

  // 404 Not Found state
  if (notFound) {
    return (
      <div className="max-w-xl mx-auto py-16 px-4 text-center">
        <div className="h-16 w-16 rounded-2xl bg-slate-800 text-slate-400 mx-auto flex items-center justify-center mb-4 border border-slate-700">
          <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h2 className="text-xl font-bold text-white mb-2">Job Not Found</h2>
        <p className="text-sm text-slate-400 mb-6 max-w-md mx-auto">
          The requested job opening does not exist or belongs to another recruiter account.
        </p>
        <Link
          to="/recruiter/jobs"
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold shadow-md shadow-indigo-600/20 transition-all"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Back to Job Postings
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-6xl animate-in fade-in duration-200">
      {/* Top back navigation */}
      <div>
        <Link
          to="/recruiter/jobs"
          className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-400 hover:text-indigo-400 transition-colors"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back to Job Postings
        </Link>
      </div>

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-2xl md:text-3xl font-bold text-white tracking-tight">
              {job ? job.title : `Job #${jobId}`}
            </h1>
            {job && <StatusBadge status={job.status} />}
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Review submitted candidate applications and access evaluation dossiers.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-xs font-semibold px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-300">
            Total Applicants: <span className="text-white font-bold">{total}</span>
          </span>
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-sm text-rose-300 flex items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <svg className="w-5 h-5 shrink-0 text-rose-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>{error}</span>
          </div>
          <button
            type="button"
            onClick={handleRetry}
            className="px-3 py-1.5 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 text-xs font-semibold text-rose-200 transition-colors cursor-pointer"
          >
            Retry
          </button>
        </div>
      )}

      {/* Filter Controls Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-md flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3">
          {/* Status Filter */}
          <div className="flex items-center gap-2">
            <label htmlFor="status-filter" className="text-xs font-semibold text-slate-400">
              Status:
            </label>
            <select
              id="status-filter"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              <option value="all">All Statuses</option>
              <option value="applied">Applied / Awaiting review</option>
              <option value="reviewed">Reviewed</option>
            </select>
          </div>

          {/* Decision Filter */}
          <div className="flex items-center gap-2">
            <label htmlFor="decision-filter" className="text-xs font-semibold text-slate-400">
              Latest Decision:
            </label>
            <select
              id="decision-filter"
              value={decisionFilter}
              onChange={(e) => setDecisionFilter(e.target.value)}
              className="px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              <option value="all">All Decisions</option>
              <option value="shortlist">Shortlisted</option>
              <option value="hold">On Hold</option>
              <option value="reject">Rejected</option>
              <option value="none">No Decision Yet</option>
            </select>
          </div>

          {isFilterActive && (
            <button
              type="button"
              onClick={() => {
                setStatusFilter('all');
                setDecisionFilter('all');
              }}
              className="text-xs text-slate-400 hover:text-indigo-400 underline transition-colors cursor-pointer"
            >
              Reset Filters
            </button>
          )}
        </div>

        {/* Note when total > limit */}
        {total > PAGE_SIZE && (
          <span className="text-[11px] text-amber-400/90 font-medium bg-amber-500/10 px-2.5 py-1 rounded-lg border border-amber-500/20">
            Filters apply to the current page only
          </span>
        )}
      </div>

      {/* Loading Skeletons */}
      {loading ? (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
          {[...Array(4)].map((_, i) => (
            <div
              key={i}
              className="py-4 border-b border-slate-800 last:border-0 flex items-center justify-between animate-pulse"
            >
              <div className="space-y-2 w-1/3">
                <div className="h-4 bg-slate-800 rounded w-3/4" />
                <div className="h-3 bg-slate-800/60 rounded w-1/2" />
              </div>
              <div className="h-6 bg-slate-800 rounded-full w-24" />
            </div>
          ))}
        </div>
      ) : total === 0 ? (
        /* Empty State: No applicants at all */
        <div className="text-center py-16 px-4 bg-slate-900 border border-slate-800 rounded-2xl shadow-xl">
          <div className="h-14 w-14 rounded-2xl bg-indigo-500/10 text-indigo-400 mx-auto flex items-center justify-center mb-4">
            <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          </div>
          <h3 className="text-base font-bold text-white">No applicants yet</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto mt-1 mb-5">
            Candidates who apply to this open job posting will appear here in the review pipeline.
          </p>
          <Link
            to="/recruiter/jobs"
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition-colors inline-block"
          >
            Back to Job Postings
          </Link>
        </div>
      ) : filteredApplicants.length === 0 ? (
        /* Empty State: Filter matched 0 items on this page */
        <div className="text-center py-12 px-4 bg-slate-900 border border-slate-800 rounded-2xl shadow-xl">
          <p className="text-sm font-semibold text-white">No applicants match the selected filters on this page.</p>
          <p className="text-xs text-slate-400 mt-1 mb-4">
            Try choosing different filter options or resetting the filters.
          </p>
          <button
            type="button"
            onClick={() => {
              setStatusFilter('all');
              setDecisionFilter('all');
            }}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition-colors cursor-pointer"
          >
            Clear Filters
          </button>
        </div>
      ) : (
        /* Applicants Table */
        <div className="bg-slate-900 border border-slate-800 rounded-2xl shadow-xl overflow-hidden">
          <div className="p-4 border-b border-slate-800 flex items-center justify-between">
            <h2 className="text-sm font-bold text-white uppercase tracking-wider">
              Candidate Applications ({filteredApplicants.length})
            </h2>
            <span className="text-xs text-slate-400">
              Page {currentPage} of {totalPages || 1}
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="text-xs uppercase bg-slate-950/60 text-slate-400 border-b border-slate-800">
                <tr>
                  <th scope="col" className="px-6 py-3.5 font-semibold">Candidate</th>
                  <th scope="col" className="px-6 py-3.5 font-semibold">Headline</th>
                  <th scope="col" className="px-6 py-3.5 font-semibold">Date Applied</th>
                  <th scope="col" className="px-6 py-3.5 font-semibold">Application Status</th>
                  <th scope="col" className="px-6 py-3.5 font-semibold">Latest Decision</th>
                  <th scope="col" className="px-6 py-3.5 font-semibold text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {filteredApplicants.map((app) => (
                  <tr key={app.id} className="hover:bg-slate-800/40 transition-colors">
                    {/* Candidate Name */}
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="h-8 w-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center font-bold text-indigo-400 text-xs shrink-0">
                          {app.candidate_name?.charAt(0)?.toUpperCase() || 'C'}
                        </div>
                        <div className="min-w-0">
                          <p className="font-semibold text-white truncate max-w-xs">
                            {app.candidate_name}
                          </p>
                          <p className="text-[11px] text-slate-400">
                            Candidate #{app.candidate_id}
                          </p>
                        </div>
                      </div>
                    </td>

                    {/* Headline */}
                    <td className="px-6 py-4">
                      <span className="text-xs text-slate-300 truncate max-w-xs block">
                        {app.headline || <span className="text-slate-400 italic">Not specified</span>}
                      </span>
                    </td>

                    {/* Applied Date */}
                    <td className="px-6 py-4 text-xs text-slate-400 whitespace-nowrap">
                      {new Date(app.created_at).toLocaleDateString()}
                    </td>

                    {/* Application Status (Recruiter Audience) */}
                    <td className="px-6 py-4 whitespace-nowrap">
                      <StatusBadge status={app.status} audience="recruiter" />
                    </td>

                    {/* Latest Decision */}
                    <td className="px-6 py-4 whitespace-nowrap">
                      {app.latest_review_decision ? (
                        <StatusBadge status={app.latest_review_decision} />
                      ) : (
                        <span className="text-xs text-slate-400 font-medium">None</span>
                      )}
                    </td>

                    {/* Action */}
                    <td className="px-6 py-4 text-right whitespace-nowrap">
                      <Link
                        to={`/recruiter/applications/${app.id}`}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/20 transition-all cursor-pointer"
                      >
                        <span>View Dossier</span>
                        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Pagination controls */}
      {!loading && total > PAGE_SIZE && (
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-4 border-t border-slate-800 text-xs">
          <p className="text-slate-400">
            Showing <span className="font-semibold text-white">{offset + 1}</span> to{' '}
            <span className="font-semibold text-white">{Math.min(offset + PAGE_SIZE, total)}</span> of{' '}
            <span className="font-semibold text-white">{total}</span> applicants
          </p>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handlePrevPage}
              disabled={offset === 0}
              className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors cursor-pointer"
            >
              Previous
            </button>
            <span className="px-2 font-medium text-slate-400">
              Page {currentPage} of {totalPages}
            </span>
            <button
              type="button"
              onClick={handleNextPage}
              disabled={offset + PAGE_SIZE >= total}
              className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors cursor-pointer"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
