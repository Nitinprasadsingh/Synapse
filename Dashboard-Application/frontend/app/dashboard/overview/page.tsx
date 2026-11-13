"use client";

import React, { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { endpoints } from "@/lib/api/endpoints";
import { KpiCard } from "@/components/dashboard/KpiCard";
import { EnergyFlowDiagram } from "@/components/dashboard/EnergyFlowDiagram";
import { PvVsLoadChart } from "@/components/dashboard/PvVsLoadChart";
import { BatterySocChart } from "@/components/dashboard/BatterySocChart";
import { OperationalStatusCard } from "@/components/dashboard/OperationalStatusCard";
import { Sun, Home, Battery, Zap, DollarSign, Activity, RefreshCw } from "lucide-react";

export default function OverviewPage() {
  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ["dashboardOverview"],
    queryFn: endpoints.getDashboardOverview,
    refetchInterval: 10000, // 10s polling for live simulation
  });

  if (isLoading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-28 bg-slate-200 rounded-lg" />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="h-28 bg-slate-200 rounded-lg" />
          ))}
        </div>
        <div className="h-96 bg-slate-200 rounded-lg" />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="p-8 text-center bg-white rounded-lg border border-red-200 shadow-sm">
        <h3 className="text-base font-bold text-red-700 mb-2">Failed to retrieve microgrid telemetry</h3>
        <p className="text-xs text-slate-500 mb-4">{error ? (error as Error).message : "Unknown error"}</p>
        <button
          onClick={() => refetch()}
          className="px-4 py-2 rounded-md bg-slate-900 text-white text-xs font-semibold"
        >
          Retry Connection
        </button>
      </div>
    );
  }

  const { kpis, energy_flow, series, operational_status, operational_status_message } = data;

  return (
    <div className="space-y-6">
      {/* Top Banner: Status & Live Controls */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex-1 w-full">
          <OperationalStatusCard
            status={operational_status}
            message={operational_status_message}
          />
        </div>
        <button
          onClick={() => refetch()}
          className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-white border border-slate-200 text-slate-700 text-xs font-medium hover:bg-slate-50 shadow-sm transition-colors flex-shrink-0"
          title="Force telemetry refresh"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isFetching ? "animate-spin text-blue-600" : ""}`} />
          <span>Sync Telemetry</span>
        </button>
      </div>

      {/* 9 KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
        <KpiCard
          title={kpis.current_pv_kw.label}
          value={kpis.current_pv_kw.value}
          unit={kpis.current_pv_kw.unit}
          status={kpis.current_pv_kw.status}
          changePct={kpis.current_pv_kw.change_pct}
          changePeriod={kpis.current_pv_kw.change_period}
          theme="solar"
          icon={<Sun className="w-4 h-4 text-emerald-500" />}
        />

        <KpiCard
          title={kpis.current_load_kw.label}
          value={kpis.current_load_kw.value}
          unit={kpis.current_load_kw.unit}
          status={kpis.current_load_kw.status}
          changePct={kpis.current_load_kw.change_pct}
          changePeriod={kpis.current_load_kw.change_period}
          theme="cost"
          icon={<Home className="w-4 h-4 text-amber-500" />}
        />

        <KpiCard
          title={kpis.battery_soc_pct.label}
          value={kpis.battery_soc_pct.value}
          unit={kpis.battery_soc_pct.unit}
          status={kpis.battery_soc_pct.status}
          changePct={kpis.battery_soc_pct.change_pct}
          changePeriod={kpis.battery_soc_pct.change_period}
          theme="battery"
          icon={<Battery className="w-4 h-4 text-purple-500" />}
        />

        <KpiCard
          title={kpis.grid_import_kw.label}
          value={kpis.grid_import_kw.value}
          unit={kpis.grid_import_kw.unit}
          status={kpis.grid_import_kw.status}
          theme="grid"
          icon={<Zap className="w-4 h-4 text-blue-500" />}
        />

        <KpiCard
          title={kpis.grid_export_kw.label}
          value={kpis.grid_export_kw.value}
          unit={kpis.grid_export_kw.unit}
          status={kpis.grid_export_kw.status}
          theme="solar"
          icon={<Zap className="w-4 h-4 text-teal-500" />}
        />

        <KpiCard
          title={kpis.current_energy_cost.label}
          value={kpis.current_energy_cost.value}
          unit={kpis.current_energy_cost.unit}
          status={kpis.current_energy_cost.status}
          theme="cost"
          icon={<DollarSign className="w-4 h-4 text-slate-500" />}
        />

        <KpiCard
          title={kpis.renewable_utilization_pct.label}
          value={kpis.renewable_utilization_pct.value}
          unit={kpis.renewable_utilization_pct.unit}
          status={kpis.renewable_utilization_pct.status}
          theme="solar"
          icon={<Activity className="w-4 h-4 text-emerald-500" />}
        />

        <KpiCard
          title={kpis.forecasted_pv_next_hour_kw.label}
          value={kpis.forecasted_pv_next_hour_kw.value}
          unit={kpis.forecasted_pv_next_hour_kw.unit}
          theme="default"
          icon={<Sun className="w-4 h-4 text-slate-400" />}
        />

        <KpiCard
          title={kpis.forecasted_load_next_hour_kw.label}
          value={kpis.forecasted_load_next_hour_kw.value}
          unit={kpis.forecasted_load_next_hour_kw.unit}
          theme="default"
          icon={<Home className="w-4 h-4 text-slate-400" />}
        />
      </div>

      {/* Dynamic Animated Energy Flow Diagram */}
      <EnergyFlowDiagram flow={energy_flow} />

      {/* Time-Series Charts Grid: Generation vs Load & Battery SOC */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <PvVsLoadChart data={series} />
        </div>
        <div>
          <BatterySocChart data={series} />
        </div>
      </div>
    </div>
  );
}
