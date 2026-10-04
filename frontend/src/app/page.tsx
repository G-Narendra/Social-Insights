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
import { Navbar } from "@/components/Navbar";
import { OverviewTab } from "@/components/OverviewTab";
import { MentionsTab } from "@/components/MentionsTab";
import { InsightsTab } from "@/components/InsightsTab";
import { CompareTab } from "@/components/CompareTab";
import { TrendsAlertsBanner } from "@/components/TrendsAlertsBanner";
import { CollectionModal } from "@/components/CollectionModal";
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

type ActiveTab = "overview" | "mentions" | "insights" | "compare";

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState<ActiveTab>("overview");
  const [keywords, setKeywords] = useState<Keyword[]>([]);
  const [activeKeyword, setActiveKeyword] = useState<string>("Toyota");

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
      if (kws.length > 0 && !activeKeyword) {
        setActiveKeyword(kws[0].term);
      }
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
      if (trendsData.status === "fulfilled") setTrends(trendsData.value.trends);
      if (alertsData.status === "fulfilled") setAlerts(alertsData.value.alerts);
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

  // Trigger loads when active keyword changes
  useEffect(() => {
    if (activeKeyword) {
      loadDashboardData(activeKeyword);
      loadMentions(activeKeyword);
      loadSummary(activeKeyword);
    }
  }, [activeKeyword]);

  // Trigger mentions reload when filters change
  useEffect(() => {
    if (activeKeyword) {
      loadMentions(activeKeyword);
    }
  }, [mentionsFilters]);

  const handleCollectionSuccess = (kw: string) => {
    setActiveKeyword(kw);
    loadKeywords();
    loadDashboardData(kw);
    loadMentions(kw);
    loadSummary(kw);
  };

  return (
    <div className="flex flex-col min-h-screen">
      {/* Top Navbar */}
      <Navbar
        keywords={keywords}
        activeKeyword={activeKeyword}
        onSelectKeyword={(kw) => setActiveKeyword(kw)}
        onOpenCollectModal={() => setIsCollectModalOpen(true)}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 lg:px-8 py-6">
        {/* Anomaly & Trends Banner (BON-01, BON-04) */}
        <TrendsAlertsBanner alerts={alerts} trends={trends} />

        {/* Tab Navigation Navigation Bar */}
        <div className="flex items-center justify-between border-b border-slate-800/80 mb-6 pb-2">
          <div className="flex items-center gap-1 sm:gap-2">
            {/* Overview */}
            <button
              onClick={() => setActiveTab("overview")}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
                activeTab === "overview"
                  ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/30"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
              }`}
            >
              <BarChart3 className="h-4 w-4" />
              <span>Overview</span>
            </button>

            {/* Mentions */}
            <button
              onClick={() => setActiveTab("mentions")}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
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
            </button>

            {/* AI Summary & Intelligence */}
            <button
              onClick={() => setActiveTab("insights")}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
                activeTab === "insights"
                  ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/30"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
              }`}
            >
              <Bot className="h-4 w-4" />
              <span>AI Insights</span>
              <span className="h-2 w-2 rounded-full bg-violet-400 animate-ping" />
            </button>

            {/* Competitor Benchmark (BON-02) */}
            <button
              onClick={() => setActiveTab("compare")}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
                activeTab === "compare"
                  ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/30"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
              }`}
            >
              <GitCompare className="h-4 w-4" />
              <span>Compare Brands</span>
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
