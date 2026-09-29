import enum

from sqlalchemy import Enum, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class InterestStatus(str, enum.Enum):
    INTERESTED = "INTERESTED"
    CONTACTED = "CONTACTED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    COMPLETED = "COMPLETED"


class TransactionInterest(Base, TimestampMixin):
    """
    Lightweight record linking a farmer and a buyer for a specific crop.
    Full transaction/payment logic belongs to a later phase.
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

    quantity: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    status: Mapped[InterestStatus] = mapped_column(
        Enum(InterestStatus, name="intereststatus"),
        nullable=False,
        default=InterestStatus.INTERESTED,
    )

    # Relationships
    farmer: Mapped["Farmer"] = relationship("Farmer", back_populates="transaction_interests")  # noqa: F821
    buyer: Mapped["Buyer"] = relationship("Buyer", back_populates="transaction_interests")  # noqa: F821
    crop: Mapped["Crop"] = relationship("Crop", back_populates="transaction_interests")  # noqa: F821

    def __repr__(self) -> str:
        return (
            f"<TransactionInterest id={self.id} farmer_id={self.farmer_id} "
            f"buyer_id={self.buyer_id} status={self.status}>"
        )
