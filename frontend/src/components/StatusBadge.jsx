/**
 * StatusBadge — consistent status chip using design system badge classes.
 * Covers: PENDING, ACCEPTED, REJECTED, CANCELLED, ACTIVE, FULFILLED, EXPIRED
 */
export default function StatusBadge({ status }) {
  const map = {
    PENDING:   "badge-pending",
    ACCEPTED:  "badge-accepted",
    REJECTED:  "badge-rejected",
    CANCELLED: "badge-cancelled",
    ACTIVE:    "badge-active",
    FULFILLED: "badge-fulfilled",
    EXPIRED:   "badge-expired",
  };

  const cls = map[status] || "badge bg-neutral-100 text-neutral-500 border-neutral-300";

  // Short dot indicator
  const dots = {
    PENDING:   "bg-amber-400",
    ACCEPTED:  "bg-lime-500",
    REJECTED:  "bg-red-400",
    CANCELLED: "bg-neutral-400",
    ACTIVE:    "bg-brand-500",
    FULFILLED: "bg-sky-400",
    EXPIRED:   "bg-neutral-300",
  };
  const dotCls = dots[status] || "bg-neutral-400";

  return (
    <span className={cls}>
      <span className={`w-1.5 h-1.5 rounded-full ${dotCls}`} aria-hidden="true" />
      {status}
    </span>
  );
}
