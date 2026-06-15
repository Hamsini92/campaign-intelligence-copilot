"""
Keyword-based intent routing for the chat endpoint.
Locally replaces the Bedrock Agent orchestrator.
"""

from data_analyst.handler import query_data, compare_segments, simulate_campaign
from ml_scorer.handler import score_customer
from strategy_advisor.handler import generate_strategy_local
import re


def _extract_job(message: str) -> str | None:
    jobs = [
        "admin.", "blue-collar", "entrepreneur", "housemaid", "management",
        "retired", "self-employed", "services", "student", "technician",
        "unemployed", "unknown",
    ]
    msg_lower = message.lower()
    for job in jobs:
        if job in msg_lower:
            return job
    return None


def _extract_age_range(message: str) -> tuple[int | None, int | None]:
    patterns = [
        r"age\s*(\d+)\s*(?:to|-)\s*(\d+)",
        r"between\s*(\d+)\s*and\s*(\d+)",
        r"(\d+)\s*(?:to|-)\s*(\d+)\s*year",
        r"over\s*(\d+)",
        r"under\s*(\d+)",
    ]
    msg_lower = message.lower()
    for pattern in patterns:
        match = re.search(pattern, msg_lower)
        if match:
            groups = match.groups()
            if len(groups) == 2:
                return int(groups[0]), int(groups[1])
            elif "over" in pattern:
                return int(groups[0]), None
            elif "under" in pattern:
                return None, int(groups[0])
    return None, None


def _extract_budget(message: str) -> int | None:
    match = re.search(r"budget\s*(?:of\s*)?(\d+)", message.lower())
    if match:
        return int(match.group(1))
    match = re.search(r"(\d+)\s*(?:contacts?|people|customers?)", message.lower())
    if match:
        return int(match.group(1))
    return None


EXPLANATIONS = {
    "propensity": (
        "**Propensity Score** is the predicted probability (0-100%) that a customer will subscribe "
        "to a term deposit. The model uses 41 features (demographics, contact history, economic indicators) "
        "to generate this score.\n\n"
        "**Tiers:**\n"
        "- **High propensity** (70%+): Strong likelihood of subscribing. Prioritize these customers.\n"
        "- **Medium propensity** (40-70%): Moderate chance. Worth contacting with the right strategy.\n"
        "- **Low propensity** (below 40%): Unlikely to subscribe. Consider skipping or low-cost channels.\n\n"
        "The decision threshold is 67.17% — above this the model predicts \"will subscribe.\""
    ),
    "tier": (
        "**Propensity Tiers** classify customers by their likelihood to subscribe:\n\n"
        "- **High propensity** (score >= 70%): Top priority. These customers have strong indicators "
        "like previous successful contact, favorable economic conditions, or high-converting demographics.\n"
        "- **Medium propensity** (40-70%): Worth pursuing with targeted messaging and optimal timing.\n"
        "- **Low propensity** (below 40%): Low ROI expected. Consider excluding from campaigns or "
        "using low-cost automated outreach.\n\n"
        "These tiers help allocate campaign budget efficiently."
    ),
    "shap": (
        "**SHAP (SHapley Additive exPlanations)** values explain why the model made a specific prediction.\n\n"
        "Each feature gets a SHAP value:\n"
        "- **Positive impact** (green): This feature *increases* the customer's likelihood to subscribe.\n"
        "- **Negative impact** (red): This feature *decreases* the likelihood.\n"
        "- **Larger absolute value** = stronger influence on the prediction.\n\n"
        "For example, a low euribor rate (SHAP: +0.5) means favorable interest rates are strongly "
        "pushing the prediction toward subscription."
    ),
    "euribor": (
        "**Euribor 3M** (Euro Interbank Offered Rate, 3-month) is a key European interest rate benchmark.\n\n"
        "In this model:\n"
        "- **Low euribor** (< 2%): Favorable for term deposits — customers are more likely to lock in rates. "
        "Historically correlates with 25%+ conversion rates.\n"
        "- **High euribor** (> 4%): Customers prefer flexible savings. Conversion drops to ~5%.\n\n"
        "Euribor is one of the strongest predictors in the model."
    ),
    "conversion": (
        "**Conversion rate** is the percentage of contacted customers who actually subscribed to a term deposit.\n\n"
        "In this dataset:\n"
        "- Overall conversion rate: ~12.5%\n"
        "- Best channel: Cellular (16.5%) vs Telephone (5.9%)\n"
        "- Best months: March (53%), December (47%), October (46%)\n"
        "- Best demographics: Students (31%), Retired (27%)\n\n"
        "The model uses historical conversion patterns to predict future outcomes."
    ),
    "model": (
        "**The ML Model** is an XGBoost gradient-boosted decision tree classifier.\n\n"
        "- **Algorithm**: XGBoost (eXtreme Gradient Boosting)\n"
        "- **Performance**: AUC-ROC = 0.80 (good discrimination between subscribers and non-subscribers)\n"
        "- **Features**: 41 input features (demographics, contact history, economic indicators)\n"
        "- **Threshold**: 0.6717 — optimized to balance precision and recall\n"
        "- **Training data**: 28,903 customer records from bank marketing campaigns\n\n"
        "The model outputs a probability and SHAP explanations for each prediction."
    ),
    "threshold": (
        "**Decision Threshold** (67.17%) is the cutoff point for the binary prediction.\n\n"
        "- Score **above** 67.17%: Model predicts \"will subscribe\"\n"
        "- Score **below** 67.17%: Model predicts \"will not subscribe\"\n\n"
        "This threshold was optimized during training to balance:\n"
        "- **Precision**: Avoiding false positives (wasting budget on unlikely subscribers)\n"
        "- **Recall**: Not missing actual potential subscribers\n\n"
        "Note: The propensity tier (high/medium/low) uses different cutoffs (70%/40%) "
        "for campaign prioritization."
    ),
}


def _is_explanation_question(msg: str) -> bool:
    """Check if the user is asking a definitional/educational question rather than requesting an action."""
    explanation_patterns = [
        r"what\s+(does|do|is|are|means?)\b",
        r"what'?s\s+(a|an|the)?\s*\w+\s*(mean|score|tier|propensity)",
        r"explain\b",
        r"define\b",
        r"meaning\s+of\b",
        r"tell\s+me\s+(about|more)\b",
        r"how\s+does\s+.+\s+work",
        r"what\s+do\s+you\s+mean",
        r"what\s+does\s+\w+\s+mean",
        r"what\s+is\s+(a|an|the)?\s*(propensity|shap|euribor|tier|threshold|model|conversion|score)",
    ]
    return any(re.search(p, msg) for p in explanation_patterns)


def _match_explanation(msg: str) -> str | None:
    """Match the message to the best explanation topic."""
    topic_keywords = {
        "propensity": ["propensity", "medium propensity", "high propensity", "low propensity", "propensity score"],
        "tier": ["tier", "tiers", "high_propensity", "medium_propensity", "low_propensity", "priority level"],
        "shap": ["shap", "shapley", "feature impact", "top factors", "feature importance", "why did the model"],
        "euribor": ["euribor", "interest rate", "euribor3m"],
        "conversion": ["conversion rate", "conversion", "subscribe rate"],
        "model": ["model", "xgboost", "algorithm", "auc", "how does the model", "ml model", "machine learning"],
        "threshold": ["threshold", "cutoff", "decision boundary", "67", "0.6717"],
    }
    for topic, keywords in topic_keywords.items():
        if any(kw in msg for kw in keywords):
            return topic
    return None


def route_message(message: str) -> dict:
    msg = message.lower()

    # Intent: Explain concepts (check BEFORE action intents)
    if _is_explanation_question(msg):
        topic = _match_explanation(msg)
        if topic and topic in EXPLANATIONS:
            return {
                "intent": "explain",
                "response": EXPLANATIONS[topic],
                "data": {},
            }

    # Intent: Score a customer
    if any(kw in msg for kw in ["score", "propensity", "predict", "likelihood"]):
        age_min, age_max = _extract_age_range(message)
        job = _extract_job(message)
        customer_data = {
            "age": age_min or 40,
            "job": job or "admin.",
            "marital": "married",
            "education": "university.degree",
            "default": "no",
            "contact": "cellular",
            "campaign": 1,
            "pdays": 999,
            "previous": 0,
            "poutcome": "nonexistent",
            "euribor3m": 1.3,
            "cons_price_idx": 93.0,
            "cons_conf_idx": -40.0,
        }
        result = score_customer(customer_data)
        return {
            "intent": "score",
            "response": f"Based on the profile (age {customer_data['age']}, {customer_data['job']}, {customer_data['marital']}), "
                        f"the propensity score is **{result['probability']:.1%}** ({result['tier'].replace('_', ' ')}).\n\n"
                        f"**Top factors:**\n" +
                        "\n".join(f"- {f['feature']}: {f['impact']:+.4f} ({f['direction']})" for f in result["top_factors"]),
            "data": result,
        }

    # Intent: Simulate campaign
    if any(kw in msg for kw in ["simulate", "simulation", "campaign", "budget"]):
        budget = _extract_budget(message) or 500
        job = _extract_job(message)
        filters = {}
        age_min, age_max = _extract_age_range(message)
        if age_min:
            filters["age_min"] = age_min
        if age_max:
            filters["age_max"] = age_max
        if job:
            filters["job"] = job
        result = simulate_campaign(target_filters=filters, budget_contacts=budget)
        return {
            "intent": "simulate",
            "response": f"**Campaign Simulation** (budget: {budget} contacts)\n\n"
                        f"- Eligible customers: {result['total_eligible']:,}\n"
                        f"- Contacts planned: {result['actual_contacts']:,}\n"
                        f"- Historical conversion rate: {result['historical_conversion_rate']}%\n"
                        f"- Expected conversions: {result['expected_conversions']}\n"
                        f"- Cost per conversion: {result['expected_cost_per_conversion']} contacts",
            "data": result,
        }

    # Intent: Compare segments
    if any(kw in msg for kw in ["compare", "versus", "vs", "difference"]):
        job = _extract_job(message)
        result = compare_segments(
            segment_a_filters={"contact": "cellular"},
            segment_b_filters={"contact": "telephone"},
        )
        return {
            "intent": "compare",
            "response": f"**Segment Comparison: Cellular vs Telephone**\n\n"
                        f"| Metric | Cellular | Telephone |\n"
                        f"|--------|----------|----------|\n"
                        f"| Count | {result['segment_a']['count']:,} | {result['segment_b']['count']:,} |\n"
                        f"| Conversion Rate | {result['segment_a']['conversion_rate']}% | {result['segment_b']['conversion_rate']}% |\n"
                        f"| Subscribers | {result['segment_a']['subscribers']:,} | {result['segment_b']['subscribers']:,} |",
            "data": result,
        }

    # Intent: Conversion rate / stats query
    if any(kw in msg for kw in ["conversion", "rate", "how many", "total", "average", "subscriber", "stats", "overview"]):
        job = _extract_job(message)
        filters = {}
        if job:
            filters["job"] = job
        age_min, age_max = _extract_age_range(message)
        if age_min:
            filters["age_min"] = age_min
        if age_max:
            filters["age_max"] = age_max
        result = query_data(filters=filters if filters else None, aggregation="count")
        filter_desc = ""
        if filters:
            parts = []
            if job:
                parts.append(f"job={job}")
            if age_min:
                parts.append(f"age>={age_min}")
            if age_max:
                parts.append(f"age<={age_max}")
            filter_desc = f" (filtered: {', '.join(parts)})"
        return {
            "intent": "query",
            "response": f"**Dataset Overview{filter_desc}**\n\n"
                        f"- Total customers: {result['total_rows']:,}\n"
                        f"- Subscribers: {result['subscribers']:,}\n"
                        f"- Non-subscribers: {result['non_subscribers']:,}\n"
                        f"- Conversion rate: {result['conversion_rate']}%",
            "data": result,
        }

    # Intent: Strategy advice
    if any(kw in msg for kw in ["strategy", "recommend", "advice", "suggest", "what should", "how to"]):
        result = generate_strategy_local(
            segment_profile={"avg_campaign": 1.5},
            propensity_score=0.55,
            top_factors=[
                {"feature": "euribor3m", "impact": -0.15, "direction": "negative"},
                {"feature": "contact", "impact": 0.08, "direction": "positive"},
                {"feature": "age", "impact": 0.05, "direction": "positive"},
            ],
            economic_context={"euribor3m": 1.3},
        )
        return {
            "intent": "strategy",
            "response": result,
            "data": {},
        }

    # Intent: Help / fallback
    return {
        "intent": "help",
        "response": "I can help you with:\n\n"
                    "- **Conversion rates** — \"What's the conversion rate?\"\n"
                    "- **Score a customer** — \"Score a 45-year-old retired customer\"\n"
                    "- **Compare segments** — \"Compare cellular vs telephone\"\n"
                    "- **Simulate campaigns** — \"Simulate a campaign with budget 1000\"\n"
                    "- **Strategy advice** — \"What strategy should I use?\"\n\n"
                    "Try asking one of these questions!",
        "data": {},
    }
