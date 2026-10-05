/**
 * Robust typed API client for Social Insights backend.
 * Uses Next.js proxy rewrite or NEXT_PUBLIC_API_URL.
 */

import {
  AlertItem,
  AlertsResponse,
  CollectionRun,
  CompetitorComparisonResponse,
  Keyword,
  MentionsPage,
  OverviewStats,
  StructuredInsights,
  SummaryResponse,
  TimeSeriesResponse,
  TrendsResponse,
} from "./types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "";

export class ApiError extends Error {
  code: string;
  statusCode: number;

  constructor(message: string, code = "error", statusCode = 500) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.statusCode = statusCode;
  }
}

async function request<T>(path: string, options: RequestInit = {}, retries = 2): Promise<T> {
  const url = `${BASE_URL}${path}`;
  const headers = new Headers(options.headers || {});
  if (!headers.has("Content-Type") && options.body) {
    headers.set("Content-Type", "application/json");
  }

  const isGet = !options.method || options.method.toUpperCase() === "GET";
  const maxAttempts = isGet ? retries : 0;

  for (let attempt = 0; attempt <= maxAttempts; attempt++) {
    try {
      const res = await fetch(url, {
        ...options,
        headers,
      });

      if (!res.ok) {
        // If 502/503/504 (transient gateway/proxy disconnect) and we have retries left
        if (isGet && (res.status === 502 || res.status === 503 || res.status === 504) && attempt < maxAttempts) {
          await new Promise((r) => setTimeout(r, 600 * (attempt + 1)));
          continue;
        }

        let errorMsg = `HTTP ${res.status} ${res.statusText}`;
        let errorCode = "http_error";
        try {
          const errJson = await res.json();
          if (errJson.error) {
            errorMsg = errJson.error.message || errorMsg;
            errorCode = errJson.error.code || errorCode;
          } else if (errJson.detail) {
            errorMsg = typeof errJson.detail === "string" ? errJson.detail : JSON.stringify(errJson.detail);
          }
        } catch {
          // Body not JSON
        }
        throw new ApiError(errorMsg, errorCode, res.status);
      }

      return (await res.json()) as T;
    } catch (err: any) {
      if (err instanceof ApiError) {
        throw err;
      }
      // Transient socket hang up or network error on GET: retry with backoff
      if (isGet && attempt < maxAttempts) {
        await new Promise((r) => setTimeout(r, 600 * (attempt + 1)));
        continue;
      }
      throw new ApiError(err?.message || "Network request failed", "network_error", 500);
    }
  }

  throw new ApiError("Network request failed after retries", "network_error", 500);
}

export const api = {
  // System Health
  async getHealth(): Promise<{ status: string }> {
    return request<{ status: string }>("/health");
  },

  async getReady(): Promise<{ status: string }> {
    return request<{ status: string }>("/ready");
  },

  // Keywords
  async getKeywords(): Promise<Keyword[]> {
    return request<Keyword[]>("/api/keywords");
  },

  async createKeyword(data: {
    term: string;
    aliases?: string[];
    context_hint?: string;
  }): Promise<Keyword> {
    return request<Keyword>("/api/keywords", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async deleteKeyword(keywordId: number): Promise<{ message: string; keyword_id?: number }> {
    return request<{ message: string; keyword_id?: number }>(`/api/keywords/${keywordId}`, {
      method: "DELETE",
    });
  },

  // Collection Ingestion Trigger
  async triggerCollection(data: {
    keyword: string;
    limit?: number;
    sources?: string[];
    aliases?: string[];
    context_hint?: string;
  }): Promise<{ run_id: number; status: string }> {
    return request<{ run_id: number; status: string }>("/api/collect", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async getRunStatus(runId: number): Promise<CollectionRun> {
    return request<CollectionRun>(`/api/runs/${runId}`);
  },

  // Mentions Feed
  async getMentions(params: {
    keyword?: string;
    keyword_id?: number;
    sentiment?: string;
    topic?: string;
    source?: string;
    query?: string;
    page?: number;
    limit?: number;
    sort_by?: string;
    sort_order?: "asc" | "desc";
  }): Promise<MentionsPage> {
    const qp = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== "") {
        qp.set(k, String(v));
      }
    });
    return request<MentionsPage>(`/api/mentions?${qp.toString()}`);
  },

  // Statistics
  async getOverviewStats(keyword: string): Promise<OverviewStats> {
    const qp = new URLSearchParams({ keyword });
    return request<OverviewStats>(`/api/stats/overview?${qp.toString()}`);
  },

  async getTimeSeries(
    keyword: string,
    interval: "day" | "hour" = "day"
  ): Promise<TimeSeriesResponse> {
    const qp = new URLSearchParams({ keyword, interval });
    return request<TimeSeriesResponse>(`/api/stats/timeseries?${qp.toString()}`);
  },

  // AI Summary & Insights
  async getSummary(keyword: string): Promise<SummaryResponse> {
    const qp = new URLSearchParams({ keyword });
    return request<SummaryResponse>(`/api/insights/summary?${qp.toString()}`);
  },

  async refreshSummary(keyword: string): Promise<SummaryResponse> {
    const qp = new URLSearchParams({ keyword });
    return request<SummaryResponse>(`/api/insights/summary/refresh?${qp.toString()}`, {
      method: "POST",
    });
  },

  async getStructuredInsights(keyword: string): Promise<StructuredInsights> {
    const qp = new URLSearchParams({ keyword });
    return request<StructuredInsights>(`/api/insights?${qp.toString()}`);
  },

  // Trends & Alerts
  async getTrends(keyword: string, windowDays = 7): Promise<TrendsResponse> {
    const qp = new URLSearchParams({ keyword, window_days: String(windowDays) });
    return request<TrendsResponse>(`/api/insights/trends?${qp.toString()}`);
  },

  async getAlerts(keyword: string): Promise<AlertsResponse> {
    const qp = new URLSearchParams({ keyword });
    return request<AlertsResponse>(`/api/alerts?${qp.toString()}`);
  },

  async resolveAlert(alertId: number): Promise<{ message: string; alert_id: number }> {
    return request<{ message: string; alert_id: number }>(`/api/alerts/${alertId}/resolve`, {
      method: "POST",
    });
  },

  async simulateSpikeAlert(keyword: string, scenario = "sentiment_spike"): Promise<AlertItem> {
    return request<AlertItem>(`/api/alerts/simulate`, {
      method: "POST",
      body: JSON.stringify({ keyword, scenario }),
    });
  },

  // Competitor Comparison
  async compareKeywords(keywords: string[]): Promise<CompetitorComparisonResponse> {
    const qp = new URLSearchParams({ keywords: keywords.join(",") });
    return request<CompetitorComparisonResponse>(`/api/compare?${qp.toString()}`);
  },
};
