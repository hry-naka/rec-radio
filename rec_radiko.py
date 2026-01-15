#!/usr/bin/python3
# coding: utf-8
"""
rec_radiko.py

This module provides functionalities for recording Radiko.

Author: Hiroyuki NAKAMURA (https://github.com/hry-naka)
Date: May 25, 2023
"""
import argparse
import sys
import shutil
import shlex
import subprocess
import time
from datetime import datetime as DT
import re
import requests
from mutagen.mp4 import MP4, MP4Cover
from mypkg.radiko_api import Radikoapi


def get_args():
    """
    Get command-line arguments.
    """
    parser = argparse.ArgumentParser(description="Recording Radiko.")
    parser.add_argument("channel", metavar="channel", help=" Channel Name")
    parser.add_argument(
        "duration", metavar="duration", type=float, help="Duration(minutes)"
    )
    parser.add_argument(
        "outputdir",
        metavar="outputdir",
        nargs="?",
        default=".",
        help="Output path default:'.'",
    )
    parser.add_argument(
        "prefix", metavar="Prefix name", nargs="?", help="Prefix name for output file."
    )
    return parser.parse_args()


def get_streamurl(channel, authtoken):
    """
    Retrieve download URL from XML.
    """
    url = f"https://f-radiko.smartstream.ne.jp/{ channel }"
    url += "/_definst_/simul-stream.stream/playlist.m3u8"
    headers = {
        "X-Radiko-AuthToken": authtoken,
    }
    res = requests.get(url, headers=headers, timeout=(20, 5))
    res.encoding = "utf-8"
    if res.status_code == 200:
        body = res.text
        lines = re.findall("^https?://.+m3u8$", body, flags=re.MULTILINE)
        if len(lines) > 0:
            return lines[0]
        print("Radiko: no m3u8 in the responce.")
        sys.exit(1)
    else:
        print(res.text)
        print(f"adiko: error {res.status_code} encounterd.")
        sys.exit(1)


def live_rec(url_parts, auth_token, prefix, duration, date, outdir):
    """
    Perform live recording.
    """
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        print("This tool need ffmpeg to be installed to executable path")
        print("Soryy, bye.")
        sys.exit(1)
    cmd = f"{ffmpeg} -loglevel warning -y "
    # cmd += f"{ffmpeg} -loglevel fatal -y "
    # cmd += f"{ffmpeg} -loglevel info -y "
    cmd += "-reconnect 1 -reconnect_at_eof 0 -reconnect_streamed 1 "
    cmd += "-reconnect_delay_max 600 "
    cmd += '-user_agent "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/117.0.0.0 Safari/537.36" '
    cmd += f'-headers "X-Radiko-AuthToken: {auth_token}\r\n" -i "{url_parts}" '
    cmd += f"-t {duration+5} "
    cmd += f"-acodec copy {outdir}/{prefix}_{date}.mp4"
    print(cmd, flush=True)

    # Exec ffmpeg
    try:
        result = subprocess.run(
            shlex.split(cmd),
            capture_output=True,  # capture stdout/stderr
            text=True,  # automatic decode
            check=True,  # if returncode != 0 throw exception
        )
        # log output when success
        print(result.stdout, flush=True)
        print(result.stderr, flush=True)
        return f"{outdir}/{prefix}_{date}.mp4"
    except subprocess.CalledProcessError as e:
        # log output when not success
        print(f"ffmpeg abnormal end. returncode={e.returncode}", flush=True)
        print(e.stdout, flush=True)
        print(e.stderr, flush=True)
        sys.exit(1)


def set_mp4_meta(program, channel, area_id, rec_file, track_num=None):
    """
    Set metadata tags in the MP4 file.
    """
    audio = MP4(rec_file)

    # タイトル
    title = program.get_title(channel, area_id)
    if title:
        audio.tags["\xa9nam"] = title

    # アルバム（局名）
    audio.tags["\xa9alb"] = channel

    # アーティスト（パーソナリティ）
    pfm = program.get_pfm(channel, area_id)
    if pfm:
        audio.tags["\xa9ART"] = pfm
        audio.tags["aART"] = pfm

    # コメント（番組説明や info）
    desc = program.get_desc(channel, area_id)
    info = program.get_info(channel, area_id)
    comment_text = ""
    if desc:
        comment_text += desc
    if info:
        comment_text += " / " + info
    if comment_text:
        audio.tags["\xa9cmt"] = comment_text

    # ジャンル
    audio.tags["\xa9gen"] = "Radio"

    # トラック番号（録音回数などを渡せるように）
    if track_num:
        audio.tags["trkn"] = [(track_num, 0)]

    # ディスク番号（固定で 1）
    audio.tags["disk"] = [(1, 1)]

    # カバーアート
    logo_url = program.get_img(channel, area_id)
    if logo_url:
        coverart = requests.get(logo_url, timeout=(20, 5)).content
        cover = MP4Cover(coverart, imageformat=MP4Cover.FORMAT_PNG)
        audio["covr"] = [cover]

    audio.save()


def main():
    """
    Main function for the script.
    """
    args = get_args()
    channel = args.channel
    duration = int(args.duration * 60)
    outdir = args.outputdir
    if args.prefix is None:
        prefix = args.channel
    else:
        prefix = args.prefix
    # setting date
    date = DT.now().strftime("%Y-%m-%d-%H_%M")
    fromtime = DT.now().strftime("%Y%m%d%H%M00")
    print(f"fromtime = {fromtime}")
    # Construct RadikoApi
    api = Radikoapi()
    # Check whether channel is available
    if api.is_avail(channel) is False:
        print(f"Specified station {channel} is not found.")
        sys.exit(1)
    # auhorize, get token and areaid
    auth_token, area_id = api.authorize()
    # get program meta via radiko api
    url = get_streamurl(channel, auth_token)
    # load program info
    prog = api.load_program(channel, fromtime, None, area_id, now=True)
    rec_file = live_rec(url, auth_token, prefix, duration, date, outdir)
    if prog is None:
        api.load_program(channel, fromtime, None, area_id, now=True)
    set_mp4_meta(api, channel, area_id, rec_file)
    sys.exit(0)


if __name__ == "__main__":
    main()
