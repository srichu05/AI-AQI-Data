"""Utilities for merging weather source CSV files into a normalized master dataset."""

from __future__ import annotations

import logging
import re
from pathlib import Path

import pandas as pd

LOGGER = logging.getLogger(__name__)


def _extract_year(file_path: Path) -> int:
    """Extract the year portion from a weather CSV filename."""
    match = re.search(r"(\d{4})", file_path.stem)
    if not match:
        raise ValueError(f"Could not determine year from weather file: {file_path.name}")
    return int(match.group(1))


def _standardize_weather_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize weather fields required by the merge pipeline."""
    required_columns = {"date", "district"}
    missing = required_columns.difference(df.columns)
    if missing:
        raise ValueError(
            f"Weather file is missing required columns: {sorted(missing)}"
        )

    standardized = df.copy()
    standardized["date"] = pd.to_datetime(
        standardized["date"],
        errors="coerce",
    )
    standardized["district"] = (
        standardized["district"].astype(str).str.strip().str.lower()
    )

    if standardized["date"].isna().any():
        raise ValueError("Weather merge encountered invalid or missing date values.")

    return standardized


def merge_weather_data(
    source_dir: str | Path = "data/raw/weather",
    output_path: str | Path = "data/interim/weather_master.csv",
) -> pd.DataFrame:
    """Read all weather source CSV files, concatenate them chronologically, and validate the master result.

    Parameters
    ----------
    source_dir:
        Directory containing weather_YYYY.csv files.
    output_path:
        Destination path for the merged master weather dataset.

    Returns
    -------
    pandas.DataFrame
        The validated weather master dataset.
    """
    source_dir = Path(source_dir)
    output_path = Path(output_path)

    if not source_dir.exists():
        raise FileNotFoundError(f"Weather source directory not found: {source_dir}")

    weather_files = sorted(source_dir.glob("weather_*.csv"), key=_extract_year)
    if not weather_files:
        raise FileNotFoundError(
            f"No weather CSV files were found in {source_dir}"
        )

    frames = []
    for weather_file in weather_files:
        LOGGER.info("Loading weather file: %s", weather_file)
        frame = pd.read_csv(weather_file)
        frames.append(_standardize_weather_frame(frame))

    if not frames:
        raise ValueError("No weather frames were loaded for concatenation.")

    master_df = pd.concat(frames, ignore_index=True, sort=False)
    master_df = master_df.sort_values(["date", "district"]).reset_index(drop=True)

    duplicate_mask = master_df.duplicated(subset=["date", "district"], keep=False)
    if duplicate_mask.any():
        duplicates = master_df.loc[duplicate_mask, ["date", "district"]].drop_duplicates()
        raise ValueError(
            "Duplicate (date, district) records detected in weather master data: "
            f"{duplicates.to_dict(orient='records')}"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    master_df.to_csv(output_path, index=False)
    LOGGER.info("Saved weather master dataset to %s", output_path)

    return master_df
