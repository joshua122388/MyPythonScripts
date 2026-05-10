"""
Script description: python script that run on linux that assists on updating the DNS records. the script must update the DNS records in the corresponding configuration file, then restart the DNS service if required. the script must use logging to show the tasks being performed at the moment to the user. The script must also be able to handle exceptions properly
"""

#!/usr/bin/env python3

# ─── Standard Library Imports ────────────────────────────────────────────────
import os
import sys
import shutil
import socket
import logging
import argparse
import subprocess
from datetime import datetime
from pathlib import Path

# ─── Constants ───────────────────────────────────────────────────────────────
VERSION = "1.0.0"
RESOLV_CONF = "/etc/resolv.conf"
DNS_SERVICE = "NetworkManager"
LOG_FILE = "/var/log/dnsupdate.log"

# ─── Logging Setup ───────────────────────────────────────────────────────────
logger = logging.getLogger(__name__)


def setup_logging(logfile: str) -> None:
    fmt = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")

    try:
        file_handler = logging.FileHandler(logfile)
    except PermissionError:
        fallback = os.path.expanduser("~/dnsupdate.log")
        file_handler = logging.FileHandler(fallback)
        print(f"No write permission to {logfile}, logging to {fallback}")

    file_handler.setFormatter(fmt)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(fmt)

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(file_handler)
    root.addHandler(stream_handler)


# ─── resolv.conf Functions ────────────────────────────────────────────────────

def read_resolv_conf(path: str) -> list:
    """Read /etc/resolv.conf and return its lines."""
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    return lines


def write_resolv_conf(lines: list, path: str) -> None:
    """Write lines back to /etc/resolv.conf."""
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    logger.info("Wrote changes to %s", path)


def backup_resolv_conf(path: str) -> str:
    """Create a timestamped backup of resolv.conf."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{path}.{ts}.bak"
    shutil.copy2(path, backup_path)
    logger.info("Backup created: %s", backup_path)
    return backup_path


def parse_dns_entries(lines: list) -> list:
    """Return a list of (line_index, keyword, value) for each DNS directive."""
    entries = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("#") or not stripped:
            continue
        parts = stripped.split(None, 1)
        if len(parts) == 2:
            keyword, value = parts
            entries.append({"line_index": i, "keyword": keyword, "value": value})
    return entries


# ─── DNS Record Operations ────────────────────────────────────────────────────

def list_dns(lines: list) -> None:
    """Print a formatted table of all entries in resolv.conf."""
    entries = parse_dns_entries(lines)
    if not entries:
        print("  (resolv.conf is empty or has no directives)")
        return

    col_kw  = max(len(e["keyword"]) for e in entries)
    col_kw  = max(col_kw, 7)
    col_val = max(len(e["value"])   for e in entries)
    col_val = max(col_val, 5)

    sep = f"+{'-'*(col_kw+2)}+{'-'*(col_val+2)}+"
    print(sep)
    print(f"| {'Keyword':<{col_kw}} | {'Value':<{col_val}} |")
    print(sep)
    for e in entries:
        print(f"| {e['keyword']:<{col_kw}} | {e['value']:<{col_val}} |")
    print(sep)
    logger.info("Listed %d DNS entries", len(entries))


def add_dns(lines: list, keyword: str, value: str) -> list:
    """Append a new directive to resolv.conf lines."""
    # Duplicate check
    for e in parse_dns_entries(lines):
        if e["keyword"] == keyword and e["value"] == value:
            raise ValueError(f"Entry already exists: {keyword} {value}")

    lines = lines.copy()
    # Ensure file ends with a newline before appending
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"
    lines.append(f"{keyword} {value}\n")
    logger.info("Added entry: %s %s", keyword, value)
    return lines


def update_dns(lines: list, keyword: str, old_value: str, new_value: str) -> list:
    """Replace old_value with new_value for the given keyword."""
    lines = lines.copy()
    for i, line in enumerate(lines):
        stripped = line.strip()
        parts = stripped.split(None, 1)
        if len(parts) == 2 and parts[0] == keyword and parts[1] == old_value:
            # Preserve any leading whitespace/comment style
            lines[i] = f"{keyword} {new_value}\n"
            logger.info("Updated %s: '%s' -> '%s'", keyword, old_value, new_value)
            return lines
    raise ValueError(f"Entry not found: {keyword} {old_value}")


def delete_dns(lines: list, keyword: str, value: str) -> list:
    """Remove a directive line from resolv.conf lines."""
    lines = lines.copy()
    for i, line in enumerate(lines):
        stripped = line.strip()
        parts = stripped.split(None, 1)
        if len(parts) == 2 and parts[0] == keyword and parts[1] == value:
            lines.pop(i)
            logger.info("Deleted entry: %s %s", keyword, value)
            return lines
    raise ValueError(f"Entry not found: {keyword} {value}")


# ─── DNS Lookup ───────────────────────────────────────────────────────────────

def resolve_forward(hostname: str) -> list:
    """Resolve a hostname to one or more IP addresses."""
    results = socket.getaddrinfo(hostname, None)
    # getaddrinfo returns (family, type, proto, canonname, sockaddr)
    # sockaddr is (address, port) for IPv4 or (address, port, flow, scope) for IPv6
    seen = []
    for item in results:
        ip = item[4][0]
        family = "IPv6" if item[0] == socket.AF_INET6 else "IPv4"
        entry = (family, ip)
        if entry not in seen:
            seen.append(entry)
    return seen


def resolve_reverse(ip: str) -> str:
    """Resolve an IP address to its hostname."""
    hostname, _, _ = socket.gethostbyaddr(ip)
    return hostname


# ─── System Integration ───────────────────────────────────────────────────────

def restart_dns_service(service_name: str) -> bool:
    """Restart the DNS service via systemctl."""
    try:
        result = subprocess.run(
            ["sudo", "systemctl", "restart", service_name],
            capture_output=True, text=True, check=False,
        )
        if result.returncode == 0:
            logger.info("Service '%s' restarted successfully.", service_name)
            print(f"Service '{service_name}' restarted successfully.")
            return True
        else:
            msg = (result.stderr or result.stdout).strip()
            logger.error("Failed to restart '%s': %s", service_name, msg)
            print(f"Failed to restart '{service_name}': {msg}")
            return False
    except FileNotFoundError:
        logger.warning("systemctl not found — cannot restart service")
        print("systemctl is not available on this system.")
        return False


# ─── Interactive Menu ─────────────────────────────────────────────────────────

def show_main_menu() -> None:
    print()
    print("+--------+---------------------------+")
    print("| Option | Function                  |")
    print("+--------+---------------------------+")
    print("|   1    | List DNS Records          |")
    print("|   2    | Add DNS Record            |")
    print("|   3    | Update DNS Record         |")
    print("|   4    | Delete DNS Record         |")
    print("|   5    | Forward DNS Lookup        |")
    print("|   6    | Reverse DNS Lookup        |")
    print("|   7    | Restart DNS Service       |")
    print("|   8    | Exit                      |")
    print("+--------+---------------------------+")


def handle_list(lines: list) -> None:
    print(f"\nDNS configuration ({RESOLV_CONF}):")
    list_dns(lines)


def handle_add(lines: list, args) -> list:
    keyword = input("Enter directive keyword (e.g. nameserver, search, domain): ").strip()
    value   = input("Enter value (e.g. 8.8.8.8): ").strip()

    if not keyword or not value:
        print("Keyword and value are required.")
        return lines

    try:
        if not args.no_backup:
            backup_resolv_conf(args.resolv_conf)
        else:
            logger.warning("Backup skipped (--no-backup flag set)")

        lines = add_dns(lines, keyword, value)
        write_resolv_conf(lines, args.resolv_conf)
        print(f"Added: {keyword} {value}")
        return lines
    except PermissionError:
        logger.error("Permission denied writing %s", args.resolv_conf)
        print("Permission denied. Try running as root.")
        return lines
    except ValueError as e:
        logger.error("Add failed: %s", e)
        print(f"Error: {e}")
        return lines


def handle_update(lines: list, args) -> list:
    print(f"\nCurrent DNS configuration ({RESOLV_CONF}):")
    list_dns(lines)

    keyword   = input("Enter directive keyword to update (e.g. nameserver): ").strip()
    old_value = input("Enter current value (old): ").strip()
    new_value = input("Enter new value: ").strip()

    if not keyword or not old_value or not new_value:
        print("Keyword, old value, and new value are required.")
        return lines

    try:
        if not args.no_backup:
            backup_resolv_conf(args.resolv_conf)
        else:
            logger.warning("Backup skipped (--no-backup flag set)")

        lines = update_dns(lines, keyword, old_value, new_value)
        write_resolv_conf(lines, args.resolv_conf)
        print(f"Updated: {keyword} '{old_value}' -> '{new_value}'")
        return lines
    except PermissionError:
        logger.error("Permission denied writing %s", args.resolv_conf)
        print("Permission denied. Try running as root.")
        return lines
    except ValueError as e:
        logger.error("Update failed: %s", e)
        print(f"Error: {e}")
        return lines


def handle_delete(lines: list, args) -> list:
    print(f"\nCurrent DNS configuration ({RESOLV_CONF}):")
    list_dns(lines)

    keyword = input("Enter directive keyword to delete (e.g. nameserver): ").strip()
    value   = input("Enter value to delete (e.g. 8.8.8.8): ").strip()

    if not keyword or not value:
        print("Keyword and value are required.")
        return lines

    confirm = input(f"Delete '{keyword} {value}'? [y/N]: ").strip().lower()
    if confirm != "y":
        print("Cancelled.")
        return lines

    try:
        if not args.no_backup:
            backup_resolv_conf(args.resolv_conf)
        else:
            logger.warning("Backup skipped (--no-backup flag set)")

        lines = delete_dns(lines, keyword, value)
        write_resolv_conf(lines, args.resolv_conf)
        print(f"Deleted: {keyword} {value}")
        return lines
    except PermissionError:
        logger.error("Permission denied writing %s", args.resolv_conf)
        print("Permission denied. Try running as root.")
        return lines
    except ValueError as e:
        logger.error("Delete failed: %s", e)
        print(f"Error: {e}")
        return lines


def handle_forward_lookup() -> None:
    hostname = input("Enter hostname to resolve (e.g. google.com): ").strip()
    if not hostname:
        print("Hostname is required.")
        return
    try:
        results = resolve_forward(hostname)
        print(f"\nForward lookup: {hostname}")
        print(f"+--------+{'─'*40}+")
        print(f"| {'Family':<6} | {'IP Address':<38} |")
        print(f"+--------+{'─'*40}+")
        for family, ip in results:
            print(f"| {family:<6} | {ip:<38} |")
        print(f"+--------+{'─'*40}+")
        logger.info("Forward lookup '%s': %d result(s)", hostname, len(results))
    except socket.gaierror as e:
        logger.error("Forward lookup failed for '%s': %s", hostname, e)
        print(f"Could not resolve '{hostname}': {e}")


def handle_reverse_lookup() -> None:
    ip = input("Enter IP address to resolve (e.g. 8.8.8.8): ").strip()
    if not ip:
        print("IP address is required.")
        return
    try:
        hostname = resolve_reverse(ip)
        print(f"\nReverse lookup: {ip} -> {hostname}")
        logger.info("Reverse lookup '%s': %s", ip, hostname)
    except socket.herror as e:
        logger.error("Reverse lookup failed for '%s': %s", ip, e)
        print(f"Could not resolve '{ip}': {e}")
    except socket.gaierror as e:
        logger.error("Reverse lookup failed for '%s': %s", ip, e)
        print(f"Could not resolve '{ip}': {e}")


def handle_restart(service_name: str) -> None:
    confirm = input(f"Restart DNS service '{service_name}'? [y/N]: ").strip().lower()
    if confirm != "y":
        print("Cancelled.")
        return
    restart_dns_service(service_name)


# ─── Argument Parsing ─────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="DNS record management tool for /etc/resolv.conf.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--resolv-conf", metavar="PATH", default=RESOLV_CONF,
                        help="Path to the DNS config file")
    parser.add_argument("--service",     metavar="STR",  default=DNS_SERVICE,
                        help="DNS service name to restart")
    parser.add_argument("--logfile",     metavar="STR",  default=LOG_FILE,
                        help="Log file path")
    parser.add_argument("--no-backup",   action="store_true",
                        help="Skip automatic backup before changes (logged as WARNING)")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Enable DEBUG logging")
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    return parser.parse_args()


# ─── Entry Point ──────────────────────────────────────────────────────────────

def main() -> int:
    args = parse_args()
    setup_logging(args.logfile)

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose/debug logging enabled.")

    logger.info("dnsupdate.py v%s starting", VERSION)

    try:
        lines = read_resolv_conf(args.resolv_conf)
    except FileNotFoundError:
        logger.error("DNS config file not found: %s", args.resolv_conf)
        print(f"Error: {args.resolv_conf} not found.")
        return 1
    except PermissionError:
        logger.error("Permission denied reading %s", args.resolv_conf)
        print(f"Permission denied: {args.resolv_conf}. Try running as root.")
        return 1

    changes_made = False

    try:
        while True:
            show_main_menu()
            choice = input("Select an option (1-8): ").strip()

            if choice == "1":
                handle_list(lines)

            elif choice == "2":
                new_lines = handle_add(lines, args)
                if new_lines is not lines:
                    lines = new_lines
                    changes_made = True

            elif choice == "3":
                new_lines = handle_update(lines, args)
                if new_lines is not lines:
                    lines = new_lines
                    changes_made = True

            elif choice == "4":
                new_lines = handle_delete(lines, args)
                if new_lines is not lines:
                    lines = new_lines
                    changes_made = True

            elif choice == "5":
                handle_forward_lookup()

            elif choice == "6":
                handle_reverse_lookup()

            elif choice == "7":
                handle_restart(args.service)

            elif choice == "8":
                if changes_made:
                    restart = input(
                        f"Changes were made. Restart '{args.service}' now? [y/N]: "
                    ).strip().lower()
                    if restart == "y":
                        restart_dns_service(args.service)
                print("Exiting. Goodbye!")
                logger.info("dnsupdate.py exiting normally.")
                break

            else:
                print("Invalid option. Please enter a number between 1 and 8.")

    except KeyboardInterrupt:
        print("\nInterrupted.")
        logger.info("dnsupdate.py interrupted by user.")
        return 0

    except Exception as e:
        logger.exception("Unexpected error: %s", e)
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
