"""
Synthetic dataset generation for vehicle load monitoring.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd


def generate_synthetic_data(
    n_samples: int = 5000, random_state: Optional[int] = 42
) -> pd.DataFrame:
    """
    Generate synthetic sensor readings and a target `vehicle_load`.

    Features:
    - suspension_displacement (mm)
    - axle_pressure (kPa)
    - vehicle_speed (km/h)
    - vibration_levels (g)
    """
    rng = np.random.default_rng(random_state)

    suspension_displacement = rng.normal(loc=70, scale=18, size=n_samples).clip(20, 140)
    axle_pressure = rng.normal(loc=260, scale=70, size=n_samples).clip(80, 500)
    vehicle_speed = rng.normal(loc=58, scale=22, size=n_samples).clip(0, 130)
    vibration_levels = rng.normal(loc=1.7, scale=0.65, size=n_samples).clip(0.2, 4.8)

    # Core load relationship with small non-linearity and noise.
    noise = rng.normal(loc=0, scale=180, size=n_samples)
    vehicle_load = (
        18.0 * suspension_displacement
        + 10.5 * axle_pressure
        - 4.2 * vehicle_speed
        + 220 * vibration_levels
        + 0.02 * axle_pressure * suspension_displacement
        + noise
    )
    vehicle_load = np.clip(vehicle_load, 1200, 16000)

    return pd.DataFrame(
        {
            "suspension_displacement": suspension_displacement,
            "axle_pressure": axle_pressure,
            "vehicle_speed": vehicle_speed,
            "vibration_levels": vibration_levels,
            "vehicle_load": vehicle_load,
        }
    )


def save_dataset(
    output_path: Path | str = Path("data") / "vehicle_sensor_data.csv",
    n_samples: int = 5000,
    random_state: int = 42,
) -> Path:
    """Generate and save synthetic dataset to CSV."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = generate_synthetic_data(n_samples=n_samples, random_state=random_state)
    df.to_csv(output_path, index=False)
    return output_path


if __name__ == "__main__":
    path = save_dataset()
    print(f"Dataset generated at: {path}")
