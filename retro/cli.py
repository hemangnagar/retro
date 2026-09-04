"""retro CLI — the deterministic plumbing the /retro skill drives.

Subcommands:
  inputs    gather learned-behavior review + git history + transcripts (JSON)
  classify  suggest a scope for one lesson claim (JSON)
  playbook  init | add | list | hit | status   (the size-capped playbook)
  finish    write retro.json into the repo and create the retro/<date> tag
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

from . import classify as classify_mod
from . import inputs as inputs_mod
from . import playbook as playbook_mod
from . import questions as questions_mod


def _print(obj) -> None:
    print(json.dumps(obj, indent=2))


def cmd_inputs(args) -> int:
    _print(inputs_mod.gather(args.repo, extra_transcript_dirs=args.transcripts))
    return 0


def cmd_questions(args) -> int:
    _print({
        "interview": [{"key": k, "question": q} for k, q in questions_mod.INTERVIEW],
        "reply_protocol": questions_mod.REPLY_PROTOCOL,
        "scope_options": [{"option": k, "meaning": d} for k, d in questions_mod.SCOPE_OPTIONS],
    })
    return 0


def cmd_classify(args) -> int:
    suggestion = classify_mod.suggest_scope(args.claim, args.repo)
    suggestion["options"] = [k for k, _ in questions_mod.SCOPE_OPTIONS]
    suggestion["prompt"] = questions_mod.scope_prompt(
        args.index, args.claim, args.evidence or [], suggestion["scope"])
    _print(suggestion)
    return 0


def cmd_scope(args) -> int:
    parsed = questions_mod.parse_scope_answer(args.answer)
    _print({"answer": args.answer, "scope": parsed, "valid": parsed is not None,
            "options": [k for k, _ in questions_mod.SCOPE_OPTIONS]})
    return 0 if parsed else 1


def cmd_playbook(args) -> int:
    path = Path(args.path) if args.path else playbook_mod.PLAYBOOK_PATH
    if args.action == "init":
        template = Path(__file__).resolve().parents[1] / "playbook.md"
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(template.read_text(encoding="utf-8"), encoding="utf-8")
        changed = playbook_mod.ensure_claude_md_reference()
        _print({"playbook": str(path), "created": True,
                "claude_md_updated": changed})
    elif args.action == "add":
        _print(playbook_mod.add(args.claim, args.scope, args.confidence,
                                args.src or "manual", path))
    elif args.action == "hit":
        _print({"bumped": playbook_mod.bump_hit(args.id, path)})
    elif args.action in ("list", "status"):
        lessons = playbook_mod.load(path)
        _print({"count": len(lessons), "cap": playbook_mod.MAX_LESSONS,
                "lessons": [vars(l) | {"score": round(l.score, 2)} for l in lessons]})
    return 0


def cmd_finish(args) -> int:
    repo = Path(args.repo).resolve()
    retro_file = Path(args.retro_json).resolve()
    if not retro_file.exists():
        print(f"retro json not found: {retro_file}", file=sys.stderr)
        return 1
    data = json.loads(retro_file.read_text(encoding="utf-8"))  # validate it parses
    dest = repo / "retro.json"
    dest.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    tag = f"retro/{date.today().isoformat()}"
    result = subprocess.run(["git", "tag", tag], cwd=repo, capture_output=True, text=True)
    _print({"retro_json": str(dest), "tag": tag,
            "tag_created": result.returncode == 0,
            "tag_note": result.stderr.strip() or None})
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="retro", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("inputs", help="gather retro inputs as JSON")
    p.add_argument("--repo", default=".")
    p.add_argument("--transcripts", nargs="*", default=None,
                   help="extra transcript directories to include")
    p.set_defaults(func=cmd_inputs)

    p = sub.add_parser("questions", help="print the fixed interview script + scope menu")
    p.set_defaults(func=cmd_questions)

    p = sub.add_parser("classify", help="suggest a scope for a lesson claim (+ the menu prompt)")
    p.add_argument("--claim", required=True)
    p.add_argument("--repo", default=".")
    p.add_argument("--index", type=int, default=1, help="lesson number shown in the prompt")
    p.add_argument("--evidence", nargs="*", help="evidence refs shown in the prompt")
    p.set_defaults(func=cmd_classify)

    p = sub.add_parser("scope", help="normalize a user's scope reply to a menu option")
    p.add_argument("answer")
    p.set_defaults(func=cmd_scope)

    p = sub.add_parser("playbook", help="manage the cross-project playbook")
    p.add_argument("action", choices=["init", "add", "list", "hit", "status"])
    p.add_argument("--claim")
    p.add_argument("--scope")
    p.add_argument("--confidence", type=float, default=0.7)
    p.add_argument("--src")
    p.add_argument("--id")
    p.add_argument("--path", help="override playbook path (tests)")
    p.set_defaults(func=cmd_playbook)

    p = sub.add_parser("finish", help="write retro.json + retro/<date> tag")
    p.add_argument("--repo", default=".")
    p.add_argument("--retro-json", required=True)
    p.set_defaults(func=cmd_finish)

    args = parser.parse_args(argv)
    if args.command == "playbook" and args.action == "add" and not (args.claim and args.scope):
        parser.error("playbook add requires --claim and --scope")
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
