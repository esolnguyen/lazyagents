"""lazyagents docs init-feature <name> — scaffold feature docs across phases."""

from __future__ import annotations

from pathlib import Path

from ..util import ASSETS_DIR, PHASES, bold, cyan, info, ok, slugify

USAGE = """lazyagents docs <init-feature> <name>

  init-feature <name>   Create docs/ai/<phase>/feature-<name>.md for every phase"""


def run(args) -> int:
    if args.sub != "init-feature":
        print(USAGE)
        return 0
    if not args.name:
        raise ValueError("docs init-feature requires a <name> (kebab-case)")

    slug = slugify(args.name)
    cwd = Path.cwd()
    created = []

    for phase in PHASES:
        d = cwd / "docs" / "ai" / phase
        d.mkdir(parents=True, exist_ok=True)
        dst = d / f"feature-{slug}.md"
        if not dst.exists():
            template = ASSETS_DIR / "phases" / phase / "README.md"
            content = template.read_text() if template.exists() else f"# {phase}\n"
            content = content.replace("{{ feature }}", slug).replace(
                "{{feature}}", slug
            )
            dst.write_text(content)
        created.append(f"docs/ai/{phase}/feature-{slug}.md")

    ok(f"Initialized feature {bold(slug)} across {len(PHASES)} phases")
    info("Fill these documents:")
    for p in created:
        print(f"  {cyan(p)}")
    return 0
