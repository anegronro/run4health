"""Loads programs from data/programs/*.json.

Programs are files on disk, not a database: edit them in any editor, keep
them in git, and they reload on every page view. The slug comes from the
file name so two programs can never collide.
"""
from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from .models import Program

ROOT = Path(__file__).resolve().parent.parent
PROGRAMS_DIR = ROOT / "data" / "programs"


class InvalidProgram(Exception):
    pass


def _read(path: Path) -> Program:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise InvalidProgram(f"{path.name}: malformed JSON — {e}") from e
    raw["slug"] = path.stem
    try:
        return Program(**raw)
    except ValidationError as e:
        raise InvalidProgram(f"{path.name}: {e}") from e


def list_all() -> list[Program]:
    """Every program in progression order. Files starting with _ stay hidden."""
    if not PROGRAMS_DIR.is_dir():
        return []
    programs = [
        _read(p)
        for p in sorted(PROGRAMS_DIR.glob("*.json"))
        if not p.name.startswith("_")
    ]
    return sorted(programs, key=lambda p: (p.order, p.name.lower()))


def get(slug: str) -> Program | None:
    path = PROGRAMS_DIR / f"{slug}.json"
    # Keeps a slug containing ../ from escaping the programs directory.
    if not path.is_file() or path.parent != PROGRAMS_DIR:
        return None
    return _read(path)
