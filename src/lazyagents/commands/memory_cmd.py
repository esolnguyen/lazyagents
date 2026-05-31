"""lazyagents memory — local project memory (store/search/list/update/rm)."""

from __future__ import annotations

from pathlib import Path

from .. import memory as mem
from ..util import bold, cyan, dim, info, ok

USAGE = """lazyagents memory <store|search|list|update|rm>

  store   --title <t> --content <c> [--tags a,b,c]
  search  --query <q> [--limit N]
  list    [--limit N]
  update  --id <id> [--title <t>] [--content <c>] [--tags a,b,c]
  rm      --id <id>"""


def _print_entry(e: dict) -> None:
    tags = cyan(f" [{', '.join(e['tags'])}]") if e["tags"] else ""
    print(f"{bold(e['title'])}{tags} {dim(e['id'][:8])}")
    body = e["content"].replace("\n", "\n  ")
    print(f"  {body}")
    print(dim(f"  {e.get('createdAt', '')}\n"))


def run(args) -> int:
    cwd = Path.cwd()
    sub = args.sub

    if sub == "store":
        entry = mem.store(cwd, args.title, args.content, args.tags)
        ok(f"Stored memory {dim(entry['id'][:8])} — {bold(entry['title'])}")
        return 0

    if sub == "search":
        q = args.query
        if not q:
            raise ValueError("memory search requires --query")
        results = mem.search(cwd, q, args.limit or 10)
        if not results:
            info(f'No memory found for "{q}"')
            return 0
        print(dim(f'{len(results)} result(s) for "{q}"\n'))
        for e in results:
            _print_entry(e)
        return 0

    if sub == "list":
        results = mem.list_entries(cwd, args.limit or 50)
        if not results:
            info("Memory is empty")
            return 0
        for e in results:
            _print_entry(e)
        return 0

    if sub == "update":
        if not args.id:
            raise ValueError("memory update requires --id")
        entry = mem.update(cwd, args.id, args.title, args.content, args.tags)
        ok(f"Updated memory {dim(entry['id'][:8])} — {bold(entry['title'])}")
        return 0

    if sub == "rm":
        if not args.id:
            raise ValueError("memory rm requires --id")
        n = mem.remove(cwd, args.id)
        ok(f"Removed {n} entry(ies)")
        return 0

    print(USAGE)
    return 0
