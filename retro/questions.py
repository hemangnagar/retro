"""The fixed interview script and the deterministic scope menu.

The questions are constants, not prose in SKILL.md, so every harness that
runs a retro asks the identical words — the value of the ritual is that
retros are comparable across projects. The scope answer is a closed menu:
the user picks exactly one of four options per lesson, never free text.
"""

from __future__ import annotations

import re

INTERVIEW: tuple[tuple[str, str], ...] = (
    ("goal", "What was the goal, and did it change?"),
    ("slower_than_expected", "What took longer than expected, and why?"),
    ("wrong_first", "What did we get wrong first, and what was the fix?"),
    ("lb_candidates",
     "Which of learned-behavior's candidate lessons have a real cause vs. are noise? "
     "(If learned-behavior had nothing: what recurring friction did you notice?)"),
)

# Reply protocol for the four drafted questions — one token per question.
REPLY_PROTOCOL = "For each numbered question answer exactly one of: agree | edit: <your text> | skip"

SCOPE_OPTIONS: tuple[tuple[str, str], ...] = (
    ("project", "About this repo. Written to learned-behavior for this workspace only."),
    ("stack",   "About this language/tooling. Enters the cross-project playbook as stack:<name>."),
    ("global",  "About how you work, any stack. Enters the cross-project playbook (budgeted)."),
    ("discard", "Not worth keeping. Recorded in retro.json as considered-and-dropped, written nowhere else."),
)

_SCOPE_ALIASES = {
    "p": "project", "proj": "project", "repo": "project", "project": "project",
    "s": "stack", "stack": "stack",
    "g": "global", "global": "global",
    "d": "discard", "discard": "discard", "drop": "discard", "skip": "discard", "no": "discard",
}


def scope_prompt(index: int, claim: str, evidence: list[str], suggestion: str) -> str:
    """The exact text to show when no structured-choice UI is available."""
    lines = [
        f"Lesson {index}: {claim}",
        f"  evidence: {'; '.join(evidence) if evidence else '(none)'}",
        f"  classifier suggests: {suggestion}",
        "  Scope — answer with exactly one of:",
    ]
    for key, desc in SCOPE_OPTIONS:
        marker = "  ← suggested" if key == suggestion.split(":")[0] else ""
        lines.append(f"    {key:<8} {desc}{marker}")
    lines.append("  (for stack, name it: stack:python, stack:git, ...)")
    return "\n".join(lines)


def parse_scope_answer(text: str) -> str | None:
    """Normalize a user's scope reply to project | stack:<name> | global | discard.
    Returns None when the reply is not one of the menu options."""
    raw = text.strip().lower()
    if not raw:
        return None
    match = re.match(r"^(stack)[\s:/-]+([a-z0-9][a-z0-9 .+-]*)$", raw)
    if match:
        return f"stack:{match.group(2).strip().replace(' ', '-')}"
    return _SCOPE_ALIASES.get(raw)
