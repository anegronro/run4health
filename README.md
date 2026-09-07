# fitness-app — catálogo de programas

Lector personal de programas de entrenamiento. **Solo lectura**: muestra las
rutinas y sus guías, no registra entrenamientos ni progreso.

El contenido es tuyo: cada programa es un archivo JSON en `data/programas/`.

## Correr

```bash
./scripts/run.sh                 # http://127.0.0.1:8770
./scripts/run.sh 100.64.0.1   # accesible desde el teléfono por Tailscale
```

## Crear un programa

```bash
uv run python scripts/nuevo_programa.py
```

Genera el esqueleto (semanas y días vacíos) en `data/programas/<slug>.json`;
los ejercicios se escriben después en ese archivo. También puedes copiar
`data/programas/_ejemplo.json` con otro nombre — los archivos que empiezan
con `_` no salen en el listado.

La app relee los archivos en cada carga, así que basta con refrescar.
Si un JSON está mal, la página lo dice con el nombre del archivo y el error.

## Estructura de un programa

```
Programa → semanas → días → bloques → ejercicios
```

| Campo | Dónde | Notas |
|---|---|---|
| `nombre`, `descripcion`, `nivel`, `equipo`, `color` | programa | `color` es el acento de la tarjeta |
| `guia` | programa | texto largo; separa párrafos con línea en blanco |
| `numero`, `titulo`, `objetivo` | semana | |
| `titulo`, `enfoque`, `duracion`, `notas` | día | `"descanso_total": true` lo marca como día libre |
| `titulo`, `notas` | bloque | calentamiento, superserie A, accesorios… |
| `nombre`, `series`, `reps`, `descanso`, `tempo`, `rpe`, `notas`, `video` | ejercicio | todo texto libre; `video` es un enlace externo |

El `slug` (la URL) sale del nombre del archivo.
