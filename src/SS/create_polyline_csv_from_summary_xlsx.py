import os
import re
import pandas as pd

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

def parse_polyline(polyline_str):
    matches = re.findall(r'\((-?\d*\.?\d+),\s*(-?\d*\.?\d+),\s*(-?\d*\.?\d+)\)', str(polyline_str))
    return [(float(x), float(y), float(z)) for x, y, z in matches] if matches else []

def create_dimensions_csv(df, output_folder):
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

def main():
    data_folder = get_data_folder()
    xlsx_filename = '20250602_Central model Polyline check_JW.xlsx'
    xlsx_path = os.path.join(data_folder, xlsx_filename)

    if not os.path.exists(xlsx_path):
        raise FileNotFoundError(f"{xlsx_filename} not found in {data_folder}.")

    df = pd.read_excel(xlsx_path, sheet_name='Summary', header=3)
    output_folder = get_output_folder()

    for idx, row in df.iterrows():
        asset = str(row.get('Asset', '')).strip()
        polyline_str = row.get('Ph3 report polyline', '')
        coords = parse_polyline(polyline_str)
        if not asset or not coords:
            continue

        csv_rows = [{
            'Asset': asset,
            'X': x,
            'Y': y,
            'Z': z,
            'Material': row.get('Material', ''),
            'Name': row.get('Name', ''),
            'Internal diameter': row.get('Internal diameter', ''),
            'Wall thickness': row.get('Wall thickness', '')
        } for x, y, z in coords]

        asset_filename = f"{asset}.csv"
        asset_path = os.path.join(output_folder, asset_filename)
        pd.DataFrame(csv_rows).to_csv(asset_path, index=False)

    create_dimensions_csv(df, get_dimensions_folder())
    print(df.head())

if __name__ == "__main__":
    main()
