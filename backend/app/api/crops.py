"""
Crops API — Correction 5.

Open catalog endpoint + crop suggestion submission.

Routes:
  GET  /api/crops          — all active crops (any authenticated user)
  POST /api/crops/suggest  — submit a crop suggestion (any authenticated user)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import Optional

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.crop import Crop
from app.models.crop_suggestion import CropSuggestion, SuggestionStatus
from app.models.user import User
from app.schemas.market import CropSummary

router = APIRouter(prefix="/api/crops", tags=["Crops"])


class CropSuggestRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, description="Proposed crop name")
    category: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=500, description="Why this crop should be added")


class CropSuggestResponse(BaseModel):
    id: int
    suggested_name: str
    status: str
    message: str

    model_config = {"from_attributes": True}


@router.get(
    "",
    response_model=list[CropSummary],
    summary="List all active crops in the catalog",
    dependencies=[Depends(get_current_user)],
)
def list_all_crops(db: Session = Depends(get_db)):
    """
    Returns every active crop — used by buyer requirement forms,
    farmer crop management, and any other place that needs the full catalog.
    """
    return (
        db.query(Crop)
        .filter(Crop.is_active == True)  # noqa: E712
        .order_by(Crop.name)
        .all()
    )


@router.post(
    "/suggest",
    response_model=CropSuggestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a new crop suggestion for admin review",
)
def suggest_crop(
    payload: CropSuggestRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Any authenticated user can suggest a new crop.
    The suggestion is stored as PENDING — admin must approve before the
    crop appears in the catalog. Prevents duplicate names (case-insensitive).
    """
    name_clean = payload.name.strip()

    # Check if crop already exists in the catalog
    existing_crop = (
        db.query(Crop)
        .filter(func.lower(Crop.name) == name_clean.lower())
        .first()
    )
    if existing_crop:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"'{existing_crop.name}' is already in the crop catalog (id={existing_crop.id}). You can use it directly.",
        )

    # Check if a PENDING suggestion with the same name already exists
    existing_suggestion = (
        db.query(CropSuggestion)
        .filter(
            func.lower(CropSuggestion.suggested_name) == name_clean.lower(),
            CropSuggestion.status == SuggestionStatus.PENDING,
        )
        .first()
    )
    if existing_suggestion:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A suggestion for '{name_clean}' is already pending admin review.",
        )

    suggestion = CropSuggestion(
        suggested_name=name_clean,
        category=payload.category,
        notes=payload.notes,
        suggested_by_user_id=current_user.id,
        status=SuggestionStatus.PENDING,
    )
    db.add(suggestion)
    db.commit()
    db.refresh(suggestion)

    return CropSuggestResponse(
        id=suggestion.id,
        suggested_name=suggestion.suggested_name,
        status=suggestion.status,
        message=f"Your suggestion for '{name_clean}' has been submitted. An admin will review it shortly.",
    )
