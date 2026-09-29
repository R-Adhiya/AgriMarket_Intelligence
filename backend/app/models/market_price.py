from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class MarketPrice(Base):
    """
    Historical and current crop price records for a market.
    Supports multiple records per crop/market combination (one per date).
    """
    __tablename__ = "market_prices"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    market_id: Mapped[int] = mapped_column(
        ForeignKey("markets.id", ondelete="CASCADE"), nullable=False
    )
    crop_id: Mapped[int] = mapped_column(
        ForeignKey("crops.id", ondelete="CASCADE"), nullable=False
    )
    price_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Prices stored as NUMERIC(12,2) — supports up to ₹9,999,999,999.99
    min_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    max_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    modal_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    # Quantity in the crop's native unit (nullable — not always reported)
    available_quantity: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)

    # Data source identifier: 'development_sample', 'agmarknet', 'manual', etc.
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    market: Mapped["Market"] = relationship("Market", back_populates="prices")  # noqa: F821
    crop: Mapped["Crop"] = relationship("Crop", back_populates="market_prices")  # noqa: F821

    __table_args__ = (
        # Price sanity constraints
        CheckConstraint("min_price >= 0", name="ck_market_prices_min_price_non_negative"),
        CheckConstraint("max_price >= 0", name="ck_market_prices_max_price_non_negative"),
        CheckConstraint("modal_price >= 0", name="ck_market_prices_modal_price_non_negative"),
        CheckConstraint("available_quantity >= 0", name="ck_market_prices_qty_non_negative"),
        CheckConstraint("min_price <= modal_price", name="ck_market_prices_min_le_modal"),
        CheckConstraint("modal_price <= max_price", name="ck_market_prices_modal_le_max"),
        # Indexes for common query patterns
        Index("ix_market_prices_crop_id", "crop_id"),
        Index("ix_market_prices_market_id", "market_id"),
        Index("ix_market_prices_price_date", "price_date"),
    )

    def __repr__(self) -> str:
        return (
            f"<MarketPrice id={self.id} market_id={self.market_id} "
            f"crop_id={self.crop_id} date={self.price_date} modal={self.modal_price}>"
        )
