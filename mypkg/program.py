"""Program data model for Radiko radio programs.

This module defines the data structure for representing radio program information.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Program:
    """Represents a radio program with its metadata.

    Attributes:
        title: Program title
        subtitle: Program subtitle
        start_time: Start time in format "YYYYMMDDHHMMSS"
        end_time: End time in format "YYYYMMDDHHMMSS"
        station: Station ID (e.g., 'TBS')
        area: Area ID (e.g., 'JP13')
        duration: Duration in seconds
        performer: Program host/personality
        description: Program description
        info: Additional program information
        image_url: URL to program cover image
        url: Program information URL
    """

    title: str
    station: str
    area: str
    start_time: str
    end_time: str
    duration: int = 0
    performer: Optional[str] = None
    description: Optional[str] = None
    info: Optional[str] = None
    image_url: Optional[str] = None
    url: Optional[str] = None
    subtitle: Optional[str] = None

    def get_duration_minutes(self) -> int:
        """Calculate duration in minutes.

        Returns:
            Duration in minutes
        """
        return self.duration // 60

    def get_start_datetime(self) -> datetime:
        """Parse start time as datetime object.

        Returns:
            Parsed datetime object
        """
        return datetime.strptime(self.start_time, "%Y%m%d%H%M%S")

    def get_end_datetime(self) -> datetime:
        """Parse end time as datetime object.

        Returns:
            Parsed datetime object
        """
        return datetime.strptime(self.end_time, "%Y%m%d%H%M%S")

    def __str__(self) -> str:
        """Return string representation of program."""
        return (
            f"{self.title} ({self.station}) "
            f"{self.start_time[:8]} {self.start_time[8:12]}-{self.end_time[8:12]}"
        )
