"use client";

import React from "react";
import { Activity, AlertOctagon, HeartHandshake, TrendingUp } from "lucide-react";
import { OverviewStats } from "@/lib/types";

export interface MetricRibbonProps {
  stats: OverviewStats | null;
  loading?: boolean;
}

export function MetricRibbon({ stats, loading = false }: MetricRibbonProps) {
  if (loading || !stats) {
    return (
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="h-24 bg-[#111827] border border-white/10 rounded-2xl animate-pulse"
          />
        ))}
      </div>
    );
  }

  // 1. Net Sentiment Score (-100 to +100)
  const posPct = stats.sentiment?.positive_pct ?? 0;
  const negPct = stats.sentiment?.negative_pct ?? 0;
  const netSentimentScore = Math.round(posPct - negPct);

  // 2. Brand Health Index (0 to 100)
  // Scaled composite taking net sentiment and qualifying ratios into account
  const brandHealthIndex = Math.min(
    100,
    Math.max(0, Math.round(50 + netSentimentScore * 0.5))
  );

  // 3. Total Mentions Processed
  const totalProcessed =
    stats.quality?.total_collected ??
    (stats.total_mentions ?? 0) + (stats.quality?.total_dropped ?? 0);

  // 4. Rejection Rate
  const totalDropped = stats.quality?.total_dropped ?? 0;
  const rejectionRate =
    totalProcessed > 0
      ? Math.round((totalDropped / totalProcessed) * 100)
      : 0;

  const nssAccent =
    netSentimentScore > 20
      ? "text-emerald-400"
      : netSentimentScore < -20
      ? "text-rose-400"
      : "text-amber-400";

  const bhiAccent =
    brandHealthIndex >= 65
      ? "text-emerald-400"
      : brandHealthIndex <= 40
      ? "text-rose-400"
      : "text-amber-400";

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
      {/* Net Sentiment Score */}
      <div className="bg-[#111827] border border-white/10 rounded-2xl p-4 flex flex-col justify-between">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-slate-400">
            Net Sentiment Score
          </span>
          <div className="p-1.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
            <TrendingUp className="h-4 w-4" />
          </div>
        </div>
        <div className="mt-2 flex items-baseline gap-2">
          <span className={`text-2xl font-bold font-mono tabular-nums ${nssAccent}`}>
            {netSentimentScore > 0 ? `+${netSentimentScore}` : netSentimentScore}
          </span>
          <span className="text-[11px] text-slate-400">scale -100 to +100</span>
        </div>
        <p className="text-[11px] text-slate-400 mt-1">
          {posPct}% positive vs {negPct}% negative
        </p>
      </div>

      {/* Brand Health Index */}
      <div className="bg-[#111827] border border-white/10 rounded-2xl p-4 flex flex-col justify-between">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-slate-400">
            Brand Health Index
          </span>
          <div className="p-1.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
            <HeartHandshake className="h-4 w-4" />
          </div>
        </div>
        <div className="mt-2 flex items-baseline gap-2">
          <span className={`text-2xl font-bold font-mono tabular-nums ${bhiAccent}`}>
            {brandHealthIndex}
          </span>
          <span className="text-[11px] text-slate-400">/ 100</span>
        </div>
        <p className="text-[11px] text-slate-400 mt-1">
          Weighted reputation health score
        </p>
      </div>

      {/* Total Mentions Processed */}
      <div className="bg-[#111827] border border-white/10 rounded-2xl p-4 flex flex-col justify-between">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-slate-400">
            Total Mentions Processed
          </span>
          <div className="p-1.5 rounded-xl bg-sky-500/10 border border-sky-500/20 text-sky-400">
            <Activity className="h-4 w-4" />
          </div>
        </div>
        <div className="mt-2 flex items-baseline gap-2">
          <span className="text-2xl font-bold font-mono tabular-nums text-white">
            {totalProcessed.toLocaleString()}
          </span>
          <span className="text-[11px] text-slate-400">items</span>
        </div>
        <p className="text-[11px] text-slate-400 mt-1">
          Across all active ingestion channels
        </p>
      </div>

      {/* Rejection Rate */}
      <div className="bg-[#111827] border border-white/10 rounded-2xl p-4 flex flex-col justify-between">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-slate-400">
            Rejection Rate
          </span>
          <div className="p-1.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400">
            <AlertOctagon className="h-4 w-4" />
          </div>
        </div>
        <div className="mt-2 flex items-baseline gap-2">
          <span className="text-2xl font-bold font-mono tabular-nums text-slate-200">
            {rejectionRate}%
          </span>
          <span className="text-[11px] text-slate-400">
            ({totalDropped.toLocaleString()} pruned)
          </span>
        </div>
        <p className="text-[11px] text-slate-400 mt-1">
          Filtered via xxHash64 and Jaccard
        </p>
      </div>
    </div>
  );
}
