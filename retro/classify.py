"""Scope suggestion for lessons: project | stack | global.

The classifier only SUGGESTS — the interview confirms. It errs toward
narrow scopes on weak evidence: a project lesson wrongly kept local costs one
repo a re-learn; a project lesson wrongly promoted to global rots the
cross-project playbook, which is the failure the whole scope rule exists to
prevent. When it has no signal it says so ("unknown") instead of guessing,
so the human question actually gets asked.
"""

from __future__ import annotations

import re
from pathlib import Path

# manifest file -> stack tokens it implies
_MANIFEST_STACKS = {
    "pyproject.toml": ["python"],
    "requirements.txt": ["python"],
    "package.json": ["node", "javascript", "typescript"],
    "tsconfig.json": ["typescript"],
    "Cargo.toml": ["rust"],
    "go.mod": ["go"],
    "pom.xml": ["java"],
    "Dockerfile": ["docker"],
    "docker-compose.yml": ["docker"],
}

# tech terms that mark a claim as stack-scoped even without repo manifests
_STACK_TERMS = {
    "python", "pydantic", "fastapi", "pytest", "pip", "venv", "duckdb", "pandas",
    "node", "npm", "typescript", "javascript", "react", "next.js", "jekyll",
    "docker", "playwright", "sqlite", "git", "github", "github actions",
    "github pages", "powershell", "windows", "bash", "curl", "python-docx",
}

_GLOBAL_MARKERS = (
    # phrasing that describes how the developer/agent works, not a technology
    "before", "always", "never", "when estimating", "verify", "check", "assume",
    "ask", "confirm", "prefer", "avoid",
)


def detect_stack(repo: str) -> list[str]:
    root = Path(repo)
    tokens: list[str] = []
    for manifest, stacks in _MANIFEST_STACKS.items():
        if (root / manifest).exists():
            tokens.extend(stacks)
    return sorted(set(tokens))


def repo_terms(repo: str) -> list[str]:
    """Identifiers that mark a claim as project-scoped: the repo name and its
    top-level packages/modules."""
    root = Path(repo).resolve()
    terms = {root.name.lower().replace("_", "-"), root.name.lower()}
    for child in root.iterdir():
        if child.is_dir() and not child.name.startswith(".") and (child / "__init__.py").exists():
            terms.add(child.name.lower())
    return sorted(terms)


def suggest_scope(claim: str, repo: str) -> dict:
    """Return {"scope": project|stack|global|unknown, "reason": str, "stack": [...]}"""
    text = claim.lower()
    hits_project = [t for t in repo_terms(repo) if t and t in text]
    if hits_project:
        return {"scope": "project", "stack": [],
                "reason": f"claim names project identifiers: {', '.join(hits_project)}"}

    words = set(re.findall(r"[a-z0-9.+-]+", text))
    hits_stack = sorted(_STACK_TERMS & words)
    # multi-word terms
    hits_stack += [t for t in _STACK_TERMS if " " in t and t in text]
    if hits_stack:
        return {"scope": "stack", "stack": hits_stack,
                "reason": f"claim names stack technology: {', '.join(sorted(set(hits_stack)))}"}

    if any(text.startswith(m) or f" {m} " in text for m in _GLOBAL_MARKERS):
        return {"scope": "global", "stack": [],
                "reason": "claim reads as a working-practice rule with no project or stack tie"}

    return {"scope": "unknown", "stack": [],
            "reason": "no project, stack, or practice signal — decide in the interview"}
