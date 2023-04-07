#!/usr/bin/python3
# coding: utf-8
import argparse
import sys
import os
import subprocess
import urllib.request, urllib.error, urllib.parse
import json
import xml.etree.ElementTree as ET
import re
from retrying import retry
from datetime import datetime as DT
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, error

@retry(stop_max_attempt_number=5,wait_exponential_multiplier=1000, wait_exponential_max=10000)
def urlopen_w_retry( url ):
    headers = {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:47.0) Gecko/20100101 Firefox/47.0",}
    request = urllib.request.Request(url, headers=headers)
    resp = urllib.request.urlopen( request ).read()
    #try:
    #    resp = urllib.request.urlopen( request ).read()
    #except urllib.error.HTTPError as e:
    #    print((e.code))
    #    print((e.reason))
    #    print((e.read()))
    return( resp )

# show id3 tag
def show_id3_tags(file_path):
    tags = ID3(file_path)
    print((tags.pprint()))

def add_id3_art(path,url):
    art = urlopen_w_retry(url)
    mp3 = MP3(path, ID3=ID3)
    art_tag = APIC()
    art_tag.encoding = 3
    art_tag.type = 3
    art_tag.desc = u"Album Cover"
    if url.endswith('png'):
        art_tag.mime = u"image/png"
    else:
        art_tag.mime = u"image/jpeg"
    art_tag.data = art
    mp3.tags.add(art_tag)
    mp3.save()
    return

if __name__ == '__main__':
    parser=argparse.ArgumentParser( description='Recording NHK radio.' )
    parser.add_argument('channel', \
                metavar='channel', \
                help=' Channel Name' )
    parser.add_argument('duration', \
                metavar='duration', \
                type=int, \
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
    args = parser.parse_args()
    channel=args.channel
    duration=args.duration * 60
    outdir=args.outputdir
    timing=args.timing

    if args.prefix is None:
        prefix=args.channel
    else:
        prefix=args.prefix

    # tools
    #        '-re -y -err_detect aggressive ' + \
    #       '-loglevel quiet -y ' + \
    ffmpeg_cmd = '/usr/bin/ffmpeg ' + \
            '-loglevel error -y ' + \
            '-i {} -t {} -c:a libmp3lame -ab 128k ' + \
            '{}/{}_{}.mp3'
    path = '{}/{}_{}.mp3'
    # where are you?
    here = 'tokyo'
    area_code = '130'
    # variables for xml parsing
    url = 'https://www.nhk.or.jp/radio/config/config_web.xml'
    nhk_xpath_base = './/stream_url/data/*'
    nhk_xpath = {
        'NHK1':	'.//stream_url/data/r1hls',
        'NHK2': './/stream_url/data/r2hls',
        'FM': './/stream_url/data/fmhls'
    }
    # variables for NHK-API
    api_key = 'DxMJ0WtG0wVd2v65V0txn4ejeD5SkmLa'
    now_base = 'http://api.nhk.or.jp/v2/pg/now/{}/{}.json?key={}'
    info_base = 'http://api.nhk.or.jp/v2/pg/info/{}/{}/{}.json?key={}'
    nhk_code = {
        'NHK1':	'r1',
        'NHK2': 'r2',
        'FM': 'r3'
    }
    nhk_album = {
        'NHK1':	'NHKラジオ第一',
        'NHK2': 'NHKラジオ第二',
        'FM': 'NHK-FM'
    }

    # setting date
    date = DT.now()
    date = date.strftime('%Y-%m-%d-%H_%M')

    # retrieve download url from xml
    root = ET.fromstring( urlopen_w_retry( url ) )
    xpath = nhk_xpath.get( channel , None )
    if xpath is None:
        print( "channel doesn't exist" )
        sys.exit(1)
    else:
        code = nhk_code.get( channel , None )

    for child in root.findall( nhk_xpath_base ):
        if child.tag == 'area' and child.text == here:
            dl_url = root.findtext( xpath )

    # NowOnAir API
    now_url = now_base.format( area_code, code, api_key )

    # get program json program data
    resp = urlopen_w_retry(now_url)

    # ProgramInfo API
    if json.loads(resp)['nowonair_list'] is None:
        print( 'Could no find any program information' )
        sys.exit(1)

    program_id = \
            json.loads(resp)['nowonair_list'][code][timing]['id']
    info_url = info_base.format( area_code, code , program_id, api_key)

    # get program information
    program = json.loads(urlopen_w_retry(info_url))['list'][code]

    # Recording...
    cmd = ffmpeg_cmd.format( dl_url, duration, outdir, prefix, date )
    path = path.format( outdir, prefix, date )
    proc = subprocess.run( cmd.split(' ') , stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if( proc.returncode != 0 ):
        print( proc.returncode, proc.stdout, proc.stderr)
        sys.exit(1)

    # set front cover of mp3
    logo = program[0]['program_logo']
    if logo is None:
        logo = program[0]['service']['logo_l']
        if logo is None:
            logo = program[0]['service']['logo_m']
            if logo is None:
                logo = program[0]['service']['logo_s']

    if logo is not None:
        logo_url = 'https:' + logo['url']
        add_id3_art(path,logo_url)
                
    # set tags of mp3
    tags = EasyID3(path)
    tags['album'] = nhk_album.get( channel , None )
    if program[0]['title']:
        tags['title'] = program[0]['title']
    if program[0]['subtitle']:
        tags['artist'] = program[0]['subtitle']
    if program[0]['act']:
        tags['artist'] = program[0]['act']

    tags.save()
    #show_id3_tags(path)

