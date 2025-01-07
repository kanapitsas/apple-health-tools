#!/usr/bin/env python3
"""
Apple Health Data Export Utility

This script processes Apple Health XML export files and converts specific health metrics
to CSV format for further analysis. It can list all available metrics in the export
and convert any specific metric to a CSV file.

Typical usage:
    # List all available metrics
    python health_export.py --list

    # Export heart rate data
    python health_export.py --type HKQuantityTypeIdentifierHeartRate --output heartrate.csv

    # Export steps with default output filename
    python health_export.py --type HKQuantityTypeIdentifierStepCount
"""

import xml.etree.ElementTree as ET
import csv
from datetime import datetime
import argparse
import sys
from pathlib import Path
from typing import Optional, Set, List, Dict
from tqdm import tqdm
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HealthDataExporter:
    """Handles the export of Apple Health data from XML to CSV format."""

    def __init__(self, xml_path: Path):
        """
        Initialize the exporter with the path to the Apple Health export XML.

        Args:
            xml_path: Path to the export.xml file
        """
        self.xml_path = xml_path
        self._tree = None
        self._root = None

    def _load_xml(self) -> None:
        """Load the XML file if not already loaded."""
        if self._root is None:
            logger.info(f"Loading XML file: {self.xml_path}")
            self._tree = ET.parse(self.xml_path)
            self._root = self._tree.getroot()

    def get_available_types(self) -> Set[str]:
        """
        Get all unique record types in the export file.

        Returns:
            Set of all record types found in the export
        """
        self._load_xml()
        return set(record.get('type') for record in self._root.findall('.//Record'))

    def _get_metadata_keys(self, records: List[ET.Element]) -> Set[str]:
        """
        Find all possible metadata keys in all records.

        Args:
            records: List of XML Record elements

        Returns:
            Set of metadata keys found
        """
        metadata_keys = set()
        # First pass: collect all possible metadata keys
        logger.debug("Collecting all metadata keys...")
        for record in records:
            metadata = record.findall('./MetadataEntry')
            metadata_keys.update(entry.get('key') for entry in metadata)
        logger.debug(f"Found metadata keys: {metadata_keys}")
        return metadata_keys

    def export_record_type(self, record_type: str, output_path: Optional[Path] = None) -> None:
        """
        Export records of a specific type to CSV.

        Args:
            record_type: The type of health record to export
            output_path: Optional path for output CSV file. If None, creates based on record type
        """
        self._load_xml()

        # Create default output path if none provided
        if output_path is None:
            output_path = Path(f"{record_type.replace('HKQuantityTypeIdentifier', '')}.csv")

        # Find all matching records
        records = self._root.findall(f'.//Record[@type="{record_type}"]')

        if not records:
            logger.warning(f"No records found for type: {record_type}")
            return

        record_count = len(records)
        logger.info(f"Found {record_count:,} records")

        # Determine all possible metadata keys
        metadata_keys = self._get_metadata_keys(records)
        logger.info(f"Found {len(metadata_keys)} metadata keys")

        # Prepare headers
        headers = ['startDate', 'value', 'unit', 'sourceName']
        if metadata_keys:
            headers.extend(sorted(metadata_keys))

        try:
            with output_path.open('w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()

                for record in tqdm(records, total=record_count, desc="Processing records"):
                    row = {
                        'startDate': record.get('startDate'),
                        'value': record.get('value'),
                        'unit': record.get('unit'),
                        'sourceName': record.get('sourceName')
                    }

                    # Add metadata if present
                    metadata = record.findall('./MetadataEntry')
                    for entry in metadata:
                        row[entry.get('key')] = entry.get('value')

                    writer.writerow(row)

            logger.info(f"Data successfully written to {output_path}")
            logger.info(f"Total records processed: {record_count:,}")

        except IOError as e:
            logger.error(f"Error writing to file {output_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during export: {e}")
            raise


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Convert Apple Health Export data to CSV format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        '--input',
        type=Path,
        default=Path('apple_health_export/export.xml'),
        help='Path to the Apple Health export.xml file'
    )

    parser.add_argument(
        '--list',
        action='store_true',
        help='List all available record types in the export file'
    )

    parser.add_argument(
        '--type',
        type=str,
        help='Type of health record to export (e.g., HKQuantityTypeIdentifierHeartRate)'
    )

    parser.add_argument(
        '--output',
        type=Path,
        help='Output CSV file path (optional, will generate based on type if not provided)'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )

    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)

    # Verify input file exists
    if not args.input.exists():
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)

    exporter = HealthDataExporter(args.input)

    if args.list:
        # List all available types
        types = exporter.get_available_types()
        print("\nAvailable record types:")
        for t in sorted(types):
            print(f"- {t}")
    elif args.type:
        # Export specific type
        exporter.export_record_type(args.type, args.output)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
