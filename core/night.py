import json
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

CONFIG = Path.home() / ".config/ran-os/config.json"
NEON = "#00ff9c"
console = Console()

def load_config():
    try:
        return json.loads(CONFIG.read_text())
    except (OSError, ValueError):
        return {}

def save_config(data):
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text(json.dumps(data, indent=2) + "\n")

def run_night(args):
    data = load_config()
    action = args[0] if args else "on"

    if action in ("status", "info"):
        active = bool(data.get("night_mode"))
        console.print(Panel(
            "[bold #00ff9c]ACTIVE — CYBERPUNK THEME[/]" if active else "[dim]OFF — normal theme[/]",
            title="ROS NIGHT MODE",
            border_style=NEON if active else "grey50"
        ))
        return

    if action in ("off", "disable"):
        if data.get("night_mode"):
            data["color"] = data.pop("night_previous_color", "#00ffff")
            data["night_mode"] = False
            save_config(data)
            console.print("[bold #00ff9c]Night mode disabled.[/] Previous theme restored.")
        else:
            console.print("[dim]Night mode is already off.[/]")
        return

    if action not in ("on", "enable"):
        console.print("[yellow]Usage: ros night [on|off|status][/]")
        return

    if not data.get("night_mode"):
        data["night_previous_color"] = data.get("color", "#00ffff")
    data["night_mode"] = True
    data["color"] = NEON
    save_config(data)

    console.print(Panel(
        Text("N I G H T   M O D E   E N G A G E D", style="bold #00ff9c", justify="center"),
        subtitle="[dim]ROS // CYBERPUNK TERMINAL THEME[/]",
        border_style=NEON,
        padding=(1, 2)
    ))
    console.print("[#00ff9c]Neon palette loaded. Run 'ros' to view the dashboard.[/]")
