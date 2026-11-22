import os
import shutil
import getpass
import subprocess
from datetime import datetime

def get_ram_info():
    try:
        with open("/proc/meminfo") as file:
            data = file.readlines()

        values = {}
        for line in data:
            key, value = line.split(":", 1)
            values[key] = int(value.strip().split()[0])

        total = values["MemTotal"]
        available = values["MemAvailable"]
        used = total - available

        return {
            "total": f"{total / 1024:.0f} MB",
            "used": f"{used / 1024:.0f} MB",
            "free": f"{available / 1024:.0f} MB"
        }
    except (OSError, KeyError, ValueError):
        return {"total": "N/A", "used": "N/A", "free": "N/A"}


def get_android_version():
    try:
        return subprocess.check_output(
            ["getprop", "ro.build.version.release"],
            text=True
        ).strip() or "Unknown"
    except (OSError, subprocess.SubprocessError):
        return "Unknown"


def get_system_info():
    now = datetime.now().astimezone()
    storage = shutil.disk_usage(os.path.expanduser("~"))
    ram = get_ram_info()

    return {
        "Date": now.strftime("%d %b, %Y"),
        "Time": now.strftime("%H:%M"),
        "User": getpass.getuser(),
        "Shell": os.environ.get("SHELL", "Unknown").split("/")[-1],
        "Operating System": f"Android {get_android_version()}",
        "Storage Used": f"{(storage.used / storage.total) * 100:.1f}%",
        "Storage Free": f"{storage.free / (1024**3):.2f} GB",
        "RAM Total": ram["total"],
        "RAM Used": ram["used"],
        "Current Directory": os.getcwd()
    }
