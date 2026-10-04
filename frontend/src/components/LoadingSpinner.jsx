/**
 * LoadingSpinner — used for full-section loading states.
 * size: "sm" | "md" (default) | "lg"
 */
export default function LoadingSpinner({ size = "md", message = "Loading…" }) {
  const sizes = { sm: "w-4 h-4", md: "w-6 h-6", lg: "w-8 h-8" };
  return (
    <div className="flex flex-col items-center justify-center py-12 gap-3 text-gray-400">
      <span
        className={`${sizes[size]} border-2 border-gray-200 border-t-green-600 rounded-full animate-spin`}
      />
      <span className="text-sm">{message}</span>
    </div>
  );
}
