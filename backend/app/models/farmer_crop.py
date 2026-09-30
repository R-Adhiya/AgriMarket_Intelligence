"""
FarmerCrop — a farmer's declared produce inventory.
One farmer can have many crop entries (different crops or different lots).
"""

import enum

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Numeric, String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class QuantityUnit(str, enum.Enum):
    KG = "kg"
    QUINTAL = "quintal"
    TON = "ton"


class FarmerCrop(Base, TimestampMixin):
    """Crop/produce entry added by a farmer."""

    __tablename__ = "farmer_crops"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    farmer_id: Mapped[int] = mapped_column(
        ForeignKey("farmers.id", ondelete="CASCADE"), nullable=False
    )
    crop_id: Mapped[int] = mapped_column(
        ForeignKey("crops.id", ondelete="RESTRICT"), nullable=False
    )

    quantity: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False)
    unit: Mapped[QuantityUnit] = mapped_column(
        Enum(QuantityUnit, name="quantityunit"), nullable=False, default=QuantityUnit.QUINTAL
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    farmer: Mapped["Farmer"] = relationship("Farmer", back_populates="farmer_crops")  # noqa: F821
    crop: Mapped["Crop"] = relationship("Crop", back_populates="farmer_crops")  # noqa: F821

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_farmer_crops_quantity_positive"),
        Index("ix_farmer_crops_farmer_id", "farmer_id"),
        Index("ix_farmer_crops_crop_id", "crop_id"),
    )

    def __repr__(self) -> str:
        return f"<FarmerCrop id={self.id} farmer_id={self.farmer_id} crop_id={self.crop_id}>"
