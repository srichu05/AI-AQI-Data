import logging
from pathlib import Path

import pandas as pd

from src.weather.merge_weather import merge_weather_data
from src.weather.weather_features import compute_weather_features

LOGGER = logging.getLogger(__name__)


def _standardize_join_columns(df, date_col="date", district_col="district"):
    """Normalize date and district columns for join operations."""
    df = df.copy()
    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    if district_col in df.columns:
        df[district_col] = (
            df[district_col]
            .astype(str)
            .str.strip()
            .str.lower()
        )
    return df


def _validate_key_uniqueness(df, key_columns, source_name):
    """Raise an exception if duplicate join keys are found in a dataset."""
    duplicates = df.duplicated(subset=key_columns, keep=False)
    if duplicates.any():
        dup_rows = df.loc[duplicates, key_columns].drop_duplicates()
        raise ValueError(
            f"Duplicate {key_columns} records detected in {source_name}: "
            f"{dup_rows.to_dict(orient='records')}"
        )


def _merge_weather_into_final(final_dataset_path: Path, output_path: Path) -> pd.DataFrame:
    """Join the cleaned weather dataset into the final project dataset using a left join."""
    if not final_dataset_path.exists():
        raise FileNotFoundError(f"Required final dataset not found: {final_dataset_path}")

    weather_master_path = Path("data/interim/weather_master.csv")
    weather_clean_path = Path("data/interim/weather_clean.csv")

    if not weather_master_path.exists():
        merge_weather_data()
    if not weather_clean_path.exists():
        compute_weather_features()

    final_df = pd.read_csv(final_dataset_path)
    weather_df = pd.read_csv(weather_clean_path)

    final_df = _standardize_join_columns(final_df, date_col="date", district_col="district")
    weather_df = _standardize_join_columns(weather_df, date_col="date", district_col="district")

    _validate_key_uniqueness(final_df, ["date", "district"], "final_dataset")
    _validate_key_uniqueness(weather_df, ["date", "district"], "weather_clean")

    merged_weather_df = final_df.merge(
        weather_df,
        on=["date", "district"],
        how="left",
    )

    if len(merged_weather_df) != len(final_df):
        raise ValueError(
            "Weather merge validation failed: output row count does not match "
            "the input final_dataset row count."
        )

    weather_columns = [
        "temperature_C",
        "precipitation_mm",
        "pressure_hPa",
        "wind_speed_10m",
        "relative_humidity",
    ]

    if merged_weather_df[weather_columns].isna().any().any():
        raise ValueError(
            "Weather merge validation failed: weather columns contain unexpected nulls after the left join."
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    merged_weather_df.to_csv(output_path, index=False)
    LOGGER.info("Saved merged output to %s", output_path)

    return merged_weather_df


def merge_datasets(df_cpcb, df_gee):

    # ---------------------------------
    # Standardize district names
    # ---------------------------------
    df_cpcb["district"] = (
        df_cpcb["district"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    df_gee["district"] = (
        df_gee["district"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    # ---------------------------------
    # Standardize dates
    # ---------------------------------
    df_cpcb["date"] = pd.to_datetime(
        df_cpcb["date"],
        errors="coerce"
    ).dt.date

    df_gee["date"] = pd.to_datetime(
        df_gee["date"],
        errors="coerce"
    ).dt.date

    # ---------------------------------
    # Drop redundant columns from CPCB
    # ---------------------------------
    # We want to keep GEE's coordinates (lat/lon)
    df_cpcb = df_cpcb.drop(columns=["lat", "lon"], errors="ignore")

    # ---------------------------------
    # LEFT MERGE
    # KEEP ALL GEE ROWS
    # ---------------------------------
    merged_df = pd.merge(
        df_gee,          # LEFT DATASET = KEEP ALL ROWS
        df_cpcb,
        on=["district", "date"],
        how="left"       # KEEP ALL SATELLITE ROWS
    )

    # ---------------------------------
    # Save output
    # ---------------------------------
    merged_df.to_csv(
        "data/final/merged_dataset.csv",
        index=False
    )

    LOGGER.info("Datasets merged successfully.")
    LOGGER.info("Final rows: %s", len(merged_df))
    LOGGER.info("Columns: %s", list(merged_df.columns))

    final_dataset_path = Path("data/final/final_dataset.csv")
    output_weather_path = Path("data/final/final_dataset_weather.csv")

    if final_dataset_path.exists():
        weather_merged_df = _merge_weather_into_final(
            final_dataset_path,
            output_weather_path,
        )
        return weather_merged_df

    return merged_df