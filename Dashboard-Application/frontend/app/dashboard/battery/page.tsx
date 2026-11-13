"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { endpoints } from "@/lib/api/endpoints";
import { BatteryOverviewCard } from "@/components/battery/BatteryOverviewCard";
import { BatteryScheduleChart } from "@/components/battery/BatteryScheduleChart";
import { BatteryScheduleTable } from "@/components/battery/BatteryScheduleTable";
import { Play, Sparkles, RefreshCw, Cpu } from "lucide-react";
import { useAuth } from "@/lib/auth/AuthContext";

export default function BatterySchedulingPage() {
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const [successNotice, setSuccessNotice] = useState<string | null>(null);

  const statusQuery = useQuery({
    queryKey: ["batteryStatus"],
    queryFn: endpoints.getBatteryStatus,
  });

  const scheduleQuery = useQuery({
    queryKey: ["batterySchedule"],
    queryFn: endpoints.getBatterySchedule,
  });

  const generateMutation = useMutation({
    mutationFn: () => endpoints.generateBatterySchedule(24),
    onSuccess: (newSchedule) => {
      queryClient.setQueryData(["batterySchedule"], newSchedule);
      setSuccessNotice(`New schedule ${newSchedule.schedule_id} generated successfully.`);
      setTimeout(() => setSuccessNotice(null), 5000);
    },
  });

  const isLoading = statusQuery.isLoading || scheduleQuery.isLoading;

  if (isLoading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-44 bg-slate-200 rounded-lg" />
        <div className="h-96 bg-slate-200 rounded-lg" />
        <div className="h-96 bg-slate-200 rounded-lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Controls Banner */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 rounded-lg bg-white border border-slate-200 shadow-sm">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-bold text-slate-900">
              Battery Storage (BESS) Dispatch & Scheduling Engine
            </h2>
          </div>
          <p className="text-xs text-slate-500">
            Heuristic energy balance respecting storage constraints. Interface ready for Python OR-Tools / MPC integration.
          </p>
        </div>

        {/* Generate Schedule Button */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => generateMutation.mutate()}
            disabled={generateMutation.isPending}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-700 text-white font-semibold text-xs shadow-md shadow-purple-900/20 transition-all disabled:opacity-50"
            title="Compute new 24h battery schedule"
          >
            {generateMutation.isPending ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <Play className="w-4 h-4 fill-white" />
            )}
            <span>Generate Battery Schedule</span>
          </button>
        </div>
      </div>

      {successNotice && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-emerald-800 text-xs font-semibold">
          {successNotice}
        </div>
      )}

      {/* 1. Battery Overview Card */}
      {statusQuery.data && <BatteryOverviewCard status={statusQuery.data} />}

      {/* 2. Schedule Trajectory Chart */}
      {scheduleQuery.data && <BatteryScheduleChart schedule={scheduleQuery.data} />}

      {/* 3. Hourly Physical Balance Ledger Table */}
      {scheduleQuery.data && <BatteryScheduleTable steps={scheduleQuery.data.steps} />}
    </div>
  );
}
