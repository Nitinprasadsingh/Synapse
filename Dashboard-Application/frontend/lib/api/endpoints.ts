import { api } from "./client";
import {
  AuthToken,
  User,
  OverviewDashboardData,
  EnergyFlow,
  OverviewKpis,
  PVForecastResponse,
  LoadForecastResponse,
  CombinedForecastResponse,
  ModelMetadata,
  BatteryStatus,
  BatteryConfig,
  BatterySchedule,
  GridStatus,
  GridConfig,
  GridAnalytics,
  AnalyticsSummary,
  SystemAlert,
  AllSettings,
} from "@/types";

export const endpoints = {
  // Auth
  login: (data: { email: string; password: string }) =>
    api.post<AuthToken>("/auth/login", data),
  logout: () => api.post<{ message: string }>("/auth/logout"),
  getCurrentUser: () => api.get<User>("/auth/me"),

  // Dashboard
  getDashboardOverview: () => api.get<OverviewDashboardData>("/dashboard/overview"),
  getEnergyFlow: () => api.get<EnergyFlow>("/dashboard/energy-flow"),
  getKpis: () => api.get<OverviewKpis>("/dashboard/kpis"),

  // Forecasting
  getPVForecast: (horizon = 24, modelId = "open-meteo-xgboost-v1") =>
    api.get<PVForecastResponse>(`/forecasts/pv?horizon=${horizon}&model_id=${modelId}`),
  getLoadForecast: (horizon = 24, modelId = "lstm-load-forecaster-v1") =>
    api.get<LoadForecastResponse>(`/forecasts/load?horizon=${horizon}&model_id=${modelId}`),
  getCombinedForecast: (horizon = 24) =>
    api.get<CombinedForecastResponse>(`/forecasts/combined?horizon=${horizon}`),
  getModels: () => api.get<ModelMetadata[]>("/forecasts/models"),

  // Battery
  getBatteryStatus: () => api.get<BatteryStatus>("/battery/status"),
  getBatteryConfig: () => api.get<BatteryConfig>("/battery/config"),
  updateBatteryConfig: (data: Partial<BatteryConfig>) =>
    api.put<BatteryConfig>("/battery/config", data),
  getBatterySchedule: () => api.get<BatterySchedule>("/battery/schedule"),
  generateBatterySchedule: (horizon_hours = 24, custom_initial_soc?: number) =>
    api.post<BatterySchedule>("/battery/schedule/generate", {
      horizon_hours,
      custom_initial_soc,
    }),

  // Grid
  getGridStatus: () => api.get<GridStatus>("/grid/status"),
  getGridConfig: () => api.get<GridConfig>("/grid/config"),
  updateGridConfig: (data: Partial<GridConfig>) =>
    api.put<GridConfig>("/grid/config", data),
  getGridAnalytics: () => api.get<GridAnalytics>("/grid/analytics"),

  // Analytics
  getAnalyticsSummary: (period = "7d") =>
    api.get<AnalyticsSummary>(`/analytics/summary?period=${period}`),
  getReports: () => api.get<any[]>("/analytics/reports"),
  exportAnalyticsUrl: (format = "csv", period = "7d") => {
    const base = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
    return `${base}/analytics/export?format=${format}&period=${period}`;
  },

  // Alerts
  getAlerts: (params?: { category?: string; severity?: string; is_acknowledged?: boolean }) => {
    const q = new URLSearchParams();
    if (params?.category) q.append("category", params.category);
    if (params?.severity) q.append("severity", params.severity);
    if (params?.is_acknowledged !== undefined)
      q.append("is_acknowledged", String(params.is_acknowledged));
    return api.get<SystemAlert[]>(`/alerts${q.toString() ? `?${q.toString()}` : ""}`);
  },
  acknowledgeAlert: (alertId: number) =>
    api.post<SystemAlert>(`/alerts/${alertId}/acknowledge`),
  createAlert: (data: { title: string; message: string; category: string; severity: string }) =>
    api.post<SystemAlert>("/alerts", data),

  // Settings
  getAllSettings: () => api.get<AllSettings>("/settings"),
  updateAllSettings: (data: Partial<AllSettings>) =>
    api.put<AllSettings>("/settings", data),

  // System
  getSystemHealth: () => api.get<{ status: string; version: string; database: string }>("/system/health"),
  getSystemStatus: () => api.get<{ demo_mode: boolean; simulation_refresh_seconds: number; badge: string }>("/system/status"),
};
