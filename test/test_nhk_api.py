#!/usr/bin/env python3
"""Unit tests for NHKApi client.

This module provides comprehensive unit tests for the NHKApi class,
including:
- Initialization tests
- API method tests with mocking
- Response normalization tests
- Error handling tests
- Extraction method tests
"""

import unittest
from unittest.mock import MagicMock, Mock, patch
import requests

from mypkg.nhk_api import (
    NHKApi,
    NHKApiError,
    NHKApiHttpError,
    NHKApiJsonError,
)


class TestNHKApiInitialization(unittest.TestCase):
    """Tests for NHKApi initialization."""

    def test_default_initialization(self):
        """Test default initialization with default timeout."""
        api = NHKApi()
        self.assertEqual(api.timeout, 10)

    def test_custom_timeout_initialization(self):
        """Test initialization with custom timeout."""
        api = NHKApi(timeout=20)
        self.assertEqual(api.timeout, 20)

    def test_invalid_timeout_zero(self):
        """Test that zero timeout raises ValueError."""
        with self.assertRaises(ValueError):
            NHKApi(timeout=0)

    def test_invalid_timeout_negative(self):
        """Test that negative timeout raises ValueError."""
        with self.assertRaises(ValueError):
            NHKApi(timeout=-5)

    def test_float_timeout(self):
        """Test that float timeout is accepted."""
        api = NHKApi(timeout=5.5)
        self.assertEqual(api.timeout, 5.5)


class TestNHKApiNewArrivals(unittest.TestCase):
    """Tests for get_new_arrivals method."""

    def setUp(self):
        """Set up test fixtures."""
        self.api = NHKApi()
        self.sample_response = {
            "corners": [
                {
                    "id": 1341,
                    "title": "邦楽のひととき",
                    "radio_broadcast": "FM",
                    "series_site_id": "WW2Z47QY27",
                    "corner_site_id": "01",
                    "onair_date": "2026年1月19日(月)放送",
                    "started_at": "2026-01-19T11:00:03+09:00",
                    "thumbnail_url": "https://example.com/img.jpg",
                }
            ]
        }

    @patch("requests.get")
    def test_get_new_arrivals_success(self, mock_get):
        """Test successful new arrivals retrieval."""
        mock_response = MagicMock()
        mock_response.json.return_value = self.sample_response
        mock_get.return_value = mock_response

        result = self.api.get_new_arrivals()

        self.assertIn("corners", result)
        self.assertEqual(len(result["corners"]), 1)
        self.assertEqual(result["corners"][0]["title"], "邦楽のひととき")

    @patch("requests.get")
    def test_get_new_arrivals_http_error(self, mock_get):
        """Test new arrivals with HTTP error."""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")

        with self.assertRaises(NHKApiHttpError):
            self.api.get_new_arrivals()

    @patch("requests.get")
    def test_get_new_arrivals_json_error(self, mock_get):
        """Test new arrivals with JSON parse error."""
        mock_response = MagicMock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response

        with self.assertRaises(NHKApiJsonError):
            self.api.get_new_arrivals()


class TestNHKApiCornersByDate(unittest.TestCase):
    """Tests for get_corners_by_date method."""

    def setUp(self):
        """Set up test fixtures."""
        self.api = NHKApi()
        self.sample_response = {
            "onair_date": "20260118",
            "corners": [
                {
                    "id": 18,
                    "title": "マイあさ！",
                    "radio_broadcast": "R1",
                    "series_site_id": "J8792PY43V",
                    "corner_site_id": "07",
                    "onair_date": "2026年1月18日(日)放送",
                    "started_at": "2026-01-18T05:00:03+09:00",
                }
            ],
        }

    @patch("requests.get")
    def test_get_corners_by_date_success(self, mock_get):
        """Test successful corners by date retrieval."""
        mock_response = MagicMock()
        mock_response.json.return_value = self.sample_response
        mock_get.return_value = mock_response

        result = self.api.get_corners_by_date("20260118")

        self.assertEqual(result["onair_date"], "20260118")
        self.assertEqual(len(result["corners"]), 1)
        self.assertEqual(result["corners"][0]["title"], "マイあさ！")

    @patch("requests.get")
    def test_get_corners_by_date_formats_url(self, mock_get):
        """Test that URL is formatted correctly."""
        mock_response = MagicMock()
        mock_response.json.return_value = self.sample_response
        mock_get.return_value = mock_response

        self.api.get_corners_by_date("20260118")

        # Verify the URL was called correctly
        mock_get.assert_called_once()
        called_url = mock_get.call_args[0][0]
        self.assertIn("20260118", called_url)


class TestNHKApiSeries(unittest.TestCase):
    """Tests for get_series method."""

    def setUp(self):
        """Set up test fixtures."""
        self.api = NHKApi()
        self.sample_response = {
            "id": 76,
            "title": "眠れない貴女へ",
            "radio_broadcast": "FM",
            "schedule": "毎週日曜 午後11時30分",
            "series_description": "女性向けの心のデトックス番組",
            "episodes": [
                {
                    "id": 4296074,
                    "program_title": "眠れない貴女(あなた)へ 【ゲスト】山崎佐知子",
                    "onair_date": "1月18日(日)午後11:30放送",
                    "closed_at": "2026年1月26日(月)午前1:00配信終了",
                    "stream_url": "https://vod-stream.nhk.jp/radioondemand/r/47Q5W9WQK9/s/stream.m3u8",
                    "program_sub_title": "【ＤＪ】和田明日香，【ゲスト】山崎佐知子",
                }
            ],
        }

    @patch("requests.get")
    def test_get_series_success(self, mock_get):
        """Test successful series retrieval."""
        mock_response = MagicMock()
        mock_response.json.return_value = self.sample_response
        mock_get.return_value = mock_response

        result = self.api.get_series("47Q5W9WQK9", "01")

        self.assertEqual(result["title"], "眠れない貴女へ")
        self.assertEqual(len(result["episodes"]), 1)
        self.assertEqual(
            result["episodes"][0]["program_title"],
            "眠れない貴女(あなた)へ 【ゲスト】山崎佐知子",
        )

    @patch("requests.get")
    def test_get_series_default_corner_id(self, mock_get):
        """Test series with default corner_site_id."""
        mock_response = MagicMock()
        mock_response.json.return_value = self.sample_response
        mock_get.return_value = mock_response

        # Call without corner_site_id
        result = self.api.get_series("47Q5W9WQK9")

        self.assertEqual(result["title"], "眠れない貴女へ")

        # Verify the URL was called with default "01"
        mock_get.assert_called_once()
        called_url = mock_get.call_args[0][0]
        self.assertIn("47Q5W9WQK9-01", called_url)


class TestNHKApiExtraction(unittest.TestCase):
    """Tests for data extraction methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.api = NHKApi()

    def test_extract_corners_success(self):
        """Test successful corners extraction."""
        data = {
            "onair_date": "20260118",
            "corners": [
                {"id": 1, "title": "Program 1"},
                {"id": 2, "title": "Program 2"},
            ],
        }

        result = self.api.extract_corners(data)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["title"], "Program 1")

    def test_extract_corners_empty(self):
        """Test extraction from empty response."""
        data = {"corners": []}

        result = self.api.extract_corners(data)

        self.assertEqual(result, [])

    def test_extract_episodes_success(self):
        """Test successful episodes extraction."""
        series_data = {
            "title": "Series",
            "episodes": [
                {"id": 1, "program_title": "Ep 1"},
                {"id": 2, "program_title": "Ep 2"},
            ],
        }

        result = self.api.extract_episodes(series_data)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[1]["program_title"], "Ep 2")

    def test_extract_recording_info_success(self):
        """Test successful recording info extraction."""
        series_data = {
            "title": "Series Title",
            "episodes": [
                {
                    "program_title": "Program 1",
                    "onair_date": "2026-01-18",
                    "closed_at": "2026-01-26",
                    "stream_url": "https://example.com/stream.m3u8",
                }
            ],
        }

        result = self.api.extract_recording_info(series_data)

        self.assertEqual(len(result), 1)
        info = result[0]
        self.assertEqual(info["title"], "Series Title")
        self.assertEqual(info["program_title"], "Program 1")
        self.assertEqual(info["stream_url"], "https://example.com/stream.m3u8")

    def test_extract_recording_info_multiple_episodes(self):
        """Test recording info with multiple episodes."""
        series_data = {
            "title": "Series",
            "episodes": [
                {
                    "program_title": "Ep 1",
                    "onair_date": "2026-01-18",
                    "closed_at": "2026-01-26",
                    "stream_url": "url1",
                },
                {
                    "program_title": "Ep 2",
                    "onair_date": "2026-01-25",
                    "closed_at": "2026-02-02",
                    "stream_url": "url2",
                },
            ],
        }

        result = self.api.extract_recording_info(series_data)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["program_title"], "Ep 1")
        self.assertEqual(result[1]["program_title"], "Ep 2")

    def test_extract_recording_info_with_full_episode(self):
        """Test extracting recording info from complete episode data."""
        episode = {
            "id": 4296074,
            "program_title": "眠れない貴女(あなた)へ 【ゲスト】山崎佐知子",
            "onair_date": "1月18日(日)午後11:30放送",
            "closed_at": "2026年1月26日(月)午前1:00配信終了",
            "stream_url": "https://vod-stream.nhk.jp/radioondemand/r/47Q5W9WQK9/s/stream/index.m3u8",
            "program_sub_title": "【ＤＪ】和田明日香，【ゲスト】山崎佐知子",
        }

        result = self.api.extract_recording_info(
            title="眠れない貴女へ", series_site_id="47Q5W9WQK9", episode=episode
        )

        self.assertEqual(result["title"], "眠れない貴女へ")
        self.assertEqual(
            result["program_title"], "眠れない貴女(あなた)へ 【ゲスト】山崎佐知子"
        )
        self.assertEqual(result["series_site_id"], "47Q5W9WQK9")
        self.assertEqual(
            result["stream_url"],
            "https://vod-stream.nhk.jp/radioondemand/r/47Q5W9WQK9/s/stream/index.m3u8",
        )
        self.assertEqual(result["closed_at"], "2026年1月26日(月)午前1:00配信終了")


class TestNHKApiExceptionHierarchy(unittest.TestCase):
    """Tests for exception class hierarchy."""

    def test_exception_inheritance(self):
        """Test exception class inheritance."""
        self.assertTrue(issubclass(NHKApiHttpError, NHKApiError))
        self.assertTrue(issubclass(NHKApiJsonError, NHKApiError))
        self.assertTrue(issubclass(NHKApiError, Exception))

    def test_exception_creation(self):
        """Test exception creation and messages."""
        error = NHKApiHttpError("Test error message")
        self.assertEqual(str(error), "Test error message")
        self.assertIsInstance(error, NHKApiError)

    @patch("requests.get")
    def test_exception_hierarchy_http_error(self, mock_get):
        """Test that HTTP errors are raised as NHKApiHttpError."""
        mock_get.side_effect = requests.exceptions.RequestException("Connection failed")

        with self.assertRaises(NHKApiHttpError):
            NHKApi().get_new_arrivals()

    @patch("requests.get")
    def test_exception_hierarchy_json_error(self, mock_get):
        """Test that JSON parsing errors are raised as NHKApiJsonError."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "Invalid JSON"
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response

        with self.assertRaises(NHKApiJsonError):
            NHKApi().get_new_arrivals()


if __name__ == "__main__":
    unittest.main()
