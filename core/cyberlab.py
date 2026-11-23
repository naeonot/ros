#!/usr/bin/env python3
"""ROS Cyber Lab: safe local terminal experiments."""
import argparse
import base64
import hashlib
import getpass
import socket
import random
import shutil
import sys
import time
from rich.console import Console
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from rich import box

GREEN = "\033[38;5;46m"
NEON = "\033[38;5;46m"
CYAN = NEON
DIM = "\033[2m"
RESET = "\033[0m"
BOLD = "\033[1m"

def clear():
    print("\033[2J\033[H", end="")

def header():
    print(f"{GREEN}{BOLD}╔══════════════════════════════════════╗")
    print("║       ROS // CYBER OPERATIONS        ║")
    print(f"╚══════════════════════════════════════╝{RESET}")

def matrix():
    # Endless cinematic terminal animation. All scan data is fabricated locally.
    phases = (
        ("NETWORK DISCOVERY", "Mapping fictional nodes"),
        ("PORT ANALYSIS", "Inspecting simulated service ports"),
        ("FIREWALL AUDIT", "Reviewing fictional rule sets"),
        ("PACKET TRACE", "Following generated packet paths"),
        ("ENCRYPTION CHECK", "Testing simulated cipher layers"),
        ("SYSTEM INTEGRITY", "Verifying imaginary system modules"),
    )
    digits = "0123456789ABCDEF"
    width = max(36, shutil.get_terminal_size((80, 24)).columns - 1)
    height = max(16, shutil.get_terminal_size((80, 24)).lines - 1)
    hide_cursor = "\033[?25l"
    show_cursor = "\033[?25h"
    cyan = GREEN
    red = "\033[38;5;196m"
    yellow = "\033[38;5;226m"
    try:
        print(hide_cursor, end="", flush=True)
        phase_index = 0
        while True:
            phase, description = phases[phase_index % len(phases)]
            for progress in range(0, 101, 2):
                width = max(36, shutil.get_terminal_size((80, 24)).columns - 1)
                bar_width = max(12, min(30, width - 20))
                filled = int(bar_width * progress / 100)
                bar = "█" * filled + "░" * (bar_width - filled)
                hex_stream = " ".join("".join(random.choices(digits, k=2)) for _ in range(8))
                binary = " ".join("".join(random.choices("01", k=8)) for _ in range(4))
                node = f"192.0.2.{random.randint(1, 254)}"
                port = random.choice((21, 22, 53, 80, 443, 8080, 8443))
                frame = [
                    f"{GREEN}{BOLD}╔{'═' * (width - 2)}╗{RESET}",
                    f"{GREEN}{BOLD}║{' ROS // CYBER OPERATIONS ':^{width - 2}}║{RESET}",
                    f"{GREEN}{BOLD}╚{'═' * (width - 2)}╝{RESET}",
                    f"{GREEN}{BOLD}>>> {phase} <<< {RESET}",
                    f"{yellow}{BOLD}   SCANNING IN PROGRESS{RESET}",
                    f"   {description}",
                    "",
                    f"{GREEN}{BOLD}   [{bar}] {progress:03d}%{RESET}",
                    "",
                    f"{GREEN}{BOLD}   ENCRYPTED DATA STREAM{RESET}",
                    f"   0x{hex_stream}",
                    f"   BIN: {binary}",
                    "",
                    f"{GREEN}{BOLD}   SIMULATED NODE // LOCAL SANDBOX{RESET}",
                    f"   NODE: {node}     PORT: {port}",
                    f"   SESSION: 0x{''.join(random.choices(digits, k=8))}",
                    f"   PACKETS: {random.randint(1200, 98000):,}   |   LATENCY: {random.randint(2, 98)} ms",
                    "",
                    f"{red}{BOLD}   !! SIMULATION ONLY - NO REAL SCANNING !!{RESET}",
                    f"{DIM}   PHASE {phase_index + 1}  //  CTRL+C TO EXIT{RESET}",
                ]
                print("\033[2J\033[H" + "\n".join(frame[:height]), end="", flush=True)
                time.sleep(0.10)
            phase_index += 1
    except KeyboardInterrupt:
        pass
    finally:
        print(show_cursor + RESET + "\033[0m\nROS Matrix simulation stopped.")

def fire(seconds=6):
    palette = [" ", ".", ":", "*", "🔥", "▓", "▒"]
    end = time.time() + seconds
    width = max(12, shutil.get_terminal_size((40, 20)).columns - 1)
    try:
        while time.time() < end:
            row = "".join(random.choices(palette, weights=[2, 3, 4, 4, 1, 2, 3], k=width))
            print(f"\033[38;5;{random.choice([202,208,214,220])}m{row}{RESET}")
            time.sleep(0.12)
    except KeyboardInterrupt:
        pass
    finally:
        print(RESET + "\nFire simulation stopped.")

def encrypt():
    print(f"{CYAN}LOCAL BASE64 ENCODER / DECODER{RESET}")
    mode = input("Encode or decode? [e/d]: ").strip().lower()
    value = input("Message: ")
    try:
        if mode == "e":
            result = base64.urlsafe_b64encode(value.encode()).decode()
        elif mode == "d":
            result = base64.urlsafe_b64decode(value.encode()).decode()
        else:
            print("Choose e or d."); return
        print(f"\n{GREEN}Result:{RESET} {result}")
        print(f"{DIM}Note: Base64 is encoding, not secure encryption.{RESET}")
    except Exception as exc:
        print(f"Invalid input: {exc}")

def password_check():
    print(f"{CYAN}LOCAL PASSWORD STRENGTH CHECKER{RESET}")
    print("Input is checked locally and is not saved or transmitted.")
    value = getpass.getpass("Password to evaluate (hidden): ")
    if not value:
        print("No password entered."); return
    score = 0
    checks = [
        (len(value) >= 8, "At least 8 characters"),
        (len(value) >= 12, "At least 12 characters"),
        (any(c.islower() for c in value), "Lowercase letter"),
        (any(c.isupper() for c in value), "Uppercase letter"),
        (any(c.isdigit() for c in value), "Number"),
        (any(not c.isalnum() for c in value), "Symbol"),
    ]
    for passed, label in checks:
        score += int(passed)
        print(f"{'[+] ' if passed else '[-] '}{label}")
    level = "WEAK" if score <= 2 else "FAIR" if score <= 4 else "STRONG"
    color = "red" if score <= 2 else "yellow" if score <= 4 else GREEN
    print(f"\nStrength: {color}{BOLD}{level}{RESET} ({score}/6 checks)")
    print("This is a basic heuristic, not a guarantee against password attacks.")

def hash_tool():
    print(f"{CYAN}LOCAL HASH GENERATOR{RESET}")
    value = input("Text to hash: ")
    data = value.encode("utf-8")
    for name in ("sha256", "sha512", "sha3_256"):
        digest = hashlib.new(name, data).hexdigest()
        print(f"\n{GREEN}{name.upper()}{RESET}\n{digest}")
    print("\nHashes are one-way digests; they are not encryption.")

def network_info():
    print(f"{CYAN}LOCAL NETWORK DIAGNOSTICS{RESET}")
    try:
        host = socket.gethostname()
        print(f"Hostname: {host}")
        info = socket.getaddrinfo(host, None, family=socket.AF_INET)
        addresses = sorted({item[4][0] for item in info})
        print("Local IPv4: " + (", ".join(addresses) if addresses else "Not reported"))
    except OSError as exc:
        print(f"Local address lookup unavailable: {exc}")
    print("\nNo ports are scanned and no external hosts are contacted.")

def challenge():
    code = f"{random.randrange(100, 1000)}"
    print(f"{CYAN}SECURITY SIMULATION // Guess the 3-digit code{RESET}")
    print("You have 7 attempts. This is a local game, not a real login.")
    for attempt in range(1, 8):
        guess = input(f"Attempt {attempt}/7 > ").strip()
        if not guess.isdigit() or len(guess) != 3:
            print("Enter exactly three digits."); continue
        if guess == code:
            print(f"{GREEN}ACCESS GRANTED — puzzle solved.{RESET}"); return
        correct = sum(a == b for a, b in zip(guess, code))
        print(f"Hint: {correct} digit(s) are correct and in the right position.")
    print(f"Challenge ended. The code was {code}.")

def menu():
    console = Console()
    neon = "#39ff14"
    modules = [
        ("01  MATRIX RAIN", "Animated hexadecimal stream", "Visual simulation"),
        ("02  FIRE SIMULATION", "Terminal particle effect", "Local visual effect"),
        ("03  BASE64 TOOL", "Encode / decode text", "Text transformation"),
        ("04  PASSWORD CHECK", "Basic strength assessment", "Input stays local"),
        ("05  HASH GENERATOR", "SHA-256 / SHA-512 / SHA3-256", "One-way digests"),
        ("06  NETWORK INFO", "Hostname and local IPv4", "No port scanning"),
        ("07  ACCESS PUZZLE", "Three-digit logic challenge", "Local security game"),
    ]
    while True:
        clear()
        console.print(Panel.fit(
            Text.assemble(("ROS", f"bold {neon}"), ("  //  CYBER OPERATIONS LAB", "bold white"),
                          ("\nLOCAL SANDBOX  •  SEVEN MODULES", "dim")),
            border_style=neon, box=box.DOUBLE, padding=(1, 3)))
        cards = [Panel(
            f"[bold {neon}]{number}[/]\n[bold white]{name[4:]}[/]\n[dim]{desc}[/]\n\n[white]{kind}[/]",
            title=f"MODULE {number}", border_style=neon, box=box.HEAVY,
            padding=(1, 2), expand=True)
            for number, name, desc, kind in [
                (f"{i:02d}", title, desc, kind) for i, (title, desc, kind) in enumerate(modules, 1)
            ]]
        console.print(Columns(cards, equal=True, expand=True))
        console.print(Panel(
            "[bold #39ff14]01[/] Matrix  [bold #39ff14]02[/] Fire  [bold #39ff14]03[/] Base64  [bold #39ff14]04[/] Password\n"
            "[bold #39ff14]05[/] Hash  [bold #39ff14]06[/] Network  [bold #39ff14]07[/] Puzzle  [bold #39ff14]Q[/] Exit",
            title="COMMAND INPUT", subtitle="ROS-LAB:// SELECT MODULE",
            border_style=neon, box=box.HEAVY, padding=(0, 2)))
        choice = input("\033[38;5;46mROS-LAB://\033[0m ").strip().lower()
        if choice in ("1", "01"): matrix()
        elif choice in ("2", "02"): fire()
        elif choice in ("3", "03"): encrypt()
        elif choice in ("4", "04"): password_check()
        elif choice in ("5", "05"): hash_tool()
        elif choice in ("6", "06"): network_info()
        elif choice in ("7", "07"): challenge()
        elif choice == "q": break
        else: print("Unknown module."); time.sleep(0.8)
        if choice != "q": input("\nPress Enter to return to Cyber Operations...")

def main():
    parser = argparse.ArgumentParser(description="ROS Cyber Lab")
    parser.add_argument("mode", nargs="?", choices=["matrix", "fire", "encode", "decode", "challenge", "menu"], default="menu")
    parser.add_argument("value", nargs="?", default="")
    args = parser.parse_args()
    if args.mode == "menu": menu()
    elif args.mode == "matrix": matrix()
    elif args.mode == "fire": fire()
    elif args.mode == "encode":
        print(base64.urlsafe_b64encode(args.value.encode()).decode())
    elif args.mode == "decode":
        try: print(base64.urlsafe_b64decode(args.value.encode()).decode())
        except Exception as exc: print(f"Invalid Base64: {exc}")
    elif args.mode == "challenge": challenge()

if __name__ == "__main__":
    main()
