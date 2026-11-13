import React from "react";
import { StrategyComparison as StrategyComparisonType } from "@/types";
import { ArrowDownRight, Award, CheckCircle2, TrendingUp, Sparkles } from "lucide-react";
import { formatCurrency, formatKwh, formatPct } from "@/lib/utils";

interface StrategyComparisonProps {
  comparison: StrategyComparisonType;
}

export function StrategyComparison({ comparison }: StrategyComparisonProps) {
  const { baseline_strategy, scheduled_strategy, cost_savings_amount, cost_savings_pct, import_reduction_kwh } = comparison;

  return (
    <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-6">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-base font-semibold text-slate-900">
              Microgrid Dispatch Strategy Optimization Comparison
            </h3>
          </div>
          <p className="text-xs text-slate-500">
            Quantifying cost savings and peak shaving enabled by intelligent battery storage dispatch
          </p>
        </div>

        {/* Savings Highlight Pill */}
        <div className="flex items-center gap-2 bg-emerald-50 border border-emerald-200 px-3.5 py-1.5 rounded-lg">
          <Sparkles className="w-4 h-4 text-emerald-600" />
          <div className="text-xs">
            <span className="text-emerald-700 font-medium">Estimated 24h Savings: </span>
            <strong className="text-emerald-800 font-mono text-sm">
              {formatCurrency(cost_savings_amount)} ({cost_savings_pct.toFixed(1)}%)
            </strong>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Baseline Card */}
        <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                Baseline Strategy
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded bg-slate-200 text-slate-700 font-mono">
                No Battery Storage
              </span>
            </div>
            <p className="text-xs text-slate-600 mb-4 leading-relaxed">
              Standard passive setup where load draws solar directly and any surplus is dumped to grid without peak-shaving.
            </p>

            <div className="space-y-3 text-xs">
              <div className="flex items-center justify-between py-1.5 border-b border-slate-200">
                <span className="text-slate-500">Total Grid Import:</span>
                <span className="font-mono font-bold text-slate-900">
                  {formatKwh(baseline_strategy.total_grid_import_kwh)}
                </span>
              </div>
              <div className="flex items-center justify-between py-1.5 border-b border-slate-200">
                <span className="text-slate-500">Total Grid Export:</span>
                <span className="font-mono font-bold text-slate-900">
                  {formatKwh(baseline_strategy.total_grid_export_kwh)}
                </span>
              </div>
              <div className="flex items-center justify-between py-1.5 border-b border-slate-200">
                <span className="text-slate-500">Peak Grid Demand:</span>
                <span className="font-mono font-bold text-red-600">
                  {baseline_strategy.peak_grid_demand_kw.toFixed(1)} kW
                </span>
              </div>
              <div className="flex items-center justify-between py-1.5 border-b border-slate-200">
                <span className="text-slate-500">Renewable Utilization:</span>
                <span className="font-mono font-bold text-slate-700">
                  {formatPct(baseline_strategy.renewable_utilization_pct)}
                </span>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-200 flex items-center justify-between">
            <span className="text-xs text-slate-500 font-medium">Daily Energy Cost:</span>
            <span className="text-xl font-bold font-mono text-slate-800">
              {formatCurrency(baseline_strategy.total_cost)}
            </span>
          </div>
        </div>

        {/* Scheduled AI Strategy Card */}
        <div className="p-4 rounded-lg bg-emerald-50/40 border border-emerald-200 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-1.5">
                <Award className="w-4 h-4 text-emerald-600" />
                <span className="text-xs font-bold uppercase tracking-wider text-emerald-800">
                  Scheduled Strategy
                </span>
              </div>
              <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 font-bold font-mono">
                AI / Storage Enabled
              </span>
            </div>
            <p className="text-xs text-slate-600 mb-4 leading-relaxed">
              Storage-augmented microgrid absorbing midday solar peaks and discharging during high-tariff evening load spikes.
            </p>

            <div className="space-y-3 text-xs">
              <div className="flex items-center justify-between py-1.5 border-b border-emerald-100">
                <span className="text-slate-500">Total Grid Import:</span>
                <span className="font-mono font-bold text-emerald-700">
                  {formatKwh(scheduled_strategy.total_grid_import_kwh)}
                  <span className="text-[10px] text-emerald-600 ml-1">
                    (-{import_reduction_kwh.toFixed(1)} kWh)
                  </span>
                </span>
              </div>
              <div className="flex items-center justify-between py-1.5 border-b border-emerald-100">
                <span className="text-slate-500">Total Grid Export:</span>
                <span className="font-mono font-bold text-teal-700">
                  {formatKwh(scheduled_strategy.total_grid_export_kwh)}
                </span>
              </div>
              <div className="flex items-center justify-between py-1.5 border-b border-emerald-100">
                <span className="text-slate-500">Peak Grid Demand:</span>
                <span className="font-mono font-bold text-emerald-600">
                  {scheduled_strategy.peak_grid_demand_kw.toFixed(1)} kW (Peak Shaved)
                </span>
              </div>
              <div className="flex items-center justify-between py-1.5 border-b border-emerald-100">
                <span className="text-slate-500">Renewable Utilization:</span>
                <span className="font-mono font-bold text-emerald-600">
                  {formatPct(scheduled_strategy.renewable_utilization_pct)}
                </span>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-emerald-200 flex items-center justify-between">
            <span className="text-xs text-emerald-800 font-medium">Optimized Energy Cost:</span>
            <span className="text-xl font-bold font-mono text-emerald-700">
              {formatCurrency(scheduled_strategy.total_cost)}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
