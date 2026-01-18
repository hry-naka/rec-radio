#!/usr/bin/env python3
"""Radiko live radio recording module.

This module provides functionalities for recording live radio from Radiko,
including authentication, stream retrieval, and metadata management.

Author: Hiroyuki NAKAMURA (https://github.com/hry-naka)
Date: May 25, 2023
"""
import argparse
import re
import shlex
import shutil
import subprocess
import sys
import time
from datetime import datetime as DT
from typing import Optional, Tuple

import requests
from mutagen.mp4 import MP4, MP4Cover

from mypkg.radiko_api import Radikoapi


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


def get_streamurl(channel: str, authtoken: str) -> str:
    """Retrieve M3U8 stream URL from Radiko API.

    Args:
        channel: Channel ID
        authtoken: Authentication token from Radiko API

    Returns:
        M3U8 stream URL

    Raises:
        SystemExit: If stream URL cannot be retrieved
    """
    url = f"https://f-radiko.smartstream.ne.jp/{channel}"
    url += "/_definst_/simul-stream.stream/playlist.m3u8"
    headers = {
        "X-Radiko-AuthToken": authtoken,
    }
    res = requests.get(url, headers=headers, timeout=(20, 5))
    res.encoding = "utf-8"
    if res.status_code == 200:
        body = res.text
        # Extract M3U8 URL from response body
        lines = re.findall("^https?://.+m3u8$", body, flags=re.MULTILINE)
        if len(lines) > 0:
            return lines[0]
        print("Radiko: no m3u8 in the response.")
        sys.exit(1)
    else:
        print(res.text)
        print(f"Radiko: error {res.status_code} encountered.")
        sys.exit(1)


def live_rec(
    url_parts: str,
    auth_token: str,
    prefix: str,
    duration: int,
    date: str,
    outdir: str,
) -> str:
    """Perform live recording from Radiko stream using ffmpeg.

    Args:
        url_parts: M3U8 stream URL
        auth_token: Radiko authentication token
        prefix: Output file prefix
        duration: Recording duration in seconds
        date: Date string for filename
        outdir: Output directory path

    Returns:
        Path to recorded file

    Raises:
        SystemExit: If ffmpeg is not available or recording fails
    """
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        print("Error: ffmpeg must be installed and available in PATH")
        sys.exit(1)

    # Build ffmpeg command with reconnection and auth headers
    cmd = f"{ffmpeg} -loglevel warning -y "
    cmd += "-reconnect 1 -reconnect_at_eof 0 -reconnect_streamed 1 "
    cmd += "-reconnect_delay_max 600 "
    cmd += (
        '-user_agent "Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 Chrome/117.0.0.0 Safari/537.36" '
    )
    cmd += f'-headers "X-Radiko-AuthToken: {auth_token}\\r\\n" ' f'-i "{url_parts}" '
    cmd += f"-t {duration + 5} "
    cmd += f"-acodec copy {outdir}/{prefix}_{date}.mp4"
    print(cmd, flush=True)

    # Execute ffmpeg command
    try:
        result = subprocess.run(
            shlex.split(cmd),
            capture_output=True,
            text=True,
            check=True,
        )
        # Log output on success
        print(result.stdout, flush=True)
        print(result.stderr, flush=True)
        return f"{outdir}/{prefix}_{date}.mp4"
    except subprocess.CalledProcessError as e:
        # Log output on failure
        print(
            f"ffmpeg abnormal end. returncode={e.returncode}",
            flush=True,
        )
        print(e.stdout, flush=True)
        print(e.stderr, flush=True)
        sys.exit(1)


def set_mp4_meta(
    program,
    channel: str,
    area_id: str,
    rec_file: str,
    track_num: Optional[int] = None,
) -> None:
    """Set metadata tags in the MP4 file for Radiko recordings.

    Args:
        program: Program info object from Radiko API
        channel: Channel ID
        area_id: Area ID for the broadcast
        rec_file: Path to recorded MP4 file
        track_num: Optional track number
    """
    audio = MP4(rec_file)

    # Set title from program info
    title = program.get_title(channel, area_id)
    if title:
        audio.tags["\xa9nam"] = title

    # Set album (station name)
    audio.tags["\xa9alb"] = channel

    # Set artist (personality/host names)
    pfm = program.get_pfm(channel, area_id)
    if pfm:
        audio.tags["\xa9ART"] = pfm
        audio.tags["aART"] = pfm

    # Set comment (description and info)
    desc = program.get_desc(channel, area_id)
    info = program.get_info(channel, area_id)
    comment_text = ""
    if desc:
        comment_text += desc
    if info:
        comment_text += " / " + info
    if comment_text:
        audio.tags["\xa9cmt"] = comment_text

    # Set genre
    audio.tags["\xa9gen"] = "Radio"

    # Set track number (if provided)
    if track_num:
        audio.tags["trkn"] = [(track_num, 0)]

    # Set disk number (fixed to 1)
    audio.tags["disk"] = [(1, 1)]

    # Set cover art from program image
    logo_url = program.get_img(channel, area_id)
    if logo_url:
        coverart = requests.get(logo_url, timeout=(20, 5)).content
        cover = MP4Cover(coverart, imageformat=MP4Cover.FORMAT_PNG)
        audio["covr"] = [cover]

    audio.save()


def main() -> None:
    """Main function for Radiko recording.

    Orchestrates the recording workflow: argument parsing, API auth,
    stream retrieval, recording, and metadata tagging.
    """
    args = get_args()
    channel = args.channel
    duration = int(args.duration * 60)
    outdir = args.outputdir
    prefix = args.prefix if args.prefix else channel

    # Generate timestamps for filename and API query
    date = DT.now().strftime("%Y-%m-%d-%H_%M")
    fromtime = DT.now().strftime("%Y%m%d%H%M00")
    print(f"fromtime = {fromtime}")

    # Initialize Radiko API client
    api = Radikoapi()

    # Validate channel availability
    if api.is_avail(channel) is False:
        print(f"Error: Specified station {channel} is not found.")
        sys.exit(1)

    # Authorize and get authentication token and area ID
    auth_token, area_id = api.authorize()

    # Retrieve stream URL and program information
    url = get_streamurl(channel, auth_token)
    prog = api.load_program(channel, fromtime, None, area_id, now=True)

    # Perform recording
    rec_file = live_rec(url, auth_token, prefix, duration, date, outdir)

    # Handle case where program info was not loaded
    if prog is None:
        prog = api.load_program(channel, fromtime, None, area_id, now=True)

    # Set MP4 metadata
    set_mp4_meta(api, channel, area_id, rec_file)
    sys.exit(0)


if __name__ == "__main__":
    main()
