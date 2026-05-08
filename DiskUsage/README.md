# Disk Usage Monitor

A Python script that actively monitors disk space utilization on the root partition (`/`) of a Linux system and triggers an alert when usage exceeds a configurable threshold.

## Features

- Monitors disk usage at a regular interval
- Sends an alert when disk usage exceeds the threshold
- Logs alerts to a file
- Broadcasts a warning to all logged-in terminal users via `wall`
- Falls back to a home directory log file if write permission is denied

## Requirements

- Python 3
- Linux (the `wall` command is Linux-specific; the script runs on other systems but skips the broadcast)

## Usage

```bash
python3 DiskUsage.py
```

### Options

| Argument | Default | Description |
|---|---|---|
| `--threshold` | `80` | Alert threshold as a percentage |
| `--interval` | `60` | How often to check disk usage, in seconds |
| `--logfile` | `/var/log/disk_usage_monitor.log` | Path to the log file |

### Examples

Run with default settings:
```bash
python3 DiskUsage.py
```

Alert at 90% usage, check every 30 seconds:
```bash
python3 DiskUsage.py --threshold 90 --interval 30
```

Use a custom log file:
```bash
python3 DiskUsage.py --logfile ~/my_disk_log.log
```

## Output

While running, the script prints a status line every interval:
```
[2026-05-05 10:00:00] Disk usage: 73% (25 GB free)
```

When the threshold is exceeded, an alert is printed and logged:
```
[2026-05-05 10:00:00] ALERT: Disk usage at 85% (Used: 85 GB / Total: 100 GB / Free: 15 GB)
```

## Stopping the Monitor

Press `Ctrl+C` to stop the script.
