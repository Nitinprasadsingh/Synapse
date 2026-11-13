"use client";

import React, { useState } from "react";
import { SystemAlert } from "@/types";
import {
  AlertTriangle,
  AlertOctagon,
  Info,
  CheckCircle2,
  Clock,
  Filter,
  Check
} from "lucide-react";
import { formatDate } from "@/lib/utils";

interface AlertsListProps {
  alerts: SystemAlert[];
  onAcknowledge: (alertId: number) => Promise<void>;
}

export function AlertsList({ alerts, onAcknowledge }: AlertsListProps) {
  const [categoryFilter, setCategoryFilter] = useState<string>("ALL");
  const [severityFilter, setSeverityFilter] = useState<string>("ALL");
  const [acknowledgingId, setAcknowledgingId] = useState<number | null>(null);

  const filteredAlerts = alerts.filter((a) => {
    if (categoryFilter !== "ALL" && a.category !== categoryFilter) return false;
    if (severityFilter !== "ALL" && a.severity !== severityFilter) return false;
    return true;
  });

  const handleAck = async (id: number) => {
    setAcknowledgingId(id);
    try {
      await onAcknowledge(id);
    } finally {
      setAcknowledgingId(null);
    }
  };

  return (
    <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
      {/* Filters Bar */}
      <div className="p-4 border-b border-slate-200 bg-slate-50 flex flex-wrap items-center justify-between gap-4 text-xs">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <span className="font-semibold text-slate-700 uppercase tracking-wider">Filters:</span>

          {/* Severity filter */}
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="border border-slate-300 rounded px-2.5 py-1 bg-white font-medium text-slate-700"
          >
            <option value="ALL">All Severities</option>
            <option value="CRITICAL">Critical</option>
            <option value="WARNING">Warning</option>
            <option value="INFO">Info</option>
          </select>

          {/* Category filter */}
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="border border-slate-300 rounded px-2.5 py-1 bg-white font-medium text-slate-700"
          >
            <option value="ALL">All Categories</option>
            <option value="Battery">Battery</option>
            <option value="PV">Solar PV</option>
            <option value="Load">Load</option>
            <option value="Grid">Grid</option>
            <option value="System">System</option>
          </select>
        </div>

        <div className="text-slate-500 font-mono">
          Showing {filteredAlerts.length} of {alerts.length} total events
        </div>
      </div>

      {/* List */}
      <div className="divide-y divide-slate-100">
        {filteredAlerts.length === 0 ? (
          <div className="p-12 text-center text-slate-400">
            <CheckCircle2 className="w-8 h-8 mx-auto mb-2 text-slate-300" />
            <p className="text-sm">No alerts match the selected criteria.</p>
          </div>
        ) : (
          filteredAlerts.map((alert) => {
            const isCritical = alert.severity === "CRITICAL";
            const isWarning = alert.severity === "WARNING";
            const isInfo = alert.severity === "INFO";

            return (
              <div
                key={alert.id}
                className={`p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 transition-colors ${
                  !alert.is_acknowledged ? "bg-white" : "bg-slate-50/50 opacity-75"
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className="mt-0.5 flex-shrink-0">
                    {isCritical && <AlertOctagon className="w-5 h-5 text-red-600" />}
                    {isWarning && <AlertTriangle className="w-5 h-5 text-amber-600" />}
                    {isInfo && <Info className="w-5 h-5 text-blue-600" />}
                  </div>

                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-bold text-sm text-slate-900">
                        {alert.title}
                      </span>
                      <span
                        className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded ${
                          isCritical
                            ? "bg-red-100 text-red-800"
                            : isWarning
                            ? "bg-amber-100 text-amber-800"
                            : "bg-blue-100 text-blue-800"
                        }`}
                      >
                        {alert.severity}
                      </span>
                      <span className="text-[10px] font-medium px-2 py-0.5 rounded bg-slate-100 text-slate-600">
                        {alert.category}
                      </span>
                    </div>

                    <p className="text-xs text-slate-600 leading-relaxed mb-2">
                      {alert.message}
                    </p>

                    <div className="flex items-center gap-3 text-[11px] text-slate-400 font-mono">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {new Date(alert.timestamp).toLocaleString([], {
                          month: "short",
                          day: "numeric",
                          hour: "2-digit",
                          minute: "2-digit",
                          second: "2-digit",
                          hour12: false,
                        })}
                      </span>
                      {alert.is_acknowledged && (
                        <span className="text-emerald-600">
                          Acknowledged by {alert.acknowledged_by || "Operator"}
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex-shrink-0 self-end sm:self-center">
                  {alert.is_acknowledged ? (
                    <span className="inline-flex items-center gap-1 text-xs text-slate-400 font-medium px-2 py-1 bg-slate-100 rounded">
                      <Check className="w-3.5 h-3.5 text-emerald-600" />
                      Acknowledged
                    </span>
                  ) : (
                    <button
                      onClick={() => handleAck(alert.id)}
                      disabled={acknowledgingId === alert.id}
                      className="px-3 py-1.5 rounded-md text-xs font-semibold bg-slate-900 text-white hover:bg-slate-800 transition-colors disabled:opacity-50"
                    >
                      {acknowledgingId === alert.id ? "Acknowledging..." : "Acknowledge"}
                    </button>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
