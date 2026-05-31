"""lazyagents init — install the Claude-only workflow into the current project."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from ..util import ASSETS_DIR, PHASES, bold, cyan, dim, info, ok, warn


def run(args) -> int:
    cwd = Path.cwd()
    force = bool(args.force)

    info(f"Initializing LazyAgents workflow in {bold(str(cwd))}")

    # 1. Commands -> .claude/commands
    cmd_src = ASSETS_DIR / "commands"
    cmd_dst = cwd / ".claude" / "commands"
    cmd_dst.mkdir(parents=True, exist_ok=True)
    cmd_count = 0
    for f in sorted(cmd_src.iterdir()):
        dst = cmd_dst / f.name
        if dst.exists() and not force:
            continue
        shutil.copy2(f, dst)
        cmd_count += 1
    ok(f"Installed {cmd_count} command(s) → .claude/commands/")

    # 2. Skills -> .claude/skills
    skill_src = ASSETS_DIR / "skills"
    skill_dst = cwd / ".claude" / "skills"
    skill_dst.mkdir(parents=True, exist_ok=True)
    skill_count = 0
    for d in sorted(skill_src.iterdir()):
        if not d.is_dir():
            continue
        dst = skill_dst / d.name
        if dst.exists() and not force:
            continue
        shutil.copytree(d, dst, dirs_exist_ok=force)
        skill_count += 1
    ok(f"Installed {skill_count} skill(s) → .claude/skills/")

    # 3. Agents -> .claude/agents
    agent_src = ASSETS_DIR / "agents"
    agent_dst = cwd / ".claude" / "agents"
    agent_dst.mkdir(parents=True, exist_ok=True)
    agent_count = 0
    for f in sorted(agent_src.iterdir()):
        if f.suffix != ".md":
            continue
        dst = agent_dst / f.name
        if dst.exists() and not force:
            continue
        shutil.copy2(f, dst)
        agent_count += 1
    ok(f"Installed {agent_count} agent(s) → .claude/agents/")

    # 4. Phase docs -> docs/ai/<phase>/README.md
    phase_src = ASSETS_DIR / "phases"
    phase_count = 0
    for phase in PHASES:
        dst_dir = cwd / "docs" / "ai" / phase
        dst_dir.mkdir(parents=True, exist_ok=True)
        readme = dst_dir / "README.md"
        if not readme.exists() or force:
            shutil.copy2(phase_src / phase / "README.md", readme)
            phase_count += 1
    ok(f"Scaffolded {phase_count} phase template(s) → docs/ai/")

    # 5. Project marker / config
    cfg_path = cwd / ".lazyagents" / "config.json"
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    if not cfg_path.exists() or force:
        cfg = {
            "version": "0.1.0",
            "phases": PHASES,
            "createdAt": datetime.now(timezone.utc).isoformat(),
        }
        cfg_path.write_text(json.dumps(cfg, indent=2) + "\n")
    ok("Wrote .lazyagents/config.json")

    print()
    info("Next steps:")
    print(f"  {dim('1.')} In Claude Code, run {cyan('/new-requirement <feature>')}")
    print(
        f"  {dim('2.')} Then {cyan('/review-design')} → {cyan('/execute-plan')} → {cyan('/code-review')}"
    )
    print(f"  {dim('3.')} Verify structure anytime with {cyan('lazyagents lint')}")

    if cmd_count == 0 and skill_count == 0 and agent_count == 0 and not force:
        warn("Existing files were kept. Re-run with --force to overwrite.")

    return 0
