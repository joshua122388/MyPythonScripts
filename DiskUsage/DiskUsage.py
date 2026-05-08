#!/usr/bin/env python3
"""
script that actively monitors disk space utilization in the root partition on a linux virtual machine that triggers an alert when disk space exceeds a threshold of 80%
"""

import shutil
import time
import subprocess
import argparse
import os
from datetime import datetime

THRESHOLD = 80
CHECK_INTERVAL = 60
LOG_PATH = "/var/log/disk_usage_monitor.log"


def get_disk_usage(path="/"):
    # Ask the OS for disk stats at the given path (defaults to root "/")
    # Returns a named tuple with .total, .used, and .free — all in bytes
    usage = shutil.disk_usage(path)

    # Convert bytes → gigabytes by dividing by 1024^3 (i.e. 1,073,741,824)
    total_gb = usage.total / (1024 ** 3)
    used_gb = usage.used / (1024 ** 3)
    free_gb = usage.free / (1024 ** 3)

    # Calculate what percentage of the disk is currently used
    # e.g. used=80GB, total=100GB → 80.0%
    used_pct = usage.used / usage.total * 100

    # Return all four values so the caller can use whichever it needs
    return used_pct, total_gb, used_gb, free_gb


def send_alert(used_pct, total_gb, used_gb, free_gb, log_path):
    # Build a timestamped alert message with all the disk stats
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = (
        f"[{timestamp}] ALERT: Disk usage at {used_pct:.0f}% "
        f"(Used: {used_gb:.0f} GB / Total: {total_gb:.0f} GB / Free: {free_gb:.0f} GB)"
    )

    # Print the alert to the terminal
    print(message)

    resolved_log = log_path
    try:
        # Append the alert message to the log file
        with open(log_path, "a") as f:
            f.write(message + "\n")
    except PermissionError:
        # If we can't write to the system log path, fall back to the user's home directory
        fallback = os.path.expanduser("~/disk_usage.log")
        with open(fallback, "a") as f:
            f.write(message + "\n")
        print(f"No write permission to {log_path}, logging to {fallback}")

    # Broadcast a short alert to all logged-in terminal users via the 'wall' command
    wall_message = f"ALERT: Disk usage at {used_pct:.0f}% on / ({free_gb:.0f} GB free)"
    try:
        subprocess.run(["wall", wall_message], check=False, capture_output=True)
    except FileNotFoundError:
        pass  # 'wall' not available on this system


def monitor_loop(threshold, interval, log_path):
    print(f"Monitoring disk usage on / — threshold: {threshold}%, interval: {interval}s, log: {log_path}")
    while True:
        used_pct, total_gb, used_gb, free_gb = get_disk_usage("/")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] Disk usage: {used_pct:.0f}% ({free_gb:.0f} GB free)")

        if used_pct >= threshold:
            send_alert(used_pct, total_gb, used_gb, free_gb, log_path)

        time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description="Monitor disk usage on / and alert when threshold is exceeded.")
    parser.add_argument("--threshold", type=float, default=THRESHOLD,
                        help=f"Alert threshold percentage (default: {THRESHOLD})")
    parser.add_argument("--interval", type=int, default=CHECK_INTERVAL,
                        help=f"Check interval in seconds (default: {CHECK_INTERVAL})")
    parser.add_argument("--logfile", default=LOG_PATH,
                        help=f"Log file path (default: {LOG_PATH})")
    args = parser.parse_args()

    try:
        monitor_loop(args.threshold, args.interval, args.logfile)
    except KeyboardInterrupt:
        print("\nMonitor stopped.")


if __name__ == "__main__":
    main()
