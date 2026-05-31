"""Shared helpers: paths, colors, simple output."""

from __future__ import annotations

import sys
from pathlib import Path

# Directory layout: <pkg>/assets lives next to this file.
PKG_DIR = Path(__file__).resolve().parent
ASSETS_DIR = PKG_DIR / "assets"

PHASES = ["requirements", "design", "planning", "implementation", "testing"]


def _supports_color() -> bool:
    return sys.stdout.isatty()


_USE_COLOR = _supports_color()


def _wrap(code: str):
    def fn(s: str) -> str:
        if not _USE_COLOR:
            return s
        return f"\x1b[{code}m{s}\x1b[0m"

    return fn


green = _wrap("32")
red = _wrap("31")
yellow = _wrap("33")
cyan = _wrap("36")
dim = _wrap("2")
bold = _wrap("1")


def ok(msg: str) -> None:
    print(f"{green('✓')} {msg}")


def warn(msg: str) -> None:
    print(f"{yellow('!')} {msg}")


def fail(msg: str) -> None:
    print(f"{red('✗')} {msg}")


def info(msg: str) -> None:
    print(f"{cyan('›')} {msg}")


def slugify(name: str) -> str:
    out = []
    for ch in name.lower():
        out.append(ch if (ch.isalnum() or ch == "-") else "-")
    s = "".join(out)
    while "--" in s:
        s = s.replace("--", "-")
    return s.strip("-")
