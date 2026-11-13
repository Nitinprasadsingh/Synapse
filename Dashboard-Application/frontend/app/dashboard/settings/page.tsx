"use client";

import React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { endpoints } from "@/lib/api/endpoints";
import { SettingsForm } from "@/components/settings/SettingsForm";
import { AllSettings } from "@/types";

export default function SettingsPage() {
  const queryClient = useQueryClient();

  const settingsQuery = useQuery({
    queryKey: ["allSettings"],
    queryFn: endpoints.getAllSettings,
  });

  const saveMutation = useMutation({
    mutationFn: (updated: AllSettings) => endpoints.updateAllSettings(updated),
    onSuccess: (newSettings) => {
      queryClient.setQueryData(["allSettings"], newSettings);
      // Invalidate simulation queries so updated parameters immediately reflect on overview & schedules
      queryClient.invalidateQueries({ queryKey: ["dashboardOverview"] });
      queryClient.invalidateQueries({ queryKey: ["batteryStatus"] });
      queryClient.invalidateQueries({ queryKey: ["batterySchedule"] });
      queryClient.invalidateQueries({ queryKey: ["gridStatus"] });
      queryClient.invalidateQueries({ queryKey: ["gridAnalytics"] });
    },
  });

  const handleSave = async (updated: AllSettings) => {
    await saveMutation.mutateAsync(updated);
  };

  if (settingsQuery.isLoading) {
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
              System Parameters & Operational Configuration
            </h2>
          </div>
          <p className="text-xs text-slate-500">
            Configure physical asset ratings, state-of-charge constraints, tariffs, and forecasting horizons
          </p>
        </div>
      </div>

      {settingsQuery.data && (
        <SettingsForm
          initialSettings={settingsQuery.data}
          onSave={handleSave}
        />
      )}
    </div>
  );
}
