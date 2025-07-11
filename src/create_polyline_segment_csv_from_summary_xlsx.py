import os
import re
import pandas as pd
import numpy as np

# Constants
BEND_ANGLE_THRESHOLD = 60  # degrees, adjust as needed 

# May use bend angle over distance ratio in the future

# --- Folder Utilities ---

def get_data_folder():
    return os.path.join(os.path.dirname(__file__), '..', 'data', 'summary')

def get_output_folder():
    folder = os.path.join(os.path.dirname(__file__), '..', 'data', 'polylines')
    os.makedirs(folder, exist_ok=True)
    return folder

def get_dimensions_folder():
    folder = os.path.join(os.path.dirname(__file__), '..', 'data', 'dimensions')
    os.makedirs(folder, exist_ok=True)
    return folder

# --- Polyline and Geometry Utilities ---

def parse_polyline(polyline_str):
    """Parse a polyline string into a list of (x, y, z) tuples."""
    matches = re.findall(r'\((-?\d*\.?\d+),\s*(-?\d*\.?\d+),\s*(-?\d*\.?\d+)\)', str(polyline_str))
    return [(float(x), float(y), float(z)) for x, y, z in matches] if matches else []

def angle_between(v1, v2):
    """Calculate the angle in degrees between two vectors."""
    v1 = np.array(v1)
    v2 = np.array(v2)
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 == 0 or norm2 == 0:
        return 0
    cos_theta = np.clip(np.dot(v1, v2) / (norm1 * norm2), -1.0, 1.0)
    return np.degrees(np.arccos(cos_theta))

# --- CSV Creation Functions ---

def create_dimensions_csv(df, output_folder):
    """Create a CSV file with dimensions information."""
    dimensions_df = df[['Name', 'Internal diameter', 'Wall thickness']].copy()
    dimensions_df = dimensions_df.rename(columns={
        'Name': 'Names',
        'Internal diameter': 'Internal Diameter [mm]',
        'Wall thickness': 'Wall Thickness [mm]'
    })
    dimensions_df = dimensions_df.dropna(subset=['Names', 'Internal Diameter [mm]', 'Wall Thickness [mm]'])
    dimensions_df = dimensions_df.drop_duplicates()
    dimensions_csv_path = os.path.join(output_folder, 'dimensions.csv')
    dimensions_df.to_csv(dimensions_csv_path, index=False)
    print(f"Dimensions CSV created at: {dimensions_csv_path}")

# --- Master CSV Collector ---
master_csv_rows = []

def process_polyline(row, output_folder):
    """Process a single polyline row and write segment CSVs. Also collect for master CSV."""
    lon_num = str(row.get('Lon-No', '')).strip()
    asset = str(row.get('Asset', '')).strip()
    polyline_str = row.get('Ph3 report polyline', '')
    coords = parse_polyline(polyline_str)
    if not lon_num or not asset or not coords:
        print(f"Skipping row: Lon-No='{lon_num}', Asset='{asset}', Polyline='{polyline_str}' (asset or coords missing)")
        return

    polyline_name_base = f"{lon_num}_{asset}"

    def write_segment(segment_coords, segment_num=1):
        global master_csv_rows
        segment_filename = f"{polyline_name_base}_segment-{segment_num}.csv"
        segment_name = f"{polyline_name_base}_segment-{segment_num}"  # No .csv extension
        segment_path = os.path.join(output_folder, segment_filename)
        csv_rows = [{
            'polyline': segment_name,  # Use name without .csv
            'x': x,
            'y': y,
            'z': z,
            'acceptance_criteria': row.get('Material', ''),
            'internal diameter': row.get('Internal diameter', ''),
            'wall thickness': row.get('Wall thickness', ''),
            'pipe_segment_length': row.get('Pipe Segment Length', '')
        } for x, y, z in segment_coords]
        pd.DataFrame(csv_rows).to_csv(segment_path, index=False)
        master_csv_rows += csv_rows
        print(f"Segment {segment_num} CSV created: {segment_path}")

    if len(coords) > 3:
        bend_indices = []
        for i in range(1, len(coords) - 1):
            v1 = np.subtract(coords[i], coords[i - 1])
            v2 = np.subtract(coords[i + 1], coords[i])
            ang = angle_between(v1, v2)
            if ang > BEND_ANGLE_THRESHOLD:
                bend_indices.append(i)
        if bend_indices:
            segment_indices = [0] + bend_indices + [len(coords) - 1]
            for seg_num in range(len(segment_indices) - 1):
                start = segment_indices[seg_num]
                end = segment_indices[seg_num + 1]
                segment_coords = coords[start:end + 1]
                write_segment(segment_coords, seg_num + 1)
        else:
            write_segment(coords, 1)
            print(f"No bends found for asset '{asset}', output as single segment.")
    else:
        write_segment(coords, 1)
        print(f"Polyline for asset '{asset}' has <=3 points, output as single segment.")

def write_master_csv(output_folder):
    """Write the master CSV with all polylines/segments."""
    if master_csv_rows:
        master_csv_path = os.path.join(output_folder, "0_central_model_polylines.csv")
        pd.DataFrame(master_csv_rows).to_csv(master_csv_path, index=False)
        print(f"Master CSV created at: {master_csv_path}")
    else:
        print("No data collected for master CSV.")

# --- Main Execution ---

def main():
    data_folder = get_data_folder()
    xlsx_filename = '20250602_Central model Polyline check_JW.xlsx'
    xlsx_path = os.path.join(data_folder, xlsx_filename)

    if not os.path.exists(xlsx_path):
        raise FileNotFoundError(f"{xlsx_filename} not found in {data_folder}.")

    df = pd.read_excel(xlsx_path, sheet_name='Summary', header=3)
    output_folder = get_output_folder()

    for idx, row in df.iterrows():
        process_polyline(row, output_folder)
    create_dimensions_csv(df, get_dimensions_folder())
    write_master_csv(output_folder)
    print("Processing complete. DataFrame head:")
    print(df.head())

if __name__ == "__main__":
    main()
