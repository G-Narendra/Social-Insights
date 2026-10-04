"use client";

import React, { useState } from "react";
import {
  AlertCircle,
  ArrowRight,
  BarChart,
  GitCompare,
  Plus,
  RefreshCw,
  TrendingDown,
  TrendingUp,
  X,
} from "lucide-react";
import { CompetitorComparisonResponse } from "@/lib/types";
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
    if (trimmed && !competitors.includes(trimmed)) {
      const nextList = [...competitors, trimmed];
      setCompetitors(nextList);
      setNewBrandInput("");
      fetchComparison(nextList);
    }
  };

  const handleRemoveBrand = (brand: string) => {
    const nextList = competitors.filter((b) => b !== brand);
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

  return (
    <div className="space-y-6">
      {/* Brands Selector */}
      <div className="glass-card rounded-2xl p-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
          <div>
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <GitCompare className="h-4 w-4 text-indigo-400" />
              Competitor Benchmark (BON-02)
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Compare brand volume, sentiment distribution, and customer complaints side-by-side
            </p>
          </div>

          <button
            onClick={() => fetchComparison(competitors)}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 border border-slate-700 self-start sm:self-center disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin text-indigo-400" : ""}`} />
            <span>Re-run Comparison</span>
          </button>
        </div>

        {/* Selected brands pills */}
        <div className="flex flex-wrap items-center gap-2">
          {competitors.map((brand) => (
            <span
              key={brand}
              className="inline-flex items-center gap-1.5 px-3 py-1 rounded-xl bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-xs font-semibold"
            >
              <span>{brand}</span>
              <button
                onClick={() => handleRemoveBrand(brand)}
                className="hover:text-rose-400 transition-colors"
              >
                <X className="h-3 w-3" />
              </button>
            </span>
          ))}

          {/* Add brand input */}
          <div className="flex items-center bg-slate-900 border border-slate-700 rounded-xl px-2 py-1">
            <input
              type="text"
              placeholder="Add competitor..."
              value={newBrandInput}
              onChange={(e) => setNewBrandInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleAddBrand()}
              className="bg-transparent text-xs text-white placeholder-slate-400 focus:outline-none w-28"
            />
            <button
              onClick={handleAddBrand}
              className="p-1 text-slate-400 hover:text-indigo-400 transition-colors"
            >
              <Plus className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>

        {error && (
          <div className="mt-3 p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs text-rose-400 flex items-center gap-2">
            <AlertCircle className="h-4 w-4" />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* Comparison Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 animate-pulse">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-72 bg-slate-800/40 rounded-2xl border border-slate-700/50" />
          ))}
        </div>
      ) : data && data.competitors.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {data.competitors.map((comp) => {
            const hasData = comp.total_mentions > 0;
            return (
              <div
                key={comp.keyword}
                className="glass-card rounded-2xl p-5 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between pb-3 border-b border-slate-800/80 mb-4">
                    <h4 className="text-base font-bold text-white tracking-tight">{comp.keyword}</h4>
                    <span className="text-xs font-mono text-slate-400 bg-slate-800 px-2 py-0.5 rounded-md">
                      {comp.total_mentions} mentions
                    </span>
                  </div>

                  {hasData ? (
                    <div className="space-y-4">
                      {/* Sentiment distribution bar */}
                      <div>
                        <div className="flex justify-between text-xs text-slate-400 mb-1.5">
                          <span className="text-emerald-400 font-semibold">
                            {comp.sentiment.positive_pct.toFixed(0)}% Pos
                          </span>
                          <span className="text-slate-300">
                            {comp.sentiment.neutral_pct.toFixed(0)}% Neu
                          </span>
                          <span className="text-rose-400 font-semibold">
                            {comp.sentiment.negative_pct.toFixed(0)}% Neg
                          </span>
                        </div>
                        <div className="h-2 w-full rounded-full bg-slate-800 overflow-hidden flex">
                          <div
                            className="bg-emerald-500 h-full"
                            style={{ width: `${comp.sentiment.positive_pct}%` }}
                          />
                          <div
                            className="bg-slate-400 h-full"
                            style={{ width: `${comp.sentiment.neutral_pct}%` }}
                          />
                          <div
                            className="bg-rose-500 h-full"
                            style={{ width: `${comp.sentiment.negative_pct}%` }}
                          />
                        </div>
                      </div>

                      {/* Top topics */}
                      <div>
                        <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-2">
                          Top Discussion Topics
                        </span>
                        <div className="space-y-1.5">
                          {comp.top_topics.slice(0, 3).map((t, idx) => (
                            <div
                              key={idx}
                              className="flex items-center justify-between text-xs text-slate-300 bg-slate-900/60 px-2.5 py-1 rounded-lg"
                            >
                              <span className="capitalize">{t.topic.replace(/_/g, " ")}</span>
                              <span className="font-mono text-slate-400 text-[11px]">{t.percentage}%</span>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Top complaints */}
                      <div>
                        <span className="text-[11px] font-semibold text-rose-400 uppercase tracking-wider block mb-2">
                          Frequent Complaint Themes
                        </span>
                        <div className="space-y-1">
                          {comp.top_complaint_themes.slice(0, 3).map((c, idx) => (
                            <div
                              key={idx}
                              className="text-xs text-rose-300/90 bg-rose-500/10 border border-rose-500/20 px-2.5 py-1 rounded-lg truncate"
                            >
                              • {c}
                            </div>
                          ))}
                          {comp.top_complaint_themes.length === 0 && (
                            <span className="text-xs text-slate-400">None detected</span>
                          )}
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="py-8 text-center text-xs text-slate-400">
                      No mentions collected for {comp.keyword} yet. Collect mentions to see metrics.
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
