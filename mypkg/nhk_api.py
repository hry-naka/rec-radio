"""NHK Radio Ondemand API client module.

This module provides a stateless API client for interacting with the NHK
radio streaming ondemand service. It handles program retrieval and stream
URL acquisition.

The API returns structured data optimized for use with Program and recording
pipeline components.

Attributes:
    BASE_URL (str): Base URL for NHK API endpoints.
    DEFAULT_TIMEOUT (int): Default timeout for API requests in seconds.
"""

from typing import Any, Dict, List, Optional, Union

import requests


class NHKApiError(Exception):
    """Base exception for NHK API errors."""

    pass


class NHKApiHttpError(NHKApiError):
    """Exception raised for HTTP/network errors."""

    pass


class NHKApiJsonError(NHKApiError):
    """Exception raised for JSON parsing errors."""

    pass


class NHKApi:
    """Stateless client for NHK Radio Ondemand API interactions.

    This class provides methods for retrieving program information, episode
    details, and streaming URLs from the NHK radio ondemand API.

    All methods return structured dictionaries optimized for downstream
    consumers like recorder_nhk.py and find_radio.py.

    Attributes:
        BASE_URL (str): Base URL for NHK API endpoints.
        BASE_NEW_ARRIVALS_URL (str): URL for new arrivals endpoint.
        BASE_CORNERS_URL (str): URL pattern for corners by date endpoint.
        BASE_SERIES_URL (str): URL pattern for series endpoint.
        DEFAULT_TIMEOUT (int): Default timeout in seconds.
    """

    # API endpoints
    BASE_URL = "https://www.nhk.or.jp/radioondemand/json"
    BASE_NEW_ARRIVALS_URL = "https://www.nhk.or.jp/radioondemand/json/new_arrivals.json"
    BASE_CORNERS_URL = (
        "https://www.nhk.or.jp/radioondemand/json/corners-{onair_date}.json"
    )
    BASE_SERIES_URL = (
        "https://www.nhk.or.jp/radioondemand/json/{site_id}-{corner_site_id}.json"
    )

    DEFAULT_TIMEOUT = 10

    def __init__(self, timeout: int = DEFAULT_TIMEOUT) -> None:
        """Initialize NHK API client.

        Args:
            timeout: Request timeout in seconds. Defaults to 10.

        Raises:
            ValueError: If timeout is not positive.
        """
        if timeout <= 0:
            raise ValueError("Timeout must be positive")
        self.timeout = timeout

    def get_new_arrivals(self) -> Dict[str, Any]:
        """Fetch newly arrived programs with structured data.

        Returns:
            Dictionary with structured corner information:
            {
                "onair_date": str,  # Date when fetched
                "corners": [
                    {
                        "id": int,
                        "title": str,
                        "radio_broadcast": str,  # R1, R2, FM
                        "series_site_id": str,
                        "corner_site_id": str,
                        "onair_date": str,
                        "started_at": str,  # ISO format timestamp
                        "thumbnail_url": str,
                    },
                    ...
                ]
            }

        Raises:
            NHKApiHttpError: If HTTP request fails.
            NHKApiJsonError: If response JSON parsing fails.
        """
        data = self._fetch_json(self.BASE_NEW_ARRIVALS_URL)
        return self._normalize_corners_response(data)

    def get_corners_by_date(self, onair_date: str) -> Dict[str, Any]:
        """Fetch programs for a specific date with structured data.

        Args:
            onair_date: Date in YYYYMMDD format (e.g., "20260118").

        Returns:
            Dictionary with structured corner information:
            {
                "onair_date": str,  # The requested date
                "corners": [
                    {
                        "id": int,
                        "title": str,
                        "radio_broadcast": str,
                        "series_site_id": str,
                        "corner_site_id": str,
                        "onair_date": str,
                        "started_at": str,
                        "thumbnail_url": str,
                    },
                    ...
                ]
            }

        Raises:
            NHKApiHttpError: If HTTP request fails.
            NHKApiJsonError: If response JSON parsing fails.
        """
        url = self.BASE_CORNERS_URL.format(onair_date=onair_date)
        data = self._fetch_json(url)
        return self._normalize_corners_response(data)

    def get_series(self, site_id: str, corner_site_id: str = "01") -> Dict[str, Any]:
        """Fetch series information with episode details and stream URLs.

        Args:
            site_id: Series site ID (e.g., "47Q5W9WQK9").
            corner_site_id: Corner site ID. Defaults to "01".

        Returns:
            Dictionary with structured series information:
            {
                "id": int,
                "title": str,
                "radio_broadcast": str,
                "schedule": str,
                "series_description": str,
                "series_site_id": str,
                "corner_site_id": str,
                "episodes": [
                    {
                        "id": int,
                        "program_title": str,
                        "onair_date": str,
                        "closed_at": str,
                        "stream_url": str,  # M3U8 URL for ffmpeg
                        "program_sub_title": str,  # DJ/guest info
                    },
                    ...
                ]
            }

        Raises:
            NHKApiHttpError: If HTTP request fails.
            NHKApiJsonError: If response JSON parsing fails.
        """
        url = self.BASE_SERIES_URL.format(
            site_id=site_id, corner_site_id=corner_site_id
        )
        data = self._fetch_json(url)
        return self._normalize_series_response(data, site_id, corner_site_id)

    def _fetch_json(self, url: str) -> Dict[str, Any]:
        """Fetch and parse JSON from API endpoint.

        Args:
            url: API endpoint URL.

        Returns:
            Parsed JSON response as dictionary.

        Raises:
            NHKApiHttpError: If HTTP request fails.
            NHKApiJsonError: If JSON parsing fails.
        """
        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise NHKApiHttpError(f"HTTP request failed: {e}") from e

        try:
            return response.json()
        except ValueError as e:
            raise NHKApiJsonError(f"JSON parsing failed: {e}") from e

    def _normalize_corners_response(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize corners API response to structured format.

        Extracts essential fields from raw corners data and ensures
        consistent structure across new_arrivals and get_corners_by_date.

        Args:
            raw_data: Raw API response dictionary.

        Returns:
            Normalized dictionary with corners list.

        Raises:
            NHKApiJsonError: If required fields are missing.
        """
        try:
            corners_raw = raw_data.get("corners", [])
            normalized_corners = []

            for corner in corners_raw:
                normalized_corner = {
                    "id": corner.get("id"),
                    "title": corner.get("title", ""),
                    "radio_broadcast": corner.get("radio_broadcast", ""),
                    "series_site_id": corner.get("series_site_id", ""),
                    "corner_site_id": corner.get("corner_site_id", ""),
                    "onair_date": corner.get("onair_date", ""),
                    "started_at": corner.get("started_at", ""),
                    "thumbnail_url": corner.get("thumbnail_url", ""),
                }
                normalized_corners.append(normalized_corner)

            return {
                "onair_date": raw_data.get("onair_date", ""),
                "corners": normalized_corners,
            }
        except (KeyError, TypeError) as e:
            raise NHKApiJsonError(f"Failed to normalize corners data: {e}") from e

    def _normalize_series_response(
        self, raw_data: Dict[str, Any], site_id: str, corner_site_id: str
    ) -> Dict[str, Any]:
        """Normalize series API response to structured format.

        Extracts and structures series and episode data for convenient
        access in recording pipelines.

        Args:
            raw_data: Raw API response dictionary from get_series.
            site_id: Series site ID (for consistency).
            corner_site_id: Corner site ID (for consistency).

        Returns:
            Normalized dictionary with series and episodes.

        Raises:
            NHKApiJsonError: If required fields are missing.
        """
        try:
            episodes_raw = raw_data.get("episodes", [])
            normalized_episodes = []

            for episode in episodes_raw:
                normalized_episode = {
                    "id": episode.get("id"),
                    "program_title": episode.get("program_title", ""),
                    "onair_date": episode.get("onair_date", ""),
                    "closed_at": episode.get("closed_at", ""),
                    "stream_url": episode.get("stream_url", ""),
                    "program_sub_title": episode.get("program_sub_title", ""),
                }
                normalized_episodes.append(normalized_episode)

            return {
                "id": raw_data.get("id"),
                "title": raw_data.get("title", ""),
                "radio_broadcast": raw_data.get("radio_broadcast", ""),
                "schedule": raw_data.get("schedule", ""),
                "series_description": raw_data.get("series_description", ""),
                "series_site_id": site_id,
                "corner_site_id": corner_site_id,
                "episodes": normalized_episodes,
            }
        except (KeyError, TypeError) as e:
            raise NHKApiJsonError(f"Failed to normalize series data: {e}") from e

    @staticmethod
    def extract_corners(data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract corner information from normalized API response.

        Safely extracts the corners list from a response returned by
        get_new_arrivals() or get_corners_by_date().

        Args:
            data: Normalized response dictionary from get_new_arrivals()
                  or get_corners_by_date().

        Returns:
            List of corner/program dictionaries, empty list if none found.

        Raises:
            NHKApiJsonError: If data structure is invalid.
        """
        try:
            if not isinstance(data, dict):
                raise TypeError("data must be a dictionary")
            return data.get("corners", [])
        except (KeyError, TypeError) as e:
            raise NHKApiJsonError(f"Failed to extract corners: {e}") from e

    @staticmethod
    def extract_episodes(series_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract episode information from normalized series data.

        Safely extracts the episodes list from a response returned by
        get_series().

        Args:
            series_data: Normalized response dictionary from get_series().

        Returns:
            List of episode dictionaries with streaming information.

        Raises:
            NHKApiJsonError: If data structure is invalid.
        """
        try:
            if not isinstance(series_data, dict):
                raise TypeError("series_data must be a dictionary")
            return series_data.get("episodes", [])
        except (KeyError, TypeError) as e:
            raise NHKApiJsonError(f"Failed to extract episodes: {e}") from e

    def extract_recording_info(
        self,
        series_data: Optional[Dict[str, Any]] = None,
        title: Optional[str] = None,
        series_site_id: Optional[str] = None,
        episode: Optional[Dict[str, Any]] = None,
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Extract recording info for use with recorder_nhk.py.

        Args:
            series_data: Full series data dict with episodes (optional)
            title: Series title (optional)
            series_site_id: Series site ID (optional)
            episode: Single episode dict (optional)

        Returns:
            dict if single episode, list of dicts if multiple episodes

        Raises:
            ValueError: If neither episode nor series_data provided
        """
        if episode:
            return {
                "title": title,
                "series_site_id": series_site_id,
                "program_title": episode.get("program_title"),
                "onair_date": episode.get("onair_date"),
                "closed_at": episode.get("closed_at"),
                "stream_url": episode.get("stream_url"),
                "program_sub_title": episode.get("program_sub_title"),
            }

        if series_data and "episodes" in series_data:
            episodes = series_data.get("episodes", [])
            series_title = series_data.get("title", title)

            return [
                {
                    "title": series_title,
                    "program_title": ep.get("program_title"),
                    "onair_date": ep.get("onair_date"),
                    "closed_at": ep.get("closed_at"),
                    "stream_url": ep.get("stream_url"),
                    "program_sub_title": ep.get("program_sub_title"),
                }
                for ep in episodes
            ]

        raise ValueError("Either 'episode' or 'series_data' must be provided")

    def dump(self) -> None:
        """Dump API client status (for debugging).

        Note: NHKApi is stateless, so this only shows configuration.
        Useful for verifying client initialization in logs.
        """
        print(f"NHKApi(timeout={self.timeout}s, base_url={self.BASE_URL})")
