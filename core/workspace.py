#!/usr/bin/env python
"""Central menu for ROS's four practical core systems."""

import subprocess
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
CLI = Path(__file__).resolve().parent.parent / "ros_cli.py"

CORE = {
    "1": ("ORACLE", "AI assistant and model settings", "oracle"),
    "2": ("DOWNLOAD", "Supported media and file downloads", "download"),
    "3": ("DESK", "Tasks, focus timer, notes and habits", "desk"),
}
SYSTEM = {
    "1": ("WATCH", "Live device telemetry", "watch"),
    "2": ("CONFIG", "ROS configuration manager", "config"),
    "3": ("DOCTOR", "Installation health checks", "doctor"),
    "4": ("INFO", "ROS and runtime information", "info"),
    "5": ("UPDATE", "Check configured update source", "update"),
}


def launch(command, extra=()):
    return subprocess.run(
        [sys.executable, str(CLI), command, *extra],
        check=False,
    ).returncode


def show_core():
    table = Table(show_header=True, header_style="bold green", expand=True)
    table.add_column("KEY", width=5, justify="center")
    table.add_column("CORE SYSTEM", style="bold white")
    table.add_column("PURPOSE")
    for key, (name, description, _) in CORE.items():
        table.add_row(key, name, description)
    table.add_row("4", "SYSTEM", "Monitoring, configuration, diagnostics and updates")
    table.add_row("5", "OTHER TOOLS", "Weather, Cyber Lab, games, themes and utilities")
    table.add_row("Q", "EXIT", "Return to the terminal")
    console.print(Panel(table, title="[bold green]ROS CORE SYSTEMS[/]", border_style="green"))
    console.print("[dim]Choose a core system. Existing standalone commands still work.[/]")


def show_system():
    table = Table(show_header=True, header_style="bold green", expand=True)
    table.add_column("KEY", width=5, justify="center")
    table.add_column("SYSTEM TOOL", style="bold white")
    table.add_column("PURPOSE")
    for key, (name, description, _) in SYSTEM.items():
        table.add_row(key, name, description)
    table.add_row("B", "BACK", "Return to Core Systems")
    console.print(Panel(table, title="[bold green]ROS SYSTEM[/]", border_style="green"))


def run(args=None):
    args = [str(x).lower() for x in (args or [])]
    if args and args[0] in ("-h", "--help", "help"):
        console.print("Usage: ros core [oracle|download|desk|system|watch|config|doctor|info|update]", markup=False)
        console.print("Run 'ros core' to open the central menu.")
        return 0

    aliases = {
        "oracle": "oracle", "ai": "oracle",
        "download": "download", "files": "download",
        "desk": "desk", "system": "system",
        "watch": "watch", "config": "config", "doctor": "doctor",
        "info": "info", "update": "update",
    }
    if args:
        target = aliases.get(args[0])
        if target is None:
            console.print("[red]Unknown core system/tool.[/] Use 'ros core --help'.")
            return 2
        if target == "system":
            args = ["system"]
        else:
            return launch(target, args[1:])

    if not sys.stdin.isatty():
        show_core()
        console.print("Interactive menu requires a terminal. Try 'ros core --help'.")
        return 0

    while True:
        show_core()
        try:
            choice = input("\nROS CORE > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Leaving ROS Core.[/]")
            return 0
        if choice in ("q", "quit", "exit", ""):
            return 0
        if choice in CORE:
            launch(CORE[choice][2])
        elif choice == "4":
            while True:
                show_system()
                try:
                    sub = input("\nROS SYSTEM > ").strip().lower()
                except (EOFError, KeyboardInterrupt):
                    break
                if sub in ("b", "back", "q", ""):
                    break
                if sub in SYSTEM:
                    launch(SYSTEM[sub][2])
                else:
                    console.print("[yellow]Choose 1–5 or B.[/]")
        elif choice == "5":
            launch("list")
        else:
            console.print("[yellow]Choose 1–5 or Q.[/]")
