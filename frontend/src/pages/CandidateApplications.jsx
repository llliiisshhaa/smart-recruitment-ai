import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { candidateApi } from '../api/candidate.js';
import { extractErrorMessage } from '../api/client.js';
import { StatusBadge } from '../components/StatusBadge.jsx';

export function CandidateApplications() {
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadApplications = useCallback(async () => {
    try {
      const data = await candidateApi.getMyApplications();
      setApplications(data || []);
      setError(null);
    } catch (err) {
      setError(extractErrorMessage(err, 'Failed to load your submitted applications.'));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let isMounted = true;

    async function init() {
      try {
        const data = await candidateApi.getMyApplications();
        if (isMounted) {
          setApplications(data || []);
          setError(null);
        }
      } catch (err) {
        if (isMounted) {
          setError(extractErrorMessage(err, 'Failed to load your submitted applications.'));
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
  }, []);

  const handleRetry = () => {
    setLoading(true);
    setError(null);
    loadApplications();
  };

  return (
    <div className="space-y-6 max-w-6xl animate-in fade-in duration-200">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-white tracking-tight">
            My Applications
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Track the status of your submitted job applications and attached resumes.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            to="/candidate/jobs"
            className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs shadow-md shadow-indigo-600/25 transition-all flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            Browse Open Jobs
          </Link>
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
            className="px-3 py-1.5 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 text-xs font-semibold text-rose-200 transition-colors cursor-pointer"
          >
            Retry
          </button>
        </div>
      )}

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
              <div className="h-6 bg-slate-800 rounded-full w-28" />
            </div>
          ))}
        </div>
      ) : applications.length === 0 ? (
        /* Empty State */
        <div className="text-center py-16 px-4 bg-slate-900 border border-slate-800 rounded-2xl shadow-xl">
          <div className="h-14 w-14 rounded-2xl bg-indigo-500/10 text-indigo-400 mx-auto flex items-center justify-center mb-4">
            <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
            </svg>
          </div>
          <h3 className="text-base font-bold text-white">No applications submitted yet</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto mt-1 mb-5">
            You haven't submitted any job applications yet. Browse open positions to find roles that match your skills.
          </p>
          <Link
            to="/candidate/jobs"
            className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs shadow-md shadow-indigo-600/20 transition-all inline-flex items-center gap-2"
          >
            <span>Explore Open Positions</span>
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
            </svg>
          </Link>
        </div>
      ) : (
        /* Applications Table / Cards */
        <div className="bg-slate-900 border border-slate-800 rounded-2xl shadow-xl overflow-hidden">
          <div className="p-5 border-b border-slate-800 flex items-center justify-between">
            <h2 className="text-base font-bold text-white">
              Application History
            </h2>
            <span className="text-xs font-semibold px-2.5 py-1 rounded-lg bg-slate-800 text-slate-300">
              {applications.length} submitted
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="text-xs uppercase bg-slate-950/60 text-slate-400 border-b border-slate-800">
                <tr>
                  <th scope="col" className="px-6 py-3.5 font-semibold">Job Title</th>
                  <th scope="col" className="px-6 py-3.5 font-semibold">Attached Resume</th>
                  <th scope="col" className="px-6 py-3.5 font-semibold">Date Applied</th>
                  <th scope="col" className="px-6 py-3.5 font-semibold">Evaluation Status</th>
                  <th scope="col" className="px-6 py-3.5 font-semibold text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {applications.map((app) => (
                  <tr key={app.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="px-6 py-4">
                      <div className="min-w-0">
                        <Link
                          to={`/candidate/jobs/${app.job_id}`}
                          className="font-semibold text-white hover:text-indigo-400 transition-colors line-clamp-1"
                        >
                          {app.job_title}
                        </Link>
                        <div className="flex items-center gap-2 mt-0.5">
                          <span className="text-[11px] text-slate-400">
                            Position: {app.job_status === 'open' ? 'Currently Open' : 'Closed'}
                          </span>
                        </div>
                      </div>
                    </td>

                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <svg className="w-4 h-4 text-slate-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        <span className="text-xs text-slate-200 truncate max-w-xs">
                          {app.resume_filename || (
                            <span className="text-slate-400 italic">Resume removed</span>
                          )}
                        </span>
                      </div>
                    </td>

                    <td className="px-6 py-4 text-xs text-slate-400 whitespace-nowrap">
                      {new Date(app.created_at).toLocaleDateString()}
                    </td>

                    <td className="px-6 py-4 whitespace-nowrap">
                      <StatusBadge status={app.status} audience="candidate" />
                    </td>

                    <td className="px-6 py-4 text-right whitespace-nowrap">
                      <Link
                        to={`/candidate/jobs/${app.job_id}`}
                        className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 transition-colors"
                      >
                        View Job &rarr;
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
