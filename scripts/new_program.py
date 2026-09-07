#!/usr/bin/env python3
"""Creates a new program in data/programs/ from a few questions.

It writes the skeleton (weeks and empty days); the exercises go into the
JSON afterwards, which is far less painful than typing them in here.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

DIR = Path(__file__).resolve().parent.parent / "data" / "programs"
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def slugify(text: str) -> str:
    t = text.lower()
    for a, b in (("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"), ("ñ", "n")):
        t = t.replace(a, b)
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return t or "program"


def ask(text: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    return input(f"{text}{suffix}: ").strip() or default


def main() -> int:
    name = ask("Program name")
    if not name:
        print("I need a name.")
        return 1
    slug = slugify(ask("Slug (file name)", slugify(name)))
    target = DIR / f"{slug}.json"
    if target.exists():
        print(f"{target.name} already exists. Pick another slug.")
        return 1

    description = ask("Description", "")
    level = ask("Level", "Intermediate")
    try:
        weeks = int(ask("How many weeks?", "4"))
    except ValueError:
        print("Weeks has to be a number.")
        return 1
    training = ask("Training days (comma-separated)", "Monday,Wednesday,Friday")
    chosen = [d.strip().capitalize() for d in training.split(",") if d.strip()]
    unknown = [d for d in chosen if d not in DAYS]
    if unknown:
        print(f"I don't know these days: {', '.join(unknown)}. Use English weekday names.")
        return 1

    def day(name_of_day: str) -> dict:
        if name_of_day in chosen:
            return {
                "title": f"{name_of_day} — ",
                "focus": "",
                "blocks": [{"title": "Main", "exercises": []}],
            }
        return {"title": f"{name_of_day} — Rest", "rest_day": True}

    program = {
        "name": name,
        "description": description,
        "level": level,
        "days_per_week": len(chosen),
        "equipment": [],
        "guide": "",
        "weeks": [
            {
                "number": n,
                "title": "",
                "goal": "",
                "days": [day(d) for d in DAYS],
            }
            for n in range(1, weeks + 1)
        ],
    }
    DIR.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(program, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"\nCreated: {target}")
    print("Open it and fill in the exercises for each block.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
