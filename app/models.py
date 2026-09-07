"""Data model for a training program.

Content lives in data/programs/*.json and is validated against these models
on load, so a malformed file fails with a clear message instead of breaking
the page halfway through rendering.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class Exercise(BaseModel):
    name: str
    sets: str | None = None            # "4" or "3-4" — free text on purpose
    reps: str | None = None            # "8-10", "AMRAP", "30 s", "5 km"
    rest: str | None = None            # "90 s"
    tempo: str | None = None           # "3-1-1"
    rpe: str | None = None             # "7-8"
    notes: str | None = None
    video: str | None = None           # external link, never embedded


class Block(BaseModel):
    """Groups exercises within a day: warm-up, superset A, cool-down…"""
    title: str
    notes: str | None = None
    exercises: list[Exercise] = Field(default_factory=list)


class Day(BaseModel):
    title: str                         # "Monday — Push"
    focus: str | None = None
    duration: str | None = None        # "60 min"
    rest_day: bool = False             # a full rest day carries no blocks
    notes: str | None = None
    blocks: list[Block] = Field(default_factory=list)


class Week(BaseModel):
    number: int
    title: str | None = None
    goal: str | None = None
    days: list[Day] = Field(default_factory=list)


class Program(BaseModel):
    slug: str                          # overwritten with the file name
    name: str
    description: str | None = None
    level: str | None = None           # "Beginner", "Intermediate", "Advanced"
    days_per_week: int | None = None
    equipment: list[str] = Field(default_factory=list)
    color: str = "#5b8cff"             # card accent
    guide: str | None = None           # program-wide guide (blank-line paragraphs)
    weeks: list[Week] = Field(default_factory=list)

    @property
    def total_weeks(self) -> int:
        return len(self.weeks)
