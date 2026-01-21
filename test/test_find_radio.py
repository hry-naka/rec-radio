"""Unit tests for find_radio.py unified search CLI.

Tests cover:
- Argument parsing for both Radiko and NHK
- Program fetching from both APIs
- Keyword filtering with regex patterns
- Area ID resolution from environment
"""

from unittest.mock import MagicMock, patch
from typing import List
import unittest  # ← 追加
import pytest

from mypkg.radiko_api import RadikoApi
from mypkg.nhk_api import NHKApi
from mypkg.program import Program
from find_radio import (
    filter_programs_by_keyword,
    get_area_id,
)


class TestGetAreaId(unittest.TestCase):
    """Test area ID resolution."""

    def test_explicit_area_takes_precedence(self):
        """Test that explicit area argument overrides env variable."""
        result = get_area_id("radiko", "JP14")
        self.assertEqual(result, "JP14")

    @patch.dict("os.environ", {"RADIKO_AREA_ID": "JP14"})
    def test_radiko_area_from_env(self):
        """Test Radiko area from environment variable."""
        result = get_area_id("radiko", None)
        self.assertEqual(result, "JP14")

    @patch.dict("os.environ", {"NHK_AREA_ID": "JP15"})
    def test_nhk_area_from_env(self):
        """Test NHK area from environment variable."""
        result = get_area_id("nhk", None)
        self.assertEqual(result, "JP15")

    @patch.dict("os.environ", {}, clear=True)
    def test_default_area(self):
        """Test default area when env variables not set."""
        result = get_area_id("radiko", None)
        self.assertEqual(result, "JP13")


class TestFilterProgramsByKeyword(unittest.TestCase):
    """Test keyword filtering functionality."""

    def setUp(self):
        """Set up test programs."""
        self.programs = [
            Program(
                title="Jazz Night",
                station="TBS",
                start_time="20260120130000",
                end_time="20260120140000",
                source="radiko",
                description="Jazz music program",
            ),
            Program(
                title="News Hour",
                station="NHK",
                start_time="20260120140000",
                end_time="20260120150000",
                source="nhk",
                description="Latest news",
            ),
            Program(
                title="Classical Music Hour",  # ← "Hour" を追加
                station="FM",
                start_time="20260120150000",
                end_time="20260120160000",
                source="radiko",
                info="Symphony orchestra",
            ),
        ]

    def test_filter_by_title(self):
        """Test filtering by program title."""
        result = filter_programs_by_keyword(self.programs, "jazz")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].title, "Jazz Night")

    def test_filter_by_description(self):
        """Test filtering by program description."""
        result = filter_programs_by_keyword(self.programs, "news")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].title, "News Hour")

    def test_filter_by_info(self):
        """Test filtering by program info field.

        Note: NHK と Radiko で検索対象を統一するため、現在は title のみを検索対象としています。
        info フィールドの検索は非サポートです。
        """
        # info フィールドで検索しても、title に含まれていない場合は見つかりません
        result = filter_programs_by_keyword(self.programs, "symphony")
        # info にのみ含まれるキーワードは見つからないことを期待
        self.assertEqual(len(result), 0)

    def test_filter_by_title_only(self):
        """Test that filtering searches title field only."""
        # title に含まれるキーワードは見つかる
        result = filter_programs_by_keyword(self.programs, "Classical")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].title, "Classical Music Hour")

    def test_case_insensitive_filter(self):
        """Test that filtering is case-insensitive."""
        result = filter_programs_by_keyword(self.programs, "JAZZ")
        self.assertEqual(len(result), 1)

    def test_regex_pattern(self):
        """Test filtering with regex pattern."""
        result = filter_programs_by_keyword(self.programs, "^News")
        self.assertEqual(len(result), 1)

    def test_no_keyword_returns_all(self):
        """Test that no keyword returns all programs."""
        result = filter_programs_by_keyword(self.programs, "")
        self.assertEqual(len(result), 3)

    def test_invalid_regex_raises_system_exit(self):
        """Test that invalid regex raises SystemExit."""
        import sys

        with self.assertRaises(SystemExit):
            filter_programs_by_keyword(self.programs, "[invalid(regex")


class TestRadikoSearch(unittest.TestCase):  # ← unittest.TestCase を継承
    """Test cases for Radiko API search functionality."""

    def test_radiko_api_get_programs(self):
        """Test Radiko API returns programs."""
        api = RadikoApi()
        programs = api.get_programs("JP13", "TBS")

        self.assertIsInstance(programs, list)
        self.assertGreater(len(programs), 0)
        self.assertTrue(all(isinstance(p, Program) for p in programs))

    def test_radiko_api_get_programs_with_invalid_station(self):
        """Test Radiko API with invalid station raises exception."""
        api = RadikoApi()
        from mypkg.radiko_api import RadikoApiError

        # Invalid station should raise RadikoApiError
        with self.assertRaises(RadikoApiError):
            api.get_programs("JP13", "INVALID")


class TestNHKSearch(unittest.TestCase):  # ← unittest.TestCase を継承
    """Test cases for NHK API search functionality."""

    def test_nhk_api_get_programs(self):
        """Test NHK API returns programs."""
        api = NHKApi()
        programs = api.get_programs()

        self.assertIsInstance(programs, list)
        self.assertGreater(len(programs), 0)
        self.assertTrue(all(isinstance(p, Program) for p in programs))


class TestProgramFormatterIntegration(unittest.TestCase):
    """Integration tests with ProgramFormatter."""

    def test_format_list_radiko_program(self):
        """Test format_list output for Radiko program."""
        from mypkg.program_formatter import ProgramFormatter

        program = Program(
            title="Test Radio",
            station="TBS",
            start_time="20260120130000",
            end_time="20260120140000",
            source="radiko",
        )

        output = ProgramFormatter.format_list([program])

        self.assertIn("[1]", output)
        self.assertIn("Test Radio", output)
        self.assertIn("radiko", output)
        self.assertIn("tfrec_radiko.py", output)

    def test_format_list_nhk_program(self):
        """Test format_list output for NHK program."""
        from mypkg.program_formatter import ProgramFormatter

        program = Program(
            title="NHK Program",
            station="NHK",
            start_time="20260120130000",
            end_time="20260120140000",
            source="nhk",
            series_site_id="series_123",
        )

        output = ProgramFormatter.format_list([program])

        self.assertIn("[1]", output)
        self.assertIn("NHK Program", output)
        self.assertIn("NHK (らじる★らじる)", output)
        self.assertIn("tfrec_nhk.py", output)


if __name__ == "__main__":
    unittest.main()
