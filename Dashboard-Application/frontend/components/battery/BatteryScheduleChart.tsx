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
} from "recharts";
import { BatterySchedule } from "@/types";
import { formatTime } from "@/lib/utils";

interface BatteryScheduleChartProps {
  schedule: BatterySchedule;
}

export function BatteryScheduleChart({ schedule }: BatteryScheduleChartProps) {
  const chartData = schedule.steps.map((step) => ({
    ...step,
    timeLabel: formatTime(step.timestamp),
    chargePower: step.action === "CHARGE" ? step.battery_power_kw : 0,
    dischargePower: step.action === "DISCHARGE" ? step.battery_power_kw : 0,
  }));

  return (
    <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-4">
        <div>
          <h3 className="text-base font-semibold text-slate-900">
            24-Hour Battery Dispatch & SOC Trajectory
          </h3>
          <p className="text-xs text-slate-500">
            Coordinated charging/discharging schedule with state-of-charge tracking
          </p>
        </div>

        <div className="text-xs text-slate-500">
          Estimated Schedule Cost:{" "}
          <span className="font-mono font-bold text-slate-900">
            ${schedule.total_cost.toFixed(2)}
          </span>
        </div>
      </div>

      <div className="w-full h-80">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis dataKey="timeLabel" stroke="#94a3b8" fontSize={11} tickLine={false} />
            <YAxis
              yAxisId="left"
              stroke="#94a3b8"
              fontSize={11}
              unit=" kW"
              tickLine={false}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              domain={[0, 100]}
              stroke="#8b5cf6"
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
              formatter={(val: number, name: string) => [
                name.includes("SOC") ? `${val.toFixed(1)}%` : `${val.toFixed(1)} kW`,
                name,
              ]}
            />
            <Legend wrapperStyle={{ fontSize: "12px", paddingTop: "8px" }} />

            {/* Solar PV Line */}
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="pv_forecast_kw"
              name="PV Generation (kW)"
              stroke="#10b981"
              strokeWidth={2}
              dot={false}
            />

            {/* Load Line */}
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="load_forecast_kw"
              name="Facility Load (kW)"
              stroke="#f59e0b"
              strokeWidth={2}
              dot={false}
            />

            {/* Charging Power Bar */}
            <Bar
              yAxisId="left"
              dataKey="chargePower"
              name="Battery Charge (kW)"
              fill="#10b981"
              fillOpacity={0.8}
            />

            {/* Discharging Power Bar */}
            <Bar
              yAxisId="left"
              dataKey="dischargePower"
              name="Battery Discharge (kW)"
              fill="#8b5cf6"
              fillOpacity={0.8}
            />

            {/* SOC Trajectory Line */}
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="soc_after"
              name="Battery SOC (%)"
              stroke="#7c3aed"
              strokeWidth={3}
              dot={{ r: 3, fill: "#7c3aed" }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
