#!/usr/bin/env python3
# coding: utf-8
"""Find keyword in Radiko program listings.

This module searches for programs matching a keyword using the Radiko API.
"""

import argparse
import sys
import os

from mypkg.radiko_api import RadikoAPIClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
AREA_CODE = os.getenv("AREA_CODE", "130")


def get_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(description="Find keyword in Radiko program.")
    parser.add_argument(
        "-k",
        "--keyword",
        required=True,
        nargs=1,
        help="Keyword to search for in Radiko programs.",
    )

    return parser.parse_args()


def main() -> None:
    """Main function for program search."""
    args = get_args()
    client = RadikoAPIClient()
    keyword = args.keyword[0]

    # Determine area ID
    area_id = f"JP{AREA_CODE[:2]}"  # Use AREA_CODE from .env or default to JP13

    # Search for programs
    print(f"Searching for programs with keyword: '{keyword}'")
    print(f"Area ID: {area_id}")
    print()

    results = client.search_past_week(keyword=keyword, area_id=area_id)

    # Display results
    if not results:
        print("No programs found.")
        sys.exit(0)

    for r in results:
        print(f"{r.title} \t: python ./tfrec_radiko.py -s {r.station} -ft {r.start_time}")


if __name__ == "__main__":
    main()
