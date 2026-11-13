"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import { endpoints } from "@/lib/api/endpoints";
import { GridOverviewCard } from "@/components/grid/GridOverviewCard";
import { StrategyComparison } from "@/components/grid/StrategyComparison";
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";
import { formatTime, formatCurrency } from "@/lib/utils";

export default function GridOptimizationPage() {
  const statusQuery = useQuery({
    queryKey: ["gridStatus"],
    queryFn: endpoints.getGridStatus,
  });

  const analyticsQuery = useQuery({
    queryKey: ["gridAnalytics"],
    queryFn: endpoints.getGridAnalytics,
  });

  const isLoading = statusQuery.isLoading || analyticsQuery.isLoading;

  if (isLoading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-44 bg-slate-200 rounded-lg" />
        <div className="h-96 bg-slate-200 rounded-lg" />
        <div className="h-96 bg-slate-200 rounded-lg" />
      </div>
    );
  }

  const seriesData = analyticsQuery.data?.hourly_series.map((pt) => ({
    ...pt,
    timeLabel: formatTime(pt.timestamp),
  })) || [];

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 rounded-lg bg-white border border-slate-200 shadow-sm">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-bold text-slate-900">
              Grid Interconnection & Tariff Cost Optimization
            </h2>
          </div>
          <p className="text-xs text-slate-500">
            Monitoring import/export dynamics, TOU tariffs, and storage-enabled peak reduction
          </p>
        </div>
      </div>

      {/* 1. Grid Overview Card */}
      {statusQuery.data && (
        <GridOverviewCard
          status={statusQuery.data}
          analytics={analyticsQuery.data}
        />
      )}

      {/* 2. Strategy Optimization Comparison (Baseline vs Scheduled) */}
      {analyticsQuery.data && (
        <StrategyComparison comparison={analyticsQuery.data.strategy_comparison} />
      )}

      {/* 3. Grid Import vs Export Power & Cost Chart */}
      <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-base font-semibold text-slate-900">
              Hourly Grid Exchange & Net Cost Profile
            </h3>
            <p className="text-xs text-slate-500">
              24-hour import energy versus feed-in export and net financial balance
            </p>
          </div>
        </div>

        <div className="w-full h-80">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={seriesData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="timeLabel" stroke="#94a3b8" fontSize={11} tickLine={false} />
              <YAxis
                yAxisId="power"
                stroke="#94a3b8"
                fontSize={11}
                unit=" kW"
                tickLine={false}
              />
              <YAxis
                yAxisId="cost"
                orientation="right"
                stroke="#64748b"
                fontSize={11}
                unit=" $"
                tickLine={false}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#0f172a",
                  borderColor: "#334155",
                  borderRadius: "8px",
                  color: "#f8fafc",
                  fontSize: "12px",
                }}
                formatter={(val: number, name: string) => [
                  name.includes("Cost") ? `$${val.toFixed(2)}` : `${val.toFixed(1)} kW`,
                  name,
                ]}
              />
              <Legend wrapperStyle={{ fontSize: "12px", paddingTop: "8px" }} />

              <Bar
                yAxisId="power"
                dataKey="grid_import_kw"
                name="Grid Import (kW)"
                fill="#3b82f6"
                fillOpacity={0.7}
              />
              <Bar
                yAxisId="power"
                dataKey="grid_export_kw"
                name="Grid Export (kW)"
                fill="#06b6d4"
                fillOpacity={0.7}
              />
              <Line
                yAxisId="cost"
                type="monotone"
                dataKey="net_cost"
                name="Hourly Net Cost ($)"
                stroke="#f59e0b"
                strokeWidth={2.5}
                dot={{ r: 3 }}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
