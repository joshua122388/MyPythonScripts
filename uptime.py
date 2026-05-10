"""
Script that monitors server uptime and prompts an administrator for approval
before rebooting if uptime exceeds a configurable threshold. All events are
logged to both a file and the terminal throughout the process.
"""

import subprocess
import logging
import argparse
import sys


# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

def setup_logging(logfile: str) -> None:
    """Configure root logger with a file handler and a console handler."""
    log_format = "[%(asctime)s] [%(levelname)s] %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Write all log events to the specified file on disk so there is a
    # persistent audit trail even after the terminal session ends.
    file_handler = logging.FileHandler(logfile)
    file_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))

    # Echo the same events to the terminal so the operator can follow along
    # in real time without having to tail the log file separately.
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


# ---------------------------------------------------------------------------
# Uptime retrieval
# ---------------------------------------------------------------------------

def get_uptime_days() -> float:
    """Run `uptime -p` and return the server uptime as a float number of days.

    `uptime -p` is used instead of plain `uptime` because the -p flag produces
    a structured, human-readable string (e.g. "up 3 days, 5 hours") that is
    straightforward to parse, whereas plain `uptime` includes load averages and
    current time in a format that varies across distributions.

    Returns:
        Total uptime in days (hours are converted to a fractional day).

    Raises:
        RuntimeError: If the command fails or the output cannot be parsed.
    """
    result = subprocess.run(
        ["uptime", "-p"],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"'uptime -p' exited with code {result.returncode}: {result.stderr.strip()}"
        )

    raw = result.stdout.strip()
    logging.info(f"uptime output: '{raw}'")

    # The output starts with "up " followed by optional "X days" and/or
    # "Y hours" and/or "Z minutes".  We pull days and hours out separately
    # so that, for example, "up 1 day, 12 hours" becomes 1.5 days.
    import re
    # Search for a number followed by "day" or "days" in the uptime string.
    # The \s+ matches the space between the number and the word.
    days_match = re.search(r"(\d+)\s+day", raw)
    # Search for a number followed by "hour" or "hours" in the uptime string.
    # This is captured separately so hours can be converted to a fractional day.
    hours_match = re.search(r"(\d+)\s+hour", raw)

    days = int(days_match.group(1)) if days_match else 0
    hours = int(hours_match.group(1)) if hours_match else 0

    if not days_match and not hours_match:
        # If neither days nor hours appear the server has been up for only
        # minutes, which is well below any reasonable threshold.
        logging.info("Uptime is less than one hour; treating as 0 days.")
        return 0.0

    total_days = days + hours / 24.0
    logging.info(f"Parsed uptime: {days} day(s), {hours} hour(s) → {total_days:.4f} days total")
    return total_days


# ---------------------------------------------------------------------------
# Threshold check and administrator prompt
# ---------------------------------------------------------------------------

def check_and_prompt_reboot(uptime_days: float, threshold_days: float) -> None:
    """Compare uptime against the threshold and prompt the admin if exceeded.

    Args:
        uptime_days:    Current server uptime expressed as a float number of days.
        threshold_days: The configured maximum uptime before a reboot is suggested.
    """
    if uptime_days < threshold_days:
        # Uptime is within acceptable limits; nothing to do.
        logging.info(
            f"Uptime ({uptime_days:.2f} days) is below threshold ({threshold_days} days). "
            "No action required."
        )
        return

    # Log the breach before doing anything else so the event is recorded even
    # if the administrator's terminal session is later interrupted.
    logging.warning(
        f"Uptime ({uptime_days:.2f} days) has exceeded the threshold ({threshold_days} days)."
    )

    # The prompt is intentionally explicit so the administrator understands
    # exactly what will happen before typing anything.  Defaulting to 'N'
    # (capital N in the "[y/N]" convention) means an accidental Enter press
    # will NOT trigger a reboot — the safer default.
    answer = input(
        f"\nUptime is {uptime_days:.2f} days. Threshold is {threshold_days} days.\n"
        "Reboot the server? [y/N]: "
    ).strip()

    if answer.lower() == "y":
        logging.info("Administrator approved the reboot.")
        logging.info("Initiating reboot...")
        # `sudo reboot` is used rather than calling the reboot syscall
        # directly so that the standard sudoers policy applies and the action
        # is subject to the system's normal privilege controls.
        subprocess.run(["sudo", "reboot"])
    else:
        # Any input other than 'y'/'Y' — including an empty Enter — is
        # treated as a decline so that accidents do not cause unintended
        # reboots.
        logging.info("Administrator declined the reboot. No action taken.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Monitor server uptime and prompt for a reboot when a threshold is exceeded."
    )
    parser.add_argument(
        "-t", "--threshold",
        type=float,
        default=30,
        metavar="DAYS",
        help="Uptime threshold in days before prompting for a reboot (default: 30).",
    )
    parser.add_argument(
        "-l", "--logfile",
        default="/var/log/uptime_reboot.log",
        metavar="PATH",
        help="Path to the log file (default: /var/log/uptime_reboot.log).",
    )
    args = parser.parse_args()

    setup_logging(args.logfile)
    logging.info("Uptime reboot monitor started.")
    logging.info(f"Threshold: {args.threshold} day(s) | Log file: {args.logfile}")

    try:
        uptime_days = get_uptime_days()
        check_and_prompt_reboot(uptime_days, args.threshold)
    except RuntimeError as exc:
        # A RuntimeError here means we could not read the uptime reliably;
        # log the reason and exit with a non-zero code so any calling
        # automation (cron, systemd timer) can detect the failure.
        logging.error(f"Failed to retrieve uptime: {exc}")
        sys.exit(1)
    except Exception as exc:
        # Catch-all for unexpected exceptions so they are always recorded in
        # the log file rather than silently disappearing.
        logging.exception(f"Unexpected error: {exc}")
        sys.exit(1)

    logging.info("Uptime reboot monitor finished.")


if __name__ == "__main__":
    main()
