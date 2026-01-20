# Program Data Model

## Overview

The `Program` class is a unified data structure for representing radio programs from both NHK and Radiko APIs. It provides a common interface for downstream consumers (recorders, finders, formatters, etc.) regardless of the source API.

## Class Definition

```python
@dataclass
class Program:
    """Represents a radio program with unified metadata for NHK and Radiko."""
    
    # Required fields
    title: str                          # Program title
    station: str                        # Station ID (e.g., 'TBS', 'INT', 'NR1')
    start_time: str                     # Start time in YYYYMMDDHHMMSS format
    end_time: str                       # End time in YYYYMMDDHHMMSS format
    source: Literal["nhk", "radiko"]   # Source API
    
    # Optional fields with defaults
    area: str = "JP13"                  # Area ID (e.g., 'JP13' for Kanto)
    stream_url: Optional[str] = None    # M3U8 streaming URL
    duration: int = 0                   # Duration in minutes (auto-calculated)
    
    # NHK-specific fields
    program_title: Optional[str] = None           # Episode title
    onair_date: Optional[str] = None              # Broadcast date string (Japanese format)
    closed_at: Optional[str] = None               # Content delivery end date
    series_site_id: Optional[str] = None          # Series ID
    corner_site_id: Optional[str] = None          # Corner ID
    program_sub_title: Optional[str] = None       # Subtitle or additional title
    
    # Radiko-specific fields
    performer: Optional[str] = None     # Program host/personality name
    description: Optional[str] = None   # Program description
    info: Optional[str] = None          # Additional information string
    image_url: Optional[str] = None     # URL to program cover image
    url: Optional[str] = None           # Program information URL
```

## Factory Methods

### `from_nhk_series(series_data: dict, episode_data: dict) -> Program`

Creates a Program instance from NHK API response data.

**Parameters:**
- `series_data`: Series information dict from `NHKApi.get_series()`
- `episode_data`: Episode information dict from `extract_recording_info()`

**Example:**
```python
from mypkg.nhk_api import NHKApi
from mypkg.program import Program

api = NHKApi()
series_data = api.get_series("nhk_FM_jbkc", "01")

# Simulating extract_recording_info() return value
episode_info = {
    "program_title": "「にほんごであそぼ」～鼠小僧次郎吉～",
    "onair_date": "2026-01-18(日)午後11:30放送",
    "closed_at": "2026-01-26",
    "stream_url": "https://example.com/nhk_stream.m3u8",
    "program_sub_title": "作: 劇作家太郎",
}

program = Program.from_nhk_series(
    {"title": series_data["title"]},
    episode_info
)
```

**Auto-generated Fields:**
- `source`: "nhk"
- `station`: "NHK"
- `start_time`: Parsed from `onair_date` (Japanese format)
- `end_time`: Parsed from `closed_at`
- `area`: "JP13"

### `from_radiko_program(program_data: dict) -> Program`

Creates a Program instance from Radiko API response data.

**Parameters:**
- `program_data`: Program information dict from `RadikoApi.fetch_*_program()`

**Example:**
```python
from mypkg.radiko_api import RadikoApi
from mypkg.program import Program

api = RadikoApi()
auth_token, area_id = api.authorize()
program_data = api.fetch_now_program("INT", area_id=area_id)

program = Program.from_radiko_program(program_data)
```

**Auto-generated Fields:**
- `source`: "radiko"

## Helper Methods

### `is_nhk() -> bool`

Checks if the program is from NHK API.

```python
program = Program.from_nhk_series(...)
if program.is_nhk():
    print("This is an NHK program")
```

### `is_radiko() -> bool`

Checks if the program is from Radiko API.

```python
program = Program.from_radiko_program(...)
if program.is_radiko():
    print("This is a Radiko program")
```

### `is_recordable() -> bool`

Checks if the program can be recorded (i.e., `stream_url` is available).

```python
if program.is_recordable():
    # Proceed with recording
    stream_url = program.stream_url
    duration = program.get_duration_minutes()
else:
    print("No stream URL available")
```

### `get_start_datetime() -> datetime`

Parses start time as a datetime object.

```python
start = program.get_start_datetime()
# datetime(2026, 1, 20, 13, 30, 0)
```

### `get_end_datetime() -> datetime`

Parses end time as a datetime object.

```python
end = program.get_end_datetime()
# datetime(2026, 1, 20, 13, 55, 0)
```

### `get_duration_minutes() -> int`

Returns program duration in minutes.

```python
duration = program.get_duration_minutes()
# 25 (25 minutes)
```

### `get_duration_seconds() -> int`

Returns program duration in seconds.

```python
duration = program.get_duration_seconds()
# 1500 (25 minutes = 1500 seconds)
```

### `__str__() -> str`

Returns a human-readable string representation.

```python
str(program)
# "[NHK] ニュース (14:00-14:15)"
# "[INT] レコレール (13:30-13:55)"
```

## Time Format and Normalization

### Standard Time Format

All times are internally stored in `YYYYMMDDHHMMSS` format (14 characters):

| Format | Example | Description |
|--------|---------|-------------|
| YYYYMMDDHHMMSS | 20260120133000 | 2026-01-20 13:30:00 |

### NHK Date/Time Normalization

NHK API returns times in Japanese format (e.g., `"1月18日(日)午後11:30放送"`). The Program class automatically normalizes these to standard format.

**Supported Formats:**
- `"1月18日(日)午前9:00放送"` → `20260118090000`
- `"1月18日(日)午後3:30放送"` → `20260118153000`
- `"1月18日(日)午後11:30放送"` → `20260118233000`

**Implementation Details:**
- Month and day are extracted from Japanese text
- "午前" (AM) hours are kept as-is (except 12 AM → 0)
- "午後" (PM) hours are converted to 24-hour format
- Current year is used (since NHK API doesn't specify year)

## Data Mapping

### NHK API → Program

| `extract_recording_info()` Return | Program Field | Notes |
|---|---|---|
| `title` | `title` | Series title |
| `series_site_id` | `series_site_id` | Series ID |
| `program_title` | `program_title` | Episode title |
| `onair_date` | `onair_date` | Broadcast date (Japanese) |
| | `start_time` | Normalized from `onair_date` |
| `closed_at` | `closed_at` | Delivery end date |
| | `end_time` | Normalized from `closed_at` |
| `stream_url` | `stream_url` | M3U8 URL |
| `program_sub_title` | `program_sub_title` | Subtitle/DJ info |

### Radiko API → Program

| `fetch_*_program()` Return | Program Field | Notes |
|---|---|---|
| `title` | `title` | Program name |
| `station` | `station` | Station ID |
| `start_time` | `start_time` | Already in standard format |
| `end_time` | `end_time` | Already in standard format |
| `area` | `area` | Area ID |
| `performer` | `performer` | Host/DJ name |
| `description` | `description` | Program description |
| `info` | `info` | Additional info |
| `image_url` | `image_url` | Cover image URL |
| `url` | `url` | Info page URL |
| `stream_url` | `stream_url` | M3U8 URL (optional) |

## Integration with Recorder Scripts

### Usage in recorder_nhk.py

```python
from mypkg.nhk_api import NHKApi
from mypkg.program import Program
from mypkg.recorder import Recorder

api = NHKApi()
recorder = Recorder()

# Get series
series_data = api.get_series("nhk_FM_jbkc")

# Create Program instances
programs = []
for episode_info in series_data.get("episodes", []):
    program = Program.from_nhk_series(
        {"title": series_data["title"]},
        episode_info
    )
    if program.is_recordable():
        programs.append(program)

# Record programs
for program in programs:
    print(f"Recording: {program}")
    recorder.record(program.stream_url, program.title, program.get_duration_seconds())
```

### Usage in recorder_radiko.py

```python
from mypkg.radiko_api import RadikoApi
from mypkg.program import Program
from mypkg.recorder import Recorder

api = RadikoApi()
recorder = Recorder()

# Authorize
auth_token, area_id = api.authorize()

# Get current programs
programs = []
for station in ["TBS", "INT", "FM4"]:
    program_data = api.fetch_now_program(station, area_id=area_id)
    if program_data:
        program = Program.from_radiko_program(program_data)
        # Get stream URL
        program.stream_url = api.get_stream_url(program, auth_token)
        if program.is_recordable():
            programs.append(program)

# Record programs
for program in programs:
    print(f"Recording: {program}")
    recorder.record(program.stream_url, program.title, program.get_duration_seconds())
```

### Usage in find_radio.py

```python
from mypkg.nhk_api import NHKApi
from mypkg.radiko_api import RadikoApi
from mypkg.program import Program
from mypkg.program_formatter import ProgramFormatter

nhk_api = NHKApi()
radiko_api = RadikoApi()

# Collect programs from both sources
programs = []

# NHK programs
series = nhk_api.get_new_arrivals()
for series_data in series.get("corners", []):
    for episode in series_data.get("episodes", []):
        program = Program.from_nhk_series(series_data, episode)
        programs.append(program)

# Radiko programs
auth_token, area_id = radiko_api.authorize()
for station in ["TBS", "INT", "FM4"]:
    program_data = radiko_api.fetch_now_program(station, area_id=area_id)
    if program_data:
        program = Program.from_radiko_program(program_data)
        programs.append(program)

# Format and display
for program in programs:
    print(ProgramFormatter.get_display_list_string(program))
```

## Testing

Comprehensive unit tests are available in `test/test_program.py`:

```bash
python -m unittest test.test_program -v
```

**Test Coverage:**
- Factory methods (NHK/Radiko): 12 tests
- Helper methods: 7 tests
- Time handling: 6 tests
- String representation: 2 tests
- Date normalization: 4 tests
- Integration scenarios: 2 tests

**All 32 tests pass ✅**

## Error Handling

The Program class uses defensive programming:

```python
# Missing required fields are handled gracefully
program = Program(
    source="nhk",
    title="Test",
    station="NHK",
    start_time="20260120130000",
    end_time="20260120131500",
)

# Duration is auto-calculated
print(program.duration)  # 15 (minutes)

# Optional fields default to None
print(program.stream_url)  # None
print(program.is_recordable())  # False
```

## Backward Compatibility

- **NHK API**: No breaking changes. `extract_recording_info()` return value can be directly passed to `Program.from_nhk_series()`
- **Radiko API**: No breaking changes. `fetch_now_program()` return value can be directly passed to `Program.from_radiko_program()`
- Existing recorder scripts continue to work with Program instances

## Version History

- **2026-01-20**: Initial release
  - Unified Program class for NHK and Radiko
  - Factory methods for API integration
  - Comprehensive helper methods
  - Japanese date/time normalization
