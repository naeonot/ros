import json
import sys
from pathlib import Path

config = Path.home() / ".config/rana-os/config.json"

if len(sys.argv) != 2:
    print("Usage: python setname.py NAME")
    sys.exit(1)

name = sys.argv[1].strip()

if not name.isascii() or not name.replace(" ", "").isalnum() or len(name) > 15:
    print("Use 1-15 English letters or numbers.")
    sys.exit(1)

try:
    data = json.loads(config.read_text())
except (OSError, ValueError):
    data = {}

data["name"] = name
config.parent.mkdir(parents=True, exist_ok=True)
config.write_text(json.dumps(data))

print(f"RAN OS name changed to: {name}")
