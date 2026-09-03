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

## How this is different from the files you already have

Every surface below answers a different question. retro doesn't replace any
of them — it is the **process that writes two of them and decides what the
others should never contain**.

| Surface | Question it answers | Loaded when | Who writes it | What retires content |
|---|---|---|---|---|
| `README.md` | "What is this project?" (for humans) | Never auto-loaded | You | You, manually |
| `CLAUDE.md` (project) | "How should Claude work *in this repo*?" | Every session in that repo | You, ad hoc | Nothing — it only grows |
| `~/.claude/CLAUDE.md` (user) | "How should Claude work *everywhere*?" | Every session, every project | You, ad hoc | Nothing — it only grows |
| `SKILL.md` (a skill) | "*How* do I perform this repeatable task?" | On demand, when triggered | You, deliberately | You, manually |
| `STATE.md` | "Where were we? What's next?" | When you point Claude at it | Each working session | Dies with the project |
| `retro.json` | "What did this milestone teach us?" (audit) | Read by the *next* retro | **/retro** | Superseded by the next retro |
| `~/.retro/playbook.md` | "What do we now *always* do, having learned it the hard way?" | Every session (via user CLAUDE.md) | **/retro only** | Displacement: capped at 25, weakest lesson evicted |

The failure mode retro exists to prevent: without it, transferable lessons
either die in STATE.md when the project ends, or get pasted into a global
CLAUDE.md that grows forever until Claude stops reading it carefully. The
scope rule decides *which file* a lesson belongs in; the budget decides
whether it's *worth a slot* in the always-loaded one. When a retro lesson
turns out to be a *procedure* ("here's how we deploy"), the right output is
a skill, not a playbook line — retro should say so and hand off.

`STATE.md` vs retro, in one line: STATE.md is a bookmark (forward-looking,
same project); retro is an inheritance (backward-looking, next project).

## Not a loop, not recursion

**vs `/loop`** (or any scheduled re-run): a loop repeats the *doing* — the
same instruction on an interval, exactly as smart on run 100 as on run 1.
retro is punctuated, not periodic: it fires at milestones, and its output
*changes the standing instructions* every future session starts from. They
compose: `/loop` executes; retro decides what future executions should
already know.

**vs recursion / "self-improvement loops"**: a naive self-improving agent
feeds its own output back into itself — edit your own prompt every session
and you compound noise as fast as insight. retro is closed-loop *control*,
and it deliberately breaks the recursion in three places:

1. a **human gate** — the interview's answers and scope calls are confirmed
   by a person, not self-certified;
2. **evidence** — a lesson needs a commit/session ref, so the input to the
   next cycle is what *happened*, not what the last cycle *said*;
3. **bounded state** — the playbook can't grow past its cap, so the system
   converges instead of accreting. Rejection is a designed outcome.

So: feedback with a damper, not a function calling itself.

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
