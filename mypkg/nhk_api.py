import json
import os
import shlex
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime as DT, timedelta
from typing import Any, Dict, Optional, Tuple

import requests

class NhkAPIClient:
    def __init__(self, api_key: str, location: str, area_code: str, code: str, api_version: str = "v3"):
        if( api_version != "v3" ):
            print("Warning: API version is not v3. This application only supports v3. The parameter is ignored.")
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
        print(f"Error: No stream URL found for channel={self.code}, " f"location={self.location}")
        return None

    def get_program_info(
        self,target_time: DT
    ) -> Optional[Dict[str, Any]]:
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
  
        now_url = self.NHK_API_V3_NOW.format(service=self.code, area=self.area_code, key=self.api_key)

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
                end_dt = DT.fromisoformat(program.get("endDate", "").replace("Z", "+00:00"))

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
        info_url = self.NHK_API_V3_INFO.format(broadcastEventId=event_id, key=self.api_key)

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
