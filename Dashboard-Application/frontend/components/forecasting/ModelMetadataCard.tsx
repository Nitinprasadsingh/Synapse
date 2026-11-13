import React from "react";
import { ModelMetadata } from "@/types";
import { Cpu, CheckCircle2, Info, Database } from "lucide-react";
import { formatDate } from "@/lib/utils";

interface ModelMetadataCardProps {
  models: ModelMetadata[];
}

export function ModelMetadataCard({ models }: ModelMetadataCardProps) {
  return (
    <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-base font-semibold text-slate-900">
            Registered Forecasting Models & Pipeline Registry
          </h3>
          <p className="text-xs text-slate-500">
            PV forecasting pipelines and neural load forecasters ready for live Python model integration
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {models.map((model) => {
          let metrics: Record<string, string> = {};
          if (model.metrics_json) {
            try {
              metrics = JSON.parse(model.metrics_json);
            } catch {
              // ignore
            }
          }

          const isBenchmark = model.model_id.includes("nsrdb") || model.status.includes("BENCHMARK");

          return (
            <div
              key={model.model_id}
              className={`p-4 rounded-lg border transition-all ${
                isBenchmark
                  ? "bg-slate-50 border-slate-200"
                  : "bg-emerald-50/40 border-emerald-200"
              }`}
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <div
                    className={`w-7 h-7 rounded flex items-center justify-center ${
                      isBenchmark ? "bg-slate-200 text-slate-700" : "bg-emerald-100 text-emerald-700"
                    }`}
                  >
                    <Cpu className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-slate-900 leading-tight">
                      {model.model_name}
                    </h4>
                    <span className="text-[11px] font-mono text-slate-500">
                      ID: {model.model_id} | v{model.version}
                    </span>
                  </div>
                </div>

                <span
                  className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded ${
                    isBenchmark
                      ? "bg-slate-200 text-slate-700"
                      : "bg-emerald-200 text-emerald-800"
                  }`}
                >
                  {model.status}
                </span>
              </div>

              <p className="text-xs text-slate-600 mb-3 leading-relaxed">
                {model.description}
              </p>

              {/* Data Source & Metrics */}
              <div className="pt-2 border-t border-slate-200/80 flex flex-wrap items-center justify-between text-[11px] text-slate-500 gap-2">
                <div className="flex items-center gap-1">
                  <Database className="w-3.5 h-3.5 text-slate-400" />
                  <span>Source: {model.source || "N/A"}</span>
                </div>

                <div className="flex items-center gap-2 font-mono">
                  {Object.entries(metrics).map(([key, val]) => (
                    <span key={key} className="bg-white/80 px-1.5 py-0.5 rounded border border-slate-200">
                      {key}: <strong className="text-slate-800">{val}</strong>
                    </span>
                  ))}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
