import api from "./api";

export const getAdminDashboard = () =>
  api.get("/api/admin/dashboard").then(r => r.data);

export const getAdminUsers = (params = {}) =>
  api.get("/api/admin/users", { params }).then(r => r.data);

export const getAdminUser = (id) =>
  api.get(`/api/admin/users/${id}`).then(r => r.data);

export const updateUserStatus = (id, is_active) =>
  api.patch(`/api/admin/users/${id}/status`, { is_active }).then(r => r.data);

export const getAdminFarmers = (params = {}) =>
  api.get("/api/admin/farmers", { params }).then(r => r.data);

export const getAdminBuyers = (params = {}) =>
  api.get("/api/admin/buyers", { params }).then(r => r.data);

export const getAdminMarkets = (params = {}) =>
  api.get("/api/admin/markets", { params }).then(r => r.data);

export const getAdminMarketPrices = (params = {}) =>
  api.get("/api/admin/market-prices", { params }).then(r => r.data);

export const getAdminActivity = (params = {}) =>
  api.get("/api/admin/activity", { params }).then(r => r.data);
