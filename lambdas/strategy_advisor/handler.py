import json
import os
import boto3

BEDROCK_REGION = os.environ.get("BEDROCK_REGION", "us-east-1")
MODEL_ID = os.environ.get("MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0")

_client = None


def _get_bedrock_client():
    global _client
    if _client is None:
        _client = boto3.client("bedrock-runtime", region_name=BEDROCK_REGION)
    return _client


def _call_llm(prompt):
    """Call Bedrock FM for strategy generation."""
    client = _get_bedrock_client()

    response = client.invoke_model(
        modelId=MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        })
    )

    result = json.loads(response["body"].read())
    return result["content"][0]["text"]


def generate_strategy(segment_profile, propensity_score, top_factors, economic_context=None):
    """Generate a contact strategy for a customer segment."""
    prompt = f"""You are a banking campaign strategy advisor. Based on the following
customer segment data, provide a concise, actionable contact strategy.

SEGMENT PROFILE:
{json.dumps(segment_profile, indent=2)}

PROPENSITY SCORE: {propensity_score}

KEY FACTORS DRIVING THE SCORE:
{json.dumps(top_factors, indent=2)}

ECONOMIC CONTEXT:
{json.dumps(economic_context or {}, indent=2)}

Provide your strategy in this format:
1. PRIORITY: High/Medium/Low (based on score)
2. CHANNEL: Recommended contact method and why
3. TIMING: Best time to contact
4. MESSAGING: Key talking points (2-3 bullets)
5. CAUTION: Any risks or things to avoid
6. EXPECTED OUTCOME: Realistic conversion expectation

Keep it concise and actionable. Do not give personal financial advice.
Base all recommendations on the data provided."""

    return _call_llm(prompt)


def explain_trend(trend_data, question):
    """Explain a campaign trend or anomaly."""
    prompt = f"""You are a banking campaign analyst. Based on the following data,
answer the question below.

CAMPAIGN DATA:
{json.dumps(trend_data, indent=2)}

QUESTION: {question}

Provide a data-driven explanation. Cite specific numbers from the data.
Do not invent statistics. If the data doesn't support a conclusion, say so.
Keep your response concise (3-5 key points)."""

    return _call_llm(prompt)


# For local testing without Bedrock
def generate_strategy_local(segment_profile, propensity_score, top_factors, economic_context=None):
    """Generate strategy without calling Bedrock (for local testing)."""
    score = propensity_score

    if score >= 0.7:
        priority = "HIGH"
        outcome = "Strong conversion expected"
    elif score >= 0.4:
        priority = "MEDIUM"
        outcome = "Moderate conversion potential"
    else:
        priority = "LOW"
        outcome = "Low conversion likelihood — consider skipping"

    # Determine channel recommendation from factors
    channel = "Cellular (historically 2.8x better conversion than telephone)"

    # Check for contact fatigue
    campaign_count = segment_profile.get("avg_campaign", 1)
    if campaign_count > 2:
        caution = f"Contact fatigue risk — segment averages {campaign_count} contacts. Do not exceed 3."
    else:
        caution = "No fatigue risk detected."

    # Economic context
    euribor = economic_context.get("euribor3m", 3.0) if economic_context else 3.0
    if euribor < 2.0:
        econ_msg = f"Euribor is low ({euribor}%) — favorable for term deposits. Emphasize locking in rates."
    elif euribor > 4.0:
        econ_msg = f"Euribor is high ({euribor}%) — customers may prefer flexible savings. Harder sell."
    else:
        econ_msg = f"Euribor is moderate ({euribor}%) — neutral economic environment."

    # Build top factor explanations
    factor_lines = []
    for f in top_factors[:3]:
        direction = "increases" if f["direction"] == "positive" else "decreases"
        factor_lines.append(f"- {f['feature']} {direction} likelihood (impact: {f['impact']})")

    strategy = f"""STRATEGY RECOMMENDATION
========================
PRIORITY: {priority}
SCORE: {round(score * 100, 1)}%

CHANNEL: {channel}

TIMING: Thursday or Friday (historical best for similar segments)

KEY FACTORS:
{chr(10).join(factor_lines)}

ECONOMIC CONTEXT: {econ_msg}

MESSAGING:
- Lead with guaranteed returns and capital security
- Mention current rate environment
- Keep call under 5 minutes for this segment

CAUTION: {caution}

EXPECTED OUTCOME: {outcome}"""

    return strategy


# AWS Lambda handler
def lambda_handler(event, context):
    """Entry point for AWS Lambda / Bedrock Agent Action Group."""
    try:
        api_path = event.get("apiPath", "")
        body = json.loads(event.get("requestBody", {}).get("content", {}).get("application/json", {}).get("body", "{}"))

        use_local = os.environ.get("LOCAL_MODE", "false").lower() == "true"

        if api_path == "/strategy":
            if use_local:
                result = generate_strategy_local(
                    segment_profile=body.get("segment_profile", {}),
                    propensity_score=body.get("propensity_score", 0.5),
                    top_factors=body.get("top_factors", []),
                    economic_context=body.get("economic_context")
                )
            else:
                result = generate_strategy(
                    segment_profile=body.get("segment_profile", {}),
                    propensity_score=body.get("propensity_score", 0.5),
                    top_factors=body.get("top_factors", []),
                    economic_context=body.get("economic_context")
                )
        elif api_path == "/explain-trend":
            if use_local:
                result = "Local mode: trend explanation requires Bedrock. Deploy to AWS to use this feature."
            else:
                result = explain_trend(
                    trend_data=body.get("trend_data", {}),
                    question=body.get("question", "")
                )
        else:
            result = {"error": f"Unknown path: {api_path}"}

        return {
            "statusCode": 200,
            "body": json.dumps({"response": result}) if isinstance(result, str) else json.dumps(result)
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
