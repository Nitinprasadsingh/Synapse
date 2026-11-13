"use client";

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { endpoints } from "@/lib/api/endpoints";
import { PvForecastChart } from "@/components/forecasting/PvForecastChart";
import { LoadForecastChart } from "@/components/forecasting/LoadForecastChart";
import { CombinedForecastChart } from "@/components/forecasting/CombinedForecastChart";
import { ModelMetadataCard } from "@/components/forecasting/ModelMetadataCard";
import { Sun, RefreshCw, BarChart2 } from "lucide-react";

export default function ForecastingPage() {
  const [horizon, setHorizon] = useState<number>(24);
  const [pvModelId, setPvModelId] = useState<string>("open-meteo-xgboost-v1");

  const pvQuery = useQuery({
    queryKey: ["pvForecast", horizon, pvModelId],
    queryFn: () => endpoints.getPVForecast(horizon, pvModelId),
  });

  const loadQuery = useQuery({
    queryKey: ["loadForecast", horizon],
    queryFn: () => endpoints.getLoadForecast(horizon),
  });

  const combinedQuery = useQuery({
    queryKey: ["combinedForecast", horizon],
    queryFn: () => endpoints.getCombinedForecast(horizon),
  });

  const modelsQuery = useQuery({
    queryKey: ["modelsMetadata"],
    queryFn: endpoints.getModels,
  });

  const isInitialLoading =
    pvQuery.isLoading || loadQuery.isLoading || combinedQuery.isLoading || modelsQuery.isLoading;

  if (isInitialLoading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-20 bg-slate-200 rounded-lg" />
        <div className="h-96 bg-slate-200 rounded-lg" />
        <div className="h-96 bg-slate-200 rounded-lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 rounded-lg bg-white border border-slate-200 shadow-sm">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-bold text-slate-900">
              Operational Solar PV & Load Forecasting Engines
            </h2>
          </div>
          <p className="text-xs text-slate-500">
            Next 24-hour meteorological regression pipelines and deep learning load estimation
          </p>
        </div>

        {/* Model Switcher and Horizon selector */}
        <div className="flex items-center gap-3 text-xs">
          <div className="flex items-center gap-1.5">
            <span className="text-slate-500 font-medium">PV Model:</span>
            <select
              value={pvModelId}
              onChange={(e) => setPvModelId(e.target.value)}
              className="border border-slate-300 rounded px-2.5 py-1.5 bg-white font-medium text-slate-800"
            >
              <option value="open-meteo-xgboost-v1">Open-Meteo XGBoost (Operational)</option>
              <option value="nsrdb-xgboost-benchmark">NSRDB XGBoost (Historical Benchmark)</option>
            </select>
          </div>

          <div className="flex items-center gap-1.5">
            <span className="text-slate-500 font-medium">Horizon:</span>
            <select
              value={horizon}
              onChange={(e) => setHorizon(Number(e.target.value))}
              className="border border-slate-300 rounded px-2.5 py-1.5 bg-white font-medium text-slate-800"
            >
              <option value={12}>12 Hours</option>
              <option value={24}>24 Hours</option>
              <option value={48}>48 Hours</option>
            </select>
          </div>
        </div>
      </div>

      {/* 1. Combined PV vs Load Surplus/Deficit Chart */}
      {combinedQuery.data && <CombinedForecastChart data={combinedQuery.data} />}

      {/* 2. Solar PV Forecasting Chart */}
      {pvQuery.data && <PvForecastChart data={pvQuery.data} />}

      {/* 3. Load Demand Forecasting Chart */}
      {loadQuery.data && <LoadForecastChart data={loadQuery.data} />}

      {/* 4. Model Metadata Registry */}
      {modelsQuery.data && <ModelMetadataCard models={modelsQuery.data} />}
    </div>
  );
}
