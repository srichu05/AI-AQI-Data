import pandas as pd
import geopandas as gpd
import numpy as np
import json
import os
from esda.moran import Moran_Local
from libpysal.weights import Queen
from scipy.stats import linregress

def main():
    print("Starting Feature Extraction...")
    
    # 1. Load Data
    csv_path = "data/final/karnataka_gis_enriched.csv"
    if not os.path.exists(csv_path) or 'pop_density' not in pd.read_csv(csv_path, nrows=1).columns:
        fallback_path = "data/final/final_dataset.csv"
        if os.path.exists(fallback_path):
            csv_path = fallback_path
            
    df = pd.read_csv(csv_path)
    shp = gpd.read_file("data/raw/gis/gadm41_IND_2.shp")
    
    for pol, ground, sat in [('PM25', 'PM2_5', 'PM25_est'), ('NO2', 'NO2', 'NO2_col'), ('O3', 'O3', 'O3_col'), ('PM10', 'PM10', None)]:
        col_name = f'{pol}_unified'
        if col_name not in df.columns:
            if ground in df.columns and sat in df.columns:
                df[col_name] = df[ground].fillna(df[sat])
            elif ground in df.columns:
                df[col_name] = df[ground]
            elif sat and sat in df.columns:
                df[col_name] = df[sat]
            else:
                df[col_name] = np.nan
                
    if 'exposure_index' not in df.columns:
        df['exposure_index'] = df.get('pop_density', 0) * df['PM25_unified'].fillna(0) / 1000

    df['district_key'] = df['district'].str.lower().str.strip()
    
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        df['date_ordinal'] = df['date'].apply(lambda x: x.toordinal())
        df['month'] = df['date'].dt.month
        
    print("Computing district level features...")
    district_features = []
    
    shp_ka = shp[shp['NAME_1'] == 'Karnataka'].copy()
    shp_ka['district_key'] = shp_ka['NAME_2'].str.lower().str.strip()
    
    # Base district aggregation
    dist_agg = df.groupby('district_key')['PM25_unified'].agg(['mean', 'std']).reset_index()
    dist_agg.rename(columns={'mean': 'pm25_district_mean', 'std': 'pm25_district_std'}, inplace=True)
    dist_agg['pm25_percentile_rank'] = dist_agg['pm25_district_mean'].rank(pct=True)
    
    # Merge with shapefile to compute spatial lag and hotspot
    gdf = shp_ka.merge(dist_agg, on='district_key', how='inner')
    
    w = Queen.from_dataframe(gdf)
    w.transform = 'r'
    
    from libpysal.weights.spatial_lag import lag_spatial
    y = gdf['pm25_district_mean'].values
    gdf['spatial_lag_pm25'] = lag_spatial(w, y)
    
    lisa = Moran_Local(y, w)
    sig = lisa.p_sim < 0.05
    gdf['hotspot_label'] = np.where((sig) & (lisa.q == 1), 1, 0)
    
    # Compute distance to nearest hotspot
    gdf_proj = gdf.to_crs(epsg=32643)
    hotspots_proj = gdf_proj[gdf_proj['hotspot_label'] == 1].copy()
    
    distances = []
    for idx, row in gdf_proj.iterrows():
        if len(hotspots_proj) > 0:
            dist = hotspots_proj.geometry.centroid.distance(row.geometry.centroid).min() / 1000.0 # in km
        else:
            dist = np.nan
        distances.append(dist)
    gdf['distance_to_nearest_hotspot_km'] = distances
    
    # Extract features back to dataframe format
    spatial_features = gdf[['district_key', 'pm25_district_mean', 'pm25_district_std', 'pm25_percentile_rank', 
                            'spatial_lag_pm25', 'hotspot_label', 'distance_to_nearest_hotspot_km']].copy()
    
    # Compute trends and seasonal amplitude
    trend_amp_features = []
    for d, d_group in df.groupby('district_key'):
        d_group = d_group.dropna(subset=['PM25_unified'])
        if len(d_group) > 1 and 'date_ordinal' in d_group.columns:
            slope, _, _, _, _ = linregress(d_group['date_ordinal'], d_group['PM25_unified'])
        else:
            slope = np.nan
            
        if 'month' in d_group.columns and len(d_group) > 0:
            monthly = d_group.groupby('month')['PM25_unified'].mean()
            amp = monthly.max() - monthly.min()
        else:
            amp = np.nan
            
        trend_amp_features.append({
            'district_key': d,
            'pollution_trend_slope': slope,
            'seasonal_amplitude': amp
        })
        
    trend_df = pd.DataFrame(trend_amp_features)
    
    district_all_features = spatial_features.merge(trend_df, on='district_key', how='left')
    
    print("Merging features back into row-level dataset...")
    df_enriched = df.merge(district_all_features, on='district_key', how='left')
    if 'date_ordinal' in df_enriched.columns:
        df_enriched.drop(columns=['date_ordinal'], inplace=True)
    df_enriched.drop(columns=['district_key'], inplace=True)
    
    out_path = "data/final/karnataka_spatial_features.csv"
    os.makedirs("data/final", exist_ok=True)
    df_enriched.to_csv(out_path, index=False)
    print(f"Feature extraction complete. Enriched dataset saved to {out_path} ({len(df_enriched)} rows).")
    
    summary = {
        "features_added": [
            "pm25_district_mean", "pm25_district_std", "pm25_percentile_rank",
            "pollution_trend_slope", "seasonal_amplitude", "spatial_lag_pm25",
            "hotspot_label", "distance_to_nearest_hotspot_km"
        ],
        "districts_processed": int(df_enriched['district'].nunique()),
        "rows_processed": int(len(df_enriched))
    }
    with open("data/final/spatial_feature_summary.json", "w") as f:
        json.dump(summary, f, indent=4)
        
if __name__ == "__main__":
    main()
