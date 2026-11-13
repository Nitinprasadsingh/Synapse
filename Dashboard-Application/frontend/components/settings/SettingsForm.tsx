"use client";

import React, { useState } from "react";
import { AllSettings } from "@/types";
import { Save, AlertCircle, CheckCircle2, Lock } from "lucide-react";
import { useAuth } from "@/lib/auth/AuthContext";

interface SettingsFormProps {
  initialSettings: AllSettings;
  onSave: (updated: AllSettings) => Promise<void>;
}

export function SettingsForm({ initialSettings, onSave }: SettingsFormProps) {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";

  const [formData, setFormData] = useState<AllSettings>(initialSettings);
  const [isSaving, setIsSaving] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setSuccessMsg(null);

    // Frontend validation
    if (formData.battery.min_soc > formData.battery.max_soc) {
      setErrorMsg("Validation Error: Minimum SOC cannot be greater than Maximum SOC.");
      return;
    }
    if (formData.battery.capacity_kwh <= 0) {
      setErrorMsg("Validation Error: Battery capacity must be strictly positive.");
      return;
    }
    if (formData.pv.installed_capacity_kw <= 0) {
      setErrorMsg("Validation Error: PV installed capacity must be positive.");
      return;
    }

    setIsSaving(true);
    try {
      await onSave(formData);
      setSuccessMsg("System configuration successfully persisted to PostgreSQL.");
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to persist configuration.");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Role permission banner */}
      {!isAdmin && (
        <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg flex items-center gap-2 text-xs text-amber-800">
          <Lock className="w-4 h-4 text-amber-600" />
          <span>
            You are signed in with <strong>{user?.role?.toUpperCase()}</strong> role (Read-Only Mode). Contact System Administrator to modify parameters.
          </span>
        </div>
      )}

      {errorMsg && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-xs text-red-800 font-medium">
          <AlertCircle className="w-4 h-4 text-red-600" />
          <span>{errorMsg}</span>
        </div>
      )}

      {successMsg && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg flex items-center gap-2 text-xs text-emerald-800 font-medium">
          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Grid: 4 Configuration Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* 1. Solar PV Configuration */}
        <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm space-y-4">
          <div className="border-b border-slate-100 pb-2">
            <h4 className="text-sm font-bold text-slate-900 uppercase tracking-wide">
              Solar PV Plant Configuration
            </h4>
            <span className="text-xs text-slate-500">Photovoltaic hardware & generation parameters</span>
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <label className="font-semibold text-slate-700 block mb-1">
                Installed Capacity (kW)
              </label>
              <input
                type="number"
                step="0.1"
                disabled={!isAdmin}
                value={formData.pv.installed_capacity_kw}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    pv: { ...formData.pv, installed_capacity_kw: parseFloat(e.target.value) || 0 },
                  })
                }
                className="w-full border border-slate-300 rounded px-3 py-1.5 font-mono disabled:bg-slate-50"
              />
            </div>

            <div>
              <label className="font-semibold text-slate-700 block mb-1">
                PV Derating Factor (0.0 - 1.0)
              </label>
              <input
                type="number"
                step="0.01"
                min="0.1"
                max="1.0"
                disabled={!isAdmin}
                value={formData.pv.derating_factor}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    pv: { ...formData.pv, derating_factor: parseFloat(e.target.value) || 0 },
                  })
                }
                className="w-full border border-slate-300 rounded px-3 py-1.5 font-mono disabled:bg-slate-50"
              />
            </div>

            <div>
              <label className="font-semibold text-slate-700 block mb-1">
                Inverter / System Efficiency
              </label>
              <input
                type="number"
                step="0.01"
                min="0.1"
                max="1.0"
                disabled={!isAdmin}
                value={formData.pv.system_efficiency}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    pv: { ...formData.pv, system_efficiency: parseFloat(e.target.value) || 0 },
                  })
                }
                className="w-full border border-slate-300 rounded px-3 py-1.5 font-mono disabled:bg-slate-50"
              />
            </div>

            <div>
              <label className="font-semibold text-slate-700 block mb-1">
                Operational PV Model Identifier
              </label>
              <select
                disabled={!isAdmin}
                value={formData.pv.pv_model_identifier}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    pv: { ...formData.pv, pv_model_identifier: e.target.value },
                  })
                }
                className="w-full border border-slate-300 rounded px-3 py-1.5 font-mono bg-white disabled:bg-slate-50"
              >
                <option value="open-meteo-xgboost-v1">open-meteo-xgboost-v1 (Operational)</option>
                <option value="nsrdb-xgboost-benchmark">nsrdb-xgboost-benchmark (NSRDB Baseline)</option>
              </select>
            </div>
          </div>
        </div>

        {/* 2. Battery Storage Configuration */}
        <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm space-y-4">
          <div className="border-b border-slate-100 pb-2">
            <h4 className="text-sm font-bold text-slate-900 uppercase tracking-wide">
              Battery Storage (BESS) Parameters
            </h4>
            <span className="text-xs text-slate-500">Lithium-ion electrochemical constraints & SOC limits</span>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs">
            <div>
              <label className="font-semibold text-slate-700 block mb-1">Capacity (kWh)</label>
              <input
                type="number"
                step="1"
                disabled={!isAdmin}
                value={formData.battery.capacity_kwh}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    battery: { ...formData.battery, capacity_kwh: parseFloat(e.target.value) || 0 },
                  })
                }
                className="w-full border border-slate-300 rounded px-3 py-1.5 font-mono disabled:bg-slate-50"
              />
            </div>

            <div>
              <label className="font-semibold text-slate-700 block mb-1">Initial SOC (%)</label>
              <input
                type="number"
                step="1"
                min="0"
                max="100"
                disabled={!isAdmin}
                value={formData.battery.initial_soc}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    battery: { ...formData.battery, initial_soc: parseFloat(e.target.value) || 0 },
                  })
                }
                className="w-full border border-slate-300 rounded px-3 py-1.5 font-mono disabled:bg-slate-50"
              />
            </div>

            <div>
              <label className="font-semibold text-slate-700 block mb-1">Minimum SOC (%)</label>
              <input
                type="number"
                step="1"
                min="0"
                max="100"
                disabled={!isAdmin}
                value={formData.battery.min_soc}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    battery: { ...formData.battery, min_soc: parseFloat(e.target.value) || 0 },
                  })
                }
                className="w-full border border-slate-300 rounded px-3 py-1.5 font-mono disabled:bg-slate-50"
              />
            </div>

            <div>
              <label className="font-semibold text-slate-700 block mb-1">Maximum SOC (%)</label>
              <input
                type="number"
                step="1"
                min="0"
                max="100"
                disabled={!isAdmin}
                value={formData.battery.max_soc}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    battery: { ...formData.battery, max_soc: parseFloat(e.target.value) || 0 },
                  })
                }
                className="w-full border border-slate-300 rounded px-3 py-1.5 font-mono disabled:bg-slate-50"
              />
            </div>

            <div>
              <label className="font-semibold text-slate-700 block mb-1">Max Charge (kW)</label>
              <input
                type="number"
                step="1"
                disabled={!isAdmin}
                value={formData.battery.max_charge_kw}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    battery: { ...formData.battery, max_charge_kw: parseFloat(e.target.value) || 0 },
                  })
                }
                className="w-full border border-slate-300 rounded px-3 py-1.5 font-mono disabled:bg-slate-50"
              />
            </div>

            <div>
              <label className="font-semibold text-slate-700 block mb-1">Max Discharge (kW)</label>
              <input
                type="number"
                step="1"
                disabled={!isAdmin}
                value={formData.battery.max_discharge_kw}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    battery: { ...formData.battery, max_discharge_kw: parseFloat(e.target.value) || 0 },
                  })
                }
                className="w-full border border-slate-300 rounded px-3 py-1.5 font-mono disabled:bg-slate-50"
              />
            </div>

            <div>
              <label className="font-semibold text-slate-700 block mb-1">Charge Efficiency</label>
              <input
                type="number"
                step="0.01"
                min="0.1"
                max="1.0"
                disabled={!isAdmin}
                value={formData.battery.charge_efficiency}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    battery: { ...formData.battery, charge_efficiency: parseFloat(e.target.value) || 0 },
                  })
                }
                className="w-full border border-slate-300 rounded px-3 py-1.5 font-mono disabled:bg-slate-50"
              />
            </div>

            <div>
              <label className="font-semibold text-slate-700 block mb-1">Discharge Efficiency</label>
              <input
                type="number"
                step="0.01"
                min="0.1"
                max="1.0"
                disabled={!isAdmin}
                value={formData.battery.discharge_efficiency}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    battery: { ...formData.battery, discharge_efficiency: parseFloat(e.target.value) || 0 },
                  })
                }
                className="w-full border border-slate-300 rounded px-3 py-1.5 font-mono disabled:bg-slate-50"
              />
            </div>
          </div>
        </div>

        {/* 3. Utility Grid Configuration */}
        <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm space-y-4">
          <div className="border-b border-slate-100 pb-2">
            <h4 className="text-sm font-bold text-slate-900 uppercase tracking-wide">
              Grid Interconnection & Tariffs
            </h4>
            <span className="text-xs text-slate-500">Distribution feeder limits and energy purchase pricing</span>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs">
            <div>
              <label className="font-semibold text-slate-700 block mb-1">Import Limit (kW)</label>
              <input
                type="number"
                step="1"
                disabled={!isAdmin}
                value={formData.grid.import_limit_kw}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    grid: { ...formData.grid, import_limit_kw: parseFloat(e.target.value) || 0 },
                  })
                }
                className="w-full border border-slate-300 rounded px-3 py-1.5 font-mono disabled:bg-slate-50"
              />
            </div>

            <div>
              <label className="font-semibold text-slate-700 block mb-1">Export Limit (kW)</label>
              <input
                type="number"
                step="1"
                disabled={!isAdmin}
                value={formData.grid.export_limit_kw}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    grid: { ...formData.grid, export_limit_kw: parseFloat(e.target.value) || 0 },
                  })
                }
                className="w-full border border-slate-300 rounded px-3 py-1.5 font-mono disabled:bg-slate-50"
              />
            </div>

            <div>
              <label className="font-semibold text-slate-700 block mb-1">Import Tariff ($/kWh)</label>
              <input
                type="number"
                step="0.01"
                disabled={!isAdmin}
                value={formData.grid.import_tariff}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    grid: { ...formData.grid, import_tariff: parseFloat(e.target.value) || 0 },
                  })
                }
                className="w-full border border-slate-300 rounded px-3 py-1.5 font-mono disabled:bg-slate-50"
              />
            </div>

            <div>
              <label className="font-semibold text-slate-700 block mb-1">Feed-In Tariff ($/kWh)</label>
              <input
                type="number"
                step="0.01"
                disabled={!isAdmin}
                value={formData.grid.export_tariff}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    grid: { ...formData.grid, export_tariff: parseFloat(e.target.value) || 0 },
                  })
                }
                className="w-full border border-slate-300 rounded px-3 py-1.5 font-mono disabled:bg-slate-50"
              />
            </div>
          </div>
        </div>

        {/* 4. Forecasting & Optimization Intervals */}
        <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm space-y-4">
          <div className="border-b border-slate-100 pb-2">
            <h4 className="text-sm font-bold text-slate-900 uppercase tracking-wide">
              Forecasting Horizons & Scheduling
            </h4>
            <span className="text-xs text-slate-500">Lookahead horizons for predictive controllers</span>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs">
            <div>
              <label className="font-semibold text-slate-700 block mb-1">Forecast Horizon (Hours)</label>
              <input
                type="number"
                step="1"
                min="1"
                max="168"
                disabled={!isAdmin}
                value={formData.forecast.forecast_horizon_hours}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    forecast: { ...formData.forecast, forecast_horizon_hours: parseInt(e.target.value) || 24 },
                  })
                }
                className="w-full border border-slate-300 rounded px-3 py-1.5 font-mono disabled:bg-slate-50"
              />
            </div>

            <div>
              <label className="font-semibold text-slate-700 block mb-1">Schedule Horizon (Hours)</label>
              <input
                type="number"
                step="1"
                min="1"
                max="168"
                disabled={!isAdmin}
                value={formData.forecast.scheduling_horizon_hours}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    forecast: { ...formData.forecast, scheduling_horizon_hours: parseInt(e.target.value) || 24 },
                  })
                }
                className="w-full border border-slate-300 rounded px-3 py-1.5 font-mono disabled:bg-slate-50"
              />
            </div>

            <div>
              <label className="font-semibold text-slate-700 block mb-1">Optimization Step (Min)</label>
              <input
                type="number"
                step="5"
                min="5"
                max="1440"
                disabled={!isAdmin}
                value={formData.forecast.optimization_interval_minutes}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    forecast: { ...formData.forecast, optimization_interval_minutes: parseInt(e.target.value) || 60 },
                  })
                }
                className="w-full border border-slate-300 rounded px-3 py-1.5 font-mono disabled:bg-slate-50"
              />
            </div>

            <div>
              <label className="font-semibold text-slate-700 block mb-1">Model Refresh (Min)</label>
              <input
                type="number"
                step="5"
                min="5"
                max="1440"
                disabled={!isAdmin}
                value={formData.forecast.forecast_update_interval_minutes}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    forecast: { ...formData.forecast, forecast_update_interval_minutes: parseInt(e.target.value) || 60 },
                  })
                }
                className="w-full border border-slate-300 rounded px-3 py-1.5 font-mono disabled:bg-slate-50"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Save Button for Admin */}
      {isAdmin && (
        <div className="flex justify-end pt-2">
          <button
            type="submit"
            disabled={isSaving}
            className="inline-flex items-center gap-2 px-6 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm shadow transition-all disabled:opacity-50"
          >
            <Save className="w-4 h-4" />
            {isSaving ? "Persisting Parameters..." : "Save System Parameters"}
          </button>
        </div>
      )}
    </form>
  );
}
