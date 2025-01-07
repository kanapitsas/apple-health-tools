#!/usr/bin/env python3
"""
GPX Route Data Extractor

This script processes GPX files to extract route data including coordinates, elevation,
timestamps, and any extension data. It converts the data into a pandas DataFrame and
saves it as a CSV file.

Usage:
    python gpx_routes.py --input "path/to/gpx/files/*.gpx" --output "output.csv"
"""

import argparse
import glob
import os
import sys
from typing import Dict, List

import pandas as pd
import xml.etree.ElementTree as ET
from tqdm import tqdm

def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.

    Returns:
        argparse.Namespace: Parsed command line arguments
    """
    parser = argparse.ArgumentParser(description='Extract route data from GPX files')
    parser.add_argument(
        '--input',
        type=str,
        default='apple_health_export/workout-routes/*.gpx',
        help='Path pattern to GPX files (default: apple_health_export/workout-routes/*.gpx)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='gpx_data.csv',
        help='Output CSV file path (default: gpx_data.csv)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    return parser.parse_args()

def parse_gpx_file(file_path: str) -> List[Dict]:
    """
    Parse a single GPX file and extract route data.

    Args:
        file_path (str): Path to the GPX file

    Returns:
        List[Dict]: List of dictionaries containing parsed trackpoint data

    Raises:
        ET.ParseError: If XML parsing fails
        ValueError: If required data is missing or malformed
    """
    # Parse the XML
    tree = ET.parse(file_path)
    root = tree.getroot()

    # Define namespace
    namespace = {'ns': 'http://www.topografix.com/GPX/1/1'}

    # Initialize list to store data
    data = []
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
                clean_tag = ext.tag.split('}')[-1]
                point_data[clean_tag] = float(ext.text) if ext.text.replace('.','').isdigit() else ext.text

        data.append(point_data)

    return data

def process_gpx_files(input_pattern: str, verbose: bool = False) -> pd.DataFrame:
    """
    Process multiple GPX files and combine their data.

    Args:
        input_pattern (str): Glob pattern for input GPX files
        verbose (bool): Whether to print verbose output

    Returns:
        pd.DataFrame: Combined data from all GPX files
    """
    all_data = []
    gpx_files = glob.glob(input_pattern)

    if not gpx_files:
        raise FileNotFoundError(f"No GPX files found matching pattern: {input_pattern}")

    for gpx_file in tqdm(gpx_files, desc="Processing GPX files"):
        try:
            file_data = parse_gpx_file(gpx_file)
            all_data.extend(file_data)
            if verbose:
                print(f"Successfully processed: {gpx_file}")
        except Exception as e:
            print(f"Error processing {gpx_file}: {str(e)}", file=sys.stderr)

    df = pd.DataFrame(all_data)

    # Convert time column to datetime if it exists
    if 'time' in df.columns:
        df['time'] = pd.to_datetime(df['time'])

    return df

def main():
    """Main execution function."""
    args = parse_arguments()

    try:
        df = process_gpx_files(args.input, args.verbose)

        if args.verbose:
            print(f"\nTotal points: {len(df)}")
            print(f"Columns: {df.columns.tolist()}")
            print("\nFirst few rows:")
            print(df.head())

        df.to_csv(args.output, index=False)
        print(f"\nData successfully saved to: {args.output}")

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
