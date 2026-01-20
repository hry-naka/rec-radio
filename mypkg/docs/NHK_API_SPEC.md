# NHKApi - NHK Radio Ondemand API Client

## Overview

`NHKApi` is a Python 3.12.3 API client class for the NHK Radio Ondemand API (radio-api/v1/web/ondemand).

## Installation

Included in the existing `mypkg` package.

```python
from mypkg.nhk_api import NHKApi, NHKApiError
```

## Basic Usage

### Initialization

```python
# Default timeout (10 seconds)
api = NHKApi()

# Custom timeout
api = NHKApi(timeout=15)
```

## Methods

### 1. `get_new_arrivals()` - Get Latest Programs

Retrieves the latest ondemand programs.

```python
api = NHKApi()
data = api.get_new_arrivals()
```

**Return Value**: `Dict[str, Any]`
- `corners`: List of program information

**Exceptions**:
- `NHKApiHttpError`: HTTP request error
- `NHKApiJsonError`: JSON parse error

### 2. `get_corners_by_date(onair_date)` - Get Programs by Date

Retrieves program information for a specified date.

```python
api = NHKApi()
data = api.get_corners_by_date("20260118")  # YYYYMMDD format
```

**Parameters**:
- `onair_date` (str): Broadcast date (YYYYMMDD format)

**Return Value**: `Dict[str, Any]`
- `onair_date`: Specified date
- `corners`: Program information list for that date

### 3. `get_series(site_id, corner_site_id)` - Get Series Information

Retrieves detailed series information and streaming URLs.

```python
api = NHKApi()
data = api.get_series(site_id="47Q5W9WQK9", corner_site_id="01")
```

**Parameters**:
- `site_id` (str): Series site ID
- `corner_site_id` (str, optional): Corner site ID (default: "01")

**Return Value**: `Dict[str, Any]`
- `id`: Series ID
- `title`: Series name
- `radio_broadcast`: Broadcast station (R1, R2, FM, etc.)
- `schedule`: Regular broadcast date/time
- `series_description`: Series description
- `episodes`: List of episode information
  - `id`: Episode ID
  - `program_title`: Program title
  - `onair_date`: Broadcast date/time
  - `closed_at`: Delivery end date/time
  - `stream_url`: M3U8 streaming URL
  - `program_sub_title`: Subtitle (DJ/guest information)

## Utility Methods

### `extract_corners(data)`

Extracts program information from the response of `get_new_arrivals()` or `get_corners_by_date()`.

```python
corners = api.extract_corners(data)
for corner in corners:
    print(corner['title'])
```

**Return Value**: `List[Dict[str, str]]`

### `extract_episodes(series_data)`

Extracts episode information from the response of `get_series()`.

```python
episodes = api.extract_episodes(series_data)
for episode in episodes:
    print(episode['program_title'])
    print(episode['stream_url'])  # M3U8 URL
```

**Return Value**: `List[Dict[str, str]]`

### `extract_recording_info(series_data)`

Extracts recording-necessary information from the response of `get_series()`.

```python
recording_info = api.extract_recording_info(series_data)
for info in recording_info:
    title = info['title']
    program_title = info['program_title']
    stream_url = info['stream_url']
    closed_at = info['closed_at']
    # Use for recording processing
```

**Return Value**: `List[Dict[str, str]]`
- `title`: Series name
- `program_title`: Program title
- `onair_date`: Broadcast date/time
- `stream_url`: M3U8 streaming URL
- `closed_at`: Delivery end date/time

## Exception Handling

### Exception Classes

```python
from mypkg.nhk_api import NHKApi, NHKApiError, NHKApiHttpError, NHKApiJsonError
```

**Inheritance Hierarchy**:
- `NHKApiError` (base exception)
  - `NHKApiHttpError` (HTTP error)
  - `NHKApiJsonError` (JSON parse error)

### Error Handling Example

```python
api = NHKApi()

try:
    data = api.get_new_arrivals()
except NHKApiHttpError as e:
    print(f"Network error: {e}")
except NHKApiJsonError as e:
    print(f"API response error: {e}")
except NHKApiError as e:
    print(f"Other API error: {e}")
```

## API Specification

### Base URL

```
https://www.nhk.or.jp/radio-api/v1/web/ondemand/
```

### Endpoints

#### 1. `/new_arrivals`

Retrieves the list of latest programs.

**Method**: GET

**Query Parameters**: None

**Response Example**:
```json
{
  "corners": [
    {
      "id": 1341,
      "title": "邦楽のひととき",
      "radio_broadcast": "FM",
      "onair_date": "2026年1月19日(月)放送",
      "series_site_id": "WW2Z47QY27",
      "corner_site_id": "01",
      "started_at": "2026-01-19T11:00:03+09:00"
    }
  ]
}
```

#### 2. `/corners?onair_date=YYYYMMDD`

Retrieves the program list for a specified date.

**Method**: GET

**Query Parameters**:
- `onair_date` (string): Broadcast date (YYYYMMDD format)

**Response Example**:
```json
{
  "onair_date": "20260118",
  "corners": [
    {
      "id": 18,
      "title": "マイあさ！",
      "radio_broadcast": "R1",
      "onair_date": "2026年1月18日(日)放送"
    }
  ]
}
```

#### 3. `/series?site_id=XXX&corner_site_id=YYY`

Retrieves detailed series information.

**Method**: GET

**Query Parameters**:
- `site_id` (string): Series site ID
- `corner_site_id` (string): Corner site ID

**Response Example**:
```json
{
  "id": 76,
  "title": "眠れない貴女へ",
  "radio_broadcast": "FM",
  "schedule": "毎週日曜 午後11時30分",
  "series_description": "...",
  "episodes": [
    {
      "id": 4296074,
      "program_title": "眠れない貴女(あなた)へ 【ゲスト】山崎佐知子",
      "onair_date": "1月18日(日)午後11:30放送",
      "closed_at": "2026年1月26日(月)午前1:00配信終了",
      "stream_url": "https://vod-stream.nhk.jp/radioondemand/r/47Q5W9WQK9/s/...",
      "program_sub_title": "【ＤＪ】和田明日香，【ゲスト】山崎佐知子"
    }
  ]
}
```

## Integration with Program Class

The return value of `extract_recording_info()` is formatted suitable for use in `recorder_nhk.py`:

```python
from mypkg.nhk_api import NHKApi

api = NHKApi()
series_data = api.get_series("47Q5W9WQK9", "01")
recording_info = api.extract_recording_info(series_data)

for info in recording_info:
    # All necessary information is included
    - title: Series name
    - program_title: Program title
    - onair_date: Broadcast date/time
    - stream_url: M3U8 URL (usable with ffmpeg)
    - closed_at: Delivery end date/time
```

## File Structure

```
mypkg/
├── nhk_api.py              # NHKApi class implementation
├── program.py              # Program data class
├── radiko_api.py           # Radiko API client
└── ...

nhk_api_examples.py         # Usage examples
test_nhk_api.py             # Unit tests
```

## Python Version

- Python 3.12.3

## Required Packages

- `requests` - HTTP request processing

## License

As per project license.

## Testing

### Running Unit Tests

The NHKApi class includes comprehensive unit tests covering:
- Initialization with various timeout values
- API method success and error cases
- Response normalization
- Utility method extraction
- Exception hierarchy validation

#### Run Tests with pytest

```bash
cd /path/to/rec-radio
python -m pytest test/test_nhk_api.py -v
```

#### Run Tests with unittest

```bash
cd /path/to/rec-radio
python -m unittest test.test_nhk_api -v
```

#### Run Specific Test Class

```bash
python -m pytest test/test_nhk_api.py::TestNHKApiNewArrivals -v
```

#### Run with Coverage

```bash
python -m pytest test/test_nhk_api.py --cov=mypkg.nhk_api --cov-report=html
```

### Test Results

Expected output (22 tests):
- TestNHKApiInitialization: 5 tests
- TestNHKApiNewArrivals: 3 tests
- TestNHKApiCornersByDate: 2 tests
- TestNHKApiSeries: 2 tests
- TestNHKApiExtraction: 6 tests
- TestNHKApiExceptionHierarchy: 4 tests

All tests should pass with `22 passed`.
