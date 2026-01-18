#!/usr/bin/env python3
"""Record radio programs with configurable scheduling and cleanup.

This module handles scheduled radio recording based on configuration files,
with support for conditional overrides and automated file cleanup.
"""

import glob
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta

# Parse command-line arguments
if len(sys.argv) < 3:
    print("Usage: python3 record_radio.py <station> <prefix> [-c]")
    sys.exit(1)

station_input = sys.argv[1]
prefix_input = sys.argv[2]
cleanup_mode = "-c" in sys.argv


def is_last_weekday_in_month(date: datetime) -> bool:
    """Check if the given date is the last occurrence of that weekday in month.

    Args:
        date: Date to check

    Returns:
        True if date is the last occurrence of that weekday, False otherwise
    """
    target_weekday = date.weekday()  # 0: Monday ~ 6: Sunday
    # Get the last day of the month
    last_day = date.replace(day=1) + timedelta(days=32)
    last_day = last_day.replace(day=1) - timedelta(days=1)

    # Collect all dates in the month with the same weekday
    weekday_dates = [
        day
        for day in range(1, last_day.day + 1)
        if date.replace(day=day).weekday() == target_weekday
    ]

    return date.day == weekday_dates[-1]


def resolve_recording_config(entry: dict, date: datetime = None) -> dict:
    """Resolve recording configuration with conditional overrides.

    Applies last_weekday_override if the current date is the last occurrence
    of that weekday in the month.

    Args:
        entry: Configuration entry from program_config
        date: Reference date (defaults to today)

    Returns:
        Merged configuration dictionary
    """
    date = date or datetime.today()
    config = entry.copy()

    # Apply conditional override for last weekday of the month
    if "last_weekday_override" in entry and is_last_weekday_in_month(date):
        config.update(entry["last_weekday_override"])

    return config


def build_command(config: dict, service_name: str) -> list:
    """Build command list for executing the service-specific recorder.

    Args:
        config: Recording configuration dictionary
        service_name: Name of the service (e.g., 'radiko', 'nhk')

    Returns:
        List representing the command to execute
    """
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


# Get current date and time information
now = datetime.now()
today = now.date()
now_time = now.replace(second=0, microsecond=0)

# Load configuration files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(BASE_DIR, "program_config.json"), "r", encoding="utf-8") as f:
    config = json.load(f)

with open(os.path.join(BASE_DIR, "streaming_config.json"), "r", encoding="utf-8") as f:
    stream_config = json.load(f)

# Process recording for matching entries
for name, entry in config.items():
    if entry["station"] != station_input:
        continue
    if prefix_input and entry["prefix"] != prefix_input:
        continue

    # Insert sleep delay before recording (service-specific)
    service_name = entry["service"]
    sleep_sec = stream_config.get(service_name, {}).get("sleep", 0)
    if sleep_sec > 0:
        print(f"{name}: {service_name}  {sleep_sec} sec sleep.", flush=True)
        time.sleep(sleep_sec)

    # Execute recording
    entry_config = resolve_recording_config(entry)
    cmd = build_command(entry_config, service_name)
    print(f"[{datetime.now()}]: recording start [{name}] [{cmd}]", flush=True)
    subprocess.run(cmd)
    print(f"[{datetime.now()}]: recording done.", flush=True)

    # Cleanup phase (only if -c option is specified)
    if cleanup_mode:
        print(f"[{datetime.now()}]: clean up start.", flush=True)
        files = glob.glob(f'{entry_config["outputdir"]}/{entry_config["prefix"]}*')
        if len(files) > 1:
            # Keep only the largest file
            largest = max(files, key=os.path.getsize)
            for f in files:
                if f != largest:
                    os.remove(f)
            shutil.move(largest, entry_config["destdir"])
        elif len(files) == 1:
            shutil.move(files[0], entry_config["destdir"])
        else:
            print(f"[{datetime.now()}]: No recording files found.")

        # Synchronize with OneDrive
        subprocess.run(["/usr/bin/onedrive", "--synchronize"])
        print(f"[{datetime.now()}]: clean up done.", flush=True)
    break
else:
    print(f"[{datetime.now()}]: No matching programs found ({station_input})")

print(f"[{datetime.now()}]: done.", flush=True)
