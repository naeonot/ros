import json, random, textwrap, shutil
from datetime import datetime
from pathlib import Path

STORE = Path.home() / ".local/share/ros/connect.json"
AI = {
    "Alex": ("Curious", "curious"),
    "Nova": ("Tech-minded", "tech"),
    "Milo": ("Funny", "fun"),
}

RESET = "\033[0m"
CYAN = "\033[96m"
GREEN = "\033[92m"
DIM = "\033[2m"
WHITE = "\033[1;97m"

def load():
    STORE.parent.mkdir(parents=True, exist_ok=True)
    try:
        d = json.loads(STORE.read_text())
        if not isinstance(d, dict): raise ValueError()
    except (OSError, ValueError):
        d = {}
    d.setdefault("people", [])
    d.setdefault("chats", {})
    return d

def save(d):
    STORE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STORE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=2))
    tmp.replace(STORE)

def clear():
    print("\033[2J\033[H", end="")

def header(title, sub="", width=36):
    width = max(18, min(width, 54))
    inner = width - 2
    print(CYAN + "╭" + "─" * inner + "╮")
    print("│" + WHITE + " ROS CONNECT".ljust(inner) + CYAN + "│")
    print("╰" + "─" * inner + "╯" + RESET)
    print("\\n" + WHITE + title[:inner] + RESET)
    if sub: print(DIM + sub[:inner] + RESET)
    print()

def display_width(value):
    import unicodedata
    return sum(0 if unicodedata.combining(ch) else (2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1) for ch in value)

def wrap_display(value, limit):
    words = value.split()
    lines, line = [], ""
    for word in words:
        candidate = word if not line else line + " " + word
        if line and display_width(candidate) > limit:
            lines.append(line)
            line = word
        else:
            line = candidate
        while display_width(line) > limit:
            part, rest = "", ""
            for ch in line:
                if display_width(part + ch) <= limit: part += ch
                else: rest += ch
            if part: lines.append(part)
            line = rest
    if line: lines.append(line)
    return lines or [""]


def reply(name, msg):
    style = AI[name][1]
    m = msg.lower()
    if any(x in m for x in ("hello", "hi", "hey")):
        options = {
            "curious": ["Hey! What's on your mind today?", "Hi! What shall we talk about?"],
            "tech": ["Hey! Building or learning something interesting?", "Hi! Any tech ideas today?"],
            "fun": ["Yooo! What's the latest? 😄", "Hey! Good to see you!"],
        }
    elif any(x in m for x in ("sad", "upset", "bad day")):
        options = {
            "curious": ["That sounds rough. Want to tell me what happened?"],
            "tech": ["Sorry it's been rough. Want to talk or find a distraction?"],
            "fun": ["Oof. Sending a virtual cup of tea ☕ Want to vent?"],
        }
    elif "?" in msg:
        options = {
            "curious": ["Interesting question. What have you considered so far?"],
            "tech": ["Let's break it into smaller parts and reason it through."],
            "fun": ["Big question alert 😄 Give me a little more context!"],
        }
    else:
        options = {
            "curious": ["I get you. Tell me a little more.", "That's worth thinking about. What happened next?"],
            "tech": ["Makes sense. Want to break it down step by step?"],
            "fun": ["Noted! And then what happened? 😄"],
        }
    return random.choice(options[style])

def draw_message(item, name, width):
    own = item["from"] == "you"
    label = "You" if own else name
    colour = CYAN if own else GREEN
    # Keep every message left-aligned; the blank line between messages separates turns.
    max_text = max(10, min(44, width - 4))
    lines = wrap_display(item["text"], max_text)
    stamp = item.get("time", "")
    label_line = label + ("  " + stamp if stamp else "")
    pad = " "
    print(pad + colour + label_line + RESET)
    for line in lines:
        print(pad + WHITE + line + RESET)

def open_chat(d, name, is_ai):
    key = ("ai:" if is_ai else "person:") + name
    history = d["chats"].setdefault(key, [])
    while True:
        clear()
        width = shutil.get_terminal_size((40, 24)).columns
        width = max(18, min(width, 60))
        header(name, ("AI friend · " + AI[name][0] + " · offline demo") if is_ai else "Person contact · local-only chat", width=width)
        for item in history[-10:]:
            draw_message(item, name, width)
            print()
        if not history: print(DIM + "No messages yet. Say hello!" + RESET + "\n")
        if is_ai:
            print(DIM + "Demo personality only; connect an AI provider for real AI replies." + RESET)
        else:
            print("\033[93mLocal-only:\033[0m saved on this device, not delivered.")
            print(DIM + "Human messaging needs a ROS server/backend." + RESET)
        try: msg = input("\nYou > ").strip()
        except (EOFError, KeyboardInterrupt): return
        if msg.lower() in ("/back", "/exit", "q"):
            save(d)
            return
        if not msg: continue
        now = datetime.now().strftime("%H:%M")
        history.append({"from":"you", "text":msg, "time":now})
        if is_ai:
            history.append({"from":"friend", "text":reply(name, msg), "time":datetime.now().strftime("%H:%M")})
        save(d)

def add_person(d):
    clear()
    header("ADD A PERSON", "Create a local contact")
    name = input("Display name: ").strip()[:32]
    if name and name.lower() not in [x.lower() for x in d["people"]]:
        d["people"].append(name)
        save(d)
        print("\nContact saved.")
    elif name:
        print("\nThat contact already exists.")
    input("Press Enter...")

def run():
    d = load()
    while True:
        clear()
        header("YOUR CONNECTIONS", "Select a friend to open a conversation")
        print(CYAN + "AI FRIENDS" + RESET)
        names = list(AI)
        for i, name in enumerate(names, 1):
            print(f"  {i}. {name:<12} {DIM}{AI[name][0]}{RESET}")
        base = len(names)
        print("\n" + CYAN + "PEOPLE" + RESET)
        if d["people"]:
            for i, name in enumerate(d["people"], base+1): print(f"  {i}. {name}")
        else: print("  " + DIM + "No contacts yet." + RESET)
        print("\n  A. Add person")
        print("  Q. Exit")
        print("\n" + DIM + "AI = offline demo replies | People = local saved messages only" + RESET)
        try: choice = input("\nSelect > ").strip()
        except (EOFError, KeyboardInterrupt): print(); return
        if choice.lower() == "q": return
        if choice.lower() == "a":
            add_person(d); continue
        if not choice.isdigit(): continue
        n = int(choice)
        if 1 <= n <= base: open_chat(d, names[n-1], True)
        elif base < n <= base + len(d["people"]): open_chat(d, d["people"][n-base-1], False)

if __name__ == "__main__":
    run()
