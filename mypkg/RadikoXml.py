#!/usr/bin/python3
# coding: utf-8
from datetime import datetime as DT
import urllib.request, urllib.error, urllib.parse
import xml.etree.ElementTree as ET

class RadikoXml:
    def __init__(self, location):
        self.d = DT.today()
        self.title = self.url = self.desc = self.info = self.pfm = []
        self.img = []
        if location is not None:
            self.location = location
        self.weekly_url = 'http://radiko.jp/v3/program/station/weekly/{}.xml'
        today_url = 'http://radiko.jp/v3/program/today/{}.xml'
        self.today_url = today_url.format( location )
        tomorrow_url = 'http://radiko.jp/v3/program/tomorrow/{}.xml'
        self.tomorrow_url = tomorrow_url.format( location )
        now_url = 'http://radiko.jp/v3/program/now/{}.xml'
        self.now_url = now_url.format( location )
        resp = urllib.request.urlopen( self.now_url ).read()
        self.now = ET.fromstring( resp )

    def is_avail( self, station ):
        xpath_tmp = './/station[@id="{}"]//*'
        xpath = xpath_tmp.format( station )
        if self.now.findall( xpath ) == []:
            return False
        else:
            return True

    def get_channel( self ):
        list1 = self.now.findall( './/station[@id]' )
        list2 = self.now.findall( './/station/name' )
        dic = {}
        for i, data in enumerate( list1 ):
            dic.update( { data.attrib['id']:list2[i].text } )
        return dic

    def get_weekly( self , station ):
        url = self.weekly_url.format( station )
        resp = urllib.request.urlopen( url ).read()
        root = ET.fromstring( resp )
        return( root )

    def print_weekly( self , station ):
        print('----------------------------------')
        root = self.get_weekly( station )
        ldate = root.findall( './/progs/date' )
        lprog = root.findall( './/progs/prog' )
        count = 0
        for date in ldate:
            print('Date : {}'.format( date.text ))

    def get_now( self, station ):
        xpath_tmp = './/station[@id="{}"]//*/{}'
        xpath = xpath_tmp.format( station , 'title' )
        self.title = self.now.findall( xpath )
        xpath = xpath_tmp.format( station , 'url' )
        self.url = self.now.findall( xpath )
        xpath = xpath_tmp.format( station , 'desc' )
        self.desc = self.now.findall( xpath )
        xpath = xpath_tmp.format( station , 'info' )
        self.info = self.now.findall( xpath )
        xpath = xpath_tmp.format( station , 'pfm' )
        self.pfm = self.now.findall( xpath )
        xpath = xpath_tmp.format( station , 'img' )
        self.img = self.now.findall( xpath )

    def dump( self ):
        #print self.d
        print('Title: ')
        for m in self.title:
            print(m.text)
        print('Url: ')
        for m in self.url:
            print(m.text)
        print('Desc: ')
        for m in self.desc: 
            print(m.text)
        print('Info: ')
        for m in self.info:
            print(m.text)
        print('Pfm: ')
        for m in self.pfm:
            print(m.text)
        print('Img: ')
        for m in self.img:
            print(m.text)

if __name__ == '__main__':
    main = RadikoXml( 'JP13' )
#    main.print_weekly('TBS')
#    main.get_now('TBS')
    dic = main.get_channel()
    print('--------------------')
    for i, data in enumerate( dic.keys() ):
        print(data + ':\t\t' + list(dic.values())[i])
    print('--------------------')
#    main.dump()
