#!/usr/bin/python3
# coding: utf-8
import sys
import argparse
import shutil
import mutagen
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
    # needed?
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
    return parser.parse_args()
#
# Time Free record by ffmpeg.
#
def tf_rec( auth_token, channel, ft, to, outdir, prefix, date ):
    ffmpeg = shutil.which( 'ffmpeg' )
    if ffmpeg is None:
        print( 'This tool need ffmpeg to be installed to executable path' )
        print( 'Soryy, bye.')
        sys.exit(1)
    url_parts = f' -i "https://radiko.jp/v2/api/ts/playlist.m3u8?station_id={channel}&ft={ft}&to={to}"'
    cmd = f'{ffmpeg} -loglevel fatal '
    cmd += f'-headers "X-Radiko-AuthToken: {auth_token}" -i "{url_parts}" '
    cmd += f'-acodec copy {outdir}/{prefix}_{date}.mp4'

    # Exec ffmpeg...? is there any reason to spec. duration?
    p1 = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, shell=True)
    time.sleep( duration )
    p1.communicate(b'q')
    time.sleep(10)
    return f'{outdir}/{prefix}_{date}.mp4'
#
# set program meta by mutagen for mp4 file
#
def set_mp4_meta( program, channel, area_id, rec_file ):
    # Gee.. get_now() will not provide propper info.
    program.get_now( channel )
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
    channel=args.station
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
    rec_file=live_rec( url, auth_token, prefix, duration, date, outdir )
    '''
    if args.timefree is None:
        index = 1
        rec_file=live_rec( url, auth_token, prefix, \
                duration, date, outdir )
    else:
        index = 0
        rec_file=tf_rec( auth_token, channel, ft, to, outdir, prefix, date )
    '''
    index = 1 #What's this?
    set_mp4_meta( api, channel, area_id, rec_file )
    if( args.cleanup ):
        removeRecFile( outdir , DT.today() )
    sys.exit(0)
