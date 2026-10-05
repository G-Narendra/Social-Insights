"use client";

import React, { useState } from "react";
import {
  Activity,
  AlertTriangle,
  ArrowDownRight,
  ArrowUpRight,
  Award,
  BarChart2,
  Calendar,
  CheckCircle,
  Database,
  ExternalLink,
  Filter,
  Flame,
  MessageSquare,
  Search,
  ShieldCheck,
  Smile,
  Sparkles,
  TrendingDown,
  TrendingUp,
  Zap,
} from "lucide-react";
import { OverviewStats, TimeSeriesResponse } from "@/lib/types";

interface OverviewTabProps {
  stats: OverviewStats | null;
  timeseries: TimeSeriesResponse | null;
  loading: boolean;
  onRefresh: () => void;
  onSelectSearchTerm?: (term: string) => void;
  onSelectFilter?: (filters: { sentiment?: string; topic?: string; search?: string }) => void;
}

const TOPIC_LABELS: Record<string, string> = {
  product: "Product & Architecture",
  features: "Features & Capabilities",
  pricing: "Pricing & Plans",
  quality: "Quality & Performance",
  customer_service: "Customer Support",
  complaints: "Complaints & Issues",
  competitors: "Competitor Comparison",
  other: "General & Community",
  // Fallbacks
  pricing_billing: "Pricing & Plans",
  customer_support: "Customer Support",
  bug_issue: "Complaints & Issues",
  feature_request: "Features & Capabilities",
  performance: "Quality & Performance",
  onboarding_setup: "Onboarding & UX",
  general_feedback: "General Feedback",
};

export function OverviewTab({
  stats,
  timeseries,
  loading,
  onRefresh,
  onSelectSearchTerm,
  onSelectFilter,
}: OverviewTabProps) {
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

  const {
    total_mentions = 0,
    sentiment,
    top_topics = [],
    quality = { total_collected: 0, total_kept: 0, total_dropped: 0, drop_reasons: {} },
    sources = {},
  } = stats || {};

  const safeSentiment = {
    positive: sentiment?.positive ?? 0,
    neutral: sentiment?.neutral ?? 0,
    negative: sentiment?.negative ?? 0,
    positive_pct: sentiment?.positive_pct ?? 0,
    neutral_pct: sentiment?.neutral_pct ?? 0,
    negative_pct: sentiment?.negative_pct ?? 0,
    net_sentiment: sentiment?.net_sentiment ?? 0,
  };

  // Compute Brand Reputation Health Index (NPS-style Score: 0-100)
  const posPct = safeSentiment.positive_pct;
  const negPct = safeSentiment.negative_pct;
  const neuPct = safeSentiment.neutral_pct;
  const netSentimentScore = Math.round(posPct - negPct);
  const healthScore = Math.min(100, Math.max(0, Math.round(50 + netSentimentScore / 2)));

  let healthTier = {
    label: "Healthy & Stable",
    color: "text-emerald-400",
    border: "border-emerald-500/40",
    bg: "bg-emerald-500/10",
    desc: "Positive brand sentiment comfortably exceeds negative friction across community discussions.",
  };

  if (healthScore >= 75) {
    healthTier = {
      label: "Outstanding Perception",
      color: "text-emerald-300",
      border: "border-emerald-500/50",
      bg: "bg-emerald-500/15",
      desc: "Overwhelmingly favorable community reception with high recommendation velocity.",
    };
  } else if (healthScore < 45) {
    healthTier = {
      label: "At Risk / High Friction",
      color: "text-rose-400",
      border: "border-rose-500/50",
      bg: "bg-rose-500/15",
      desc: "Negative discussion volume warrants urgent customer success and PR triage.",
    };
  } else if (healthScore < 55) {
    healthTier = {
      label: "Balanced / Neutral",
      color: "text-slate-300",
      border: "border-slate-500/40",
      bg: "bg-slate-500/10",
      desc: "Even distribution of feedback with no dominant sentiment bias.",
    };
  }

  // Dynamic Voice of Customer (VoC) Drivers derived directly from active keyword data
  const positiveDrivers: Array<{
    label: string;
    count: number;
    filter: { topic?: string; sentiment?: string; search?: string };
  }> = [];

  // 1. High praise overall if positive mentions exist
  if (safeSentiment.positive > 0) {
    positiveDrivers.push({
      label: "General Praise & Endorsements",
      count: safeSentiment.positive,
      filter: { sentiment: "positive" },
    });
  }

  // 2. Add positive-leaning topics that actually exist in the data
  const positiveTopicCandidates = [
    { key: "features", label: "Features & Capabilities" },
    { key: "quality", label: "Quality & Reliability" },
    { key: "product", label: "Product & Architecture" },
    { key: "customer_service", label: "Support Experience" },
    { key: "pricing", label: "Value & Pricing" },
  ];

  for (const cand of positiveTopicCandidates) {
    const found = top_topics.find((t) => t.topic === cand.key);
    if (found && found.count > 0) {
      positiveDrivers.push({
        label: cand.label,
        count: found.count,
        filter: { topic: cand.key },
      });
    }
  }

  if (positiveDrivers.length === 0) {
    positiveDrivers.push({
      label: "Community Feedback",
      count: safeSentiment.positive || total_mentions,
      filter: { sentiment: "positive" },
    });
  }

  const frictionPoints: Array<{
    label: string;
    count: number;
    filter: { topic?: string; sentiment?: string; search?: string };
  }> = [];

  // 1. Critical negatives if negative mentions exist
  if (safeSentiment.negative > 0) {
    frictionPoints.push({
      label: "Urgent Negative Feedback",
      count: safeSentiment.negative,
      filter: { sentiment: "negative" },
    });
  }

  // 2. Friction topics that actually exist in data
  const frictionTopicCandidates = [
    { key: "complaints", label: "Complaints & Bug Reports" },
    { key: "pricing", label: "Cost & Pricing Concerns" },
    { key: "customer_service", label: "Customer Support Friction" },
    { key: "competitors", label: "Competitor Comparison" },
    { key: "quality", label: "Performance Deficits" },
  ];

  for (const cand of frictionTopicCandidates) {
    const found = top_topics.find((t) => t.topic === cand.key);
    if (found && found.count > 0 && !frictionPoints.some((f) => f.label === cand.label)) {
      frictionPoints.push({
        label: cand.label,
        count: found.count,
        filter: { topic: cand.key },
      });
    }
  }

  if (frictionPoints.length === 0 && safeSentiment.negative > 0) {
    frictionPoints.push({
      label: "Critical Mentions",
      count: safeSentiment.negative,
      filter: { sentiment: "negative" },
    });
  }

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
              {posPct.toFixed(1)}%
            </span>
            <span className="text-xs text-slate-400">({safeSentiment.positive} items)</span>
          </div>
          <div className="w-full bg-slate-800 rounded-full h-1.5 mt-3 overflow-hidden">
            <div
              className="bg-emerald-500 h-1.5 rounded-full"
              style={{ width: `${Math.min(100, posPct)}%` }}
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
              {neuPct.toFixed(1)}%
            </span>
            <span className="text-xs text-slate-400">({safeSentiment.neutral} items)</span>
          </div>
          <div className="w-full bg-slate-800 rounded-full h-1.5 mt-3 overflow-hidden">
            <div
              className="bg-slate-400 h-1.5 rounded-full"
              style={{ width: `${Math.min(100, neuPct)}%` }}
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
              {negPct.toFixed(1)}%
            </span>
            <span className="text-xs text-slate-400">({safeSentiment.negative} items)</span>
          </div>
          <div className="w-full bg-slate-800 rounded-full h-1.5 mt-3 overflow-hidden">
            <div
              className="bg-rose-500 h-1.5 rounded-full"
              style={{ width: `${Math.min(100, negPct)}%` }}
            />
          </div>
        </div>
      </div>

      {/* Brand Reputation Health Index Card (BON-02 / Enterprise Score) */}
      <div className="glass-card rounded-2xl p-6 relative overflow-hidden border border-slate-700/80 bg-gradient-to-r from-slate-900 via-indigo-950/20 to-slate-900 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Award className="h-5 w-5 text-indigo-400" />
              <h3 className="text-sm font-bold text-white tracking-wide">
                Brand Reputation Health Index (NPS Normalized)
              </h3>
              <span
                className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full uppercase tracking-wider border ${healthTier.border} ${healthTier.bg} ${healthTier.color}`}
              >
                {healthTier.label}
              </span>
            </div>
            <p className="text-xs text-slate-300 max-w-xl leading-relaxed">{healthTier.desc}</p>
          </div>

          {/* Metric Meters */}
          <div className="flex items-center gap-6 shrink-0">
            {/* Health Score Gauge */}
            <div className="flex flex-col items-center">
              <div className="flex items-baseline gap-1">
                <span className="text-4xl font-extrabold text-white font-mono">{healthScore}</span>
                <span className="text-xs text-slate-400 font-semibold">/100</span>
              </div>
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mt-0.5">
                Reputation Score
              </span>
            </div>

            <div className="h-10 w-px bg-slate-800" />

            {/* Net Sentiment Score */}
            <div className="flex flex-col items-center">
              <div className="flex items-baseline gap-1">
                <span
                  className={`text-4xl font-extrabold font-mono ${
                    netSentimentScore >= 0 ? "text-emerald-400" : "text-rose-400"
                  }`}
                >
                  {netSentimentScore >= 0 ? `+${netSentimentScore}` : netSentimentScore}
                </span>
                <span className="text-xs text-slate-400 font-semibold">pts</span>
              </div>
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mt-0.5">
                Net Sentiment (NSS)
              </span>
            </div>
          </div>
        </div>

        {/* Progress Spectrum Bar */}
        <div className="mt-4 pt-3 border-t border-slate-800/80">
          <div className="flex justify-between text-[11px] text-slate-400 mb-1.5 font-mono">
            <span>Critical Friction (0)</span>
            <span>Balanced Neutral (50)</span>
            <span>High Advocacy (100)</span>
          </div>
          <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden flex shadow-inner">
            <div
              className={`h-full transition-all duration-700 ${
                healthScore >= 60 ? "bg-emerald-500" : healthScore >= 45 ? "bg-indigo-500" : "bg-rose-500"
              }`}
              style={{ width: `${healthScore}%` }}
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
                  <button
                    key={idx}
                    type="button"
                    onClick={() => {
                      if (onSelectFilter) {
                        onSelectFilter({ topic: item.topic });
                      } else {
                        onSelectSearchTerm?.(item.topic);
                      }
                    }}
                    title={`Click to filter mentions by topic: ${label}`}
                    className="w-full text-left space-y-1 group hover:bg-slate-800/60 p-1.5 rounded-xl transition-all cursor-pointer block"
                  >
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-300 group-hover:text-indigo-300 font-medium truncate max-w-[170px] transition-colors">
                        {label}
                      </span>
                      <span className="text-slate-400 font-mono text-[11px]">
                        {item.count} ({item.percentage}%)
                      </span>
                    </div>
                    <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                      <div
                        className="bg-gradient-to-r from-indigo-500 to-violet-500 h-1.5 rounded-full group-hover:from-indigo-400 group-hover:to-violet-400 transition-all"
                        style={{ width: `${Math.min(100, item.percentage)}%` }}
                      />
                    </div>
                  </button>
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

      {/* Voice of Customer (VoC) Interactive Buzzword Cloud */}
      <div className="glass-card rounded-2xl p-6 border border-slate-800/80">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4 pb-3 border-b border-slate-800/80">
          <div>
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-amber-400" />
              <h3 className="text-sm font-semibold text-white">
                Voice of Customer (VoC) Theme Cloud
              </h3>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Click any buzzword to instantly filter the Mentions feed and inspect live mentions.
            </p>
          </div>
          <span className="text-[11px] text-slate-400 font-mono">
            {total_mentions} mentions analyzed
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Positive Praise Drivers */}
          <div className="space-y-2">
            <span className="text-[11px] font-bold text-emerald-400 uppercase tracking-wider block">
              Key Positive Drivers (Praise)
            </span>
            <div className="flex flex-wrap gap-2">
              {positiveDrivers.map((item, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    if (onSelectFilter) {
                      onSelectFilter(item.filter);
                    } else {
                      onSelectSearchTerm?.(item.filter.topic || item.filter.search || item.label);
                    }
                  }}
                  title={`Click to filter mentions for "${item.label}"`}
                  className="group flex items-center gap-2 px-3 py-1.5 rounded-xl bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 text-xs text-emerald-300 hover:text-white transition-all shadow-sm cursor-pointer"
                >
                  <span className="font-medium">{item.label}</span>
                  <span className="px-1.5 py-0.2 rounded bg-emerald-500/20 text-emerald-300 font-mono text-[10px] group-hover:bg-emerald-500/40">
                    +{item.count}
                  </span>
                </button>
              ))}
            </div>
          </div>

          {/* Friction Points & Complaints */}
          <div className="space-y-2">
            <span className="text-[11px] font-bold text-rose-400 uppercase tracking-wider block">
              Friction Points & Complaints
            </span>
            <div className="flex flex-wrap gap-2">
              {frictionPoints.map((item, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    if (onSelectFilter) {
                      onSelectFilter(item.filter);
                    } else {
                      onSelectSearchTerm?.(item.filter.topic || item.filter.search || item.label);
                    }
                  }}
                  title={`Click to filter mentions for "${item.label}"`}
                  className="group flex items-center gap-2 px-3 py-1.5 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/30 text-xs text-rose-300 hover:text-white transition-all shadow-sm cursor-pointer"
                >
                  <span className="font-medium">{item.label}</span>
                  <span className="px-1.5 py-0.2 rounded bg-rose-500/20 text-rose-300 font-mono text-[10px] group-hover:bg-rose-500/40">
                    {item.count}
                  </span>
                </button>
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
