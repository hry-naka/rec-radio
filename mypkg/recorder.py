"""Audio recording module for Radiko streams using ffmpeg."""

import importlib.util
import os
import sys
import shlex
import shutil
import subprocess
from typing import Optional

import requests
from mutagen.mp4 import MP4, MP4Cover

from .program import Program
from .program_formatter import ProgramFormatter
from .nhk_api import NhkAPIClient
class Recorder:
    """Handle audio recording and metadata management for MP4 files."""

    def __init__(
        self,
        loglevel: Optional[str] = None,
        reconnect_delay_max: Optional[str] = None,
        rw_timeout: Optional[str] = None,
        audio_codec: Optional[str] = None,
        audio_bitrate: Optional[str] = None,
        audio_sample_rate: Optional[str] = None,
        extra_options: Optional[str] = None
    ):
        # load environment variables from .env file, if not specified in constructor
        self.loglevel = loglevel or os.getenv("FFMPEG_LOGLEVEL", "warning")
        self.reconnect_delay_max = reconnect_delay_max or os.getenv("FFMPEG_RECONNECT_DELAY_MAX", "600")
        self.rw_timeout = rw_timeout or os.getenv("FFMPEG_RW_TIMEOUT", "900000000")
        self.audio_codec = audio_codec or os.getenv("FFMPEG_AUDIO_CODEC", "aac")
        self.audio_bitrate = audio_bitrate or os.getenv("FFMPEG_AUDIO_BITRATE", "96k")
        self.audio_sample_rate = audio_sample_rate or os.getenv("FFMPEG_AUDIO_SAMPLE_RATE", "22050")
        default_extra = "-reconnect 1 -reconnect_at_eof 0 -reconnect_streamed 1 -live_start_index -2 -http_persistent 0"
        self.extra_options = extra_options or os.getenv("FFMPEG_EXTRA_OPTIONS", default_extra)

        self.ffmpeg_path = shutil.which("ffmpeg")
        self.timeout_path = shutil.which("timeout") or shutil.which("gtimeout")
        self.yt_dlp_spec = importlib.util.find_spec("yt_dlp")

    def _is_available(self,service="radiko") -> bool:
        """Check if required tools are available.

        Returns:
            True if both ffmpeg and yt_dlp are available, False otherwise
        """
        if(service=="radiko"):
            has_yt_dlp = self.yt_dlp_spec is not None
            return has_yt_dlp
        else:
            has_ffmpeg = self.ffmpeg_path is not None or self.timeout_path is not None
            return has_ffmpeg

    def record_radiko_timefree(self,station, ft, output) -> bool:
        if not self._is_available("radiko"):
            print("Error: yt_dlp must be installed and available in PATH")
            return False
        url = f"https://radiko.jp/#!/ts/{station}/{ft}"
        output_tmpl = output.replace(".m4a", ".%(ext)s")
        cmd = [
            sys.executable,
            "-m",
            "yt_dlp",
            "-q", "--no-warnings", "--progress", "-x",
            "--external-downloader-args", f"ffmpeg:-loglevel {self.loglevel}",
            "--postprocessor-args", f"ffmpeg:-loglevel {self.loglevel}",
            "--audio-format", "m4a",
            "--audio-quality", "0",
            "-o",output_tmpl,
            url,
        ]
        print( cmd, flush=True)
        try:
            subprocess.run(cmd, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Radiko Timefree Rec. Error:\n{e.stderr}", file=sys.stderr)
            return False

    def record_radiko_live(self,station, duration, output) -> bool:
        if not self._is_available("radiko"):
            print("Error: yt_dlp must be installed and available in PATH")
            return False
        url = f"https://radiko.jp/#!/live/{station}"
        output_tmpl = output.replace(".m4a", ".%(ext)s")
        cmd = [
            sys.executable,
            "-m",
            "yt_dlp",
            "-q", "--no-warnings", "--progress", "-x",
            "--external-downloader-args", f"ffmpeg:-loglevel {self.loglevel}",
            "--postprocessor-args", f"ffmpeg:-loglevel {self.loglevel}",
            "--download-sections", f"*0-{duration}",
            "--audio-format", "m4a",
            "--audio-quality", "0",
            "-o", output_tmpl,
            url,
        ]
        print( cmd, flush=True)
        try:
            subprocess.run(cmd, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Radiko Live Rec. Error:\n{e.stderr}", file=sys.stderr)
            return False

    def record_nhk_live(
        self,
        nhk_apiclient: NhkAPIClient,
        duration: int,
        output: str,
        prefix: str,
        date: str,
    ) -> bool:
        """Perform live recording using ffmpeg with timeout.

        Args:
            nhk_apiclient: NhkAPIClient instance
            duration: Recording duration in seconds
            outdir: Output directory
            prefix: Output file prefix
            date: Date string for filename

        Returns:
            True if recording succeeded, False otherwise
        """
        if self._is_available("nhk") is False:
            print("Error: ffmpeg and timeout must be installed and in PATH")
            return False
        url = nhk_apiclient.get_streamurl()
        if url is None:
            print("Error: Failed to retrieve NHK stream URL")
            return False
        cmd = [
            self.timeout_path,
            str(duration + 20),
            self.ffmpeg_path,
            "-loglevel", self.loglevel,
            "-y",
            "-nostdin",
            "-re",
            *self.extra_options.split(),
            "-reconnect_delay_max", self.reconnect_delay_max,
            "-rw_timeout", self.rw_timeout,
            "-user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "-i", url,
            "-t", str(duration + 5),
            "-vn",
            "-c:a", self.audio_codec,
            "-b:a", self.audio_bitrate,
            "-ar", self.audio_sample_rate,
            output,
        ]
        print(cmd, flush=True)
        try:
            subprocess.run(cmd, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error: ffmpeg failed with return code {e.returncode}")
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
                audio.tags["\xa9nam"] = program.title

            # Set album (station name)
            audio.tags["\xa9alb"] = program.station

            # Set artist (performer/host)
            if program.performer:
                audio.tags["\xa9ART"] = program.performer
                audio.tags["aART"] = program.performer

            # Set comment (description and info)
            comment = ProgramFormatter.get_metadata_comment(
                program.description,
                program.info,
            )
            if comment:
                audio.tags["\xa9cmt"] = comment

            # Set genre
            audio.tags["\xa9gen"] = "Radio"

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
        except Exception as e:
            print(f"Error setting metadata: {e}")
            return False
