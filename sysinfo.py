#!/usr/bin/env python3
"""
#!/usr/bin/python3
#sysinfo.py - Collect system information from a Linux/AWS machine.
#Usage: sysinfo.py <screen | csv | json>
# YijunLu-20260607: 1.5
"""
# ── Imports ────────────────────────────────────────────────────────────────────

import sys
import os
import csv
import json
import socket
import struct
import fcntl
import platform
import subprocess
from datetime import timedelta


# ── Helpers ────────────────────────────────────────────────────────────────────

def _run(cmd: list[str], default: str = "N/A") -> str:
    """Run a shell command and return stripped stdout, or default on failure."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        return result.stdout.strip() if result.returncode == 0 else default
    except Exception:
        return default


def _read(path: str, default: str = "N/A") -> str:
    """Read the first line of a file, or return default."""
    try:
        with open(path) as fh:
            return fh.readline().strip()
    except OSError:
        return default


# ──  Functions ──────────────────────────────────────────────────────────────────

def get_hostname() -> str:
    return socket.gethostname()


def get_os_info() -> str:
    info = platform.freedesktop_os_release() if hasattr(platform, "freedesktop_os_release") else {}
    pretty = info.get("PRETTY_NAME", "")
    if pretty:
        return pretty
    # Fallback: /etc/os-release
    for line in _run(["cat", "/etc/os-release"]).splitlines():
        if line.startswith("PRETTY_NAME="):
            return line.split("=", 1)[1].strip().strip('"')
    return platform.platform()


def get_cpu_info() -> str:
    model = "N/A"
    cores = "N/A"
    try:
        with open("/proc/cpuinfo") as fh:
            for line in fh:
                if line.startswith("model name"):
                    model = line.split(":", 1)[1].strip()
                    break
        with open("/proc/cpuinfo") as fh:
            cores = str(sum(1 for l in fh if l.startswith("processor")))
    except OSError:
        pass
    return f"{model}, {cores} core(s)"


def get_memory() -> str:
    try:
        mem = {}
        with open("/proc/meminfo") as fh:
            for line in fh:
                parts = line.split()
                if parts[0] in ("MemTotal:", "MemAvailable:"):
                    mem[parts[0]] = int(parts[1])  # kB
        total_gb = mem.get("MemTotal:", 0) / (1024 ** 2)
        avail_gb = mem.get("MemAvailable:", 0) / (1024 ** 2)
        used_gb  = total_gb - avail_gb
        return f"Total: {total_gb:.1f} GB  Used: {used_gb:.1f} GB  Available: {avail_gb:.1f} GB"
    except (OSError, KeyError, ValueError):
        return "N/A"


def get_disk() -> str:
    try:
        st = os.statvfs("/")
        total_gb = (st.f_blocks * st.f_frsize) / (1024 ** 3)
        free_gb  = (st.f_bavail * st.f_frsize) / (1024 ** 3)
        used_gb  = total_gb - free_gb
        pct_used = (used_gb / total_gb * 100) if total_gb else 0
        return (f"Total: {total_gb:.1f} GB  Used: {used_gb:.1f} GB  "
                f"Free: {free_gb:.1f} GB  ({pct_used:.1f}% used)")
    except OSError:
        return "N/A"


def _get_default_iface() -> str:
    """Return the interface used for the default route."""
    route = _run(["ip", "route", "show", "default"])
    # e.g. "default via 10.0.0.1 dev eth0 ..."
    for part in route.split():
        if part not in ("default", "via", "dev", "proto", "src", "metric",
                        "onlink", "scope", "link") and "." not in part:
            idx = route.split().index(part)
            if idx > 0 and route.split()[idx - 1] == "dev":
                return part
    # Fallback: first non-loopback interface
    try:
        with open("/proc/net/if_inet6") as _:
            pass
    except OSError:
        pass
    for iface in os.listdir("/sys/class/net"):
        if iface != "lo":
            return iface
    return "eth0"


def get_ip_address() -> str:
    iface = _get_default_iface()
    # Try `hostname -I` first (simple)
    ips = _run(["hostname", "-I"])
    if ips and ips != "N/A":
        return ips.split()[0]
    # Fallback via socket ioctl
    try:
        import socket, fcntl, struct
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(
            fcntl.ioctl(s.fileno(), 0x8915,
                        struct.pack("256s", iface[:15].encode()))[20:24]
        )
    except Exception:
        return "N/A"


def get_mac_address() -> str:
    iface = _get_default_iface()
    mac = _read(f"/sys/class/net/{iface}/address")
    if mac and mac != "N/A":
        return mac
    # Fallback: ip link
    output = _run(["ip", "link", "show", iface])
    for line in output.splitlines():
        line = line.strip()
        if line.startswith("link/ether"):
            return line.split()[1]
    return "N/A"


def get_uptime() -> str:
    try:
        with open("/proc/uptime") as fh:
            seconds = float(fh.read().split()[0])
        delta = timedelta(seconds=int(seconds))
        days    = delta.days
        hours   = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60
        return f"{days}d {hours}h {minutes}m"
    except (OSError, ValueError):
        return "N/A"


# ── Main data builder ──────────────────────────────────────────────────────────

def collect() -> dict:
    """Display name and order to matching functions"""
    return {
        "Hostname":    get_hostname(),
        "OS":          get_os_info(),
        "CPU":         get_cpu_info(),
        "Memory":      get_memory(),
        "Disk (/)":    get_disk(),
        "IP Address":  get_ip_address(),
        "MAC Address": get_mac_address(),
        "Uptime":      get_uptime(),
    }


# ── Output formatters ──────────────────────────────────────────────────────────

def output_screen(data: dict) -> None:
    """Fancy display settings for easy reading"""
    width = 60
    print("=" * width)
    print(f"{'System Information':^{width}}")
    print("=" * width)
    label_w = max(len(k) for k in data) + 1
    for key, value in data.items():
        print(f"  {key:<{label_w}}  {value}")
    print("=" * width)


def output_csv(data: dict, path: str = "sysinfo.csv") -> None:
    """Display settings to ensure each infromation get their own line in a consistant format"""
    with open(path, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["Field", "Value"])
        for key, value in data.items():
            writer.writerow([key, value])
    print(f"CSV written to: {os.path.abspath(path)}")


def output_json(data: dict, path: str = "sysinfo.json") -> None:
    """Display setting for json, nothing special"""
    with open(path, "w") as fh:
        json.dump(data, fh, indent=2)
    print(f"JSON written to: {os.path.abspath(path)}")


# ── Run Main  ────────────────────────────────────────────────────────────────

VALID_FORMATS = ("screen", "csv", "json")

def main() -> None:
    # ── Argument validation ──────────────────────────────────────────────────
    """Error handling for valid and invalid formats"""
    if len(sys.argv) != 2:
        print(
            f"Error: expected exactly 1 argument, got {len(sys.argv) - 1}.\n"
            f"Usage: {os.path.basename(sys.argv[0])} <{'|'.join(VALID_FORMATS)}>"
        )
        sys.exit(1)

    fmt = sys.argv[1].strip().lower()

    if fmt not in VALID_FORMATS:
        print(
            f"Error: '{sys.argv[1]}' is not a valid output format.\n"
            f"Usage: {os.path.basename(sys.argv[0])} <{'|'.join(VALID_FORMATS)}>\n"
            f"  screen  – print results to the terminal\n"
            f"  csv     – write results to sysinfo.csv\n"
            f"  json    – write results to sysinfo.json"
        )
        sys.exit(1)

    # ── Collect & output ─────────────────────────────────────────────────────
    data = collect()

    if fmt == "screen":
        output_screen(data)
    elif fmt == "csv":
        output_csv(data)
    elif fmt == "json":
        output_json(data)


if __name__ == "__main__":
    main()
