#!/usr/bin/env python3
"""Install the complete ROS project into ~/ran-os on Termux."""
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

SOURCE = Path(__file__).resolve().parent
APP = Path.home() / "ran-os"
PREFIX = Path(os.environ.get("PREFIX", "/data/data/com.termux/files/usr"))
BIN = PREFIX / "bin"
CONFIG_DIR = Path.home() / ".config" / "ran-os"
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


def save_install_logo(name):
    """Persist the install-time logo separately from later manual overrides."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    try:
        config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        if not isinstance(config, dict):
            raise ValueError("ROS config must be a JSON object")
    except FileNotFoundError:
        config = {}

    config["install_logo"] = name.upper()
    temporary = CONFIG_FILE.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(config, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.chmod(0o600)
    temporary.replace(CONFIG_FILE)
    CONFIG_DIR.chmod(0o700)


def personalize_logo():
    """Choose the local installation's baseline ASCII-art logo."""
    default_logo = "RAN-OS"
    print("\nPERSONALIZE YOUR ROS LOGO")
    print("Enter a name to turn it into your local ASCII-art logo.")
    print(f"Leave it blank to use the default {default_logo} logo.")

    if not sys.stdin.isatty():
        save_install_logo(default_logo)
        print(f"Default {default_logo} logo saved locally (non-interactive install).")
        return

    try:
        name = input("Logo name (up to 12 characters): ").strip()
    except (EOFError, KeyboardInterrupt):
        name = ""
        print("\nInput skipped; using the default logo.")

    if not name:
        name = default_logo
    elif len(name) > 12:
        print(f"Name is too long (maximum 12 characters). Using {default_logo}.")
        name = default_logo
    elif not all(ch.isalnum() or ch.isspace() or ch in "-_." for ch in name):
        print(f"Unsupported characters. Using {default_logo}.")
        name = default_logo

    save_install_logo(name)
    print(f"Installation ASCII-art logo saved locally: {name.upper()}")


def migrate_legacy_paths():
    """Move earlier rana-os storage paths to the current ran-os names."""
    pairs = (
        (Path.home() / "rana-os", APP),
        (Path.home() / ".config" / "rana-os", CONFIG_DIR),
        (Path.home() / ".cache" / "rana-os", Path.home() / ".cache" / "ran-os"),
        (Path.home() / ".local" / "share" / "rana-os", Path.home() / ".local" / "share" / "ran-os"),
    )
    for legacy, current in pairs:
        if not legacy.exists() or legacy.is_symlink():
            continue
        if not current.exists():
            current.parent.mkdir(parents=True, exist_ok=True)
            legacy.rename(current)
            print(f"Migrated: {legacy.name} -> {current.name}")
            continue
        if legacy.is_dir() and current.is_dir():
            for item in legacy.iterdir():
                destination = current / item.name
                if not destination.exists():
                    shutil.move(str(item), str(destination))
            try:
                legacy.rmdir()
            except OSError:
                print(f"Note: some older files remain in {legacy}")


def configure_shell_startup():
    """Show the ROS logo and system dashboard in each interactive Termux shell."""
    bashrc = Path.home() / ".bashrc"
    hushlogin = Path.home() / ".hushlogin"
    marker = "# >>> RAN-OS STARTUP >>>"
    end_marker = "# <<< RAN-OS STARTUP <<<"

    try:
        content = bashrc.read_text(encoding="utf-8") if bashrc.exists() else ""
    except OSError as exc:
        print(f"Could not configure shell startup: {exc}")
        return

    # Replace a previous ROS-managed block without touching unrelated shell settings.
    content = re.sub(
        r"(?ms)^# >>> RAN-OS STARTUP >>>\n.*?^# <<< RAN-OS STARTUP <<<\n?",
        "",
        content,
    )
    # Remove the temporary unmarked startup snippets used during local testing.
    content = re.sub(
        r"(?ms)^# RAN-OS startup (?:display only; preserve the ordinary Termux shell|panel; then return to the normal home prompt)\ncase \$- in\n.*?^esac\n?",
        "",
        content,
    )
    block = (
        marker + "\n"
        + 'case $- in\n'
        + '    *i*)\n'
        + '        clear 2>/dev/null || true\n'
        + '        (cd "$HOME/ran-os" && python "$HOME/ran-os/main.py" --append) || true\n'
        + '        ;;\n'
        + 'esac\n'
        + end_marker + "\n"
    )
    content = content.rstrip() + ("\n\n" if content.strip() else "") + block
    temporary = bashrc.with_suffix(".bashrc.ros-tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(bashrc)

    if not hushlogin.exists():
        hushlogin.touch()
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        (CONFIG_DIR / "created-hushlogin").write_text("1\n", encoding="utf-8")

    print("Termux startup configured: ROS logo and system dashboard, normal shell preserved.")


def main():
    if "com.termux" not in str(PREFIX):
        print("This installer is designed for Termux.")
        return 1

    migrate_legacy_paths()

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
    configure_shell_startup()
    print("ROS installed successfully.")
    personalize_logo()
    print("Run: ros")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

