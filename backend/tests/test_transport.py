"""
Phase 6 — Location and transport cost tests.
Uses the shared SQLite engine from conftest.py.
"""

import app.models  # noqa: F401

import math
import pytest
from fastapi.testclient import TestClient
from tests.conftest import get_test_session
from app.main import app as fastapi_app
from app.models.farmer import Farmer
from app.models.market import Market, MarketType
from app.services.location import (
    haversine_km,
    estimate_transport_cost,
    resolve_farmer_coords,
    resolve_market_coords,
    CoordinateError,
    LocationError,
)

client = TestClient(fastapi_app)

# Module-level refs set in setup_module
_MKT_WITH_COORDS = None
_MKT_NO_COORDS   = None
_FARMER_H        = None   # farmer with district only
_FARMER_GPS_H    = None   # farmer with stored GPS coords


def _make_auth(email, role="FARMER", password="Password1"):
    reg = client.post("/api/auth/register", json={
        "full_name": "Test User", "email": email, "password": password, "role": role,
    })
    if reg.status_code == 409:
        from app.models.user import User
        db = get_test_session()
        u = db.query(User).filter_by(email=email).first()
        if u:
            u.is_active = True
            db.commit()
        db.close()
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, f"Login failed for {email}: {r.text}"
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def setup_module(_m):
    global _MKT_WITH_COORDS, _MKT_NO_COORDS, _FARMER_H, _FARMER_GPS_H

    db = get_test_session()

    # Market WITH coordinates (Coimbatore)
    m1 = db.query(Market).filter_by(market_code="T6-MKT-GPS").first()
    if not m1:
        m1 = Market(name="Transport Test Market GPS", market_code="T6-MKT-GPS",
                    district="Coimbatore", state="Tamil Nadu",
                    latitude=11.0168, longitude=76.9558,
                    market_type=MarketType.APMC, is_active=True)
        db.add(m1); db.commit(); db.refresh(m1)
    _MKT_WITH_COORDS = m1.id

    # Market WITHOUT coordinates
    m2 = db.query(Market).filter_by(market_code="T6-MKT-NOGPS").first()
    if not m2:
        m2 = Market(name="Transport Test Market NoGPS", market_code="T6-MKT-NOGPS",
                    district="Unknown", state="Tamil Nadu",
                    latitude=None, longitude=None,
                    market_type=MarketType.LOCAL, is_active=True)
        db.add(m2); db.commit(); db.refresh(m2)
    _MKT_NO_COORDS = m2.id

    db.close()

    # Farmer with district=Coimbatore (no GPS stored)
    _FARMER_H = _make_auth("t6_farmer_district@test.com")
    client.put("/api/farmer/profile", headers=_FARMER_H,
               json={"district": "Coimbatore", "state": "Tamil Nadu"})

    # Farmer with stored GPS coords (Erode)
    _FARMER_GPS_H = _make_auth("t6_farmer_gps@test.com")
    # Update via DB since profile endpoint doesn't expose lat/lon yet
    db = get_test_session()
    from app.models.user import User
    u = db.query(User).filter_by(email="t6_farmer_gps@test.com").first()
    if u:
        f = db.query(Farmer).filter_by(user_id=u.id).first()
        if not f:
            f = Farmer(user_id=u.id)
            db.add(f)
        f.latitude = 11.3410
        f.longitude = 77.7172
        f.district = "Erode"
        db.commit()
    db.close()


# ── Unit tests: Haversine ─────────────────────────────────────────────────────

def test_haversine_same_point():
    assert haversine_km(11.0, 77.0, 11.0, 77.0) == pytest.approx(0.0, abs=0.01)


def test_haversine_known_distance():
    # Coimbatore → Erode ≈ 80 km straight line
    dist = haversine_km(11.0168, 76.9558, 11.3410, 77.7172)
    assert 70 < dist < 100  # known approximate range


def test_haversine_invalid_lat():
    with pytest.raises(CoordinateError):
        haversine_km(91.0, 0.0, 0.0, 0.0)


def test_haversine_invalid_lon():
    with pytest.raises(CoordinateError):
        haversine_km(0.0, 181.0, 0.0, 0.0)


def test_haversine_invalid_lat2():
    with pytest.raises(CoordinateError):
        haversine_km(0.0, 0.0, -91.0, 0.0)


def test_haversine_symmetry():
    d1 = haversine_km(11.0168, 76.9558, 11.3410, 77.7172)
    d2 = haversine_km(11.3410, 77.7172, 11.0168, 76.9558)
    assert d1 == pytest.approx(d2, abs=0.001)


# ── Unit tests: location resolution ──────────────────────────────────────────

def test_resolve_farmer_uses_stored_coords():
    lat, lon = resolve_farmer_coords(12.0, 78.0, "Coimbatore")
    assert lat == 12.0 and lon == 78.0


def test_resolve_farmer_uses_district_lookup():
    lat, lon = resolve_farmer_coords(None, None, "Coimbatore")
    assert abs(lat - 11.0168) < 0.01


def test_resolve_farmer_case_insensitive():
    lat, lon = resolve_farmer_coords(None, None, "ERODE")
    assert lat is not None


def test_resolve_farmer_unknown_district():
    with pytest.raises(LocationError):
        resolve_farmer_coords(None, None, "Atlantis")


def test_resolve_farmer_no_info():
    with pytest.raises(LocationError):
        resolve_farmer_coords(None, None, None)


def test_resolve_market_with_coords():
    lat, lon = resolve_market_coords(11.0, 77.0, "Test Market")
    assert lat == 11.0 and lon == 77.0


def test_resolve_market_without_coords():
    with pytest.raises(LocationError):
        resolve_market_coords(None, None, "No GPS Market")


# ── Unit tests: transport cost ────────────────────────────────────────────────

def test_transport_cost_basic():
    cost = estimate_transport_cost(100, 10, 200, 2.5)
    assert cost == pytest.approx(200 + 100 * 2.5 * 10)  # 2700


def test_transport_cost_zero_distance():
    cost = estimate_transport_cost(0, 10, 200, 2.5)
    assert cost == pytest.approx(200.0)


def test_transport_cost_negative_distance():
    with pytest.raises(ValueError):
        estimate_transport_cost(-1, 10, 200, 2.5)


def test_transport_cost_zero_quantity():
    with pytest.raises(ValueError):
        estimate_transport_cost(100, 0, 200, 2.5)


def test_transport_cost_negative_quantity():
    with pytest.raises(ValueError):
        estimate_transport_cost(100, -5, 200, 2.5)


# ── API: distance ─────────────────────────────────────────────────────────────

def test_distance_endpoint():
    r = client.get(f"/api/transport/distance/{_MKT_WITH_COORDS}", headers=_FARMER_H)
    assert r.status_code == 200
    d = r.json()
    assert d["market_id"] == _MKT_WITH_COORDS
    assert d["distance_km"] >= 0
    assert "farmer_location_source" in d
    assert d["farmer_location_source"] == "district_lookup"


def test_distance_stored_gps():
    r = client.get(f"/api/transport/distance/{_MKT_WITH_COORDS}", headers=_FARMER_GPS_H)
    assert r.status_code == 200
    d = r.json()
    assert d["farmer_location_source"] == "stored_coordinates"
    assert d["distance_km"] >= 0


def test_distance_invalid_market():
    r = client.get("/api/transport/distance/99999", headers=_FARMER_H)
    assert r.status_code == 404


def test_distance_market_no_coords():
    r = client.get(f"/api/transport/distance/{_MKT_NO_COORDS}", headers=_FARMER_H)
    assert r.status_code == 422


def test_distance_requires_auth():
    r = client.get(f"/api/transport/distance/{_MKT_WITH_COORDS}")
    assert r.status_code == 401


def test_distance_no_farmer_profile():
    h = _make_auth("t6_noprofile@test.com")
    r = client.get(f"/api/transport/distance/{_MKT_WITH_COORDS}", headers=h)
    assert r.status_code == 422


# ── API: single-market estimate ───────────────────────────────────────────────

def test_estimate_endpoint():
    r = client.get(f"/api/transport/estimate/{_MKT_WITH_COORDS}?quantity=50",
                   headers=_FARMER_H)
    assert r.status_code == 200
    d = r.json()
    assert d["market_id"] == _MKT_WITH_COORDS
    assert d["quantity_quintals"] == 50
    assert d["estimated_transport_cost"] >= 0
    assert d["currency"] == "INR"
    assert "assumptions" in d
    assert "disclaimer" in d


def test_estimate_invalid_quantity_zero():
    r = client.get(f"/api/transport/estimate/{_MKT_WITH_COORDS}?quantity=0",
                   headers=_FARMER_H)
    assert r.status_code == 422


def test_estimate_invalid_quantity_negative():
    r = client.get(f"/api/transport/estimate/{_MKT_WITH_COORDS}?quantity=-5",
                   headers=_FARMER_H)
    assert r.status_code == 422


def test_estimate_invalid_market():
    r = client.get("/api/transport/estimate/99999?quantity=10", headers=_FARMER_H)
    assert r.status_code == 404


def test_estimate_requires_auth():
    r = client.get(f"/api/transport/estimate/{_MKT_WITH_COORDS}?quantity=10")
    assert r.status_code == 401


# ── API: multi-market ─────────────────────────────────────────────────────────

def test_all_markets_endpoint():
    r = client.get("/api/transport/markets?quantity=20", headers=_FARMER_H)
    assert r.status_code == 200
    d = r.json()
    assert isinstance(d["markets"], list)
    assert d["quantity_quintals"] == 20
    assert "farmer_district" in d


def test_all_markets_sorted_by_distance():
    r = client.get("/api/transport/markets?quantity=10", headers=_FARMER_H)
    assert r.status_code == 200
    distances = [m["distance_km"] for m in r.json()["markets"]]
    assert distances == sorted(distances)


def test_all_markets_skips_no_coords():
    """Markets without coordinates are skipped, not errored."""
    r = client.get("/api/transport/markets?quantity=10", headers=_FARMER_H)
    assert r.status_code == 200
    names = [m["market_name"] for m in r.json()["markets"]]
    assert "Transport Test Market NoGPS" not in names


def test_all_markets_filter_state():
    r = client.get("/api/transport/markets?quantity=5&state=Tamil Nadu", headers=_FARMER_H)
    assert r.status_code == 200


def test_all_markets_requires_auth():
    r = client.get("/api/transport/markets?quantity=10")
    assert r.status_code == 401
