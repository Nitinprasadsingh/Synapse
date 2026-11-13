"use client";

import React from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
} from "recharts";
import { TimeSeriesPoint } from "@/types";
import { formatTime } from "@/lib/utils";

interface BatterySocChartProps {
  data: TimeSeriesPoint[];
  minSoc?: number;
  maxSoc?: number;
}

export function BatterySocChart({
  data,
  minSoc = 20.0,
  maxSoc = 95.0,
}: BatterySocChartProps) {
  const formattedData = data.map((pt) => ({
    ...pt,
    timeLabel: formatTime(pt.timestamp),
  }));

  const latestSoc = data.length > 0 ? data[0].battery_soc_pct : 50.0;

  return (
    <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm flex flex-col justify-between">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-base font-semibold text-slate-900">
            Battery State of Charge (SOC)
          </h3>
          <p className="text-xs text-slate-500">
            24-hour SOC progression relative to operational depth-of-discharge constraints
          </p>
        </div>
        <div className="text-right">
          <span className="text-xl font-bold font-mono text-purple-600">
            {latestSoc.toFixed(1)}%
          </span>
          <span className="text-[10px] text-slate-400 block">Current Level</span>
        </div>
      </div>

      <div className="w-full h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={formattedData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis
              dataKey="timeLabel"
              stroke="#94a3b8"
              fontSize={11}
              tickLine={false}
            />
            <YAxis
              domain={[0, 100]}
              stroke="#94a3b8"
              fontSize={11}
              unit="%"
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
              formatter={(val: number) => [`${val.toFixed(1)}%`, "Battery SOC"]}
            />
            {/* Minimum SOC limit line */}
            <ReferenceLine
              y={minSoc}
              stroke="#ef4444"
              strokeDasharray="3 3"
              label={{ value: `Min SOC (${minSoc}%)`, fill: "#ef4444", fontSize: 10, position: "insideBottomLeft" }}
            />
            {/* Maximum SOC limit line */}
            <ReferenceLine
              y={maxSoc}
              stroke="#10b981"
              strokeDasharray="3 3"
              label={{ value: `Max SOC (${maxSoc}%)`, fill: "#10b981", fontSize: 10, position: "insideTopLeft" }}
            />
            <Line
              type="monotone"
              dataKey="battery_soc_pct"
              name="SOC (%)"
              stroke="#8b5cf6"
              strokeWidth={3}
              dot={{ r: 2, fill: "#8b5cf6" }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="flex items-center justify-between text-xs text-slate-500 pt-3 border-t border-slate-100 mt-2">
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-0.5 bg-red-500" />
          <span>Min SOC: {minSoc}%</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-0.5 bg-emerald-500" />
          <span>Max SOC: {maxSoc}%</span>
        </div>
        <div className="flex items-center gap-1.5 font-medium text-purple-700">
          <span className="w-2.5 h-2.5 rounded-full bg-purple-600" />
          <span>Capacity: 100 kWh</span>
        </div>
      </div>
    </div>
  );
}
