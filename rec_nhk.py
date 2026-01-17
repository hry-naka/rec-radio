#!/usr/bin/python3
# coding: utf-8
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
from datetime import datetime as DT
from typing import Any, Dict, List, Optional, Tuple

import requests
from dotenv import load_dotenv
from mutagen.mp4 import MP4, MP4Cover

# Load environment variables from .env file
load_dotenv()

# Constants - API Configuration
NHK_API_KEY = os.getenv("NHK_API_KEY")
if not NHK_API_KEY:
    print("Error: NHK_API_KEY not found in environment. " "Please set it in .env file.")
    sys.exit(1)

API_VERSION = os.getenv("API_VERSION", "v2")
if API_VERSION not in ("v2", "v3"):
    print(f"Error: API_VERSION must be 'v2' or 'v3', got '{API_VERSION}'")
    sys.exit(1)

LOCATION = os.getenv("LOCATION", "tokyo")
AREA_CODE = os.getenv("AREA_CODE", "130")
NHK_STREAM_URL = "https://www.nhk.or.jp/radio/config/config_web.xml"
NHK_API_V2_NOW = "http://api.nhk.or.jp/v2/pg/now/{}/{}.json?key={}"
NHK_API_V2_INFO = "http://api.nhk.or.jp/v2/pg/info/{}/{}/{}.json?key={}"
NHK_API_V3_NOW = (
    "https://program-api.nhk.jp/v3/papiPgDateRadio"
    "?service={service}&area={area}&date={date}&key={key}"
)
NHK_API_V3_INFO = (
    "https://program-api.nhk.jp/v3/papiBroadcastEventRadio"
    "?broadcastEventId={broadcastEventId}&key={key}"
)
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
NHK_XPATHS = {
    "NHK1": ".//stream_url/data/r1hls",
    "NHK2": ".//stream_url/data/r2hls",
    "FM": ".//stream_url/data/fmhls",
}
HTTP_TIMEOUT = (20, 5)
REQUEST_TIMEOUT = 20

# FFmpeg Configuration from .env
FFMPEG_LOGLEVEL = os.getenv("FFMPEG_LOGLEVEL", "warning")
FFMPEG_RECONNECT_DELAY_MAX = os.getenv("FFMPEG_RECONNECT_DELAY_MAX", "600")
FFMPEG_RW_TIMEOUT = os.getenv("FFMPEG_RW_TIMEOUT", "900000000")
FFMPEG_AUDIO_CODEC = os.getenv("FFMPEG_AUDIO_CODEC", "aac")
FFMPEG_AUDIO_BITRATE = os.getenv("FFMPEG_AUDIO_BITRATE", "96k")
FFMPEG_AUDIO_SAMPLE_RATE = os.getenv("FFMPEG_AUDIO_SAMPLE_RATE", "22050")
FFMPEG_EXTRA_OPTIONS = os.getenv(
    "FFMPEG_EXTRA_OPTIONS",
    "-reconnect 1 -reconnect_at_eof 0 -reconnect_streamed 1 "
    "-live_start_index -2 -http_persistent 0",
)


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


def get_streamurl(channel: str, location: str) -> Optional[Tuple[str, str]]:
    """Retrieve HLS stream URL and channel code from NHK XML config.

    Args:
        channel: Channel name (NHK1, NHK2, FM)
        location: Geographic location (e.g., 'tokyo')

    Returns:
        Tuple of (stream_url, channel_code) or None if not found
    """
    if channel not in NHK_STREAM_CODES:
        print(f"Error: Channel '{channel}' doesn't exist")
        return None

    try:
        response = requests.get(NHK_STREAM_URL, timeout=HTTP_TIMEOUT)
        response.raise_for_status()
        root = ET.fromstring(response.content)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching NHK stream config: {e}")
        return None
    except ET.ParseError as e:
        print(f"Error parsing NHK stream config XML: {e}")
        return None

    xpath = NHK_XPATHS[channel]
    code = NHK_STREAM_CODES[channel]

    # Find the stream URL for the specified location
    for child in root.findall(".//stream_url/data/*"):
        if child.tag == "area" and child.text == location:
            stream_url = root.findtext(xpath)
            if stream_url:
                return stream_url, code

    print(f"Error: No stream URL found for channel={channel}, " f"location={location}")
    return None


def get_program_info(
    area_code: str, code: str, timing: str
) -> Optional[Dict[str, Any]]:
    """Get program information from NHK API with error handling.

    Args:
        area_code: Area code (e.g., "130" for Tokyo)
        code: Channel code (e.g., "r1", "r2", "r3")
        timing: Timing option ("present", "previous", "following")

    Returns:
        Program info dict or None if not available
    """
    if API_VERSION == "v3":
        return _get_program_info_v3(area_code, code, timing)
    else:
        return _get_program_info_v2(area_code, code, timing)


def _get_program_info_v2(
    area_code: str, code: str, timing: str
) -> Optional[Dict[str, Any]]:
    """Get program information from NHK API v2 with error handling.

    Args:
        area_code: Area code (e.g., "130" for Tokyo)
        code: Channel code (e.g., "r1", "r2", "r3")
        timing: Timing option ("present", "previous", "following")

    Returns:
        Program info dict or None if not available
    """
    # Fetch current on-air program
    now_url = NHK_API_V2_NOW.format(area_code, code, NHK_API_KEY)

    try:
        resp = requests.get(now_url, timeout=HTTP_TIMEOUT)
        resp.raise_for_status()
        now_json = resp.json()
    except requests.exceptions.RequestException as e:
        print(f"[NHK] now API request error: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"[NHK] now API JSON decode error: {e}")
        return None

    # Validate structure
    nol = now_json.get("nowonair_list")
    if nol is None:
        print("[NHK] nowonair_list is None (no program info currently)")
        return None

    station = nol.get(code)
    if station is None:
        print(f"[NHK] nowonair_list has no entry for code='{code}'")
        return None

    # Select timing entry
    chosen = station.get(timing)
    if not chosen or not isinstance(chosen, dict):
        print(f"[NHK] timing='{timing}' entry is missing or invalid")
        return None

    program_id = chosen.get("id")
    if not program_id:
        print(f"[NHK] timing='{timing}' has no 'id'")
        return None

    # Fetch program details
    info_url = NHK_API_V2_INFO.format(area_code, code, program_id, NHK_API_KEY)

    try:
        info_resp = requests.get(info_url, timeout=HTTP_TIMEOUT)
        info_resp.raise_for_status()
        info_json = info_resp.json()
    except requests.exceptions.RequestException as e:
        print(f"[NHK] info API request error: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"[NHK] info API JSON decode error: {e}")
        return None

    # Extract program info
    program_list = info_json.get("list", {}).get(code)
    if not program_list:
        print(f"[NHK] info API returned no 'list[{code}]'")
        return None

    # Handle both list and dict responses
    program = program_list[0] if isinstance(program_list, list) else program_list
    if not program:
        print(f"[NHK] empty program detail for id={program_id}")
        return None

    # Verify program time validity
    try:
        now = DT.now().astimezone()
        start_dt = DT.fromisoformat(
            program.get("start_time", "").replace("Z", "+00:00")
        )
        end_dt = DT.fromisoformat(program.get("end_time", "").replace("Z", "+00:00"))

        if start_dt <= now <= end_dt:
            p_title = program.get("title")
            p_area = program.get("area", {}).get("name", "unknown")
            print(
                f"[NHK] {timing}: id={program_id} " f"title={p_title!r} area={p_area}"
            )
            return program
        else:
            print(
                f"[NHK] current time {now.isoformat()} "
                f"outside program window "
                f"{start_dt.isoformat()}-{end_dt.isoformat()}"
            )
            return None
    except (ValueError, AttributeError) as e:
        print(f"[NHK] time parse error: {e}")
        return None


def _get_program_info_v3(
    area_code: str, code: str, timing: str
) -> Optional[Dict[str, Any]]:
    """Get program information from NHK API v3 with error handling."""
    today = DT.now().strftime("%Y-%m-%d")
    now_url = NHK_API_V3_NOW.format(
        service=code, area=area_code, date=today, key=NHK_API_KEY
    )

    try:
        resp = requests.get(now_url, timeout=HTTP_TIMEOUT)
        resp.raise_for_status()
        now_json = resp.json()
    except requests.exceptions.RequestException as e:
        print(f"[NHK v3] now API request error: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"[NHK v3] now API JSON decode error: {e}")
        return None

    # Extract publication list
    if code not in now_json:
        print(f"[NHK v3] no program data for {code} on {today}")
        return None

    service_data = now_json.get(code, {})
    publication = service_data.get("publication", [])

    if not publication:
        print(f"[NHK v3] no program data for {code} on {today}")
        return None

    # Find currently broadcasting program
    now = DT.now().astimezone()
    current_program = None

    for program in publication:
        try:
            start_dt = DT.fromisoformat(
                program.get("startDate", "").replace("Z", "+00:00")
            )
            end_dt = DT.fromisoformat(program.get("endDate", "").replace("Z", "+00:00"))

            if start_dt <= now <= end_dt:
                current_program = program
                break
        except (ValueError, AttributeError) as e:
            print(f"[NHK v3] time parse error: {e}")
            continue

    if not current_program:
        print(f"[NHK v3] no currently broadcasting program found")
        return None

    # Get broadcast event ID for detailed info
    event_id = current_program.get("id")
    if not event_id:
        print("[NHK v3] program has no 'id' field")
        return None

    # Fetch detailed program information
    info_url = NHK_API_V3_INFO.format(broadcastEventId=event_id, key=NHK_API_KEY)

    try:
        info_resp = requests.get(info_url, timeout=HTTP_TIMEOUT)
        info_resp.raise_for_status()
        info_json = info_resp.json()
    except requests.exceptions.RequestException as e:
        print(f"[NHK v3] info API request error: {e}")
        # Return basic info if detail fetch fails
        p_title = current_program.get("name")
        print(f"[NHK v3] current: id={event_id} title={p_title!r}")
        return current_program
    except json.JSONDecodeError as e:
        print(f"[NHK v3] info API JSON decode error: {e}")
        return current_program

    # Return detailed program info
    p_title = info_json.get("name")
    print(f"[NHK v3] current: id={event_id} title={p_title!r}")

    return info_json


def live_rec(
    dl_url: str,
    duration: int,
    outdir: str,
    prefix: str,
    date: str,
) -> Optional[str]:
    """Perform live recording using ffmpeg with timeout.

    Args:
        dl_url: HLS stream URL
        duration: Recording duration in seconds
        outdir: Output directory
        prefix: Output file prefix
        date: Date string for filename

    Returns:
        Path to recorded file or None on failure
    """
    ffmpeg = shutil.which("ffmpeg")
    timeout = shutil.which("timeout")

    # Mac compatibility: use gtimeout if timeout not available
    if timeout is None:
        timeout = shutil.which("gtimeout")

    if ffmpeg is None or timeout is None:
        print("Error: ffmpeg and timeout must be installed and " "in PATH")
        print("  Install with: brew install ffmpeg coreutils")
        return None

    output_path = f"{outdir}/{prefix}_{date}.mp4"

    cmd = (
        f"{timeout} {duration + 20} "
        f"{ffmpeg} -loglevel {FFMPEG_LOGLEVEL} -y "
        "-nostdin -re "
        f"{FFMPEG_EXTRA_OPTIONS} "
        f"-reconnect_delay_max {FFMPEG_RECONNECT_DELAY_MAX} "
        f"-rw_timeout {FFMPEG_RW_TIMEOUT} "
        "-user_agent "
        '"Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36" '
        f"-i {dl_url} -t {duration + 5} "
        f"-vn -c:a {FFMPEG_AUDIO_CODEC} "
        f"-b:a {FFMPEG_AUDIO_BITRATE} "
        f"-ar {FFMPEG_AUDIO_SAMPLE_RATE} "
        f"{output_path}"
    )

    print(cmd, flush=True)

    try:
        result = subprocess.run(
            shlex.split(cmd),
            capture_output=True,
            text=True,
            check=True,
        )
        print(result.stdout, flush=True)
        print(result.stderr, flush=True)
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"Error: ffmpeg failed with return code {e.returncode}")
        print(e.stdout, flush=True)
        print(e.stderr, flush=True)
        return None


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
    audio.tags["\xa9alb"] = NHK_ALBUM_NAMES.get(channel, channel)

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
    duration = int(args.duration * 60)
    outdir = args.outputdir
    prefix = args.prefix if args.prefix else channel

    # Get stream URL
    stream_result = get_streamurl(channel, LOCATION)
    if stream_result is None:
        print("Error: Failed to retrieve stream URL")
        sys.exit(1)

    dl_url, code = stream_result

    # Get program information (always "present" for v3)
    program = get_program_info(AREA_CODE, code, "present")
    if program is None:
        print("Error: No program information available")
        sys.exit(1)

    # Perform recording
    date = DT.now().strftime("%Y-%m-%d-%H_%M")
    rec_file = live_rec(dl_url, duration, outdir, prefix, date)

    if rec_file is None:
        print("Error: Recording failed")
        sys.exit(1)

    # Set metadata
    try:
        set_mp4_meta(program, channel, rec_file)
    except Exception as e:
        print(f"Warning: Failed to set MP4 metadata: {e}")

    print(f"Successfully recorded: {rec_file}")
    sys.exit(0)


if __name__ == "__main__":
    main()
