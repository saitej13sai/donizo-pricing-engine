from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class MaterialOut(BaseModel):
    material_name: str
    description: str
    unit_price: float
    unit: str
    region: str
    vendor: Optional[str] = None
    vat_rate: Optional[float] = None
    quality_score: Optional[int] = None
    updated_at: datetime
    source: str
    similarity_score: float = Field(..., ge=0, le=1)
    confidence_tier: str

class ProposalIn(BaseModel):
    transcript: str
    region: Optional[str] = None
    build_type: Optional[str] = Field(default="renovation")

class TaskOut(BaseModel):
    label: str
    materials: list
    estimated_duration: str
    margin_protected_price: float
    confidence_score: float

class ProposalOut(BaseModel):
    tasks: list[TaskOut]
    total_estimate: float

class FeedbackIn(BaseModel):
    task_id: str
    quote_id: str
    user_type: str
    verdict: str
    comment: Optional[str] = None
    target_component: Optional[str] = None
