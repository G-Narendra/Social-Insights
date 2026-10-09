"use client";

import React, { useState } from "react";
import {
  AlertCircle,
  Calendar,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Download,
  ExternalLink,
  FileSpreadsheet,
  FileText,
  Filter,
  Flame,
  MessageSquare,
  Search,
  Sparkles,
  Tag,
  User,
  X,
} from "lucide-react";
import { Mention, MentionsPage, Sentiment, Topic } from "@/lib/types";

interface MentionsTabProps {
  data: MentionsPage | null;
  loading: boolean;
  filters: {
    search: string;
    sentiment: string;
    topic: string;
    source: string;
    page: number;
    limit: number;
  };
  onFilterChange: (newFilters: Partial<MentionsTabProps["filters"]>) => void;
}

const TOPICS = [
  { value: "", label: "All Topics" },
  { value: "product", label: "Product & Architecture" },
  { value: "features", label: "Features & Specs" },
  { value: "pricing", label: "Pricing & Plans" },
  { value: "quality", label: "Quality & Reliability" },
  { value: "customer_service", label: "Customer Support" },
  { value: "complaints", label: "Complaints & Bugs" },
  { value: "competitors", label: "Competitor Comparison" },
  { value: "other", label: "General & Community" },
];

const TOPIC_LABELS: Record<string, string> = {
  product: "Product & Architecture",
  features: "Features & Specs",
  pricing: "Pricing & Plans",
  quality: "Quality & Reliability",
  customer_service: "Customer Support",
  complaints: "Complaints & Bugs",
  competitors: "Competitor Comparison",
  other: "General & Community",
  // Fallbacks
  pricing_billing: "Pricing & Plans",
  bug_issue: "Complaints & Bugs",
  feature_request: "Features & Specs",
  performance: "Quality & Reliability",
  onboarding_setup: "Onboarding & UX",
  general_feedback: "General Feedback",
};

const SOURCES = [
  { value: "", label: "All Sources" },
  { value: "hackernews", label: "Hacker News" },
  { value: "googlenews", label: "Google News" },
  { value: "wikipedia", label: "Wikipedia" },
  { value: "linkedin", label: "LinkedIn / Wire" },
  { value: "github", label: "GitHub" },
  { value: "reddit", label: "Reddit" },
  { value: "youtube", label: "YouTube" },
  { value: "stackexchange", label: "Stack Exchange" },
];

const SOURCE_COLORS: Record<string, string> = {
  hackernews: "bg-orange-500/10 text-orange-400 border-orange-500/20",
  googlenews: "bg-blue-500/10 text-blue-400 border-blue-500/20",
  wikipedia: "bg-zinc-500/10 text-zinc-300 border-zinc-500/20",
  linkedin: "bg-sky-500/10 text-sky-400 border-sky-500/20",
  github: "bg-purple-500/10 text-purple-400 border-purple-500/20",
  reddit: "bg-red-500/10 text-red-400 border-red-500/20",
  youtube: "bg-rose-600/10 text-rose-500 border-rose-600/20",
  stackexchange: "bg-amber-500/10 text-amber-400 border-amber-500/20",
};

export function MentionsTab({ data, loading, filters, onFilterChange }: MentionsTabProps) {
  const [expandedMentionId, setExpandedMentionId] = useState<number | null>(null);
  const [showExportMenu, setShowExportMenu] = useState(false);
  const [exportNotice, setExportNotice] = useState<string | null>(null);

  const getSentimentBadge = (sentiment: Sentiment | null, score: number | null) => {
    const formattedScore = score !== null ? `(${score.toFixed(2)})` : "";
    if (sentiment === "positive") {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
          Positive {formattedScore}
        </span>
      );
    }
    if (sentiment === "negative") {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
          <span className="h-1.5 w-1.5 rounded-full bg-rose-400" />
          Negative {formattedScore}
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
        <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />
        Neutral {formattedScore}
      </span>
    );
  };

  // Export to CSV
  const handleExportCSV = () => {
    if (!data || data.items.length === 0) return;
    setShowExportMenu(false);

    const headers = [
      "ID",
      "Source",
      "Author",
      "Published Date",
      "Sentiment",
      "Sentiment Score",
      "Topic",
      "Topic Score",
      "URL",
      "Title",
      "Text",
    ];

    const escapeCSV = (val: any) => {
      if (val === null || val === undefined) return '""';
      const str = String(val).replace(/"/g, '""');
      return `"${str}"`;
    };

    const rows = data.items.map((m) => [
      m.id,
      m.source,
      escapeCSV(m.author || "Anonymous"),
      escapeCSV(m.published_at || ""),
      m.sentiment || "neutral",
      m.sentiment_score ?? "",
      m.topic || "general_feedback",
      m.topic_score ?? "",
      escapeCSV(m.url || ""),
      escapeCSV(m.title || ""),
      escapeCSV(m.text_raw || ""),
    ]);

    const csvContent = [headers.join(","), ...rows.map((r) => r.join(","))].join("\r\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    const dateStr = new Date().toISOString().slice(0, 10);
    link.setAttribute("href", url);
    link.setAttribute("download", `social-mentions-${dateStr}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    setExportNotice(`Exported ${data.items.length} mentions to CSV`);
    setTimeout(() => setExportNotice(null), 3500);
  };

  // Export to JSON
  const handleExportJSON = () => {
    if (!data || data.items.length === 0) return;
    setShowExportMenu(false);

    const blob = new Blob([JSON.stringify(data.items, null, 2)], {
      type: "application/json;charset=utf-8;",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    const dateStr = new Date().toISOString().slice(0, 10);
    link.setAttribute("href", url);
    link.setAttribute("download", `social-mentions-${dateStr}.json`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    setExportNotice(`Exported ${data.items.length} mentions to JSON`);
    setTimeout(() => setExportNotice(null), 3500);
  };

  const hasActiveFilters = Boolean(
    filters.search || filters.sentiment || filters.topic || filters.source
  );

  return (
    <div className="space-y-4">
      {/* Control Filter Toolbar */}
      <div className="bg-[#111827] border border-white/10 rounded-2xl p-4 flex flex-col gap-3 backdrop-blur-md">
        <div className="flex flex-col md:flex-row gap-3 items-stretch md:items-center justify-between">
          {/* Search */}
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search keywords, phrases or authors..."
              value={filters.search}
              onChange={(e) => onFilterChange({ search: e.target.value, page: 1 })}
              className="w-full bg-[#1f2937] border border-white/10 rounded-xl pl-9 pr-4 py-2 text-xs text-white placeholder-slate-400 focus:outline-none focus:border-indigo-500"
            />
            {filters.search && (
              <button
                onClick={() => onFilterChange({ search: "", page: 1 })}
                className="absolute right-3 top-2.5 text-slate-400 hover:text-white"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>

          {/* Filters Row */}
          <div className="flex flex-wrap items-center gap-2">
            {/* Sentiment Filter */}
            <select
              value={filters.sentiment}
              onChange={(e) => onFilterChange({ sentiment: e.target.value, page: 1 })}
              className="bg-[#1f2937] border border-white/10 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
            >
              <option value="">All Sentiments</option>
              <option value="positive">Positive</option>
              <option value="neutral">Neutral</option>
              <option value="negative">Negative</option>
            </select>

            {/* Topic Filter */}
            <select
              value={filters.topic}
              onChange={(e) => onFilterChange({ topic: e.target.value, page: 1 })}
              className="bg-[#1f2937] border border-white/10 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
            >
              {TOPICS.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>

            {/* Source Filter */}
            <select
              value={filters.source}
              onChange={(e) => onFilterChange({ source: e.target.value, page: 1 })}
              className="bg-[#1f2937] border border-white/10 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
            >
              {SOURCES.map((s) => (
                <option key={s.value} value={s.value}>
                  {s.label}
                </option>
              ))}
            </select>

            {/* Reset Filters */}
            {hasActiveFilters && (
              <button
                onClick={() =>
                  onFilterChange({
                    search: "",
                    sentiment: "",
                    topic: "",
                    source: "",
                    page: 1,
                  })
                }
                className="px-2.5 py-2 text-xs text-slate-400 hover:text-white rounded-xl hover:bg-slate-800/80 transition-colors flex items-center gap-1"
                title="Reset all filters"
              >
                <X className="h-3.5 w-3.5" />
                <span>Reset</span>
              </button>
            )}

            {/* Export Dropdown Engine */}
            <div className="relative">
              <button
                onClick={() => setShowExportMenu(!showExportMenu)}
                disabled={!data || data.items.length === 0}
                className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-800/80 hover:bg-slate-800 border border-slate-700/80 text-xs font-semibold text-slate-200 hover:text-white disabled:opacity-40 transition-all shadow-sm"
              >
                <Download className="h-3.5 w-3.5 text-indigo-400" />
                <span>Export</span>
                <ChevronDown className="h-3 w-3 text-slate-400" />
              </button>

              {showExportMenu && (
                <div className="absolute right-0 mt-1.5 w-44 rounded-xl bg-slate-900 border border-slate-700 shadow-2xl py-1 z-30">
                  <button
                    onClick={handleExportCSV}
                    className="w-full flex items-center gap-2 px-3 py-2 text-xs text-slate-200 hover:bg-slate-800 transition-colors text-left"
                  >
                    <FileSpreadsheet className="h-4 w-4 text-emerald-400" />
                    <span>Export to CSV (.csv)</span>
                  </button>
                  <button
                    onClick={handleExportJSON}
                    className="w-full flex items-center gap-2 px-3 py-2 text-xs text-slate-200 hover:bg-slate-800 transition-colors text-left"
                  >
                    <FileText className="h-4 w-4 text-indigo-400" />
                    <span>Export to JSON (.json)</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Quick Triage Chips (PR & Support Fast-Filters) */}
        <div className="flex flex-wrap items-center gap-1.5 pt-2 border-t border-slate-800/80 text-xs">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mr-1">
            Quick Triage:
          </span>
          <button
            onClick={() => onFilterChange({ sentiment: "", topic: "", page: 1 })}
            className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all ${
              !filters.sentiment && !filters.topic
                ? "bg-slate-700 text-white font-semibold"
                : "bg-slate-900/60 text-slate-400 hover:text-slate-200 hover:bg-slate-800/80"
            }`}
          >
            All
          </button>
          <button
            onClick={() => {
              if (filters.sentiment === "negative" && !filters.topic) {
                onFilterChange({ sentiment: "", page: 1 });
              } else {
                onFilterChange({ sentiment: "negative", topic: "", page: 1 });
              }
            }}
            className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all flex items-center gap-1 ${
              filters.sentiment === "negative" && !filters.topic
                ? "bg-rose-500/20 text-rose-300 border border-rose-500/40 font-semibold"
                : "bg-slate-900/60 text-rose-400/80 hover:text-rose-300 hover:bg-rose-500/10"
            }`}
          >
            <span>🚨 Urgent Negatives</span>
          </button>
          <button
            onClick={() => {
              if (filters.sentiment === "positive" && !filters.topic) {
                onFilterChange({ sentiment: "", page: 1 });
              } else {
                onFilterChange({ sentiment: "positive", topic: "", page: 1 });
              }
            }}
            className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all flex items-center gap-1 ${
              filters.sentiment === "positive" && !filters.topic
                ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 font-semibold"
                : "bg-slate-900/60 text-emerald-400/80 hover:text-emerald-300 hover:bg-emerald-500/10"
            }`}
          >
            <span>⭐ High Praise</span>
          </button>
          <button
            onClick={() => {
              if (filters.topic === "complaints" && !filters.sentiment) {
                onFilterChange({ topic: "", page: 1 });
              } else {
                onFilterChange({ topic: "complaints", sentiment: "", page: 1 });
              }
            }}
            className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all ${
              filters.topic === "complaints" && !filters.sentiment
                ? "bg-amber-500/20 text-amber-300 border border-amber-500/40 font-semibold"
                : "bg-slate-900/60 text-amber-400/80 hover:text-amber-300 hover:bg-amber-500/10"
            }`}
          >
            🛠️ Bugs & Complaints
          </button>
          <button
            onClick={() => {
              if (filters.topic === "customer_service" && !filters.sentiment) {
                onFilterChange({ topic: "", page: 1 });
              } else {
                onFilterChange({ topic: "customer_service", sentiment: "", page: 1 });
              }
            }}
            className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all ${
              filters.topic === "customer_service" && !filters.sentiment
                ? "bg-indigo-500/20 text-indigo-300 border border-indigo-500/40 font-semibold"
                : "bg-slate-900/60 text-indigo-400/80 hover:text-indigo-300 hover:bg-indigo-500/10"
            }`}
          >
            💬 Support Requests
          </button>
          <button
            onClick={() => {
              if (filters.topic === "pricing" && !filters.sentiment) {
                onFilterChange({ topic: "", page: 1 });
              } else {
                onFilterChange({ topic: "pricing", sentiment: "", page: 1 });
              }
            }}
            className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all ${
              filters.topic === "pricing" && !filters.sentiment
                ? "bg-violet-500/20 text-violet-300 border border-violet-500/40 font-semibold"
                : "bg-slate-900/60 text-violet-400/80 hover:text-violet-300 hover:bg-violet-500/10"
            }`}
          >
            💰 Pricing & Plans
          </button>
          <button
            onClick={() => {
              if (filters.topic === "features" && !filters.sentiment) {
                onFilterChange({ topic: "", page: 1 });
              } else {
                onFilterChange({ topic: "features", sentiment: "", page: 1 });
              }
            }}
            className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all ${
              filters.topic === "features" && !filters.sentiment
                ? "bg-sky-500/20 text-sky-300 border border-sky-500/40 font-semibold"
                : "bg-slate-900/60 text-sky-400/80 hover:text-sky-300 hover:bg-sky-500/10"
            }`}
          >
            ✨ Features & Specs
          </button>
        </div>

        {/* Active Filters Summary Bar */}
        {hasActiveFilters && (
          <div className="flex flex-wrap items-center gap-1.5 pt-2 border-t border-slate-800/80 text-xs">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mr-1">
              Active Filters:
            </span>
            {filters.search && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-indigo-500/15 text-indigo-300 border border-indigo-500/30 text-[11px]">
                Search: "{filters.search}"
                <button
                  onClick={() => onFilterChange({ search: "", page: 1 })}
                  className="hover:text-white ml-0.5"
                  title="Remove search query"
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            )}
            {filters.sentiment && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-slate-800 text-slate-200 border border-slate-700 text-[11px] capitalize">
                Sentiment: {filters.sentiment}
                <button
                  onClick={() => onFilterChange({ sentiment: "", page: 1 })}
                  className="hover:text-white ml-0.5"
                  title="Remove sentiment filter"
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            )}
            {filters.topic && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-slate-800 text-slate-200 border border-slate-700 text-[11px]">
                Topic: {TOPIC_LABELS[filters.topic] || filters.topic}
                <button
                  onClick={() => onFilterChange({ topic: "", page: 1 })}
                  className="hover:text-white ml-0.5"
                  title="Remove topic filter"
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            )}
            {filters.source && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-slate-800 text-slate-200 border border-slate-700 text-[11px]">
                Source: {filters.source}
                <button
                  onClick={() => onFilterChange({ source: "", page: 1 })}
                  className="hover:text-white ml-0.5"
                  title="Remove source filter"
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            )}
            <button
              onClick={() =>
                onFilterChange({
                  search: "",
                  sentiment: "",
                  topic: "",
                  source: "",
                  page: 1,
                })
              }
              className="text-[11px] font-semibold text-rose-400 hover:text-rose-300 hover:underline ml-2"
            >
              Clear All Filters
            </button>
          </div>
        )}
      </div>

      {/* Export Feedback Banner */}
      {exportNotice && (
        <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center justify-between animate-in fade-in">
          <div className="flex items-center gap-2">
            <Download className="h-4 w-4 text-emerald-400" />
            <span>{exportNotice}</span>
          </div>
          <button onClick={() => setExportNotice(null)} className="text-emerald-400 hover:text-white">
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      )}

      {/* Mentions Feed */}
      <div className="space-y-3">
        {loading && !data ? (
          <div className="space-y-3 animate-pulse">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-24 bg-slate-800/40 rounded-2xl border border-slate-700/40" />
            ))}
          </div>
        ) : !data || data.items.length === 0 ? (
          <div className="glass-card rounded-2xl p-12 text-center">
            <MessageSquare className="h-8 w-8 text-slate-500 mx-auto mb-2" />
            <p className="text-sm font-semibold text-white">No mentions match these filters</p>
            <p className="text-xs text-slate-400 mt-1">Try broadening your search or sentiment filters.</p>
          </div>
        ) : (
          data.items.map((m) => {
            const isExpanded = expandedMentionId === m.id;
            const sourceColor =
              SOURCE_COLORS[m.source] || "bg-slate-800 text-slate-300 border-slate-700";

            return (
              <div
                key={m.id}
                className="bg-[#111827] border border-white/10 rounded-2xl p-4 transition-all hover:border-indigo-500/30 backdrop-blur-md"
              >
                {/* Header row: Source, Sentiment, Topic, Date */}
                <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                  <div className="flex flex-wrap items-center gap-2">
                    {/* Source Pill */}
                    <span
                      className={`text-[11px] font-semibold uppercase px-2.5 py-0.5 rounded-full border ${sourceColor}`}
                    >
                      {m.source}
                    </span>

                    {/* Sentiment Badge */}
                    {getSentimentBadge(m.sentiment, m.sentiment_score)}

                    {/* Topic Pill */}
                    {m.topic && (
                      <span className="inline-flex items-center gap-1 text-[11px] px-2.5 py-0.5 rounded-full bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 font-medium">
                        <Tag className="h-3 w-3" />
                        {TOPIC_LABELS[m.topic] || m.topic.replace(/_/g, " ")}
                      </span>
                    )}

                    {/* Low confidence badge */}
                    {m.is_low_confidence && (
                      <span className="inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
                        <AlertCircle className="h-3 w-3" />
                        Low Confidence
                      </span>
                    )}
                  </div>

                  {/* Date & Link */}
                  <div className="flex items-center gap-3 text-xs text-slate-400">
                    <span className="flex items-center gap-1">
                      <Calendar className="h-3 w-3" />
                      {m.published_at ? new Date(m.published_at).toLocaleDateString() : "Recent"}
                    </span>
                    {m.url && (
                      <a
                        href={m.url}
                        target="_blank"
                        rel="noreferrer noopener"
                        className="text-indigo-400 hover:text-indigo-300 flex items-center gap-1 font-medium hover:underline"
                      >
                        <span>Original</span>
                        <ExternalLink className="h-3 w-3" />
                      </a>
                    )}
                  </div>
                </div>

                {/* Content */}
                {m.title && (
                  <h4 className="text-sm font-semibold text-white mb-1 tracking-tight">
                    {m.title}
                  </h4>
                )}

                <p className="text-xs text-slate-300 leading-relaxed">
                  {isExpanded
                    ? m.text_raw
                    : m.text_raw.slice(0, 240) + (m.text_raw.length > 240 ? "..." : "")}
                </p>

                {m.text_raw.length > 240 && (
                  <button
                    onClick={() => setExpandedMentionId(isExpanded ? null : m.id)}
                    className="text-[11px] font-medium text-indigo-400 hover:text-indigo-300 mt-1"
                  >
                    {isExpanded ? "Show less" : "Read full text"}
                  </button>
                )}

                {/* Author footer if available */}
                {m.author && (
                  <div className="flex items-center gap-1 text-[11px] text-slate-400 mt-2 pt-2 border-t border-slate-800/60">
                    <User className="h-3 w-3" />
                    <span>Posted by {m.author}</span>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Pagination controls */}
      {data && data.pages > 1 && (
        <div className="glass-card rounded-2xl p-4 flex items-center justify-between text-xs text-slate-400">
          <div>
            Showing Page <strong className="text-white">{data.page}</strong> of{" "}
            <strong className="text-white">{data.pages}</strong> ({data.total} total items)
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => onFilterChange({ page: Math.max(1, filters.page - 1) })}
              disabled={filters.page <= 1}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-white disabled:opacity-40 transition-colors flex items-center gap-1"
            >
              <ChevronLeft className="h-3.5 w-3.5" />
              Previous
            </button>
            <button
              onClick={() => onFilterChange({ page: Math.min(data.pages, filters.page + 1) })}
              disabled={filters.page >= data.pages}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-white disabled:opacity-40 transition-colors flex items-center gap-1"
            >
              Next
              <ChevronRight className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
