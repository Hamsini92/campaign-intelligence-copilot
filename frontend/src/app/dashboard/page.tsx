"use client";

import { useEffect, useState } from "react";
import { getDashboardStats } from "@/lib/api";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
} from "recharts";
import { Users, TrendingUp, Phone, Target } from "lucide-react";

type DashboardData = Awaited<ReturnType<typeof getDashboardStats>>;

const COLORS = [
  "#4f6df5",
  "#6c5ce7",
  "#38b2ac",
  "#e07c4f",
  "#48a865",
  "#d35db0",
  "#5b8def",
  "#9b6ddb",
  "#43c6b1",
  "#e8955a",
  "#5cc07a",
];

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getDashboardStats()
      .then(setData)
      .catch((e) => setError(e.message));
  }, []);

  if (error) {
    return (
      <div className="p-6">
        <Card>
          <CardContent className="pt-6">
            <p className="text-destructive">Failed to load dashboard: {error}</p>
            <p className="text-sm text-muted-foreground mt-2">
              Make sure the backend is running on localhost:8000
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="p-6 space-y-6">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i}>
              <CardHeader className="pb-2">
                <Skeleton className="h-4 w-24" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-8 w-16" />
              </CardContent>
            </Card>
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-5 w-40" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-64 w-full" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  const { kpi } = data;

  const kpiCards = [
    {
      title: "Total Customers",
      value: kpi.total_customers.toLocaleString(),
      icon: Users,
      accent: "text-blue-600",
      border: "border-l-blue-500",
      bg: "bg-blue-50",
    },
    {
      title: "Subscribers",
      value: kpi.subscribers.toLocaleString(),
      icon: Target,
      accent: "text-emerald-600",
      border: "border-l-emerald-500",
      bg: "bg-emerald-50",
    },
    {
      title: "Conversion Rate",
      value: `${kpi.conversion_rate}%`,
      icon: TrendingUp,
      accent: "text-amber-600",
      border: "border-l-amber-500",
      bg: "bg-amber-50",
    },
    {
      title: "Avg Contacts",
      value: kpi.avg_campaign_contacts.toFixed(1),
      icon: Phone,
      accent: "text-violet-600",
      border: "border-l-violet-500",
      bg: "bg-violet-50",
    },
  ];

  return (
    <div className="p-6 md:p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-sm text-muted-foreground mt-1">Campaign performance overview</p>
        </div>
        <span className="text-xs text-muted-foreground bg-card border border-border px-3 py-1.5 rounded-full">
          Historical data &middot; 28,903 records
        </span>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpiCards.map((kpi) => (
          <Card key={kpi.title} className={`border-l-4 ${kpi.border}`}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {kpi.title}
              </CardTitle>
              <div className={`h-8 w-8 rounded-lg ${kpi.bg} flex items-center justify-center`}>
                <kpi.icon className={`h-4 w-4 ${kpi.accent}`} />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold tracking-tight">{kpi.value}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Conversion by Month */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-semibold tracking-tight">Conversion Rate by Month</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={data.conversion_by_month}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} unit="%" />
                <Tooltip
                  formatter={(value) => [`${value}%`, "Conversion Rate"]}
                />
                <Line
                  type="monotone"
                  dataKey="conversion_rate"
                  stroke="#4f6df5"
                  strokeWidth={2.5}
                  dot={{ r: 4, fill: "#4f6df5" }}
                  activeDot={{ r: 6, strokeWidth: 2, stroke: "#fff" }}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Conversion by Job */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-semibold tracking-tight">Conversion Rate by Job</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={data.conversion_by_job} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" tick={{ fontSize: 12 }} unit="%" />
                <YAxis
                  dataKey="job"
                  type="category"
                  tick={{ fontSize: 11 }}
                  width={90}
                />
                <Tooltip
                  formatter={(value) => [`${value}%`, "Conversion Rate"]}
                />
                <Bar dataKey="conversion_rate" radius={[0, 4, 4, 0]}>
                  {data.conversion_by_job.map((_, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={COLORS[index % COLORS.length]}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Conversion by Channel */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-semibold tracking-tight">Conversion by Channel</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-center">
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie
                    data={data.conversion_by_channel}
                    dataKey="subscribers"
                    nameKey="channel"
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    label={({ name, value }) =>
                      `${name}: ${value}`
                    }
                  >
                    {data.conversion_by_channel.map((_, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={index === 0 ? "#4f6df5" : "#38b2ac"}
                      />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Economic Trends */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-semibold tracking-tight">
              Conversion by Euribor Rate
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={data.conversion_by_euribor}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="euribor_range"
                  tick={{ fontSize: 10 }}
                  angle={-20}
                  textAnchor="end"
                  height={60}
                />
                <YAxis tick={{ fontSize: 12 }} unit="%" />
                <Tooltip
                  formatter={(value) => [`${value}%`, "Conversion Rate"]}
                />
                <Bar dataKey="conversion_rate" fill="#6c5ce7" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
