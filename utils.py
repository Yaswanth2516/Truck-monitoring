"""
Utility helpers for model loading, validation, anomaly and event logging.
"""

from __future__ import annotations

import json
import pickle
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, Tuple

import pandas as pd

FEATURE_COLUMNS = [
    "suspension_displacement",
    "axle_pressure",
    "vehicle_speed",
    "vibration_levels",
]

DEFAULT_LOAD_THRESHOLD = 7600.0
DB_PATH = Path("data") / "events.db"


def ensure_db(db_path: Path | str = DB_PATH) -> Path:
    """Create SQLite DB and table if they do not exist."""
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS overload_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                predicted_load REAL NOT NULL,
                status TEXT NOT NULL,
                is_anomaly INTEGER NOT NULL,
                sensor_payload TEXT NOT NULL
            )
            """
        )
        conn.commit()
    return db_path


def log_event(
    predicted_load: float,
    status: str,
    is_anomaly: bool,
    payload: Dict[str, float],
    db_path: Path | str = DB_PATH,
) -> None:
    """Insert an overload/anomaly event into SQLite."""
    ensure_db(db_path)
    timestamp = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO overload_events
            (timestamp, predicted_load, status, is_anomaly, sensor_payload)
            VALUES (?, ?, ?, ?, ?)
            """,
            (timestamp, predicted_load, status, int(is_anomaly), json.dumps(payload)),
        )
        conn.commit()


def load_pickle(path: Path | str):
    with open(path, "rb") as f:
        return pickle.load(f)


def load_model_artifacts(
    model_dir: Path | str = Path("model"),
) -> Tuple[object, object]:
    """Load trained regression and anomaly models."""
    model_dir = Path(model_dir)
    regressor = load_pickle(model_dir / "load_predictor.pkl")
    anomaly_detector = load_pickle(model_dir / "anomaly_detector.pkl")
    return regressor, anomaly_detector


def validate_payload(payload: Dict[str, float], required: Iterable[str] = FEATURE_COLUMNS) -> None:
    """Raise ValueError when required sensor fields are missing or invalid."""
    missing = [key for key in required if key not in payload]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")

    for key in required:
        try:
            float(payload[key])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid numeric value for '{key}'") from exc


def payload_to_array(payload: Dict[str, float]) -> pd.DataFrame:
    """Convert request payload to a one-row dataframe with training feature names."""
    return pd.DataFrame(
        [{col: float(payload[col]) for col in FEATURE_COLUMNS}],
        columns=FEATURE_COLUMNS,
    )


def overload_status(predicted_load: float, threshold: float = DEFAULT_LOAD_THRESHOLD) -> str:
    return "OVERLOADED" if predicted_load > threshold else "SAFE"
