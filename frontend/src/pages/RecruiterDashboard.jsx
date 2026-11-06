import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/useAuth.js';
import { recruiterApi } from '../api/recruiter.js';
import { extractErrorMessage } from '../api/client.js';
import { StatCard } from '../components/recruiter/StatCard.jsx';
import { ApplicationsPerJobChart } from '../components/recruiter/ApplicationsPerJobChart.jsx';
import { RecentApplicationsTable } from '../components/recruiter/RecentApplicationsTable.jsx';
import { DashboardSkeleton } from '../components/recruiter/DashboardSkeleton.jsx';

export function RecruiterDashboard() {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  // Initial dashboard data load
  useEffect(() => {
    let isMounted = true;

    recruiterApi
      .getStats()
      .then((data) => {
        if (isMounted) {
          setStats(data);
          setError(null);
        }
      })
      .catch((err) => {
        if (isMounted) {
          const errorMsg = extractErrorMessage(
            err,
            'Failed to load recruiter statistics. Please ensure the backend service is running.'
          );
          setError(errorMsg);
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
      const data = await recruiterApi.getStats();
      setStats(data);
    } catch (err) {
      const errorMsg = extractErrorMessage(
        err,
        'Failed to refresh recruiter statistics. Please try again.'
      );
      setError(errorMsg);
    } finally {
      setRefreshing(false);
    }
  };

  // Retry loading handler
  const handleRetry = async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await recruiterApi.getStats();
      setStats(data);
    } catch (err) {
      const errorMsg = extractErrorMessage(
        err,
        'Failed to load recruiter statistics. Please ensure the backend service is running.'
      );
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  // Loading Skeleton State
  if (loading && !stats) {
    return <DashboardSkeleton />;
  }

  // Error State with Retry Button
  if (error && !stats) {
    return (
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div>
            <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
              Recruiter Dashboard
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Overview of hiring pipeline and application metrics.
            </p>
          </div>
        </div>

        <div className="bg-rose-500/10 border border-rose-500/30 rounded-2xl p-6 md:p-8 text-center max-w-xl mx-auto shadow-xl">
          <div className="h-12 w-12 rounded-2xl bg-rose-500/20 text-rose-400 mx-auto flex items-center justify-center mb-4">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h2 className="text-lg font-bold text-white mb-2">Unable to Load Dashboard</h2>
          <p className="text-sm text-slate-300 mb-6 leading-relaxed">
            {error}
          </p>
          <button
            onClick={handleRetry}
            className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm shadow-lg shadow-indigo-600/25 transition-all inline-flex items-center gap-2 cursor-pointer"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            <span>Retry Loading</span>
          </button>
        </div>
      </div>
    );
  }

  const isBrandNewRecruiter =
    stats &&
    stats.active_jobs === 0 &&
    stats.closed_jobs === 0 &&
    stats.total_applications === 0;

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      {/* Top Header & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
            Recruiter Dashboard
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Welcome back, <span className="text-slate-200 font-semibold">{user?.full_name || 'Recruiter'}</span>. Here is your hiring pipeline overview.
          </p>
        </div>

        <div className="flex items-center gap-3 self-start sm:self-auto">
          {/* Refresh button */}
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition-colors disabled:opacity-50 flex items-center gap-2 cursor-pointer shadow-sm"
            title="Refresh statistics"
          >
            <svg
              className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin text-indigo-400' : ''}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            <span>{refreshing ? 'Updating...' : 'Refresh'}</span>
          </button>

          {/* Post Job CTA button */}
          <Link
            to="/recruiter/jobs"
            className="px-4 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/25 transition-all flex items-center gap-1.5"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            <span>Post New Job</span>
          </Link>
        </div>
      </div>

      {/* Onboarding Empty State Banner for Recruiters with no jobs yet */}
      {isBrandNewRecruiter && (
        <div className="relative overflow-hidden bg-gradient-to-r from-indigo-950/60 to-slate-900 border border-indigo-500/30 rounded-2xl p-6 shadow-xl">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-5">
            <div className="space-y-1 max-w-xl">
              <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full bg-indigo-500/20 border border-indigo-500/30 text-[11px] font-semibold text-indigo-300">
                Getting Started
              </div>
              <h2 className="text-lg font-bold text-white">Create Your First Job Posting</h2>
              <p className="text-xs text-slate-300 leading-relaxed">
                You haven&apos;t published any job openings yet. Set up job requirements, required technical skills, and experience criteria to start receiving candidate applications.
              </p>
            </div>
            <Link
              to="/recruiter/jobs"
              className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/30 transition-all self-start md:self-auto shrink-0 inline-flex items-center gap-2"
            >
              <span>Create Job Opening &rarr;</span>
            </Link>
          </div>
        </div>
      )}

      {/* Primary KPI Metrics Cards (4 cards) */}
      <section aria-labelledby="pipeline-overview-title">
        <h2 id="pipeline-overview-title" className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
          Pipeline Overview
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            title="Active Jobs"
            value={stats?.active_jobs ?? 0}
            color="emerald"
            subtitle="Currently accepting applicants"
            icon={
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            }
          />

          <StatCard
            title="Closed Jobs"
            value={stats?.closed_jobs ?? 0}
            color="slate"
            subtitle="Archived or fulfilled roles"
            icon={
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
              </svg>
            }
          />

          <StatCard
            title="Total Applications"
            value={stats?.total_applications ?? 0}
            color="indigo"
            subtitle="Total candidate submissions"
            icon={
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
            }
          />

          <StatCard
            title="Awaiting Review"
            value={stats?.awaiting_review ?? 0}
            color="amber"
            subtitle="Applications with status 'applied'"
            badge={stats?.awaiting_review > 0 ? `${stats.awaiting_review} pending` : undefined}
            highlight={stats?.awaiting_review > 0}
            icon={
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            }
          />
        </div>
      </section>

      {/* Review Decisions Breakdown Cards (3 cards) */}
      <section aria-labelledby="review-decisions-title">
        <h2 id="review-decisions-title" className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
          Candidate Evaluation Decisions (Latest Review per Candidate)
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <StatCard
            title="Shortlisted"
            value={stats?.shortlisted ?? 0}
            color="emerald"
            subtitle="Advanced for interview & hire"
            icon={
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            }
          />

          <StatCard
            title="On Hold"
            value={stats?.on_hold ?? 0}
            color="amber"
            subtitle="Standby / deferred consideration"
            icon={
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            }
          />

          <StatCard
            title="Rejected"
            value={stats?.rejected ?? 0}
            color="rose"
            subtitle="Declined applications"
            icon={
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            }
          />
        </div>
      </section>

      {/* Applications by Job Opening Bar Chart */}
      <section aria-labelledby="chart-section-title">
        <ApplicationsPerJobChart data={stats?.applications_per_job || []} />
      </section>

      {/* Recent Applications Table */}
      <section aria-labelledby="recent-apps-section-title">
        <RecentApplicationsTable applications={stats?.recent_applications || []} />
      </section>
    </div>
  );
}
