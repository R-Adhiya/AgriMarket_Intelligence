"""
Phase 4 — Farmer module tests.
Uses the shared SQLite engine from conftest.py — no PostgreSQL required.
"""

import app.models  # noqa: F401

from fastapi.testclient import TestClient
from tests.conftest import get_test_session
from app.main import app as fastapi_app
from app.models.crop import Crop, CropUnit

client = TestClient(fastapi_app)


# ── Seed helpers ──────────────────────────────────────────────────────────────

def _seed_crop(name, unit=CropUnit.KG):
    db = get_test_session()
    crop = db.query(Crop).filter_by(name=name).first()
    if not crop:
        crop = Crop(name=name, unit=unit, is_active=True)
        db.add(crop)
        db.commit()
        db.refresh(crop)
    crop_id = crop.id
    db.close()
    return crop_id


def _register(email, role="FARMER", password="Password1"):
    r = client.post("/api/auth/register", json={
        "full_name": "Test Farmer",
        "email": email,
        "password": password,
        "role": role,
    })
    assert r.status_code in (201, 409), r.text
    return r


def _login(email, password="Password1"):
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _auth(email, role="FARMER", password="Password1"):
    _register(email, role, password)
    return {"Authorization": f"Bearer {_login(email, password)}"}


# ── Profile tests ─────────────────────────────────────────────────────────────

def test_get_profile_creates_if_missing():
    h = _auth("prof_get@test.com")
    r = client.get("/api/farmer/profile", headers=h)
    assert r.status_code == 200
    data = r.json()
    assert data["email"] == "prof_get@test.com"
    assert "password_hash" not in data
    assert "password" not in data


def test_update_profile():
    h = _auth("prof_upd@test.com")
    r = client.put("/api/farmer/profile", headers=h, json={
        "village": "Coimbatore",
        "district": "Coimbatore",
        "state": "Tamil Nadu",
        "farm_size": 3.5,
    })
    assert r.status_code == 200
    d = r.json()
    assert d["village"] == "Coimbatore"
    assert d["district"] == "Coimbatore"
    assert d["state"] == "Tamil Nadu"
    assert d["farm_size"] == 3.5


def test_update_profile_partial():
    h = _auth("prof_partial@test.com")
    client.put("/api/farmer/profile", headers=h, json={"state": "Kerala"})
    r = client.put("/api/farmer/profile", headers=h, json={"district": "Thrissur"})
    assert r.status_code == 200
    d = r.json()
    assert d["state"] == "Kerala"
    assert d["district"] == "Thrissur"


def test_profile_requires_auth():
    r = client.get("/api/farmer/profile")
    assert r.status_code == 401


def test_buyer_cannot_access_profile():
    h = _auth("buyer_prof@test.com", role="BUYER")
    r = client.get("/api/farmer/profile", headers=h)
    assert r.status_code == 403


def test_profile_no_password_exposed():
    h = _auth("prof_nopw@test.com")
    r = client.get("/api/farmer/profile", headers=h)
    assert r.status_code == 200
    assert "password_hash" not in r.text
    assert "password_hash" not in r.json()


# ── Crop tests ────────────────────────────────────────────────────────────────

def test_add_crop():
    crop_id = _seed_crop("Onion")
    h = _auth("crop_add@test.com")
    r = client.post("/api/farmer/crops", headers=h, json={
        "crop_id": crop_id,
        "quantity": 50,
        "unit": "quintal",
    })
    assert r.status_code == 201
    d = r.json()
    assert d["crop"]["name"] == "Onion"
    assert d["quantity"] == 50.0
    assert d["unit"] == "quintal"


def test_list_crops():
    crop_id = _seed_crop("Potato")
    h = _auth("crop_list@test.com")
    client.post("/api/farmer/crops", headers=h, json={"crop_id": crop_id, "quantity": 10, "unit": "kg"})
    r = client.get("/api/farmer/crops", headers=h)
    assert r.status_code == 200
    assert len(r.json()) >= 1


def test_update_crop():
    crop_id = _seed_crop("Rice")
    h = _auth("crop_upd@test.com")
    add = client.post("/api/farmer/crops", headers=h, json={"crop_id": crop_id, "quantity": 20, "unit": "quintal"})
    entry_id = add.json()["id"]
    r = client.put(f"/api/farmer/crops/{entry_id}", headers=h, json={"quantity": 35})
    assert r.status_code == 200
    assert r.json()["quantity"] == 35.0


def test_delete_crop():
    crop_id = _seed_crop("Wheat")
    h = _auth("crop_del@test.com")
    add = client.post("/api/farmer/crops", headers=h, json={"crop_id": crop_id, "quantity": 5, "unit": "ton"})
    entry_id = add.json()["id"]
    r = client.delete(f"/api/farmer/crops/{entry_id}", headers=h)
    assert r.status_code == 204
    r2 = client.get("/api/farmer/crops", headers=h)
    ids = [c["id"] for c in r2.json()]
    assert entry_id not in ids


def test_invalid_quantity_zero():
    crop_id = _seed_crop("Banana")
    h = _auth("crop_zero@test.com")
    r = client.post("/api/farmer/crops", headers=h, json={"crop_id": crop_id, "quantity": 0, "unit": "kg"})
    assert r.status_code == 422


def test_invalid_quantity_negative():
    crop_id = _seed_crop("Mango")
    h = _auth("crop_neg@test.com")
    r = client.post("/api/farmer/crops", headers=h, json={"crop_id": crop_id, "quantity": -5, "unit": "kg"})
    assert r.status_code == 422


def test_invalid_crop_id():
    h = _auth("crop_badid@test.com")
    r = client.post("/api/farmer/crops", headers=h, json={"crop_id": 99999, "quantity": 10, "unit": "kg"})
    assert r.status_code == 404


def test_crop_requires_auth():
    r = client.get("/api/farmer/crops")
    assert r.status_code == 401


def test_buyer_cannot_add_crop():
    h = _auth("buyer_crop@test.com", role="BUYER")
    r = client.post("/api/farmer/crops", headers=h, json={"crop_id": 1, "quantity": 10, "unit": "kg"})
    assert r.status_code == 403


def test_farmer_cannot_access_another_farmers_crop():
    crop_id = _seed_crop("Sugarcane")
    h_a = _auth("farmer_a@test.com")
    h_b = _auth("farmer_b@test.com")
    add = client.post("/api/farmer/crops", headers=h_a, json={"crop_id": crop_id, "quantity": 10, "unit": "ton"})
    entry_id = add.json()["id"]
    r = client.put(f"/api/farmer/crops/{entry_id}", headers=h_b, json={"quantity": 99})
    assert r.status_code == 404


def test_missing_required_field_crop_id():
    h = _auth("crop_missing@test.com")
    r = client.post("/api/farmer/crops", headers=h, json={"quantity": 10, "unit": "kg"})
    assert r.status_code == 422


def test_missing_required_field_quantity():
    crop_id = _seed_crop("Groundnut")
    h = _auth("crop_noqty@test.com")
    r = client.post("/api/farmer/crops", headers=h, json={"crop_id": crop_id, "unit": "kg"})
    assert r.status_code == 422
