# PR: `review --output json`

_Target: lisn0/learned-behavior `main` (patch made against 6ff565e). Apply on a
fork with `git am docs/upstream/learned-behavior-review-json.patch`, push, open PR._

**Title:** review: add `--output json` for scripts and other tools

**Body:**

`learned-behavior review` is the natural surface for anything that wants to
build on the stored lessons, but its output is human text: `rule_text` and
error summaries are truncated, and the line format isn't a contract. This
adds `--output json` (mirroring the existing `advice --output` flag) that
emits the same query results as a stable, untruncated shape:

```json
{
  "workspace": "...", "since": "...", "include_candidates": false,
  "repeated_failures": [{"fingerprint", "tool_name", "summary", "count", "last_seen"}],
  "lessons": [{"status", "title", "rule_text", "confidence", "observations", "updated_at"}]
}
```

- Default output is unchanged (`--output text`).
- Two tests: JSON shape + untruncated rule_text; text output still has its header/sections.
- CHANGELOG (Unreleased) and README cheatsheet updated.

Context: I'm building a small retrospective layer on top of learned-behavior
(milestone interviews that scope lessons as project / stack / global and keep
cross-project ones in a size-capped playbook: github.com/hemangnagar/retro).
It reads `review` to seed the interview; I was parsing the text lines, which
is fragile against your own changes, hence the flag. Happy to adjust the
field names to whatever you'd prefer as the contract.
