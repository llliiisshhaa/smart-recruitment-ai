/**
 * Reusable StatCard component for recruiter analytics and dashboard KPIs.
 */
export function StatCard({
  title,
  value,
  icon,
  subtitle,
  color = 'indigo',
  badge,
  highlight = false,
}) {
  const colorSchemes = {
    indigo: {
      bg: 'bg-indigo-500/10',
      text: 'text-indigo-400',
      border: 'border-indigo-500/20',
      glow: 'from-indigo-600/10 to-transparent',
    },
    emerald: {
      bg: 'bg-emerald-500/10',
      text: 'text-emerald-400',
      border: 'border-emerald-500/20',
      glow: 'from-emerald-600/10 to-transparent',
    },
    amber: {
      bg: 'bg-amber-500/10',
      text: 'text-amber-400',
      border: 'border-amber-500/20',
      glow: 'from-amber-600/10 to-transparent',
    },
    rose: {
      bg: 'bg-rose-500/10',
      text: 'text-rose-400',
      border: 'border-rose-500/20',
      glow: 'from-rose-600/10 to-transparent',
    },
    sky: {
      bg: 'bg-sky-500/10',
      text: 'text-sky-400',
      border: 'border-sky-500/20',
      glow: 'from-sky-600/10 to-transparent',
    },
    slate: {
      bg: 'bg-slate-800/60',
      text: 'text-slate-400',
      border: 'border-slate-700/60',
      glow: 'from-slate-700/10 to-transparent',
    },
  };

  const scheme = colorSchemes[color] || colorSchemes.indigo;

  return (
    <div
      className={`relative bg-slate-900 border rounded-2xl p-5 shadow-lg transition-all duration-200 overflow-hidden ${
        highlight
          ? 'border-amber-500/40 ring-1 ring-amber-500/20'
          : 'border-slate-800 hover:border-slate-700/80'
      }`}
    >
      {/* Decorative subtle ambient gradient */}
      <div
        className={`absolute -top-12 -right-12 w-28 h-28 bg-gradient-to-br ${scheme.glow} rounded-full blur-2xl pointer-events-none`}
      />

      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider truncate">
            {title}
          </p>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-white tracking-tight">
              {typeof value === 'number' ? value.toLocaleString() : value ?? 0}
            </span>
            {badge && (
              <span
                className={`text-[11px] font-semibold px-2 py-0.5 rounded-full border ${scheme.bg} ${scheme.text} ${scheme.border}`}
              >
                {badge}
              </span>
            )}
          </div>
          {subtitle && (
            <p className="mt-1 text-xs text-slate-400 truncate">{subtitle}</p>
          )}
        </div>

        {icon && (
          <div
            className={`p-3 rounded-xl border ${scheme.bg} ${scheme.text} ${scheme.border} shrink-0`}
          >
            {icon}
          </div>
        )}
      </div>
    </div>
  );
}

