"""
Farmer module API — Phase 4.

All endpoints require a valid JWT with role=FARMER.

Routes:
  GET    /api/farmer/profile
  PUT    /api/farmer/profile
  GET    /api/farmer/crops
  POST   /api/farmer/crops
  PUT    /api/farmer/crops/{crop_entry_id}
  DELETE /api/farmer/crops/{crop_entry_id}
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.database.session import get_db
from app.models.crop import Crop
from app.models.farmer import Farmer
from app.models.farmer_crop import FarmerCrop
from app.models.user import User, UserRole
from app.schemas.farmer import (
    FarmerCropCreate,
    FarmerCropResponse,
    FarmerCropUpdate,
    FarmerProfileResponse,
    FarmerProfileUpdate,
)

router = APIRouter(
    prefix="/api/farmer",
    tags=["Farmer"],
    dependencies=[Depends(require_role(UserRole.FARMER))],
)

# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_or_create_farmer(user: User, db: Session) -> Farmer:
    """Return the farmer profile for this user, creating one if absent."""
    farmer = db.query(Farmer).filter_by(user_id=user.id).first()
    if not farmer:
        farmer = Farmer(user_id=user.id)
        db.add(farmer)
        db.commit()
        db.refresh(farmer)
    return farmer


def _build_profile_response(farmer: Farmer, user: User) -> FarmerProfileResponse:
    return FarmerProfileResponse(
        id=farmer.id,
        user_id=farmer.user_id,
        full_name=user.full_name,
        email=user.email,
        phone=user.phone,
        village=farmer.village,
        district=farmer.district,
        state=farmer.state,
        farm_size=float(farmer.farm_size) if farmer.farm_size is not None else None,
        created_at=farmer.created_at,
        updated_at=farmer.updated_at,
    )


# ── Profile endpoints ─────────────────────────────────────────────────────────

@router.get(
    "/profile",
    response_model=FarmerProfileResponse,
    summary="Get the authenticated farmer's profile",
)
def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    farmer = _get_or_create_farmer(current_user, db)
    return _build_profile_response(farmer, current_user)


@router.put(
    "/profile",
    response_model=FarmerProfileResponse,
    summary="Create or update the authenticated farmer's profile",
)
def update_profile(
    payload: FarmerProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    farmer = _get_or_create_farmer(current_user, db)

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(farmer, field, value)

    db.commit()
    db.refresh(farmer)
    return _build_profile_response(farmer, current_user)


# ── Crop endpoints ────────────────────────────────────────────────────────────

@router.get(
    "/crops",
    response_model=list[FarmerCropResponse],
    summary="List all crop entries for the authenticated farmer",
)
def list_crops(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    farmer = _get_or_create_farmer(current_user, db)
    entries = (
        db.query(FarmerCrop)
        .filter_by(farmer_id=farmer.id)
        .order_by(FarmerCrop.created_at.desc())
        .all()
    )
    return entries


@router.post(
    "/crops",
    response_model=FarmerCropResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a crop entry for the authenticated farmer",
)
def add_crop(
    payload: FarmerCropCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    farmer = _get_or_create_farmer(current_user, db)

    # Verify the crop exists and is active
    crop = db.query(Crop).filter_by(id=payload.crop_id, is_active=True).first()
    if not crop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Crop with id={payload.crop_id} not found or inactive.",
        )

    entry = FarmerCrop(
        farmer_id=farmer.id,
        crop_id=payload.crop_id,
        quantity=payload.quantity,
        unit=payload.unit,
        notes=payload.notes,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.put(
    "/crops/{crop_entry_id}",
    response_model=FarmerCropResponse,
    summary="Update a crop entry",
)
def update_crop(
    crop_entry_id: int,
    payload: FarmerCropUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    farmer = _get_or_create_farmer(current_user, db)
    entry = db.query(FarmerCrop).filter_by(id=crop_entry_id, farmer_id=farmer.id).first()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crop entry not found.")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(entry, field, value)

    db.commit()
    db.refresh(entry)
    return entry


@router.delete(
    "/crops/{crop_entry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a crop entry",
)
def delete_crop(
    crop_entry_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    farmer = _get_or_create_farmer(current_user, db)
    entry = db.query(FarmerCrop).filter_by(id=crop_entry_id, farmer_id=farmer.id).first()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crop entry not found.")

    db.delete(entry)
    db.commit()
