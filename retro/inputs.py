"""Gather retro inputs: learned-behavior review, git history, transcripts.

Everything degrades gracefully — a missing CLI, a repo with no retro tag yet,
or an absent transcripts directory each produce an explicit "available: False"
(or empty list) rather than an error, because the interview must be able to
run on day one of any machine.
"""

from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

# learned-behavior's `review` output is plain text (no JSON mode as of 0.x —
# see upstream learning.py:command_review). These two regexes match the only
# two structured line shapes it prints. Alpha software, single maintainer:
# on any drift the line simply lands in `unparsed` instead of crashing.
_FAILURE_LINE = re.compile(
    r"^- (?P<count>\d+)x (?P<tool>\S+): (?P<summary>.*) \(last seen (?P<last_seen>[^)]*)\)$"
)
_LESSON_LINE = re.compile(
    r"^- \[(?P<status>\w+)\] (?P<title>.*?): (?P<rule>.*) "
    r"\(confidence (?P<confidence>[\d.]+), observations (?P<observations>\d+)\)$"
)


def _run(cmd: list[str], cwd: str | None = None) -> tuple[int, str]:
    try:
        proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=60)
        return proc.returncode, (proc.stdout or "") + (proc.stderr or "")
    except FileNotFoundError:
        return 127, f"{cmd[0]}: not found"
    except subprocess.TimeoutExpired:
        return 124, f"{cmd[0]}: timed out"


def lb_review(workspace: str, include_candidates: bool = True) -> dict:
    """Parse `learned-behavior review` for a workspace into structured rows."""
    cmd = ["learned-behavior", "review", "--workspace", workspace]
    if include_candidates:
        cmd.append("--all")
    code, out = _run(cmd)
    if code != 0:
        return {"available": False, "error": out.strip()[:300],
                "repeated_failures": [], "lessons": [], "unparsed": []}

    failures, lessons, unparsed = [], [], []
    section = None
    for line in out.splitlines():
        stripped = line.strip()
        if stripped == "Repeated failures:":
            section = "failures"
        elif stripped == "Stored lessons:":
            section = "lessons"
        elif stripped.startswith("- "):
            match = _FAILURE_LINE.match(stripped) if section == "failures" else None
            if match:
                row = match.groupdict()
                row["count"] = int(row["count"])
                failures.append(row)
                continue
            match = _LESSON_LINE.match(stripped) if section == "lessons" else None
            if match:
                row = match.groupdict()
                row["confidence"] = float(row["confidence"])
                row["observations"] = int(row["observations"])
                lessons.append(row)
                continue
            unparsed.append(stripped)
    return {"available": True, "repeated_failures": failures,
            "lessons": lessons, "unparsed": unparsed}


def last_retro_tag(repo: str) -> str | None:
    code, out = _run(["git", "tag", "--list", "retro/*", "--sort=-creatordate"], cwd=repo)
    if code != 0:
        return None
    tags = [t for t in out.splitlines() if t.strip()]
    return tags[0] if tags else None


def last_retro_boundary(repo: str) -> tuple[str | None, str | None]:
    """(tag, sha) of the previous retro. Tags are the primary marker, but
    some hosted environments refuse tag pushes, so the commit that last
    touched retro.json is an equivalent boundary on a fresh clone."""
    tag = last_retro_tag(repo)
    if tag:
        return tag, None
    code, out = _run(["git", "log", "-1", "--format=%H", "--", "retro.json"], cwd=repo)
    sha = out.strip() if code == 0 and out.strip() else None
    return None, sha


def git_since_last_retro(repo: str, fallback_commits: int = 200) -> dict:
    """Commits + diffstat since the last retro boundary (bounded otherwise)."""
    tag, boundary_sha = last_retro_boundary(repo)
    start = tag or boundary_sha
    span = f"{start}..HEAD" if start else f"-{fallback_commits}"
    code, log = _run(["git", "log", span, "--pretty=format:%h|%ad|%s", "--date=short"], cwd=repo)
    commits = []
    if code == 0:
        for line in log.splitlines():
            parts = line.split("|", 2)
            if len(parts) == 3:
                commits.append({"sha": parts[0], "date": parts[1], "subject": parts[2]})
    # Diff against the oldest visible sha, never HEAD~N: on shallow clones
    # HEAD~N crosses the shallow boundary and git errors out.
    if start:
        stat_range = [f"{start}..HEAD"]
    elif len(commits) > 1:
        stat_range = [f"{commits[-1]['sha']}..HEAD"]
    else:
        stat_range = None
    _, stat = _run(["git", "diff", "--stat", *stat_range], cwd=repo) if stat_range else (0, "")
    _, head = _run(["git", "rev-parse", "--short", "HEAD"], cwd=repo)
    return {"last_retro_tag": tag, "last_retro_boundary_sha": boundary_sha,
            "head": head.strip(), "commit_count": len(commits),
            "commits": commits, "diffstat_tail": stat.strip().splitlines()[-1:] }


def transcript_files(repo: str, projects_dir: str | None = None,
                     extra_dirs: list[str] | None = None, limit: int = 10) -> list[dict]:
    """Claude Code transcripts for this repo (newest first, paths only).

    Claude Code stores transcripts under ~/.claude/projects/<encoded-cwd>/ —
    the cwd with path separators flattened to '-'. Sessions that worked on
    this repo from a DIFFERENT cwd won't be found automatically; pass those
    via extra_dirs.
    """
    base = Path(projects_dir or Path.home() / ".claude" / "projects")
    # Claude Code flattens EVERY non-alphanumeric in the cwd to '-'
    # (/home/user/grocery_optimizer -> -home-user-grocery-optimizer),
    # so mirror that exactly rather than translating separators only.
    encoded = re.sub(r"[^A-Za-z0-9-]", "-", str(Path(repo).resolve()))
    candidates = [base / encoded] + [Path(d) for d in (extra_dirs or [])]
    rows = []
    for directory in candidates:
        if not directory.is_dir():
            continue
        for path in directory.glob("*.jsonl"):
            stat = path.stat()
            rows.append({"path": str(path), "bytes": stat.st_size,
                         "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
                                             .isoformat(timespec="seconds")})
    rows.sort(key=lambda r: r["modified"], reverse=True)
    return rows[:limit]


def gather(repo: str, projects_dir: str | None = None,
           extra_transcript_dirs: list[str] | None = None) -> dict:
    return {
        "repo": str(Path(repo).resolve()),
        "gathered_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "learned_behavior": lb_review(str(Path(repo).resolve())),
        "git": git_since_last_retro(repo),
        "transcripts": transcript_files(repo, projects_dir, extra_transcript_dirs),
    }


if __name__ == "__main__":  # manual sanity check
    print(json.dumps(gather("."), indent=2))
