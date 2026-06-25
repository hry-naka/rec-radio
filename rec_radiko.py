#!/usr/bin/env python3
"""Radiko live radio recording application.

This module orchestrates the complete recording workflow:
1. Parse command-line arguments
2. Authenticate with Radiko API
3. Retrieve program and stream information
4. Record audio stream using ffmpeg
5. Set metadata tags in output MP4 file

Author: Hiroyuki NAKAMURA (https://github.com/hry-naka)
Date: May 25, 2023
"""

import argparse
import sys
from datetime import datetime as DT
import os

from mypkg.program_formatter import ProgramFormatter
from mypkg.radiko_api import RadikoAPIClient
from mypkg.recorder import Recorder

def get_args() -> argparse.Namespace:
    """Parse command-line arguments for Radiko recording.

    Returns:
        Parsed command-line arguments namespace
    """
    parser = argparse.ArgumentParser(description="Recording Radiko.")
    parser.add_argument("channel", metavar="channel", help="Channel Name")
    parser.add_argument(
        "duration",
        metavar="duration",
        type=float,
        help="Duration (minutes)",
    )
    parser.add_argument(
        "outputdir",
        metavar="outputdir",
        nargs="?",
        default=".",
        help="Output path default:'.'",
    )
    parser.add_argument(
        "prefix",
        metavar="Prefix name",
        nargs="?",
        help="Prefix name for output file.",
    )
    return parser.parse_args()


def main() -> None:
    """Main function for Radiko recording.

    Orchestrates the recording workflow: argument parsing, API auth,
    stream retrieval, recording, and metadata tagging.
    """
    # Parse command-line arguments
    args = get_args()
    channel = args.channel
    duration = int(args.duration * 60)
    outdir = args.outputdir
    prefix = args.prefix if args.prefix else channel

    # Generate timestamps for filename and API query
    date = DT.now().strftime("%Y-%m-%d-%H_%M")
    fromtime = DT.now().strftime("%Y%m%d%H%M00")
    print(f"Recording start time: {fromtime}")

    # Initialize Radiko API client and recorder
    api_client = RadikoAPIClient()
    recorder = Recorder()

    # Validate channel availability
    area_id = api_client.get_current_area_id()
    if not api_client.is_station_available(channel, area_id):
        print(f"Error: Specified station '{channel}' is not found.")
        sys.exit(1)

    # Fetch program information
    program = api_client.fetch_program(channel, fromtime, area_id, now=True)
    if program is None:
        print("Warning: Program information not available")
        program_info = "(Unknown)"
    else:
        program_info = ProgramFormatter.get_log_string(program)

    print(f"Program: {program_info}")

    # Generate output filename
    output_file = f"{outdir}/{ProgramFormatter.generate_filename(
        program if program else None, prefix, date
    )}"

    # Perform recording
    print(f"Recording {channel} for {duration} seconds " f"to {output_file}")
    success = recorder.record_radiko_live(channel, duration, output_file)

    if not success:
        print("Error: Recording failed")
        sys.exit(1)
    else:
        print("Recording completed successfully")

        # Set MP4 metadata if program information is available
        if program is not None:
            print("Setting metadata...")
            if recorder.set_metadata(output_file, program):
                print("Metadata set successfully")
            else:
                print("Warning: Failed to set metadata")
        else:
            print("Skipping metadata (program info not available)")

    print(f"Output file: {output_file}")
    sys.exit(0)


if __name__ == "__main__":
    main()
