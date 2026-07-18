import os
import json
import csv
from flask import Flask, jsonify, render_template

app = Flask(__name__)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'final')

@app.route('/')
def index():
    return render_template('index.html')

def read_json_file(filename):
    filepath = os.path.join(DATA_DIR, filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        return {"error": str(e)}

@app.route('/api/district_stats')
def district_stats():
    return jsonify(read_json_file('karnataka_district_stats.json'))

@app.route('/api/analysis_results')
def analysis_results():
    return jsonify(read_json_file('geospatial_analysis_results.json'))

@app.route('/api/geojson')
def geojson():
    return jsonify(read_json_file('karnataka_risk_zones.geojson'))

@app.route('/api/heatmap_points')
def heatmap_points():
    return jsonify(read_json_file('karnataka_heatmap_points.json'))

@app.route('/api/spatial_features')
def spatial_features():
    return jsonify(read_json_file('spatial_feature_summary.json'))

@app.route('/api/dataset_preview')
def dataset_preview():
    filepath = os.path.join(DATA_DIR, 'final_dataset.csv')
    try:
        if not os.path.exists(filepath):
            return jsonify({"error": "File not found"})
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)
            rows = []
            row_count = 0
            for row in reader:
                if row_count < 5:
                    rows.append(dict(zip(header, row)))
                row_count += 1
        return jsonify({
            "total_rows": row_count,
            "total_columns": len(header),
            "columns": header,
            "preview": rows
        })
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/api/spatial_preview')
def spatial_preview():
    filepath = os.path.join(DATA_DIR, 'karnataka_spatial_features.csv')
    try:
        if not os.path.exists(filepath):
            return jsonify({"error": "File not found"})
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)
            rows = []
            for i, row in enumerate(reader):
                if i < 100:
                    rows.append(dict(zip(header, row)))
                else:
                    break
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(port=5050, debug=True)
