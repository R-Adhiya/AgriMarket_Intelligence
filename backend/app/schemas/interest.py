"""
Pydantic schemas for TransactionInterest — Phase 9.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.transaction_interest import InterestStatus


class InterestCreate(BaseModel):
    farmer_id: int
    crop_id: int
    requirement_id: Optional[int] = None
    quantity: Optional[float] = Field(None, gt=0)
    notes: Optional[str] = Field(None, max_length=1000)


class InterestResponse(BaseModel):
    id: int
    farmer_id: int
    buyer_id: int
    crop_id: int
    requirement_id: Optional[int] = None
    crop_name: Optional[str] = None
    quantity: Optional[float] = None
    notes: Optional[str] = None
    status: InterestStatus
    # Contact info — only populated when status == ACCEPTED
    farmer_name: Optional[str] = None
    farmer_phone: Optional[str] = None
    farmer_location: Optional[str] = None
    buyer_name: Optional[str] = None
    buyer_phone: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
