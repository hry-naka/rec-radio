# API and Data Model Documentation

Complete documentation for the rec-radio project's APIs and unified data model.

## API Specifications

### [NHK_API_SPEC.md](NHK_API_SPEC.md)

API client for NHK Radio Ondemand service.

**Key Features:**
- Retrieve latest programs
- Get programs by specific date
- Fetch series and episode information
- Extract recording information with stream URLs
- Comprehensive error handling

**Integration:**
- Returns data compatible with `Program` class
- Automatic time normalization (Japanese format to standard)
- All data mapped to unified Program structure

---

### [RADIKO_API_SPEC.md](RADIKO_API_SPEC.md)

API client for Radiko radio streaming service.

**Key Features:**
- Two-step OAuth-like authentication
- Station information retrieval
- Current, today's, and weekly program schedules
- Stream URL extraction for playback
- Support for multiple stations and areas

**Integration:**
- Returns data compatible with `Program` class
- Standard time format (no normalization needed)
- All data mapped to unified Program structure

---

## Data Models

### [PROGRAM_DATA_MODEL.md](PROGRAM_DATA_MODEL.md)

Unified data model for radio programs from any source (NHK or Radiko).

**Purpose:**
- Single interface for all recording operations
- Abstracts API differences
- Provides common methods for both sources
- Enables source-agnostic recorder implementations

**Key Components:**
- `Program` dataclass with unified fields
- `from_nhk_series()` factory method
- `from_radiko_program()` factory method
- Helper methods: `is_nhk()`, `is_radiko()`, `is_recordable()`
- Time methods: `get_start_datetime()`, `get_end_datetime()`
- Japanese date/time normalization

---

## Architecture

### Data Flow

```
┌─────────────────────────────────────────────┐
│  Recorder Scripts                            │
│ (recorder_nhk.py, recorder_radiko.py)       │
│ (find_radio.py)                             │
└──────────────────┬──────────────────────────┘
                   │
       ┌───────────┴────────────┐
       │                        │
┌──────▼────────┐        ┌──────▼────────┐
│ NHKApi        │        │ RadikoApi      │
│ (API client)  │        │ (API client)   │
└──────┬────────┘        └──────┬────────┘
       │                        │
       └───────────┬────────────┘
                   │
         ┌─────────▼────────┐
         │ Program Factory  │
         │ Methods          │
         └─────────┬────────┘
                   │
         ┌─────────▼────────────┐
         │ Program Class        │
         │ (Unified Data Model) │
         └──────────┬───────────┘
                    │
    ┌───────────────┴──────────────┐
    │                              │
┌───▼──────────────┐     ┌────────▼───────┐
│ProgramFormatter  │     │ Recorder        │
│(Display/Format)  │     │(Recording Logic)│
└──────────────────┘     └─────────────────┘
```

### Separation of Concerns

1. **API Layer** - Direct communication with NHK and Radiko services
2. **Data Model Layer** - Unified Program class
3. **Formatter Layer** - Display and metadata formatting
4. **Recorder Layer** - Recording operations

---

## Testing

### Test Coverage

| Module | Tests | Status |
|--------|-------|--------|
| NHK API | 22 | ✅ PASS |
| Radiko API | 25 | ✅ PASS |
| Program | 32 | ✅ PASS |
| **Total** | **79** | **✅ ALL PASS** |

### Running Tests

```bash
# Run all tests
python -m unittest discover test -v

# Run specific test suite
python -m unittest test.test_nhk_api -v
python -m unittest test.test_radiko_api -v
python -m unittest test.test_program -v

# Run with coverage
python -m pytest test/ --cov=mypkg --cov-report=html
```

---

## Quick Start

### Using NHK API with Program Model

```python
from mypkg.nhk_api import NHKApi
from mypkg.program import Program

api = NHKApi()
series = api.get_series("nhk_FM_jbkc", "01")

# Convert to Program instances
programs = []
for episode in series.get("episodes", []):
    program = Program.from_nhk_series(series, episode)
    programs.append(program)

# Check and use programs
for program in programs:
    if program.is_recordable():
        print(f"Recording: {program}")
        duration = program.get_duration_minutes()
```

### Using Radiko API with Program Model

```python
from mypkg.radiko_api import RadikoApi
from mypkg.program import Program

api = RadikoApi()
auth_token, area_id = api.authorize()

# Fetch current programs
program_data = api.fetch_now_program("INT", area_id=area_id)
program = Program.from_radiko_program(program_data)

# Get stream URL
stream_url = api.get_stream_url(program, auth_token)
program.stream_url = stream_url

if program.is_recordable():
    print(f"Recording: {program}")
```

### Unified Program Usage

```python
from mypkg.program_formatter import ProgramFormatter

# Works with both NHK and Radiko programs
programs = [nhk_program, radiko_program]

for program in programs:
    # Source-aware formatting
    print(ProgramFormatter.get_display_list_string(program))
    print(ProgramFormatter.get_detailed_info(program))
    
    # Common methods work on both
    print(f"Duration: {program.get_duration_minutes()} min")
    print(f"Recordable: {program.is_recordable()}")
```

---

## Key Concepts

### Source Field

All Program instances have a `source` field indicating the origin:

```python
program.source  # "nhk" or "radiko"

if program.is_nhk():
    print("NHK program with Japanese time format")
elif program.is_radiko():
    print("Radiko program with standard format")
```

### Time Handling

**NHK Format:**
- Input: `"1月18日(日)午後11:30放送"` (Japanese)
- Stored: `"20260118233000"` (Standard)
- Auto-normalized in `Program.from_nhk_series()`

**Radiko Format:**
- Input: `"20260120133000"` (Standard)
- Stored: `"20260120133000"` (Standard)
- No normalization needed

### Recordability

```python
# A program is recordable if it has a stream URL
if program.is_recordable():
    stream_url = program.stream_url
    duration = program.get_duration_seconds()
    # Proceed with recording
```

---

## Backward Compatibility

All changes maintain backward compatibility:

- Existing NHK API usage continues to work
- Existing Radiko API usage continues to work
- New Program class is purely additive
- No breaking changes to recorder scripts

---

## File Structure

```
mypkg/docs/
├── README.md                    # This file
├── NHK_API_SPEC.md             # NHK API documentation
├── RADIKO_API_SPEC.md          # Radiko API documentation
└── PROGRAM_DATA_MODEL.md       # Unified Program class

mypkg/
├── nhk_api.py                  # NHK API implementation
├── radiko_api.py               # Radiko API implementation
├── program.py                  # Program data model
├── program_formatter.py        # Formatter utilities
└── recorder.py                 # Recording logic

test/
├── test_nhk_api.py             # NHK API tests
├── test_radiko_api.py          # Radiko API tests
└── test_program.py             # Program class tests
```

---

## Version Information

- **Language**: Python 3.12.3
- **Last Updated**: 2026-01-20
- **Status**: Stable - All tests passing

---

## See Also

- [Program Data Model](PROGRAM_DATA_MODEL.md) - Detailed guide to the Program class
- [NHK API Specification](NHK_API_SPEC.md) - Complete NHK API reference
- [Radiko API Specification](RADIKO_API_SPEC.md) - Complete Radiko API reference
