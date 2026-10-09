import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        canvas: {
          dark: "#0b0f19",
        },
        surface: {
          50: "#f8fafc",
          100: "#f1f5f9",
          layer1: "#111827",
          layer2: "#1f2937",
          layer3: "#374151",
          800: "#1e293b",
          900: "#0f172a",
          950: "#020617",
        },
        accent: {
          indigo: "#6366f1",
          emerald: "#10b981",
          amber: "#f59e0b",
          rose: "#f43f5e",
        },
        brand: {
          50: "#eef2ff",
          100: "#e0e7ff",
          200: "#c7d2fe",
          300: "#a5b4fc",
          400: "#818cf8",
          500: "#6366f1",
          600: "#4f46e5",
          700: "#4338ca",
          800: "#3730a3",
          900: "#312e81",
          950: "#1e1b4b",
        },
        sentiment: {
          pos: "#10b981",
          neu: "#f59e0b",
          neg: "#f43f5e",
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "Inter", "Plus Jakarta Sans", "system-ui", "sans-serif"],
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "Monaco", "Consolas", "monospace"],
      },
    },
  },
  plugins: [],
};
export default config;
