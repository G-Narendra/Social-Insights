import React from "react";

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "surface1" | "surface2" | "glass";
  isInteractive?: boolean;
}

export function Card({
  children,
  className = "",
  variant = "surface1",
  isInteractive = false,
  ...props
}: CardProps) {
  const variantStyles = {
    surface1: "bg-[#111827] border border-white/10",
    surface2: "bg-[#1f2937] border border-white/10",
    glass: "bg-[#111827]/80 backdrop-blur-md border border-white/10",
  };

  const interactiveStyles = isInteractive
    ? "transition-all duration-150 hover:border-indigo-500/40 hover:bg-[#1a2333] cursor-pointer"
    : "";

  return (
    <div
      className={`rounded-2xl p-5 ${variantStyles[variant]} ${interactiveStyles} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardHeader({
  children,
  className = "",
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={`flex items-center justify-between gap-4 pb-3 border-b border-white/5 mb-4 ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardTitle({
  children,
  className = "",
  ...props
}: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3
      className={`text-sm font-semibold text-slate-100 tracking-tight ${className}`}
      {...props}
    >
      {children}
    </h3>
  );
}

export function CardDescription({
  children,
  className = "",
  ...props
}: React.HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p className={`text-xs text-slate-400 mt-0.5 ${className}`} {...props}>
      {children}
    </p>
  );
}
