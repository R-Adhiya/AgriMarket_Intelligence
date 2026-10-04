/**
 * StatusBadge — consistent status chip used across buyer/farmer marketplace.
 * Covers: PENDING, ACCEPTED, REJECTED, CANCELLED, ACTIVE, FULFILLED, EXPIRED
 */
export default function StatusBadge({ status }) {
  const map = {
    PENDING:   "bg-amber-100 text-amber-700 border border-amber-200",
    ACCEPTED:  "bg-green-100 text-green-700 border border-green-200",
    REJECTED:  "bg-red-100 text-red-700 border border-red-200",
    CANCELLED: "bg-gray-100 text-gray-500 border border-gray-200",
    ACTIVE:    "bg-green-100 text-green-700 border border-green-200",
    FULFILLED: "bg-blue-100 text-blue-700 border border-blue-200",
    EXPIRED:   "bg-gray-100 text-gray-500 border border-gray-200",
  };
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-semibold tracking-wide
                  ${map[status] || "bg-gray-100 text-gray-600 border border-gray-200"}`}
    >
      {status}
    </span>
  );
}
