"""initial_schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-09-29

Creates all Phase 2 tables:
  users, farmers, buyers, crops, markets, market_prices,
  buyer_requirements, recommendations, transaction_interests
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Enums ──────────────────────────────────────────────────────────────────
    userrole = postgresql.ENUM("FARMER", "BUYER", "ADMIN", name="userrole", create_type=False)
    userrole.create(op.get_bind(), checkfirst=True)

    cropunit = postgresql.ENUM("kg", "quintal", "ton", name="cropunit", create_type=False)
    cropunit.create(op.get_bind(), checkfirst=True)

    markettype = postgresql.ENUM(
        "APMC", "WHOLESALE", "LOCAL", "REGULATED", "OTHER",
        name="markettype", create_type=False,
    )
    markettype.create(op.get_bind(), checkfirst=True)

    requirementstatus = postgresql.ENUM(
        "ACTIVE", "FULFILLED", "EXPIRED", "CANCELLED",
        name="requirementstatus", create_type=False,
    )
    requirementstatus.create(op.get_bind(), checkfirst=True)

    intereststatus = postgresql.ENUM(
        "INTERESTED", "CONTACTED", "ACCEPTED", "REJECTED", "COMPLETED",
        name="intereststatus", create_type=False,
    )
    intereststatus.create(op.get_bind(), checkfirst=True)

    # ── users ──────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("role", sa.Enum("FARMER", "BUYER", "ADMIN", name="userrole"), nullable=False, server_default="FARMER"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_email", "users", ["email"])

    # ── crops ──────────────────────────────────────────────────────────────────
    op.create_table(
        "crops",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("unit", sa.Enum("kg", "quintal", "ton", name="cropunit"), nullable=False, server_default="quintal"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("name", name="uq_crops_name"),
    )
    op.create_index("ix_crops_id", "crops", ["id"])
    op.create_index("ix_crops_name", "crops", ["name"])

    # ── markets ────────────────────────────────────────────────────────────────
    op.create_table(
        "markets",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("market_code", sa.String(50), nullable=False),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("district", sa.String(255), nullable=True),
        sa.Column("state", sa.String(255), nullable=True),
        sa.Column("latitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("longitude", sa.Numeric(9, 6), nullable=True),
        sa.Column(
            "market_type",
            sa.Enum("APMC", "WHOLESALE", "LOCAL", "REGULATED", "OTHER", name="markettype"),
            nullable=False,
            server_default="APMC",
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("market_code", name="uq_markets_market_code"),
    )
    op.create_index("ix_markets_id", "markets", ["id"])
    op.create_index("ix_markets_name", "markets", ["name"])
    op.create_index("ix_markets_district", "markets", ["district"])
    op.create_index("ix_markets_state", "markets", ["state"])

    # ── farmers ────────────────────────────────────────────────────────────────
    op.create_table(
        "farmers",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("village", sa.String(255), nullable=True),
        sa.Column("district", sa.String(255), nullable=True),
        sa.Column("state", sa.String(255), nullable=True),
        sa.Column("latitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("longitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("farm_size", sa.Numeric(10, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", name="uq_farmers_user_id"),
    )
    op.create_index("ix_farmers_id", "farmers", ["id"])

    # ── buyers ─────────────────────────────────────────────────────────────────
    op.create_table(
        "buyers",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("business_name", sa.String(255), nullable=True),
        sa.Column("business_type", sa.String(100), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("district", sa.String(255), nullable=True),
        sa.Column("state", sa.String(255), nullable=True),
        sa.Column("latitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("longitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", name="uq_buyers_user_id"),
    )
    op.create_index("ix_buyers_id", "buyers", ["id"])

    # ── market_prices ──────────────────────────────────────────────────────────
    op.create_table(
        "market_prices",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("market_id", sa.Integer(), sa.ForeignKey("markets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("crop_id", sa.Integer(), sa.ForeignKey("crops.id", ondelete="CASCADE"), nullable=False),
        sa.Column("price_date", sa.Date(), nullable=False),
        sa.Column("min_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("max_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("modal_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("available_quantity", sa.Numeric(14, 2), nullable=True),
        sa.Column("source", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("min_price >= 0", name="ck_market_prices_min_price_non_negative"),
        sa.CheckConstraint("max_price >= 0", name="ck_market_prices_max_price_non_negative"),
        sa.CheckConstraint("modal_price >= 0", name="ck_market_prices_modal_price_non_negative"),
        sa.CheckConstraint("available_quantity >= 0", name="ck_market_prices_qty_non_negative"),
        sa.CheckConstraint("min_price <= modal_price", name="ck_market_prices_min_le_modal"),
        sa.CheckConstraint("modal_price <= max_price", name="ck_market_prices_modal_le_max"),
    )
    op.create_index("ix_market_prices_id", "market_prices", ["id"])
    op.create_index("ix_market_prices_crop_id", "market_prices", ["crop_id"])
    op.create_index("ix_market_prices_market_id", "market_prices", ["market_id"])
    op.create_index("ix_market_prices_price_date", "market_prices", ["price_date"])

    # ── buyer_requirements ─────────────────────────────────────────────────────
    op.create_table(
        "buyer_requirements",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("buyer_id", sa.Integer(), sa.ForeignKey("buyers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("crop_id", sa.Integer(), sa.ForeignKey("crops.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("quantity", sa.Numeric(14, 2), nullable=True),
        sa.Column("minimum_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("maximum_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("district", sa.String(255), nullable=True),
        sa.Column("state", sa.String(255), nullable=True),
        sa.Column("latitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("longitude", sa.Numeric(9, 6), nullable=True),
        sa.Column(
            "status",
            sa.Enum("ACTIVE", "FULFILLED", "EXPIRED", "CANCELLED", name="requirementstatus"),
            nullable=False,
            server_default="ACTIVE",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("quantity >= 0", name="ck_buyer_requirements_qty_non_negative"),
        sa.CheckConstraint("minimum_price >= 0", name="ck_buyer_requirements_min_price"),
        sa.CheckConstraint("maximum_price >= 0", name="ck_buyer_requirements_max_price"),
    )
    op.create_index("ix_buyer_requirements_id", "buyer_requirements", ["id"])
    op.create_index("ix_buyer_requirements_crop_id", "buyer_requirements", ["crop_id"])
    op.create_index("ix_buyer_requirements_status", "buyer_requirements", ["status"])

    # ── recommendations ────────────────────────────────────────────────────────
    op.create_table(
        "recommendations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("farmer_id", sa.Integer(), sa.ForeignKey("farmers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("crop_id", sa.Integer(), sa.ForeignKey("crops.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("recommended_market_id", sa.Integer(), sa.ForeignKey("markets.id", ondelete="SET NULL"), nullable=True),
        sa.Column("quantity", sa.Numeric(14, 2), nullable=True),
        sa.Column("current_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("transport_cost", sa.Numeric(12, 2), nullable=True),
        sa.Column("expected_gross_revenue", sa.Numeric(14, 2), nullable=True),
        sa.Column("expected_net_revenue", sa.Numeric(14, 2), nullable=True),
        sa.Column("confidence", sa.Numeric(4, 3), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_recommendations_id", "recommendations", ["id"])
    op.create_index("ix_recommendations_farmer_id", "recommendations", ["farmer_id"])
    op.create_index("ix_recommendations_created_at", "recommendations", ["created_at"])

    # ── transaction_interests ──────────────────────────────────────────────────
    op.create_table(
        "transaction_interests",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("farmer_id", sa.Integer(), sa.ForeignKey("farmers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("buyer_id", sa.Integer(), sa.ForeignKey("buyers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("crop_id", sa.Integer(), sa.ForeignKey("crops.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("quantity", sa.Numeric(14, 2), nullable=True),
        sa.Column(
            "status",
            sa.Enum("INTERESTED", "CONTACTED", "ACCEPTED", "REJECTED", "COMPLETED", name="intereststatus"),
            nullable=False,
            server_default="INTERESTED",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_transaction_interests_id", "transaction_interests", ["id"])


def downgrade() -> None:
    op.drop_table("transaction_interests")
    op.drop_table("recommendations")
    op.drop_table("buyer_requirements")
    op.drop_table("market_prices")
    op.drop_table("buyers")
    op.drop_table("farmers")
    op.drop_table("markets")
    op.drop_table("crops")
    op.drop_table("users")

    # Drop enums
    for enum_name in ["intereststatus", "requirementstatus", "markettype", "cropunit", "userrole"]:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
