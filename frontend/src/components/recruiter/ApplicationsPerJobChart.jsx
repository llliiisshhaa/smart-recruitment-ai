import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Cell,
} from 'recharts';

/**
 * Custom dark-themed tooltip for Recharts.
 */
function CustomTooltip({ active, payload }) {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-slate-900 border border-slate-700/80 rounded-xl p-3 shadow-2xl text-xs space-y-1">
        <p className="font-semibold text-white max-w-[240px] truncate">
          {data.title}
        </p>
        <p className="text-slate-300 flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-indigo-400" />
          <span>Applications:</span>
          <strong className="text-white font-bold">{data.count}</strong>
        </p>
      </div>
    );
  }
  return null;
}

/**
 * Recharts Bar Chart visualizing applications per job opening.
 * @param {{ data: Array<{ job_id: number, title: string, count: number }> }} props
 */
export function ApplicationsPerJobChart({ data = [] }) {
  const hasData = Array.isArray(data) && data.length > 0;
  const totalCount = hasData
    ? data.reduce((acc, curr) => acc + (curr.count || 0), 0)
    : 0;

  // Prepare chart items with abbreviated display titles
  const chartData = hasData
    ? data.map((item) => ({
        ...item,
        shortTitle:
          item.title && item.title.length > 15
            ? `${item.title.substring(0, 15)}...`
            : item.title || `Job #${item.job_id}`,
      }))
    : [];

  // Determine dynamic max domain for Y-axis so it looks balanced
  const maxCount = hasData
    ? Math.max(...data.map((d) => d.count || 0), 5)
    : 5;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 md:p-6 shadow-lg flex flex-col h-full">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-6">
        <div>
          <h2 className="text-base font-bold text-white tracking-tight flex items-center gap-2">
            <span>Applications by Job Role</span>
            {hasData && (
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                {data.length} {data.length === 1 ? 'Job' : 'Jobs'}
              </span>
            )}
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Applicant volume distribution across your open and archived positions.
          </p>
        </div>

        {hasData && (
          <div className="text-xs text-slate-400 font-medium">
            Total Applicants: <span className="text-white font-bold">{totalCount}</span>
          </div>
        )}
      </div>

      {!hasData ? (
        <div className="flex-1 min-h-[260px] flex flex-col items-center justify-center text-center p-6 border border-dashed border-slate-800 rounded-xl bg-slate-950/40">
          <div className="h-12 w-12 rounded-2xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center mb-3">
            <svg
              className="w-6 h-6"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
              />
            </svg>
          </div>
          <h3 className="text-sm font-semibold text-white mb-1">
            No Application Data
          </h3>
          <p className="text-xs text-slate-400 max-w-sm">
            You currently have no job postings. Once you publish jobs and candidates apply, this chart will display candidate volumes.
          </p>
        </div>
      ) : (
        <div className="w-full h-[280px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={chartData}
              margin={{ top: 10, right: 10, left: -20, bottom: 25 }}
            >
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="#1e293b"
                vertical={false}
              />
              <XAxis
                dataKey="shortTitle"
                stroke="#64748b"
                fontSize={11}
                tickLine={false}
                axisLine={{ stroke: '#334155' }}
                interval={0}
                angle={-20}
                textAnchor="end"
              />
              <YAxis
                stroke="#64748b"
                fontSize={11}
                tickLine={false}
                axisLine={{ stroke: '#334155' }}
                allowDecimals={false}
                domain={[0, maxCount]}
              />
              <Tooltip
                content={<CustomTooltip />}
                cursor={{ fill: 'rgba(99, 102, 241, 0.08)' }}
              />
              <Bar
                dataKey="count"
                radius={[6, 6, 0, 0]}
                maxBarSize={48}
              >
                {chartData.map((entry, index) => (
                  <Cell
                    key={`cell-${entry.job_id || index}`}
                    fill={entry.count > 0 ? '#6366f1' : '#334155'}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

