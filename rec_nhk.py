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
    parser = argparse.ArgumentParser(description="Recording NHK radio.")
    parser.add_argument("channel", metavar="channel", help="Channel Name")
    parser.add_argument(
        "duration",
        metavar="duration",
        type=float,
        help="Duration(minutes)",
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
        print(f"Error: Invalid channel '{channel}'. Valid channels are: {list(NHK_STREAM_CODES.keys())}")
        sys.exit(1)
    duration = int(args.duration * 60)
    outdir = args.outputdir
    prefix = args.prefix if args.prefix else channel
    target_time = DT.now().astimezone() + timedelta(seconds=duration / 2)
    recorder = Recorder()
    api_client = NhkAPIClient(NHK_API_KEY, LOCATION, AREA_CODE, code, API_VERSION)

    # Get program information
    program = api_client.fetch_program(target_time)
    if program is None:
        print("Error: No program information available")

    # Perform recording
    date = DT.now().strftime("%Y-%m-%d-%H_%M")
    output = f"{outdir}/{prefix}_{date}.m4a"
    success = recorder.record_nhk_live(api_client, duration, output, prefix, date)
    if not success:
        print("Error: Recording failed")
        sys.exit(1)

    # retry after recording
    if program is None:
        print("Retry getting program info.")
        program = api_client.fetch_program(target_time)
    else:
        print("Retry skipped.")

    # Set metadata
    try:
        recorder.set_metadata(output,program)
    except Exception as e:
        print(f"Warning: Failed to set MP4 metadata: {e}")

    print(f"Successfully recorded: {output}")
    sys.exit(0)

if __name__ == "__main__":
    main()
