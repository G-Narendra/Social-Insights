"use client";

import React, { useState } from "react";
import {
  AlertCircle,
  AlertTriangle,
  Bot,
  CheckCircle2,
  Cpu,
  FileText,
  HelpCircle,
  Lightbulb,
  RefreshCw,
  Sparkles,
  ThumbsUp,
  Zap,
} from "lucide-react";
import { InsightItem, SummaryResponse } from "@/lib/types";

interface InsightsTabProps {
  summary: SummaryResponse | null;
  loading: boolean;
  onRefreshSummary: () => Promise<void>;
}

export function InsightsTab({ summary, loading, onRefreshSummary }: InsightsTabProps) {
  const [refreshing, setRefreshing] = useState(false);

  const handleRefresh = async () => {
    try {
      setRefreshing(true);
      await onRefreshSummary();
    } finally {
      setRefreshing(false);
    }
  };

  if (loading && !summary) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-48 bg-slate-800/40 rounded-2xl border border-slate-700/50" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-44 bg-slate-800/40 rounded-2xl border border-slate-700/50" />
          ))}
        </div>
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="glass-card rounded-2xl p-12 text-center">
        <Sparkles className="h-10 w-10 text-indigo-400 mx-auto mb-3" />
        <h3 className="text-base font-semibold text-white">No AI summary generated yet</h3>
        <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto">
          Collect mentions for this keyword first to allow the tiered intelligence engine to synthesize insights.
        </p>
      </div>
    );
  }

  const { content, method, model_name, created_at, insights } = summary;

  return (
    <div className="space-y-6">
      {/* Executive Summary Card */}
      <div className="glass-card rounded-2xl p-6 relative overflow-hidden border-indigo-500/20">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <Bot className="h-5 w-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-white tracking-tight">Executive AI Synthesis</h3>
                {/* Method Badge */}
                {method === "llm" ? (
                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/30">
                    <Sparkles className="h-3 w-3" />
                    AI: {model_name || "NVIDIA NIM Llama 3.1"}
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-slate-700/40 text-slate-300 border border-slate-600/40">
                    <Cpu className="h-3 w-3" />
                    Template Fallback (Offline Tier 3)
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Generated {new Date(created_at).toLocaleDateString()} at{" "}
                {new Date(created_at).toLocaleTimeString()}
              </p>
            </div>
          </div>

          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 active:scale-95 text-xs text-slate-200 font-semibold border border-slate-700 disabled:opacity-50 transition-all self-start sm:self-center"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${refreshing ? "animate-spin text-indigo-400" : ""}`} />
            <span>{refreshing ? "Synthesizing..." : "Refresh Summary"}</span>
          </button>
        </div>

        {/* Synthesis Text */}
        <div className="mt-5 prose prose-invert max-w-none text-slate-200 text-sm leading-relaxed whitespace-pre-line font-normal">
          {content}
        </div>
      </div>

      {/* Structured Intelligence Grid */}
      {insights && (
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <Lightbulb className="h-4 w-4 text-amber-400" />
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-300">
              Structured Product Intelligence
            </h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Emerging Complaints */}
            <div className="glass-card rounded-2xl p-5 border-rose-500/20">
              <div className="flex items-center gap-2 text-rose-400 mb-3">
                <AlertTriangle className="h-4 w-4" />
                <h4 className="text-xs font-bold uppercase tracking-wider">Emerging Complaints</h4>
              </div>
              <div className="space-y-3">
                {insights.emerging_complaints.map((item, idx) => (
                  <InsightCard key={idx} item={item} accent="rose" />
                ))}
                {insights.emerging_complaints.length === 0 && (
                  <p className="text-xs text-slate-400">No severe emerging complaints detected.</p>
                )}
              </div>
            </div>

            {/* Requested Features */}
            <div className="glass-card rounded-2xl p-5 border-indigo-500/20">
              <div className="flex items-center gap-2 text-indigo-400 mb-3">
                <Zap className="h-4 w-4" />
                <h4 className="text-xs font-bold uppercase tracking-wider">Requested Features</h4>
              </div>
              <div className="space-y-3">
                {insights.requested_features.map((item, idx) => (
                  <InsightCard key={idx} item={item} accent="indigo" />
                ))}
                {insights.requested_features.length === 0 && (
                  <p className="text-xs text-slate-400">No specific feature requests detected.</p>
                )}
              </div>
            </div>

            {/* Pain Points */}
            <div className="glass-card rounded-2xl p-5 border-amber-500/20">
              <div className="flex items-center gap-2 text-amber-400 mb-3">
                <AlertCircle className="h-4 w-4" />
                <h4 className="text-xs font-bold uppercase tracking-wider">Core Pain Points</h4>
              </div>
              <div className="space-y-3">
                {insights.pain_points.map((item, idx) => (
                  <InsightCard key={idx} item={item} accent="amber" />
                ))}
                {insights.pain_points.length === 0 && (
                  <p className="text-xs text-slate-400">No recurring pain points logged.</p>
                )}
              </div>
            </div>

            {/* Positive Themes */}
            <div className="glass-card rounded-2xl p-5 border-emerald-500/20">
              <div className="flex items-center gap-2 text-emerald-400 mb-3">
                <ThumbsUp className="h-4 w-4" />
                <h4 className="text-xs font-bold uppercase tracking-wider">Positive Praises & Themes</h4>
              </div>
              <div className="space-y-3">
                {insights.positive_themes.map((item, idx) => (
                  <InsightCard key={idx} item={item} accent="emerald" />
                ))}
                {insights.positive_themes.length === 0 && (
                  <p className="text-xs text-slate-400">No recurring praise themes detected.</p>
                )}
              </div>
            </div>
          </div>

          {/* Strategic Opportunities */}
          {insights.opportunities && insights.opportunities.length > 0 && (
            <div className="glass-card rounded-2xl p-5 border-violet-500/20 mt-4">
              <div className="flex items-center gap-2 text-violet-400 mb-3">
                <Lightbulb className="h-4 w-4" />
                <h4 className="text-xs font-bold uppercase tracking-wider">
                  Market & Growth Opportunities
                </h4>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {insights.opportunities.map((item, idx) => (
                  <InsightCard key={idx} item={item} accent="violet" />
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function InsightCard({
  item,
  accent,
}: {
  item: InsightItem;
  accent: "rose" | "indigo" | "amber" | "emerald" | "violet";
}) {
  const borderColors = {
    rose: "hover:border-rose-500/40",
    indigo: "hover:border-indigo-500/40",
    amber: "hover:border-amber-500/40",
    emerald: "hover:border-emerald-500/40",
    violet: "hover:border-violet-500/40",
  };

  return (
    <div
      className={`p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 transition-colors ${borderColors[accent]}`}
    >
      <div className="flex items-start justify-between gap-2">
        <h5 className="text-xs font-semibold text-white tracking-tight">{item.title}</h5>
        {item.volume ? (
          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
            {item.volume} mentions
          </span>
        ) : null}
      </div>
      <p className="text-xs text-slate-300 mt-1 leading-relaxed">{item.description}</p>
      {item.evidence_mention_ids && item.evidence_mention_ids.length > 0 && (
        <div className="mt-2 text-[10px] text-slate-500 flex items-center gap-1 font-mono">
          <span>Cited mentions:</span>
          <span>{item.evidence_mention_ids.slice(0, 4).join(", ")}</span>
        </div>
      )}
    </div>
  );
}
