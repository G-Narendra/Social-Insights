"use client";

import React, { useState } from "react";
import {
  AlertCircle,
  ArrowRight,
  CheckCircle2,
  Cpu,
  Crown,
  Eye,
  EyeOff,
  LineChart,
  Lock,
  Mail,
  Shield,
  Sparkles,
  Zap,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { UserRole } from "@/lib/types";

const EMAIL_REGEX = /^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$/;

export function LoginPortal() {
  const { demoLogin, login, signup, isLoading } = useAuth();
  const [selectedDemoRole, setSelectedDemoRole] = useState<UserRole | null>(null);
  const [activeTab, setActiveTab] = useState<"demo" | "custom">("demo");
  const [customMode, setCustomMode] = useState<"login" | "signup">("login");

  // Form State
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [signupRole, setSignupRole] = useState<UserRole>("analyst");
  const [showPassword, setShowPassword] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [authenticating, setAuthenticating] = useState(false);

  const handleDemoClick = async (role: UserRole) => {
    setErrorMsg(null);
    setSelectedDemoRole(role);
    setAuthenticating(true);
    try {
      await demoLogin(role);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to start demo session. Please ensure the backend is running.");
      setAuthenticating(false);
      setSelectedDemoRole(null);
    }
  };

  const handleCustomSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    const cleanEmail = email.trim();
    if (!EMAIL_REGEX.test(cleanEmail)) {
      setErrorMsg("Please enter a valid email address.");
      return;
    }

    if (password.length < 8) {
      setErrorMsg("Password must be at least 8 characters in length.");
      return;
    }

    setAuthenticating(true);
    try {
      if (customMode === "login") {
        await login(cleanEmail, password);
      } else {
        await signup(cleanEmail, password, fullName.trim() || undefined, signupRole);
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Authentication failed. Please verify your credentials.");
      setAuthenticating(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0b0f19] flex flex-col justify-between px-4 py-8 lg:px-8">
      {/* Top Brand Banner */}
      <div className="max-w-6xl w-full mx-auto text-center pt-4 pb-8 space-y-3">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-xs font-semibold text-indigo-400">
          <Zap className="h-3.5 w-3.5" />
          <span>Tiered Social Listening & Intelligence Engine</span>
        </div>
        <h1 className="text-3xl sm:text-5xl font-extrabold text-white tracking-tight">
          Social Insights
        </h1>
        <p className="text-sm sm:text-base text-slate-400 max-w-2xl mx-auto leading-relaxed">
          Monitor brand sentiment, detect statistical volume anomalies, and generate executive summaries with cost-controlled tiered intelligence.
        </p>
      </div>

      {/* Main Card Container */}
      <div className="max-w-5xl w-full mx-auto space-y-6">
        {/* Navigation Selector: Demo Personas vs Corporate Credentials */}
        <div className="flex items-center justify-center">
          <div className="inline-flex p-1 bg-[#111827] border border-white/10 rounded-2xl">
            <button
              type="button"
              onClick={() => {
                setActiveTab("demo");
                setErrorMsg(null);
              }}
              className={`px-5 py-2 rounded-xl text-xs font-semibold transition-all ${
                activeTab === "demo"
                  ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/30"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              1-Click evaluation personas
            </button>
            <button
              type="button"
              onClick={() => {
                setActiveTab("custom");
                setErrorMsg(null);
              }}
              className={`px-5 py-2 rounded-xl text-xs font-semibold transition-all ${
                activeTab === "custom"
                  ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/30"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              Corporate login / signup
            </button>
          </div>
        </div>

        {errorMsg && (
          <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center justify-between max-w-xl mx-auto animate-fadeIn">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-4 w-4 shrink-0 text-rose-400" />
              <span>{errorMsg}</span>
            </div>
            <button
              type="button"
              onClick={() => setErrorMsg(null)}
              className="text-rose-400 hover:text-white ml-2 text-xs"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Tab 1: 1-Click Evaluation Personas */}
        {activeTab === "demo" && (
          <div className="space-y-4">
            <div className="text-center space-y-1">
              <h2 className="text-lg font-bold text-white">Select a role to evaluate the platform</h2>
              <p className="text-xs text-slate-400">
                Each persona provides pre-configured role permissions to test security enforcement and workflow limits.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              {/* Persona 1: Administrator */}
              <div className="bg-[#111827] border border-white/10 rounded-2xl p-6 flex flex-col justify-between hover:border-amber-500/40 transition-all backdrop-blur-md group">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="p-3 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-400 group-hover:bg-amber-500/20 transition-colors">
                      <Crown className="h-6 w-6" />
                    </div>
                    <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full uppercase tracking-wider bg-amber-500/10 text-amber-300 border border-amber-500/30">
                      Full access
                    </span>
                  </div>

                  <div>
                    <h3 className="text-base font-bold text-white">Administrator</h3>
                    <p className="text-xs font-mono text-slate-400 mt-0.5">admin@socialinsights.io</p>
                  </div>

                  <p className="text-xs text-slate-300 leading-relaxed">
                    Full system access. Manage tracked brands, delete keywords, purge data, and inspect container telemetry.
                  </p>

                  <div className="space-y-2 pt-2 border-t border-white/5 text-[11px] text-slate-400">
                    <div className="flex items-center gap-2 text-slate-300">
                      <CheckCircle2 className="h-3.5 w-3.5 text-amber-400 shrink-0" />
                      <span>Purge and delete brand records</span>
                    </div>
                    <div className="flex items-center gap-2 text-slate-300">
                      <CheckCircle2 className="h-3.5 w-3.5 text-amber-400 shrink-0" />
                      <span>Trigger multi-source ingestion</span>
                    </div>
                    <div className="flex items-center gap-2 text-slate-300">
                      <CheckCircle2 className="h-3.5 w-3.5 text-amber-400 shrink-0" />
                      <span>Resolve anomaly alerts & telemetry</span>
                    </div>
                    <div className="flex items-center gap-2 text-slate-300">
                      <CheckCircle2 className="h-3.5 w-3.5 text-amber-400 shrink-0" />
                      <span>Force AI synthesis re-generation</span>
                    </div>
                  </div>
                </div>

                <button
                  type="button"
                  disabled={authenticating}
                  onClick={() => handleDemoClick("admin")}
                  className="mt-6 w-full py-2.5 px-4 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs flex items-center justify-center gap-2 transition-all shadow-lg shadow-amber-500/20 disabled:opacity-50 cursor-pointer"
                >
                  <span>
                    {authenticating && selectedDemoRole === "admin"
                      ? "Entering..."
                      : "Evaluate as Admin"}
                  </span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </button>
              </div>

              {/* Persona 2: Market Analyst */}
              <div className="bg-[#111827] border border-white/10 rounded-2xl p-6 flex flex-col justify-between hover:border-indigo-500/40 transition-all backdrop-blur-md group">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="p-3 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 group-hover:bg-indigo-500/20 transition-colors">
                      <LineChart className="h-6 w-6" />
                    </div>
                    <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full uppercase tracking-wider bg-indigo-500/10 text-indigo-300 border border-indigo-500/30">
                      Operational
                    </span>
                  </div>

                  <div>
                    <h3 className="text-base font-bold text-white">Market Analyst</h3>
                    <p className="text-xs font-mono text-slate-400 mt-0.5">analyst@socialinsights.io</p>
                  </div>

                  <p className="text-xs text-slate-300 leading-relaxed">
                    Operational role. Run collection scrapers, refresh AI summaries, and acknowledge anomaly spikes.
                  </p>

                  <div className="space-y-2 pt-2 border-t border-white/5 text-[11px] text-slate-400">
                    <div className="flex items-center gap-2 text-slate-300">
                      <CheckCircle2 className="h-3.5 w-3.5 text-indigo-400 shrink-0" />
                      <span>Trigger multi-source ingestion</span>
                    </div>
                    <div className="flex items-center gap-2 text-slate-300">
                      <CheckCircle2 className="h-3.5 w-3.5 text-indigo-400 shrink-0" />
                      <span>Force AI synthesis re-generation</span>
                    </div>
                    <div className="flex items-center gap-2 text-slate-300">
                      <CheckCircle2 className="h-3.5 w-3.5 text-indigo-400 shrink-0" />
                      <span>Resolve anomaly volume alerts</span>
                    </div>
                    <div className="flex items-center gap-2 text-slate-400">
                      <Shield className="h-3.5 w-3.5 text-slate-500 shrink-0" />
                      <span>Brand deletion blocked (Admin only)</span>
                    </div>
                  </div>
                </div>

                <button
                  type="button"
                  disabled={authenticating}
                  onClick={() => handleDemoClick("analyst")}
                  className="mt-6 w-full py-2.5 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs flex items-center justify-center gap-2 transition-all shadow-lg shadow-indigo-600/20 disabled:opacity-50 cursor-pointer"
                >
                  <span>
                    {authenticating && selectedDemoRole === "analyst"
                      ? "Entering..."
                      : "Evaluate as Analyst"}
                  </span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </button>
              </div>

              {/* Persona 3: Executive Viewer */}
              <div className="bg-[#111827] border border-white/10 rounded-2xl p-6 flex flex-col justify-between hover:border-emerald-500/40 transition-all backdrop-blur-md group">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="p-3 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 group-hover:bg-emerald-500/20 transition-colors">
                      <Eye className="h-6 w-6" />
                    </div>
                    <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full uppercase tracking-wider bg-emerald-500/10 text-emerald-300 border border-emerald-500/30">
                      Read-only
                    </span>
                  </div>

                  <div>
                    <h3 className="text-base font-bold text-white">Executive Viewer</h3>
                    <p className="text-xs font-mono text-slate-400 mt-0.5">viewer@socialinsights.io</p>
                  </div>

                  <p className="text-xs text-slate-300 leading-relaxed">
                    Executive oversight. Inspect reputation metrics, sentiment charts, and competitor benchmarks.
                  </p>

                  <div className="space-y-2 pt-2 border-t border-white/5 text-[11px] text-slate-400">
                    <div className="flex items-center gap-2 text-slate-300">
                      <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
                      <span>Inspect Net Sentiment & Brand Health</span>
                    </div>
                    <div className="flex items-center gap-2 text-slate-300">
                      <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
                      <span>Review AI executive synthesis cards</span>
                    </div>
                    <div className="flex items-center gap-2 text-slate-300">
                      <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
                      <span>Inspect competitor comparison benchmarks</span>
                    </div>
                    <div className="flex items-center gap-2 text-slate-400">
                      <Shield className="h-3.5 w-3.5 text-slate-500 shrink-0" />
                      <span>Write operations return 403 Forbidden</span>
                    </div>
                  </div>
                </div>

                <button
                  type="button"
                  disabled={authenticating}
                  onClick={() => handleDemoClick("viewer")}
                  className="mt-6 w-full py-2.5 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs flex items-center justify-center gap-2 transition-all shadow-lg shadow-emerald-600/20 disabled:opacity-50 cursor-pointer"
                >
                  <span>
                    {authenticating && selectedDemoRole === "viewer"
                      ? "Entering..."
                      : "Evaluate as Viewer"}
                  </span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Tab 2: Corporate Login & Signup Form */}
        {activeTab === "custom" && (
          <div className="max-w-md mx-auto bg-[#111827] border border-white/10 rounded-2xl p-6 sm:p-8 backdrop-blur-md space-y-6">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <button
                type="button"
                onClick={() => setCustomMode("login")}
                className={`text-sm font-semibold pb-1 border-b-2 transition-all ${
                  customMode === "login"
                    ? "text-white border-indigo-500"
                    : "text-slate-400 border-transparent hover:text-slate-200"
                }`}
              >
                Sign in to account
              </button>
              <button
                type="button"
                onClick={() => setCustomMode("signup")}
                className={`text-sm font-semibold pb-1 border-b-2 transition-all ${
                  customMode === "signup"
                    ? "text-white border-indigo-500"
                    : "text-slate-400 border-transparent hover:text-slate-200"
                }`}
              >
                Create new account
              </button>
            </div>

            <form onSubmit={handleCustomSubmit} className="space-y-4">
              {customMode === "signup" && (
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                    Full name (optional)
                  </label>
                  <input
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="Jane Doe"
                    className="w-full bg-[#1f2937] border border-white/10 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-400 focus:outline-none focus:border-indigo-500"
                  />
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  Email address
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="user@company.com"
                    className="w-full bg-[#1f2937] border border-white/10 rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder-slate-400 focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  Password (minimum 8 characters)
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                  <input
                    type={showPassword ? "text" : "password"}
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full bg-[#1f2937] border border-white/10 rounded-xl pl-9 pr-10 py-2 text-xs text-white placeholder-slate-400 focus:outline-none focus:border-indigo-500"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-2.5 text-slate-400 hover:text-white"
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              {customMode === "signup" && (
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                    Select account role
                  </label>
                  <select
                    value={signupRole}
                    onChange={(e) => setSignupRole(e.target.value as UserRole)}
                    className="w-full bg-[#1f2937] border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                  >
                    <option value="analyst">Market Analyst (Ingest data, refresh AI)</option>
                    <option value="viewer">Executive Viewer (Read-only dashboards)</option>
                    <option value="admin">Administrator (Full controls)</option>
                  </select>
                </div>
              )}

              <button
                type="submit"
                disabled={authenticating}
                className="w-full py-2.5 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs transition-all shadow-lg shadow-indigo-600/30 disabled:opacity-50 cursor-pointer mt-2"
              >
                {authenticating
                  ? "Authenticating..."
                  : customMode === "login"
                  ? "Sign In"
                  : "Create Account"}
              </button>
            </form>
          </div>
        )}
      </div>

      {/* Operational Compliance Footer */}
      <div className="max-w-4xl w-full mx-auto text-center pt-8 border-t border-white/5 text-[11px] text-slate-500 space-y-1">
        <p>
          Operational constraints: Render 512 MB RAM ceiling • 4-tier cost controlled NLP funnel • NFKC and xxHash64 deduplication
        </p>
        <p>
          Open source under MIT License. Standard library PBKDF2-HMAC-SHA256 and RFC 7519 JWT security.
        </p>
      </div>
    </div>
  );
}
