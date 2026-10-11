/**
 * Farmer API service — profile, crop management, and buyer-requirement interests.
 */

import api from "./api";

// ── Profile ───────────────────────────────────────────────────────────────────

export async function getFarmerProfile() {
  const r = await api.get("/api/farmer/profile");
  return r.data;
}

export async function updateFarmerProfile(data) {
  const r = await api.put("/api/farmer/profile", data);
  return r.data;
}

// ── Crops ──────────────────────────────────────────────────────────────────────

export async function getFarmerCrops() {
  const r = await api.get("/api/farmer/crops");
  return r.data;
}

export async function addFarmerCrop(data) {
  const r = await api.post("/api/farmer/crops", data);
  return r.data;
}

export async function updateFarmerCrop(id, data) {
  const r = await api.put(`/api/farmer/crops/${id}`, data);
  return r.data;
}

export async function deleteFarmerCrop(id) {
  await api.delete(`/api/farmer/crops/${id}`);
}

// ── Buyer requirements (farmer discovery) ─────────────────────────────────────

export async function getFarmerBuyerRequirements() {
  const r = await api.get("/api/farmer/buyer-requirements");
  return r.data;
}

// ── Farmer interests (Correction 1) ───────────────────────────────────────────

export async function farmerExpressInterest(requirementId, notes = "") {
  const params = new URLSearchParams({ requirement_id: requirementId });
  if (notes) params.append("notes", notes);
  const r = await api.post(`/api/farmer/interests?${params.toString()}`);
  return r.data;
}

export async function getFarmerInterests() {
  const r = await api.get("/api/farmer/interests");
  return r.data;
}
