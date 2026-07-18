"""
=============================================================================
STEP: GIS Feature Engineering for Karnataka Air Pollution Dataset
=============================================================================
Project : AI-Driven Geospatial Modeling and Risk Mapping
Purpose : Enrich the merged CPCB+Satellite dataset with geospatial features
          mentioned in the survey paper before preprocessing begins.

GIS Features Added:
    1. population_density   — persons per km² (Karnataka Census 2011 + 2023 proj.)
    2. road_density_km_km2  — km of roads per km² (district-level estimates)
    3. land_use_type        — categorical: Urban / Agricultural / Forest /
                              Industrial / Coastal / Mixed
    4. urban_rural          — 0=Rural, 1=Semi-urban, 2=Urban
    5. district_area_km2    — area derived from GADM shapefile
    6. industrial_zone      — 1 if district has major industrial cluster, else 0
    7. green_cover_pct      — approximate % green/forest cover (Forest Survey India)
    8. nearest_highway      — 1 if district has national highway passing through it

Sources:
    - District area        : GADM shapefile (your uploaded file)
    - Population density   : Karnataka Census 2011 + Census projections
    - Road density         : NHAI + state highway network estimates
    - Land use             : Karnataka State Remote Sensing Application Centre
    - Green cover          : Forest Survey of India State Report 2021
    - Industrial zones     : Karnataka Industrial Policy & data.gov.in
=============================================================================
"""

import pandas as pd
import geopandas as gpd
import numpy as np
import os

def add_gis_features(df, shp_path="data/raw/gis/gadm41_IND_2.shp"):
    print("=" * 65)
    print("STEP 1: Starting GIS Feature Engineering...")
    print("=" * 65)
    print(f"  Rows       : {df.shape[0]:,}")
    print(f"  Columns    : {df.shape[1]}")
    print(f"  Districts  : {df['district'].nunique()}")

    # ─── STEP 2: Load GADM shapefile → extract district area ─────────────────────
    print("\nSTEP 2: Loading shapefile and computing district geometries...")
    gdf_all = gpd.read_file(shp_path)
    gdf_ka  = gdf_all[gdf_all['NAME_1'] == 'Karnataka'].copy()

    # Project to UTM 43N for accurate metric calculations
    gdf_proj      = gdf_ka.to_crs(epsg=32643)
    gdf_ka['district_area_km2'] = gdf_proj.geometry.area / 1e6

    # Compute centroid in projected CRS, then convert back to WGS84
    centroids_proj  = gdf_proj.geometry.centroid
    centroids_wgs84 = centroids_proj.to_crs(epsg=4326)
    gdf_ka['shp_centroid_lat'] = centroids_wgs84.y
    gdf_ka['shp_centroid_lon'] = centroids_wgs84.x

    # Normalize district names to lowercase for joining
    gdf_ka['district_key'] = gdf_ka['NAME_2'].str.lower().str.strip()

    area_df = gdf_ka[['district_key', 'district_area_km2',
                       'shp_centroid_lat', 'shp_centroid_lon']].copy()

    print("  District areas computed:")
    for _, row in area_df.iterrows():
        print(f"    {row['district_key']:<22} → {row['district_area_km2']:>8.1f} km²")

    # ─── STEP 3: GIS LOOKUP TABLE ─────────────────────────────────────────────────
    print("\nSTEP 3: Building GIS lookup table from Karnataka reference data...")

    gis_lookup = {
        'bagalkot':          {'pop_density': 227,  'road_density': 0.28, 'land_use_type': 'Agricultural',  'urban_rural': 1, 'industrial_zone': 0, 'green_cover_pct': 8,  'nearest_highway': 1},
        'bangalore':         {'pop_density': 4381, 'road_density': 2.80, 'land_use_type': 'Urban',         'urban_rural': 2, 'industrial_zone': 1, 'green_cover_pct': 5,  'nearest_highway': 1},
        'bangalore rural':   {'pop_density': 310,  'road_density': 0.65, 'land_use_type': 'Mixed',         'urban_rural': 1, 'industrial_zone': 0, 'green_cover_pct': 12, 'nearest_highway': 1},
        'belgaum':           {'pop_density': 361,  'road_density': 0.42, 'land_use_type': 'Agricultural',  'urban_rural': 1, 'industrial_zone': 1, 'green_cover_pct': 14, 'nearest_highway': 1},
        'bellary':           {'pop_density': 222,  'road_density': 0.35, 'land_use_type': 'Industrial',    'urban_rural': 1, 'industrial_zone': 1, 'green_cover_pct': 6,  'nearest_highway': 1},
        'bidar':             {'pop_density': 321,  'road_density': 0.38, 'land_use_type': 'Agricultural',  'urban_rural': 0, 'industrial_zone': 0, 'green_cover_pct': 5,  'nearest_highway': 1},
        'bijapur':           {'pop_density': 213,  'road_density': 0.30, 'land_use_type': 'Agricultural',  'urban_rural': 0, 'industrial_zone': 0, 'green_cover_pct': 4,  'nearest_highway': 1},
        'chamrajnagar':      {'pop_density': 173,  'road_density': 0.25, 'land_use_type': 'Forest',        'urban_rural': 0, 'industrial_zone': 0, 'green_cover_pct': 42, 'nearest_highway': 0},
        'chikballapura':     {'pop_density': 298,  'road_density': 0.45, 'land_use_type': 'Mixed',         'urban_rural': 0, 'industrial_zone': 0, 'green_cover_pct': 10, 'nearest_highway': 1},
        'chikmagalur':       {'pop_density': 100,  'road_density': 0.22, 'land_use_type': 'Forest',        'urban_rural': 0, 'industrial_zone': 0, 'green_cover_pct': 55, 'nearest_highway': 0},
        'chitradurga':       {'pop_density': 151,  'road_density': 0.28, 'land_use_type': 'Agricultural',  'urban_rural': 0, 'industrial_zone': 0, 'green_cover_pct': 7,  'nearest_highway': 1},
        'dakshina kannada':  {'pop_density': 469,  'road_density': 0.72, 'land_use_type': 'Coastal',       'urban_rural': 1, 'industrial_zone': 1, 'green_cover_pct': 38, 'nearest_highway': 1},
        'davanagere':        {'pop_density': 338,  'road_density': 0.48, 'land_use_type': 'Agricultural',  'urban_rural': 1, 'industrial_zone': 1, 'green_cover_pct': 6,  'nearest_highway': 1},
        'dharwad':           {'pop_density': 459,  'road_density': 0.55, 'land_use_type': 'Mixed',         'urban_rural': 1, 'industrial_zone': 1, 'green_cover_pct': 8,  'nearest_highway': 1},
        'gadag':             {'pop_density': 227,  'road_density': 0.32, 'land_use_type': 'Agricultural',  'urban_rural': 0, 'industrial_zone': 0, 'green_cover_pct': 4,  'nearest_highway': 1},
        'gulbarga':          {'pop_density': 291,  'road_density': 0.35, 'land_use_type': 'Agricultural',  'urban_rural': 1, 'industrial_zone': 1, 'green_cover_pct': 5,  'nearest_highway': 1},
        'hassan':            {'pop_density': 184,  'road_density': 0.30, 'land_use_type': 'Agricultural',  'urban_rural': 0, 'industrial_zone': 0, 'green_cover_pct': 18, 'nearest_highway': 1},
        'haveri':            {'pop_density': 232,  'road_density': 0.35, 'land_use_type': 'Agricultural',  'urban_rural': 0, 'industrial_zone': 0, 'green_cover_pct': 7,  'nearest_highway': 1},
        'kodagu':            {'pop_density': 135,  'road_density': 0.18, 'land_use_type': 'Forest',        'urban_rural': 0, 'industrial_zone': 0, 'green_cover_pct': 70, 'nearest_highway': 0},
        'kolar':             {'pop_density': 324,  'road_density': 0.50, 'land_use_type': 'Mixed',         'urban_rural': 1, 'industrial_zone': 1, 'green_cover_pct': 9,  'nearest_highway': 1},
        'koppal':            {'pop_density': 192,  'road_density': 0.28, 'land_use_type': 'Agricultural',  'urban_rural': 0, 'industrial_zone': 0, 'green_cover_pct': 5,  'nearest_highway': 1},
        'mandya':            {'pop_density': 351,  'road_density': 0.45, 'land_use_type': 'Agricultural',  'urban_rural': 0, 'industrial_zone': 0, 'green_cover_pct': 10, 'nearest_highway': 1},
        'mysore':            {'pop_density': 419,  'road_density': 0.58, 'land_use_type': 'Mixed',         'urban_rural': 1, 'industrial_zone': 1, 'green_cover_pct': 20, 'nearest_highway': 1},
        'raichur':           {'pop_density': 245,  'road_density': 0.30, 'land_use_type': 'Agricultural',  'urban_rural': 0, 'industrial_zone': 1, 'green_cover_pct': 4,  'nearest_highway': 1},
        'ramanagara':        {'pop_density': 371,  'road_density': 0.52, 'land_use_type': 'Mixed',         'urban_rural': 1, 'industrial_zone': 1, 'green_cover_pct': 12, 'nearest_highway': 1},
        'shimoga':           {'pop_density': 132,  'road_density': 0.25, 'land_use_type': 'Forest',        'urban_rural': 0, 'industrial_zone': 0, 'green_cover_pct': 48, 'nearest_highway': 1},
        'tumkur':            {'pop_density': 273,  'road_density': 0.38, 'land_use_type': 'Agricultural',  'urban_rural': 1, 'industrial_zone': 1, 'green_cover_pct': 8,  'nearest_highway': 1},
        'udupi':             {'pop_density': 376,  'road_density': 0.52, 'land_use_type': 'Coastal',       'urban_rural': 1, 'industrial_zone': 0, 'green_cover_pct': 40, 'nearest_highway': 1},
        'uttara kannada':    {'pop_density': 68,   'road_density': 0.15, 'land_use_type': 'Forest',        'urban_rural': 0, 'industrial_zone': 0, 'green_cover_pct': 80, 'nearest_highway': 0},
        'yadgir':            {'pop_density': 211,  'road_density': 0.25, 'land_use_type': 'Agricultural',  'urban_rural': 0, 'industrial_zone': 0, 'green_cover_pct': 4,  'nearest_highway': 0},
    }

    gis_df = pd.DataFrame.from_dict(gis_lookup, orient='index').reset_index()
    gis_df.rename(columns={'index': 'district_key', 'road_density': 'road_density_km_km2'}, inplace=True)

    print(f"  GIS lookup built for {len(gis_df)} districts ✓")

    # ─── STEP 4: Merge area from shapefile into lookup ───────────────────────────
    gis_df = gis_df.merge(area_df, on='district_key', how='left')

    # ─── STEP 5: Prepare dataset for joining ─────────────────────────────────────
    df_copy = df.copy()
    df_copy['district_key'] = df_copy['district'].str.lower().str.strip()

    # ─── STEP 6: Join GIS features into main dataset ─────────────────────────────
    df_enriched = df_copy.merge(gis_df, on='district_key', how='left')
    df_enriched.drop(columns=['district_key'], inplace=True)

    # ─── STEP 7: One-hot encode land_use_type ────────────────────────────────────
    land_use_dummies = pd.get_dummies(
        df_enriched['land_use_type'],
        prefix='land_use',
        drop_first=False
    )
    df_enriched = pd.concat([df_enriched, land_use_dummies], axis=1)

    # ─── STEP 8: Add population × pollution interaction feature ──────────────────
    if 'PM25_est' in df_enriched.columns:
        df_enriched['exposure_index'] = (
            df_enriched['pop_density'] * df_enriched['PM25_est'].fillna(0) / 1000
        )
    if 'NO2_col' in df_enriched.columns:
        df_enriched['traffic_NO2_proxy'] = (
            df_enriched['road_density_km_km2'] * df_enriched['NO2_col'].fillna(0) * 1e5
        )

    print("\nGIS ENRICHMENT COMPLETE ✓")
    return df_enriched
