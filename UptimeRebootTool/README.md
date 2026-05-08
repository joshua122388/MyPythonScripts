# Uptime Auto-Reboot Tool

A Linux command-line script that monitors server uptime and prompts an administrator for approval before rebooting if uptime exceeds a configurable threshold. All events are logged to both a file and the terminal.

---

## Requirements

- Linux (uses the `uptime -p` command)
- Python 3.6+
- `sudo` privileges to execute the reboot command

No third-party packages are required — only Python standard library modules are used.

---

## Usage

```bash
python uptime.py [OPTIONS]
```

### Options

| Flag | Long form | Default | Description |
|------|-----------|---------|-------------|
| `-t` | `--threshold` | `30` | Uptime in days before prompting for a reboot |
| `-l` | `--logfile` | `/var/log/uptime_reboot.log` | Path to the log file |

### Examples

```bash
# Run with defaults (prompts if uptime exceeds 30 days)
python uptime.py

# Prompt if uptime exceeds 7 days
python uptime.py --threshold 7

# Use a custom log file location
python uptime.py --logfile /home/admin/uptime.log

# Combine both options
python uptime.py --threshold 14 --logfile /home/admin/uptime.log

# Force the prompt immediately (useful for testing)
python uptime.py --threshold 0
```

---

## How It Works

1. Runs `uptime -p` to get the current server uptime.
2. Parses the output to calculate total uptime in days (hours are converted to a fractional day).
3. Compares uptime against the configured threshold.
4. If the threshold is **not** exceeded, logs the result and exits cleanly.
5. If the threshold **is** exceeded, prints a prompt asking the administrator whether to reboot.
   - Type `y` and press Enter to approve the reboot.
   - Press Enter or type anything else to decline — no reboot will occur.
6. All events (uptime value, threshold check result, administrator decision) are written to both the terminal and the log file.

---

## Log Output

Events are logged in the following format:

```
[YYYY-MM-DD HH:MM:SS] [LEVEL] message
```

Example log entries:

```
[2026-05-07 09:00:00] [INFO] Uptime reboot monitor started.
[2026-05-07 09:00:00] [INFO] Threshold: 30.0 day(s) | Log file: /var/log/uptime_reboot.log
[2026-05-07 09:00:00] [INFO] uptime output: 'up 35 days, 4 hours'
[2026-05-07 09:00:00] [INFO] Parsed uptime: 35 day(s), 4 hour(s) -> 35.1667 days total
[2026-05-07 09:00:00] [WARNING] Uptime (35.17 days) has exceeded the threshold (30.0 days).
[2026-05-07 09:00:05] [INFO] Administrator approved the reboot.
[2026-05-07 09:00:05] [INFO] Initiating reboot...
```

> **Note:** The default log path `/var/log/uptime_reboot.log` requires root or sudo write permissions. Use `--logfile` to specify a writable path if needed.

---

## Scheduling with Cron (Monthly)

To have this script run automatically once a month on Linux, add it to your crontab.

### Step 1 — Open the crontab editor

```bash
crontab -e
```

### Step 2 — Add the cron entry

Paste the following line at the bottom of the file:

```cron
# Run on the 1st of every month at 9:00 AM
0 9 1 * * /usr/bin/python3 /path/to/uptime.py --threshold 30 --logfile /var/log/uptime_reboot.log
```

Replace `/path/to/uptime.py` with the actual absolute path to the script.

### Cron field reference

```
.------------ minute (0-59)
|  .--------- hour (0-23)
|  |  .------ day of month (1-31)
|  |  |  .--- month (1-12)
|  |  |  |  . day of week (0-7, where 0 and 7 = Sunday)
|  |  |  |  |
0  9  1  *  *   command
```

### Step 3 — Save and exit

- If using `nano`: press `Ctrl+O`, then `Enter`, then `Ctrl+X`.
- If using `vim`: type `:wq` and press `Enter`.

Cron will automatically pick up the new entry — no restart needed.

### Step 4 — Verify the cron job was saved

```bash
crontab -l
```

### Important notes for cron usage

- **Cron runs without a terminal**, so the administrator prompt will not be visible. For unattended use, consider modifying the script to send the prompt via email or a notification service instead.
- Make sure the script is executable: `chmod +x /path/to/uptime.py`
- Use the full path to the Python interpreter (find it with `which python3`).
- Ensure the user running the cron job has `sudo` privileges for the `reboot` command, or configure `/etc/sudoers` accordingly.
