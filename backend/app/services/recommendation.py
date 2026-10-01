"""
Recommendation engine — Phase 8.

Deterministic rule-based engine: ranks markets by expected net revenue.

Net revenue = gross_revenue − transport_cost
           = (price_per_unit × quantity_kg) − transport_cost

Price basis:
  "current"   — latest recorded modal price
  "predicted" — Phase 7 ML prediction (1-day horizon by default)

The engine is transparent: every number is traceable to its source.
No LLM, no black-box model, no invented confidence score.

Recommendation method: "rule_based_net_revenue"
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Optional

# Ensure project root is on sys.path so ml/ is importable
_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.crop import Crop
from app.models.farmer import Farmer
from app.models.market import Market
from app.models.market_price import MarketPrice
from app.services.location import (
    LocationError, CoordinateError,
    estimate_transport_cost, haversine_km,
    resolve_farmer_coords, resolve_market_coords,
)

# ── Currency precision ────────────────────────────────────────────────────────

def _d(value: float) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# ── Data structures ───────────────────────────────────────────────────────────

@dataclass
class MarketOption:
    market_id:      int
    market_name:    str
    district:       Optional[str]
    state:          Optional[str]
    price_per_unit: float       # modal price, in native unit (kg or quintal)
    price_unit:     str
    price_date:     str
    price_basis:    str         # "current" or "predicted"
    distance_km:    float
    transport_cost: float
    gross_revenue:  float
    net_revenue:    float
    source:         Optional[str]
    is_recommended: bool = False

    def as_dict(self) -> dict:
        return {
            "market_id":      self.market_id,
            "market_name":    self.market_name,
            "district":       self.district,
            "state":          self.state,
            "price_per_unit": float(self.price_per_unit),
            "price_unit":     self.price_unit,
            "price_date":     self.price_date,
            "price_basis":    self.price_basis,
            "distance_km":    float(self.distance_km),
            "transport_cost": float(self.transport_cost),
            "gross_revenue":  float(self.gross_revenue),
            "net_revenue":    float(self.net_revenue),
            "source":         self.source,
            "is_recommended": self.is_recommended,
        }


@dataclass
class RecommendationResult:
    crop_id:            int
    crop_name:          str
    crop_unit:          str
    quantity_kg:        float
    price_basis:        str
    recommendation_method: str
    confidence:         None       # deterministic engine — always None
    recommended:        Optional[MarketOption]
    comparison:         list[MarketOption]
    excluded_markets:   list[dict]
    explanation:        str
    currency:           str = "INR"


# ── Engine ────────────────────────────────────────────────────────────────────

def run_recommendation(
    farmer:       Farmer,
    crop:         Crop,
    quantity_kg:  float,
    price_basis:  str,          # "current" or "predicted"
    db:           Session,
) -> RecommendationResult:
    """
    Evaluate all active markets and return the one with the highest
    expected net revenue.

    quantity_kg is always in kilograms; internally we convert to the
    crop's native unit (kg or quintal) for price × quantity revenue.
    """
    if quantity_kg <= 0:
        raise ValueError("quantity_kg must be greater than 0.")
    if price_basis not in ("current", "predicted"):
        raise ValueError(f"price_basis must be 'current' or 'predicted', got '{price_basis}'.")

    # Resolve farmer location
    try:
        farmer_coords = resolve_farmer_coords(
            float(farmer.latitude)  if farmer.latitude  is not None else None,
            float(farmer.longitude) if farmer.longitude is not None else None,
            farmer.district,
        )
        f_lat, f_lon = farmer_coords
    except (LocationError, CoordinateError) as exc:
        raise LocationError(str(exc))

    markets = db.query(Market).filter(Market.is_active == True).all()  # noqa: E712

    options: list[MarketOption] = []
    excluded: list[dict] = []

    for mkt in markets:
        # Resolve market coordinates
        try:
            m_lat, m_lon = resolve_market_coords(mkt.latitude, mkt.longitude, mkt.name)
        except (LocationError, CoordinateError):
            excluded.append({"market_id": mkt.id, "market_name": mkt.name,
                             "reason": "No coordinates available"})
            continue

        # Get price
        price_row: Optional[MarketPrice] = None
        price_date_str: str = ""
        price_per_unit: float = 0.0
        source_label: str = ""

        if price_basis == "current":
            price_row = (
                db.query(MarketPrice)
                .filter_by(market_id=mkt.id, crop_id=crop.id)
                .order_by(MarketPrice.price_date.desc())
                .first()
            )
            if not price_row:
                excluded.append({"market_id": mkt.id, "market_name": mkt.name,
                                 "reason": "No current price data"})
                continue
            price_per_unit = float(price_row.modal_price)
            price_date_str = str(price_row.price_date)
            source_label   = price_row.source or "database"

        elif price_basis == "predicted":
            try:
                import pandas as pd
                from app.services.prediction import (
                    predict_price, InsufficientDataError, ModelNotFoundError
                )
            except (ImportError, OSError) as _dll_err:
                raise ValueError(
                    f"Prediction service unavailable: {_dll_err}. "
                    "ML libraries could not be loaded."
                ) from _dll_err
            history_rows = (
                db.query(MarketPrice)
                .filter_by(market_id=mkt.id, crop_id=crop.id)
                .order_by(MarketPrice.price_date.asc())
                .all()
            )
            if len(history_rows) < 8:
                excluded.append({"market_id": mkt.id, "market_name": mkt.name,
                                 "reason": "Insufficient history for prediction"})
                continue
            history_df = pd.DataFrame([
                {"price_date": str(r.price_date), "modal_price": float(r.modal_price)}
                for r in history_rows
            ])
            try:
                pred = predict_price(crop.name, mkt.id, history_df, horizon=1)
                price_per_unit = pred["predictions"][0]["predicted_price"]
                price_date_str = pred["predictions"][0]["date"]
                source_label   = f"predicted/{pred['model_used']}"
            except (InsufficientDataError, ModelNotFoundError) as exc:
                excluded.append({"market_id": mkt.id, "market_name": mkt.name,
                                 "reason": str(exc)})
                continue

        # Revenue calculation
        # Convert kg quantity to crop unit for gross revenue
        if crop.unit.value == "quintal":
            quantity_in_unit = quantity_kg / 100.0
        elif crop.unit.value == "ton":
            quantity_in_unit = quantity_kg / 1000.0
        else:  # kg
            quantity_in_unit = quantity_kg

        gross   = float(_d(price_per_unit) * _d(quantity_in_unit))

        # Transport cost (quantity in quintals for Phase 6 formula)
        qty_quintals = max(quantity_kg / 100.0, 0.01)
        dist = round(haversine_km(f_lat, f_lon, m_lat, m_lon), 2)
        transport = estimate_transport_cost(
            dist, qty_quintals,
            settings.TRANSPORT_BASE_COST,
            settings.TRANSPORT_RATE_PER_KM,
        )
        net = float(_d(gross) - _d(transport))

        options.append(MarketOption(
            market_id=mkt.id,
            market_name=mkt.name,
            district=mkt.district,
            state=mkt.state,
            price_per_unit=round(price_per_unit, 2),
            price_unit=crop.unit.value,
            price_date=price_date_str,
            price_basis=price_basis,
            distance_km=dist,
            transport_cost=round(transport, 2),
            gross_revenue=round(gross, 2),
            net_revenue=round(net, 2),
            source=source_label,
        ))

    if not options:
        return RecommendationResult(
            crop_id=crop.id, crop_name=crop.name, crop_unit=crop.unit.value,
            quantity_kg=quantity_kg, price_basis=price_basis,
            recommendation_method="rule_based_net_revenue",
            confidence=None,
            recommended=None,
            comparison=[],
            excluded_markets=excluded,
            explanation="No eligible markets found. Check that market price data exists.",
        )

    # Sort by net revenue descending
    options.sort(key=lambda o: o.net_revenue, reverse=True)
    best = options[0]
    best.is_recommended = True

    # Build explanation
    price_label_adj = "current" if price_basis == "current" else "predicted"
    explanation = (
        f"{best.market_name} is recommended because its {price_label_adj} "
        f"{crop.name} price of ₹{best.price_per_unit}/{best.price_unit} "
        f"produces the highest expected net revenue of ₹{best.net_revenue:,.2f} "
        f"after subtracting the estimated transport cost of ₹{best.transport_cost:,.2f}."
    )

    # Add note if best-price market ≠ best-net-revenue market
    best_price_mkt = max(options, key=lambda o: o.price_per_unit)
    if best_price_mkt.market_id != best.market_id:
        explanation += (
            f" Although {best_price_mkt.market_name} has a higher price "
            f"(₹{best_price_mkt.price_per_unit}/{best_price_mkt.price_unit}), "
            f"its greater transport cost results in a lower expected net return."
        )

    return RecommendationResult(
        crop_id=crop.id, crop_name=crop.name, crop_unit=crop.unit.value,
        quantity_kg=quantity_kg, price_basis=price_basis,
        recommendation_method="rule_based_net_revenue",
        confidence=None,
        recommended=best,
        comparison=options,
        excluded_markets=excluded,
        explanation=explanation,
    )
