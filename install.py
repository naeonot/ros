#!/usr/bin/env python3
"""Install the complete ROS project into ~/rana-os on Termux."""
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

SOURCE = Path(__file__).resolve().parent
APP = Path.home() / "rana-os"
PREFIX = Path(os.environ.get("PREFIX", "/data/data/com.termux/files/usr"))
BIN = PREFIX / "bin"
CONFIG_DIR = Path.home() / ".config" / "rana-os"
CONFIG_FILE = CONFIG_DIR / "config.json"
REPOSITORY = "https://github.com/naeonot/ros"


def installed_revision():
    revision = os.environ.get("ROS_INSTALL_COMMIT", "").strip()
    if not re.fullmatch(r"[0-9a-fA-F]{40}", revision):
        try:
            result = subprocess.run(
                ["git", "-C", str(SOURCE), "rev-parse", "HEAD"],
                check=True, capture_output=True, text=True,
            )
            revision = result.stdout.strip()
        except (OSError, subprocess.CalledProcessError):
            revision = ""
    return revision if re.fullmatch(r"[0-9a-fA-F]{40}", revision) else ""


def configure_updates():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    try:
        config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        if not isinstance(config, dict):
            raise ValueError("ROS config must be a JSON object")
    except FileNotFoundError:
        config = {}

    config.setdefault("update_repo", REPOSITORY)
    revision = installed_revision()
    if revision:
        config["installed_commit"] = revision.lower()

    temporary = CONFIG_FILE.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(config, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.chmod(0o600)
    temporary.replace(CONFIG_FILE)
    CONFIG_DIR.chmod(0o700)


def personalize_logo():
    """Ask for a local ASCII-art logo name after installation."""
    if not sys.stdin.isatty():
        print("Interactive logo setup skipped (no terminal input).")
        return

    print("\nPERSONALIZE YOUR ROS LOGO")
    print("Enter a name to turn it into your local ASCII-art logo.")
    print("Leave it blank to keep the default RAN-OS logo.")

    try:
        name = input("Logo name (up to 12 characters): ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nLogo personalization skipped.")
        return

    if not name:
        print("Default RAN-OS logo kept.")
        return
    if len(name) > 12:
        print("Name is too long (maximum 12 characters). Default logo kept.")
        return
    if not all(ch.isalnum() or ch.isspace() or ch in "-_." for ch in name):
        print("Use letters, numbers, spaces, hyphens, underscores or periods only.")
        print("Default logo kept.")
        return

    try:
        config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        if not isinstance(config, dict):
            raise ValueError("ROS config must be a JSON object")
    except FileNotFoundError:
        config = {}

    config["main_logo"] = name.upper()
    temporary = CONFIG_FILE.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(config, indent=2, ensure_ascii=False) + "\\n",
        encoding="utf-8",
    )
    temporary.chmod(0o600)
    temporary.replace(CONFIG_FILE)
    CONFIG_DIR.chmod(0o700)
    print(f"Personal ASCII-art logo saved locally: {name.upper()}")


def main():
    if "com.termux" not in str(PREFIX):
        print("This installer is designed for Termux.")
        return 1

    subprocess.check_call([
        sys.executable, "-m", "pip", "install", "-r",
        str(SOURCE / "requirements.txt")
    ])

    APP.mkdir(parents=True, exist_ok=True)
    files = json.loads(
        (SOURCE / "ros_manifest.json").read_text(encoding="utf-8")
    )["files"]

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

    configure_updates()
    print("ROS installed successfully.")
    personalize_logo()
    print("Run: ros")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
