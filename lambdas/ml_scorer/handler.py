import json
import os
import joblib
import numpy as np
import pandas as pd
import shap

# Load model and explainer once (reused across invocations)
MODEL_PATH = os.environ.get("MODEL_PATH", "../../model/artifacts/propensity_model.joblib")
FEATURE_PATH = os.environ.get("FEATURE_PATH", "../../model/artifacts/feature_list.csv")
THRESHOLD = float(os.environ.get("THRESHOLD", "0.6717"))

_model = None
_explainer = None
_features = None


def _load_model():
    global _model, _explainer, _features
    if _model is None:
        _model = joblib.load(MODEL_PATH)
        _explainer = shap.TreeExplainer(_model)
        _features = pd.read_csv(FEATURE_PATH).iloc[:, 0].tolist()
    return _model, _explainer, _features


def _prepare_input(customer_data, features):
    """Convert raw customer input into model-ready feature vector."""
    row = {}

    # Numeric features
    row["age"] = customer_data.get("age", 0)
    row["campaign"] = customer_data.get("campaign", 1)
    row["previous"] = customer_data.get("previous", 0)
    row["cons.price.idx"] = customer_data.get("cons_price_idx", 93.0)
    row["cons.conf.idx"] = customer_data.get("cons_conf_idx", -40.0)
    row["euribor3m"] = customer_data.get("euribor3m", 3.0)

    # Binary encoded features
    default_map = {"no": 0, "unknown": 1, "yes": 2}
    contact_map = {"cellular": 0, "telephone": 1}
    row["default"] = default_map.get(customer_data.get("default", "no"), 0)
    row["contact"] = contact_map.get(customer_data.get("contact", "cellular"), 0)

    # Derived feature
    pdays = customer_data.get("pdays", 999)
    row["was_previously_contacted"] = 0 if pdays == 999 else 1

    # One-hot: job
    job = customer_data.get("job", "")
    job_categories = ["blue-collar", "entrepreneur", "housemaid", "management",
                      "retired", "self-employed", "services", "student",
                      "technician", "unemployed", "unknown"]
    for cat in job_categories:
        row[f"job_{cat}"] = 1 if job == cat else 0

    # One-hot: marital
    marital = customer_data.get("marital", "")
    for cat in ["married", "single", "unknown"]:
        row[f"marital_{cat}"] = 1 if marital == cat else 0

    # One-hot: education
    education = customer_data.get("education", "")
    edu_categories = ["basic.6y", "basic.9y", "high.school", "illiterate",
                      "professional.course", "university.degree", "unknown"]
    for cat in edu_categories:
        row[f"education_{cat}"] = 1 if education == cat else 0

    # One-hot: month
    month = customer_data.get("month", "")
    month_categories = ["aug", "dec", "jul", "jun", "mar", "may",
                        "nov", "oct", "sep"]
    for cat in month_categories:
        row[f"month_{cat}"] = 1 if month == cat else 0

    # One-hot: poutcome
    poutcome = customer_data.get("poutcome", "nonexistent")
    row["poutcome_nonexistent"] = 1 if poutcome == "nonexistent" else 0
    row["poutcome_success"] = 1 if poutcome == "success" else 0

    # Build DataFrame in correct feature order
    df = pd.DataFrame([row])
    for col in features:
        if col not in df.columns:
            df[col] = 0
    df = df[features]

    return df


def score_customer(customer_data):
    """Score a single customer and return probability + SHAP explanation."""
    model, explainer, features = _load_model()

    input_df = _prepare_input(customer_data, features)
    probability = float(model.predict_proba(input_df)[:, 1][0])

    # SHAP explanation
    shap_values = explainer.shap_values(input_df)
    shap_dict = dict(zip(features, shap_values[0]))

    # Top factors (sorted by absolute impact)
    sorted_factors = sorted(shap_dict.items(), key=lambda x: abs(x[1]), reverse=True)
    top_factors = [
        {
            "feature": name,
            "impact": round(float(value), 4),
            "direction": "positive" if value > 0 else "negative"
        }
        for name, value in sorted_factors[:5]
    ]

    # Determine tier
    if probability >= 0.7:
        tier = "high_propensity"
    elif probability >= 0.4:
        tier = "medium_propensity"
    else:
        tier = "low_propensity"

    return {
        "probability": round(probability, 4),
        "tier": tier,
        "will_subscribe": probability >= THRESHOLD,
        "threshold": THRESHOLD,
        "top_factors": top_factors
    }


def score_batch(df):
    """Score a DataFrame of customers."""
    model, explainer, features = _load_model()

    input_df = df[features]
    probabilities = model.predict_proba(input_df)[:, 1]

    results = pd.DataFrame({
        "probability": probabilities,
        "tier": pd.cut(probabilities,
                       bins=[0, 0.4, 0.7, 1.0],
                       labels=["low_propensity", "medium_propensity", "high_propensity"]),
        "will_subscribe": probabilities >= THRESHOLD
    })

    return results


# AWS Lambda handler
def lambda_handler(event, context):
    """Entry point for AWS Lambda / Bedrock Agent Action Group."""
    try:
        action = event.get("actionGroup", "")
        api_path = event.get("apiPath", "")
        body = json.loads(event.get("requestBody", {}).get("content", {}).get("application/json", {}).get("body", "{}"))

        if api_path == "/score":
            result = score_customer(body)
        elif api_path == "/score-batch":
            df = pd.DataFrame(body.get("customers", []))
            result = score_batch(df).to_dict(orient="records")
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
