"""LazyAgents CLI entry point."""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .commands import agent_cmd, docs_cmd, init_cmd, lint_cmd, memory_cmd
from .util import red


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lazyagents",
        description="A repeatable engineering workflow for Claude Code — CLI-first, Claude-only.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Workflow (run inside Claude Code after init):\n"
            "  /new-requirement <feature>   /review-requirements   /review-design\n"
            "  /execute-plan <feature>      /writing-test          /code-review"
        ),
    )
    parser.add_argument("-v", "--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command")

    # init
    p_init = sub.add_parser("init", help="Install commands, skills & phase docs")
    p_init.add_argument("--force", action="store_true", help="Overwrite existing files")
    # Accept and ignore these legacy flags for prompt compatibility.
    p_init.add_argument("-a", action="store_true", help=argparse.SUPPRESS)
    p_init.add_argument("-e", default=None, help=argparse.SUPPRESS)
    p_init.add_argument("--built-in", action="store_true", help=argparse.SUPPRESS)
    p_init.add_argument("--yes", action="store_true", help=argparse.SUPPRESS)
    p_init.set_defaults(func=init_cmd.run)

    # lint
    p_lint = sub.add_parser("lint", help="Validate the docs/ai structure")
    p_lint.add_argument("--feature", default=None, help="Also check feature-<name>.md")
    p_lint.set_defaults(func=lint_cmd.run)

    # docs
    p_docs = sub.add_parser("docs", help="Scaffold feature docs across phases")
    p_docs.add_argument("sub", nargs="?", default=None, help="init-feature")
    p_docs.add_argument("name", nargs="?", default=None, help="feature name (kebab-case)")
    p_docs.set_defaults(func=docs_cmd.run)

    # memory
    p_mem = sub.add_parser("memory", help="Local project memory (file-based)")
    p_mem.add_argument("sub", nargs="?", default=None,
                       help="store|search|list|update|rm")
    p_mem.add_argument("--title", default=None)
    p_mem.add_argument("--content", default=None)
    p_mem.add_argument("--tags", default=None)
    p_mem.add_argument("--query", default=None)
    p_mem.add_argument("--id", default=None)
    p_mem.add_argument("--limit", type=int, default=None)
    p_mem.set_defaults(func=memory_cmd.run)

    # agent
    p_agent = sub.add_parser(
        "agent", help="List running Claude agents and send them prompts (tmux)"
    )
    p_agent.add_argument("sub", nargs="?", default=None, help="list|send|console")
    p_agent.add_argument("message", nargs="?", default=None,
                         help="prompt text (for send)")
    p_agent.add_argument("--id", default=None, help="agent name (for send)")
    p_agent.add_argument("--stdin", action="store_true",
                         help="read the message from stdin")
    p_agent.add_argument("-j", "--json", action="store_true",
                         help="JSON output (for list)")
    p_agent.set_defaults(func=agent_cmd.run)

    return parser


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    parser = build_parser()
    args = parser.parse_args(argv)

    if not getattr(args, "command", None):
        parser.print_help()
        return 0

    try:
        return args.func(args) or 0
    except (ValueError, OSError) as e:
        print(f"{red('error:')} {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
