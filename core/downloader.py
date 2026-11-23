"""ROS Download Manager — direct files and yt-dlp supported media sites."""
import json
import os
import mimetypes
import re
import socket
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote
from urllib.request import Request, urlopen

DATA_DIR = Path.home() / ".local/share/ros-downloads"
HISTORY = DATA_DIR / "history.json"
KNOWN_HOSTS = {
    "youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be",
    "instagram.com", "www.instagram.com",
    "pinterest.com", "www.pinterest.com", "pin.it",
    "google.com", "www.google.com", "google.co.in",
    "googleusercontent.com", "gstatic.com",
}
BLOCK_TERMS = (
    "porn", "xxx", "hentai", "onlyfans", "child sexual abuse",
    "sexual exploitation", "rape porn", "csam", "bestiality",
    "white supremacist", "white power", "neo-nazi", "nazi propaganda",
    "heil hitler", "racial hatred", "ethnic cleansing propaganda",
)
RISKY_EXTENSIONS = {
    "apk", "xapk", "exe", "msi", "bat", "cmd", "sh", "bash",
    "ps1", "jar", "deb", "rpm", "py", "js", "vbs", "scr", "com",
}


def ask(prompt, default=""):
    try:
        value = input(prompt).strip()
        return value if value else default
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled.")
        return None


def valid_url(raw):
    parsed = urlparse(raw.strip())
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        return None, "Only valid HTTP/HTTPS links are supported."
    if parsed.username or parsed.password:
        return None, "Links containing embedded credentials are not accepted."
    host = parsed.hostname.lower().rstrip(".")
    if host in ("localhost",) or host.endswith(".localhost") or host.endswith(".local"):
        return None, "Local/private network addresses are blocked."
    try:
        import ipaddress
        ip = ipaddress.ip_address(host)
        if not ip.is_global:
            return None, "Private or non-public IP addresses are blocked."
    except ValueError:
        try:
            addresses = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
            for item in addresses:
                ip = __import__("ipaddress").ip_address(item[4][0])
                if not ip.is_global:
                    return None, "This domain resolves to a private/non-public address."
        except socket.gaierror:
            return None, "Could not resolve the website hostname. Check the link/network."
    return parsed, None


def is_known(host):
    return any(host == item or host.endswith("." + item) for item in KNOWN_HOSTS)


def google_image_target(url):
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if host.endswith("google.com") or host.endswith("google.co.in"):
        params = parse_qs(parsed.query)
        target = params.get("imgurl", [None])[0]
        if target and urlparse(target).scheme in ("http", "https"):
            return unquote(target)
    return url


def choose_folder():
    downloads = Path.home() / "storage/downloads"
    if not downloads.exists():
        downloads = Path.home() / "Downloads"
    print("\nSAVE LOCATION")
    print("  [1] Downloads")
    print("  [2] Current folder")
    print("  [3] Choose folder")
    choice = ask("Choose [1]: ", "1")
    if choice is None:
        return None
    if choice == "1":
        folder = downloads
    elif choice == "2":
        folder = Path.cwd()
    elif choice == "3":
        raw = ask("Folder path: ")
        if raw is None or not raw:
            print("No folder selected.")
            return None
        folder = Path(os.path.expandvars(os.path.expanduser(raw)))
    else:
        print("Invalid choice.")
        return None
    try:
        folder.mkdir(parents=True, exist_ok=True)
        if not folder.is_dir():
            raise OSError("Path is not a directory")
        probe = folder / ".ros-write-test"
        probe.touch(exist_ok=True)
        probe.unlink(missing_ok=True)
    except OSError as exc:
        print(f"Cannot use this folder: {exc}")
        print("For shared Android storage, run: termux-setup-storage")
        return None
    return folder.resolve()


def sensitive_reason(text):
    lowered = (text or "").casefold()
    for term in BLOCK_TERMS:
        if term in lowered:
            return term
    return None


def save_history(entry):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        items = json.loads(HISTORY.read_text(encoding="utf-8")) if HISTORY.exists() else []
        if not isinstance(items, list):
            items = []
    except (OSError, ValueError):
        items = []
    items.insert(0, entry)
    HISTORY.write_text(json.dumps(items[:100], indent=2, ensure_ascii=False), encoding="utf-8")


def show_history():
    try:
        items = json.loads(HISTORY.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        items = []
    if not items:
        print("No download history yet.")
        return
    print("\nROS DOWNLOAD HISTORY")
    for item in items[:15]:
        print(f"  {item.get('time', '?')}  {item.get('status', '?'):<8}  {item.get('file', '?')}")
        print(f"      {item.get('source', '')}")


def infer_extension(url, info):
    ext = str(info.get("ext") or "").lower()
    if ext and ext not in ("unknown_video", "unknown", "none"):
        return ext
    path_ext = Path(urlparse(url).path).suffix.lower().lstrip(".")
    if path_ext and len(path_ext) <= 10 and path_ext.isalnum():
        return path_ext
    try:
        request = Request(url, method="HEAD", headers={"User-Agent": "ROS-Downloader/1.0"})
        with urlopen(request, timeout=12) as response:
            content_type = response.headers.get_content_type()
        guessed = mimetypes.guess_extension(content_type, strict=False)
        if guessed:
            return guessed.lstrip(".").lower()
    except Exception:
        pass
    return "bin"


def progress_hook(data):
    status = data.get("status")
    if status == "downloading":
        total = data.get("total_bytes") or data.get("total_bytes_estimate") or 0
        done = data.get("downloaded_bytes") or 0
        percent = f"{done * 100 / total:5.1f}%" if total else "  ..."
        speed = data.get("速度") or data.get("speed")
        speed_text = f"{speed / 1024 / 1024:.1f} MB/s" if speed else ""
        sys.stdout.write(f"\r  Downloading {percent}  {speed_text}       ")
        sys.stdout.flush()
    elif status == "finished":
        sys.stdout.write("\r  Download finished; finalizing file...       \n")
        sys.stdout.flush()



class SafeRedirectHandler(__import__("urllib.request", fromlist=["HTTPRedirectHandler"]).HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        _, error = valid_url(newurl)
        if error:
            raise OSError(f"Redirect blocked by ROS safety checks: {error}")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def safe_filename(value, fallback="download"):
    name = Path(unquote(str(value or ""))).name
    name = re.sub(r'[\\/:*?"<>|\x00-\x1f]', "_", name).strip(" .")
    return (name[:180] or fallback)


def direct_file_download(url, folder):
    """Fallback for ordinary direct files, including APKs and documents."""
    from urllib.request import build_opener
    request = Request(url, headers={"User-Agent": "ROS-Downloader/1.0"})
    opener = build_opener(SafeRedirectHandler())
    temp_path = None
    try:
        with opener.open(request, timeout=30) as response:
            final_url = response.geturl()
            final_parsed, final_error = valid_url(final_url)
            if final_error:
                print(f"Blocked redirect destination: {final_error}")
                return False
            content_type = response.headers.get_content_type().lower()
            disposition = response.headers.get("Content-Disposition", "")
            match = re.search(r"filename\*?=(?:UTF-8''|\")?([^;\"]+)", disposition, re.I)
            filename = unquote(match.group(1).strip().strip('"')) if match else Path(urlparse(final_url).path).name
            filename = safe_filename(filename, "download")
            if content_type in ("text/html", "application/xhtml+xml") or filename.lower().endswith((".html", ".htm")):
                print("This link returned a webpage, not a direct downloadable file.")
                return False
            ext = Path(filename).suffix.lower().lstrip(".")
            if not ext:
                guessed = mimetypes.guess_extension(content_type, strict=False)
                ext = (guessed or ".bin").lstrip(".")
                filename += "." + ext
            metadata = " ".join((final_url, filename, content_type))
            flagged = sensitive_reason(metadata)
            if flagged:
                print("Blocked by ROS content safety filter: restricted indicator in file metadata.")
                return False
            if ext in RISKY_EXTENSIONS:
                print(f"\nSecurity warning: this is a potentially executable/app file (.{ext}).")
                print("ROS will only save it. It will NOT install or run the file.")
                answer = ask("Download it anyway? [y/N]: ", "n")
                if answer is None or answer.lower() not in ("y", "yes"):
                    print("Download cancelled.")
                    return False
            length = response.headers.get("Content-Length")
            print(f"\nFile : {filename}")
            print(f"Type : {content_type}")
            print(f"From : {final_parsed.hostname}")
            print(f"Save : {folder}")
            if length:
                print(f"Size : {int(length) / (1024*1024):.2f} MB")
            answer = ask("Start download? [Y/n]: ", "y")
            if answer is None or answer.lower() not in ("y", "yes"):
                print("Download cancelled.")
                return False
            destination = folder / filename
            if destination.exists():
                stem, suffix = destination.stem, destination.suffix
                counter = 1
                while destination.exists():
                    destination = folder / f"{stem} ({counter}){suffix}"
                    counter += 1
            temp_path = destination.with_name(destination.name + ".ros-part")
            downloaded = 0
            with temp_path.open("wb") as out:
                while True:
                    chunk = response.read(1024 * 256)
                    if not chunk:
                        break
                    out.write(chunk)
                    downloaded += len(chunk)
                    if length:
                        pct = downloaded * 100 / max(int(length), 1)
                        sys.stdout.write(f"\r  Downloading {pct:5.1f}%  {downloaded/(1024*1024):.1f} MB")
                    else:
                        sys.stdout.write(f"\r  Downloaded {downloaded/(1024*1024):.1f} MB")
                    sys.stdout.flush()
            temp_path.replace(destination)
            print(f"\nDownload completed: {destination}")
            save_history({"time": datetime.now().strftime("%Y-%m-%d %H:%M"), "status": "DONE", "file": destination.name, "source": final_parsed.hostname})
            return True
    except KeyboardInterrupt:
        print("\nDownload interrupted.")
        return False
    except Exception as exc:
        print(f"Direct file download failed: {exc}")
        return False
    finally:
        if temp_path and temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass

def download(url, folder):
    parsed, error = valid_url(url)
    if error:
        print(f"Blocked: {error}")
        return False

    host = (parsed.hostname or "").lower()
    if not is_known(host):
        print(f"\nWARNING: {host} is not on ROS's known-platform list.")
        print("The site may be unsafe. ROS cannot guarantee the file is clean.")
        answer = ask("Continue anyway? [y/N]: ", "n")
        if answer is None or answer.lower() not in ("y", "yes"):
            print("Download cancelled.")
            return False

    target_url = google_image_target(url)
    if target_url != url:
        print("Google Images result detected; downloading the linked image.")
        parsed_target, target_error = valid_url(target_url)
        if target_error:
            print(f"Blocked: linked image URL failed safety checks: {target_error}")
            return False
        target_host = (parsed_target.hostname or "").lower()
        if not is_known(target_host):
            print(f"WARNING: linked image is hosted on {target_host}, not Google.")
            answer = ask("Continue with this image source? [y/N]: ", "n")
            if answer is None or answer.lower() not in ("y", "yes"):
                print("Download cancelled.")
                return False

    try:
        import yt_dlp
    except ImportError:
        print("Missing dependency: yt-dlp")
        print("Install it with: python -m pip install -U yt-dlp")
        return False

    print("\nChecking link and content...")
    opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "skip_download": True,
        "socket_timeout": 25,
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(target_url, download=False)
    except Exception as exc:
        print(f"Media extractor could not read this link: {exc}")
        print("Trying it as a direct file link...")
        return direct_file_download(target_url, folder)

    if isinstance(info, dict) and info.get("entries"):
        info = next((entry for entry in info["entries"] if entry), None)
    if not isinstance(info, dict):
        print("No media metadata found. Trying a direct file download...")
        return direct_file_download(target_url, folder)

    title = str(info.get("title") or info.get("id") or "download")
    ext = infer_extension(target_url, info)
    if ext in ("bin", "unknown_video", "unknown", "none"):
        print("This may be a regular file rather than a media stream. Trying direct download...")
        return direct_file_download(target_url, folder)
    source_text = " ".join((target_url, title, str(info.get("description") or "")[:1200]))
    flagged = sensitive_reason(source_text)
    if flagged:
        print("Blocked by ROS content safety filter.")
        print("The link metadata matched a restricted-content indicator.")
        return False

    if ext in RISKY_EXTENSIONS:
        print(f"\nSecurity warning: this is a potentially executable file (.{ext}).")
        answer = ask("Download it anyway? ROS will NOT run or install it. [y/N]: ", "n")
        if answer is None or answer.lower() not in ("y", "yes"):
            print("Download cancelled.")
            return False

    print(f"Title : {title[:100]}")
    print(f"Type  : {ext or 'website media'}")
    print(f"From  : {host}")
    print(f"Save  : {folder}")
    answer = ask("Start download? [Y/n]: ", "y")
    if answer is None or answer.lower() not in ("y", "yes"):
        print("Download cancelled.")
        return False

    template = str(folder / "%(title).160B [%(id)s].%(ext)s") if ext == str(info.get("ext") or "").lower() else str(folder / f"%(title).160B [%(id)s].{ext}")
    options = {
        "outtmpl": template,
        "noplaylist": True,
        "nooverwrites": True,
        "continuedl": True,
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "progress_hooks": [progress_hook],
        "socket_timeout": 30,
        "retries": 3,
        "fragment_retries": 3,
    }
    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([target_url])
        save_history({
            "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "status": "DONE",
            "file": title[:120],
            "source": host,
        })
        print("Download completed.")
        return True
    except KeyboardInterrupt:
        print("\nDownload interrupted.")
        return False
    except Exception as exc:
        print(f"\nDownload failed: {exc}")
        return False


def run(args=None):
    raw = list(args or [])
    if raw and raw[0] in ("-h", "--help", "help"):
        print("ROS DOWNLOAD MANAGER")
        print("  ros download                 Paste a link and choose a folder")
        print("  ros download URL             Download a link")
        print("  ros download history         Show recent downloads")
        print("\nSupports direct files (including APKs) and websites supported by yt-dlp.")
        print("Unknown sites and executable files require warnings/confirmation. Login, DRM and site restrictions may still prevent downloads. ROS never installs or runs downloaded files.")
        return 0
    if raw and raw[0].lower() == "history":
        show_history()
        return 0
    if raw and raw[0].lower() == "folder":
        folder = choose_folder()
        if folder:
            print(f"Selected folder: {folder}")
        return 0

    url = raw[0] if raw else ask("Paste download link: ")
    if not url:
        return 1
    parsed, error = valid_url(url)
    if error:
        print(f"Invalid link: {error}")
        return 1
    folder = choose_folder()
    if folder is None:
        return 1
    return 0 if download(url, folder) else 1
