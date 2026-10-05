"use client";

import React, { useState } from "react";
import {
  AlertTriangle,
  CheckCircle,
  Flame,
  Radio,
  ShieldAlert,
  Sparkles,
  TrendingUp,
} from "lucide-react";
import { AlertItem, TrendItem } from "@/lib/types";

interface TrendsAlertsBannerProps {
  alerts: AlertItem[];
  trends: TrendItem[];
  onResolveAlert?: (alertId: number) => Promise<void> | void;
  onSimulateAlert?: () => Promise<void> | void;
}

export function TrendsAlertsBanner({
  alerts,
  trends,
  onResolveAlert,
  onSimulateAlert,
}: TrendsAlertsBannerProps) {
  const [resolvingId, setResolvingId] = useState<number | null>(null);
  const [simulating, setSimulating] = useState(false);

  const handleResolve = async (id: number) => {
    if (!onResolveAlert) return;
    setResolvingId(id);
    try {
      await onResolveAlert(id);
    } finally {
      setResolvingId(null);
    }
  };

  const handleSimulate = async () => {
    if (!onSimulateAlert) return;
    setSimulating(true);
    try {
      await onSimulateAlert();
    } finally {
      setSimulating(false);
    }
  };

  if (alerts.length === 0 && trends.length === 0 && !onSimulateAlert) {
    return null;
  }

  return (
    <div className="space-y-3 mb-6">
      {/* Anomaly Alerts (BON-04) */}
      {alerts.map((alert) => {
        const title =
          alert.title ||
          (alert.alert_type === "sentiment_spike"
            ? "Negative Sentiment Spike Detected"
            : alert.alert_type === "volume_spike"
            ? "Abnormal Volume Surge Detected"
            : "Statistical Anomaly Alert");
        const message = alert.message || alert.description || "Elevated anomaly metrics detected.";
        const isCritical = alert.severity === "critical";

        return (
          <div
            key={alert.id}
            className={`p-4 rounded-2xl border transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-4 ${
              isCritical
                ? "bg-rose-500/10 border-rose-500/30 text-rose-300 shadow-lg shadow-rose-950/20"
                : "bg-amber-500/10 border-amber-500/30 text-amber-300"
            }`}
          >
            <div className="flex items-start gap-3">
              <div
                className={`p-2 rounded-xl shrink-0 mt-0.5 ${
                  isCritical ? "bg-rose-500/20 text-rose-400" : "bg-amber-500/20 text-amber-400"
                }`}
              >
                <ShieldAlert className="h-5 w-5" />
              </div>
              <div className="space-y-1">
                <div className="flex flex-wrap items-center gap-2">
                  <h4 className="text-xs font-bold uppercase tracking-wider">{title}</h4>
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider font-mono ${
                      isCritical
                        ? "bg-rose-500/20 text-rose-300 border border-rose-500/30"
                        : "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                    }`}
                  >
                    {alert.severity || "warning"}
                  </span>
                  <span className="text-[10px] text-slate-400 font-mono">
                    {new Date(alert.created_at).toLocaleDateString()}
                  </span>
                </div>
                <p className="text-xs text-slate-200 leading-relaxed max-w-3xl">{message}</p>
              </div>
            </div>

            {/* Resolve / Acknowledge Action Button */}
            {onResolveAlert && (
              <div className="shrink-0 flex items-center gap-2 self-end sm:self-center">
                <button
                  onClick={() => handleResolve(alert.id)}
                  disabled={resolvingId === alert.id}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-900/80 hover:bg-slate-900 border border-slate-700/80 hover:border-emerald-500/50 text-xs font-semibold text-slate-200 hover:text-emerald-400 transition-all shadow-sm"
                >
                  <CheckCircle className={`h-3.5 w-3.5 ${resolvingId === alert.id ? "animate-spin" : "text-emerald-400"}`} />
                  <span>{resolvingId === alert.id ? "Resolving..." : "Acknowledge & Resolve"}</span>
                </button>
              </div>
            )}
          </div>
        );
      })}

      {/* Trending Topics (BON-01) */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3.5 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-xs text-indigo-200">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-1.5 text-indigo-400 font-bold uppercase tracking-wider text-[11px]">
            <Flame className="h-4 w-4 text-amber-400 animate-bounce" />
            <span>Topic Velocity:</span>
          </div>
          {trends.length > 0 ? (
            <div className="flex flex-wrap items-center gap-2">
              {trends.map((t, idx) => (
                <span
                  key={idx}
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-xl bg-slate-900/90 border border-indigo-500/30 text-indigo-200 font-medium"
                >
                  <span className="capitalize">{t.topic.replace(/_/g, " ")}</span>
                  <span className="text-emerald-400 font-mono text-[11px] font-bold">
                    +{t.pct_change}%
                  </span>
                </span>
              ))}
            </div>
          ) : (
            <span className="text-xs text-slate-400">Stable volume baseline across all topics.</span>
          )}
        </div>

        {/* Interactive Anomaly Simulator Button for Evaluators */}
        {onSimulateAlert && (
          <button
            onClick={handleSimulate}
            disabled={simulating}
            title="Simulate a real-time statistical anomaly to test the alerting pipeline"
            className="flex items-center gap-1 px-2.5 py-1 rounded-xl bg-indigo-600/30 hover:bg-indigo-600/50 border border-indigo-500/40 text-[11px] font-semibold text-indigo-200 hover:text-white transition-all shadow-sm"
          >
            <Radio className={`h-3 w-3 ${simulating ? "animate-spin text-rose-400" : "text-indigo-400"}`} />
            <span>{simulating ? "Triggering..." : "Simulate Alert"}</span>
          </button>
        )}
      </div>
    </div>
  );
}
