"""
Pydantic schemas for the Buyer module — Phase 9.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.models.buyer_requirement import RequirementStatus


# ── Buyer Profile ─────────────────────────────────────────────────────────────

class BuyerProfileResponse(BaseModel):
    id: int
    user_id: int
    full_name: Optional[str] = None
    email: str
    phone: Optional[str] = None
    business_name: Optional[str] = None
    business_type: Optional[str] = None
    location: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BuyerProfileUpdate(BaseModel):
    business_name: Optional[str] = Field(None, max_length=255)
    business_type: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = Field(None, max_length=255)
    district: Optional[str] = Field(None, max_length=255)
    state: Optional[str] = Field(None, max_length=255)


# ── Buyer Requirements ────────────────────────────────────────────────────────

class BuyerRequirementCreate(BaseModel):
    crop_id: int
    quantity: float = Field(..., gt=0, description="Required quantity (must be > 0)")
    minimum_price: Optional[float] = Field(None, ge=0)
    maximum_price: Optional[float] = Field(None, ge=0)
    location: Optional[str] = Field(None, max_length=255)
    district: Optional[str] = Field(None, max_length=255)
    state: Optional[str] = Field(None, max_length=255)

    @field_validator("maximum_price")
    @classmethod
    def max_gte_min(cls, v, info):
        min_p = info.data.get("minimum_price")
        if v is not None and min_p is not None and v < min_p:
            raise ValueError("maximum_price must be >= minimum_price")
        return v


class BuyerRequirementUpdate(BaseModel):
    quantity: Optional[float] = Field(None, gt=0)
    minimum_price: Optional[float] = Field(None, ge=0)
    maximum_price: Optional[float] = Field(None, ge=0)
    location: Optional[str] = Field(None, max_length=255)
    district: Optional[str] = Field(None, max_length=255)
    state: Optional[str] = Field(None, max_length=255)
    status: Optional[RequirementStatus] = None


class BuyerRequirementResponse(BaseModel):
    id: int
    buyer_id: int
    crop_id: int
    crop_name: Optional[str] = None
    quantity: Optional[float] = None
    minimum_price: Optional[float] = None
    maximum_price: Optional[float] = None
    location: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    status: RequirementStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Farmer Match (for buyer searching farmers) ────────────────────────────────

class FarmerMatchResponse(BaseModel):
    farmer_id: int
    farmer_crop_id: int
    crop_id: int
    crop_name: str
    available_quantity: float
    unit: str
    location: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    # Contact only revealed after interest is accepted
    farmer_name: Optional[str] = None   # shown always (first name / display)
    phone: Optional[str] = None         # None until accepted

    model_config = {"from_attributes": True}


# ── Buyer Requirement Match (for farmer discovering buyers) ───────────────────

class BuyerRequirementPublicResponse(BaseModel):
    id: int
    crop_id: int
    crop_name: str
    quantity: Optional[float] = None
    minimum_price: Optional[float] = None
    maximum_price: Optional[float] = None
    location: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    buyer_name: Optional[str] = None    # business name (no private data)
    status: RequirementStatus
    created_at: datetime

    model_config = {"from_attributes": True}
