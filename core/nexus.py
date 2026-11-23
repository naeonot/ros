#!/usr/bin/env python3
"""ROS NEXUS: a local, read-only cyber command center."""
import os
import sys
import time
import shutil
import platform
import socket
from datetime import datetime
from pathlib import Path

G = "\033[38;5;46m"
DG = "\033[38;5;22m"
C = "\033[38;5;51m"
Y = "\033[38;5;226m"
R = "\033[0m"
B = "\033[1m"
D = "\033[2m"
W = 76


def clear():
    if sys.stdout.isatty():
        print("\033[2J\033[H", end="")


def bar(value, width=18):
    value = max(0, min(100, float(value)))
    n = round(width * value / 100)
    return G + "█" * n + DG + "░" * (width - n) + R


def system_snapshot():
    home = Path.home()
    try:
        usage = shutil.disk_usage(home)
        storage = 100 * usage.used / usage.total
        storage_text = f"{usage.used / 2**30:.1f} / {usage.total / 2**30:.1f} GB"
    except OSError:
        storage, storage_text = 0, "unavailable"
    ram_text, ram_pct = "unavailable", 0
    try:
        from core.system import get_ram_info
        info = get_ram_info()
        if isinstance(info, dict):
            ram_text = str(info.get("used", info.get("total", "available")))
            ram_pct = float(info.get("percent", 0) or 0)
        else:
            ram_text = str(info)
    except Exception:
        pass
    try:
        host = socket.gethostname()
    except OSError:
        host = "local-device"
    return storage, storage_text, ram_text, ram_pct, host


def boot():
    clear()
    print(G + B + r"""
   ███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗
   ████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝
   ██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗
   ██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║
   ██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║
   ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝
""" + R)
    print(C + "  R A N A   O P E R A T I N G   S Y S T E M" + R)
    print(D + "  LOCAL COMMAND CENTER  //  NEXUS INTERFACE" + R)
    print()
    steps = ["Loading local modules", "Checking terminal environment",
             "Reading device telemetry", "Mounting command interface"]
    for step in steps:
        print(f"  {G}[*]{R} {step}...", end="", flush=True)
        time.sleep(0.22)
        print(f" {G}OK{R}")
    print()
    time.sleep(0.25)


def frame():
    storage, storage_text, ram_text, ram_pct, host = system_snapshot()
    now = datetime.now().astimezone().strftime("%Y-%m-%d  %H:%M:%S %Z")
    clear()
    print(G + B + "╔" + "═" * 74 + "╗" + R)
    print(G + B + "║" + R + "  ROS / NEXUS" + C + "                                      " + D + "LOCAL COMMAND CENTER" + R + "  " + G + B + "║" + R)
    print(G + B + "╠" + "═" * 74 + "╣" + R)
    print(G + "║" + R + f"  NODE      {B}{host[:22]:22}{R}  " + f"TIME  {now[:28]:28}" + G + "║" + R)
    print(G + "╠" + "═" * 74 + "╣" + R)
    print(G + "║" + R + "  " + C + B + "DEVICE TELEMETRY" + R + "                                                   " + G + "║" + R)
    print(G + "║" + R + f"  STORAGE   {bar(storage)}  {storage:5.1f}%   {D}{storage_text}{R}" + " " * max(0, 5-len(storage_text)) + G + "║" + R)
    print(G + "║" + R + f"  MEMORY    {ram_text[:52]:52}" + G + "║" + R)
    print(G + "╠" + "═" * 74 + "╣" + R)
    print(G + "║" + R + "  " + C + B + "MODULE STATUS" + R + "                                                       " + G + "║" + R)
    modules = [("CYBER LAB", "ros lab"), ("SYSTEM WATCH", "ros watch"),
               ("DAILY DESK", "ros desk"), ("DUNGEON", "ros dungeon"),
               ("TYPING TEST", "ros tt"), ("WEATHER", "ros weather")]
    for name, command in modules:
        line = f"  {G}●{R} {name:14} {D}{command}{R}"
        print(G + "║" + R + line + " " * 42 + G + "║" + R)
    print(G + "╠" + "═" * 74 + "╣" + R)
    print(G + "║" + R + "  " + C + B + "SIGNAL SCAN" + R + "   " + D + "SIMULATION ONLY · NO NETWORK SCANNING" + R + "              " + G + "║" + R)
    print(G + "║" + R + "  Local environment integrity: " + G + B + "READY" + R + "                                  " + G + "║" + R)
    print(G + "║" + R + "  External connections:        " + Y + "NOT TESTED" + R + "                              " + G + "║" + R)
    print(G + "╠" + "═" * 74 + "╣" + R)
    print(G + "║" + R + "  [1] Run visual signal scan     [2] Refresh telemetry                 " + G + "║" + R)
    print(G + "║" + R + "  [3] Open Cyber Lab             [4] Open System Watch                  " + G + "║" + R)
    print(G + "║" + R + "  [5] Open Daily Desk            [q] Exit                               " + G + "║" + R)
    print(G + B + "╚" + "═" * 74 + "╝" + R)


def signal_scan():
    clear()
    print(G + B + "\n  NEXUS // SIGNAL SCAN" + R)
    print(D + "  This is a visual simulation. It does not inspect networks or devices." + R + "\n")
    stages = ["Initializing local signal map", "Rendering fictional node graph",
              "Checking interface modules", "Closing simulation"]
    for stage in stages:
        print(f"  {G}▸{R} {stage}")
        for n in range(0, 31, 3):
            print(f"\r    {bar(n * 100 / 30, 26)} {n * 100 // 30:3d}%", end="", flush=True)
            time.sleep(0.035)
        print(f"\r    {bar(100, 26)} {G}100%{R}")
    print(f"\n  {G}{B}SIMULATION COMPLETE{R}  //  No external target contacted.")
    input("\n  Press Enter to return to NEXUS...")


def run(argv=None):
    args = list(argv or [])
    if args and args[0] in ("-h", "--help", "help"):
        print("ROS NEXUS\nUsage: ros nexus\nLocal read-only command center with a harmless visual scan simulation.")
        return 0
    boot()
    while True:
        frame()
        choice = input("\n  nexus> ").strip().lower()
        if choice == "q":
            print("\n  NEXUS offline. ROS remains active.")
            return 0
        elif choice == "1":
            signal_scan()
        elif choice == "2":
            continue
        elif choice == "3":
            from core.cyberlab import main
            sys.argv = ["ros-cyberlab", "menu"]
            main()
        elif choice == "4":
            from core.system_watch import run as watch
            watch([])
        elif choice == "5":
            from core.desk import run as desk
            desk([])
        else:
            print("  Select 1-5 or q.")
            time.sleep(0.7)


if __name__ == "__main__":
    raise SystemExit(run(sys.argv[1:]))
