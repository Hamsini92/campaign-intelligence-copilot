const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function getDashboardStats() {
  return apiFetch<{
    kpi: {
      total_customers: number;
      subscribers: number;
      conversion_rate: number;
      avg_age: number;
      avg_campaign_contacts: number;
    };
    conversion_by_job: Array<{
      job: string;
      total: number;
      subscribers: number;
      conversion_rate: number;
    }>;
    conversion_by_month: Array<{
      month: string;
      total: number;
      subscribers: number;
      conversion_rate: number;
    }>;
    conversion_by_channel: Array<{
      channel: string;
      total: number;
      subscribers: number;
      conversion_rate: number;
    }>;
    conversion_by_euribor: Array<{
      euribor_range: string;
      total: number;
      subscribers: number;
      conversion_rate: number;
    }>;
  }>("/api/dashboard-stats");
}

export interface ScoreResult {
  probability: number;
  tier: string;
  will_subscribe: boolean;
  threshold: number;
  top_factors: Array<{
    feature: string;
    impact: number;
    direction: string;
  }>;
}

export async function scoreCustomer(data: Record<string, unknown>) {
  return apiFetch<ScoreResult>("/api/score", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function getStrategy(data: {
  segment_profile: Record<string, unknown>;
  propensity_score: number;
  top_factors: Array<{ feature: string; impact: number; direction: string }>;
  economic_context?: Record<string, unknown>;
}) {
  return apiFetch<{ response: string }>("/api/strategy", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function simulateCampaign(data: {
  target_filters: Record<string, unknown>;
  budget_contacts: number;
}) {
  return apiFetch<{
    total_eligible: number;
    budget_contacts: number;
    actual_contacts: number;
    historical_conversion_rate: number;
    expected_conversions: number;
    expected_cost_per_conversion: number;
  }>("/api/simulate", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function compareSegments(data: {
  segment_a: Record<string, unknown>;
  segment_b: Record<string, unknown>;
  metric?: string;
}) {
  return apiFetch<{
    segment_a: {
      count: number;
      subscribers: number;
      conversion_rate: number;
      avg_age: number;
      avg_campaign: number;
    };
    segment_b: {
      count: number;
      subscribers: number;
      conversion_rate: number;
      avg_age: number;
      avg_campaign: number;
    };
  }>("/api/compare", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export interface ChatResponse {
  intent: string;
  response: string;
  data: Record<string, unknown>;
}

export async function sendChatMessage(message: string) {
  return apiFetch<ChatResponse>("/api/chat", {
    method: "POST",
    body: JSON.stringify({ message }),
  });
}
