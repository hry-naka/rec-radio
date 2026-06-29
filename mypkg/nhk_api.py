import json
import xml.etree.ElementTree as ET
from datetime import datetime as DT
from typing import Any, Dict, Optional

import requests

from .program import Program


class NhkAPIClient:
    def __init__(
        self,
        api_key: str,
        location: str,
        area_code: str,
        code: str,
        api_version: str = "v3",
    ):
        if api_version != "v3":
            print(
                "Warning: API version is not v3. This application only supports v3. The parameter is ignored."
            )
        self.api_version = "v3"
        self.api_key = api_key
        self.location = location
        self.area_code = area_code
        self.code = code
        # v3のエンドポイントURLを保持
        self.NHK_STREAM_URL = "https://www.nhk.or.jp/radio/config/config_web.xml"
        self.NHK_API_V3_NOW = (
            "https://program-api.nhk.jp/v3/papiPgNowRadio"
            "?service={service}&area={area}&key={key}"
        )
        self.NHK_API_V3_INFO = (
            "https://program-api.nhk.jp/v3/papiBroadcastEventRadio"
            "?broadcastEventId={broadcastEventId}&key={key}"
        )
        self.NHK_XPATHS = {
            "r1": ".//stream_url/data/r1hls",
            "r2": ".//stream_url/data/r2hls",
            "r3": ".//stream_url/data/fmhls",
        }
        self.HTTP_TIMEOUT = (20, 5)
        self.REQUEST_TIMEOUT = 20

    def get_streamurl(self) -> Optional[str]:
        """Retrieve HLS stream URL from NHK XML config.

        Args:
            code: Channel code (r1, r2, r3)

        Returns:
            Stream URL or None if not found
        """
        if self.code not in self.NHK_XPATHS:
            print(f"Error: Channel code '{self.code}' doesn't exist")
            return None

        xpath = self.NHK_XPATHS[self.code]

        try:
            response = requests.get(self.NHK_STREAM_URL, timeout=self.HTTP_TIMEOUT)
            response.raise_for_status()
            root = ET.fromstring(response.content)
        except requests.exceptions.RequestException as e:
            print(f"Error fetching NHK stream config: {e}")
            return None
        except ET.ParseError as e:
            print(f"Error parsing NHK stream config XML: {e}")
            return None

        # Find the stream URL for the specified location
        for child in root.findall(".//stream_url/data/*"):
            if child.tag == "area" and child.text == self.location:
                stream_url = root.findtext(xpath)
                if stream_url:
                    return stream_url
        print(
            f"Error: No stream URL found for channel={self.code}, "
            f"location={self.location}"
        )
        return None

    def _get_title(self, program: Dict[str, Any]) -> str:
        """Get the title of the program, falling back to 'name' if 'title' is not available.

        Args:
            program: Program info dict
        Returns:
            Title of the program or 'name' if 'title' is not available
        """
        return program.get("name", "Unknown Program")

    def _get_station(self, program: Dict[str, Any]) -> Optional[str]:
        """Get the station code of the program.

        Args:
            program: Program info dict
        Returns:
            Station code of the program
        """
        service_name = program.get("publishedOn", {}).get("broadcastDisplayName", {})
        return service_name if service_name else None

    def _get_description(self, program: Dict[str, Any]) -> Optional[str]:
        """Get the description of the program.

        Args:
            program: Program info dict
        Returns:
            Description of the program
        """
        fallback_description = program.get("description", {})
        description = (
            program.get("about", {})
            .get("partOfSeries", {})
            .get("description", fallback_description)
        )
        return description if description else None

    def _get_subtitle(self, program: Dict[str, Any]) -> Optional[str]:
        """Get the subtitle of the program.

        Args:
            program: Program info dict
        Returns:
            Subtitle of the program or None if not available
        """
        subtitle = program.get("about", {}).get("partOfSeries", {}).get("detailedCatch")
        return subtitle if subtitle else None

    def _get_start_time(self, program: Dict[str, Any]) -> Optional[str]:
        """Get the start time of the program in "YYYYMMDDHHMMSS" format.

        Args:
            program: Program info dict
        Returns:
            Start time of the program or None if not available
        """
        start_time = program.get("startDate")
        if start_time:
            try:
                dt = DT.fromisoformat(start_time.replace("Z", "+00:00"))
                return dt.strftime("%Y%m%d%H%M%S")
            except ValueError:
                print(f"Error parsing start time: {start_time}")
                return None
        return None

    def _get_end_time(self, program: Dict[str, Any]) -> Optional[str]:
        """Get the end time of the program in "YYYYMMDDHHMMSS" format.

        Args:
            program: Program info dict
        Returns:
            End time of the program or None if not available
        """
        end_time = program.get("endDate")
        if end_time:
            try:
                dt = DT.fromisoformat(end_time.replace("Z", "+00:00"))
                return dt.strftime("%Y%m%d%H%M%S")
            except ValueError:
                print(f"Error parsing end time: {end_time}")
                return None
        return None

    def _convert_iso_duration(self, duration_str: str) -> int:
        """
        Convert ISO 8601 duration strings like 'PT15M' or 'PT1H30M' to total seconds (int)
        """
        import re

        # define regular expression to match time components
        # ?P<name> allows us to access matched parts by name
        pattern = re.compile(
            r"PT(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?"
        )
        match = pattern.match(duration_str)

        if not match:
            return 0

        # set 0, if not match.
        hours = int(match.group("hours") or 0)
        minutes = int(match.group("minutes") or 0)
        seconds = int(match.group("seconds") or 0)

        # sum up total seconds
        total_seconds = (hours * 3600) + (minutes * 60) + seconds
        return total_seconds

    def _get_duration(self, program: Dict[str, Any]) -> int:
        """Get the duration of the program in seconds.

        Args:
            program: Program info dict
        Returns:
            Duration of the program in seconds or 0 if not available
        """
        duration_str = program.get("duration")
        if not duration_str:
            return 0
        return self._convert_iso_duration(duration_str)

    def _get_performer(self, program: Dict[str, Any]) -> str:
        """Get the performer of the program.

        Args:
            program: Program info dict
        Returns:
            Performer of the program or empty string if not available
        """
        # try to get performer from actList first
        act_list = program.get("misc", {}).get("actList", [])
        performers = [one.get("name") for one in act_list if one.get("name")]

        if performers:
            # if found from actList, return joined string
            return " ".join(performers)

        # fallback
        fallback_desc = program.get("description", "")
        if fallback_desc:
            return fallback_desc.replace("\uff0c", " ").replace("\u3001", " ").strip()

        return ""

    def _get_genre(self, program: Dict[str, Any]) -> str:
        """Get the genre of the program.

        Args:
            program: Program info dict
        Returns:
            Genre of the program or empty string if not available
        """
        id_group = program.get("about", {}).get("identifierGroup", {})

        # if themeGenreTag does not exist, look for the regular genre list
        genre_tags = id_group.get("themeGenreTag") or id_group.get("genre") or []

        genres = [entry.get("name") for entry in genre_tags if entry.get("name")]
        return " ".join(genres)

    def _get_logo_url(self, program: Dict[str, Any]) -> Optional[str]:
        """Get the logo URL of the program.

        Args:
            program: Program info dict
        Returns:
            Logo URL of the program or None if not available
        """
        # set base dictionary for the image location
        eyecatch = program.get("about", {}).get("partOfSeries", {}).get("eyecatch", {})

        # loop through sizes in order of priority
        for size in ["main", "large", "medium", "small"]:
            url = eyecatch.get(size, {}).get("url")
            if url:
                return url  # return the most high-priority URL
        return None  # if no URL found, return None

    def _get_url(self, program: Dict[str, Any]) -> Optional[str]:
        """Get the URL of the program.

        Args:
            program: Program info dict
        Returns:
            URL of the program or None if not available
        """
        return program.get("about", {}).get("canonical", "")

    def fetch_program(self, target_time: DT) -> Optional[Program]:
        """Fetch program information from NHK API with error handling.

        Args:
            target_time: The time for which to get program information

        Returns:
            Program info dict or None if not available
        """
        program_info = self.get_program_info(target_time)
        if not program_info:
            return None

        return Program(
            title=self._get_title(program_info),
            subtitle=self._get_subtitle(program_info),
            station=self._get_station(program_info),
            area=self.area_code,
            description=self._get_description(program_info),
            start_time=self._get_start_time(program_info),
            end_time=self._get_end_time(program_info),
            duration=self._get_duration(program_info),
            genre=self._get_genre(program_info),
            performer=self._get_performer(program_info),
            image_url=self._get_logo_url(program_info),
            url=self._get_url(program_info),
        )

    def get_program_info(self, target_time: DT) -> Optional[Dict[str, Any]]:
        """Get program information from NHK API with error handling.

        Args:
            target_time: The time for which to get program information

        Returns:
            Program info dict or None if not available
        """
        if self.api_version == "v3":
            return self._get_program_info_v3(target_time)
        else:
            # this brach if for future extension, currently only v3 is supported
            return None

    def _get_program_info_v3(self, target_time: DT) -> Optional[Dict[str, Any]]:
        """Get program information from NHK API v3 with error handling."""

        now_url = self.NHK_API_V3_NOW.format(
            service=self.code, area=self.area_code, key=self.api_key
        )

        try:
            resp = requests.get(now_url, timeout=self.HTTP_TIMEOUT)
            resp.raise_for_status()
            now_json = resp.json()
        except requests.exceptions.RequestException as e:
            print(f"[NHK v3] now API request error: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"[NHK v3] now API JSON decode error: {e}")
            return None

        # Extract publication list
        if self.code not in now_json:
            print(f"[NHK v3] no program data for {self.code} now")
            return None

        service_data = now_json.get(self.code, {})
        publication = service_data.get("publication", [])

        if not publication:
            print(f"[NHK v3] no program data for {self.code} now")
            return None

        # Find currently broadcasting program
        # now = DT.now().astimezone()
        current_program = None

        for program in publication:
            try:
                start_dt = DT.fromisoformat(
                    program.get("startDate", "").replace("Z", "+00:00")
                )
                end_dt = DT.fromisoformat(
                    program.get("endDate", "").replace("Z", "+00:00")
                )

                if start_dt <= target_time <= end_dt:
                    current_program = program
                    break
            except (ValueError, AttributeError) as e:
                print(f"[NHK v3] time parse error: {e}")
                continue

        if not current_program:
            print("[NHK v3] no currently broadcasting program found")
            return None

        # Get broadcast event ID for detailed info
        event_id = current_program.get("id")
        if not event_id:
            print("[NHK v3] program has no 'id' field")
            return None

        # Fetch detailed program information
        info_url = self.NHK_API_V3_INFO.format(
            broadcastEventId=event_id, key=self.api_key
        )

        try:
            info_resp = requests.get(info_url, timeout=self.HTTP_TIMEOUT)
            info_resp.raise_for_status()
            info_json = info_resp.json()
        except requests.exceptions.RequestException as e:
            print(f"[NHK v3] info API request error: {e}")
            # Return basic info if detail fetch fails
            p_title = current_program.get("name")
            print(f"[NHK v3] current: id={event_id} title={p_title!r}")
            return current_program
        except json.JSONDecodeError as e:
            print(f"[NHK v3] info API JSON decode error: {e}")
            return current_program

        # Return detailed program info
        p_title = info_json.get("name")
        print(f"[NHK v3] current: id={event_id} title={p_title!r}")

        return info_json
