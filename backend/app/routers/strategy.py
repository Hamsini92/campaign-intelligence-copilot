from fastapi import APIRouter
from app.schemas.strategy import StrategyRequest
from app.config import LOCAL_MODE
import os

os.environ["LOCAL_MODE"] = str(LOCAL_MODE).lower()

from strategy_advisor.handler import generate_strategy_local, generate_strategy

router = APIRouter()


@router.post("/api/strategy")
def strategy(req: StrategyRequest):
    if LOCAL_MODE:
        result = generate_strategy_local(
            segment_profile=req.segment_profile,
            propensity_score=req.propensity_score,
            top_factors=req.top_factors,
            economic_context=req.economic_context,
        )
    else:
        result = generate_strategy(
            segment_profile=req.segment_profile,
            propensity_score=req.propensity_score,
            top_factors=req.top_factors,
            economic_context=req.economic_context,
        )
    return {"response": result}
