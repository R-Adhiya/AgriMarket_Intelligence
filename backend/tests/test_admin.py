"""Phase 11 tests -- Admin Panel API."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.security import hash_password
from app.models.user import User, UserRole
from tests.conftest import get_test_session

client = TestClient(app)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _register(email, password, full_name, role="FARMER"):
    r = client.post("/api/auth/register", json={
        "email": email, "password": password,
        "full_name": full_name, "role": role,
    })
    assert r.status_code in (200, 201, 409), f"register failed: {r.text}"


def _login(email, password):
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, f"login failed: {r.text}"
    return r.json()["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

ADMIN_EMAIL   = "admin_test11@example.com"
ADMIN_PWD     = "AdminPass123!"
FARMER_EMAIL  = "adm_farmer11@test.com"
BUYER_EMAIL   = "adm_buyer11@test.com"
PWD           = "TestPass123!"

admin_token:  str = ""
farmer_token: str = ""
buyer_token:  str = ""
target_user_id: int = 0


def setup_module(_):
    global admin_token, farmer_token, buyer_token, target_user_id

    # Create admin directly via DB (registration endpoint blocks ADMIN role)
    db = get_test_session()
    try:
        existing = db.query(User).filter(User.email == ADMIN_EMAIL).first()
        if not existing:
            admin_user = User(
                full_name="Test Admin",
                email=ADMIN_EMAIL,
                password_hash=hash_password(ADMIN_PWD),
                role=UserRole.ADMIN,
                is_active=True,
            )
            db.add(admin_user)
            db.commit()
    finally:
        db.close()

    admin_token  = _login(ADMIN_EMAIL, ADMIN_PWD)

    _register(FARMER_EMAIL, PWD, "Adm Farmer Test")
    _register(BUYER_EMAIL,  PWD, "Adm Buyer Test", "BUYER")
    farmer_token = _login(FARMER_EMAIL, PWD)
    buyer_token  = _login(BUYER_EMAIL,  PWD)

    # Get the farmer's user ID for status tests
    r = client.get("/api/admin/users", headers=_auth(admin_token))
    for u in r.json()["items"]:
        if u["email"] == FARMER_EMAIL:
            target_user_id = u["id"]
            break


# ===========================================================================
# Authentication
# ===========================================================================

class TestAdminAuth:
    def test_dashboard_unauthenticated(self):
        assert client.get("/api/admin/dashboard").status_code == 401

    def test_users_unauthenticated(self):
        assert client.get("/api/admin/users").status_code == 401

    def test_farmers_unauthenticated(self):
        assert client.get("/api/admin/farmers").status_code == 401

    def test_buyers_unauthenticated(self):
        assert client.get("/api/admin/buyers").status_code == 401

    def test_markets_unauthenticated(self):
        assert client.get("/api/admin/markets").status_code == 401

    def test_prices_unauthenticated(self):
        assert client.get("/api/admin/market-prices").status_code == 401

    def test_activity_unauthenticated(self):
        assert client.get("/api/admin/activity").status_code == 401


# ===========================================================================
# Authorization -- FARMER gets 403
# ===========================================================================

class TestAdminAuthzFarmer:
    def test_dashboard_farmer_403(self):
        assert client.get("/api/admin/dashboard", headers=_auth(farmer_token)).status_code == 403

    def test_users_farmer_403(self):
        assert client.get("/api/admin/users", headers=_auth(farmer_token)).status_code == 403

    def test_farmers_farmer_403(self):
        assert client.get("/api/admin/farmers", headers=_auth(farmer_token)).status_code == 403

    def test_markets_farmer_403(self):
        assert client.get("/api/admin/markets", headers=_auth(farmer_token)).status_code == 403

    def test_activity_farmer_403(self):
        assert client.get("/api/admin/activity", headers=_auth(farmer_token)).status_code == 403


# ===========================================================================
# Authorization -- BUYER gets 403
# ===========================================================================

class TestAdminAuthzBuyer:
    def test_dashboard_buyer_403(self):
        assert client.get("/api/admin/dashboard", headers=_auth(buyer_token)).status_code == 403

    def test_users_buyer_403(self):
        assert client.get("/api/admin/users", headers=_auth(buyer_token)).status_code == 403

    def test_buyers_buyer_403(self):
        assert client.get("/api/admin/buyers", headers=_auth(buyer_token)).status_code == 403

    def test_activity_buyer_403(self):
        assert client.get("/api/admin/activity", headers=_auth(buyer_token)).status_code == 403


# ===========================================================================
# Admin Dashboard
# ===========================================================================

class TestAdminDashboard:
    def test_dashboard_200(self):
        r = client.get("/api/admin/dashboard", headers=_auth(admin_token))
        assert r.status_code == 200

    def test_dashboard_schema(self):
        r = client.get("/api/admin/dashboard", headers=_auth(admin_token))
        stats = r.json()["stats"]
        required = [
            "total_users", "total_farmers", "total_buyers", "total_admins",
            "total_farmer_profiles", "total_crop_listings", "available_crop_listings",
            "total_requirements", "active_requirements",
            "total_markets", "total_crops", "total_price_records",
            "total_recommendations",
            "total_interests", "pending_interests", "accepted_interests", "rejected_interests",
        ]
        for field in required:
            assert field in stats, f"Missing field: {field}"

    def test_dashboard_counts_nonnegative(self):
        r = client.get("/api/admin/dashboard", headers=_auth(admin_token))
        stats = r.json()["stats"]
        assert stats["total_users"] >= 0
        assert stats["total_farmers"] >= 0
        assert stats["total_buyers"] >= 0

    def test_dashboard_no_password_hash(self):
        r = client.get("/api/admin/dashboard", headers=_auth(admin_token))
        assert "password_hash" not in r.text
        assert "password" not in r.text.lower() or "total" in r.text.lower()


# ===========================================================================
# User Management
# ===========================================================================

class TestAdminUsers:
    def test_list_users_200(self):
        r = client.get("/api/admin/users", headers=_auth(admin_token))
        assert r.status_code == 200

    def test_list_users_schema(self):
        r = client.get("/api/admin/users", headers=_auth(admin_token))
        data = r.json()
        assert "total" in data
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_list_users_no_password_hash(self):
        r = client.get("/api/admin/users", headers=_auth(admin_token))
        assert "password_hash" not in r.text

    def test_filter_by_role_farmer(self):
        r = client.get("/api/admin/users?role=FARMER", headers=_auth(admin_token))
        assert r.status_code == 200
        for u in r.json()["items"]:
            assert u["role"] == "FARMER"

    def test_filter_by_role_buyer(self):
        r = client.get("/api/admin/users?role=BUYER", headers=_auth(admin_token))
        assert r.status_code == 200
        for u in r.json()["items"]:
            assert u["role"] == "BUYER"

    def test_filter_invalid_role_422(self):
        r = client.get("/api/admin/users?role=INVALID", headers=_auth(admin_token))
        assert r.status_code == 422

    def test_get_user_detail_200(self):
        if not target_user_id:
            pytest.skip("No target user found")
        r = client.get(f"/api/admin/users/{target_user_id}", headers=_auth(admin_token))
        assert r.status_code == 200
        data = r.json()
        assert "email" in data
        assert "role" in data
        assert "password_hash" not in data

    def test_get_user_not_found_404(self):
        r = client.get("/api/admin/users/999999", headers=_auth(admin_token))
        assert r.status_code == 404

    def test_deactivate_user(self):
        if not target_user_id:
            pytest.skip("No target user found")
        r = client.patch(
            f"/api/admin/users/{target_user_id}/status",
            json={"is_active": False},
            headers=_auth(admin_token),
        )
        assert r.status_code == 200
        assert r.json()["is_active"] is False

    def test_reactivate_user(self):
        if not target_user_id:
            pytest.skip("No target user found")
        r = client.patch(
            f"/api/admin/users/{target_user_id}/status",
            json={"is_active": True},
            headers=_auth(admin_token),
        )
        assert r.status_code == 200
        assert r.json()["is_active"] is True

    def test_admin_cannot_deactivate_self(self):
        """Admin should not be able to deactivate their own account."""
        # Get admin user id
        r = client.get("/api/admin/users?role=ADMIN", headers=_auth(admin_token))
        admin_id = r.json()["items"][0]["id"] if r.json()["items"] else None
        if not admin_id:
            pytest.skip("Admin user not found")
        r2 = client.patch(
            f"/api/admin/users/{admin_id}/status",
            json={"is_active": False},
            headers=_auth(admin_token),
        )
        assert r2.status_code == 400

    def test_status_update_not_found_404(self):
        r = client.patch(
            "/api/admin/users/999999/status",
            json={"is_active": False},
            headers=_auth(admin_token),
        )
        assert r.status_code == 404

    def test_status_update_invalid_payload_422(self):
        if not target_user_id:
            pytest.skip("No target user found")
        r = client.patch(
            f"/api/admin/users/{target_user_id}/status",
            json={"is_active": "not_a_bool"},
            headers=_auth(admin_token),
        )
        assert r.status_code == 422


# ===========================================================================
# Farmer Management
# ===========================================================================

class TestAdminFarmers:
    def test_list_farmers_200(self):
        r = client.get("/api/admin/farmers", headers=_auth(admin_token))
        assert r.status_code == 200

    def test_list_farmers_schema(self):
        r = client.get("/api/admin/farmers", headers=_auth(admin_token))
        data = r.json()
        assert "total" in data
        assert "items" in data
        for item in data["items"]:
            assert "user_id" in item
            assert "district" in item
            assert "crop_count" in item

    def test_farmer_filter_state(self):
        r = client.get("/api/admin/farmers?state=Tamil%20Nadu", headers=_auth(admin_token))
        assert r.status_code == 200

    def test_farmer_filter_district(self):
        r = client.get("/api/admin/farmers?district=Coimbatore", headers=_auth(admin_token))
        assert r.status_code == 200


# ===========================================================================
# Buyer Management
# ===========================================================================

class TestAdminBuyers:
    def test_list_buyers_200(self):
        r = client.get("/api/admin/buyers", headers=_auth(admin_token))
        assert r.status_code == 200

    def test_list_buyers_schema(self):
        r = client.get("/api/admin/buyers", headers=_auth(admin_token))
        data = r.json()
        assert "total" in data
        assert "items" in data
        for item in data["items"]:
            assert "user_id" in item
            assert "active_requirement_count" in item


# ===========================================================================
# Market Management
# ===========================================================================

class TestAdminMarkets:
    def test_list_markets_200(self):
        r = client.get("/api/admin/markets", headers=_auth(admin_token))
        assert r.status_code == 200

    def test_list_markets_schema(self):
        r = client.get("/api/admin/markets", headers=_auth(admin_token))
        data = r.json()
        assert "total" in data
        assert "items" in data
        for item in data["items"]:
            assert "name" in item
            assert "state" in item

    def test_market_prices_200(self):
        r = client.get("/api/admin/market-prices", headers=_auth(admin_token))
        assert r.status_code == 200

    def test_market_prices_schema(self):
        r = client.get("/api/admin/market-prices", headers=_auth(admin_token))
        data = r.json()
        assert "total" in data
        assert "items" in data
        for item in data["items"]:
            assert "crop_name" in item
            assert "market_name" in item
            assert "modal_price" in item


# ===========================================================================
# Activity
# ===========================================================================

class TestAdminActivity:
    def test_activity_200(self):
        r = client.get("/api/admin/activity", headers=_auth(admin_token))
        assert r.status_code == 200

    def test_activity_schema(self):
        r = client.get("/api/admin/activity", headers=_auth(admin_token))
        data = r.json()
        assert "items" in data
        for item in data["items"]:
            assert "kind" in item
            assert "description" in item
            assert "timestamp" in item

    def test_activity_limit_param(self):
        r = client.get("/api/admin/activity?limit=5", headers=_auth(admin_token))
        assert r.status_code == 200
        assert len(r.json()["items"]) <= 5

    def test_activity_no_password(self):
        r = client.get("/api/admin/activity", headers=_auth(admin_token))
        assert "password_hash" not in r.text


# ===========================================================================
# Security
# ===========================================================================

class TestAdminSecurity:
    def test_password_hash_never_in_user_list(self):
        r = client.get("/api/admin/users", headers=_auth(admin_token))
        assert "password_hash" not in r.text

    def test_password_hash_never_in_user_detail(self):
        r = client.get("/api/admin/users", headers=_auth(admin_token))
        if r.json()["items"]:
            uid = r.json()["items"][0]["id"]
            r2 = client.get(f"/api/admin/users/{uid}", headers=_auth(admin_token))
            assert "password_hash" not in r2.text

    def test_farmer_cannot_status_update(self):
        if not target_user_id:
            pytest.skip("No target user found")
        r = client.patch(
            f"/api/admin/users/{target_user_id}/status",
            json={"is_active": False},
            headers=_auth(farmer_token),
        )
        assert r.status_code == 403

    def test_buyer_cannot_status_update(self):
        if not target_user_id:
            pytest.skip("No target user found")
        r = client.patch(
            f"/api/admin/users/{target_user_id}/status",
            json={"is_active": False},
            headers=_auth(buyer_token),
        )
        assert r.status_code == 403
