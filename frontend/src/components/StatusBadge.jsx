const StatusBadge = ({ status }) => {
  // Normalize the value safely before using string methods.
  const normalizedStatus =
    typeof status === "string" ? status.toLowerCase().trim() : "";

  const statusStyles = {
    pending: "bg-amber-100 text-amber-800",
    parsed: "bg-green-100 text-green-800",
    failed: "bg-red-100 text-red-800",
    active: "bg-green-100 text-green-800",
    inactive: "bg-gray-100 text-gray-700",
    approved: "bg-green-100 text-green-800",
    rejected: "bg-red-100 text-red-800",
  };

  const label = normalizedStatus
    ? normalizedStatus.charAt(0).toUpperCase() + normalizedStatus.slice(1)
    : "Unknown";

  const styles = statusStyles[normalizedStatus] || "bg-gray-100 text-gray-700";

  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium ${styles}`}
    >
      {label}
    </span>
  );
};

export default StatusBadge;
