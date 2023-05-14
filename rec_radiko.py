#!/usr/bin/python3
# coding: utf-8
import argparse
import sys
import os
import glob
import shutil
import subprocess
import time
from datetime import datetime as DT
import re
import base64
import requests
import mutagen
from mutagen.mp4 import MP4, MP4Cover
from mypkg.RadikoApi import RadikoApi


def get_args():
    parser=argparse.ArgumentParser( description='Recording Radiko.' )
    parser.add_argument('channel', \
                metavar='channel', \
                help=' Channel Name' )
    parser.add_argument('duration', \
                metavar='duration', \
                type=float, \
                help='Duration(minutes)' )
    parser.add_argument('outputdir', \
                metavar='outputdir', \
                nargs='?', \
                default='.' , \
                help='Output path default:\'.\'' )
    parser.add_argument('prefix', \
                metavar='Prefix name',\
                nargs='?', \
                help='Prefix name for output file.' )
    parser.add_argument( '-c', '--cleanup' , \
                action='store_true' , \
                help='Cleanup(remove) output file which recording is not completed.' )
    return parser.parse_args()
#
# get authorized token and areaid(ex, JP13)
#
def authorize():
    authKey = "bcd151073c03b352e1ef2fd66c32209da9ca0afa"
    headers = {
        "x-radiko-app": "pc_html5",
        "x-radiko-app-version": "0.0.1",
        "x-radiko-device": "pc",
        "x-radiko-user": "dummy_user",
    }
    url = 'https://radiko.jp/v2/api/auth1'
    res = requests.get( url, headers=headers )
    if res.status_code == 200:
        token = res.headers["x-radiko-authtoken"]
        offset = int(res.headers["x-radiko-keyoffset"])
        length = int(res.headers["x-radiko-keylength"])
        partial_key = base64.b64encode(authKey[offset:offset + length].encode("ascii")).decode("utf-8")
        headers = {
            "x-radiko-authtoken": token,
            "x-radiko-device": "pc",
            "x-radiko-partialkey": partial_key,
            "x-radiko-user": "dummy_user",
        }
        url = 'https://radiko.jp/v2/api/auth2'
        res = requests.get( url, headers=headers )
        if res.status_code == 200:
            return token, res.text.split(',')[0]
        else:
            print( f'authorize errr at phase#2 : {res.status_code}' )
            sys.exit(1)
    else:
        print( f'authorize errr at phase#1 : {res.status_code}' )
        sys.exit(1)
#
# get stream-url
#
def get_streamurl( channel , authtoken ):
    url = f'https://f-radiko.smartstream.ne.jp/{ channel }/_definst_/simul-stream.stream/playlist.m3u8'
    headers =  {
        "X-Radiko-AuthToken": authtoken,
    }
    res  = requests.get(url, headers=headers)
    res.encoding = "utf-8"
    if (res.status_code == 200):
        body = res.text
        lines = re.findall( f'^https?://.+m3u8$' , body, flags=(re.MULTILINE) )
        if len(lines) > 0:
            return lines[0]
        else:
            print("Radiko: no m3u8 in the responce.")
            sys.exit(1)
    else:
        print(res.text)
        print('Radiko: error {} encounterd.'.format(res.status_code) )
        sys.exit(1)
#
# Live record by ffmpeg. output file is mp4 format and it's filename is returned from this proc.
#
def live_rec( url_parts, auth_token, prefix, duration, date, outdir ):
    ffmpeg = shutil.which( 'ffmpeg' )
    if ffmpeg is None:
        print( 'This tool need ffmpeg to be installed to executable path' )
        print( 'Soryy, bye.')
        sys.exit(1)
    cmd = f'{ffmpeg} -loglevel fatal '
    cmd += f'-headers "X-Radiko-AuthToken: {auth_token}" -i "{url_parts}" '
    cmd += f'-acodec copy {outdir}/{prefix}_{date}.mp4'

    # Exec ffmpeg
    p1 = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, shell=True)
    time.sleep( duration )
    p1.communicate(b'q')
    time.sleep(10)
    return f'{outdir}/{prefix}_{date}.mp4'
#
# set program meta by mutagen for mp4 file
#
def set_mp4_meta( program, channel, area_id, rec_file ):
    #program.get_now( channel )
    audio = MP4(rec_file)
    # track title
    title = program.get_title( channel, area_id )
    if title is not None:
        audio.tags["\xa9nam"] = title
    # album
    audio.tags["\xa9alb"] = channel
    # artist and album artist
    pfm = program.get_pfm( channel, area_id )
    if pfm is not None:
        audio.tags['\aART'] = pfm
        audio.tags["\xa9ART"] = pfm
    logo_url = program.get_img( channel, area_id )
    coverart = requests.get(logo_url).content
    cover = MP4Cover(coverart)
    audio["covr"] = [cover]
    audio.save()  
    return

def getFileList( path, date ):
    date = date.strftime( '%Y-%m-%d' )
    l = glob.glob( path + '/*' + date + '*.mp4' )
    return l

def removeRecFile( path , date ):
    fl = getFileList( path, date )
    fl_dic = {}
    for f in fl:
        size = os.path.getsize( f )
        fl_dic[f] = size
    remove = sorted(fl_dic.items(), key = lambda x : x[1] , reverse=True)
    remove.pop(0)
    for f in remove:
        #print( 'removing file will be: ' + f[0] )
        os.remove( f[0] )

if __name__ == '__main__':
    args = get_args()
    channel=args.channel
    stream_delay = 25 #second
    duration=int(args.duration * 60) + stream_delay
    outdir=args.outputdir
    if args.prefix is None:
        prefix=args.channel
    else:
        prefix=args.prefix
    # setting date
    date = DT.now().strftime('%Y-%m-%d-%H_%M')
    # Construct RadikoApi
    api = RadikoApi()
    # Check whether channel is available
    if api.is_avail( channel ) == False:
        print( f'Specified station {channel} is not found.' )
        sys.exit(1)
    # auhorize, get token and areaid
    auth_token, area_id = api.authorize()
    # get program meta via radiko api
    url = get_streamurl( channel ,auth_token )
    api.load_program(channel, None, None, area_id, now=True)
    rec_file=live_rec( url, auth_token, prefix, duration, date, outdir )
    set_mp4_meta( api, channel, area_id, rec_file )
    if( args.cleanup ):
        removeRecFile( outdir , DT.today() )
    sys.exit(0)
