"""Moves the old JSON files into the database, once.

Accounts created before passwords existed arrive with no password set: their
owner claims them by signing up again with the same address, which is safe
because the shared password already stands in front of the whole app.
"""
from __future__ import annotations

import json
from pathlib import Path

from . import db

ROOT = Path(__file__).resolve().parent.parent
OLD_PEOPLE = ROOT / "data" / "people.json"
OLD_PROGRESS = ROOT / "data" / "progress.json"


def _read(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def run() -> str:
    people = _read(OLD_PEOPLE).get("people", [])
    done = _read(OLD_PROGRESS).get("done", {})
    if isinstance(done, list):
        done = {"everyone": done}
    if not people and not done:
        return "nothing to migrate"

    moved_people = moved_done = 0
    with db.connect() as con:
        for person in people:
            cur = con.execute(
                "INSERT OR IGNORE INTO people (email, name, color) VALUES (?, ?, ?)",
                (person["id"], person.get("name") or person["id"].split("@")[0],
                 person.get("color") or "#5b8cff"),
            )
            moved_people += cur.rowcount
        for email, items in done.items():
            # Progress belonging to nobody would break the foreign key.
            if not con.execute("SELECT 1 FROM people WHERE email = ?", (email,)).fetchone():
                continue
            for item in items:
                cur = con.execute(
                    "INSERT OR IGNORE INTO done (email, item) VALUES (?, ?)",
                    (email, item),
                )
                moved_done += cur.rowcount

    for path in (OLD_PEOPLE, OLD_PROGRESS):
        if path.exists():
            path.rename(path.with_suffix(".json.migrated"))
    return f"migrated {moved_people} people and {moved_done} ticks"
