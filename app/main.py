"""Personal catalogue of training programs — read only.

No tracker, no login: it reads the routines you keep in data/programs/.
Built to be opened on a phone.
"""
from __future__ import annotations

import base64
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import loader, progress
from .loader import InvalidProgram

HERE = Path(__file__).resolve().parent

app = FastAPI(title="Programs", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")
templates = Jinja2Templates(directory=str(HERE / "templates"))

_assets: dict[str, tuple[float, str]] = {}


def asset(name: str) -> str:
    """The stylesheet and script are inlined into the page.

    Content blockers happily block every subresource of a host they don't
    recognise while letting the document through, which left the app
    rendering as naked HTML. Inlined, there is nothing left to block.
    Re-read whenever the file changes, so editing still hot-reloads.
    """
    path = HERE / "static" / name
    stamp = path.stat().st_mtime
    cached = _assets.get(name)
    if cached is None or cached[0] != stamp:
        _assets[name] = (stamp, path.read_text(encoding="utf-8"))
    return _assets[name][1]


_data_uris: dict[str, tuple[float, str]] = {}


def photo(name: str) -> str:
    """A photo as a data: URI, for the same reason the CSS is inlined.

    Uses the smaller copies under static/img/inline/, since an inlined image
    is re-sent with every page view and never cached on its own.
    """
    path = HERE / "static" / "img" / "inline" / name
    if not path.is_file():
        return ""
    stamp = path.stat().st_mtime
    cached = _data_uris.get(name)
    if cached is None or cached[0] != stamp:
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        _data_uris[name] = (stamp, f"data:image/jpeg;base64,{encoded}")
    return _data_uris[name][1]


templates.env.globals["asset"] = asset
templates.env.globals["photo"] = photo


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
def program(request: Request, slug: str, reset: int = 0):
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
            "confirm_reset": bool(reset),
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


@app.post("/toggle")
def toggle(
    slug: str = Form(...),
    week: int = Form(...),
    day: int = Form(...),
    done: int = Form(...),
    back: str = Form(...),
):
    """Tick or untick one session, then go back where you came from."""
    prog = loader.get(slug)
    if prog is None:
        raise HTTPException(404, "Program not found")
    wk = next((w for w in prog.weeks if w.number == week), None)
    if wk is None or not (1 <= day <= len(wk.days)):
        raise HTTPException(404, "Day not found")
    if wk.days[day - 1].rest_day:
        raise HTTPException(400, "Rest days are not sessions")
    progress.set_done(slug, week, day, bool(done))
    return RedirectResponse(_safe_back(back, slug), status_code=303)


@app.post("/reset")
def reset(slug: str = Form(...)):
    if loader.get(slug) is None:
        raise HTTPException(404, "Program not found")
    progress.clear_program(slug)
    return RedirectResponse(f"/program/{slug}", status_code=303)


def _safe_back(back: str, slug: str) -> str:
    """Only ever redirect inside this app."""
    if back.startswith("/") and not back.startswith("//"):
        return back
    return f"/program/{slug}"


@app.get("/health")
def health():
    return {"ok": True, "programs": len(loader.list_all())}
