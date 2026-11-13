import React from "react";
import { Card, CardContent } from "@/components/ui/card";
import { ArrowUpRight, ArrowDownRight, Minus } from "lucide-react";
import { cn } from "@/lib/utils";

interface KpiCardProps {
  title: string;
  value: number | string;
  unit: string;
  status?: "normal" | "warning" | "critical" | "success";
  changePct?: number | null;
  changePeriod?: string | null;
  icon?: React.ReactNode;
  theme?: "solar" | "grid" | "battery" | "cost" | "default";
}

export function KpiCard({
  title,
  value,
  unit,
  status = "normal",
  changePct,
  changePeriod,
  icon,
  theme = "default",
}: KpiCardProps) {
  const themeBorder = {
    solar: "border-l-4 border-l-emerald-500",
    grid: "border-l-4 border-l-blue-600",
    battery: "border-l-4 border-l-purple-600",
    cost: "border-l-4 border-l-amber-500",
    default: "border-l-4 border-l-slate-300",
  }[theme];

  const formattedVal = typeof value === "number" ? value.toFixed(1) : value;

  return (
    <Card className={cn("transition-all hover:shadow-md bg-white", themeBorder)}>
      <CardContent className="p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 truncate">
            {title}
          </span>
          {icon && <div className="text-slate-400">{icon}</div>}
        </div>

        <div className="flex items-baseline gap-1.5 mb-2">
          <span className="text-2xl font-bold tracking-tight text-slate-900 font-mono">
            {formattedVal}
          </span>
          <span className="text-xs font-medium text-slate-500">{unit}</span>
        </div>

        <div className="flex items-center justify-between text-[11px] text-slate-500">
          {changePct !== undefined && changePct !== null ? (
            <div className="flex items-center gap-1 font-medium">
              {changePct > 0 ? (
                <span className="flex items-center text-emerald-600">
                  <ArrowUpRight className="w-3.5 h-3.5" />
                  +{changePct.toFixed(1)}%
                </span>
              ) : changePct < 0 ? (
                <span className="flex items-center text-blue-600">
                  <ArrowDownRight className="w-3.5 h-3.5" />
                  {changePct.toFixed(1)}%
                </span>
              ) : (
                <span className="flex items-center text-slate-400">
                  <Minus className="w-3.5 h-3.5" />
                  0.0%
                </span>
              )}
              {changePeriod && <span className="text-slate-400">{changePeriod}</span>}
            </div>
          ) : (
            <span className="text-slate-400 font-mono text-[10px]">Real-time telemetry</span>
          )}

          <div className="flex items-center gap-1">
            <span
              className={cn(
                "inline-block w-2 h-2 rounded-full",
                status === "success" && "bg-emerald-500",
                status === "normal" && "bg-blue-500",
                status === "warning" && "bg-amber-500",
                status === "critical" && "bg-red-500"
              )}
            />
            <span className="capitalize text-[10px] text-slate-500">{status}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
