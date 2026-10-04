"use client";

import React, { useState } from "react";
import {
  AlertCircle,
  Calendar,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  Filter,
  MessageSquare,
  Search,
  Tag,
  User,
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
  { value: "pricing_billing", label: "Pricing & Billing" },
  { value: "customer_service", label: "Customer Support" },
  { value: "bug_issue", label: "Bugs & Issues" },
  { value: "feature_request", label: "Feature Requests" },
  { value: "performance", label: "Performance & Reliability" },
  { value: "competitors", label: "Competitors" },
  { value: "onboarding_setup", label: "Onboarding & Setup" },
  { value: "general_feedback", label: "General Feedback" },
];

const SOURCES = [
  { value: "", label: "All Sources" },
  { value: "hackernews", label: "Hacker News" },
  { value: "googlenews", label: "Google News" },
  { value: "reddit", label: "Reddit" },
  { value: "youtube", label: "YouTube" },
  { value: "stackexchange", label: "Stack Exchange" },
];

const SOURCE_COLORS: Record<string, string> = {
  hackernews: "bg-orange-500/10 text-orange-400 border-orange-500/20",
  googlenews: "bg-blue-500/10 text-blue-400 border-blue-500/20",
  reddit: "bg-red-500/10 text-red-400 border-red-500/20",
  youtube: "bg-rose-600/10 text-rose-500 border-rose-600/20",
  stackexchange: "bg-amber-500/10 text-amber-400 border-amber-500/20",
};

export function MentionsTab({ data, loading, filters, onFilterChange }: MentionsTabProps) {
  const [expandedMentionId, setExpandedMentionId] = useState<number | null>(null);

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
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-500/10 text-slate-300 border border-slate-500/20">
        <span className="h-1.5 w-1.5 rounded-full bg-slate-400" />
        Neutral {formattedScore}
      </span>
    );
  };

  return (
    <div className="space-y-4">
      {/* Control Filter Toolbar */}
      <div className="glass-card rounded-2xl p-4 flex flex-col md:flex-row gap-3 items-stretch md:items-center justify-between">
        {/* Search */}
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search keywords, phrases or authors..."
            value={filters.search}
            onChange={(e) => onFilterChange({ search: e.target.value, page: 1 })}
            className="w-full bg-slate-900/90 border border-slate-700/80 rounded-xl pl-9 pr-4 py-2 text-xs text-white placeholder-slate-400 focus:outline-none focus:border-indigo-500"
          />
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Sentiment Filter */}
          <select
            value={filters.sentiment}
            onChange={(e) => onFilterChange({ sentiment: e.target.value, page: 1 })}
            className="bg-slate-900/90 border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
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
            className="bg-slate-900/90 border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
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
            className="bg-slate-900/90 border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
          >
            {SOURCES.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
        </div>
      </div>

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
                className="glass-card rounded-2xl p-4 transition-all hover:border-slate-600/80"
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
                        {m.topic.replace(/_/g, " ")}
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
