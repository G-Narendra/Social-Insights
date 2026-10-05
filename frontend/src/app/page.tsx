"use client";

import React, { useEffect, useState } from "react";
import {
  BarChart3,
  Bot,
  Flame,
  GitCompare,
  Layers,
  MessageSquare,
  RefreshCw,
  Sparkles,
} from "lucide-react";
import dynamic from "next/dynamic";
import { Navbar } from "@/components/Navbar";
import { OverviewTab } from "@/components/OverviewTab";
import { TrendsAlertsBanner } from "@/components/TrendsAlertsBanner";
import {
  AlertItem,
  Keyword,
  MentionsPage,
  OverviewStats,
  SummaryResponse,
  TimeSeriesResponse,
  TrendItem,
} from "@/lib/types";
import { api } from "@/lib/api";

// Dynamically code-split non-critical tabs and modals for lightning-fast initial load
const MentionsTab = dynamic(
  () => import("@/components/MentionsTab").then((mod) => mod.MentionsTab),
  {
    loading: () => (
      <div className="space-y-4 py-8 animate-pulse">
        <div className="h-14 bg-slate-800/40 rounded-2xl border border-slate-700/50" />
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-28 bg-slate-800/40 rounded-2xl border border-slate-700/50" />
          ))}
        </div>
      </div>
    ),
  }
);

const InsightsTab = dynamic(
  () => import("@/components/InsightsTab").then((mod) => mod.InsightsTab),
  {
    loading: () => (
      <div className="space-y-6 py-8 animate-pulse">
        <div className="h-48 bg-slate-800/40 rounded-2xl border border-slate-700/50" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-40 bg-slate-800/40 rounded-2xl border border-slate-700/50" />
          ))}
        </div>
      </div>
    ),
  }
);

const CompareTab = dynamic(
  () => import("@/components/CompareTab").then((mod) => mod.CompareTab),
  {
    loading: () => (
      <div className="space-y-6 py-8 animate-pulse">
        <div className="h-16 bg-slate-800/40 rounded-2xl border border-slate-700/50" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-72 bg-slate-800/40 rounded-2xl border border-slate-700/50" />
          ))}
        </div>
      </div>
    ),
  }
);

const CollectionModal = dynamic(
  () => import("@/components/CollectionModal").then((mod) => mod.CollectionModal),
  { ssr: false }
);

type ActiveTab = "overview" | "mentions" | "insights" | "compare";

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState<ActiveTab>("overview");
  const [keywords, setKeywords] = useState<Keyword[]>([]);
  const [activeKeyword, setActiveKeyword] = useState<string>("");

  // Tab Data States
  const [stats, setStats] = useState<OverviewStats | null>(null);
  const [timeseries, setTimeseries] = useState<TimeSeriesResponse | null>(null);
  const [mentions, setMentions] = useState<MentionsPage | null>(null);
  const [summary, setSummary] = useState<SummaryResponse | null>(null);
  const [trends, setTrends] = useState<TrendItem[]>([]);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);

  // Loading States
  const [loadingStats, setLoadingStats] = useState(false);
  const [loadingMentions, setLoadingMentions] = useState(false);
  const [loadingSummary, setLoadingSummary] = useState(false);

  // Filters State for Mentions Tab
  const [mentionsFilters, setMentionsFilters] = useState({
    search: "",
    sentiment: "",
    topic: "",
    source: "",
    page: 1,
    limit: 15,
  });

  // Modal State
  const [isCollectModalOpen, setIsCollectModalOpen] = useState(false);

  // 1. Initial Load: Fetch tracked keywords
  const loadKeywords = async () => {
    try {
      const kws = await api.getKeywords();
      setKeywords(kws);
      setActiveKeyword((current) => {
        if (kws.length === 0) return "";
        const exists = kws.some((k) => k.term.toLowerCase() === current.toLowerCase());
        return exists ? current : kws[0].term;
      });
    } catch (err) {
      console.error("Failed to load keywords", err);
    }
  };

  useEffect(() => {
    loadKeywords();
  }, []);

  // 2. Fetch Dashboard Overview Data
  const loadDashboardData = async (kw: string) => {
    if (!kw) return;
    try {
      setLoadingStats(true);
      const [overviewData, tsData, trendsData, alertsData] = await Promise.allSettled([
        api.getOverviewStats(kw),
        api.getTimeSeries(kw, "day"),
        api.getTrends(kw),
        api.getAlerts(kw),
      ]);

      if (overviewData.status === "fulfilled") setStats(overviewData.value);
      if (tsData.status === "fulfilled") setTimeseries(tsData.value);
      if (trendsData.status === "fulfilled") setTrends(trendsData.value.trends || []);
      if (alertsData.status === "fulfilled") {
        const val = alertsData.value as any;
        setAlerts(Array.isArray(val) ? val : val?.alerts || []);
      }
    } catch (err) {
      console.error("Failed to load dashboard stats", err);
    } finally {
      setLoadingStats(false);
    }
  };

  // 3. Fetch Mentions Feed
  const loadMentions = async (kw: string) => {
    if (!kw) return;
    try {
      setLoadingMentions(true);
      const res = await api.getMentions({
        keyword: kw,
        query: mentionsFilters.search || undefined,
        sentiment: mentionsFilters.sentiment || undefined,
        topic: mentionsFilters.topic || undefined,
        source: mentionsFilters.source || undefined,
        page: mentionsFilters.page,
        limit: mentionsFilters.limit,
      });
      setMentions(res);
    } catch (err) {
      console.error("Failed to load mentions", err);
    } finally {
      setLoadingMentions(false);
    }
  };

  // 4. Fetch AI Summary
  const loadSummary = async (kw: string) => {
    if (!kw) return;
    try {
      setLoadingSummary(true);
      const res = await api.getSummary(kw);
      setSummary(res);
    } catch (err) {
      console.error("Failed to load AI summary", err);
    } finally {
      setLoadingSummary(false);
    }
  };

  const handleRefreshSummary = async () => {
    if (!activeKeyword) return;
    try {
      const res = await api.refreshSummary(activeKeyword);
      setSummary(res);
    } catch (err) {
      console.error("Failed to refresh summary", err);
    }
  };

  const handleResolveAlert = async (id: number) => {
    try {
      await api.resolveAlert(id);
      setAlerts((prev) => prev.filter((a) => a.id !== id));
    } catch (err) {
      console.error("Failed to resolve alert", err);
    }
  };

  const handleSimulateAlert = async () => {
    if (!activeKeyword) return;
    try {
      const newAlert = await api.simulateSpikeAlert(activeKeyword);
      setAlerts((prev) => [newAlert, ...prev]);
    } catch (err) {
      console.error("Failed to simulate alert", err);
    }
  };

  const handleSelectSearchTerm = (term: string) => {
    setMentionsFilters((prev) => ({ ...prev, search: term, page: 1 }));
    setActiveTab("mentions");
  };

  // Lazy tab data loading: only load data needed for active tab
  useEffect(() => {
    if (!activeKeyword) return;
    if (activeTab === "overview") {
      loadDashboardData(activeKeyword);
    } else if (activeTab === "mentions") {
      loadMentions(activeKeyword);
    } else if (activeTab === "insights") {
      loadSummary(activeKeyword);
    }
  }, [activeTab, activeKeyword]);

  // When keyword changes, invalidate other tab caches so they re-fetch when clicked
  useEffect(() => {
    if (activeKeyword) {
      if (activeTab !== "mentions") setMentions(null);
      if (activeTab !== "insights") setSummary(null);
    }
  }, [activeKeyword]);

  // Trigger mentions reload when filters change (only if on mentions tab)
  useEffect(() => {
    if (activeKeyword && activeTab === "mentions") {
      loadMentions(activeKeyword);
    }
  }, [mentionsFilters]);

  const handleCollectionSuccess = (kw: string) => {
    setActiveKeyword(kw);
    loadKeywords();
    loadDashboardData(kw);
    setMentions(null);
    setSummary(null);
  };

  const handleDeleteKeyword = async (id: number, term: string) => {
    const confirmed = window.confirm(
      `Remove brand "${term}"?\n\nThis will remove the tracked brand and all its associated mentions, analytics, and summaries.`
    );
    if (!confirmed) return;

    try {
      await api.deleteKeyword(id);
      const remaining = keywords.filter((k) => k.id !== id);
      setKeywords(remaining);

      // If active keyword was deleted, switch to first remaining brand
      if (activeKeyword.toLowerCase() === term.toLowerCase()) {
        const nextKw = remaining.length > 0 ? remaining[0].term : "";
        setActiveKeyword(nextKw);
        setMentions(null);
        setSummary(null);
        if (nextKw) {
          if (activeTab === "overview") loadDashboardData(nextKw);
          else if (activeTab === "mentions") loadMentions(nextKw);
          else if (activeTab === "insights") loadSummary(nextKw);
        } else {
          setStats(null);
          setTimeseries(null);
          setMentions(null);
          setSummary(null);
          setTrends([]);
          setAlerts([]);
        }
      }
    } catch (err) {
      console.error("Failed to delete keyword", err);
      alert(`Could not remove ${term}. Please try again.`);
    }
  };


  // Global Keyboard Shortcuts (1-4 for tabs, 'C' for collect, Escape to close)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      if (target && (target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.isContentEditable)) {
        if (e.key === "Escape") setIsCollectModalOpen(false);
        return;
      }

      if (e.key === "1") setActiveTab("overview");
      else if (e.key === "2") setActiveTab("mentions");
      else if (e.key === "3") setActiveTab("insights");
      else if (e.key === "4") setActiveTab("compare");
      else if (e.key.toLowerCase() === "c") {
        e.preventDefault();
        setIsCollectModalOpen(true);
      } else if (e.key === "Escape") {
        setIsCollectModalOpen(false);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <div className="flex flex-col min-h-screen">
      {/* Top Navbar */}
      <Navbar
        keywords={keywords}
        activeKeyword={activeKeyword}
        onSelectKeyword={(kw) => setActiveKeyword(kw)}
        onDeleteKeyword={handleDeleteKeyword}
        onOpenCollectModal={() => setIsCollectModalOpen(true)}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 lg:px-8 py-6">
        {/* Anomaly & Trends Banner (BON-01, BON-04) */}
        <TrendsAlertsBanner
          alerts={alerts}
          trends={trends}
          onResolveAlert={handleResolveAlert}
          onSimulateAlert={handleSimulateAlert}
        />

        {/* Tab Navigation Navigation Bar */}
        <div className="flex items-center justify-between border-b border-slate-800/80 mb-6 pb-2">
          <div className="flex items-center gap-1 sm:gap-2">
            {/* Overview */}
            <button
              onClick={() => setActiveTab("overview")}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold transition-all ${
                activeTab === "overview"
                  ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/30"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
              }`}
            >
              <BarChart3 className="h-4 w-4" />
              <span>Overview</span>
              <kbd className="hidden md:inline-block text-[10px] font-mono px-1 py-0.2 rounded bg-slate-900/60 text-slate-400 border border-slate-700/50">1</kbd>
            </button>

            {/* Mentions */}
            <button
              onClick={() => setActiveTab("mentions")}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold transition-all ${
                activeTab === "mentions"
                  ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/30"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
              }`}
            >
              <MessageSquare className="h-4 w-4" />
              <span>Mentions Feed</span>
              {stats?.total_mentions ? (
                <span
                  className={`text-[10px] px-1.5 py-0.2 rounded-full ${
                    activeTab === "mentions" ? "bg-indigo-700 text-white" : "bg-slate-800 text-slate-400"
                  }`}
                >
                  {stats.total_mentions}
                </span>
              ) : null}
              <kbd className="hidden md:inline-block text-[10px] font-mono px-1 py-0.2 rounded bg-slate-900/60 text-slate-400 border border-slate-700/50">2</kbd>
            </button>

            {/* AI Summary & Intelligence */}
            <button
              onClick={() => setActiveTab("insights")}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold transition-all ${
                activeTab === "insights"
                  ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/30"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
              }`}
            >
              <Bot className="h-4 w-4" />
              <span>AI Insights</span>
              <span className="h-1.5 w-1.5 rounded-full bg-violet-400 animate-ping" />
              <kbd className="hidden md:inline-block text-[10px] font-mono px-1 py-0.2 rounded bg-slate-900/60 text-slate-400 border border-slate-700/50">3</kbd>
            </button>

            {/* Competitor Benchmark (BON-02) */}
            <button
              onClick={() => setActiveTab("compare")}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold transition-all ${
                activeTab === "compare"
                  ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/30"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
              }`}
            >
              <GitCompare className="h-4 w-4" />
              <span>Compare Brands</span>
              <kbd className="hidden md:inline-block text-[10px] font-mono px-1 py-0.2 rounded bg-slate-900/60 text-slate-400 border border-slate-700/50">4</kbd>
            </button>
          </div>

          {/* Quick Refresh Active Brand Button */}
          <button
            onClick={() => {
              loadDashboardData(activeKeyword);
              loadMentions(activeKeyword);
            }}
            title="Refresh metrics"
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800/60 transition-colors"
          >
            <RefreshCw className={`h-4 w-4 ${loadingStats ? "animate-spin text-indigo-400" : ""}`} />
          </button>
        </div>

        {/* Tab Views */}
        {activeTab === "overview" && (
          <OverviewTab
            stats={stats}
            timeseries={timeseries}
            loading={loadingStats}
            onRefresh={() => loadDashboardData(activeKeyword)}
            onSelectSearchTerm={handleSelectSearchTerm}
          />
        )}

        {activeTab === "mentions" && (
          <MentionsTab
            data={mentions}
            loading={loadingMentions}
            filters={mentionsFilters}
            onFilterChange={(newF) =>
              setMentionsFilters((prev) => ({ ...prev, ...newF }))
            }
          />
        )}

        {activeTab === "insights" && (
          <InsightsTab
            summary={summary}
            loading={loadingSummary}
            onRefreshSummary={handleRefreshSummary}
          />
        )}

        {activeTab === "compare" && <CompareTab initialKeyword={activeKeyword} />}
      </main>

      {/* Collection Ingestion Trigger Modal */}
      <CollectionModal
        isOpen={isCollectModalOpen}
        onClose={() => setIsCollectModalOpen(false)}
        defaultKeyword={activeKeyword}
        onSuccess={handleCollectionSuccess}
      />
    </div>
  );
}
