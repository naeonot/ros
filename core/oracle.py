"""ROS ORACLE — Groq-powered terminal assistant (stdlib-only client)."""
import getpass
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

CONFIG_DIR = Path.home() / ".config/ran-os"
ORACLE_CONFIG = CONFIG_DIR / "oracle.json"
API_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-oss-120b"
SYSTEM_PROMPT = (
    "You are ROS ORACLE, the built-in AI assistant for ROS (RAN Operating System), "
    "a Python terminal environment running in Termux on Android. Be accurate, "
    "practical, concise, and friendly. Explain commands before suggesting risky actions. "
    "You cannot inspect or control the user's device unless the user provides output; "
    "never claim to have executed commands or changed files. Do not ask the user to reveal API keys."
)


def read_settings():
    try:
        data = json.loads(ORACLE_CONFIG.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def write_settings(data):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    try:
        CONFIG_DIR.chmod(0o700)
    except OSError:
        pass
    temp = ORACLE_CONFIG.with_suffix(".tmp")
    temp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    try:
        temp.chmod(0o600)
    except OSError:
        pass
    temp.replace(ORACLE_CONFIG)
    try:
        ORACLE_CONFIG.chmod(0o600)
    except OSError:
        pass


def get_api_key():
    env_key = os.environ.get("GROQ_API_KEY", "").strip()
    if env_key:
        return env_key
    return str(read_settings().get("api_key", "")).strip()


def setup_key():
    print("\nROS ORACLE — GROQ SETUP")
    print("Paste your Groq API key below. Input will remain hidden.")
    try:
        key = getpass.getpass("Groq API key: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nSetup cancelled.")
        return 1
    if not key:
        print("No key entered. Nothing saved.")
        return 1
    if not key.startswith("gsk_"):
        print("Warning: this key does not look like a standard Groq key (gsk_...).")
        try:
            confirm = input("Save it anyway? [y/N]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nSetup cancelled.")
            return 1
        if confirm not in ("y", "yes"):
            print("Key not saved.")
            return 1
    data = read_settings()
    data["api_key"] = key
    data.setdefault("model", DEFAULT_MODEL)
    write_settings(data)
    print("API key saved in the private ROS ORACLE config file.")
    print("Next: ros oracle")
    return 0


def show_status():
    data = read_settings()
    configured = bool(os.environ.get("GROQ_API_KEY", "").strip() or data.get("api_key"))
    source = "environment variable" if os.environ.get("GROQ_API_KEY", "").strip() else ("private config file" if data.get("api_key") else "not configured")
    print("ROS ORACLE STATUS")
    print(f"  API key : {'configured' if configured else 'missing'} ({source})")
    print(f"  Model   : {data.get('model', DEFAULT_MODEL)}")
    return 0 if configured else 1


def set_model(model):
    model = model.strip()
    if not model or any(ch.isspace() for ch in model):
        print("Usage: ros oracle model MODEL_ID")
        return 1
    data = read_settings()
    data["model"] = model
    write_settings(data)
    print(f"ROS ORACLE model set to: {model}")
    return 0


def request_completion(messages, model, api_key):
    body = json.dumps({
        "model": model,
        "messages": messages,
        "max_completion_tokens": 2048,
        "stream": False,
    }).encode("utf-8")
    request = urllib.request.Request(
        API_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "ROS-ORACLE/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=75) as response:
            result = json.loads(response.read().decode("utf-8"))
        return result["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as exc:
        try:
            payload = json.loads(exc.read().decode("utf-8"))
            message = payload.get("error", {}).get("message", "Request rejected")
        except Exception:
            message = f"HTTP {exc.code}"
        if exc.code == 401:
            raise RuntimeError("Groq rejected the API key. Check it with 'ros oracle setup'.")
        if exc.code == 429:
            raise RuntimeError("Groq rate limit or quota reached. Check your Groq console and try later.")
        raise RuntimeError(f"Groq API error ({exc.code}): {message[:350]}")
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Network connection failed: {exc.reason}")
    except (KeyError, IndexError, TypeError, json.JSONDecodeError):
        raise RuntimeError("Groq returned an unexpected response format.")


def chat():
    """Run the full ORACLE interface in the current terminal page."""
    return chat_new(clear_page=False)

def chat_new(clear_page=True):
    """Run the ORACLE interface; optionally clear the terminal first."""
    api_key = get_api_key()
    if not api_key:
        print("ROS ORACLE is not configured yet.")
        print("Run 'ros oracle setup' to securely add your Groq API key.")
        return 1

    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.text import Text
        from rich.align import Align
        from rich import box
    except ImportError:
        print("The ORACLE interface needs Rich. Install it with: pip install rich")
        return 1

    settings = read_settings()
    model = settings.get("model", DEFAULT_MODEL)
    theme_name = settings.get("theme", "matrix")
    themes = {
        "matrix": {"accent": "bright_green", "secondary": "bright_cyan", "prompt": "92", "reply": "96"},
        "cyber": {"accent": "bright_cyan", "secondary": "bright_magenta", "prompt": "96", "reply": "95"},
        "amber": {"accent": "bright_yellow", "secondary": "bright_white", "prompt": "93", "reply": "97"},
        "classic": {"accent": "bright_white", "secondary": "bright_blue", "prompt": "97", "reply": "94"},
    }
    if theme_name not in themes:
        theme_name = "matrix"
    palette = themes[theme_name]
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    console = Console()

    # Only the explicit `ros oracle new` command clears the terminal.
    # Plain `ros oracle` renders the identical interface in the current page.
    if clear_page:
        console.clear()
    header = Text()
    try:
        from pyfiglet import Figlet
        oracle_art = Figlet(font="ansi_shadow", width=70).renderText("ORACLE").rstrip()
        header.append(oracle_art, style=f"bold {palette['accent']}")
    except ImportError:
        header.append("O R A C L E", style=f"bold {palette['accent']}")

    def render_interface():
        header = Text()
        try:
            from pyfiglet import Figlet
            oracle_art = Figlet(font="ansi_shadow", width=70).renderText("ORACLE").rstrip()
            header.append(oracle_art, style="bold bright_green")
        except ImportError:
            header.append("O R A C L E", style="bold bright_green")
        console.print(Panel(
            Align.center(header),
            subtitle=f"[{palette['secondary']}]MODEL: {model} · THEME: {theme_name.upper()}[/]",
            border_style=palette["accent"],
            box=box.DOUBLE,
            padding=(1, 2),
        ))
        console.print(f"[bold {palette['secondary']}]CHAT COMMANDS[/]")
        console.print(f"  [bold {palette['accent']}]settings[/]   [white]—[/]  Change model or theme")
        console.print(f"  [bold {palette['accent']}]new page[/]   [white]—[/]  Reopen this interface")
        console.print(f"  [bold {palette['accent']}]clear[/]      [white]—[/]  Reset conversation")
        console.print(f"  [bold {palette['accent']}]help[/]       [white]—[/]  Show available commands")
        console.print(f"  [bold {palette['accent']}]exit[/]       [white]—[/]  Close ORACLE")
        console.print()

    render_interface()

    def open_settings():
        nonlocal model, theme_name, palette
        while True:
            print("\nORACLE SETTINGS")
            print("  [1] Change Model")
            print("  [2] Change Theme")
            print("  [3] Back to Chat")
            choice = input("Select option: ").strip().lower()
            if choice in ("3", "back", "b", "q"):
                break
            if choice == "1":
                print(f"Current model: {model}")
                candidate = input("Enter Groq model ID: ").strip()
                if not candidate or any(ch.isspace() for ch in candidate):
                    print("Invalid model ID. Nothing changed.")
                    continue
                model = candidate
                saved = read_settings()
                saved["model"] = model
                write_settings(saved)
                print(f"Model saved: {model}")
                print("The model will be checked by Groq on the next request.")
            elif choice == "2":
                print("  [1] Matrix Green")
                print("  [2] Cyber Cyan")
                print("  [3] Amber")
                print("  [4] Classic")
                selected = input("Choose theme: ").strip()
                theme_map = {"1": "matrix", "2": "cyber", "3": "amber", "4": "classic"}
                if selected not in theme_map:
                    print("Invalid choice. Theme unchanged.")
                    continue
                theme_name = theme_map[selected]
                palette = themes[theme_name]
                saved = read_settings()
                saved["theme"] = theme_name
                write_settings(saved)
                console.clear()
                render_interface()
                print(f"Theme changed to {theme_name.title()}.\n")
            else:
                print("Choose 1, 2, or 3.")

    try:
        while True:
            try:
                prompt = input(f"\033[{palette['prompt']}myou  >\033[0m ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not prompt:
                continue

            command = prompt.lower()
            if command in ("exit", "quit", "/exit"):
                break
            if command in ("new page", "new", "/new"):
                console.clear()
                render_interface()
                continue
            if command in ("settings", "setting", "/settings"):
                open_settings()
                console.clear()
                render_interface()
                continue
            if command in ("clear", "/clear"):
                messages = [{"role": "system", "content": SYSTEM_PROMPT}]
                print("Conversation context cleared.\n")
                continue
            if command in ("help", "/help"):
                print("Commands: settings · new page · clear · help · exit\n")
                continue

            messages.append({"role": "user", "content": prompt})
            print("\033[96moracle >\033[0m Thinking...", flush=True)
            try:
                answer = request_completion(messages, model, api_key)
            except RuntimeError as exc:
                messages.pop()
                print(f"\033[91mORACLE ERROR:\033[0m {exc}\n")
                continue

            messages.append({"role": "assistant", "content": answer})
            if len(messages) > 13:
                messages = [messages[0]] + messages[-12:]
            print(f"\033[{palette['reply']}moracle >\033[0m {answer}\n")
    finally:
        print("\n\033[92mROS ORACLE session closed.\033[0m")
    return 0


def run(args=None):
    args = list(args or [])
    action = args[0].lower() if args else "chat"
    if action in ("-h", "--help", "help"):
        print("ROS ORACLE — Groq-powered AI assistant")
        print("  ros oracle                 Start AI chat in current terminal")
        print("  ros oracle new             Open dedicated full-screen chat page")
        print("  settings (inside chat)     Change model or theme")
        print("  ros oracle setup           Securely save your Groq API key")
        print("  ros oracle status          Check setup and model")
        print("  ros oracle model MODEL_ID  Change the model ID")
        print("  ros oracle remove-key      Remove the locally saved API key")
        print("  ros ai                     Alias for ros oracle")
        return 0
    if action == "new":
        return chat_new()
    if action == "setup":
        return setup_key()
    if action == "status":
        return show_status()
    if action == "model":
        if len(args) != 2:
            print("Usage: ros oracle model MODEL_ID")
            return 1
        return set_model(args[1])
    if action == "remove-key":
        data = read_settings()
        if "api_key" not in data:
            print("No locally saved API key found.")
            return 0
        data.pop("api_key", None)
        write_settings(data)
        print("Locally saved API key removed. Environment variables are unchanged.")
        return 0
    if action != "chat":
        print(f"Unknown ORACLE action: {action}")
        print("Run 'ros oracle --help' for usage.")
        return 2
    return chat()
