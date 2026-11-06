/**
 * StatusBadge component.
 * Displays normalized status badges across candidate and recruiter interfaces.
 * Maps status="applied" to "Awaiting review" per recruiter workflow requirements.
 */
export function StatusBadge({ status, type }) {
  // Handle consent type specifically
  if (type === 'consent') {
    const isGranted = Boolean(status);
    return (
      <span
        className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium border ${
          isGranted
            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
            : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
        }`}
      >
        <span
          className={`h-1.5 w-1.5 rounded-full ${
            isGranted ? 'bg-emerald-400' : 'bg-amber-400'
          }`}
        />
        {isGranted ? 'Granted' : 'Required'}
      </span>
    );
  }

  // Normalize string status safely
  const normalizedStatus =
    typeof status === 'string' ? status.toLowerCase().trim() : '';

  // Custom labels for specific domain statuses
  const customLabels = {
    applied: 'Awaiting review',
    awaiting_review: 'Awaiting review',
    shortlist: 'Shortlisted',
    shortlisted: 'Shortlisted',
    hold: 'On Hold',
    on_hold: 'On Hold',
    reject: 'Rejected',
    rejected: 'Rejected',
    interviewing: 'Interviewing',
    completed: 'Completed',
    reviewed: 'Reviewed',
    open: 'Open',
    closed: 'Closed',
    parsed: 'Parsed',
    pending: 'Pending',
    failed: 'Failed',
    active: 'Active',
    inactive: 'Inactive',
    approved: 'Approved',
  };

  // Modern styling matching the dark application theme
  const statusStyles = {
    // Review / Pipeline stages
    applied: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    awaiting_review: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    interviewing: 'bg-sky-500/10 text-sky-400 border-sky-500/20',
    completed: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
    reviewed: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
    shortlist: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    shortlisted: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    hold: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    on_hold: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    reject: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
    rejected: 'bg-rose-500/10 text-rose-400 border-rose-500/20',

    // Job posting statuses
    open: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    closed: 'bg-slate-500/10 text-slate-400 border-slate-500/20',

    // Parser & generic statuses
    parsed: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    pending: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    failed: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
    active: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    inactive: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
    approved: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  };

  const label =
    customLabels[normalizedStatus] ||
    (normalizedStatus
      ? normalizedStatus.charAt(0).toUpperCase() + normalizedStatus.slice(1)
      : 'Unknown');

  const styles =
    statusStyles[normalizedStatus] ||
    'bg-slate-800/80 text-slate-300 border-slate-700';

  // Status indicator dot color
  const dotColor =
    normalizedStatus === 'applied' ||
    normalizedStatus === 'awaiting_review' ||
    normalizedStatus === 'pending' ||
    normalizedStatus === 'hold' ||
    normalizedStatus === 'on_hold'
      ? 'bg-amber-400'
      : normalizedStatus === 'shortlist' ||
        normalizedStatus === 'shortlisted' ||
        normalizedStatus === 'open' ||
        normalizedStatus === 'parsed' ||
        normalizedStatus === 'active' ||
        normalizedStatus === 'approved'
      ? 'bg-emerald-400'
      : normalizedStatus === 'reject' ||
        normalizedStatus === 'rejected' ||
        normalizedStatus === 'failed'
      ? 'bg-rose-400'
      : normalizedStatus === 'interviewing'
      ? 'bg-sky-400'
      : normalizedStatus === 'completed'
      ? 'bg-purple-400'
      : 'bg-slate-400';

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium border ${styles}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full shrink-0 ${dotColor}`} />
      <span>{label}</span>
    </span>
  );
}

export default StatusBadge;
