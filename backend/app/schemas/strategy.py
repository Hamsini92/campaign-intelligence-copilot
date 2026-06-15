from pydantic import BaseModel, Field
from typing import Optional


class StrategyRequest(BaseModel):
    segment_profile: dict = Field(default_factory=dict)
    propensity_score: float = 0.5
    top_factors: list = Field(default_factory=list)
    economic_context: Optional[dict] = None
