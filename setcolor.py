import json
import re
import sys
from pathlib import Path

config = Path.home() / ".config/ran-os/config.json"

if len(sys.argv) != 2 or not re.fullmatch(r"#?[0-9a-fA-F]{6}", sys.argv[1]):
    print("Usage: python setcolor.py HEX  (example: #ff00aa)")
    sys.exit(1)

color = sys.argv[1]
if not color.startswith("#"):
    color = "#" + color
color = color.lower()

try:
    data = json.loads(config.read_text())
except (OSError, ValueError):
    data = {}

data["color"] = color
config.parent.mkdir(parents=True, exist_ok=True)
config.write_text(json.dumps(data))

print(f"RAN OS theme colour set to {color}")
