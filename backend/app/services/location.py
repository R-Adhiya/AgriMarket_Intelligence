"""
Location and transport cost service — Phase 6.

Distance: Haversine formula (no external API required).
Transport cost: simple deterministic formula documented below.

ASSUMPTIONS
-----------
* Distance method: Haversine (great-circle), returns km.
* Transport formula:
      estimated_cost = base_cost + (distance_km × rate_per_km × quantity_quintals)
  where base_cost and rate_per_km come from app settings (configurable).
* These are development estimates, NOT real commercial transporter quotes.
* Predefined coordinates cover the sample Tamil Nadu development locations only.
  If the farmer's district is not in the lookup, a 422 is raised.
"""

import math
from typing import Optional

# ── Predefined development coordinates (Tamil Nadu sample districts) ───────────
# Source: approximate geographic centres; development/sample data only.
DISTRICT_COORDS: dict[str, tuple[float, float]] = {
    "coimbatore":  (11.0168, 76.9558),
    "erode":       (11.3410, 77.7172),
    "tiruppur":    (11.1085, 77.3411),
    "salem":       (11.6643, 78.1460),
    "chennai":     (13.0827, 80.2707),
    "madurai":     ( 9.9252, 78.1198),
    "tiruchirappalli": (10.7905, 78.7047),
    "tirunelveli": ( 8.7139, 77.7567),
    "vellore":     (12.9165, 79.1325),
    "thanjavur":   (10.7870, 79.1378),
    "namakkal":    (11.2200, 78.1600),
    "krishnagiri": (12.5266, 78.2137),
    "dharmapuri":  (12.1288, 78.1580),
    "villupuram":  (11.9401, 79.4861),
    "cuddalore":   (11.7480, 79.7714),
    "nagapattinam":(10.7672, 79.8449),
}


class LocationError(ValueError):
    """Raised when a location cannot be resolved to coordinates."""
    pass


class CoordinateError(ValueError):
    """Raised when raw coordinates are out of valid range."""
    pass


# ── Validation ────────────────────────────────────────────────────────────────

def validate_coordinates(lat: float, lon: float) -> None:
    if not (-90.0 <= lat <= 90.0):
        raise CoordinateError(f"Latitude {lat} is out of range -90..90.")
    if not (-180.0 <= lon <= 180.0):
        raise CoordinateError(f"Longitude {lon} is out of range -180..180.")


# ── Haversine distance ────────────────────────────────────────────────────────

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Return the great-circle distance in kilometres between two points.
    Inputs are decimal degrees (WGS-84).
    """
    validate_coordinates(lat1, lon1)
    validate_coordinates(lat2, lon2)

    R = 6371.0  # Earth mean radius, km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lam = math.radians(lon2 - lon1)

    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ── Location resolution ───────────────────────────────────────────────────────

def resolve_farmer_coords(
    farmer_lat: Optional[float],
    farmer_lon: Optional[float],
    district: Optional[str],
) -> tuple[float, float]:
    """
    Resolve the farmer's coordinates.

    Priority:
    1. Farmer's own stored lat/lon (from Phase 4 profile update).
    2. Predefined lookup by district name (development/sample only).

    Raises LocationError if neither is available.
    """
    if farmer_lat is not None and farmer_lon is not None:
        validate_coordinates(float(farmer_lat), float(farmer_lon))
        return float(farmer_lat), float(farmer_lon)

    if district:
        key = district.strip().lower()
        if key in DISTRICT_COORDS:
            return DISTRICT_COORDS[key]

    location_hint = district or "unknown"
    raise LocationError(
        f"Cannot resolve coordinates for farmer location '{location_hint}'. "
        "Please update your profile with a supported district (e.g. Coimbatore, Erode, Salem) "
        "or set your GPS coordinates in the farmer profile."
    )


def resolve_market_coords(
    market_lat: Optional[float],
    market_lon: Optional[float],
    market_name: str,
) -> tuple[float, float]:
    """
    Resolve market coordinates.

    Uses the stored lat/lon from the Market model (populated in Phase 2 seed data).
    Raises LocationError if coordinates are missing.
    """
    if market_lat is not None and market_lon is not None:
        validate_coordinates(float(market_lat), float(market_lon))
        return float(market_lat), float(market_lon)

    raise LocationError(
        f"Market '{market_name}' does not have coordinates stored. "
        "Please update the market record with latitude/longitude."
    )


# ── Transport cost estimation ─────────────────────────────────────────────────

def estimate_transport_cost(
    distance_km: float,
    quantity_quintals: float,
    base_cost: float,
    rate_per_km: float,
) -> float:
    """
    Estimated transport cost (INR).

    Formula:
        cost = base_cost + (distance_km × rate_per_km × quantity_quintals)

    This is a simplified model for a college project. Actual costs
    depend on vehicle type, road condition, fuel prices, and negotiation.
    """
    if distance_km < 0:
        raise ValueError("distance_km must be non-negative.")
    if quantity_quintals <= 0:
        raise ValueError("quantity must be greater than 0.")
    return round(base_cost + (distance_km * rate_per_km * quantity_quintals), 2)
