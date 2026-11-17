import { Link } from 'react-router-dom';
import { StatusBadge } from '../StatusBadge.jsx';

/**
 * Formats ISO 8601 date string into human-friendly format.
 */
function formatAppliedDate(dateString) {
  if (!dateString) return '—';
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return '—';
    return date.toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return '—';
  }
}

/**
 * Table displaying the latest candidate applications for recruiter review.
 * Enforces privacy: displays ONLY candidate name, no contact details.
 *
 * @param {{
 *   applications: Array<{
 *     application_id: number,
 *     candidate_name: string,
 *     job_title: string,
 *     status: string,
 *     applied_at: string
 *   }>
 * }} props
 */
export function RecentApplicationsTable({ applications = [] }) {
  const hasApplications = Array.isArray(applications) && applications.length > 0;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 md:p-6 shadow-lg">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5">
        <div>
          <h2 className="text-base font-bold text-white tracking-tight flex items-center gap-2">
            <span>Recent Applications</span>
            {hasApplications && (
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-800 text-indigo-400 border border-slate-700">
                Latest {applications.length}
              </span>
            )}
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Latest candidate submissions across all your posted roles.
          </p>
        </div>

        <Link
          to="/recruiter/jobs"
          className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 transition-colors inline-flex items-center gap-1.5 self-start sm:self-auto"
        >
          <span>Manage All Jobs</span>
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </Link>
      </div>

      {!hasApplications ? (
        <div className="flex flex-col items-center justify-center text-center p-8 border border-dashed border-slate-800 rounded-xl bg-slate-950/40">
          <div className="h-12 w-12 rounded-2xl bg-slate-800 text-slate-400 flex items-center justify-center mb-3">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <h3 className="text-sm font-semibold text-white mb-1">
            No Applications Received Yet
          </h3>
          <p className="text-xs text-slate-400 max-w-sm">
            When candidates discover and apply to your open job roles, their submissions will be listed here for evaluation.
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto -mx-5 md:-mx-6">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-800 text-[11px] font-semibold text-slate-400 uppercase tracking-wider bg-slate-950/30">
                <th className="py-3 px-5 md:px-6">Candidate</th>
                <th className="py-3 px-4">Job Position</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Applied Date</th>
                <th className="py-3 px-5 md:px-6 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-sm">
              {applications.map((app) => {
                const initial =
                  app.candidate_name?.trim()?.charAt(0)?.toUpperCase() || 'C';

                return (
                  <tr
                    key={app.application_id}
                    className="hover:bg-slate-800/40 transition-colors group"
                  >
                    {/* Candidate Identity (Name only, strictly NO contact details) */}
                    <td className="py-3.5 px-5 md:px-6">
                      <div className="flex items-center gap-3">
                        <div className="h-8 w-8 rounded-full bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 flex items-center justify-center font-bold text-xs shrink-0">
                          {initial}
                        </div>
                        <span className="font-semibold text-white group-hover:text-indigo-300 transition-colors">
                          {app.candidate_name}
                        </span>
                      </div>
                    </td>

                    {/* Applied Job Role */}
                    <td className="py-3.5 px-4 text-slate-300">
                      <span className="font-medium text-slate-200">
                        {app.job_title}
                      </span>
                    </td>

                    {/* Review Status (maps 'applied' -> 'Awaiting review') */}
                    <td className="py-3.5 px-4">
                      <StatusBadge status={app.status} />
                    </td>

                    {/* Submission Timestamp */}
                    <td className="py-3.5 px-4 text-xs text-slate-400 whitespace-nowrap">
                      {formatAppliedDate(app.applied_at)}
                    </td>

                    {/* Action link */}
                    <td className="py-3.5 px-5 md:px-6 text-right whitespace-nowrap">
                      <Link
                        to={`/recruiter/applications/${app.application_id}`}
                        className="inline-flex items-center gap-1 text-xs font-semibold px-3 py-1.5 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 hover:text-white border border-indigo-500/30 transition-all"
                      >
                        <span>Review Dossier</span>
                        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      </Link>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

