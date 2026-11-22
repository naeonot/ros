#!/usr/bin/env python
"""Install RANA OS directly from GitHub on Termux."""
import os
import sys
import shutil
import subprocess
import urllib.request
from pathlib import Path

BASE = "https://raw.githubusercontent.com/naeonot/ros/main/"
FILES = (
    "main.py",
    "setname.py",
    "setcolor.py",
    "core/__init__.py",
    "core/banner.py",
    "core/system.py",
)
HOME = Path.home()
APP = HOME / ".local" / "share" / "rana-os"
PREFIX = Path(os.environ.get("PREFIX", str(HOME / ".local")))
BIN = PREFIX / "bin"

def download(path):
    url = BASE + path
    with urllib.request.urlopen(url, timeout=30) as response:
        return response.read()

def main():
    print("Installing RANA OS...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "rich"])
    for relative in FILES:
        destination = APP / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(download(relative))
    BIN.mkdir(parents=True, exist_ok=True)
    launcher = BIN / "ros"
    launcher.write_text(
        "#!/data/data/com.termux/files/usr/bin/sh\n"
        f'exec "{sys.executable}" "{APP / "main.py"}" "$@"\n'
    )
    launcher.chmod(0o755)
    print("RANA OS installed successfully.")
    print("Run: ros")
    if str(BIN) not in os.environ.get("PATH", "").split(os.pathsep):
        print(f"Add this to PATH if 'ros' is not found: export PATH=\"{BIN}:$PATH\"")

if __name__ == "__main__":
    main()
