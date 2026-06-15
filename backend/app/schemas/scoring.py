from pydantic import BaseModel, Field
from typing import Optional


class CustomerInput(BaseModel):
    age: int = Field(default=40, ge=17, le=100)
    job: str = "admin."
    marital: str = "married"
    education: str = "university.degree"
    default: str = "no"
    contact: str = "cellular"
    campaign: int = Field(default=1, ge=1)
    pdays: int = Field(default=999, ge=0)
    previous: int = Field(default=0, ge=0)
    poutcome: str = "nonexistent"
    euribor3m: float = 3.0
    cons_price_idx: float = 93.0
    cons_conf_idx: float = -40.0
    month: Optional[str] = None


class ScoreResponse(BaseModel):
    probability: float
    tier: str
    will_subscribe: bool
    threshold: float
    top_factors: list


class BatchScoreRequest(BaseModel):
    customers: list[dict]
