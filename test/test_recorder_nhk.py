"""Unit tests for RecorderNHK class.

Tests cover:
- RecorderNHK initialization and ffmpeg availability check
- Recording of NHK programs
- Stream URL validation
- Metadata tagging
- Error handling for invalid programs
"""

import unittest
from unittest.mock import MagicMock, patch

from mypkg.program import Program
from mypkg.recorder_nhk import RecorderNHK


class TestRecorderNHKInit(unittest.TestCase):
    """Test cases for RecorderNHK initialization."""

    def test_init_with_api_instance(self):
        """Test initialization with provided NHKApi instance."""
        mock_api = MagicMock()
        recorder = RecorderNHK(nhk_api=mock_api, loglevel="info")

        self.assertEqual(recorder.nhk_api, mock_api)
        self.assertEqual(recorder.loglevel, "info")

    def test_init_creates_default_api(self):
        """Test that RecorderNHK creates NHKApi if not provided."""
        recorder = RecorderNHK()

        self.assertIsNotNone(recorder.nhk_api)
        # Verify it's actually an NHKApi by checking for expected methods
        self.assertTrue(hasattr(recorder.nhk_api, "get_series"))

    def test_ffmpeg_availability_check(self):
        """Test that is_available() checks for ffmpeg."""
        recorder = RecorderNHK()

        # This should not raise an exception
        result = recorder.is_available()
        self.assertIsInstance(result, bool)


class TestRecorderNHKRecording(unittest.TestCase):
    """Test cases for NHK program recording."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_api = MagicMock()
        self.recorder = RecorderNHK(nhk_api=self.mock_api, loglevel="warning")

        self.nhk_program = Program(
            title="ラジオ文芸館",
            station="NHK",
            start_time="20260120230000",
            end_time="20260120232400",
            source="nhk",
            stream_url="https://example.com/nhk_stream.m3u8",
            program_sub_title="作: 劇作家太郎",
        )

        self.output_file = "/tmp/test_nhk_recording.mp4"

    def test_record_program_validation_nhk_only(self):
        """Test that record_program rejects non-NHK programs."""
        radiko_program = Program(
            title="Test Program",
            station="TBS",
            start_time="20260120133000",
            end_time="20260120135500",
            source="radiko",
        )

        with self.assertRaises(ValueError) as context:
            self.recorder.record_program(radiko_program, self.output_file)

        self.assertIn(
            "RecorderNHK can only record NHK programs", str(context.exception)
        )

    @patch("mypkg.recorder_nhk.RecorderNHK.record_stream")
    @patch("mypkg.recorder_nhk.RecorderNHK.set_metadata")
    def test_record_program_with_stream_url(
        self, mock_set_metadata, mock_record_stream
    ):
        """Test recording when stream_url is provided."""
        mock_record_stream.return_value = True
        mock_set_metadata.return_value = True

        success = self.recorder.record_program(
            self.nhk_program,
            self.output_file,
        )

        self.assertTrue(success)
        mock_record_stream.assert_called_once()
        # Verify correct parameters were passed to record_stream
        call_args = mock_record_stream.call_args
        self.assertEqual(
            call_args[1]["stream_url"], "https://example.com/nhk_stream.m3u8"
        )
        self.assertEqual(call_args[1]["output_file"], self.output_file)
        self.assertEqual(call_args[1]["duration"], 1440)  # 24 minutes = 1440 seconds
        self.assertIsNone(call_args[1]["headers"])  # NHK doesn't use auth headers

    def test_record_program_rejects_missing_stream_url(self):
        """Test that recording fails if stream_url is not available."""
        program_without_url = Program(
            title="ラジオ文芸館",
            station="NHK",
            start_time="20260120230000",
            end_time="20260120232400",
            source="nhk",
            # No stream_url provided
        )

        success = self.recorder.record_program(
            program_without_url,
            self.output_file,
        )

        self.assertFalse(success)

    @patch("mypkg.recorder_nhk.RecorderNHK.record_stream")
    @patch("mypkg.recorder_nhk.RecorderNHK.set_metadata")
    def test_record_program_no_auth_headers(
        self, mock_set_metadata, mock_record_stream
    ):
        """Test that NHK recording does not include auth headers."""
        mock_record_stream.return_value = True
        mock_set_metadata.return_value = True

        self.recorder.record_program(
            self.nhk_program,
            self.output_file,
        )

        # Verify headers are None for NHK
        call_args = mock_record_stream.call_args
        self.assertIsNone(call_args[1]["headers"])

    @patch("mypkg.recorder_nhk.RecorderNHK.record_stream")
    @patch("mypkg.recorder_nhk.RecorderNHK.set_metadata")
    def test_record_program_handles_recording_failure(
        self, mock_set_metadata, mock_record_stream
    ):
        """Test handling of recording failure."""
        mock_record_stream.return_value = False

        success = self.recorder.record_program(
            self.nhk_program,
            self.output_file,
        )

        self.assertFalse(success)
        mock_set_metadata.assert_not_called()

    @patch("mypkg.recorder_nhk.RecorderNHK.record_stream")
    @patch("mypkg.recorder_nhk.RecorderNHK.set_metadata")
    def test_record_program_succeeds_even_if_metadata_fails(
        self, mock_set_metadata, mock_record_stream
    ):
        """Test that recording is successful even if metadata setting fails."""
        mock_record_stream.return_value = True
        mock_set_metadata.return_value = False

        success = self.recorder.record_program(
            self.nhk_program,
            self.output_file,
        )

        # Should still return True as recording succeeded
        self.assertTrue(success)
        mock_set_metadata.assert_called_once()

    @patch("mypkg.recorder_nhk.RecorderNHK.record_stream")
    @patch("mypkg.recorder_nhk.RecorderNHK.set_metadata")
    def test_record_program_with_metadata(self, mock_set_metadata, mock_record_stream):
        """Test that metadata is correctly passed to set_metadata."""
        mock_record_stream.return_value = True
        mock_set_metadata.return_value = True

        self.recorder.record_program(
            self.nhk_program,
            self.output_file,
        )

        # Verify metadata was set with correct program info
        mock_set_metadata.assert_called_once()
        call_args = mock_set_metadata.call_args
        self.assertEqual(call_args[0][0], self.output_file)
        self.assertEqual(call_args[0][1], self.nhk_program)


class TestRecorderNHKDuration(unittest.TestCase):
    """Test cases for NHK program duration handling."""

    def setUp(self):
        """Set up test fixtures."""
        self.recorder = RecorderNHK()

    @patch("mypkg.recorder_nhk.RecorderNHK.record_stream")
    @patch("mypkg.recorder_nhk.RecorderNHK.set_metadata")
    def test_duration_calculation_from_program_times(
        self, mock_set_metadata, mock_record_stream
    ):
        """Test that duration is correctly calculated from program start/end times."""
        mock_record_stream.return_value = True
        mock_set_metadata.return_value = True

        # Program with 30 minute duration (1800 seconds)
        program = Program(
            title="Test",
            station="NHK",
            start_time="20260120140000",
            end_time="20260120141000",
            source="nhk",
            stream_url="https://example.com/stream.m3u8",
        )

        self.recorder.record_program(program, "/tmp/out.mp4")

        # Verify duration passed to record_stream is in seconds
        call_args = mock_record_stream.call_args
        duration = call_args[1]["duration"]
        self.assertGreater(duration, 0)


class TestRecorderNHKFFmpegCommand(unittest.TestCase):
    """Test cases for ffmpeg command generation."""

    def setUp(self):
        """Set up test fixtures."""
        self.recorder = RecorderNHK()

        self.program = Program(
            title="ラジオ文芸館",
            station="NHK",
            start_time="20260120230000",
            end_time="20260120232400",
            source="nhk",
            stream_url="https://example.com/nhk_stream.m3u8",
        )

    def test_get_ffmpeg_command_basic(self):
        """Test basic ffmpeg command generation for NHK."""
        output_file = "/tmp/test_recording.mp4"
        cmd = self.recorder.get_ffmpeg_command(
            self.program,
            output_file,
        )

        # Verify command contains essential elements
        self.assertIn("ffmpeg", cmd)
        self.assertIn("-i", cmd)
        self.assertIn("https://example.com/nhk_stream.m3u8", cmd)
        self.assertIn("-t", cmd)
        self.assertIn("1440", cmd)  # 24 minutes = 1440 seconds
        self.assertIn("-acodec", cmd)
        self.assertIn("copy", cmd)
        self.assertIn(output_file, cmd)

    def test_ffmpeg_options_loaded_from_env(self):
        """Test that ffmpeg options are loaded from .env."""
        # Verify ffmpeg_opts is populated
        self.assertIsNotNone(self.recorder.ffmpeg_opts)
        self.assertIsInstance(self.recorder.ffmpeg_opts, list)

        # Should contain reconnection options from .env
        opts_str = " ".join(self.recorder.ffmpeg_opts)
        self.assertIn("-reconnect", opts_str)


class TestRecorderNHKRecord(unittest.TestCase):
    """Test cases for unified record() method."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_api = MagicMock()
        self.recorder = RecorderNHK(nhk_api=self.mock_api)

        self.program = Program(
            title="ラジオ文芸館",
            station="NHK",
            start_time="20260120230000",
            end_time="20260120232400",
            source="nhk",
            stream_url="https://example.com/nhk_stream.m3u8",
        )

    @patch("mypkg.recorder_nhk.RecorderNHK.record_program")
    def test_record_method_calls_record_program(self, mock_record_program):
        """Test that record() method calls record_program."""
        mock_record_program.return_value = True

        success = self.recorder.record(self.program)

        self.assertTrue(success)
        mock_record_program.assert_called_once()


class TestRecorderNHKBuildCmd(unittest.TestCase):
    """Test cases for build_ffmpeg_cmd() method."""

    def setUp(self):
        """Set up test fixtures."""
        self.recorder = RecorderNHK()

        self.program = Program(
            title="ラジオ文芸館",
            station="NHK",
            start_time="20260120230000",
            end_time="20260120232400",
            source="nhk",
            series_site_id="ABC123",
        )

    def test_build_ffmpeg_cmd_format(self):
        """Test that build_ffmpeg_cmd generates correct tfrec_nhk.py format."""
        cmd = self.recorder.build_ffmpeg_cmd(self.program)

        # Verify command format
        self.assertIn("tfrec_nhk.py", cmd)
        self.assertIn("--id", cmd)
        self.assertIn("ABC123", cmd)
        self.assertIn("--date", cmd)
        self.assertIn("20260120", cmd)
        self.assertIn("--title", cmd)
        self.assertIn("ラジオ文芸館", cmd)

    def test_build_ffmpeg_cmd_matches_tfrec_format(self):
        """Test that command matches exact tfrec_nhk.py format."""
        cmd = self.recorder.build_ffmpeg_cmd(self.program)
        expected = 'tfrec_nhk.py --id ABC123 --date 20260120 --title "ラジオ文芸館"'

        self.assertEqual(cmd, expected)


if __name__ == "__main__":
    unittest.main()
