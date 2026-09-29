"""
Development seed data for AgriMarket Intelligence.

WARNING: These are SAMPLE values for development only.
         Do NOT use these as real market prices.

Run:
    python -m app.database.seed
or from the backend directory:
    .venv/Scripts/python.exe -m app.database.seed
"""

from datetime import date, timedelta

from sqlalchemy.exc import IntegrityError

from app.database.session import SessionLocal
from app.models.crop import Crop, CropUnit
from app.models.market import Market, MarketType
from app.models.market_price import MarketPrice


SEED_CROPS = [
    {"name": "Tomato",  "category": "Vegetable", "unit": CropUnit.KG,      "description": "Fresh tomatoes"},
    {"name": "Onion",   "category": "Vegetable", "unit": CropUnit.QUINTAL, "description": "Dry onion"},
    {"name": "Potato",  "category": "Vegetable", "unit": CropUnit.QUINTAL, "description": "Potato (all varieties)"},
    {"name": "Rice",    "category": "Cereal",    "unit": CropUnit.QUINTAL, "description": "Paddy / milled rice"},
    {"name": "Banana",  "category": "Fruit",     "unit": CropUnit.KG,      "description": "Banana (all varieties)"},
]

# Sample Tamil Nadu markets (development data only)
SEED_MARKETS = [
    {
        "name": "Coimbatore APMC Market",
        "market_code": "TN-CBE-001",
        "location": "Coimbatore",
        "district": "Coimbatore",
        "state": "Tamil Nadu",
        "latitude": 11.0168,
        "longitude": 76.9558,
        "market_type": MarketType.APMC,
    },
    {
        "name": "Erode Wholesale Market",
        "market_code": "TN-ERO-001",
        "location": "Erode",
        "district": "Erode",
        "state": "Tamil Nadu",
        "latitude": 11.3410,
        "longitude": 77.7172,
        "market_type": MarketType.WHOLESALE,
    },
    {
        "name": "Tiruppur Agricultural Market",
        "market_code": "TN-TPR-001",
        "location": "Tiruppur",
        "district": "Tiruppur",
        "state": "Tamil Nadu",
        "latitude": 11.1085,
        "longitude": 77.3411,
        "market_type": MarketType.APMC,
    },
]


def seed(db=None) -> None:
    """
    Insert development seed data.
    Safe to call multiple times — uses IntegrityError to skip existing records.
    Pass an existing session for testing, or omit to use the app session.
    """
    close_after = db is None
    if db is None:
        db = SessionLocal()

    try:
        # ── Crops ──────────────────────────────────────────────────────────────
        crop_map: dict[str, Crop] = {}
        for data in SEED_CROPS:
            try:
                crop = Crop(**data)
                db.add(crop)
                db.flush()
                crop_map[data["name"]] = crop
                print(f"  [seed] Created crop: {data['name']}")
            except IntegrityError:
                db.rollback()
                existing = db.query(Crop).filter_by(name=data["name"]).first()
                if existing:
                    crop_map[data["name"]] = existing
                print(f"  [seed] Crop already exists: {data['name']}")

        # ── Markets ────────────────────────────────────────────────────────────
        market_map: dict[str, Market] = {}
        for data in SEED_MARKETS:
            try:
                market = Market(**data)
                db.add(market)
                db.flush()
                market_map[data["market_code"]] = market
                print(f"  [seed] Created market: {data['name']}")
            except IntegrityError:
                db.rollback()
                existing = db.query(Market).filter_by(market_code=data["market_code"]).first()
                if existing:
                    market_map[data["market_code"]] = existing
                print(f"  [seed] Market already exists: {data['name']}")

        # ── Sample prices (development only, not real government data) ─────────
        today = date.today()
        sample_prices = [
            # (market_code, crop_name, min, modal, max, date_offset)
            ("TN-CBE-001", "Tomato",  20.0,  25.0,  30.0, 0),
            ("TN-CBE-001", "Onion",  800.0, 950.0, 1100.0, 0),
            ("TN-ERO-001", "Tomato",  18.0,  23.0,  28.0, 0),
            ("TN-ERO-001", "Onion",  780.0, 920.0, 1080.0, 0),
            ("TN-TPR-001", "Potato", 900.0, 1050.0, 1200.0, 0),
            ("TN-CBE-001", "Tomato",  22.0,  27.0,  32.0, -1),
        ]
        for mcode, cname, mn, modal, mx, doff in sample_prices:
            market = market_map.get(mcode)
            crop = crop_map.get(cname)
            if not market or not crop:
                continue
            price_date = today + timedelta(days=doff)
            # Avoid duplicates
            exists = (
                db.query(MarketPrice)
                .filter_by(market_id=market.id, crop_id=crop.id, price_date=price_date)
                .first()
            )
            if not exists:
                db.add(MarketPrice(
                    market_id=market.id,
                    crop_id=crop.id,
                    price_date=price_date,
                    min_price=mn,
                    modal_price=modal,
                    max_price=mx,
                    source="development_sample",
                ))
                print(f"  [seed] Created price: {cname} @ {mcode} on {price_date}")

        db.commit()
        print("[seed] Done.")

    except Exception:
        db.rollback()
        raise
    finally:
        if close_after:
            db.close()


if __name__ == "__main__":
    print("[seed] Seeding development data...")
    seed()
