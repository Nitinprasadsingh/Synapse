import React from "react";
import { BatteryStatus } from "@/types";
import { Battery, Zap, Shield, HeartPulse } from "lucide-react";
import { formatKw, formatKwh, formatPct } from "@/lib/utils";

interface BatteryOverviewCardProps {
  status: BatteryStatus;
}

export function BatteryOverviewCard({ status }: BatteryOverviewCardProps) {
  const isCharging = status.mode === "CHARGING";
  const isDischarging = status.mode === "DISCHARGING";

  return (
    <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pb-4 mb-4 border-b border-slate-100">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-purple-100 text-purple-700 flex items-center justify-center">
            <Battery className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-900">
              Battery Energy Storage System (BESS)
            </h3>
            <span className="text-xs text-slate-500">
              Lithium Iron Phosphate (LFP) Substation Bank
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span
            className={`px-3 py-1 rounded-full text-xs font-bold font-mono ${
              isCharging
                ? "bg-emerald-100 text-emerald-800 border border-emerald-300"
                : isDischarging
                ? "bg-purple-100 text-purple-800 border border-purple-300"
                : "bg-slate-100 text-slate-700 border border-slate-300"
            }`}
          >
            {status.mode} {Math.abs(status.current_power_kw) > 0 ? `(${Math.abs(status.current_power_kw).toFixed(1)} kW)` : ""}
          </span>
        </div>
      </div>

      {/* Primary KPI Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        <div className="p-3 rounded-lg bg-purple-50/50 border border-purple-100">
          <span className="text-xs text-slate-500 block mb-1">State of Charge (SOC)</span>
          <div className="flex items-baseline gap-1">
            <span className="text-2xl font-bold font-mono text-purple-700">
              {status.current_soc.toFixed(1)}%
            </span>
          </div>
          <div className="w-full bg-purple-200 h-2 rounded-full mt-2 overflow-hidden">
            <div
              className="bg-purple-600 h-full rounded-full transition-all duration-500"
              style={{ width: `${Math.min(100, Math.max(0, status.current_soc))}%` }}
            />
          </div>
        </div>

        <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
          <span className="text-xs text-slate-500 block mb-1">Storage Capacity</span>
          <span className="text-2xl font-bold font-mono text-slate-900">
            {formatKwh(status.capacity_kwh)}
          </span>
          <span className="text-[11px] text-slate-400 block mt-2">
            Available: {((status.capacity_kwh * status.current_soc) / 100).toFixed(1)} kWh
          </span>
        </div>

        <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
          <span className="text-xs text-slate-500 block mb-1">Operating Envelope</span>
          <div className="flex items-baseline gap-1">
            <span className="text-lg font-bold font-mono text-slate-800">
              {status.min_soc}% - {status.max_soc}%
            </span>
          </div>
          <span className="text-[11px] text-slate-400 block mt-2">
            DOD Reserve: {status.min_soc}% Min
          </span>
        </div>

        <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
          <span className="text-xs text-slate-500 block mb-1">Power Limits</span>
          <div className="flex items-baseline gap-1">
            <span className="text-lg font-bold font-mono text-slate-800">
              ±{status.max_charge_kw.toFixed(0)} kW
            </span>
          </div>
          <span className="text-[11px] text-slate-400 block mt-2">
            C-Rate: {(status.max_charge_kw / status.capacity_kwh).toFixed(2)}C
          </span>
        </div>
      </div>

      {/* Secondary Efficiency & Health Metrics */}
      <div className="pt-3 border-t border-slate-100 flex flex-wrap items-center justify-between text-xs text-slate-500 gap-3">
        <div className="flex items-center gap-1.5">
          <Zap className="w-4 h-4 text-emerald-500" />
          <span>Round-trip Efficiency:</span>
          <strong className="text-slate-800 font-mono">
            {((status.charge_efficiency * status.discharge_efficiency) * 100).toFixed(1)}%
          </strong>
          <span className="text-slate-400">
            (Chg: {(status.charge_efficiency * 100).toFixed(0)}% / Dis: {(status.discharge_efficiency * 100).toFixed(0)}%)
          </span>
        </div>

        <div className="flex items-center gap-1.5">
          <HeartPulse className="w-4 h-4 text-purple-500" />
          <span>Battery State of Health (SOH):</span>
          <strong className="text-slate-800 font-mono">
            {status.battery_health.toFixed(1)}%
          </strong>
        </div>

        <div className="flex items-center gap-1.5">
          <Shield className="w-4 h-4 text-blue-500" />
          <span>Safety Interlock:</span>
          <strong className="text-emerald-700">ENGAGED / OK</strong>
        </div>
      </div>
    </div>
  );
}
