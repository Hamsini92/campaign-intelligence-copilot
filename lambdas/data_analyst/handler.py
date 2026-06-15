import json
import os
import pandas as pd
import numpy as np

DATA_PATH = os.environ.get("DATA_PATH", "../../data/train.csv")

_data = None


def _load_data():
    global _data
    if _data is None:
        _data = pd.read_csv(DATA_PATH)
    return _data


def query_data(filters=None, aggregation=None, group_by_field=None):
    """Query the dataset with optional filters and aggregation."""
    df = _load_data().copy()

    # Apply filters
    if filters:
        if "age_min" in filters:
            df = df[df["age"] >= filters["age_min"]]
        if "age_max" in filters:
            df = df[df["age"] <= filters["age_max"]]
        if "job" in filters:
            job_col = f"job_{filters['job']}"
            if job_col in df.columns:
                df = df[df[job_col] == 1]
        if "contact" in filters:
            contact_val = 0 if filters["contact"] == "cellular" else 1
            df = df[df["contact"] == contact_val]
        if "was_previously_contacted" in filters:
            df = df[df["was_previously_contacted"] == filters["was_previously_contacted"]]
        if "score_min" in filters and "probability" in df.columns:
            df = df[df["probability"] >= filters["score_min"]]

    # Aggregation
    if aggregation == "count":
        result = {"total_rows": len(df), "subscribers": int(df["target"].sum()),
                  "non_subscribers": int(len(df) - df["target"].sum()),
                  "conversion_rate": round(float(df["target"].mean()) * 100, 2)}

    elif aggregation == "group_by" and group_by_field:
        if group_by_field in df.columns:
            grouped = df.groupby(group_by_field)["target"].agg(["count", "sum", "mean"])
            grouped.columns = ["total", "subscribers", "conversion_rate"]
            grouped["conversion_rate"] = (grouped["conversion_rate"] * 100).round(2)
            result = grouped.reset_index().to_dict(orient="records")
        else:
            result = {"error": f"Column {group_by_field} not found"}

    elif aggregation == "distribution":
        if group_by_field and group_by_field in df.columns:
            result = df[group_by_field].describe().to_dict()
            result = {k: round(float(v), 4) if isinstance(v, (int, float, np.floating)) else v
                      for k, v in result.items()}
        else:
            result = {"error": "Specify group_by_field for distribution"}

    elif aggregation == "mean":
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        result = {col: round(float(df[col].mean()), 4) for col in numeric_cols}

    else:
        # Return summary
        result = {
            "total_rows": len(df),
            "subscribers": int(df["target"].sum()),
            "conversion_rate": round(float(df["target"].mean()) * 100, 2),
            "avg_age": round(float(df["age"].mean()), 1),
            "avg_campaign": round(float(df["campaign"].mean()), 1)
        }

    return result


def compare_segments(segment_a_filters, segment_b_filters, metric="conversion_rate"):
    """Compare two customer segments."""
    df = _load_data().copy()

    def apply_filters(data, filters):
        for key, value in filters.items():
            if key == "age_min":
                data = data[data["age"] >= value]
            elif key == "age_max":
                data = data[data["age"] <= value]
            elif key == "contact":
                contact_val = 0 if value == "cellular" else 1
                data = data[data["contact"] == contact_val]
            elif key in data.columns:
                data = data[data[key] == value]
        return data

    seg_a = apply_filters(df, segment_a_filters)
    seg_b = apply_filters(df, segment_b_filters)

    def calc_metrics(segment):
        return {
            "count": len(segment),
            "subscribers": int(segment["target"].sum()),
            "conversion_rate": round(float(segment["target"].mean()) * 100, 2),
            "avg_age": round(float(segment["age"].mean()), 1),
            "avg_campaign": round(float(segment["campaign"].mean()), 1)
        }

    return {
        "segment_a": calc_metrics(seg_a),
        "segment_b": calc_metrics(seg_b)
    }


def simulate_campaign(target_filters, budget_contacts):
    """Simulate a campaign: who to target given a budget."""
    df = _load_data().copy()

    # Apply targeting filters
    for key, value in (target_filters or {}).items():
        if key == "age_min":
            df = df[df["age"] >= value]
        elif key == "age_max":
            df = df[df["age"] <= value]
        elif key == "contact":
            contact_val = 0 if value == "cellular" else 1
            df = df[df["contact"] == contact_val]
        elif key in df.columns:
            df = df[df[key] == value]

    total_eligible = len(df)
    actual_contacts = min(budget_contacts, total_eligible)
    conversion_rate = float(df["target"].mean())
    expected_conversions = int(actual_contacts * conversion_rate)

    return {
        "total_eligible": total_eligible,
        "budget_contacts": budget_contacts,
        "actual_contacts": actual_contacts,
        "historical_conversion_rate": round(conversion_rate * 100, 2),
        "expected_conversions": expected_conversions,
        "expected_cost_per_conversion": round(actual_contacts / max(expected_conversions, 1), 1)
    }


# AWS Lambda handler
def lambda_handler(event, context):
    """Entry point for AWS Lambda / Bedrock Agent Action Group."""
    try:
        api_path = event.get("apiPath", "")
        body = json.loads(event.get("requestBody", {}).get("content", {}).get("application/json", {}).get("body", "{}"))

        if api_path == "/query":
            result = query_data(
                filters=body.get("filters"),
                aggregation=body.get("aggregation"),
                group_by_field=body.get("group_by_field")
            )
        elif api_path == "/compare":
            result = compare_segments(
                segment_a_filters=body.get("segment_a", {}),
                segment_b_filters=body.get("segment_b", {}),
                metric=body.get("metric", "conversion_rate")
            )
        elif api_path == "/simulate":
            result = simulate_campaign(
                target_filters=body.get("target_filters", {}),
                budget_contacts=body.get("budget_contacts", 500)
            )
        else:
            result = {"error": f"Unknown path: {api_path}"}

        return {
            "statusCode": 200,
            "body": json.dumps(result)
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
