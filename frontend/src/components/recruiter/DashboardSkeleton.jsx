/**
 * Loading skeleton placeholder for the Recruiter Dashboard.
 */
export function DashboardSkeleton() {
  return (
    <div className="space-y-8 animate-pulse">
      {/* Header skeleton */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <div className="h-8 w-64 bg-slate-800 rounded-xl mb-2" />
          <div className="h-4 w-96 max-w-full bg-slate-800/60 rounded-lg" />
        </div>
        <div className="flex items-center gap-3">
          <div className="h-10 w-24 bg-slate-800 rounded-xl" />
          <div className="h-10 w-32 bg-slate-800 rounded-xl" />
        </div>
      </div>

      {/* Row 1 KPI cards skeleton (4 cards) */}
      <div>
        <div className="h-4 w-36 bg-slate-800/80 rounded mb-3" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div
              key={i}
              className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg flex justify-between items-start"
            >
              <div className="space-y-2 flex-1">
                <div className="h-3 w-20 bg-slate-800 rounded" />
                <div className="h-8 w-14 bg-slate-800 rounded-lg" />
                <div className="h-3 w-28 bg-slate-800/60 rounded" />
              </div>
              <div className="h-11 w-11 rounded-xl bg-slate-800 shrink-0" />
            </div>
          ))}
        </div>
      </div>

      {/* Row 2 Review decisions skeleton (3 cards) */}
      <div>
        <div className="h-4 w-44 bg-slate-800/80 rounded mb-3" />
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg flex justify-between items-start"
            >
              <div className="space-y-2 flex-1">
                <div className="h-3 w-24 bg-slate-800 rounded" />
                <div className="h-8 w-12 bg-slate-800 rounded-lg" />
                <div className="h-3 w-32 bg-slate-800/60 rounded" />
              </div>
              <div className="h-11 w-11 rounded-xl bg-slate-800 shrink-0" />
            </div>
          ))}
        </div>
      </div>

      {/* Chart container skeleton */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-lg">
        <div className="flex justify-between items-center mb-6">
          <div className="space-y-2">
            <div className="h-5 w-48 bg-slate-800 rounded-lg" />
            <div className="h-3 w-72 bg-slate-800/60 rounded" />
          </div>
          <div className="h-4 w-28 bg-slate-800 rounded" />
        </div>
        <div className="h-[280px] w-full bg-slate-950/40 border border-slate-800/60 rounded-xl flex items-end justify-around p-6 gap-3">
          {[40, 75, 55, 90, 30].map((heightPct, idx) => (
            <div
              key={idx}
              className="w-12 bg-slate-800/70 rounded-t-lg transition-all"
              style={{ height: `${heightPct}%` }}
            />
          ))}
        </div>
      </div>

      {/* Table skeleton */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-lg space-y-4">
        <div className="h-5 w-40 bg-slate-800 rounded-lg" />
        <div className="space-y-3 pt-2">
          {[1, 2, 3, 4, 5].map((row) => (
            <div
              key={row}
              className="h-12 w-full bg-slate-950/50 border border-slate-800/50 rounded-xl"
            />
          ))}
        </div>
      </div>
    </div>
  );
}

