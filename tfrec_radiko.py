#!/usr/bin/env python3
"""Record time-free Radiko programs.

This module provides functionality for recording time-free Radiko programs
with specified time range.

Author: Hiroyuki NAKAMURA (https://github.com/hry-naka)
Date: May 30, 2023
"""

import subprocess
import sys
import argparse
import os
from dotenv import load_dotenv

from mypkg.radiko_api import RadikoAPIClient
from mypkg.recorder import Recorder

# Load environment variables from .env file
load_dotenv()
AREA_CODE = os.getenv("AREA_CODE", "130")


def get_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Recording time-free Radiko with specified time range."
    )
    parser.add_argument(
        "-s",
        "--station",
        required=True,
        nargs=1,
        help="Recording station ID.",
    )
    parser.add_argument(
        "-ft",
        "--fromtime",
        required=True,
        nargs=1,
        help="Start time (format: YYYYMMDDHHmms)",
    )
    parser.add_argument(
        "prefix",
        metavar="prefix",
        nargs="?",
        help="Prefix name for output file or output directory.",
    )
    return parser.parse_args()



def main() -> None:
    """Main function for time-free Radiko recording.

    Performs time-free Radiko recording for a specified station and
    time range, and embeds metadata.
    """
    args = get_args()
    station = args.station[0]
    fromtime = args.fromtime[0]

    # Format display time from time specification
    display_time = (
        f"{fromtime[0:4]}-{fromtime[4:6]}-{fromtime[6:8]}"
        f"-{fromtime[8:10]}_{fromtime[10:12]}"
    )

    # Determine output directory and file prefix
    if args.prefix is None:
        # No prefix: use current directory, station as prefix
        output_dir = "."
        file_prefix = station
    else:
        # Prefix specified: check if it's a directory or file prefix
        if os.path.isdir(args.prefix):
            # It's a directory
            output_dir = args.prefix
            file_prefix = station
        else:
            # Treat as file prefix (output to current dir with this prefix)
            output_dir = "."
            file_prefix = args.prefix

    # Initialize API client
    api_client = RadikoAPIClient()

    # Check if station is available
    area_id = f"JP{AREA_CODE[:2]}"  # Use AREA_CODE from .env or default to JP13
    if not api_client.is_station_available(station, area_id):
        print(
            f"Error: Specified station '{station}' is not available.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Create output directory if it doesn't exist
    if output_dir != ".":
        os.makedirs(output_dir, exist_ok=True)

    # Initialize recorder
    recorder = Recorder()

    # Check if yt_dlp is available
    if not recorder.is_available("radiko"):
        print(
            "Error: yt_dlp is not installed or not in executable path.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Record time-free playback
    try:
        # Generate output file path
        output_filename = f"{file_prefix}_{display_time}.m4a"
        output_file_path = os.path.join(output_dir, output_filename)

        # Record the stream
        success = recorder.record_radiko_timefree(station, fromtime, output_file_path)

        if success:
            print(f"Successfully recorded: {output_file_path}")

            # Fetch program information and set metadata
            program = api_client.fetch_program(station, fromtime, area_id, now=False)
            if program is not None:
                metadata_success = recorder.set_metadata(output_file_path, program)
                if metadata_success:
                    print(f"Metadata embedded: {program.title}")
                else:
                    print(
                        "Warning: Could not embed metadata",
                        file=sys.stderr,
                    )
            else:
                print(
                    "Warning: Program information not available",
                    file=sys.stderr,
                )
        else:
            print(
                "Error: Recording failed",
                file=sys.stderr,
            )
            sys.exit(1)

    except Exception as e:
        print(f"Error during recording: {e}", file=sys.stderr)
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
