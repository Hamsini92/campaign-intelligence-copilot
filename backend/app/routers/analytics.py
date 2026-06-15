from fastapi import APIRouter
import pandas as pd
from app.schemas.analytics import QueryRequest, CompareRequest, SimulateRequest
from app.config import DATA_PATH
import os

os.environ["DATA_PATH"] = DATA_PATH

from data_analyst.handler import query_data, compare_segments, simulate_campaign, _load_data

router = APIRouter()


@router.post("/api/query")
def query(req: QueryRequest):
    result = query_data(
        filters=req.filters,
        aggregation=req.aggregation,
        group_by_field=req.group_by_field,
    )
    return result


@router.post("/api/compare")
def compare(req: CompareRequest):
    result = compare_segments(
        segment_a_filters=req.segment_a,
        segment_b_filters=req.segment_b,
        metric=req.metric,
    )
    return result


@router.post("/api/simulate")
def simulate(req: SimulateRequest):
    result = simulate_campaign(
        target_filters=req.target_filters,
        budget_contacts=req.budget_contacts,
    )
    return result


@router.get("/api/dashboard-stats")
def dashboard_stats():
    """Return aggregated stats for the dashboard: conversion by job, month, channel, and overall KPIs."""
    df = _load_data().copy()

    total = len(df)
    subscribers = int(df["target"].sum())
    conversion_rate = round(float(df["target"].mean()) * 100, 2)
    avg_age = round(float(df["age"].mean()), 1)
    avg_campaign = round(float(df["campaign"].mean()), 1)

    # Reverse one-hot encoding for job
    job_cols = [c for c in df.columns if c.startswith("job_")]
    job_data = []
    for col in job_cols:
        job_name = col.replace("job_", "")
        subset = df[df[col] == 1]
        if len(subset) > 0:
            job_data.append({
                "job": job_name,
                "total": len(subset),
                "subscribers": int(subset["target"].sum()),
                "conversion_rate": round(float(subset["target"].mean()) * 100, 2),
            })
    job_data.sort(key=lambda x: x["conversion_rate"], reverse=True)

    # Reverse one-hot encoding for month
    month_cols = [c for c in df.columns if c.startswith("month_")]
    month_order = ["mar", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
    month_data = []
    for col in month_cols:
        month_name = col.replace("month_", "")
        subset = df[df[col] == 1]
        if len(subset) > 0:
            month_data.append({
                "month": month_name,
                "total": len(subset),
                "subscribers": int(subset["target"].sum()),
                "conversion_rate": round(float(subset["target"].mean()) * 100, 2),
            })
    month_data.sort(key=lambda x: month_order.index(x["month"]) if x["month"] in month_order else 99)

    # Channel: contact column (0 = cellular, 1 = telephone)
    channel_data = []
    for val, name in [(0, "cellular"), (1, "telephone")]:
        subset = df[df["contact"] == val]
        if len(subset) > 0:
            channel_data.append({
                "channel": name,
                "total": len(subset),
                "subscribers": int(subset["target"].sum()),
                "conversion_rate": round(float(subset["target"].mean()) * 100, 2),
            })

    # Economic trends (euribor3m bins)
    df["euribor_bin"] = pd.cut(df["euribor3m"], bins=5)
    econ_data = []
    for bin_label, group in df.groupby("euribor_bin", observed=True):
        econ_data.append({
            "euribor_range": str(bin_label),
            "total": len(group),
            "subscribers": int(group["target"].sum()),
            "conversion_rate": round(float(group["target"].mean()) * 100, 2),
        })

    return {
        "kpi": {
            "total_customers": total,
            "subscribers": subscribers,
            "conversion_rate": conversion_rate,
            "avg_age": avg_age,
            "avg_campaign_contacts": avg_campaign,
        },
        "conversion_by_job": job_data,
        "conversion_by_month": month_data,
        "conversion_by_channel": channel_data,
        "conversion_by_euribor": econ_data,
    }
