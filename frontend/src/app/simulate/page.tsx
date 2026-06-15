"use client";

import { useState } from "react";
import { simulateCampaign, compareSegments } from "@/lib/api";
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
import { Slider } from "@/components/ui/slider";
import { Badge } from "@/components/ui/badge";
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
import { FlaskConical, Loader2, ArrowLeftRight, Users, Target, TrendingUp, Zap } from "lucide-react";

const JOBS = [
  "",
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
];

type SimResult = Awaited<ReturnType<typeof simulateCampaign>>;
type CompareResult = Awaited<ReturnType<typeof compareSegments>>;

export default function SimulatePage() {
  const [budget, setBudget] = useState(500);
  const [job, setJob] = useState("");
  const [ageMin, setAgeMin] = useState(18);
  const [ageMax, setAgeMax] = useState(70);
  const [contact, setContact] = useState("");
  const [simResult, setSimResult] = useState<SimResult | null>(null);
  const [compareResult, setCompareResult] = useState<CompareResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSimulate() {
    setLoading(true);
    setError(null);
    try {
      const filters: Record<string, unknown> = {};
      if (ageMin > 18) filters.age_min = ageMin;
      if (ageMax < 70) filters.age_max = ageMax;
      if (job && job !== "all") filters.job = job;
      if (contact && contact !== "all") filters.contact = contact;

      const [sim, compare] = await Promise.all([
        simulateCampaign({ target_filters: filters, budget_contacts: budget }),
        compareSegments({
          segment_a: { ...filters, contact: "cellular" },
          segment_b: { ...filters, contact: "telephone" },
        }),
      ]);

      setSimResult(sim);
      setCompareResult(compare);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Simulation failed");
    } finally {
      setLoading(false);
    }
  }

  const comparisonData = compareResult
    ? [
        {
          metric: "Count",
          Cellular: compareResult.segment_a.count,
          Telephone: compareResult.segment_b.count,
        },
        {
          metric: "Conv. Rate",
          Cellular: compareResult.segment_a.conversion_rate,
          Telephone: compareResult.segment_b.conversion_rate,
        },
        {
          metric: "Subscribers",
          Cellular: compareResult.segment_a.subscribers,
          Telephone: compareResult.segment_b.subscribers,
        },
      ]
    : [];

  const simMetrics = simResult
    ? [
        {
          label: "Eligible Customers",
          value: simResult.total_eligible.toLocaleString(),
          icon: Users,
          accent: "text-blue-600",
          bg: "bg-blue-50",
        },
        {
          label: "Contacts Planned",
          value: simResult.actual_contacts.toLocaleString(),
          icon: Target,
          accent: "text-violet-600",
          bg: "bg-violet-50",
        },
        {
          label: "Historical Conv. Rate",
          value: `${simResult.historical_conversion_rate}%`,
          icon: TrendingUp,
          accent: "text-amber-600",
          bg: "bg-amber-50",
        },
        {
          label: "Expected Conversions",
          value: simResult.expected_conversions.toString(),
          icon: Zap,
          accent: "text-emerald-600",
          bg: "bg-emerald-50",
        },
      ]
    : [];

  return (
    <div className="p-6 md:p-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
          <FlaskConical className="h-6 w-6 text-primary" />
          Campaign Simulator
        </h1>
        <p className="text-sm text-muted-foreground mt-1">Model campaign outcomes before committing budget</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Controls */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-semibold tracking-tight">Campaign Parameters</CardTitle>
          </CardHeader>
          <CardContent className="space-y-5">
            <div>
              <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                Budget (contacts)
              </label>
              <div className="flex items-center gap-3 mt-2">
                <Slider
                  value={[budget]}
                  onValueChange={(val) => setBudget(Array.isArray(val) ? val[0] : val)}
                  min={50}
                  max={5000}
                  step={50}
                  className="flex-1"
                />
                <span className="text-sm font-semibold tabular-nums w-14 text-right">{budget}</span>
              </div>
            </div>

            <Separator />

            <div>
              <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                Age Range
              </label>
              <div className="flex items-center gap-2 mt-2">
                <Input
                  type="number"
                  value={ageMin}
                  onChange={(e) => setAgeMin(parseInt(e.target.value) || 18)}
                  min={18}
                  max={100}
                />
                <span className="text-muted-foreground text-xs">to</span>
                <Input
                  type="number"
                  value={ageMax}
                  onChange={(e) => setAgeMax(parseInt(e.target.value) || 70)}
                  min={18}
                  max={100}
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Target Job</label>
              <Select value={job} onValueChange={(v) => setJob(v ?? "")}>
                <SelectTrigger className="mt-1">
                  <SelectValue placeholder="All jobs" />
                </SelectTrigger>
                <SelectContent>
                  {JOBS.map((j) => (
                    <SelectItem key={j || "all"} value={j || "all"}>
                      {j || "All jobs"}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Contact Channel</label>
              <Select value={contact} onValueChange={(v) => setContact(v ?? "")}>
                <SelectTrigger className="mt-1">
                  <SelectValue placeholder="All channels" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All channels</SelectItem>
                  <SelectItem value="cellular">Cellular</SelectItem>
                  <SelectItem value="telephone">Telephone</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <Button
              onClick={handleSimulate}
              disabled={loading}
              className="w-full mt-2"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Simulating...
                </>
              ) : (
                "Run Simulation"
              )}
            </Button>

            {error && <p className="text-sm text-destructive">{error}</p>}
          </CardContent>
        </Card>

        {/* Results */}
        <div className="lg:col-span-2 space-y-6">
          {!loading && !simResult && (
            <Card className="flex flex-col items-center justify-center py-20 text-center">
              <div className="h-14 w-14 rounded-2xl bg-primary/10 flex items-center justify-center mb-4">
                <FlaskConical className="h-7 w-7 text-primary" />
              </div>
              <h3 className="text-base font-semibold tracking-tight">No simulation yet</h3>
              <p className="text-sm text-muted-foreground mt-1 max-w-sm">
                Set your campaign parameters on the left and click &ldquo;Run Simulation&rdquo; to see projected outcomes and channel comparisons.
              </p>
            </Card>
          )}

          {simResult && (
            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-semibold tracking-tight">Simulation Results</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  {simMetrics.map((m) => (
                    <div key={m.label} className="flex items-start gap-3 p-3 rounded-lg bg-muted/40">
                      <div className={`h-9 w-9 rounded-lg ${m.bg} flex items-center justify-center shrink-0`}>
                        <m.icon className={`h-4 w-4 ${m.accent}`} />
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground">{m.label}</p>
                        <p className="text-xl font-bold tracking-tight">{m.value}</p>
                      </div>
                    </div>
                  ))}
                </div>
                <Separator className="my-4" />
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-muted-foreground">Cost per Conversion</p>
                    <p className="text-lg font-semibold">{simResult.expected_cost_per_conversion} contacts</p>
                  </div>
                  <Badge
                    variant="outline"
                    className={
                      simResult.actual_contacts < simResult.budget_contacts
                        ? "bg-amber-50 text-amber-700 border-amber-200"
                        : "bg-emerald-50 text-emerald-700 border-emerald-200"
                    }
                  >
                    {simResult.actual_contacts < simResult.budget_contacts
                      ? "Under budget"
                      : "Full budget"}
                  </Badge>
                </div>
              </CardContent>
            </Card>
          )}

          {compareResult && (
            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-semibold tracking-tight flex items-center gap-2">
                  <ArrowLeftRight className="h-4 w-4 text-muted-foreground" />
                  Channel Comparison
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={comparisonData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="metric" tick={{ fontSize: 12 }} />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Bar dataKey="Cellular" fill="#4f6df5" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="Telephone" fill="#38b2ac" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
                <div className="flex gap-4 mt-3 text-xs text-muted-foreground">
                  <span className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-sm inline-block" style={{ backgroundColor: "#4f6df5" }} />
                    Cellular
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-sm inline-block" style={{ backgroundColor: "#38b2ac" }} />
                    Telephone
                  </span>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
