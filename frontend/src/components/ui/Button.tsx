import React from "react";
import { Loader2 } from "lucide-react";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "destructive" | "ghost";
  size?: "sm" | "md" | "lg";
  isLoading?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      children,
      className = "",
      variant = "primary",
      size = "md",
      isLoading = false,
      disabled,
      ...props
    },
    ref
  ) => {
    const variantStyles = {
      primary:
        "bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-600/20 border border-indigo-500/30",
      secondary:
        "bg-[#1f2937] hover:bg-[#374151] text-slate-200 border border-white/10",
      destructive:
        "bg-rose-600/20 hover:bg-rose-600/30 text-rose-300 border border-rose-500/30",
      ghost:
        "hover:bg-slate-800 text-slate-300 hover:text-white border border-transparent",
    };

    const sizeStyles = {
      sm: "text-xs px-2.5 py-1.5 rounded-lg",
      md: "text-xs px-3.5 py-2 rounded-xl",
      lg: "text-sm px-4 py-2.5 rounded-xl font-medium",
    };

    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={`inline-flex items-center justify-center gap-2 font-medium transition-all active:scale-[0.98] disabled:opacity-50 disabled:pointer-events-none ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
        {...props}
      >
        {isLoading && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
        {children}
      </button>
    );
  }
);

Button.displayName = "Button";
