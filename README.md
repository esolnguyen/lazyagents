# LazyAgents

> A repeatable engineering workflow for **Claude Code** — phases, skills,
> verification, and local memory. **CLI-first, Claude-only.** Pure Python stdlib,
> no third-party dependencies.

A small, dependency-free Python CLI that gives Claude Code a repeatable engineering
workflow — slash commands, skills, subagents, and phase templates for a
Claude-only, CLI-only setup.

## Install

Requires Python ≥ 3.9. No runtime dependencies.

```bash
# isolated global install (recommended):
pipx install /Users/nguyenthang/Workspace/lazyagents
# or with uv:
uv tool install /Users/nguyenthang/Workspace/lazyagents
# or editable for development:
pip install -e /Users/nguyenthang/Workspace/lazyagents
```

No-install option (run from source):

```bash
PYTHONPATH=/Users/nguyenthang/Workspace/lazyagents/src python -m lazyagents.cli --help
```

## Quick start

```bash
cd your-project
lazyagents init          # installs .claude/{commands,skills,agents} + docs/ai phase templates
```

Then, inside **Claude Code**, drive the workflow with slash commands:

```
/new-requirement add OAuth login with Google
/review-requirements
/review-design
/execute-plan feature-oauth-login
/writing-test
/code-review
```

## What `init` writes into your project

```
your-project/
├── .claude/
│   ├── commands/      # /new-requirement, /execute-plan, /code-review, ... (9)
│   ├── skills/        # dev-lifecycle, verify, memory, tdd, ... (9)
│   └── agents/        # subagents: dev-lifecycle, verify, security-review, ... (9)
├── docs/ai/
│   ├── requirements/  design/  planning/  implementation/  testing/
└── .lazyagents/
    ├── config.json    # project marker
    └── memory.json    # local, file-based knowledge base
```

## Commands

| Command | Purpose |
|---|---|
| `lazyagents init [--force]` | Install commands, skills, agents & phase templates into the current project |
| `lazyagents lint [--feature <name>]` | Validate the `docs/ai` structure (exit code 1 on failure — good for CI) |
| `lazyagents docs init-feature <name>` | Scaffold `feature-<name>.md` across all phases |
| `lazyagents memory store --title T --content C [--tags a,b]` | Store a durable decision/convention |
| `lazyagents memory search --query Q [--limit N]` | Search project memory |
| `lazyagents memory list [--limit N]` | List recent memories |
| `lazyagents memory update --id ID [...]` | Update an entry |
| `lazyagents memory rm --id ID` | Delete an entry |
| `lazyagents agent list [--json]` | List running Claude agents (in tmux) |
| `lazyagents agent send --id NAME <msg>` | Send a prompt to an agent's tmux pane (`--stdin` to pipe) |
| `lazyagents agent console` | Interactive picker — arrow keys to select, type a prompt to send |

## Agents

`lazyagents agent` lets you see your running Claude Code sessions and drive them
without leaving your shell. It is **tmux-based**: an agent is discovered only if
Claude runs inside a tmux pane, because prompts are delivered with `tmux send-keys`.
This keeps it dependency-free and portable across macOS and Linux (no AppleScript).

```bash
# start Claude inside tmux so it can be controlled:
tmux new-session -s my-feature 'claude'

# from anywhere else:
lazyagents agent list                          # see what's running
lazyagents agent send --id my-feature "run the tests and report back"
npm test 2>&1 | lazyagents agent send --id my-feature --stdin
lazyagents agent console                        # pick + send interactively (↑/↓, i, Enter)
```

Discovery reads `tmux list-panes` plus `~/.claude/sessions/<pid>.json` and the
session JSONL for status (`running`/`waiting`/`idle`) and the last prompt — all
read-only and best-effort.

## Memory

Memory is **local and file-based** (`<project>/.lazyagents/memory.json`) — no database,
no services, no telemetry. Commit `memory.json` to share it with your team.

## License

MIT
