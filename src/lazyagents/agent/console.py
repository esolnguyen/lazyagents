"""Interactive agent console: list running agents, select with arrow keys,
type a prompt and send it via tmux. Pure stdlib (curses)."""

from __future__ import annotations

import curses

from . import detect, tmux

STATUS_GLYPH = {"running": "●", "waiting": "◐", "idle": "○", "unknown": "?"}


def _draw(stdscr, agents, selected, mode, buffer, message):
    stdscr.erase()
    h, w = stdscr.getmaxyx()

    title = " LazyAgents — agent console "
    stdscr.addstr(0, 0, title[: w - 1], curses.A_REVERSE)

    if not agents:
        stdscr.addstr(2, 2, "No running Claude agents found in tmux.")
        stdscr.addstr(3, 2, "Start Claude inside a tmux session, then reopen.")
        stdscr.addstr(h - 1, 0, " q quit ", curses.A_DIM)
        stdscr.refresh()
        return

    stdscr.addstr(2, 2, "Agents:", curses.A_BOLD)
    row = 3
    for i, a in enumerate(agents):
        if row >= h - 4:
            break
        glyph = STATUS_GLYPH.get(a.status, "?")
        marker = "▶ " if i == selected else "  "
        line = f"{marker}{glyph} {a.name}  [{a.status}]  {a.cwd}"
        attr = curses.A_REVERSE if i == selected else curses.A_NORMAL
        stdscr.addstr(row, 2, line[: w - 4], attr)
        row += 1

    # Preview of selected agent's last user message.
    sel = agents[selected]
    if sel.summary:
        stdscr.addstr(row + 1, 2, "Last: ", curses.A_DIM)
        stdscr.addstr(row + 1, 8, sel.summary[: w - 10])

    # Input box
    box_y = h - 3
    if mode == "input":
        prompt = f"› send to {sel.name}: "
        stdscr.addstr(box_y, 2, prompt, curses.A_BOLD)
        stdscr.addstr(box_y, 2 + len(prompt), buffer[: w - 4 - len(prompt)])
        curses.curs_set(1)
    else:
        curses.curs_set(0)

    if message:
        stdscr.addstr(box_y - 1, 2, message[: w - 4], curses.A_DIM)

    help_line = (
        " ↑/↓ select   i type prompt   r refresh   q quit "
        if mode == "list"
        else " Enter send   Esc cancel "
    )
    stdscr.addstr(h - 1, 0, help_line[: w - 1], curses.A_DIM)
    stdscr.refresh()


def _loop(stdscr):
    curses.use_default_colors()
    stdscr.keypad(True)
    agents = detect.discover()
    selected = 0
    mode = "list"  # list | input
    buffer = ""
    message = ""

    while True:
        if selected >= len(agents):
            selected = max(0, len(agents) - 1)
        _draw(stdscr, agents, selected, mode, buffer, message)
        ch = stdscr.getch()

        if mode == "list":
            if ch in (ord("q"), 27):  # q / Esc
                return
            if ch in (curses.KEY_UP, ord("k")) and agents:
                selected = (selected - 1) % len(agents)
            elif ch in (curses.KEY_DOWN, ord("j")) and agents:
                selected = (selected + 1) % len(agents)
            elif ch in (ord("i"), ord("m")) and agents:
                mode = "input"
                buffer = ""
                message = ""
            elif ch in (ord("r"), curses.KEY_F5):
                agents = detect.discover()
                message = "refreshed"
        else:  # input mode
            if ch == 27:  # Esc
                mode = "list"
                buffer = ""
            elif ch in (curses.KEY_ENTER, 10, 13):
                if buffer.strip() and agents:
                    target = agents[selected]
                    try:
                        tmux.send(target.pane_id, buffer)
                        message = f"sent to {target.name}"
                    except Exception as e:  # noqa: BLE001 — surface any send failure
                        message = f"send failed: {e}"
                mode = "list"
                buffer = ""
            elif ch in (curses.KEY_BACKSPACE, 127, 8):
                buffer = buffer[:-1]
            elif 32 <= ch < 127:
                buffer += chr(ch)


def run() -> int:
    if not detect.tmux_available():
        print("error: tmux is not installed or not on PATH.")
        return 1
    curses.wrapper(_loop)
    return 0
