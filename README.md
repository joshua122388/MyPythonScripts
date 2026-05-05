# Log Analyzer

A command-line tool for Linux that lets you search, filter, and export system logs from `/var/log`. It auto-detects date formats, sorts log entries, outputs results as JSON, and can archive all logs into a `.zip` file.

## Features

- Recursively searches `/var/log` for a named log file
- Auto-detects date format (`YYYY-MM-DD`, `MM/DD/YYYY`, `DD/MM/YYYY`, etc.)
- Sort log entries by date or event type
- Outputs filtered results as formatted JSON
- Collects all logs from `/var/log` into a compressed `.zip` archive while preserving directory structure
- Logs its own activity to `loganalyzer.log`

## Requirements

- Python 3.6+
- Linux (reads from `/var/log`)
- Run with sufficient permissions to read log files (use `sudo` if needed)

## Usage

```bash
sudo python3 logAnalyzer.py
```

### Main Menu

```
+--------+-------------------------+
| Option | Function                |
+--------+-------------------------+
|   1    | Log Analyzer Tool       |
|   2    | Log Collector           |
|   3    | Exit                    |
+--------+-------------------------+
```

### Option 1 — Log Analyzer

Prompts you for a log filename (e.g. `sshd.log`, `firewalld.log`), locates it under `/var/log`, then lets you sort and view entries:

- **Sort by Date** — orders entries chronologically
- **Sort by Event** — orders entries alphabetically by event type, then by date

Results are printed as JSON:

```json
[
    {
        "date": "2024-03-15",
        "message": "Accepted publickey for user from 192.168.1.10 port 52341"
    }
]
```

### Option 2 — Log Collector

Recursively collects all files from `/var/log` and compresses them into `collected_logs.zip` in the current directory, preserving the original directory structure. Files that cannot be read due to permissions are skipped and reported.

## Notes

- `loganalyzer.log` is written to the current working directory and contains debug/info/warning output from each run.
- Ambiguous date formats (where day and month cannot be distinguished) default to `MM/DD/YYYY`.
- Binary or unreadable log files are read with `errors="replace"` to avoid crashes.
