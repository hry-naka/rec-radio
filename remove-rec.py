#!/usr/bin/python3
# coding: utf-8
import argparse
import glob
import re
import os
import sys
import datetime

def setup():
    help_desc_msg = 'Remove files for rec_*.py' \
                    ' \n' \
                    'This script removes the files which fail to record.' \
                    ' \n' \
                    'The file which has the maximum file size is assumed ' \
                    'to be successfully recorded.' \
                    ' \n'
    parser=argparse.ArgumentParser( description=help_desc_msg , \
            formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('path', metavar='path', help=' path to recorded files' )
    args = parser.parse_args()
    return args.path

def getToday():
    today=datetime.date.today()
    return today

def getYesterday():
    today=datetime.date.today()
    oneday=datetime.timedelta(days=1)
    yesterday=today-oneday
    return yesterday

def getFileList( path, date ):
    date = date.strftime( '%Y-%m-%d' )
    l = glob.glob( path + '/*' + date + '*.mp4' )
    return l

'''
 ファイル名とサイズの組み合わせで辞書型のデータを作って
 サイズでソートして、一番上以外を全部os.removeするのが
 正しい。
'''
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
    path = setup()

    removeRecFile( path , getToday() )
    #removeRecFile( path , getYesterday() )
