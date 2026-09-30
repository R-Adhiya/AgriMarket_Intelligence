"""phase8_recommendation_fields

Revision ID: 0003_recommendation_fields
Revises: 0002_farmer_crops
Create Date: 2026-09-30

Adds Phase 8 fields to the recommendations table:
  - distance_km
  - price_basis
  - explanation
"""

from alembic import op
import sqlalchemy as sa

revision = "0003_recommendation_fields"
down_revision = "0002_farmer_crops"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("recommendations", sa.Column("distance_km",   sa.Numeric(10, 2), nullable=True))
    op.add_column("recommendations", sa.Column("price_basis",   sa.String(20),     nullable=True))
    op.add_column("recommendations", sa.Column("explanation",   sa.Text(),         nullable=True))


def downgrade() -> None:
    op.drop_column("recommendations", "explanation")
    op.drop_column("recommendations", "price_basis")
    op.drop_column("recommendations", "distance_km")
