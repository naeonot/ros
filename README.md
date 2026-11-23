# ROS — RAN Operating System

A modular personal terminal environment for Termux on Android, written in Python.

## Quick install

On a fresh Termux installation, run:

    pkg update
    pkg install curl python -y
    bash -c "$(curl -fsSL https://raw.githubusercontent.com/naeonot/ros/main/install.sh)"

The installer downloads the public GitHub repository archive, validates archive paths, and runs the included Python installer. It places ROS in `~/rana-os` and creates the `ros` command.

## Manual install

    pkg update && pkg upgrade
    pkg install python git
    git clone https://github.com/naeonot/ros.git
    cd ros
    python install.py

Then launch with: `ros`

Personal settings and API keys remain in `~/.config/rana-os/` and are not part of this repository.

## Main commands

- `ros` — Main ROS dashboard
- `ros core` — Central menu for core systems
- `ros oracle` — ORACLE AI assistant
- `ros nexus` — NEXUS command center
- `ros desk` — Tasks, focus timer, notes and habits
- `ros watch` — Device telemetry
- `ros download` — Media and file downloader
- `ros lab` — Cyber Lab utilities
- `ros config` — Local configuration manager
- `ros doctor` — Installation health checks
- `ros update` — Check GitHub for ROS updates
- `ros update download` — Download an update package
- `ros update install` — Install a downloaded update after confirmation

## Updating ROS

`pkg upgrade` updates Termux packages. It does not update ROS project files.

Use the ROS updater separately:

    ros update
    ros update download
    ros update install

The updater keeps a timestamped backup of replaced project files. Personal configuration remains outside the project directory.

## Dependencies

See `requirements.txt`. ROS uses Python's standard library and Rich; some optional modules use Termux utilities such as `termux-battery-status` and `ffmpeg`.

## Security and privacy

- ORACLE credentials are stored locally in the user's private Termux config directory, not in this repository.
- Downloader safety checks are best-effort and are not a malware scanner.
- NEXUS signal scan visuals are simulations, not actual network scans.
- Review installation scripts before running them, especially when installing software from the internet.

## License

MIT — see LICENSE.
