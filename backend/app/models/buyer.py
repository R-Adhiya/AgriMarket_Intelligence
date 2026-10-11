from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class Buyer(Base, TimestampMixin):
    """Buyer profile — one-to-one with User (role=BUYER)."""
    __tablename__ = "buyers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    business_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    business_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    district: Mapped[str | None] = mapped_column(String(255), nullable=True)
    state: Mapped[str | None] = mapped_column(String(255), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)

    # Verification — Correction 7
    completed_transaction_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="buyer_profile")  # noqa: F821
    requirements: Mapped[list["BuyerRequirement"]] = relationship(  # noqa: F821
        "BuyerRequirement", back_populates="buyer", cascade="all, delete-orphan"
    )
    transaction_interests: Mapped[list["TransactionInterest"]] = relationship(  # noqa: F821
        "TransactionInterest", back_populates="buyer", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Buyer id={self.id} business_name={self.business_name!r}>"
