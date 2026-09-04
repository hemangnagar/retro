---
name: retro
description: Run a structured project retrospective at a milestone and carry transferable lessons across projects. Use whenever the user says /retro, "retro", "retrospective", "post-mortem", "what did we learn", or hits a natural milestone — tagging a release, merging a feature branch to main, archiving or wrapping up a project, ending a multi-session push. Also suggest it (don't auto-run) when a project clearly just crossed a milestone and no retro tag exists for it. Not for mid-task debugging reflection — this is a milestone ritual with durable, scoped outputs.
---

# /retro — milestone retrospective with cross-project memory

CLAUDE.md, skills, and memory files are storage with no writer. This skill is
the writer: at each milestone it asks what the project taught, decides which
lessons are project-local vs transferable, and writes each to the surface
that manages it. It sits ON TOP of `learned-behavior` (behavioral signal,
no LLM, workspace-scoped) — never replace or bypass it for project-scoped
lessons.

Three rules carry the whole design. Hold them even when a step is awkward:

1. **Ritual** — run at milestones, not every session. A retro without a new
   milestone since the last `retro/*` tag should usually be declined.
2. **Scope** — every lesson is `project`, `stack`, or `global`. Only `stack`
   and `global` cross projects. This is what keeps the global playbook from
   rotting into project trivia — when in doubt, scope DOWN.
3. **Budget** — the cross-project playbook is size-capped; a new lesson must
   displace something to enter. Rejection is a valid outcome.

Prerequisite: the `retro` package installed (`pip install -e <retro repo>`),
`learned-behavior` optional but preferred.

## Step 1 — Gather inputs (all local, no judgment yet)

```bash
python -m retro.cli inputs --repo "$PWD" [--transcripts <extra dirs>]
```

That returns JSON with: learned-behavior's repeated failures + candidate and
approved lessons (parsed from its CLI text output — if `available: false`,
proceed without it and say so), git commits + diffstat since the last
`retro/*` tag (bounded history if none), and paths to Claude Code session
transcripts for this repo. Skim the newest transcript(s) with targeted reads
(errors, reversals, user corrections) — do not ingest whole files.

If the repo has had no meaningful work since the last retro tag, say so and
stop; a retro over nothing manufactures lessons.

## Step 2 — The interview (fixed questions, drafted answers, one-token replies)

The four questions are constants — print them with
`python -m retro.cli questions` and use those exact words:

1. What was the goal, and did it change?
2. What took longer than expected, and why?
3. What did we get wrong first, and what was the fix?
4. Which of learned-behavior's candidate lessons have a real cause vs. are
   noise? (If learned-behavior had nothing: what recurring friction did you
   notice?)

Draft an answer to each from the evidence first, then show all four
questions with their drafts in one message and ask for the fixed reply
protocol: **for each number, `agree` | `edit: <text>` | `skip`**. Drafts
carry the load so the user reacts instead of composes; the closed reply set
keeps the answers comparable across retros and cheap to give. A skipped
question is recorded as declined and produces no lesson.

If running autonomously, mark every answer `agent-draft` and do not proceed
past Step 3 until a person has replied.

## Step 3 — Distill, then scope each lesson from a closed menu

Turn the confirmed answers into lessons. Each lesson needs:

- **claim** — one sentence, imperative, testable by the next project.
- **evidence** — at least one commit sha, session/transcript ref, or
  learned-behavior fingerprint. A lesson with no evidence is an opinion; drop
  it or mark confidence ≤ 0.4.
- **confidence** — 0–1; how surprised you'd be if it didn't hold next time.

Then scope **one lesson at a time**, and never with an open question. Run
`python -m retro.cli classify --claim "..." --repo "$PWD" --index N
--evidence <refs>` — it returns the classifier's suggestion AND the menu.
Put the choice to the user as exactly these four options, suggestion marked:

| option | meaning |
|---|---|
| `project` | About this repo. → learned-behavior, this workspace only. |
| `stack` | About this language/tooling. → playbook as `stack:<name>` (ask which). |
| `global` | About how the developer works, any stack. → playbook, budgeted. |
| `discard` | Not worth keeping. → retro.json as considered-and-dropped, nowhere else. |

When the `AskUserQuestion` tool is available, use it: one question per
lesson (header "Scope", the four options in this order, the suggested one
labelled "(suggested)"), batching up to four lessons per call. Without it,
print the `prompt` text the CLI returned verbatim and normalize the reply
with `python -m retro.cli scope "<reply>"` — a reply outside the menu is
re-asked, not interpreted.

The classifier assists; the person decides. Scoping tests to offer if they
hesitate: true and useful in a repo sharing only the tooling → `stack`; true
in a different stack → `global`; needs this repo's nouns → `project`.

Bias check after all lessons are scoped: everything `project` → probably
timid, offer the two strongest for re-scoping. More than ~2 `global` from
one retro → probably grandiose, say so before writing.

## Step 4 — Write the outputs

**Project-scoped lessons** → learned-behavior owns their lifecycle
(promote/decay). One call per lesson:

```bash
learned-behavior learn --workspace "$PWD" --title "<short>" \
  --rule "<claim>" --rationale "<evidence>" --confidence <c>
```

**Stack/global lessons** → the size-capped playbook (`~/.retro/playbook.md`,
run `python -m retro.cli playbook init` on first use — it also links the
playbook from `~/.claude/CLAUDE.md`):

```bash
python -m retro.cli playbook add --claim "<claim>" \
  --scope global|stack:<name> --confidence <c> --src "<repo>@retro/<date>"
```

Report each result honestly: `added`, `reinforced` (a duplicate claim bumps
its hit counter instead of adding a row), or `rejected` (budget held —
tell the user which incumbent won, don't retry with inflated confidence).
When a playbook lesson visibly helped during the project, credit it:
`python -m retro.cli playbook hit --id R<n>` — hits protect lessons from
displacement, which is how the playbook learns what earns its place.

**The audit trail** — write `retro.json` (template below) somewhere
temporary, then:

```bash
python -m retro.cli finish --repo "$PWD" --retro-json <file>
```

which copies it to `<repo>/retro.json` and creates the `retro/YYYY-MM-DD`
tag so the next retro knows where this one ended. Commit `retro.json` and
push the tag with the repo's normal flow.

retro.json shape (keep exactly these keys so retros stay comparable):

```json
{
  "date": "YYYY-MM-DD",
  "repo": "name",
  "milestone": "what triggered this retro",
  "since": "<previous retro tag or null>",
  "interview": {"goal": "...", "slower_than_expected": "...",
                 "wrong_first": "...", "lb_candidates": "...",
                 "answered_by": "user | agent-draft"},
  "lessons": [{"claim": "...", "evidence": ["sha|ref"], "scope": "project|stack:<name>|global|discard",
                "confidence": 0.0, "written_to": "learned-behavior|playbook:R<n>|rejected|discarded", "hits": 0}]
}
```

Discarded lessons stay in `retro.json` on purpose: the next retro can see
what was considered and dropped, so the same non-lesson isn't re-litigated.

## Degraded modes (normal, not failures)

- No learned-behavior: run the retro; question 4 becomes "what recurring
  friction did you notice?" and project lessons go into `retro.json` only.
- No transcripts found: rely on git + memory of the sessions; note it in
  `retro.json`.
- Playbook rejects everything: that is the budget working. Say so.
