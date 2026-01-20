"""NHK Radio Ondemand API client module.

This module provides a stateless API client for interacting with the NHK
radio streaming ondemand service. It handles program retrieval and stream
URL acquisition.

Attributes:
    BASE_URL (str): Base URL for NHK API endpoints.
    DEFAULT_TIMEOUT (int): Default timeout for API requests in seconds.
"""

from typing import Any, Dict, List, Optional

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

    Attributes:
        BASE_URL (str): Base URL for NHK API endpoints.
        DEFAULT_TIMEOUT (int): Default timeout in seconds.
    """

    BASE_URL = "https://www.nhk.or.jp/radioondemand/json"
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
        """Fetch newly arrived programs.

        Returns:
            Dictionary containing new arrivals data with 'corners' key.

        Raises:
            NHKApiHttpError: If HTTP request fails.
            NHKApiJsonError: If response JSON parsing fails.
        """
        url = f"{self.BASE_URL}/new_arrivals.json"
        return self._fetch_json(url)

    def get_corners_by_date(self, onair_date: str) -> Dict[str, Any]:
        """Fetch programs for a specific date.

        Args:
            onair_date: Date in YYYYMMDD format.

        Returns:
            Dictionary containing programs data with 'corners' key.

        Raises:
            NHKApiHttpError: If HTTP request fails.
            NHKApiJsonError: If response JSON parsing fails.
        """
        url = f"{self.BASE_URL}/corners-{onair_date}.json"
        return self._fetch_json(url)

    def get_series(self, site_id: str, corner_site_id: str) -> Dict[str, Any]:
        """Fetch series information with episode details.

        Args:
            site_id: Series site ID.
            corner_site_id: Corner site ID.

        Returns:
            Dictionary containing series info with 'episodes' and stream URLs.

        Raises:
            NHKApiHttpError: If HTTP request fails.
            NHKApiJsonError: If response JSON parsing fails.
        """
        url = f"{self.BASE_URL}/{site_id}-{corner_site_id:02d}.json"
        return self._fetch_json(url)

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

    @staticmethod
    def extract_corners(data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract corner information from API response.

        Args:
            data: API response dictionary.

        Returns:
            List of corner/program dictionaries.

        Raises:
            NHKApiJsonError: If required keys are missing.
        """
        try:
            return data.get("corners", [])
        except (KeyError, TypeError) as e:
            raise NHKApiJsonError(f"Failed to extract corners: {e}") from e

    @staticmethod
    def extract_episodes(series_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract episode information from series data.

        Args:
            series_data: Series data dictionary from get_series().

        Returns:
            List of episode dictionaries with streaming information.

        Raises:
            NHKApiJsonError: If required keys are missing.
        """
        try:
            return series_data.get("episodes", [])
        except (KeyError, TypeError) as e:
            raise NHKApiJsonError(f"Failed to extract episodes: {e}") from e

    @staticmethod
    def extract_recording_info(
        series_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Extract information needed for recording.

        Combines series metadata with episode details to create recording
        information suitable for use with external recorders.

        Args:
            series_data: Series data dictionary from get_series().

        Returns:
            List of dictionaries with keys: title, program_title, onair_date,
            closed_at, stream_url.

        Raises:
            NHKApiJsonError: If required keys are missing.
        """
        try:
            title = series_data.get("title", "")
            episodes = series_data.get("episodes", [])

            recording_info = []
            for episode in episodes:
                info = {
                    "title": title,
                    "program_title": episode.get("program_title", ""),
                    "onair_date": episode.get("onair_date", ""),
                    "closed_at": episode.get("closed_at", ""),
                    "stream_url": episode.get("stream_url", ""),
                }
                recording_info.append(info)

            return recording_info
        except (KeyError, TypeError) as e:
            raise NHKApiJsonError(f"Failed to extract recording info: {e}") from e

    def dump(self) -> None:
        """Dump API client status (for debugging).

        Note: NHKApi is stateless, so this only shows configuration.
        """
        print(f"NHKApi(timeout={self.timeout}s)")
