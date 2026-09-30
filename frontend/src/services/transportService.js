/**
 * Transport / Location API service — Phase 6.
 */

import api from "./api";

/**
 * Get distance + estimated transport cost for all active markets.
 * @param {number} quantity  Quantity in quintals
 * @param {string} [state]   Optional state filter
 */
export async function getAllMarketTransport(quantity = 10, state) {
  const params = { quantity };
  if (state) params.state = state;
  const r = await api.get("/api/transport/markets", { params });
  return r.data;
}

/**
 * Get distance + transport estimate for a single market.
 * @param {number} marketId
 * @param {number} quantity  Quantity in quintals
 */
export async function getMarketTransport(marketId, quantity = 10) {
  const r = await api.get(`/api/transport/estimate/${marketId}`, {
    params: { quantity },
  });
  return r.data;
}
