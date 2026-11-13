"use client";

import React from "react";
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
  ReferenceLine,
  Cell,
} from "recharts";
import { CombinedForecastResponse } from "@/types";
import { formatTime, formatKwh } from "@/lib/utils";

interface CombinedForecastChartProps {
  data: CombinedForecastResponse;
}

export function CombinedForecastChart({ data }: CombinedForecastChartProps) {
  const chartData = data.points.map((pt) => ({
    ...pt,
    timeLabel: formatTime(pt.timestamp),
    surplusPower: pt.net_power_kw > 0 ? pt.net_power_kw : 0,
    deficitPower: pt.net_power_kw < 0 ? pt.net_power_kw : 0,
  }));

  return (
    <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-4">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-base font-semibold text-slate-900">
              PV vs Load Net Energy Balance (Surplus / Deficit)
            </h3>
          </div>
          <p className="text-xs text-slate-500">
            Net Power = PV Forecast - Load Forecast (Green = Surplus, Red = Deficit)
          </p>
        </div>

        {/* Balance Metrics */}
        <div className="flex items-center gap-3 text-xs">
          <div className="bg-emerald-50 border border-emerald-200 px-3 py-1.5 rounded">
            <span className="text-emerald-700 font-medium">Surplus Hours: </span>
            <span className="font-mono font-bold text-emerald-800">
              {data.surplus_hours} hrs
            </span>
          </div>
          <div className="bg-red-50 border border-red-200 px-3 py-1.5 rounded">
            <span className="text-red-700 font-medium">Deficit Hours: </span>
            <span className="font-mono font-bold text-red-800">
              {data.deficit_hours} hrs
            </span>
          </div>
        </div>
      </div>

      <div className="w-full h-80">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
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
              formatter={(val: number) => [`${val.toFixed(1)} kW`]}
            />
            <Legend wrapperStyle={{ fontSize: "12px", paddingTop: "8px" }} />

            <ReferenceLine y={0} stroke="#94a3b8" strokeWidth={1.5} />

            {/* PV Forecast Line */}
            <Line
              type="monotone"
              dataKey="pv_kw"
              name="PV Forecast (kW)"
              stroke="#10b981"
              strokeWidth={2.5}
              dot={false}
            />

            {/* Load Forecast Line */}
            <Line
              type="monotone"
              dataKey="load_kw"
              name="Load Forecast (kW)"
              stroke="#f59e0b"
              strokeWidth={2.5}
              dot={false}
            />

            {/* Net Power Bar */}
            <Bar dataKey="net_power_kw" name="Net Power Surplus/(Deficit) (kW)">
              {chartData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={entry.net_power_kw >= 0 ? "#10b981" : "#ef4444"}
                  fillOpacity={0.65}
                />
              ))}
            </Bar>
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Summary Box */}
      <div className="mt-4 p-4 rounded-lg bg-slate-50 border border-slate-200 grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
        <div>
          <span className="text-slate-500 block mb-0.5">Total Forecasted PV Energy</span>
          <span className="text-base font-bold font-mono text-emerald-600">
            {formatKwh(data.total_pv_kwh)}
          </span>
        </div>
        <div>
          <span className="text-slate-500 block mb-0.5">Total Forecasted Load Energy</span>
          <span className="text-base font-bold font-mono text-amber-600">
            {formatKwh(data.total_load_kwh)}
          </span>
        </div>
        <div>
          <span className="text-slate-500 block mb-0.5">Net Energy Balance</span>
          <span
            className={`text-base font-bold font-mono ${
              data.net_energy_kwh >= 0 ? "text-emerald-600" : "text-blue-600"
            }`}
          >
            {data.net_energy_kwh >= 0 ? "+" : ""}
            {formatKwh(data.net_energy_kwh)}
          </span>
        </div>
      </div>
    </div>
  );
}
