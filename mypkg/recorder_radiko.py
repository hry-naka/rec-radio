"""Radiko-specific audio recording module.

This module handles recording of Radiko radio streams. It provides
the RecorderRadiko class that manages the complete recording workflow
for Radiko programs, including stream acquisition and metadata management.
"""

import os
import shlex
import subprocess
from typing import Optional

from dotenv import load_dotenv

from .program import Program
from .program_formatter import ProgramFormatter
from .radiko_api import RadikoApi
from .recorder_common import RecorderCommon

# Load environment variables
load_dotenv()


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
        # Load ffmpeg options from .env
        self.ffmpeg_opts = self._load_ffmpeg_options()

    def _load_ffmpeg_options(self) -> list:
        """Load Radiko-specific ffmpeg options from .env.

        Returns:
            List of ffmpeg command-line arguments
        """
        opts_str = os.getenv(
            "RADIKO_FFMPEG_OPTS",
            "-loglevel warning -y -reconnect 1 -reconnect_at_eof 0 "
            "-reconnect_streamed 1 -reconnect_delay_max 600 "
            '-user_agent "Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 Chrome/117.0.0.0 Safari/537.36"',
        )
        return shlex.split(opts_str)

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

    def record(
        self,
        program: Program,
        output_file: Optional[str] = None,
    ) -> bool:
        """Record a Radiko program (main entry point).

        This is the unified recording method that handles both live and time-free.
        It automatically retrieves auth token and stream URL if needed.

        Args:
            program: Program instance to record (must have source == "radiko")
            output_file: Output MP4 file path. If None, auto-generated.

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

        # Generate output filename if not provided
        if output_file is None:
            output_file = ProgramFormatter.generate_filename(program, program.station)

        # Get auth token
        auth_result = self.radiko_api.authorize()
        if auth_result is None:
            print("Error: Radiko authorization failed")
            return False

        auth_token, area_id = auth_result
        print(f"Authorization successful. Area ID: {area_id}")

        # Call record_program with auth token
        return self.record_program(program, auth_token, output_file)

    def record_stream_with_ffmpeg(
        self,
        stream_url: str,
        output_file: str,
        duration: int,
        auth_token: Optional[str] = None,
    ) -> bool:
        """Record stream using ffmpeg with Radiko-specific options.

        This method uses ffmpeg options loaded from .env (RADIKO_FFMPEG_OPTS).

        Args:
            stream_url: M3U8 stream URL
            output_file: Output file path
            duration: Recording duration in seconds
            auth_token: Optional Radiko authentication token

        Returns:
            True if recording succeeded, False otherwise
        """
        if not self.is_available():
            print("Error: ffmpeg must be installed and available in PATH")
            return False

        cmd_parts = [self.ffmpeg_path] + self.ffmpeg_opts

        # Add authentication headers if token is provided
        if auth_token:
            cmd_parts.extend(
                [
                    "-headers",
                    f"X-Radiko-AuthToken: {auth_token}",
                ]
            )

        cmd_parts.extend(
            [
                "-i",
                stream_url,
                "-t",
                str(duration),
                "-acodec",
                "copy",
                "-vn",
                output_file,
            ]
        )

        cmd = " ".join(shlex.quote(part) for part in cmd_parts)
        print(f"Recording command: {cmd}", flush=True)

        try:
            result = subprocess.run(
                cmd_parts,
                capture_output=True,
                text=True,
                check=True,
            )
            if result.stdout:
                print(result.stdout, flush=True)
            if result.stderr:
                print(result.stderr, flush=True)
            return True
        except subprocess.CalledProcessError as e:
            print(
                f"Recording failed with return code {e.returncode}",
                flush=True,
            )
            if e.stdout:
                print(e.stdout, flush=True)
            if e.stderr:
                print(e.stderr, flush=True)
            return False
        except FileNotFoundError:
            print(
                f"Error: ffmpeg not found at {self.ffmpeg_path}",
                flush=True,
            )
            return False

    def get_ffmpeg_command(
        self,
        program: Program,
        output_file: str,
        auth_token: Optional[str] = None,
    ) -> str:
        """Generate ffmpeg command string for recording.

        This method is used by ProgramFormatter to generate Cmd output.

        Args:
            program: Program to record
            output_file: Output file path
            auth_token: Optional authentication token

        Returns:
            ffmpeg command string
        """
        stream_url = program.stream_url or "<stream_url>"
        duration = program.get_duration_seconds()

        cmd_parts = ["ffmpeg"] + self.ffmpeg_opts

        if auth_token:
            cmd_parts.extend(
                [
                    "-headers",
                    f"X-Radiko-AuthToken: {auth_token}",
                ]
            )

        cmd_parts.extend(
            [
                "-i",
                stream_url,
                "-t",
                str(duration),
                "-acodec",
                "copy",
                "-vn",
                output_file,
            ]
        )

        return " ".join(shlex.quote(part) for part in cmd_parts)
