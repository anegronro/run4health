"""Data model for a training program.

Content lives in data/programs/*.json and is validated against these models
on load, so a malformed file fails with a clear message instead of breaking
the page halfway through rendering.
"""
from __future__ import annotations

import re

from pydantic import BaseModel, Field

# Matches a distance written as the whole rep field: "5 km", "21.1 km".
_KM = re.compile(r"^\s*([\d.,]+)\s*km\s*$", re.IGNORECASE)


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

    @property
    def distance_km(self) -> float:
        """Kilometres planned this week, read off the exercises themselves."""
        total = 0.0
        for day in self.days:
            for block in day.blocks:
                for e in block.exercises:
                    m = _KM.match(e.reps or "")
                    if m:
                        total += float(m.group(1).replace(",", ".")) * int(e.sets or 1)
        return round(total, 1)

    @property
    def sessions(self) -> int:
        return sum(1 for d in self.days if not d.rest_day)


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

    order: int = 100                   # listing order; lower comes first
    art: str = "route"                 # cover artwork: route | track | weights
    image: str | None = None           # optional own photo: /static/img/<file>

    @property
    def total_weeks(self) -> int:
        return len(self.weeks)

    @property
    def peak_km(self) -> float:
        return max((w.distance_km for w in self.weeks), default=0.0)

    @property
    def shows_volume(self) -> bool:
        """Only chart mileage when most weeks actually carry a distance."""
        with_km = sum(1 for w in self.weeks if w.distance_km)
        return with_km >= 3 and with_km >= len(self.weeks) / 2
