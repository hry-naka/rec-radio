"""Radiko API client module for radio program management.

This module provides a stateless API client for interacting with the Radiko
radio streaming service. It handles authentication, program retrieval, and
station information queries.
"""

import base64
import hashlib
import json
import random
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
    SEARCH_URL = "https://radiko.jp/v3/api/program/search"
    STATION_LIST_URL = "https://radiko.jp/v3/station/list/{}.xml"
    NOW_URL = "https://radiko.jp/v3/program/now/{}.xml"
    WEEKLY_URL = "https://radiko.jp/v3/program/station/weekly/{}.xml"
    TODAY_URL = "http://radiko.jp/v3/program/station/date/{}/{}.xml"
    AUTH_KEY = "bcd151073c03b352e1ef2fd66c32209da9ca0afa"
    AUTH1_URL = "https://radiko.jp/v2/api/auth1"
    AUTH2_URL = "https://radiko.jp/v2/api/auth2"
    STREAM_URL = "https://f-radiko.smartstream.ne.jp/{}"

    def __init__(self):
        """Initialize API client."""
        pass

    def get_station_list(self, area_id: str = "JP13") -> Optional[ET.Element]:
        """Get the list of stations for the specified area.

        Args:
            area_id: The ID of the area. Defaults to "JP13".

        Returns:
            XML element representing the station list, or None if failed.
        """
        station_list_url = self.STATION_LIST_URL.format(area_id)
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
        desc_elem = prog_elem.find("desc")
        info_elem = prog_elem.find("info")
        img_elem = prog_elem.find("img")
        url_elem = prog_elem.find("url")

        title = title_elem.text if title_elem is not None else ""
        performer = pfm_elem.text if pfm_elem is not None else None
        description = desc_elem.text if desc_elem is not None else None
        info = info_elem.text if info_elem is not None else None
        image_url = img_elem.text if img_elem is not None else None
        url = url_elem.text if url_elem is not None else None

        ft_attr = prog_elem.attrib.get("ft", "")
        to_attr = prog_elem.attrib.get("to", "")
        dur = int(prog_elem.attrib.get("dur", 0))

        return Program(
            title=title,
            station=station,
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

    def fetch_today_program(
        self,
        station: str,
        current_time: str,
        area_id: str = "JP13",
    ) -> Optional[Program]:
        """Fetch today's program schedule and find the program at current time.

        Args:
            station: Station ID
            current_time: Current time in YYYYMMDDHHMMSS format
            area_id: Area ID. Defaults to "JP13".

        Returns:
            Program object if found, None otherwise.
        """
        url = self.TODAY_URL.format(current_time[:8], station)
        print(f"Fetching: {url}")
        try:
            resp = requests.get(url, timeout=(20, 5))
            if resp.status_code != 200:
                print(f"Error: {resp.status_code}")
                return None

            root = ET.fromstring(resp.content.decode("utf-8"))
            progs = root.findall(f'.//station[@id="{station}"]//progs/prog')

            if not progs:
                print("No programs found for today.")
                return None

            # Find program containing current_time
            for prog in progs:
                ft = prog.attrib.get("ft")
                to = prog.attrib.get("to")
                if ft and to and ft <= current_time < to:
                    print(
                        f"Current program found: {ft}-{to} "
                        f"(current: {current_time})"
                    )
                    return self._extract_program_from_xml(root, station, ft)

            print(f"No program found for current time: {current_time}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Error fetching program: {e}")
            return None

    def fetch_now_program(
        self,
        station: str,
        current_time: str,
        area_id: str = "JP13",
    ) -> Optional[Program]:
        """Fetch now-on-air program information.

        Args:
            station: Station ID
            current_time: Current time in YYYYMMDDHHMMSS format
            area_id: Area ID. Defaults to "JP13".

        Returns:
            Program object if found, None otherwise.
        """
        try:
            resp = requests.get(self.NOW_URL.format(area_id), timeout=(20, 5))
            if resp.status_code != 200:
                print(f"Error: {resp.status_code}")
                return None

            root = ET.fromstring(resp.content.decode("utf-8"))
            progs = root.findall(f'.//station[@id="{station}"]//progs/prog')

            if not progs:
                print("No programs found.")
                return None

            # Find program containing current_time
            for prog in progs:
                ft = prog.attrib.get("ft")
                to = prog.attrib.get("to")
                if ft and to and ft <= current_time < to:
                    print(f"Current program: {ft}-{to} " f"(current: {current_time})")
                    return self._extract_program_from_xml(root, station, ft)

            print(f"No program found for current time: {current_time}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Error fetching program: {e}")
            return None

    def fetch_weekly_program(
        self,
        station: str,
        from_time: str,
        to_time: Optional[str] = None,
    ) -> Optional[Program]:
        """Fetch weekly program schedule for specified time range.

        Args:
            station: Station ID
            from_time: Start time in YYYYMMDDHHMMSS format
            to_time: End time in YYYYMMDDHHMMSS format (optional)

        Returns:
            Program object if found, None otherwise.
        """
        weekly_url = self.WEEKLY_URL.format(station)
        try:
            resp = requests.get(weekly_url, timeout=(20, 5))
            if resp.status_code != 200:
                print(f"Error: {resp.status_code}")
                return None

            root = ET.fromstring(resp.content.decode("utf-8"))

            # Find program by time range
            if to_time is None:
                prog_elem = root.find(f'.//prog[@ft="{from_time}"]')
            else:
                prog_elem = root.find(f'.//prog[@ft="{from_time}"][@to="{to_time}"]')

            if prog_elem is None:
                return None

            return self._extract_program_from_xml(root, station, from_time)
        except requests.exceptions.RequestException as e:
            print(f"Error fetching program: {e}")
            return None

    def fetch_program(
        self,
        station: str,
        from_time: str,
        to_time: Optional[str] = None,
        area_id: str = "JP13",
        now: bool = False,
    ) -> Optional[Program]:
        """Fetch program information.

        Args:
            station: Station ID
            from_time: Start time in YYYYMMDDHHMMSS format
            to_time: End time in YYYYMMDDHHMMSS format (optional)
            area_id: Area ID. Defaults to "JP13".
            now: Whether to fetch current program. Defaults to False.

        Returns:
            Program object if found, None otherwise.
        """
        if now:
            return self.fetch_today_program(station, from_time, area_id)
        else:
            return self.fetch_weekly_program(station, from_time, to_time)

    def get_stream_url(self, channel: str, auth_token: str) -> Optional[str]:
        """Retrieve M3U8 stream URL from Radiko server.

        Args:
            channel: Channel ID
            auth_token: Authentication token

        Returns:
            Stream URL string, or None if failed.
        """
        import re

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

    @staticmethod
    def _generate_uid() -> str:
        """Generate a unique ID for API requests.

        Returns:
            Unique ID string.
        """
        rnd = random.random() * 1000000000
        msec = TD.total_seconds(DT.now() - DT(1970, 1, 1)) * 1000
        return hashlib.md5(str(rnd + msec).encode("utf-8")).hexdigest()

    def search_programs(
        self,
        keyword: str = "",
        time_filter: str = "past",
        area_id: str = "JP13",
    ) -> dict:
        """Search for programs matching the specified keyword.

        Args:
            keyword: Search keyword
            time_filter: Time filter (past, now, future)
            area_id: Area ID. Defaults to "JP13".

        Returns:
            Search results as dictionary.
        """
        params = {
            "key": keyword,
            "filter": time_filter,
            "start_day": "",
            "end_day": "",
            "area_id": area_id,
            "region_id": "",
            "cul_area_id": area_id,
            "page_idx": "0",
            "uid": self._generate_uid(),
            "row_limit": "12",
            "app_id": "pc",
            "action_id": "0",
        }
        try:
            response = requests.get(self.SEARCH_URL, params=params, timeout=(20, 5))
            return json.loads(response.content)
        except requests.exceptions.RequestException as e:
            print(f"Error searching programs: {e}")
            return {}

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

    def dump(self) -> None:
        """Dump API statistics (for debugging)."""
        print("Note: RadikoAPIClient is stateless.")


if __name__ == "__main__":
    """Simple operational check for RadikoAPIClient."""
    client = RadikoAPIClient()

    # Authorize
    print("Authorizing...")
    auth_result = client.authorize()
    if auth_result is None:
        print("Authorization failed")
        exit(1)

    auth_token, area_id = auth_result
    print(f"Authorization successful. Area ID: {area_id}")
    print()

    # Fetch and display current program on TBS
    print("Fetching current program on TBS...")
    current_time = DT.now().strftime("%Y%m%d%H%M00")
    program = client.fetch_today_program("TBS", current_time, area_id)

    if program:
        print(f"Title:       {program.title}")
        print(f"Station:     {program.station}")
        print(f"Start time:  {program.start_time}")
        print(f"End time:    {program.end_time}")
        if program.performer:
            print(f"Performer:   {program.performer}")
        if program.description:
            print(f"Description: {program.description}")
    else:
        print("No program found")
