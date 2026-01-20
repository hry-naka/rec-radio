# RadikoApi - Radiko Radio Streaming API Client

## Overview

`RadikoApi` is a stateless API client class for Python 3.12.3 that supports the Radiko radio streaming service API. It provides authentication, station information retrieval, and program information retrieval functions.

## Installation

Included in the existing `mypkg` package.

```python
from mypkg.radiko_api import RadikoApi, RadikoApiError, RadikoApiHttpError, RadikoApiXmlError
```

## Basic Usage

### Initialization

```python
# Default timeout (10 seconds)
api = RadikoApi()

# Custom timeout
api = RadikoApi(timeout=15)
```

### Authentication

```python
api = RadikoApi()
try:
    auth_result = api.authorize()
    if auth_result:
        auth_token, area_id = auth_result
        print(f"Authorization successful. Area ID: {area_id}")
except RadikoApiHttpError as e:
    print(f"Authorization error: {e}")
```

## Methods

### Initialization

#### `__init__(timeout=10)`

Initializes a RadikoApi client.

**Parameters**:
- `timeout` (int): Request timeout in seconds. Default: 10

**Exceptions**:
- `ValueError`: If timeout is not a positive number

### Authentication

#### `authorize()`

Executes Radiko's two-stage authentication.

**Return Value**: `Tuple[str, str]` or `None`
- Success: `(auth_token, area_id)` tuple
- Failure: `None`

**Exceptions**:
- `RadikoApiHttpError`: HTTP request error

```python
result = api.authorize()
if result:
    auth_token, area_id = result
    # Use token to get stream URL
    stream_url = api.get_stream_url(channel_id, auth_token)
```

### Station Information Retrieval

#### `get_station_list(area_id="JP13")`

Retrieves the station list for a specified area.

**Parameters**:
- `area_id` (str): Area ID. Default: "JP13" (Kanto region)

**Return Value**: `ET.Element` or `None`
- XML root element

**Exceptions**:
- `RadikoApiHttpError`: HTTP request error
- `RadikoApiXmlError`: XML parse error

```python
station_list = api.get_station_list("JP13")
if station_list is not None:
    for id_elem in station_list.iter("id"):
        print(id_elem.text)
```

#### `get_channel_list(area_id="JP13")`

Retrieves channel IDs and channel names for a specified area.

**Parameters**:
- `area_id` (str): Area ID. Default: "JP13"

**Return Value**: `Tuple[List[str], List[str]]`
- `(channel_ids, channel_names)`

**Exceptions**:
- `RadikoApiError`: Station information retrieval failure

```python
ids, names = api.get_channel_list("JP13")
for id, name in zip(ids, names):
    print(f"{id}: {name}")
```

#### `is_station_available(station, area_id="JP13")`

Checks if a specified station is available in a specified area.

**Parameters**:
- `station` (str): Station ID
- `area_id` (str): Area ID. Default: "JP13"

**Return Value**: `bool`
- Available: `True`
- Unavailable: `False`

**Exceptions**:
- `RadikoApiError`: Station information retrieval failure

```python
if api.is_station_available("TBS", "JP13"):
    print("TBS is available in Kanto")
```

### Program Information Retrieval

#### `fetch_now_program(station, area_id="JP13")`

Retrieves currently broadcasting program information.

**Parameters**:
- `station` (str): Station ID
- `area_id` (str): Area ID. Default: "JP13"

**Return Value**: `Program` or `None`
- Program information object

**Exceptions**:
- `RadikoApiHttpError`: HTTP request error
- `RadikoApiXmlError`: XML parse error

```python
program = api.fetch_now_program("TBS")
if program:
    print(f"Now: {program.title}")
    print(f"Performer: {program.performer}")
```

#### `fetch_today_program(station, current_time, area_id="JP13")`

Retrieves program information for a specified time.

**Parameters**:
- `station` (str): Station ID
- `current_time` (str): Time (YYYYMMDDHHMMSS format)
- `area_id` (str): Area ID. Default: "JP13"

**Return Value**: `Program` or `None`

**Exceptions**:
- `RadikoApiHttpError`: HTTP request error
- `RadikoApiXmlError`: XML parse error

```python
program = api.fetch_today_program("TBS", "20260120143000")
```

#### `fetch_weekly_program(station)`

Retrieves the weekly program guide.

**Parameters**:
- `station` (str): Station ID

**Return Value**: `Program` or `None`

**Exceptions**:
- `RadikoApiHttpError`: HTTP request error
- `RadikoApiXmlError`: XML parse error

```python
program = api.fetch_weekly_program("TBS")
```

### Stream Processing

#### `get_stream_url(channel, auth_token)`

Retrieves the M3U8 stream URL.

**Parameters**:
- `channel` (str): Channel ID
- `auth_token` (str): Authorization token

**Return Value**: `str` or `None`
- Stream URL

**Exceptions**:
- `RadikoApiHttpError`: HTTP request error

```python
auth_result = api.authorize()
if auth_result:
    auth_token, area_id = auth_result
    stream_url = api.get_stream_url("TBS", auth_token)
    if stream_url:
        print(f"Stream URL: {stream_url}")
```

### Program Search

#### `search_programs(keyword="", time_filter="past", area_id="JP13")`

Searches for programs by keyword.

**Parameters**:
- `keyword` (str): Search keyword. Default: ""
- `time_filter` (str): Time filter. Choose from "past", "today", "future". Default: "past"
- `area_id` (str): Area ID. Default: "JP13"

**Return Value**: `Dict[str, Any]`
- Search results

**Exceptions**:
- `RadikoApiHttpError`: HTTP request error
- `RadikoApiXmlError`: JSON parse error

```python
results = api.search_programs(keyword="News", time_filter="today")
```

### Utility

#### `dump()`

Displays the API client state (for debugging).

Since RadikoApi is stateless, this method displays only configuration information.

```python
api.dump()  # Output example: RadikoApi(timeout=10s)
```

## Exception Handling

### Exception Hierarchy

```
RadikoApiError (base exception)
├── RadikoApiHttpError (HTTP/network error)
└── RadikoApiXmlError (XML parse error)
```

### Error Handling Example

```python
from mypkg.radiko_api import RadikoApi, RadikoApiError, RadikoApiHttpError, RadikoApiXmlError

api = RadikoApi()

try:
    program = api.fetch_now_program("TBS")
except RadikoApiHttpError as e:
    print(f"Network error: {e}")
except RadikoApiXmlError as e:
    print(f"XML parse error: {e}")
except RadikoApiError as e:
    print(f"Other API error: {e}")
```

## Program Class

Attributes of `Program` objects returned by each method:

- `title` (str): Program title
- `station` (str): Station ID
- `area` (str): Area ID
- `start_time` (str): Start time
- `end_time` (str): End time
- `duration` (int): Broadcast duration (minutes)
- `performer` (str): Performers
- `description` (str): Description
- `info` (str): Information
- `image_url` (str): Image URL
- `url` (str): Program page URL

## Constants

### API Endpoints

- `BASE_SEARCH_URL`: "https://radiko.jp/v3/api/program/search"
- `BASE_STATION_URL`: "https://radiko.jp/v3/station/list/{}.xml"
- `BASE_PROGRAM_NOW_URL`: "https://radiko.jp/v3/program/now/{}.xml"
- `BASE_PROGRAM_WEEKLY_URL`: "https://radiko.jp/v3/program/station/weekly/{}.xml"
- `BASE_PROGRAM_DATE_URL`: "http://radiko.jp/v3/program/station/date/{}/{}.xml"
- `BASE_STREAM_URL`: "https://f-radiko.smartstream.ne.jp/{}"

### Default Values

- `DEFAULT_TIMEOUT`: 10 (seconds)
- `DEFAULT_AREA_ID`: "JP13" (Kanto region)

## Usage Example

### Complete Execution Example

```python
from mypkg.radiko_api import RadikoApi, RadikoApiError

# Initialize API client
api = RadikoApi(timeout=15)

try:
    # 1. Get authorization
    auth_result = api.authorize()
    if not auth_result:
        print("Authorization failed")
        exit(1)
    
    auth_token, area_id = auth_result
    print(f"Authorization successful. Area: {area_id}")
    
    # 2. Get available stations
    ids, names = api.get_channel_list(area_id)
    print(f"Available stations: {list(zip(ids, names))}")
    
    # 3. Get current program for specified station
    program = api.fetch_now_program("TBS")
    if program:
        print(f"Now broadcasting: {program.title}")
        print(f"Performer: {program.performer}")
        print(f"Description: {program.description}")
    
    # 4. Get stream URL
    stream_url = api.get_stream_url("TBS", auth_token)
    if stream_url:
        print(f"Stream URL: {stream_url}")
    
    # 5. Search programs
    results = api.search_programs(keyword="News", time_filter="today")
    print(f"Search results: {results}")

except RadikoApiError as e:
    print(f"Error: {e}")
```

## Stateless Design

`RadikoApi` uses a stateless design. Each method is independent and maintains no internal state. This provides:

- Thread-safe usage
- Efficient memory usage
- Easy testing

## Python Version

- Python 3.12.3

## Required Packages

- `requests` - HTTP request processing

## License

As per project license.

## Testing

### Running Unit Tests

The RadikoApi class includes comprehensive unit tests covering:
- Initialization with various timeout values
- Authorization and token handling
- Station list retrieval and filtering
- Program information acquisition
- Stream URL extraction
- Program search functionality
- Exception handling and error cases

#### Run Tests with pytest

```bash
cd /path/to/rec-radio
python -m pytest test/test_radiko_api.py -v
```

#### Run Tests with unittest

```bash
cd /path/to/rec-radio
python -m unittest test.test_radiko_api -v
```

#### Run Specific Test Class

```bash
python -m pytest test/test_radiko_api.py::TestRadikoApiAuthorization -v
```

#### Run with Coverage

```bash
python -m pytest test/test_radiko_api.py --cov=mypkg.radiko_api --cov-report=html
```

### Test Results

Expected output (25 tests):
- TestRadikoApiInitialization: 4 tests
- TestRadikoApiAuthorization: 3 tests
- TestRadikoApiStationMethods: 6 tests
- TestRadikoApiProgramMethods: 4 tests
- TestRadikoApiStreamMethods: 4 tests
- TestRadikoApiSearchMethods: 2 tests
- TestRadikoApiExceptionHierarchy: 2 tests

All tests should pass with `25 passed`.

### Running All Tests

Run both NHK and Radiko API tests:

```bash
python -m pytest test/test_nhk_api.py test/test_radiko_api.py -v
```

Expected total: 47 tests
