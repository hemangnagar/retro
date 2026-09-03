"""The size-capped cross-project playbook (~/.retro/playbook.md).

Only stack- and global-scoped lessons live here — that is the scope rule.
The budget rule: the playbook holds at most MAX_LESSONS; once full, a new
lesson enters only by displacing the weakest incumbent (lowest
confidence + hit score), and is rejected if it can't. Lessons that keep
proving useful get their hit counter bumped, which protects them.

Format — one bullet per lesson, metadata in a trailing HTML comment so the
file stays a readable markdown doc AND a parseable database:

- [global] Claim text here. <!-- id:R3 conf:0.80 hits:2 added:2026-09-03 src:rxguard@retro/2026-09-03 -->
- [stack:python] Claim text. <!-- id:R4 conf:0.70 hits:0 added:2026-09-03 src:... -->
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

PLAYBOOK_DIR = Path.home() / ".retro"
PLAYBOOK_PATH = PLAYBOOK_DIR / "playbook.md"
MAX_LESSONS = 25

_LINE = re.compile(
    r"^- \[(?P<scope>global|stack(?::[a-z0-9 .+,-]+)?)\] (?P<claim>.*?)\s*"
    r"<!-- id:(?P<id>R\d+) conf:(?P<conf>[\d.]+) hits:(?P<hits>\d+) "
    r"added:(?P<added>\S+) src:(?P<src>.*?) -->$"
)

HEADER = """# Cross-project playbook

Lessons that earned their way out of a single project. Curated by /retro:
scoped `global` or `stack:<name>`, size-capped at {cap} — a new lesson must
displace a weaker one to get in. Do not hand-edit the metadata comments.
"""


@dataclass
class Lesson:
    id: str
    scope: str          # "global" or "stack:python"
    claim: str
    confidence: float
    hits: int = 0
    added: str = field(default_factory=lambda: date.today().isoformat())
    src: str = ""       # e.g. "rxguard@retro/2026-09-03" or "seed"

    @property
    def score(self) -> float:
        return self.confidence + 0.1 * self.hits

    def to_line(self) -> str:
        return (f"- [{self.scope}] {self.claim} "
                f"<!-- id:{self.id} conf:{self.confidence:.2f} hits:{self.hits} "
                f"added:{self.added} src:{self.src} -->")


def load(path: Path = PLAYBOOK_PATH) -> list[Lesson]:
    if not path.exists():
        return []
    lessons = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = _LINE.match(line.strip())
        if match:
            g = match.groupdict()
            lessons.append(Lesson(id=g["id"], scope=g["scope"], claim=g["claim"],
                                  confidence=float(g["conf"]), hits=int(g["hits"]),
                                  added=g["added"], src=g["src"]))
    return lessons


def save(lessons: list[Lesson], path: Path = PLAYBOOK_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered = sorted(lessons, key=lambda l: (-l.score, l.added))
    body = HEADER.format(cap=MAX_LESSONS) + "\n" + "\n".join(l.to_line() for l in ordered) + "\n"
    path.write_text(body, encoding="utf-8")


def next_id(lessons: list[Lesson]) -> str:
    used = {int(l.id[1:]) for l in lessons if l.id[1:].isdigit()}
    return f"R{max(used, default=0) + 1}"


def add(claim: str, scope: str, confidence: float, src: str,
        path: Path = PLAYBOOK_PATH) -> dict:
    """Add one lesson under the budget rule. Returns what happened."""
    if not (scope == "global" or scope.startswith("stack:")):
        return {"action": "rejected", "reason": f"scope '{scope}' does not cross projects"}
    lessons = load(path)
    for existing in lessons:
        if existing.claim.strip().lower() == claim.strip().lower():
            existing.hits += 1  # re-learning the same thing is evidence, not a duplicate row
            save(lessons, path)
            return {"action": "reinforced", "id": existing.id, "hits": existing.hits}

    lesson = Lesson(id=next_id(lessons), scope=scope, claim=claim.strip(),
                    confidence=max(0.0, min(1.0, confidence)), src=src)
    displaced = None
    if len(lessons) >= MAX_LESSONS:
        weakest = min(lessons, key=lambda l: l.score)
        if lesson.score <= weakest.score:
            return {"action": "rejected", "reason":
                    f"playbook full ({MAX_LESSONS}) and score {lesson.score:.2f} "
                    f"does not beat weakest {weakest.id} ({weakest.score:.2f})"}
        lessons.remove(weakest)
        displaced = weakest.id
    lessons.append(lesson)
    save(lessons, path)
    out = {"action": "added", "id": lesson.id}
    if displaced:
        out["displaced"] = displaced
    return out


def bump_hit(lesson_id: str, path: Path = PLAYBOOK_PATH) -> bool:
    lessons = load(path)
    for lesson in lessons:
        if lesson.id == lesson_id:
            lesson.hits += 1
            save(lessons, path)
            return True
    return False


def ensure_claude_md_reference(claude_md: Path | None = None) -> bool:
    """Reference the playbook from ~/.claude/CLAUDE.md (idempotent).
    Returns True if the file was changed."""
    target = claude_md or Path.home() / ".claude" / "CLAUDE.md"
    marker = "@~/.retro/playbook.md"
    text = target.read_text(encoding="utf-8") if target.exists() else ""
    if marker in text:
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    block = ("\n## Cross-project playbook (managed by /retro)\n"
             f"{marker}\n")
    target.write_text(text + block, encoding="utf-8")
    return True
