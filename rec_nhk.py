#!/usr/bin/python3
# coding: utf-8
import argparse
import sys
import os
import shutil
import subprocess
import requests
import json
import xml.etree.ElementTree as ET
import re
from datetime import datetime as DT
from mutagen.mp4 import MP4, MP4Cover

def get_args():
    parser=argparse.ArgumentParser( description='Recording NHK radio.' )
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
    parser.add_argument('--timing', \
                nargs='?', \
                choices=['previous', 'following', 'present'], \
                default='present')
    return parser.parse_args()

# retrieve download url from xml
def get_streamurl( channel ):
    url = 'https://www.nhk.or.jp/radio/config/config_web.xml'
    nhk_code = {
        'NHK1':	'r1',
        'NHK2': 'r2',
        'FM': 'r3'
    }
    nhk_xpath = {
        'NHK1':	'.//stream_url/data/r1hls',
        'NHK2': './/stream_url/data/r2hls',
        'FM': './/stream_url/data/fmhls'
    }
    nhk_xpath_base = './/stream_url/data/*'
    root = ET.fromstring( requests.get( url ).content )
    xpath = nhk_xpath.get( channel , None )
    if xpath is None:
        print( "channel doesn't exist" )
        sys.exit(1)
    else:
        code = nhk_code.get( channel , None )

    for child in root.findall( nhk_xpath_base ):
        if child.tag == 'area' and child.text == here:
            return root.findtext( xpath ), code
    return None

def get_program_info( area_code, code ,timing ):
    # variables for NHK-API
    api_key = 'DxMJ0WtG0wVd2v65V0txn4ejeD5SkmLa'
    now_base = 'http://api.nhk.or.jp/v2/pg/now/{}/{}.json?key={}'
    info_base = 'http://api.nhk.or.jp/v2/pg/info/{}/{}/{}.json?key={}'
    # NowOnAir API
    now_url = now_base.format( area_code, code, api_key )
    # get program json program data
    resp = requests.get(now_url).content
    # ProgramInfo API
    if json.loads(resp)['nowonair_list'] is None:
        print( 'Could no find any program information' )
        sys.exit(1)
    program_id = \
            json.loads(resp)['nowonair_list'][code][timing]['id']
    info_url = info_base.format( area_code, code , program_id, api_key)
    # get program information
    program = json.loads(requests.get(info_url).content)['list'][code]
    return program

def live_rec( dl_url, duration, outdir, prefix, date ):
    ffmpeg = shutil.which( 'ffmpeg' )
    if ffmpeg is None:
        print( 'This tool need ffmpeg to be installed to executable path' )
        print( 'Soryy, bye.')
        sys.exit(1)
    cmd  = f'{ffmpeg} -loglevel fatal -y '
    cmd += f'-i {dl_url} -t {duration} '
    cmd += f'{outdir}/{prefix}_{date}.mp4'
    proc = subprocess.run( cmd.split(' ') , stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if( proc.returncode != 0 ):
        print( f'ffmpeg abnormal end. {proc.returncode}, {proc.stdout}, {proc.stderr}' )
        sys.exit(1)
    else:
        return f'{outdir}/{prefix}_{date}.mp4'

def get_largest_logourl( program ):
    logo = program[0]['program_logo']
    if logo is None:
        logo = program[0]['service']['logo_l']
        if logo is None:
            logo = program[0]['service']['logo_m']
            if logo is None:
                logo = program[0]['service']['logo_s']
    if logo is not None:
        logo_url = 'https:' + logo['url']
    return logo_url

def set_mp4_meta( program, channel, rec_file ):
    nhk_album = {
        'NHK1':	'NHKラジオ第一',
        'NHK2': 'NHKラジオ第二',
        'FM': 'NHK-FM'
    }
    audio = MP4(rec_file)
    # track title
    if program[0]['title'] is not None:
        audio.tags["\xa9nam"] = program[0]['title']    
    # album
    audio.tags["\xa9alb"] = nhk_album.get( channel , None )
    # artist and album artist
    if program[0]['act'] is not None:
        audio.tags['\aART'] = program[0]['act']
        audio.tags["\xa9ART"] = program[0]['act']
    logo_url = get_largest_logourl( program )
    coverart = requests.get(logo_url).content
    cover = MP4Cover(coverart)
    audio["covr"] = [cover]
    audio.save()
    #print( audio.tags.pprint() )
    return

if __name__ == '__main__':
    args = get_args()
    channel=args.channel
    stream_delay = 40 #second
    duration=int(args.duration* 60) + stream_delay
    outdir=args.outputdir
    timing=args.timing
    if args.prefix is None:
        prefix=args.channel
    else:
        prefix=args.prefix
    # where are you?
    here = 'tokyo'
    area_code = '130'
    # setting date
    date = DT.now()
    date = date.strftime('%Y-%m-%d-%H_%M')
    # retrieve download url from xml
    dl_url, code = get_streamurl( channel )
    # get program information
    program = get_program_info( area_code, code, timing )
    # Recording...
    rec_file = live_rec( dl_url, duration, outdir, prefix, date )
    # Set meta information to MP4 tag
    set_mp4_meta( program, channel, rec_file )
    sys.exit(0)
