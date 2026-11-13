"use client";

import React, { useState } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";
import { TimeSeriesPoint } from "@/types";
import { formatTime } from "@/lib/utils";

interface PvVsLoadChartProps {
  data: TimeSeriesPoint[];
}

export function PvVsLoadChart({ data }: PvVsLoadChartProps) {
  const [range, setRange] = useState<"24h" | "7d" | "custom">("24h");

  const formattedData = data.map((pt) => ({
    ...pt,
    timeLabel: formatTime(pt.timestamp),
  }));

  return (
    <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-6">
        <div>
          <h3 className="text-base font-semibold text-slate-900">
            Microgrid Generation vs Demand Dispatch
          </h3>
          <p className="text-xs text-slate-500">
            Synchronized time-series of PV generation, facility load, and grid import/export
          </p>
        </div>

        {/* Range Selector */}
        <div className="flex items-center rounded-lg border border-slate-200 bg-slate-50 p-1 text-xs">
          <button
            onClick={() => setRange("24h")}
            className={`px-3 py-1 rounded-md font-medium transition-colors ${
              range === "24h"
                ? "bg-white text-slate-900 shadow-sm"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            Last 24 Hours
          </button>
          <button
            onClick={() => setRange("7d")}
            className={`px-3 py-1 rounded-md font-medium transition-colors ${
              range === "7d"
                ? "bg-white text-slate-900 shadow-sm"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            Last 7 Days
          </button>
          <button
            onClick={() => setRange("custom")}
            className={`px-3 py-1 rounded-md font-medium transition-colors ${
              range === "custom"
                ? "bg-white text-slate-900 shadow-sm"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            Custom Range
          </button>
        </div>
      </div>

      <div className="w-full h-80">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={formattedData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis
              dataKey="timeLabel"
              stroke="#94a3b8"
              fontSize={11}
              tickLine={false}
            />
            <YAxis
              stroke="#94a3b8"
              fontSize={11}
              unit=" kW"
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
              formatter={(val: number) => [`${val.toFixed(1)} kW`]}
            />
            <Legend
              wrapperStyle={{ fontSize: "12px", paddingTop: "12px" }}
              iconType="circle"
            />
            <Line
              type="monotone"
              dataKey="pv_generation_kw"
              name="Solar PV (kW)"
              stroke="#10b981"
              strokeWidth={2.5}
              dot={false}
              activeDot={{ r: 5 }}
            />
            <Line
              type="monotone"
              dataKey="load_demand_kw"
              name="Load Demand (kW)"
              stroke="#f59e0b"
              strokeWidth={2.5}
              dot={false}
              activeDot={{ r: 5 }}
            />
            <Line
              type="monotone"
              dataKey="grid_import_kw"
              name="Grid Import (kW)"
              stroke="#3b82f6"
              strokeWidth={2}
              strokeDasharray="4 4"
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="grid_export_kw"
              name="Grid Export (kW)"
              stroke="#06b6d4"
              strokeWidth={2}
              strokeDasharray="4 4"
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
