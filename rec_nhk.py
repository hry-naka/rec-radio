#!/usr/bin/python3
# coding: utf-8
"""
rec_nhk.py

This module provides functionalities for recording NHK radio.

Author: Hiroyuki NAKAMURA (https://github.com/hry-naka)
Date: May 25, 2023
"""
import argparse
import sys
import shutil
import shlex
import subprocess
import json
import xml.etree.ElementTree as ET
from datetime import datetime as DT
import requests
from typing import Optional, Dict, Any
from mutagen.mp4 import MP4, MP4Cover
from mypkg.file_op import Fileop


def get_args():
    """
    Get command-line arguments.
    """
    parser = argparse.ArgumentParser(description="Recording NHK radio.")
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
        "--timing",
        nargs="?",
        choices=["previous", "following", "present"],
        default="present",
    )
    parser.add_argument(
        "-c",
        "--cleanup",
        action="store_true",
        help="Cleanup(remove) output file which recording is not completed.",
    )
    return parser.parse_args()


# retrieve download url from xml
def get_streamurl(channel, here):
    """
    Retrieve download URL from XML.
    """
    url = "https://www.nhk.or.jp/radio/config/config_web.xml"
    nhk_code = {"NHK1": "r1", "NHK2": "r2", "FM": "r3"}
    nhk_xpath = {
        "NHK1": ".//stream_url/data/r1hls",
        "NHK2": ".//stream_url/data/r2hls",
        "FM": ".//stream_url/data/fmhls",
    }
    nhk_xpath_base = ".//stream_url/data/*"
    root = ET.fromstring(requests.get(url, timeout=(20, 5)).content)
    xpath = nhk_xpath.get(channel, None)
    if xpath is None:
        print("channel doesn't exist")
        sys.exit(1)
    else:
        code = nhk_code.get(channel, None)

    for child in root.findall(nhk_xpath_base):
        if child.tag == "area" and child.text == here:
            return root.findtext(xpath), code
    return None


#def get_program_info(area_code, code, timing):
    #"""
    #Get program information from NHK API.
    #"""
    ## variables for NHK-API
    #api_key = "DxMJ0WtG0wVd2v65V0txn4ejeD5SkmLa"
    #now_base = "http://api.nhk.or.jp/v2/pg/now/{}/{}.json?key={}"
    #info_base = "http://api.nhk.or.jp/v2/pg/info/{}/{}/{}.json?key={}"
    ## NowOnAir API
    #now_url = now_base.format(area_code, code, api_key)
    ## get program json program data
    #resp = requests.get(now_url, timeout=(20, 5)).content
    ## ProgramInfo API
    #if json.loads(resp)["nowonair_list"] is None:
        #print("Could no find any program information")
        #sys.exit(1)
    #program_id = json.loads(resp)["nowonair_list"][code][timing]["id"]
    #info_url = info_base.format(area_code, code, program_id, api_key)
    # get program information
    #program = json.loads(requests.get(info_url, timeout=(20, 5)).content)["list"][code]
    #return program
import json
import sys
import requests
from typing import Optional, Dict, Any

def get_program_info(area_code: str, code: str, timing: str) -> Optional[Dict[str, Any]]:
    """
    Get program information from NHK API with safer handling and logging.
    - timing: "present" | "previous" | "following"
    Returns:
        Program info dict or None if not available.
    """

    api_key = "DxMJ0WtG0wVd2v65V0txn4ejeD5SkmLa"
    now_base = "http://api.nhk.or.jp/v2/pg/now/{}/{}.json?key={}"
    info_base = "http://api.nhk.or.jp/v2/pg/info/{}/{}/{}.json?key={}"

    now_url = now_base.format(area_code, code, api_key)

    try:
        resp = requests.get(now_url, timeout=(20, 5))
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

    # Log all timings if present, for inspection
    def summarize(entry: Optional[Dict[str, Any]]) -> str:
        if not entry:
            return "None"
        # pick common fields if exist
        title = entry.get("title")
        start = entry.get("start_time")
        end = entry.get("end_time")
        pid = entry.get("id")
        return f"id={pid} title={title!r} start={start} end={end}"

    present = station.get("present")
    previous = station.get("previous")
    following = station.get("following")

    print("[NHK] nowonair summary:")
    print(f"  previous: {summarize(previous)}")
    print(f"  present : {summarize(present)}")
    print(f"  following: {summarize(following)}")

    # Choose timing entry safely
    chosen = station.get(timing)
    if not chosen or not isinstance(chosen, dict):
        print(f"[NHK] timing='{timing}' entry is missing or invalid")
        return None

    program_id = chosen.get("id")
    if not program_id:
        print(f"[NHK] timing='{timing}' has no 'id'")
        return None

    info_url = info_base.format(area_code, code, program_id, api_key)

    try:
        info_resp = requests.get(info_url, timeout=(20, 5))
        info_resp.raise_for_status()
        info_json = info_resp.json()
    except requests.exceptions.RequestException as e:
        print(f"[NHK] info API request error: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"[NHK] info API JSON decode error: {e}")
        return None

    # Extract program info list
    program_list = info_json.get("list", {}).get(code)
    if not program_list:
        print(f"[NHK] info API returned no 'list[{code}]'")
        return None

    # NHK ProgramInfo API typically returns an array; pick the first if so
    if isinstance(program_list, list):
        program = program_list[0] if program_list else None
    else:
        program = program_list

    if not program:
        print(f"[NHK] empty program detail for id={program_id}")
        return None

    # Log key fields for traceability
    p_title = program.get("title")
    p_id = program.get("id") or program_id
    p_area = program.get("area", {}).get("name")
    p_service = program.get("service", {}).get("name")
    p_start = program.get("start_time")
    p_end = program.get("end_time")
    print(f"[NHK] chosen timing={timing} -> id={p_id} title={p_title!r} area={p_area} service={p_service} start={p_start} end={p_end}")
    # ---- 時刻ベース判定 ----
    try:
        now = DT.now().astimezone()  # 現在時刻（タイムゾーン付き）
        start_dt = DT.fromisoformat(p_start.replace("Z", "+00:00"))
        end_dt   = DT.fromisoformat(p_end.replace("Z", "+00:00"))

        if start_dt <= now <= end_dt:
            return [program]
        else:
            print(f"[NHK] current time {now.isoformat()} not in range {start_dt.isoformat()} - {end_dt.isoformat()}")
            return None
    except Exception as e:
        print(f"[NHK] time parse error: {e}")
        return None
   # return [program]


def live_rec(dl_url, duration, outdir, prefix, date):
    """
    Perform live recording.
    """
    ffmpeg = shutil.which("ffmpeg")
    timeout = shutil.which("timeout")
    if ffmpeg is None or timeout is None:
        print("This tool need ffmpeg and timeout to be installed to executable path")
        print("Soryy, bye.")
        sys.exit(1)
    cmd = f"{timeout} {duration+20} "
    #cmd += f"{ffmpeg} -loglevel fatal -y "
    cmd += f"{ffmpeg} -loglevel warning -y "
    #cmd += f"{ffmpeg} -loglevel warning -report -y "
    #cmd += f"{ffmpeg} -loglevel debug -report -y "
    #cmd += f"{ffmpeg} -loglevel info -y "
    cmd += "-nostdin -re "
    cmd += "-reconnect 1 -reconnect_at_eof 0 -reconnect_streamed 1 "
    cmd += "-reconnect_delay_max 600 "
    cmd += "-rw_timeout 900000000 "
    cmd += "-live_start_index -2 "
    cmd += "-http_persistent 0 "
    cmd += '-user_agent "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/117.0.0.0 Safari/537.36" '
    cmd += f"-i {dl_url} -t {duration+5} "
    cmd += '-vn -c:a aac -b:a 96k -ar 22050 '
    cmd += f"{outdir}/{prefix}_{date}.mp4"
    print( cmd , flush=True )
    try:
        result = subprocess.run(
            shlex.split(cmd),
            capture_output=True,   # capture stdout/stderr
            text=True,             # automatic decode
            check=True             # if returncode != 0 throw exception
        )
        # if success output log.
        print(result.stdout, flush=True)
        print(result.stderr, flush=True)
        return f"{outdir}/{prefix}_{date}.mp4"
    except subprocess.CalledProcessError as e:
        # if not success
        print(f"ffmpeg abnormal end. returncode={e.returncode}")
        print(e.stdout, flush=True)
        print(e.stderr, flush=True)
        sys.exit(1)


def get_largest_logourl(program):
    """
    Get the URL for the largest logo image associated with the program.
    """
    logo = program[0]["program_logo"]
    if logo is None:
        logo = program[0]["service"]["logo_l"]
        if logo is None:
            logo = program[0]["service"]["logo_m"]
            if logo is None:
                logo = program[0]["service"]["logo_s"]
    if logo is not None:
        logo_url = "https:" + logo["url"]
    return logo_url


#def set_mp4_meta(program, channel, rec_file):
#    """
#    Set metadata tags in the MP4 file.
#    """
#    nhk_album = {"NHK1": "NHKラジオ第一", "NHK2": "NHKラジオ第二", "FM": "NHK-FM"}
#    audio = MP4(rec_file)
#    # track title
#    if program[0]["title"] is not None:
#        audio.tags["\xa9nam"] = program[0]["title"]
#    # album
#    audio.tags["\xa9alb"] = nhk_album.get(channel, None)
#    # artist and album artist
#    if program[0]["act"] is not None:
#        audio.tags["\aART"] = program[0]["act"]
#        audio.tags["\xa9ART"] = program[0]["act"]
#    logo_url = get_largest_logourl(program)
#    coverart = requests.get(logo_url, timeout=(20, 5)).content
#    cover = MP4Cover(coverart)
#    audio["covr"] = [cover]
#    audio.save()
#    # print( audio.tags.pprint() )

def set_mp4_meta(program, channel, rec_file, track_num=None, rec_date=None):
    """
    Set metadata tags in the MP4 file for NHK recordings.
    """
    nhk_album = {"NHK1": "NHKラジオ第一", "NHK2": "NHKラジオ第二", "FM": "NHK-FM"}
    audio = MP4(rec_file)

    # タイトル
    title = program[0].get("title")
    if title:
        audio.tags["\xa9nam"] = title

    # アルバム（局名）
    audio.tags["\xa9alb"] = nhk_album.get(channel, channel)

    # アーティスト（出演者）
    act = program[0].get("act")
    if act:
        audio.tags["\xa9ART"] = act
        audio.tags["aART"] = act

    # コメント（説明や info をまとめる）
    desc = program[0].get("desc")
    info = program[0].get("info")
    url = program[0].get("url")
    comment_text = ""
    if desc:
        comment_text += desc
    if info:
        comment_text += " / " + info
    if url:
        comment_text += " / " + url
    if comment_text:
        audio.tags["\xa9cmt"] = comment_text

    # ジャンル
    audio.tags["\xa9gen"] = "Radio"

    # 録音日（©day に YYYY-MM-DD）
    if rec_date:
        audio.tags["\xa9day"] = rec_date

    # トラック番号（録音回数など）
    if track_num:
        audio.tags["trkn"] = [(track_num, 0)]

    # ディスク番号（固定で 1）
    audio.tags["disk"] = [(1, 1)]

    # カバーアート
    logo_url = get_largest_logourl(program)
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
    timing = args.timing
    if args.prefix is None:
        prefix = args.channel
    else:
        prefix = args.prefix
    # where are you?
    here = "tokyo"
    area_code = "130"
    # setting date
    date = DT.now()
    date = date.strftime("%Y-%m-%d-%H_%M")
    # retrieve download url from xml
    dl_url, code = get_streamurl(channel, here)
    # get program information
    program = get_program_info(area_code, code, timing)
    # Recording...
    rec_file = live_rec(dl_url, duration, outdir, prefix, date)
    # Set meta information to MP4 tag
    if program is not None:
        set_mp4_meta(program, channel, rec_file)
        fop = Fileop()
    if args.cleanup:
        fop.remove_recfile(outdir, DT.today())
    sys.exit(0)


if __name__ == "__main__":
    main()
