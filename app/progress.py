"""Which sessions each person has completed.

Every tick carries the moment it was made, which the JSON file never did —
that is what any future "miles this month" or streak has to be built on.
"""
from __future__ import annotations

from . import db


def key(slug: str, week: int, day: int) -> str:
    return f"{slug}/w{week}/d{day}"


def load(email: str) -> set[str]:
    with db.connect() as con:
        rows = con.execute("SELECT item FROM done WHERE email = ?", (email,)).fetchall()
    return {row["item"] for row in rows}


def set_done(email: str, slug: str, week: int, day: int, done: bool) -> None:
    item = key(slug, week, day)
    with db.connect() as con:
        if done:
            con.execute(
                "INSERT OR IGNORE INTO done (email, item) VALUES (?, ?)", (email, item)
            )
        else:
            con.execute("DELETE FROM done WHERE email = ? AND item = ?", (email, item))


def clear_program(email: str, slug: str) -> None:
    with db.connect() as con:
        con.execute(
            "DELETE FROM done WHERE email = ? AND item LIKE ?", (email, f"{slug}/%")
        )
