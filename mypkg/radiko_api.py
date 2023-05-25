#!/usr/bin/python3
# coding: utf-8
"""
This module provides a class for performing radiko api.
"""
from datetime import datetime as DT
from datetime import timedelta as TD
import xml.etree.ElementTree as ET
import re
import random
import hashlib
import json
import base64
import requests


class Radikoapi:
    """
    A class for interacting with the Radiko API.
    """
    def __init__(self):
        self.title = []
        self.url = []
        self.desc = []
        self.info = []
        self.pfm = []
        self.img = []
        self.duration = []
        self.search_url = "https://radiko.jp/v3/api/program/search"
        self.stationlist_url = "https://radiko.jp/v3/station/list/{}.xml"
        self.now_url = "https://radiko.jp/v3/program/now/{}.xml"
        self.weekly_url = "https://radiko.jp/v3/program/station/weekly/{}.xml"
        # self.today_url = 'http://radiko.jp/v3/program/today/{}.xml'
        # self.today_url = today_url.format( station_id )
        # self.tomorrow_url = 'http://radiko.jp/v3/program/tomorrow/{}.xml'
        # self.tomorrow_url = tomorrow_url.format( station_id )

    def get_stationlist(self, area_id="JP13"):
        """
        Get the list of stations for the specified area.

        Args:
            area_id (str): The ID of the area. Defaults to "JP13".

        Returns:
            xml.etree.ElementTree.Element: The XML element representing the station list.
        """
        self.stationlist_url = self.stationlist_url.format(area_id)
        resp = requests.get(self.stationlist_url, timeout=(20, 5))
        if resp.status_code == 200:
            stationlist = ET.fromstring(resp.content.decode("utf-8"))
            return stationlist
        else:
            print(resp.status_code)
            return None

    def is_avail(self, station, area_id="JP13"):
        """
        Check if the specified station is available in the given area.

        Args:
            station (str): The ID of the station.
            area_id (str): The ID of the area. Defaults to "JP13".

        Returns:
            bool: True if the station is available, False otherwise.
        """
        stationlist = self.get_stationlist(area_id)
        for stationid in stationlist.iter("id"):
            if stationid.text == station:
                return True
        return False

    def get_channel(self, area_id="JP13"):
        """
        Get the list of channel IDs and names for the specified area.

        Args:
            area_id (str): The ID of the area. Defaults to "JP13".

        Returns:
            tuple: Two lists containing the channel IDs and names.
        """
        stationlist = self.get_stationlist(area_id)
        idlist = []
        namelist = []
        for stationid in stationlist.iter("id"):
            idlist.append(stationid.text)
        for name in stationlist.iter("name"):
            namelist.append(name.text)
        return idlist, namelist

    def load_now(self, station, area_id="JP13"):
        """
        Load the current program information for the specified station.

        Args:
            station (str): The ID of the station.
            area_id (str): The ID of the area. Defaults to "JP13".

        Returns:
            None
        """
        self.now_url = self.now_url.format(area_id)
        resp = requests.get(self.now_url, timeout=(20, 5))
        if resp.status_code == 200:
            now = ET.fromstring(resp.content.decode("utf-8"))
            xpath = './/station[@id="{}"]//*/{}'
            for elm in now.findall(xpath.format(station, "title")):
                self.title.append(elm.text)
            for elm in now.findall(xpath.format(station, "url")):
                self.url.append(elm.text)
            for elm in now.findall(xpath.format(station, "desc")):
                self.desc.append(elm.text)
            for elm in now.findall(xpath.format(station, "info")):
                self.info.append(elm.text)
            for elm in now.findall(xpath.format(station, "pfm")):
                self.pfm.append(elm.text)
            for elm in now.findall(xpath.format(station, "img")):
                self.img.append(elm.text)
            xpath = f'.//station[@id="{station}"]/progs/prog'
            for elm in now.findall(xpath):
                self.duration.append(elm.attrib["dur"])
        else:
            print(resp.status_code)
            return None

    def load_weekly(self, station, fromtime, totime):
        """
        Load the weekly program information for the specified station and time range.

        Args:
            station (str): The ID of the station.
            fromtime (str): The start time of the range in the format "YYYYMMDDHHMMSS".
            totime (str): The end time of the range in the format "YYYYMMDDHHMMSS".

        Returns:
            None
        """
        self.weekly_url = self.weekly_url.format(station)
        resp = requests.get(self.weekly_url, timeout=(20, 5))
        if resp.status_code == 200:
            weekly = ET.fromstring(resp.content.decode("utf-8"))
            xpath = './/prog[@ft="{}"][@to="{}"]//{}'
            for elm in weekly.findall(xpath.format(fromtime, totime, "title")):
                self.title.append(elm.text)
            for elm in weekly.findall(xpath.format(fromtime, totime, "url")):
                self.url.append(elm.text)
            for elm in weekly.findall(xpath.format(fromtime, totime, "desc")):
                self.desc.append(elm.text)
            for elm in weekly.findall(xpath.format(fromtime, totime, "info")):
                self.info.append(elm.text)
            for elm in weekly.findall(xpath.format(fromtime, totime, "pfm")):
                self.pfm.append(elm.text)
            for elm in weekly.findall(xpath.format(fromtime, totime, "img")):
                self.img.append(elm.text)
            xpath = f'.//prog[@ft="{fromtime}"][@to="{totime}"]'
            for elm in weekly.findall(xpath):
                self.duration.append(elm.attrib["dur"])
        else:
            print(resp.status_code)
            return None

    def load_program(self, station, fromtime, totime, area_id="JP13", now=False):
        """
        Load the program information for the specified station and time range.

        Args:
            station (str): The ID of the station.
            fromtime (str): The start time of the range in the format "YYYYMMDDHHMMSS".
            totime (str): The end time of the range in the format "YYYYMMDDHHMMSS".
            area_id (str): The ID of the area. Defaults to "JP13".
            now (bool): Whether to load the current program. Defaults to False.

        Returns:
            None
        """
        if now:
            return self.load_now(station, area_id)
        else:
            return self.load_weekly(station, fromtime, totime)

    def get_title(self, station, area_id, next_prog=False):
        """
        Get the title of the current or next program for the specified station.

        Args:
            station (str): The ID of the station.
            area_id (str): The ID of the area.
            next_prog (bool): Whether to get the next program. Defaults to False.

        Returns:
            str: The title of the program.
        """
        if next_prog is True:
            index = 1
        else:
            index = 0
        if not self.title:
            self.load_now(station, area_id)
        return self.title[index]

    def get_url(self, station, area_id, next_prog=False):
        """
        Get the URL of the current or next program for the specified station.

        Args:
            station (str): The ID of the station.
            area_id (str): The ID of the area.
            next_prog (bool): Whether to get the next program. Defaults to False.

        Returns:
            str: The URL of the program.
        """
        if next_prog is True:
            index = 1
        else:
            index = 0
        if not self.url:
            self.load_now(station, area_id)
        return self.desc[index]

    def get_desc(self, station, area_id, next_prog=False):
        """
        Get the description of the current or next program for the specified station.

        Args:
            station (str): The ID of the station.
            area_id (str): The ID of the area.
            next_prog (bool): Whether to get the next program. Defaults to False.

        Returns:
            str: The description of the program.
        """
        if next_prog is True:
            index = 1
        else:
            index = 0
        if not self.desc:
            self.load_now(station, area_id)
        return self.desc[index]

    def get_info(self, station, area_id, next_prog=False):
        """
        Get the information of the current or next program for the specified station.

        Args:
            station (str): The ID of the station.
            area_id (str): The ID of the area.
            next_prog (bool): Whether to get the next program. Defaults to False.

        Returns:
            str: The information of the program.
        """
        if next_prog is True:
            index = 1
        else:
            index = 0
        if not self.info:
            self.load_now(station, area_id)
        return self.info[index]

    def get_pfm(self, station, area_id, next_prog=False):
        """
        Get the performer of the current or next program for the specified station.

        Args:
            station (str): The ID of the station.
            area_id (str): The ID of the area.
            next_prog (bool): Whether to get the next program. Defaults to False.

        Returns:
            str: The performer of the program.
        """
        if next_prog is True:
            index = 1
        else:
            index = 0
        if not self.pfm:
            self.load_now(station, area_id)
        return self.pfm[index]

    def get_img(self, station, area_id, next_prog=False):
        """
        Get the image URL of the current or next program for the specified station.

        Args:
            station (str): The ID of the station.
            area_id (str): The ID of the area.
            next_prog (bool): Whether to get the next program. Defaults to False.

        Returns:
            str: The image URL of the program.
        """
        if next_prog is True:
            index = 1
        else:
            index = 0
        if not self.img:
            self.load_now(station, area_id)
        return self.img[index]

    def generate_uid(self):
        """
        Generate a unique ID for the API request.

        Returns:
            str: The generated unique ID.
        """
        rnd = random.random() * 1000000000
        msec = TD.total_seconds(DT.now() - DT(1970, 1, 1)) * 1000
        return hashlib.md5(str(rnd + msec).encode("utf-8")).hexdigest()

    def search(self, keyword="", time="past", area_id="JP13"):
        """
        Search for programs matching the specified keyword.

        Args:
            keyword (str): The keyword to search for.
            area_id (str): The ID of the area. Defaults to "JP13".
            count (int): The number of programs to return. Defaults to 5.
            page (int): The page number of the search results. Defaults to 0.

        Returns:
            list: A list of dictionaries containing the program information.
        """
        params = {
            "key": keyword,
            "filter": time,
            "start_day": "",
            "end_day": "",
            "area_id": area_id,
            "region_id": "",
            "cul_area_id": area_id,
            "page_idx": "0",
            "uid": self.generate_uid(),
            "row_limit": "12",
            "app_id": "pc",
            "action_id": "0",
        }
        response = requests.get(
            "http://radiko.jp/v3/api/program/search", params=params, timeout=(20, 5)
        )
        return json.loads(response.content)

    def authorize(self):
        """
        Performs authentication to obtain a token and key offset for Radiko API access.

        Returns:
            tuple: A tuple containing the authentication token and key offset.
                If authentication fails, None is returned.
        """
        authkey = "bcd151073c03b352e1ef2fd66c32209da9ca0afa"
        headers = {
            "x-radiko-app": "pc_html5",
            "x-radiko-app-version": "0.0.1",
            "x-radiko-device": "pc",
            "x-radiko-user": "dummy_user",
        }
        url = "https://radiko.jp/v2/api/auth1"
        res = requests.get(url, headers=headers, timeout=(20, 5))
        if res.status_code == 200:
            token = res.headers["x-radiko-authtoken"]
            offset = int(res.headers["x-radiko-keyoffset"])
            length = int(res.headers["x-radiko-keylength"])
            partial_key = base64.b64encode(
                authkey[offset : offset + length].encode("ascii")
            ).decode("utf-8")
            headers = {
                "x-radiko-authtoken": token,
                "x-radiko-device": "pc",
                "x-radiko-partialkey": partial_key,
                "x-radiko-user": "dummy_user",
            }
            url = "https://radiko.jp/v2/api/auth2"
            res = requests.get(url, headers=headers, timeout=(20, 5))
            if res.status_code == 200:
                return token, res.text.split(",")[0]
            else:
                print(f"authorize errr at phase#2 : {res.status_code}")
                return None
        else:
            print(f"authorize errr at phase#1 : {res.status_code}")
            return None

    def dump(self):
        """ dump class member var. for debug """
        print("Title: ", *self.title, sep="\n")
        print("Url: ", *self.url, sep="\n")
        print("Desc: ", *self.desc, sep="\n")
        print("Info: ", *self.info, sep="\n")
        print("Pfm: ", *self.pfm, sep="\n")
        print("Img: ", *self.img, sep="\n")
        print("Duration: ", *self.duration, sep="\n")


if __name__ == "__main__":
    main = Radikoapi()

    print(main.is_avail("TBS"))
    print(main.is_avail("TXS"))

    print("--------------------")
    ids, names = main.get_channel()
    for i, station_id in enumerate(ids):
        print(f"{i} station : {station_id}\t\tname : {names[i]}")
    print("--------------------")

    main.get_now("JOAK-FM")
    main.dump()
    # result = main.search('黒田 卓也')
    result = main.search("生島ヒロシ")
    for d in result["data"]:
        print(
            d["title"],
            d["station_id"],
            re.sub("[-: ]", "", d["start_time"]),
            re.sub("[-: ]", "", d["end_time"]),
        )
    # print( json.dumps( result, indent=4 ) )

    main.load_program("TBS", "20230509050000", "20230509063000")
    main.load_program("TBS", None, None, "JP13", now=True)
    main.dump()
