"""Which sessions each person has completed.

One JSON file holding one list of keys per person. Kept out of git and out
of the deploy rsync, so redeploying never wipes it.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STORE = Path(os.environ.get("FITNESS_PROGRESS", ROOT / "data" / "progress.json"))


def key(slug: str, week: int, day: int) -> str:
    return f"{slug}/w{week}/d{day}"


def _read_all() -> dict[str, list[str]]:
    try:
        raw = json.loads(STORE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    done = raw.get("done", {})
    # Before profiles existed this was a single flat list shared by everyone.
    # Park it under "everyone" rather than dropping someone's ticks.
    if isinstance(done, list):
        return {"everyone": done} if done else {}
    return {k: list(v) for k, v in done.items()}


def _write_all(everyone: dict[str, list[str]]) -> None:
    STORE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STORE.with_suffix(".json.tmp")
    payload = {"done": {k: sorted(v) for k, v in everyone.items() if v}}
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    tmp.replace(STORE)


def load(person: str) -> set[str]:
    return set(_read_all().get(person, []))


def set_done(person: str, slug: str, week: int, day: int, done: bool) -> set[str]:
    everyone = _read_all()
    mine = set(everyone.get(person, []))
    k = key(slug, week, day)
    mine.add(k) if done else mine.discard(k)
    everyone[person] = sorted(mine)
    _write_all(everyone)
    return mine


def clear_program(person: str, slug: str) -> set[str]:
    everyone = _read_all()
    mine = {k for k in everyone.get(person, []) if not k.startswith(f"{slug}/")}
    everyone[person] = sorted(mine)
    _write_all(everyone)
    return mine


def forget(person: str) -> None:
    """Drop everything for one person, when their profile is deleted."""
    everyone = _read_all()
    everyone.pop(person, None)
    _write_all(everyone)
