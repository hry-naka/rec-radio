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


if __name__ == "__main__":
    unittest.main()
