#!/usr/bin/env python3
"""ROS Daily Desk: local-first productivity workspace."""
import json, os, sys, time
from datetime import date, datetime
from pathlib import Path

DATA_FILE = Path.home() / ".local/share/ros-desk/data.json"
G='\033[38;5;46m'; DG='\033[38;5;22m'; C='\033[38;5;51m'; Y='\033[38;5;226m'; R='\033[0m'; B='\033[1m'; D='\033[2m'
W=74

def load_data():
    try:
        data=json.loads(DATA_FILE.read_text())
        if not isinstance(data,dict): raise ValueError('invalid data')
    except (OSError,ValueError): data={}
    data.setdefault('tasks',[]); data.setdefault('notes',[]); data.setdefault('habits',[])
    data.setdefault('habit_log',{}); data.setdefault('focus_minutes',0)
    return data

def save_data(data):
    DATA_FILE.parent.mkdir(parents=True,exist_ok=True)
    tmp=DATA_FILE.with_suffix('.tmp'); tmp.write_text(json.dumps(data,indent=2,ensure_ascii=False)); tmp.replace(DATA_FILE)

def clear():
    if sys.stdout.isatty(): print('\033[2J\033[H',end='')

def line(left='├',fill='─',right='┤'):
    print(G+left+fill*(W-2)+right+R)

def row(text='', color=R):
    # Content is clipped to terminal frame width; ANSI is kept outside the padding calculation.
    text=str(text)
    visible=text[:W-4]
    print(G+'│'+R+'  '+color+visible+R+' ' * max(0,W-4-len(visible))+G+'│'+R)

def screen(data, title='DAILY DESK', subtitle='PERSONAL PRODUCTIVITY SYSTEM'):
    clear(); today=date.today().isoformat(); done=sum(bool(t.get('done')) for t in data['tasks']); total=len(data['tasks'])
    checked=sum(h in data['habit_log'].get(today,[]) for h in data['habits'])
    now=datetime.now().astimezone().strftime('%a, %d %b %Y  %H:%M:%S %Z')
    print(G+B+'╔'+'═'*(W-2)+'╗'+R)
    row('R O S   /   D A I L Y   D E S K',B+C)
    row(subtitle,D)
    line('╠','═','╣')
    row(f'{now}',D)
    line('╠','═','╣')
    row('WORKSPACE OVERVIEW',B+C)
    row(f'TASKS       {done:02d}/{total:02d} complete')
    row(f'HABITS      {checked:02d}/{len(data["habits"]):02d} checked today')
    row(f'FOCUS       {data["focus_minutes"]:04d} minutes recorded')
    line('╠','═','╣')
    row(title,B+C)

def footer(prompt='desk>'):
    line('╚','═','╝')
    return input('\n'+G+B+prompt+R+' ').strip().lower()

def pause(): input('\n  Press Enter to continue...')

def tasks(data):
    while True:
        screen(data,'TASK CONTROL','TASK QUEUE  /  LOCAL STORAGE')
        if not data['tasks']: row('No tasks yet. Add one to start.',D)
        for i,t in enumerate(data['tasks'],1):
            mark=G+'[✓]'+R if t.get('done') else Y+'[ ]'+R
            # print as a dedicated line to preserve color and alignment
            label=f'{i:02d}  {mark}  {t["text"]}'
            print(G+'│'+R+'  '+label[:W-4]+' ' * max(0,W-4-len(label[:W-4]))+G+'│'+R)
        row('[A] Add task    [T] Toggle status    [D] Delete    [B] Back',B)
        c=footer('desk/tasks>')
        if c=='b': return
        if c=='a':
            value=input('  New task: ').strip()
            if value: data['tasks'].append({'text':value[:160],'done':False,'created':date.today().isoformat()}); save_data(data)
        elif c in ('t','d'):
            try:
                n=int(input('  Task number: '))
                if 1<=n<=len(data['tasks']):
                    if c=='t': data['tasks'][n-1]['done']=not data['tasks'][n-1].get('done',False)
                    else: data['tasks'].pop(n-1)
                    save_data(data)
            except ValueError: pass

def habits(data):
    while True:
        today=date.today().isoformat(); checked=data['habit_log'].setdefault(today,[])
        screen(data,'HABIT TRACKER','CONSISTENCY  /  DAILY CHECK-IN')
        if not data['habits']: row('No habits configured. Add a small repeatable action.',D)
        for i,h in enumerate(data['habits'],1):
            mark=G+'[✓]'+R if h in checked else Y+'[ ]'+R
            label=f'{i:02d}  {mark}  {h}'
            print(G+'│'+R+'  '+label[:W-4]+' ' * max(0,W-4-len(label[:W-4]))+G+'│'+R)
        row('[A] Add habit    [T] Toggle today    [D] Delete    [B] Back',B)
        c=footer('desk/habits>')
        if c=='b': return
        if c=='a':
            h=input('  Habit name: ').strip()
            if h and h not in data['habits']: data['habits'].append(h[:70]); save_data(data)
        elif c in ('t','d'):
            try:
                n=int(input('  Habit number: '))
                if 1<=n<=len(data['habits']):
                    h=data['habits'][n-1]
                    if c=='t': checked.remove(h) if h in checked else checked.append(h)
                    else:
                        data['habits'].pop(n-1)
                        for day in data['habit_log'].values():
                            if h in day: day.remove(h)
                    save_data(data)
            except ValueError: pass

def notes(data):
    while True:
        screen(data,'NOTES ARCHIVE','QUICK CAPTURE  /  SAVED LOCALLY')
        if not data['notes']: row('Your notes will appear here.',D)
        for i,n in enumerate(data['notes'],1): row(f'{i:02d}  {n["created"]}  {n["text"].replace(chr(10)," / ")[:42]}')
        row('[A] New note    [V] View note    [D] Delete    [B] Back',B)
        c=footer('desk/notes>')
        if c=='b': return
        if c=='a':
            print('  Enter note text. Finish with a single . line:'); lines=[]
            while True:
                s=input('  ')
                if s=='.': break
                lines.append(s)
            content='\n'.join(lines).strip()
            if content: data['notes'].append({'text':content[:4000],'created':date.today().isoformat()}); save_data(data)
        elif c in ('v','d'):
            try:
                n=int(input('  Note number: '))
                if 1<=n<=len(data['notes']):
                    if c=='v': print('\n'+data['notes'][n-1]['text']); pause()
                    else: data['notes'].pop(n-1); save_data(data)
            except ValueError: pass

def focus(data):
    screen(data,'FOCUS PROTOCOL','DEEP WORK  /  INTERRUPTIONS DISCOURAGED')
    raw=input('\n  Session length in minutes [25]: ').strip()
    try:
        minutes=int(raw) if raw else 25
        if not 1<=minutes<=180: raise ValueError
    except ValueError: print('  Enter a whole number from 1 to 180.'); pause(); return
    print(f'\n  {C}SESSION ARMED{R}  /  {minutes} minutes  /  Ctrl+C cancels')
    try:
        end=time.monotonic()+minutes*60
        while True:
            left=int(end-time.monotonic())
            if left<=0: break
            mm,ss=divmod(left,60); width=30; elapsed=minutes*60-left; pct=elapsed/(minutes*60)
            filled=round(width*pct)
            print(f'\r  {G}{B}'+('█'*filled)+DG+('░'*(width-filled))+R+f'  {mm:02d}:{ss:02d} remaining',end='',flush=True)
            time.sleep(1)
        print(f'\n\n  {G}{B}FOCUS SESSION COMPLETE{R}'); data['focus_minutes']+=minutes; save_data(data); print('\a',end='',flush=True)
    except KeyboardInterrupt: print('\n  Session cancelled; incomplete time was not recorded.')
    pause()

def run(argv=None):
    args=list(argv or [])
    if args and args[0] in ('--help','-h','help'):
        print('ROS Daily Desk\nUsage: ros desk [--help]\nLocal tasks, focus timer, notes and habit tracking.'); return 0
    data=load_data(); actions={'1':tasks,'2':focus,'3':notes,'4':habits}
    while True:
        screen(data,'WORKSPACE MODULES','YOUR LOCAL PRODUCTIVITY CONSOLE')
        row('[01]  TASK MANAGER       Plan, prioritize and complete work')
        row('[02]  FOCUS TIMER        Run a distraction-free session')
        row('[03]  QUICK NOTES        Capture and review information')
        row('[04]  HABIT TRACKER      Record today\'s consistency')
        line('╠','═','╣'); row('DATA STATUS: LOCAL  /  AUTO-SAVE ENABLED',G)
        row('[Q]   CLOSE WORKSPACE',B)
        c=footer('ROS/desk>')
        if c=='q': print('\n  Daily Desk closed. Local data remains saved.'); return 0
        action=actions.get(c)
        if action: action(data)
        else: print('  Select 1-4 or q.'); time.sleep(.7)

if __name__=='__main__': raise SystemExit(run(sys.argv[1:]))
