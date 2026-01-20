"""Radiko API usage examples.

This module demonstrates how to use the RadikoApi client for various tasks:
- Authentication
- Station and channel information
- Program information retrieval
- Stream URL acquisition
- Program search
"""

from mypkg.radiko_api import RadikoApi, RadikoApiError, RadikoApiHttpError, RadikoApiXmlError


def example_basic_initialization():
    """Example: Initialize RadikoApi with default and custom timeout."""
    print("=" * 60)
    print("Example 1: Basic Initialization")
    print("=" * 60)
    
    # Default initialization
    api_default = RadikoApi()
    print(f"Default API: {api_default}")
    
    # Custom timeout
    api_custom = RadikoApi(timeout=20)
    print(f"Custom timeout API: {api_custom}")


def example_authorization():
    """Example: Perform Radiko authentication."""
    print("\n" + "=" * 60)
    print("Example 2: Authorization")
    print("=" * 60)
    
    api = RadikoApi()
    
    try:
        result = api.authorize()
        if result:
            auth_token, area_id = result
            print(f"✓ Authorization successful")
            print(f"  Auth Token: {auth_token[:10]}... (truncated)")
            print(f"  Area ID: {area_id}")
            return auth_token, area_id
        else:
            print("✗ Authorization failed: No token returned")
            return None, None
    except RadikoApiHttpError as e:
        print(f"✗ HTTP Error: {e}")
        return None, None


def example_station_information():
    """Example: Get station and channel information."""
    print("\n" + "=" * 60)
    print("Example 3: Station Information")
    print("=" * 60)
    
    api = RadikoApi()
    
    try:
        # Get channel list
        print("\nRetrieving channel list for area JP13 (Kanto)...")
        ids, names = api.get_channel_list("JP13")
        
        print(f"✓ Found {len(ids)} channels:")
        for id, name in zip(ids[:5], names[:5]):  # Show first 5
            print(f"  {id}: {name}")
        if len(ids) > 5:
            print(f"  ... and {len(ids) - 5} more")
        
        # Check specific station availability
        print("\nChecking station availability...")
        for station in ["TBS", "NACK5", "NHK-FM"]:
            available = api.is_station_available(station, "JP13")
            status = "✓ Available" if available else "✗ Not available"
            print(f"  {station}: {status}")
    
    except RadikoApiError as e:
        print(f"✗ Error: {e}")


def example_now_program():
    """Example: Fetch currently airing program."""
    print("\n" + "=" * 60)
    print("Example 4: Now Playing Program")
    print("=" * 60)
    
    api = RadikoApi()
    
    try:
        print("\nFetching now-playing program for TBS...")
        program = api.fetch_now_program("TBS")
        
        if program:
            print(f"✓ Program found:")
            print(f"  Title: {program.title}")
            print(f"  Station: {program.station}")
            print(f"  Time: {program.start_time} - {program.end_time}")
            print(f"  Duration: {program.duration} minutes")
            print(f"  Performer: {program.performer}")
            print(f"  Description: {program.description}")
        else:
            print("✗ No program found")
    
    except RadikoApiError as e:
        print(f"✗ Error: {e}")


def example_weekly_program():
    """Example: Fetch weekly program schedule."""
    print("\n" + "=" * 60)
    print("Example 5: Weekly Program Schedule")
    print("=" * 60)
    
    api = RadikoApi()
    
    try:
        print("\nFetching weekly program schedule for TBS...")
        program = api.fetch_weekly_program("TBS")
        
        if program:
            print(f"✓ Program found:")
            print(f"  Title: {program.title}")
            print(f"  Start Time: {program.start_time}")
            print(f"  End Time: {program.end_time}")
        else:
            print("✗ No program found")
    
    except RadikoApiError as e:
        print(f"✗ Error: {e}")


def example_stream_url(auth_token: str = None):
    """Example: Get stream URL.
    
    Args:
        auth_token: Authentication token from authorization
    """
    print("\n" + "=" * 60)
    print("Example 6: Get Stream URL")
    print("=" * 60)
    
    api = RadikoApi()
    
    if auth_token is None:
        print("Getting authorization token...")
        result = api.authorize()
        if not result:
            print("✗ Authorization failed")
            return
        auth_token, _ = result
    
    try:
        print(f"\nFetching stream URL for TBS...")
        stream_url = api.get_stream_url("TBS", auth_token)
        
        if stream_url:
            print(f"✓ Stream URL obtained:")
            print(f"  {stream_url}")
        else:
            print("✗ Failed to get stream URL")
    
    except RadikoApiError as e:
        print(f"✗ Error: {e}")


def example_search_programs():
    """Example: Search programs."""
    print("\n" + "=" * 60)
    print("Example 7: Search Programs")
    print("=" * 60)
    
    api = RadikoApi()
    
    try:
        print("\nSearching for 'ニュース' (news) programs...")
        results = api.search_programs(keyword="ニュース", time_filter="past")
        
        if results and "programs" in results:
            programs = results["programs"]
            print(f"✓ Found {len(programs)} programs")
            for prog in programs[:3]:  # Show first 3
                print(f"  - {prog.get('title', 'N/A')}")
        else:
            print("✗ No programs found")
    
    except RadikoApiError as e:
        print(f"✗ Error: {e}")


def example_error_handling():
    """Example: Proper error handling."""
    print("\n" + "=" * 60)
    print("Example 8: Error Handling")
    print("=" * 60)
    
    api = RadikoApi(timeout=1)  # Very short timeout to trigger error
    
    print("\nDemonstrating error handling with short timeout...")
    
    try:
        api.get_station_list("JP13")
    except RadikoApiHttpError as e:
        print(f"✓ Caught RadikoApiHttpError: {e}")
    except RadikoApiXmlError as e:
        print(f"✓ Caught RadikoApiXmlError: {e}")
    except RadikoApiError as e:
        print(f"✓ Caught RadikoApiError: {e}")
    
    print("\nRecovering with normal timeout...")
    api_normal = RadikoApi()
    try:
        station_list = api_normal.get_station_list("JP13")
        if station_list is not None:
            print("✓ Successfully recovered with normal timeout")
    except RadikoApiError as e:
        print(f"✗ Still failed: {e}")


def example_complete_workflow():
    """Example: Complete workflow combining multiple operations."""
    print("\n" + "=" * 60)
    print("Example 9: Complete Workflow")
    print("=" * 60)
    
    api = RadikoApi()
    
    try:
        print("\n1. Authorizing...")
        auth_result = api.authorize()
        if not auth_result:
            print("✗ Authorization failed")
            return
        
        auth_token, area_id = auth_result
        print(f"✓ Authorized for area: {area_id}")
        
        print("\n2. Getting available stations...")
        ids, names = api.get_channel_list(area_id)
        target_station = ids[0] if ids else "TBS"
        print(f"✓ Will use station: {target_station}")
        
        print("\n3. Fetching current program...")
        program = api.fetch_now_program(target_station)
        if program:
            print(f"✓ Current program: {program.title}")
        else:
            print("⚠ No current program found")
        
        print("\n4. Getting stream URL...")
        stream_url = api.get_stream_url(target_station, auth_token)
        if stream_url:
            print(f"✓ Stream URL ready")
        else:
            print("⚠ Could not get stream URL")
        
        print("\n✓ Complete workflow executed successfully!")
    
    except RadikoApiError as e:
        print(f"✗ Error during workflow: {e}")


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("Radiko API Examples")
    print("=" * 60)
    
    # Basic examples (always safe)
    example_basic_initialization()
    
    # Network-dependent examples (may fail without network)
    print("\n" + "=" * 60)
    print("Network-Dependent Examples")
    print("=" * 60)
    print("Note: These examples require internet connection and Radiko API availability.\n")
    
    # Try authorization first to get token
    auth_token, area_id = example_authorization()
    
    # Other examples
    example_station_information()
    example_now_program()
    example_weekly_program()
    
    if auth_token:
        example_stream_url(auth_token)
    
    example_search_programs()
    example_error_handling()
    example_complete_workflow()
    
    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
