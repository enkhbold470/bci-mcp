# Agent instructions (Cursor, Claude Code, Copilot, etc.)

Read this file before making git commits or opening PRs in this repository.

## Git commits — mandatory

**Do not add `Co-authored-by` trailers to any commit message.**

Forbidden examples:

```
Co-authored-by: Cursor <cursoragent@cursor.com>
Co-authored-by: Claude Opus ... <noreply@anthropic.com>
```

The human author is the only author. AI assistants may help write code and commit messages, but must not be credited in git metadata.

Before every push:

```bash
git log -1 --format='%B' | rg 'Co-authored-by'
```

If that matches anything, amend the commit and remove the trailer before pushing.

**Cursor injects `Co-authored-by: Cursor <cursoragent@cursor.com>` automatically.** This repo sets `core.hooksPath` to `.githooks/` so `prepare-commit-msg` strips those lines on every commit. After cloning, run:

```bash
git config core.hooksPath .githooks
```

## Other conventions

- Run `ruff check src tests && python -m pytest` before PRs.
- Docs: `pip install -e ".[docs]" && mkdocs build --strict`.
- See [CLAUDE.md](CLAUDE.md) for architecture and package layout.
