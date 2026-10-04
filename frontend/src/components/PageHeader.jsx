/**
 * PageHeader — consistent page-level header used across all app pages.
 * Props:
 *   icon        — Lucide icon component (optional)
 *   title       — main heading string
 *   subtitle    — muted subheading string (optional)
 *   action      — ReactNode rendered on the right (optional)
 */
export default function PageHeader({ icon: Icon, title, subtitle, action }) {
  return (
    <div className="flex items-start justify-between gap-4 mb-6">
      <div className="flex items-center gap-3 min-w-0">
        {Icon && (
          <span className="flex items-center justify-center w-10 h-10 bg-green-50 rounded-xl shrink-0">
            <Icon className="w-5 h-5 text-green-700" />
          </span>
        )}
        <div className="min-w-0">
          <h1 className="text-xl sm:text-2xl font-bold text-gray-900 leading-tight truncate">{title}</h1>
          {subtitle && <p className="text-sm text-gray-500 mt-0.5">{subtitle}</p>}
        </div>
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </div>
  );
}
