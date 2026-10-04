"use client";

import React, { useState } from "react";
import {
  AlertTriangle,
  ArrowDownRight,
  ArrowUpRight,
  BarChart2,
  Calendar,
  CheckCircle,
  Database,
  Filter,
  MessageSquare,
  ShieldCheck,
  Smile,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import { OverviewStats, TimeSeriesResponse } from "@/lib/types";

interface OverviewTabProps {
  stats: OverviewStats | null;
  timeseries: TimeSeriesResponse | null;
  loading: boolean;
  onRefresh: () => void;
}

const TOPIC_LABELS: Record<string, string> = {
  pricing_billing: "Pricing & Billing",
  customer_service: "Customer Support",
  bug_issue: "Bugs & Outages",
  feature_request: "Feature Requests",
  performance: "Performance & Reliability",
  competitors: "Competitor Comparison",
  onboarding_setup: "Onboarding & UX",
  general_feedback: "General Feedback",
};

export function OverviewTab({ stats, timeseries, loading, onRefresh }: OverviewTabProps) {
  if (loading && !stats) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-28 bg-slate-800/40 rounded-2xl border border-slate-700/50" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="h-72 bg-slate-800/40 rounded-2xl border border-slate-700/50 lg:col-span-2" />
          <div className="h-72 bg-slate-800/40 rounded-2xl border border-slate-700/50" />
        </div>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="text-center py-20 bg-slate-900/40 rounded-2xl border border-slate-800 p-8">
        <Database className="h-10 w-10 text-slate-500 mx-auto mb-3" />
        <h3 className="text-base font-semibold text-white">No data collected yet</h3>
        <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
          Start by clicking "Collect Mentions" in the top bar to ingest mentions from Hacker News, Google News, and Reddit.
        </p>
      </div>
    );
  }

  const { total_mentions, sentiment, top_topics, quality, sources } = stats;

  return (
    <div className="space-y-6">
      {/* 4 Primary KPI Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Mentions */}
        <div className="glass-card rounded-2xl p-5 relative overflow-hidden">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Total Mentions</span>
            <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400">
              <MessageSquare className="h-4 w-4" />
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold tracking-tight text-white">
              {total_mentions.toLocaleString()}
            </span>
          </div>
          <p className="text-[11px] text-slate-400 mt-2 flex items-center gap-1">
            <CheckCircle className="h-3 w-3 text-emerald-400" />
            <span>Passed deduplication & quality filters</span>
          </p>
        </div>

        {/* Positive Sentiment */}
        <div className="glass-card rounded-2xl p-5 relative overflow-hidden">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Positive Sentiment</span>
            <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-400">
              <TrendingUp className="h-4 w-4" />
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold tracking-tight text-emerald-400">
              {sentiment.positive_pct.toFixed(1)}%
            </span>
            <span className="text-xs text-slate-400">({sentiment.positive} items)</span>
          </div>
          <div className="w-full bg-slate-800 rounded-full h-1.5 mt-3 overflow-hidden">
            <div
              className="bg-emerald-500 h-1.5 rounded-full"
              style={{ width: `${Math.min(100, sentiment.positive_pct)}%` }}
            />
          </div>
        </div>

        {/* Neutral Sentiment */}
        <div className="glass-card rounded-2xl p-5 relative overflow-hidden">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Neutral Sentiment</span>
            <div className="p-2 rounded-xl bg-slate-500/10 text-slate-300">
              <BarChart2 className="h-4 w-4" />
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold tracking-tight text-slate-200">
              {sentiment.neutral_pct.toFixed(1)}%
            </span>
            <span className="text-xs text-slate-400">({sentiment.neutral} items)</span>
          </div>
          <div className="w-full bg-slate-800 rounded-full h-1.5 mt-3 overflow-hidden">
            <div
              className="bg-slate-400 h-1.5 rounded-full"
              style={{ width: `${Math.min(100, sentiment.neutral_pct)}%` }}
            />
          </div>
        </div>

        {/* Negative Sentiment */}
        <div className="glass-card rounded-2xl p-5 relative overflow-hidden">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Negative Sentiment</span>
            <div className="p-2 rounded-xl bg-rose-500/10 text-rose-400">
              <TrendingDown className="h-4 w-4" />
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold tracking-tight text-rose-400">
              {sentiment.negative_pct.toFixed(1)}%
            </span>
            <span className="text-xs text-slate-400">({sentiment.negative} items)</span>
          </div>
          <div className="w-full bg-slate-800 rounded-full h-1.5 mt-3 overflow-hidden">
            <div
              className="bg-rose-500 h-1.5 rounded-full"
              style={{ width: `${Math.min(100, sentiment.negative_pct)}%` }}
            />
          </div>
        </div>
      </div>

      {/* Main Charts & Visualizations */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Mentions Timeline / Volume */}
        <div className="glass-card rounded-2xl p-6 lg:col-span-2 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <Calendar className="h-4 w-4 text-indigo-400" />
                Mentions Over Time
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">Chronological mention volume & sentiment mix</p>
            </div>
          </div>

          {/* Timeline visualization */}
          {timeseries && timeseries.buckets.length > 0 ? (
            <div className="space-y-3 my-2">
              <div className="h-44 flex items-end gap-2 pt-6 pb-2 border-b border-slate-800/80">
                {timeseries.buckets.map((b, idx) => {
                  const maxCount = Math.max(...timeseries.buckets.map((x) => x.total), 1);
                  const heightPct = Math.max(12, Math.round((b.total / maxCount) * 100));
                  return (
                    <div
                      key={idx}
                      className="flex-1 flex flex-col items-center gap-1 group relative h-full justify-end"
                    >
                      {/* Tooltip on hover */}
                      <div className="absolute -top-12 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none bg-slate-900 border border-slate-700 px-2 py-1 rounded text-[10px] text-white whitespace-nowrap z-20 shadow-xl">
                        <div className="font-semibold">{b.timestamp}</div>
                        <div>Total: {b.total} (Pos: {b.positive}, Neu: {b.neutral}, Neg: {b.negative})</div>
                      </div>

                      {/* Stacked bar */}
                      <div
                        className="w-full rounded-t-md overflow-hidden flex flex-col-reverse transition-all group-hover:brightness-125"
                        style={{ height: `${heightPct}%` }}
                      >
                        <div
                          className="bg-emerald-500 w-full"
                          style={{ height: `${(b.positive / (b.total || 1)) * 100}%` }}
                        />
                        <div
                          className="bg-slate-500 w-full"
                          style={{ height: `${(b.neutral / (b.total || 1)) * 100}%` }}
                        />
                        <div
                          className="bg-rose-500 w-full"
                          style={{ height: `${(b.negative / (b.total || 1)) * 100}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Bucket Labels */}
              <div className="flex justify-between text-[10px] text-slate-400 px-1">
                <span>{timeseries.buckets[0]?.timestamp}</span>
                {timeseries.buckets.length > 2 && (
                  <span>{timeseries.buckets[Math.floor(timeseries.buckets.length / 2)]?.timestamp}</span>
                )}
                <span>{timeseries.buckets[timeseries.buckets.length - 1]?.timestamp}</span>
              </div>

              {/* Legend */}
              <div className="flex items-center justify-center gap-5 text-xs text-slate-400 pt-2">
                <div className="flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-emerald-400" />
                  <span>Positive</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-slate-400" />
                  <span>Neutral</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-rose-400" />
                  <span>Negative</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="py-12 text-center text-xs text-slate-400">
              Not enough chronological buckets yet.
            </div>
          )}
        </div>

        {/* Top Topics Distribution */}
        <div className="glass-card rounded-2xl p-6 flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-1">
              <BarChart2 className="h-4 w-4 text-violet-400" />
              Topic Categorization
            </h3>
            <p className="text-xs text-slate-400 mb-4">Semantic clustering via MiniLM embeddings</p>

            <div className="space-y-3">
              {top_topics.slice(0, 6).map((item, idx) => {
                const label = TOPIC_LABELS[item.topic] || item.topic;
                return (
                  <div key={idx} className="space-y-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-300 font-medium truncate max-w-[170px]">
                        {label}
                      </span>
                      <span className="text-slate-400 font-mono text-[11px]">
                        {item.count} ({item.percentage}%)
                      </span>
                    </div>
                    <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                      <div
                        className="bg-gradient-to-r from-indigo-500 to-violet-500 h-1.5 rounded-full"
                        style={{ width: `${Math.min(100, item.percentage)}%` }}
                      />
                    </div>
                  </div>
                );
              })}
              {top_topics.length === 0 && (
                <p className="text-xs text-slate-400 py-6 text-center">No topic data available</p>
              )}
            </div>
          </div>

          {/* Sources breakdown badge row */}
          <div className="pt-4 border-t border-slate-800/80 mt-4">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-2">
              Ingested Sources
            </span>
            <div className="flex flex-wrap gap-1.5">
              {Object.entries(sources).map(([src, cnt]) => (
                <span
                  key={src}
                  className="px-2 py-0.5 bg-slate-800/80 border border-slate-700/60 rounded-md text-[11px] text-slate-300"
                >
                  {src}: <strong className="text-white">{cnt}</strong>
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Data Quality & Pipeline Audit Summary */}
      <div className="glass-card rounded-2xl p-6 border-slate-800/80">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
          <div>
            <div className="flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-emerald-400" />
              <h3 className="text-sm font-semibold text-white">Data Pipeline & Quality Audit</h3>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Deterministic deduplication, language filtering, relevance boundary checking, and anti-spam
            </p>
          </div>
          <div className="flex items-center gap-4 text-xs">
            <div>
              <span className="text-slate-400">Total Ingested: </span>
              <strong className="text-white font-mono">{quality.total_collected}</strong>
            </div>
            <div>
              <span className="text-slate-400">Kept: </span>
              <strong className="text-emerald-400 font-mono">{quality.total_kept}</strong>
            </div>
            <div>
              <span className="text-slate-400">Dropped: </span>
              <strong className="text-rose-400 font-mono">{quality.total_dropped}</strong>
            </div>
          </div>
        </div>

        {/* Drop reasons pills */}
        <div className="pt-4">
          <span className="text-xs text-slate-400 block mb-2">Filtered items by reason:</span>
          <div className="flex flex-wrap gap-2">
            {Object.entries(quality.drop_reasons).map(([reason, count]) => (
              <div
                key={reason}
                className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-slate-900/90 border border-slate-800 text-xs text-slate-300"
              >
                <span className="text-rose-400 font-mono font-bold">{count}</span>
                <span className="text-slate-400">dropped:</span>
                <span className="font-medium text-slate-200">{reason.replace(/_/g, " ")}</span>
              </div>
            ))}
            {Object.keys(quality.drop_reasons).length === 0 && (
              <span className="text-xs text-slate-400">No dropped items in this dataset.</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
