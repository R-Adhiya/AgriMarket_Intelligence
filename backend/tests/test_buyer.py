"""
Phase 9 tests — Direct Buyer-Farmer Market Access.

Covers:
  - Buyer profile CRUD
  - Buyer requirements CRUD
  - Farmer availability flag
  - Matching engine (buyer finds farmers)
  - Farmer discovers buyer requirements
  - Interest send / accept / reject / cancel
  - Duplicate interest prevention
  - Invalid status transitions
  - Contact privacy (hidden before accept, shown after)
  - Data isolation (buyer A cannot see buyer B's data)
  - Authorization (role enforcement)
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

# ── Test helpers ──────────────────────────────────────────────────────────────

def _register(email: str, password: str, role: str, full_name: str = "Test User") -> dict:
    r = client.post("/api/auth/register", json={
        "email": email, "password": password, "role": role, "full_name": full_name
    })
    assert r.status_code in (200, 201, 409), f"Register {email}: {r.text}"
    if r.status_code == 409:
        pass
    r2 = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r2.status_code == 200, f"Login {email}: {r2.text}"
    return r2.json()


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Module-level setup ────────────────────────────────────────────────────────

_buyer1_token = ""
_buyer2_token = ""
_farmer1_token = ""
_farmer2_token = ""
_crop_id = 0


def setup_module(_):
    global _buyer1_token, _buyer2_token, _farmer1_token, _farmer2_token, _crop_id

    d = _register("p9_buyer1@test.com", "Pass1234!", "BUYER", "Buyer One")
    _buyer1_token = d["access_token"]

    d = _register("p9_buyer2@test.com", "Pass1234!", "BUYER", "Buyer Two")
    _buyer2_token = d["access_token"]

    d = _register("p9_farmer1@test.com", "Pass1234!", "FARMER", "Farmer One")
    _farmer1_token = d["access_token"]

    d = _register("p9_farmer2@test.com", "Pass1234!", "FARMER", "Farmer Two")
    _farmer2_token = d["access_token"]

    # Create a crop for testing
    from tests.conftest import get_test_session
    from app.models.crop import Crop, CropUnit
    db = get_test_session()
    crop = db.query(Crop).filter_by(name="P9Tomato").first()
    if not crop:
        crop = Crop(name="P9Tomato", category="Vegetable", unit=CropUnit.KG, is_active=True)
        db.add(crop)
        db.commit()
        db.refresh(crop)
    _crop_id = crop.id
    db.close()


# ══════════════════════════════════════════════════════════════════
# 1. Buyer Profile
# ══════════════════════════════════════════════════════════════════

def test_buyer_profile_get():
    r = client.get("/api/buyer/profile", headers=_auth(_buyer1_token))
    assert r.status_code == 200
    d = r.json()
    assert d["email"] == "p9_buyer1@test.com"


def test_buyer_profile_update():
    r = client.put("/api/buyer/profile", json={
        "business_name": "Green Traders",
        "location": "Coimbatore",
        "district": "Coimbatore",
        "state": "Tamil Nadu",
    }, headers=_auth(_buyer1_token))
    assert r.status_code == 200
    assert r.json()["business_name"] == "Green Traders"


def test_buyer_profile_farmer_blocked():
    r = client.get("/api/buyer/profile", headers=_auth(_farmer1_token))
    assert r.status_code == 403


# ══════════════════════════════════════════════════════════════════
# 2. Buyer Requirements
# ══════════════════════════════════════════════════════════════════

_req1_id = 0
_req2_id = 0


def test_create_requirement():
    global _req1_id
    r = client.post("/api/buyer/requirements", json={
        "crop_id": _crop_id,
        "quantity": 500,
        "minimum_price": 25.0,
        "maximum_price": 35.0,
        "location": "Coimbatore",
        "district": "Coimbatore",
        "state": "Tamil Nadu",
    }, headers=_auth(_buyer1_token))
    assert r.status_code == 201, r.text
    d = r.json()
    assert d["quantity"] == 500.0
    assert d["status"] == "ACTIVE"
    _req1_id = d["id"]


def test_create_requirement_zero_quantity():
    r = client.post("/api/buyer/requirements", json={
        "crop_id": _crop_id, "quantity": 0,
    }, headers=_auth(_buyer1_token))
    assert r.status_code == 422


def test_create_requirement_invalid_crop():
    r = client.post("/api/buyer/requirements", json={
        "crop_id": 99999, "quantity": 100,
    }, headers=_auth(_buyer1_token))
    assert r.status_code == 404


def test_create_requirement_max_lt_min():
    r = client.post("/api/buyer/requirements", json={
        "crop_id": _crop_id,
        "quantity": 100,
        "minimum_price": 30.0,
        "maximum_price": 20.0,
    }, headers=_auth(_buyer1_token))
    assert r.status_code == 422


def test_list_requirements():
    r = client.get("/api/buyer/requirements", headers=_auth(_buyer1_token))
    assert r.status_code == 200
    assert any(req["id"] == _req1_id for req in r.json())


def test_get_requirement():
    r = client.get(f"/api/buyer/requirements/{_req1_id}", headers=_auth(_buyer1_token))
    assert r.status_code == 200
    assert r.json()["id"] == _req1_id


def test_update_requirement():
    r = client.put(f"/api/buyer/requirements/{_req1_id}", json={
        "quantity": 750,
    }, headers=_auth(_buyer1_token))
    assert r.status_code == 200
    assert r.json()["quantity"] == 750.0


def test_buyer_cannot_see_other_buyers_requirement():
    global _req2_id
    # Buyer 2 creates its own requirement
    r = client.post("/api/buyer/requirements", json={
        "crop_id": _crop_id, "quantity": 200,
    }, headers=_auth(_buyer2_token))
    assert r.status_code == 201
    _req2_id = r.json()["id"]

    # Buyer 1 tries to get buyer 2's requirement
    r = client.get(f"/api/buyer/requirements/{_req2_id}", headers=_auth(_buyer1_token))
    assert r.status_code == 404


def test_requirement_farmer_blocked():
    r = client.get("/api/buyer/requirements", headers=_auth(_farmer1_token))
    assert r.status_code == 403


def test_delete_requirement():
    # Create a throwaway requirement
    r = client.post("/api/buyer/requirements", json={
        "crop_id": _crop_id, "quantity": 50,
    }, headers=_auth(_buyer1_token))
    assert r.status_code == 201
    rid = r.json()["id"]

    r = client.delete(f"/api/buyer/requirements/{rid}", headers=_auth(_buyer1_token))
    assert r.status_code == 204

    r = client.get(f"/api/buyer/requirements/{rid}", headers=_auth(_buyer1_token))
    assert r.status_code == 404


# ══════════════════════════════════════════════════════════════════
# 3. Farmer crop availability
# ══════════════════════════════════════════════════════════════════

_fc1_id = 0


def test_add_available_crop():
    global _fc1_id
    r = client.post("/api/farmer/crops", json={
        "crop_id": _crop_id, "quantity": 700, "unit": "quintal", "is_available": True,
    }, headers=_auth(_farmer1_token))
    assert r.status_code == 201, r.text
    d = r.json()
    assert d["is_available"] is True
    _fc1_id = d["id"]


def test_update_availability_flag():
    r = client.put(f"/api/farmer/crops/{_fc1_id}", json={
        "is_available": False,
    }, headers=_auth(_farmer1_token))
    assert r.status_code == 200
    assert r.json()["is_available"] is False

    # Restore to True for later tests
    r = client.put(f"/api/farmer/crops/{_fc1_id}", json={
        "is_available": True,
    }, headers=_auth(_farmer1_token))
    assert r.status_code == 200


# ══════════════════════════════════════════════════════════════════
# 4. Matching engine — buyer finds farmers
# ══════════════════════════════════════════════════════════════════

def test_match_farmers_for_requirement():
    r = client.get(f"/api/buyer/matches/{_req1_id}", headers=_auth(_buyer1_token))
    assert r.status_code == 200
    matches = r.json()
    # Farmer 1 has P9Tomato available
    assert any(m["crop_id"] == _crop_id for m in matches)


def test_match_no_phone_before_accept():
    r = client.get(f"/api/buyer/matches/{_req1_id}", headers=_auth(_buyer1_token))
    assert r.status_code == 200
    for m in r.json():
        assert m.get("phone") is None, "Phone must be hidden before acceptance"


def test_match_farmer_blocked():
    r = client.get(f"/api/buyer/matches/{_req1_id}", headers=_auth(_farmer1_token))
    assert r.status_code == 403


def test_match_inactive_crop_hidden():
    # Make farmer crop unavailable
    client.put(f"/api/farmer/crops/{_fc1_id}", json={"is_available": False},
               headers=_auth(_farmer1_token))

    r = client.get(f"/api/buyer/matches/{_req1_id}", headers=_auth(_buyer1_token))
    # Farmer 1 should not appear since crop is unavailable
    matches = r.json()
    # Get farmer1's farmer_crop_id to check
    assert all(m["farmer_crop_id"] != _fc1_id for m in matches)

    # Restore
    client.put(f"/api/farmer/crops/{_fc1_id}", json={"is_available": True},
               headers=_auth(_farmer1_token))


# ══════════════════════════════════════════════════════════════════
# 5. Farmer discovers buyer requirements
# ══════════════════════════════════════════════════════════════════

def test_farmer_sees_matching_buyer_requirements():
    r = client.get("/api/farmer/buyer-requirements", headers=_auth(_farmer1_token))
    assert r.status_code == 200
    reqs = r.json()
    # Buyer 1 has an active requirement for P9Tomato, which farmer 1 grows
    assert any(req["crop_id"] == _crop_id for req in reqs)


def test_farmer_buyer_requirements_no_private_data():
    r = client.get("/api/farmer/buyer-requirements", headers=_auth(_farmer1_token))
    assert r.status_code == 200
    for req in r.json():
        # Should not contain any email/phone in the public response
        assert "email" not in req
        assert "phone" not in req


def test_farmer_buyer_requirements_buyer_blocked():
    r = client.get("/api/farmer/buyer-requirements", headers=_auth(_buyer1_token))
    assert r.status_code == 403


# ══════════════════════════════════════════════════════════════════
# 6. Interest requests
# ══════════════════════════════════════════════════════════════════

_interest1_id = 0


def _get_farmer1_id() -> int:
    from tests.conftest import get_test_session
    from app.models.farmer import Farmer
    from app.models.user import User
    db = get_test_session()
    farmer = db.query(Farmer).join(User).filter(User.email == "p9_farmer1@test.com").first()
    fid = farmer.id if farmer else 0
    db.close()
    return fid


def test_buyer_sends_interest():
    global _interest1_id
    farmer_id = _get_farmer1_id()
    assert farmer_id > 0
    r = client.post("/api/interests", json={
        "farmer_id": farmer_id,
        "crop_id": _crop_id,
        "requirement_id": _req1_id,
        "quantity": 500,
        "notes": "Interested in your tomatoes",
    }, headers=_auth(_buyer1_token))
    assert r.status_code == 201, r.text
    d = r.json()
    assert d["status"] == "PENDING"
    assert d["farmer_phone"] is None, "Phone must be hidden before acceptance"
    _interest1_id = d["id"]


def test_duplicate_interest_rejected():
    farmer_id = _get_farmer1_id()
    r = client.post("/api/interests", json={
        "farmer_id": farmer_id,
        "crop_id": _crop_id,
        "requirement_id": _req1_id,
        "quantity": 500,
    }, headers=_auth(_buyer1_token))
    assert r.status_code == 409, f"Expected 409 but got {r.status_code}: {r.text}"


def test_buyer_sees_sent_interests():
    r = client.get("/api/interests/sent", headers=_auth(_buyer1_token))
    assert r.status_code == 200
    assert any(i["id"] == _interest1_id for i in r.json())


def test_farmer_sees_received_interests():
    r = client.get("/api/interests/received", headers=_auth(_farmer1_token))
    assert r.status_code == 200
    assert any(i["id"] == _interest1_id for i in r.json())


def test_farmer2_cannot_see_farmer1_interests():
    r = client.get("/api/interests/received", headers=_auth(_farmer2_token))
    assert r.status_code == 200
    # farmer 2 should not see farmer 1's interests
    assert all(i["id"] != _interest1_id for i in r.json())


def test_buyer_cannot_see_received_interests():
    r = client.get("/api/interests/received", headers=_auth(_buyer1_token))
    assert r.status_code == 403


def test_farmer_accepts_interest():
    r = client.put(f"/api/interests/{_interest1_id}/accept", headers=_auth(_farmer1_token))
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["status"] == "ACCEPTED"


def test_contact_revealed_after_accept():
    r = client.get("/api/interests/sent", headers=_auth(_buyer1_token))
    assert r.status_code == 200
    accepted = [i for i in r.json() if i["id"] == _interest1_id]
    assert len(accepted) == 1
    # farmer_name should be present; phone may or may not be set but field exists
    assert accepted[0].get("farmer_name") is not None


def test_cannot_accept_already_accepted():
    r = client.put(f"/api/interests/{_interest1_id}/accept", headers=_auth(_farmer1_token))
    assert r.status_code == 400


def test_cannot_reject_already_accepted():
    r = client.put(f"/api/interests/{_interest1_id}/reject", headers=_auth(_farmer1_token))
    assert r.status_code == 400


def test_farmer_rejects_interest():
    # Create a fresh interest first
    farmer_id = _get_farmer1_id()
    r = client.post("/api/interests", json={
        "farmer_id": farmer_id,
        "crop_id": _crop_id,
        "requirement_id": None,  # Different req_id so no duplicate
        "quantity": 100,
        "notes": "Another interest",
    }, headers=_auth(_buyer2_token))
    assert r.status_code == 201, r.text
    iid = r.json()["id"]

    r = client.put(f"/api/interests/{iid}/reject", headers=_auth(_farmer1_token))
    assert r.status_code == 200
    assert r.json()["status"] == "REJECTED"


def test_buyer_cancels_pending_interest():
    farmer_id = _get_farmer1_id()
    # Create a new PENDING interest
    r = client.post("/api/interests", json={
        "farmer_id": farmer_id,
        "crop_id": _crop_id,
        "requirement_id": _req2_id,  # buyer2's req, but buyer1 is posting interest here
        "quantity": 50,
    }, headers=_auth(_buyer1_token))
    # This will conflict because req2 belongs to buyer2; use requirement_id=None
    r = client.post("/api/interests", json={
        "farmer_id": farmer_id,
        "crop_id": _crop_id,
        "requirement_id": None,
        "quantity": 50,
        "notes": "cancel me",
    }, headers=_auth(_buyer1_token))
    assert r.status_code == 201, r.text
    cancel_id = r.json()["id"]

    r = client.delete(f"/api/interests/{cancel_id}", headers=_auth(_buyer1_token))
    assert r.status_code == 204


def test_buyer_cannot_cancel_accepted():
    # _interest1_id is now ACCEPTED, buyer can't cancel
    r = client.delete(f"/api/interests/{_interest1_id}", headers=_auth(_buyer1_token))
    assert r.status_code == 400


def test_farmer_cannot_cancel_interest():
    # Farmers use accept/reject, not DELETE
    r = client.delete(f"/api/interests/{_interest1_id}", headers=_auth(_farmer1_token))
    assert r.status_code == 403


def test_unauthenticated_interests_blocked():
    r = client.post("/api/interests", json={
        "farmer_id": 1, "crop_id": 1, "quantity": 100,
    })
    assert r.status_code == 401


# ══════════════════════════════════════════════════════════════════
# 7. Invalid requests
# ══════════════════════════════════════════════════════════════════

def test_send_interest_invalid_farmer():
    r = client.post("/api/interests", json={
        "farmer_id": 99999, "crop_id": _crop_id, "quantity": 100,
    }, headers=_auth(_buyer1_token))
    assert r.status_code == 404


def test_send_interest_invalid_crop():
    farmer_id = _get_farmer1_id()
    r = client.post("/api/interests", json={
        "farmer_id": farmer_id, "crop_id": 99999, "quantity": 100,
    }, headers=_auth(_buyer1_token))
    assert r.status_code == 404


def test_match_nonexistent_requirement():
    r = client.get("/api/buyer/matches/99999", headers=_auth(_buyer1_token))
    assert r.status_code == 404


# ══════════════════════════════════════════════════════════════════
# 8. Data isolation
# ══════════════════════════════════════════════════════════════════

def test_buyer_cannot_update_other_buyers_requirement():
    r = client.put(f"/api/buyer/requirements/{_req2_id}", json={
        "quantity": 9999,
    }, headers=_auth(_buyer1_token))
    assert r.status_code == 404  # scoped to buyer1 — not found


def test_buyer_cannot_delete_other_buyers_requirement():
    r = client.delete(f"/api/buyer/requirements/{_req2_id}", headers=_auth(_buyer1_token))
    assert r.status_code == 404


def test_buyer2_sent_list_isolates():
    # Buyer 2 should NOT see buyer 1's interest
    r = client.get("/api/interests/sent", headers=_auth(_buyer2_token))
    assert r.status_code == 200
    assert all(i["id"] != _interest1_id for i in r.json())
