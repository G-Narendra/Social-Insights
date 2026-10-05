"use client";

import React, { useEffect, useState } from "react";
import {
  Activity,
  CheckCircle2,
  ChevronDown,
  Layers,
  Plus,
  Radio,
  RefreshCw,
  Search,
  Sparkles,
  Trash2,
} from "lucide-react";
import { Keyword } from "@/lib/types";
import { api } from "@/lib/api";

interface NavbarProps {
  keywords: Keyword[];
  activeKeyword: string;
  onSelectKeyword: (kw: string) => void;
  onDeleteKeyword?: (id: number, term: string) => void;
  onOpenCollectModal: () => void;
  isCollecting?: boolean;
}

export function Navbar({
  keywords,
  activeKeyword,
  onSelectKeyword,
  onDeleteKeyword,
  onOpenCollectModal,
  isCollecting = false,
}: NavbarProps) {
  const [backendHealthy, setBackendHealthy] = useState<boolean | null>(null);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [searchFilter, setSearchFilter] = useState("");

  useEffect(() => {
    let mounted = true;
    const checkStatus = async () => {
      try {
        await api.getReady();
        if (mounted) setBackendHealthy(true);
      } catch {
        if (mounted) setBackendHealthy(false);
      }
    };
    checkStatus();
    const interval = setInterval(checkStatus, 30000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  const filteredKeywords = keywords.filter((k) =>
    k.term.toLowerCase().includes(searchFilter.toLowerCase())
  );

  return (
    <header className="sticky top-0 z-40 w-full glass-panel border-b border-slate-800/80 px-4 lg:px-8 py-3.5">
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
        {/* Brand identity */}
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-violet-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <Radio className="h-5 w-5 text-white animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
                Social Insights
              </span>
              <span className="text-[10px] uppercase font-semibold px-1.5 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                v1.0
              </span>
            </div>
            <p className="text-xs text-slate-400 hidden sm:block">
              Open-Source Social Listening & Tiered AI
            </p>
          </div>
        </div>

        {/* Center: Keyword selector & Quick switch */}
        <div className="relative">
          <div className="flex items-center bg-slate-900/90 border border-slate-700/80 rounded-xl p-1 shadow-inner focus-within:border-indigo-500/60 transition-colors">
            <button
              onClick={() => setDropdownOpen(!dropdownOpen)}
              className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-slate-200 hover:text-white rounded-lg hover:bg-slate-800/60 transition-colors"
            >
              <Layers className="h-4 w-4 text-indigo-400" />
              <span className="max-w-[140px] truncate">{activeKeyword || "Select Brand"}</span>
              <ChevronDown className="h-3.5 w-3.5 text-slate-400" />
            </button>
          </div>

          {dropdownOpen && (
            <div className="absolute top-full mt-2 w-64 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl p-2 z-50">
              <div className="flex items-center gap-2 px-2.5 py-1.5 bg-slate-800/60 rounded-lg mb-2">
                <Search className="h-3.5 w-3.5 text-slate-400" />
                <input
                  type="text"
                  placeholder="Filter brands..."
                  value={searchFilter}
                  onChange={(e) => setSearchFilter(e.target.value)}
                  className="bg-transparent text-xs text-white placeholder-slate-400 focus:outline-none w-full"
                  autoFocus
                />
              </div>

              <div className="max-h-56 overflow-y-auto space-y-1">
                {filteredKeywords.map((k) => (
                  <div
                    key={k.id}
                    className={`group w-full px-2.5 py-1.5 text-xs rounded-lg flex items-center justify-between transition-colors ${
                      k.term.toLowerCase() === activeKeyword.toLowerCase()
                        ? "bg-indigo-600/20 text-indigo-300 font-semibold"
                        : "text-slate-300 hover:bg-slate-800 hover:text-white"
                    }`}
                  >
                    <button
                      type="button"
                      onClick={() => {
                        onSelectKeyword(k.term);
                        setDropdownOpen(false);
                        setSearchFilter("");
                      }}
                      className="flex-1 text-left truncate flex items-center gap-1.5 focus:outline-none"
                    >
                      <span className="truncate">{k.term}</span>
                    </button>
                    <div className="flex items-center gap-1.5 ml-2 shrink-0">
                      <span className="text-[10px] text-slate-400 px-1.5 py-0.5 rounded bg-slate-800/80 group-hover:bg-slate-700/80">
                        {k.mention_count}
                      </span>
                      {onDeleteKeyword && (
                        <button
                          type="button"
                          title={`Remove ${k.term}`}
                          onClick={(e) => {
                            e.stopPropagation();
                            onDeleteKeyword(k.id, k.term);
                          }}
                          className="opacity-0 group-hover:opacity-100 p-1 hover:bg-rose-500/20 text-slate-400 hover:text-rose-400 rounded transition-all focus:opacity-100"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      )}
                    </div>
                  </div>
                ))}
                {filteredKeywords.length === 0 && (
                  <p className="text-xs text-slate-400 text-center py-2">No brands found</p>
                )}
              </div>

              <div className="pt-2 border-t border-slate-800 mt-2">
                <button
                  onClick={() => {
                    setDropdownOpen(false);
                    onOpenCollectModal();
                  }}
                  className="w-full text-left px-2.5 py-1.5 text-xs rounded-lg text-indigo-400 hover:bg-indigo-950/40 flex items-center gap-1.5 font-medium"
                >
                  <Plus className="h-3.5 w-3.5" />
                  Track New Keyword...
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Right actions */}
        <div className="flex items-center gap-3">
          {/* Health indicator */}
          <div
            className={`hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${
              backendHealthy === true
                ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                : backendHealthy === false
                ? "bg-rose-500/10 text-rose-400 border-rose-500/20"
                : "bg-slate-800 text-slate-400 border-slate-700"
            }`}
          >
            <span
              className={`h-1.5 w-1.5 rounded-full ${
                backendHealthy === true
                  ? "bg-emerald-400 animate-pulse"
                  : backendHealthy === false
                  ? "bg-rose-400"
                  : "bg-slate-400"
              }`}
            />
            {backendHealthy === true
              ? "API Online"
              : backendHealthy === false
              ? "API Offline"
              : "Connecting..."}
          </div>

          {/* Collect button */}
          <button
            onClick={onOpenCollectModal}
            disabled={isCollecting}
            className="flex items-center gap-2 px-3.5 py-1.5 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 active:scale-95 text-white text-xs font-semibold rounded-xl shadow-md shadow-indigo-600/20 transition-all disabled:opacity-60"
          >
            {isCollecting ? (
              <RefreshCw className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Sparkles className="h-3.5 w-3.5" />
            )}
            <span>{isCollecting ? "Collecting..." : "Collect Mentions"}</span>
          </button>
        </div>
      </div>
    </header>
  );
}
