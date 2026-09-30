"""
Phase 5 — Market Intelligence tests.
Uses the shared SQLite engine from conftest.py — no PostgreSQL required.
"""

import app.models  # noqa: F401

import datetime
from fastapi.testclient import TestClient
from tests.conftest import get_test_session
from app.main import app as fastapi_app
from app.models.crop import Crop, CropUnit
from app.models.market import Market, MarketType
from app.models.market_price import MarketPrice

client = TestClient(fastapi_app)

# Module-level refs populated in setup_module
_CROP_TID = None
_CROP_TID2 = None
_MKT_A = None
_MKT_B = None
_FARMER_H = None


# ── Seed helpers ──────────────────────────────────────────────────────────────

def _seed_crop(name, unit=CropUnit.KG):
    db = get_test_session()
    c = db.query(Crop).filter_by(name=name).first()
    if not c:
        c = Crop(name=name, unit=unit, is_active=True, category="Vegetable")
        db.add(c); db.commit(); db.refresh(c)
    cid = c.id; db.close()
    return cid


def _seed_market(code, name, district="Test District", state="Tamil Nadu"):
    db = get_test_session()
    m = db.query(Market).filter_by(market_code=code).first()
    if not m:
        m = Market(name=name, market_code=code, district=district,
                   state=state, location=district, market_type=MarketType.APMC, is_active=True)
        db.add(m); db.commit(); db.refresh(m)
    mid = m.id; db.close()
    return mid


def _seed_price(market_id, crop_id, modal, price_date=None, mn=None, mx=None):
    db = get_test_session()
    pd = price_date or datetime.date.today()
    mn = mn if mn is not None else round(modal * 0.9, 2)
    mx = mx if mx is not None else round(modal * 1.1, 2)
    existing = db.query(MarketPrice).filter_by(
        market_id=market_id, crop_id=crop_id, price_date=pd
    ).first()
    if not existing:
        p = MarketPrice(market_id=market_id, crop_id=crop_id,
                        price_date=pd, min_price=mn, modal_price=modal, max_price=mx,
                        source="development_sample")
        db.add(p); db.commit()
    db.close()


def _make_farmer_headers(email):
    """Register (idempotent) and login; return auth headers."""
    client.post("/api/auth/register", json={
        "full_name": "Market Tester",
        "email": email,
        "password": "Password1",
        "role": "FARMER",
    })
    r = client.post("/api/auth/login", json={"email": email, "password": "Password1"})
    assert r.status_code == 200, f"Login failed: {r.text}"
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def setup_module(_module):
    """Seed all test data before any test runs."""
    global _CROP_TID, _CROP_TID2, _MKT_A, _MKT_B, _FARMER_H

    _CROP_TID  = _seed_crop("TestTomato")
    _CROP_TID2 = _seed_crop("TestOnion", CropUnit.QUINTAL)
    _MKT_A = _seed_market("TEST-MKT-A", "Test Market A", "Coimbatore")
    _MKT_B = _seed_market("TEST-MKT-B", "Test Market B", "Erode")

    # Today's prices
    _seed_price(_MKT_A, _CROP_TID, 25.0)
    _seed_price(_MKT_B, _CROP_TID, 28.0)

    # Historical prices: 10 days back
    today = datetime.date.today()
    for i in range(1, 11):
        _seed_price(_MKT_A, _CROP_TID, round(24.0 + i * 0.5, 2),
                    price_date=today - datetime.timedelta(days=i))

    _FARMER_H = _make_farmer_headers("mkt_farmer@test.com")


# ── Markets ───────────────────────────────────────────────────────────────────

def test_list_markets():
    r = client.get("/api/market/markets", headers=_FARMER_H)
    assert r.status_code == 200
    codes = [m["market_code"] for m in r.json()]
    assert "TEST-MKT-A" in codes
    assert "TEST-MKT-B" in codes


def test_list_markets_requires_auth():
    r = client.get("/api/market/markets")
    assert r.status_code == 401


def test_list_markets_filter_state():
    r = client.get("/api/market/markets?state=Tamil Nadu", headers=_FARMER_H)
    assert r.status_code == 200
    for m in r.json():
        assert "Tamil Nadu" in m["state"]


def test_list_markets_filter_district():
    r = client.get("/api/market/markets?district=Coimbatore", headers=_FARMER_H)
    assert r.status_code == 200
    for m in r.json():
        assert "Coimbatore" in m["district"]


# ── Crops with price data ─────────────────────────────────────────────────────

def test_list_crops_with_prices():
    r = client.get("/api/market/crops", headers=_FARMER_H)
    assert r.status_code == 200
    names = [c["name"] for c in r.json()]
    assert "TestTomato" in names


def test_list_crops_requires_auth():
    r = client.get("/api/market/crops")
    assert r.status_code == 401


# ── Price list ────────────────────────────────────────────────────────────────

def test_list_prices():
    r = client.get("/api/market/prices", headers=_FARMER_H)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_list_prices_filter_crop():
    r = client.get(f"/api/market/prices?crop_id={_CROP_TID}", headers=_FARMER_H)
    assert r.status_code == 200
    for p in r.json():
        assert p["crop"]["id"] == _CROP_TID


def test_list_prices_filter_market():
    r = client.get(f"/api/market/prices?market_id={_MKT_A}", headers=_FARMER_H)
    assert r.status_code == 200
    for p in r.json():
        assert p["market"]["id"] == _MKT_A


def test_list_prices_filter_date_range():
    today = datetime.date.today().isoformat()
    r = client.get(f"/api/market/prices?from={today}&to={today}", headers=_FARMER_H)
    assert r.status_code == 200
    for p in r.json():
        assert p["price_date"] == today


def test_list_prices_requires_auth():
    r = client.get("/api/market/prices")
    assert r.status_code == 401


# ── Price comparison ──────────────────────────────────────────────────────────

def test_compare_prices():
    r = client.get(f"/api/market/prices/{_CROP_TID}", headers=_FARMER_H)
    assert r.status_code == 200
    data = r.json()
    assert data["crop"]["id"] == _CROP_TID
    assert isinstance(data["prices"], list)
    assert len(data["prices"]) >= 2
    assert "data_notice" in data


def test_compare_prices_sorted_best_first():
    r = client.get(f"/api/market/prices/{_CROP_TID}", headers=_FARMER_H)
    prices = [p["modal_price"] for p in r.json()["prices"]]
    assert prices == sorted(prices, reverse=True)


def test_compare_prices_response_schema():
    r = client.get(f"/api/market/prices/{_CROP_TID}", headers=_FARMER_H)
    assert r.status_code == 200
    for entry in r.json()["prices"]:
        assert "market_name" in entry
        assert "modal_price" in entry
        assert "min_price" in entry
        assert "max_price" in entry
        assert "price_date" in entry


def test_compare_prices_invalid_crop():
    r = client.get("/api/market/prices/99999", headers=_FARMER_H)
    assert r.status_code == 404


def test_compare_prices_filter_district():
    r = client.get(f"/api/market/prices/{_CROP_TID}?district=Coimbatore", headers=_FARMER_H)
    assert r.status_code == 200
    for p in r.json()["prices"]:
        assert "Coimbatore" in (p["district"] or "")


def test_compare_prices_requires_auth():
    r = client.get(f"/api/market/prices/{_CROP_TID}")
    assert r.status_code == 401


# ── Historical prices ─────────────────────────────────────────────────────────

def test_price_history():
    r = client.get(f"/api/market/prices/{_CROP_TID}/history?days=30", headers=_FARMER_H)
    assert r.status_code == 200
    data = r.json()
    assert data["crop"]["id"] == _CROP_TID
    assert data["days"] == 30
    assert isinstance(data["history"], list)
    assert "data_notice" in data


def test_price_history_contains_historical_records():
    r = client.get(f"/api/market/prices/{_CROP_TID}/history?days=30", headers=_FARMER_H)
    assert r.status_code == 200
    assert len(r.json()["history"]) >= 5


def test_price_history_sorted_asc():
    r = client.get(f"/api/market/prices/{_CROP_TID}/history?days=30", headers=_FARMER_H)
    dates = [h["price_date"] for h in r.json()["history"]]
    assert dates == sorted(dates)


def test_price_history_7_days():
    r = client.get(f"/api/market/prices/{_CROP_TID}/history?days=7", headers=_FARMER_H)
    assert r.status_code == 200
    cutoff = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
    for h in r.json()["history"]:
        assert h["price_date"] >= cutoff


def test_price_history_market_filter():
    r = client.get(
        f"/api/market/prices/{_CROP_TID}/history?days=30&market_id={_MKT_A}",
        headers=_FARMER_H,
    )
    assert r.status_code == 200
    for h in r.json()["history"]:
        assert h["market_id"] == _MKT_A


def test_price_history_invalid_crop():
    r = client.get("/api/market/prices/99999/history", headers=_FARMER_H)
    assert r.status_code == 404


def test_price_history_invalid_market():
    r = client.get(
        f"/api/market/prices/{_CROP_TID}/history?market_id=99999",
        headers=_FARMER_H,
    )
    assert r.status_code == 404


def test_price_history_empty_range():
    """days=1 with only older data returns empty list without error."""
    r = client.get(f"/api/market/prices/{_CROP_TID}/history?days=1", headers=_FARMER_H)
    assert r.status_code == 200


def test_price_history_requires_auth():
    r = client.get(f"/api/market/prices/{_CROP_TID}/history")
    assert r.status_code == 401
