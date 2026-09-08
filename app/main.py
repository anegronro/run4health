"""Personal catalogue of training programs — read only.

No tracker, no login: it reads the routines you keep in data/programs/.
Built to be opened on a phone.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from . import loader, progress
from .loader import InvalidProgram


class Mark(BaseModel):
    slug: str
    week: int
    day: int
    done: bool

HERE = Path(__file__).resolve().parent

app = FastAPI(title="Programs", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")
templates = Jinja2Templates(directory=str(HERE / "templates"))


@app.exception_handler(InvalidProgram)
async def invalid_program(request: Request, exc: InvalidProgram):
    """A broken JSON file shows a readable error, not a stack trace."""
    return templates.TemplateResponse(
        request, "error.html", {"detail": str(exc)}, status_code=500
    )


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        request, "index.html", {"programs": loader.list_all()}
    )


@app.get("/program/{slug}", response_class=HTMLResponse)
def program(request: Request, slug: str):
    prog = loader.get(slug)
    if prog is None:
        raise HTTPException(404, "Program not found")
    done = progress.load()
    return templates.TemplateResponse(
        request,
        "program.html",
        {
            "p": prog,
            "done": done,
            "key": progress.key,
            "completed": sum(
                1
                for w in prog.weeks
                for i, d in enumerate(w.days, 1)
                if not d.rest_day and progress.key(prog.slug, w.number, i) in done
            ),
            "sessions": sum(w.sessions for w in prog.weeks),
        },
    )


@app.get("/program/{slug}/w{week}/d{day}", response_class=HTMLResponse)
def day(request: Request, slug: str, week: int, day: int):
    prog = loader.get(slug)
    if prog is None:
        raise HTTPException(404, "Program not found")
    wk = next((w for w in prog.weeks if w.number == week), None)
    if wk is None or not (1 <= day <= len(wk.days)):
        raise HTTPException(404, "Day not found")
    return templates.TemplateResponse(
        request,
        "day.html",
        {
            "p": prog,
            "week": wk,
            "day": wk.days[day - 1],
            "n_day": day,
            "previous": day - 1 if day > 1 else None,
            "next": day + 1 if day < len(wk.days) else None,
            "is_done": progress.key(slug, week, day) in progress.load(),
        },
    )


@app.post("/api/progress")
def mark(m: Mark):
    """Tick or untick one session. State is shared by every device."""
    prog = loader.get(m.slug)
    if prog is None:
        raise HTTPException(404, "Program not found")
    wk = next((w for w in prog.weeks if w.number == m.week), None)
    if wk is None or not (1 <= m.day <= len(wk.days)):
        raise HTTPException(404, "Day not found")
    if wk.days[m.day - 1].rest_day:
        raise HTTPException(400, "Rest days are not sessions")
    done = progress.set_done(m.slug, m.week, m.day, m.done)
    completed = sum(
        1
        for w in prog.weeks
        for i, d in enumerate(w.days, 1)
        if not d.rest_day and progress.key(m.slug, w.number, i) in done
    )
    return {"ok": True, "done": m.done, "completed": completed}


@app.post("/api/progress/{slug}/reset")
def reset(slug: str):
    if loader.get(slug) is None:
        raise HTTPException(404, "Program not found")
    progress.clear_program(slug)
    return {"ok": True, "completed": 0}


@app.get("/health")
def health():
    return {"ok": True, "programs": len(loader.list_all())}
