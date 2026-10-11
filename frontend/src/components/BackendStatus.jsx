import { useBackendStatus } from '../hooks/useBackendStatus'

export default function BackendStatus() {
  const { status } = useBackendStatus()

  const config = {
    checking:  { dot: 'bg-amber-400 animate-pulse', label: 'Checking…',  text: 'text-brand-300' },
    connected: { dot: 'bg-lime-400',                 label: 'Connected',   text: 'text-lime-300'  },
    offline:   { dot: 'bg-red-400',                  label: 'Offline',     text: 'text-red-300'   },
  }[status] || { dot: 'bg-neutral-400', label: 'Unknown', text: 'text-neutral-400' }

  return (
    <span className={`inline-flex items-center gap-1.5 text-xs font-medium ${config.text}`}>
      <span className={`w-2 h-2 rounded-full shrink-0 ${config.dot}`} aria-hidden="true" />
      API: {config.label}
    </span>
  )
}
