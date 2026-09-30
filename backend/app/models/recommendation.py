from sqlalchemy import ForeignKey, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class Recommendation(Base, TimestampMixin):
    """
    Stores a generated selling recommendation for a farmer.
    Written by the Phase 8 recommendation engine.
    """
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    farmer_id: Mapped[int] = mapped_column(
        ForeignKey("farmers.id", ondelete="CASCADE"), nullable=False
    )
    crop_id: Mapped[int] = mapped_column(
        ForeignKey("crops.id", ondelete="RESTRICT"), nullable=False
    )
    recommended_market_id: Mapped[int | None] = mapped_column(
        ForeignKey("markets.id", ondelete="SET NULL"), nullable=True
    )

    quantity: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    current_price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    transport_cost: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    expected_gross_revenue: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    expected_net_revenue: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    distance_km: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)

    # "current" or "predicted"
    price_basis: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Deterministic rule-based — confidence always null
    confidence: Mapped[float | None] = mapped_column(Numeric(4, 3), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    farmer: Mapped["Farmer"] = relationship("Farmer", back_populates="recommendations")  # noqa: F821
    crop: Mapped["Crop"] = relationship("Crop", back_populates="recommendations")  # noqa: F821
    recommended_market: Mapped["Market"] = relationship(  # noqa: F821
        "Market", back_populates="recommendations"
    )

    __table_args__ = (
        Index("ix_recommendations_farmer_id", "farmer_id"),
        Index("ix_recommendations_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<Recommendation id={self.id} farmer_id={self.farmer_id} "
            f"crop_id={self.crop_id} net_rev={self.expected_net_revenue}>"
        )
