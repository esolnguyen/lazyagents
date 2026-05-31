---
name: memory
description: LazyAgents · Use the memory CLI as a durable knowledge layer. Search before non-trivial work, store verified reusable knowledge, update stale entries, and avoid saving transcripts, secrets, or one-off task progress.
---

# LazyAgents Memory CLI

Use `lazyagents memory ...` as the durable knowledge layer. Memory is local and file-based at `<project>/.lazyagents/memory.json`.

## Workflow

1. For implementation, debugging, review, planning, or documentation tasks, search before deep work unless the task is trivial:
   ```bash
   lazyagents memory search --query "<task, subsystem, error, or convention>" --limit 5
   ```
   Search matches title, content, and tags. For broad or risky tasks, search multiple angles separately: subsystem, error text, framework, command, and task intent.

2. Use results as context:
   - Trust repo files, tests, fresh command output, and explicit user instructions over memory.
   - If memory conflicts with verified evidence, use the evidence and update the stale memory.
   - Mention memory only when it changes the plan or avoids asking the user again.

3. Search before storing (avoid duplicates):
   ```bash
   lazyagents memory search --query "<knowledge to store>"
   ```

4. Store or update only after the quality gate passes.

## Quality Gate

Before storing, all must be true:

- Future sessions are likely to reuse it.
- It is verified by code, docs, tests, command output, or explicit user instruction.
- It is not merely a restatement of obvious nearby files unless it prevents repeated agent mistakes.
- Its subject is narrow and specific, not a broad dump.
- Existing memory does not already cover it.
- It contains no secrets, credentials, private customer data, personal data, raw logs, or temporary paths.

Store:
- Project conventions, user preferences, durable decisions.
- Reusable fixes, testing patterns, commands, setup gotchas.
- Non-obvious constraints, architecture rules, failure patterns.

Do not store:
- Task progress, transcripts, speculation, generic programming facts.
- Raw errors without diagnosis.
- Anything the user did not intend to persist.

## Commands

### Search

```bash
lazyagents memory search --query "<query>" --limit 5
```

Options: `--query` (required); `--limit` (default 10). Results print each entry's title, tags, and a short id (first 8 chars) — use that id for `update` and `rm`.

### List

```bash
lazyagents memory list --limit 20
```

Most recent first. `--limit` defaults to 50.

### Store

```bash
lazyagents memory store \
  --title "<actionable title>" \
  --content "<context, guidance, evidence, exceptions>" \
  --tags "<lowercase,comma,separated,tags>"
```

`--title` and `--content` are required; `--tags` is optional. Use this content shape when helpful:

```text
Context: Where this applies.
Guidance: What to do.
Evidence: File, command, test, or user instruction.
Exceptions: When not to apply it.
```

### Update

Find the id with `search` or `list` (the short 8-char id is shown), then update only the fields you pass:

```bash
lazyagents memory update \
  --id "<memory-id>" \
  --title "<updated title>" \
  --content "<updated content>" \
  --tags "<replacement,tags>"
```

`--id` accepts the full id or a unique prefix. `--tags` replaces all existing tags. Omitted fields are left unchanged.

### Remove

```bash
lazyagents memory rm --id "<memory-id>"
```

Accepts the full id or a unique prefix.

## Troubleshooting

- CLI missing: run `lazyagents --version`.
- Duplicate knowledge: search first, then `update` the existing entry instead of storing a new one.
- Empty results: broaden terms, or search symptoms and subsystem names separately (search is keyword-based across title/content/tags).
- `--id` matches nothing: run `search`/`list` to copy the shown short id, and make sure the prefix is unique.
- DB path: `<project>/.lazyagents/memory.json`. Commit it to share memory with your team.
