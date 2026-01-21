"""NHK on-demand radio API client.

This module provides access to NHK's on-demand radio program archive API
(radiru.nhk.jp), allowing retrieval of program information, episodes, and
recording metadata.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import requests

from .program import Program


# ============================================================================
# Exception Classes
# ============================================================================


class NHKApiError(Exception):
    """Base exception for NHK API operations."""

    pass


class NHKApiHttpError(NHKApiError):
    """Exception raised when HTTP request to NHK API fails."""

    pass


class NHKApiJsonError(NHKApiError):
    """Exception raised when JSON parsing from NHK API fails."""

    pass


# ============================================================================
# NHK API Client
# ============================================================================


class NHKApi:
    """NHK on-demand radio API client."""

    # API endpoints - Correct URLs for actual NHK API
    BASE_URL = "https://www.nhk.or.jp/radio-api/app/v1/web/ondemand"
    BASE_NEW_ARRIVALS_URL = (
        "https://www.nhk.or.jp/radio-api/app/v1/web/ondemand/corners/new_arrivals"
    )
    BASE_CORNERS_URL = (
        "https://www.nhk.or.jp/radio-api/app/v1/web/ondemand/corners?date={date}"
    )
    BASE_SERIES_URL = "https://www.nhk.or.jp/radio-api/app/v1/web/ondemand/series?site_id={site_id}&corner_site_id={corner_site_id}"

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
            Dictionary with structured corner information

        Raises:
            NHKApiHttpError: If HTTP request fails.
            NHKApiJsonError: If response JSON parsing fails.
        """
        data = self._fetch_json(self.BASE_NEW_ARRIVALS_URL)
        return self._normalize_corners_response(data)

    def get_corners_by_date(self, date: str) -> Dict[str, Any]:
        """Fetch programs for a specific date with structured data.

        Args:
            date: Date in YYYYMMDD format (e.g., "20260118").

        Returns:
            Dictionary with structured corner information

        Raises:
            NHKApiHttpError: If HTTP request fails.
            NHKApiJsonError: If response JSON parsing fails.
        """
        url = self.BASE_CORNERS_URL.format(date=date)
        data = self._fetch_json(url)
        return self._normalize_corners_response(data)

    def get_series(
        self,
        site_id: str,
        corner_site_id: str = "01",
    ) -> Dict[str, Any]:
        """Fetch series information with episode details and stream URLs.

        Args:
            site_id: Series site ID (e.g., "47Q5W9WQK9").
            corner_site_id: Corner site ID. Defaults to "01".

        Returns:
            Dictionary with structured series information

        Raises:
            NHKApiHttpError: If HTTP request fails.
            NHKApiJsonError: If response JSON parsing fails.
        """
        url = self.BASE_SERIES_URL.format(
            site_id=site_id,
            corner_site_id=corner_site_id,
        )
        data = self._fetch_json(url)
        return self._normalize_series_response(data, site_id, corner_site_id)

    def get_programs(self) -> List[Program]:
        """Fetch NHK on-demand programs (new arrivals only).

        Returns only title information from new arrivals for fast filtering.

        Returns:
            List of Program objects with basic information from new arrivals
        """
        try:
            programs = []

            # Get new arrivals
            arrivals_data = self.get_new_arrivals()

            if not arrivals_data:
                return []

            # Extract corners from arrivals - title only for fast filtering
            corners = self.extract_corners(arrivals_data)

            # Convert each corner to Program instance with basic info only
            for corner in corners:
                try:
                    title = corner.get("title", "")
                    description = corner.get("description", "")
                    site_id = corner.get("site_id", "")

                    if not title:
                        continue

                    # Create Program with basic info (no detailed episodes yet)
                    program = Program(
                        title=title,
                        station="NHK",
                        start_time="",
                        end_time="",
                        source="nhk",
                        description=description,
                        performer=corner.get("main_name", ""),
                        series_site_id=site_id,
                        corner_site_id=corner.get("corner_site_id", "01"),
                    )

                    programs.append(program)

                except Exception:
                    continue

            return programs

        except Exception as e:
            raise NHKApiError(f"Failed to get programs: {e}") from e

    def enrich_program_details(self, program: Program) -> Program:
        """Fetch detailed episode information for a matched NHK program.

        This method should only be called for programs that matched the keyword
        search to minimize API calls.

        Args:
            program: Program instance with series_site_id and corner_site_id set

        Returns:
            Program instance with detailed episode information
        """
        try:
            site_id = program.series_site_id
            corner_site_id = program.corner_site_id or "01"

            if not site_id:
                return program

            # Fetch detailed series data
            series_data = self.get_series(site_id, corner_site_id)
            episodes = self.extract_episodes(series_data)

            # Get the most recent episode
            if episodes:
                episode = episodes[0]
                program = self._convert_episode_to_program(
                    episode,
                    {
                        "title": program.title,
                        "description": program.description,
                        "main_name": program.performer,
                        "site_id": site_id,
                        "corner_site_id": corner_site_id,
                    },
                )

            return program

        except Exception:
            return program

    def _convert_episode_to_program(
        self,
        episode: Dict[str, Any],
        corner: Dict[str, Any],
    ) -> Optional[Program]:
        """Convert NHK episode data to Program instance.

        Args:
            episode: Episode data from API
            corner: Corner data from API

        Returns:
            Program instance or None if conversion fails
        """
        try:
            # Extract essential information
            title = corner.get("title", "")
            subtitle = episode.get("subtitle", "")
            description = corner.get("description", "") or episode.get(
                "description", ""
            )

            # Combine title with subtitle if available
            full_title = f"{title}：{subtitle}" if subtitle else title

            # Parse broadcast date and time - support multiple formats
            onair_date = episode.get("onair_date", "")
            start_time = ""
            end_time = ""

            if onair_date:
                # Try multiple date formats
                date_formats = [
                    "%Y%m%d%H%M%S",  # 20260118000000
                    "%Y%m%d",  # 20260118
                    "%Y-%m-%d %H:%M",  # 2026-01-18 09:50
                    "%Y-%m-%d",  # 2026-01-18
                ]

                parsed_date = None
                for fmt in date_formats:
                    try:
                        parsed_date = datetime.strptime(onair_date, fmt)
                        break
                    except ValueError:
                        continue

                if parsed_date:
                    # Store in YYYYMMDD format for command generation
                    start_time = parsed_date.strftime("%Y%m%d")
                    end_time = parsed_date.strftime("%Y%m%d")
                else:
                    # If parsing fails, extract date part if format is like "1月18日(日)..."
                    import re

                    date_match = re.search(r"(\d+)月(\d+)日", onair_date)
                    if date_match:
                        month = date_match.group(1)
                        day = date_match.group(2)
                        # Assume current year
                        year = datetime.now().year
                        # Store in YYYYMMDD format for consistency
                        start_time = f"{year}{month.zfill(2)}{day.zfill(2)}"
                        end_time = f"{year}{month.zfill(2)}{day.zfill(2)}"

            # Create Program instance
            program = Program(
                title=full_title,
                station="NHK",
                start_time=start_time,
                end_time=end_time,
                source="nhk",
                description=description,
                info=episode.get("content_id", ""),
                performer=corner.get("main_name", ""),
                series_site_id=corner.get("site_id", ""),  # ← 追加
                corner_site_id=corner.get("corner_site_id", "01"),  # ← 追加
            )

            # Add NHK-specific attributes
            program.episode_id = episode.get("episode_id", "")
            program.series_id = corner.get("site_id", "")
            program.content_id = episode.get("content_id", "")
            program.file_name = episode.get("file_name", "")

            return program

        except Exception as e:
            return None

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
        """Normalize corners API response to structured format."""

        try:
            corners_raw = raw_data.get("corners", [])
            normalized_corners = []

            for corner in corners_raw:
                normalized_corner = {
                    "id": corner.get("id"),
                    "title": corner.get("title", ""),
                    "radio_broadcast": corner.get("radio_broadcast", ""),
                    "site_id": corner.get(
                        "series_site_id", ""
                    ),  # ← "series_site_id" を使用
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
