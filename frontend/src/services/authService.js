/**
 * Authentication service — wraps all auth-related API calls.
 * The JWT is stored in localStorage under a single key.
 */

import api from "./api";

const TOKEN_KEY = "agrimarket_access_token";

// ── Token helpers ─────────────────────────────────────────────────────────────

export function getStoredToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setStoredToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function removeStoredToken() {
  localStorage.removeItem(TOKEN_KEY);
}

// ── API calls ─────────────────────────────────────────────────────────────────

/**
 * Register a new farmer or buyer account.
 * @param {{ full_name, email, phone, password, role }} data
 */
export async function register(data) {
  const response = await api.post("/api/auth/register", data);
  return response.data;
}

/**
 * Login and receive a JWT.
 * Stores the token automatically.
 * @param {{ email, password }} credentials
 * @returns {{ access_token, token_type }}
 */
export async function login({ email, password }) {
  const response = await api.post("/api/auth/login", { email, password });
  const { access_token } = response.data;
  setStoredToken(access_token);
  return response.data;
}

/**
 * Fetch the currently authenticated user's profile.
 * Requires a valid token in localStorage.
 */
export async function getCurrentUser() {
  const token = getStoredToken();
  if (!token) return null;
  const response = await api.get("/api/auth/me", {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.data;
}

/**
 * Logout — clears the stored token locally.
 * No backend call needed for stateless JWT auth.
 */
export function logout() {
  removeStoredToken();
}
