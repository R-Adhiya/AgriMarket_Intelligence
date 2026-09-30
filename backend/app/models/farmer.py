from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class Farmer(Base, TimestampMixin):
    """Farmer profile — one-to-one with User (role=FARMER)."""
    __tablename__ = "farmers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    village: Mapped[str | None] = mapped_column(String(255), nullable=True)
    district: Mapped[str | None] = mapped_column(String(255), nullable=True)
    state: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Decimal(9,6) gives ±999.999999° — suitable for GPS coordinates
    latitude: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)

    # Farm size in acres
    farm_size: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="farmer_profile")  # noqa: F821
    farmer_crops: Mapped[list["FarmerCrop"]] = relationship(  # noqa: F821
        "FarmerCrop", back_populates="farmer", cascade="all, delete-orphan"
    )
    recommendations: Mapped[list["Recommendation"]] = relationship(  # noqa: F821
        "Recommendation", back_populates="farmer", cascade="all, delete-orphan"
    )
    transaction_interests: Mapped[list["TransactionInterest"]] = relationship(  # noqa: F821
        "TransactionInterest", back_populates="farmer", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Farmer id={self.id} user_id={self.user_id} district={self.district!r}>"
