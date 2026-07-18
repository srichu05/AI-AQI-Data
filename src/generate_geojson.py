import pandas as pd
import geopandas as gpd
import json
import os

def main():
    print("Generating GeoJSON and map data...")
    
    csv_path = "data/final/karnataka_spatial_features.csv"
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found. Run feature_extraction.py first.")
        return
        
    df = pd.read_csv(csv_path)
    shp = gpd.read_file("data/raw/gis/gadm41_IND_2.shp")
    
    df['district_key'] = df['district'].str.lower().str.strip()
    
    # We need mean PM25, NO2, O3, exposure_index, hotspot_label
    # Since the csv has row-level, we aggregate it
    agg_dict = {
        'PM25_unified': 'mean',
        'NO2_unified': 'mean',
        'O3_unified': 'mean',
        'exposure_index': 'mean',
        'hotspot_label': 'first',
        'lat': 'first',
        'lon': 'first'
    }
    
    district_stats = df.groupby('district_key').agg(agg_dict).reset_index()
    
    # Try to load LISA clusters from geospatial_analysis_results.json
    lisa_map = {}
    res_path = "data/final/geospatial_analysis_results.json"
    if os.path.exists(res_path):
        with open(res_path, 'r') as f:
            res_data = json.load(f)
            lisa_map = res_data.get('district_clusters', {})
            
    district_stats['lisa_cluster'] = district_stats['district_key'].map(lambda x: lisa_map.get(x, 'Unknown'))
    
    shp_ka = shp[shp['NAME_1'] == 'Karnataka'].copy()
    shp_ka['district_key'] = shp_ka['NAME_2'].str.lower().str.strip()
    
    gdf = shp_ka.merge(district_stats, on='district_key', how='inner')
    
    # 1. karnataka_risk_zones.geojson
    # Rename columns for properties
    gdf_out = gdf[['NAME_2', 'PM25_unified', 'NO2_unified', 'O3_unified', 
                   'lisa_cluster', 'hotspot_label', 'exposure_index', 'geometry']].copy()
    gdf_out.rename(columns={
        'NAME_2': 'district',
        'PM25_unified': 'mean_pm25',
        'NO2_unified': 'mean_no2',
        'O3_unified': 'mean_o3'
    }, inplace=True)
    
    gdf_out = gdf_out.to_crs(epsg=4326)
    
    os.makedirs("data/final", exist_ok=True)
    gdf_out.to_file("data/final/karnataka_risk_zones.geojson", driver='GeoJSON')
    print(f"Created karnataka_risk_zones.geojson with {len(gdf_out)} features.")
    
    # 2. karnataka_heatmap_points.json
    heatmap_points = []
    # Using centroid for heatmap points
    for idx, row in gdf_out.iterrows():
        centroid = row.geometry.centroid
        heatmap_points.append({
            "lat": centroid.y,
            "lon": centroid.x,
            "pm25_value": row['mean_pm25'],
            "no2_value": row['mean_no2']
        })
        
    with open("data/final/karnataka_heatmap_points.json", "w") as f:
        json.dump(heatmap_points, f, indent=4)
    print(f"Created karnataka_heatmap_points.json with {len(heatmap_points)} points.")
    
    # 3. karnataka_district_stats.json
    # Drop geometry for simple json
    stats_df = gdf_out.drop(columns=['geometry'])
    stats_list = stats_df.to_dict(orient='records')
    with open("data/final/karnataka_district_stats.json", "w") as f:
        json.dump(stats_list, f, indent=4)
    print("Created karnataka_district_stats.json.")
    print("Summary: Processed", len(gdf_out), "districts successfully.")

if __name__ == "__main__":
    main()
