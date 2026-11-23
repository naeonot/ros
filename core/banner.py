import json
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from rich.text import Text

console = Console()
CONFIG = Path.home() / ".config/ran-os/config.json"

def get_settings():
    try:
        return json.loads(CONFIG.read_text())
    except (OSError, ValueError):
        return {}

def show_banner():
    settings = get_settings()
    color = settings.get("color", "#00ffff")
    display_name = settings.get("main_name", "ROS")
    display_text = settings.get("main_text", "PERSONAL TERMINAL ENVIRONMENT")
    width = console.size.width

    # A manual logo override wins; otherwise use the install-time choice.
    # Fresh installs and older configs without either key default to RAN-OS.
    custom_logo = settings.get("main_logo") or settings.get("install_logo") or "RAN-OS"
    try:
        from pyfiglet import Figlet
        art = "\n" + Figlet(font="ansi_shadow", width=120).renderText(custom_logo).rstrip("\n")
    except ImportError:
        art = custom_logo.upper()

    if width < 54:
        content = Align.center(Text(display_name, style=f"bold {color}"))
    else:
        content = Align.center(Text(art, style=f"bold {color}"))

    console.print(
        Panel(
            content,
            title=f"[bold {color}]{display_name}[/]",
            subtitle=f"[{color}]{display_text}[/]",
            border_style=color,
            padding=(0, 1 if width < 54 else 2),
            expand=True
        )
    )

[executed on device: localhost (34059f63-7af7-4f50-89c5-e6d1ecbd6567)]