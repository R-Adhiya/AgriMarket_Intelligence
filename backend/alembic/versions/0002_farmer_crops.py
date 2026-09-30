"""phase4_farmer_crops

Revision ID: 0002_farmer_crops
Revises: 0001_initial_schema
Create Date: 2026-09-30

Adds the farmer_crops table introduced in Phase 4 (Farmer Module).
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "0002_farmer_crops"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum type for quantity unit
    quantityunit = sa.Enum("kg", "quintal", "ton", name="quantityunit")
    quantityunit.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "farmer_crops",
        sa.Column("id", sa.Integer(), primary_key=True, index=True, nullable=False),
        sa.Column("farmer_id", sa.Integer(), sa.ForeignKey("farmers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("crop_id", sa.Integer(), sa.ForeignKey("crops.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("quantity", sa.Numeric(12, 3), nullable=False),
        sa.Column("unit", sa.Enum("kg", "quintal", "ton", name="quantityunit"), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("quantity > 0", name="ck_farmer_crops_quantity_positive"),
    )
    op.create_index("ix_farmer_crops_farmer_id", "farmer_crops", ["farmer_id"])
    op.create_index("ix_farmer_crops_crop_id", "farmer_crops", ["crop_id"])


def downgrade() -> None:
    op.drop_index("ix_farmer_crops_crop_id", table_name="farmer_crops")
    op.drop_index("ix_farmer_crops_farmer_id", table_name="farmer_crops")
    op.drop_table("farmer_crops")
    sa.Enum(name="quantityunit").drop(op.get_bind(), checkfirst=True)
