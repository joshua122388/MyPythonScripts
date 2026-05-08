#!/usr/bin/env python3

#Log Analyzer tool that opens up a log file in linux and allows to filter by date and events and format the event entered in a json format.


import logging
import re
import json
import zipfile
from datetime import datetime
from pathlib import Path

#logging setup
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("loganalyzer.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def show_menu():
    print("+------+---------------------------+")
    print("| Option | Function                |")
    print("+--------+-------------------------+")
    print("|   1    | Log Analyzer Tool       |")
    print("|   2    | Log Collector           |")
    print("|   3    | Exit                    |")
    print("+--------+-------------------------+")

def logAction():
    print("+------+---------------------------+")
    print("| Option | Function                |")
    print("+--------+-------------------------+")
    print("|   1    | Sort by Date            |")
    print("|   2    | Sort by Event           |")
    print("|   3    | Exit                    |")
    print("+--------+-------------------------+")

def main():
    while True:
        show_menu()
        choice = input("Select an option (1-3): ").strip()

        if choice == "1":
            logReview()
        elif choice == "2":
            logCollector()
        elif choice == "3":
            print("Exiting. Goodbye!")
            break
        else:
            print("Invalid option. Please enter a number between 1 and 3.")

DATE_PATTERN = re.compile(r'(\d{1,4})[/\-](\d{1,2})[/\-](\d{1,4})')


def detect_date_format(lines):
    for line in lines:
        m = DATE_PATTERN.search(line)
        if not m:
            continue
        a, c = m.group(1), m.group(3)
        if len(a) == 4:
            return "%Y/%m/%d" if "/" in m.group(0) else "%Y-%m-%d"
        if len(c) == 4:
            sep = "/" if "/" in m.group(0) else "-"
            first_vals = [int(DATE_PATTERN.search(l).group(1))
                          for l in lines if DATE_PATTERN.search(l)]
            second_vals = [int(DATE_PATTERN.search(l).group(2))
                           for l in lines if DATE_PATTERN.search(l)]
            if any(v > 12 for v in first_vals):
                logger.info("Detected date format: dd/mm/yyyy")
                return f"%d{sep}%m{sep}%Y"
            if any(v > 12 for v in second_vals):
                logger.info("Detected date format: mm/dd/yyyy")
                return f"%m{sep}%d{sep}%Y"
            logger.warning("Ambiguous date format — defaulting to mm/dd/yyyy")
            return f"%m{sep}%d{sep}%Y"
    logger.warning("No recognisable date pattern found in log lines")
    return "%m/%d/%Y"


def parse_log_lines(lines, date_format):
    entries = []
    for line in lines:
        line = line.rstrip()
        if not line:
            continue
        m = DATE_PATTERN.search(line)
        if not m:
            logger.warning("No date found in line: %s", line)
            entries.append({"date": None, "message": line, "parsed_date": None})
            continue
        date_str = m.group(0)
        try:
            parsed_date = datetime.strptime(date_str, date_format)
        except ValueError:
            logger.warning("Could not parse date '%s' with format '%s'", date_str, date_format)
            parsed_date = None
        message = line[m.end():].strip()
        entries.append({"date": date_str, "message": message, "parsed_date": parsed_date})
    return entries


def sort_by_date(log_entries):
    return sorted(log_entries, key=lambda e: (e["parsed_date"] is None, e["parsed_date"]))


def sort_by_event(log_entries):
    def event_key(e):
        token = re.split(r'[\s:]', e["message"])[0].lower() if e["message"] else ""
        return (token, e["parsed_date"] is None, e["parsed_date"])
    return sorted(log_entries, key=event_key)


def to_json(sorted_entries):
    output = [{"date": e["date"], "message": e["message"]} for e in sorted_entries]
    return json.dumps(output, indent=4)


#create a function that iterates recursively through /var/log until finding the log the user wants to review

def logReview():
    baseLogDir = "/var/log"

    while True:
        logFile = input("what log file would you like to review? (eg: sshd.log, firewalld.log): ")
        if not logFile.strip():
            logger.error("the value entered is empty, please try again!")
            continue
        if logFile.strip().isnumeric():
            logger.error("you entered a number, please try again!")
            continue
        break

    logger.info("searching for %s", logFile)

    found = False
    for match in Path(baseLogDir).rglob(logFile):
        found = True
        absolutePath = match.resolve()
        print(f"log file {logFile} is located in {absolutePath}")
        with open(absolutePath, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        date_format = detect_date_format(lines)
        logger.info("Using date format: %s", date_format)
        entries = parse_log_lines(lines, date_format)

        while True:
            logAction()
            action = input("Select a sort option (1-3): ").strip()
            if action == "1":
                logger.info("Sorting by date")
                print(to_json(sort_by_date(entries)))
            elif action == "2":
                logger.info("Sorting by event")
                print(to_json(sort_by_event(entries)))
            elif action == "3":
                break
            else:
                print("Invalid option. Please enter 1, 2, or 3.")

    if not found:
        logger.error("Log file '%s' not found under %s", logFile, baseLogDir)

#create a function to collect logs from /var/log while preserving their directory structure
#then .zip the logs into a .zip file

def logCollector():
    baseLogDir = Path("/var/log")
    outputZip = Path("collected_logs.zip")

    if not baseLogDir.exists():
        logger.error("Log directory %s does not exist", baseLogDir)
        return

    logger.info("Starting log collection from %s", baseLogDir)

    collected = 0
    skipped = 0

    with zipfile.ZipFile(outputZip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for logFile in baseLogDir.rglob("*"):
            if not logFile.is_file():
                continue
            # Preserve directory structure inside the zip (relative to /var/log)
            arcname = logFile.relative_to(baseLogDir.parent)
            try:
                zf.write(logFile, arcname)
                logger.info("Added: %s", arcname)
                collected += 1
            except PermissionError:
                logger.warning("Permission denied, skipping: %s", logFile)
                skipped += 1
            except OSError as e:
                logger.warning("Could not read %s: %s", logFile, e)
                skipped += 1

    print(f"Collection complete: {collected} files added, {skipped} skipped.")
    print(f"Archive saved to: {outputZip.resolve()}")
    logger.info("Log collection finished — %d collected, %d skipped", collected, skipped)


if __name__ == "__main__":
    main()