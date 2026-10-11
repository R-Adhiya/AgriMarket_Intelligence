"""
CropSuggestion model — Correction 5.

Buyers can suggest new crop names; admins approve or reject them.
Only approved suggestions trigger a real Crop row insert.
"""
import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class SuggestionStatus(str, enum.Enum):
    PENDING  = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class CropSuggestion(Base, TimestampMixin):
    """
    Pending crop name submitted by a buyer.
    Admins approve → a real Crop row is created.
    """
    __tablename__ = "crop_suggestions"

    id: Mapped[int]         = mapped_column(primary_key=True, index=True)
    suggested_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None]    = mapped_column(Text, nullable=True)

    # Who suggested it
    suggested_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    status: Mapped[SuggestionStatus] = mapped_column(
        Enum(SuggestionStatus, name="suggestionstatus"),
        nullable=False,
        default=SuggestionStatus.PENDING,
    )

    # If approved: the resulting Crop row id
    approved_crop_id: Mapped[int | None] = mapped_column(
        ForeignKey("crops.id", ondelete="SET NULL"), nullable=True
    )
    admin_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    suggested_by: Mapped["User | None"] = relationship("User", foreign_keys=[suggested_by_user_id])  # noqa: F821
    approved_crop: Mapped["Crop | None"] = relationship("Crop", foreign_keys=[approved_crop_id])     # noqa: F821

    __table_args__ = (
        Index("ix_crop_suggestions_status", "status"),
        Index("ix_crop_suggestions_name",   "suggested_name"),
    )

    def __repr__(self) -> str:
        return f"<CropSuggestion id={self.id} name={self.suggested_name!r} status={self.status}>"
