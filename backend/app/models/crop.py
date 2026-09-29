import enum

from sqlalchemy import Boolean, Enum, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from sqlalchemy import DateTime, func
from sqlalchemy.orm import mapped_column
from datetime import datetime


class CropUnit(str, enum.Enum):
    KG = "kg"
    QUINTAL = "quintal"
    TON = "ton"


class Crop(Base):
    """
    Reference catalogue of agricultural crops.
    Adding a new crop does not require a code change — insert a row.
    """
    __tablename__ = "crops"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    unit: Mapped[CropUnit] = mapped_column(
        Enum(CropUnit, name="cropunit"), nullable=False, default=CropUnit.QUINTAL
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    market_prices: Mapped[list["MarketPrice"]] = relationship(  # noqa: F821
        "MarketPrice", back_populates="crop"
    )
    buyer_requirements: Mapped[list["BuyerRequirement"]] = relationship(  # noqa: F821
        "BuyerRequirement", back_populates="crop"
    )
    recommendations: Mapped[list["Recommendation"]] = relationship(  # noqa: F821
        "Recommendation", back_populates="crop"
    )
    transaction_interests: Mapped[list["TransactionInterest"]] = relationship(  # noqa: F821
        "TransactionInterest", back_populates="crop"
    )

    __table_args__ = (
        Index("ix_crops_name", "name"),
    )

    def __repr__(self) -> str:
        return f"<Crop id={self.id} name={self.name!r} unit={self.unit}>"
