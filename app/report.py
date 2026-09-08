"""Somebody's own record, as a PDF they can keep.

Written to be read by a person: what they did, when, and how far — not a
dump of table rows. The machine-readable JSON is still offered beside it for
anyone moving their data elsewhere.
"""
from __future__ import annotations

import io
import re
from datetime import datetime, timezone

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from . import loader

INK = colors.HexColor("#15181C")
MUTED = colors.HexColor("#5D646D")
RULE = colors.HexColor("#DCD9D4")
ACCENT = colors.HexColor("#1E6F4B")
MILES_PER_KM = 0.621371

ITEM = re.compile(r"^(?P<slug>.+)/w(?P<week>\d+)/d(?P<day>\d+)$")


def _styles() -> dict:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("title", parent=base["Title"], fontName="Helvetica-Bold",
                                fontSize=22, leading=26, textColor=INK,
                                alignment=TA_LEFT, spaceAfter=2),
        "sub": ParagraphStyle("sub", parent=base["Normal"], fontName="Helvetica",
                              fontSize=10.5, leading=15, textColor=MUTED),
        "h2": ParagraphStyle("h2", parent=base["Normal"], fontName="Helvetica-Bold",
                             fontSize=12, leading=15, textColor=INK,
                             spaceBefore=16, spaceAfter=6),
        "body": ParagraphStyle("body", parent=base["Normal"], fontName="Helvetica",
                               fontSize=10, leading=14.5, textColor=INK),
        "small": ParagraphStyle("small", parent=base["Normal"], fontName="Helvetica",
                                fontSize=8.5, leading=12.5, textColor=MUTED),
        # Table cells must be Paragraphs, not bare strings, or long text
        # overflows the cell instead of wrapping.
        "cell": ParagraphStyle("cell", parent=base["Normal"], fontName="Helvetica",
                               fontSize=9.5, leading=13, textColor=INK),
        "cellb": ParagraphStyle("cellb", parent=base["Normal"], fontName="Helvetica-Bold",
                                fontSize=9.5, leading=13, textColor=INK),
    }


def _grid(data, widths, align_right=(), header=True) -> Table:
    t = Table(data, colWidths=widths, hAlign="LEFT", repeatRows=1 if header else 0)
    style = [
        ("LINEBELOW", (0, 0), (-1, 0), 0.9, INK) if header
        else ("LINEABOVE", (0, 0), (-1, 0), 0.9, INK),
        ("LINEBELOW", (0, 0 if header else 0), (-1, -2), 0.4, RULE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]
    for col in align_right:
        style.append(("ALIGN", (col, 0), (col, -1), "RIGHT"))
    t.setStyle(TableStyle(style))
    return t


def _describe(item: str) -> tuple[str, str, float]:
    """Turn "10k/w1/d3" into a program name, a session title and its miles."""
    m = ITEM.match(item)
    if not m:
        return item, "", 0.0
    prog = loader.get(m["slug"])
    if prog is None:
        return m["slug"], f"Week {m['week']}, day {m['day']}", 0.0
    week = next((w for w in prog.weeks if w.number == int(m["week"])), None)
    if week is None or not (1 <= int(m["day"]) <= len(week.days)):
        return prog.name, f"Week {m['week']}, day {m['day']}", 0.0
    day = week.days[int(m["day"]) - 1]
    return prog.name, f"Week {m['week']} · {day.title}", day.distance_km * MILES_PER_KM


def build(data: dict) -> bytes:
    s = _styles()
    account = data["account"]
    ticks = data["completed_sessions"]

    rows, miles_by_program, total_miles = [], {}, 0.0
    for tick in ticks:
        program, session, miles = _describe(tick["item"])
        rows.append((tick["done_at"][:10], program, session, miles))
        miles_by_program[program] = miles_by_program.get(program, 0.0) + miles
        total_miles += miles
    rows.sort(key=lambda r: r[0])

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=LETTER,
        leftMargin=20 * mm, rightMargin=20 * mm,
        topMargin=18 * mm, bottomMargin=18 * mm,
        title=f"run4health — {account['name']}",
        author="run4health",
    )
    story = [
        Paragraph("Your run4health record", s["title"]),
        Paragraph(
            f"{account['name']} · {account['email']}<br/>"
            f"Account created {account['created_at'][:10]} · "
            f"Downloaded {datetime.now(timezone.utc):%d %B %Y}",
            s["sub"],
        ),
        Spacer(1, 6),
    ]

    summary = [
        [Paragraph("Sessions completed", s["cell"]), Paragraph(str(len(ticks)), s["cellb"])],
        [Paragraph("Miles run", s["cell"]), Paragraph(f"{total_miles:.1f}", s["cellb"])],
    ]
    for program, miles in sorted(miles_by_program.items()):
        summary.append([Paragraph(program, s["cell"]), Paragraph(f"{miles:.1f} mi", s["cell"])])

    story += [
        Paragraph("Summary", s["h2"]),
        _grid(summary, [110 * mm, 40 * mm], align_right=(1,), header=False),
    ]

    story.append(Paragraph("Every session you ticked off", s["h2"]))
    if rows:
        head = [Paragraph(h, s["cellb"]) for h in ("Date", "Program", "Session", "Miles")]
        body = [
            [Paragraph(date, s["cell"]), Paragraph(program, s["cell"]),
             Paragraph(session, s["cell"]),
             Paragraph(f"{miles:.1f}" if miles else "—", s["cell"])]
            for date, program, session, miles in rows
        ]
        story.append(_grid([head] + body,
                           [22 * mm, 38 * mm, 74 * mm, 16 * mm], align_right=(3,)))
    else:
        story.append(Paragraph("Nothing ticked off yet.", s["body"]))

    story.append(KeepTogether([
        Spacer(1, 14),
        Paragraph(
            "Sessions the plan writes in minutes rather than a distance — tempo "
            "runs, the walk-run weeks — count as sessions but add no miles.<br/><br/>"
            "This file does not contain your password. It is stored hashed and "
            "cannot be read back by anyone, including whoever runs the server.<br/><br/>"
            "If you delete your account, this data is removed from the database "
            "immediately and expires from the nightly backups within fourteen days.",
            s["small"]),
    ]))

    doc.build(story)
    return buf.getvalue()
