#!/usr/bin/env python3
"""Record time-free Radiko programs.

This module provides functionality for recording time-free Radiko programs
with specified time range.

Author: Hiroyuki NAKAMURA (https://github.com/hry-naka)
Date: May 30, 2023
"""
import sys
import argparse
import os
from datetime import datetime as DT
from mypkg.radiko_api import RadikoAPIClient
from mypkg.recorder import Recorder
from mypkg.program import Program


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
        "-to",
        "--totime",
        required=True,
        nargs=1,
        help="End time (format: YYYYMMDDHHmms)",
    )
    parser.add_argument(
        "prefix",
        metavar="prefix",
        nargs="?",
        help="Prefix name for output file or output directory.",
    )
    return parser.parse_args()


def fetch_program_info(
    api_client: RadikoAPIClient,
    station: str,
    fromtime: str,
) -> Program:
    """Fetch program information from Radiko API.

    Args:
        api_client: RadikoAPIClient instance
        station: Station ID
        fromtime: Start time (YYYYMMDDHHmmss format)

    Returns:
        Program object with program information or None if not found
    """
    try:
        # Use fromtime to search in weekly program schedule
        # fromtime is in format: YYYYMMDDHHmmss
        program = api_client.fetch_weekly_program(
            station=station,
            from_time=fromtime,
        )

        return program

    except Exception as e:
        print(
            f"Warning: Could not fetch program info: {e}",
            file=sys.stderr,
        )
        return None


def main() -> None:
    """Main function for time-free Radiko recording.

    Performs time-free Radiko recording for a specified station and
    time range, and embeds metadata.
    """
    args = get_args()
    station = args.station[0]
    fromtime = args.fromtime[0]
    totime = args.totime[0]

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
    if not api_client.is_station_available(station):
        print(
            f"Error: Specified station '{station}' is not available.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Authorize and get token
    try:
        auth_result = api_client.authorize()
        if auth_result is None:
            raise RuntimeError("Authorization failed")
        auth_token, _ = auth_result
    except Exception as e:
        print(f"Error during authorization: {e}", file=sys.stderr)
        sys.exit(1)

    # Create output directory if it doesn't exist
    if output_dir != ".":
        os.makedirs(output_dir, exist_ok=True)

    # Initialize recorder
    recorder = Recorder()

    # Check if ffmpeg is available
    if not recorder.is_available():
        print(
            "Error: ffmpeg is not installed or not in executable path.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Get stream URL for time-free playback
    try:
        stream_url = (
            f"https://radiko.jp/v2/api/ts/playlist.m3u8?"
            f"station_id={station}&l=15&ft={fromtime}&to={totime}"
        )

        # Calculate recording duration in seconds
        from_dt = DT.strptime(fromtime, "%Y%m%d%H%M%S")
        to_dt = DT.strptime(totime, "%Y%m%d%H%M%S")
        duration_seconds = int((to_dt - from_dt).total_seconds())

        # Generate output file path
        output_filename = f"{file_prefix}_{display_time}.mp4"
        output_file_path = os.path.join(output_dir, output_filename)

        # Record the stream
        success = recorder.record_stream(
            stream_url=stream_url,
            auth_token=auth_token,
            output_file=output_file_path,
            duration=duration_seconds,
        )

        if success:
            print(f"Successfully recorded: {output_file_path}")

            # Fetch program information and set metadata
            program = fetch_program_info(api_client, station, fromtime)
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
