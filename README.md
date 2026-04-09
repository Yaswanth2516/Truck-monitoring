# Machine Learning Vehicle Load Monitoring System

This project predicts vehicle load from sensor readings, flags overload conditions, detects anomalous sensor patterns, and logs important events.

## Tech stack
- Python
- Scikit-learn
- Flask
- SQLite
- HTML/CSS/JavaScript dashboard (Flask template)
- Chart.js (CDN for client-side visualization)

## Project structure
- `data/` - synthetic dataset + SQLite event DB
- `model/` - trained regression and anomaly model artifacts
- `data/generate_data.py` - synthetic data generation
- `train.py` - model training, evaluation, artifact export
- `utils.py` - shared helpers (validation, db logging, model loading)
- `app.py` - Flask API + dashboard routes
- `templates/index.html` - dashboard layout and component structure
- `static/css/styles.css` - modern responsive UI styling (light/dark modes)
- `static/js/dashboard.js` - dashboard interactions, validation, chart updates

## Dashboard features
- Modern card-based monitoring UI with responsive layout (mobile + desktop)
- Sensor input form with labels, placeholders, inline validation, and tooltips
- Prediction actions: `Predict Load`, `Sample Data`, and `Reset`
- Output panel with predicted load, status, anomaly flag, and threshold
- Status indicators with color coding:
  - Green = safe
  - Red = overloaded
- Progress bar for load vs threshold
- Chart.js bar chart for predicted load and threshold comparison
- Overload toast alert for critical conditions
- Theme toggle with persistent preference:
  - Light mode
  - Dark mode

## Sensor input guide (what changes and how it acts)

### 1) Suspension Displacement (`suspension_displacement`)
- **What it represents:** vertical suspension movement caused by payload weight and road conditions.
- **How it changes:** usually increases when cargo weight increases; can also spike on bumps/uneven roads.
- **How it acts in prediction:** higher displacement generally pushes the model toward higher predicted load, especially when paired with high axle pressure.

### 2) Axle Pressure (`axle_pressure`)
- **What it represents:** force applied on axle(s) due to vehicle + cargo mass.
- **How it changes:** rises as payload increases; may fluctuate slightly due to braking, acceleration, and road gradient.
- **How it acts in prediction:** this is typically one of the strongest load indicators; sustained high values are commonly linked to overload outcomes.

### 3) Vehicle Speed (`vehicle_speed`)
- **What it represents:** current vehicle speed at the time of measurement.
- **How it changes:** depends on driving behavior, traffic, and route profile.
- **How it acts in prediction:** speed provides context rather than direct weight; unusual combinations (for example very high speed with extreme pressure/vibration) can contribute to anomaly detection.

### 4) Vibration Levels (`vibration_levels`)
- **What it represents:** intensity/frequency of vibration measured by onboard sensors.
- **How it changes:** tends to increase with poor road surfaces, unstable load distribution, or mechanical stress.
- **How it acts in prediction:** moderate increase can align with heavier loads, but extreme or inconsistent values are often useful for anomaly flagging.

### 5) Vehicle Load (`predicted_load`, output from model)
- **What it represents:** estimated current load computed from the above sensor inputs.
- **How it changes:** rises when displacement/pressure (and sometimes vibration) trends indicate heavier payload.
- **How it acts in system behavior:**
  - Compared against `threshold_load`
  - `predicted_load > threshold_load` -> status becomes `OVERLOADED`
  - `predicted_load <= threshold_load` -> status remains `SAFE`

### Important note
- Sensor effects are **combined** (multivariate). A single field alone may not determine the final result.
- Different truck types, sensor calibration, and road environments can change exact behavior.

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
