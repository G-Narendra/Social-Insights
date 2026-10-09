"use client";

import React from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { TimeSeriesResponse } from "@/lib/types";

// Theme color tokens
const THEME = {
  positive: "#10b981", // emerald
  neutral: "#f59e0b",  // amber
  negative: "#f43f5e", // rose
  indigo: "#6366f1",   // electric indigo
  slate: "#64748b",
  grid: "rgba(255, 255, 255, 0.06)",
  sources: {
    googlenews: "#60a5fa",
    hackernews: "#f97316",
    wikipedia: "#818cf8",
    github: "#a78bfa",
    stackexchange: "#f59e0b",
    reddit: "#fb7185",
    youtube: "#f43f5e",
    linkedin: "#38bdf8",
  } as Record<string, string>,
};

// Custom SVG Tooltip for Timeline
function TimelineTooltip({ active, payload, label }: any) {
  if (!active || !payload || !payload.length) return null;
  const total = payload.reduce((acc: number, p: any) => acc + (p.value || 0), 0);

  return (
    <div className="bg-[#111827] border border-white/10 rounded-xl p-3 shadow-2xl text-xs space-y-1.5 backdrop-blur-md min-w-[150px]">
      <div className="font-semibold text-slate-100 border-b border-white/10 pb-1">
        {label}
      </div>
      <div className="space-y-1 font-mono tabular-nums">
        {payload.map((entry: any, index: number) => (
          <div key={index} className="flex items-center justify-between gap-4">
            <span className="flex items-center gap-1.5 text-slate-400 capitalize">
              <span
                className="h-2 w-2 rounded-full"
                style={{ backgroundColor: entry.color }}
              />
              {entry.name}
            </span>
            <span className="font-semibold text-slate-200">{entry.value}</span>
          </div>
        ))}
        <div className="flex items-center justify-between gap-4 pt-1 border-t border-white/5 font-bold">
          <span className="text-slate-300">Total</span>
          <span className="text-white">{total}</span>
        </div>
      </div>
    </div>
  );
}

export function SentimentTimelineChart({
  timeseries,
}: {
  timeseries: TimeSeriesResponse | null;
}) {
  if (!timeseries || !timeseries.buckets || timeseries.buckets.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-xs text-slate-400">
        Insufficient chronological samples for trend chart.
      </div>
    );
  }

  const data = timeseries.buckets.map((b) => ({
    timestamp: b.timestamp,
    positive: b.positive,
    neutral: b.neutral,
    negative: b.negative,
    total: b.total,
  }));

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="posGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={THEME.positive} stopOpacity={0.4} />
              <stop offset="95%" stopColor={THEME.positive} stopOpacity={0.0} />
            </linearGradient>
            <linearGradient id="neuGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={THEME.neutral} stopOpacity={0.4} />
              <stop offset="95%" stopColor={THEME.neutral} stopOpacity={0.0} />
            </linearGradient>
            <linearGradient id="negGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={THEME.negative} stopOpacity={0.4} />
              <stop offset="95%" stopColor={THEME.negative} stopOpacity={0.0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke={THEME.grid} strokeDasharray="3 3" />
          <XAxis
            dataKey="timestamp"
            stroke="#64748b"
            tick={{ fill: "#94a3b8", fontSize: 10 }}
            tickLine={false}
          />
          <YAxis
            stroke="#64748b"
            tick={{ fill: "#94a3b8", fontSize: 10 }}
            tickLine={false}
          />
          <Tooltip content={<TimelineTooltip />} />
          <Area
            type="monotone"
            dataKey="positive"
            name="Positive"
            stroke={THEME.positive}
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#posGradient)"
            stackId="1"
          />
          <Area
            type="monotone"
            dataKey="neutral"
            name="Neutral"
            stroke={THEME.neutral}
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#neuGradient)"
            stackId="1"
          />
          <Area
            type="monotone"
            dataKey="negative"
            name="Negative"
            stroke={THEME.negative}
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#negGradient)"
            stackId="1"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

// Custom Tooltip for Topics
function TopicTooltip({ active, payload }: any) {
  if (!active || !payload || !payload.length) return null;
  const item = payload[0];

  return (
    <div className="bg-[#111827] border border-white/10 rounded-xl p-2.5 shadow-2xl text-xs backdrop-blur-md">
      <div className="font-semibold text-slate-100">{item.payload.topicLabel}</div>
      <div className="text-slate-400 font-mono mt-1">
        Count: <span className="text-white font-bold">{item.value}</span> (
        {item.payload.percentage}%)
      </div>
    </div>
  );
}

export function TopicDistributionChart({
  topTopics,
  onSelectTopic,
}: {
  topTopics: { topic: string; count: number; percentage: number }[];
  onSelectTopic?: (topic: string) => void;
}) {
  if (!topTopics || topTopics.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-xs text-slate-400">
        No topic clustering records available.
      </div>
    );
  }

  const data = topTopics.slice(0, 6).map((t) => ({
    topic: t.topic,
    topicLabel: t.topic.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
    count: t.count,
    percentage: t.percentage,
  }));

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          layout="vertical"
          margin={{ top: 5, right: 20, left: 20, bottom: 5 }}
          onClick={(state) => {
            if (state && state.activePayload && state.activePayload.length) {
              const clicked = state.activePayload[0].payload.topic;
              onSelectTopic?.(clicked);
            }
          }}
        >
          <CartesianGrid stroke={THEME.grid} strokeDasharray="3 3" horizontal={false} />
          <XAxis
            type="number"
            stroke="#64748b"
            tick={{ fill: "#94a3b8", fontSize: 10 }}
            tickLine={false}
          />
          <YAxis
            type="category"
            dataKey="topicLabel"
            stroke="#64748b"
            tick={{ fill: "#94a3b8", fontSize: 10 }}
            tickLine={false}
            width={85}
          />
          <Tooltip content={<TopicTooltip />} />
          <Bar dataKey="count" radius={[0, 4, 4, 0]} className="cursor-pointer">
            {data.map((_, index) => (
              <Cell
                key={`cell-${index}`}
                fill={index === 0 ? THEME.indigo : "#4f46e5"}
                opacity={1 - index * 0.1}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// Custom Tooltip for Source Share
function SourceTooltip({ active, payload }: any) {
  if (!active || !payload || !payload.length) return null;
  const item = payload[0];

  return (
    <div className="bg-[#111827] border border-white/10 rounded-xl p-2.5 shadow-2xl text-xs backdrop-blur-md">
      <div className="flex items-center gap-2">
        <span
          className="h-2 w-2 rounded-full"
          style={{ backgroundColor: item.payload.color }}
        />
        <span className="font-semibold text-slate-100">{item.name}</span>
      </div>
      <div className="text-slate-400 font-mono mt-1">
        Mentions: <span className="text-white font-bold">{item.value}</span>
      </div>
    </div>
  );
}

export function SourceShareChart({
  sources,
}: {
  sources: Record<string, number>;
}) {
  const entries = Object.entries(sources || {});
  if (entries.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-xs text-slate-400">
        No source breakdown available.
      </div>
    );
  }

  const data = entries.map(([src, count]) => {
    const cleanName = src.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
    const color = THEME.sources[src.toLowerCase()] || THEME.indigo;
    return {
      name: cleanName,
      value: count,
      color,
    };
  });

  return (
    <div className="h-64 w-full flex items-center justify-center">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Tooltip content={<SourceTooltip />} />
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={50}
            outerRadius={78}
            paddingAngle={3}
            dataKey="value"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} stroke="#111827" strokeWidth={2} />
            ))}
          </Pie>
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
