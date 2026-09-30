"""
Phase 3 authentication tests.
Uses the shared SQLite engine from conftest.py — no PostgreSQL required.
"""

# Models must be first
import app.models  # noqa: F401

from fastapi.testclient import TestClient
from tests.conftest import get_test_session
from app.main import app as fastapi_app

client = TestClient(fastapi_app)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _register(email="farmer@test.com", role="FARMER", password="Password1"):
    return client.post("/api/auth/register", json={
        "full_name": "Test User",
        "email": email,
        "password": password,
        "role": role,
    })


def _login(email="farmer@test.com", password="Password1"):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def _token(email, password="Password1"):
    r = _register(email, password=password)
    if r.status_code not in (201, 409):
        raise RuntimeError(f"Register failed: {r.text}")
    resp = _login(email, password)
    if resp.status_code != 200:
        raise RuntimeError(f"Login failed: {resp.text}")
    return resp.json()["access_token"]


# ── Registration tests ────────────────────────────────────────────────────────

def test_register_farmer():
    r = _register("farmer_reg@test.com", role="FARMER")
    assert r.status_code == 201
    data = r.json()
    assert data["user"]["role"] == "FARMER"
    assert "password" not in data["user"]
    assert "password_hash" not in data["user"]


def test_register_buyer():
    r = _register("buyer_reg@test.com", role="BUYER")
    assert r.status_code == 201
    assert r.json()["user"]["role"] == "BUYER"


def test_register_admin_rejected():
    r = client.post("/api/auth/register", json={
        "full_name": "Hacker", "email": "hack@test.com",
        "password": "Password1", "role": "ADMIN",
    })
    assert r.status_code == 422


def test_register_duplicate_email():
    _register("dup@test.com")
    r = _register("dup@test.com")
    assert r.status_code == 409
    assert "already exists" in r.json()["detail"].lower()


def test_register_invalid_email():
    r = client.post("/api/auth/register", json={
        "full_name": "Bad", "email": "not-an-email",
        "password": "Password1", "role": "FARMER",
    })
    assert r.status_code == 422


def test_register_weak_password_too_short():
    r = client.post("/api/auth/register", json={
        "full_name": "Weak", "email": "weak1@test.com",
        "password": "abc123", "role": "FARMER",
    })
    assert r.status_code == 422


def test_register_weak_password_no_number():
    r = client.post("/api/auth/register", json={
        "full_name": "Weak", "email": "weak2@test.com",
        "password": "abcdefgh", "role": "FARMER",
    })
    assert r.status_code == 422


def test_register_weak_password_no_letter():
    r = client.post("/api/auth/register", json={
        "full_name": "Weak", "email": "weak3@test.com",
        "password": "12345678", "role": "FARMER",
    })
    assert r.status_code == 422


def test_register_invalid_role():
    r = client.post("/api/auth/register", json={
        "full_name": "Bad", "email": "badrole@test.com",
        "password": "Password1", "role": "SUPERUSER",
    })
    assert r.status_code == 422


# ── Login tests ───────────────────────────────────────────────────────────────

def test_login_success():
    _register("login_ok@test.com")
    r = _login("login_ok@test.com")
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password():
    _register("login_wp@test.com")
    r = _login("login_wp@test.com", password="WrongPass9")
    assert r.status_code == 401


def test_login_unknown_email():
    r = _login("nobody@test.com")
    assert r.status_code == 401


def test_login_inactive_account():
    _register("inactive@test.com")
    from app.models.user import User
    db = get_test_session()
    user = db.query(User).filter_by(email="inactive@test.com").first()
    assert user is not None, "User was not created"
    user.is_active = False
    db.commit()
    db.close()
    r = _login("inactive@test.com")
    assert r.status_code == 401


# ── JWT tests ─────────────────────────────────────────────────────────────────

def test_valid_token_me():
    token = _token("jwt_ok@test.com")
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == "jwt_ok@test.com"


def test_missing_token():
    r = client.get("/api/auth/me")
    assert r.status_code == 401


def test_malformed_token():
    r = client.get("/api/auth/me", headers={"Authorization": "Bearer notavalidtoken"})
    assert r.status_code == 401


def test_expired_token():
    from datetime import timedelta
    from app.core.security import create_access_token
    _register("exp@test.com")
    token = create_access_token(
        {"sub": "9999", "role": "FARMER"},
        expires_delta=timedelta(seconds=-1),
    )
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


# ── Current user ──────────────────────────────────────────────────────────────

def test_me_returns_no_password_hash():
    token = _token("me_check@test.com")
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert "password_hash" not in data
    assert "password" not in data


def test_me_unauthorized():
    r = client.get("/api/auth/me")
    assert r.status_code == 401


# ── Role authorisation ────────────────────────────────────────────────────────

def test_farmer_can_access_farmer_endpoint():
    token = _token("role_farmer@test.com")
    r = client.get("/api/auth/test/farmer", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["message"] == "Farmer access verified"


def test_buyer_cannot_access_farmer_endpoint():
    _register("role_buyer_f@test.com", role="BUYER")
    token = _login("role_buyer_f@test.com").json()["access_token"]
    r = client.get("/api/auth/test/farmer", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403


def test_buyer_can_access_buyer_endpoint():
    _register("role_buyer_ok@test.com", role="BUYER")
    token = _login("role_buyer_ok@test.com").json()["access_token"]
    r = client.get("/api/auth/test/buyer", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200


def test_farmer_cannot_access_admin_endpoint():
    token = _token("role_farmer_adm@test.com")
    r = client.get("/api/auth/test/admin", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403


def test_admin_can_access_admin_endpoint():
    from app.core.security import hash_password
    from app.models.user import User, UserRole
    db = get_test_session()
    # Only create if not already present
    existing = db.query(User).filter_by(email="admin_role@test.com").first()
    if not existing:
        admin = User(
            full_name="Admin",
            email="admin_role@test.com",
            password_hash=hash_password("AdminPass1"),
            role=UserRole.ADMIN,
            is_active=True,
        )
        db.add(admin)
        db.commit()
    db.close()
    token = _login("admin_role@test.com", "AdminPass1").json()["access_token"]
    r = client.get("/api/auth/test/admin", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["message"] == "Admin access verified"


# ── Security: password never returned ────────────────────────────────────────

def test_register_response_has_no_password():
    r = _register("nopw_reg@test.com")
    assert r.status_code == 201
    assert "password_hash" not in r.text
