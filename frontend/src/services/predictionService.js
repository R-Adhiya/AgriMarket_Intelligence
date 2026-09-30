/**
 * Price Prediction API service — Phase 7.
 */

import api from "./api";

/**
 * @param {number} cropId
 * @param {number} marketId
 * @param {number} horizon  - 1, 3, or 7
 */
export async function getPricePrediction(cropId, marketId, horizon = 1) {
  const r = await api.get("/api/prediction/price", {
    params: { crop_id: cropId, market_id: marketId, horizon },
  });
  return r.data;
}
