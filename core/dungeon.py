from pathlib import Path
import socket
import subprocess
import sys
import time

GAME = Path.home() / "rana-os" / "dungeon"
HOST = "127.0.0.1"
PORT = 8765
URL = f"http://{HOST}:{PORT}/"

def server_running():
    try:
        with socket.create_connection((HOST, PORT), timeout=0.5):
            return True
    except OSError:
        return False

def launch():
    if not (GAME / "index.html").is_file():
        print("ROS Dungeon files are missing.")
        return
    if not server_running():
        subprocess.Popen(
            [sys.executable, "-m", "http.server", str(PORT),
             "--bind", HOST, "--directory", str(GAME)],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        for _ in range(20):
            if server_running():
                break
            time.sleep(0.15)
    if not server_running():
        print("Could not start the local game server.")
        return
    print("Opening ROS Dungeon in your browser...")
    result = subprocess.run(
        ["am", "start", "-a", "android.intent.action.VIEW", "-d", URL],
        text=True, capture_output=True
    )
    if result.returncode == 0:
        print("ROS Dungeon URL:", URL)
    else:
        print("Browser launch was not confirmed.")
        print(result.stderr.strip() or result.stdout.strip())
        print("Open this address in your browser:", URL)
