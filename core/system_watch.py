#!/usr/bin/env python3
"""ROS System Watch: live, read-only Android/Termux telemetry."""
import argparse
import json
import os
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path

from rich import box
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from core.system import get_ram_info, get_android_version

GREEN = "#39ff14"


def read_uptime():
    try:
        seconds = float(Path('/proc/uptime').read_text().split()[0])
        days, rem = divmod(int(seconds), 86400)
        hours, rem = divmod(rem, 3600)
        minutes, _ = divmod(rem, 60)
        return f"{days}d {hours:02d}h {minutes:02d}m"
    except (OSError, ValueError, IndexError):
        return "N/A"


def read_battery():
    """Use Termux:API when installed; otherwise show a truthful unavailable state."""
    binary = shutil.which('termux-battery-status')
    if not binary:
        return "Unavailable (Termux:API not installed)", None
    try:
        raw = subprocess.check_output([binary], text=True, timeout=2)
        data = json.loads(raw)
        percent = data.get('percentage')
        status = data.get('status', 'Unknown')
        if percent is None:
            return f"{status} · level unavailable", None
        return f"{percent}% · {status}", int(percent)
    except (OSError, subprocess.SubprocessError, ValueError, TypeError):
        return "Unavailable (API permission/service)", None


def read_cpu_load():
    try:
        values = Path('/proc/loadavg').read_text().split()
        return f"{values[0]}  /  {values[1]}  /  {values[2]}  (1/5/15 min)"
    except (OSError, IndexError):
        return "N/A"


def meter(percent, width=22):
    if percent is None:
        return "[dim]Not available[/]"
    filled = max(0, min(width, round(width * percent / 100)))
    color = GREEN if percent < 75 else "yellow" if percent < 90 else "red"
    return f"[{color}]{'█' * filled}{'░' * (width - filled)}[/] {percent:5.1f}%"


def build_view():
    now = datetime.now().astimezone()
    ram = get_ram_info()
    try:
        usage = shutil.disk_usage(Path.home())
        storage_pct = usage.used / usage.total * 100 if usage.total else None
        storage_free = f"{usage.free / (1024 ** 3):.2f} GB"
        storage_total = f"{usage.total / (1024 ** 3):.2f} GB"
    except OSError:
        storage_pct, storage_free, storage_total = None, "N/A", "N/A"

    try:
        ram_used = float(ram['used'].split()[0])
        ram_total = float(ram['total'].split()[0])
        ram_pct = ram_used / ram_total * 100 if ram_total else None
    except (ValueError, KeyError, IndexError):
        ram_pct = None

    battery_text, battery_pct = read_battery()
    width = max(48, min(90, Console().size.width - 4))

    title = Text()
    title.append("ROS", style=f"bold {GREEN}")
    title.append("  //  SYSTEM WATCH", style="bold white")
    title.append("\nLIVE DEVICE TELEMETRY  •  READ-ONLY", style="dim")

    system = Table.grid(padding=(0, 2))
    system.add_column(style="dim", min_width=17)
    system.add_column(style="bold white")
    system.add_row("DEVICE", "Android / Termux")
    system.add_row("ANDROID", get_android_version())
    system.add_row("HOST", os.environ.get('HOSTNAME', 'Termux device'))
    system.add_row("UPTIME", read_uptime())
    system.add_row("LOCAL TIME", now.strftime('%d %b %Y  %H:%M:%S'))
    system.add_row("CPU LOAD", read_cpu_load())

    resources = Table.grid(padding=(0, 1))
    resources.add_column(min_width=15, style="dim")
    resources.add_column(ratio=1)
    resources.add_row("RAM", meter(ram_pct))
    resources.add_row("RAM USED", f"{ram.get('used', 'N/A')} / {ram.get('total', 'N/A')}")
    resources.add_row("STORAGE", meter(storage_pct))
    resources.add_row("STORAGE", f"{storage_free} free / {storage_total} total")
    resources.add_row("BATTERY", meter(battery_pct))
    resources.add_row("BATTERY INFO", battery_text)

    layout = Table.grid(expand=True)
    layout.add_column(ratio=1)
    layout.add_row(Panel(system, title="DEVICE STATUS", border_style=GREEN, box=box.HEAVY, padding=(1, 2)))
    layout.add_row(Panel(resources, title="RESOURCE MONITOR", border_style=GREEN, box=box.HEAVY, padding=(1, 2)))
    footer = Text("CTRL+C  EXIT     •     REFRESH 1s     •     NO DATA UPLOAD", style="dim", justify="center")
    return Panel(layout, title=title, subtitle=footer, border_style=GREEN, box=box.DOUBLE, width=width, padding=(1, 1))


def run(argv=None):
    parser = argparse.ArgumentParser(prog='ros watch', description='Live read-only device telemetry')
    parser.add_argument('--once', action='store_true', help='print one snapshot and exit')
    parser.add_argument('--interval', type=float, default=1.0, help='refresh interval in seconds (minimum 0.5)')
    args = parser.parse_args(argv)
    console = Console()
    if args.once:
        console.print(build_view())
        return 0
    interval = max(0.5, args.interval)
    try:
        with Live(build_view(), console=console, refresh_per_second=4, screen=True, transient=False) as live:
            while True:
                time.sleep(interval)
                live.update(build_view(), refresh=True)
    except KeyboardInterrupt:
        console.print('\n[bold #39ff14]ROS System Watch stopped.[/]')
    return 0


if __name__ == '__main__':
    raise SystemExit(run())
