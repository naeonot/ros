import os
import sys
import json
from pathlib import Path

from rich.console import Console
from rich.table import Table

from core.banner import show_banner
from core.system import get_system_info

console = Console()
CONFIG = Path.home() / ".config/ran-os/config.json"

def get_color():
    try:
        return json.loads(CONFIG.read_text()).get("color", "#00ffff")
    except (OSError, ValueError):
        return "#00ffff"

def create_dashboard():
    info = get_system_info()
    color = get_color()
    width = console.size.width

    if width < 64:
        table = Table(
            title=f"[bold {color}]SYSTEM INFORMATION[/]",
            border_style=color,
            expand=True,
            show_header=False,
            show_edge=True,
            pad_edge=False
        )
        table.add_column("DETAILS", overflow="fold", ratio=1)
        for key, value in info.items():
            table.add_row(f"[bold {color}]{key}[/]\n{value}")
    else:
        table = Table(
            title=f"[bold {color}]SYSTEM INFORMATION[/]",
            border_style=color,
            expand=True
        )
        table.add_column("PROPERTY", style=color, ratio=1, overflow="fold")
        table.add_column("VALUE", style="white", ratio=2, overflow="fold")
        for key, value in info.items():
            table.add_row(str(key), str(value))
    return table

def main():
    if "--append" not in sys.argv:
        os.system("clear")
    show_banner()
    color = get_color()
    console.print(
        f"[bold green]● SYSTEM ONLINE[/bold green]  "
        f"[dim]ROS Environment Loaded[/dim]"
    )
    console.print(create_dashboard())

if __name__ == "__main__":
    main()
