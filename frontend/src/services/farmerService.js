/**
 * Farmer API service — profile and crop management.
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
