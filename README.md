# retro

A `/retro` skill for Claude Code: a structured retrospective at project
milestones that carries transferable lessons across projects.

**The gap it fills:** CLAUDE.md, skills, and memory files are storage
surfaces with no writer. Nothing in the normal workflow asks "what did this
project teach us that the next one should inherit?", distinguishes
project-specific from developer-level lessons, or retires lessons that stop
earning their place. `retro` is that writer — the reasoning and curation
layer on top of [`learned-behavior`](https://github.com/lisn0/learned-behavior)
(behavioral signal, no LLM, workspace-scoped), not a replacement for it and
not another session-memory tool.

## The three rules

1. **Ritual** — runs at milestones (release tag, merge to main, project
   archive), not every session.
2. **Scope** — every lesson is tagged `project`, `stack`, or `global`. Only
   `stack` and `global` cross projects; that is what keeps a global
   CLAUDE.md from rotting into project trivia.
3. **Budget** — the cross-project playbook (`~/.retro/playbook.md`) is
   size-capped; a new lesson has to displace something to get in, and
   rejection is a valid outcome.

## How it flows

```
milestone → /retro
  inputs   : learned-behavior review · git log since last retro tag · session transcripts
  interview: five fixed questions, every time
  distill  : claim + evidence + scope + confidence per lesson
  write    : project → learned-behavior (its promote/decay manages them)
             stack/global → ~/.retro/playbook.md (size-capped, linked from ~/.claude/CLAUDE.md)
             audit → retro.json in the repo + git tag retro/YYYY-MM-DD
```

## Install

```bash
pip install -e .                       # the plumbing CLI (`retro`, stdlib only)
cp -r . ~/.claude/skills/retro         # or symlink; SKILL.md drives Claude
retro playbook init                    # seeds ~/.retro/playbook.md + CLAUDE.md link
```

`learned-behavior` is optional but recommended; without it the retro still
runs in a degraded mode (see SKILL.md).

## Layout

```
retro/
  SKILL.md          # the /retro skill — interview + write-out steps
  retro/            # small Python package wrapping the two CLIs
    inputs.py       #   learned-behavior review, git log, transcripts
    classify.py     #   scope suggestion (the interview decides)
    playbook.py     #   size-capped playbook read/merge/write
    cli.py
  playbook.md       # template (seeds ~/.retro/playbook.md)
  tests/
```

Python 3.10+, no third-party runtime dependencies (matching
learned-behavior). MIT.

## Status / roadmap

Skill + file convention first; it becomes a product only if the scope
classifier and promote/decay prove hard enough that others want them done
for them. Known deviations from the original brief:

- `learned-behavior review` has **no JSON output** as of 0.x — `inputs.py`
  parses its two structured text line shapes, fail-soft. A `--format json`
  flag upstream would be a good first PR.
- Harness-agnostic export (AGENTS.md, `.cursor/rules`) — later, not MVP.
