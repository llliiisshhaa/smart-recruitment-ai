import { useState, useEffect } from 'react';
import { healthApi } from '../api/health.js';
import { useAuth } from '../context/useAuth.js';

export function Navbar({ onOpenMobileMenu }) {
  const { user, logout } = useAuth();
  const [backendOnline, setBackendOnline] = useState(null);

  useEffect(() => {
    let isMounted = true;
    async function check() {
      try {
        const res = await healthApi.checkHealth();
        if (isMounted) {
          setBackendOnline(res?.status === 'ok');
        }
      } catch {
        if (isMounted) {
          setBackendOnline(false);
        }
      }
    }
    check();
    const interval = setInterval(check, 30000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <header className="h-16 border-b border-slate-800 bg-slate-900/50 backdrop-blur-md sticky top-0 z-30 px-4 lg:px-8 flex items-center justify-between">
      <div className="flex items-center gap-3">
        {/* Mobile menu button */}
        <button
          onClick={onOpenMobileMenu}
          className="lg:hidden p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 focus:outline-none"
          aria-label="Open mobile navigation menu"
        >
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>

        <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 hidden sm:inline">
          Smart Recruitment Platform
        </span>
      </div>

      <div className="flex items-center gap-4">
        {/* Live backend health pill */}
        <div
          title={
            backendOnline === null
              ? 'Checking backend connectivity'
              : backendOnline
              ? 'Backend API Connected'
              : 'Backend API Offline'
          }
          className="flex items-center gap-2 px-2.5 py-1 rounded-full bg-slate-800/80 border border-slate-700/80 text-xs font-medium text-slate-300"
        >
          <span
            className={`h-2 w-2 rounded-full ${
              backendOnline === null
                ? 'bg-amber-400 animate-pulse'
                : backendOnline
                ? 'bg-emerald-400'
                : 'bg-rose-400 animate-ping'
            }`}
          />
          <span className="hidden sm:inline">
            {backendOnline === null ? 'Checking...' : backendOnline ? 'API Connected' : 'API Offline'}
          </span>
        </div>

        {/* User badge */}
        <div className="flex items-center gap-2 pl-2 border-l border-slate-800">
          <div className="h-8 w-8 rounded-full bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 flex items-center justify-center font-bold text-xs">
            {user?.full_name?.charAt(0)?.toUpperCase() || 'C'}
          </div>
          <span className="text-xs font-medium text-slate-200 hidden md:inline max-w-[120px] truncate">
            {user?.full_name}
          </span>
          <button
            onClick={logout}
            className="text-xs text-slate-400 hover:text-rose-400 p-1.5 rounded-lg hover:bg-slate-800 transition-colors"
            title="Sign Out"
            aria-label="Sign Out"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
          </button>
        </div>
      </div>
    </header>
  );
}
