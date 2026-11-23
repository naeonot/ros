#!/usr/bin/env python3
"""Install the complete ROS project into ~/rana-os on Termux."""
import os
import shutil
import subprocess
import sys
import json
from pathlib import Path

SOURCE = Path(__file__).resolve().parent
APP = Path.home() / "rana-os"
PREFIX = Path(os.environ.get("PREFIX", "/data/data/com.termux/files/usr"))
BIN = PREFIX / "bin"

def main():
    if "com.termux" not in str(PREFIX):
        print("This installer is designed for Termux.")
        return 1
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(SOURCE / "requirements.txt")])
    APP.mkdir(parents=True, exist_ok=True)
    files = json.loads((SOURCE / "ros_manifest.json").read_text(encoding="utf-8"))["files"]
    for name in files:
        source = (SOURCE / name).resolve()
        if SOURCE.resolve() not in source.parents or not source.is_file():
            raise RuntimeError("Unsafe or missing project file: " + name)
        target = APP / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    BIN.mkdir(parents=True, exist_ok=True)
    launcher = BIN / "ros"
    launcher.write_text(
        "#!/data/data/com.termux/files/usr/bin/bash\n"
        + 'exec "' + sys.executable + '" "' + str(APP / "ros_cli.py") + '" "$@"\n',
        encoding="utf-8",
    )
    launcher.chmod(0o755)
    print("ROS installed successfully.")
    print("Run: ros")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
