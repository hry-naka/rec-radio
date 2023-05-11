#!/usr/bin/python3
# coding: utf-8
#import datetime
from datetime import datetime as DT
from datetime import timedelta as TD
import xml.etree.ElementTree as ET
import random
import hashlib
import json
import re
import base64
import requests

class RadikoApi():
    def __init__(self):
        self.d = DT.today()
        self.title = self.url = self.desc = self.info = self.pfm = []
        self.img = []
        self.search_url = 'https://radiko.jp/v3/api/program/search'
        self.stationlist_url = 'http://radiko.jp/v3/station/list/{}.xml'
        self.now_url = 'http://radiko.jp/v3/program/now/{}.xml'
        #self.now_url = now_url.format( area_id )
        #self.weekly_url = 'http://radiko.jp/v3/program/station/weekly/{}.xml'
        #self.today_url = 'http://radiko.jp/v3/program/today/{}.xml'
        #self.today_url = today_url.format( station_id )
        #self.tomorrow_url = 'http://radiko.jp/v3/program/tomorrow/{}.xml'
        #self.tomorrow_url = tomorrow_url.format( station_id )

    def get_stationlist( self,area_id='JP13' ):
        self.stationlist_url = self.stationlist_url.format( area_id )
        resp = requests.get( self.stationlist_url, timeout=(20,5) )
        if resp.status_code == 200:
            stationlist = ET.fromstring( resp.content.decode('utf-8') )
            return( stationlist )
        else:
            print( resp.status_code )
            return None
        
    def is_avail( self, station, area_id='JP13' ):
        stationlist = self.get_stationlist( area_id )
        for id in stationlist.iter('id'):
            if id.text == station:
                return True
        return False

    def get_channel( self , area_id='JP13' ):
        stationlist = self.get_stationlist( area_id )
        idlist = []
        namelist = []
        for id in stationlist.iter('id'):
            idlist.append( id.text )
        for name in stationlist.iter('name'):
            namelist.append( name.text )
        return idlist, namelist
        
    def get_now(self, station, area_id='JP13'):
        self.now_url = self.now_url.format( area_id )
        resp = requests.get( self.now_url, timeout=(20,5) )
        if resp.status_code == 200:
            now = ET.fromstring( resp.content.decode("utf-8") )
            tmp = './/station[@id="{}"]//*/{}'
            for e in now.findall( tmp.format( station , 'title' ) ):
                self.title.append( e.text )
            for e in now.findall( tmp.format( station , 'url' ) ):
                self.url.append( e.text )
            for e in now.findall( tmp.format( station , 'desc' ) ):
                self.desc.append( e.text )
            for e in now.findall( tmp.format( station , 'info' ) ):
                self.info.append( e.text )
            for e in now.findall( tmp.format( station , 'pfm' ) ):
                self.pfm.append( e.text )
            for e in now.findall( tmp.format( station , 'img' ) ):
                self.img.append( e.text )
        else:
            print( resp.status_code )
            return None
    
    def get_title( self, station, area_id , next=False ):
        if next is True:
            index = 1
        else:
            index = 0
        if self.title == []:
            self.get_now( station, area_id )
        return( self.title[index] )

    def get_url( self, station, area_id , next=False ):
        if next is True:
            index = 1
        else:
            index = 0
        if self.url == []:
            self.get_now( station, area_id )
        return( self.desc[index] )

    def get_desc( self, station, area_id , next=False ):
        if next is True:
            index = 1
        else:
            index = 0
        if self.desc == []:
            self.get_now( station, area_id )
        return( self.desc[index] )
    
    def get_info( self, station, area_id , next=False ):
        if next is True:
            index = 1
        else:
            index = 0
        if self.info == []:
            self.get_now( station, area_id )
        return( self.info[index] )

    def get_pfm( self, station, area_id , next=False ):
        if next is True:
            index = 1
        else:
            index = 0
        if self.pfm == []:
            self.get_now( station, area_id )
        return( self.pfm[index] )

    def get_img( self, station, area_id , next=False ):
        if next is True:
            index = 1
        else:
            index = 0
        if self.img == []:
            self.get_now( station, area_id )
        return( self.img[index] )

    def generate_uid(self):
        rnd = random.random() * 1000000000
        ms = TD.total_seconds(DT.now() - DT(1970, 1, 1)) * 1000
        return hashlib.md5(str(rnd + ms).encode('utf-8')).hexdigest()

    def search(self, keyword='', t='past', area_id='JP13'):
        params = {
            'key': keyword,
            'filter': t,
            'start_day': '',
            'end_day': '',
            'area_id': area_id,
            'region_id': '',
            'cul_area_id': area_id,
            'page_idx': '0',
            'uid': self.generate_uid(),
            'row_limit': '12',
            'app_id': 'pc',
            'action_id': '0',
        }
        response = requests.get('http://radiko.jp/v3/api/program/search', params=params, timeout=(20,5))
        return json.loads(response.content)

    def authorize(self):
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
                return None
        else:
            print( f'authorize errr at phase#1 : {res.status_code}' )
            return None

    def dump( self ):
        #print self.d
        print('Title: ')
        for m in self.title:
            print(m)
        print('Url: ')
        for m in self.url:
            print(m)
        print('Desc: ')
        for m in self.desc: 
            print(m)
        print('Info: ')
        for m in self.info:
            print(m)
        print('Pfm: ')
        for m in self.pfm:
            print(m)
        print('Img: ')
        for m in self.img:
            print(m)

if __name__ == '__main__':
    main = RadikoApi(  )
    '''
    print( main.is_avail( 'TBS' ) )
    print( main.is_avail( "TXS" ) )
    
    print('--------------------')
    idlist, namelist = main.get_channel()
    for i,id in enumerate(idlist):
        print( f'{i} station : {id}\t\tname : {namelist[i]}')
    print('--------------------')

    main.get_now('JOAK-FM')
    main.dump()
    '''
    #result = main.search('黒田 卓也')
    result = main.search('生島ヒロシ')
    for d in result['data']:
        print( d['title'], d['station_id'], re.sub( '[-: ]' ,'' , d['start_time']), re.sub( '[-: ]' ,'' , d['end_time']) )
    #print( json.dumps( result, indent=4 ) )