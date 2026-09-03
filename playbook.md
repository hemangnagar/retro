# Cross-project playbook

Lessons that earned their way out of a single project. Curated by /retro:
scoped `global` or `stack:<name>`, size-capped at 25 — a new lesson must
displace a weaker one to get in. Do not hand-edit the metadata comments.

- [global] Private GitHub repo access from a sandbox needs a fine-grained token with Contents: Read set explicitly — repo selection alone gives "Resource not accessible". Revoke after use. <!-- id:R1 conf:0.90 hits:0 added:2026-09-03 src:seed -->
- [stack:windows] Claude Code on Windows: PATH fix is $env:USERPROFILE\.local\bin via [Environment]::SetEnvironmentVariable, then close all terminals. <!-- id:R2 conf:0.90 hits:0 added:2026-09-03 src:seed -->
- [stack:python] Docx → template transfer: python-docx style assignment needs no_numbering() (inject w:numId val=0) to stop template auto-numbering on transferred headings. <!-- id:R3 conf:0.85 hits:0 added:2026-09-03 src:seed -->
