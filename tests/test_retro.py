import json
import subprocess
from pathlib import Path

from retro import classify, playbook
from retro.inputs import _FAILURE_LINE, _LESSON_LINE
from retro.playbook import Lesson, add, load, save

# ---- learned-behavior review parser (the fragile seam) ----------------------

def test_review_line_shapes_parse():
    f = _FAILURE_LINE.match(
        "- 3x Bash: npm ERR! peer dep conflict (last seen 2026-09-01T10:00:00+00:00)")
    assert f and int(f["count"]) == 3 and f["tool"] == "Bash"
    l = _LESSON_LINE.match(
        "- [approved] Use sh -c: vapor image has no bash — use sh -c "
        "(confidence 0.85, observations 4)")
    assert l and l["status"] == "approved" and float(l["confidence"]) == 0.85


# ---- scope classifier --------------------------------------------------------

def test_classifier_project_beats_stack(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'")
    pkg = tmp_path / "rxguard"
    pkg.mkdir(); (pkg / "__init__.py").touch()
    got = classify.suggest_scope("rxguard's gold layer must never read live LLM output", tmp_path)
    assert got["scope"] == "project"


def test_classifier_stack_and_unknown(tmp_path):
    assert classify.suggest_scope("pydantic v2 validators run before type coercion", tmp_path)["scope"] == "stack"
    assert classify.suggest_scope("verify assumptions against primary sources", tmp_path)["scope"] == "global"
    assert classify.suggest_scope("the blue button flickers", tmp_path)["scope"] == "unknown"


# ---- playbook budget ---------------------------------------------------------

def test_playbook_roundtrip_and_budget(tmp_path):
    pb = tmp_path / "playbook.md"
    for i in range(playbook.MAX_LESSONS):
        result = add(f"lesson number {i}", "global", 0.5 + i * 0.01, "seed", pb)
        assert result["action"] == "added"
    assert len(load(pb)) == playbook.MAX_LESSONS

    # too weak to displace anything
    rejected = add("a weak new idea", "global", 0.10, "x", pb)
    assert rejected["action"] == "rejected"

    # strong enough: displaces the weakest (lesson number 0, score 0.50)
    accepted = add("a strong new rule", "global", 0.99, "x", pb)
    assert accepted["action"] == "added" and accepted["displaced"]
    claims = [l.claim for l in load(pb)]
    assert "lesson number 0" not in claims and "a strong new rule" in claims


def test_duplicate_reinforces_not_duplicates(tmp_path):
    pb = tmp_path / "playbook.md"
    add("always do the thing", "global", 0.6, "a", pb)
    again = add("Always do the thing", "global", 0.6, "b", pb)
    assert again["action"] == "reinforced"
    lessons = load(pb)
    assert len(lessons) == 1 and lessons[0].hits == 1


def test_project_scope_rejected_from_playbook(tmp_path):
    pb = tmp_path / "playbook.md"
    assert add("repo-only detail", "project", 0.9, "x", pb)["action"] == "rejected"


def test_save_load_stable(tmp_path):
    pb = tmp_path / "playbook.md"
    save([Lesson(id="R1", scope="stack:python", claim="c1", confidence=0.7, hits=2, src="s")], pb)
    loaded = load(pb)
    assert loaded[0].scope == "stack:python" and loaded[0].hits == 2
    save(loaded, pb)
    assert load(pb)[0].claim == "c1"


# ---- CLI smoke ----------------------------------------------------------------

def test_cli_inputs_runs_on_a_git_repo(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / "a.txt").write_text("x")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                    "commit", "-qm", "init"], cwd=tmp_path, check=True)
    out = subprocess.run(
        ["python", "-m", "retro.cli", "inputs", "--repo", str(tmp_path)],
        capture_output=True, text=True, check=True)
    data = json.loads(out.stdout)
    assert data["git"]["commit_count"] == 1
    assert data["git"]["last_retro_tag"] is None


def test_retro_json_commit_is_the_boundary_when_tags_missing(tmp_path):
    def g(*a):
        subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", *a],
                       cwd=tmp_path, check=True, capture_output=True)
    g("init", "-q")
    (tmp_path / "a.txt").write_text("1"); g("add", "."); g("commit", "-qm", "one")
    (tmp_path / "retro.json").write_text("{}"); g("add", "."); g("commit", "-qm", "retro")
    (tmp_path / "b.txt").write_text("2"); g("add", "."); g("commit", "-qm", "after")

    from retro.inputs import git_since_last_retro
    got = git_since_last_retro(str(tmp_path))
    assert got["last_retro_tag"] is None
    assert got["last_retro_boundary_sha"]
    assert got["commit_count"] == 1
    assert got["commits"][0]["subject"] == "after"
