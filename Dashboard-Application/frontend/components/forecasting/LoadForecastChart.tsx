"use client";

import React from "react";
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
} from "recharts";
import { LoadForecastResponse } from "@/types";
import { formatTime, formatKw, formatKwh } from "@/lib/utils";

interface LoadForecastChartProps {
  data: LoadForecastResponse;
}

export function LoadForecastChart({ data }: LoadForecastChartProps) {
  const combined = [
    ...data.historical_points.map((pt) => ({
      ...pt,
      historical_val: pt.value_kw,
      forecast_val: null,
      timeLabel: formatTime(pt.timestamp),
    })),
    ...data.forecast_points.map((pt) => ({
      ...pt,
      historical_val: null,
      forecast_val: pt.value_kw,
      timeLabel: formatTime(pt.timestamp),
    })),
  ];

  return (
    <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-4">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-base font-semibold text-slate-900">
              Electricity Demand / Load Forecast (24h)
            </h3>
          </div>
          <p className="text-xs text-slate-500">
            Model: {data.model_name}
          </p>
        </div>

        {/* Load Summary Badges */}
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <div className="bg-slate-50 border border-slate-200 px-2.5 py-1 rounded">
            <span className="text-slate-500 mr-1">Peak:</span>
            <span className="font-mono font-bold text-amber-600">
              {formatKw(data.summary.expected_peak_kw)}
            </span>
          </div>
          <div className="bg-slate-50 border border-slate-200 px-2.5 py-1 rounded">
            <span className="text-slate-500 mr-1">Min:</span>
            <span className="font-mono font-bold text-blue-600">
              {formatKw(data.summary.expected_min_kw)}
            </span>
          </div>
          <div className="bg-slate-50 border border-slate-200 px-2.5 py-1 rounded">
            <span className="text-slate-500 mr-1">Avg:</span>
            <span className="font-mono font-bold text-slate-800">
              {formatKw(data.summary.average_demand_kw)}
            </span>
          </div>
          <div className="bg-slate-50 border border-slate-200 px-2.5 py-1 rounded">
            <span className="text-slate-500 mr-1">Total:</span>
            <span className="font-mono font-bold text-purple-600">
              {formatKwh(data.summary.total_energy_kwh)}
            </span>
          </div>
        </div>
      </div>

      <div className="w-full h-80">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={combined} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis dataKey="timeLabel" stroke="#94a3b8" fontSize={11} tickLine={false} />
            <YAxis stroke="#94a3b8" fontSize={11} unit=" kW" tickLine={false} />
            <Tooltip
              contentStyle={{
                backgroundColor: "#0f172a",
                borderColor: "#334155",
                borderRadius: "8px",
                color: "#f8fafc",
                fontSize: "12px",
              }}
              formatter={(val: any) => [val !== null ? `${Number(val).toFixed(1)} kW` : "-"]}
            />
            <Legend wrapperStyle={{ fontSize: "12px", paddingTop: "8px" }} />

            <ReferenceLine
              x={formatTime(data.forecast_timestamp)}
              stroke="#64748b"
              strokeDasharray="4 4"
              label={{ value: "Now (T0)", fill: "#64748b", fontSize: 10, position: "top" }}
            />

            <Area
              type="monotone"
              dataKey="upper_bound_kw"
              stroke="transparent"
              fill="#f59e0b"
              fillOpacity={0.12}
              name="Demand Uncertainty Band"
            />
            <Area
              type="monotone"
              dataKey="lower_bound_kw"
              stroke="transparent"
              fill="#ffffff"
              fillOpacity={1}
            />

            <Line
              type="monotone"
              dataKey="historical_val"
              name="Historical Metered Load (kW)"
              stroke="#64748b"
              strokeWidth={2}
              dot={false}
            />

            <Line
              type="monotone"
              dataKey="forecast_val"
              name="Forecasted Demand (kW)"
              stroke="#f59e0b"
              strokeWidth={3}
              dot={false}
              activeDot={{ r: 5 }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
