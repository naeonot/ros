# ROS — RAN Operating System

**Current development version:** `0.1.0-dev`

ROS is a modular personal terminal environment for **Termux on Android**, written in Python. It combines a command-line dashboard with optional utilities and local productivity tools.

> ROS is an actively developed project, not a certified production platform. Android/Termux compatibility varies by device and environment. Only the maintainer's Android 14 / Termux environment has been exercised end-to-end so far.

## Quick install

On a fresh Termux installation, run:

```bash
pkg update
pkg install curl python -y
bash -c "$(curl -fsSL https://raw.githubusercontent.com/naeonot/ros/main/install.sh)"
```

Then launch:

```bash
ros
```

The bootstrap installer checks the latest GitHub commit, downloads that exact repository archive, validates archive paths and size, then runs the Python installer. It installs ROS into `~/rana-os`, creates the `ros` launcher, and configures the update source.

Review [install.sh](install.sh) and [install.py](install.py) before executing them if you want to inspect the installation process.

## Manual installation

```bash
pkg update && pkg upgrade
pkg install python git
git clone https://github.com/naeonot/ros.git
cd ros
python install.py
ros
```

## Main commands

| Command | Purpose |
|---|---|
| `ros` | Main ROS dashboard |
| `ros core` | Central menu for core systems |
| `ros oracle` | ORACLE AI assistant |
| `ros nexus` | NEXUS command center |
| `ros desk` | Tasks, focus timer, notes and habits |
| `ros watch` | Device telemetry |
| `ros download` | Media and file downloads |
| `ros lab` | Cyber Lab utilities |
| `ros config` | Local configuration manager |
| `ros doctor` | Installation health checks |
| `ros update` | Check GitHub for ROS updates |

For update installation:

```bash
ros update
ros update download
ros update install
```

The updater asks for confirmation before installing unless explicitly passed `--yes`. It creates a timestamped backup of files it replaces. `pkg upgrade` updates Termux packages; `ros update` updates ROS project files.

## Uninstall

To remove ROS, run:

```bash
ros uninstall
```

The uninstaller always asks for confirmation. By default it removes the ROS program, launcher, local settings (including the ORACLE API key), Daily Desk data, download history, update backups and update cache. This deletion is permanent.

To remove the program but retain personal ROS settings and data, run:

```bash
ros uninstall --keep-data
```

Both modes leave Termux, Python, curl and other Termux packages untouched. Review the confirmation prompt before proceeding.

## Data, privacy and security

- ORACLE credentials and personal configuration are stored locally under `~/.config/rana-os/`; they are not included in this repository.
- Daily Desk data and download history are stored locally under `~/.local/share/`.
- Back up those directories separately if you want to preserve settings and personal data across a Termux reset.
- Never commit API keys, passwords, tokens, private files or personal data.
- Downloader safety checks are best-effort and are **not** a malware scanner.
- NEXUS signal scan visuals are simulations, not actual network scans.
- See [SECURITY.md](SECURITY.md) for vulnerability reporting.

## Compatibility

ROS is designed for Termux on Android. It has not yet been validated across a broad range of Android versions, CPU architectures or Termux distributions. Optional features may require Termux:API, `ffmpeg`, storage permissions or network access.

When reporting a problem, include Android version, Termux source, Python version and the exact command. Remove secrets and personal information from logs.

## Contributing and support

- [Report a bug](https://github.com/naeonot/ros/issues/new?template=bug_report.yml)
- [Request a feature](https://github.com/naeonot/ros/issues/new?template=feature_request.yml)
- [Contributing guide](CONTRIBUTING.md)
- [Security policy](SECURITY.md)
- [Changelog](CHANGELOG.md)

Pull requests are welcome, but compatibility claims should include actual test environments.

## License

MIT — see [LICENSE](LICENSE).
