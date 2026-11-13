import React from "react";
import { BatteryScheduleStep } from "@/types";
import { formatTime, formatCurrency } from "@/lib/utils";

interface BatteryScheduleTableProps {
  steps: BatteryScheduleStep[];
}

export function BatteryScheduleTable({ steps }: BatteryScheduleTableProps) {
  return (
    <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
      <div className="p-4 border-b border-slate-200 flex items-center justify-between">
        <div>
          <h3 className="text-base font-semibold text-slate-900">
            Hourly Dispatch Plan & Physical Balance Ledger
          </h3>
          <p className="text-xs text-slate-500">
            24 discrete time-steps respecting storage capacity, C-rate, DOD, and interconnection limits
          </p>
        </div>
        <span className="text-xs font-mono font-medium text-slate-500">
          Showing {steps.length} Hours
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider">
            <tr>
              <th className="px-3 py-2.5">Time</th>
              <th className="px-3 py-2.5 text-right">PV (kW)</th>
              <th className="px-3 py-2.5 text-right">Load (kW)</th>
              <th className="px-3 py-2.5 text-center">Action</th>
              <th className="px-3 py-2.5 text-right">Battery (kW)</th>
              <th className="px-3 py-2.5 text-right">SOC Range</th>
              <th className="px-3 py-2.5 text-right">Grid Imp (kW)</th>
              <th className="px-3 py-2.5 text-right">Grid Exp (kW)</th>
              <th className="px-3 py-2.5 text-right">Step Cost</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 font-mono">
            {steps.map((step) => {
              const isChg = step.action === "CHARGE";
              const isDis = step.action === "DISCHARGE";

              return (
                <tr key={step.step_index} className="hover:bg-slate-50/80 transition-colors">
                  <td className="px-3 py-2 font-sans font-medium text-slate-800">
                    {formatTime(step.timestamp)}
                  </td>
                  <td className="px-3 py-2 text-right text-emerald-600 font-medium">
                    {step.pv_forecast_kw.toFixed(1)}
                  </td>
                  <td className="px-3 py-2 text-right text-amber-600 font-medium">
                    {step.load_forecast_kw.toFixed(1)}
                  </td>
                  <td className="px-3 py-2 text-center">
                    <span
                      className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold ${
                        isChg
                          ? "bg-emerald-100 text-emerald-800 border border-emerald-300"
                          : isDis
                          ? "bg-purple-100 text-purple-800 border border-purple-300"
                          : "bg-slate-100 text-slate-600 border border-slate-200"
                      }`}
                    >
                      {step.action}
                    </span>
                  </td>
                  <td
                    className={`px-3 py-2 text-right font-semibold ${
                      isChg ? "text-emerald-600" : isDis ? "text-purple-600" : "text-slate-400"
                    }`}
                  >
                    {step.battery_power_kw > 0 ? (isChg ? `+${step.battery_power_kw.toFixed(1)}` : `-${step.battery_power_kw.toFixed(1)}`) : "0.0"}
                  </td>
                  <td className="px-3 py-2 text-right text-slate-700">
                    {step.soc_before.toFixed(1)}% →{" "}
                    <strong
                      className={
                        step.soc_after < 25
                          ? "text-red-600"
                          : step.soc_after > 90
                          ? "text-purple-600"
                          : "text-slate-900"
                      }
                    >
                      {step.soc_after.toFixed(1)}%
                    </strong>
                  </td>
                  <td className="px-3 py-2 text-right text-blue-600">
                    {step.grid_import_kw > 0 ? step.grid_import_kw.toFixed(1) : "-"}
                  </td>
                  <td className="px-3 py-2 text-right text-teal-600">
                    {step.grid_export_kw > 0 ? step.grid_export_kw.toFixed(1) : "-"}
                  </td>
                  <td
                    className={`px-3 py-2 text-right font-medium ${
                      step.step_cost > 0 ? "text-slate-900" : step.step_cost < 0 ? "text-emerald-600" : "text-slate-400"
                    }`}
                  >
                    {formatCurrency(step.step_cost)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
