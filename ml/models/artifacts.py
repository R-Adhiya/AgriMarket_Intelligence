"""
Model artifact utilities — save, load, and list trained models.

Artifacts are stored as:
  ml/models/<crop>_<market_id>.joblib   — trained sklearn model
  ml/models/registry.json              — metadata for all saved models
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np

ML_DIR        = Path(__file__).resolve().parent.parent
MODELS_DIR    = ML_DIR / "models"
REGISTRY_FILE = MODELS_DIR / "registry.json"


def _key(crop: str, market_id: int) -> str:
    return f"{crop.lower().replace(' ', '_')}_{int(market_id)}"


class _NumpyEncoder(json.JSONEncoder):
    """Serialize numpy scalars to native Python types."""
    def default(self, obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


def save_model(model, crop: str, market_id: int, metadata: dict) -> Path:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    key  = _key(crop, market_id)
    path = MODELS_DIR / f"{key}.joblib"
    joblib.dump(model, path)

    registry = load_registry()
    registry[key] = {
        "crop":       crop,
        "market_id":  int(market_id),
        "model_path": str(path),
        "saved_at":   datetime.now(timezone.utc).isoformat(),
        **{k: v for k, v in metadata.items() if k not in ("trained_models",)},
    }
    REGISTRY_FILE.write_text(
        json.dumps(registry, indent=2, cls=_NumpyEncoder), encoding="utf-8"
    )
    return path


def load_model(crop: str, market_id: int):
    key  = _key(crop, market_id)
    path = MODELS_DIR / f"{key}.joblib"
    if not path.exists():
        return None
    return joblib.load(path)


def load_registry() -> dict:
    if not REGISTRY_FILE.exists():
        return {}
    return json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))


def model_exists(crop: str, market_id: int) -> bool:
    return (MODELS_DIR / f"{_key(crop, market_id)}.joblib").exists()
