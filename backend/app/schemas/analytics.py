from pydantic import BaseModel, Field
from typing import Optional


class QueryRequest(BaseModel):
    filters: Optional[dict] = None
    aggregation: Optional[str] = None
    group_by_field: Optional[str] = None


class CompareRequest(BaseModel):
    segment_a: dict = Field(default_factory=dict)
    segment_b: dict = Field(default_factory=dict)
    metric: str = "conversion_rate"


class SimulateRequest(BaseModel):
    target_filters: dict = Field(default_factory=dict)
    budget_contacts: int = Field(default=500, ge=1)
