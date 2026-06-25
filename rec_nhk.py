#!/usr/bin/env python3
"""rec_nhk.py - NHK radio recording module.

This module provides functionalities for recording NHK radio.

Author: Hiroyuki NAKAMURA (https://github.com/hry-naka)
Date: May 25, 2023
"""

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime as DT, timedelta
from typing import Any, Dict, Optional, Tuple

import requests
from dotenv import load_dotenv
from mutagen.mp4 import MP4, MP4Cover
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

NHK_ALBUM_NAMES = {
    "NHK1": "NHKラジオ第一",
    "NHK2": "NHKラジオ第二",
    "FM": "NHK-FM",
}
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

def get_largest_logourl(program: Dict[str, Any]) -> Optional[str]:
    """Get the largest logo image URL associated with the program.

    Args:
        program: Program info dict

    Returns:
        URL to logo image or None if not found
    """
    if not program:
        return None

    prog = program

    # v3: Check about.partOfSeries.logo
    about = prog.get("about", {})
    part_of_series = about.get("partOfSeries", {})
    logo = part_of_series.get("logo", {})

    if logo:
        # Try main -> medium -> small
        for size in ["main", "medium", "small"]:
            url = logo.get(size, {}).get("url")
            if url:
                return url

    # v2 fallback
    logo = prog.get("program_logo")
    if logo is None:
        service = prog.get("service", {})
        logo = service.get("logo_l") or service.get("logo_m") or service.get("logo_s")

    if logo and isinstance(logo, dict):
        url = logo.get("url")
        if url:
            if not url.startswith("https"):
                return f"https:{url}"
            return url
    return None


def set_mp4_meta(
    program: Dict[str, Any],
    channel: str,
    rec_file: str,
    track_num: Optional[int] = None,
    rec_date: Optional[str] = None,
) -> None:
    """Set metadata tags in the MP4 file for NHK recordings.

    Args:
        program: Program info dict
        channel: Channel name (NHK1, NHK2, FM)
        rec_file: Path to recorded MP4 file
        track_num: Optional track number
        rec_date: Optional recording date (YYYY-MM-DD format)
    """
    audio = MP4(rec_file)
    prog = program

    # Title (v3: 'name', v2: 'title')
    title = prog.get("name") or prog.get("title")
    if title:
        audio.tags["\xa9nam"] = title

    # Album (station name)
    audio.tags["\xa9alb"] = NHK_ALBUM_NAMES.get(channel)

    # Artist (cast/performers)
    # v3: misc.actList[], v2: act
    artists = []
    act = prog.get("act")
    if act:
        artists.append(act)

    misc = prog.get("misc", {})
    act_list = misc.get("actList", [])
    for actor in act_list:
        name = actor.get("name")
        if name:
            artists.append(name)

    if artists:
        artist_str = " / ".join(artists)
        audio.tags["\xa9ART"] = artist_str
        audio.tags["aART"] = artist_str

    # Comment (description, info, URL)
    comment_parts = []
    for field in ["description", "desc", "info", "url"]:
        value = prog.get(field)
        if value:
            comment_parts.append(value)
    if comment_parts:
        audio.tags["\xa9cmt"] = " / ".join(comment_parts)

    # Genre (v3: identifierGroup.genre, v2: genre field)
    genre = None
    identifier_group = prog.get("identifierGroup", {})
    genre_list = identifier_group.get("genre", [])
    if genre_list:
        genre = genre_list[0].get("name2") or genre_list[0].get("name1")

    if not genre:
        genre = prog.get("genre")

    audio.tags["\xa9gen"] = genre or "Radio"

    # Recording date
    if rec_date:
        audio.tags["\xa9day"] = rec_date

    # Track number
    if track_num:
        audio.tags["trkn"] = [(track_num, 0)]

    # Disk number
    audio.tags["disk"] = [(1, 1)]

    # Cover art
    logo_url = get_largest_logourl(program)
    if logo_url:
        try:
            coverart = requests.get(logo_url, timeout=HTTP_TIMEOUT).content
            cover = MP4Cover(coverart, imageformat=MP4Cover.FORMAT_PNG)
            audio["covr"] = [cover]
        except requests.exceptions.RequestException as e:
            print(f"Warning: Failed to fetch cover art: {e}")

    audio.save()


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

    # Get stream URL
    print( f"Retrieving stream URL for code={code}, location={LOCATION}")
    dl_url = api_client.get_streamurl()
    if dl_url is None:
        print("Error: Failed to retrieve stream URL")
        sys.exit(1)

    # Get program information
    program = api_client.get_program_info(target_time)
    if program is None:
        print("Error: No program information available")

    # Perform recording
    date = DT.now().strftime("%Y-%m-%d-%H_%M")
    output = f"{outdir}/{prefix}_{date}.m4a"
    success = recorder.record_nhk_live(dl_url, duration, output, prefix, date)
    if not success:
        print("Error: Recording failed")
        sys.exit(1)

    # retry after recording
    if program is None:
        print("Retry getting program info.")
        program = api_client.get_program_info(target_time)
    else:
        print("Retry skipped.")

    # Set metadata
    try:
        set_mp4_meta(program, channel, output)
    except Exception as e:
        print(f"Warning: Failed to set MP4 metadata: {e}")

    print(f"Successfully recorded: {output}")
    sys.exit(0)

if __name__ == "__main__":
    main()
