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

## Step 2 — The interview (fixed questions, every time)

Ask the user these five questions, in order, one at a time. If running
autonomously, draft answers from the evidence, label them clearly as drafts,
and get confirmation before Step 4's cross-project writes.

1. What was the goal, and did it change?
2. What took longer than expected, and why?
3. What did we get wrong first, and what was the fix?
4. Which of learned-behavior's candidate lessons have a real cause vs. are
   noise? (Skip if learned-behavior had nothing.)
5. For each lesson emerging from 1–4: is this about **this repo**, **this
   stack**, or **the developer's way of working**?

The questions are fixed on purpose — the value is in the ritual being
comparable across projects, not in clever adaptive questioning.

## Step 3 — Distill and scope the lessons

Turn the interview into lessons. Each lesson needs:

- **claim** — one sentence, imperative, testable by the next project.
- **evidence** — at least one commit sha, session/transcript ref, or
  learned-behavior fingerprint. A lesson with no evidence is an opinion; drop
  it or mark confidence ≤ 0.4.
- **scope** — get a suggestion per claim from
  `python -m retro.cli classify --claim "..." --repo "$PWD"`, then decide
  yourself; the classifier assists, the interview decides. Scoping tests:
  - Would this sentence be true and useful in a repo that shares nothing
    with this one but the language/tooling? → `stack`.
  - True and useful even in a different stack? → `global`.
  - Needs this repo's nouns to make sense? → `project`.
- **confidence** — 0–1; how surprised you'd be if it didn't hold next time.

Bias check before moving on: if everything came out `project`, the
classification was probably timid — re-ask question 5 for the two strongest
lessons. If more than ~2 lessons came out `global` from a single retro, it
was probably grandiose — global lessons should be rare.

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
  "lessons": [{"claim": "...", "evidence": ["sha|ref"], "scope": "project|stack:<name>|global",
                "confidence": 0.0, "written_to": "learned-behavior|playbook|rejected", "hits": 0}]
}
```

## Degraded modes (normal, not failures)

- No learned-behavior: run the retro; question 4 becomes "what recurring
  friction did you notice?" and project lessons go into `retro.json` only.
- No transcripts found: rely on git + memory of the sessions; note it in
  `retro.json`.
- Playbook rejects everything: that is the budget working. Say so.
