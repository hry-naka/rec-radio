"""Program formatting utilities for radio recordings (NHK and Radiko).

This module provides utility functions for formatting program data for:
- Display in find_radio.py
- Logging in recorder_nhk.py / recorder_radiko.py
- File naming for recordings
- Metadata for recorded files
"""

from datetime import datetime
from typing import Optional

from .program import Program


class ProgramFormatter:
    """Utility class for formatting program information.

    Provides consistent formatting for both NHK and Radiko programs
    across different use cases (display, logging, naming, metadata).
    """

    @staticmethod
    def generate_filename(
        program: Optional[Program],
        prefix: str,
        date_str: Optional[str] = None,
    ) -> str:
        """Generate output filename for recording.

        Filename format: {prefix}_{YYYY-MM-DD-HH_MM}.mp4

        Args:
            program: Program information (optional, for future enhancement)
            prefix: Filename prefix (e.g., station ID like 'TBS', 'INT')
            date_str: Date string for filename (defaults to current time)

        Returns:
            Generated filename with .mp4 extension

        Example:
            >>> program = Program(title="News", station="TBS", ...)
            >>> filename = ProgramFormatter.generate_filename(program, "TBS")
            >>> # Returns something like: TBS_2026-01-20-13_55.mp4
        """
        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d-%H_%M")
        return f"{prefix}_{date_str}.mp4"

    @staticmethod
    def format_title_with_subtitle(
        title: str,
        subtitle: Optional[str] = None,
    ) -> str:
        """Format title with subtitle/performer information.

        Args:
            title: Program title
            subtitle: Subtitle or performer name

        Returns:
            Formatted title string

        Example:
            >>> ProgramFormatter.format_title_with_subtitle(
            ...     "眠れない貴女へ",
            ...     "【DJ】和田明日香，【ゲスト】山崎佐知子"
            ... )
            >>> # Returns: "眠れない貴女へ (【DJ】和田明日香，【ゲスト】山崎佐知子)"
        """
        if subtitle:
            return f"{title} ({subtitle})"
        return title

    @staticmethod
    def format_time_range(start_time: str, end_time: str) -> str:
        """Format time range for display (HH:MM-HH:MM format).

        Args:
            start_time: Start time in YYYYMMDDHHMMSS format
            end_time: End time in YYYYMMDDHHMMSS format

        Returns:
            Formatted time range string

        Example:
            >>> ProgramFormatter.format_time_range("20260118133000", "20260118135500")
            >>> # Returns: "13:30-13:55"
        """
        if len(start_time) >= 12 and len(end_time) >= 12:
            start_hm = f"{start_time[8:10]}:{start_time[10:12]}"
            end_hm = f"{end_time[8:10]}:{end_time[10:12]}"
            return f"{start_hm}-{end_hm}"
        return f"{start_time}-{end_time}"

    @staticmethod
    def format_time_display(time_str: str) -> str:
        """Format time string for display (HH:MM format).

        Args:
            time_str: Time string in YYYYMMDDHHMMSS format

        Returns:
            Formatted time string (HH:MM)

        Example:
            >>> ProgramFormatter.format_time_display("20260118133000")
            >>> # Returns: "13:30"
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

        Example:
            >>> ProgramFormatter.format_date_display("20260118")
            >>> # Returns: "2026-01-18"
        """
        if len(date_str) >= 8:
            return f"{date_str[0:4]}-{date_str[4:6]}-{date_str[6:8]}"
        return date_str

    @staticmethod
    def get_log_string(program: Program) -> str:
        """Generate formatted log string for program.

        Format: [STATION] title (HH:MM-HH:MM) AREA

        Args:
            program: Program information

        Returns:
            Formatted log string

        Example:
            >>> program = Program(
            ...     title="レコレール",
            ...     station="INT",
            ...     start_time="20260120133000",
            ...     end_time="20260120135500",
            ...     source="radiko",
            ...     area="JP13"
            ... )
            >>> ProgramFormatter.get_log_string(program)
            >>> # Returns: "[INT] レコレール (13:30-13:55) JP13"
        """
        time_str = ProgramFormatter.format_time_range(
            program.start_time, program.end_time
        )
        return f"[{program.station}] {program.title} ({time_str}) {program.area}"

    @staticmethod
    def get_display_list_string(program: Program) -> str:
        """Generate formatted string for program list display.

        Format: [SOURCE] [STATION] title (duration_min) at HH:MM

        Args:
            program: Program information

        Returns:
            Formatted display string

        Example:
            >>> program = Program(
            ...     title="ニュース",
            ...     station="TBS",
            ...     start_time="20260120140000",
            ...     end_time="20260120141500",
            ...     source="radiko",
            ...     area="JP13"
            ... )
            >>> ProgramFormatter.get_display_list_string(program)
            >>> # Returns: "[radiko] [TBS] ニュース (15 min) at 14:00"
        """
        time_display = ProgramFormatter.format_time_display(program.start_time)
        duration_min = program.get_duration_minutes()
        source_upper = program.source.upper()
        return (
            f"[{source_upper}] [{program.station}] {program.title} "
            f"({duration_min} min) at {time_display}"
        )

    @staticmethod
    def get_metadata_comment(
        description: Optional[str] = None, info: Optional[str] = None
    ) -> str:
        """Generate metadata comment string for recorded file.

        Args:
            description: Program description (NHK)
            info: Additional info string (Radiko)

        Returns:
            Formatted comment string

        Example:
            >>> comment = ProgramFormatter.get_metadata_comment(
            ...     description="Jazz program",
            ...     info="Additional info"
            ... )
        """
        if description:
            return description
        elif info:
            return info
        return ""

    @staticmethod
    def get_status_message(
        stage: str,
        program: Optional[Program] = None,
        detail: Optional[str] = None,
    ) -> str:
        """Generate status message for logging.

        Format: [YYYY-MM-DD HH:MM:SS] stage: [program info] - detail

        Args:
            stage: Stage name (e.g., 'START', 'DONE', 'ERROR')
            program: Optional program information
            detail: Optional detail message

        Returns:
            Formatted status message

        Example:
            >>> program = Program(title="News", station="TBS", ...)
            >>> msg = ProgramFormatter.get_status_message(
            ...     "START",
            ...     program=program,
            ...     detail="Recording for 60 seconds"
            ... )
            >>> # Returns: "[2026-01-20 13:55:30] START: [TBS] News - Recording for 60 seconds"
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"[{timestamp}] {stage}"
        if program:
            message += f": {ProgramFormatter.get_log_string(program)}"
        if detail:
            message += f" - {detail}"
        return message

    @staticmethod
    def get_detailed_info(program: Program) -> str:
        """Generate detailed information string for program.

        Includes all available metadata.

        Args:
            program: Program information

        Returns:
            Detailed information string

        Example:
            >>> program = Program(
            ...     title="眠れない貴女へ",
            ...     station="FM",
            ...     start_time="20260118233000",
            ...     end_time="20260119000000",
            ...     source="nhk",
            ...     area="JP13",
            ...     stream_url="https://...",
            ...     closed_at="2026-01-26",
            ... )
            >>> info = ProgramFormatter.get_detailed_info(program)
        """
        lines = [
            f"Title: {program.title}",
            f"Station: {program.station}",
            f"Source: {program.source.upper()}",
            f"Date: {ProgramFormatter.format_date_display(program.start_time)}",
            f"Time: {ProgramFormatter.format_time_range(program.start_time, program.end_time)}",
            f"Duration: {program.get_duration_minutes()} minutes",
            f"Area: {program.area}",
        ]

        if program.performer:
            lines.append(f"Performer: {program.performer}")
        if program.description:
            lines.append(f"Description: {program.description}")
        if program.program_sub_title:
            lines.append(f"Subtitle: {program.program_sub_title}")
        if program.closed_at:
            lines.append(f"Available until: {program.closed_at}")
        if program.is_recordable():
            lines.append("Status: Recordable ✓")
        else:
            lines.append("Status: Not recordable (no stream URL)")

        return "\n".join(lines)
