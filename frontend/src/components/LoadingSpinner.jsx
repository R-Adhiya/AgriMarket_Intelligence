/**
 * LoadingSpinner — full-page or inline centered loading indicator.
 * Props:
 *   size  — 'sm' | 'md' (default) | 'lg'
 *   label — accessible label (default "Loading…")
 */
export default function LoadingSpinner({ size = "md", label = "Loading…" }) {
  const sizes = {
    sm: "w-4 h-4 border-2",
    md: "w-8 h-8 border-[3px]",
    lg: "w-12 h-12 border-4",
  };

  return (
    <div className="flex flex-col items-center justify-center py-16 gap-3" role="status" aria-label={label}>
      <div
        className={`${sizes[size]} border-brand-200 border-t-brand-600 rounded-full animate-spin`}
        aria-hidden="true"
      />
      <p className="text-sm text-neutral-400">{label}</p>
    </div>
  );
}
