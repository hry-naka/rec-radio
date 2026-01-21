"""Common recording utilities shared between Radiko and NHK recorders.

This module provides shared functionality for audio recording, metadata management,
and ffmpeg command construction that is used by both RecorderRadiko and RecorderNHK.
"""

import shlex
import shutil
import subprocess
from typing import Optional

import requests
from mutagen.mp4 import MP4, MP4Cover

from .program import Program
from .program_formatter import ProgramFormatter


class RecorderCommon:
    """Common recorder utilities for audio recording and metadata management."""

    def __init__(self, loglevel: str = "warning"):
        """Initialize common recorder with ffmpeg configuration.

        Args:
            loglevel: ffmpeg loglevel (warning, error, info, etc.)
        """
        self.loglevel = loglevel
        self.ffmpeg_path = shutil.which("ffmpeg")

    def is_available(self) -> bool:
        """Check if ffmpeg is available in PATH.

        Returns:
            True if ffmpeg is available, False otherwise
        """
        return self.ffmpeg_path is not None

    def record_stream(
        self,
        stream_url: str,
        output_file: str,
        duration: int,
        headers: Optional[dict] = None,
    ) -> bool:
        """Record audio from stream using ffmpeg.

        Args:
            stream_url: M3U8 stream URL
            output_file: Output MP4 file path
            duration: Recording duration in seconds
            headers: Optional HTTP headers to include (e.g., auth tokens)

        Returns:
            True if recording succeeded, False otherwise
        """
        if not self.is_available():
            print("Error: ffmpeg must be installed and available in PATH")
            return False

        # Build ffmpeg command with reconnection options
        cmd_parts = [
            self.ffmpeg_path,
            "-loglevel",
            self.loglevel,
            "-y",
            "-reconnect",
            "1",
            "-reconnect_at_eof",
            "0",
            "-reconnect_streamed",
            "1",
            "-reconnect_delay_max",
            "600",
            "-user_agent",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/117.0.0.0 Safari/537.36",
        ]

        # Add custom headers if provided
        if headers:
            header_str = "\r\n".join(f"{k}: {v}" for k, v in headers.items())
            cmd_parts.extend(["-headers", header_str])

        cmd_parts.extend(
            [
                "-i",
                stream_url,
                "-t",
                str(duration),
                "-acodec",
                "copy",
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
            print(result.stdout, flush=True)
            if result.stderr:
                print(result.stderr, flush=True)
            return True
        except subprocess.CalledProcessError as e:
            print(
                f"Recording failed with return code {e.returncode}",
                flush=True,
            )
            print(e.stdout, flush=True)
            if e.stderr:
                print(e.stderr, flush=True)
            return False

    def set_metadata(
        self,
        audio_file: str,
        program: Program,
        track_num: Optional[int] = None,
    ) -> bool:
        """Set MP4 metadata tags for recorded file.

        Args:
            audio_file: Path to MP4 file
            program: Program information
            track_num: Optional track number

        Returns:
            True if metadata was set successfully, False otherwise
        """
        try:
            audio = MP4(audio_file)

            # Set title
            if program.title:
                audio.tags["\xa9nam"] = [program.title]

            # Set album (station name)
            audio.tags["\xa9alb"] = [program.station]

            # Set artist (performer/host)
            if program.performer:
                audio.tags["\xa9ART"] = [program.performer]
                audio.tags["aART"] = [program.performer]

            # Set comment (description and info)
            comment = ProgramFormatter.get_metadata_comment(
                program.description,
                program.info,
            )
            if comment:
                audio.tags["\xa9cmt"] = [comment]

            # Set genre
            audio.tags["\xa9gen"] = ["Radio"]

            # Set track number if provided
            if track_num:
                audio.tags["trkn"] = [(track_num, 0)]

            # Set disk number
            audio.tags["disk"] = [(1, 1)]

            # Set cover art if available
            if program.image_url:
                try:
                    coverart = requests.get(program.image_url, timeout=(20, 5)).content
                    cover = MP4Cover(coverart, imageformat=MP4Cover.FORMAT_PNG)
                    audio["covr"] = [cover]
                except requests.exceptions.RequestException as e:
                    print(f"Warning: Failed to fetch cover art: {e}")

            audio.save()
            return True
        except (OSError, ValueError, AttributeError) as e:
            print(f"Error setting metadata: {e}")
            return False
