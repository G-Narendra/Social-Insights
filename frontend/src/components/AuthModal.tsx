"use client";

import React, { useState } from "react";
import {
  AlertCircle,
  Check,
  CheckCircle2,
  Crown,
  Eye,
  EyeOff,
  LineChart,
  Lock,
  Mail,
  Shield,
  Sparkles,
  User as UserIcon,
  X,
  Zap,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { UserRole } from "@/lib/types";

const EMAIL_REGEX = /^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$/;

export function AuthModal() {
  const {
    isAuthModalOpen,
    authModalTab,
    closeAuthModal,
    openAuthModal,
    login,
    signup,
    demoLogin,
    isLoading,
  } = useAuth();

  const [tab, setTab] = useState<"login" | "signup">(authModalTab);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [selectedRole, setSelectedRole] = useState<UserRole>("analyst");
  const [showPassword, setShowPassword] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Sync tab with context if opened from external trigger
  React.useEffect(() => {
    setTab(authModalTab);
    setErrorMsg(null);
  }, [authModalTab, isAuthModalOpen]);

  if (!isAuthModalOpen) return null;

  const isEmailValid = EMAIL_REGEX.test(email.trim());
  const isPasswordValid = password.length >= 8;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    if (!isEmailValid) {
      setErrorMsg("Please enter a valid email address.");
      return;
    }

    if (!isPasswordValid) {
      setErrorMsg("Password must be at least 8 characters long.");
      return;
    }

    try {
      if (tab === "login") {
        await login(email.trim(), password);
      } else {
        await signup(email.trim(), password, fullName.trim() || undefined, selectedRole);
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Authentication failed. Please check your details.");
    }
  };

  const handleDemoSwitch = async (role: UserRole) => {
    setErrorMsg(null);
    try {
      await demoLogin(role);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to initiate demo session.");
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fadeIn">
      {/* Modal Card */}
      <div className="relative w-full max-w-md bg-slate-900/95 border border-slate-700/80 rounded-2xl shadow-2xl shadow-indigo-950/50 overflow-hidden">
        {/* Glow ambient header */}
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500" />

        {/* Close Button */}
        <button
          onClick={closeAuthModal}
          className="absolute top-4 right-4 p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
          title="Close modal"
        >
          <X className="h-5 w-5" />
        </button>

        <div className="p-6">
          {/* Header Title */}
          <div className="flex items-center gap-3 mb-5">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-indigo-600 to-violet-600 flex items-center justify-center shadow-lg shadow-indigo-600/30">
              <Shield className="h-5 w-5 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white tracking-tight">
                {tab === "login" ? "Sign In to Social Insights" : "Create Enterprise Account"}
              </h2>
              <p className="text-xs text-slate-400">
                Role-Based Access Control (RBAC) & Secure Analytics
              </p>
            </div>
          </div>

          {/* 1-Click Demo Profiles Bar */}
          <div className="mb-6 p-3 rounded-xl bg-slate-950/60 border border-slate-800">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-semibold tracking-wider uppercase text-indigo-400 flex items-center gap-1">
                <Zap className="h-3 w-3 text-amber-400" />
                1-Click Instant Demo Testing
              </span>
              <span className="text-[10px] text-slate-400">No email required</span>
            </div>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => handleDemoSwitch("admin")}
                disabled={isLoading}
                className="flex items-center justify-center gap-1.5 py-1.5 px-2 rounded-lg bg-indigo-950/50 hover:bg-indigo-900/60 border border-indigo-700/40 text-indigo-200 text-xs font-medium transition-all active:scale-95 disabled:opacity-50"
              >
                <Crown className="h-3.5 w-3.5 text-amber-400" />
                <span>Admin</span>
              </button>
              <button
                type="button"
                onClick={() => handleDemoSwitch("analyst")}
                disabled={isLoading}
                className="flex items-center justify-center gap-1.5 py-1.5 px-2 rounded-lg bg-sky-950/50 hover:bg-sky-900/60 border border-sky-700/40 text-sky-200 text-xs font-medium transition-all active:scale-95 disabled:opacity-50"
              >
                <LineChart className="h-3.5 w-3.5 text-sky-400" />
                <span>Analyst</span>
              </button>
              <button
                type="button"
                onClick={() => handleDemoSwitch("viewer")}
                disabled={isLoading}
                className="flex items-center justify-center gap-1.5 py-1.5 px-2 rounded-lg bg-slate-800/60 hover:bg-slate-700/60 border border-slate-600/40 text-slate-200 text-xs font-medium transition-all active:scale-95 disabled:opacity-50"
              >
                <Eye className="h-3.5 w-3.5 text-slate-400" />
                <span>Viewer</span>
              </button>
            </div>
          </div>

          {/* Form Tabs */}
          <div className="flex rounded-xl bg-slate-950/80 p-1 border border-slate-800 mb-5">
            <button
              type="button"
              onClick={() => {
                setTab("login");
                setErrorMsg(null);
              }}
              className={`flex-1 py-1.5 text-xs font-medium rounded-lg transition-all ${
                tab === "login"
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => {
                setTab("signup");
                setErrorMsg(null);
              }}
              className={`flex-1 py-1.5 text-xs font-medium rounded-lg transition-all ${
                tab === "signup"
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Sign Up
            </button>
          </div>

          {/* Error Message Alert */}
          {errorMsg && (
            <div className="mb-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-start gap-2.5 text-rose-300 text-xs animate-shake">
              <AlertCircle className="h-4 w-4 shrink-0 text-rose-400 mt-0.5" />
              <div className="flex-1">{errorMsg}</div>
            </div>
          )}

          {/* Input Form */}
          <form onSubmit={handleSubmit} className="space-y-3.5">
            {tab === "signup" && (
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Full Name (Optional)
                </label>
                <div className="relative">
                  <UserIcon className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                  <input
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="e.g. Narendra G."
                    className="w-full bg-slate-950/80 border border-slate-700 rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
                  />
                </div>
              </div>
            )}

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                Corporate or Personal Email
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@company.com"
                  className="w-full bg-slate-950/80 border border-slate-700 rounded-xl pl-9 pr-9 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
                />
                {email && (
                  <div className="absolute right-3 top-2.5">
                    {isEmailValid ? (
                      <Check className="h-4 w-4 text-emerald-400" />
                    ) : (
                      <X className="h-4 w-4 text-rose-400" />
                    )}
                  </div>
                )}
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs font-medium text-slate-300">Password</label>
                <span className="text-[10px] text-slate-500">Min 8 characters</span>
              </div>
              <div className="relative">
                <Lock className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                <input
                  type={showPassword ? "text" : "password"}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full bg-slate-950/80 border border-slate-700 rounded-xl pl-9 pr-9 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-2.5 text-slate-400 hover:text-slate-200"
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            {tab === "signup" && (
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Assigned Permission Role
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {(["admin", "analyst", "viewer"] as UserRole[]).map((r) => (
                    <button
                      key={r}
                      type="button"
                      onClick={() => setSelectedRole(r)}
                      className={`p-2 rounded-xl border text-center transition-all ${
                        selectedRole === r
                          ? "bg-indigo-600/20 border-indigo-500 text-indigo-300 font-semibold"
                          : "bg-slate-950/60 border-slate-800 text-slate-400 hover:text-slate-200"
                      }`}
                    >
                      <div className="text-[11px] capitalize">{r}</div>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full mt-2 py-2.5 px-4 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 active:scale-98 text-white text-xs font-semibold rounded-xl shadow-lg shadow-indigo-600/30 transition-all disabled:opacity-60 flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <div className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <Sparkles className="h-4 w-4" />
              )}
              <span>{tab === "login" ? "Sign In to Workspace" : "Create Account & Start"}</span>
            </button>
          </form>

          {/* Footer note */}
          <div className="mt-4 text-center">
            <p className="text-[11px] text-slate-500">
              Demo accounts pre-seeded with bcrypt-compatible PBKDF2 hashing & RFC 7519 JWT security.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
