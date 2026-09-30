import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const TOKEN_KEY = "agrimarket_access_token";

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: { "Content-Type": "application/json" },
});

// Attach JWT automatically to every request that doesn't already carry one
api.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY);
  if (token && !config.headers["Authorization"]) {
    config.headers["Authorization"] = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 globally — clear stale token and redirect to login
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem(TOKEN_KEY);
      if (!window.location.pathname.startsWith("/login")) {
        window.location.href = "/login";
      }
    }
    console.error("[API Error]", error.message);
    return Promise.reject(error);
  }
);

/**
 * Check whether the backend API is reachable.
 * @returns {{ status: string, service: string }}
 */
export async function checkHealth() {
  const response = await api.get("/api/health");
  return response.data;
}

export default api;
