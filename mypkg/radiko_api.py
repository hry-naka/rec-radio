"""Radiko API client module for radio program management.

This module provides a stateless API client for interacting with the Radiko
radio streaming service. It handles authentication, program retrieval, and
station information queries.

Attributes:
    BASE_URL (str): Base URL for Radiko API endpoints.
    DEFAULT_TIMEOUT (int): Default timeout for API requests in seconds.
"""

import base64
import hashlib
import json
import random
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime as DT
from datetime import timedelta as TD
from typing import Any, Dict, List, Optional, Tuple

import requests

from .program import Program


class RadikoApiError(Exception):
    """Base exception for Radiko API errors."""

    pass


class RadikoApiHttpError(RadikoApiError):
    """Exception raised for HTTP/network errors."""

    pass


class RadikoApiXmlError(RadikoApiError):
    """Exception raised for XML parsing errors."""

    pass


class RadikoApi:
    """Stateless client for Radiko API interactions.

    This class provides methods for authentication, station information
    retrieval, and program data fetching from the Radiko API.

    Attributes:
        BASE_SEARCH_URL (str): Base URL for program search.
        BASE_STATION_URL (str): Base URL for station list.
        BASE_PROGRAM_URL (str): Base URL for program data.
        DEFAULT_TIMEOUT (int): Default timeout in seconds.
    """

    # API endpoints
    BASE_SEARCH_URL = "https://radiko.jp/v3/api/program/search"
    BASE_STATION_URL = "https://radiko.jp/v3/station/list/{}.xml"
    BASE_PROGRAM_NOW_URL = "https://radiko.jp/v3/program/now/{}.xml"
    BASE_PROGRAM_WEEKLY_URL = "https://radiko.jp/v3/program/station/weekly/{}.xml"
    BASE_PROGRAM_DATE_URL = "http://radiko.jp/v3/program/station/date/{}/{}.xml"
    BASE_STREAM_URL = "https://f-radiko.smartstream.ne.jp/{}"
    AUTH1_URL = "https://radiko.jp/v2/api/auth1"
    AUTH2_URL = "https://radiko.jp/v2/api/auth2"
    AUTH_KEY = "bcd151073c03b352e1ef2fd66c32209da9ca0afa"
    DEFAULT_TIMEOUT = 10
    DEFAULT_AREA_ID = "JP13"

    def __init__(self, timeout: int = DEFAULT_TIMEOUT) -> None:
        """Initialize Radiko API client.

        Args:
            timeout: Request timeout in seconds. Defaults to 10.

        Raises:
            ValueError: If timeout is not positive.
        """
        if timeout <= 0:
            raise ValueError("Timeout must be positive")
        self.timeout = timeout

    def get_station_list(self, area_id: str = DEFAULT_AREA_ID) -> Optional[ET.Element]:
        """Get the list of stations for the specified area.

        Args:
            area_id: Area ID. Defaults to "JP13".

        Returns:
            XML root element representing the station list, or None if failed.

        Raises:
            RadikoApiHttpError: If HTTP request fails.
            RadikoApiXmlError: If XML parsing fails.
        """
        url = self.BASE_STATION_URL.format(area_id)
        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise RadikoApiHttpError(f"HTTP request failed: {e}") from e

        try:
            return ET.fromstring(response.content)
        except ET.ParseError as e:
            raise RadikoApiXmlError(f"XML parsing failed: {e}") from e

    def is_station_available(
        self, station: str, area_id: str = DEFAULT_AREA_ID
    ) -> bool:
        """Check if the specified station is available in the given area.

        Args:
            station: Station ID.
            area_id: Area ID. Defaults to "JP13".

        Returns:
            True if the station is available, False otherwise.

        Raises:
            RadikoApiError: If station list retrieval fails.
        """
        station_list = self.get_station_list(area_id)
        if station_list is None:
            return False

        for station_elem in station_list.iter("id"):
            if station_elem.text == station:
                return True

        return False

    def get_channel_list(
        self, area_id: str = DEFAULT_AREA_ID
    ) -> Tuple[List[str], List[str]]:
        """Get the list of channel IDs and names for the specified area.

        Args:
            area_id: Area ID. Defaults to "JP13".

        Returns:
            Tuple of (channel IDs list, channel names list).

        Raises:
            RadikoApiError: If station list retrieval fails.
        """
        station_list = self.get_station_list(area_id)
        id_list = []
        name_list = []

        if station_list is not None:
            for id_elem in station_list.iter("id"):
                if id_elem.text:
                    id_list.append(id_elem.text)

            for name_elem in station_list.iter("name"):
                if name_elem.text:
                    name_list.append(name_elem.text)

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
        area_id: str = DEFAULT_AREA_ID,
    ) -> Optional[Program]:
        """Fetch today's program schedule and find the program at current time.

        Args:
            station: Station ID.
            current_time: Current time in YYYYMMDDHHMMSS format.
            area_id: Area ID. Defaults to "JP13".

        Returns:
            Program object if found, None otherwise.

        Raises:
            RadikoApiHttpError: If HTTP request fails.
            RadikoApiXmlError: If XML parsing fails.
        """
        url = self.BASE_PROGRAM_DATE_URL.format(current_time[:8], station)
        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise RadikoApiHttpError(f"HTTP request failed: {e}") from e

        try:
            root = ET.fromstring(response.content)
            return self._extract_program_from_xml(root, station, current_time[:8])
        except ET.ParseError as e:
            raise RadikoApiXmlError(f"XML parsing failed: {e}") from e

    def fetch_now_program(
        self,
        station: str,
        area_id: str = DEFAULT_AREA_ID,
    ) -> Optional[Program]:
        """Fetch now-on-air program information.

        Args:
            station: Station ID.
            area_id: Area ID. Defaults to "JP13".

        Returns:
            Program object if found, None otherwise.

        Raises:
            RadikoApiHttpError: If HTTP request fails.
            RadikoApiXmlError: If XML parsing fails.
        """
        url = self.BASE_PROGRAM_NOW_URL.format(station)
        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise RadikoApiHttpError(f"HTTP request failed: {e}") from e

        try:
            root = ET.fromstring(response.content)
            # Find the first program element
            prog_elem = root.find(".//prog")
            if prog_elem is None:
                return None

            return self._extract_program_from_element(prog_elem, station)
        except ET.ParseError as e:
            raise RadikoApiXmlError(f"XML parsing failed: {e}") from e

    def fetch_weekly_program(
        self,
        station: str,
    ) -> Optional[Program]:
        """Fetch weekly program schedule.

        Args:
            station: Station ID.

        Returns:
            Program object if found, None otherwise.

        Raises:
            RadikoApiHttpError: If HTTP request fails.
            RadikoApiXmlError: If XML parsing fails.
        """
        url = self.BASE_PROGRAM_WEEKLY_URL.format(station)
        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise RadikoApiHttpError(f"HTTP request failed: {e}") from e

        try:
            root = ET.fromstring(response.content)
            prog_elem = root.find(".//prog")
            if prog_elem is None:
                return None

            return self._extract_program_from_element(prog_elem, station)
        except ET.ParseError as e:
            raise RadikoApiXmlError(f"XML parsing failed: {e}") from e

    def get_stream_url(self, channel: str, auth_token: str) -> Optional[str]:
        """Retrieve M3U8 stream URL from Radiko server.

        Args:
            channel: Channel ID.
            auth_token: Authentication token.

        Returns:
            Stream URL string, or None if failed.

        Raises:
            RadikoApiHttpError: If HTTP request fails.
        """
        url = self.BASE_STREAM_URL.format(channel)
        try:
            response = requests.get(
                url,
                headers={"X-Radiko-AuthToken": auth_token},
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.text.strip()
        except requests.exceptions.RequestException as e:
            raise RadikoApiHttpError(f"Stream URL retrieval failed: {e}") from e

    def authorize(self) -> Optional[Tuple[str, str]]:
        """Perform Radiko authentication.

        Executes two-step authentication to obtain auth token and area ID.

        Returns:
            Tuple of (auth_token, area_id) if successful, None otherwise.

        Raises:
            RadikoApiHttpError: If HTTP request fails.
        """
        try:
            # Step 1: Initial auth request
            response1 = requests.post(self.AUTH1_URL, timeout=self.timeout)
            response1.raise_for_status()
            auth_token = response1.headers.get("X-Radiko-AuthToken")

            if not auth_token:
                return None

            # Step 2: Get area ID
            response2 = requests.get(
                self.AUTH2_URL,
                headers={"X-Radiko-AuthToken": auth_token},
                timeout=self.timeout,
            )
            response2.raise_for_status()
            area_id = response2.text.strip()

            return (auth_token, area_id)

        except requests.exceptions.RequestException as e:
            raise RadikoApiHttpError(f"Authorization failed: {e}") from e

    def search_programs(
        self,
        keyword: str = "",
        time_filter: str = "past",
        area_id: str = DEFAULT_AREA_ID,
    ) -> Dict[str, Any]:
        """Search programs by keyword.

        Args:
            keyword: Search keyword.
            time_filter: Time filter ("past", "today", "future"). Defaults to "past".
            area_id: Area ID. Defaults to "JP13".

        Returns:
            Search results as dictionary.

        Raises:
            RadikoApiHttpError: If HTTP request fails.
            RadikoApiJsonError: If response parsing fails.
        """
        params = {
            "keyword": keyword,
            "time_filter": time_filter,
            "area_id": area_id,
        }
        try:
            response = requests.get(
                self.BASE_SEARCH_URL, params=params, timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise RadikoApiHttpError(f"Program search failed: {e}") from e
        except ValueError as e:
            raise RadikoApiXmlError(f"JSON parsing failed: {e}") from e

    def dump(self) -> None:
        """Dump API client status (for debugging).

        Note: RadikoApi is stateless, so this only shows configuration.
        """
        print(f"RadikoApi(timeout={self.timeout}s)")

    @staticmethod
    def _extract_program_from_element(
        prog_elem: ET.Element, station: str
    ) -> Optional[Program]:
        """Extract program information from XML prog element.

        Args:
            prog_elem: XML prog element.
            station: Station ID.

        Returns:
            Program object or None if required fields are missing.

        Raises:
            RadikoApiXmlError: If extraction fails.
        """
        try:
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
                area="JP13",
                start_time=ft_attr,
                end_time=to_attr,
                duration=dur,
                performer=performer,
                description=description,
                info=info,
                image_url=image_url,
                url=url,
            )
        except (KeyError, ValueError, AttributeError) as e:
            raise RadikoApiXmlError(f"Program extraction failed: {e}") from e


if __name__ == "__main__":
    """Simple operational check for RadikoApi."""
    client = RadikoApi()

    # Authorize
    print("Authorizing...")
    try:
        auth_result = client.authorize()
        if auth_result is None:
            print("Authorization failed")
        else:
            auth_token, area_id = auth_result
            print(f"Authorization successful. Area ID: {area_id}")
    except RadikoApiError as e:
        print(f"Authorization error: {e}")
