#!/usr/bin/env python3
"""Build the retro flow diagram: docs/retro-flow.svg (standalone, light) and
docs/retro-flow.html (themed page with the same SVG inline).
Hand-authored SVG; the only dependency is Python."""
from __future__ import annotations
from pathlib import Path

HERE = Path(__file__).resolve().parent
W, H = 1200, 1090

# ---- tokens: placeholders resolved per output ---------------------------------
LIGHT = {"PAPER": "#f6f5f1", "CARD": "#ffffff", "INK": "#1b1f24", "MUTED": "#5f6670",
         "LINE": "#1b1f24", "ACCENT": "#5b4bd6", "ACCENT_SOFT": "#e9e6fb",
         "AMBER": "#b7791f", "AMBER_SOFT": "#fbf1dc", "HILITE": "#d9d3ff"}
VARS = {k: f"var(--{k.lower()})" for k in LIGHT}


def node(x, y, w, h, title, sub=None, sub2=None, fill="{CARD}", stroke="{LINE}", title_size=15):
    parts = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>']
    ty = y + (h / 2 - 8 if (sub or sub2) else h / 2 + 5)
    if sub and sub2:
        ty = y + h / 2 - 18
    parts.append(f'<text x="{x + w/2}" y="{ty:.0f}" text-anchor="middle" font-size="{title_size}" font-weight="600" fill="{{INK}}">{title}</text>')
    if sub:
        parts.append(f'<text x="{x + w/2}" y="{ty + 19:.0f}" text-anchor="middle" font-size="12" font-family="{{MONO}}" fill="{{MUTED}}">{sub}</text>')
    if sub2:
        parts.append(f'<text x="{x + w/2}" y="{ty + 37:.0f}" text-anchor="middle" font-size="12" font-family="{{MONO}}" fill="{{MUTED}}">{sub2}</text>')
    return "\n".join(parts)


def badge(x, y, text):
    w = 8 * len(text) + 18
    return (f'<rect x="{x}" y="{y}" width="{w}" height="22" rx="11" fill="{{AMBER_SOFT}}" stroke="{{AMBER}}" stroke-width="1.2"/>'
            f'<text x="{x + w/2}" y="{y + 15}" text-anchor="middle" font-size="11" font-weight="700" letter-spacing=".06em" fill="{{AMBER}}">{text}</text>')


def arrow(points, label=None, lx=None, ly=None, dashed=False, color="{LINE}", anchor="middle"):
    pts = " ".join(f"{x},{y}" for x, y in points)
    dash = ' stroke-dasharray="6 5"' if dashed else ""
    marker = "url(#arrow-accent)" if color == "{ACCENT}" else "url(#arrow)"
    s = f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="1.6"{dash} marker-end="{marker}"/>'
    if label:
        s += (f'<text x="{lx}" y="{ly}" text-anchor="{anchor}" font-size="11.5" font-family="{{MONO}}" '
              f'fill="{color if color != "{LINE}" else "{MUTED}"}">{label}</text>')
    return s


def chip(x, y, w, head, body):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="54" rx="8" fill="{{CARD}}" stroke="{{LINE}}" stroke-width="1"/>'
            f'<text x="{x + 14}" y="{y + 22}" font-size="11.5" font-weight="700" letter-spacing=".1em" fill="{{ACCENT}}">{head}</text>'
            f'<text x="{x + 14}" y="{y + 41}" font-size="12.5" fill="{{INK}}">{body}</text>')


def svg_body() -> str:
    s = []
    # title
    s.append(f'<rect x="90" y="36" width="470" height="52" fill="{{HILITE}}"/>')
    s.append(f'<text x="100" y="76" font-size="36" fill="{{INK}}"><tspan font-weight="800">Milestone Retrospectives</tspan>'
             f'<tspan font-weight="400" dx="16">with a curated playbook</tspan></text>')
    s.append(f'<text x="600" y="118" text-anchor="middle" font-size="16.5" fill="{{MUTED}}">retro turns what a project taught into lessons scoped to where they belong. A person decides what a lesson is about;</text>')
    s.append(f'<text x="600" y="141" text-anchor="middle" font-size="16.5" fill="{{MUTED}}">a size budget decides what stays. Nothing here runs per task — only at milestones.</text>')

    # ---- flow column (center x=390) ----
    s.append(node(230, 190, 320, 62, "Milestone reached", "release tag · merge to main · archive"))
    # fan-out: N1 -> three input cards
    s.append(f'<polyline points="390,252 390,268" fill="none" stroke="{{LINE}}" stroke-width="1.6"/>')
    s.append(f'<polyline points="150,268 590,268" fill="none" stroke="{{LINE}}" stroke-width="1.6"/>')
    for cx in (150, 370, 590):
        s.append(f'<polyline points="{cx},268 {cx},294" fill="none" stroke="{{LINE}}" stroke-width="1.6" marker-end="url(#arrow)"/>')
    s.append(node(50, 300, 200, 72, "git log", "since the last", "retro boundary", title_size=14))
    s.append(node(270, 300, 200, 72, "learned-behavior", "repeated failures", "candidate lessons", title_size=14))
    s.append(node(490, 300, 200, 72, "session transcripts", "~/.claude/projects/", "&lt;repo&gt;/*.jsonl", title_size=14))
    # fan-in to interview
    for cx in (150, 370, 590):
        s.append(f'<polyline points="{cx},372 {cx},398" fill="none" stroke="{{LINE}}" stroke-width="1.6"/>')
    s.append(f'<polyline points="150,398 590,398" fill="none" stroke="{{LINE}}" stroke-width="1.6"/>')
    s.append(f'<polyline points="390,398 390,414" fill="none" stroke="{{LINE}}" stroke-width="1.6" marker-end="url(#arrow)"/>')

    s.append(node(230, 420, 320, 84, "Interview — 4 fixed questions", "answers drafted from the evidence", "you reply: agree · edit · skip"))
    s.append(badge(462, 408, "HUMAN GATE"))
    s.append(arrow([(390, 504), (390, 534)]))
    s.append(node(230, 540, 320, 60, "Distill", "claim · evidence · confidence"))
    s.append(arrow([(390, 600), (390, 630)]))
    s.append(node(230, 636, 320, 76, "Scope — closed menu", "one lesson at a time", "project | stack | global | discard"))
    s.append(badge(462, 624, "HUMAN GATE"))

    # branches out of Scope
    s.append(arrow([(390, 712), (390, 764)], "stack · global", 402, 744, color="{ACCENT}", anchor="start"))
    s.append(arrow([(550, 675), (809, 675)], "project", 615, 667))
    s.append(arrow([(550, 700), (680, 700), (680, 805), (809, 805)], "discard", 714, 760, anchor="start"))

    s.append(node(230, 770, 320, 96, "Budget gate", "playbook capped at 25 slots", "must displace the weakest — or is rejected",
                  fill="{ACCENT_SOFT}", stroke="{ACCENT}"))
    # budget gate -> playbook card (route up the gap)
    s.append(f'<polyline points="550,818 700,818 700,318 809,318" fill="none" stroke="{{PAPER}}" stroke-width="7"/>')
    s.append(arrow([(550, 818), (700, 818), (700, 318), (809, 318)], color="{ACCENT}"))
    s.append(f'<text x="686" y="560" transform="rotate(-90 686 560)" text-anchor="middle" font-size="11.5" font-family="{{MONO}}" fill="{{ACCENT}}">added · reinforced · rejected</text>')
    s.append(arrow([(390, 866), (390, 904)]))
    s.append(node(230, 910, 320, 62, "Finish", "retro.json written · tag retro/YYYY-MM-DD"))
    s.append(arrow([(550, 941), (740, 941), (740, 845), (809, 845)]))
    # loop back: Finish -> git log input (dashed)
    s.append(arrow([(230, 941), (28, 941), (28, 336), (44, 336)], dashed=True))
    s.append(f'<text x="40" y="640" transform="rotate(-90 40 640)" text-anchor="middle" font-size="11.5" font-family="{{MONO}}" fill="{{MUTED}}">boundary for the next retro</text>')

    # ---- right panel: where lessons live ----
    s.append(f'<rect x="790" y="190" width="370" height="782" rx="14" fill="{{ACCENT_SOFT}}" stroke="{{ACCENT}}" stroke-width="1.5"/>')
    s.append(f'<text x="975" y="228" text-anchor="middle" font-size="16" font-weight="700" fill="{{INK}}">Where lessons live</text>')
    s.append(node(815, 255, 320, 122, "~/.retro/playbook.md", "stack:&lt;name&gt; + global lessons only", "25 slots · evidence + hit counter per line", stroke="{ACCENT}"))
    s.append(f'<text x="975" y="366" text-anchor="middle" font-size="12" font-family="{{MONO}}" fill="{{ACCENT}}">written by /retro, nothing else</text>')
    s.append(arrow([(975, 377), (975, 418)], "@-import", 986, 402, color="{ACCENT}", anchor="start"))
    s.append(node(815, 425, 320, 80, "~/.claude/CLAUDE.md", "loaded at every session start,", "in every project", stroke="{ACCENT}"))
    s.append(node(815, 630, 320, 90, "learned-behavior (SQLite)", "project lessons, this workspace only", "auto promote / decay, no LLM"))
    s.append(node(815, 760, 320, 100, "retro.json + tag retro/YYYY-MM-DD", "per-repo audit trail:", "kept · rejected · discarded"))

    # ---- footer chips ----
    s.append(chip(90, 1010, 330, "RITUAL", "runs at milestones, never every session"))
    s.append(chip(435, 1010, 330, "SCOPE", "only stack + global lessons cross projects"))
    s.append(chip(780, 1010, 330, "BUDGET", "a new lesson must displace one — or lose"))
    return "\n".join(s)


DEFS = '''<defs>
  <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
    <path d="M 0 0 L 10 5 L 0 10 z" fill="{LINE}"/></marker>
  <marker id="arrow-accent" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
    <path d="M 0 0 L 10 5 L 0 10 z" fill="{ACCENT}"/></marker>
</defs>'''

LABEL = "How retro works: a milestone triggers a retro; three local inputs feed a four-question interview a person confirms; each lesson is scoped from a closed menu; project lessons go to learned-behavior, stack and global lessons pass a size budget into a playbook loaded every session, discards are recorded in retro.json, and the retro tag becomes the next retro's boundary."


def render(tokens: dict, mono: str, standalone: bool) -> str:
    body = (DEFS + "\n" + svg_body()).replace("{MONO}", mono)
    for k, v in tokens.items():
        body = body.replace("{" + k + "}", v)
    bg = f'<rect width="{W}" height="{H}" fill="{tokens["PAPER"]}"/>\n' if standalone else ""
    font = (' font-family="IBM Plex Sans, Segoe UI, Liberation Sans, system-ui, sans-serif"')
    xmlns = ' xmlns="http://www.w3.org/2000/svg"' if standalone else ""
    return (f'<svg{xmlns} viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="{LABEL}"{font}>\n'
            f'{bg}{body}\n</svg>')


def render_png(scale: int = 2) -> Path | None:
    """Rasterize the standalone SVG with Playwright's Chromium (optional dep).
    Returns the PNG path, or None with a hint when Playwright isn't installed."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("PNG skipped: `pip install playwright && playwright install chromium` to enable --png")
        return None
    out = HERE / "retro-flow.png"
    # Screenshot the <svg> inside a minimal HTML page: Chromium's full-page
    # capture of a bare SVG document can hang, element capture is reliable.
    wrapper = HERE / ".retro-flow.render.html"
    wrapper.write_text(
        '<!doctype html><html><head><meta charset="utf-8"><style>body{margin:0;background:#f6f5f1}'
        f'svg{{display:block;width:{W}px;height:{H}px}}</style></head><body>'
        + (HERE / "retro-flow.svg").read_text(encoding="utf-8") + "</body></html>", encoding="utf-8")
    import os
    # A pinned Playwright may not match the browsers on disk; point it at one
    # with PLAYWRIGHT_CHROMIUM_EXECUTABLE=/path/to/chrome when that happens.
    launch_kwargs = {}
    if os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE"):
        launch_kwargs["executable_path"] = os.environ["PLAYWRIGHT_CHROMIUM_EXECUTABLE"]
    with sync_playwright() as pw:
        browser = pw.chromium.launch(**launch_kwargs)
        page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=scale)
        page.goto(wrapper.resolve().as_uri())
        page.wait_for_timeout(300)
        page.locator("svg").screenshot(path=str(out))
        browser.close()
    wrapper.unlink(missing_ok=True)
    return out


if __name__ == "__main__":
    import sys
    mono = "IBM Plex Mono, ui-monospace, Consolas, Liberation Mono, monospace"
    (HERE / "retro-flow.svg").write_text(render(LIGHT, mono, standalone=True), encoding="utf-8")
    inline = render(VARS, mono, standalone=False)
    page = (HERE / "retro-flow.template.html").read_text(encoding="utf-8").replace("{{SVG}}", inline)
    (HERE / "retro-flow.html").write_text(page, encoding="utf-8")
    print("wrote docs/retro-flow.svg and docs/retro-flow.html")
    if "--png" in sys.argv:
        png = render_png()
        if png:
            print(f"wrote {png.relative_to(HERE.parent)} ({png.stat().st_size // 1024} KB)")
