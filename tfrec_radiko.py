#!/usr/bin/python3
# coding: utf-8
import sys
import argparse
import shutil
import subprocess
import time
import requests
from mutagen.mp4 import MP4, MP4Cover
from mypkg.RadikoApi import RadikoApi


def get_args():
    parser=argparse.ArgumentParser( description='Recording time-free-Radiko.' )
    parser.add_argument('-s', '--station', \
                required=True, \
                nargs=1, \
                help='Recording station.' )
    parser.add_argument('-ft', '--fromtime', \
                required=True, \
                nargs=1, \
                help="from time" )
    parser.add_argument('-to', '--totime', \
                required=True, \
                nargs=1, \
                help="to time" )
    parser.add_argument('outputdir', \
                metavar='outputdir', \
                nargs='?', \
                default='.' , \
                help='Output path default:\'.\'' )
    parser.add_argument('prefix', \
                metavar='Prefix-name',\
                nargs='?', \
                help='Prefix name for output file.' )
    parser.add_argument( '-c', '--cleanup' , \
                action='store_true' , \
                help='Cleanup(remove) output file which recording is not completed.' )
    return parser.parse_args()
#
# Time Free record by ffmpeg.
#
def tf_rec( auth_token, channel, ft, to, prefix, duration, date, outdir ):
    ffmpeg = shutil.which( 'ffmpeg' )
    if ffmpeg is None:
        print( 'This tool need ffmpeg to be installed to executable path' )
        print( 'Soryy, bye.')
        sys.exit(1)
    url = f'https://radiko.jp/v2/api/ts/playlist.m3u8?station_id={channel}&l=15&ft={ft}&to={to}'
    
    cmd = f'{ffmpeg} -loglevel fatal '
    cmd += f'-headers "X-Radiko-AuthToken: {auth_token}" -i "{url}" '
    cmd += f'-acodec copy {outdir}/{prefix}_{date}.mp4'
    # Exec ffmpeg...? is there any reason to spec. duration?
    p1 = subprocess.Popen(cmd, shell=True)
    p1.wait()
    if( p1.returncode != 0 ):
        print( p1.returncode, '\n', p1.stderr, '\n', p1.stdout )
        sys.exit(1)
    return f'{outdir}/{prefix}_{date}.mp4'
#
# set program meta by mutagen for mp4 file
#
def set_mp4_meta( program, channel, area_id, rec_file ):
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


if __name__ == '__main__':
    args = get_args()
    station = args.station[0]
    if args.prefix is None:
        prefix=station
    else:
        prefix=args.prefix
    ft = args.fromtime[0]
    to = args.totime[0]
    # setting date
    date = f'{ft[0:4]}-{ft[4:6]}-{ft[6:8]}-{ft[8:10]}_{ft[10:12]}'
    # Construct RadikoApi
    api = RadikoApi()
    # Check whether channel is available
    if api.is_avail( station ) == False:
        print( f'Specified station {station} is not found.' )
        sys.exit(1)
    # auhorize, get token and areaid
    auth_token, area_id = api.authorize()
    # get program meta via radiko api
    api.load_program(station, ft, to, area_id)
    rec_file=tf_rec( auth_token, station, ft, to, prefix, int(api.duration[0]), date, args.outputdir )
    set_mp4_meta( api, station, area_id, rec_file )
    if( args.cleanup ):
        removeRecFile( outdir , DT.today() )
    sys.exit(0)
