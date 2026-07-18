import os
import json
import csv

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data', 'final')
OUT_DIR = os.path.join(os.path.dirname(__file__), 'frontend', 'static', 'data')

def create_dataset_preview():
    filepath = os.path.join(DATA_DIR, 'final_dataset.csv')
    if not os.path.exists(filepath):
        return
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = []
        row_count = 0
        for row in reader:
            if row_count < 5:
                rows.append(dict(zip(header, row)))
            row_count += 1
    out = {
        "total_rows": row_count,
        "total_columns": len(header),
        "columns": header,
        "preview": rows
    }
    with open(os.path.join(OUT_DIR, 'dataset_preview.json'), 'w') as f:
        json.dump(out, f)

def create_spatial_preview():
    filepath = os.path.join(DATA_DIR, 'karnataka_spatial_features.csv')
    if not os.path.exists(filepath):
        return
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = []
        for i, row in enumerate(reader):
            if i < 100:
                rows.append(dict(zip(header, row)))
            else:
                break
    with open(os.path.join(OUT_DIR, 'spatial_preview.json'), 'w') as f:
        json.dump(rows, f)

if __name__ == '__main__':
    create_dataset_preview()
    create_spatial_preview()
