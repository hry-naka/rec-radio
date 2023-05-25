#!/usr/bin/python3
# coding: utf-8
""" Recording time-free-Radiko. """
import sys
import argparse
import shutil
import subprocess
from datetime import datetime as DT
import requests
from mutagen.mp4 import MP4, MP4Cover
from .mypkg.radiko_api import Radikoapi
from .mypkg.file_op import Fileop


def get_args():
    """define arguments and get args"""
    parser = argparse.ArgumentParser(description="Recording time-free-Radiko.")
    parser.add_argument(
        "-s", "--station", required=True, nargs=1, help="Recording station."
    )
    parser.add_argument("-ft", "--fromtime", required=True, nargs=1, help="from time")
    parser.add_argument("-to", "--totime", required=True, nargs=1, help="to time")
    parser.add_argument(
        "outputdir",
        metavar="outputdir",
        nargs="?",
        default=".",
        help="Output path default:'.'",
    )
    parser.add_argument(
        "prefix", metavar="Prefix-name", nargs="?", help="Prefix name for output file."
    )
    parser.add_argument(
        "-c",
        "--cleanup",
        action="store_true",
        help="Cleanup(remove) output file which recording is not completed.",
    )
    return parser.parse_args()


#
# Time Free record by ffmpeg.
#
def tf_rec(token, channel, fromtime, totime, pre_fix, time, out_dir):
    """ffmpeg execution for time free recording"""
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        print("This tool need ffmpeg to be installed to executable path")
        print("Soryy, bye.")
        sys.exit(1)
    url = "https://radiko.jp/v2/api/ts/playlist.m3u8?station_id={}&l=15&ft={}&to={}"
    url = url.format(channel, fromtime, totime)
    cmd = f"{ffmpeg} -loglevel fatal "
    cmd += f'-headers "X-Radiko-AuthToken: {token}" -i "{url}" '
    cmd += f"-acodec copy {out_dir}/{pre_fix}_{time}.mp4"
    # Exec ffmpeg...
    proc = subprocess.Popen(cmd, shell=True)
    proc.wait()
    if proc.returncode != 0:
        print(proc.returncode, "\n", proc.stderr, "\n", proc.stdout)
        sys.exit(1)
    return f"{out_dir}/{pre_fix}_{time}.mp4"


def set_mp4_meta(program, channel, area_id, rec_file):
    """set program meta by mutagen for mp4 file"""
    audio = MP4(rec_file)
    # track title
    title = program.get_title(channel, area_id)
    if title is not None:
        audio.tags["\xa9nam"] = title
    # album
    audio.tags["\xa9alb"] = channel
    # artist and album artist
    pfm = program.get_pfm(channel, area_id)
    if pfm is not None:
        audio.tags["\aART"] = pfm
        audio.tags["\xa9ART"] = pfm
    logo_url = program.get_img(channel, area_id)
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
    station = args.station[0]
    if args.prefix is None:
        prefix = station
    else:
        prefix = args.prefix
    fromtime = args.fromtime[0]
    totime = args.totime[0]
    # setting date
    now = f"{fromtime[0:4]}-{fromtime[4:6]}-{fromtime[6:8]}-{fromtime[8:10]}_{fromtime[10:12]}"
    # Construct RadikoApi
    api = Radikoapi()
    # Check whether channel is available
    if api.is_avail(station) is False:
        print(f"Specified station {station} is not found.")
        sys.exit(1)
    # auhorize, get token and areaid
    auth_token, areaid = api.authorize()
    # get program meta via radiko api
    api.load_program(station, fromtime, totime, areaid)
    recfile = tf_rec(auth_token, station, fromtime, totime, prefix, now, args.outputdir)
    set_mp4_meta(api, station, areaid, recfile)
    fop = Fileop()
    if args.cleanup:
        fop.remove_recfile(args.outputdir, DT.today())
    sys.exit(0)

if __name__ == "__main__":
    main()
