"""Who is using the app.

Identity is an email address and nothing else: no password, no verification.
This is four or five people who know each other on a private tailnet, so an
email is a label that keeps their progress apart — it is not proof of who
they are, and anyone who can reach the app can type anyone's address.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STORE = Path(os.environ.get("FITNESS_PEOPLE", ROOT / "data" / "people.json"))

MAX_PEOPLE = 12
COLORS = ["#4ade80", "#5b8cff", "#f59e0b", "#a78bfa", "#f472b6", "#22d3ee"]
# Deliberately loose: enough to catch a typo, not to police what is valid.
EMAIL = re.compile(r"^[^@\s]+@[^@\s.]+(\.[^@\s.]+)+$")


class PersonError(Exception):
    pass


def normalise(email: str) -> str:
    return " ".join(email.split()).lower()[:120]


def guess_name(email: str) -> str:
    """A first guess at someone's name, from the part before the @.

    Only ever a suggestion to prefill the name screen with — an address
    cannot know that angel is written Ángel.
    """
    local = email.split("@")[0]
    parts = [p for p in re.split(r"[._\-+]+", local) if p]
    return " ".join(p[:1].upper() + p[1:] for p in parts) or local


def tidy_name(name: str) -> str:
    """Trim it, cap the length, and capitalise only if they typed it all in
    lower case — so "angel" becomes "Ángel"-shaped, while "Ángel de la Cruz"
    is left exactly as written."""
    name = " ".join(name.split())[:40]
    if name and name == name.lower():
        name = " ".join(w[:1].upper() + w[1:] for w in name.split())
    return name


def load() -> list[dict]:
    try:
        raw = json.loads(STORE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return []
    people = raw.get("people", [])
    for person in people:
        # "named" says whether they chose it themselves; if not, we show a
        # guess and ask them once.
        person["named"] = bool(person.get("name"))
        person["name"] = person.get("name") or guess_name(person["id"])
    return people


def _save(people: list[dict]) -> None:
    STORE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STORE.with_suffix(".json.tmp")
    tmp.write_text(
        json.dumps({"people": people}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    tmp.replace(STORE)


def get(email: str) -> dict | None:
    email = normalise(email)
    return next((p for p in load() if p["id"] == email), None)


def sign_in(email: str) -> dict:
    """Look the address up, creating the profile the first time it is used."""
    email = normalise(email)
    if not email:
        raise PersonError("Type your email address.")
    if not EMAIL.match(email):
        raise PersonError("That doesn't look like an email address.")
    people = load()
    existing = next((p for p in people if p["id"] == email), None)
    if existing:
        return existing
    if len(people) >= MAX_PEOPLE:
        raise PersonError(f"This app is set up for {MAX_PEOPLE} people at most.")
    person = {"id": email, "name": "", "color": COLORS[len(people) % len(COLORS)]}
    people.append(person)
    _save(people)
    return {**person, "name": guess_name(email), "named": False}


def set_name(email: str, name: str) -> dict | None:
    email = normalise(email)
    name = tidy_name(name)
    if not name:
        raise PersonError("Type the name you want to be called.")
    people = load()
    for person in people:
        if person["id"] == email:
            person["name"] = name
            _save([{k: v for k, v in p.items() if k != "named"} for p in people])
            return {**person, "named": True}
    return None


def remove(email: str) -> None:
    email = normalise(email)
    _save([p for p in load() if p["id"] != email])
