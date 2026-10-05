/**
 * TypeScript domain types for Social Insights, mirroring backend Pydantic models.
 */

export type Sentiment = "positive" | "neutral" | "negative";

export type Topic =
  | "pricing_billing"
  | "customer_service"
  | "bug_issue"
  | "feature_request"
  | "performance"
  | "competitors"
  | "onboarding_setup"
  | "general_feedback";

export interface Keyword {
  id: number;
  term: string;
  aliases: string[];
  context_hint: string | null;
  mention_count: number;
  last_collected_at: string | null;
  created_at: string;
}

export interface Mention {
  id: number;
  keyword_id: number;
  source: string;
  source_id: string;
  title: string | null;
  text_raw: string;
  url: string | null;
  author: string | null;
  published_at: string;
  sentiment: Sentiment | null;
  sentiment_score: number | null;
  topic: Topic | null;
  topic_score: number | null;
  is_low_confidence: boolean;
  status: "pending" | "done" | "dropped";
  drop_reason: string | null;
}

export interface MentionsPage {
  items: Mention[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export interface SentimentBreakdown {
  positive: number;
  neutral: number;
  negative: number;
  positive_pct: number;
  neutral_pct: number;
  negative_pct: number;
  net_sentiment?: number;
}

export interface TopicCount {
  topic: Topic | string;
  count: number;
  percentage: number;
}

export interface QualityMetrics {
  total_collected: number;
  total_kept: number;
  total_dropped: number;
  drop_reasons: Record<string, number>;
}

export interface OverviewStats {
  keyword: string;
  keyword_id: number;
  total_mentions: number;
  sentiment: SentimentBreakdown;
  top_topics: TopicCount[];
  sources: Record<string, number>;
  quality: QualityMetrics;
  last_collected_at: string | null;
}

export interface TimeSeriesBucket {
  timestamp: string;
  total: number;
  positive: number;
  neutral: number;
  negative: number;
}

export interface TimeSeriesResponse {
  keyword: string;
  interval: "day" | "hour";
  buckets: TimeSeriesBucket[];
}

export interface InsightItem {
  title: string;
  description: string;
  evidence_mention_ids: number[];
  volume?: number | null;
  sentiment?: string | null;
}

export interface StructuredInsights {
  emerging_complaints: InsightItem[];
  requested_features: InsightItem[];
  pain_points: InsightItem[];
  positive_themes: InsightItem[];
  opportunities: InsightItem[];
}

export interface SummaryResponse {
  id: number;
  keyword_id: number;
  keyword: string;
  content: string;
  method: "llm" | "template" | string;
  model_name: string | null;
  prompt_version: string | null;
  created_at: string;
  insights: StructuredInsights | null;
}

export interface TrendItem {
  topic: string;
  current_count: number;
  previous_count: number;
  pct_change: number;
  message: string;
}

export interface TrendsResponse {
  keyword: string;
  window_days: number;
  trends: TrendItem[];
}

export interface CompetitorStats {
  keyword: string;
  keyword_id?: number;
  total_mentions: number;
  positive_pct?: number;
  neutral_pct?: number;
  negative_pct?: number;
  sentiment?: {
    positive_pct: number;
    neutral_pct: number;
    negative_pct: number;
    positive?: number;
    neutral?: number;
    negative?: number;
  };
  top_topics?: (string | TopicCount)[];
  common_complaints?: string[];
  top_complaint_themes?: string[];
}

export interface CompetitorComparisonResponse {
  keywords: string[];
  competitors: CompetitorStats[];
}

export interface AlertItem {
  id: number;
  keyword_id?: number;
  keyword?: string;
  alert_type?: string;
  severity?: string;
  title?: string;
  description?: string;
  message?: string;
  threshold_used?: number;
  observed_value?: number;
  details?: Record<string, any>;
  created_at: string;
  resolved_at?: string | null;
}

export interface AlertsResponse {
  keyword?: string;
  alerts?: AlertItem[];
}

export interface CollectionRun {
  id: number;
  keyword_id: number;
  keyword: string | null;
  status: "queued" | "running" | "succeeded" | "failed";
  started_at: string;
  finished_at: string | null;
  requested_limit: number;
  per_source: Record<string, number>;
  errors: Array<{ error: string; timestamp: string }>;
}
