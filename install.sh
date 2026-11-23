#!/data/data/com.termux/files/usr/bin/bash
set -eu

REPO="naeonot/ros"
BRANCH="main"
ARCHIVE_URL="https://github.com/${REPO}/archive/refs/heads/${BRANCH}.zip"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT INT TERM

if [ -z "${PREFIX:-}" ] || [ ! -d "$PREFIX" ]; then
  echo "ERROR: This installer is designed for Termux on Android."
  exit 1
fi

if ! command -v python >/dev/null 2>&1; then
  echo "Installing Python..."
  pkg install python -y
fi
if ! command -v curl >/dev/null 2>&1; then
  echo "Installing curl..."
  pkg install curl -y
fi

echo "Downloading ROS from GitHub..."
curl -fL --retry 3 --connect-timeout 20 "$ARCHIVE_URL" -o "$WORK/ros.zip"

echo "Extracting and validating package..."
python - "$WORK/ros.zip" "$WORK/source" <<'PY'
import sys, zipfile
from pathlib import PurePosixPath
archive, destination = sys.argv[1:3]
total = 0
count = 0
with zipfile.ZipFile(archive) as zf:
    members = zf.infolist()
    if len(members) > 500:
        raise SystemExit("ERROR: Package contains too many files.")
    for item in members:
        name = item.filename.replace("\\", "/")
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts:
            raise SystemExit("ERROR: Unsafe path in package.")
        mode = (item.external_attr >> 16) & 0o170000
        if mode == 0o120000:
            raise SystemExit("ERROR: Symbolic links are not allowed.")
        if item.is_dir():
            continue
        total += item.file_size
        count += 1
        if total > 100 * 1024 * 1024:
            raise SystemExit("ERROR: Extracted package exceeds 100 MB.")
    if count == 0:
        raise SystemExit("ERROR: Empty package.")
    zf.extractall(destination)
PY

SOURCE_DIR="$(find "$WORK/source" -mindepth 1 -maxdepth 1 -type d | head -n 1)"
if [ ! -f "$SOURCE_DIR/install.py" ] || [ ! -f "$SOURCE_DIR/ros_manifest.json" ]; then
  echo "ERROR: GitHub package is missing required installer files."
  exit 1
fi

echo "Running ROS installer..."
python "$SOURCE_DIR/install.py"
echo
echo "ROS setup complete. Start it with: ros"
