# upstream/

Patches retro depends on that live in other projects until merged.

- `learned-behavior-review-json.patch` — `review --output json` for lisn0/learned-behavior.
  retro's `inputs.py` uses the JSON output when the installed learned-behavior
  supports it and falls back to parsing the text lines otherwise, so it works
  either way. PR text: `learned-behavior-review-json.PR.md`.
