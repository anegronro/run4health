"""Which sessions have been completed.

One small JSON file, one user: this app is served on a private tailnet and
has no login, so there is nothing to key the progress by. Kept out of git
and out of the deploy rsync, so redeploying never wipes it.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STORE = Path(os.environ.get("FITNESS_PROGRESS", ROOT / "data" / "progress.json"))


def key(slug: str, week: int, day: int) -> str:
    return f"{slug}/w{week}/d{day}"


def load() -> set[str]:
    try:
        raw = json.loads(STORE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()
    return set(raw.get("done", []))


def _save(done: set[str]) -> None:
    STORE.parent.mkdir(parents=True, exist_ok=True)
    # Write beside the target and rename, so an interrupted write can't
    # leave a truncated file behind.
    tmp = STORE.with_suffix(".json.tmp")
    tmp.write_text(
        json.dumps({"done": sorted(done)}, indent=2) + "\n", encoding="utf-8"
    )
    tmp.replace(STORE)


def set_done(slug: str, week: int, day: int, done: bool) -> set[str]:
    current = load()
    k = key(slug, week, day)
    current.add(k) if done else current.discard(k)
    _save(current)
    return current


def clear_program(slug: str) -> set[str]:
    current = {k for k in load() if not k.startswith(f"{slug}/")}
    _save(current)
    return current
