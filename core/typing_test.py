import random
import sys
import time
import select
import termios
import tty
import shutil
import textwrap

PARAGRAPHS = [
    "A focused mind turns small daily actions into meaningful progress. Consistency matters more than speed.",
    "Technology is useful when we understand it and use it to solve real problems. Curiosity helps us learn.",
    "Every journey begins with one step. Some days bring progress, while others teach patience. Both matter.",
    "Reading expands our understanding and gives us new ways to express our thoughts. Practice makes writing clear.",
    "Good habits grow through repeated actions, not sudden motivation. A realistic plan makes goals manageable.",
    "When a program fails, checking each small part can reveal the cause and help us find a reliable solution.",
    "Time is limited, so choosing what deserves our attention is important. Focus grows when we remove distractions."
]

C = {
    "reset": "\033[0m", "cyan": "\033[96m", "green": "\033[92m",
    "red": "\033[91m", "yellow": "\033[93m", "dim": "\033[2m",
    "bold": "\033[1m", "white": "\033[97m", "magenta": "\033[95m"
}

def score(typed, target, elapsed):
    correct = sum(1 for i, ch in enumerate(typed) if i < len(target) and ch == target[i])
    accuracy = correct / len(typed) * 100 if typed else 100.0
    wpm = (correct / 5) / max(elapsed / 60, 1 / 60)
    return correct, accuracy, wpm

def play():
    if not sys.stdin.isatty():
        print("ROS TT needs an interactive Termux terminal.")
        return
    target = random.choice(PARAGRAPHS)
    typed = ""
    started = None
    fd = sys.stdin.fileno()
    previous = termios.tcgetattr(fd)
    finished = False
    last_draw = 0.0

    def render(now):
        cols = shutil.get_terminal_size((40, 24)).columns
        width = max(24, min(cols, 46))
        inner = width - 6
        elapsed = 0 if started is None else now - started
        remaining = max(0, 60 - elapsed)
        correct, accuracy, wpm = score(typed, target, max(elapsed, 0.01))
        def wrap(s):
            return textwrap.wrap(s, width=inner, break_long_words=True, break_on_hyphens=False) or [""]
        lines = [
            C["cyan"] + C["bold"] + "  ╭" + "─"*(width-4) + "╮" + C["reset"],
            C["cyan"] + C["bold"] + "  │" + "  ROS  /  TYPING TEST".ljust(width-4) + "│" + C["reset"],
            C["cyan"] + C["bold"] + "  ╰" + "─"*(width-4) + "╯" + C["reset"],
            "",
            "  " + C["yellow"] + C["bold"] + f"{remaining:04.1f}s" + C["reset"] +
            "   " + C["green"] + f"{wpm:4.1f} WPM" + C["reset"] +
            "   " + C["magenta"] + f"{accuracy:4.1f}%" + C["reset"],
            "  " + C["dim"] + "TIME          SPEED       ACCURACY" + C["reset"],
            "",
            "  " + C["cyan"] + C["bold"] + "01  PASSAGE" + C["reset"],
            "  " + C["dim"] + "┌" + "─"*(width-4) + "┐" + C["reset"]
        ]
        for line in wrap(target):
            lines.append("  " + C["white"] + "│ " + line.ljust(inner) + " │" + C["reset"])
        lines.extend([
            "  " + C["dim"] + "└" + "─"*(width-4) + "┘" + C["reset"],
            "",
            "  " + C["magenta"] + C["bold"] + "02  YOUR TYPING" + C["reset"],
            "  " + C["dim"] + "┌" + "─"*(width-4) + "┐" + C["reset"]
        ])
        if typed:
            for start in range(0, len(typed), inner):
                chunk = typed[start:start+inner]
                painted = ""
                for j, ch in enumerate(chunk, start):
                    colour = C["green"] if j < len(target) and ch == target[j] else C["red"]
                    painted += colour + ch + C["reset"]
                lines.append("  " + C["dim"] + "│ " + C["reset"] + painted +
                             " "*(inner-len(chunk)) + C["dim"] + " │" + C["reset"])
        else:
            lines.append("  " + C["dim"] + "│ Start typing here..." .ljust(inner+1) + "│" + C["reset"])
        progress = int(12 * min(elapsed, 60) / 60)
        lines.extend([
            "  " + C["dim"] + "└" + "─"*(width-4) + "┘" + C["reset"],
            "",
            "  " + C["cyan"] + "▰"*progress + C["dim"] + "▱"*(12-progress) + C["reset"] +
            C["dim"] + f"  {len(typed)}/{len(target)} chars" + C["reset"],
            "  " + C["dim"] + "Backspace undo  ·  Enter finish  ·  Ctrl+C quit" + C["reset"]
        ])
        return "\n".join(lines)

    def draw(now):
        sys.stdout.write("\033[H" + render(now) + "\033[J")
        sys.stdout.flush()

    try:
        tty.setraw(fd)
        sys.stdout.write("\033[2J\033[H\033[?25l")
        sys.stdout.flush()
        while True:
            now = time.monotonic()
            if started is not None and now - started >= 60:
                finished = True
                break
            if now - last_draw >= 1.0:
                draw(now)
                last_draw = now
            ready, _, _ = select.select([fd], [], [], 0.08)
            if not ready:
                continue
            key = sys.stdin.read(1)
            if key == "\x03":
                break
            if key in ("\r", "\n"):
                if typed:
                    finished = True
                    break
                continue
            if key in ("\x7f", "\b"):
                typed = typed[:-1]
                draw(time.monotonic())
                last_draw = time.monotonic()
                continue
            if key.isprintable() and len(typed) < len(target):
                if started is None:
                    started = time.monotonic()
                typed += key
                draw(time.monotonic())
                last_draw = time.monotonic()
                if len(typed) >= len(target):
                    finished = True
                    break
    except KeyboardInterrupt:
        pass
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, previous)
        sys.stdout.write("\033[0m\033[?25h\n")
        sys.stdout.flush()

    if not finished and not typed:
        return
    elapsed = 0 if started is None else min(time.monotonic() - started, 60)
    correct, accuracy, wpm = score(typed, target, max(elapsed, 0.01))
    print("\n" + C["cyan"] + C["bold"] + "  ROS TYPING TEST / RESULTS" + C["reset"])
    print("  " + C["green"] + f"Speed: {wpm:.1f} WPM" + C["reset"])
    print("  " + C["magenta"] + f"Accuracy: {accuracy:.1f}%" + C["reset"])
    print(f"  Correct characters: {correct}/{len(typed)}")
    print(f"  Time: {elapsed:.1f} seconds")
    if not typed:
        print("  No typing recorded. Try another round!")
    elif accuracy >= 95:
        print("  Excellent accuracy. Keep building speed without losing control.")
    elif accuracy >= 85:
        print("  Good attempt. Focus on reducing mistakes.")
    else:
        print("  Slow down a little and prioritise accuracy.")
    print("\n  Run ros tt again for a new random paragraph.")

if __name__ == "__main__":
    play()
