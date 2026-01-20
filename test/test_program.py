"""Unit tests for the Program class.

Tests cover:
- Program factory methods (from_nhk_series, from_radiko_program)
- Helper methods (is_nhk, is_radiko, is_recordable)
- Time handling (get_start_datetime, get_end_datetime, duration)
- Normalization of different date formats
"""

import unittest
from datetime import datetime

from mypkg.program import Program


class TestProgramFactoryNHK(unittest.TestCase):
    """Test cases for Program.from_nhk_series() factory method."""

    def setUp(self):
        """Set up test fixtures for NHK program data."""
        self.series_data = {
            "title": "ラジオ文芸館",
            "series_site_id": "nhk_FM",
        }

        self.episode_data = {
            "program_title": "「にほんごであそぼ」～鼠小僧次郎吉～",
            "onair_date": "2026-01-18(日)午後11:30放送",
            "closed_at": "2026-01-26",
            "stream_url": "https://example.com/nhk_stream.m3u8",
            "program_sub_title": "作: 劇作家太郎",
        }

    def test_from_nhk_series_basic(self):
        """Test basic creation from NHK series/episode data."""
        program = Program.from_nhk_series(self.series_data, self.episode_data)

        self.assertEqual(program.source, "nhk")
        self.assertEqual(program.title, "ラジオ文芸館")
        self.assertEqual(program.program_sub_title, "作: 劇作家太郎")
        self.assertEqual(program.stream_url, "https://example.com/nhk_stream.m3u8")
        self.assertEqual(program.closed_at, "2026-01-26")
        self.assertTrue(program.is_nhk())
        self.assertFalse(program.is_radiko())

    def test_from_nhk_series_has_onair_date(self):
        """Test that onair_date is properly set."""
        program = Program.from_nhk_series(self.series_data, self.episode_data)
        self.assertIsNotNone(program.onair_date)
        self.assertEqual(program.onair_date, "2026-01-18(日)午後11:30放送")

    def test_from_nhk_series_with_missing_optional_fields(self):
        """Test creation with missing optional fields."""
        minimal_episode = {
            "stream_url": "https://example.com/stream.m3u8",
        }

        program = Program.from_nhk_series(self.series_data, minimal_episode)
        self.assertEqual(program.title, "ラジオ文芸館")
        self.assertIsNone(program.program_sub_title)
        self.assertIsNone(program.closed_at)
        self.assertIsNone(program.onair_date)

    def test_from_nhk_series_sets_default_station(self):
        """Test that default station is set to 'NHK'."""
        program = Program.from_nhk_series(self.series_data, self.episode_data)
        self.assertEqual(program.station, "NHK")

    def test_from_nhk_series_is_recordable_with_stream_url(self):
        """Test that program is recordable when stream_url is present."""
        program = Program.from_nhk_series(self.series_data, self.episode_data)
        self.assertTrue(program.is_recordable())

    def test_from_nhk_series_is_not_recordable_without_stream_url(self):
        """Test that program is not recordable without stream_url."""
        episode = {
            "program_title": "Test",
            # No stream_url
        }
        program = Program.from_nhk_series(self.series_data, episode)
        self.assertFalse(program.is_recordable())


class TestProgramFactoryRadiko(unittest.TestCase):
    """Test cases for Program.from_radiko_program() factory method."""

    def setUp(self):
        """Set up test fixtures for Radiko program data."""
        self.program_data = {
            "title": "レコレール",
            "station": "INT",
            "start_time": "20260120133000",
            "end_time": "20260120135500",
            "area": "JP13",
            "performer": 'SOIL&"PIMP"SESSIONS',
            "description": "Music program",
            "info": "Groove Music",
            "image_url": "https://example.com/image.jpg",
            "url": "https://example.com/program",
        }

    def test_from_radiko_program_basic(self):
        """Test basic creation from Radiko program data."""
        program = Program.from_radiko_program(self.program_data)

        self.assertEqual(program.source, "radiko")
        self.assertEqual(program.title, "レコレール")
        self.assertEqual(program.station, "INT")
        self.assertEqual(program.start_time, "20260120133000")
        self.assertEqual(program.end_time, "20260120135500")
        self.assertEqual(program.area, "JP13")
        self.assertEqual(program.performer, 'SOIL&"PIMP"SESSIONS')
        self.assertFalse(program.is_nhk())
        self.assertTrue(program.is_radiko())

    def test_from_radiko_program_stores_all_fields(self):
        """Test that all Radiko-specific fields are stored."""
        program = Program.from_radiko_program(self.program_data)
        self.assertEqual(program.description, "Music program")
        self.assertEqual(program.info, "Groove Music")
        self.assertEqual(program.image_url, "https://example.com/image.jpg")
        self.assertEqual(program.url, "https://example.com/program")

    def test_from_radiko_program_default_stream_url(self):
        """Test that stream_url defaults to None for Radiko."""
        program = Program.from_radiko_program(self.program_data)
        self.assertIsNone(program.stream_url)

    def test_from_radiko_program_with_stream_url(self):
        """Test Radiko program with explicit stream_url."""
        data = self.program_data.copy()
        data["stream_url"] = "https://example.com/stream.m3u8"

        program = Program.from_radiko_program(data)
        self.assertEqual(program.stream_url, "https://example.com/stream.m3u8")

    def test_from_radiko_program_is_recordable_with_stream_url(self):
        """Test that Radiko program is recordable with stream_url."""
        data = self.program_data.copy()
        data["stream_url"] = "https://example.com/stream.m3u8"

        program = Program.from_radiko_program(data)
        self.assertTrue(program.is_recordable())

    def test_from_radiko_program_is_not_recordable_without_stream_url(self):
        """Test that Radiko program without stream_url is not recordable."""
        program = Program.from_radiko_program(self.program_data)
        self.assertFalse(program.is_recordable())


class TestProgramHelperMethods(unittest.TestCase):
    """Test cases for Program helper methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.nhk_program = Program(
            source="nhk",
            title="番組名",
            station="NHK",
            start_time="20260120133000",
            end_time="20260120135500",
            area="JP13",
            stream_url="https://example.com/stream.m3u8",
        )

        self.radiko_program = Program(
            source="radiko",
            title="レコレール",
            station="INT",
            start_time="20260120133000",
            end_time="20260120135500",
            area="JP13",
            stream_url="https://example.com/stream.m3u8",
        )

    def test_is_nhk_returns_true_for_nhk_source(self):
        """Test is_nhk() returns True for NHK programs."""
        self.assertTrue(self.nhk_program.is_nhk())

    def test_is_nhk_returns_false_for_radiko_source(self):
        """Test is_nhk() returns False for Radiko programs."""
        self.assertFalse(self.radiko_program.is_nhk())

    def test_is_radiko_returns_false_for_nhk_source(self):
        """Test is_radiko() returns False for NHK programs."""
        self.assertFalse(self.nhk_program.is_radiko())

    def test_is_radiko_returns_true_for_radiko_source(self):
        """Test is_radiko() returns True for Radiko programs."""
        self.assertTrue(self.radiko_program.is_radiko())

    def test_is_recordable_returns_true_with_stream_url(self):
        """Test is_recordable() returns True when stream_url is present."""
        self.assertTrue(self.nhk_program.is_recordable())
        self.assertTrue(self.radiko_program.is_recordable())

    def test_is_recordable_returns_false_without_stream_url(self):
        """Test is_recordable() returns False when stream_url is missing."""
        program = Program(
            source="nhk",
            title="Test",
            station="NHK",
            start_time="20260120133000",
            end_time="20260120135500",
            area="JP13",
            # No stream_url
        )
        self.assertFalse(program.is_recordable())


class TestProgramTimeHandling(unittest.TestCase):
    """Test cases for Program time handling."""

    def setUp(self):
        """Set up test fixtures."""
        self.program = Program(
            source="radiko",
            title="Test",
            station="INT",
            start_time="20260120133000",  # 2026-01-20 13:30:00
            end_time="20260120135500",  # 2026-01-20 13:55:00
            area="JP13",
        )

    def test_get_start_datetime(self):
        """Test get_start_datetime() returns correct datetime object."""
        start_dt = self.program.get_start_datetime()
        self.assertEqual(start_dt.year, 2026)
        self.assertEqual(start_dt.month, 1)
        self.assertEqual(start_dt.day, 20)
        self.assertEqual(start_dt.hour, 13)
        self.assertEqual(start_dt.minute, 30)
        self.assertEqual(start_dt.second, 0)

    def test_get_end_datetime(self):
        """Test get_end_datetime() returns correct datetime object."""
        end_dt = self.program.get_end_datetime()
        self.assertEqual(end_dt.year, 2026)
        self.assertEqual(end_dt.month, 1)
        self.assertEqual(end_dt.day, 20)
        self.assertEqual(end_dt.hour, 13)
        self.assertEqual(end_dt.minute, 55)
        self.assertEqual(end_dt.second, 0)

    def test_get_duration_minutes(self):
        """Test get_duration_minutes() returns correct duration."""
        duration = self.program.get_duration_minutes()
        self.assertEqual(duration, 25)

    def test_get_duration_seconds(self):
        """Test get_duration_seconds() returns correct duration."""
        duration = self.program.get_duration_seconds()
        self.assertEqual(duration, 25 * 60)

    def test_duration_set_in_post_init(self):
        """Test that duration is set automatically in __post_init__()."""
        # Duration should be calculated and set to 25 minutes
        self.assertEqual(self.program.duration, 25)

    def test_time_across_midnight(self):
        """Test duration calculation for program crossing midnight."""
        program = Program(
            source="nhk",
            title="Late Night Show",
            station="NHK",
            start_time="20260120230000",  # 23:00
            end_time="20260121010000",  # 01:00 (next day)
            area="JP13",
        )
        duration = program.get_duration_minutes()
        self.assertEqual(duration, 120)  # 2 hours


class TestProgramStringRepresentation(unittest.TestCase):
    """Test cases for Program string representation."""

    def test_str_representation_nhk(self):
        """Test __str__() for NHK program."""
        program = Program(
            source="nhk",
            title="ニュース",
            station="NHK",
            start_time="20260120140000",
            end_time="20260120141500",
            area="JP13",
        )
        expected = "[NHK] ニュース (14:00-14:15)"
        self.assertEqual(str(program), expected)

    def test_str_representation_radiko(self):
        """Test __str__() for Radiko program."""
        program = Program(
            source="radiko",
            title="レコレール",
            station="INT",
            start_time="20260120133000",
            end_time="20260120135500",
            area="JP13",
        )
        expected = "[INT] レコレール (13:30-13:55)"
        self.assertEqual(str(program), expected)


class TestProgramNormalizationNHK(unittest.TestCase):
    """Test cases for NHK date/time normalization."""

    def test_normalize_nhk_datetime_full_format(self):
        """Test normalization of full NHK datetime format."""
        # Format: "1月18日(日)午後11:30放送"
        date_str = "1月18日(日)午後11:30放送"
        normalized = Program._normalize_nhk_datetime(date_str)

        # Should be in YYYYMMDDHHMMSS format (14 digits)
        self.assertEqual(len(normalized), 14)
        self.assertTrue(normalized.isdigit())
        # Should end with 233000 (23:30:00 in 24-hour format)
        self.assertTrue(normalized.endswith("233000"))

    def test_normalize_nhk_datetime_returns_string(self):
        """Test that _normalize_nhk_datetime() returns a string."""
        result = Program._normalize_nhk_datetime("1月18日(日)午後11:30放送")
        self.assertIsInstance(result, str)

    def test_normalize_nhk_datetime_handles_morning(self):
        """Test normalization of morning time."""
        result = Program._normalize_nhk_datetime("1月18日(日)午前9:00放送")
        # Should end with 090000 (09:00:00)
        self.assertTrue(result.endswith("090000"))

    def test_normalize_nhk_datetime_handles_afternoon(self):
        """Test normalization of afternoon time."""
        result = Program._normalize_nhk_datetime("1月18日(日)午後3:30放送")
        # Should end with 153000 (15:30:00)
        self.assertTrue(result.endswith("153000"))


class TestProgramIntegration(unittest.TestCase):
    """Integration tests for Program class with real-world scenarios."""

    def test_nhk_to_program_workflow(self):
        """Test creating Program from NHK API response structure."""
        # Simulating nhk_api.extract_recording_info() return value
        nhk_recording_info = {
            "title": "ラジオ文芸館",
            "series_site_id": "nhk_FM_jbkc",
            "program_title": "「にほんごであそぼ」～鼠小僧次郎吉～",
            "onair_date": "2026-01-18(日)午後11:30放送",
            "closed_at": "2026-01-26",
            "stream_url": "https://example.com/nhk_stream.m3u8",
            "program_sub_title": "作: 劇作家太郎",
        }

        # Create Program from NHK data
        program = Program.from_nhk_series(
            {"title": nhk_recording_info["title"]},
            nhk_recording_info,
        )

        # Verify program is properly constructed
        self.assertTrue(program.is_nhk())
        self.assertTrue(program.is_recordable())
        self.assertEqual(program.stream_url, nhk_recording_info["stream_url"])

    def test_radiko_to_program_workflow(self):
        """Test creating Program from Radiko API response structure."""
        radiko_program_data = {
            "title": "レコレール",
            "station": "INT",
            "start_time": "20260120133000",
            "end_time": "20260120135500",
            "area": "JP13",
            "performer": 'SOIL&"PIMP"SESSIONS',
            "description": "Groove Music",
            "info": "FM",
            "image_url": "https://example.com/image.jpg",
            "url": "https://example.com/program",
            "stream_url": "https://example.com/radiko_stream.m3u8",
        }

        # Create Program from Radiko data
        program = Program.from_radiko_program(radiko_program_data)

        # Verify program is properly constructed
        self.assertTrue(program.is_radiko())
        self.assertTrue(program.is_recordable())
        self.assertEqual(program.title, radiko_program_data["title"])
        self.assertEqual(program.performer, radiko_program_data["performer"])


if __name__ == "__main__":
    unittest.main()
