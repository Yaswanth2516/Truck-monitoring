"""
Flask application for real time vehicle load prediction and monitoring dashboard.

"""

from __future__ import annotations

from pathlib import Path

from flask import Flask, jsonify, render_template, request

from utils import (
    DEFAULT_LOAD_THRESHOLD,
    ensure_db,
    load_model_artifacts,
    log_event,
    overload_status,
    payload_to_array,
    validate_payload,
)

app = Flask(__name__)

THRESHOLD_LOAD = DEFAULT_LOAD_THRESHOLD
MODEL_DIR = Path("model")

# Load artifacts on startup.
regressor, anomaly_detector = load_model_artifacts(MODEL_DIR)
ensure_db()


@app.get("/")
def index():
    return render_template("index.html", threshold=THRESHOLD_LOAD)


@app.post("/predict")
def predict():
    """
    Predict vehicle load and return overload + anomaly flags.
    """
    payload = request.get_json(silent=True) or {}

    try:
        validate_payload(payload)
        model_input = payload_to_array(payload)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    predicted_load = float(regressor.predict(model_input)[0])
    anomaly_label = int(anomaly_detector.predict(model_input)[0])  # -1 anomaly, 1 normal
    is_anomaly = anomaly_label == -1
    status = overload_status(predicted_load, threshold=THRESHOLD_LOAD)

    if status == "OVERLOADED":
        print(f"[ALERT] Overload detected. Predicted load={predicted_load:.2f}")
        log_event(
            predicted_load=predicted_load,
            status=status,
            is_anomaly=is_anomaly,
            payload=payload,
        )

    # Optional log for unusual, non-overload behavior.
    if is_anomaly and status == "SAFE":
        print(f"[ALERT] Anomalous sensor pattern. Predicted load={predicted_load:.2f}")
        log_event(
            predicted_load=predicted_load,
            status="ANOMALY",
            is_anomaly=is_anomaly,
            payload=payload,
        )

    return jsonify(
        {
            "predicted_load": round(predicted_load, 2),
            "threshold_load": THRESHOLD_LOAD,
            "status": status,
            "is_anomaly": is_anomaly,
        }
    )


if __name__ == "__main__":
    app.run(debug=True)
