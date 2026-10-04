"use client";

import React from "react";
import { AlertTriangle, Flame, ShieldAlert, TrendingUp } from "lucide-react";
import { AlertItem, TrendItem } from "@/lib/types";

interface TrendsAlertsBannerProps {
  alerts: AlertItem[];
  trends: TrendItem[];
}

export function TrendsAlertsBanner({ alerts, trends }: TrendsAlertsBannerProps) {
  if (alerts.length === 0 && trends.length === 0) {
    return null;
  }

  return (
    <div className="space-y-2 mb-6">
      {/* Anomaly Alerts (BON-04) */}
      {alerts.map((alert) => (
        <div
          key={alert.id}
          className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 flex items-start gap-3 text-rose-300"
        >
          <div className="p-1.5 rounded-lg bg-rose-500/20 text-rose-400 shrink-0 mt-0.5">
            <ShieldAlert className="h-5 w-5" />
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <h4 className="text-xs font-bold uppercase tracking-wider text-rose-300">
                {alert.title}
              </h4>
              <span className="text-[10px] px-1.5 py-0.2 rounded bg-rose-500/20 text-rose-300 font-mono">
                {new Date(alert.created_at).toLocaleDateString()}
              </span>
            </div>
            <p className="text-xs text-rose-200 mt-1 leading-relaxed">{alert.description}</p>
          </div>
        </div>
      ))}

      {/* Trending Topics (BON-01) */}
      {trends.length > 0 && (
        <div className="p-3.5 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex flex-wrap items-center gap-3 text-xs text-indigo-200">
          <div className="flex items-center gap-1.5 text-indigo-400 font-bold uppercase tracking-wider text-[11px]">
            <Flame className="h-4 w-4 text-amber-400 animate-bounce" />
            <span>Topic Velocity:</span>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {trends.map((t, idx) => (
              <span
                key={idx}
                className="inline-flex items-center gap-1 px-2.5 py-1 rounded-xl bg-slate-900/90 border border-indigo-500/30 text-indigo-200 font-medium"
              >
                <span className="capitalize">{t.topic.replace(/_/g, " ")}</span>
                <span className="text-emerald-400 font-mono text-[11px] font-bold">
                  +{t.pct_change}%
                </span>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
