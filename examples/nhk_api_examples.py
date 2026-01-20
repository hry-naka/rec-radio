"""Usage examples for NHKApi module."""

from mypkg.nhk_api import NHKApi, NHKApiError, NHKApiHttpError, NHKApiJsonError


def example_1_basic_initialization():
    """Example 1: Initialize the API client."""
    # Default 10 second timeout
    api = NHKApi()

    # Custom timeout
    api = NHKApi(timeout=15)
    print(f"API initialized with {api.timeout}s timeout")


def example_2_get_new_arrivals():
    """Example 2: Get newly arrived programs."""
    api = NHKApi()

    try:
        # Get new arrivals
        data = api.get_new_arrivals()

        # Extract corner info
        corners = api.extract_corners(data)

        # Process corners
        for corner in corners[:5]:  # First 5
            print(f"{corner['title']} ({corner['radio_broadcast']})")
            print(f"  Broadcast: {corner['onair_date']}")
            print(f"  Series ID: {corner['series_site_id']}")

    except NHKApiHttpError as e:
        print(f"HTTP error: {e}")
    except NHKApiJsonError as e:
        print(f"JSON error: {e}")


def example_3_get_corners_by_date():
    """Example 3: Get programs for a specific date."""
    api = NHKApi()

    try:
        # Get programs for January 18, 2026
        data = api.get_corners_by_date("20260118")

        # Extract programs
        programs = api.extract_corners(data)

        print(f"Found {len(programs)} programs on {data['onair_date']}")

        # Filter by broadcast channel
        fm_programs = [p for p in programs if "FM" in p["radio_broadcast"]]
        print(f"FM programs: {len(fm_programs)}")

    except NHKApiError as e:
        print(f"API error: {e}")


def example_4_get_series_with_stream_url():
    """Example 4: Get series information with streaming URLs."""
    api = NHKApi()

    try:
        # Get series info (眠れない貴女へ)
        series_data = api.get_series(site_id="47Q5W9WQK9", corner_site_id="01")

        # Extract episodes
        episodes = api.extract_episodes(series_data)

        print(f"Series: {series_data['title']}")
        print(f"Schedule: {series_data['schedule']}")
        print(f"Episodes: {len(episodes)}")

        for episode in episodes:
            print(f"\n  Title: {episode['program_title']}")
            print(f"  Onair: {episode['onair_date']}")
            print(f"  Expires: {episode['closed_at']}")
            print(f"  Stream: {episode['stream_url']}")

    except NHKApiError as e:
        print(f"API error: {e}")


def example_5_get_recording_info():
    """Example 5: Get information needed for recording."""
    api = NHKApi()

    try:
        # Get series info
        series_data = api.get_series(site_id="47Q5W9WQK9", corner_site_id="01")

        # Extract recording info
        recording_info = api.extract_recording_info(series_data)

        for info in recording_info:
            print(f"Title: {info['title']}")
            print(f"Program: {info['program_title']}")
            print(f"Onair Date: {info['onair_date']}")
            print(f"Closed At: {info['closed_at']}")
            print(f"Stream URL: {info['stream_url']}")

            # Ready to pass to recorder
            # stream_url can be downloaded with ffmpeg or similar

    except NHKApiError as e:
        print(f"API error: {e}")


def example_6_error_handling():
    """Example 6: Comprehensive error handling."""
    api = NHKApi()

    try:
        # This will fail if API is unavailable
        data = api.get_new_arrivals()

    except NHKApiHttpError as e:
        print(f"Network/HTTP error (check connectivity): {e}")

    except NHKApiJsonError as e:
        print(f"Response parsing error (API may have changed): {e}")

    except NHKApiError as e:
        print(f"Other API error: {e}")


if __name__ == "__main__":
    print("NHKApi Usage Examples\n")

    print("=== Example 1: Initialization ===")
    example_1_basic_initialization()

    print("\n=== Example 2: Get New Arrivals ===")
    # example_2_get_new_arrivals()  # Requires network

    print("\n=== Example 3: Get Programs by Date ===")
    # example_3_get_corners_by_date()  # Requires network

    print("\n=== Example 4: Get Series with Stream URL ===")
    # example_4_get_series_with_stream_url()  # Requires network

    print("\n=== Example 5: Get Recording Info ===")
    # example_5_get_recording_info()  # Requires network

    print("\n=== Example 6: Error Handling ===")
    # example_6_error_handling()  # Requires network
