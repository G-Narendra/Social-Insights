import React from "react";

export interface MetricStatProps {
  label: string;
  value: string | number;
  subtext?: string;
  icon?: React.ReactNode;
  accent?: "indigo" | "emerald" | "amber" | "rose" | "neutral";
  change?: {
    value: string;
    isPositive?: boolean;
  };
}

export function MetricStat({
  label,
  value,
  subtext,
  icon,
  accent = "indigo",
  change,
}: MetricStatProps) {
  const accentStyles = {
    indigo: "text-indigo-400 bg-indigo-500/10 border-indigo-500/20",
    emerald: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
    amber: "text-amber-400 bg-amber-500/10 border-amber-500/20",
    rose: "text-rose-400 bg-rose-500/10 border-rose-500/20",
    neutral: "text-slate-400 bg-slate-800 border-white/10",
  };

  return (
    <div className="bg-[#111827] border border-white/10 rounded-2xl p-4 flex flex-col justify-between">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-medium text-slate-400">{label}</span>
        {icon && (
          <div
            className={`p-2 rounded-xl border ${accentStyles[accent]} flex items-center justify-center`}
          >
            {icon}
          </div>
        )}
      </div>

      <div className="flex items-baseline gap-2">
        <span className="text-2xl font-bold tracking-tight text-white font-mono tabular-nums">
          {value}
        </span>
        {change && (
          <span
            className={`text-xs font-semibold ${
              change.isPositive ? "text-emerald-400" : "text-rose-400"
            }`}
          >
            {change.isPositive ? "+" : ""}
            {change.value}
          </span>
        )}
      </div>

      {subtext && <p className="text-[11px] text-slate-400 mt-1">{subtext}</p>}
    </div>
  );
}
