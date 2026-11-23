#!/usr/bin/env python
"""Display non-sensitive ROS and runtime environment information."""

import importlib.util
import os
import platform
import shutil
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

console = Console()
ROOT = Path(__file__).resolve().parent.parent
ROS_VERSION = "development (release version not configured)"

MODULE_FILES = {
    "Weather": "weather.py",
    "Night mode": "night.py",
    "Cyber Lab": "cyberlab.py",
    "Terminal Dungeon": "dungeon_terminal.py",
    "Typing Test": "typing_test.py",
    "Connect": "connect.py",
    "Doctor": "doctor.py",
    "System Watch": "system_watch.py",
    "Daily Desk": "desk.py",
    "NEXUS": "nexus.py",
    "Download Manager": "downloader.py",
    "ORACLE": "oracle.py",
}


def run(args=None):
    args = [str(arg).lower() for arg in (args or [])]
    if args:
        if args in (["help"], ["-h"], ["--help"]):
            console.print("Usage: ros info [OPTION]")
            console.print("Show ROS installation and runtime information.")
            console.print("Options: -h, --help  Show this help")
            return 0
        console.print("[red]ros info: unsupported option[/]")
        console.print("Try 'ros info --help' for usage.")
        return 2

    table = Table(title="ROS INFO", expand=True)
    table.add_column("PROPERTY", style="cyan", no_wrap=True)
    table.add_column("VALUE", overflow="fold")

    prefix = os.environ.get("PREFIX", "")
    termux = "Detected" if "com.termux" in prefix else "Not detected"
    launcher = shutil.which("ros") or "Not found in PATH"
    rich_available = importlib.util.find_spec("rich") is not None

    rows = (
        ("ROS version", ROS_VERSION),
        ("Project path", str(ROOT)),
        ("Python", sys.version.split()[0]),
        ("Python implementation", platform.python_implementation()),
        ("Platform", platform.platform()),
        ("Termux", termux),
        ("ROS launcher", launcher),
        ("Rich dependency", "Available" if rich_available else "Missing"),
    )
    for name, value in rows:
        table.add_row(name, value)

    console.print(table)

    modules = Table(title="ROS MODULES", expand=True)
    modules.add_column("MODULE", style="cyan")
    modules.add_column("STATUS", no_wrap=True)
    for name, filename in MODULE_FILES.items():
        present = (ROOT / "core" / filename).is_file()
        modules.add_row(name, "[green]Available[/]" if present else "[red]Missing[/]")
    console.print(modules)
    return 0
