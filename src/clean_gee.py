import pandas as pd


def clean_gee():

    df = pd.read_csv(
        "data/raw/gee/Karnataka_AirQuality.csv"
    )

    # ---------------------------------
    # Clean column names
    # ---------------------------------
    df.columns = df.columns.str.strip()

    # ---------------------------------
    # Convert district names to lowercase
    # ---------------------------------
    df["district"] = (
        df["district"]
        .str.strip()
        .str.lower()
    )

    # ---------------------------------
    # Rename columns if required
    # ---------------------------------
    rename_map = {}

    if "Date" in df.columns:
        rename_map["Date"] = "date"

    df = df.rename(columns=rename_map)

    # ---------------------------------
    # Convert dates
    # ---------------------------------
    df["date"] = pd.to_datetime(
        df["date"],
        dayfirst=True,
        errors="coerce"
    )

    # ---------------------------------
    # Drop empty placeholder columns if they exist
    # ---------------------------------
    placeholder_cols = ["PM25_cpcb", "PM10_cpcb", "PM25_sensor", "PM10_sensor"]
    df = df.drop(columns=[c for c in placeholder_cols if c in df.columns])

    # ---------------------------------
    # Drop missing rows only if essential data is missing
    # ---------------------------------
    # We only drop if date or district is missing
    df = df.dropna(subset=["date", "district"])

    # ---------------------------------
    # Save cleaned file
    # ---------------------------------
    df.to_csv(
        "data/interim/gee_clean.csv",
        index=False
    )

    return df