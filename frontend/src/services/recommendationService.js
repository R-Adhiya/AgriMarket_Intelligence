/**
 * Recommendation API service — Phase 8.
 */

import api from "./api";

export async function getRecommendation({ cropId, quantityKg, priceBasis = "current" }) {
  const r = await api.post("/api/recommendation/market", {
    crop_id:     cropId,
    quantity_kg: quantityKg,
    price_basis: priceBasis,
  });
  return r.data;
}

export async function getRecommendationHistory() {
  const r = await api.get("/api/recommendation/history");
  return r.data;
}
