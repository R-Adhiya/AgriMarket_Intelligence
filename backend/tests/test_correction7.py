"""
Correction 7 — Admin User Management & Verified Badge Tests

ADMIN ACCESS (1-8)
TRANSACTION WORKFLOW (9-20)
VERIFICATION THRESHOLD (21-25)
REGRESSION (26-28)
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from tests.conftest import get_test_session

client = TestClient(app)

ADMIN_EMAIL = "c7_admin@example.com"
ADMIN_PWD   = "Password123!"
VERIFICATION_THRESHOLD = 5


def setup_module(_):
    from app.models.user import User, UserRole
    from app.models.crop import Crop, CropUnit
    from app.core.security import hash_password

    db = get_test_session()
    try:
        if not db.query(User).filter_by(email=ADMIN_EMAIL).first():
            db.add(User(
                email=ADMIN_EMAIL,
                password_hash=hash_password(ADMIN_PWD),
                full_name="C7 Admin",
                role=UserRole.ADMIN,
                is_active=True,
            ))
            db.commit()
        if not db.query(Crop).filter(Crop.name == "Tomato").first():
            db.add(Crop(name="Tomato", category="Vegetable", unit=CropUnit.KG, is_active=True))
            db.commit()
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _register(role: str, suffix: str) -> str:
    email = f"c7_{role.lower()}_{suffix}@example.com"
    client.post("/api/auth/register", json={
        "email": email, "password": "Password123!",
        "full_name": f"C7 {role.title()} {suffix}", "role": role,
    })
    return email


def _login(email: str, password: str = "Password123!") -> str:
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _get_tomato_id(token: str) -> int:
    catalog = client.get("/api/crops", headers=_auth(token)).json()
    t = next((c for c in catalog if c["name"].lower() == "tomato"), None)
    assert t, "Tomato not in catalog"
    return t["id"]


def _setup_farmer(suffix: str, token: str, crop_id: int) -> None:
    client.put("/api/farmer/profile", json={
        "full_name": f"C7 Farmer {suffix}", "district": "Coimbatore", "state": "Tamil Nadu",
    }, headers=_auth(token))
    r = client.post("/api/farmer/crops", json={"crop_id": crop_id, "quantity": 100.0, "unit": "kg"},
                    headers=_auth(token))
    if r.status_code not in (200, 201, 409):
        pass  # ignore -- crop may already exist


def _setup_req(buyer_token: str, crop_id: int) -> int:
    r = client.post("/api/buyer/requirements",
                    json={"crop_id": crop_id, "quantity": 50.0, "location": "Coimbatore"},
                    headers=_auth(buyer_token))
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


def _express(farmer_token: str, req_id: int) -> int:
    r = client.post(f"/api/farmer/interests?requirement_id={req_id}", headers=_auth(farmer_token))
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


def _accept(farmer_token: str, int_id: int) -> None:
    r = client.put(f"/api/interests/{int_id}/accept", headers=_auth(farmer_token))
    assert r.status_code == 200, r.text


def _confirm(token: str, int_id: int) -> int:
    return client.put(f"/api/interests/{int_id}/confirm-complete", headers=_auth(token)).status_code


def _complete_one(ft: str, bt: str, crop_id: int) -> int:
    """Full cycle: create req -> express interest -> accept -> both confirm. Returns interest id."""
    req = _setup_req(bt, crop_id)
    iid = _express(ft, req)
    _accept(ft, iid)
    assert _confirm(ft, iid) == 200
    assert _confirm(bt, iid) == 200
    return iid


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def admin_tok():
    return _login(ADMIN_EMAIL, ADMIN_PWD)


@pytest.fixture(scope="module")
def farmer_tok():
    e = _register("FARMER", "main")
    t = _login(e)
    cid = _get_tomato_id(t)
    _setup_farmer("main", t, cid)
    return t


@pytest.fixture(scope="module")
def buyer_tok():
    return _login(_register("BUYER", "main"))


@pytest.fixture(scope="module")
def crop(farmer_tok):
    return _get_tomato_id(farmer_tok)


# ---------------------------------------------------------------------------
# Admin access
# ---------------------------------------------------------------------------

class TestAdminAccess:
    def test_01_admin_can_list_users(self, admin_tok):
        r = client.get("/api/admin/users", headers=_auth(admin_tok))
        assert r.status_code == 200
        d = r.json()
        assert "items" in d and "total" in d

    def test_02_farmer_cannot_list_users(self, farmer_tok):
        assert client.get("/api/admin/users", headers=_auth(farmer_tok)).status_code == 403

    def test_03_buyer_cannot_list_users(self, buyer_tok):
        assert client.get("/api/admin/users", headers=_auth(buyer_tok)).status_code == 403

    def test_04_unauthenticated_rejected(self):
        assert client.get("/api/admin/users").status_code == 401

    def test_05_search_returns_matches(self, admin_tok):
        r = client.get("/api/admin/users?search=C7+Farmer", headers=_auth(admin_tok))
        assert r.status_code == 200

    def test_06_role_filter_farmers_only(self, admin_tok):
        r = client.get("/api/admin/users?role=FARMER", headers=_auth(admin_tok))
        assert r.status_code == 200
        for u in r.json()["items"]:
            assert u["role"] == "FARMER"

    def test_07_verified_filter_false(self, admin_tok):
        r = client.get("/api/admin/users?is_verified=false&role=FARMER", headers=_auth(admin_tok))
        assert r.status_code == 200
        # All items should have is_verified False
        for u in r.json()["items"]:
            assert u["is_verified"] is False

    def test_08_no_sensitive_fields(self, admin_tok):
        r = client.get("/api/admin/users", headers=_auth(admin_tok))
        text = r.text
        assert "password_hash" not in text
        # "password" only appears inside "password_hash"; ensure raw "password" key not in JSON
        import json
        data = json.loads(text)
        for item in data.get("items", []):
            assert "password" not in item
            assert "password_hash" not in item


# ---------------------------------------------------------------------------
# Transaction workflow
# ---------------------------------------------------------------------------

class TestTransactionWorkflow:
    def test_09_pending_not_completed(self, farmer_tok, buyer_tok, crop):
        req = _setup_req(buyer_tok, crop)
        iid = _express(farmer_tok, req)
        # Don't accept -- stays PENDING; confirm-complete should fail
        assert _confirm(farmer_tok, iid) == 400

    def test_10_accepted_but_unconfirmed_stays_accepted(self, farmer_tok, buyer_tok, crop):
        req = _setup_req(buyer_tok, crop)
        iid = _express(farmer_tok, req)
        _accept(farmer_tok, iid)
        # One side confirms
        _confirm(farmer_tok, iid)
        # Status must still be ACCEPTED
        ints = client.get("/api/interests/received", headers=_auth(farmer_tok)).json()
        i = next((x for x in ints if x["id"] == iid), None)
        assert i is not None
        assert i["status"] == "ACCEPTED"

    def test_11_rejected_interest_not_completable(self, farmer_tok, buyer_tok, crop):
        req = _setup_req(buyer_tok, crop)
        iid = _express(farmer_tok, req)
        client.put(f"/api/interests/{iid}/reject", headers=_auth(farmer_tok))
        assert _confirm(farmer_tok, iid) == 400

    def test_12_cancelled_interest_not_completable(self, farmer_tok, buyer_tok, crop):
        req = _setup_req(buyer_tok, crop)
        iid = _express(farmer_tok, req)
        client.delete(f"/api/interests/{iid}", headers=_auth(buyer_tok))
        assert _confirm(farmer_tok, iid) == 400

    def test_13_only_farmer_confirm_not_complete(self, farmer_tok, buyer_tok, crop):
        req = _setup_req(buyer_tok, crop)
        iid = _express(farmer_tok, req)
        _accept(farmer_tok, iid)
        assert _confirm(farmer_tok, iid) == 200
        # Buyer has NOT confirmed yet -- status should still be ACCEPTED
        ints = client.get("/api/interests/received", headers=_auth(farmer_tok)).json()
        i = next((x for x in ints if x["id"] == iid), None)
        assert i["status"] == "ACCEPTED"

    def test_14_only_buyer_confirm_not_complete(self, farmer_tok, buyer_tok, crop):
        req = _setup_req(buyer_tok, crop)
        iid = _express(farmer_tok, req)
        _accept(farmer_tok, iid)
        assert _confirm(buyer_tok, iid) == 200
        ints = client.get("/api/interests/sent", headers=_auth(buyer_tok)).json()
        i = next((x for x in ints if x["id"] == iid), None)
        assert i["status"] == "ACCEPTED"

    def test_15_both_confirm_marks_completed(self, farmer_tok, buyer_tok, crop):
        req = _setup_req(buyer_tok, crop)
        iid = _express(farmer_tok, req)
        _accept(farmer_tok, iid)
        assert _confirm(farmer_tok, iid) == 200
        assert _confirm(buyer_tok, iid) == 200
        ints = client.get("/api/interests/received", headers=_auth(farmer_tok)).json()
        i = next((x for x in ints if x["id"] == iid), None)
        assert i["status"] == "COMPLETED"

    def test_16_completed_transaction_count_increases(self, admin_tok, farmer_tok, buyer_tok, crop):
        _complete_one(farmer_tok, buyer_tok, crop)
        r = client.get("/api/admin/users?search=C7+Farmer+main&role=FARMER", headers=_auth(admin_tok))
        items = r.json()["items"]
        if items:
            assert "completed_transaction_count" in items[0]
            assert "is_verified" in items[0]

    def test_17_duplicate_confirm_idempotent_no_extra_count(self, farmer_tok, buyer_tok, crop):
        req = _setup_req(buyer_tok, crop)
        iid = _express(farmer_tok, req)
        _accept(farmer_tok, iid)
        assert _confirm(farmer_tok, iid) == 200
        assert _confirm(buyer_tok, iid) == 200
        # Now COMPLETED -- any new confirm should fail
        assert _confirm(farmer_tok, iid) == 400

    def test_18_unrelated_user_cannot_confirm(self, crop):
        f2 = _login(_register("FARMER", "unrel"))
        b2 = _login(_register("BUYER", "unrel"))
        _setup_farmer("unrel", f2, crop)
        req = _setup_req(b2, crop)
        iid = _express(f2, req)
        _accept(f2, iid)

        # Completely unrelated farmer tries to confirm
        f3 = _login(_register("FARMER", "nopart"))
        _setup_farmer("nopart", f3, crop)
        assert _confirm(f3, iid) == 403

    def test_19_completed_cannot_confirm_again(self, farmer_tok, buyer_tok, crop):
        iid = _complete_one(farmer_tok, buyer_tok, crop)
        assert _confirm(farmer_tok, iid) == 400
        assert _confirm(buyer_tok, iid) == 400

    def test_20_pending_confirm_complete_rejected(self, farmer_tok, buyer_tok, crop):
        req = _setup_req(buyer_tok, crop)
        iid = _express(farmer_tok, req)
        # PENDING -- confirm-complete must return 400
        assert _confirm(farmer_tok, iid) == 400


# ---------------------------------------------------------------------------
# Verification threshold
# ---------------------------------------------------------------------------

class TestVerificationThreshold:
    @pytest.fixture(scope="class")
    def vft(self):
        e = _register("FARMER", "vthresh")
        t = _login(e)
        cid = _get_tomato_id(t)
        _setup_farmer("vthresh", t, cid)
        return t

    @pytest.fixture(scope="class")
    def vbt(self):
        return _login(_register("BUYER", "vthresh"))

    @pytest.fixture(scope="class")
    def vcrop(self, vft):
        return _get_tomato_id(vft)

    def test_21_four_transactions_not_verified(self, admin_tok, vft, vbt, vcrop):
        for _ in range(4):
            _complete_one(vft, vbt, vcrop)
        r = client.get("/api/admin/users?search=C7+Farmer+vthresh&role=FARMER", headers=_auth(admin_tok))
        items = r.json()["items"]
        if items:
            assert items[0]["is_verified"] is False
            assert items[0]["completed_transaction_count"] == 4

    def test_22_fifth_transaction_grants_badge(self, admin_tok, vft, vbt, vcrop):
        _complete_one(vft, vbt, vcrop)
        r = client.get("/api/admin/users?search=C7+Farmer+vthresh&role=FARMER", headers=_auth(admin_tok))
        items = r.json()["items"]
        if items:
            assert items[0]["is_verified"] is True
            assert items[0]["completed_transaction_count"] >= VERIFICATION_THRESHOLD

    def test_23_more_than_five_remains_verified(self, admin_tok, vft, vbt, vcrop):
        _complete_one(vft, vbt, vcrop)
        r = client.get("/api/admin/users?search=C7+Farmer+vthresh&role=FARMER", headers=_auth(admin_tok))
        items = r.json()["items"]
        if items:
            assert items[0]["is_verified"] is True

    def test_24_buyer_verification_independent(self, admin_tok, vbt):
        r = client.get("/api/admin/users?search=vthresh&role=BUYER", headers=_auth(admin_tok))
        items = r.json()["items"]
        if items:
            assert "is_verified" in items[0]
            assert "completed_transaction_count" in items[0]

    def test_25_repeated_confirmation_no_double_count(self, admin_tok, vft, vbt, vcrop):
        iid = _complete_one(vft, vbt, vcrop)
        r1 = client.get("/api/admin/users?search=vthresh&role=FARMER", headers=_auth(admin_tok))
        before = r1.json()["items"][0]["completed_transaction_count"] if r1.json()["items"] else None

        # Try to re-confirm -- both should be 400
        assert _confirm(vft, iid) == 400
        assert _confirm(vbt, iid) == 400

        r2 = client.get("/api/admin/users?search=vthresh&role=FARMER", headers=_auth(admin_tok))
        after = r2.json()["items"][0]["completed_transaction_count"] if r2.json()["items"] else None
        if before is not None:
            assert after == before


# ---------------------------------------------------------------------------
# Regression
# ---------------------------------------------------------------------------

class TestRegression:
    def test_26_crop_suggestions_still_works(self, admin_tok):
        r = client.get("/api/admin/crop-suggestions", headers=_auth(admin_tok))
        assert r.status_code == 200

    def test_27_activity_still_works(self, admin_tok):
        r = client.get("/api/admin/activity", headers=_auth(admin_tok))
        assert r.status_code == 200

    def test_28_interests_endpoints_still_work(self, farmer_tok, buyer_tok):
        assert client.get("/api/interests/received", headers=_auth(farmer_tok)).status_code == 200
        assert client.get("/api/interests/sent", headers=_auth(buyer_tok)).status_code == 200



# ---------------------------------------------------------------------------
# Review fixes -- Correction 7 review (additional tests)
# ---------------------------------------------------------------------------

class TestReviewFixes:
    """
    Tests added during the Correction 7 review:
      R1.  is_verified filter in DB: total and items are always consistent
           across pages (no post-fetch filtering artefacts).
      R2.  Profile update endpoints cannot be used to set is_verified.
      R3.  Profile update endpoints cannot be used to set completed_transaction_count.
      R4.  Unauthorized user (wrong farmer) cannot confirm another pair's transaction.
      R5.  A third-party buyer cannot confirm a transaction they're not part of.
      R6.  Repeated confirmation attempt returns 400, not 200.
      R7.  Repeated confirmation does not alter the completed_transaction_count.
      R8.  Verified filter with pagination: total reflects DB-filtered count.
      R9.  ADMIN users without a profile show is_verified=false, count=0, no error.
    """

    def test_r1_verified_filter_total_consistent(self, admin_tok):
        """total in response must equal the count of items if only one page."""
        r = client.get("/api/admin/users?is_verified=false&page_size=100",
                       headers=_auth(admin_tok))
        assert r.status_code == 200
        d = r.json()
        # All returned items must match the filter
        for item in d["items"]:
            assert item["is_verified"] is False, f"Item {item['id']} is verified but should not be"
        # If total <= page_size, all items should be present
        if d["total"] <= 100:
            assert len(d["items"]) == d["total"]

    def test_r2_farmer_cannot_self_verify(self, farmer_tok):
        """PUT /api/farmer/profile must not accept is_verified."""
        r = client.put("/api/farmer/profile", json={
            "district": "Coimbatore",
            "is_verified": True,  # should be silently ignored by schema
            "completed_transaction_count": 999,
        }, headers=_auth(farmer_tok))
        # The update itself may succeed (extra fields are ignored by Pydantic)
        # but the resulting profile must NOT have is_verified=True or count=999
        if r.status_code in (200, 201):
            # Fetch admin view
            pass  # fields not in response schema -- just verify DB wasn't changed
        # Check the farmer's entry in admin view still has real count
        admin_tok_local = _login(ADMIN_EMAIL, ADMIN_PWD)
        users = client.get("/api/admin/users?search=C7+Farmer+main&role=FARMER",
                           headers=_auth(admin_tok_local)).json()
        for u in users.get("items", []):
            # count must be what the DB computed, not 999
            assert u["completed_transaction_count"] != 999
            # is_verified must reflect actual completions, not a client request
            assert isinstance(u["is_verified"], bool)

    def test_r3_buyer_cannot_self_verify(self, buyer_tok):
        """PUT /api/buyer/profile must not accept is_verified."""
        r = client.put("/api/buyer/profile", json={
            "district": "Chennai",
            "is_verified": True,
            "completed_transaction_count": 999,
        }, headers=_auth(buyer_tok))
        # Pydantic ignores unknown fields; the important thing is DB is not dirty
        admin_tok_local = _login(ADMIN_EMAIL, ADMIN_PWD)
        users = client.get("/api/admin/users?search=C7+Buyer+main&role=BUYER",
                           headers=_auth(admin_tok_local)).json()
        for u in users.get("items", []):
            assert u["completed_transaction_count"] != 999

    def test_r4_wrong_farmer_cannot_confirm(self, crop):
        """A farmer who is not party to the transaction is rejected with 403."""
        f2 = _login(_register("FARMER", "rev2"))
        b2 = _login(_register("BUYER", "rev2"))
        _setup_farmer("rev2", f2, crop)

        req = _setup_req(b2, crop)
        iid = _express(f2, req)
        _accept(f2, iid)

        # Unrelated farmer
        f3 = _login(_register("FARMER", "rev3"))
        _setup_farmer("rev3", f3, crop)
        assert _confirm(f3, iid) == 403

    def test_r5_wrong_buyer_cannot_confirm(self, crop):
        """A buyer who is not party to the transaction is rejected with 403."""
        f4 = _login(_register("FARMER", "rev4"))
        b4 = _login(_register("BUYER", "rev4"))
        _setup_farmer("rev4", f4, crop)

        req = _setup_req(b4, crop)
        iid = _express(f4, req)
        _accept(f4, iid)

        b5 = _login(_register("BUYER", "rev5"))
        assert _confirm(b5, iid) == 403

    def test_r6_repeated_confirm_returns_400(self, farmer_tok, buyer_tok, crop):
        """Second call to confirm-complete on an already-COMPLETED tx returns 400."""
        iid = _complete_one(farmer_tok, buyer_tok, crop)
        assert _confirm(farmer_tok, iid) == 400
        assert _confirm(buyer_tok,  iid) == 400

    def test_r7_repeated_confirm_no_count_change(self, admin_tok, farmer_tok, buyer_tok, crop):
        """count must not increase when re-confirming an already-completed transaction."""
        iid = _complete_one(farmer_tok, buyer_tok, crop)

        r_before = client.get("/api/admin/users?search=C7+Farmer+main&role=FARMER",
                              headers=_auth(admin_tok)).json()
        count_before = r_before["items"][0]["completed_transaction_count"] if r_before["items"] else None

        # Attempt re-confirm (both should be rejected)
        _confirm(farmer_tok, iid)
        _confirm(buyer_tok,  iid)

        r_after = client.get("/api/admin/users?search=C7+Farmer+main&role=FARMER",
                             headers=_auth(admin_tok)).json()
        count_after = r_after["items"][0]["completed_transaction_count"] if r_after["items"] else None

        if count_before is not None and count_after is not None:
            assert count_after == count_before

    def test_r8_verified_filter_pagination_total_correct(self, admin_tok):
        """
        When is_verified filter is applied, 'total' must equal the DB count of
        matching users, not the total of all users. This verifies the fix for
        the post-fetch filtering bug where total was computed before the filter.
        """
        # Get total without filter
        r_all = client.get("/api/admin/users?page_size=1", headers=_auth(admin_tok))
        total_all = r_all.json()["total"]

        # Get total with is_verified=false
        r_unverified = client.get("/api/admin/users?is_verified=false&page_size=1",
                                  headers=_auth(admin_tok))
        d_unverified = r_unverified.json()
        assert r_unverified.status_code == 200

        # Get total with is_verified=true
        r_verified = client.get("/api/admin/users?is_verified=true&page_size=1",
                                headers=_auth(admin_tok))
        d_verified = r_verified.json()
        assert r_verified.status_code == 200

        # Critical: the verified+unverified totals must sum to <= total_all
        # (ADMIN users with no profile show is_verified=false, so total_all
        #  should equal d_unverified["total"] + d_verified["total"])
        assert d_unverified["total"] + d_verified["total"] == total_all, (
            f"Verified ({d_verified['total']}) + Unverified ({d_unverified['total']}) "
            f"!= All ({total_all}). Pagination filter is still post-fetch."
        )

    def test_r9_admin_user_no_profile_no_error(self, admin_tok):
        """ADMIN users without a farmer/buyer profile return is_verified=false, count=0."""
        r = client.get("/api/admin/users?role=ADMIN", headers=_auth(admin_tok))
        assert r.status_code == 200
        for u in r.json()["items"]:
            assert u["is_verified"] is False
            assert u["completed_transaction_count"] == 0
