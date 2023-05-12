#!/usr/bin/python3
# coding: utf-8
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
    return parser.parse_args()#
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
# Time Free record by ffmpeg.
# Underconstruction
def tf_rec( auth_token, channel, ft, to, outdir, prefix, date ):
    ffmpeg = shutil.which( 'ffmpeg' )
    headers = f' -headers "X-Radiko-AuthToken: { auth_token }"'
    url = ' -i "https://radiko.jp/v2/api/ts/playlist.m3u8?station_id={}&ft={}&to={}"'.format( channel, ft, to )
    path = '{}/{}_{}.mp3'.format( outdir, prefix, date )

    cmd = '{} -loglevel quiet -y'.format( ffmpeg )
    cmd = cmd + headers + url
    cmd = cmd + ' -acodec libmp3lame -ab 128k -vn {}'.format( path )
    # Exec ffmpeg
    subprocess.call( cmd.strip().split(" ")  ) 
#
# set program meta by mutagen for mp4 file
#
def set_mp4_meta( program, channel, area_id, rec_file ):
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
