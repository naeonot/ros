import json
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from rich.text import Text

console = Console()
CONFIG = Path.home() / ".config/rana-os/config.json"

def get_settings():
    try:
        return json.loads(CONFIG.read_text())
    except (OSError, ValueError):
        return {}

def show_banner():
    settings = get_settings()
    color = settings.get("color", "#00ffff")

    art = r"""
    ██████╗  █████╗ ███╗   ██╗ █████╗
    ██╔══██╗██╔══██╗████╗  ██║██╔══██╗
    ██████╔╝███████║██╔██╗ ██║███████║
    ██╔══██╗██╔══██║██║╚██╗██║██╔══██╗
    ██║  ██║██║  ██║██║ ╚████║██║  ██║
    ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝
    """

    console.print(
        Panel(
            Align.center(Text(art, style=f"bold {color}")),
            title=f"[bold {color}]{'ROS' if settings.get('name', 'ROS').upper() == 'RANA' else settings.get('name', 'ROS').upper()}[/]",
            subtitle=f"[{color}]PERSONAL TERMINAL ENVIRONMENT[/]",
            border_style=color,
            padding=(1, 2)
        )
    )
