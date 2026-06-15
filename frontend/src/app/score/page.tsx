"use client";

import { useState } from "react";
import { scoreCustomer, getStrategy, type ScoreResult } from "@/lib/api";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { UserCheck, Loader2, TrendingUp, TrendingDown, Lightbulb } from "lucide-react";

const JOBS = [
  "admin.",
  "blue-collar",
  "entrepreneur",
  "housemaid",
  "management",
  "retired",
  "self-employed",
  "services",
  "student",
  "technician",
  "unemployed",
  "unknown",
];

const EDUCATION = [
  "basic.4y",
  "basic.6y",
  "basic.9y",
  "high.school",
  "illiterate",
  "professional.course",
  "university.degree",
  "unknown",
];

const MARITAL = ["divorced", "married", "single", "unknown"];
const CONTACT = ["cellular", "telephone"];
const POUTCOME = ["failure", "nonexistent", "success"];

export default function ScorePage() {
  const [form, setForm] = useState({
    age: 45,
    job: "admin.",
    marital: "married",
    education: "university.degree",
    default: "no",
    contact: "cellular",
    campaign: 1,
    pdays: 999,
    previous: 0,
    poutcome: "nonexistent",
    euribor3m: 1.3,
    cons_price_idx: 93.0,
    cons_conf_idx: -40.0,
  });

  const [result, setResult] = useState<ScoreResult | null>(null);
  const [strategy, setStrategy] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleScore() {
    setLoading(true);
    setError(null);
    setStrategy(null);
    try {
      const scoreResult = await scoreCustomer(form);
      setResult(scoreResult);

      // Also fetch strategy
      const strategyResult = await getStrategy({
        segment_profile: {
          age: form.age,
          job: form.job,
          contact: form.contact,
          avg_campaign: form.campaign,
        },
        propensity_score: scoreResult.probability,
        top_factors: scoreResult.top_factors,
        economic_context: { euribor3m: form.euribor3m },
      });
      setStrategy(strategyResult.response);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Scoring failed");
    } finally {
      setLoading(false);
    }
  }

  const tierConfig = (tier: string) => {
    switch (tier) {
      case "high_propensity":
        return { classes: "bg-emerald-50 text-emerald-700 border-emerald-200", label: "High Propensity" };
      case "medium_propensity":
        return { classes: "bg-amber-50 text-amber-700 border-amber-200", label: "Medium Propensity" };
      default:
        return { classes: "bg-red-50 text-red-700 border-red-200", label: "Low Propensity" };
    }
  };

  const scoreColor = (probability: number) => {
    if (probability >= 0.7) return "text-emerald-600";
    if (probability >= 0.4) return "text-amber-600";
    return "text-red-600";
  };

  // SHAP chart data
  const shapData = result?.top_factors.map((f) => ({
    feature: f.feature.replace(/_/g, " ").replace(/\./g, " "),
    impact: f.impact,
    fill: f.direction === "positive" ? "#48a865" : "#e07c4f",
  })) || [];

  return (
    <div className="p-6 md:p-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
          <UserCheck className="h-6 w-6 text-primary" />
          Score Customer
        </h1>
        <p className="text-sm text-muted-foreground mt-1">Predict subscription likelihood with ML-powered scoring</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Input Form */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-sm font-semibold tracking-tight">Customer Profile</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Age</label>
              <Input
                type="number"
                value={form.age}
                onChange={(e) =>
                  setForm({ ...form, age: parseInt(e.target.value) || 0 })
                }
                className="mt-1"
              />
            </div>

            <div>
              <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Job</label>
              <Select
                value={form.job}
                onValueChange={(v) => v && setForm({ ...form, job: v })}
              >
                <SelectTrigger className="mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {JOBS.map((j) => (
                    <SelectItem key={j} value={j}>
                      {j}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Marital Status</label>
              <Select
                value={form.marital}
                onValueChange={(v) => v && setForm({ ...form, marital: v })}
              >
                <SelectTrigger className="mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {MARITAL.map((m) => (
                    <SelectItem key={m} value={m}>
                      {m}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Education</label>
              <Select
                value={form.education}
                onValueChange={(v) => v && setForm({ ...form, education: v })}
              >
                <SelectTrigger className="mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {EDUCATION.map((e) => (
                    <SelectItem key={e} value={e}>
                      {e}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Contact Method</label>
              <Select
                value={form.contact}
                onValueChange={(v) => v && setForm({ ...form, contact: v })}
              >
                <SelectTrigger className="mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {CONTACT.map((c) => (
                    <SelectItem key={c} value={c}>
                      {c}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Previous Outcome</label>
              <Select
                value={form.poutcome}
                onValueChange={(v) => v && setForm({ ...form, poutcome: v })}
              >
                <SelectTrigger className="mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {POUTCOME.map((p) => (
                    <SelectItem key={p} value={p}>
                      {p}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <Separator />

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Contacts</label>
                <Input
                  type="number"
                  value={form.campaign}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      campaign: parseInt(e.target.value) || 1,
                    })
                  }
                  className="mt-1"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Euribor 3M</label>
                <Input
                  type="number"
                  step="0.1"
                  value={form.euribor3m}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      euribor3m: parseFloat(e.target.value) || 0,
                    })
                  }
                  className="mt-1"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">CPI</label>
                <Input
                  type="number"
                  step="0.1"
                  value={form.cons_price_idx}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      cons_price_idx: parseFloat(e.target.value) || 0,
                    })
                  }
                  className="mt-1"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">CCI</label>
                <Input
                  type="number"
                  step="0.1"
                  value={form.cons_conf_idx}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      cons_conf_idx: parseFloat(e.target.value) || 0,
                    })
                  }
                  className="mt-1"
                />
              </div>
            </div>

            <Button onClick={handleScore} disabled={loading} className="w-full mt-2">
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Scoring...
                </>
              ) : (
                "Score Customer"
              )}
            </Button>

            {error && (
              <p className="text-sm text-destructive">{error}</p>
            )}
          </CardContent>
        </Card>

        {/* Results */}
        <div className="lg:col-span-2 space-y-6">
          {!loading && !result && (
            <Card className="flex flex-col items-center justify-center py-20 text-center">
              <div className="h-14 w-14 rounded-2xl bg-primary/10 flex items-center justify-center mb-4">
                <UserCheck className="h-7 w-7 text-primary" />
              </div>
              <h3 className="text-base font-semibold tracking-tight">No score yet</h3>
              <p className="text-sm text-muted-foreground mt-1 max-w-sm">
                Fill in the customer profile on the left and click &ldquo;Score Customer&rdquo; to see propensity results, SHAP analysis, and strategy recommendations.
              </p>
            </Card>
          )}

          {loading && !result && (
            <Card>
              <CardHeader>
                <Skeleton className="h-5 w-32" />
              </CardHeader>
              <CardContent className="space-y-4">
                <Skeleton className="h-20 w-full" />
                <Skeleton className="h-64 w-full" />
              </CardContent>
            </Card>
          )}

          {result && (
            <>
              {/* Score Card */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm font-semibold tracking-tight">Propensity Score</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-6">
                    <div className={`text-5xl font-bold tracking-tight ${scoreColor(result.probability)}`}>
                      {(result.probability * 100).toFixed(1)}%
                    </div>
                    <div className="space-y-2">
                      <Badge
                        variant="outline"
                        className={tierConfig(result.tier).classes}
                      >
                        {tierConfig(result.tier).label}
                      </Badge>
                      <p className="text-sm text-muted-foreground flex items-center gap-1.5">
                        {result.will_subscribe ? (
                          <TrendingUp className="h-3.5 w-3.5 text-emerald-500" />
                        ) : (
                          <TrendingDown className="h-3.5 w-3.5 text-red-400" />
                        )}
                        {result.will_subscribe
                          ? "Predicted to subscribe"
                          : "Unlikely to subscribe"}{" "}
                        (threshold: {(result.threshold * 100).toFixed(1)}%)
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* SHAP Chart */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm font-semibold tracking-tight">
                    Top Contributors
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={220}>
                    <BarChart data={shapData} layout="vertical">
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis type="number" tick={{ fontSize: 12 }} />
                      <YAxis
                        dataKey="feature"
                        type="category"
                        tick={{ fontSize: 11 }}
                        width={120}
                      />
                      <Tooltip
                        formatter={(value) => [
                          Number(value).toFixed(4),
                          "Impact",
                        ]}
                      />
                      <Bar dataKey="impact" radius={[0, 4, 4, 0]}>
                        {shapData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.fill} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                  <div className="flex gap-4 mt-3 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1.5">
                      <span className="w-2.5 h-2.5 rounded-sm bg-[#48a865] inline-block" />
                      Increases likelihood
                    </span>
                    <span className="flex items-center gap-1.5">
                      <span className="w-2.5 h-2.5 rounded-sm bg-[#e07c4f] inline-block" />
                      Decreases likelihood
                    </span>
                  </div>
                </CardContent>
              </Card>

              {/* Strategy */}
              {strategy && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm font-semibold tracking-tight flex items-center gap-2">
                      <Lightbulb className="h-4 w-4 text-amber-500" />
                      Strategy Recommendation
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <pre className="whitespace-pre-wrap text-sm leading-relaxed font-mono bg-muted/50 border border-border p-4 rounded-lg">
                      {strategy}
                    </pre>
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
