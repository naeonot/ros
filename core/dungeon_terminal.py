import os
import random
import sys
import termios
import tty
import select
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()
W, H = 15, 9
MAX_FLOOR = 5

def read_key():
    """Read keys as raw bytes so CSI and SS3 arrow keys work reliably."""
    if not sys.stdin.isatty():
        raise EOFError
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        first = os.read(fd, 1)
        if first == b"\x1b":
            seq = b""
            # Supports ESC [ A, ESC O A and modified CSI arrow sequences.
            while len(seq) < 16 and select.select([fd], [], [], 0.18)[0]:
                part = os.read(fd, 1)
                if not part:
                    break
                seq += part
                if part.isalpha() or part == b"~":
                    break
            if seq.endswith(b"A"): return "w"
            if seq.endswith(b"B"): return "s"
            if seq.endswith(b"D"): return "a"
            if seq.endswith(b"C"): return "d"
            return "escape"
        try:
            return first.decode("utf-8").lower()
        except UnicodeDecodeError:
            return ""
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

class Dungeon:
    def __init__(self):
        self.floor=1; self.hp=self.max_hp=24; self.attack=5
        self.potions=2; self.coins=self.kills=0; self.running=True
        self.victory=False
        self.message="Find the stairs. Survive."
        self.new_floor()

    def new_floor(self):
        self.player=[1,1]; self.stairs=[W-2,H-2]
        self.walls=({(x,0) for x in range(W)}|{(x,H-1) for x in range(H)}|
                    {(0,y) for y in range(H)}|{(W-1,y) for y in range(H)})
        for _ in range(18):
            x,y=random.randint(2,W-3),random.randint(2,H-3)
            if (x,y) not in (tuple(self.player),tuple(self.stairs)): self.walls.add((x,y))
        self.walls.discard(tuple(self.player)); self.walls.discard(tuple(self.stairs))
        free=[(x,y) for y in range(1,H-1) for x in range(1,W-1)
              if (x,y) not in self.walls and (x,y) not in (tuple(self.player),tuple(self.stairs))]
        random.shuffle(free); self.enemies=[]
        for _ in range(min(3+self.floor,7,len(free))):
            x,y=free.pop(); hp=7+self.floor
            self.enemies.append({"x":x,"y":y,"hp":hp,"atk":2+self.floor//2,
                                 "name":random.choice(["Goblin","Slime","Skeleton"])})
        self.items={}
        for _ in range(min(4,len(free))): self.items[free.pop()]=random.choice(["coin","potion","chest"])

    def render(self):
        rows=[]; enemies={(e["x"],e["y"]):e for e in self.enemies}
        for y in range(H):
            row=Text()
            for x in range(W):
                pos=(x,y)
                if pos==tuple(self.player): row.append("😄 ",style="bold bright_cyan")
                elif pos==tuple(self.stairs): row.append(" ◆ ",style="bold yellow")
                elif pos in enemies: row.append(" ☠ ",style="bold bright_red")
                elif pos in self.items:
                    icon,style={"coin":(" ● ","bold yellow"),"potion":(" ♥ ","bold magenta"),"chest":(" ▣ ","bold white")}[self.items[pos]]
                    row.append(icon,style=style)
                elif pos in self.walls: row.append("###",style="bold #53657d")
                else: row.append(" · ",style="#35465a")
            rows.append(row)
        board=Panel(Text("\n").join(rows),title=f"[bold bright_cyan]ROS DUNGEON[/] [dim]FLOOR {self.floor:02}/{MAX_FLOOR}[/]",border_style="bright_cyan")
        stats=Table.grid(expand=True)
        for _ in range(4): stats.add_column()
        stats.add_row(f"[red]♥ {self.hp}/{self.max_hp}[/]",f"[cyan]⚔ {self.attack}[/]",f"[yellow]● {self.coins}[/]",f"[magenta]☘ {self.potions}[/]")
        return Group(board,stats,
            Text("😄 You  ☠ Monster  ◆ Stairs  ● Coins  ♥ Potion  ▣ Chest  ### Wall",style="dim"),
            Text(self.message,style="italic bright_white"),
            Text.from_markup("[bold cyan]WASD / Arrow keys[/] move   [magenta]P[/] potion   [yellow]E[/] wait   [red]Q[/] quit"))

    def enemy_turn(self):
        for e in list(self.enemies):
            dx=self.player[0]-e["x"]; dy=self.player[1]-e["y"]
            if abs(dx)+abs(dy)==1:
                self.hp-=e["atk"]; self.message=f"{e['name']} hits you for {e['atk']} damage!"
                continue
            steps=[(1 if dx>0 else -1,0),(0,1 if dy>0 else -1)]; random.shuffle(steps)
            occupied={(m["x"],m["y"]) for m in self.enemies if m is not e}
            for sx,sy in steps:
                nx,ny=e["x"]+sx,e["y"]+sy
                if (nx,ny) not in self.walls and (nx,ny) not in occupied and [nx,ny]!=self.player and [nx,ny]!=self.stairs:
                    e["x"],e["y"]=nx,ny; break
        if self.hp<=0: self.hp=0; self.running=False

    def move(self,dx,dy):
        nx,ny=self.player[0]+dx,self.player[1]+dy
        if (nx,ny) in self.walls: self.message="A stone wall blocks your path."; return
        enemy=next((e for e in self.enemies if (e["x"],e["y"])==(nx,ny)),None)
        if enemy:
            enemy["hp"]-=self.attack; self.message=f"You strike {enemy['name']} for {self.attack} damage."
            if enemy["hp"]<=0:
                self.enemies.remove(enemy); self.kills+=1; reward=random.randint(2,5); self.coins+=reward
                self.message=f"Enemy defeated! +{reward} coins."
        else:
            self.player=[nx,ny]; item=self.items.pop((nx,ny),None)
            if item=="coin":
                reward=random.randint(3,7); self.coins+=reward; self.message=f"You found {reward} coins!"
            elif item=="potion": self.potions+=1; self.message="Potion collected."
            elif item=="chest":
                prize=random.choice(["attack","heal","coins"])
                if prize=="attack": self.attack+=1; self.message="Chest: attack +1!"
                elif prize=="heal": self.hp=min(self.max_hp,self.hp+8); self.message="Chest: recovered up to 8 HP."
                else: self.coins+=12; self.message="Chest: +12 coins!"
            if self.player==self.stairs:
                if self.floor >= MAX_FLOOR:
                    self.victory=True; self.running=False
                    self.message="You conquered all five floors!"
                    return
                self.floor+=1; self.hp=min(self.max_hp,self.hp+3); self.new_floor()
                self.message=f"You descend to floor {self.floor}! +3 HP."
                return
        self.enemy_turn()

    def use_potion(self):
        if self.potions<=0: self.message="No potions left."; return
        if self.hp==self.max_hp: self.message="Health is already full."; return
        self.potions-=1; healed=min(10,self.max_hp-self.hp); self.hp+=healed
        self.message=f"Potion restores {healed} HP."; self.enemy_turn()

def play():
    game=Dungeon()
    try:
        with Live(game.render(), console=console, screen=True, auto_refresh=False, vertical_overflow="visible") as live:
            while game.running:
                key=read_key()
                if key=="q": game.message="You left the dungeon."; break
                if key in ("w","a","s","d"):
                    dx,dy={"w":(0,-1),"s":(0,1),"a":(-1,0),"d":(1,0)}[key]
                    game.move(dx,dy)
                elif key=="p": game.use_potion()
                elif key=="e":
                    game.hp=min(game.max_hp,game.hp+1); game.message="You rest and recover 1 HP."; game.enemy_turn()
                live.update(game.render(), refresh=True)
    except (EOFError,KeyboardInterrupt):
        pass

    if game.victory:
        console.print(Panel(f"[bold green]😎 YOU WIN![/]\nAll {MAX_FLOOR} floors conquered!\nEnemies defeated: {game.kills}\nCoins collected: {game.coins}",title="ROS DUNGEON",border_style="green"))
    elif game.hp<=0:
        console.print(Panel(f"[bold red]🤕 YOU LOST[/]\nFloor reached: {game.floor}\nEnemies defeated: {game.kills}\nCoins collected: {game.coins}",title="ROS DUNGEON",border_style="red"))
    else:
        console.print("[yellow]You returned safely to ROS.[/]")

if __name__=="__main__": play()
