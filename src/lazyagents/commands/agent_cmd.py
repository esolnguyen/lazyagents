"""lazyagents agent — list running Claude agents and send them prompts (tmux)."""

from __future__ import annotations

import json
import sys

from ..agent import detect, tmux
from ..agent import console as agent_console
from ..util import bold, cyan, dim, fail, info, ok

STATUS_GLYPH = {"running": "●", "waiting": "◐", "idle": "○", "unknown": "?"}

USAGE = """lazyagents agent <list|send|console>

  list                       List running Claude agents (in tmux)
  send --id <name> <message> Send a prompt to an agent's tmux pane
       [--stdin]             Read the message from stdin instead
  console                    Interactive picker (arrow keys + type prompt)"""


def _cmd_list(args) -> int:
    agents = detect.discover()
    if args.json:
        print(
            json.dumps(
                [
                    {
                        "name": a.name,
                        "pane": a.pane_id,
                        "status": a.status,
                        "cwd": a.cwd,
                        "claudePid": a.claude_pid,
                        "summary": a.summary,
                    }
                    for a in agents
                ],
                indent=2,
            )
        )
        return 0

    if not detect.tmux_available():
        fail("tmux is not installed — agent list/send requires tmux.")
        return 1
    if not agents:
        info("No running Claude agents found in tmux.")
        info("Start Claude inside a tmux session to control it here.")
        return 0

    info(f"{len(agents)} agent(s):")
    for a in agents:
        glyph = STATUS_GLYPH.get(a.status, "?")
        head = f"  {glyph} {bold(a.name)} {dim('(' + a.pane_id + ')')}  {cyan(a.status)}"
        print(head)
        print(f"      {dim(a.cwd)}")
        if a.summary:
            print(f"      {dim('last: ' + a.summary)}")
    return 0


def _cmd_send(args) -> int:
    if not detect.tmux_available():
        fail("tmux is not installed — agent send requires tmux.")
        return 1
    if not args.id:
        raise ValueError("agent send requires --id <name>")

    if args.stdin:
        message = sys.stdin.read().strip()
    else:
        message = (args.message or "").strip()
    if not message:
        raise ValueError("no message to send (pass a message or use --stdin)")

    target = detect.resolve(args.id)
    if target is None:
        fail(f'No unique agent matching "{args.id}". Run "lazyagents agent list".')
        return 1

    tmux.send(target.pane_id, message)
    ok(f"Sent to {bold(target.name)} {dim('(' + target.pane_id + ')')}")
    return 0


def run(args) -> int:
    sub = args.sub
    if sub == "list":
        return _cmd_list(args)
    if sub == "send":
        return _cmd_send(args)
    if sub == "console":
        return agent_console.run()
    print(USAGE)
    return 0
