"use client";

import React from "react";
import { AlertTriangle, CheckCircle, Flame, X } from "lucide-react";

export interface AlertBannerProps {
  type?: "volume_surge" | "sentiment_drop" | "general";
  title: string;
  message: string;
  timestamp?: string;
  onAcknowledge?: () => void;
  onDismiss?: () => void;
}

export function AlertBanner({
  type = "general",
  title,
  message,
  timestamp,
  onAcknowledge,
  onDismiss,
}: AlertBannerProps) {
  const isSurge = type === "volume_surge";
  const icon = isSurge ? (
    <Flame className="h-5 w-5 text-amber-400 shrink-0 mt-0.5" />
  ) : (
    <AlertTriangle className="h-5 w-5 text-rose-400 shrink-0 mt-0.5" />
  );

  const borderBgStyles = isSurge
    ? "border-amber-500/30 bg-amber-500/10"
    : "border-rose-500/30 bg-rose-500/10";

  return (
    <div
      role="alert"
      className={`rounded-2xl border p-4 backdrop-blur-md flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${borderBgStyles}`}
    >
      <div className="flex items-start gap-3">
        {icon}
        <div>
          <div className="flex items-center gap-2">
            <h4 className="text-xs font-semibold text-white">{title}</h4>
            {timestamp && (
              <span className="text-[10px] text-slate-400">{timestamp}</span>
            )}
          </div>
          <p className="text-xs text-slate-300 mt-0.5">{message}</p>
        </div>
      </div>

      <div className="flex items-center gap-2 self-end sm:self-center shrink-0">
        {onAcknowledge && (
          <button
            onClick={onAcknowledge}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium bg-[#111827] text-slate-200 border border-white/10 hover:bg-[#1f2937] transition-colors"
          >
            <CheckCircle className="h-3.5 w-3.5 text-emerald-400" />
            <span>Acknowledge</span>
          </button>
        )}
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
            aria-label="Dismiss alert"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>
    </div>
  );
}
