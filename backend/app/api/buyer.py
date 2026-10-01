"""
Buyer module API — Phase 9.

All endpoints require a valid JWT. Buyer-only endpoints require role=BUYER.
Farmer-discovery endpoint requires role=FARMER.

Routes:
  GET  /api/buyer/profile
  PUT  /api/buyer/profile
  POST /api/buyer/requirements
  GET  /api/buyer/requirements
  GET  /api/buyer/requirements/{id}
  PUT  /api/buyer/requirements/{id}
  DELETE /api/buyer/requirements/{id}
  GET  /api/buyer/matches/{requirement_id}

Farmer-side (cross-module, FARMER role):
  GET  /api/farmer/buyer-requirements   (in farmer.py)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, require_role
from app.database.session import get_db
from app.models.buyer import Buyer
from app.models.buyer_requirement import BuyerRequirement, RequirementStatus
from app.models.crop import Crop
from app.models.farmer import Farmer
from app.models.farmer_crop import FarmerCrop
from app.models.user import User, UserRole
from app.schemas.buyer import (
    BuyerProfileResponse,
    BuyerProfileUpdate,
    BuyerRequirementCreate,
    BuyerRequirementResponse,
    BuyerRequirementUpdate,
    FarmerMatchResponse,
)

router = APIRouter(prefix="/api/buyer", tags=["Buyer"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_or_create_buyer(user: User, db: Session) -> Buyer:
    buyer = db.query(Buyer).filter_by(user_id=user.id).first()
    if not buyer:
        buyer = Buyer(user_id=user.id)
        db.add(buyer)
        db.commit()
        db.refresh(buyer)
    return buyer


def _build_profile_response(buyer: Buyer, user: User) -> BuyerProfileResponse:
    return BuyerProfileResponse(
        id=buyer.id,
        user_id=buyer.user_id,
        full_name=user.full_name,
        email=user.email,
        phone=user.phone,
        business_name=buyer.business_name,
        business_type=buyer.business_type,
        location=buyer.location,
        district=buyer.district,
        state=buyer.state,
        created_at=buyer.created_at,
        updated_at=buyer.updated_at,
    )


def _req_response(req: BuyerRequirement) -> BuyerRequirementResponse:
    return BuyerRequirementResponse(
        id=req.id,
        buyer_id=req.buyer_id,
        crop_id=req.crop_id,
        crop_name=req.crop.name if req.crop else None,
        quantity=float(req.quantity) if req.quantity is not None else None,
        minimum_price=float(req.minimum_price) if req.minimum_price is not None else None,
        maximum_price=float(req.maximum_price) if req.maximum_price is not None else None,
        location=req.location,
        district=req.district,
        state=req.state,
        status=req.status,
        created_at=req.created_at,
        updated_at=req.updated_at,
    )


# ── Profile ───────────────────────────────────────────────────────────────────

@router.get(
    "/profile",
    response_model=BuyerProfileResponse,
    summary="Get the authenticated buyer's profile",
    dependencies=[Depends(require_role(UserRole.BUYER))],
)
def get_buyer_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    buyer = _get_or_create_buyer(current_user, db)
    return _build_profile_response(buyer, current_user)


@router.put(
    "/profile",
    response_model=BuyerProfileResponse,
    summary="Update the authenticated buyer's profile",
    dependencies=[Depends(require_role(UserRole.BUYER))],
)
def update_buyer_profile(
    payload: BuyerProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    buyer = _get_or_create_buyer(current_user, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(buyer, field, value)
    db.commit()
    db.refresh(buyer)
    return _build_profile_response(buyer, current_user)


# ── Requirements ──────────────────────────────────────────────────────────────

@router.post(
    "/requirements",
    response_model=BuyerRequirementResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Post a new purchase requirement",
    dependencies=[Depends(require_role(UserRole.BUYER))],
)
def create_requirement(
    payload: BuyerRequirementCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    buyer = _get_or_create_buyer(current_user, db)

    crop = db.query(Crop).filter_by(id=payload.crop_id, is_active=True).first()
    if not crop:
        raise HTTPException(status_code=404, detail=f"Crop id={payload.crop_id} not found.")

    req = BuyerRequirement(
        buyer_id=buyer.id,
        crop_id=payload.crop_id,
        quantity=payload.quantity,
        minimum_price=payload.minimum_price,
        maximum_price=payload.maximum_price,
        location=payload.location,
        district=payload.district,
        state=payload.state,
        status=RequirementStatus.ACTIVE,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    req = db.query(BuyerRequirement).options(joinedload(BuyerRequirement.crop)).filter_by(id=req.id).first()
    return _req_response(req)


@router.get(
    "/requirements",
    response_model=list[BuyerRequirementResponse],
    summary="List all requirements for the authenticated buyer",
    dependencies=[Depends(require_role(UserRole.BUYER))],
)
def list_requirements(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    buyer = _get_or_create_buyer(current_user, db)
    reqs = (
        db.query(BuyerRequirement)
        .options(joinedload(BuyerRequirement.crop))
        .filter_by(buyer_id=buyer.id)
        .order_by(BuyerRequirement.created_at.desc())
        .all()
    )
    return [_req_response(r) for r in reqs]


@router.get(
    "/requirements/{requirement_id}",
    response_model=BuyerRequirementResponse,
    summary="Get a single requirement by ID",
    dependencies=[Depends(require_role(UserRole.BUYER))],
)
def get_requirement(
    requirement_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    buyer = _get_or_create_buyer(current_user, db)
    req = (
        db.query(BuyerRequirement)
        .options(joinedload(BuyerRequirement.crop))
        .filter_by(id=requirement_id, buyer_id=buyer.id)
        .first()
    )
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found.")
    return _req_response(req)


@router.put(
    "/requirements/{requirement_id}",
    response_model=BuyerRequirementResponse,
    summary="Update a purchase requirement",
    dependencies=[Depends(require_role(UserRole.BUYER))],
)
def update_requirement(
    requirement_id: int,
    payload: BuyerRequirementUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    buyer = _get_or_create_buyer(current_user, db)
    req = db.query(BuyerRequirement).filter_by(id=requirement_id, buyer_id=buyer.id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found.")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(req, field, value)
    db.commit()
    db.refresh(req)
    req = db.query(BuyerRequirement).options(joinedload(BuyerRequirement.crop)).filter_by(id=req.id).first()
    return _req_response(req)


@router.delete(
    "/requirements/{requirement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel/delete a purchase requirement",
    dependencies=[Depends(require_role(UserRole.BUYER))],
)
def delete_requirement(
    requirement_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    buyer = _get_or_create_buyer(current_user, db)
    req = db.query(BuyerRequirement).filter_by(id=requirement_id, buyer_id=buyer.id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found.")
    db.delete(req)
    db.commit()


# ── Matching: buyer finds farmers ─────────────────────────────────────────────

@router.get(
    "/matches/{requirement_id}",
    response_model=list[FarmerMatchResponse],
    summary="Find farmers matching a buyer requirement",
    dependencies=[Depends(require_role(UserRole.BUYER))],
)
def find_matching_farmers(
    requirement_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    buyer = _get_or_create_buyer(current_user, db)
    req = db.query(BuyerRequirement).filter_by(id=requirement_id, buyer_id=buyer.id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found.")
    if req.status != RequirementStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Requirement is not active.")

    # Find available farmer crops for this crop
    farmer_crops = (
        db.query(FarmerCrop)
        .options(
            joinedload(FarmerCrop.farmer).joinedload(Farmer.user),
            joinedload(FarmerCrop.crop),
        )
        .filter(
            FarmerCrop.crop_id == req.crop_id,
            FarmerCrop.is_available == True,  # noqa: E712
            FarmerCrop.quantity > 0,
        )
        .all()
    )

    results = []
    for fc in farmer_crops:
        farmer = fc.farmer
        user = farmer.user

        # Location compatibility: if requirement has district, prefer same district
        # but don't hard-exclude — show all, sorted client-side or by distance later
        results.append(
            FarmerMatchResponse(
                farmer_id=farmer.id,
                farmer_crop_id=fc.id,
                crop_id=fc.crop_id,
                crop_name=fc.crop.name,
                available_quantity=float(fc.quantity),
                unit=fc.unit.value,
                location=farmer.village,
                district=farmer.district,
                state=farmer.state,
                farmer_name=user.full_name,
                # phone withheld until interest accepted — set None here
                phone=None,
            )
        )

    return results
