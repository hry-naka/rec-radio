"""NHK API usage examples.

This module demonstrates how to use the NHKApi client for various tasks:
- Fetching new arrivals
- Getting programs by date
- Retrieving series information with episodes
- Extracting recording information
- Error handling
"""

from mypkg.nhk_api import NHKApi, NHKApiError, NHKApiHttpError, NHKApiJsonError


def example_1_basic_initialization():
    """Example 1: Initialize the API client."""
    print("=" * 60)
    print("Example 1: Basic Initialization")
    print("=" * 60)

    # Default 10 second timeout
    api = NHKApi()
    api.dump()

    # Custom timeout
    api = NHKApi(timeout=15)
    api.dump()


def example_2_get_new_arrivals():
    """Example 2: Get newly arrived programs."""
    print("\n" + "=" * 60)
    print("Example 2: Get New Arrivals")
    print("=" * 60)

    api = NHKApi()

    try:
        # Get new arrivals
        print("\nFetching new arrivals...")
        data = api.get_new_arrivals()

        # Extract corner info
        corners = api.extract_corners(data)

        print(f"✓ Found {len(corners)} new programs")

        # Process first 5
        for corner in corners[:5]:
            print(f"\n  - {corner['title']}")
            print(f"    Broadcast: {corner['radio_broadcast']}")
            print(f"    Air Date: {corner['onair_date']}")
            print(f"    Series ID: {corner['series_site_id']}")

    except NHKApiHttpError as e:
        print(f"✗ HTTP error: {e}")
    except NHKApiJsonError as e:
        print(f"✗ JSON error: {e}")


def example_3_get_corners_by_date():
    """Example 3: Get programs for a specific date."""
    print("\n" + "=" * 60)
    print("Example 3: Get Programs by Date")
    print("=" * 60)

    api = NHKApi()

    try:
        # Get programs for January 18, 2026
        onair_date = "20260118"
        print(f"\nFetching programs for {onair_date}...")
        data = api.get_corners_by_date(onair_date)

        # Extract programs
        programs = api.extract_corners(data)

        print(f"✓ Found {len(programs)} programs on {data['onair_date']}")

        # Filter by broadcast channel
        fm_programs = [p for p in programs if "FM" in p["radio_broadcast"]]
        r1_programs = [p for p in programs if "R1" in p["radio_broadcast"]]
        r2_programs = [p for p in programs if "R2" in p["radio_broadcast"]]

        print(f"  FM programs: {len(fm_programs)}")
        print(f"  R1 programs: {len(r1_programs)}")
        print(f"  R2 programs: {len(r2_programs)}")

    except NHKApiError as e:
        print(f"✗ API error: {e}")


def example_4_get_series_with_episodes():
    """Example 4: Get series information with episodes."""
    print("\n" + "=" * 60)
    print("Example 4: Get Series with Episodes")
    print("=" * 60)

    api = NHKApi()

    try:
        # Get series info (眠れない貴女へ)
        print("\nFetching series information...")
        series_data = api.get_series(site_id="47Q5W9WQK9", corner_site_id="01")

        print(f"✓ Series: {series_data['title']}")
        print(f"  Broadcast: {series_data['radio_broadcast']}")
        print(f"  Schedule: {series_data['schedule']}")

        # Extract episodes
        episodes = api.extract_episodes(series_data)
        print(f"  Episodes: {len(episodes)}")

        for i, episode in enumerate(episodes[:3], 1):
            print(f"\n  Episode {i}:")
            print(f"    Title: {episode['program_title']}")
            print(f"    Air Date: {episode['onair_date']}")
            print(f"    Closed At: {episode['closed_at']}")
            if episode.get("stream_url"):
                print(f"    Stream: {episode['stream_url'][:50]}...")

    except NHKApiError as e:
        print(f"✗ API error: {e}")


def example_5_extract_recording_info():
    """Example 5: Extract recording information for pipeline."""
    print("\n" + "=" * 60)
    print("Example 5: Extract Recording Information")
    print("=" * 60)

    api = NHKApi()

    try:
        # Get series info
        print("\nFetching series and extracting recording info...")
        series_data = api.get_series(site_id="47Q5W9WQK9", corner_site_id="01")

        # Extract recording info (optimized for recorder_nhk.py)
        recording_info = api.extract_recording_info(series_data)

        print(f"✓ Recording info for {len(recording_info)} episodes")

        for i, info in enumerate(recording_info[:2], 1):
            print(f"\n  Record {i}:")
            print(f"    Series: {info['title']}")
            print(f"    Program: {info['program_title']}")
            print(f"    Air Date: {info['onair_date']}")
            print(f"    Closed At: {info['closed_at']}")
            print(
                f"    Stream URL: {info['stream_url'][:50]}..."
                if info.get("stream_url")
                else "    Stream URL: N/A"
            )

    except NHKApiError as e:
        print(f"✗ API error: {e}")


def example_6_error_handling():
    """Example 6: Comprehensive error handling."""
    print("\n" + "=" * 60)
    print("Example 6: Error Handling")
    print("=" * 60)

    # Test 1: Invalid timeout
    print("\nTest 1: Invalid timeout")
    try:
        api = NHKApi(timeout=-1)
    except ValueError as e:
        print(f"✓ Caught ValueError: {e}")

    # Test 2: Invalid data extraction
    print("\nTest 2: Invalid data extraction")
    api = NHKApi()
    try:
        invalid_data = {"invalid": "structure"}
        corners = api.extract_corners(invalid_data)
        print(f"✓ Safely handled: extracted {len(corners)} items")
    except NHKApiJsonError as e:
        print(f"✓ Caught NHKApiJsonError: {e}")


def example_7_complete_workflow():
    """Example 7: Complete workflow from discovery to recording info."""
    print("\n" + "=" * 60)
    print("Example 7: Complete Workflow")
    print("=" * 60)

    api = NHKApi()

    try:
        print("\n1. Getting new arrivals...")
        new_arrivals = api.get_new_arrivals()
        corners = api.extract_corners(new_arrivals)
        print(f"   ✓ Found {len(corners)} programs")

        print("\n2. Finding target series...")
        # Find first FM program with series_site_id
        target = next((c for c in corners if c.get("series_site_id")), None)

        if target:
            print(
                f"   ✓ Target: {target['title']} (Series ID: {target['series_site_id']})"
            )

            print("\n3. Fetching series details...")
            series_data = api.get_series(
                target["series_site_id"], target.get("corner_site_id", "01")
            )
            print(f"   ✓ Series: {series_data['title']}")

            print("\n4. Extracting recording information...")
            recording_info = api.extract_recording_info(series_data)
            print(f"   ✓ Ready to record {len(recording_info)} episodes")

            if recording_info:
                first = recording_info[0]
                print(f"\n   Sample recording:")
                print(f"   - {first['title']} / {first['program_title']}")
                print(
                    f"   - Stream: {first['stream_url'][:50]}..."
                    if first.get("stream_url")
                    else "   - Stream: N/A"
                )
                print(f"   - Valid until: {first['closed_at']}")
        else:
            print("   ⚠ No programs found")

    except NHKApiHttpError as e:
        print(f"✗ Network error (check connectivity): {e}")

    except NHKApiJsonError as e:
        print(f"✗ Response parsing error (API may have changed): {e}")

    except NHKApiError as e:
        print(f"✗ Other API error: {e}")


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("NHK Radio Ondemand API - Usage Examples")
    print("=" * 70)

    # Basic examples (always work)
    example_1_basic_initialization()
    example_6_error_handling()

    # Network-dependent examples
    print("\n" + "=" * 70)
    print("Network-Dependent Examples")
    print("=" * 70)
    print("Note: The following examples require internet connectivity.\n")

    try:
        example_2_get_new_arrivals()
        example_3_get_corners_by_date()
        example_4_get_series_with_episodes()
        example_5_extract_recording_info()
        example_7_complete_workflow()
    except Exception as e:
        print(f"\n⚠ Skipping network examples due to: {type(e).__name__}: {e}")

    print("\n" + "=" * 70)
    print("All examples completed!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
