"""
Phase 2 database tests.
Uses the SQLite in-memory fixture from conftest.py — no PostgreSQL required.
"""

from datetime import date

import pytest
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.models.farmer import Farmer
from app.models.buyer import Buyer
from app.models.crop import Crop, CropUnit
from app.models.market import Market, MarketType
from app.models.market_price import MarketPrice
from app.models.buyer_requirement import BuyerRequirement, RequirementStatus
from app.models.recommendation import Recommendation


# ── Test 1: Database connection ───────────────────────────────────────────────

def test_database_connection(db: Session):
    """The test DB session is alive and accepts queries."""
    from sqlalchemy import text
    result = db.execute(text("SELECT 1")).scalar()
    assert result == 1


# ── Test 2: User creation ─────────────────────────────────────────────────────

def test_create_user(db: Session):
    user = User(full_name="Ravi Kumar", email="ravi@example.com", role=UserRole.FARMER)
    db.add(user)
    db.flush()
    assert user.id is not None
    fetched = db.query(User).filter_by(email="ravi@example.com").first()
    assert fetched is not None
    assert fetched.full_name == "Ravi Kumar"
    assert fetched.role == UserRole.FARMER
    assert fetched.is_active is True


# ── Test 3: Farmer associated with User ───────────────────────────────────────

def test_create_farmer_with_user(db: Session):
    user = User(full_name="Suresh Patel", email="suresh@example.com", role=UserRole.FARMER)
    db.add(user)
    db.flush()

    farmer = Farmer(
        user_id=user.id,
        village="Mettupalayam",
        district="Coimbatore",
        state="Tamil Nadu",
        farm_size=5.5,
    )
    db.add(farmer)
    db.flush()

    assert farmer.id is not None
    assert farmer.user_id == user.id
    fetched = db.query(Farmer).filter_by(user_id=user.id).first()
    assert fetched is not None
    assert fetched.district == "Coimbatore"


# ── Test 4: Crop creation ─────────────────────────────────────────────────────

def test_create_crop(db: Session):
    crop = Crop(name="Tomato_test", category="Vegetable", unit=CropUnit.KG)
    db.add(crop)
    db.flush()
    assert crop.id is not None
    fetched = db.query(Crop).filter_by(name="Tomato_test").first()
    assert fetched is not None
    assert fetched.unit == CropUnit.KG
    assert fetched.is_active is True


# ── Test 5: Market creation ───────────────────────────────────────────────────

def test_create_market(db: Session):
    market = Market(
        name="Coimbatore Test Market",
        market_code="TN-TEST-001",
        district="Coimbatore",
        state="Tamil Nadu",
        market_type=MarketType.APMC,
    )
    db.add(market)
    db.flush()
    assert market.id is not None
    fetched = db.query(Market).filter_by(market_code="TN-TEST-001").first()
    assert fetched is not None
    assert fetched.market_type == MarketType.APMC


# ── Test 6: MarketPrice references Market and Crop ───────────────────────────

def test_market_price_references_market_and_crop(db: Session):
    crop = Crop(name="Onion_test", unit=CropUnit.QUINTAL)
    market = Market(name="Erode Test", market_code="TN-ERO-TEST", market_type=MarketType.WHOLESALE)
    db.add_all([crop, market])
    db.flush()

    price = MarketPrice(
        market_id=market.id,
        crop_id=crop.id,
        price_date=date(2026, 9, 29),
        min_price=800,
        modal_price=950,
        max_price=1100,
        source="development_sample",
    )
    db.add(price)
    db.flush()

    assert price.id is not None
    fetched = db.query(MarketPrice).filter_by(market_id=market.id, crop_id=crop.id).first()
    assert fetched is not None
    assert float(fetched.modal_price) == 950.0
    assert fetched.source == "development_sample"


# ── Test 7: BuyerRequirement references Buyer and Crop ───────────────────────

def test_buyer_requirement_references_buyer_and_crop(db: Session):
    user = User(full_name="Anbu Traders", email="anbu@example.com", role=UserRole.BUYER)
    db.add(user)
    db.flush()

    buyer = Buyer(user_id=user.id, business_name="Anbu Traders", district="Erode")
    db.add(buyer)
    db.flush()

    crop = Crop(name="Potato_test", unit=CropUnit.QUINTAL)
    db.add(crop)
    db.flush()

    req = BuyerRequirement(
        buyer_id=buyer.id,
        crop_id=crop.id,
        quantity=50,
        minimum_price=900,
        maximum_price=1200,
        district="Erode",
        status=RequirementStatus.ACTIVE,
    )
    db.add(req)
    db.flush()

    assert req.id is not None
    fetched = db.query(BuyerRequirement).filter_by(buyer_id=buyer.id).first()
    assert fetched is not None
    assert fetched.status == RequirementStatus.ACTIVE


# ── Test 8: Recommendation references Farmer, Crop, Market ───────────────────

def test_recommendation_references_farmer_crop_market(db: Session):
    user = User(full_name="Mani Raj", email="mani@example.com", role=UserRole.FARMER)
    db.add(user)
    db.flush()

    farmer = Farmer(user_id=user.id, district="Tiruppur", state="Tamil Nadu")
    db.add(farmer)
    db.flush()

    crop = Crop(name="Banana_test", unit=CropUnit.KG)
    market = Market(name="Tiruppur Test", market_code="TN-TPR-TEST", market_type=MarketType.LOCAL)
    db.add_all([crop, market])
    db.flush()

    rec = Recommendation(
        farmer_id=farmer.id,
        crop_id=crop.id,
        recommended_market_id=market.id,
        quantity=200,
        expected_gross_revenue=5000,
        expected_net_revenue=4500,
        confidence=0.85,
        reason="Highest modal price in district",
    )
    db.add(rec)
    db.flush()

    assert rec.id is not None
    fetched = db.query(Recommendation).filter_by(farmer_id=farmer.id).first()
    assert fetched is not None
    assert float(fetched.confidence) == pytest.approx(0.85, abs=0.001)


# ── Test 9: Foreign key relationship integrity ────────────────────────────────

def test_foreign_key_relationships(db: Session):
    """Verify ORM relationship traversal works correctly."""
    user = User(full_name="Karthik FM", email="karthik@example.com", role=UserRole.FARMER)
    db.add(user)
    db.flush()

    farmer = Farmer(user_id=user.id, district="Salem", state="Tamil Nadu")
    db.add(farmer)
    db.flush()

    # Traverse relationship: farmer → user
    loaded_farmer = db.query(Farmer).filter_by(id=farmer.id).first()
    loaded_user = db.query(User).filter_by(id=loaded_farmer.user_id).first()
    assert loaded_user is not None
    assert loaded_user.full_name == "Karthik FM"
