#!/usr/bin/env python3
"""Test script for NHKApi module."""

import json
import sys
from pathlib import Path

# Add parent directory to path to import mypkg
sys.path.insert(0, str(Path(__file__).parent.parent))

from mypkg.nhk_api import NHKApi, NHKApiError


def test_nhk_api():
    """Test NHKApi with mock data."""
    print("Testing NHKApi module...")

    # Initialize API client
    api = NHKApi(timeout=15)
    print(f"✓ NHKApi initialized with timeout={api.timeout}")

    # Load sample data from attachments
    home_dir = Path.home()

    # Test 1: Load and parse new_arrivals
    print("\n--- Test 1: Parse new_arrivals ---")
    with open(home_dir / "new_arrivals.log") as f:
        new_arrivals = json.load(f)
    corners = api.extract_corners(new_arrivals)
    print(f"✓ Extracted {len(corners)} corners from new_arrivals")
    if corners:
        print(f"  First corner: {corners[0]['title']}")

    # Test 2: Parse corners by date
    print("\n--- Test 2: Parse corners by date ---")
    with open(home_dir / "corners-20260118.log") as f:
        corners_data = json.load(f)
    corners_by_date = api.extract_corners(corners_data)
    print(
        f"✓ Extracted {len(corners_by_date)} corners for date {corners_data['onair_date']}"
    )
    if corners_by_date:
        print(f"  First program: {corners_by_date[0]['title']}")

    # Test 3: Parse series with episodes
    print("\n--- Test 3: Parse series with episodes ---")
    with open(home_dir / "corner-47Q5W9WQK9-01.log") as f:
        series_data = json.load(f)

    # Test extract_episodes
    episodes = api.extract_episodes(series_data)
    print(f"✓ Extracted {len(episodes)} episodes from series")
    if episodes:
        print(f"  First episode: {episodes[0]['program_title']}")
        print(f"  Stream URL: {episodes[0]['stream_url'][:50]}...")
        print(f"  Closed at: {episodes[0]['closed_at']}")

    # Test extract_recording_info
    recording_info = api.extract_recording_info(series_data)
    print(f"\n✓ Recording info extracted:")
    for info in recording_info:
        print(f"  Title: {info['title']}")
        print(f"  Program: {info['program_title']}")
        print(f"  Onair date: {info['onair_date']}")
        print(f"  Closed at: {info['closed_at']}")
        print(f"  Stream URL: {info['stream_url'][:50]}...")

    # Test 4: Verify exception classes
    print("\n--- Test 4: Exception classes ---")
    try:
        raise NHKApiError("Test error")
    except NHKApiError as e:
        print(f"✓ NHKApiError caught: {e}")

    print("\n✓ All tests passed!")


if __name__ == "__main__":
    test_nhk_api()
