"""
TransactionInterest API — Phase 9.

Interest/contact request workflow between buyers and farmers.

Status flow:  PENDING -> ACCEPTED | REJECTED | CANCELLED

Routes:
  POST   /api/interests                 buyer sends interest to farmer
  GET    /api/interests/sent            buyer sees their sent interests
  GET    /api/interests/received        farmer sees received interests
  PUT    /api/interests/{id}/accept     farmer accepts
  PUT    /api/interests/{id}/reject     farmer rejects
  DELETE /api/interests/{id}            buyer cancels (own PENDING only)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, require_role
from app.database.session import get_db
from app.models.buyer import Buyer
from app.models.buyer_requirement import BuyerRequirement
from app.models.crop import Crop
from app.models.farmer import Farmer
from app.models.farmer_crop import FarmerCrop
from app.models.transaction_interest import InterestStatus, TransactionInterest, is_valid_transition
from app.models.user import User, UserRole
from app.schemas.interest import InterestCreate, InterestResponse

router = APIRouter(prefix="/api/interests", tags=["Interests"])

_INTEREST_OPTS = [
    joinedload(TransactionInterest.farmer).joinedload(Farmer.user),
    joinedload(TransactionInterest.buyer).joinedload(Buyer.user),
    joinedload(TransactionInterest.crop),
]


# ── Helper: build response dict ───────────────────────────────────────────────

def _build_response(interest: TransactionInterest, reveal_contact: bool = False) -> InterestResponse:
    farmer_user = interest.farmer.user if interest.farmer else None
    buyer_user = interest.buyer.user if interest.buyer else None
    accepted = interest.status == InterestStatus.ACCEPTED

    return InterestResponse(
        id=interest.id,
        farmer_id=interest.farmer_id,
        buyer_id=interest.buyer_id,
        crop_id=interest.crop_id,
        requirement_id=interest.requirement_id,
        crop_name=interest.crop.name if interest.crop else None,
        quantity=float(interest.quantity) if interest.quantity is not None else None,
        notes=interest.notes,
        status=interest.status,
        # Reveal contact on both sides only after acceptance
        farmer_name=farmer_user.full_name if farmer_user else None,
        farmer_phone=farmer_user.phone if (farmer_user and accepted) else None,
        farmer_location=interest.farmer.village if (interest.farmer and accepted) else None,
        buyer_name=(
            interest.buyer.business_name or buyer_user.full_name
            if buyer_user else None
        ),
        buyer_phone=buyer_user.phone if (buyer_user and accepted) else None,
        created_at=interest.created_at,
        updated_at=interest.updated_at,
    )


# ── POST: buyer sends interest ────────────────────────────────────────────────

@router.post(
    "",
    response_model=InterestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Buyer sends an interest/contact request to a farmer",
    dependencies=[Depends(require_role(UserRole.BUYER))],
)
def send_interest(
    payload: InterestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    buyer = db.query(Buyer).filter_by(user_id=current_user.id).first()
    if not buyer:
        buyer = Buyer(user_id=current_user.id)
        db.add(buyer)
        db.commit()
        db.refresh(buyer)

    # Validate farmer exists
    farmer = db.query(Farmer).filter_by(id=payload.farmer_id).first()
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found.")

    # Validate crop
    crop = db.query(Crop).filter_by(id=payload.crop_id, is_active=True).first()
    if not crop:
        raise HTTPException(status_code=404, detail="Crop not found.")

    # Validate requirement if provided
    if payload.requirement_id:
        req = db.query(BuyerRequirement).filter_by(id=payload.requirement_id, buyer_id=buyer.id).first()
        if not req:
            raise HTTPException(status_code=404, detail="Requirement not found.")

    # Duplicate prevention: same buyer, farmer, crop, requirement with active status
    existing = (
        db.query(TransactionInterest)
        .filter(
            TransactionInterest.buyer_id == buyer.id,
            TransactionInterest.farmer_id == payload.farmer_id,
            TransactionInterest.crop_id == payload.crop_id,
            TransactionInterest.requirement_id == payload.requirement_id,
            TransactionInterest.status.in_([InterestStatus.PENDING, InterestStatus.INTERESTED]),
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An active interest request already exists for this farmer/crop/requirement.",
        )

    interest = TransactionInterest(
        farmer_id=payload.farmer_id,
        buyer_id=buyer.id,
        crop_id=payload.crop_id,
        requirement_id=payload.requirement_id,
        quantity=payload.quantity,
        notes=payload.notes,
        status=InterestStatus.PENDING,
    )
    db.add(interest)
    db.commit()
    db.refresh(interest)

    interest = (
        db.query(TransactionInterest)
        .options(*_INTEREST_OPTS)
        .filter_by(id=interest.id)
        .first()
    )
    return _build_response(interest)


# ── GET: buyer sees sent interests ────────────────────────────────────────────

@router.get(
    "/sent",
    response_model=list[InterestResponse],
    summary="List all interest requests sent by the authenticated buyer",
    dependencies=[Depends(require_role(UserRole.BUYER))],
)
def list_sent(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    buyer = db.query(Buyer).filter_by(user_id=current_user.id).first()
    if not buyer:
        return []
    interests = (
        db.query(TransactionInterest)
        .options(*_INTEREST_OPTS)
        .filter_by(buyer_id=buyer.id)
        .order_by(TransactionInterest.created_at.desc())
        .all()
    )
    return [_build_response(i) for i in interests]


# ── GET: farmer sees received interests ───────────────────────────────────────

@router.get(
    "/received",
    response_model=list[InterestResponse],
    summary="List all interest requests received by the authenticated farmer",
    dependencies=[Depends(require_role(UserRole.FARMER))],
)
def list_received(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    farmer = db.query(Farmer).filter_by(user_id=current_user.id).first()
    if not farmer:
        return []
    interests = (
        db.query(TransactionInterest)
        .options(*_INTEREST_OPTS)
        .filter_by(farmer_id=farmer.id)
        .order_by(TransactionInterest.created_at.desc())
        .all()
    )
    return [_build_response(i) for i in interests]


# ── PUT: farmer accepts ───────────────────────────────────────────────────────

@router.put(
    "/{interest_id}/accept",
    response_model=InterestResponse,
    summary="Farmer accepts an interest request",
    dependencies=[Depends(require_role(UserRole.FARMER))],
)
def accept_interest(
    interest_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    farmer = db.query(Farmer).filter_by(user_id=current_user.id).first()
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer profile not found.")

    interest = (
        db.query(TransactionInterest)
        .options(*_INTEREST_OPTS)
        .filter_by(id=interest_id, farmer_id=farmer.id)
        .first()
    )
    if not interest:
        raise HTTPException(status_code=404, detail="Interest request not found.")

    if not is_valid_transition(interest.status, InterestStatus.ACCEPTED):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot accept a request with status '{interest.status}'.",
        )

    interest.status = InterestStatus.ACCEPTED
    db.commit()
    db.refresh(interest)
    interest = db.query(TransactionInterest).options(*_INTEREST_OPTS).filter_by(id=interest.id).first()
    return _build_response(interest, reveal_contact=True)


# ── PUT: farmer rejects ───────────────────────────────────────────────────────

@router.put(
    "/{interest_id}/reject",
    response_model=InterestResponse,
    summary="Farmer rejects an interest request",
    dependencies=[Depends(require_role(UserRole.FARMER))],
)
def reject_interest(
    interest_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    farmer = db.query(Farmer).filter_by(user_id=current_user.id).first()
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer profile not found.")

    interest = (
        db.query(TransactionInterest)
        .options(*_INTEREST_OPTS)
        .filter_by(id=interest_id, farmer_id=farmer.id)
        .first()
    )
    if not interest:
        raise HTTPException(status_code=404, detail="Interest request not found.")

    if not is_valid_transition(interest.status, InterestStatus.REJECTED):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot reject a request with status '{interest.status}'.",
        )

    interest.status = InterestStatus.REJECTED
    db.commit()
    db.refresh(interest)
    interest = db.query(TransactionInterest).options(*_INTEREST_OPTS).filter_by(id=interest.id).first()
    return _build_response(interest)


# ── DELETE: buyer cancels their own PENDING interest ─────────────────────────

@router.delete(
    "/{interest_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Buyer cancels their own pending interest request",
    dependencies=[Depends(require_role(UserRole.BUYER))],
)
def cancel_interest(
    interest_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    buyer = db.query(Buyer).filter_by(user_id=current_user.id).first()
    if not buyer:
        raise HTTPException(status_code=404, detail="Interest not found.")

    interest = db.query(TransactionInterest).filter_by(id=interest_id, buyer_id=buyer.id).first()
    if not interest:
        raise HTTPException(status_code=404, detail="Interest not found.")

    if not is_valid_transition(interest.status, InterestStatus.CANCELLED):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel a request with status '{interest.status}'.",
        )

    interest.status = InterestStatus.CANCELLED
    db.commit()



# ── PUT: buyer or farmer confirms transaction completed (Correction 7) ────────

from datetime import datetime, timezone as _tz  # noqa: E402  (placed here to avoid re-ordering)

VERIFICATION_THRESHOLD = 5  # completed transactions needed for verified badge


def _update_verification(profile, db: Session) -> None:
    """Recalculate completed_transaction_count from DB and grant badge if threshold met."""
    from app.models.farmer import Farmer as _Farmer
    if isinstance(profile, _Farmer):
        count = (
            db.query(TransactionInterest)
            .filter(
                TransactionInterest.farmer_id == profile.id,
                TransactionInterest.status == InterestStatus.COMPLETED,
            )
            .count()
        )
    else:
        count = (
            db.query(TransactionInterest)
            .filter(
                TransactionInterest.buyer_id == profile.id,
                TransactionInterest.status == InterestStatus.COMPLETED,
            )
            .count()
        )
    profile.completed_transaction_count = count
    profile.is_verified = count >= VERIFICATION_THRESHOLD


@router.put(
    "/{interest_id}/confirm-complete",
    response_model=InterestResponse,
    summary="Buyer or farmer confirms the transaction was completed. "
            "When both parties confirm, the transaction is marked COMPLETED "
            "and their completion count and verified status are updated.",
)
def confirm_complete(
    interest_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Dual-confirmation completion flow (Correction 7):
      1. Only the farmer or buyer directly involved can confirm.
      2. Confirmation is allowed only when the interest is ACCEPTED.
      3. A party can confirm at most once (idempotent after the first call).
      4. When BOTH parties have confirmed, the status moves to COMPLETED
         and each participant's count is recalculated from DB records.
      5. COMPLETED transactions cannot be confirmed again.

    Race-condition protection:
      We use SELECT ... FOR UPDATE on the TransactionInterest row so that
      concurrent confirmations from buyer and farmer are serialised at the
      database level.  The eagerly-loaded response copy is fetched AFTER the
      lock is released (post-commit) to avoid SQLAlchemy loader conflicts.
    """
    # -- Step 1: lock the row so concurrent confirmations are serialised ------
    interest = (
        db.query(TransactionInterest)
        .filter_by(id=interest_id)
        .with_for_update()          # row-level lock; no eager loads here
        .first()
    )
    if not interest:
        raise HTTPException(status_code=404, detail="Interest not found.")

    # Determine caller's role in this transaction
    farmer = db.query(Farmer).filter_by(user_id=current_user.id).first()
    buyer  = db.query(Buyer).filter_by(user_id=current_user.id).first()

    is_farmer_party = farmer and farmer.id == interest.farmer_id
    is_buyer_party  = buyer  and buyer.id  == interest.buyer_id

    if not is_farmer_party and not is_buyer_party:
        raise HTTPException(
            status_code=403,
            detail="You are not a party to this transaction.",
        )

    if interest.status == InterestStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail="This transaction is already marked as completed.",
        )

    if interest.status != InterestStatus.ACCEPTED:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot confirm completion for a transaction with status '{interest.status}'. "
                   "Only ACCEPTED transactions can be completed.",
        )

    # Record the confirmation (idempotent — second call for same party is a no-op)
    if is_farmer_party:
        if interest.farmer_confirmed:
            # Already confirmed — release the row lock and return current state
            db.rollback()
            interest = (
                db.query(TransactionInterest)
                .options(*_INTEREST_OPTS)
                .filter_by(id=interest_id)
                .first()
            )
            return _build_response(interest, reveal_contact=True)
        interest.farmer_confirmed = True

    if is_buyer_party:
        if interest.buyer_confirmed:
            # Already confirmed — release the row lock and return current state
            db.rollback()
            interest = (
                db.query(TransactionInterest)
                .options(*_INTEREST_OPTS)
                .filter_by(id=interest_id)
                .first()
            )
            return _build_response(interest, reveal_contact=True)
        interest.buyer_confirmed = True

    # If both parties have now confirmed, finalise
    if interest.buyer_confirmed and interest.farmer_confirmed:
        interest.status = InterestStatus.COMPLETED
        interest.completed_at = datetime.now(_tz.utc)

        db.flush()  # write the status change before recalculating counts

        # Also lock the profile rows while we update counts to prevent concurrent writes
        farmer_profile = (
            db.query(Farmer).filter_by(id=interest.farmer_id).with_for_update().first()
        )
        buyer_profile = (
            db.query(Buyer).filter_by(id=interest.buyer_id).with_for_update().first()
        )
        if farmer_profile:
            _update_verification(farmer_profile, db)
        if buyer_profile:
            _update_verification(buyer_profile, db)

    db.commit()
    # Reload with eager joins for the response (lock already released by commit)
    interest = (
        db.query(TransactionInterest)
        .options(*_INTEREST_OPTS)
        .filter_by(id=interest_id)
        .first()
    )
    return _build_response(interest, reveal_contact=True)
