# CLAUDE.md

Entry point for agent sessions in `ai-emissions-map`. Four things, then get to work:

1. **[`AGENTS.md`](AGENTS.md) is the repo map**: layout, the `build/` modules, the data model, how
   to write to `sources/`, and the traps. Read it.
2. **[`docs/README.md`](docs/README.md) routes your task to its workflow.** Follow the workflow;
   do not improvise a procedure one already carries.
3. **Use the registered skill for that workflow.** They live under `.claude/skills/` (symlinks
   into `skills/`); if the Skill tool does not list them, read `skills/<name>/SKILL.md` directly.
4. **Read `docs/rulings/log.yaml` before asking the maintainer anything.** A settled question is
   never asked twice.

## Conventions

- `uv` for everything Python: `uv run python -m build.<module>`; every module answers `--help`.
  If a pyenv `VIRTUAL_ENV` is set in your shell, prefix commands with `VIRTUAL_ENV=`.
- American English, plain prose.
- The maintainer reviews every commit: ask before committing, showing the message; no
  `Co-Authored-By` trailer; never push without asking.
- Plans, specs and working notes never go in the repository.
