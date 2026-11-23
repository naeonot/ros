#!/usr/bin/env python
import argparse
import json
import sys
import subprocess
import shutil
import difflib
import urllib.request
import urllib.error
import urllib.parse
import zipfile
import tempfile
import os
from datetime import datetime
from pathlib import Path

CONFIG = Path.home() / ".config/rana-os/config.json"
MAIN = Path.home() / "rana-os/main.py"
BASH = Path("/data/data/com.termux/files/usr/bin/bash")

COLORS = [
    ("Cyan", "#00ffff"), ("Matrix Green", "#39ff14"), ("Lime", "#00ff00"), ("Magenta", "#ff00aa"),
    ("Blue", "#3388ff"), ("Red", "#ff4444"), ("Yellow", "#ffff00"),
    ("White", "#ffffff"), ("Purple", "#bb66ff"), ("Orange", "#ff8800"),
    ("Pink", "#ff77bb"), ("Green", "#22cc88"), ("Sky Blue", "#55ccff"),
]

def show_version():
    print("ROS version: development (release version not configured)")

UPDATE_DIR = Path.home() / ".cache" / "rana-os" / "updates"
APP_DIR = Path.home() / "rana-os"


def build_update_parser():
    parser = argparse.ArgumentParser(
        prog="ros update",
        description="Check, download and manually install ROS updates.",
        epilog=(
            "Examples:\n"
            "  ros update                 Check GitHub\n"
            "  ros update download        Download update package\n"
            "  ros update install         Install downloaded package\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "action", nargs="?", choices=("check", "download", "install"),
        help="check, download or install a ROS update"
    )
    parser.add_argument("-c", "--check", action="store_true", help="check update source")
    return parser


def _update_repo_details():
    data = load_config()
    repo_url = data.get("update_repo")
    if not repo_url:
        raise ValueError("Update source is not configured. Set update_repo in ROS config.")
    parsed = urllib.parse.urlparse(str(repo_url).strip())
    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if parsed.scheme != "https" or parsed.netloc.lower() != "github.com" or len(parts) != 2:
        raise ValueError("Invalid GitHub URL. Expected https://github.com/OWNER/REPO")
    owner, repo = parts
    if repo.endswith(".git"):
        repo = repo[:-4]
    branch = str(data.get("update_branch", "main")).strip() or "main"
    return owner, repo, branch, data


def _github_json(url):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "ROS-Manual-Updater", "Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(request, timeout=25) as response:
        return json.loads(response.read().decode("utf-8"))


def _latest_update(owner, repo, branch):
    url = (
        f"https://api.github.com/repos/{urllib.parse.quote(owner, safe='')}/"
        f"{urllib.parse.quote(repo, safe='')}/commits/{urllib.parse.quote(branch, safe='')}"
    )
    payload = _github_json(url)
    sha = payload.get("sha")
    if not isinstance(sha, str) or len(sha) != 40:
        raise ValueError("GitHub returned an invalid commit identifier.")
    commit = payload.get("commit") or {}
    message = (commit.get("message") or "No commit message").splitlines()[0]
    date_text = ((commit.get("committer") or {}).get("date") or "")
    return sha, message, date_text


def _print_update_status(sha, message, date_text, data):
    print("\nGitHub latest commit:")
    print(f"  Commit: {sha[:7]}")
    if date_text:
        print(f"  Date:   {date_text}")
    print(f"  Change: {message}")
    installed = data.get("installed_commit")
    if installed == sha:
        print("\nROS is up to date.")
        return False
    if isinstance(installed, str) and len(installed) == 40:
        print("\nA different commit is available.")
    else:
        print("\nInstalled commit is not recorded yet.")
        print("This source has not been linked to an installed version.")
    return True


def _safe_member_path(name):
    path = Path(name)
    if path.is_absolute() or any(part in ("..", "") for part in path.parts):
        return None
    if not path.parts or path.parts[0] in (".git", "__pycache__"):
        return None
    if any(part.endswith((".bak", ".pyc")) or ".bak-" in part for part in path.parts):
        return None
    return path


def _download_update(owner, repo, branch, sha):
    UPDATE_DIR.mkdir(parents=True, exist_ok=True)
    archive_path = UPDATE_DIR / f"ros-{sha}.zip"
    stage_path = UPDATE_DIR / f"ros-{sha}"
    if archive_path.exists() and stage_path.exists():
        print(f"Update package already downloaded: {archive_path}")
        return stage_path

    url = (
        f"https://api.github.com/repos/{urllib.parse.quote(owner, safe='')}/"
        f"{urllib.parse.quote(repo, safe='')}/zipball/{urllib.parse.quote(sha, safe='')}"
    )
    request = urllib.request.Request(url, headers={"User-Agent": "ROS-Manual-Updater"})
    temporary = archive_path.with_suffix(".zip.part")
    try:
        with urllib.request.urlopen(request, timeout=60) as response, temporary.open("wb") as out:
            total = 0
            while True:
                chunk = response.read(1024 * 128)
                if not chunk:
                    break
                total += len(chunk)
                if total > 50 * 1024 * 1024:
                    raise ValueError("Update archive exceeds the 50 MB safety limit.")
                out.write(chunk)
        with zipfile.ZipFile(temporary) as archive:
            members = [n for n in archive.namelist() if _safe_member_path(n.split("/", 1)[-1])]
            if not members:
                raise ValueError("The GitHub archive contains no usable project files.")
            temp_stage = Path(tempfile.mkdtemp(prefix="ros-stage-", dir=UPDATE_DIR))
            try:
                for name in members:
                    relative = _safe_member_path(name.split("/", 1)[-1])
                    if relative is None or name.endswith("/"):
                        continue
                    destination = temp_stage / relative
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    with archive.open(name) as src, destination.open("wb") as dst:
                        shutil.copyfileobj(src, dst)
                if not (temp_stage / "ros_cli.py").is_file():
                    raise ValueError("Archive is missing ros_cli.py; refusing this package.")
                if not (temp_stage / "core" / "doctor.py").is_file():
                    raise ValueError("Archive is missing required ROS modules; refusing this package.")
                if stage_path.exists():
                    shutil.rmtree(stage_path)
                temp_stage.replace(stage_path)
            except Exception:
                shutil.rmtree(temp_stage, ignore_errors=True)
                raise
        temporary.replace(archive_path)
        print(f"Download complete: {archive_path}")
        print(f"Staged safely at: {stage_path}")
        return stage_path
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def _install_update(stage_path, sha):
    if not APP_DIR.is_dir() or not (APP_DIR / "ros_cli.py").is_file():
        raise ValueError(f"ROS installation folder not found: {APP_DIR}")
    files = [p for p in stage_path.rglob("*") if p.is_file()]
    if not any(p.relative_to(stage_path).as_posix() == "ros_cli.py" for p in files):
        raise ValueError("Downloaded package is incomplete.")
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_root = Path.home() / ".local" / "share" / "rana-os" / "update-backups" / stamp
    backup_root.mkdir(parents=True, exist_ok=False)
    changed = []
    try:
        for source in files:
            relative = source.relative_to(stage_path)
            if _safe_member_path(relative.as_posix()) is None:
                continue
            destination = APP_DIR / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists():
                backup = backup_root / relative
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(destination, backup)
            temp = destination.with_name(destination.name + ".ros-update-tmp")
            shutil.copy2(source, temp)
            temp.replace(destination)
            changed.append(relative)
        config = load_config()
        config["installed_commit"] = sha
        save_config(config)
    except Exception:
        for relative in reversed(changed):
            destination = APP_DIR / relative
            backup = backup_root / relative
            if backup.exists():
                shutil.copy2(backup, destination)
            else:
                destination.unlink(missing_ok=True)
        raise
    print(f"ROS update installed successfully. Commit: {sha[:7]}")
    print(f"Backup saved at: {backup_root}")
    print("Run 'ros doctor' to verify the installation.")


def run_update(args=None):
    raw_args = list(args or [])
    if raw_args and raw_args[0].lower() == "help":
        build_update_parser().print_help()
        return
    parsed = build_update_parser().parse_args(raw_args)
    action = parsed.action or "check"
    try:
        owner, repo, branch, data = _update_repo_details()
        print(f"ROS update source: {owner}/{repo} ({branch})")
        sha, message, date_text = _latest_update(owner, repo, branch)
        available = _print_update_status(sha, message, date_text, data)
        if action == "check":
            print("\nNo files have been changed.")
            return
        if not available and action == "download":
            print("\nNo download needed.")
            return
        if action == "download":
            _download_update(owner, repo, branch, sha)
            print("\nNext step: ros update install")
            return
        if action == "install":
            stage_path = UPDATE_DIR / f"ros-{sha}"
            if not stage_path.is_dir():
                print("\nNo matching downloaded package found.")
                print("Run 'ros update download' first.")
                return
            if not sys.stdin.isatty():
                print("\nInstall requires an interactive confirmation.")
                return
            answer = input("\nInstall this update now? Existing files will be backed up. [y/N]: ").strip().lower()
            if answer not in ("y", "yes"):
                print("Installation cancelled. No project files changed.")
                return
            _install_update(stage_path, sha)
    except urllib.error.HTTPError as exc:
        print(f"GitHub request failed: HTTP {exc.code}")
    except (urllib.error.URLError, TimeoutError) as exc:
        print(f"Network error while contacting GitHub: {exc}")
    except (OSError, ValueError, zipfile.BadZipFile, json.JSONDecodeError) as exc:
        print(f"ROS updater error: {exc}")


def suggest_command(token, choices, full_prefix="ros"):
    """Ask before correcting a likely command typo."""
    matches = difflib.get_close_matches(token.lower(), sorted(set(choices)), n=1, cutoff=0.62)
    if not matches or matches[0] == token.lower():
        return None
    suggestion = matches[0]
    try:
        answer = input(f"Unknown command '{token}'.\nDo you mean '{full_prefix} {suggestion}'? [y/N]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled.")
        return None
    if answer in ("y", "yes"):
        return suggestion
    print("No command executed.")
    return None


def run_config(args=None):
    """Manage top-level ROS configuration properties."""
    raw = list(args or [])
    usage = (
        "ROS CONFIG\n"
        "  ros config set PROPERTY VALUE   Add or update a property\n"
        "  ros config get PROPERTY         Show a property's value\n"
        "  ros config list                 Show all properties\n"
        "  ros config remove PROPERTY      Remove a property\n"
        "  ros config reset                Reset all settings (asks first)\n"
        "\nValues accept JSON types: strings, numbers, true, false, null, arrays and objects."
    )
    if not raw or raw[0] in ("-h", "--help", "help"):
        print(usage)
        return

    action = raw[0].lower()
    config_actions = ("set", "get", "list", "remove", "reset")
    if action not in config_actions:
        corrected = suggest_command(action, config_actions, "ros config")
        if corrected is None:
            print(usage)
            return
        raw[0] = corrected
        action = corrected
    data = load_config()
    if action == "list" and len(raw) == 1:
        if not data:
            print("ROS config is empty.")
        else:
            print(json.dumps(data, indent=2, ensure_ascii=False))
        return
    if action == "get" and len(raw) == 2:
        key = raw[1]
        if key not in data:
            print(f"Property not found: {key}")
            return
        print(json.dumps(data[key], ensure_ascii=False))
        return
    if action == "set" and len(raw) >= 3:
        key = raw[1]
        value_text = " ".join(raw[2:])
        try:
            value = json.loads(value_text)
        except json.JSONDecodeError:
            value = value_text
        data[key] = value
        save_config(data)
        print(f"Saved: {key} = {json.dumps(value, ensure_ascii=False)}")
        return
    if action == "remove" and len(raw) == 2:
        key = raw[1]
        if key not in data:
            print(f"Property not found: {key}")
            return
        del data[key]
        save_config(data)
        print(f"Removed property: {key}")
        return
    if action == "reset" and len(raw) == 1:
        try:
            answer = input("Reset ALL ROS settings to defaults? [y/N]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nCancelled.")
            return
        if answer not in ("y", "yes"):
            print("Reset cancelled. No settings changed.")
            return
        if CONFIG.exists():
            backup = CONFIG.with_name("config.json.bak-before-reset")
            backup.write_text(CONFIG.read_text(encoding="utf-8"), encoding="utf-8")
        save_config({})
        print("ROS configuration reset. Default values will be used.")
        return
    print(usage)


def save_config(data):
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    temp = CONFIG.with_suffix(".tmp")
    temp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temp.replace(CONFIG)


def show_help():
    print("ROS — Available commands")
    print("  ros help              Show this help")
    print("  ros --help            Show this help")
    print("  ros -h                Short help option")
    print("  ros version           Show ROS version")
    print("  ros --version         Show ROS version")
    print("  ros -V                Short version option")
    print("  ros core              Open the four core ROS systems")
    print("  ros core --help       Show core menu usage")
    print("  ros list              List commands by category")
    print("  ros list --help       Show list help")
    print("  ros about             About ROS")
    print("  ros doctor            Run ROS health checks")
    print("  ros doctor --help     Show doctor help")
    print("  ros info              Show ROS and environment information")
    print("  ros info --help       Show info help")
    print("  ros update            Check for ROS updates")
    print("  ros update download   Download the latest ROS package")
    print("  ros update install    Install a downloaded update (asks first)")
    print("  ros update check      Legacy check command")
    print("  ros update --check    Standard check option")
    print("  ros update -c         Short check option")
    print("  ros update help       Show updater help")
    print("  ros update --help     Show updater help")
    print("  ros new        Ask to open ROS in a new terminal workspace")
    print("  ros theme      Open the inline theme picker")
    print("  ros theme dir  Open the theme picker")
    print("  ros theme new  Pick a theme and open a fresh ROS screen")
    print("  ros night      Enable cyberpunk night theme")
    print("  ros night off  Restore the previous theme")
    print("  ros night status  Check night mode status")
    print("  ros lab        Open ROS Cyber Lab")
    print("  ros matrix     Start Matrix rain")
    print("  ros watch      Open live device System Watch")
    print("  ros desk       Open ROS Daily Desk (tasks, focus, notes, habits)")
    print("  ros nexus      Open ROS NEXUS command center")
    print("  ros download   Download supported links, media and files")
    print("  ros download history  Show recent downloads")
    print("  ros oracle     Open ROS ORACLE AI assistant (Groq)")
    print("  ros ai         Short alias for ROS ORACLE")
    print("  ros main       Customize main banner name and text")
    print("  ros config     Manage configuration properties and values")
    print("  ros fire       Start fire simulation")
    print("  ros dungeon    Play ROS Dungeon in the terminal")
    print("  ros tt         Open ROS Typing Test")
    print("  ros connect    Open ROS Connect chat")
    print("  ros weather    Show current weather and 5-day forecast")
    print("  ros weather auto  Use device location when available")
    print("  ros weather CITY  Check weather for a city")
    print("  ros weather --city CITY  Standard city option")
    print("  ros weather -c CITY  Short city option")
    print("  ros weather --auto  Try device location")
    print("  ros weather setcity CITY  Save default weather city")
    print("  ros weather --set-city CITY  Standard save-city option")
    print("  ros weather --forecast  Show forecast only")
    print("  ros forecast   Show the 5-day forecast")
    print()
    print("Theme picker controls:")
    print("  Up/Down        Move between theme names")
    print("  Enter          Apply selected theme")
    print("  q              Cancel")

def open_new_session():
    try:
        answer = input("Open a fresh ROS screen? [y/N]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled.")
        return

    if answer not in ("y", "yes"):
        print("Okay, staying on the current screen.")
        return

    subprocess.run([sys.executable, str(MAIN)], check=False)

def load_config():
    try:
        return json.loads(CONFIG.read_text())
    except (OSError, ValueError):
        return {}

def choose_color():
    data = load_config()
    current = data.get("color", "#39ff14").lower()
    selected = next((i for i, (_, value) in enumerate(COLORS) if value == current), 0)

    print("\nROS THEME")
    print("Arrow keys: move | Enter: apply | q: cancel")

    if not sys.stdin.isatty():
        for name, _ in COLORS:
            print(f"  {name}")
        try:
            choice = int(input("Select number (0 cancel): "))
            if choice == 0:
                return False
            if not 1 <= choice <= len(COLORS):
                print("Invalid selection.")
                return False
            selected = choice - 1
        except (ValueError, EOFError, KeyboardInterrupt):
            return False
    else:
        import termios
        import tty
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)

        def draw():
            for i, (name, _) in enumerate(COLORS):
                marker = "> " if i == selected else "  "
                suffix = " (current)" if COLORS[i][1] == current else ""
                label = "\x1b[7m" + name + "\x1b[0m" if i == selected else name
                sys.stdout.write("\r\x1b[2K" + marker + label + suffix + "\n")
            sys.stdout.flush()

        try:
            tty.setraw(fd)
            attrs = termios.tcgetattr(fd)
            attrs[3] |= termios.ISIG
            termios.tcsetattr(fd, termios.TCSANOW, attrs)
            sys.stdout.write("\x1b[?25l")
            draw()
            while True:
                key = sys.stdin.read(1)
                if key == "\x1b":
                    seq = sys.stdin.read(2)
                    if seq == "[A":
                        selected = (selected - 1) % len(COLORS)
                    elif seq == "[B":
                        selected = (selected + 1) % len(COLORS)
                    else:
                        continue
                elif key in ("\r", "\n"):
                    break
                elif key.lower() == "q":
                    print("\nCancelled.")
                    return False
                else:
                    continue
                sys.stdout.write(f"\x1b[{len(COLORS)}A")
                draw()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
            sys.stdout.write("\x1b[?25h")
            sys.stdout.flush()

    name, value = COLORS[selected]
    data["color"] = value
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text(json.dumps(data))
    print(f"\nROS theme changed to {name}.")
    return True

def run_main_settings(raw_args=None):
    """Configure the main ROS banner using standard long options."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="ros main",
        description="Customize the main ROS banner name and subtitle.",
        epilog=(
            "Examples:\n"
            "  ros main --name RAN\n"
            "  ros main --text \"Personal Terminal Environment\"\n"
            "  ros main --logo \"MY NAME\"\n"
            "  ros main logo \"MY NAME\"\n"
            "  ros main title \"MY TITLE\"\n"
            "  ros main subtitle \"MY SUBTITLE\"\n"
            "  ros main logo reset\n"
            "  ros main title reset\n"
            "  ros main subtitle reset\n"
            "  ros main --reset-name\n"
            "  ros main --reset-text\n"
            "  ros main --reset-logo\n"
            "  ros main --reset"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--name", metavar="NAME", help="set the banner title")
    group.add_argument("--text", metavar="TEXT", help="set the banner subtitle")
    group.add_argument("--logo", metavar="WORDS", help="set the large ASCII-art logo text")
    group.add_argument("--reset-name", action="store_true", help="restore the default title: ROS")
    group.add_argument("--reset-text", action="store_true", help="restore the default subtitle")
    group.add_argument("--reset-logo", action="store_true", help="restore the original RANA ASCII-art logo")
    group.add_argument("--reset", action="store_true", help="restore title, subtitle and logo defaults")
    parser.add_argument("legacy", nargs="*", help=argparse.SUPPRESS)
    parsed = parser.parse_args(list(raw_args or []))

    data = load_config()
    logo_changed = parsed.logo is not None or parsed.reset_logo
    if parsed.name is not None:
        value = parsed.name.strip()
        if not value:
            parser.error("NAME cannot be empty")
        data["main_name"] = value[:24]
        message = f"Main title set to: {data['main_name']}"
    elif parsed.text is not None:
        value = parsed.text.strip()
        if not value:
            parser.error("TEXT cannot be empty")
        data["main_text"] = value[:64]
        message = f"Main subtitle set to: {data['main_text']}"
    elif parsed.logo is not None:
        value = parsed.logo.strip()
        if not value:
            parser.error("WORDS cannot be empty")
        if len(value) > 12:
            parser.error("logo text must be 12 characters or fewer to fit the terminal")
        if not all(ch.isalnum() or ch.isspace() or ch in "-_." for ch in value):
            parser.error("logo text may contain letters, numbers, spaces, hyphens, underscores and periods only")
        data["main_logo"] = value
        message = f"ASCII-art logo set to: {value}"
    elif parsed.reset_name:
        data.pop("main_name", None)
        message = "Main title restored to default: ROS"
    elif parsed.reset_text:
        data.pop("main_text", None)
        message = "Main subtitle restored to default."
    elif parsed.reset_logo:
        data.pop("main_logo", None)
        message = "Original RANA ASCII-art logo restored."
    elif parsed.reset:
        data.pop("main_name", None)
        data.pop("main_text", None)
        data.pop("main_logo", None)
        message = "Main title, subtitle and ASCII-art logo restored to defaults."
    elif parsed.legacy:
        # Backward compatibility for the earlier informal command forms.
        old = parsed.legacy
        key = old[0].lower()
        value = " ".join(old[1:]).strip()
        if key in ("logo", "title", "subtitle") and value.lower() in ("reset", "def", "default"):
            if key == "logo":
                data.pop("main_logo", None)
                message = "Original RANA ASCII-art logo restored."
                logo_changed = True
            elif key == "title":
                data.pop("main_name", None)
                message = "Main title restored to default: ROS"
            else:
                data.pop("main_text", None)
                message = "Main subtitle restored to default."
        elif key in ("subtitle", "text") and value:
            if value.lower() in ("def", "default"):
                data.pop("main_text", None)
                message = "Main subtitle restored to default."
            else:
                data["main_text"] = value[:64]
                message = f"Main subtitle set to: {data['main_text']}"
        elif key == "title" and value:
            if value.lower() in ("def", "default"):
                data.pop("main_name", None)
                message = "Main title restored to default: ROS"
            else:
                data["main_name"] = value[:24]
                message = f"Main title set to: {data['main_name']}"
        elif key == "reset" and value.lower() in ("title", "subtitle"):
            config_key = "main_name" if value.lower() == "title" else "main_text"
            data.pop(config_key, None)
            message = f"Main {value.lower()} restored to default."
        elif key == "logo" and value:
            if value.lower() in ("def", "default"):
                data.pop("main_logo", None)
                message = "Original RANA ASCII-art logo restored."
            else:
                if len(value) > 12:
                    parser.error("logo text must be 12 characters or fewer to fit the terminal")
                data["main_logo"] = value
                message = f"ASCII-art logo set to: {value}"
            logo_changed = True
        elif key == "reset" and value.lower() == "logo":
            data.pop("main_logo", None)
            message = "Original RANA ASCII-art logo restored."
            logo_changed = True
        elif key == "name" and value.lower() in ("def", "default"):
            data.pop("main_name", None)
            message = "Main title restored to default: ROS"
        elif key.startswith("name="):
            name = " ".join([key.split("=", 1)[1], *old[1:]]).strip().strip("[]\"'")
            if not name:
                parser.error("NAME cannot be empty")
            data["main_name"] = name[:24]
            message = f"Main title set to: {data['main_name']}"
        elif key == "name" and value:
            data["main_name"] = value.strip("[]\"'")[:24]
            message = f"Main title set to: {data['main_name']}"
        else:
            parser.error("use --name, --text, --logo, --reset-name, --reset-text, --reset-logo or --reset")
    else:
        print("ROS MAIN SETTINGS")
        print(f"  Current title    : {data.get('main_name', 'ROS')}")
        print(f"  Current subtitle : {data.get('main_text', 'PERSONAL TERMINAL ENVIRONMENT')}")
        print(f"  Current logo     : {data.get('main_logo', 'Original RANA logo')}")
        print("\nRun 'ros main --help' for available options.")
        return

    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(message)
    print("Saved.")
    open_new_session()


def main():
    parser = argparse.ArgumentParser(
        prog="ros",
        description="ROS — RAN Operating System command-line interface",
        add_help=False,
    )
    parser.add_argument("-h", "--help", action="store_true", dest="show_help")
    parser.add_argument("-V", "--version", action="store_true", dest="show_version")
    parser.add_argument("command", nargs="?")
    parser.add_argument("command_args", nargs=argparse.REMAINDER)
    parsed = parser.parse_args()

    if parsed.show_help:
        show_help()
        return
    if parsed.show_version:
        show_version()
        return
    if parsed.command is None:
        show_help()
        return

    known_commands = (
        "help", "version", "list", "about", "doctor", "info", "update", "new",
        "theme", "night", "lab", "matrix", "watch", "monitor", "desk", "nexus",
        "main", "config", "fire", "dungeon", "tt", "typing", "connect", "chat", "oracle", "ai",
        "weather", "forecast", "download", "core",
    )
    if parsed.command.lower() not in known_commands:
        corrected = suggest_command(parsed.command, known_commands)
        if corrected is None:
            print(f"Unknown command: {parsed.command}")
            print("Type 'ros help' to see all available commands.")
            return
        parsed.command = corrected

    if parsed.command.lower() == "core":
        from core.workspace import run as run_core
        exit_code = run_core(parsed.command_args)
        if exit_code:
            raise SystemExit(exit_code)
        return
    if parsed.command.lower() == "main":
        run_main_settings(parsed.command_args)
        return
    if parsed.command.lower() == "config":
        run_config(parsed.command_args)
        return
    if parsed.command.lower() == "download":
        from core.downloader import run as run_downloader
        exit_code = run_downloader(parsed.command_args)
        if exit_code:
            raise SystemExit(exit_code)
        return
    if parsed.command.lower() in ("oracle", "ai"):
        from core.oracle import run as run_oracle
        exit_code = run_oracle(parsed.command_args)
        if exit_code:
            raise SystemExit(exit_code)
        return

    args = [parsed.command.lower(), *[arg.lower() for arg in parsed.command_args]]
    if args[0] == "help":
        show_help()
        return
    if args[0] == "list":
        from core.commands import run as run_command_list
        exit_code = run_command_list(args[1:])
        if exit_code:
            raise SystemExit(exit_code)
        return
    if args[0] == "version":
        show_version()
        return
    if args[0] == "update":
        run_update(args[1:])
        return
    if args[0] == "doctor":
        from core.doctor import run as run_doctor
        exit_code = run_doctor(args[1:])
        if exit_code:
            raise SystemExit(exit_code)
        return
    if args[0] == "info":
        from core.info import run as run_info
        exit_code = run_info(args[1:])
        if exit_code:
            raise SystemExit(exit_code)
        return
    if args[0] == "about":
        print("ROS — RAN Operating System")
        print("A personal terminal-based environment built with Python for Termux.")
        print("Created as a learning and customization project.")
        print("Explore themes, system tools, and small utilities from one place.")
        print("ROS is a project running inside Termux, not a standalone Android OS.")
        return
    if args[0] == "new":
        open_new_session()
        return
    if args[0] == "dungeon":
        from core.dungeon_terminal import play
        play()
        return
    if args[0] in ("tt", "typing"):
        from core.typing_test import play
        play()
        return
    if args[0] in ("connect", "chat"):
        from core.connect import run
        run()
        return
    if args[0] in ("weather", "forecast"):
        from core.weather import run as run_weather
        run_weather(args[1:], forecast_only=(args[0] == "forecast"))
        return
    if args[0] == "night":
        from core.night import run_night
        run_night(args[1:])
        return
    if args[0] == "nexus":
        from core.nexus import run as run_nexus
        exit_code = run_nexus(args[1:])
        if exit_code:
            raise SystemExit(exit_code)
        return
    if args[0] == "desk":
        from core.desk import run as run_desk
        exit_code = run_desk(args[1:])
        if exit_code:
            raise SystemExit(exit_code)
        return
    if args[0] in ("watch", "monitor"):
        from core.system_watch import run as run_system_watch
        exit_code = run_system_watch(args[1:])
        if exit_code:
            raise SystemExit(exit_code)
        return
    if args[0] in ("lab", "matrix", "fire"):
        from core.cyberlab import main as run_lab
        import sys as _sys
        mode = "menu" if args[0] == "lab" else args[0]
        _sys.argv = ["ros-cyberlab", mode]
        run_lab()
        return
    if args[0] == "theme":
        new_screen = "new" in args[1:]
        if choose_color():
            command = [sys.executable, str(MAIN)]
            if not new_screen:
                command.append("--append")
            subprocess.run(command, check=False)
        return
    print(f"Unknown command: {' '.join(args)}")
    print("Type 'ros help' to see all available commands.")

if __name__ == "__main__":
    main()
