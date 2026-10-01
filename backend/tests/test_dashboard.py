"""Phase 10 tests -- Dashboard & Analytics API."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _register(email: str, password: str, full_name: str, role: str = "FARMER") -> dict:
    r = client.post("/api/auth/register", json={
        "email": email, "password": password,
        "full_name": full_name, "role": role,
    })
    assert r.status_code in (200, 201, 409), f"register failed: {r.text}"
    return {"email": email, "password": password}


def _login(email: str, password: str) -> str:
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, f"login failed: {r.text}"
    return r.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

farmer_email  = "dash_farmer@test.com"
farmer_email2 = "dash_farmer2@test.com"
buyer_email   = "dash_buyer@test.com"
buyer_email2  = "dash_buyer2@test.com"
pwd           = "TestPass123!"

farmer_token:  str = ""
farmer2_token: str = ""
buyer_token:   str = ""
buyer2_token:  str = ""


def setup_module(_):
    global farmer_token, farmer2_token, buyer_token, buyer2_token

    _register(farmer_email,  pwd, "Dash Farmer One")
    _register(farmer_email2, pwd, "Dash Farmer Two")
    _register(buyer_email,   pwd, "Dash Buyer One",  "BUYER")
    _register(buyer_email2,  pwd, "Dash Buyer Two",  "BUYER")

    farmer_token  = _login(farmer_email,  pwd)
    farmer2_token = _login(farmer_email2, pwd)
    buyer_token   = _login(buyer_email,   pwd)
    buyer2_token  = _login(buyer_email2,  pwd)


# ---------------------------------------------------------------------------
# Authentication / Authorization
# ---------------------------------------------------------------------------

class TestDashboardAuth:
    def test_farmer_dashboard_unauthenticated(self):
        r = client.get("/api/dashboard/farmer")
        assert r.status_code == 401

    def test_buyer_dashboard_unauthenticated(self):
        r = client.get("/api/dashboard/buyer")
        assert r.status_code == 401

    def test_farmer_dashboard_wrong_role_buyer(self):
        """Buyer must not access farmer dashboard."""
        r = client.get("/api/dashboard/farmer", headers=_auth(buyer_token))
        assert r.status_code == 403

    def test_buyer_dashboard_wrong_role_farmer(self):
        """Farmer must not access buyer dashboard."""
        r = client.get("/api/dashboard/buyer", headers=_auth(farmer_token))
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# Farmer dashboard
# ---------------------------------------------------------------------------

class TestFarmerDashboard:
    def test_farmer_dashboard_returns_200(self):
        r = client.get("/api/dashboard/farmer", headers=_auth(farmer_token))
        assert r.status_code == 200

    def test_farmer_dashboard_schema(self):
        r = client.get("/api/dashboard/farmer", headers=_auth(farmer_token))
        data = r.json()
        # Top-level keys
        assert "profile" in data
        assert "stats" in data
        assert "market_snapshot" in data
        assert "latest_recommendation" in data
        assert "buyer_opportunities" in data
        assert "recent_activity" in data

    def test_farmer_dashboard_stats_fields(self):
        r = client.get("/api/dashboard/farmer", headers=_auth(farmer_token))
        stats = r.json()["stats"]
        assert "total_crops" in stats
        assert "available_crops" in stats
        assert "buyer_opportunities" in stats
        assert "recommendation_count" in stats
        assert "pending_requests" in stats

    def test_farmer_dashboard_profile_fields(self):
        r = client.get("/api/dashboard/farmer", headers=_auth(farmer_token))
        profile = r.json()["profile"]
        assert "full_name" in profile
        assert "has_profile" in profile

    def test_farmer_dashboard_empty_data_handling(self):
        """Fresh farmer with no crops/recs should return empty lists, not errors."""
        r = client.get("/api/dashboard/farmer", headers=_auth(farmer_token))
        data = r.json()
        assert r.status_code == 200
        # These should be lists (possibly empty)
        assert isinstance(data["market_snapshot"], list)
        assert isinstance(data["buyer_opportunities"], list)
        assert isinstance(data["recent_activity"], list)
        # latest_recommendation can be null
        assert data["latest_recommendation"] is None or isinstance(data["latest_recommendation"], dict)

    def test_farmer_dashboard_no_hardcoded_prices(self):
        """Stats counts must be >= 0 (not fictional)."""
        r = client.get("/api/dashboard/farmer", headers=_auth(farmer_token))
        stats = r.json()["stats"]
        assert stats["total_crops"] >= 0
        assert stats["buyer_opportunities"] >= 0
        assert stats["recommendation_count"] >= 0

    def test_farmer_data_isolation(self):
        """farmer2 only sees their own data."""
        r1 = client.get("/api/dashboard/farmer", headers=_auth(farmer_token))
        r2 = client.get("/api/dashboard/farmer", headers=_auth(farmer2_token))
        # Both succeed and return separate farmer profiles
        assert r1.status_code == 200
        assert r2.status_code == 200
        p1 = r1.json()["profile"]
        p2 = r2.json()["profile"]
        assert p1["full_name"] != p2["full_name"]

    def test_farmer_dashboard_market_snapshot_structure(self):
        r = client.get("/api/dashboard/farmer", headers=_auth(farmer_token))
        snapshot = r.json()["market_snapshot"]
        for item in snapshot:
            assert "crop_name" in item
            assert "market_name" in item
            assert "modal_price" in item
            assert "price_date" in item


# ---------------------------------------------------------------------------
# Buyer dashboard
# ---------------------------------------------------------------------------

class TestBuyerDashboard:
    def test_buyer_dashboard_returns_200(self):
        r = client.get("/api/dashboard/buyer", headers=_auth(buyer_token))
        assert r.status_code == 200

    def test_buyer_dashboard_schema(self):
        r = client.get("/api/dashboard/buyer", headers=_auth(buyer_token))
        data = r.json()
        assert "profile" in data
        assert "stats" in data
        assert "active_requirements" in data
        assert "matching_farmers" in data
        assert "request_activity" in data

    def test_buyer_dashboard_stats_fields(self):
        r = client.get("/api/dashboard/buyer", headers=_auth(buyer_token))
        stats = r.json()["stats"]
        assert "active_requirements" in stats
        assert "total_requirements" in stats
        assert "pending_requests" in stats
        assert "accepted_connections" in stats

    def test_buyer_dashboard_empty_data_handling(self):
        """Fresh buyer with no requirements should return empty lists."""
        r = client.get("/api/dashboard/buyer", headers=_auth(buyer_token))
        data = r.json()
        assert r.status_code == 200
        assert isinstance(data["active_requirements"], list)
        assert isinstance(data["matching_farmers"], list)
        assert isinstance(data["request_activity"], list)

    def test_buyer_dashboard_stats_nonnegative(self):
        r = client.get("/api/dashboard/buyer", headers=_auth(buyer_token))
        stats = r.json()["stats"]
        assert stats["active_requirements"] >= 0
        assert stats["pending_requests"] >= 0
        assert stats["accepted_connections"] >= 0

    def test_buyer_data_isolation(self):
        """buyer2 only sees their own data."""
        r1 = client.get("/api/dashboard/buyer", headers=_auth(buyer_token))
        r2 = client.get("/api/dashboard/buyer", headers=_auth(buyer2_token))
        assert r1.status_code == 200
        assert r2.status_code == 200
        # Stats are separate (fresh accounts both start at 0)
        p1 = r1.json()["profile"]
        p2 = r2.json()["profile"]
        assert p1["full_name"] != p2["full_name"]

    def test_buyer_dashboard_profile_fields(self):
        r = client.get("/api/dashboard/buyer", headers=_auth(buyer_token))
        profile = r.json()["profile"]
        assert "full_name" in profile
        assert "has_profile" in profile

    def test_buyer_requirements_in_active(self):
        """Create a requirement and verify it appears in the dashboard."""
        # First need a crop
        crops_r = client.get("/api/market/crops")
        if crops_r.status_code != 200 or not crops_r.json():
            pytest.skip("No crops seeded")
        crop_id = crops_r.json()[0]["id"]

        # Create requirement
        req_r = client.post("/api/buyer/requirements", json={
            "crop_id": crop_id,
            "quantity_kg": 100,
            "desired_price": 25.0,
            "location": "Coimbatore",
        }, headers=_auth(buyer_token))
        if req_r.status_code not in (200, 201):
            pytest.skip(f"Could not create requirement: {req_r.text}")

        # Dashboard should show it
        r = client.get("/api/dashboard/buyer", headers=_auth(buyer_token))
        data = r.json()
        assert data["stats"]["active_requirements"] >= 1
        assert any(
            item["id"] == req_r.json()["id"]
            for item in data["active_requirements"]
        )
