"use client";

import React, { useEffect, useState } from "react";
import {
  Activity,
  CheckCircle2,
  ChevronDown,
  Crown,
  Eye,
  Layers,
  LineChart,
  LogOut,
  Plus,
  Radio,
  RefreshCw,
  Search,
  Shield,
  Sparkles,
  Trash2,
  User as UserIcon,
  Zap,
} from "lucide-react";
import { Keyword, UserRole } from "@/lib/types";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

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
  const { user, role, demoLogin, logout, openAuthModal, isAuthenticated } = useAuth();
  const [backendHealthy, setBackendHealthy] = useState<boolean | null>(null);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
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

  const isViewer = role === "viewer";
  const isAdmin = role === "admin";

  const getRoleBadge = (r: UserRole) => {
    switch (r) {
      case "admin":
        return {
          icon: <Crown className="h-3 w-3 text-amber-400" />,
          label: "Admin",
          classes: "bg-amber-500/10 text-amber-300 border-amber-500/30",
        };
      case "analyst":
        return {
          icon: <LineChart className="h-3 w-3 text-sky-400" />,
          label: "Analyst",
          classes: "bg-sky-500/10 text-sky-300 border-sky-500/30",
        };
      case "viewer":
      default:
        return {
          icon: <Eye className="h-3 w-3 text-slate-400" />,
          label: "Viewer",
          classes: "bg-slate-800 text-slate-300 border-slate-700",
        };
    }
  };

  const badge = getRoleBadge(role);

  return (
    <header className="sticky top-0 z-40 w-full glass-panel border-b border-slate-800/80 px-4 lg:px-8 py-3">
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
            </div>
            <p className="text-xs text-slate-400 hidden sm:block">
              Open-Source Social Listening & Brand Intelligence
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
                          title={isAdmin ? `Remove ${k.term}` : "Admin permissions required to delete brands"}
                          disabled={!isAdmin}
                          onClick={(e) => {
                            e.stopPropagation();
                            if (isAdmin) {
                              onDeleteKeyword(k.id, k.term);
                            }
                          }}
                          className={`p-1 rounded transition-all ${
                            isAdmin
                              ? "opacity-0 group-hover:opacity-100 hover:bg-rose-500/20 text-slate-400 hover:text-rose-400 focus:opacity-100"
                              : "hidden"
                          }`}
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
                  disabled={isViewer}
                  onClick={() => {
                    setDropdownOpen(false);
                    onOpenCollectModal();
                  }}
                  className={`w-full text-left px-2.5 py-1.5 text-xs rounded-lg flex items-center gap-1.5 font-medium ${
                    isViewer
                      ? "text-slate-500 cursor-not-allowed"
                      : "text-indigo-400 hover:bg-indigo-950/40"
                  }`}
                  title={isViewer ? "Viewers cannot track new brands" : undefined}
                >
                  <Plus className="h-3.5 w-3.5" />
                  <span>{isViewer ? "Track Brand (Requires Analyst/Admin)" : "Track New Keyword..."}</span>
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Right actions: Health, RBAC Role Switcher & User Menu, Ingestion CTA */}
        <div className="flex items-center gap-2.5">
          {/* Health indicator */}
          <div
            className={`hidden xl:flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${
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

          {/* Instant 1-Click Evaluation Persona Switcher */}
          <div className="hidden lg:flex items-center gap-1 bg-[#111827] border border-white/10 rounded-xl p-1 text-[11px]">
            {(["admin", "analyst", "viewer"] as UserRole[]).map((r) => {
              const isCurrent = role === r;
              return (
                <button
                  key={r}
                  type="button"
                  onClick={() => demoLogin(r)}
                  className={`px-2.5 py-1 rounded-lg font-medium transition-colors ${
                    isCurrent
                      ? "bg-indigo-600 text-white shadow-sm"
                      : "text-slate-400 hover:text-white hover:bg-white/5"
                  }`}
                >
                  {r === "admin" ? "Admin" : r === "analyst" ? "Analyst" : "Viewer"}
                </button>
              );
            })}
          </div>

          {/* User & Role Dropdown */}
          <div className="relative">
            <button
              type="button"
              onClick={() => setUserMenuOpen(!userMenuOpen)}
              className="flex items-center gap-2 py-1 px-2 rounded-xl bg-slate-900/90 border border-slate-700/80 hover:border-slate-600 transition-colors text-xs text-slate-200"
            >
              <div className="h-6 w-6 rounded-lg bg-indigo-600/30 border border-indigo-500/40 flex items-center justify-center font-semibold text-[11px] text-indigo-300">
                {user?.email ? user.email.charAt(0).toUpperCase() : "U"}
              </div>
              <div className="flex items-center gap-1.5">
                <span className="hidden sm:inline font-medium max-w-[110px] truncate text-slate-300">
                  {user?.full_name || user?.email?.split("@")[0] || "Guest"}
                </span>
                <span
                  className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md text-[10px] font-semibold border ${badge.classes}`}
                >
                  {badge.icon}
                  {badge.label}
                </span>
              </div>
              <ChevronDown className="h-3 w-3 text-slate-400" />
            </button>

            {userMenuOpen && (
              <div className="absolute right-0 top-full mt-2 w-64 bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl p-2.5 z-50 animate-fadeIn">
                <div className="p-2 bg-slate-950/70 rounded-xl border border-slate-800/80 mb-2">
                  <p className="text-xs font-semibold text-white truncate">
                    {user?.full_name || "Enterprise User"}
                  </p>
                  <p className="text-[11px] text-slate-400 truncate">{user?.email || "demo@socialinsights.io"}</p>
                  <div className="mt-1.5 flex items-center justify-between text-[10px]">
                    <span className="text-slate-400">Current Permissions:</span>
                    <span className={`px-1.5 py-0.5 rounded border uppercase font-bold text-[9px] ${badge.classes}`}>
                      {role}
                    </span>
                  </div>
                </div>

                {/* 1-Click Role Switcher */}
                <div className="mb-2">
                  <div className="px-2 py-1 text-[10px] uppercase tracking-wider font-semibold text-slate-400 flex items-center gap-1">
                    <Zap className="h-2.5 w-2.5 text-amber-400" />
                    <span>Quick Switch RBAC Role:</span>
                  </div>
                  <div className="space-y-1">
                    {(["admin", "analyst", "viewer"] as UserRole[]).map((r) => {
                      const itemBadge = getRoleBadge(r);
                      const isCurrent = role === r;
                      return (
                        <button
                          key={r}
                          type="button"
                          onClick={() => {
                            demoLogin(r);
                            setUserMenuOpen(false);
                          }}
                          className={`w-full flex items-center justify-between px-2.5 py-1.5 text-xs rounded-lg transition-colors ${
                            isCurrent
                              ? "bg-indigo-600/20 text-indigo-300 font-semibold border border-indigo-500/30"
                              : "text-slate-300 hover:bg-slate-800 hover:text-white"
                          }`}
                        >
                          <div className="flex items-center gap-2">
                            {itemBadge.icon}
                            <span className="capitalize">{r}</span>
                          </div>
                          {isCurrent ? (
                            <span className="text-[10px] text-indigo-400">Active</span>
                          ) : (
                            <span className="text-[10px] text-slate-400">Test</span>
                          )}
                        </button>
                      );
                    })}
                  </div>
                </div>

                <div className="pt-2 border-t border-slate-800 space-y-1">
                  <button
                    type="button"
                    onClick={() => {
                      setUserMenuOpen(false);
                      openAuthModal("login");
                    }}
                    className="w-full flex items-center gap-2 px-2.5 py-1.5 text-xs text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
                  >
                    <Shield className="h-3.5 w-3.5 text-indigo-400" />
                    <span>Sign In With Email...</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setUserMenuOpen(false);
                      logout();
                    }}
                    className="w-full flex items-center gap-2 px-2.5 py-1.5 text-xs text-rose-400 hover:bg-rose-950/30 rounded-lg transition-colors"
                  >
                    <LogOut className="h-3.5 w-3.5" />
                    <span>Log Out</span>
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Collect button */}
          <button
            onClick={() => {
              if (isViewer) {
                alert("Viewer role has read-only access. Use the role switcher in the top right to switch to Admin or Analyst.");
                return;
              }
              onOpenCollectModal();
            }}
            disabled={isCollecting}
            className={`flex items-center gap-2 px-3.5 py-1.5 text-white text-xs font-semibold rounded-xl shadow-md transition-all active:scale-95 disabled:opacity-60 ${
              isViewer
                ? "bg-slate-800 text-slate-400 border border-slate-700 hover:bg-slate-700/60"
                : "bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 shadow-indigo-600/20"
            }`}
            title={isViewer ? "Viewer mode is read-only. Switch role to collect mentions." : undefined}
          >
            {isCollecting ? (
              <RefreshCw className="h-3.5 w-3.5 animate-spin" />
            ) : isViewer ? (
              <Eye className="h-3.5 w-3.5 text-slate-400" />
            ) : (
              <Sparkles className="h-3.5 w-3.5" />
            )}
            <span>
              {isCollecting
                ? "Collecting..."
                : isViewer
                ? "Viewer (Read-Only)"
                : "Collect Mentions"}
            </span>
          </button>
        </div>
      </div>
    </header>
  );
}
