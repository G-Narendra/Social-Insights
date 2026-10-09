import React from "react";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "indigo" | "emerald" | "amber" | "rose" | "neutral";
  size?: "sm" | "md";
}

export function Badge({
  children,
  className = "",
  variant = "neutral",
  size = "sm",
  ...props
}: BadgeProps) {
  const variantStyles = {
    indigo: "bg-indigo-500/10 text-indigo-300 border-indigo-500/30",
    emerald: "bg-emerald-500/10 text-emerald-300 border-emerald-500/30",
    amber: "bg-amber-500/10 text-amber-300 border-amber-500/30",
    rose: "bg-rose-500/10 text-rose-300 border-rose-500/30",
    neutral: "bg-slate-800 text-slate-300 border-white/10",
  };

  const sizeStyles = {
    sm: "text-[11px] px-2 py-0.5",
    md: "text-xs px-2.5 py-1",
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-medium rounded-lg border ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
      {...props}
    >
      {children}
    </span>
  );
}
