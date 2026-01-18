"""Radiko Recording Application - Refactoring Summary

## Overview
The Radiko radio recording application has been comprehensively refactored
to improve code organization, maintainability, and adherence to SOLID principles.

## Architecture Changes

### Before: Monolithic Structure
- radiko_api.py: RadikoAPI class mixed API calls, state management, and business logic
- rec_radiko.py: Contained orchestration logic along with utility functions
- No clear separation of concerns

### After: Modular Architecture

#### 1. mypkg/program.py - Data Model
   - Program (dataclass): Pure data representation of a radio program
   - Attributes: title, station, area, start_time, end_time, performer, etc.
   - Methods: get_duration_minutes(), get_start_datetime(), get_end_datetime()
   - No business logic, no API calls

#### 2. mypkg/radiko_api.py - Stateless API Client
   - RadikoAPIClient: Handles all Radiko API interactions
   - Methods:
     * is_station_available(station, area_id): Check station availability
     * get_station_list(area_id): Retrieve station list XML
     * get_channel_list(area_id): Get channel IDs and names
     * get_stream_url(channel, auth_token): Retrieve M3U8 stream URL
     * fetch_program(station, from_time, ...): Get program information
     * fetch_today_program(...): Get today's program
     * fetch_now_program(...): Get current on-air program
     * fetch_weekly_program(...): Get weekly schedule
     * authorize(): Perform Radiko authentication
     * search_programs(keyword, ...): Search for programs
   - No state management (stateless design)
   - All methods return data types (Program objects or None)

#### 3. mypkg/program_formatter.py - Data Formatting Utilities
   - ProgramFormatter: Pure utility functions for data transformation
   - Static methods:
     * generate_filename(program, prefix, date_str): Create output filename
     * format_title_with_performer(title, performer): Format display title
     * get_metadata_comment(description, info): Generate metadata comment
     * get_log_string(program): Create log display string
     * format_time_display(time_str): Format time for display (HH:MM)
     * format_date_display(date_str): Format date for display (YYYY-MM-DD)
     * get_status_message(stage, program, detail): Generate status messages
   - No state, all operations are pure functions
   - Reusable across different contexts

#### 4. mypkg/recorder.py - Recording & Metadata Management
   - Recorder: Handles ffmpeg recording and MP4 metadata
   - Methods:
     * is_available(): Check if ffmpeg is available
     * record_stream(stream_url, auth_token, output_file, duration): Record audio
     * set_metadata(audio_file, program, track_num): Set MP4 metadata tags
   - Encapsulates ffmpeg execution
   - Handles MP4 metadata using mutagen library

#### 5. rec_radiko.py - Application Orchestration
   - get_args(): Parse command-line arguments
   - main(): Orchestrate the recording workflow
   - Workflow:
     1. Parse arguments
     2. Initialize API client and recorder
     3. Validate ffmpeg availability
     4. Check station availability
     5. Authorize with Radiko API
     6. Retrieve stream URL
     7. Fetch program information
     8. Execute recording
     9. Set metadata
     10. Exit

## Key Improvements

### 1. Separation of Concerns
   - API client: Only handles HTTP communication with Radiko
   - Data models: Only represent program information
   - Formatters: Only transform data for display/storage
   - Recorder: Only handles ffmpeg and metadata
   - Application: Only orchestrates the workflow

### 2. Stateless Design
   - RadikoAPIClient has no instance variables (except initialization)
   - Each method is independent and reusable
   - No side effects (except I/O)
   - Easier to test and debug

### 3. Type Hints
   - All methods include proper type annotations
   - Return types are explicit (Program, Optional[str], bool, etc.)
   - IDE support and early error detection

### 4. PEP8 Compliance
   - 79-character line length limits
   - Proper import ordering
   - Consistent naming conventions
   - Professional docstring format

### 5. Error Handling
   - Explicit error checks with meaningful messages
   - Graceful degradation (e.g., recording without program info)
   - Proper exception handling in API calls

### 6. Extensibility
   - New recording sources can be added (future: NHK, other services)
   - ProgramFormatter can be extended for different output formats
   - Recorder can support different audio formats
   - API client methods are independently testable

## Backward Compatibility Notes

### Old Import Path (Deprecated)
```python
from mypkg.radiko_api import Radikoapi
api = Radikoapi()
api.get_stationlist()  # Old method name
```

### New Import Path (Use This)
```python
from mypkg.radiko_api import RadikoAPIClient
from mypkg.program import Program
from mypkg.program_formatter import ProgramFormatter
from mypkg.recorder import Recorder

client = RadikoAPIClient()
stations = client.get_station_list()  # New method name
```

## Migration Guide for External Code

### If using RadikoAPI to fetch programs:

OLD:
```python
api = Radikoapi()
api.load_today(station, current_time, area_id)
title = api.title[0]
pfm = api.pfm[0]
```

NEW:
```python
client = RadikoAPIClient()
program = client.fetch_today_program(station, current_time, area_id)
if program:
    title = program.title
    performer = program.performer
```

### If using for metadata:

OLD:
```python
set_mp4_meta(api_object, channel, area_id, rec_file)
```

NEW:
```python
program = client.fetch_program(station, time, area_id, now=True)
recorder = Recorder()
recorder.set_metadata(rec_file, program)
```

## Testing Recommendations

### Unit Tests for Each Module:
1. test_program.py: Test Program dataclass methods
2. test_program_formatter.py: Test formatting utilities
3. test_radiko_api_client.py: Mock HTTP calls for API testing
4. test_recorder.py: Mock ffmpeg for recording tests
5. test_integration.py: End-to-end workflow testing

### Manual Testing:
```bash
# Test basic recording (requires valid credentials)
python3 rec_radiko.py TBS 10 . test

# Test with custom output
python3 rec_radiko.py INT 5 /tmp myprefix

# Test API client directly
python3 -c "
from mypkg.radiko_api import RadikoAPIClient
client = RadikoAPIClient()
ids, names = client.get_channel_list()
print('Available channels:', list(zip(ids, names))[:3])
"
```

## Performance Considerations

- Stateless API client: Lower memory footprint
- No caching: Always fetches fresh data (can be added as needed)
- Streaming recording: Direct ffmpeg piping without buffering
- Minimal data retention: Program objects deleted after use

## Future Enhancements

1. Add Program caching with TTL
2. Implement retry logic with exponential backoff
3. Add support for multiple recording sources
4. Create async versions of API calls
5. Add detailed logging framework
6. Create web UI for scheduling
7. Add recording queue management
8. Implement database storage for program history

## Conclusion

The refactored architecture provides a solid foundation for the Radiko
recording application with improved maintainability, testability, and
extensibility while maintaining backward compatibility with existing
workflows (via rec_radiko.py).
