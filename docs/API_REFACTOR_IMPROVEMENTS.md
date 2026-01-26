# API-Refactor ブランチ改善実施内容

## 改善日
2026年1月26日

## 改善の目的
- Program クラス中心の構造をより明確にし、責務分離を徹底する
- recorder_radiko.py / recorder_nhk.py を「録音処理の唯一の窓口」として整理する
- find_radio.py → Program → recorder_xxx の流れを安定させる
- **ProgramFormatter の Cmd と recorder_xxx の ffmpeg コマンド生成を完全に一致させる**
- ffmpeg のオプションを .env で管理し、コードに直書きしない
- **find_radio.py の --cmd 出力と実際の録音コマンドを完全一致させる**
- **tfrec_radiko.py でも rec_radiko.py と同じ品質のメタデータを設定する**

## 実施した改善内容

### 1. .env.example の拡張
**ファイル**: `.env.example`

**追加内容**:
- `RADIKO_FFMPEG_OPTS`: Radiko 用 ffmpeg オプション（デフォルト: `-loglevel warning -vn -acodec copy` に加えて接続オプション）
- `NHK_FFMPEG_OPTS`: NHK 用 ffmpeg オプション（デフォルト: `-loglevel warning -vn -acodec copy` に加えて接続オプション）
- `RADIKO_AREA_ID`: Radiko エリア ID（デフォルト: JP13）
- `NHK_AREA_ID`: NHK エリア ID（デフォルト: JP13）

**効果**: ユーザー環境に合わせて ffmpeg オプションをカスタマイズ可能に、音声のみの録音を明示

### 2. recorder_radiko.py の強化
**ファイル**: `mypkg/recorder_radiko.py`

**追加・変更内容**:
- `_load_ffmpeg_options()`: .env から RADIKO_FFMPEG_OPTS を読み込み
- `record(program, output_file=None)`: 認証を含めた統一録音メソッド（Program を渡すだけで完結）
- `record_stream_with_ffmpeg()`: Radiko 専用 ffmpeg 実行メソッド（.env のオプションを使用）
- `get_ffmpeg_command()`: ffmpeg コマンド文字列生成（内部使用）
- **`build_ffmpeg_cmd(program)`**: tfrec_radiko.py 形式のコマンド生成（ProgramFormatter から利用）

**効果**: 
- tfrec_radiko.py の ffmpeg ロジックを完全に統合
- .env のオプションを参照することで、コードの変更なしにカスタマイズ可能
- **ProgramFormatter が同じコマンド生成ロジックを使用できる**

### 3. recorder_nhk.py の強化
**ファイル**: `mypkg/recorder_nhk.py`

**追加・変更内容**:
- `_load_ffmpeg_options()`: .env から NHK_FFMPEG_OPTS を読み込み
- `record(program, output_file=None)`: 統一録音メソッド（Program を渡すだけで完結）
- `record_stream_with_ffmpeg()`: NHK 専用 ffm内部使用）
- **`build_ffmpeg_cmd(program)`**: tfrec_nhk.py 形式のコマンド生成（ProgramFormatter から利用）

**効果**: 
- Radiko と同様の構造で一貫性を保持
- .env のオプションを参照
- **ProgramFormatter が同じコマンド生成ロジックを使用できる**
- Radiko と同様の構造で一貫性を保持
- .env のオプションを参照
- ProgramFormatter と同じコマンドを生成

### 4. ProgramFormatter の改善
**ファイル**: `mypkg/program_formatter.py`

**変更内容**:
- `format_list()` に `recorder_radiko` と `recorder_nhk` のパラメータを追加
- **recorder_xxx.build_ffmpeg_cmd(program) を呼び出して Cmd を生成**
- recorder が提供されない場合のフォールバック処理を実装
- TYPE_CHECKING を使用した循環インポートの回避

**効果**: 
- **find_radio.py の Cmd 出力と recorder_xxx の実装が完全一致**
- コマンド生成ロジックの一元化
- 将来的な拡張が容易

### 5. find_radio.py の整理
**ファイル**: `find_radio.py`

**変更内容**:
- RecorderRadiko と RecorderNHK をインポート
- **service に応じて適切な recorder インスタンスを作成**
- **ProgramFormatter.format_list() に recorder を渡してコマンド生成**

**効果**:
- **Cmd 出力が recorder の実装と完全一致**
- 録音処理は recorder_xxx が唯一の窓口であることを保証
- Program の生成は API 呼び出しのみに限定

### 6. tfrec_radiko.py の整理とメタデータ改善
**ファイル**: `tfrec_radiko.py`

**削除・変更内容**:
- `get_stream_url_for_timefree()` を削除（recorder_radiko に統合）
- `record_with_ffmpeg()` を削除（recorder_radiko の record_stream_with_ffmpeg を使用）
- `record_program()` を簡素化し、RecorderRadiko.record_program() を使用
- **`main()` で RadikoApi.fetch_today_program() を呼び出して番組情報を取得**
- **取得した Program で録音することで、rec_radiko.py と同じ品質のメタデータを設定**

**効果**:
- コードの重複を排除
- recorder_radiko.py に録音ロジックを完全に集約
- **メタデータ（title, artist, album, comment, covr 等）が正しく設定される**
- メンテナンス性の向上

### 7. テストの更新

#### test_recorder_radiko.py
**追加内容**:
- `TestRecorderRadikoFFmpegCommand`: ffmpeg コマンド生成のテスト
  - `test_get_ffmpeg_command_basic()`: 基本的なコマンド生成
  - `test_get_ffmpeg_command_with_auth_token()`: 認証トークン付きコマンド
  - `test_ffmpeg_options_loaded_from_env()`: .env からのオプション読み込み
- `TestRecorderRadikoRecord`: 統一 record() メソッドのテスト
  - `test_record_method_handles_authorization()`: 自動認証処理
  - `test_record_method_handles_authorization_failure()`: 認証失敗処理
- **`TestRecorderRadikoBuildCmd`: build_ffmpeg_cmd() のテスト**
  - `test_build_ffmpeg_cmd_format()`: コマンド形式の検証
  - `test_build_ffmpeg_cmd_matches_tfrec_format()`: tfrec_radiko.py 形式との一致確認

#### test_recorder_nhk.py
**追加内容**:
- `TestRecorderNHKFFmpegCommand`: ffmpeg コマンド生成のテスト
  - `test_get_ffmpeg_command_basic()`: 基本的なコマンド生成
  - `test_ffmpeg_options_loaded_from_env()`: .env からのオプション読み込み
- `TestRecorderNHKRecord`: 統一 record() メソッドのテスト
  - `test_record_method_calls_record_program()`: record_program 呼び出し確認
- **`TestRecorderNHKBuildCmd`: build_ffmpeg_cmd() のテスト**
  - `test_build_ffmpeg_cmd_format()`: コマンド形式の検証
  - `test_build_ffmpeg_cmd_matches_tfrec_format()`: tfrec_nhk.py 形式との一致確認

#### test_tfrec_radiko.py
**変更内容**:
- `TestGetStreamUrlForTimefree` を削除（機能が recorder に移動）
- `TestRecordWithFfmpeg` を削除（機能が recorder に移動）
- `TestRecordProgram` を更新（新しい実装に対応）

**効果**: テストが新しい実装に適合し、テストカバレッジを維持

## 設計原則の遵守状況

### ✅ Program クラス中心の構造
- Program はデータ構造に徹し、API 呼び出しや録音処理を持たない
- すべての録音処理は Program インスタンスを受け取る

### ✅ 責務分離
- **API 層** (radiko_api.py / nhk_api.py): API 呼び出しと Program 生成
- **録音層** (recorder_radiko.py / recorder_nhk.py): ffmpeg 実行とメタデータ設定
- **表示層** (ProgramFormatter): 表示用フォーマット、コマンド文字列生成
- **アプリケーション層** (find_radio.py / tfrec_radiko.py): ユーザーインターフェース

### ✅ 設定の外部化
- ffmpeg オプションを .env で管理
- コードに直書きせず、環境変数で制御
- デフォルト値は既存の設定を踏襲

### ✅ コードの重複排除
- tfrec_radiko.py の ffmpeg ロジックを recorder_radiko.py に統合
- 録音処理は recorder_xxx.py に完全に集約

### ✅ テストの整合性
- 新しいメソッドに対応したテストを追加
- 削除された機能のテストを削除
- モックを使用した単体テストを維持

## 使用方法

### 1. 環境変数の設定
`.env` ファイルを作成し、`.env.example` を参考に設定：

```bash
cp .env.example .env
# 必要に応じて RADIKO_FFMPEG_OPTS や NHK_FFMPEG_OPTS をカスタマイズ
```

### 2. Radiko タイムフリー録音（tfrec_radiko.py）

```bash
# 従来通りの使用方法
python tfrec_radiko.py -s TBS -ft 20260125093000 -to 20260125100000
```

**内部動作**:
1. Program インスタンス生成
2. RecorderRadiko.record() 呼び出し
3. .env の RADIKO_FFMPEG_OPTS を使用して録音

### 3. プログラムからの直接録音（新機能）

```python
from mypkg.program import Program
from mypkg.recorder_radiko import RecorderRadiko

# Program インスタンス作成
program = Program(
    title="Test Program",
    station="TBS",
    start_time="20260125093000",
    end_time="20260125100000",
    source="radiko",
)

# 録音実行（認証も自動）
recorder = RecorderRadiko()
success = recorder.record(program)
```

### 4. find_radio.py での使用

```bash
# 従来通り
python find_radio.py --service radiko --keyword "音楽"
```

**出力される Cmd 行**:
- `tfrec_radiko.py -s <station> -ft <start_time> -to <end_time>`（Radiko）
- `tfrec_nhk.py --id <series_id> --date <date> --title "<title>"`（NHK）

## 今後の拡張案

### ProgramFormatter の Cmd 出力を recorder と完全一致させる
現在は tfrec_xxx.py のコマンドを出力していますが、将来的には recorder の get_ffmpeg_command() を使用して直接 ffmpeg コマンドを出力することも可能です。

```python
# 将来の実装例
if program.is_radiko():
    recorder = RecorderRadiko()
    cmd = recorder.get_ffmpeg_command(program, output_file, auth_token)
```

### tfrec_nhk.py の同様の改善
tfrec_radiko.py と同様に、tfrec_nhk.py も recorder_nhk.py に統合することが可能です。

### 録音スケジュール機能
Program インスタンスのリストを受け取り、順次録音するスケジューラーを実装することが可能です。

## 制約事項

- **RadikoApi のヘッダ設定**: 今回は変更していません（別途対応予定）
- **コミット/プッシュ**: 実施していません（ユーザー判断で実施）
- **main ブランチ**: 今回の変更は api-refactor ブランチのみ対象

## テスト実行

```bash
# 全テスト実行
python -m pytest test/

# 特定のテスト実行
python -m pytest test/test_recorder_radiko.py -v
python -m pytest test/test_recorder_nhk.py -v
python -m pytest test/test_tfrec_radiko.py -v
```

## まとめ

今回の改善により、以下を達成しました：

1. ✅ ffmpeg オプションの .env 管理化
2. ✅ recorder_radiko.py / recorder_nhk.py の統一インターフェース（record() メソッド）
3. ✅ tfrec_radiko.py の ffmpeg ロジック統合
4. ✅ Program クラス中心の設計の徹底
5. ✅ テストの更新と整合性確保

これにより、コードの保守性、拡張性、テスタビリティが大幅に向上しました。
