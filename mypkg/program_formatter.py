"""Program formatting utilities for Radiko recordings.

This module provides utility functions for formatting program data,
including file naming, time formatting, and display strings.
"""

from datetime import datetime
from typing import Optional

from .program import Program


class ProgramFormatter:
    """Utility class for formatting program information."""

    @staticmethod
    def generate_filename(
        program: Program,
        prefix: str,
        date_str: Optional[str] = None,
    ) -> str:
        """Generate output filename for recording.

        Args:
            program: Program information
            prefix: Filename prefix
            date_str: Date string (defaults to current date/time)

        Returns:
            Generated filename with .mp4 extension
        """
        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d-%H_%M")
        return f"{prefix}_{date_str}.mp4"

    @staticmethod
    def format_title_with_performer(
        title: str,
        performer: Optional[str] = None,
    ) -> str:
        """Format title with performer information.

        Args:
            title: Program title
            performer: Performer/host name

        Returns:
            Formatted title string
        """
        if performer:
            return f"{title} ({performer})"
        return title

    @staticmethod
    def get_metadata_comment(
        description: Optional[str] = None,
        info: Optional[str] = None,
    ) -> str:
        """Generate comment metadata from description and info.

        Args:
            description: Program description
            info: Additional program information

        Returns:
            Formatted comment string
        """
        parts = []
        if description:
            parts.append(description)
        if info:
            parts.append(info)
        return " / ".join(parts)

    @staticmethod
    def get_log_string(program: Program) -> str:
        """Generate formatted log string for program.

        Args:
            program: Program information

        Returns:
            Formatted log string
        """
        start = program.start_time
        end = program.end_time
        time_str = f"{start[8:10]}:{start[10:12]}-{end[8:10]}:{end[10:12]}"
        return f"[{program.station}] {program.title} " f"({time_str}) {program.area}"

    @staticmethod
    def format_time_display(time_str: str) -> str:
        """Format time string for display (HH:MM format).

        Args:
            time_str: Time string in YYYYMMDDHHMMSS format

        Returns:
            Formatted time string (HH:MM)
        """
        if len(time_str) >= 12:
            return f"{time_str[8:10]}:{time_str[10:12]}"
        return time_str

    @staticmethod
    def format_date_display(date_str: str) -> str:
        """Format date string for display (YYYY-MM-DD format).

        Args:
            date_str: Date string in YYYYMMDD... format

        Returns:
            Formatted date string (YYYY-MM-DD)
        """
        if len(date_str) >= 8:
            return f"{date_str[0:4]}-{date_str[4:6]}-{date_str[6:8]}"
        return date_str

    @staticmethod
    def get_status_message(
        stage: str,
        program: Optional[Program] = None,
        detail: Optional[str] = None,
    ) -> str:
        """Generate status message for logging.

        Args:
            stage: Stage name (e.g., 'start', 'done', 'error')
            program: Optional program information
            detail: Optional detail message

        Returns:
            Formatted status message
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"[{timestamp}] {stage}"
        if program:
            message += f": {program.title}"
        if detail:
            message += f" - {detail}"
        return message
