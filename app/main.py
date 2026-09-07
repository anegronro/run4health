"""Catalogo personal de programas de entrenamiento — solo lectura.

Sin tracker, sin login: es un lector de las rutinas que guardes en
data/programas/. Pensado para abrirse en el telefono.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import loader
from .loader import ProgramaInvalido

AQUI = Path(__file__).resolve().parent

app = FastAPI(title="Programas", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=AQUI / "static"), name="static")
plantillas = Jinja2Templates(directory=str(AQUI / "templates"))


@app.exception_handler(ProgramaInvalido)
async def programa_invalido(request: Request, exc: ProgramaInvalido):
    """Un JSON roto se muestra como error legible, no como stacktrace."""
    return plantillas.TemplateResponse(
        request, "error.html", {"detalle": str(exc)}, status_code=500
    )


@app.get("/", response_class=HTMLResponse)
def indice(request: Request):
    return plantillas.TemplateResponse(
        request, "indice.html", {"programas": loader.listar()}
    )


@app.get("/programa/{slug}", response_class=HTMLResponse)
def programa(request: Request, slug: str):
    prog = loader.obtener(slug)
    if prog is None:
        raise HTTPException(404, "Programa no encontrado")
    return plantillas.TemplateResponse(request, "programa.html", {"p": prog})


@app.get("/programa/{slug}/s{semana}/d{dia}", response_class=HTMLResponse)
def dia(request: Request, slug: str, semana: int, dia: int):
    prog = loader.obtener(slug)
    if prog is None:
        raise HTTPException(404, "Programa no encontrado")
    sem = next((s for s in prog.semanas if s.numero == semana), None)
    if sem is None or not (1 <= dia <= len(sem.dias)):
        raise HTTPException(404, "Dia no encontrado")
    return plantillas.TemplateResponse(
        request,
        "dia.html",
        {
            "p": prog,
            "semana": sem,
            "dia": sem.dias[dia - 1],
            "n_dia": dia,
            "anterior": dia - 1 if dia > 1 else None,
            "siguiente": dia + 1 if dia < len(sem.dias) else None,
        },
    )


@app.get("/salud")
def salud():
    return {"ok": True, "programas": len(loader.listar())}
