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
  ReferenceLine
} from "recharts";
import { PVForecastResponse } from "@/types";
import { formatTime } from "@/lib/utils";

interface PvForecastChartProps {
  data: PVForecastResponse;
}

export function PvForecastChart({ data }: PvForecastChartProps) {
  // Combine historical and future forecast points
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
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 mb-4">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-base font-semibold text-slate-900">
              Solar PV Generation Forecast (24h Horizon)
            </h3>
          </div>
          <p className="text-xs text-slate-500">
            Model: {data.model_name} ({data.model_id}) with 95% Confidence Interval
          </p>
        </div>

        <div className="text-xs text-slate-500 bg-slate-50 px-3 py-1.5 rounded border border-slate-200">
          Peak Solar Forecast:{" "}
          <span className="font-mono font-bold text-emerald-600">
            {Math.max(...data.forecast_points.map((p) => p.value_kw), 0).toFixed(1)} kW
          </span>
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

            {/* Separator between historical and forecast */}
            <ReferenceLine
              x={formatTime(data.forecast_timestamp)}
              stroke="#64748b"
              strokeDasharray="4 4"
              label={{ value: "Now (Forecast T0)", fill: "#64748b", fontSize: 10, position: "top" }}
            />

            {/* Confidence Interval Band */}
            <Area
              type="monotone"
              dataKey="upper_bound_kw"
              stroke="transparent"
              fill="#10b981"
              fillOpacity={0.12}
              name="Confidence Interval (95%)"
            />
            <Area
              type="monotone"
              dataKey="lower_bound_kw"
              stroke="transparent"
              fill="#ffffff"
              fillOpacity={1}
            />

            {/* Historical Generation Line */}
            <Line
              type="monotone"
              dataKey="historical_val"
              name="Historical Actual (kW)"
              stroke="#64748b"
              strokeWidth={2}
              dot={false}
            />

            {/* Future Forecasted Generation Line */}
            <Line
              type="monotone"
              dataKey="forecast_val"
              name="Operational Forecast (kW)"
              stroke="#10b981"
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
