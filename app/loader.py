"""Carga los programas desde data/programas/*.json.

Los programas son archivos en disco, no base de datos: se editan con
cualquier editor, viven en git y se recargan solos al refrescar la pagina.
El slug sale del nombre del archivo, para que no se pueda duplicar.
"""
from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from .models import Programa

RAIZ = Path(__file__).resolve().parent.parent
DIR_PROGRAMAS = RAIZ / "data" / "programas"


class ProgramaInvalido(Exception):
    pass


def _leer(ruta: Path) -> Programa:
    try:
        crudo = json.loads(ruta.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ProgramaInvalido(f"{ruta.name}: JSON mal formado — {e}") from e
    crudo["slug"] = ruta.stem
    try:
        return Programa(**crudo)
    except ValidationError as e:
        raise ProgramaInvalido(f"{ruta.name}: {e}") from e


def listar() -> list[Programa]:
    """Todos los programas, ordenados por nombre. Archivos con _ delante se ocultan."""
    if not DIR_PROGRAMAS.is_dir():
        return []
    programas = [
        _leer(p)
        for p in sorted(DIR_PROGRAMAS.glob("*.json"))
        if not p.name.startswith("_")
    ]
    return sorted(programas, key=lambda p: p.nombre.lower())


def obtener(slug: str) -> Programa | None:
    ruta = DIR_PROGRAMAS / f"{slug}.json"
    # Evita que un slug con ../ salga del directorio de programas.
    if not ruta.is_file() or ruta.parent != DIR_PROGRAMAS:
        return None
    return _leer(ruta)
