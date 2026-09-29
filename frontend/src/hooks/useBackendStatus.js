import { useState, useEffect } from 'react'
import { checkHealth } from '../services/api'

/**
 * Polls the backend health endpoint once on mount.
 * Returns { status: 'connected' | 'offline' | 'checking', service }
 */
export function useBackendStatus() {
  const [status, setStatus] = useState('checking')
  const [service, setService] = useState(null)

  useEffect(() => {
    let cancelled = false

    async function ping() {
      try {
        const data = await checkHealth()
        if (!cancelled) {
          setStatus('connected')
          setService(data.service)
        }
      } catch {
        if (!cancelled) setStatus('offline')
      }
    }

    ping()
    return () => { cancelled = true }
  }, [])

  return { status, service }
}
