# RadikoApi - Radiko ラジオストリーミング API クライアント

## 概要

`RadikoApi` は Radiko ラジオストリーミングサービスの API に対応した Python 3.12.3 用のステートレス API クライアントクラスです。認証、局情報取得、番組情報取得などの機能を提供します。

## インストール

既存の `mypkg` パッケージに含まれます。

```python
from mypkg.radiko_api import RadikoApi, RadikoApiError, RadikoApiHttpError, RadikoApiXmlError
```

## 基本的な使用方法

### 初期化

```python
# デフォルトタイムアウト（10秒）
api = RadikoApi()

# カスタムタイムアウト
api = RadikoApi(timeout=15)
```

### 認証

```python
api = RadikoApi()
try:
    auth_result = api.authorize()
    if auth_result:
        auth_token, area_id = auth_result
        print(f"認可成功。エリアID: {area_id}")
except RadikoApiHttpError as e:
    print(f"認可エラー: {e}")
```

## メソッド一覧

### 初期化

#### `__init__(timeout=10)`

RadikoApi クライアントを初期化します。

**パラメータ**:
- `timeout` (int): リクエストのタイムアウト時間（秒）。デフォルト: 10

**例外**:
- `ValueError`: タイムアウトが正数でない場合

### 認証関連

#### `authorize()`

Radiko の2段階認証を実行します。

**戻り値**: `Tuple[str, str]` または `None`
- 成功時: `(auth_token, area_id)` のタプル
- 失敗時: `None`

**例外**:
- `RadikoApiHttpError`: HTTP リクエストエラー

```python
result = api.authorize()
if result:
    auth_token, area_id = result
    # トークンを使用してストリーム URL を取得
    stream_url = api.get_stream_url(channel_id, auth_token)
```

### 局情報取得

#### `get_station_list(area_id="JP13")`

指定したエリアの局一覧を取得します。

**パラメータ**:
- `area_id` (str): エリアID。デフォルト: "JP13"（関東地方）

**戻り値**: `ET.Element` または `None`
- XML ルート要素

**例外**:
- `RadikoApiHttpError`: HTTP リクエストエラー
- `RadikoApiXmlError`: XML パースエラー

```python
station_list = api.get_station_list("JP13")
if station_list is not None:
    for id_elem in station_list.iter("id"):
        print(id_elem.text)
```

#### `get_channel_list(area_id="JP13")`

指定したエリアのチャンネル ID とチャンネル名のリストを取得します。

**パラメータ**:
- `area_id` (str): エリアID。デフォルト: "JP13"

**戻り値**: `Tuple[List[str], List[str]]`
- `(channel_ids, channel_names)`

**例外**:
- `RadikoApiError`: 局情報取得失敗

```python
ids, names = api.get_channel_list("JP13")
for id, name in zip(ids, names):
    print(f"{id}: {name}")
```

#### `is_station_available(station, area_id="JP13")`

指定した局が指定したエリアで利用可能かどうかを確認します。

**パラメータ**:
- `station` (str): 局ID
- `area_id` (str): エリアID。デフォルト: "JP13"

**戻り値**: `bool`
- 利用可能な場合: `True`
- 利用不可の場合: `False`

**例外**:
- `RadikoApiError`: 局情報取得失敗

```python
if api.is_station_available("TBS", "JP13"):
    print("TBS は関東で利用可能")
```

### 番組情報取得

#### `fetch_now_program(station, area_id="JP13")`

現在放送中の番組情報を取得します。

**パラメータ**:
- `station` (str): 局ID
- `area_id` (str): エリアID。デフォルト: "JP13"

**戻り値**: `Program` または `None`
- 番組情報オブジェクト

**例外**:
- `RadikoApiHttpError`: HTTP リクエストエラー
- `RadikoApiXmlError`: XML パースエラー

```python
program = api.fetch_now_program("TBS")
if program:
    print(f"現在: {program.title}")
    print(f"出演: {program.performer}")
```

#### `fetch_today_program(station, current_time, area_id="JP13")`

指定した時刻の番組情報を取得します。

**パラメータ**:
- `station` (str): 局ID
- `current_time` (str): 時刻（YYYYMMDDHHMMSS 形式）
- `area_id` (str): エリアID。デフォルト: "JP13"

**戻り値**: `Program` または `None`

**例外**:
- `RadikoApiHttpError`: HTTP リクエストエラー
- `RadikoApiXmlError`: XML パースエラー

```python
program = api.fetch_today_program("TBS", "20260120143000")
```

#### `fetch_weekly_program(station)`

週間番組表を取得します。

**パラメータ**:
- `station` (str): 局ID

**戻り値**: `Program` または `None`

**例外**:
- `RadikoApiHttpError`: HTTP リクエストエラー
- `RadikoApiXmlError`: XML パースエラー

```python
program = api.fetch_weekly_program("TBS")
```

### ストリーム処理

#### `get_stream_url(channel, auth_token)`

M3U8 ストリーム URL を取得します。

**パラメータ**:
- `channel` (str): チャンネルID
- `auth_token` (str): 認可トークン

**戻り値**: `str` または `None`
- ストリーム URL

**例外**:
- `RadikoApiHttpError`: HTTP リクエストエラー

```python
auth_result = api.authorize()
if auth_result:
    auth_token, area_id = auth_result
    stream_url = api.get_stream_url("TBS", auth_token)
    if stream_url:
        print(f"ストリーム URL: {stream_url}")
```

### プログラム検索

#### `search_programs(keyword="", time_filter="past", area_id="JP13")`

キーワードで番組を検索します。

**パラメータ**:
- `keyword` (str): 検索キーワード。デフォルト: ""
- `time_filter` (str): 時間フィルター。"past", "today", "future" から選択。デフォルト: "past"
- `area_id` (str): エリアID。デフォルト: "JP13"

**戻り値**: `Dict[str, Any]`
- 検索結果

**例外**:
- `RadikoApiHttpError`: HTTP リクエストエラー
- `RadikoApiXmlError`: JSON パースエラー

```python
results = api.search_programs(keyword="ニュース", time_filter="today")
```

### ユーティリティ

#### `dump()`

API クライアントの状態を表示します（デバッグ用）。

RadikoApi はステートレスなため、このメソッドは設定情報のみを表示します。

```python
api.dump()  # 出力例: RadikoApi(timeout=10s)
```

## 例外処理

### 例外クラス階層

```
RadikoApiError (基底例外)
├── RadikoApiHttpError (HTTP/ネットワークエラー)
└── RadikoApiXmlError (XML パースエラー)
```

### エラーハンドリング例

```python
from mypkg.radiko_api import RadikoApi, RadikoApiError, RadikoApiHttpError, RadikoApiXmlError

api = RadikoApi()

try:
    program = api.fetch_now_program("TBS")
except RadikoApiHttpError as e:
    print(f"ネットワークエラー: {e}")
except RadikoApiXmlError as e:
    print(f"XML パースエラー: {e}")
except RadikoApiError as e:
    print(f"その他の API エラー: {e}")
```

## Program クラス

各メソッドが返す `Program` オブジェクトの属性：

- `title` (str): 番組タイトル
- `station` (str): 局ID
- `area` (str): エリアID
- `start_time` (str): 開始時刻
- `end_time` (str): 終了時刻
- `duration` (int): 放送時間（分）
- `performer` (str): 出演者
- `description` (str): 説明
- `info` (str): 情報
- `image_url` (str): 画像 URL
- `url` (str): 番組ページ URL

## 定数

### API エンドポイント

- `BASE_SEARCH_URL`: "https://radiko.jp/v3/api/program/search"
- `BASE_STATION_URL`: "https://radiko.jp/v3/station/list/{}.xml"
- `BASE_PROGRAM_NOW_URL`: "https://radiko.jp/v3/program/now/{}.xml"
- `BASE_PROGRAM_WEEKLY_URL`: "https://radiko.jp/v3/program/station/weekly/{}.xml"
- `BASE_PROGRAM_DATE_URL`: "http://radiko.jp/v3/program/station/date/{}/{}.xml"
- `BASE_STREAM_URL`: "https://f-radiko.smartstream.ne.jp/{}"

### デフォルト値

- `DEFAULT_TIMEOUT`: 10 (秒)
- `DEFAULT_AREA_ID`: "JP13" (関東地方)

## 使用例

### 完全な実行例

```python
from mypkg.radiko_api import RadikoApi, RadikoApiError

# API クライアントを初期化
api = RadikoApi(timeout=15)

try:
    # 1. 認可を取得
    auth_result = api.authorize()
    if not auth_result:
        print("認可失敗")
        exit(1)
    
    auth_token, area_id = auth_result
    print(f"認可成功。エリア: {area_id}")
    
    # 2. 利用可能な局を取得
    ids, names = api.get_channel_list(area_id)
    print(f"利用可能な局: {list(zip(ids, names))}")
    
    # 3. 指定した局の現在の番組を取得
    program = api.fetch_now_program("TBS")
    if program:
        print(f"現在放送中: {program.title}")
        print(f"出演: {program.performer}")
        print(f"説明: {program.description}")
    
    # 4. ストリーム URL を取得
    stream_url = api.get_stream_url("TBS", auth_token)
    if stream_url:
        print(f"ストリーム URL: {stream_url}")
    
    # 5. 番組を検索
    results = api.search_programs(keyword="ニュース", time_filter="today")
    print(f"検索結果: {results}")

except RadikoApiError as e:
    print(f"エラー: {e}")
```

## ステートレス設計

`RadikoApi` はステートレス設計です。各メソッドは独立しており、内部状態を保持しません。これにより：

- 複数のスレッドから安全に使用可能
- メモリ効率が良い
- テストが容易

## Python バージョン

- Python 3.12.3

## 依存パッケージ

- `requests` - HTTP リクエスト処理

## ライセンス

プロジェクトに準じます。
