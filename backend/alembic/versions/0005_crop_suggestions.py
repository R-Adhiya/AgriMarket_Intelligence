"""Correction 5: crop suggestions table

Revision ID: 0005_crop_suggestions
Revises: 0004_phase9_buyer_farmer_market
Create Date: 2026-10-11
"""

from alembic import op
import sqlalchemy as sa

revision = "0005_crop_suggestions"
down_revision = "0004_phase9_buyer_farmer_market"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "crop_suggestions",
        sa.Column("id",                   sa.Integer(),    primary_key=True, index=True),
        sa.Column("suggested_name",       sa.String(255),  nullable=False),
        sa.Column("category",             sa.String(100),  nullable=True),
        sa.Column("notes",                sa.Text(),       nullable=True),
        sa.Column("suggested_by_user_id", sa.Integer(),    sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status",               sa.Enum("PENDING", "APPROVED", "REJECTED", name="suggestionstatus"), nullable=False, server_default="PENDING"),
        sa.Column("approved_crop_id",     sa.Integer(),    sa.ForeignKey("crops.id", ondelete="SET NULL"),  nullable=True),
        sa.Column("admin_notes",          sa.Text(),       nullable=True),
        sa.Column("created_at",           sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at",           sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index("ix_crop_suggestions_status", "crop_suggestions", ["status"])
    op.create_index("ix_crop_suggestions_name",   "crop_suggestions", ["suggested_name"])


def downgrade() -> None:
    op.drop_index("ix_crop_suggestions_name",   "crop_suggestions")
    op.drop_index("ix_crop_suggestions_status", "crop_suggestions")
    op.drop_table("crop_suggestions")
    op.execute("DROP TYPE IF EXISTS suggestionstatus")
