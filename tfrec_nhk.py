#!/usr/bin/env python3
"""rec_nhk.py - NHK radio recording module.

This module provides functionalities for recording NHK radio.

Author: Hiroyuki NAKAMURA (https://github.com/hry-naka)
Date: May 25, 2023
"""

import argparse
import os
import sys
from datetime import datetime as DT, timedelta

from dotenv import load_dotenv
from mypkg.recorder import Recorder
from mypkg.nhk_api import NhkAPIClient

# Load environment variables from .env file
load_dotenv()

# Constants - API Configuration
NHK_API_KEY = os.getenv("NHK_API_KEY")
if not NHK_API_KEY:
    print("Error: NHK_API_KEY not found in environment. " "Please set it in .env file.")
    sys.exit(1)

API_VERSION = os.getenv("API_VERSION", "v3")
LOCATION = os.getenv("LOCATION", "tokyo")
AREA_CODE = os.getenv("AREA_CODE", "130")

NHK_STREAM_CODES = {
    "NHK1": "r1",
    "NHK2": "r2",
    "FM": "r3",
}

HTTP_TIMEOUT = (20, 5)
REQUEST_TIMEOUT = 20


def get_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Recording timefree NHK radio.")
    parser.add_argument(
        "channel",
        metavar="channel",
        help="Channel Name for tagging olny. (NHK1, NHK2, FM)",
    )
    parser.add_argument(
        "url",
        metavar="url",
        help="URL of the program to record",
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
    """Main function for NHK radio recording."""
    args = get_args()
    channel = args.channel
    code = NHK_STREAM_CODES.get(channel)
    if code is None:
        print(
            f"Error: Invalid channel '{channel}'. Valid channels are: {list(NHK_STREAM_CODES.keys())}"
        )
        sys.exit(1)
    import validators

    if validators.url(args.url) is not True:
        print(f"Error: Invalid URL '{args.url}'. Please provide a valid URL.")
        sys.exit(1)
    outdir = args.outputdir
    prefix = args.prefix if args.prefix else channel

    recorder = Recorder()
    api_client = NhkAPIClient(NHK_API_KEY, LOCATION, AREA_CODE, code, API_VERSION)

    # Get program information
    program = api_client.fetch_program_via_ytdlp(args.url)
    if program is None:
        print("Error: No program information available")
        sys.exit(1)

    # Perform recording
    dt = DT.strptime(program.start_time, "%Y%m%d%H%M%S")
    date = dt.strftime("%Y-%m-%d-%H_%M")
    output = f"{outdir}/{prefix}_{date}.m4a"
    success = recorder.record_nhk_timefree(args.url, output)
    if not success:
        print("Error: Recording failed")
        sys.exit(1)

    # Set metadata
    try:
        recorder.set_metadata(output, program)
    except Exception as e:
        print(f"Warning: Failed to set MP4 metadata: {e}")

    print(f"Successfully recorded: {output}")
    sys.exit(0)


if __name__ == "__main__":
    main()
