# AI-Driven Geospatial Modeling and Risk Mapping for Karnataka Air Quality

This project builds an air-quality intelligence pipeline for Karnataka using multi-source environmental data, including:

- CPCB ground monitoring station records
- Google Earth Engine / satellite-derived air quality observations
- GIS contextual variables such as population density, land use, road density, and district boundaries

The workflow integrates these datasets into a unified, geospatially enriched dataset and generates analysis artifacts for dashboard visualization and downstream AI modeling.

## Project Goal

The project aims to:

1. Combine heterogeneous air quality data sources into one consistent dataset
2. Perform geospatial analysis for district-level pollution patterns
3. Generate spatial features for risk mapping and future model development
4. Visualize key findings through a Flask-based dashboard

## Current Workflow

The repository currently supports the following pipeline:

1. Load raw CPCB data
2. Add geographic coordinates
3. Clean and standardize CPCB records
4. Load and clean GEE / satellite data
5. Merge CPCB and GEE data
6. Add GIS and contextual features
7. Save the final dataset
8. Run geospatial analysis and feature extraction
9. Expose results through the dashboard

## Main Entry Points

- `main.py` – runs the core end-to-end data ingestion and fusion pipeline
- `src/geospatial_analysis.py` – computes spatial autocorrelation, hotspot analysis, and district summary statistics
- `src/feature_extraction.py` – generates spatial features such as district mean PM2.5, trend slope, seasonal amplitude, and hotspot distance
- `frontend/dashboard_app.py` – starts the Flask dashboard for viewing analysis results

## Repository Structure

```text
.
├── main.py
├── extract_previews.py
├── requirements.txt
├── config/
│   └── config.yaml
├── data/
│   ├── raw/
│   ├── interim/
│   └── final/
├── src/
│   ├── add_coordinates.py
│   ├── add_gis_features.py
│   ├── clean_cpcb.py
│   ├── clean_gee.py
│   ├── feature_extraction.py
│   ├── geospatial_analysis.py
│   ├── load_cpcb.py
│   ├── merge_datasets.py
│   └── weather/
└── frontend/
    ├── dashboard_app.py
    ├── static/
    └── templates/
```

## Environment Setup

Create and activate a Python environment, then install dependencies:

```bash
pip install -r requirements.txt
```

If you are running the dashboard locally, make sure Flask is available as well:

```bash
pip install flask
```

## Run the Data Pipeline

To build the base merged dataset:

```bash
python main.py
```

This writes the following output to `data/final/`:

- `final_dataset.csv`
- `merged_dataset.csv`

## Run Geospatial Analysis

To compute district-level clustering and interpretation metrics:

```bash
python src/geospatial_analysis.py
```

This generates:

- `data/final/geospatial_analysis_results.json`

## Run Feature Extraction

To enrich the cleaned dataset with district-level spatial and temporal features:

```bash
python src/feature_extraction.py
```

This generates:

- `data/final/karnataka_spatial_features.csv`
- `data/final/spatial_feature_summary.json`

## Launch the Dashboard

To open the dashboard locally:

```bash
cd frontend
python dashboard_app.py
```

Then visit:

```text
http://localhost:5050
```

The dashboard reads results from the final data artifacts and shows:

- district pollution summaries
- hotspot and clustering visuals
- spatial feature tables
- dataset preview panels

## Key Output Artifacts

The project currently produces these main analysis outputs:

- `data/final/final_dataset.csv` – fused air-quality dataset
- `data/final/karnataka_gis_enriched.csv` – GIS-enriched dataset
- `data/final/karnataka_spatial_features.csv` – row-level feature-enriched dataset
- `data/final/geospatial_analysis_results.json` – Moran's I, LISA, and district analysis metrics
- `data/final/karnataka_district_stats.json` – district-level aggregate statistics
- `data/final/karnataka_risk_zones.geojson` – geospatial risk zone map data
- `data/final/karnataka_heatmap_points.json` – heatmap-ready point data

## Notes

- This project is focused on environmental health risk estimation and geospatial analytics.
- It does not perform medical diagnosis.
- The current codebase is designed for a Karnataka-focused air pollution analysis workflow and can be extended for model training and deployment in later stages.

## Future Directions

Potential next steps for the project include:

- training an AI or machine learning risk model
- deploying the dashboard to a web server
- adding automated data refresh pipelines
- improving model explainability and prediction features
