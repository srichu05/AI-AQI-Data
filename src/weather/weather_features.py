"""Weather feature engineering utilities."""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

LOGGER = logging.getLogger(__name__)


def compute_weather_features(
    input_path: str | Path = "data/interim/weather_master.csv",
    output_path: str | Path = "data/interim/weather_clean.csv",
) -> pd.DataFrame:
    """Create engineered weather features and save the cleaned weather dataset.

    The function computes two derived variables:
    - wind_speed_10m from u10 and v10
    - relative_humidity from temperature_C and dewpoint_C
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Weather master file not found: {input_path}")

    required_columns = {
        "date",
        "district",
        "u10",
        "v10",
        "dewpoint_C",
        "temperature_C",
        "precipitation_mm",
        "pressure_hPa",
    }

    weather_df = pd.read_csv(input_path)
    missing_columns = required_columns.difference(weather_df.columns)
    if missing_columns:
        raise ValueError(
            f"Weather master file is missing required columns: {sorted(missing_columns)}"
        )

    weather_df = weather_df.copy()
    weather_df["date"] = pd.to_datetime(weather_df["date"], errors="coerce")
    weather_df["district"] = (
        weather_df["district"].astype(str).str.strip().str.lower()
    )

    if weather_df["date"].isna().any():
        raise ValueError("Weather feature generation encountered invalid or missing date values.")

    u10 = weather_df["u10"].astype(float)
    v10 = weather_df["v10"].astype(float)
    temperature_c = weather_df["temperature_C"].astype(float)
    dewpoint_c = weather_df["dewpoint_C"].astype(float)

    gamma_temp = (17.625 * temperature_c) / (243.04 + temperature_c)
    gamma_dew = (17.625 * dewpoint_c) / (243.04 + dewpoint_c)
    relative_humidity = 100 * np.exp(gamma_dew) / np.exp(gamma_temp)

    weather_df["wind_speed_10m"] = np.sqrt(np.square(u10) + np.square(v10))
    weather_df["relative_humidity"] = np.clip(relative_humidity, 0, 100)

    cleaned_df = weather_df[
        [
            "date",
            "district",
            "temperature_C",
            "precipitation_mm",
            "pressure_hPa",
            "wind_speed_10m",
            "relative_humidity",
        ]
    ].copy()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cleaned_df.to_csv(output_path, index=False)
    LOGGER.info("Saved cleaned weather dataset to %s", output_path)

    return cleaned_df
