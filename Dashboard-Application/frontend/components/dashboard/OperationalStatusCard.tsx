import React from "react";
import { ShieldCheck, AlertTriangle, AlertOctagon, CheckCircle2 } from "lucide-react";

interface OperationalStatusCardProps {
  status: "Normal" | "Warning" | "Critical";
  message: string;
}

export function OperationalStatusCard({ status, message }: OperationalStatusCardProps) {
  const isNormal = status === "Normal";
  const isWarning = status === "Warning";
  const isCritical = status === "Critical";

  return (
    <div
      className={`p-4 rounded-lg border transition-all ${
        isNormal
          ? "bg-emerald-50/60 border-emerald-200 text-emerald-900"
          : isWarning
          ? "bg-amber-50/60 border-amber-200 text-amber-900"
          : "bg-red-50/60 border-red-200 text-red-900"
      }`}
    >
      <div className="flex items-start gap-3">
        <div className="mt-0.5 flex-shrink-0">
          {isNormal && <CheckCircle2 className="w-5 h-5 text-emerald-600" />}
          {isWarning && <AlertTriangle className="w-5 h-5 text-amber-600" />}
          {isCritical && <AlertOctagon className="w-5 h-5 text-red-600" />}
        </div>

        <div className="flex-1">
          <div className="flex items-center justify-between mb-1">
            <span className="font-bold text-xs uppercase tracking-wider">
              Micro-Grid Controller: {status.toUpperCase()}
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white/70 border border-current">
              Frequency: 50.00 Hz (Nominal)
            </span>
          </div>
          <p className="text-xs leading-relaxed opacity-90">{message}</p>
        </div>
      </div>
    </div>
  );
}
