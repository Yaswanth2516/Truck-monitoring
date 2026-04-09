# Machine Learning Vehicle Load Monitoring System

This project predicts vehicle load from sensor readings, flags overload conditions, detects anomalous sensor patterns, and logs important events.

## Tech stack
- Python
- Scikit-learn
- Flask
- SQLite
- HTML/CSS dashboard (Flask template)

## Project structure
- `data/` - synthetic dataset + SQLite event DB
- `model/` - trained regression and anomaly model artifacts
- `data/generate_data.py` - synthetic data generation
- `train.py` - model training, evaluation, artifact export
- `utils.py` - shared helpers (validation, db logging, model loading)
- `app.py` - Flask API + dashboard routes
- `templates/index.html` - basic monitoring dashboard

## Step-by-step setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Generate dataset and train models:
   ```bash
   python train.py
   ```
3. Run Flask app:
   ```bash
   python app.py
   ```
4. Open dashboard:
   - `http://127.0.0.1:5000`

## API usage
### `POST /predict`
Request JSON:
```json
{
  "suspension_displacement": 80,
  "axle_pressure": 300,
  "vehicle_speed": 45,
  "vibration_levels": 2.1
}
```

Response JSON example:
```json
{
  "predicted_load": 8600.42,
  "threshold_load": 7600.0,
  "status": "OVERLOADED",
  "is_anomaly": false
}
```

## Sample test payloads
- Safe-ish:
```json
{
  "suspension_displacement": 62,
  "axle_pressure": 240,
  "vehicle_speed": 70,
  "vibration_levels": 1.3
}
```

- Likely overload:
```json
{
  "suspension_displacement": 110,
  "axle_pressure": 430,
  "vehicle_speed": 22,
  "vibration_levels": 3.4
}
```

- Suspicious/anomaly candidate:
```json
{
  "suspension_displacement": 20,
  "axle_pressure": 500,
  "vehicle_speed": 125,
  "vibration_levels": 4.8
}
```
