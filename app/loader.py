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
FALLBACK_LANG = "en"
IMG_DIR = Path(__file__).resolve().parent / "static" / "img"
IMG_SUFFIXES = (".jpg", ".jpeg", ".png", ".webp", ".avif")


def _photo_for(slug: str) -> str | None:
    """A photo named after the program is picked up with no config.

    Drop app/static/img/<slug>.jpg and that program uses it as its cover;
    an explicit "image" in the JSON still wins.
    """
    for suffix in IMG_SUFFIXES:
        if (IMG_DIR / f"{slug}{suffix}").is_file():
            return f"/static/img/{slug}{suffix}"
    return None


class InvalidProgram(Exception):
    pass


def _read(path: Path) -> Program:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise InvalidProgram(f"{path.name}: malformed JSON — {e}") from e
    raw["slug"] = path.stem
    try:
        program = Program(**raw)
    except ValidationError as e:
        raise InvalidProgram(f"{path.name}: {e}") from e
    if not program.image:
        program.image = _photo_for(program.slug)
    return program


def _dir_for(lang: str) -> Path:
    """Where this language's programs live, or English if it has none yet."""
    wanted = PROGRAMS_DIR / lang
    if wanted.is_dir() and any(
        p for p in wanted.glob("*.json") if not p.name.startswith("_")
    ):
        return wanted
    return PROGRAMS_DIR / FALLBACK_LANG


def list_all(lang: str = FALLBACK_LANG) -> list[Program]:
    """Every program in progression order. Files starting with _ stay hidden."""
    folder = _dir_for(lang)
    if not folder.is_dir():
        return []
    programs = [
        _read(p)
        for p in sorted(folder.glob("*.json"))
        if not p.name.startswith("_")
    ]
    return sorted(programs, key=lambda p: (p.order, p.name.lower()))


def get(slug: str, lang: str = FALLBACK_LANG) -> Program | None:
    """One program. A slug is the same in every language, so progress ticked
    off in Spanish is the same progress in English."""
    for folder in (_dir_for(lang), PROGRAMS_DIR / FALLBACK_LANG):
        path = folder / f"{slug}.json"
        # Keeps a slug containing ../ from escaping the programs directory.
        if path.is_file() and path.parent == folder:
            return _read(path)
    return None
