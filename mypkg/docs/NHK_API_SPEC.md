# NHKApi - NHK ラジオ聞き逃し配信 API クライアント

## 概要

`NHKApi` は NHK ラジオの聞き逃し配信 API（radio-api/v1/web/ondemand）に対応した Python 3.12.3 用の API クライアントクラスです。

## インストール

既存の `mypkg` パッケージに含まれます。

```python
from mypkg.nhk_api import NHKApi, NHKApiError
```

## 基本的な使用方法

### 初期化

```python
# デフォルトタイムアウト（10秒）
api = NHKApi()

# カスタムタイムアウト
api = NHKApi(timeout=15)
```

## メソッド

### 1. `get_new_arrivals()` - 新着番組取得

最新の聞き逃し配信番組を取得します。

```python
api = NHKApi()
data = api.get_new_arrivals()
```

**戻り値**: `Dict[str, Any]`
- `corners`: 番組情報のリスト

**例外**:
- `NHKApiHttpError`: HTTP リクエストエラー
- `NHKApiJsonError`: JSON パースエラー

### 2. `get_corners_by_date(onair_date)` - 日付別番組取得

指定した日付の番組情報を取得します。

```python
api = NHKApi()
data = api.get_corners_by_date("20260118")  # YYYYMMDD形式
```

**パラメータ**:
- `onair_date` (str): 放送日（YYYYMMDD形式）

**戻り値**: `Dict[str, Any]`
- `onair_date`: 指定した日付
- `corners`: その日の番組情報のリスト

### 3. `get_series(site_id, corner_site_id)` - シリーズ情報取得

番組シリーズの詳細情報とストリーミング URL を取得します。

```python
api = NHKApi()
data = api.get_series(site_id="47Q5W9WQK9", corner_site_id="01")
```

**パラメータ**:
- `site_id` (str): シリーズサイト ID
- `corner_site_id` (str, オプション): コーナーサイト ID（デフォルト: "01"）

**戻り値**: `Dict[str, Any]`
- `id`: シリーズ ID
- `title`: シリーズ名
- `radio_broadcast`: 放送局（R1, R2, FM など）
- `schedule`: 定期放送日時
- `series_description`: シリーズ説明
- `episodes`: エピソード情報のリスト
  - `id`: エピソード ID
  - `program_title`: 番組タイトル
  - `onair_date`: 放送日時
  - `closed_at`: 配信終了日時
  - `stream_url`: M3U8 ストリーミング URL
  - `program_sub_title`: 副題（DJ/ゲスト情報）

## ユーティリティメソッド

### `extract_corners(data)`

`get_new_arrivals()` または `get_corners_by_date()` のレスポンスから番組情報を抽出します。

```python
corners = api.extract_corners(data)
for corner in corners:
    print(corner['title'])
```

**戻り値**: `List[Dict[str, str]]`

### `extract_episodes(series_data)`

`get_series()` のレスポンスからエピソード情報を抽出します。

```python
episodes = api.extract_episodes(series_data)
for episode in episodes:
    print(episode['program_title'])
    print(episode['stream_url'])  # M3U8 URL
```

**戻り値**: `List[Dict[str, str]]`

### `extract_recording_info(series_data)`

`get_series()` のレスポンスから録音に必要な情報を抽出します。

```python
recording_info = api.extract_recording_info(series_data)
for info in recording_info:
    title = info['title']
    program_title = info['program_title']
    stream_url = info['stream_url']
    closed_at = info['closed_at']
    # 録音処理に使用
```

**戻り値**: `List[Dict[str, str]]`
- `title`: シリーズ名
- `program_title`: 番組タイトル
- `onair_date`: 放送日時
- `stream_url`: M3U8 ストリーミング URL
- `closed_at`: 配信終了日時

## 例外処理

### 例外クラス

```python
from mypkg.nhk_api import NHKApi, NHKApiError, NHKApiHttpError, NHKApiJsonError
```

**継承関係**:
- `NHKApiError` (基底例外)
  - `NHKApiHttpError` (HTTP エラー)
  - `NHKApiJsonError` (JSON パースエラー)

### エラーハンドリング例

```python
api = NHKApi()

try:
    data = api.get_new_arrivals()
except NHKApiHttpError as e:
    print(f"ネットワークエラー: {e}")
except NHKApiJsonError as e:
    print(f"API レスポンスエラー: {e}")
except NHKApiError as e:
    print(f"その他の API エラー: {e}")
```

## API 仕様

### ベース URL

```
https://www.nhk.or.jp/radio-api/v1/web/ondemand/
```

### エンドポイント

#### 1. `/new_arrivals`

新着番組一覧を取得します。

**メソッド**: GET

**クエリパラメータ**: なし

**レスポンス例**:
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

指定日付の番組一覧を取得します。

**メソッド**: GET

**クエリパラメータ**:
- `onair_date` (string): 放送日（YYYYMMDD形式）

**レスポンス例**:
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

シリーズの詳細情報を取得します。

**メソッド**: GET

**クエリパラメータ**:
- `site_id` (string): シリーズサイト ID
- `corner_site_id` (string): コーナーサイト ID

**レスポンス例**:
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

## Program クラスとの連携

`extract_recording_info()` の戻り値は、`recorder_nhk.py` での使用に適した形式です：

```python
from mypkg.nhk_api import NHKApi

api = NHKApi()
series_data = api.get_series("47Q5W9WQK9", "01")
recording_info = api.extract_recording_info(series_data)

for info in recording_info:
    # 必要な情報がすべて含まれています
    - title: シリーズ名
    - program_title: 番組タイトル
    - onair_date: 放送日時
    - stream_url: M3U8 URL（ffmpeg で利用可能）
    - closed_at: 配信終了日時
```

## ファイル構成

```
mypkg/
├── nhk_api.py              # NHKApi クラス実装
├── program.py              # Program データクラス
├── radiko_api.py           # Radiko API クライアント
└── ...

nhk_api_examples.py         # 使用例
test_nhk_api.py             # ユニットテスト
```

## Python バージョン

- Python 3.12.3

## 依存パッケージ

- `requests` - HTTP リクエスト処理

## ライセンス

プロジェクトに準じます。
