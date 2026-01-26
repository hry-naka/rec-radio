"""Unit tests for RecorderRadiko class.

Tests cover:
- RecorderRadiko initialization and ffmpeg availability check
- Recording of Radiko programs with authentication
- Stream URL retrieval via RadikoApi
- Metadata tagging
- Error handling for invalid programs
"""

import unittest
from unittest.mock import MagicMock, patch, call

from mypkg.program import Program
from mypkg.recorder_radiko import RecorderRadiko


class TestRecorderRadikoInit(unittest.TestCase):
    """Test cases for RecorderRadiko initialization."""

    def test_init_with_api_instance(self):
        """Test initialization with provided RadikoApi instance."""
        mock_api = MagicMock()
        recorder = RecorderRadiko(radiko_api=mock_api, loglevel="info")

        self.assertEqual(recorder.radiko_api, mock_api)
        self.assertEqual(recorder.loglevel, "info")

    def test_init_creates_default_api(self):
        """Test that RecorderRadiko creates RadikoApi if not provided."""
        recorder = RecorderRadiko()

        self.assertIsNotNone(recorder.radiko_api)
        # Verify it's actually a RadikoApi by checking for expected methods
        self.assertTrue(hasattr(recorder.radiko_api, "get_stream_url"))

    def test_ffmpeg_availability_check(self):
        """Test that is_available() checks for ffmpeg."""
        recorder = RecorderRadiko()

        # This should not raise an exception
        result = recorder.is_available()
        self.assertIsInstance(result, bool)


class TestRecorderRadikoRecording(unittest.TestCase):
    """Test cases for Radiko program recording."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_api = MagicMock()
        self.recorder = RecorderRadiko(radiko_api=self.mock_api, loglevel="warning")

        self.radiko_program = Program(
            title="Test Program",
            station="TBS",
            start_time="20260120133000",
            end_time="20260120135500",
            source="radiko",
            area="JP13",
            stream_url="https://example.com/stream.m3u8",
        )

        self.auth_token = "test_auth_token_123"
        self.output_file = "/tmp/test_recording.mp4"

    def test_record_program_validation_radiko_only(self):
        """Test that record_program rejects non-Radiko programs."""
        nhk_program = Program(
            title="NHK Program",
            station="NHK",
            start_time="20260120133000",
            end_time="20260120135500",
            source="nhk",
        )

        with self.assertRaises(ValueError) as context:
            self.recorder.record_program(nhk_program, self.auth_token, self.output_file)

        self.assertIn(
            "RecorderRadiko can only record Radiko programs", str(context.exception)
        )

    @patch("mypkg.recorder_radiko.RecorderRadiko.record_stream")
    @patch("mypkg.recorder_radiko.RecorderRadiko.set_metadata")
    def test_record_program_with_stream_url(
        self, mock_set_metadata, mock_record_stream
    ):
        """Test recording when stream_url is already provided."""
        mock_record_stream.return_value = True
        mock_set_metadata.return_value = True

        success = self.recorder.record_program(
            self.radiko_program,
            self.auth_token,
            self.output_file,
        )

        self.assertTrue(success)
        mock_record_stream.assert_called_once()
        # Verify correct parameters were passed to record_stream
        call_args = mock_record_stream.call_args
        self.assertEqual(call_args[1]["stream_url"], "https://example.com/stream.m3u8")
        self.assertEqual(call_args[1]["output_file"], self.output_file)
        self.assertEqual(call_args[1]["duration"], 1500)  # 25 minutes = 1500 seconds
        self.assertEqual(
            call_args[1]["headers"], {"X-Radiko-AuthToken": self.auth_token}
        )

    @patch("mypkg.recorder_radiko.RecorderRadiko.record_stream")
    @patch("mypkg.recorder_radiko.RecorderRadiko.set_metadata")
    def test_record_program_retrieves_stream_url_if_missing(
        self, mock_set_metadata, mock_record_stream
    ):
        """Test that stream URL is retrieved from API if not provided."""
        program_without_url = Program(
            title="Test Program",
            station="TBS",
            start_time="20260120133000",
            end_time="20260120135500",
            source="radiko",
            area="JP13",
            # No stream_url provided
        )

        self.mock_api.get_stream_url.return_value = (
            "https://example.com/retrieved_stream.m3u8"
        )
        mock_record_stream.return_value = True
        mock_set_metadata.return_value = True

        success = self.recorder.record_program(
            program_without_url,
            self.auth_token,
            self.output_file,
        )

        self.assertTrue(success)
        # Verify API was called to retrieve stream URL
        self.mock_api.get_stream_url.assert_called_once_with("TBS", self.auth_token)
        # Verify the retrieved URL was used
        call_args = mock_record_stream.call_args
        self.assertEqual(
            call_args[1]["stream_url"], "https://example.com/retrieved_stream.m3u8"
        )

    @patch("mypkg.recorder_radiko.RecorderRadiko.record_stream")
    def test_record_program_handles_api_failure(self, mock_record_stream):
        """Test handling of API failure when retrieving stream URL."""
        program_without_url = Program(
            title="Test Program",
            station="TBS",
            start_time="20260120133000",
            end_time="20260120135500",
            source="radiko",
        )

        self.mock_api.get_stream_url.return_value = None

        success = self.recorder.record_program(
            program_without_url,
            self.auth_token,
            self.output_file,
        )

        self.assertFalse(success)
        mock_record_stream.assert_not_called()

    @patch("mypkg.recorder_radiko.RecorderRadiko.record_stream")
    @patch("mypkg.recorder_radiko.RecorderRadiko.set_metadata")
    def test_record_program_handles_recording_failure(
        self, mock_set_metadata, mock_record_stream
    ):
        """Test handling of recording failure."""
        mock_record_stream.return_value = False

        success = self.recorder.record_program(
            self.radiko_program,
            self.auth_token,
            self.output_file,
        )

        self.assertFalse(success)
        mock_set_metadata.assert_not_called()

    @patch("mypkg.recorder_radiko.RecorderRadiko.record_stream")
    @patch("mypkg.recorder_radiko.RecorderRadiko.set_metadata")
    def test_record_program_succeeds_even_if_metadata_fails(
        self, mock_set_metadata, mock_record_stream
    ):
        """Test that recording is successful even if metadata setting fails."""
        mock_record_stream.return_value = True
        mock_set_metadata.return_value = False

        success = self.recorder.record_program(
            self.radiko_program,
            self.auth_token,
            self.output_file,
        )

        # Should still return True as recording succeeded
        self.assertTrue(success)
        mock_set_metadata.assert_called_once()


class TestRecorderRadikoAuthHeaders(unittest.TestCase):
    """Test cases for Radiko authentication header handling."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_api = MagicMock()
        self.recorder = RecorderRadiko(radiko_api=self.mock_api)

    @patch("mypkg.recorder_radiko.RecorderRadiko.record_stream")
    @patch("mypkg.recorder_radiko.RecorderRadiko.set_metadata")
    def test_auth_token_passed_in_headers(self, mock_set_metadata, mock_record_stream):
        """Test that auth token is correctly included in request headers."""
        mock_record_stream.return_value = True
        mock_set_metadata.return_value = True

        program = Program(
            title="Test",
            station="TBS",
            start_time="20260120133000",
            end_time="20260120135500",
            source="radiko",
            stream_url="https://example.com/stream.m3u8",
        )

        auth_token = "my_special_auth_token"
        self.recorder.record_program(program, auth_token, "/tmp/out.mp4")

        # Verify auth token was passed in headers
        call_args = mock_record_stream.call_args
        headers = call_args[1]["headers"]
        self.assertEqual(headers["X-Radiko-AuthToken"], auth_token)


class TestRecorderRadikoFFmpegCommand(unittest.TestCase):
    """Test cases for ffmpeg command generation."""

    def setUp(self):
        """Set up test fixtures."""
        self.recorder = RecorderRadiko()

        self.program = Program(
            title="Test Program",
            station="TBS",
            start_time="20260120133000",
            end_time="20260120135500",
            source="radiko",
            stream_url="https://example.com/stream.m3u8",
        )

    def test_get_ffmpeg_command_basic(self):
        """Test basic ffmpeg command generation."""
        output_file = "/tmp/test_recording.mp4"
        cmd = self.recorder.get_ffmpeg_command(
            self.program,
            output_file,
        )

        # Verify command contains essential elements
        self.assertIn("ffmpeg", cmd)
        self.assertIn("-i", cmd)
        self.assertIn("https://example.com/stream.m3u8", cmd)
        self.assertIn("-t", cmd)
        self.assertIn("1500", cmd)  # 25 minutes = 1500 seconds
        self.assertIn("-acodec", cmd)
        self.assertIn("copy", cmd)
        self.assertIn(output_file, cmd)

    def test_get_ffmpeg_command_with_auth_token(self):
        """Test ffmpeg command generation with auth token."""
        output_file = "/tmp/test_recording.mp4"
        auth_token = "test_token_123"

        cmd = self.recorder.get_ffmpeg_command(
            self.program,
            output_file,
            auth_token=auth_token,
        )

        # Verify auth token is included
        self.assertIn("X-Radiko-AuthToken", cmd)
        self.assertIn(auth_token, cmd)

    def test_ffmpeg_options_loaded_from_env(self):
        """Test that ffmpeg options are loaded from .env."""
        # Verify ffmpeg_opts is populated
        self.assertIsNotNone(self.recorder.ffmpeg_opts)
        self.assertIsInstance(self.recorder.ffmpeg_opts, list)

        # Should contain reconnection options from .env
        opts_str = " ".join(self.recorder.ffmpeg_opts)
        self.assertIn("-reconnect", opts_str)


class TestRecorderRadikoRecord(unittest.TestCase):
    """Test cases for unified record() method."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_api = MagicMock()
        self.recorder = RecorderRadiko(radiko_api=self.mock_api)

        self.program = Program(
            title="Test Program",
            station="TBS",
            start_time="20260120133000",
            end_time="20260120135500",
            source="radiko",
        )

    @patch("mypkg.recorder_radiko.RecorderRadiko.record_program")
    def test_record_method_handles_authorization(self, mock_record_program):
        """Test that record() method handles authorization automatically."""
        self.mock_api.authorize.return_value = ("test_token", "JP13")
        mock_record_program.return_value = True

        success = self.recorder.record(self.program)

        self.assertTrue(success)
        self.mock_api.authorize.assert_called_once()
        mock_record_program.assert_called_once()

    @patch("mypkg.recorder_radiko.RecorderRadiko.record_program")
    def test_record_method_handles_authorization_failure(self, mock_record_program):
        """Test that record() handles authorization failure."""
        self.mock_api.authorize.return_value = None

        success = self.recorder.record(self.program)

        self.assertFalse(success)
        mock_record_program.assert_not_called()


class TestRecorderRadikoBuildCmd(unittest.TestCase):
    """Test cases for build_ffmpeg_cmd() method."""

    def setUp(self):
        """Set up test fixtures."""
        self.recorder = RecorderRadiko()

        self.program = Program(
            title="Test Program",
            station="TBS",
            start_time="20260120133000",
            end_time="20260120135500",
            source="radiko",
        )

    def test_build_ffmpeg_cmd_format(self):
        """Test that build_ffmpeg_cmd generates correct tfrec_radiko.py format."""
        cmd = self.recorder.build_ffmpeg_cmd(self.program)

        # Verify command format
        self.assertIn("tfrec_radiko.py", cmd)
        self.assertIn("-s", cmd)
        self.assertIn("TBS", cmd)
        self.assertIn("-ft", cmd)
        self.assertIn("20260120133000", cmd)
        self.assertIn("-to", cmd)
        self.assertIn("20260120135500", cmd)

    def test_build_ffmpeg_cmd_matches_tfrec_format(self):
        """Test that command matches exact tfrec_radiko.py format."""
        cmd = self.recorder.build_ffmpeg_cmd(self.program)
        expected = "tfrec_radiko.py -s TBS -ft 20260120133000 -to 20260120135500"

        self.assertEqual(cmd, expected)


if __name__ == "__main__":
    unittest.main()
