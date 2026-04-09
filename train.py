"""
Train and save vehicle load prediction and anomaly detection models.
"""

from __future__ import annotations

import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split

from data.generate_data import save_dataset
from utils import FEATURE_COLUMNS

DATA_PATH = Path("data") / "vehicle_sensor_data.csv"
MODEL_DIR = Path("model")


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.sqrt(mean_squared_error(y_true, y_pred)))


def train_and_save_models() -> None:
    """Train regression + anomaly models and save model artifacts."""
    if not DATA_PATH.exists():
        save_dataset(output_path=DATA_PATH, n_samples=6000, random_state=42)

    df = pd.read_csv(DATA_PATH)
    x = df[FEATURE_COLUMNS]
    y = df["vehicle_load"]

    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.2, random_state=42
    )

    # Train two regressors and keep the one with lower RMSE.
    candidates = {
        "linear_regression": LinearRegression(),
        "random_forest": RandomForestRegressor(
            n_estimators=220, random_state=42, n_jobs=-1
        ),
    }
    scores = {}
    trained = {}

    for name, model in candidates.items():
        model.fit(x_train, y_train)
        pred = model.predict(x_test)
        scores[name] = {
            "MAE": float(mean_absolute_error(y_test, pred)),
            "RMSE": rmse(y_test, pred),
        }
        trained[name] = model

    best_name = min(scores, key=lambda k: scores[k]["RMSE"])
    best_model = trained[best_name]

    # Isolation Forest learns normal sensor behavior and flags unusual patterns.
    anomaly_detector = IsolationForest(
        n_estimators=200, contamination=0.03, random_state=42
    )
    anomaly_detector.fit(x_train)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    with open(MODEL_DIR / "load_predictor.pkl", "wb") as f:
        pickle.dump(best_model, f)
    with open(MODEL_DIR / "anomaly_detector.pkl", "wb") as f:
        pickle.dump(anomaly_detector, f)

    metrics = {
        "dataset_path": str(DATA_PATH),
        "selected_model": best_name,
        "scores": scores,
        "feature_columns": FEATURE_COLUMNS,
    }
    with open(MODEL_DIR / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print("Training complete.")
    print(f"Selected model: {best_name}")
    print(f"MAE:  {scores[best_name]['MAE']:.2f}")
    print(f"RMSE: {scores[best_name]['RMSE']:.2f}")
    print(f"Saved: {MODEL_DIR / 'load_predictor.pkl'}")
    print(f"Saved: {MODEL_DIR / 'anomaly_detector.pkl'}")
    print(f"Saved: {MODEL_DIR / 'metrics.json'}")


if __name__ == "__main__":
    train_and_save_models()
