"""lazyagents lint — validate the docs/ai structure (exit 1 on failure)."""

from __future__ import annotations

from pathlib import Path

from ..util import PHASES, bold, fail, info, ok


def run(args) -> int:
    cwd = Path.cwd()
    feature = args.feature
    failures = 0

    info(f"Linting docs/ai structure in {bold(str(cwd))}")

    for phase in PHASES:
        d = cwd / "docs" / "ai" / phase
        if d.is_dir():
            ok(f"docs/ai/{phase}/")
        else:
            fail(f'missing docs/ai/{phase}/  — run "lazyagents init"')
            failures += 1

        if feature:
            fdoc = d / f"feature-{feature}.md"
            if fdoc.exists():
                ok(f"  feature-{feature}.md")
            else:
                fail(f"  missing docs/ai/{phase}/feature-{feature}.md")
                failures += 1

    claude_cmds = cwd / ".claude" / "commands"
    if claude_cmds.exists():
        ok(".claude/commands/")
    else:
        fail('missing .claude/commands/  — run "lazyagents init"')
        failures += 1

    print()
    if failures > 0:
        fail(f"{failures} check(s) failed")
        return 1
    ok("All checks passed")
    return 0
