#!/usr/bin/env python3
"""
healthmon.py — System Health Monitor
Usage:
    healthmon.py <config.json>          Run checks; write alerts to logs + syslog
    healthmon.py <config.json> --check  Run checks + emit a summary report via logging
"""

import argparse
import json
import logging
import logging.handlers
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

import psutil


# ─── Data Structures ──────────────────────────────────────────────────────────

@dataclass
class CheckResult:
    name: str
    value: float | str
    threshold: float | str | None
    status: str          # "OK" | "WARNING" | "CRITICAL"
    message: str
    unit: str = ""


@dataclass
class HealthReport:
    timestamp: datetime = field(default_factory=datetime.now)
    results: list[CheckResult] = field(default_factory=list)

    @property
    def has_alerts(self) -> bool:
        return any(r.status != "OK" for r in self.results)

    @property
    def alert_results(self) -> list[CheckResult]:
        return [r for r in self.results if r.status != "OK"]


# ─── Logging Setup ────────────────────────────────────────────────────────────

class _SilentSysLogHandler(logging.handlers.SysLogHandler):
    """SysLogHandler that silently drops records when the socket is unavailable."""
    def handleError(self, record: logging.LogRecord) -> None:
        pass


def _detect_syslog() -> Optional[str]:
    """Return the first available syslog socket path, or None."""
    for candidate in ("/dev/log", "/var/run/syslog", "/var/run/log"):
        if os.path.exists(candidate):
            return candidate
    return None


def setup_logging(
    log_file: str,
    alert_log: str,
    console: bool = False,
) -> tuple[logging.Logger, logging.Logger]:
    """
    Build and return (main_logger, alert_logger).

    Sink layout
    ───────────
    main_logger (healthmon)           DEBUG+
      ├── RotatingFileHandler  → log_file        (all levels, 5 MB × 3)
      └── StreamHandler        → stdout          (INFO+, only when --check)

    alert_logger (healthmon.alerts)   WARNING+   propagates → main_logger
      ├── RotatingFileHandler  → alert_log       (WARNING+, 2 MB × 5)
      └── _SilentSysLogHandler → /dev/log        (WARNING+, LOG_DAEMON)
    """
    # ── Formatters ──────────────────────────────────────────────────────────
    file_fmt = logging.Formatter(
        fmt="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    console_fmt = logging.Formatter("%(message)s")   # clean for --check output
    syslog_fmt  = logging.Formatter(
        "healthmon[%(process)d]: %(levelname)s %(message)s"
    )

    # ── Main logger ─────────────────────────────────────────────────────────
    main = logging.getLogger("healthmon")
    main.setLevel(logging.DEBUG)
    main.handlers.clear()

    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    main_fh = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=3
    )
    main_fh.setLevel(logging.DEBUG)
    main_fh.setFormatter(file_fmt)
    main.addHandler(main_fh)

    if console:
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        ch.setFormatter(console_fmt)
        main.addHandler(ch)

    # ── Alert logger ────────────────────────────────────────────────────────
    alert = logging.getLogger("healthmon.alerts")
    alert.setLevel(logging.WARNING)
    alert.propagate = True          # WARNING+ also flows through to log_file

    Path(alert_log).parent.mkdir(parents=True, exist_ok=True)
    alert_fh = logging.handlers.RotatingFileHandler(
        alert_log, maxBytes=2 * 1024 * 1024, backupCount=5
    )
    alert_fh.setLevel(logging.WARNING)
    alert_fh.setFormatter(file_fmt)
    alert.addHandler(alert_fh)

    syslog_addr = _detect_syslog()
    if syslog_addr:
        try:
            sl = _SilentSysLogHandler(
                address=syslog_addr,
                facility=logging.handlers.SysLogHandler.LOG_DAEMON,
            )
            sl.setLevel(logging.WARNING)
            sl.setFormatter(syslog_fmt)
            alert.addHandler(sl)
        except OSError as exc:
            main.warning("syslog attach failed (%s) — skipping syslog alerts.", exc)
    else:
        main.warning("No syslog socket found — skipping syslog alerts.")

    return main, alert


# ─── Config Loading ───────────────────────────────────────────────────────────

_REQUIRED_CHECKS = {"disk_usage_percent", "memory_usage_percent",
                    "cpu_load_1min", "services"}

def load_config(path: str) -> dict:
    with open(path) as fh:
        cfg = json.load(fh)

    missing_top = {"checks", "log_file", "alert_log"} - cfg.keys()
    if missing_top:
        raise ValueError(f"Config missing top-level keys: {missing_top}")

    missing_checks = _REQUIRED_CHECKS - cfg["checks"].keys()
    if missing_checks:
        raise ValueError(f"Config missing checks keys: {missing_checks}")

    if not isinstance(cfg["checks"]["services"], list):
        raise ValueError("checks.services must be a JSON array of service names.")

    return cfg


# ─── Individual Checks ────────────────────────────────────────────────────────

def check_disk(threshold: float) -> CheckResult:
    usage = psutil.disk_usage("/")
    pct      = usage.percent
    free_gb  = usage.free / (1024 ** 3)
    total_gb = usage.total / (1024 ** 3)
    status   = "CRITICAL" if pct >= threshold else "OK"
    msg = (
        f"Disk  {pct:.1f}% used  ({free_gb:.1f} GB free of {total_gb:.1f} GB)  "
        f"threshold={threshold}%"
    )
    return CheckResult("disk_usage_percent", pct, threshold, status, msg, unit="%")


def check_memory(threshold: float) -> CheckResult:
    mem      = psutil.virtual_memory()
    pct      = mem.percent
    avail_gb = mem.available / (1024 ** 3)
    total_gb = mem.total    / (1024 ** 3)
    status   = "CRITICAL" if pct >= threshold else "OK"
    msg = (
        f"Memory  {pct:.1f}% used  ({avail_gb:.1f} GB available of {total_gb:.1f} GB)  "
        f"threshold={threshold}%"
    )
    return CheckResult("memory_usage_percent", pct, threshold, status, msg, unit="%")


def check_cpu_load(threshold: float) -> CheckResult:
    load_1, load_5, load_15 = os.getloadavg()
    cpu_count  = psutil.cpu_count(logical=True) or 1
    normalised = load_1 / cpu_count
    status     = "WARNING" if load_1 >= threshold else "OK"
    msg = (
        f"CPU load  1m={load_1:.2f}  5m={load_5:.2f}  15m={load_15:.2f}  "
        f"({normalised:.2f}/core, {cpu_count} cores)  threshold={threshold}"
    )
    return CheckResult("cpu_load_1min", load_1, threshold, status, msg)


def _service_active(name: str) -> bool:
    """Return True if the named service is running (systemd → SysV fallback)."""
    if shutil.which("systemctl"):
        return subprocess.run(
            ["systemctl", "is-active", "--quiet", name],
            capture_output=True,
        ).returncode == 0
    if shutil.which("service"):
        return subprocess.run(
            ["service", name, "status"],
            capture_output=True,
        ).returncode == 0
    return False


def check_services(services: list[str]) -> list[CheckResult]:
    results = []
    for svc in services:
        active = _service_active(svc)
        status = "OK" if active else "CRITICAL"
        state  = "active" if active else "INACTIVE / NOT FOUND"
        msg    = f"Service '{svc}'  {state}"
        results.append(
            CheckResult(f"service:{svc}", "active" if active else "inactive",
                        "active", status, msg)
        )
    return results


# ─── Check Runner ─────────────────────────────────────────────────────────────

def _emit(result: CheckResult,
          log: logging.Logger,
          alert: logging.Logger) -> None:
    """Write one result to the main log; escalate alerts to the alert logger."""
    prefix = f"[{result.status:<8}]"
    if result.status == "OK":
        log.info("%s %s", prefix, result.message)
    elif result.status == "WARNING":
        log.warning("%s %s", prefix, result.message)
        alert.warning("THRESHOLD BREACH  %s — %s", result.name, result.message)
    else:  # CRITICAL
        log.critical("%s %s", prefix, result.message)
        alert.critical("THRESHOLD BREACH  %s — %s", result.name, result.message)


def run_checks(cfg: dict,
               log: logging.Logger,
               alert: logging.Logger) -> HealthReport:
    checks = cfg["checks"]
    report = HealthReport()

    log.info("=== health check started ===")

    for fn, key in [
        (lambda: check_disk(checks["disk_usage_percent"]),     "disk_usage_percent"),
        (lambda: check_memory(checks["memory_usage_percent"]), "memory_usage_percent"),
        (lambda: check_cpu_load(checks["cpu_load_1min"]),      "cpu_load_1min"),
    ]:
        r = fn()
        report.results.append(r)
        _emit(r, log, alert)

    for r in check_services(checks["services"]):
        report.results.append(r)
        _emit(r, log, alert)

    if report.has_alerts:
        alert.warning(
            "=== health check complete — %d alert(s) raised ===",
            len(report.alert_results),
        )
    else:
        log.info("=== health check complete — all checks OK ===")

    return report


# ─── Summary Report (via logging, no print) ───────────────────────────────────

_ICON = {"OK": "[OK]      ", "WARNING": "[WARNING] ", "CRITICAL": "[CRITICAL]"}
_W    = 70   # inner width of the box


def _box_line(text: str = "", fill: str = " ") -> str:
    return f"║ {text:{fill}<{_W - 2}} ║"


def emit_summary(report: HealthReport,
                 cfg: dict,
                 log: logging.Logger) -> None:
    """Render the summary report entirely through log.info()."""
    border_top = "╔" + "═" * (_W) + "╗"
    border_mid = "╠" + "═" * (_W) + "╣"
    border_bot = "╚" + "═" * (_W) + "╝"

    log.info(border_top)
    log.info(_box_line(f"  SYSTEM HEALTH REPORT"))
    log.info(_box_line(f"  {report.timestamp.strftime('%A %d %B %Y  %H:%M:%S')}"))
    log.info(_box_line(f"  Config : {cfg.get('_config_path', 'N/A')}"))
    log.info(_box_line(f"  Log    : {cfg['log_file']}"))
    log.info(_box_line(f"  Alerts : {cfg['alert_log']}"))
    log.info(border_mid)

    # Column header
    log.info(_box_line(f"  {'CHECK':<28}  {'VALUE':<14}  {'STATUS':<10}  THRESHOLD"))
    log.info(_box_line("", fill="─"))

    for r in report.results:
        icon   = _ICON.get(r.status, "?")
        val    = f"{r.value:.1f}{r.unit}" if isinstance(r.value, float) else str(r.value)
        thr    = f"{r.threshold}{r.unit}" if r.threshold is not None else "—"
        line   = f"  {icon} {r.name:<28}  {val:<14}  {r.status:<10}  {thr}"
        log.info(_box_line(line))

    log.info(border_mid)

    if report.has_alerts:
        log.info(_box_line("  ⚠  ALERTS RAISED"))
        for r in report.alert_results:
            msg_line = f"  → {r.message}"
            # wrap long messages to box width
            for chunk in [msg_line[i:i+(_W-4)]
                          for i in range(0, len(msg_line), _W - 4)]:
                log.info(_box_line(f"  {chunk}"))
    else:
        log.info(_box_line("  ✓  All checks passed — system is healthy"))

    log.info(border_bot)


# ─── Entry Point ──────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        prog="healthmon.py",
        description="System health monitor — all output via Python logging.",
    )
    parser.add_argument("config", help="Path to JSON config file")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Also emit a formatted summary report via logging",
    )
    args = parser.parse_args()

    # ── Load config first (before loggers exist) ────────────────────────────
    try:
        cfg = load_config(args.config)
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as exc:
        sys.stderr.write(f"ERROR: could not load config '{args.config}': {exc}\n")
        return 2

    cfg["_config_path"] = str(Path(args.config).resolve())   # stash for report

    # ── Build loggers ───────────────────────────────────────────────────────
    log, alert = setup_logging(
        log_file  = cfg["log_file"],
        alert_log = cfg["alert_log"],
        console   = args.check,          # attach stdout handler only for --check
    )

    log.debug("Config loaded from %s", cfg["_config_path"])

    # ── Run checks ──────────────────────────────────────────────────────────
    try:
        report = run_checks(cfg, log, alert)
    except Exception as exc:
        log.exception("Unexpected error during health checks: %s", exc)
        return 1

    # ── Optional summary ────────────────────────────────────────────────────
    if args.check:
        emit_summary(report, cfg, log)

    return 1 if report.has_alerts else 0


if __name__ == "__main__":
    sys.exit(main())
