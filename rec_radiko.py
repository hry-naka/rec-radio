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
import subprocess
import time
from datetime import datetime as DT
import re
import requests
from mutagen.mp4 import MP4, MP4Cover
from mypkg.radiko_api import Radikoapi
from mypkg.file_op import Fileop


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
    parser.add_argument(
        "-n",
        "--next",
        action="store_true",
        help="Read tag informtion from next program.",
    )
    parser.add_argument(
        "-c",
        "--cleanup",
        action="store_true",
        help="Cleanup(remove) output file which recording is not completed.",
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
        else:
            print("Radiko: no m3u8 in the responce.")
            sys.exit(1)
    else:
        print(res.text)
        print(f'adiko: error {res.status_code} encounterd.')
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
    cmd = f"{ffmpeg} -loglevel fatal "
    cmd += f'-headers "X-Radiko-AuthToken: {auth_token}" -i "{url_parts}" '
    cmd += f"-acodec copy {outdir}/{prefix}_{date}.mp4"

    # Exec ffmpeg
    proc = subprocess.Popen(
        cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, shell=True
    )
    time.sleep(duration)
    proc.communicate(b"q")
    time.sleep(10)
    return f"{outdir}/{prefix}_{date}.mp4"



def set_mp4_meta(program, channel, area_id, rec_file, nextflg):
    """
    Set metadata tags in the MP4 file.
    """
    # program.get_now( channel )
    audio = MP4(rec_file)
    # track title
    title = program.get_title(channel, area_id, nextflg)
    if title is not None:
        audio.tags["\xa9nam"] = title
    # album
    audio.tags["\xa9alb"] = channel
    # artist and album artist
    pfm = program.get_pfm(channel, area_id, nextflg)
    if pfm is not None:
        audio.tags["\aART"] = pfm
        audio.tags["\xa9ART"] = pfm
    logo_url = program.get_img(channel, area_id, nextflg)
    coverart = requests.get(logo_url, timeout=(20, 5)).content
    cover = MP4Cover(coverart)
    audio["covr"] = [cover]
    audio.save()
    return


def main():
    """
    Main function for the script.
    """
    args = get_args()
    channel = args.channel
    stream_delay = 25  # second
    duration = int(args.duration * 60) + stream_delay
    outdir = args.outputdir
    if args.prefix is None:
        prefix = args.channel
    else:
        prefix = args.prefix
    # setting date
    date = DT.now().strftime("%Y-%m-%d-%H_%M")
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
    api.load_program(channel, None, None, area_id, now=True)
    rec_file = live_rec(url, auth_token, prefix, duration, date, outdir)
    set_mp4_meta(api, channel, area_id, rec_file, args.next)
    fop = Fileop()
    if args.cleanup:
        fop.remove_recfile(outdir, DT.today())
    sys.exit(0)


if __name__ == "__main__":
    main()
