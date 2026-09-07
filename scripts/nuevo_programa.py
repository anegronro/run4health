#!/usr/bin/env python3
"""Crea un programa nuevo en data/programas/ a partir de unas preguntas.

Genera el esqueleto (semanas y dias vacios); los ejercicios se escriben
despues en el JSON, que es mas comodo que teclearlos aqui uno por uno.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

DIR = Path(__file__).resolve().parent.parent / "data" / "programas"


def slugificar(texto: str) -> str:
    t = texto.lower()
    for a, b in (("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"), ("ñ", "n")):
        t = t.replace(a, b)
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return t or "programa"


def preguntar(texto: str, defecto: str = "") -> str:
    sufijo = f" [{defecto}]" if defecto else ""
    return input(f"{texto}{sufijo}: ").strip() or defecto


def main() -> int:
    nombre = preguntar("Nombre del programa")
    if not nombre:
        print("Necesito un nombre.")
        return 1
    slug = slugificar(preguntar("Slug (archivo)", slugificar(nombre)))
    destino = DIR / f"{slug}.json"
    if destino.exists():
        print(f"Ya existe {destino.name}. Elige otro slug.")
        return 1

    descripcion = preguntar("Descripción", "")
    nivel = preguntar("Nivel", "Intermedio")
    try:
        semanas = int(preguntar("¿Cuántas semanas?", "4"))
        dias = int(preguntar("¿Días por semana?", "3"))
    except ValueError:
        print("Semanas y días tienen que ser números.")
        return 1

    programa = {
        "nombre": nombre,
        "descripcion": descripcion,
        "nivel": nivel,
        "dias_por_semana": dias,
        "equipo": [],
        "guia": "",
        "semanas": [
            {
                "numero": n,
                "titulo": "",
                "objetivo": "",
                "dias": [
                    {
                        "titulo": f"Día {d}",
                        "enfoque": "",
                        "bloques": [{"titulo": "Principal", "ejercicios": []}],
                    }
                    for d in range(1, dias + 1)
                ],
            }
            for n in range(1, semanas + 1)
        ],
    }
    DIR.mkdir(parents=True, exist_ok=True)
    destino.write_text(
        json.dumps(programa, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"\nCreado: {destino}")
    print("Ábrelo y llena los ejercicios de cada bloque.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
