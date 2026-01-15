#!/usr/bin/python3
# coding: utf-8
"""
This module provides a class for performing radiko api.
"""
from datetime import datetime as DT
from datetime import timedelta as TD
import xml.etree.ElementTree as ET
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
        #self.today_url = 'http://radiko.jp/v3/program/today/{}.xml'
        self.today_url = "http://radiko.jp/v3/program/station/date/{}/{}.xml"
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
        stationlist_url = self.stationlist_url.format(area_id)
        resp = requests.get(stationlist_url, timeout=(20, 5))
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

    def set_member(self, prog, xpath):
        """
        Set the program information by xpath.

        Args:
            prog (xml): xml data of weekly or now program.
            xpath(str): xpath string.

        Returns:
            None
        """
        for elm in prog.findall(xpath):
            self.duration.append(elm.attrib["dur"])
        xpath = xpath + '/{}'
        for elm in prog.findall(xpath.format("title")):
            self.title.append(elm.text)
        for elm in prog.findall(xpath.format("url")):
            self.url.append(elm.text)
        for elm in prog.findall(xpath.format("desc")):
            self.desc.append(elm.text)
        for elm in prog.findall(xpath.format("info")):
            self.info.append(elm.text)
        for elm in prog.findall(xpath.format("pfm")):
            self.pfm.append(elm.text)
        for elm in prog.findall(xpath.format("img")):
            self.img.append(elm.text)

#    def load_now(self, station, fromtime, area_id="JP13"):
#        """
#        Load the current program information for the specified station.
#
#        Args:
#            station (str): The ID of the station.
#            fromtime(str): The start time of the range in the format "YYYYMMDDHHMMSS".
#            area_id (str): The ID of the area. Defaults to "JP13".
#
#        Returns:
#            None if not found or fail
#            True if found
#        """
#        now_url = self.now_url.format(area_id)
#        resp = requests.get(now_url, timeout=(20, 5))
#        if resp.status_code == 200:
#            #print( "======Response=====" )
#            #print( resp.content.decode("utf-8") )
#            now = ET.fromstring(resp.content.decode("utf-8"))
#            xpath = f'.//station[@id="{station}"]//progs/prog[@ft="{fromtime}"]'
#            if now.find(xpath) is None:
#                print( f"Fromtime={fromtime} not found. overwriten." )
#                xpath = f'.//station[@id="{station}"]//progs/prog'
#                if now.find(xpath) is None:
#                    return None
#            self.set_member(now, xpath)
#            return True
#        else:
#            print(resp.status_code)
#            return None

    def load_today(self, station, current, area_id="JP13"):
        """
        今日の番組表を取得して current に一致する番組を set_member する。
        station: 局ID (例: "INT")
        current: YYYYMMDDHHMMSS 文字列（録音開始時刻など）
        """
        url = self.today_url.format(current[:8],station)
        print( url )
        resp = requests.get(url, timeout=(20, 5))
        if resp.status_code != 200:
            print(f"Error: {resp.status_code}")
            return None

        root = ET.fromstring(resp.content.decode("utf-8"))
        progs = root.findall(f'.//station[@id="{station}"]//progs/prog')
        if not progs:
            print("No programs found for today.")
            return None

        # ft/to の範囲に current が入る番組を探す
        for prog in progs:
            ft = prog.attrib.get("ft")
            to = prog.attrib.get("to")
            if ft and to and ft <= current < to:
                title_elem = prog.find("title")
                pfm_elem = prog.find("pfm")
                info_elem = prog.find("info")

                title = title_elem.text if title_elem is not None else ""
                pfm = pfm_elem.text if pfm_elem is not None else ""
                info = info_elem.text if info_elem is not None else ""

                # ログ出力
                print("=== Program Found (today) ===")
                print(f"Current time: {current}")
                print(f"Station: {station}")
                print(f"From: {ft}")
                print(f"To:   {to}")
                print(f"Title: {title}")
                print(f"Pfm:   {pfm}")
                print("=============================")

                # set_member に渡す
                xpath = f'.//station[@id="{station}"]//progs/prog[@ft="{ft}"]'
                self.set_member(root, xpath)
                return True

        print("No program found in today's schedule for current time.")
        return None


    def load_now(self, station, fromtime, area_id="JP13"):
        now_url = self.now_url.format(area_id)
        resp = requests.get(now_url, timeout=(20, 5))
        if resp.status_code != 200:
            print(resp.status_code)
            return None

        now = ET.fromstring(resp.content.decode("utf-8"))

        # 現在時刻を JST の文字列と比較できるように整形
        # current = DT.now().strftime("%Y%m%d%H%M%S")
        print( DT.now().strftime("%Y%m%d%H%M%S") )
        current = fromtime

        # station の prog を全部取得
        progs = now.findall(f'.//station[@id="{station}"]//progs/prog')
        if not progs:
            return None

        # ft, to の範囲に現在時刻が入っているものを探す
        for prog in progs:
            ft = prog.attrib.get("ft")  # 例: "20251117090000"
            to = prog.attrib.get("to")  # 例: "20251117100000"
            print(f"From: {ft}")
            print(f"To:   {to}")
            print(f"Compare: {ft} <= {current} < {to} ? {ft <= current < to}")
            if ft and to and ft <= current < to:
               title_elem = prog.find("title")
               pfm_elem = prog.find("pfm")
               info_elem = prog.find("info")

               title = title_elem.text if title_elem is not None else ""
               pfm = pfm_elem.text if pfm_elem is not None else ""
               info = info_elem.text if info_elem is not None else ""

               # ★ログ出力（主要データ）
               print("=== Current Program Found ===")
               print(f"Current time: {current}")
               print(f"Station: {station}")
               print(f"From: {ft}")
               print(f"To:   {to}")
               print(f"Title: {title}")
               print(f"Pfm:   {pfm}")
               print("=============================")
               # 範囲内にある番組を採用
               xpath = f'.//station[@id="{station}"]//progs/prog[@ft="{ft}"]'
               self.set_member(now, xpath)
               return True

        print("No program found in current time range.")
        return None

    def load_weekly(self, station, fromtime, totime):
        """
        Load the weekly program information for the specified station and time range.

        Args:
            station (str): The ID of the station.
            fromtime (str): The start time of the range in the format "YYYYMMDDHHMMSS".
            totime (str): The end time of the range in the format "YYYYMMDDHHMMSS".

        Returns:
            None if not found or fail
            True if found
        """
        weekly_url = self.weekly_url.format(station)
        resp = requests.get(weekly_url, timeout=(20, 5))
        if resp.status_code == 200:
            weekly = ET.fromstring(resp.content.decode("utf-8"))
            if totime is None:
                xpath = f'.//prog[@ft="{fromtime}"]'
                if weekly.find(xpath) is None:
                    return None
                xpath = xpath.format(fromtime)
                self.set_member(weekly, xpath)
            else:
                xpath = f'.//prog[@ft="{fromtime}"][@to="{totime}"]'
                self.set_member(weekly, xpath)
            return True
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
            return self.load_today(station, fromtime, area_id)
            #result = self.load_now(station, fromtime, area_id)
            #if result is None:
            #    return self.load_today(station, fromtime, area_id)
            #return result
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
                authkey[offset: offset + length].encode("ascii")
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
    api = Radikoapi()

    print(api.is_avail("TBS"))
    print(api.is_avail("TXS"))

    print("--------------------")
    ids, names = api.get_channel()
    for i, station_id in enumerate(ids):
        print(f"{i} station : {station_id}\t\tname : {names[i]}")
    print("--------------------")

    # result = api.search('黒田 卓也')
    result = api.search("生島ヒロシ")
    for d in result["data"]:
        print(
            d["title"],
            d["station_id"],
            re.sub("[-: ]", "", d["start_time"]),
            re.sub("[-: ]", "", d["end_time"]),
        )
    # print( json.dumps( result, indent=4 ) )

    api.load_program("TBS", "20230529050000", "20230529063000")
    api.dump()

    fromt = DT.now().strftime("%Y%m%d%H%M00")
    # api.load_program("TBS", fromt, None, now=True)
    api.load_program("TBS", "20230605190000", None, now=True)
    api.dump()
