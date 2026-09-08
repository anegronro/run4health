"""Personal catalogue of training programs — read only.

No tracker, no login: it reads the routines you keep in data/programs/.
Built to be opened on a phone.
"""
from __future__ import annotations

import base64
from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import gate, loader, people, progress
from .loader import InvalidProgram

HERE = Path(__file__).resolve().parent

app = FastAPI(title="Programs", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")
gate.install(app)
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


COOKIE = "who"
A_YEAR = 60 * 60 * 24 * 365


def whoami(request: Request) -> dict | None:
    """The person this browser last signed in as, if their profile still exists."""
    email = request.cookies.get(COOKIE)
    return people.get(email) if email else None


def _sign_in_first(request: Request) -> RedirectResponse:
    back = request.url.path or "/"
    return RedirectResponse(f"/who?back={quote(back, safe='')}", status_code=303)


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
    me = whoami(request)
    if me is None:
        return _sign_in_first(request)
    return templates.TemplateResponse(
        request, "index.html", {"programs": loader.list_all(), "me": me}
    )


@app.get("/program/{slug}", response_class=HTMLResponse)
def program(request: Request, slug: str, reset: int = 0):
    me = whoami(request)
    if me is None:
        return _sign_in_first(request)
    prog = loader.get(slug)
    if prog is None:
        raise HTTPException(404, "Program not found")
    done = progress.load(me["id"])
    return templates.TemplateResponse(
        request,
        "program.html",
        {
            "p": prog,
            "me": me,
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
    me = whoami(request)
    if me is None:
        return _sign_in_first(request)
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
            "me": me,
            "week": wk,
            "day": wk.days[day - 1],
            "n_day": day,
            "previous": day - 1 if day > 1 else None,
            "next": day + 1 if day < len(wk.days) else None,
            "is_done": progress.key(slug, week, day) in progress.load(me["id"]),
        },
    )


@app.post("/toggle")
def toggle(
    request: Request,
    slug: str = Form(...),
    week: int = Form(...),
    day: int = Form(...),
    done: int = Form(...),
    back: str = Form(...),
):
    """Tick or untick one session, then go back where you came from."""
    me = whoami(request)
    if me is None:
        return _sign_in_first(request)
    prog = loader.get(slug)
    if prog is None:
        raise HTTPException(404, "Program not found")
    wk = next((w for w in prog.weeks if w.number == week), None)
    if wk is None or not (1 <= day <= len(wk.days)):
        raise HTTPException(404, "Day not found")
    if wk.days[day - 1].rest_day:
        raise HTTPException(400, "Rest days are not sessions")
    progress.set_done(me["id"], slug, week, day, bool(done))
    return RedirectResponse(_safe_back(back, slug), status_code=303)


@app.post("/reset")
def reset(request: Request, slug: str = Form(...)):
    me = whoami(request)
    if me is None:
        return _sign_in_first(request)
    if loader.get(slug) is None:
        raise HTTPException(404, "Program not found")
    progress.clear_program(me["id"], slug)
    return RedirectResponse(f"/program/{slug}", status_code=303)


def _safe_back(back: str, slug: str) -> str:
    """Only ever redirect inside this app."""
    if back.startswith("/") and not back.startswith("//"):
        return back
    return f"/program/{slug}" if slug else "/"


MILES_PER_KM = 0.621371


def miles(km: float) -> float:
    return round(km * MILES_PER_KM, 1)


templates.env.globals["miles"] = miles


@app.get("/me", response_class=HTMLResponse)
def me_page(request: Request):
    """One runner's own numbers: what they have actually ticked off."""
    me = whoami(request)
    if me is None:
        return _sign_in_first(request)
    done = progress.load(me["id"])

    tracked, done_km, done_sessions, plan_km, plan_sessions = [], 0.0, 0, 0.0, 0
    for prog in loader.list_all():
        weeks, p_done_km, p_done, p_plan_km, p_plan = [], 0.0, 0, 0.0, 0
        for w in prog.weeks:
            w_km, w_done = 0.0, 0
            for i, d in enumerate(w.days, 1):
                if d.rest_day:
                    continue
                if progress.key(prog.slug, w.number, i) in done:
                    w_km += d.distance_km
                    w_done += 1
            weeks.append(
                {
                    "number": w.number,
                    "done_km": round(w_km, 2),
                    "plan_km": w.distance_km,
                    "done": w_done,
                    "sessions": w.sessions,
                }
            )
            p_done_km += w_km
            p_done += w_done
            p_plan_km += w.distance_km
            p_plan += w.sessions
        if p_done:
            tracked.append(
                {
                    "program": prog,
                    "weeks": weeks,
                    "done_km": round(p_done_km, 2),
                    "plan_km": round(p_plan_km, 2),
                    "done": p_done,
                    "sessions": p_plan,
                    # Scale to the biggest PLANNED week: the outline is the
                    # yardstick, so it has to fit.
                    "top_km": max((w["plan_km"] for w in weeks), default=0.0),
                }
            )
        done_km += p_done_km
        done_sessions += p_done
        plan_km += p_plan_km
        plan_sessions += p_plan

    return templates.TemplateResponse(
        request,
        "me.html",
        {
            "me": me,
            "tracked": tracked,
            "started": bool(tracked),
            "done_km": round(done_km, 2),
            "done_sessions": done_sessions,
            "plan_km": round(plan_km, 2),
            "plan_sessions": plan_sessions,
        },
    )


@app.get("/enter", response_class=HTMLResponse)
def enter(request: Request, back: str = "/", error: str = ""):
    if not gate.password():
        return RedirectResponse(_safe_back(back, ""), status_code=303)
    return templates.TemplateResponse(
        request, "enter.html", {"back": _safe_back(back, ""), "error": error}
    )


@app.post("/enter")
def enter_post(password: str = Form(""), back: str = Form("/")):
    target = _safe_back(back, "")
    if not gate.check(password, gate.password()):
        return RedirectResponse(
            f"/enter?back={quote(target, safe='')}&error=1", status_code=303
        )
    response = RedirectResponse(target, status_code=303)
    response.set_cookie(
        gate.COOKIE,
        gate.token(gate.password()),
        max_age=gate.A_YEAR,
        httponly=True,
        samesite="lax",
    )
    return response


@app.get("/who", response_class=HTMLResponse)
def who(request: Request, back: str = "/", error: str = ""):
    return templates.TemplateResponse(
        request,
        "who.html",
        {"back": _safe_back(back, ""), "error": error, "me": whoami(request)},
    )


@app.post("/who")
def sign_in(email: str = Form(""), back: str = Form("/")):
    target = _safe_back(back, "")
    try:
        person = people.sign_in(email)
    except people.PersonError as e:
        return RedirectResponse(
            f"/who?back={quote(target, safe='')}&error={quote(str(e), safe='')}",
            status_code=303,
        )
    response = RedirectResponse(target, status_code=303)
    response.set_cookie(
        COOKIE, person["id"], max_age=A_YEAR, httponly=True, samesite="lax"
    )
    return response


@app.post("/who/out")
def sign_out():
    """Forget this browser. Nothing is deleted — the progress stays."""
    response = RedirectResponse("/who", status_code=303)
    response.delete_cookie(COOKIE)
    return response


@app.get("/health")
def health():
    return {"ok": True, "programs": len(loader.list_all())}
