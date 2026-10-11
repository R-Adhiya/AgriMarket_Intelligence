"""
TransactionInterest model — Phase 9 + Correction 7.

Correction 7 adds:
  - buyer_confirmed / farmer_confirmed flags: both parties must confirm to complete
  - ACCEPTED -> COMPLETED transition unlocked
  - completed_at timestamp
"""
import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Numeric, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class InterestStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    # Legacy values kept for backwards-compat with seeded data
    INTERESTED = "INTERESTED"
    CONTACTED = "CONTACTED"
    COMPLETED = "COMPLETED"


# Valid forward transitions
_ALLOWED_TRANSITIONS: dict[InterestStatus, set[InterestStatus]] = {
    InterestStatus.PENDING:    {InterestStatus.ACCEPTED, InterestStatus.REJECTED, InterestStatus.CANCELLED},
    InterestStatus.INTERESTED: {InterestStatus.ACCEPTED, InterestStatus.REJECTED, InterestStatus.CANCELLED},
    InterestStatus.CONTACTED:  {InterestStatus.ACCEPTED, InterestStatus.REJECTED},
    # Correction 7: ACCEPTED can now transition to COMPLETED (requires both-party confirmation)
    InterestStatus.ACCEPTED:   {InterestStatus.COMPLETED},
    InterestStatus.REJECTED:   set(),
    InterestStatus.CANCELLED:  set(),
    InterestStatus.COMPLETED:  set(),
}


def is_valid_transition(current: InterestStatus, new: InterestStatus) -> bool:
    return new in _ALLOWED_TRANSITIONS.get(current, set())


class TransactionInterest(Base, TimestampMixin):
    """
    Interest/contact request from a buyer to a farmer for a specific crop.
    Optionally linked to a BuyerRequirement.

    Status workflow:
        PENDING -> ACCEPTED | REJECTED | CANCELLED
        ACCEPTED -> COMPLETED  (requires buyer_confirmed AND farmer_confirmed)

    Correction 7 additions:
        buyer_confirmed   — buyer has confirmed the transaction happened
        farmer_confirmed  — farmer has confirmed the transaction happened
        completed_at      — timestamp when both confirmations were received
    """
    __tablename__ = "transaction_interests"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    farmer_id: Mapped[int] = mapped_column(
        ForeignKey("farmers.id", ondelete="CASCADE"), nullable=False
    )
    buyer_id: Mapped[int] = mapped_column(
        ForeignKey("buyers.id", ondelete="CASCADE"), nullable=False
    )
    crop_id: Mapped[int] = mapped_column(
        ForeignKey("crops.id", ondelete="RESTRICT"), nullable=False
    )
    # Optional: link to the buyer requirement that triggered this interest
    requirement_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("buyer_requirements.id", ondelete="SET NULL"), nullable=True
    )

    quantity: Mapped[Optional[float]] = mapped_column(Numeric(14, 2), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    status: Mapped[InterestStatus] = mapped_column(
        Enum(InterestStatus, name="intereststatus"),
        nullable=False,
        default=InterestStatus.PENDING,
    )

    # Correction 7: dual-confirmation completion tracking
    buyer_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    farmer_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    farmer: Mapped["Farmer"] = relationship("Farmer", back_populates="transaction_interests")  # noqa: F821
    buyer: Mapped["Buyer"] = relationship("Buyer", back_populates="transaction_interests")  # noqa: F821
    crop: Mapped["Crop"] = relationship("Crop", back_populates="transaction_interests")  # noqa: F821
    requirement: Mapped[Optional["BuyerRequirement"]] = relationship(  # noqa: F821
        "BuyerRequirement", back_populates="interests"
    )

    def __repr__(self) -> str:
        return (
            f"<TransactionInterest id={self.id} farmer_id={self.farmer_id} "
            f"buyer_id={self.buyer_id} status={self.status}>"
        )
