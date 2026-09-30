"""
Phase 8 — Recommendation engine tests.
Uses the shared SQLite engine from conftest.py.
"""

import app.models  # noqa: F401

import sys
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from tests.conftest import get_test_session
from app.main import app as fastapi_app
from app.models.crop import Crop, CropUnit
from app.models.market import Market, MarketType
from app.models.market_price import MarketPrice
from app.models.farmer import Farmer
from app.models.user import User, UserRole

client = TestClient(fastapi_app)

# Module-level state
_CROP_KG     = None  # price per kg (Tomato)
_CROP_QT     = None  # price per quintal (Onion)
_MKT_NEAR    = None  # close market (Coimbatore)
_MKT_FAR     = None  # distant market with higher price (Erode)
_FARMER_H    = None
_FARMER2_H   = None  # second farmer — isolation test


def _make_auth(email, role="FARMER"):
    client.post("/api/auth/register", json={
        "full_name": "Rec Tester", "email": email, "password": "Password1", "role": role,
    })
    r = client.post("/api/auth/login", json={"email": email, "password": "Password1"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _seed_crop(name, unit=CropUnit.KG):
    db = get_test_session()
    c = db.query(Crop).filter_by(name=name).first()
    if not c:
        c = Crop(name=name, unit=unit, is_active=True, category="Vegetable")
        db.add(c); db.commit(); db.refresh(c)
    cid = c.id; db.close(); return cid


def _seed_market(code, name, district, lat, lon):
    db = get_test_session()
    m = db.query(Market).filter_by(market_code=code).first()
    if not m:
        m = Market(name=name, market_code=code, district=district, state="Tamil Nadu",
                   location=district, latitude=lat, longitude=lon,
                   market_type=MarketType.APMC, is_active=True)
        db.add(m); db.commit(); db.refresh(m)
    mid = m.id; db.close(); return mid


def _seed_price(market_id, crop_id, modal, mn=None, mx=None):
    db = get_test_session()
    pd_ = date.today()
    mn = mn or round(modal * 0.9, 2)
    mx = mx or round(modal * 1.1, 2)
    exists = db.query(MarketPrice).filter_by(market_id=market_id, crop_id=crop_id, price_date=pd_).first()
    if not exists:
        db.add(MarketPrice(market_id=market_id, crop_id=crop_id, price_date=pd_,
                           min_price=mn, modal_price=modal, max_price=mx,
                           source="development_sample"))
        db.commit()
    db.close()


def setup_module(_m):
    global _CROP_KG, _CROP_QT, _MKT_NEAR, _MKT_FAR, _FARMER_H, _FARMER2_H

    _CROP_KG = _seed_crop("RecTomato", CropUnit.KG)
    _CROP_QT = _seed_crop("RecOnion",  CropUnit.QUINTAL)

    # Near market (Coimbatore, ~0 km from farmer)
    _MKT_NEAR = _seed_market("R8-CBE", "Rec Market CBE", "Coimbatore", 11.0168, 76.9558)
    # Far market (Erode, ~80 km, higher price)
    _MKT_FAR  = _seed_market("R8-ERO", "Rec Market ERO", "Erode",      11.3410, 77.7172)

    # Prices: Far has higher price, Near has lower price
    _seed_price(_MKT_NEAR, _CROP_KG, 25.0)   # ₹25/kg near
    _seed_price(_MKT_FAR,  _CROP_KG, 30.0)   # ₹30/kg far
    _seed_price(_MKT_NEAR, _CROP_QT, 900.0)
    _seed_price(_MKT_FAR,  _CROP_QT, 1000.0)

    # Farmer 1: Coimbatore
    _FARMER_H = _make_auth("rec_farmer1@test.com")
    client.put("/api/farmer/profile", headers=_FARMER_H,
               json={"district": "Coimbatore", "state": "Tamil Nadu"})

    # Farmer 2: also Coimbatore — isolation test
    _FARMER2_H = _make_auth("rec_farmer2@test.com")
    client.put("/api/farmer/profile", headers=_FARMER2_H,
               json={"district": "Coimbatore", "state": "Tamil Nadu"})


# ── Unit tests: revenue calculation ──────────────────────────────────────────

def test_gross_revenue_kg():
    """500 kg × ₹25/kg = ₹12,500"""
    from decimal import Decimal, ROUND_HALF_UP
    price = Decimal("25.0")
    qty   = Decimal("500")
    gross = price * qty
    assert gross == Decimal("12500.00")


def test_net_revenue_formula():
    gross     = 12500.0
    transport = 1250.0
    net = gross - transport
    assert net == pytest.approx(11250.0)


def test_quintal_conversion():
    """500 kg = 5 quintals; ₹900/quintal → ₹4,500 gross"""
    from decimal import Decimal
    price_per_qt = Decimal("900")
    qty_kg = Decimal("500")
    qty_qt = qty_kg / 100
    gross  = price_per_qt * qty_qt
    assert gross == Decimal("4500.0")


# ── API: current-price recommendation ────────────────────────────────────────

def test_recommend_current_price():
    r = client.post("/api/recommendation/market", headers=_FARMER_H,
                    json={"crop_id": _CROP_KG, "quantity_kg": 500, "price_basis": "current"})
    assert r.status_code == 201
    data = r.json()
    assert data["price_basis"] == "current"
    assert data["recommended_market"] is not None
    assert data["quantity_kg"] == 500
    assert "explanation" in data
    assert data["disclaimer"]


def test_recommend_response_schema():
    r = client.post("/api/recommendation/market", headers=_FARMER_H,
                    json={"crop_id": _CROP_KG, "quantity_kg": 100, "price_basis": "current"})
    assert r.status_code == 201
    d = r.json()
    mkt = d["recommended_market"]
    assert "market_name"    in mkt
    assert "price_per_unit" in mkt
    assert "distance_km"    in mkt
    assert "transport_cost" in mkt
    assert "gross_revenue"  in mkt
    assert "net_revenue"    in mkt
    assert "price_basis"    in mkt
    assert "is_recommended" in mkt


def test_recommend_sorted_by_net_revenue():
    r = client.post("/api/recommendation/market", headers=_FARMER_H,
                    json={"crop_id": _CROP_KG, "quantity_kg": 500, "price_basis": "current"})
    comparison = r.json()["comparison"]
    net_revs = [c["net_revenue"] for c in comparison]
    assert net_revs == sorted(net_revs, reverse=True)


def test_recommend_highest_net_not_always_highest_price():
    """
    Near market: ₹25/kg, ~0 km, tiny transport.
    Far market:  ₹30/kg, ~80 km, higher transport.
    For very small quantity, near might win on net; for large quantity, far might win.
    Either way the recommendation must be the highest net_revenue market.
    """
    r = client.post("/api/recommendation/market", headers=_FARMER_H,
                    json={"crop_id": _CROP_KG, "quantity_kg": 500, "price_basis": "current"})
    data = r.json()
    best_mkt = data["recommended_market"]
    # The best market must have the highest net_revenue in the comparison
    max_net = max(c["net_revenue"] for c in data["comparison"])
    assert best_mkt["net_revenue"] == pytest.approx(max_net)


def test_recommend_explanation_present():
    r = client.post("/api/recommendation/market", headers=_FARMER_H,
                    json={"crop_id": _CROP_KG, "quantity_kg": 500, "price_basis": "current"})
    expl = r.json()["explanation"]
    assert len(expl) > 20
    assert "₹" in expl


def test_recommend_confidence_is_null():
    r = client.post("/api/recommendation/market", headers=_FARMER_H,
                    json={"crop_id": _CROP_KG, "quantity_kg": 100, "price_basis": "current"})
    assert r.json()["confidence"] is None
    assert r.json()["recommendation_method"] == "rule_based_net_revenue"


def test_recommend_currency_inr():
    r = client.post("/api/recommendation/market", headers=_FARMER_H,
                    json={"crop_id": _CROP_KG, "quantity_kg": 100, "price_basis": "current"})
    assert r.json()["currency"] == "INR"


# ── Validation ────────────────────────────────────────────────────────────────

def test_recommend_invalid_crop():
    r = client.post("/api/recommendation/market", headers=_FARMER_H,
                    json={"crop_id": 99999, "quantity_kg": 100, "price_basis": "current"})
    assert r.status_code == 404


def test_recommend_zero_quantity():
    r = client.post("/api/recommendation/market", headers=_FARMER_H,
                    json={"crop_id": _CROP_KG, "quantity_kg": 0, "price_basis": "current"})
    assert r.status_code == 422


def test_recommend_negative_quantity():
    r = client.post("/api/recommendation/market", headers=_FARMER_H,
                    json={"crop_id": _CROP_KG, "quantity_kg": -50, "price_basis": "current"})
    assert r.status_code == 422


def test_recommend_invalid_price_basis():
    r = client.post("/api/recommendation/market", headers=_FARMER_H,
                    json={"crop_id": _CROP_KG, "quantity_kg": 100, "price_basis": "magic"})
    assert r.status_code == 422


def test_recommend_requires_auth():
    r = client.post("/api/recommendation/market",
                    json={"crop_id": _CROP_KG, "quantity_kg": 100, "price_basis": "current"})
    assert r.status_code == 401


def test_recommend_buyer_blocked():
    h = _make_auth("rec_buyer@test.com", role="BUYER")
    r = client.post("/api/recommendation/market", headers=h,
                    json={"crop_id": _CROP_KG, "quantity_kg": 100, "price_basis": "current"})
    assert r.status_code == 403


def test_recommend_no_farmer_profile():
    h = _make_auth("rec_noprofile@test.com")
    r = client.post("/api/recommendation/market", headers=h,
                    json={"crop_id": _CROP_KG, "quantity_kg": 100, "price_basis": "current"})
    assert r.status_code == 422


# ── Predicted price basis ─────────────────────────────────────────────────────

def test_recommend_predicted_basis_or_422():
    """
    With synthetic development data, prediction may succeed (models trained on
    Tomato/Onion/Potato) or return 422 (RecTomato has no trained model).
    Both outcomes are valid — the important thing is no 500.
    """
    r = client.post("/api/recommendation/market", headers=_FARMER_H,
                    json={"crop_id": _CROP_KG, "quantity_kg": 100, "price_basis": "predicted"})
    assert r.status_code in (201, 422)
    if r.status_code == 201:
        assert r.json()["price_basis"] == "predicted"


# ── History & isolation ───────────────────────────────────────────────────────

def test_recommendation_saved_to_history():
    r = client.post("/api/recommendation/market", headers=_FARMER_H,
                    json={"crop_id": _CROP_KG, "quantity_kg": 200, "price_basis": "current"})
    assert r.status_code == 201
    saved_id = r.json()["saved_recommendation_id"]
    assert saved_id is not None and saved_id > 0

    hist = client.get("/api/recommendation/history", headers=_FARMER_H)
    assert hist.status_code == 200
    ids = [h["id"] for h in hist.json()]
    assert saved_id in ids


def test_history_requires_auth():
    r = client.get("/api/recommendation/history")
    assert r.status_code == 401


def test_history_farmer_isolation():
    """Farmer 2 must not see Farmer 1's recommendations."""
    # Trigger a recommendation for farmer 1
    client.post("/api/recommendation/market", headers=_FARMER_H,
                json={"crop_id": _CROP_KG, "quantity_kg": 300, "price_basis": "current"})

    # Farmer 2's history must be separate
    hist1 = client.get("/api/recommendation/history", headers=_FARMER_H).json()
    hist2 = client.get("/api/recommendation/history", headers=_FARMER2_H).json()
    ids1 = {h["id"] for h in hist1}
    ids2 = {h["id"] for h in hist2}
    assert ids1.isdisjoint(ids2), "Farmer 1 and Farmer 2 share recommendation records"


def test_history_buyer_blocked():
    h = _make_auth("rec_buyer_hist@test.com", role="BUYER")
    r = client.get("/api/recommendation/history", headers=h)
    assert r.status_code == 403
