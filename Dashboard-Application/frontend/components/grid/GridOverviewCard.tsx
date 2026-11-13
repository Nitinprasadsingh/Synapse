import React from "react";
import { GridStatus, GridAnalytics } from "@/types";
import { Zap, DollarSign, TrendingDown, ShieldAlert, ArrowUpRight, ArrowDownRight } from "lucide-react";
import { formatKw, formatKwh, formatCurrency, formatPct } from "@/lib/utils";

interface GridOverviewCardProps {
  status: GridStatus;
  analytics?: GridAnalytics;
}

export function GridOverviewCard({ status, analytics }: GridOverviewCardProps) {
  const isImporting = status.current_import_kw > 0.1;
  const isExporting = status.current_export_kw > 0.1;

  return (
    <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pb-4 mb-4 border-b border-slate-100">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center">
            <Zap className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-900">
              Utility Interconnection & Tariff Telemetry
            </h3>
            <span className="text-xs text-slate-500">
              Point of Common Coupling (PCC) Distribution Feeder
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span
            className={`px-3 py-1 rounded-full text-xs font-bold font-mono ${
              status.status === "NORMAL"
                ? "bg-blue-100 text-blue-800 border border-blue-300"
                : status.status === "WARNING"
                ? "bg-amber-100 text-amber-800 border border-amber-300"
                : "bg-red-100 text-red-800 border border-red-300"
            }`}
          >
            Interconnection: {status.status}
          </span>
        </div>
      </div>

      {/* Grid KPI Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        <div className="p-3 rounded-lg bg-blue-50/50 border border-blue-100">
          <span className="text-xs text-slate-500 block mb-1">Instantaneous Flow</span>
          <div className="flex items-baseline gap-1">
            <span className="text-2xl font-bold font-mono text-blue-700">
              {isExporting ? `-${status.current_export_kw.toFixed(1)}` : `+${status.current_import_kw.toFixed(1)}`}
            </span>
            <span className="text-xs text-slate-500">kW</span>
          </div>
          <span className="text-[11px] text-slate-500 block mt-2">
            {isExporting ? "Feeding excess solar to grid" : isImporting ? "Supplementing local load" : "Zero exchange (Islanded)"}
          </span>
        </div>

        <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
          <span className="text-xs text-slate-500 block mb-1">PCC Limits</span>
          <div className="flex items-baseline gap-1">
            <span className="text-lg font-bold font-mono text-slate-800">
              {status.import_limit_kw} kW / {status.export_limit_kw} kW
            </span>
          </div>
          <span className="text-[11px] text-slate-400 block mt-2">
            Import Cap / Export Cap
          </span>
        </div>

        <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
          <span className="text-xs text-slate-500 block mb-1">Active Electricity Tariffs</span>
          <div className="flex items-baseline gap-1">
            <span className="text-lg font-bold font-mono text-slate-800">
              ${status.import_tariff.toFixed(2)} / ${status.export_tariff.toFixed(2)}
            </span>
          </div>
          <span className="text-[11px] text-slate-400 block mt-2">
            Import ($/kWh) / Feed-in ($/kWh)
          </span>
        </div>

        <div className="p-3 rounded-lg bg-emerald-50/50 border border-emerald-100">
          <span className="text-xs text-slate-500 block mb-1">Renewable Self-Sufficiency</span>
          <div className="flex items-baseline gap-1">
            <span className="text-2xl font-bold font-mono text-emerald-700">
              {formatPct(status.renewable_utilization_pct)}
            </span>
          </div>
          <span className="text-[11px] text-emerald-600 block mt-2">
            Peak Demand: {formatKw(status.peak_grid_demand_kw)}
          </span>
        </div>
      </div>

      {/* 24-Hour Cumulative Analytics Banner */}
      {analytics && (
        <div className="pt-3 border-t border-slate-100 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
          <div>
            <span className="text-slate-400 block">24h Total Import:</span>
            <strong className="text-slate-800 font-mono text-sm">{formatKwh(analytics.total_import_kwh)}</strong>
          </div>
          <div>
            <span className="text-slate-400 block">24h Total Export:</span>
            <strong className="text-slate-800 font-mono text-sm">{formatKwh(analytics.total_export_kwh)}</strong>
          </div>
          <div>
            <span className="text-slate-400 block">Gross Import Cost:</span>
            <strong className="text-slate-800 font-mono text-sm">{formatCurrency(analytics.total_import_cost)}</strong>
          </div>
          <div>
            <span className="text-slate-400 block">Net Energy Cost:</span>
            <strong className="text-blue-700 font-mono text-sm">{formatCurrency(analytics.net_grid_cost)}</strong>
          </div>
        </div>
      )}
    </div>
  );
}
