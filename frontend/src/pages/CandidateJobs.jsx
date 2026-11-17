import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { jobsApi } from '../api/jobs.js';
import { extractErrorMessage } from '../api/client.js';

const PAGE_SIZE = 10;

export function CandidateJobs() {
  const [jobs, setJobs] = useState([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Debounce search query by 300ms
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(searchTerm.trim());
      setOffset(0);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchTerm]);

  const loadJobs = useCallback(async (query, pageOffset) => {
    try {
      const data = await jobsApi.browseJobs({
        q: query || undefined,
        limit: PAGE_SIZE,
        offset: pageOffset,
      });
      setJobs(data?.items || []);
      setTotal(data?.total || 0);
      setError(null);
    } catch (err) {
      setError(extractErrorMessage(err, 'Failed to load open job postings.'));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let isMounted = true;

    async function init() {
      try {
        const data = await jobsApi.browseJobs({
          q: debouncedQuery || undefined,
          limit: PAGE_SIZE,
          offset,
        });
        if (isMounted) {
          setJobs(data?.items || []);
          setTotal(data?.total || 0);
          setError(null);
        }
      } catch (err) {
        if (isMounted) {
          setError(extractErrorMessage(err, 'Failed to load open job postings.'));
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
  }, [debouncedQuery, offset]);

  const handleRetry = () => {
    setLoading(true);
    loadJobs(debouncedQuery, offset);
  };

  const totalPages = Math.ceil(total / PAGE_SIZE);
  const currentPage = Math.floor(offset / PAGE_SIZE) + 1;

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

  return (
    <div className="space-y-6 max-w-6xl animate-in fade-in duration-200">
      {/* Header and Search */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-white tracking-tight">
            Explore Open Positions
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Discover opportunities matching your skills and background.
          </p>
        </div>

        {/* Search Input */}
        <div className="relative w-full md:w-80">
          <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by job title..."
            className="w-full pl-10 pr-9 py-2 rounded-xl bg-slate-900 border border-slate-800 text-sm text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all"
          />
          {searchTerm && (
            <button
              type="button"
              onClick={() => setSearchTerm('')}
              className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-white"
              aria-label="Clear search"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* Error state */}
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
            className="px-3 py-1.5 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 text-xs font-semibold text-rose-200 transition-colors"
          >
            Retry
          </button>
        </div>
      )}

      {/* Loading Skeletons */}
      {loading ? (
        <div className="space-y-4">
          {[...Array(4)].map((_, i) => (
            <div
              key={i}
              className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 animate-pulse space-y-4"
            >
              <div className="flex justify-between items-start">
                <div className="space-y-2 w-1/3">
                  <div className="h-5 bg-slate-800 rounded-lg w-3/4" />
                  <div className="h-3 bg-slate-800/60 rounded w-1/2" />
                </div>
                <div className="h-8 bg-slate-800 rounded-xl w-24" />
              </div>
              <div className="h-3 bg-slate-800/40 rounded w-5/6" />
              <div className="flex gap-2">
                <div className="h-6 bg-slate-800 rounded-full w-20" />
                <div className="h-6 bg-slate-800 rounded-full w-24" />
                <div className="h-6 bg-slate-800 rounded-full w-16" />
              </div>
            </div>
          ))}
        </div>
      ) : jobs.length === 0 ? (
        /* Empty States */
        <div className="text-center py-16 px-4 bg-slate-900 border border-slate-800 rounded-2xl shadow-xl">
          <div className="h-14 w-14 rounded-2xl bg-slate-800 text-slate-400 mx-auto flex items-center justify-center mb-4">
            <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          </div>
          {debouncedQuery ? (
            <>
              <h3 className="text-base font-bold text-white">No matching job postings</h3>
              <p className="text-xs text-slate-400 max-w-sm mx-auto mt-1 mb-4">
                We couldn't find any open positions matching "{debouncedQuery}". Try refining your search keywords.
              </p>
              <button
                type="button"
                onClick={() => setSearchTerm('')}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition-colors"
              >
                Clear Search
              </button>
            </>
          ) : (
            <>
              <h3 className="text-base font-bold text-white">No open jobs available</h3>
              <p className="text-xs text-slate-400 max-w-sm mx-auto mt-1">
                There are currently no active job postings published by recruiters. Please check back soon!
              </p>
            </>
          )}
        </div>
      ) : (
        /* Job Cards List */
        <div className="space-y-4">
          {jobs.map((job) => {
            const requiredSkills = (job.skills || []).filter((s) => s.importance === 'required');
            const preferredSkills = (job.skills || []).filter((s) => s.importance === 'preferred');

            return (
              <div
                key={job.id}
                className="bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-2xl p-6 transition-all shadow-md hover:shadow-xl flex flex-col justify-between gap-5 group"
              >
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2.5 flex-wrap">
                      <Link
                        to={`/candidate/jobs/${job.id}`}
                        className="text-lg font-bold text-white hover:text-indigo-400 transition-colors"
                      >
                        {job.title}
                      </Link>
                      <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
                        Open
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-slate-400 flex-wrap">
                      <span className="font-medium text-slate-300">
                        {job.company_name || 'Hiring Company'}
                      </span>
                      <span>&bull;</span>
                      <span>
                        Posted {new Date(job.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>

                  <Link
                    to={`/candidate/jobs/${job.id}`}
                    className="self-start sm:self-center px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/20 transition-all flex items-center gap-1.5 shrink-0"
                  >
                    <span>View Details</span>
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </Link>
                </div>

                {/* Meta details */}
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 text-xs bg-slate-950/40 p-3.5 rounded-xl border border-slate-800/80">
                  <div>
                    <span className="text-slate-400">Experience Required: </span>
                    <span className="font-semibold text-slate-200">
                      {job.min_experience_years === 0
                        ? 'Entry Level / None'
                        : `${job.min_experience_years}+ years`}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400">Education: </span>
                    <span className="font-semibold text-slate-200">
                      {job.education || 'Not specified'}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400">Total Skills: </span>
                    <span className="font-semibold text-slate-200">
                      {(job.skills || []).length} requirement{job.skills?.length !== 1 ? 's' : ''}
                    </span>
                  </div>
                </div>

                {/* Skills tags */}
                <div className="flex flex-wrap items-center gap-2 pt-1">
                  {requiredSkills.map((s) => (
                    <span
                      key={s.skill_id}
                      className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium bg-indigo-500/10 text-indigo-300 border border-indigo-500/20"
                      title={`${s.name} (${s.category}) - Required`}
                    >
                      <span className="h-1.5 w-1.5 rounded-full bg-indigo-400" />
                      <span>{s.name}</span>
                      <span className="text-[10px] text-indigo-400/80 font-normal ml-0.5">(Required)</span>
                    </span>
                  ))}
                  {preferredSkills.map((s) => (
                    <span
                      key={s.skill_id}
                      className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium bg-slate-800 text-slate-300 border border-slate-700"
                      title={`${s.name} (${s.category}) - Preferred`}
                    >
                      <span className="h-1.5 w-1.5 rounded-full bg-slate-400" />
                      <span>{s.name}</span>
                      <span className="text-[10px] text-slate-400 font-normal ml-0.5">(Preferred)</span>
                    </span>
                  ))}
                  {requiredSkills.length === 0 && preferredSkills.length === 0 && (
                    <span className="text-xs text-slate-400 italic">No specific skills listed</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Pagination controls */}
      {!loading && total > PAGE_SIZE && (
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-4 border-t border-slate-800 text-xs">
          <p className="text-slate-400">
            Showing <span className="font-semibold text-white">{offset + 1}</span> to{' '}
            <span className="font-semibold text-white">{Math.min(offset + PAGE_SIZE, total)}</span> of{' '}
            <span className="font-semibold text-white">{total}</span> open jobs
          </p>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handlePrevPage}
              disabled={offset === 0}
              className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
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
              className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
