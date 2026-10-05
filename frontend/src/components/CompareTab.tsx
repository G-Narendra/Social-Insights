"use client";

import React, { useState } from "react";
import {
  AlertCircle,
  Award,
  BarChart2,
  CheckCircle2,
  Download,
  GitCompare,
  PieChart,
  Plus,
  RefreshCw,
  Sparkles,
  TrendingDown,
  TrendingUp,
  X,
} from "lucide-react";
import { CompetitorComparisonResponse, CompetitorStats } from "@/lib/types";
import { api } from "@/lib/api";

interface CompareTabProps {
  initialKeyword: string;
}

export function CompareTab({ initialKeyword }: CompareTabProps) {
  const [competitors, setCompetitors] = useState<string[]>([
    initialKeyword || "Toyota",
    "Honda",
    "Tesla",
  ]);
  const [newBrandInput, setNewBrandInput] = useState("");
  const [data, setData] = useState<CompetitorComparisonResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchComparison = async (brandsToCompare: string[]) => {
    if (brandsToCompare.length < 2) {
      setError("Please add at least 2 brands to compare.");
      return;
    }
    try {
      setLoading(true);
      setError(null);
      const res = await api.compareKeywords(brandsToCompare);
      setData(res);
    } catch (err: any) {
      setError(err.message || "Failed to compare competitors");
    } finally {
      setLoading(false);
    }
  };

  const handleAddBrand = () => {
    const trimmed = newBrandInput.trim();
    if (trimmed && !competitors.map((c) => c.toLowerCase()).includes(trimmed.toLowerCase())) {
      const nextList = [...competitors, trimmed];
      setCompetitors(nextList);
      setNewBrandInput("");
      fetchComparison(nextList);
    }
  };

  const handleRemoveBrand = (brand: string) => {
    const nextList = competitors.filter((b) => b.toLowerCase() !== brand.toLowerCase());
    setCompetitors(nextList);
    if (nextList.length >= 2) {
      fetchComparison(nextList);
    } else {
      setData(null);
    }
  };

  React.useEffect(() => {
    if (competitors.length >= 2) {
      fetchComparison(competitors);
    }
  }, []);

  // Compute Share of Voice & Leader Metrics
  const validCompetitors = data?.competitors || [];
  const totalVolumeAcrossAll = validCompetitors.reduce((acc, c) => acc + (c.total_mentions || 0), 0);

  // Find leader by Net Sentiment (Positive% - Negative%)
  const leader = validCompetitors
    .filter((c) => (c.total_mentions || 0) > 0)
    .map((c) => {
      const pos = c.sentiment?.positive_pct ?? c.positive_pct ?? 0;
      const neg = c.sentiment?.negative_pct ?? c.negative_pct ?? 0;
      return { brand: c.keyword, netScore: pos - neg, mentions: c.total_mentions };
    })
    .sort((a, b) => b.netScore - a.netScore)[0];

  const handleExportCSV = () => {
    if (!validCompetitors.length) return;
    const headers = ["Brand", "Total Mentions", "Share of Voice %", "Positive %", "Neutral %", "Negative %", "Net Score"];
    const rows = validCompetitors.map((c) => {
      const pos = c.sentiment?.positive_pct ?? c.positive_pct ?? 0;
      const neu = c.sentiment?.neutral_pct ?? c.neutral_pct ?? 0;
      const neg = c.sentiment?.negative_pct ?? c.negative_pct ?? 0;
      const sov = totalVolumeAcrossAll > 0 ? ((c.total_mentions / totalVolumeAcrossAll) * 100).toFixed(1) : "0.0";
      return [c.keyword, c.total_mentions, `${sov}%`, `${pos.toFixed(1)}%`, `${neu.toFixed(1)}%`, `${neg.toFixed(1)}%`, (pos - neg).toFixed(1)];
    });

    const csvContent = [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
    const blob = new Blob([csvContent], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `brand-comparison-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      {/* Brands Selector */}
      <div className="glass-card rounded-2xl p-5 border-indigo-500/20">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <GitCompare className="h-5 w-5 text-indigo-400" />
                Multi-Brand Competitor Intelligence
              </h3>
              <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                BON-02
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Side-by-side volume, Share of Voice (SOV), sentiment distribution, and customer complaints
            </p>
          </div>

          <div className="flex items-center gap-2 self-start sm:self-center">
            {validCompetitors.length > 0 && (
              <button
                onClick={handleExportCSV}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 border border-slate-700 transition-all"
              >
                <Download className="h-3.5 w-3.5 text-slate-300" />
                <span>Export CSV</span>
              </button>
            )}

            <button
              onClick={() => fetchComparison(competitors)}
              disabled={loading}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 active:scale-95 text-xs font-semibold text-white shadow-md shadow-indigo-600/20 transition-all disabled:opacity-50"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin text-white" : ""}`} />
              <span>{loading ? "Analyzing..." : "Re-run Analysis"}</span>
            </button>
          </div>
        </div>

        {/* Selected brands pills */}
        <div className="flex flex-wrap items-center gap-2">
          {competitors.map((brand) => (
            <span
              key={brand}
              className="inline-flex items-center gap-1.5 px-3 py-1 rounded-xl bg-indigo-500/15 border border-indigo-500/40 text-indigo-200 text-xs font-semibold shadow-sm"
            >
              <span>{brand}</span>
              <button
                onClick={() => handleRemoveBrand(brand)}
                className="hover:text-rose-400 transition-colors p-0.5"
                title={`Remove ${brand}`}
              >
                <X className="h-3 w-3" />
              </button>
            </span>
          ))}

          {/* Add brand input */}
          <div className="flex items-center bg-slate-900 border border-slate-700 rounded-xl px-2.5 py-1 focus-within:border-indigo-500 transition-colors">
            <input
              type="text"
              placeholder="Add competitor..."
              value={newBrandInput}
              onChange={(e) => setNewBrandInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleAddBrand()}
              className="bg-transparent text-xs text-white placeholder-slate-500 focus:outline-none w-32"
            />
            <button
              onClick={handleAddBrand}
              className="p-1 text-slate-400 hover:text-indigo-400 transition-colors"
              title="Add Brand"
            >
              <Plus className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>

        {error && (
          <div className="mt-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs text-rose-300 flex items-center gap-2">
            <AlertCircle className="h-4 w-4 shrink-0 text-rose-400" />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* Brand Leadership Scorecard Banner */}
      {leader && (
        <div className="p-4 rounded-2xl bg-gradient-to-r from-emerald-500/10 via-indigo-500/10 to-violet-500/10 border border-emerald-500/30 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400 shadow-md">
              <Award className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs uppercase font-bold tracking-wider text-emerald-400">Brand Sentiment Leader</span>
                <span className="text-[10px] px-2 py-0.2 rounded-full bg-emerald-500/20 text-emerald-300 font-mono font-bold">
                  Net Score: {leader.netScore >= 0 ? `+${leader.netScore.toFixed(0)}%` : `${leader.netScore.toFixed(0)}%`}
                </span>
              </div>
              <h4 className="text-sm font-bold text-white mt-0.5">
                {leader.brand} leads the comparative cohort across {leader.mentions} analyzed public discussions.
              </h4>
            </div>
          </div>

          {/* Share of Voice Progress */}
          {totalVolumeAcrossAll > 0 && (
            <div className="text-xs text-slate-400">
              <span className="font-semibold text-slate-200">{totalVolumeAcrossAll}</span> total mentions analyzed across {validCompetitors.length} brands
            </div>
          )}
        </div>
      )}

      {/* Comparative Cards Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 animate-pulse">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-72 bg-slate-800/40 rounded-2xl border border-slate-700/50" />
          ))}
        </div>
      ) : validCompetitors.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {validCompetitors.map((comp) => {
            const hasData = (comp.total_mentions || 0) > 0;
            const posPct = comp.sentiment?.positive_pct ?? comp.positive_pct ?? 0;
            const neuPct = comp.sentiment?.neutral_pct ?? comp.neutral_pct ?? 0;
            const negPct = comp.sentiment?.negative_pct ?? comp.negative_pct ?? 0;
            const sovPct = totalVolumeAcrossAll > 0 ? ((comp.total_mentions / totalVolumeAcrossAll) * 100).toFixed(1) : "0.0";
            const complaints = comp.common_complaints || comp.top_complaint_themes || [];
            const topics = comp.top_topics || [];

            return (
              <div
                key={comp.keyword}
                className="glass-card rounded-2xl p-5 flex flex-col justify-between border-slate-700/60 hover:border-slate-600 transition-all"
              >
                <div>
                  <div className="flex items-center justify-between pb-3 border-b border-slate-800/80 mb-4">
                    <div>
                      <h4 className="text-base font-bold text-white tracking-tight">{comp.keyword}</h4>
                      <p className="text-[11px] text-slate-400 font-mono">Share of Voice: {sovPct}%</p>
                    </div>
                    <span className="text-xs font-mono font-semibold text-indigo-300 bg-indigo-500/10 border border-indigo-500/20 px-2.5 py-1 rounded-xl">
                      {comp.total_mentions} mentions
                    </span>
                  </div>

                  {hasData ? (
                    <div className="space-y-4">
                      {/* Sentiment distribution bar */}
                      <div>
                        <div className="flex justify-between text-xs text-slate-400 mb-1.5 font-mono">
                          <span className="text-emerald-400 font-semibold">{posPct.toFixed(0)}% Pos</span>
                          <span className="text-slate-300">{neuPct.toFixed(0)}% Neu</span>
                          <span className="text-rose-400 font-semibold">{negPct.toFixed(0)}% Neg</span>
                        </div>
                        <div className="h-2 w-full rounded-full bg-slate-800 overflow-hidden flex shadow-inner">
                          <div
                            className="bg-emerald-500 h-full transition-all"
                            style={{ width: `${Math.max(posPct, 2)}%` }}
                            title={`Positive: ${posPct.toFixed(1)}%`}
                          />
                          <div
                            className="bg-slate-400 h-full transition-all"
                            style={{ width: `${neuPct}%` }}
                            title={`Neutral: ${neuPct.toFixed(1)}%`}
                          />
                          <div
                            className="bg-rose-500 h-full transition-all"
                            style={{ width: `${negPct}%` }}
                            title={`Negative: ${negPct.toFixed(1)}%`}
                          />
                        </div>
                      </div>

                      {/* Top topics */}
                      <div>
                        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-2">
                          Top Discussion Topics
                        </span>
                        <div className="space-y-1.5">
                          {topics.slice(0, 3).map((t, idx) => {
                            const name = typeof t === "string" ? t : (t as any).topic || "Topic";
                            const pct = typeof t === "string" ? null : (t as any).percentage ?? null;
                            return (
                              <div
                                key={idx}
                                className="flex items-center justify-between text-xs text-slate-300 bg-slate-900/60 border border-slate-800/80 px-2.5 py-1 rounded-xl"
                              >
                                <span className="capitalize">{name.replace(/_/g, " ")}</span>
                                {pct !== null && (
                                  <span className="font-mono text-slate-400 text-[11px] font-semibold">{pct}%</span>
                                )}
                              </div>
                            );
                          })}
                          {topics.length === 0 && (
                            <span className="text-xs text-slate-500 italic">No topic clusters detected</span>
                          )}
                        </div>
                      </div>

                      {/* Top complaints */}
                      <div>
                        <span className="text-[10px] font-bold text-rose-400 uppercase tracking-wider block mb-2">
                          Common Complaints
                        </span>
                        <div className="space-y-1.5">
                          {complaints.slice(0, 2).map((c, idx) => (
                            <div
                              key={idx}
                              className="text-xs text-rose-300/90 bg-rose-500/10 border border-rose-500/20 px-2.5 py-1.5 rounded-xl line-clamp-2 leading-relaxed"
                            >
                              • {c}
                            </div>
                          ))}
                          {complaints.length === 0 && (
                            <span className="text-xs text-slate-500 italic">No negative complaints recorded</span>
                          )}
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="py-10 text-center text-xs text-slate-400 flex flex-col items-center justify-center gap-2">
                      <Sparkles className="h-6 w-6 text-slate-600 mb-1" />
                      <p className="font-medium text-slate-300">No public mentions ingested yet</p>
                      <p className="text-[11px] text-slate-500 max-w-[200px]">
                        Click "Collect Mentions" in the top bar to pull live data for {comp.keyword}.
                      </p>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      ) : null}
    </div>
  );
}
