"""Pydantic schemas for the Farmer module (Phase 4)."""

from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models.farmer_crop import QuantityUnit


# ── Farmer Profile ────────────────────────────────────────────────────────────

class FarmerProfileUpdate(BaseModel):
    """Fields a farmer can set or update on their profile."""
    village: Optional[str] = Field(None, max_length=255, description="Village / city / locality")
    district: Optional[str] = Field(None, max_length=255)
    state: Optional[str] = Field(None, max_length=255)
    farm_size: Optional[float] = Field(None, gt=0, description="Farm size in acres")

    @field_validator("village", "district", "state", mode="before")
    @classmethod
    def strip_strings(cls, v):
        if isinstance(v, str):
            v = v.strip()
            return v if v else None
        return v


class FarmerProfileResponse(BaseModel):
    id: int
    user_id: int
    full_name: str          # from the related User
    email: str
    phone: Optional[str]
    village: Optional[str]
    district: Optional[str]
    state: Optional[str]
    farm_size: Optional[float]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Farmer Crop ───────────────────────────────────────────────────────────────

class CropInfo(BaseModel):
    """Embedded crop reference inside FarmerCropResponse."""
    id: int
    name: str
    category: Optional[str]

    model_config = {"from_attributes": True}


class FarmerCropCreate(BaseModel):
    crop_id: int = Field(..., gt=0)
    quantity: float = Field(..., gt=0, description="Must be greater than 0")
    unit: QuantityUnit = QuantityUnit.QUINTAL
    notes: Optional[str] = Field(None, max_length=1000)

    @field_validator("quantity")
    @classmethod
    def quantity_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Quantity must be greater than 0.")
        return v


class FarmerCropUpdate(BaseModel):
    quantity: Optional[float] = Field(None, gt=0)
    unit: Optional[QuantityUnit] = None
    notes: Optional[str] = Field(None, max_length=1000)

    @field_validator("quantity")
    @classmethod
    def quantity_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Quantity must be greater than 0.")
        return v


class FarmerCropResponse(BaseModel):
    id: int
    farmer_id: int
    crop: CropInfo
    quantity: float
    unit: QuantityUnit
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
