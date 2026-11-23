#!/usr/bin/env python
"""Read-only health checks for the ROS Termux environment."""

import importlib.util
import json
import os
import shutil
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

console = Console()
ROOT = Path(__file__).resolve().parent.parent
CONFIG = Path.home() / ".config/rana-os/config.json"

REQUIRED_FILES = (
    "ros_cli.py",
    "main.py",
    "core/banner.py",
    "core/system.py",
    "core/weather.py",
    "core/night.py",
    "core/cyberlab.py",
    "core/dungeon_terminal.py",
    "core/typing_test.py",
    "core/connect.py",
    "core/desk.py",
    "core/nexus.py",
    "core/system_watch.py",
    "core/downloader.py",
    "core/oracle.py",
)


def run(args=None):
    args = [str(arg).lower() for arg in (args or [])]
    if args:
        if args in (["-h"], ["--help"], ["help"]):
            console.print("Usage: ros doctor [OPTION]")
            console.print("Run read-only checks on the ROS installation.")
            console.print("Options: -h, --help  Show this help")
            return 0
        console.print("[red]ros doctor: unsupported option[/]")
        console.print("Try 'ros doctor --help' for usage.")
        return 2

    checks = []

    def add(status, name, detail):
        checks.append((status, name, detail))

    add(
        "PASS" if sys.version_info >= (3, 9) else "WARN",
        "Python",
        sys.version.split()[0],
    )

    is_termux = "com.termux" in os.environ.get("PREFIX", "")
    add(
        "PASS" if is_termux else "WARN",
        "Termux environment",
        "Detected" if is_termux else "Termux PREFIX not detected",
    )

    for relative in REQUIRED_FILES:
        exists = (ROOT / relative).is_file()
        add("PASS" if exists else "FAIL", f"File: {relative}",
            "Present" if exists else "Missing")

    try:
        rich_available = importlib.util.find_spec("rich") is not None
    except (ImportError, ValueError):
        rich_available = False
    add(
        "PASS" if rich_available else "FAIL",
        "Dependency: rich",
        "Available" if rich_available else "Not installed",
    )

    for module in ("yt_dlp",):
        try:
            available = importlib.util.find_spec(module) is not None
        except (ImportError, ValueError):
            available = False
        add("PASS" if available else "WARN", f"Dependency: {module}",
            "Available" if available else "Not installed; downloader media extraction is limited")

    ffmpeg = shutil.which("ffmpeg")
    add("PASS" if ffmpeg else "WARN", "Dependency: ffmpeg",
        ffmpeg if ffmpeg else "Not found; media conversion/merging may be unavailable")

    oracle_config = Path.home() / ".config/rana-os/oracle.json"
    if oracle_config.exists():
        try:
            oracle_data = json.loads(oracle_config.read_text(encoding="utf-8"))
            valid_oracle = isinstance(oracle_data, dict)
            add("PASS" if valid_oracle else "FAIL", "ORACLE config",
                "Valid JSON object" if valid_oracle else "Expected a JSON object")
            if valid_oracle:
                model = str(oracle_data.get("model", ""))
                model_ok = bool(model and model not in ("1", "2", "3", "4", "5"))
                add("PASS" if model_ok else "WARN", "ORACLE model",
                    model if model_ok else "Model setting looks invalid; run ros oracle model MODEL_ID")
                mode = oracle_config.stat().st_mode & 0o777
                secure = (mode & 0o077) == 0
                add("PASS" if secure else "WARN", "ORACLE key-file permissions",
                    oct(mode) if secure else f"{oct(mode)}; recommend chmod 600 {oracle_config}")
        except (OSError, UnicodeError, json.JSONDecodeError):
            add("FAIL", "ORACLE config", "Cannot read valid JSON")
    else:
        add("WARN", "ORACLE config", "Not configured yet")

    if CONFIG.exists():
        try:
            config_data = json.loads(CONFIG.read_text(encoding="utf-8"))
            valid_config = isinstance(config_data, dict)
            add(
                "PASS" if valid_config else "FAIL",
                "Configuration",
                "Valid JSON object" if valid_config else "Expected a JSON object",
            )
        except (OSError, UnicodeError, json.JSONDecodeError):
            add("FAIL", "Configuration", "Cannot read valid JSON")
    else:
        add("WARN", "Configuration", "Not created yet; defaults may be used")

    launcher = shutil.which("ros")
    if launcher:
        add("PASS", "ROS launcher", launcher)
    else:
        add("WARN", "ROS launcher", "Command 'ros' not found in PATH")

    table = Table(title="ROS DOCTOR", expand=True)
    table.add_column("STATUS", no_wrap=True)
    table.add_column("CHECK")
    table.add_column("DETAIL", overflow="fold")
    for status, name, detail in checks:
        style = {"PASS": "green", "WARN": "yellow", "FAIL": "red"}[status]
        table.add_row(f"[{style}]{status}[/{style}]", name, detail)

    console.print(table)

    passed = sum(status == "PASS" for status, _, _ in checks)
    warnings = sum(status == "WARN" for status, _, _ in checks)
    failed = sum(status == "FAIL" for status, _, _ in checks)
    console.print(
        f"Summary: [green]{passed} passed[/], "
        f"[yellow]{warnings} warnings[/], [red]{failed} failed[/]"
    )

    if failed:
        console.print("[red]ROS needs attention. Review the failed checks above.[/]")
        return 1
    if warnings:
        console.print("[yellow]ROS is usable, but review the warnings above.[/]")
        return 0
    console.print("[green]ROS environment looks healthy.[/]")
    return 0
