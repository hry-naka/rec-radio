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

    # Validate recorder is available
    if not recorder.is_available():
        print("Error: ffmpeg is not available")
        sys.exit(1)

    # Validate channel availability
    if not api_client.is_station_available(channel):
        print(f"Error: Specified station '{channel}' is not found.")
        sys.exit(1)

    # Authorize and get authentication token and area ID
    auth_result = api_client.authorize()
    if auth_result is None:
        print("Error: Authorization failed")
        sys.exit(1)

    auth_token, area_id = auth_result
    print(f"Authorization successful. Area ID: {area_id}")

    # Retrieve stream URL
    stream_url = api_client.get_stream_url(channel, auth_token)
    if stream_url is None:
        print("Error: Failed to retrieve stream URL")
        sys.exit(1)

    print(f"Stream URL: {stream_url}")

    # Fetch program information
    program = api_client.fetch_program(channel, fromtime, None, area_id, now=True)
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
    success = recorder.record_stream(stream_url, auth_token, output_file, duration)

    if not success:
        print("Error: Recording failed")
        sys.exit(1)

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
