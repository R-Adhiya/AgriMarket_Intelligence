import enum

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class RequirementStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    FULFILLED = "FULFILLED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class BuyerRequirement(Base, TimestampMixin):
    """What a buyer wants to purchase — location, crop, price range, quantity."""
    __tablename__ = "buyer_requirements"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    buyer_id: Mapped[int] = mapped_column(
        ForeignKey("buyers.id", ondelete="CASCADE"), nullable=False
    )
    crop_id: Mapped[int] = mapped_column(
        ForeignKey("crops.id", ondelete="RESTRICT"), nullable=False
    )

    quantity: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    minimum_price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    maximum_price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)

    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    district: Mapped[str | None] = mapped_column(String(255), nullable=True)
    state: Mapped[str | None] = mapped_column(String(255), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)

    status: Mapped[RequirementStatus] = mapped_column(
        Enum(RequirementStatus, name="requirementstatus"),
        nullable=False,
        default=RequirementStatus.ACTIVE,
    )

    # Relationships
    buyer: Mapped["Buyer"] = relationship("Buyer", back_populates="requirements")  # noqa: F821
    crop: Mapped["Crop"] = relationship("Crop", back_populates="buyer_requirements")  # noqa: F821

    __table_args__ = (
        CheckConstraint("quantity >= 0", name="ck_buyer_requirements_qty_non_negative"),
        CheckConstraint("minimum_price >= 0", name="ck_buyer_requirements_min_price"),
        CheckConstraint("maximum_price >= 0", name="ck_buyer_requirements_max_price"),
        Index("ix_buyer_requirements_crop_id", "crop_id"),
        Index("ix_buyer_requirements_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<BuyerRequirement id={self.id} buyer_id={self.buyer_id} crop_id={self.crop_id} status={self.status}>"
