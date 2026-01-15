import json
import sys
import subprocess
import os
import glob
import shutil
from datetime import datetime, timedelta

# === 引数処理 ===
if len(sys.argv) < 3:
    print("Usage: python3 record_radio.py <station> <prefix> [-c]")
    sys.exit(1)

station_input = sys.argv[1]
prefix_input = sys.argv[2]
cleanup_mode = "-c" in sys.argv


def is_last_weekday_in_month(date: datetime) -> bool:
    target_weekday = date.weekday()  # 0:月〜6:日
    last_day = date.replace(day=1) + timedelta(days=32)
    last_day = last_day.replace(day=1) - timedelta(days=1)

    # 月内で同じ曜日の日付を列挙
    weekday_dates = [
        day
        for day in range(1, last_day.day + 1)
        if date.replace(day=day).weekday() == target_weekday
    ]

    return date.day == weekday_dates[-1]


def resolve_recording_config(entry, date=None):
    date = date or datetime.today()
    config = entry.copy()

    # 条件付き上書き（last_weekday_override が存在する場合のみ）
    if "last_weekday_override" in entry and is_last_weekday_in_month(date):
        config.update(entry["last_weekday_override"])

    return config


def build_command(config, service_name):
    rec_path = os.path.join(BASE_DIR, f"rec_{service_name.lower()}.py")
    cmd = [
        sys.executable,
        rec_path,
        config["station"],
        str(config["duration"]),
        config["outputdir"],
        config["prefix"],
    ]
    if "option" in config and config["option"]:
        cmd.extend(config["option"].split())
    return cmd


# === 現在の情報 ===
now = datetime.now()
today = now.date()
now_time = now.replace(second=0, microsecond=0)

# === 設定読み込み ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(BASE_DIR, "program_config.json"), "r", encoding="utf-8") as f:
    config = json.load(f)
with open(os.path.join(BASE_DIR, "streaming_config.json"), "r", encoding="utf-8") as f:
    stream_config = json.load(f)

# === 録音対象の判定と実行 ===
for name, entry in config.items():
    if entry["station"] != station_input:
        continue
    if prefix_input and entry["prefix"] != prefix_input:
        continue

    # sleep挿入
    service_name = entry["service"]
    sleep_sec = stream_config.get(service_name, {}).get("sleep", 0)
    if sleep_sec > 0:
        print(f"{name}: {service_name}  {sleep_sec} sec sleep.", flush=True)
        import time

        time.sleep(sleep_sec)

    # 録音処理
    entry_config = resolve_recording_config(entry)
    cmd = build_command(entry_config, service_name)
    print(f"[{datetime.now()}]:recorgind start [{name}] [{cmd}]", flush=True)
    subprocess.run(cmd)
    print(f"[{datetime.now()}]:recording done.", flush=True)

    # cleanup処理（-c オプションがある場合のみ）
    if cleanup_mode:
        print(f"[{datetime.now()}]:clean up start.", flush=True)
        files = glob.glob(f'{entry_config["outputdir"]}/{entry_config["prefix"]}*')
        if len(files) > 1:
            largest = max(files, key=os.path.getsize)
            for f in files:
                if f != largest:
                    os.remove(f)
            shutil.move(largest, entry_config["destdir"])
        elif len(files) == 1:
            shutil.move(files[0], entry_config["destdir"])
        else:
            print(f"[{datetime.now()}]:録音ファイルが見つかりません")
        # subprocess.run(
        #        ["/usr/bin/onedrive", "--synchronize"],
        #        stdout=subprocess.DEVNULL,
        #        stderr=subprocess.DEVNULL
        # )
        subprocess.run(["/usr/bin/onedrive", "--synchronize"])
        print(f"[{datetime.now()}]:clean up done.", flush=True)
    break
else:
    print(f"[{datetime.now()}]: 該当番組なし（{station_input}）")

print(f"[{datetime.now()}]: done.", flush=True)
