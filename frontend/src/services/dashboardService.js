import api from "./api";

export async function getFarmerDashboard() {
  const r = await api.get("/api/dashboard/farmer");
  return r.data;
}

export async function getBuyerDashboard() {
  const r = await api.get("/api/dashboard/buyer");
  return r.data;
}
