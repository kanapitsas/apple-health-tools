#!/usr/bin/env python3
"""
Workout Route Visualization Tool

This script creates an interactive map visualization of workout routes using GPS data.
It generates both individual route traces and a heatmap overlay to show frequently
traversed areas.

Features:
- Plots individual workout routes on an interactive map
- Creates a heatmap overlay of all activities
- Allows customization of visualization parameters
- Supports data sampling for performance optimization

Usage:
    python plot_routes.py --input gpx_data.csv --output workout_map.html
    python plot_routes.py --input gpx_data.csv --sample-rate 20 --blur 15

Required input CSV format:
    - filename: Unique identifier for each workout
    - latitude: GPS latitude coordinates
    - longitude: GPS longitude coordinates
"""

import argparse
import pandas as pd
import folium
from folium import plugins
from tqdm import tqdm


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Create an interactive map of workout routes with heatmap overlay.'
    )
    parser.add_argument(
        '--input',
        '-i',
        required=True,
        help='Input CSV file containing GPS coordinates'
    )
    parser.add_argument(
        '--output',
        '-o',
        default='workout_routes.html',
        help='Output HTML file for the map (default: workout_routes.html)'
    )
    parser.add_argument(
        '--sample-rate',
        '-s',
        type=int,
        default=10,
        help='Sample rate for route simplification (default: 10)'
    )
    parser.add_argument(
        '--heatmap-sample',
        type=int,
        default=20,
        help='Sample rate for heatmap data (default: 20)'
    )
    parser.add_argument(
        '--blur',
        '-b',
        type=int,
        default=20,
        help='Blur radius for heatmap (default: 20)'
    )
    parser.add_argument(
        '--radius',
        '-r',
        type=int,
        default=15,
        help='Point radius for heatmap (default: 15)'
    )
    parser.add_argument(
        '--opacity',
        type=float,
        default=0.3,
        help='Minimum opacity for heatmap (default: 0.3)'
    )
    return parser.parse_args()


def simplify_route(route, sample_rate=10):
    """
    Reduce the number of points in a route by sampling.

    Args:
        route (pandas.DataFrame): DataFrame containing route coordinates
        sample_rate (int): Take every nth point

    Returns:
        pandas.DataFrame: Simplified route
    """
    return route.iloc[::sample_rate]


def create_map(args):
    """
    Create an interactive map with workout routes and heatmap overlay.

    Args:
        args: Parsed command line arguments containing visualization parameters
    """
    # Load the data
    print("Loading data...")
    df = pd.read_csv(args.input)

    # Create base map
    print("Creating map...")
    center_lat = df['latitude'].mean()
    center_lon = df['longitude'].mean()
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=12,
        tiles='CartoDB positron'
    )

    # Process individual routes
    unique_files = df['filename'].unique()
    print("Processing routes...")
    for filename in tqdm(unique_files, desc="Processing routes"):
        route = df[df['filename'] == filename]
        route = simplify_route(route, sample_rate=args.sample_rate)

        coordinates = [[row['latitude'], row['longitude']]
                      for _, row in route.iterrows()]

        if len(coordinates) > 1:
            folium.PolyLine(
                coordinates,
                weight=2,
                color='blue',
                opacity=0.6
            ).add_to(m)

    # Create heatmap overlay
    print("Creating heatmap...")
    simplified_df = simplify_route(df, sample_rate=args.heatmap_sample)
    heat_data = simplified_df[['latitude', 'longitude']].values.tolist()
    plugins.HeatMap(
        heat_data,
        min_opacity=args.opacity,
        radius=args.radius,
        blur=args.blur,
    ).add_to(m)

    # Save the map
    print(f"Saving map to {args.output}...")
    m.save(args.output)


def main():
    """Main execution function."""
    args = parse_args()
    create_map(args)
    print(f"Map has been created as '{args.output}'")


if __name__ == "__main__":
    main()
