#!/usr/bin/env python3
"""Freezes the running app into a static site anyone can click through.

Every page is already rendered on the server with its CSS and photos inlined,
so a saved page is self-contained. This walks the app as a signed-in demo
user, saves each page, and rewrites the links to point at the saved files —
giving a browsable demo with no server, no database and no sign-in.

Anything that would write (ticking a session, signing in) is disabled and
labelled, rather than left to fail silently when someone clicks it.

    python scripts/build_demo.py http://127.0.0.1:8770 <session-cookie> <gate-cookie>
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.request import Request, urlopen

OUT = Path(__file__).resolve().parent.parent / "docs" / "demo"

BANNER = """<div class="demo-banner">
  <b>Static demo.</b> A real copy of the app, frozen — browse the programs and
  the training log. Ticking a session needs the live version.
  <a href="https://github.com/anegronro/run4health">Source</a>
</div>
<style>
.demo-banner{
  position:sticky;top:0;z-index:60;padding:9px 16px;font-size:13px;
  background:#4ade80;color:#0e0f13;text-align:center;line-height:1.4;
}
.demo-banner a{color:#0e0f13}
.check,.done-btn,.reset,.account-out,.signin-form button{
  pointer-events:none;opacity:.55;
}
</style>
"""


def filename(path: str) -> str:
    """A flat name per page, so every link is a plain relative href."""
    if path in ("/", ""):
        return "index.html"
    return path.strip("/").replace("/", "-") + ".html"


def fetch(base: str, path: str, cookies: str) -> str:
    req = Request(base + path, headers={"Cookie": cookies})
    with urlopen(req) as r:
        return r.read().decode("utf-8")


def rewrite(html: str, keep: set[str]) -> str:
    """Point internal links at the saved files; neuter what can't work."""
    def link(m):
        href = m.group(2)
        if href.startswith(("http", "#", "mailto:", "data:")):
            return m.group(0)
        clean = href.split("?")[0].split("#")[0]
        if clean in keep:
            return f'{m.group(1)}="{filename(clean)}"'
        # A page we didn't save — leave it visibly inert rather than broken.
        return f'{m.group(1)}="#"'

    html = re.sub(r'(href)="([^"]*)"', link, html)
    html = re.sub(r'<form([^>]*)>', r'<form\1 onsubmit="return false">', html)
    return html.replace("<body", BANNER.join(["", ""]) + "<body", 1) if False else html


def main() -> int:
    base, sid, gate = sys.argv[1], sys.argv[2], sys.argv[3]
    cookies = f"sid={sid}; gate={gate}"

    index = fetch(base, "/", cookies)
    slugs = sorted(set(re.findall(r'href="/program/([a-z0-9\-]+)"', index)))
    paths = ["/", "/me", "/privacy"]
    for slug in slugs:
        paths.append(f"/program/{slug}")
        page = fetch(base, f"/program/{slug}", cookies)
        paths += sorted(set(
            f"/program/{slug}/w{w}/d{d}"
            for w, d in re.findall(rf'href="/program/{slug}/w(\d+)/d(\d+)"', page)
        ), key=lambda p: [int(n) for n in re.findall(r"\d+", p)])

    keep = set(paths)
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.html"):
        old.unlink()

    for path in paths:
        html = rewrite(fetch(base, path, cookies), keep)
        # The banner goes right after <body ...>, so it sits above everything.
        html = re.sub(r"(<body[^>]*>)", r"\1" + BANNER, html, count=1)
        (OUT / filename(path)).write_text(html, encoding="utf-8")

    total = sum(f.stat().st_size for f in OUT.glob("*.html"))
    print(f"{len(paths)} pages -> {OUT} ({total / 1024 / 1024:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
