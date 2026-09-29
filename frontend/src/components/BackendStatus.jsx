import { useBackendStatus } from '../hooks/useBackendStatus'

export default function BackendStatus() {
  const { status } = useBackendStatus()

  const config = {
    checking: { dot: 'bg-yellow-400 animate-pulse', label: 'Checking…', text: 'text-yellow-700' },
    connected: { dot: 'bg-green-500',               label: 'Connected',  text: 'text-green-700'  },
    offline:   { dot: 'bg-red-500',                 label: 'Offline',    text: 'text-red-700'    },
  }[status]

  return (
    <span className={`inline-flex items-center gap-1.5 text-xs font-medium ${config.text}`}>
      <span className={`w-2 h-2 rounded-full shrink-0 ${config.dot}`} />
      Backend Status: {config.label}
    </span>
  )
}
