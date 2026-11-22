import os
import json
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from core.banner import show_banner
from core.system import get_system_info

console = Console()
CONFIG = Path.home() / ".config/rana-os/config.json"

def get_color():
    try:
        return json.loads(CONFIG.read_text()).get("color", "#00ffff")
    except (OSError, ValueError):
        return "#00ffff"

def create_dashboard():
    info = get_system_info()
    color = get_color()

    table = Table(
        title=f"[bold {color}]SYSTEM INFORMATION[/]",
        border_style=color,
        expand=True
    )

    table.add_column("PROPERTY", style=color)
    table.add_column("VALUE", style="white")

    for key, value in info.items():
        table.add_row(key, str(value))

    return table

def main():
    os.system("clear")
    show_banner()
    color = get_color()

    console.print(
        Panel(
            "[bold green]● SYSTEM ONLINE[/bold green]   "
            "[dim]RANA OS Environment Loaded[/dim]",
            border_style=color
        )
    )
    console.print(create_dashboard())

if __name__ == "__main__":
    main()
