import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { healthApi } from '../api/health.js';
import { useAuth } from '../context/useAuth.js';
import { API_BASE_URL } from '../api/client.js';

export function HomePage() {
  const { user, isAuthenticated } = useAuth();
  const [healthData, setHealthData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastChecked, setLastChecked] = useState(null);

  useEffect(() => {
    let isMounted = true;

    async function fetchHealth() {
      try {
        const data = await healthApi.checkHealth();
        if (isMounted) {
          setHealthData(data);
          setLastChecked(new Date().toLocaleTimeString());
        }
      } catch {
        if (isMounted) {
          setError(
            `Failed to connect to backend at ${API_BASE_URL}. Ensure the FastAPI server is running.`
          );
          setHealthData(null);
          setLastChecked(new Date().toLocaleTimeString());
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    fetchHealth();

    return () => {
      isMounted = false;
    };
  }, []);

  const handleManualCheck = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await healthApi.checkHealth();
      setHealthData(data);
      setLastChecked(new Date().toLocaleTimeString());
    } catch {
      setError(
        `Failed to connect to backend at ${API_BASE_URL}. Ensure the FastAPI server is running.`
      );
      setHealthData(null);
      setLastChecked(new Date().toLocaleTimeString());
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-indigo-500 selection:text-white">
      {/* Top Navigation */}
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-indigo-500 to-violet-500 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/25">
              AI
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight text-white">Smart Recruitment System</h1>
              <p className="text-xs text-slate-400">AI-Powered Virtual Interview Platform</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {isAuthenticated ? (
              user?.role === 'candidate' ? (
                <Link
                  to="/candidate"
                  className="px-4 py-2 text-sm font-semibold rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-600/25 transition-all"
                >
                  Candidate Portal &rarr;
                </Link>
              ) : (
                <span className="text-xs text-slate-400 px-3 py-1.5 rounded-lg bg-slate-800">
                  Logged in as {user?.role}
                </span>
              )
            ) : (
              <>
                <Link
                  to="/login"
                  className="px-4 py-2 text-sm font-medium text-slate-300 hover:text-white hover:bg-slate-800 rounded-xl transition-colors"
                >
                  Sign In
                </Link>
                <Link
                  to="/register"
                  className="px-4 py-2 text-sm font-semibold rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-600/25 transition-all"
                >
                  Get Started
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-6xl mx-auto w-full px-4 py-10 flex flex-col gap-10">
        {/* Hero Section */}
        <section className="text-center max-w-3xl mx-auto pt-4 pb-2">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-800/80 border border-slate-700 text-xs text-slate-300 mb-5">
            <span className="h-2 w-2 rounded-full bg-indigo-400 animate-pulse"></span>
            Stage 6B Candidate Portal Active
          </div>
          <h2 className="text-4xl md:text-5xl font-extrabold tracking-tight text-white mb-4">
            Smart Recruitment System
          </h2>
          <p className="text-lg text-slate-400 leading-relaxed mb-8">
            An intelligent recruitment platform featuring AI virtual interviews, secure resume management,
            adaptive skill assessment, and automated candidate evaluations with human-in-the-loop decisions.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-4">
            <Link
              to="/candidate"
              className="px-6 py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-semibold shadow-xl shadow-indigo-600/25 transition-all flex items-center gap-2"
            >
              Candidate Portal
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
              </svg>
            </Link>
            <Link
              to="/register"
              className="px-6 py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium border border-slate-700 transition-colors"
            >
              Create Candidate Account
            </Link>
          </div>
        </section>

        {/* System Health Status Card */}
        <section className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 md:p-8 shadow-xl relative overflow-hidden">
          <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-600/5 rounded-full blur-3xl pointer-events-none"></div>

          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
            <div>
              <h3 className="text-xl font-bold text-white flex items-center gap-2">
                <span>Backend Health Monitor</span>
                {healthData?.status === 'ok' ? (
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                    Operational
                  </span>
                ) : error ? (
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
                    <span className="h-1.5 w-1.5 rounded-full bg-rose-400"></span>
                    Offline
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                    Checking...
                  </span>
                )}
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                Monitors backend API and PostgreSQL connectivity at <code className="text-indigo-300 font-mono">{API_BASE_URL}</code>
              </p>
            </div>

            <div className="flex items-center gap-3">
              {lastChecked && (
                <span className="text-xs text-slate-400">
                  Last checked: {lastChecked}
                </span>
              )}
              <button
                onClick={handleManualCheck}
                disabled={loading}
                className="px-3.5 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors disabled:opacity-50 flex items-center gap-2 cursor-pointer"
              >
                <svg
                  className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`}
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                {loading ? 'Pinging...' : 'Check Health'}
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
            <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-4">
              <div className="text-xs font-medium text-slate-400 mb-1">FastAPI Server</div>
              <div className="text-base font-semibold text-white flex items-center gap-2">
                <span
                  className={`h-2.5 w-2.5 rounded-full ${
                    healthData?.status === 'ok' ? 'bg-emerald-400' : 'bg-rose-400'
                  }`}
                />
                {healthData?.status === 'ok' ? 'Healthy (HTTP 200)' : 'Unreachable'}
              </div>
            </div>

            <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-4">
              <div className="text-xs font-medium text-slate-400 mb-1">PostgreSQL Database</div>
              <div className="text-base font-semibold text-white flex items-center gap-2">
                <span
                  className={`h-2.5 w-2.5 rounded-full ${
                    healthData?.database === 'connected' ? 'bg-emerald-400' : 'bg-rose-400'
                  }`}
                />
                {healthData?.database === 'connected'
                  ? 'Connected (SQL query active)'
                  : healthData?.database || 'Unavailable'}
              </div>
            </div>
          </div>

          {error && (
            <div className="mt-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs text-rose-300">
              {error}
            </div>
          )}
        </section>
      </main>

      <footer className="border-t border-slate-800 bg-slate-900/40 py-6 text-center text-xs text-slate-400">
        Smart Recruitment System &copy; 2026. Academic AI Project.
      </footer>
    </div>
  );
}
