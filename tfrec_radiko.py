#!/usr/bin/env python3
"""Record time-free Radiko programs.

This module provides functionality for recording time-free (タイムフリー) Radiko programs
with specified time range. Supports both CLI usage and Program-based invocation.

Filename format: <station>_<yyyymmdd>_<hhmmss>-<hhmmss>.m4a
Command format: tfrec_radiko.py -s <station> -ft <from_yyyymmddhhmmss> -to <to_yyyymmddhhmmss>

Author: Hiroyuki NAKAMURA (https://github.com/hry-naka)
Date: May 30, 2023
"""
import argparse
import os
import subprocess
import sys
from datetime import datetime
from typing import Optional, Tuple

from dotenv import load_dotenv

from mypkg.program import Program
from mypkg.program_formatter import ProgramFormatter
from mypkg.radiko_api import RadikoApi
from mypkg.recorder_radiko import RecorderRadiko


def get_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments namespace with station, from_time, and to_time.
    """
    parser = argparse.ArgumentParser(
        description="Record time-free Radiko programs with specified time range."
    )
    parser.add_argument(
        "-s",
        "--station",
        required=True,
        help="Station ID (e.g., TBS, INT, FMT)",
    )
    parser.add_argument(
        "-ft",
        "--from",
        dest="from_time",
        required=True,
        help="Start time in yyyymmddhhmmss format (e.g., 20260125093000)",
    )
    parser.add_argument(
        "-to",
        "--to",
        dest="to_time",
        required=True,
        help="End time in yyyymmddhhmmss format (e.g., 20260125100000)",
    )
    return parser.parse_args()


def validate_datetime_format(time_str: str) -> bool:
    """Validate datetime string format (yyyymmddhhmmss).

    Args:
        time_str: Datetime string to validate.

    Returns:
        True if format is valid, False otherwise.
    """
    if len(time_str) != 14:
        return False
    try:
        datetime.strptime(time_str, "%Y%m%d%H%M%S")
        return True
    except ValueError:
        return False


def generate_output_filename(
    station: str,
    start_time: str,
    end_time: str,
) -> str:
    """Generate output filename for time-free recording.

    Format: <station>_<YYYY-MM-DD-HH_MM>.mp4 (same as rec_radiko.py and rec_nhk.py)

    Args:
        station: Station ID (e.g., TBS, INT)
        start_time: Start time in yyyymmddhhmmss format
        end_time: End time in yyyymmddhhmmss format (not used, kept for compatibility)

    Returns:
        Generated filename with .mp4 extension.

    Example:
        >>> generate_output_filename("TBS", "20260125093000", "20260125100000")
        'TBS_2026-01-25-09_30.mp4'
    """
    # Format: YYYY-MM-DD-HH_MM
    date_str = f"{start_time[0:4]}-{start_time[4:6]}-{start_time[6:8]}-{start_time[8:10]}_{start_time[10:12]}"
    return f"{station}_{date_str}.mp4"


def record_program(program: Program) -> bool:
    """Record a time-free Radiko program using Program instance.

    This function is designed for integration with recorder_radiko.py.

    Args:
        program: Program instance with station, start_time, and end_time.

    Returns:
        True if recording succeeded, False otherwise.

    Raises:
        ValueError: If program is not from Radiko or missing required fields.
    """
    if program.source != "radiko":
        raise ValueError(f"Program source must be 'radiko', got '{program.source}'")

    if not program.station or not program.start_time or not program.end_time:
        raise ValueError("Program must have station, start_time, and end_time")

    # Validate time format
    if not validate_datetime_format(program.start_time):
        raise ValueError(f"Invalid start_time format: {program.start_time}")
    if not validate_datetime_format(program.end_time):
        raise ValueError(f"Invalid end_time format: {program.end_time}")

    # Load environment
    load_dotenv()

    # Initialize API and Recorder
    api = RadikoApi()
    recorder = RecorderRadiko()

    # Get auth token and stream URL for time-free
    try:
        auth_result = api.authorize()
        if auth_result is None:
            print("Error: Radiko authorization failed")
            return False

        auth_token, area_id = auth_result
        print(f"Authorization successful. Area ID: {area_id}")

        # Build time-free stream URL
        stream_url = (
            f"https://radiko.jp/v2/api/ts/playlist.m3u8?"
            f"station_id={program.station}&l=15&ft={program.start_time}&to={program.end_time}"
        )

        # Set stream URL in program
        program.stream_url = stream_url

        # Generate output filename
        output_file = generate_output_filename(
            program.station,
            program.start_time,
            program.end_time,
        )

        # Use recorder's record_program method
        print(f"Recording to: {output_file}")
        success = recorder.record_program(program, auth_token, output_file)

        if success:
            print(f"Recording completed successfully: {output_file}")
        else:
            print("Recording failed")

        return success

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return False


def main() -> None:
    """Main function for CLI execution.

    Parses command-line arguments and records time-free Radiko program.
    """
    args = get_args()

    station = args.station
    start_time = args.from_time
    end_time = args.to_time

    # Validate datetime format
    if not validate_datetime_format(start_time):
        print(
            f"Error: Invalid start time format: {start_time}. "
            f"Expected yyyymmddhhmmss format.",
            file=sys.stderr,
        )
        sys.exit(1)

    if not validate_datetime_format(end_time):
        print(
            f"Error: Invalid end time format: {end_time}. "
            f"Expected yyyymmddhhmmss format.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Load environment
    load_dotenv()

    # Initialize API to fetch program information
    api = RadikoApi()

    # Try to fetch detailed program information
    print(f"Fetching program information for {station}...")
    try:
        # Fetch program information for the specified time
        program = api.fetch_today_program(station, start_time)
        
        if program is not None:
            program_info = ProgramFormatter.get_log_string(program)
            print(f"Program: {program_info}")
            
            # Update program times to match user-specified range
            # (User may want to record a portion of the program)
            program.start_time = start_time
            program.end_time = end_time
        else:
            print("Warning: Program information not available, using minimal metadata")
            # Create Program with minimal information if API fetch fails
            program = Program(
                title=f"{station} Timefree Recording",
                station=station,
                start_time=start_time,
                end_time=end_time,
                source="radiko",
            )
    except Exception as e:
        print(f"Warning: Could not fetch program info: {e}")
        # Fallback to minimal Program instance
        program = Program(
            title=f"{station} Timefree Recording",
            station=station,
            start_time=start_time,
            end_time=end_time,
            source="radiko",
        )

    # Record program
    success = record_program(program)

    if success:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
