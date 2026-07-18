import pandas as pd
import geopandas as gpd
import numpy as np
import json
import os
from esda.moran import Moran, Moran_Local
from esda.getisord import G_Local
from libpysal.weights import Queen
from scipy.stats import mannwhitneyu

def main():
    print("Starting Geospatial Analysis...")
    
    # 1. Load Data
    csv_path = "data/final/karnataka_gis_enriched.csv"
    if not os.path.exists(csv_path) or 'pop_density' not in pd.read_csv(csv_path, nrows=1).columns:
        fallback_path = "data/final/final_dataset.csv"
        if os.path.exists(fallback_path):
            csv_path = fallback_path
            
    df = pd.read_csv(csv_path)
    shp = gpd.read_file("data/raw/gis/gadm41_IND_2.shp")
    
    # Handle missing unified columns gracefully
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

    # 2. Compute district-level aggregates
    df['district_key'] = df['district'].str.lower().str.strip()
    
    agg_dict = {
        'PM25_unified': 'mean',
        'NO2_unified': 'mean',
        'O3_unified': 'mean',
        'exposure_index': 'mean'
    }
    if 'urban_rural' in df.columns: agg_dict['urban_rural'] = 'first'
    if 'industrial_zone' in df.columns: agg_dict['industrial_zone'] = 'first'
    
    district_agg = df.groupby('district_key').agg(agg_dict).reset_index()
    
    # Merge with shapefile
    shp_ka = shp[shp['NAME_1'] == 'Karnataka'].copy()
    shp_ka['district_key'] = shp_ka['NAME_2'].str.lower().str.strip()
    
    gdf = shp_ka.merge(district_agg, on='district_key', how='inner')
    
    # 3. Moran's I
    print("\nComputing Moran's I...")
    w = Queen.from_dataframe(gdf)
    w.transform = 'r'
    
    y = gdf['PM25_unified'].values
    moran = Moran(y, w)
    print(f"Moran's I: {moran.I:.4f}, p-value: {moran.p_sim:.4f}")
    
    # 4. Local Moran's I (LISA)
    print("\nComputing Local Moran's I (LISA)...")
    lisa = Moran_Local(y, w)
    
    sig = lisa.p_sim < 0.05
    hotspots = []
    for i in range(len(gdf)):
        if sig[i]:
            if lisa.q[i] == 1: hotspots.append("High-High hotspot")
            elif lisa.q[i] == 2: hotspots.append("Low-Low coldspot")
            elif lisa.q[i] == 3: hotspots.append("Low-High outlier")
            elif lisa.q[i] == 4: hotspots.append("High-Low outlier")
            else: hotspots.append("Not Significant")
        else:
            hotspots.append("Not Significant")
            
    gdf['lisa_cluster'] = hotspots
    print("LISA clusters identified.")
    
    # 5. Getis-Ord Gi*
    print("\nComputing Getis-Ord Gi*...")
    gi = G_Local(y, w, star=True)
    gdf['gi_star_p'] = gi.p_sim
    gdf['gi_star_z'] = gi.Zs
    
    results = {
        "morans_i": {
            "statistic": float(moran.I),
            "p_value": float(moran.p_sim),
            "interpretation": "Significant positive spatial autocorrelation (clustering of similar values)." if moran.p_sim < 0.05 and moran.I > 0 else "No significant positive spatial autocorrelation."
        },
        "lisa_clusters": gdf['lisa_cluster'].value_counts().to_dict(),
        "district_clusters": dict(zip(gdf['district_key'], gdf['lisa_cluster']))
    }
    
    # 6. Urban vs Rural
    print("\nUrban vs Rural Comparison...")
    if 'urban_rural' in gdf.columns:
        urban = gdf[gdf['urban_rural'] == 2]['PM25_unified'].dropna()
        rural = gdf[gdf['urban_rural'] == 0]['PM25_unified'].dropna()
        if len(urban) > 0 and len(rural) > 0:
            stat, p = mannwhitneyu(urban, rural, alternative='two-sided')
            results["urban_vs_rural"] = {
                "urban_mean_pm25": float(urban.mean()),
                "rural_mean_pm25": float(rural.mean()),
                "mann_whitney_u": float(stat),
                "p_value": float(p)
            }
            print(f"Urban mean PM25: {urban.mean():.2f}, Rural mean PM25: {rural.mean():.2f}, p-value: {p:.4f}")
            
    # 7. Seasonal Pattern
    print("\nSeasonal Pattern Analysis...")
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        df['month'] = df['date'].dt.month
        monthly_avg = df.groupby('month')['PM25_unified'].mean().to_dict()
        results["monthly_avg_pm25"] = {int(k): float(v) for k, v in monthly_avg.items()}
        peak_month = max(monthly_avg, key=monthly_avg.get)
        print(f"Peak pollution month: {peak_month}")
        results["peak_month"] = int(peak_month)
        
    # 8. Industrial Zone
    print("\nIndustrial Zone Comparison...")
    if 'industrial_zone' in gdf.columns:
        ind = gdf[gdf['industrial_zone'] == 1]['PM25_unified'].dropna()
        non_ind = gdf[gdf['industrial_zone'] == 0]['PM25_unified'].dropna()
        if len(ind) > 0 and len(non_ind) > 0:
            results["industrial_vs_non_industrial"] = {
                "industrial_mean_pm25": float(ind.mean()),
                "non_industrial_mean_pm25": float(non_ind.mean())
            }
            print(f"Industrial mean PM25: {ind.mean():.2f}, Non-industrial mean PM25: {non_ind.mean():.2f}")
            
    os.makedirs("data/final", exist_ok=True)
    with open("data/final/geospatial_analysis_results.json", "w") as f:
        json.dump(results, f, indent=4)
        
    print("\nGeospatial analysis complete. Results saved.")

if __name__ == "__main__":
    main()
