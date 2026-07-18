from src.load_cpcb import load_cpcb_data
from src.add_coordinates import add_coordinates
from src.clean_cpcb import clean_cpcb
from src.clean_gee import clean_gee
from src.merge_datasets import merge_datasets
from src.add_gis_features import add_gis_features
import os

# -----------------------------------
# LOAD CPCB
# -----------------------------------
df_cpcb = load_cpcb_data()

# -----------------------------------
# ADD COORDINATES
# -----------------------------------
df_cpcb = add_coordinates(df_cpcb)

# -----------------------------------
# CLEAN CPCB
# -----------------------------------
df_cpcb = clean_cpcb(df_cpcb)

# -----------------------------------
# CLEAN GEE
# -----------------------------------
df_gee = clean_gee()

# -----------------------------------
# MERGE DATASETS
# -----------------------------------
df_final = merge_datasets(
    df_cpcb,
    df_gee
)

# -----------------------------------
# ADD GIS FEATURES
# -----------------------------------
df_final = add_gis_features(df_final)

# -----------------------------------
# SAVE FINAL DATASET
# -----------------------------------
print("\nSaving final dataset...")
os.makedirs("data/final", exist_ok=True)
df_final.to_csv("data/final/final_dataset.csv", index=False)

print("\nPIPELINE COMPLETED SUCCESSFULLY!")
print(df_final.head())