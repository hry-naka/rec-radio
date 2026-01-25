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


def get_stream_url_for_timefree(
    api: RadikoApi,
    station: str,
    start_time: str,
    end_time: str,
) -> Optional[Tuple[str, str]]:
    """Get time-free stream URL and auth token from Radiko API.

    Args:
        api: RadikoApi instance
        station: Station ID
        start_time: Start time in yyyymmddhhmmss format
        end_time: End time in yyyymmddhhmmss format

    Returns:
        Tuple of (stream_url, auth_token) or None if failed.

    Raises:
        Exception: If authorization or stream URL retrieval fails.
    """
    # Authorize and get token
    auth_result = api.authorize()
    if auth_result is None:
        raise RuntimeError("Authorization failed")

    auth_token, area_id = auth_result

    # Build time-free stream URL
    # Format: https://radiko.jp/v2/api/ts/playlist.m3u8?station_id=<station>&l=15&ft=<from>&to=<to>
    stream_url = (
        f"https://radiko.jp/v2/api/ts/playlist.m3u8?"
        f"station_id={station}&l=15&ft={start_time}&to={end_time}"
    )

    return (stream_url, auth_token)


def record_with_ffmpeg(
    stream_url: str,
    output_file: str,
    duration_seconds: int,
    auth_token: Optional[str] = None,
) -> bool:
    """Record stream using ffmpeg.

    Args:
        stream_url: M3U8 stream URL
        output_file: Output file path
        duration_seconds: Recording duration in seconds
        auth_token: Optional authentication token for Radiko time-free

    Returns:
        True if recording succeeded, False otherwise.
    """
    # Determine ffmpeg path
    if os.path.exists("/usr/local/bin/ffmpeg"):
        ffmpeg_cmd = "/usr/local/bin/ffmpeg"
    elif os.path.exists("/usr/bin/ffmpeg"):
        ffmpeg_cmd = "/usr/bin/ffmpeg"
    else:
        ffmpeg_cmd = "ffmpeg"

    cmd = [
        ffmpeg_cmd,
        "-loglevel",
        "error",
    ]

    # Add authentication headers if token is provided
    if auth_token:
        cmd.extend(
            [
                "-headers",
                f"X-Radiko-AuthToken: {auth_token}",
            ]
        )

    cmd.extend(
        [
            "-i",
            stream_url,
            "-t",
            str(duration_seconds),
            "-acodec",
            "copy",
            "-vn",
            output_file,
        ]
    )

    # Print ffmpeg command
    print(f"ffmpeg command: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"ffmpeg error: {e.stderr.decode('utf-8')}", file=sys.stderr)
        return False
    except FileNotFoundError:
        print(f"Error: ffmpeg not found at {ffmpeg_cmd}", file=sys.stderr)
        return False


def record_program(program: Program) -> bool:
    """Record a time-free Radiko program using Program instance.

    This function is designed for future integration with recorder_radiko.py.

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
    area_id = os.getenv("RADIKO_AREA_ID", "JP13")

    # Initialize API
    api = RadikoApi()

    # Get stream URL and auth token
    try:
        result = get_stream_url_for_timefree(
            api,
            program.station,
            program.start_time,
            program.end_time,
        )
        if not result:
            print("Error: Failed to get stream URL", file=sys.stderr)
            return False
        stream_url, auth_token = result
    except Exception as e:
        print(f"Error getting stream URL: {e}", file=sys.stderr)
        return False

    # Generate output filename
    output_file = generate_output_filename(
        program.station,
        program.start_time,
        program.end_time,
    )

    # Calculate duration
    try:
        start_dt = datetime.strptime(program.start_time, "%Y%m%d%H%M%S")
        end_dt = datetime.strptime(program.end_time, "%Y%m%d%H%M%S")
        duration_seconds = int((end_dt - start_dt).total_seconds())
    except ValueError as e:
        print(f"Error calculating duration: {e}", file=sys.stderr)
        return False

    # Record
    print(f"Recording {program.station}: {program.title}")
    print(f"Output: {output_file}")

    success = record_with_ffmpeg(stream_url, output_file, duration_seconds, auth_token)

    if success:
        print(f"Successfully recorded: {output_file}")
    else:
        print("Recording failed", file=sys.stderr)

    return success


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
    area_id = os.getenv("RADIKO_AREA_ID", "JP13")

    # Initialize API
    api = RadikoApi()

    # Check station availability
    try:
        if not api.is_station_available(station, area_id):
            print(
                f"Error: Station '{station}' is not available in area {area_id}",
                file=sys.stderr,
            )
            sys.exit(1)
    except Exception as e:
        print(f"Warning: Could not verify station availability: {e}", file=sys.stderr)

    # Fetch program information
    try:
        program = api.fetch_today_program(station, start_time, area_id)
        if program is None:
            print("Warning: Program information not available")
            program_info = "(Unknown)"
        else:
            program_info = ProgramFormatter.get_log_string(program)
        print(f"Program: {program_info}")
    except Exception as e:
        print(f"Warning: Could not fetch program info: {e}", file=sys.stderr)
        program = None
        program_info = "(Unknown)"

    # Get stream URL and auth token
    try:
        result = get_stream_url_for_timefree(
            api,
            station,
            start_time,
            end_time,
        )
        if not result:
            print("Error: Failed to get stream URL", file=sys.stderr)
            sys.exit(1)
        stream_url, auth_token = result
    except Exception as e:
        print(f"Error getting stream URL: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Stream URL: {stream_url}")

    # Generate output filename
    output_file = generate_output_filename(station, start_time, end_time)

    # Calculate duration
    try:
        start_dt = datetime.strptime(start_time, "%Y%m%d%H%M%S")
        end_dt = datetime.strptime(end_time, "%Y%m%d%H%M%S")
        duration_seconds = int((end_dt - start_dt).total_seconds())
    except ValueError as e:
        print(f"Error calculating duration: {e}", file=sys.stderr)
        sys.exit(1)

    # Record
    print(f"Recording {station} from {start_time} to {end_time}")
    print(f"Output: {output_file}")
    print(f"Duration: {duration_seconds} seconds")

    success = record_with_ffmpeg(stream_url, output_file, duration_seconds, auth_token)

    if success:
        print(f"Recording completed successfully")

        # Set metadata if program information is available
        if program is not None:
            try:
                recorder = RecorderRadiko()
                recorder.set_metadata(output_file, program)
                print("Metadata set successfully")
            except Exception as e:
                print(f"Warning: Failed to set metadata: {e}", file=sys.stderr)
        else:
            print("Skipping metadata (program info not available)")

        print(f"Output file: {output_file}")
        sys.exit(0)
    else:
        print("Recording failed", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
