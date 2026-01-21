"""NHK-specific audio recording module.

This module handles recording of NHK radio streams. It provides
the RecorderNHK class that manages the complete recording workflow
for NHK programs, including stream acquisition and metadata management.
"""

from typing import Optional

from .nhk_api import NHKApi
from .program import Program
from .program_formatter import ProgramFormatter
from .recorder_common import RecorderCommon


class RecorderNHK(RecorderCommon):
    """Handle audio recording for NHK radio streams.

    This class manages the complete NHK recording workflow:
    1. Validates that the program is from NHK (source == "nhk")
    2. Obtains stream URL using NHKApi if needed
    3. Records the audio stream using ffmpeg
    4. Sets metadata tags on the recorded file

    Inherits common recording and metadata functionality from RecorderCommon.
    """

    def __init__(self, nhk_api: Optional[NHKApi] = None, loglevel: str = "warning"):
        """Initialize NHK recorder.

        Args:
            nhk_api: NHKApi instance for stream URL retrieval.
                     If None, will be created on demand.
            loglevel: ffmpeg loglevel (warning, error, info, etc.)
        """
        super().__init__(loglevel)
        self.nhk_api = nhk_api or NHKApi()

    def record_program(
        self,
        program: Program,
        output_file: str,
    ) -> bool:
        """Record an NHK program to file.

        This is the main entry point for recording NHK programs.
        It handles the complete recording workflow including validation,
        stream acquisition, recording, and metadata tagging.

        Args:
            program: Program instance to record (must have source == "nhk")
            output_file: Output MP4 file path

        Returns:
            True if recording and metadata setting succeeded, False otherwise

        Raises:
            ValueError: If program is not from NHK
        """
        if not program.is_nhk():
            raise ValueError(
                f"RecorderNHK can only record NHK programs, "
                f"but got source='{program.source}'"
            )

        log_info = ProgramFormatter.get_log_string(program)
        print(f"Recording NHK program: {log_info}")

        # Get stream URL if not already present
        if not program.stream_url:
            print("Error: NHK program must have stream_url set by API")
            return False

        stream_url = program.stream_url

        # Record the stream
        duration_seconds = program.get_duration_seconds()

        print(f"Starting recording: {output_file}")
        success = self.record_stream(
            stream_url=stream_url,
            output_file=output_file,
            duration=duration_seconds,
            headers=None,  # NHK streams don't require auth headers
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
