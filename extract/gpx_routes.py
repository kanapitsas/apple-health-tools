import pandas as pd
import xml.etree.ElementTree as ET
import glob
import os
from tqdm import tqdm

def parse_gpx_file(file_path):
    # Parse the XML
    tree = ET.parse(file_path)
    root = tree.getroot()

    # Define namespace
    namespace = {'ns': 'http://www.topografix.com/GPX/1/1'}

    # Initialize lists to store data
    data = []

    # Get filename without extension for later reference
    filename = os.path.basename(file_path)

    # Find all trackpoints
    for trkpt in root.findall('.//ns:trkpt', namespace):
        point_data = {
            'filename': filename,
            'latitude': float(trkpt.get('lat')),
            'longitude': float(trkpt.get('lon')),
            'elevation': float(trkpt.find('ns:ele', namespace).text) if trkpt.find('ns:ele', namespace) is not None else None,
            'time': trkpt.find('ns:time', namespace).text if trkpt.find('ns:time', namespace) is not None else None
        }

        # Get extension data if available
        extensions = trkpt.find('.//ns:extensions', namespace)
        if extensions is not None:
            for ext in extensions:
                # Clean up the tag name by removing the namespace
                clean_tag = ext.tag.split('}')[-1]  # Take everything after the last }
                point_data[clean_tag] = float(ext.text) if ext.text.replace('.','').isdigit() else ext.text

        data.append(point_data)

    return data

def main():
    # Path to your GPX files
    gpx_files_path = 'apple_health_export/workout-routes/*.gpx'

    # Initialize an empty list to store all data
    all_data = []

    # Process each GPX file
    for gpx_file in tqdm(glob.glob(gpx_files_path), desc="Processing GPX files"):
        try:
            file_data = parse_gpx_file(gpx_file)
            all_data.extend(file_data)
        except Exception as e:
            print(f"Error processing {gpx_file}: {str(e)}")

    # Create DataFrame
    df = pd.DataFrame(all_data)

    # Convert time column to datetime if it exists
    if 'time' in df.columns:
        df['time'] = pd.to_datetime(df['time'])

    return df

if __name__ == "__main__":
    df = main()
    print(df.head())
    print(f"\nTotal points: {len(df)}")
    print(f"\nColumns: {df.columns.tolist()}")
    df.to_csv('gpx_data.csv', index=False)
