#!/usr/bin/env python3
# coding: utf-8
"""Find keyword in Radiko program listings.

This module searches for programs matching a keyword using the Radiko API.
"""
import argparse
import re
import sys

from mypkg.radiko_api import RadikoAPIClient


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
    parser.add_argument(
        "-a",
        "--area_id",
        required=False,
        nargs=1,
        help=(
            "Area ID for Radiko program search (e.g., 'JP13' for "
            "Tokyo/Japan). If omitted, area ID will be auto-retrieved."
        ),
    )
    return parser.parse_args()


def main() -> None:
    """Main function for program search."""
    args = get_args()
    client = RadikoAPIClient()
    keyword = args.keyword[0]

    # Determine area ID
    if args.area_id is None:
        # Authorize to get area ID
        auth_result = client.authorize()
        if auth_result is None:
            print("Error: Could not resolve area ID. Use -a option.")
            sys.exit(1)
        _, area_id = auth_result
    else:
        area_id = args.area_id[0]

    # Search for programs
    print(f"Searching for programs with keyword: '{keyword}'")
    print(f"Area ID: {area_id}")
    print()

    results = client.search_programs(keyword=keyword, area_id=area_id)

    # Display results
    if not results or "data" not in results:
        print("No programs found.")
        sys.exit(0)

    for data in results["data"]:
        title = data.get("title", "Unknown")
        station_id = data.get("station_id", "")
        start_time = re.sub(r"[-: ]", "", data.get("start_time", ""))
        end_time = re.sub(r"[-: ]", "", data.get("end_time", ""))

        print(
            f"Title: {title}\t"
            f"-s {station_id} "
            f"-ft {start_time} "
            f"-to {end_time}"
        )


if __name__ == "__main__":
    main()
