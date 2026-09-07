"""Modelo de datos de un programa de entrenamiento.

El contenido vive en data/programas/*.json y se valida contra estos modelos
al cargarlo, para que un JSON mal escrito falle con un mensaje claro en vez
de romper la pagina a mitad del render.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class Ejercicio(BaseModel):
    nombre: str
    series: str | None = None          # "4" o "3-4" — texto libre a proposito
    reps: str | None = None            # "8-10", "AMRAP", "30 s"
    descanso: str | None = None        # "90 s"
    tempo: str | None = None           # "3-1-1"
    rpe: str | None = None             # "7-8"
    notas: str | None = None
    video: str | None = None           # enlace externo, no se incrusta


class Bloque(BaseModel):
    """Agrupa ejercicios dentro de un dia: calentamiento, superserie A, etc."""
    titulo: str
    notas: str | None = None
    ejercicios: list[Ejercicio] = Field(default_factory=list)


class Dia(BaseModel):
    titulo: str                        # "Dia 1 — Empuje"
    enfoque: str | None = None
    duracion: str | None = None        # "60 min"
    descanso_total: bool = False       # dia de descanso: sin bloques
    notas: str | None = None
    bloques: list[Bloque] = Field(default_factory=list)


class Semana(BaseModel):
    numero: int
    titulo: str | None = None
    objetivo: str | None = None
    dias: list[Dia] = Field(default_factory=list)


class Programa(BaseModel):
    slug: str                          # se sobreescribe con el nombre del archivo
    nombre: str
    descripcion: str | None = None
    nivel: str | None = None           # "Principiante", "Intermedio", "Avanzado"
    dias_por_semana: int | None = None
    equipo: list[str] = Field(default_factory=list)
    color: str = "#5b8cff"             # acento de la tarjeta
    guia: str | None = None            # guia general del programa (markdown ligero)
    semanas: list[Semana] = Field(default_factory=list)

    @property
    def total_semanas(self) -> int:
        return len(self.semanas)
