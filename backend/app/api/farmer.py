"""
Farmer module API — Phase 4 + Phase 9 additions.

All endpoints require a valid JWT with role=FARMER.

Routes:
  GET    /api/farmer/profile
  PUT    /api/farmer/profile
  GET    /api/farmer/crops
  POST   /api/farmer/crops
  PUT    /api/farmer/crops/{crop_entry_id}
  DELETE /api/farmer/crops/{crop_entry_id}

Phase 9 additions:
  GET    /api/farmer/buyer-requirements   -- discover active buyer requirements
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, require_role
from app.database.session import get_db
from app.models.crop import Crop
from app.models.farmer import Farmer
from app.models.farmer_crop import FarmerCrop
from app.models.buyer_requirement import BuyerRequirement, RequirementStatus
from app.models.buyer import Buyer
from app.models.user import User, UserRole
from app.schemas.farmer import (
    FarmerCropCreate,
    FarmerCropResponse,
    FarmerCropUpdate,
    FarmerProfileResponse,
    FarmerProfileUpdate,
)
from app.schemas.buyer import BuyerRequirementPublicResponse

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



# ── Phase 9: Farmer discovers active buyer requirements ───────────────────────

@router.get(
    "/buyer-requirements",
    response_model=list[BuyerRequirementPublicResponse],
    summary="List active buyer requirements matching the farmer's crops",
)
def list_buyer_requirements(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return ACTIVE buyer requirements for crops this farmer has listed.
    Shows public buyer info only (no private contact data).
    """
    farmer = db.query(Farmer).filter_by(user_id=current_user.id).first()
    if not farmer:
        return []

    # Get crop IDs this farmer has (available)
    farmer_crop_ids = (
        db.query(FarmerCrop.crop_id)
        .filter_by(farmer_id=farmer.id, is_available=True)
        .distinct()
        .all()
    )
    crop_ids = [r[0] for r in farmer_crop_ids]
    if not crop_ids:
        return []

    reqs = (
        db.query(BuyerRequirement)
        .options(
            joinedload(BuyerRequirement.crop),
            joinedload(BuyerRequirement.buyer).joinedload(Buyer.user),
        )
        .filter(
            BuyerRequirement.crop_id.in_(crop_ids),
            BuyerRequirement.status == RequirementStatus.ACTIVE,
        )
        .order_by(BuyerRequirement.created_at.desc())
        .all()
    )

    results = []
    for r in reqs:
        buyer_user = r.buyer.user if r.buyer else None
        results.append(
            BuyerRequirementPublicResponse(
                id=r.id,
                crop_id=r.crop_id,
                crop_name=r.crop.name if r.crop else "",
                quantity=float(r.quantity) if r.quantity is not None else None,
                minimum_price=float(r.minimum_price) if r.minimum_price is not None else None,
                maximum_price=float(r.maximum_price) if r.maximum_price is not None else None,
                location=r.location,
                district=r.district,
                state=r.state,
                buyer_name=r.buyer.business_name or (buyer_user.full_name if buyer_user else None),
                status=r.status,
                created_at=r.created_at,
            )
        )
    return results
