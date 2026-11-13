"use client";

import React from "react";
import { Sun, Battery, Zap, Home, ArrowRight, Activity } from "lucide-react";
import { EnergyFlow } from "@/types";
import { formatKw } from "@/lib/utils";

interface EnergyFlowDiagramProps {
  flow: EnergyFlow;
}

export function EnergyFlowDiagram({ flow }: EnergyFlowDiagramProps) {
  const isCharging = flow.battery_power_kw > 0.1;
  const isDischarging = flow.battery_power_kw < -0.1;
  const isExporting = flow.grid_export_kw > 0.1;
  const isImporting = flow.grid_import_kw > 0.1;
  const hasPvGeneration = flow.pv_power_kw > 0.1;

  return (
    <div className="relative w-full rounded-xl bg-slate-900 border border-slate-800 p-6 shadow-inner text-white overflow-hidden">
      {/* Background Grid Pattern */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#1e293b_1px,transparent_1px),linear-gradient(to_bottom,#1e293b_1px,transparent_1px)] bg-[size:24px_24px] opacity-30 pointer-events-none" />

      {/* Header bar */}
      <div className="flex items-center justify-between mb-6 relative z-10">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-emerald-400 animate-pulse" />
          <span className="text-xs font-bold tracking-wider uppercase text-slate-300">
            Micro-Grid Dispatch Power Flow Routing
          </span>
        </div>
        <div className="flex items-center gap-3 text-xs">
          <span className="font-mono text-slate-400">
            Updated: {new Date(flow.timestamp).toLocaleTimeString([], { hour12: false })}
          </span>
        </div>
      </div>

      {/* SVG Diagram Canvas */}
      <div className="relative z-10 w-full min-h-[360px] flex items-center justify-center">
        <svg
          viewBox="0 0 800 380"
          className="w-full h-auto max-w-4xl"
          style={{ overflow: "visible" }}
        >
          <defs>
            <linearGradient id="pvGrad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#10b981" />
              <stop offset="100%" stopColor="#059669" />
            </linearGradient>
            <linearGradient id="gridGrad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#3b82f6" />
              <stop offset="100%" stopColor="#2563eb" />
            </linearGradient>
            <linearGradient id="batteryGrad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#8b5cf6" />
              <stop offset="100%" stopColor="#7c3aed" />
            </linearGradient>
            <linearGradient id="loadGrad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#f59e0b" />
              <stop offset="100%" stopColor="#d97706" />
            </linearGradient>

            <style>{`
              @keyframes dashFlowForward {
                to {
                  stroke-dashoffset: -24;
                }
              }
              @keyframes dashFlowBackward {
                to {
                  stroke-dashoffset: 24;
                }
              }
              .flow-active-forward {
                stroke-dasharray: 6 6;
                animation: dashFlowForward 1s linear infinite;
              }
              .flow-active-backward {
                stroke-dasharray: 6 6;
                animation: dashFlowBackward 1s linear infinite;
              }
            `}</style>
          </defs>

          {/* Connectors / Power Lines */}
          {/* PV -> Bus (X1=160, Y1=90 -> X2=400, Y2=190) */}
          <path
            d="M 170 90 L 330 90 L 370 160"
            fill="none"
            stroke={hasPvGeneration ? "#10b981" : "#334155"}
            strokeWidth="3"
            className={hasPvGeneration ? "flow-active-forward" : ""}
          />

          {/* Grid <-> Bus (X1=400, Y1=50 -> X2=400, Y2=160) */}
          <path
            d="M 400 60 L 400 160"
            fill="none"
            stroke={isImporting ? "#3b82f6" : isExporting ? "#10b981" : "#334155"}
            strokeWidth="3"
            className={
              isImporting
                ? "flow-active-forward"
                : isExporting
                ? "flow-active-backward"
                : ""
            }
          />

          {/* Battery <-> Bus (X1=170, Y1=290 -> X2=370, Y2=220) */}
          <path
            d="M 170 290 L 330 290 L 370 220"
            fill="none"
            stroke={isCharging ? "#10b981" : isDischarging ? "#8b5cf6" : "#334155"}
            strokeWidth="3"
            className={
              isCharging
                ? "flow-active-backward"
                : isDischarging
                ? "flow-active-forward"
                : ""
            }
          />

          {/* Bus -> Load (X1=430, Y1=190 -> X2=630, Y2=190) */}
          <path
            d="M 430 190 L 630 190"
            fill="none"
            stroke={flow.load_demand_kw > 0 ? "#f59e0b" : "#334155"}
            strokeWidth="4"
            className={flow.load_demand_kw > 0 ? "flow-active-forward" : ""}
          />

          {/* Node 1: Solar PV Plant (Top Left) */}
          <g transform="translate(40, 40)">
            <rect
              width="130"
              height="100"
              rx="10"
              fill="#0f172a"
              stroke="#10b981"
              strokeWidth="2"
              className="filter drop-shadow"
            />
            <circle cx="35" cy="40" r="18" fill="#10b981" fillOpacity="0.15" />
            <foreignObject x="25" y="30" width="20" height="20">
              <Sun className="w-5 h-5 text-emerald-400" />
            </foreignObject>
            <text x="60" y="36" fill="#94a3b8" fontSize="11" fontWeight="bold">
              SOLAR PV
            </text>
            <text x="60" y="55" fill="#10b981" fontSize="16" fontWeight="bold" fontFamily="monospace">
              {formatKw(flow.pv_power_kw)}
            </text>
            <text x="60" y="75" fill="#64748b" fontSize="10">
              Gen Capacity: 50 kW
            </text>
          </g>

          {/* Node 2: Utility Grid (Top Center) */}
          <g transform="translate(330, -10)">
            <rect
              width="140"
              height="75"
              rx="10"
              fill="#0f172a"
              stroke={isExporting ? "#10b981" : "#3b82f6"}
              strokeWidth="2"
            />
            <foreignObject x="15" y="22" width="24" height="24">
              <Zap className={`w-6 h-6 ${isExporting ? "text-emerald-400" : "text-blue-400"}`} />
            </foreignObject>
            <text x="45" y="26" fill="#94a3b8" fontSize="11" fontWeight="bold">
              UTILITY GRID
            </text>
            <text
              x="45"
              y="45"
              fill={isExporting ? "#10b981" : "#60a5fa"}
              fontSize="14"
              fontWeight="bold"
              fontFamily="monospace"
            >
              {isExporting ? `Export: ${flow.grid_export_kw.toFixed(1)} kW` : `Import: ${flow.grid_import_kw.toFixed(1)} kW`}
            </text>
            <text x="45" y="62" fill="#64748b" fontSize="9">
              Interconnection: 150 kW
            </text>
          </g>

          {/* Central Microgrid Bus Node */}
          <g transform="translate(365, 155)">
            <circle cx="35" cy="35" r="35" fill="#1e293b" stroke="#64748b" strokeWidth="3" />
            <circle cx="35" cy="35" r="28" fill="#0f172a" />
            <text x="35" y="32" textAnchor="middle" fill="#f8fafc" fontSize="11" fontWeight="bold">
              SCADA
            </text>
            <text x="35" y="47" textAnchor="middle" fill="#38bdf8" fontSize="10" fontFamily="monospace">
              BUS 400V
            </text>
          </g>

          {/* Node 3: Battery Storage BESS (Bottom Left) */}
          <g transform="translate(40, 240)">
            <rect
              width="130"
              height="100"
              rx="10"
              fill="#0f172a"
              stroke="#8b5cf6"
              strokeWidth="2"
            />
            <foreignObject x="15" y="20" width="24" height="24">
              <Battery className="w-6 h-6 text-purple-400" />
            </foreignObject>
            <text x="45" y="28" fill="#94a3b8" fontSize="11" fontWeight="bold">
              BESS STORAGE
            </text>
            <text x="45" y="48" fill="#c084fc" fontSize="14" fontWeight="bold" fontFamily="monospace">
              SOC: {flow.battery_soc_pct.toFixed(1)}%
            </text>
            {/* Battery state bar */}
            <rect x="45" y="58" width="70" height="7" rx="3" fill="#334155" />
            <rect
              x="45"
              y="58"
              width={Math.max(4, Math.min(70, (flow.battery_soc_pct / 100) * 70))}
              height="7"
              rx="3"
              fill={flow.battery_soc_pct < 25 ? "#ef4444" : "#a855f7"}
            />
            <text x="45" y="80" fill="#64748b" fontSize="10">
              {isCharging ? `Charging: +${flow.battery_power_kw.toFixed(1)} kW` : isDischarging ? `Discharge: -${Math.abs(flow.battery_power_kw).toFixed(1)} kW` : "State: Standby"}
            </text>
          </g>

          {/* Node 4: Community / Facility Load (Right) */}
          <g transform="translate(630, 140)">
            <rect
              width="140"
              height="100"
              rx="10"
              fill="#0f172a"
              stroke="#f59e0b"
              strokeWidth="2"
            />
            <circle cx="35" cy="40" r="18" fill="#f59e0b" fillOpacity="0.15" />
            <foreignObject x="25" y="30" width="20" height="20">
              <Home className="w-5 h-5 text-amber-400" />
            </foreignObject>
            <text x="60" y="36" fill="#94a3b8" fontSize="11" fontWeight="bold">
              FACILITY LOAD
            </text>
            <text x="60" y="58" fill="#fbbf24" fontSize="16" fontWeight="bold" fontFamily="monospace">
              {formatKw(flow.load_demand_kw)}
            </text>
            <text x="60" y="78" fill="#64748b" fontSize="10">
              Demand Peak: 55 kW
            </text>
          </g>

          {/* Flow Indicator Badges on Paths */}
          {/* PV to Load branch badge */}
          {flow.flow_pv_to_load_kw > 0.1 && (
            <g transform="translate(230, 75)">
              <rect width="70" height="20" rx="4" fill="#064e3b" stroke="#059669" />
              <text x="35" y="14" textAnchor="middle" fill="#6ee7b7" fontSize="10" fontWeight="bold" fontFamily="monospace">
                +{flow.flow_pv_to_load_kw.toFixed(1)} kW
              </text>
            </g>
          )}

          {/* Battery branch badge */}
          {Math.abs(flow.battery_power_kw) > 0.1 && (
            <g transform="translate(230, 275)">
              <rect width="70" height="20" rx="4" fill="#3b0764" stroke="#7e22ce" />
              <text x="35" y="14" textAnchor="middle" fill="#d8b4fe" fontSize="10" fontWeight="bold" fontFamily="monospace">
                {isCharging ? `+${flow.battery_power_kw.toFixed(1)} kW` : `-${Math.abs(flow.battery_power_kw).toFixed(1)} kW`}
              </text>
            </g>
          )}

          {/* Grid branch badge */}
          {(flow.grid_import_kw > 0.1 || flow.grid_export_kw > 0.1) && (
            <g transform="translate(415, 100)">
              <rect width="70" height="20" rx="4" fill="#172554" stroke="#1d4ed8" />
              <text x="35" y="14" textAnchor="middle" fill="#93c5fd" fontSize="10" fontWeight="bold" fontFamily="monospace">
                {isExporting ? `-${flow.grid_export_kw.toFixed(1)} kW` : `+${flow.grid_import_kw.toFixed(1)} kW`}
              </text>
            </g>
          )}

          {/* Main Load Feed Badge */}
          <g transform="translate(500, 175)">
            <rect width="80" height="22" rx="4" fill="#451a03" stroke="#b45309" />
            <text x="40" y="15" textAnchor="middle" fill="#fde68a" fontSize="11" fontWeight="bold" fontFamily="monospace">
              {flow.load_demand_kw.toFixed(1)} kW
            </text>
          </g>
        </svg>
      </div>

      {/* Dynamic Summary Breakdown Bar */}
      <div className="mt-4 pt-4 border-t border-slate-800 grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
        <div className="bg-slate-800/60 p-2.5 rounded-lg border border-slate-700/60">
          <span className="text-slate-400 block mb-0.5">PV to Load</span>
          <span className="text-emerald-400 font-mono font-bold text-sm">
            {formatKw(flow.flow_pv_to_load_kw)}
          </span>
        </div>
        <div className="bg-slate-800/60 p-2.5 rounded-lg border border-slate-700/60">
          <span className="text-slate-400 block mb-0.5">PV to Storage</span>
          <span className="text-purple-400 font-mono font-bold text-sm">
            {formatKw(flow.flow_pv_to_battery_kw)}
          </span>
        </div>
        <div className="bg-slate-800/60 p-2.5 rounded-lg border border-slate-700/60">
          <span className="text-slate-400 block mb-0.5">Battery to Load</span>
          <span className="text-purple-400 font-mono font-bold text-sm">
            {formatKw(flow.flow_battery_to_load_kw)}
          </span>
        </div>
        <div className="bg-slate-800/60 p-2.5 rounded-lg border border-slate-700/60">
          <span className="text-slate-400 block mb-0.5">Grid to Load</span>
          <span className="text-blue-400 font-mono font-bold text-sm">
            {formatKw(flow.flow_grid_to_load_kw)}
          </span>
        </div>
      </div>
    </div>
  );
}
