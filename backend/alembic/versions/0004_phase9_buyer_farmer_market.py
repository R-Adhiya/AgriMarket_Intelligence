"""Phase 9: add is_available to farmer_crops; add requirement_id/notes to transaction_interests; update interest status enum

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-01
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add is_available to farmer_crops (default True = all existing are available)
    op.add_column(
        "farmer_crops",
        sa.Column("is_available", sa.Boolean(), nullable=False, server_default="1"),
    )

    # 2. Add requirement_id and notes to transaction_interests
    op.add_column(
        "transaction_interests",
        sa.Column(
            "requirement_id",
            sa.Integer(),
            sa.ForeignKey("buyer_requirements.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "transaction_interests",
        sa.Column("notes", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("transaction_interests", "notes")
    op.drop_column("transaction_interests", "requirement_id")
    op.drop_column("farmer_crops", "is_available")
