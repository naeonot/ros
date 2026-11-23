#!/usr/bin/env python
"""List available ROS commands, grouped by purpose."""

from rich.console import Console
from rich.table import Table

console = Console()

COMMAND_GROUPS = (
    ("CORE SYSTEMS", (
        ("ros oracle", "ORACLE — AI assistant and model settings"),
        ("ros download", "DOWNLOAD — supported media and file downloads"),
        ("ros desk", "DESK — tasks, focus timer, notes and habits"),
        ("ros watch", "SYSTEM — live device monitoring"),
        ("ros config", "SYSTEM — manage ROS configuration"),
        ("ros doctor", "SYSTEM — run installation health checks"),
        ("ros info", "SYSTEM — show ROS and runtime information"),
        ("ros update", "SYSTEM — check configured update source"),
        ("ros core", "Open the central menu for all four core systems"),
    )),
    ("OTHER TOOLS", (
        ("ros weather", "Show current weather and forecast"),
        ("ros forecast", "Show the 5-day forecast"),
        ("ros theme", "Open the theme picker"),
        ("ros night", "Enable night theme (ros night off to restore)"),
        ("ros nexus", "Open ROS NEXUS command center"),
        ("ros lab", "Open the Cyber Lab learning menu"),
        ("ros matrix", "Start Matrix rain visual"),
        ("ros fire", "Start fire simulation"),
        ("ros dungeon", "Play the terminal dungeon game"),
        ("ros tt", "Open the typing test (alias: ros typing)"),
        ("ros connect", "Open ROS Connect chat (alias: ros chat)"),
        ("ros main", "Customize the main banner"),
        ("ros new", "Open a fresh ROS screen"),
        ("ros list", "List commands by category"),
        ("ros help", "Show full command help"),
        ("ros version", "Show ROS version"),
        ("ros about", "About the ROS project"),
    )),
)


def run(args=None):
    args = [str(arg).lower() for arg in (args or [])]
    if args:
        if args in (["help"], ["-h"], ["--help"]):
            console.print("Usage: ros list [OPTION]")
            console.print("List available ROS commands by category.")
            console.print("Options: -h, --help  Show this help")
            return 0
        console.print("[red]ros list: unsupported option[/]")
        console.print("Try 'ros list --help' for usage.")
        return 2

    console.print("[bold cyan]ROS COMMAND DIRECTORY[/]")
    console.print("[dim]Commands currently available in this installation.[/]")
    for category, commands in COMMAND_GROUPS:
        table = Table(title=category, expand=True, show_lines=False)
        table.add_column("COMMAND", style="cyan", no_wrap=True)
        table.add_column("DESCRIPTION", overflow="fold")
        for command, description in commands:
            table.add_row(command, description)
        console.print(table)
    console.print("[dim]Use 'ros help' for detailed syntax and options.[/]")
    return 0
