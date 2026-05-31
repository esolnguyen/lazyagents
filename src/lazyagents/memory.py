"""Local, file-based project memory.

Self-contained (no external services). Stored at
<project>/.lazyagents/memory.json
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path


def memory_path(cwd: Path | None = None) -> Path:
    cwd = cwd or Path.cwd()
    return cwd / ".lazyagents" / "memory.json"


def _load(cwd: Path) -> dict:
    path = memory_path(cwd)
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {"entries": []}


def _save(cwd: Path, db: dict) -> None:
    path = memory_path(cwd)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(db, indent=2) + "\n")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _split_tags(tags: str | None) -> list[str]:
    if not tags:
        return []
    return [t.strip() for t in tags.split(",") if t.strip()]


def store(cwd: Path, title: str, content: str, tags: str | None) -> dict:
    title = (title or "").strip()
    content = (content or "").strip()
    if not title or not content:
        raise ValueError("memory store requires --title and --content")
    db = _load(cwd)
    entry = {
        "id": str(uuid.uuid4()),
        "title": title,
        "content": content,
        "tags": _split_tags(tags),
        "createdAt": _now(),
    }
    db["entries"].append(entry)
    _save(cwd, db)
    return entry


def _tokenize(s: str) -> list[str]:
    return [t for t in re.split(r"[^a-z0-9]+", (s or "").lower()) if t]


def search(cwd: Path, query: str, limit: int = 10) -> list[dict]:
    terms = _tokenize(query)
    if not terms:
        return []
    db = _load(cwd)
    scored = []
    for e in db["entries"]:
        hay = f"{e['title']} {e['content']} {' '.join(e['tags'])}".lower()
        score = 0
        for t in terms:
            if t in e["title"].lower():
                score += 3
            if any(t in tag.lower() for tag in e["tags"]):
                score += 2
            if t in hay:
                score += 1
        if score > 0:
            scored.append((score, e))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [e for _, e in scored[:limit]]


def list_entries(cwd: Path, limit: int = 50) -> list[dict]:
    db = _load(cwd)
    entries = sorted(db["entries"], key=lambda e: e.get("createdAt", ""), reverse=True)
    return entries[:limit]


def update(cwd: Path, id_: str, title=None, content=None, tags=None) -> dict:
    db = _load(cwd)
    entry = next(
        (e for e in db["entries"] if e["id"] == id_ or e["id"].startswith(id_)), None
    )
    if entry is None:
        raise ValueError(f'No memory entry matching id "{id_}"')
    if title is not None:
        entry["title"] = title.strip()
    if content is not None:
        entry["content"] = content.strip()
    if tags is not None:
        entry["tags"] = _split_tags(tags)
    entry["updatedAt"] = _now()
    _save(cwd, db)
    return entry


def remove(cwd: Path, id_: str) -> int:
    db = _load(cwd)
    before = len(db["entries"])
    db["entries"] = [
        e for e in db["entries"] if e["id"] != id_ and not e["id"].startswith(id_)
    ]
    _save(cwd, db)
    return before - len(db["entries"])
