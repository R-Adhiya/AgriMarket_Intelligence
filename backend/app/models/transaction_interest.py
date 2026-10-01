import enum

from sqlalchemy import Enum, ForeignKey, Numeric, Text
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
    InterestStatus.ACCEPTED:   set(),
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
    requirement_id: Mapped[int | None] = mapped_column(
        ForeignKey("buyer_requirements.id", ondelete="SET NULL"), nullable=True
    )

    quantity: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[InterestStatus] = mapped_column(
        Enum(InterestStatus, name="intereststatus"),
        nullable=False,
        default=InterestStatus.PENDING,
    )

    # Relationships
    farmer: Mapped["Farmer"] = relationship("Farmer", back_populates="transaction_interests")  # noqa: F821
    buyer: Mapped["Buyer"] = relationship("Buyer", back_populates="transaction_interests")  # noqa: F821
    crop: Mapped["Crop"] = relationship("Crop", back_populates="transaction_interests")  # noqa: F821
    requirement: Mapped["BuyerRequirement | None"] = relationship(  # noqa: F821
        "BuyerRequirement", back_populates="interests"
    )

    def __repr__(self) -> str:
        return (
            f"<TransactionInterest id={self.id} farmer_id={self.farmer_id} "
            f"buyer_id={self.buyer_id} status={self.status}>"
        )
