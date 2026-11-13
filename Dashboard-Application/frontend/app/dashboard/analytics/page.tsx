"use client";

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { endpoints } from "@/lib/api/endpoints";
import { DailyBreakdownChart } from "@/components/analytics/DailyBreakdownChart";
import { Download, Calendar, BarChart3, Battery, DollarSign, Activity } from "lucide-react";
import { formatCurrency, formatKwh, formatPct } from "@/lib/utils";

export default function AnalyticsPage() {
  const [period, setPeriod] = useState<"7d" | "30d">("7d");

  const summaryQuery = useQuery({
    queryKey: ["analyticsSummary", period],
    queryFn: () => endpoints.getAnalyticsSummary(period),
  });

  const reportsQuery = useQuery({
    queryKey: ["energyReports"],
    queryFn: endpoints.getReports,
  });

  const isLoading = summaryQuery.isLoading;

  if (isLoading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-32 bg-slate-200 rounded-lg" />
        <div className="h-96 bg-slate-200 rounded-lg" />
      </div>
    );
  }

  const summary = summaryQuery.data;

  return (
    <div className="space-y-6">
      {/* Top Banner with Period Switcher and Export Buttons */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 rounded-lg bg-white border border-slate-200 shadow-sm">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-bold text-slate-900">
              Energy Accounting & Historical Performance Analytics
            </h2>
          </div>
          <p className="text-xs text-slate-500">
            Audit-grade energy balance metrics, storage cycling degradation, and export utilities
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Period selector */}
          <div className="flex items-center rounded-lg border border-slate-200 bg-slate-50 p-1 text-xs">
            <button
              onClick={() => setPeriod("7d")}
              className={`px-3 py-1 rounded-md font-medium transition-colors ${
                period === "7d" ? "bg-white text-slate-900 shadow-sm" : "text-slate-600"
              }`}
            >
              Last 7 Days
            </button>
            <button
              onClick={() => setPeriod("30d")}
              className={`px-3 py-1 rounded-md font-medium transition-colors ${
                period === "30d" ? "bg-white text-slate-900 shadow-sm" : "text-slate-600"
              }`}
            >
              Last 30 Days
            </button>
          </div>

          {/* Export Dropdown / Buttons */}
          <div className="flex items-center gap-2">
            <a
              href={endpoints.exportAnalyticsUrl("csv", period)}
              download
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 text-xs font-semibold shadow-sm transition-colors"
            >
              <Download className="w-3.5 h-3.5 text-slate-500" />
              <span>Export CSV</span>
            </a>
            <a
              href={endpoints.exportAnalyticsUrl("json", period)}
              download
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 text-xs font-semibold shadow-sm transition-colors"
            >
              <Download className="w-3.5 h-3.5 text-slate-500" />
              <span>Export JSON</span>
            </a>
          </div>
        </div>
      </div>

      {summary && (
        <>
          {/* Summary Metric Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 rounded-lg bg-white border border-slate-200 shadow-sm">
              <span className="text-xs text-slate-500 block mb-1">Total Solar Generation</span>
              <span className="text-2xl font-bold font-mono text-emerald-600">
                {formatKwh(summary.total_pv_kwh)}
              </span>
              <span className="text-[11px] text-slate-400 block mt-2">
                Period Total ({period})
              </span>
            </div>

            <div className="p-4 rounded-lg bg-white border border-slate-200 shadow-sm">
              <span className="text-xs text-slate-500 block mb-1">Total Facility Load</span>
              <span className="text-2xl font-bold font-mono text-amber-600">
                {formatKwh(summary.total_load_kwh)}
              </span>
              <span className="text-[11px] text-slate-400 block mt-2">
                Peak Demand: {summary.peak_demand_kw.toFixed(1)} kW
              </span>
            </div>

            <div className="p-4 rounded-lg bg-white border border-slate-200 shadow-sm">
              <span className="text-xs text-slate-500 block mb-1">Cumulative Net Cost</span>
              <span className="text-2xl font-bold font-mono text-slate-900">
                {formatCurrency(summary.total_energy_cost)}
              </span>
              <span className="text-[11px] text-slate-400 block mt-2">
                Grid Import: {formatKwh(summary.total_grid_import_kwh)}
              </span>
            </div>

            <div className="p-4 rounded-lg bg-white border border-slate-200 shadow-sm">
              <span className="text-xs text-slate-500 block mb-1">Avg Renewable Share</span>
              <span className="text-2xl font-bold font-mono text-emerald-700">
                {formatPct(summary.renewable_utilization_pct)}
              </span>
              <span className="text-[11px] text-slate-400 block mt-2">
                Clean Self-Sufficiency
              </span>
            </div>
          </div>

          {/* Daily Breakdown Bar Chart */}
          <DailyBreakdownChart data={summary.daily_breakdown} />

          {/* Battery Cycling Degradation Ledger */}
          <div className="p-5 rounded-lg bg-white border border-slate-200 shadow-sm">
            <div className="flex items-center gap-2 mb-3">
              <Battery className="w-5 h-5 text-purple-600" />
              <h3 className="text-base font-semibold text-slate-900">
                Battery Cell Cycling & Lifetime Degradation Telemetry
              </h3>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
              <div className="p-3 bg-purple-50/50 rounded border border-purple-100">
                <span className="text-slate-500 block mb-1">Full Equivalent Cycles</span>
                <span className="text-xl font-bold font-mono text-purple-800">
                  {summary.battery_stats.equivalent_full_cycles.toFixed(2)} cycles
                </span>
              </div>
              <div className="p-3 bg-slate-50 rounded border border-slate-200">
                <span className="text-slate-500 block mb-1">Total Throughput</span>
                <span className="text-xl font-bold font-mono text-slate-800">
                  {formatKwh(summary.battery_stats.total_energy_throughput_kwh)}
                </span>
              </div>
              <div className="p-3 bg-slate-50 rounded border border-slate-200">
                <span className="text-slate-500 block mb-1">Average Depth of Discharge</span>
                <span className="text-xl font-bold font-mono text-slate-800">
                  {formatPct(summary.battery_stats.average_depth_of_discharge_pct)}
                </span>
              </div>
              <div className="p-3 bg-emerald-50/50 rounded border border-emerald-100">
                <span className="text-slate-500 block mb-1">Estimated SOH (Health)</span>
                <span className="text-xl font-bold font-mono text-emerald-700">
                  {formatPct(summary.battery_stats.estimated_soh_pct)}
                </span>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
