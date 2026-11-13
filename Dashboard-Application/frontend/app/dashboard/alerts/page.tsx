"use client";

import React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { endpoints } from "@/lib/api/endpoints";
import { AlertsList } from "@/components/alerts/AlertsList";
import { Bell, RefreshCw } from "lucide-react";

export default function AlertsPage() {
  const queryClient = useQueryClient();

  const alertsQuery = useQuery({
    queryKey: ["allAlerts"],
    queryFn: () => endpoints.getAlerts(),
    refetchInterval: 10000,
  });

  const ackMutation = useMutation({
    mutationFn: (alertId: number) => endpoints.acknowledgeAlert(alertId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["allAlerts"] });
    },
  });

  const handleAcknowledge = async (alertId: number) => {
    await ackMutation.mutateAsync(alertId);
  };

  if (alertsQuery.isLoading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-20 bg-slate-200 rounded-lg" />
        <div className="h-96 bg-slate-200 rounded-lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 rounded-lg bg-white border border-slate-200 shadow-sm">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-bold text-slate-900">
              System Fault Alarms & Telemetry Event Log
            </h2>
          </div>
          <p className="text-xs text-slate-500">
            Real-time event notification ledger with operator acknowledgment logging
          </p>
        </div>

        <button
          onClick={() => alertsQuery.refetch()}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white border border-slate-200 text-slate-700 text-xs font-semibold hover:bg-slate-50 shadow-sm transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${alertsQuery.isFetching ? "animate-spin text-blue-600" : ""}`} />
          <span>Refresh Alerts</span>
        </button>
      </div>

      {/* Alerts List with Filters */}
      {alertsQuery.data && (
        <AlertsList
          alerts={alertsQuery.data}
          onAcknowledge={handleAcknowledge}
        />
      )}
    </div>
  );
}
