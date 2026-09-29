import enum

from sqlalchemy import Boolean, Enum, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class MarketType(str, enum.Enum):
    APMC = "APMC"
    WHOLESALE = "WHOLESALE"
    LOCAL = "LOCAL"
    REGULATED = "REGULATED"
    OTHER = "OTHER"


class Market(Base, TimestampMixin):
    """
    Agricultural market / mandi.
    Supports future geospatial distance calculations via lat/lng.
    """
    __tablename__ = "markets"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    market_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    district: Mapped[str | None] = mapped_column(String(255), nullable=True)
    state: Mapped[str | None] = mapped_column(String(255), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    market_type: Mapped[MarketType] = mapped_column(
        Enum(MarketType, name="markettype"), nullable=False, default=MarketType.APMC
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    prices: Mapped[list["MarketPrice"]] = relationship(  # noqa: F821
        "MarketPrice", back_populates="market", cascade="all, delete-orphan"
    )
    recommendations: Mapped[list["Recommendation"]] = relationship(  # noqa: F821
        "Recommendation", back_populates="recommended_market"
    )

    __table_args__ = (
        Index("ix_markets_name", "name"),
        Index("ix_markets_district", "district"),
        Index("ix_markets_state", "state"),
    )

    def __repr__(self) -> str:
        return f"<Market id={self.id} code={self.market_code!r} name={self.name!r}>"
