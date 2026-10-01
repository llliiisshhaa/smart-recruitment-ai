import { useState, useEffect, useCallback } from 'react'

export default function App() {
  // Read backend base URL from Vite environment variable (or fallback to default localhost:8001)
  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8001'

  // State to manage health check results
  const [healthData, setHealthData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [lastChecked, setLastChecked] = useState(null)

  // Function to call the backend /health endpoint
  const checkBackendHealth = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      // Create an abort controller to timeout requests after 5 seconds
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 5000)

      const response = await fetch(`${apiUrl}/health`, {
        signal: controller.signal,
        headers: {
          'Accept': 'application/json',
        },
      })
      clearTimeout(timeoutId)

      if (!response.ok) {
        throw new Error(`Server returned HTTP ${response.status}`)
      }

      const data = await response.json()
      setHealthData(data)
      setLastChecked(new Date().toLocaleTimeString())
    } catch (err) {
      console.error('Failed to connect to backend /health endpoint:', err)
      setError(
        err.name === 'AbortError'
          ? 'Connection timed out (backend took too long to respond).'
          : `Failed to connect to backend at ${apiUrl}. Ensure the FastAPI server is running.`
      )
      setHealthData(null)
      setLastChecked(new Date().toLocaleTimeString())
    } finally {
      setLoading(false)
    }
  }, [apiUrl])

  // Run health check on initial load
  useEffect(() => {
    checkBackendHealth()
  }, [checkBackendHealth])

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
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              Project Skeleton v0.1.0
            </span>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-6xl mx-auto w-full px-4 py-10 flex flex-col gap-10">
        {/* Hero Section */}
        <section className="text-center max-w-3xl mx-auto pt-4 pb-2">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-800/80 border border-slate-700 text-xs text-slate-300 mb-5">
            <span className="h-2 w-2 rounded-full bg-indigo-400 animate-pulse"></span>
            Final Year Academic Project
          </div>
          <h2 className="text-4xl md:text-5xl font-extrabold tracking-tight text-white mb-4">
            Smart Recruitment System
          </h2>
          <p className="text-lg text-slate-400 leading-relaxed">
            An intelligent recruitment platform featuring AI virtual interviews, resume parsing,
            adaptive question generation, multilingual interviews, and automated candidate evaluation.
          </p>
        </section>

        {/* System Health Status Card */}
        <section className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 md:p-8 shadow-xl relative overflow-hidden">
          <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-600/5 rounded-full blur-3xl pointer-events-none"></div>

          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-xl font-semibold text-white">System Service Health</h3>
                <span className="text-xs font-mono text-slate-400 bg-slate-800 px-2 py-0.5 rounded">
                  {apiUrl}/health
                </span>
              </div>
              <p className="text-sm text-slate-400 mt-1">
                Real-time connectivity monitoring between React frontend and FastAPI backend.
              </p>
            </div>

            <button
              onClick={checkBackendHealth}
              disabled={loading}
              className="inline-flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-500 text-white transition-all shadow-md shadow-indigo-600/20 active:scale-95 cursor-pointer"
            >
              <svg
                className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
              {loading ? 'Checking...' : 'Refresh Status'}
            </button>
          </div>

          {/* Health Status Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-6">
            {/* Backend Service Status */}
            <div className="bg-slate-950/60 rounded-xl p-5 border border-slate-800/80 flex items-start gap-4">
              <div className="mt-1">
                {loading ? (
                  <span className="relative flex h-4 w-4">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-sky-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-4 w-4 bg-sky-500"></span>
                  </span>
                ) : healthData ? (
                  <span className="relative flex h-4 w-4">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-4 w-4 bg-emerald-500"></span>
                  </span>
                ) : (
                  <span className="relative flex h-4 w-4">
                    <span className="relative inline-flex rounded-full h-4 w-4 bg-rose-500"></span>
                  </span>
                )}
              </div>
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <h4 className="text-sm font-semibold text-slate-200">FastAPI Backend</h4>
                  {loading ? (
                    <span className="text-xs px-2 py-0.5 rounded-full bg-sky-500/10 text-sky-400 border border-sky-500/20">
                      Checking
                    </span>
                  ) : healthData ? (
                    <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
                      Operational (status: {healthData.status})
                    </span>
                  ) : (
                    <span className="text-xs px-2 py-0.5 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20 font-medium">
                      Unreachable
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  Provides REST API endpoints, AI orchestration, and authentication.
                </p>
              </div>
            </div>

            {/* Database Status */}
            <div className="bg-slate-950/60 rounded-xl p-5 border border-slate-800/80 flex items-start gap-4">
              <div className="mt-1">
                {loading ? (
                  <span className="h-4 w-4 block rounded-full bg-slate-700 animate-pulse"></span>
                ) : healthData?.database === 'connected' ? (
                  <span className="relative flex h-4 w-4">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-4 w-4 bg-emerald-500"></span>
                  </span>
                ) : (
                  <span className="h-4 w-4 block rounded-full bg-amber-500"></span>
                )}
              </div>
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <h4 className="text-sm font-semibold text-slate-200">PostgreSQL Database</h4>
                  {loading ? (
                    <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-400">
                      Checking
                    </span>
                  ) : healthData?.database === 'connected' ? (
                    <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
                      Connected
                    </span>
                  ) : (
                    <span className="text-xs px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 font-medium">
                      Unavailable
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  Persists resumes, candidate scores, and interview histories. (Optional for initial health test).
                </p>
              </div>
            </div>
          </div>

          {/* Error Alert Display */}
          {error && (
            <div className="mt-6 p-4 rounded-xl bg-rose-950/40 border border-rose-800/60 text-rose-200 text-sm flex items-start gap-3">
              <svg className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <div>
                <div className="font-semibold text-rose-300">Backend Connection Error</div>
                <p className="mt-1 text-xs text-rose-300/80">{error}</p>
                <div className="mt-3 text-xs bg-slate-950/80 p-2.5 rounded-lg border border-slate-800 font-mono text-slate-300">
                  <span className="text-slate-500"># Start backend with:</span><br />
                  cd backend<br />
                  uvicorn app.main:app --reload --port 8001
                </div>
              </div>
            </div>
          )}

          {lastChecked && (
            <div className="mt-4 text-right text-xs text-slate-500">
              Last checked: {lastChecked}
            </div>
          )}
        </section>

        {/* Architecture Modules (Skeleton Phase Preview) */}
        <section>
          <div className="mb-4">
            <h3 className="text-lg font-semibold text-white">Project Modules (Phase Roadmap)</h3>
            <p className="text-sm text-slate-400">Core capabilities designed for the Smart Recruitment AI platform.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-5 rounded-xl bg-slate-900/50 border border-slate-800/70 hover:border-slate-700 transition">
              <div className="text-2xl mb-2">📄</div>
              <h4 className="font-semibold text-white text-sm">Resume Parser</h4>
              <p className="text-xs text-slate-400 mt-1">
                Extracts key candidate skills, experience, and project metrics using AI.
              </p>
            </div>

            <div className="p-5 rounded-xl bg-slate-900/50 border border-slate-800/70 hover:border-slate-700 transition">
              <div className="text-2xl mb-2">🎙️</div>
              <h4 className="font-semibold text-white text-sm">AI Virtual Interview</h4>
              <p className="text-xs text-slate-400 mt-1">
                Conducts interactive voice/text interviews with adaptive questioning.
              </p>
            </div>

            <div className="p-5 rounded-xl bg-slate-900/50 border border-slate-800/70 hover:border-slate-700 transition">
              <div className="text-2xl mb-2">🌐</div>
              <h4 className="font-semibold text-white text-sm">Multilingual Support</h4>
              <p className="text-xs text-slate-400 mt-1">
                Conducts dynamic interviews across multiple languages with seamless translation.
              </p>
            </div>

            <div className="p-5 rounded-xl bg-slate-900/50 border border-slate-800/70 hover:border-slate-700 transition">
              <div className="text-2xl mb-2">📊</div>
              <h4 className="font-semibold text-white text-sm">Recruiter Reports</h4>
              <p className="text-xs text-slate-400 mt-1">
                Resume-vs-interview skill match scores and comprehensive PDF candidate evaluations.
              </p>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 py-6 mt-auto bg-slate-950/80">
        <div className="max-w-6xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500">
          <p>© 2026 Smart Recruitment System Using AI — Academic Project</p>
          <div className="flex items-center gap-4">
            <span>FastAPI</span>
            <span>•</span>
            <span>React (Vite)</span>
            <span>•</span>
            <span>Tailwind CSS</span>
            <span>•</span>
            <span>PostgreSQL</span>
          </div>
        </div>
      </footer>
    </div>
  )
}
