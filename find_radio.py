#!/usr/bin/env python3
# coding: utf-8
"""Unified program search CLI for NHK and Radiko radio services.

This module provides a unified command-line interface to search for radio programs
from both NHK and Radiko services. It supports filtering by station, area, and
keyword patterns.
"""

import argparse
import os
import re
import sys
from typing import List, Optional

from dotenv import load_dotenv

from mypkg.nhk_api import NHKApi
from mypkg.program import Program
from mypkg.program_formatter import ProgramFormatter
from mypkg.radiko_api import RadikoApi
from mypkg.recorder_nhk import RecorderNHK
from mypkg.recorder_radiko import RecorderRadiko


def get_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Search for radio programs in NHK or Radiko services."
    )
    parser.add_argument(
        "--service",
        required=True,
        choices=["radiko", "nhk"],
        help="Radio service to search (radiko or nhk)",
    )
    parser.add_argument(
        "--station",
        default=None,
        help="Station ID (e.g., TBS, INT for Radiko; optional)",
    )
    parser.add_argument(
        "--area",
        default=None,
        help="Area ID (e.g., JP13 for Tokyo; optional)",
    )
    parser.add_argument(
        "--keyword",
        default=None,
        help="Keyword to search for (supports regex pattern)",
    )
    return parser.parse_args()


def get_area_id(service: str, explicit_area: Optional[str]) -> str:
    """Determine area ID from arguments or environment."""
    if explicit_area:
        return explicit_area

    load_dotenv()

    if service == "radiko":
        return os.getenv("RADIKO_AREA_ID", "JP13")
    else:  # nhk
        return os.getenv("NHK_AREA_ID", "JP13")


def filter_programs_by_keyword(
    programs: List[Program],
    keyword: str,
) -> List[Program]:
    """Filter programs by keyword using regex pattern (case-insensitive).

    Searches only in program title for consistency across NHK and Radiko.

    Args:
        programs: List of Program instances
        keyword: Regex pattern to match (supports Japanese characters)

    Returns:
        Filtered list of programs

    Raises:
        SystemExit: If regex pattern is invalid
    """
    if not keyword:
        return programs

    try:
        pattern = re.compile(keyword, re.IGNORECASE | re.UNICODE)
    except re.error as e:
        print(f"Invalid regex pattern: {e}", file=sys.stderr)
        sys.exit(1)  # ← 追加

    filtered = []
    for program in programs:
        # Search only in title for consistency across both services
        if pattern.search(program.title or ""):
            filtered.append(program)

    return filtered


def main() -> None:
    """Main function for program search."""
    args = get_args()

    # Determine area ID
    area_id = get_area_id(args.service, args.area)

    # Display search parameters
    print(f"Searching {args.service.upper()} programs...")
    print(f"Area: {area_id}")
    if args.station:
        print(f"Station: {args.station}")
    if args.keyword:
        print(f"Keyword: {args.keyword}")
    print()

    try:
        # Fetch programs from API
        if args.service == "radiko":
            api = RadikoApi()
            programs = api.get_programs(area_id, args.station)
        else:  # nhk
            api = NHKApi()
            nhk_programs = api.get_programs()

            # Filter NHK programs by keyword
            if args.keyword:
                filtered_nhk = filter_programs_by_keyword(nhk_programs, args.keyword)

                if filtered_nhk:
                    print(f"[Total programs found: {len(nhk_programs)}]")
                    print(
                        f"[Programs matched keyword '{args.keyword}': {len(filtered_nhk)}]"
                    )
                    print()

                    # Enrich matched programs with detailed episode information
                    programs = []
                    for program in filtered_nhk:
                        enriched = api.enrich_program_details(program)
                        programs.append(enriched)
                else:
                    programs = []
            else:
                programs = nhk_programs

        if not programs:
            print("No programs found.")
            sys.exit(0)

        if args.service == "radiko":
            print(f"[Total programs found: {len(programs)}]")

            # Filter by keyword if provided
            if args.keyword:
                filtered_programs = filter_programs_by_keyword(programs, args.keyword)
                matched_count = len(filtered_programs)
                print(f"[Programs matched keyword '{args.keyword}': {matched_count}]")
                print()
                programs = filtered_programs
            else:
                print()

        if not programs:
            print("No programs matched the keyword.")
            sys.exit(0)

        # Initialize recorders for command generation
        recorder_radiko = RecorderRadiko() if args.service == "radiko" else None
        recorder_nhk = RecorderNHK() if args.service == "nhk" else None

        # Display results with recorder-generated commands
        output = ProgramFormatter.format_list(
            programs,
            recorder_radiko=recorder_radiko,
            recorder_nhk=recorder_nhk,
        )
        print(output)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
