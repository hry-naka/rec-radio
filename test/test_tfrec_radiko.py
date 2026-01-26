"""Unit tests for tfrec_radiko.py module."""

import sys
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest

# Add parent directory to path
sys.path.insert(0, "/Users/nakamurahiroyuki/git/rec-radio")

from mypkg.program import Program
from tfrec_radiko import (
    generate_output_filename,
    record_program,
    validate_datetime_format,
)


class TestValidateDatetimeFormat:
    """Tests for validate_datetime_format function."""

    def test_valid_format(self):
        """Test with valid datetime format."""
        assert validate_datetime_format("20260125093000") is True
        assert validate_datetime_format("20231231235959") is True

    def test_invalid_length(self):
        """Test with invalid length."""
        assert validate_datetime_format("2026012509300") is False
        assert validate_datetime_format("202601250930000") is False

    def test_invalid_format(self):
        """Test with invalid format."""
        assert validate_datetime_format("20261325093000") is False  # Invalid month
        assert validate_datetime_format("20260132093000") is False  # Invalid day
        assert validate_datetime_format("20260125253000") is False  # Invalid hour

    def test_non_numeric(self):
        """Test with non-numeric characters."""
        assert validate_datetime_format("2026-01-25-0930") is False
        assert validate_datetime_format("abcd1225093000") is False


class TestGenerateOutputFilename:
    """Tests for generate_output_filename function."""

    def test_basic_filename(self):
        """Test basic filename generation."""
        filename = generate_output_filename("TBS", "20260125093000", "20260125100000")
        assert filename == "TBS_2026-01-25-09_30.mp4"

    def test_different_station(self):
        """Test with different station."""
        filename = generate_output_filename("INT", "20231231235500", "20240101000500")
        assert filename == "INT_2023-12-31-23_55.mp4"

    def test_filename_format(self):
        """Test filename format parts."""
        filename = generate_output_filename("FMT", "20260501120000", "20260501130000")
        assert filename.startswith("FMT_")
        assert filename.endswith(".mp4")
        assert "2026-05-01" in filename
        assert "12_00" in filename


class TestRecordProgram:
    """Tests for record_program function."""

    @patch("tfrec_radiko.RecorderRadiko")
    @patch("tfrec_radiko.RadikoApi")
    @patch("tfrec_radiko.load_dotenv")
    def test_successful_program_recording(
        self,
        mock_load_dotenv,
        mock_radiko_api_class,
        mock_recorder_class,
    ):
        """Test successful program recording."""
        # Setup mocks
        mock_api = MagicMock()
        mock_api.authorize.return_value = ("test_token", "JP13")
        mock_radiko_api_class.return_value = mock_api

        mock_recorder = MagicMock()
        mock_recorder.record_program.return_value = True
        mock_recorder_class.return_value = mock_recorder

        # Create test program
        program = Program(
            title="テスト番組",
            station="TBS",
            start_time="20260125093000",
            end_time="20260125100000",
            source="radiko",
        )

        # Call function
        result = record_program(program)

        # Verify
        assert result is True
        mock_load_dotenv.assert_called_once()
        mock_radiko_api_class.assert_called_once()
        mock_api.authorize.assert_called_once()
        mock_recorder.record_program.assert_called_once()

    def test_invalid_source(self):
        """Test with non-Radiko source."""
        program = Program(
            title="Test",
            station="NR1",
            start_time="20260125093000",
            end_time="20260125100000",
            source="nhk",
        )

        with pytest.raises(ValueError, match="Program source must be 'radiko'"):
            record_program(program)

    def test_missing_station(self):
        """Test with missing station."""
        program = Program(
            title="Test",
            station="",
            start_time="20260125093000",
            end_time="20260125100000",
            source="radiko",
        )

        with pytest.raises(ValueError, match="must have station"):
            record_program(program)

    def test_invalid_time_format(self):
        """Test with invalid time format."""
        program = Program(
            title="Test",
            station="TBS",
            start_time="2026-01-25",
            end_time="20260125100000",
            source="radiko",
        )

        with pytest.raises(ValueError, match="Invalid start_time format"):
            record_program(program)

    @patch("tfrec_radiko.RecorderRadiko")
    @patch("tfrec_radiko.RadikoApi")
    @patch("tfrec_radiko.load_dotenv")
    def test_authorization_failure(
        self,
        mock_load_dotenv,
        mock_radiko_api_class,
        mock_recorder_class,
    ):
        """Test authorization failure."""
        # Setup mocks
        mock_api = MagicMock()
        mock_api.authorize.return_value = None
        mock_radiko_api_class.return_value = mock_api

        # Create test program
        program = Program(
            title="Test",
            station="TBS",
            start_time="20260125093000",
            end_time="20260125100000",
            source="radiko",
        )

        # Call function
        result = record_program(program)

        # Verify
        assert result is False


class TestCommandLineIntegration:
    """Integration tests for command-line usage."""

    @patch("tfrec_radiko.record_program")
    def test_main_function_success(self, mock_record_program):
        """Test main function with successful recording."""
        # Setup mocks
        mock_record_program.return_value = True

        # Mock sys.argv
        with patch(
            "sys.argv",
            [
                "tfrec_radiko.py",
                "-s",
                "TBS",
                "-ft",
                "20260125093000",
                "-to",
                "20260125100000",
            ],
        ):
            from tfrec_radiko import main

            # Call main - should not raise
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
