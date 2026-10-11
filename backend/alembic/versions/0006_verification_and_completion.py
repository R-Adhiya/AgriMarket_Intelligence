"""
Correction 7: Verified badge system and transaction completion tracking.

Adds:
  farmers.completed_transaction_count  INTEGER NOT NULL DEFAULT 0
  farmers.is_verified                  BOOLEAN NOT NULL DEFAULT false
  buyers.completed_transaction_count   INTEGER NOT NULL DEFAULT 0
  buyers.is_verified                   BOOLEAN NOT NULL DEFAULT false
  transaction_interests.buyer_confirmed    BOOLEAN NOT NULL DEFAULT false
  transaction_interests.farmer_confirmed   BOOLEAN NOT NULL DEFAULT false
  transaction_interests.completed_at       TIMESTAMPTZ NULL

Revision ID: 0006
Revises: 0005
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── farmers ──────────────────────────────────────────────────────────────
    op.add_column(
        "farmers",
        sa.Column("completed_transaction_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "farmers",
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
    )

    # ── buyers ───────────────────────────────────────────────────────────────
    op.add_column(
        "buyers",
        sa.Column("completed_transaction_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "buyers",
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
    )

    # ── transaction_interests ─────────────────────────────────────────────────
    op.add_column(
        "transaction_interests",
        sa.Column("buyer_confirmed", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "transaction_interests",
        sa.Column("farmer_confirmed", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "transaction_interests",
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("transaction_interests", "completed_at")
    op.drop_column("transaction_interests", "farmer_confirmed")
    op.drop_column("transaction_interests", "buyer_confirmed")
    op.drop_column("buyers", "is_verified")
    op.drop_column("buyers", "completed_transaction_count")
    op.drop_column("farmers", "is_verified")
    op.drop_column("farmers", "completed_transaction_count")
