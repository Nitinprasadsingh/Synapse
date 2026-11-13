"use client";

import React from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";
import { DailyEnergyItem } from "@/types";

interface DailyBreakdownChartProps {
  data: DailyEnergyItem[];
}

export function DailyBreakdownChart({ data }: DailyBreakdownChartProps) {
  return (
    <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-base font-semibold text-slate-900">
            Historical Daily Energy Balance & Dispatch Trends
          </h3>
          <p className="text-xs text-slate-500">
            Comparative daily totals for generation, facility consumption, battery throughput, and grid trade
          </p>
        </div>
      </div>

      <div className="w-full h-80">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis dataKey="date" stroke="#94a3b8" fontSize={11} tickLine={false} />
            <YAxis stroke="#94a3b8" fontSize={11} unit=" kWh" tickLine={false} />
            <Tooltip
              contentStyle={{
                backgroundColor: "#0f172a",
                borderColor: "#334155",
                borderRadius: "8px",
                color: "#f8fafc",
                fontSize: "12px",
              }}
              formatter={(val: number) => [`${val.toFixed(1)} kWh`]}
            />
            <Legend wrapperStyle={{ fontSize: "12px", paddingTop: "8px" }} />

            <Bar
              dataKey="pv_generation_kwh"
              name="Solar PV (kWh)"
              fill="#10b981"
              radius={[4, 4, 0, 0]}
            />
            <Bar
              dataKey="load_consumption_kwh"
              name="Facility Load (kWh)"
              fill="#f59e0b"
              radius={[4, 4, 0, 0]}
            />
            <Bar
              dataKey="grid_import_kwh"
              name="Grid Import (kWh)"
              fill="#3b82f6"
              radius={[4, 4, 0, 0]}
            />
            <Bar
              dataKey="battery_charge_kwh"
              name="Battery Charge (kWh)"
              fill="#8b5cf6"
              radius={[4, 4, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
