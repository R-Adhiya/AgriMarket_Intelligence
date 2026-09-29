import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Response interceptor — centralised error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Log for debugging; do not crash the app
    console.error('[API Error]', error.message)
    return Promise.reject(error)
  }
)

/**
 * Check whether the backend API is reachable.
 * @returns {{ status: string, service: string }}
 */
export async function checkHealth() {
  const response = await apiClient.get('/api/health')
  return response.data
}

export default apiClient
