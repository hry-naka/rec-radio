"""Radiko API client module for radio program management.

This module provides a stateless API client for interacting with the Radiko
radio streaming service. It handles authentication, program retrieval, and
station information queries.
"""

import base64
import re
import xml.etree.ElementTree as ET
from datetime import datetime as DT
from datetime import timedelta as TD
from typing import List, Optional, Tuple

import requests

from .program import Program


class RadikoAPIClient:
    """Stateless client for Radiko API interactions.

    This class provides methods for authentication, station information
    retrieval, and program data fetching from the Radiko API.
    """

    # API endpoints
    STATION_LIST_URL = "https://radiko.jp/v3/station/list/{}"
    NOW_URL = "https://radiko.jp/v3/program/now/{}"
    WEEKLY_URL = "https://radiko.jp/v3/program/station/weekly/{}"
    DATE_URL = "http://radiko.jp/v3/program/station/date/{}/{}"
    AUTH_KEY = "bcd151073c03b352e1ef2fd66c32209da9ca0afa"
    AUTH1_URL = "https://radiko.jp/v2/api/auth1"
    AUTH2_URL = "https://radiko.jp/v2/api/auth2"
    STREAM_URL = "https://f-radiko.smartstream.ne.jp/{}"
    AREA_URL = "https://radiko.jp/v2/api/area"

    def __init__(self):
        """Initialize API client."""
        pass

    def get_current_area_id(self) -> str:
        """Get the current area ID based on the user's location."""
        try:
            # area_code get endpoint that Radiko uses for area detection
            url = self.AREA_URL
            headers = {"User-Agent": "Mozilla/5.0"}

            # send request to get area information
            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()  # 4xx, 5xx エラーがあれば例外を発生させる

            # analyze the XML text of the response
            root = ET.fromstring(response.text)

            # retrieve area ID from <area id="JP13" name="TOKYO JAPAN">... 
            return root.attrib.get("id", "JP13")

        except Exception:
            # if error, default error (timeout or network disconnection etc.) then return default JP13 (Tokyo)
            return "JP13"

    def get_station_list(self, area_id: str = "JP13") -> Optional[ET.Element]:
        """Get the list of stations for the specified area.

        Args:
            area_id: The ID of the area. Defaults to "JP13".

        Returns:
            XML element representing the station list, or None if failed.
        """
        station_list_url = f"{self.STATION_LIST_URL.format(area_id)}.xml"
        try:
            resp = requests.get(station_list_url, timeout=(20, 5))
            if resp.status_code == 200:
                return ET.fromstring(resp.content.decode("utf-8"))
            else:
                print(f"Error fetching station list: {resp.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Error fetching station list: {e}")
            return None

    def get_channel_list(self, area_id: str = "JP13") -> Tuple[List[str], List[str]]:
        """Get the list of channel IDs and names for the specified area.

        Args:
            area_id: Area ID. Defaults to "JP13".

        Returns:
            Tuple of (channel IDs list, channel names list).
        """
        station_list = self.get_station_list(area_id)
        id_list = []
        name_list = []
        if station_list is not None:
            for station_id in station_list.iter("id"):
                id_list.append(station_id.text)
            for name in station_list.iter("name"):
                name_list.append(name.text)
        return id_list, name_list

    def is_station_available(self, station: str, area_id: str = "JP13") -> bool:
        """Check if the specified station is available in the given area.

        Args:
            station: Station ID
            area_id: Area ID. Defaults to "JP13".

        Returns:
            True if the station is available, False otherwise.
        """
        station_list = self.get_station_list(area_id)
        if station_list is None:
            return False
        for station_elem in station_list.iter("id"):
            if station_elem.text == station:
                return True
        return False

    def _gettext(self, elem) -> str:
        """Extract text content from an XML element, including child elements.

        Args:
            elem: XML element to extract text from.

        Returns:
            Concatenated text content as a string.
        """
        if elem is None:
            return ""
        parts = []
        if elem.text:
            parts.append(elem.text)
        for child in elem:
            if child.text:
                parts.append(child.text)
            if child.tail:
                parts.append(child.tail)
        return "".join(parts)


    def _get_genre_from_xml(self, genre_element: ET.Element) -> str:
        
        """get string from <genre> tag
        
        Args:
            genre_element: ET.Element object of <genre>
        Returns:
            string separated by space
        """
        if genre_element is None:
            return ""

        genres = []
        for child in genre_element:
            name_element = child.find("name")
            if name_element is not None and name_element.text:
                genres.append(name_element.text.strip())
        return " ".join(genres)


    def _extract_program_from_xml(
        self,
        root: ET.Element,
        station: str,
        ft: str,
    ) -> Optional[Program]:
        """Extract program information from XML element.

        Args:
            root: XML root element
            station: Station ID
            ft: Program start time (ft attribute)

        Returns:
            Program object or None if not found.
        """
        prog_elem = root.find(f'.//station[@id="{station}"]//progs/prog[@ft="{ft}"]')
        if prog_elem is None:
            return None

        title_elem = prog_elem.find("title")
        pfm_elem = prog_elem.find("pfm")
        genre_elem = prog_elem.find("genre")
        desc_elem = prog_elem.find("desc")
        info_elem = prog_elem.find("info")
        img_elem = prog_elem.find("img")
        url_elem = prog_elem.find("url")

        title = self._gettext(title_elem)
        performer = self._gettext(pfm_elem)
        genre = self._get_genre_from_xml(genre_elem)
        description = self._gettext(desc_elem)
        info = self._gettext(info_elem)
        image_url = self._gettext(img_elem)
        url = self._gettext(url_elem)

        ft_attr = prog_elem.attrib.get("ft", "")
        to_attr = prog_elem.attrib.get("to", "")
        dur = int(prog_elem.attrib.get("dur", 0))

        return Program(
            title=title,
            station=station,
            genre=genre,
            area="JP13",  # Default, could be parameterized
            start_time=ft_attr,
            end_time=to_attr,
            duration=dur,
            performer=performer,
            description=description,
            info=info,
            image_url=image_url,
            url=url,
        )

    def _fetch_program_xml(
        self, mode: str, station: str, from_time: str, area_id: str = "JP13"
    ) -> Optional[ET.Element]:
        if mode == "now":
            url = f"{self.NOW_URL.format(area_id)}.xml"
        elif mode == "date":
            url = f"{self.DATE_URL.format(from_time[:8], station)}.xml"
        elif mode == "weekly":
            url = f"{self.WEEKLY_URL.format(station)}.xml"
        else:
            raise ValueError("Invalid mode")

        resp = requests.get(url, timeout=(20, 5))
        if resp.status_code != 200:
            return None
        return ET.fromstring(resp.content.decode("utf-8"))

    def _find_program(
        self, root: ET.Element, station: str, from_time: str
    ) -> Optional[Program]:
        progs = root.findall(f'.//station[@id="{station}"]//progs/prog')
        for prog in progs:
            ft = prog.attrib.get("ft")
            to = prog.attrib.get("to")
            if ft and to and ft <= from_time < to:
                return self._extract_program_from_xml(root, station, ft)
        return None

    def fetch_now_program(
        self, station: str, from_time: str, area_id: str = "JP13"
    ) -> Optional[Program]:
        root = self._fetch_program_xml("now", station, from_time, area_id)
        return self._find_program(root, station, from_time)

    def fetch_date_program(
        self, station: str, from_time: str, area_id: str = "JP13"
    ) -> Optional[Program]:
        root = self._fetch_program_xml("date", station, from_time, area_id)
        return self._find_program(root, station, from_time)

    def fetch_weekly_program(
        self, station: str, from_time: str, area_id: str = "JP13"
    ) -> Optional[Program]:
        root = self._fetch_program_xml("weekly", station, from_time, area_id)
        return self._find_program(root, station, from_time)

    def fetch_program(
        self, station: str, from_time: str, area_id: str = "JP13", now: bool = False
    ) -> Optional[Program]:

        # now-API (try to get from now-API)
        if now:
            prog = self.fetch_now_program(station, from_time, area_id)
            if prog:
                return prog

        today = DT.now().strftime("%Y%m%d")

        # before today use date-API
        if from_time[:8] <= today:
            return self.fetch_date_program(station, from_time, area_id)

        # after today use weekly-API
        return self.fetch_weekly_program(station, from_time, area_id)

    def search_past_week(
        self,
        keyword: str = "",
        area_id: str = "JP13",
    ) -> List[Program]:
        """Search programs from the past seven days across all stations.

        Args:
            keyword: Keyword to search in program titles and descriptions.
            area_id: Area ID. Defaults to "JP13".

        Returns:
            List of matching program objects.
        """
        today = DT.today()
        dates = [(today - TD(days=i)).strftime("%Y%m%d") for i in range(7)]

        root = self.get_station_list(area_id)
        stations = [st.find("id").text for st in root.findall(".//station")]
        results = []

        for date in dates:
            print(f"try to search program on {date}.", end="", flush=True)
            for station in stations:
                url = f"{self.DATE_URL.format(date, station)}.xml"
                try:
                    res = requests.get(url, timeout=10)
                    if res.status_code != 200:
                        continue
                    root = ET.fromstring(res.content)

                    for prog in root.findall(".//prog"):
                        title_elem = prog.find("title")
                        info_elem = prog.find("info")

                        title = self._gettext(title_elem)
                        info = self._gettext(info_elem)
                        ft = prog.get("ft")

                        if keyword in title or keyword in info:
                            print("/", end="", flush=True)
                            program = self._extract_program_from_xml(root, station, ft)
                            if program:
                                results.append(program)

                except Exception:
                    continue
            print("done.", flush=True)
        return results

    def get_stream_url(self, channel: str, auth_token: str) -> Optional[str]:
        """Retrieve M3U8 stream URL from Radiko server.

        Args:
            channel: Channel ID
            auth_token: Authentication token

        Returns:
            Stream URL string, or None if failed.
        """
        stream_url = self.STREAM_URL.format(channel)
        stream_url += "/_definst_/simul-stream.stream/playlist.m3u8"
        headers = {
            "X-Radiko-AuthToken": auth_token,
        }
        try:
            resp = requests.get(stream_url, headers=headers, timeout=(20, 5))
            if resp.status_code == 200:
                # Extract M3U8 URL from response body
                lines = re.findall("^https?://.+m3u8$", resp.text, flags=re.MULTILINE)
                if lines:
                    return lines[0]
                print("Error: No M3U8 URL found in response.")
                return None
            else:
                print(
                    f"Error: Failed to get stream URL " f"(status {resp.status_code})"
                )
                return None
        except requests.exceptions.RequestException as e:
            print(f"Error fetching stream URL: {e}")
            return None

    def authorize(self) -> Optional[Tuple[str, str]]:
        """Perform Radiko API authentication.

        Returns two-step OAuth-like authentication to obtain token and area ID.

        Returns:
            Tuple of (auth_token, area_id) or None if authentication failed.
        """
        # Step 1: Get initial token and key offset
        headers = {
            "x-radiko-app": "pc_html5",
            "x-radiko-app-version": "0.0.1",
            "x-radiko-device": "pc",
            "x-radiko-user": "dummy_user",
        }
        try:
            res = requests.get(self.AUTH1_URL, headers=headers, timeout=(20, 5))
            if res.status_code != 200:
                print(f"Authorization error (phase 1): " f"{res.status_code}")
                return None

            token = res.headers["x-radiko-authtoken"]
            offset = int(res.headers["x-radiko-keyoffset"])
            length = int(res.headers["x-radiko-keylength"])

            # Step 2: Compute partial key and request second token
            partial_key = base64.b64encode(
                self.AUTH_KEY[offset : offset + length].encode("ascii")
            ).decode("utf-8")

            headers = {
                "x-radiko-authtoken": token,
                "x-radiko-device": "pc",
                "x-radiko-partialkey": partial_key,
                "x-radiko-user": "dummy_user",
            }
            res = requests.get(self.AUTH2_URL, headers=headers, timeout=(20, 5))
            if res.status_code != 200:
                print(f"Authorization error (phase 2): " f"{res.status_code}")
                return None

            area_id = res.text.split(",")[0]
            return token, area_id
        except requests.exceptions.RequestException as e:
            print(f"Authorization error: {e}")
            return None
