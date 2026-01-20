"""Unit tests for RadikoApi client.

This module provides comprehensive unit tests for the RadikoApi class,
including:
- Initialization tests
- API method tests with mocking
- Error handling tests
- XML parsing tests
"""

import unittest
from unittest.mock import MagicMock, patch
import xml.etree.ElementTree as ET

from mypkg.radiko_api import (
    RadikoApi,
    RadikoApiError,
    RadikoApiHttpError,
    RadikoApiXmlError,
)
from mypkg.program import Program


class TestRadikoApiInitialization(unittest.TestCase):
    """Tests for RadikoApi initialization."""

    def test_default_initialization(self):
        """Test default initialization with default timeout."""
        api = RadikoApi()
        self.assertEqual(api.timeout, 10)

    def test_custom_timeout_initialization(self):
        """Test initialization with custom timeout."""
        api = RadikoApi(timeout=20)
        self.assertEqual(api.timeout, 20)

    def test_invalid_timeout(self):
        """Test that non-positive timeout raises ValueError."""
        with self.assertRaises(ValueError):
            RadikoApi(timeout=0)

        with self.assertRaises(ValueError):
            RadikoApi(timeout=-5)

    def test_float_timeout(self):
        """Test that float timeout is accepted."""
        api = RadikoApi(timeout=5.5)
        self.assertEqual(api.timeout, 5.5)


class TestRadikoApiAuthorization(unittest.TestCase):
    """Tests for Radiko authorization methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.api = RadikoApi()

    @patch("requests.post")
    @patch("requests.get")
    def test_authorize_success(self, mock_get, mock_post):
        """Test successful authorization flow."""
        # Mock first request
        mock_response1 = MagicMock()
        mock_response1.headers = {"X-Radiko-AuthToken": "test_token_123"}
        mock_post.return_value = mock_response1

        # Mock second request
        mock_response2 = MagicMock()
        mock_response2.text = "JP13"
        mock_get.return_value = mock_response2

        result = self.api.authorize()

        self.assertIsNotNone(result)
        auth_token, area_id = result
        self.assertEqual(auth_token, "test_token_123")
        self.assertEqual(area_id, "JP13")

    @patch("requests.post")
    def test_authorize_no_token(self, mock_post):
        """Test authorization when auth token is not returned."""
        mock_response = MagicMock()
        mock_response.headers = {}
        mock_post.return_value = mock_response

        result = self.api.authorize()
        self.assertIsNone(result)

    @patch("requests.post")
    def test_authorize_http_error(self, mock_post):
        """Test authorization with HTTP error."""
        import requests

        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")

        with self.assertRaises(RadikoApiHttpError):
            self.api.authorize()


class TestRadikoApiStationMethods(unittest.TestCase):
    """Tests for station-related methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.api = RadikoApi()
        self.sample_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <stations>
            <station id="TBS">
                <id>TBS</id>
                <name>TBS ラジオ</name>
            </station>
            <station id="NACK5">
                <id>NACK5</id>
                <name>ニッポン放送</name>
            </station>
        </stations>
        """

    @patch("requests.get")
    def test_get_station_list_success(self, mock_get):
        """Test successful station list retrieval."""
        mock_response = MagicMock()
        mock_response.content = self.sample_xml.encode("utf-8")
        mock_get.return_value = mock_response

        result = self.api.get_station_list("JP13")

        self.assertIsNotNone(result)
        self.assertEqual(result.tag, "stations")

    @patch("requests.get")
    def test_get_station_list_http_error(self, mock_get):
        """Test station list retrieval with HTTP error."""
        import requests

        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")

        with self.assertRaises(RadikoApiHttpError):
            self.api.get_station_list("JP13")

    @patch("requests.get")
    def test_get_station_list_xml_error(self, mock_get):
        """Test station list retrieval with XML parse error."""
        mock_response = MagicMock()
        mock_response.content = b"Invalid XML"
        mock_get.return_value = mock_response

        with self.assertRaises(RadikoApiXmlError):
            self.api.get_station_list("JP13")

    @patch("requests.get")
    def test_get_channel_list(self, mock_get):
        """Test channel list retrieval."""
        mock_response = MagicMock()
        mock_response.content = self.sample_xml.encode("utf-8")
        mock_get.return_value = mock_response

        ids, names = self.api.get_channel_list("JP13")

        self.assertEqual(ids, ["TBS", "NACK5"])
        self.assertEqual(names, ["TBS ラジオ", "ニッポン放送"])

    @patch.object(RadikoApi, "get_station_list")
    def test_is_station_available_true(self, mock_get_station_list):
        """Test station availability check when available."""
        mock_root = ET.fromstring(self.sample_xml)
        mock_get_station_list.return_value = mock_root

        result = self.api.is_station_available("TBS", "JP13")
        self.assertTrue(result)

    @patch.object(RadikoApi, "get_station_list")
    def test_is_station_available_false(self, mock_get_station_list):
        """Test station availability check when not available."""
        mock_root = ET.fromstring(self.sample_xml)
        mock_get_station_list.return_value = mock_root

        result = self.api.is_station_available("NHK-FM", "JP13")
        self.assertFalse(result)

    @patch.object(RadikoApi, "get_station_list")
    def test_is_station_available_none(self, mock_get_station_list):
        """Test station availability check when station list is None."""
        mock_get_station_list.return_value = None

        result = self.api.is_station_available("TBS", "JP13")
        self.assertFalse(result)


class TestRadikoApiProgramMethods(unittest.TestCase):
    """Tests for program-related methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.api = RadikoApi()
        self.sample_program_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <radiko>
            <station id="TBS">
                <progs>
                    <prog ft="20260120000000" to="20260120093000" dur="93">
                        <title>テスト番組</title>
                        <pfm>テストDJ</pfm>
                        <desc>テスト説明</desc>
                        <info>テスト情報</info>
                        <img>http://example.com/img.jpg</img>
                        <url>http://example.com/prog</url>
                    </prog>
                </progs>
            </station>
        </radiko>
        """

    @patch("requests.get")
    def test_fetch_now_program_success(self, mock_get):
        """Test successful now program retrieval."""
        mock_response = MagicMock()
        mock_response.content = self.sample_program_xml.encode("utf-8")
        mock_get.return_value = mock_response

        result = self.api.fetch_now_program("TBS")

        self.assertIsNotNone(result)
        self.assertIsInstance(result, Program)
        self.assertEqual(result.title, "テスト番組")
        self.assertEqual(result.performer, "テストDJ")

    @patch("requests.get")
    def test_fetch_now_program_no_program(self, mock_get):
        """Test now program retrieval when no program found."""
        empty_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <radiko>
            <station id="TBS">
                <progs></progs>
            </station>
        </radiko>
        """
        mock_response = MagicMock()
        mock_response.content = empty_xml.encode("utf-8")
        mock_get.return_value = mock_response

        result = self.api.fetch_now_program("TBS")
        self.assertIsNone(result)

    @patch("requests.get")
    def test_fetch_today_program(self, mock_get):
        """Test today program retrieval."""
        mock_response = MagicMock()
        mock_response.content = self.sample_program_xml.encode("utf-8")
        mock_get.return_value = mock_response

        result = self.api.fetch_today_program("TBS", "20260120143000")

        self.assertIsNotNone(result)

    @patch("requests.get")
    def test_fetch_weekly_program(self, mock_get):
        """Test weekly program retrieval."""
        mock_response = MagicMock()
        mock_response.content = self.sample_program_xml.encode("utf-8")
        mock_get.return_value = mock_response

        result = self.api.fetch_weekly_program("TBS")

        self.assertIsNotNone(result)


class TestRadikoApiStreamMethods(unittest.TestCase):
    """Tests for stream-related methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.api = RadikoApi()

    @patch("requests.get")
    def test_get_stream_url_success(self, mock_get):
        """Test successful stream URL retrieval."""
        mock_response = MagicMock()
        mock_response.text = "https://example.com/stream.m3u8"
        mock_get.return_value = mock_response

        result = self.api.get_stream_url("TBS", "test_token")

        self.assertEqual(result, "https://example.com/stream.m3u8")

    @patch("requests.get")
    def test_get_stream_url_http_error(self, mock_get):
        """Test stream URL retrieval with HTTP error."""
        import requests

        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")

        with self.assertRaises(RadikoApiHttpError):
            self.api.get_stream_url("TBS", "test_token")


class TestRadikoApiSearchMethods(unittest.TestCase):
    """Tests for search-related methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.api = RadikoApi()

    @patch("requests.get")
    def test_search_programs_success(self, mock_get):
        """Test successful program search."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "programs": [{"title": "ニュース", "station": "TBS"}]
        }
        mock_get.return_value = mock_response

        result = self.api.search_programs(keyword="ニュース", time_filter="today")

        self.assertIn("programs", result)
        self.assertEqual(len(result["programs"]), 1)

    @patch("requests.get")
    def test_search_programs_json_error(self, mock_get):
        """Test program search with JSON parse error."""
        mock_response = MagicMock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response

        with self.assertRaises(RadikoApiXmlError):
            self.api.search_programs()


class TestRadikoApiUtilities(unittest.TestCase):
    """Tests for utility methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.api = RadikoApi()

    def test_dump(self):
        """Test dump method for debugging."""
        # This method just prints, so we just verify it doesn't raise
        try:
            self.api.dump()
        except Exception as e:
            self.fail(f"dump() raised {e}")


class TestRadikoApiExceptionHierarchy(unittest.TestCase):
    """Tests for exception class hierarchy."""

    def test_exception_inheritance(self):
        """Test exception class inheritance."""
        self.assertTrue(issubclass(RadikoApiHttpError, RadikoApiError))
        self.assertTrue(issubclass(RadikoApiXmlError, RadikoApiError))
        self.assertTrue(issubclass(RadikoApiError, Exception))

    def test_exception_creation(self):
        """Test exception creation and messages."""
        error = RadikoApiHttpError("Test error message")
        self.assertEqual(str(error), "Test error message")
        self.assertIsInstance(error, RadikoApiError)


if __name__ == "__main__":
    unittest.main()
