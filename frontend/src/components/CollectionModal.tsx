"use client";

import React, { useState } from "react";
import {
  CheckCircle,
  Database,
  Loader2,
  RefreshCw,
  ShieldAlert,
  Sparkles,
  X,
  Zap,
} from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

interface CollectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  defaultKeyword: string;
  onSuccess: (keyword: string) => void;
}

const AVAILABLE_SOURCES = [
  { id: "googlenews", label: "Google News (RSS)" },
  { id: "hackernews", label: "Hacker News (API)" },
  { id: "wikipedia", label: "Wikipedia (API)" },
  { id: "linkedin", label: "LinkedIn / Wire (RSS)" },
  { id: "github", label: "GitHub Discussions" },
  { id: "stackexchange", label: "Stack Exchange (API)" },
  { id: "reddit", label: "Reddit (API/Mock)" },
  { id: "youtube", label: "YouTube (API/Mock)" },
];

export function CollectionModal({
  isOpen,
  onClose,
  defaultKeyword,
  onSuccess,
}: CollectionModalProps) {
  const { role } = useAuth();
  const isViewer = role === "viewer";
  const [keyword, setKeyword] = useState(defaultKeyword || "");
  const [aliases, setAliases] = useState("");
  const [contextHint, setContextHint] = useState("");
  const [limit, setLimit] = useState(25);
  const [selectedSources, setSelectedSources] = useState<string[]>([
    "googlenews",
    "hackernews",
    "wikipedia",
    "linkedin",
    "github",
    "stackexchange",
  ]);

  const [running, setRunning] = useState(false);
  const [runStatus, setRunStatus] = useState<string | null>(null);
  const [progressMsg, setProgressMsg] = useState("");
  const [error, setError] = useState<string | null>(null);

  React.useEffect(() => {
    if (isOpen) {
      setKeyword(defaultKeyword || "");
      setError(null);
      setRunStatus(null);
      setProgressMsg("");
    }
  }, [isOpen, defaultKeyword]);

  if (!isOpen) return null;

  const toggleSource = (sourceId: string) => {
    setSelectedSources((prev) =>
      prev.includes(sourceId) ? prev.filter((s) => s !== sourceId) : [...prev, sourceId]
    );
  };

  const handleStartCollection = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!keyword.trim()) return;

    try {
      setRunning(true);
      setError(null);
      setRunStatus("queued");
      setProgressMsg("Triggering collection pipeline...");

      const aliasList = aliases
        .split(",")
        .map((a) => a.trim())
        .filter(Boolean);

      const triggerRes = await api.triggerCollection({
        keyword: keyword.trim(),
        limit,
        sources: selectedSources,
        aliases: aliasList.length > 0 ? aliasList : undefined,
        context_hint: contextHint.trim() || undefined,
      });

      const runId = triggerRes.run_id;
      setProgressMsg("Ingesting mentions from public APIs & RSS...");

      // Poll until succeeded or failed with transient glitch tolerance
      const maxPolls = 60;
      let consecutiveErrors = 0;
      for (let i = 0; i < maxPolls; i++) {
        await new Promise((r) => setTimeout(r, 2000));
        try {
          const statusData = await api.getRunStatus(runId);
          consecutiveErrors = 0;
          setRunStatus(statusData.status);

          if (statusData.status === "running") {
            setProgressMsg("Processing deduplication & running local AI models...");
          } else if (statusData.status === "succeeded") {
            setProgressMsg("Enrichment complete! Updating dashboard...");
            await new Promise((r) => setTimeout(r, 1000));
            onSuccess(keyword.trim());
            onClose();
            return;
          } else if (statusData.status === "failed") {
            const errDetail = statusData.errors?.[0]?.error || "Collection run failed";
            throw new Error(errDetail);
          }
        } catch (pollErr: any) {
          if (pollErr.message && pollErr.message.includes("Collection run failed")) {
            throw pollErr;
          }
          consecutiveErrors++;
          console.warn(`Transient polling hiccup (attempt ${consecutiveErrors}/5):`, pollErr);
          if (consecutiveErrors >= 5) {
            throw pollErr;
          }
        }
      }

      throw new Error("Collection timed out. Check backend logs.");
    } catch (err: any) {
      setError(err.message || "An error occurred during collection.");
      setRunning(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="w-full max-w-lg glass-panel rounded-2xl p-6 shadow-2xl border border-slate-700">
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400">
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white tracking-tight">
                Trigger Mention Collection
              </h3>
              <p className="text-xs text-slate-400">
                Multi-source public ingestion + Tier 1 local ML classification
              </p>
            </div>
          </div>
          {!running && (
            <button
              onClick={onClose}
              className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          )}
        </div>

        {running ? (
          <div className="py-8 space-y-4 text-center">
            <div className="relative mx-auto w-14 h-14 flex items-center justify-center">
              <Loader2 className="h-12 w-12 text-indigo-500 animate-spin" />
            </div>
            <div>
              <h4 className="text-sm font-semibold text-white capitalize">
                Status: {runStatus || "Running"}
              </h4>
              <p className="text-xs text-slate-400 mt-1">{progressMsg}</p>
            </div>
            <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden max-w-xs mx-auto">
              <div className="bg-gradient-to-r from-indigo-500 to-violet-500 h-full w-full animate-pulse" />
            </div>
          </div>
        ) : (
          <form onSubmit={handleStartCollection} className="mt-4 space-y-4">
            {/* Keyword */}
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Target Brand, Product or Keyword *
              </label>
              <input
                type="text"
                required
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                placeholder="e.g. ChatGPT, Stripe, OpenAI, Tesla"
                className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
              />
            </div>

            {/* Aliases & Hint */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Aliases (comma-separated)
                </label>
                <input
                  type="text"
                  value={aliases}
                  onChange={(e) => setAliases(e.target.value)}
                  placeholder="e.g. TSLA, Model 3"
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Context Hint (Optional)
                </label>
                <input
                  type="text"
                  value={contextHint}
                  onChange={(e) => setContextHint(e.target.value)}
                  placeholder="e.g. electric automaker"
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>

            {/* Limit */}
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Mentions per Source: {limit}
              </label>
              <input
                type="range"
                min="10"
                max="50"
                step="5"
                value={limit}
                onChange={(e) => setLimit(Number(e.target.value))}
                className="w-full accent-indigo-500 cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-slate-500 mt-0.5">
                <span>10 items (fast)</span>
                <span>25 items</span>
                <span>50 items (thorough)</span>
              </div>
            </div>

            {/* Sources selection */}
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Select Active Ingestion Connectors
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {AVAILABLE_SOURCES.map((src) => {
                  const isChecked = selectedSources.includes(src.id);
                  return (
                    <button
                      type="button"
                      key={src.id}
                      onClick={() => toggleSource(src.id)}
                      className={`text-left px-3 py-2 rounded-xl text-xs flex items-center justify-between border transition-all ${
                        isChecked
                          ? "bg-indigo-500/10 border-indigo-500/30 text-indigo-300 font-semibold"
                          : "bg-slate-900/60 border-slate-800 text-slate-400 hover:border-slate-700"
                      }`}
                    >
                      <span>{src.label}</span>
                      {isChecked && <CheckCircle className="h-3.5 w-3.5 text-indigo-400" />}
                    </button>
                  );
                })}
              </div>
            </div>

            {isViewer && (
              <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-300 flex items-start gap-2">
                <ShieldAlert className="h-4 w-4 text-amber-400 shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold">Viewer Mode (Read-Only):</span> Mentions collection requires Analyst or Admin privileges. You can switch your role in the top header anytime.
                </div>
              </div>
            )}

            {error && (
              <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs text-rose-400">
                {error}
              </div>
            )}

            <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-800">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isViewer || selectedSources.length === 0}
                className="px-4 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-xs font-semibold text-white shadow-md shadow-indigo-600/20 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isViewer ? "Viewer Read-Only" : "Start Ingestion"}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
