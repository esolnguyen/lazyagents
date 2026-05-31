"""Discover running Claude Code agents that live inside tmux panes.

Strategy (tmux-only, portable across macOS + Linux):
  1. `tmux list-panes -a` → every pane with its pid, session, path.
  2. `ps` → all processes (pid, ppid, comm) to walk each pane's process tree.
  3. A pane is an "agent" if a `claude` process runs in its tree.
  4. Status / last message enriched from ~/.claude/sessions/<pid>.json and
     the project's session JSONL (best-effort; absence is fine).

Only tmux panes are reported, because sending a prompt is done via
`tmux send-keys` — an agent we cannot send to is not useful here.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

CLAUDE_DIR = Path.home() / ".claude"
SESSIONS_DIR = CLAUDE_DIR / "sessions"
PROJECTS_DIR = CLAUDE_DIR / "projects"


@dataclass
class Agent:
    name: str  # tmux session name (human-friendly)
    pane_id: str  # e.g. "%3" — target for send-keys
    pane_pid: int
    claude_pid: int
    cwd: str
    status: str = "unknown"  # running | waiting | idle | unknown
    summary: str = ""  # last user message, if discoverable
    window: str = ""
    extra: dict = field(default_factory=dict)


def _run(cmd: list[str]) -> str:
    try:
        out = subprocess.run(
            cmd, capture_output=True, text=True, timeout=10, check=False
        )
        return out.stdout
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        return ""


def tmux_available() -> bool:
    return bool(_run(["tmux", "-V"]).strip())


def has_tmux_server() -> bool:
    # `tmux list-panes -a` returns non-empty only if a server with panes exists.
    return bool(_run(["tmux", "list-panes", "-a", "-F", "#{pane_id}"]).strip())


def _list_panes() -> list[dict]:
    fmt = "#{pane_id}\t#{pane_pid}\t#{session_name}\t#{window_index}\t#{pane_current_path}\t#{pane_current_command}"
    raw = _run(["tmux", "list-panes", "-a", "-F", fmt])
    panes = []
    for line in raw.splitlines():
        parts = line.split("\t")
        if len(parts) < 6:
            continue
        pane_id, pane_pid, session, window, path, command = parts[:6]
        try:
            pid = int(pane_pid)
        except ValueError:
            continue
        panes.append(
            {
                "pane_id": pane_id,
                "pane_pid": pid,
                "session": session,
                "window": window,
                "path": path,
                "command": command,
            }
        )
    return panes


def _process_table() -> dict[int, dict]:
    """pid -> {ppid, comm} for every process (via `ps`)."""
    raw = _run(["ps", "-axo", "pid=,ppid=,comm="])
    table: dict[int, dict] = {}
    for line in raw.splitlines():
        parts = line.split(None, 2)
        if len(parts) < 3:
            continue
        try:
            pid = int(parts[0])
            ppid = int(parts[1])
        except ValueError:
            continue
        table[pid] = {"ppid": ppid, "comm": parts[2].strip()}
    return table


def _find_claude_in_tree(root_pid: int, table: dict[int, dict]) -> int | None:
    """Return the pid of a `claude` process in root_pid's subtree, if any."""
    # children index
    children: dict[int, list[int]] = {}
    for pid, info in table.items():
        children.setdefault(info["ppid"], []).append(pid)

    stack = [root_pid]
    seen = set()
    while stack:
        pid = stack.pop()
        if pid in seen:
            continue
        seen.add(pid)
        info = table.get(pid)
        if info and Path(info["comm"]).name == "claude":
            return pid
        stack.extend(children.get(pid, []))
    return None


def _read_pid_session(pid: int) -> dict | None:
    f = SESSIONS_DIR / f"{pid}.json"
    if not f.exists():
        return None
    try:
        return json.loads(f.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def _encode_cwd(cwd: str) -> str:
    # Claude Code encodes project paths by replacing non-alphanumerics with '-'.
    return "".join(c if c.isalnum() else "-" for c in cwd)


def _last_user_message(cwd: str, session_id: str | None) -> str:
    proj = PROJECTS_DIR / _encode_cwd(cwd)
    if not proj.is_dir():
        return ""
    if session_id:
        candidates = [proj / f"{session_id}.jsonl"]
    else:
        candidates = sorted(
            proj.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True
        )
    for jf in candidates:
        if not jf.exists():
            continue
        last = ""
        try:
            for line in jf.read_text().splitlines():
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if obj.get("type") == "user":
                    msg = obj.get("message", {})
                    content = msg.get("content") if isinstance(msg, dict) else None
                    if isinstance(content, str):
                        last = content
                    elif isinstance(content, list):
                        texts = [
                            b.get("text", "")
                            for b in content
                            if isinstance(b, dict) and b.get("type") == "text"
                        ]
                        if texts:
                            last = " ".join(texts)
        except OSError:
            continue
        if last:
            return last.strip().replace("\n", " ")[:100]
    return ""


def discover() -> list[Agent]:
    """Return all Claude Code agents running inside tmux panes."""
    if not has_tmux_server():
        return []
    table = _process_table()
    agents: list[Agent] = []
    for pane in _list_panes():
        claude_pid = _find_claude_in_tree(pane["pane_pid"], table)
        if claude_pid is None:
            continue
        sess = _read_pid_session(claude_pid) or {}
        cwd = sess.get("cwd") or pane["path"]
        status = sess.get("status", "unknown")
        summary = _last_user_message(cwd, sess.get("sessionId"))
        agents.append(
            Agent(
                name=pane["session"],
                pane_id=pane["pane_id"],
                pane_pid=pane["pane_pid"],
                claude_pid=claude_pid,
                cwd=cwd,
                status=status,
                summary=summary,
                window=pane["window"],
                extra={"sessionId": sess.get("sessionId")},
            )
        )
    # Stable, useful ordering: waiting first, then running, then the rest.
    rank = {"waiting": 0, "running": 1, "idle": 2, "unknown": 3}
    agents.sort(key=lambda a: (rank.get(a.status, 9), a.name))
    return agents


def resolve(identifier: str) -> Agent | None:
    """Find an agent by exact or prefix match on name or pane id."""
    agents = discover()
    for a in agents:
        if a.name == identifier or a.pane_id == identifier:
            return a
    matches = [a for a in agents if a.name.startswith(identifier)]
    return matches[0] if len(matches) == 1 else None
