# rec-radio
よくある、ラジオ番組の録音用のpythonスクリプト

## 仕様
### NHKラジオの録音用
```
usage: rec_nhk.py [-h] [--timing [{previous,following,present}]] [-c] channel duration [outputdir] [Prefix name]

Recording NHK radio.

positional arguments:
  channel               Channel Name
  duration              Duration(minutes)
  outputdir             Output path default:'.'
  Prefix name           Prefix name for output file.

optional arguments:
  -h, --help            show this help message and exit
```
### radiko用
```
usage: rec_radiko.py [-h] [-c] channel duration [outputdir] [Prefix name]

Recording Radiko.

positional arguments:
  channel        Channel Name
  duration       Duration(minutes)
  outputdir      Output path default:'.'
  Prefix name    Prefix name for output file.

optional arguments:
  -h, --help     show this help message and exit
  -c, --cleanup  Cleanup(remove) output file which recording is not completed.
```

### radikoの番組表検索
```
usage: find_radiko.py [-h] -k KEYWORD [-a AREA_ID]

find keyword in Radiko program.

options:
  -h, --help            show this help message and exit
  -k KEYWORD, --keyword KEYWORD
                        keyword to be finded in Radiko program.
  -a AREA_ID, --area_id AREA_ID
                        area_id in Radiko program(API). ex) 'JP13' is for tokyo/japan. If omitted, this may be auto-
                        retrieved.
```

### タイムフリー録音
```
usage: tfrec_radiko.py [-h] -s STATION -ft FROMTIME -to TOTIME [-c] [outputdir] [Prefix-name]

Recording time-free-Radiko.

positional arguments:
  outputdir             Output path default:'.'
  Prefix-name           Prefix name for output file.

optional arguments:
  -h, --help            show this help message and exit
  -s STATION, --station STATION
                        Recording station.
  -ft FROMTIME, --fromtime FROMTIME
                        from time
  -to TOTIME, --totime TOTIME
                        to time
  -c, --cleanup         Cleanup(remove) output file which recording is not completed.
  ```

### ラッパー録音スクリプト（record_radio.py）

usage: python3 record_radio.py <station> <prefix> [-c]

- station: 放送局名（例: NHK2, NHK-FM）
- prefix: program_config.json に記載された番組識別子（例: REC, JazzVoyage）
- -c: cleanupモード（録音後に最大サイズのファイルのみ残し、OneDrive同期を実行）

このラッパーは、stationとprefixに一致する番組設定を program_config.json から選び、
録音スクリプト（rec_nhk.py / rec_radiko.py）を呼び出します。

録音対象の時刻判定は cron によって制御されるため、program_config.json から times は削除されました。

### program_config.json の構造（例）

{
  "RadioEnglishConversation": {
    "service": "NHK",
    "station": "NHK2",
    "duration": 15,
    "outputdir": "/home/user/Radio/English/REC",
    "destdir": "/home/user/OneDrive/Sound/Radio/English/REC",
    "prefix": "REC",
    "month_end_only": false
  }
}

- service: 使用する録音スクリプト（NHK または Radiko）
- station: 放送局名（NHK2, NHK-FM など）
- duration: 録音時間（分）
- outputdir: 一時保存先
- destdir: cleanup時の保存先
- prefix: ファイル名の先頭識別子
- month_end_only: true の場合、月末日曜のみ録音

### streaming_config.json の構造と役割

録音スクリプト（rec_nhk.py / rec_radiko.py）を呼び出す前に、サービスごとの遅延対策として sleep を挿入するための設定ファイルです。

構造は以下のようになります：

```json
{
  "NHK": {
    "sleep": 0
  },
  "Radiko": {
    "sleep": 5
  }
}

### crontab 設定例

crontab.example を参照

## 検索機能

### キーワード検索

```bash
python ./find_radio.py --service nhk --keyword "ジャズ"
python ./find_radio.py --service radiko --keyword "ジャズ"
```

正規表現をサポートしています：

```bash
# 複数キーワード検索
python ./find_radio.py --service nhk --keyword "(jazz|ジャズ)"

# パターン検索
python ./find_radio.py --service radiko --keyword "^朝"
```

### 検索対象フィールド

| サービス | 検索対象 | 理由 |
|---------|--------|------|
| **NHK** | `title` のみ | 新着番組リストには詳細情報が含まれていないため、title のみで高速フィルタリングを実施。マッチした番組についてのみ詳細情報を取得 |
| **Radiko** | `title`、`description`、`info`、`performer` | 全プログラム情報が available なため、複数フィールドで詳細検索をサポート |

### パフォーマンス

- NHK: ~1 秒（新着番組を title で高速フィルタリング）
- Radiko: ~1 秒（全プログラムを複数フィールドで検索）

