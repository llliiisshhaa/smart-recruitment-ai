import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/useAuth.js";
import { candidateApi } from "../api/candidate.js";
import { resumesApi } from "../api/resumes.js";
import StatusBadge from "../components/StatusBadge";
import { LoadingSpinner } from "../components/LoadingSpinner.jsx";
import { extractErrorMessage } from "../api/client.js";

export function CandidateDashboard() {
  const { user } = useAuth();

  const [profile, setProfile] = useState(null);
  const [resumes, setResumes] = useState([]);
  const [applications, setApplications] = useState([]);
  const [applicationsSupported, setApplicationsSupported] = useState(true);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;

    async function loadDashboardData() {
      setLoading(true);
      setError(null);

      try {
        // Fetch profile
        const profileData = await candidateApi.getProfile();
        if (isMounted) setProfile(profileData);

        // Fetch resumes
        const resumesData = await resumesApi.listResumes();
        if (isMounted) setResumes(resumesData);

        // Fetch applications (integrated if supported)
        try {
          const appsData = await candidateApi.getMyApplications();
          if (isMounted) {
            setApplications(appsData || []);
            setApplicationsSupported(true);
          }
        } catch {
          if (isMounted) {
            setApplicationsSupported(false);
          }
        }
      } catch (err) {
        if (isMounted) {
          setError(
            extractErrorMessage(
              err,
              "Could not load candidate dashboard data.",
            ),
          );
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    loadDashboardData();

    return () => {
      isMounted = false;
    };
  }, []);

  if (loading) {
    return <LoadingSpinner text="Loading candidate dashboard..." />;
  }

  // Calculate profile completeness
  const profileFields = [
    { label: "Full Name", set: Boolean(user?.full_name) },
    { label: "Headline", set: Boolean(profile?.headline) },
    { label: "Phone", set: Boolean(profile?.phone) },
    { label: "Location", set: Boolean(profile?.location) },
    { label: "Consent", set: Boolean(profile?.consent_given_at) },
  ];
  const completedFields = profileFields.filter((f) => f.set).length;
  const completenessPercentage = Math.round(
    (completedFields / profileFields.length) * 100,
  );

  return (
    <div className="space-y-8">
      {/* Header Greeting */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-white tracking-tight">
            Welcome back, {user?.full_name || "Candidate"}
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Candidate overview and AI recruitment evaluation status.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            to="/candidate/resumes"
            className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm shadow-md shadow-indigo-600/25 transition-all flex items-center gap-2"
          >
            <svg
              className="w-4 h-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 4v16m8-8H4"
              />
            </svg>
            Upload Resume
          </Link>
          <Link
            to="/candidate/profile"
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium text-sm border border-slate-700 transition-colors"
          >
            Edit Profile
          </Link>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-sm text-rose-300">
          {error}
        </div>
      )}

      {/* Summary Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* 1. Profile Completeness */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 flex flex-col justify-between shadow-lg">
          <div>
            <div className="flex items-center justify-between text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
              <span>Profile Health</span>
              <span className="text-indigo-400">{completenessPercentage}%</span>
            </div>
            <div className="w-full bg-slate-800 rounded-full h-2 mb-4 overflow-hidden">
              <div
                className="bg-gradient-to-r from-indigo-500 to-emerald-500 h-2 rounded-full transition-all duration-500"
                style={{ width: `${completenessPercentage}%` }}
              />
            </div>
            <p className="text-xs text-slate-400">
              {completenessPercentage === 100
                ? "All primary profile fields completed."
                : `${profileFields.length - completedFields} profile items pending.`}
            </p>
          </div>
          <Link
            to="/candidate/profile"
            className="mt-4 inline-flex items-center text-xs font-semibold text-indigo-400 hover:text-indigo-300 transition-colors"
          >
            Update Profile &rarr;
          </Link>
        </div>

        {/* 2. Consent Status */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 flex flex-col justify-between shadow-lg">
          <div>
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
              Data Processing Consent
            </div>
            <div className="mt-1 mb-2">
              <StatusBadge
                status={Boolean(profile?.consent_given_at)}
                type="consent"
              />
            </div>
            <p className="text-xs text-slate-400">
              {profile?.consent_given_at
                ? `Consent recorded on ${new Date(profile.consent_given_at).toLocaleDateString()}.`
                : "Consent is required to submit resumes and apply."}
            </p>
          </div>
          <Link
            to="/candidate/profile"
            className="mt-4 inline-flex items-center text-xs font-semibold text-indigo-400 hover:text-indigo-300 transition-colors"
          >
            Manage Consent &rarr;
          </Link>
        </div>

        {/* 3. Number of Uploaded Resumes */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 flex flex-col justify-between shadow-lg">
          <div>
            <div className="flex items-center justify-between text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
              <span>Uploaded Resumes</span>
              <span className="text-slate-400 text-[11px]">Max 5</span>
            </div>
            <div className="text-3xl font-extrabold text-white mt-1 mb-1">
              {resumes.length}{" "}
              <span className="text-base font-normal text-slate-400">/ 5</span>
            </div>
            <p className="text-xs text-slate-400">
              {resumes.length === 0
                ? "No resumes uploaded yet."
                : `${resumes.length} active resume file${resumes.length > 1 ? "s" : ""} stored.`}
            </p>
          </div>
          <Link
            to="/candidate/resumes"
            className="mt-4 inline-flex items-center text-xs font-semibold text-indigo-400 hover:text-indigo-300 transition-colors"
          >
            View Resumes &rarr;
          </Link>
        </div>

        {/* 4. Applied Jobs */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 flex flex-col justify-between shadow-lg">
          <div>
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
              Job Applications
            </div>
            {applicationsSupported ? (
              <>
                <div className="text-3xl font-extrabold text-white mt-1 mb-1">
                  {applications.length}
                </div>
                <p className="text-xs text-slate-400">
                  {applications.length === 0
                    ? "No job applications submitted yet."
                    : `Active applications tracked in pipeline.`}
                </p>
              </>
            ) : (
              <div className="text-xs text-slate-400 mt-2">
                Application tracking is not yet available in this phase.
              </div>
            )}
          </div>
          <span className="mt-4 text-xs font-medium text-slate-400">
            {applicationsSupported
              ? `${applications.length} applications total`
              : "Feature in progress"}
          </span>
        </div>
      </div>

      {/* Recent Resumes & Quick Access */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Recent Resumes */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
          <div className="flex items-center justify-between pb-4 mb-4 border-b border-slate-800">
            <div>
              <h2 className="text-base font-bold text-white">Recent Resumes</h2>
              <p className="text-xs text-slate-400">
                Your uploaded CV documents
              </p>
            </div>
            <Link
              to="/candidate/resumes"
              className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 transition-colors"
            >
              All Resumes ({resumes.length}) &rarr;
            </Link>
          </div>

          {resumes.length === 0 ? (
            <div className="text-center py-10 px-4">
              <div className="h-12 w-12 rounded-2xl bg-indigo-500/10 text-indigo-400 mx-auto flex items-center justify-center mb-3">
                <svg
                  className="w-6 h-6"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.75}
                    d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
              </div>
              <h3 className="text-sm font-semibold text-white">
                No resumes uploaded yet
              </h3>
              <p className="text-xs text-slate-400 max-w-sm mx-auto mt-1 mb-4">
                Upload your CV in PDF or DOCX format to get started with job
                applications.
              </p>
              <Link
                to="/candidate/resumes"
                className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/20 transition-all inline-block"
              >
                Upload your first resume
              </Link>
            </div>
          ) : (
            <div className="divide-y divide-slate-800/80">
              {resumes.slice(0, 3).map((r) => (
                <div
                  key={r.id}
                  className="py-3.5 flex items-center justify-between gap-4"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="h-9 w-9 rounded-xl bg-slate-800 border border-slate-700/80 flex items-center justify-center text-slate-300 shrink-0">
                      <svg
                        className="w-5 h-5"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={1.5}
                          d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
                        />
                      </svg>
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-semibold text-white truncate">
                        {r.original_filename}
                      </p>
                      <p className="text-[11px] text-slate-400">
                        Uploaded {new Date(r.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <StatusBadge status={r.parse_status} type="parse_status" />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right Column: Platform Information */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col justify-between">
          <div>
            <h2 className="text-base font-bold text-white mb-1">
              AI Recruitment Pipeline
            </h2>
            <p className="text-xs text-slate-400 mb-4">
              How our smart platform evaluates talent
            </p>

            <div className="space-y-3.5">
              <div className="flex items-start gap-3">
                <span className="h-6 w-6 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 flex items-center justify-center text-xs font-bold shrink-0">
                  1
                </span>
                <div>
                  <h4 className="text-xs font-semibold text-slate-200">
                    Candidate Consent
                  </h4>
                  <p className="text-[11px] text-slate-400 leading-relaxed">
                    Explicit consent is strictly recorded before processing
                    personal documents.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <span className="h-6 w-6 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 flex items-center justify-center text-xs font-bold shrink-0">
                  2
                </span>
                <div>
                  <h4 className="text-xs font-semibold text-slate-200">
                    Secure Storage
                  </h4>
                  <p className="text-[11px] text-slate-400 leading-relaxed">
                    Resumes are stored on isolated disks with strict candidate
                    ownership access.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <span className="h-6 w-6 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 flex items-center justify-center text-xs font-bold shrink-0">
                  3
                </span>
                <div>
                  <h4 className="text-xs font-semibold text-slate-200">
                    Human-In-The-Loop
                  </h4>
                  <p className="text-[11px] text-slate-400 leading-relaxed">
                    All hiring decisions (shortlist/hold/reject) are made solely
                    by human recruiters.
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-slate-800 text-[11px] text-slate-400">
            Stage 6B & 7 Candidate Architecture
          </div>
        </div>
      </div>
    </div>
  );
}
