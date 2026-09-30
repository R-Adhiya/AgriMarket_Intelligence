/**
 * Market Intelligence API service — Phase 5.
 */

import api from "./api";

export async function getMarkets({ state, district } = {}) {
  const params = {};
  if (state)    params.state    = state;
  if (district) params.district = district;
  const r = await api.get("/api/market/markets", { params });
  return r.data;
}

export async function getCropsWithPrices() {
  const r = await api.get("/api/market/crops");
  return r.data;
}

export async function comparePrices(cropId, { state, district } = {}) {
  const params = {};
  if (state)    params.state    = state;
  if (district) params.district = district;
  const r = await api.get(`/api/market/prices/${cropId}`, { params });
  return r.data;
}

export async function getPriceHistory(cropId, { days = 30, marketId } = {}) {
  const params = { days };
  if (marketId) params.market_id = marketId;
  const r = await api.get(`/api/market/prices/${cropId}/history`, { params });
  return r.data;
}
