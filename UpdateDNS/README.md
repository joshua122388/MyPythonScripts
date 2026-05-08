# dnsupdate.py

A Linux DNS management tool that reads and modifies `/etc/resolv.conf`, performs forward and reverse DNS lookups, and restarts the DNS service when needed. All actions are logged to a file and the terminal.

## Requirements

- Python 3.6+
- Linux (uses `sudo systemctl` to restart the DNS service)
- Root or sudo privileges for write operations on `/etc/resolv.conf`

No third-party packages required — standard library only.

## Usage

```bash
# Run interactively (default)
sudo python3 dnsupdate.py

# Point to a custom resolv.conf
sudo python3 dnsupdate.py --resolv-conf /path/to/resolv.conf

# Use a different DNS service name
sudo python3 dnsupdate.py --service systemd-resolved

# Enable debug logging
sudo python3 dnsupdate.py --verbose

# Skip automatic backups before changes
sudo python3 dnsupdate.py --no-backup

# Write logs to a custom path
sudo python3 dnsupdate.py --logfile ~/my-dns.log
```

## Menu Options

```
+--------+---------------------------+
| Option | Function                  |
+--------+---------------------------+
|   1    | List DNS Records          |
|   2    | Add DNS Record            |
|   3    | Update DNS Record         |
|   4    | Delete DNS Record         |
|   5    | Forward DNS Lookup        |
|   6    | Reverse DNS Lookup        |
|   7    | Restart DNS Service       |
|   8    | Exit                      |
+--------+---------------------------+
```

### 1 — List DNS Records
Displays all directives currently in `/etc/resolv.conf` as a formatted table.

```
+------------+-----------------+
| Keyword    | Value           |
+------------+-----------------+
| nameserver | 8.8.8.8         |
| nameserver | 8.8.4.4         |
| search     | example.com     |
+------------+-----------------+
```

### 2 — Add DNS Record
Prompts for a keyword (e.g. `nameserver`, `search`, `domain`) and a value, then appends the new directive. Duplicate entries are rejected.

### 3 — Update DNS Record
Shows the current configuration, then prompts for the keyword, the old value, and the new value to replace it with.

### 4 — Delete DNS Record
Shows the current configuration, prompts for the entry to remove, and requires `y` confirmation before deleting.

### 5 — Forward DNS Lookup
Resolves a hostname to its IP address(es), showing both IPv4 and IPv6 results.

```
Forward lookup: google.com
+--------+------------------------------------------+
| Family | IP Address                               |
+--------+------------------------------------------+
| IPv4   | 142.251.210.78                           |
+--------+------------------------------------------+
```

### 6 — Reverse DNS Lookup
Resolves an IP address back to its hostname using a PTR record query.

```
Reverse lookup: 8.8.8.8 -> dns.google
```

### 7 — Restart DNS Service
Prompts for confirmation, then runs `sudo systemctl restart NetworkManager`.

### 8 — Exit
If any changes were made during the session, offers to restart the DNS service before exiting.

## Command-line Arguments

| Argument | Default | Description |
|---|---|---|
| `--resolv-conf PATH` | `/etc/resolv.conf` | Path to the DNS config file |
| `--service STR` | `NetworkManager` | DNS service name to restart |
| `--logfile STR` | `/var/log/dnsupdate.log` | Log file path |
| `--no-backup` | off | Skip automatic backup before changes |
| `--verbose` / `-v` | off | Enable DEBUG logging |
| `--version` | — | Print version and exit |

## Backups

Before every write operation (add, update, delete), a timestamped backup of `/etc/resolv.conf` is created automatically:

```
/etc/resolv.conf.20260507_143022.bak
```

Pass `--no-backup` to skip this step (a WARNING is logged when skipped).

## Logging

Logs are written to both the terminal and `/var/log/dnsupdate.log`. If the script lacks permission to write to that path, it falls back to `~/dnsupdate.log`.

Log format:
```
[2026-05-07 14:30:22,415] [INFO] Wrote changes to /etc/resolv.conf
[2026-05-07 14:30:22,416] [INFO] Backup created: /etc/resolv.conf.20260507_143022.bak
```

## Exit Codes

| Code | Meaning |
|---|---|
| `0` | Success or clean exit (including Ctrl+C) |
| `1` | Startup error (file not found, permission denied) |
| `2` | Unexpected runtime error |
