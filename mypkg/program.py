"""Program data model for radio programs (NHK and Radiko).

This module defines a unified data structure for representing radio program information
from both NHK and Radiko APIs. The Program class provides a common interface for
downstream consumers (recorder, finder, formatter, etc.).
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Optional


@dataclass
class Program:
    """Represents a radio program with unified metadata for NHK and Radiko.

    This class serves as the single unified data structure for all radio programs,
    regardless of source (NHK or Radiko). It normalizes data from different APIs
    into a common format.

    Attributes:
        title: Program title (required)
        station: Station ID (e.g., 'TBS', 'INT', 'NR1') (required)
        start_time: Start time in YYYYMMDDHHMMSS format (required)
        end_time: End time in YYYYMMDDHHMMSS format (required)
        source: Source API ('nhk' or 'radiko') (required)
        area: Area ID (e.g., 'JP13' for Kanto). Defaults to 'JP13'
        stream_url: M3U8 streaming URL. Required for NHK, optional for Radiko
        duration: Duration in minutes. Calculated from start/end time if not provided
        performer: Program host/personality name
        description: Program description
        program_title: Episode title (NHK-specific, alternative to title for episodes)
        program_sub_title: Subtitle or additional title (e.g., DJ/guest info for NHK)
        info: Additional information string (Radiko)
        image_url: URL to program cover image
        url: Program information URL
        onair_date: Broadcast date string (alternative to start_time[:8])
        closed_at: Content delivery end date (NHK-specific)
        series_site_id: Series ID (NHK-specific)
        corner_site_id: Corner ID (NHK-specific)
    """

    title: str
    station: str
    start_time: str
    end_time: str
    source: Literal["nhk", "radiko"]
    area: str = "JP13"
    stream_url: Optional[str] = None
    duration: int = 0
    performer: Optional[str] = None
    description: Optional[str] = None
    program_title: Optional[str] = None
    program_sub_title: Optional[str] = None
    info: Optional[str] = None
    image_url: Optional[str] = None
    url: Optional[str] = None
    onair_date: Optional[str] = None
    closed_at: Optional[str] = None
    series_site_id: Optional[str] = None
    corner_site_id: Optional[str] = None

    def __post_init__(self) -> None:
        """Calculate duration if not provided."""
        if self.duration == 0:
            try:
                start_dt = datetime.strptime(self.start_time, "%Y%m%d%H%M%S")
                end_dt = datetime.strptime(self.end_time, "%Y%m%d%H%M%S")
                # Store duration in minutes
                self.duration = int((end_dt - start_dt).total_seconds() / 60)
            except ValueError:
                self.duration = 0

    def get_duration_minutes(self) -> int:
        """Calculate duration in minutes.

        Returns:
            Duration in minutes
        """
        return self.duration

    def get_duration_seconds(self) -> int:
        """Get duration in seconds.

        Returns:
            Duration in seconds
        """
        return self.duration * 60

    def get_start_datetime(self) -> datetime:
        """Get start time as datetime object.

        Supports multiple datetime formats used by different services.

        Returns:
            datetime object

        Raises:
            ValueError: If start_time format is not supported
        """
        if not self.start_time:
            raise ValueError("start_time is not set")

        # Try multiple datetime formats
        formats = [
            "%Y%m%d%H%M%S",  # 20260118000000 (Radiko format)
            "%Y%m%d",  # 20260118 (NHK format)
            "%Y-%m-%d %H:%M",  # 2026-01-18 00:00
            "%Y-%m-%d %H:%M:%S",  # 2026-01-18 00:00:00
            "%Y-%m-%d",  # 2026-01-18
        ]

        for fmt in formats:
            try:
                return datetime.strptime(self.start_time, fmt)
            except ValueError:
                continue

        # If no format matched, raise error
        raise ValueError(
            f"start_time '{self.start_time}' does not match any supported format"
        )

    def get_end_datetime(self) -> datetime:
        """Get end time as datetime object.

        Supports multiple datetime formats used by different services.

        Returns:
            datetime object

        Raises:
            ValueError: If end_time format is not supported
        """
        if not self.end_time:
            raise ValueError("end_time is not set")

        # Try multiple datetime formats
        formats = [
            "%Y%m%d%H%M%S",  # 20260118235959 (Radiko format)
            "%Y%m%d",  # 20260118 (NHK format)
            "%Y-%m-%d %H:%M",  # 2026-01-18 23:59
            "%Y-%m-%d %H:%M:%S",  # 2026-01-18 23:59:59
            "%Y-%m-%d",  # 2026-01-18
        ]

        for fmt in formats:
            try:
                return datetime.strptime(self.end_time, fmt)
            except ValueError:
                continue

        # If no format matched, raise error
        raise ValueError(
            f"end_time '{self.end_time}' does not match any supported format"
        )

    def is_nhk(self) -> bool:
        """Check if program is from NHK API.

        Returns:
            True if source is 'nhk'
        """
        return self.source == "nhk"

    def is_radiko(self) -> bool:
        """Check if program is from Radiko API.

        Returns:
            True if source is 'radiko'
        """
        return self.source == "radiko"

    def is_recordable(self) -> bool:
        """Check if program can be recorded.

        Requires stream_url to be available.

        Returns:
            True if stream_url is available
        """
        return self.stream_url is not None

    def __str__(self) -> str:
        """Return string representation of program.

        Returns:
            Human-readable string
        """
        start_time = self.get_start_datetime()
        end_time = self.get_end_datetime()
        time_str = f"{start_time.strftime('%H:%M')}-{end_time.strftime('%H:%M')}"
        return f"[{self.station}] {self.title} ({time_str})"

    @classmethod
    def from_nhk_series(cls, series_data: dict, episode: dict) -> "Program":
        """Create Program instance from NHK series and episode data.

        Args:
            series_data: Series information dict from nhk_api.get_series()
            episode: Episode information dict

        Returns:
            Program instance configured for NHK

        Example:
            >>> series = api.get_series("47Q5W9WQK9", "01")
            >>> episode = series["episodes"][0]
            >>> program = Program.from_nhk_series(series, episode)
        """
        return cls(
            title=series_data.get("title", ""),
            station="NHK",
            start_time=cls._normalize_nhk_datetime(episode.get("onair_date", "")),
            end_time=cls._normalize_nhk_datetime(episode.get("closed_at", "")),
            source="nhk",
            area="JP13",
            stream_url=episode.get("stream_url"),
            performer=None,
            description=series_data.get("series_description"),
            program_sub_title=episode.get("program_sub_title"),
            onair_date=episode.get("onair_date"),
            closed_at=episode.get("closed_at"),
            series_site_id=series_data.get("series_site_id"),
            corner_site_id=series_data.get("corner_site_id"),
        )

    @classmethod
    def from_radiko_program(cls, program_data: dict) -> "Program":
        """Create Program instance from Radiko program data.

        Args:
            program_data: Program information dict from radiko_api

        Returns:
            Program instance configured for Radiko

        Example:
            >>> program_data = api.fetch_now_program("TBS")
            >>> program = Program.from_radiko_program(program_data)
        """
        return cls(
            title=program_data.get("title", ""),
            station=program_data.get("station", ""),
            start_time=program_data.get("start_time", ""),
            end_time=program_data.get("end_time", ""),
            source="radiko",
            area=program_data.get("area", "JP13"),
            stream_url=program_data.get("stream_url"),  # Can be None
            duration=program_data.get("duration", 0),
            performer=program_data.get("performer"),
            description=program_data.get("description"),
            info=program_data.get("info"),
            image_url=program_data.get("image_url"),
            url=program_data.get("url"),
        )

    @staticmethod
    def _normalize_nhk_datetime(nhk_time_str: str) -> str:
        """Normalize NHK time format to YYYYMMDDHHMMSS.

        NHK API may return times in various formats like "1月18日(日)午後11:30放送".
        This method converts to standard format.

        Args:
            nhk_time_str: Time string from NHK API

        Returns:
            Time string in YYYYMMDDHHMMSS format

        Example:
            >>> Program._normalize_nhk_datetime("1月18日(日)午後11:30放送")
            '20260118233000'
        """
        if not nhk_time_str:
            return ""

        # If already in YYYYMMDDHHMMSS format, return as-is
        if len(nhk_time_str) >= 14 and nhk_time_str[:14].isdigit():
            return nhk_time_str[:14]

        # Parse Japanese date format: "1月18日(日)午後11:30放送"
        # Extract month, day, and time
        month_match = re.search(r"(\d+)月", nhk_time_str)
        day_match = re.search(r"(\d+)日", nhk_time_str)
        time_match = re.search(r"(午前|午後)(\d+):(\d+)", nhk_time_str)

        if month_match and day_match and time_match:
            month = int(month_match.group(1))
            day = int(day_match.group(1))
            am_pm = time_match.group(1)
            hour = int(time_match.group(2))
            minute = int(time_match.group(3))

            # Adjust hour for PM (午後)
            if am_pm == "午後" and hour != 12:
                hour += 12
            elif am_pm == "午前" and hour == 12:
                hour = 0

            # Use current year as NHK API doesn't specify year
            now = datetime.now()
            year = now.year

            # Create datetime object and format as YYYYMMDDHHMMSS
            dt = datetime(year, month, day, hour, minute, 0)
            return dt.strftime("%Y%m%d%H%M%S")

        # Fallback: return as-is if format is unrecognized
        return nhk_time_str
