"""Radiko-specific audio recording module.

This module handles recording of Radiko radio streams. It provides
the RecorderRadiko class that manages the complete recording workflow
for Radiko programs, including stream acquisition and metadata management.
"""

from typing import Optional

from .program import Program
from .program_formatter import ProgramFormatter
from .radiko_api import RadikoApi
from .recorder_common import RecorderCommon


class RecorderRadiko(RecorderCommon):
    """Handle audio recording for Radiko radio streams.

    This class manages the complete Radiko recording workflow:
    1. Validates that the program is from Radiko (source == "radiko")
    2. Obtains stream URL using RadikoApi if needed
    3. Records the audio stream using ffmpeg
    4. Sets metadata tags on the recorded file

    Inherits common recording and metadata functionality from RecorderCommon.
    """

    def __init__(
        self, radiko_api: Optional[RadikoApi] = None, loglevel: str = "warning"
    ):
        """Initialize Radiko recorder.

        Args:
            radiko_api: RadikoApi instance for stream URL retrieval.
                        If None, will be created on demand.
            loglevel: ffmpeg loglevel (warning, error, info, etc.)
        """
        super().__init__(loglevel)
        self.radiko_api = radiko_api or RadikoApi()

    def record_program(
        self,
        program: Program,
        auth_token: str,
        output_file: str,
    ) -> bool:
        """Record a Radiko program to file.

        This is the main entry point for recording Radiko programs.
        It handles the complete recording workflow including validation,
        stream acquisition, recording, and metadata tagging.

        Args:
            program: Program instance to record (must have source == "radiko")
            auth_token: Radiko authentication token
            output_file: Output MP4 file path

        Returns:
            True if recording and metadata setting succeeded, False otherwise

        Raises:
            ValueError: If program is not from Radiko
        """
        if not program.is_radiko():
            raise ValueError(
                f"RecorderRadiko can only record Radiko programs, "
                f"but got source='{program.source}'"
            )

        log_info = ProgramFormatter.get_log_string(program)
        print(f"Recording Radiko program: {log_info}")

        # Get stream URL if not already present
        if not program.stream_url:
            print(f"Retrieving stream URL for {program.station}...")
            stream_url = self.radiko_api.get_stream_url(program.station, auth_token)
            if not stream_url:
                print(f"Error: Failed to retrieve stream URL for {program.station}")
                return False
            program.stream_url = stream_url
        else:
            stream_url = program.stream_url

        # Record the stream
        duration_seconds = program.get_duration_seconds()
        headers = {"X-Radiko-AuthToken": auth_token}

        print(f"Starting recording: {output_file}")
        success = self.record_stream(
            stream_url=stream_url,
            output_file=output_file,
            duration=duration_seconds,
            headers=headers,
        )

        if not success:
            print("Error: Stream recording failed")
            return False

        print("Recording completed successfully")

        # Set metadata
        print("Setting metadata...")
        if self.set_metadata(output_file, program):
            print(f"Metadata set successfully: {output_file}")
            return True

        print("Warning: Failed to set metadata, but file was recorded")
        return True  # Recording succeeded even if metadata failed
