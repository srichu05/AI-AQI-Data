import pandas as pd
import glob
import os


def load_cpcb_data():

    files = glob.glob("data/raw/cpcb/*.xlsx")

    df_list = []

    for file in files:

        try:

            filename = os.path.basename(file)

            district = (
                filename
                .replace("CPCB", "")
                .replace(".xlsx", "")
                .strip()
                .lower()
            )

            print(f"Processing: {district}")

            df = pd.read_excel(file)

            # Fix broken header files
            if "Remarks" in df.columns:

                df = pd.read_excel(file, header=1)

                df.columns = [
                    "From Date",
                    "To Date",
                    "PM2.5",
                    "PM10",
                    "NO2",
                    "Ozone"
                ]

            df = df.rename(columns={
                "From Date": "date",
                "PM2.5": "PM2_5",
                "PM10": "PM10",
                "NO2": "NO2",
                "Ozone": "O3"
            })

            df["date"] = pd.to_datetime(
                df["date"],
                errors="coerce",
                dayfirst=True
            )

            df["district"] = district

            df = df[
                [
                    "date",
                    "district",
                    "PM2_5",
                    "PM10",
                    "NO2",
                    "O3"
                ]
            ]

            df_list.append(df)

        except Exception as e:

            print(f"Error processing {file}")
            print(e)

    combined_df = pd.concat(
        df_list,
        ignore_index=True
    )

    combined_df.to_csv(
        "data/interim/cpcb_combined.csv",
        index=False
    )

    print("\nCPCB files combined successfully!")

    return combined_df