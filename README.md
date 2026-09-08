# fitness-app — program catalogue

A personal reader for training programs. It shows the routines and their
guides, and lets you tick off each session as you complete it. It does not
record weights, times or any other workout detail.

The content is yours: every program is a JSON file in `data/programs/`.

## Run it

```bash
./scripts/run.sh                 # http://127.0.0.1:8770
./scripts/run.sh 100.64.0.1   # reachable from the phone over Tailscale
```

## Create a program

```bash
uv run python scripts/new_program.py
```

It writes the skeleton — every week laid out Monday to Sunday, with the days
you don't train marked as rest — into `data/programs/<slug>.json`. Fill in the
exercises there. You can also copy `data/programs/_example.json` under another
name; files starting with `_` stay out of the listing.

The app re-reads the files on every request, so a refresh is enough. If a JSON
file is broken, the page says which file and what the error is.

## Program structure

```
Program → weeks → days → blocks → exercises
```

| Field | Level | Notes |
|---|---|---|
| `name`, `description`, `level`, `equipment`, `color` | program | `color` is the card accent |
| `order` | program | listing order, lowest first (default 100); ties fall back to the name |
| `art` | program | generated cover: `route`, `track` or `weights` |
| `image` | program | your own photo instead of the drawing, e.g. `/static/img/run.jpg` — see `app/static/img/README.md` |
| `guide` | program | long text; separate paragraphs with a blank line |
| `number`, `title`, `goal` | week | |
| `title`, `focus`, `duration`, `notes` | day | `"rest_day": true` marks a rest day |
| `title`, `notes` | block | warm-up, superset A, accessories… |
| `name`, `sets`, `reps`, `rest`, `tempo`, `rpe`, `notes`, `video` | exercise | all free text; `video` is an external link |

A week lists all seven days, rest included, so the plan reads as a calendar.
The `slug` (the URL) comes from the file name.

## Included programs

| Program | Length | Days | For |
|---|---|---|---|
| Zero to 5K | 8 weeks | 3/week | No running background |
| 10K in 10 weeks | 10 weeks | 4/week | Already running 5 km |
| Half Marathon — 21K | 12 weeks | 4/week | Already running 10 km |

These are generic, well-built plans — they are not tailored to any individual.

Program pages chart the planned kilometres per week, read straight off the
exercises, so the down weeks are visible. Warm-ups and cool-downs are written
in minutes rather than kilometres, so they don't appear in that total.

## Completed sessions

Every training day carries a checkbox, and each day page has a "Mark as done"
button. Ticks live server-side in `data/progress.json`, so a session ticked on
the phone shows as ticked on the Mac. That file is kept out of git and out of
the deploy sync, so redeploying never clears it. `FITNESS_PROGRESS` overrides
its path. There is no login: the tailnet is the boundary.

## Always on

`scripts/deploy_vps.sh` copies the app to the VPS and runs it under systemd as
`fitness.service`. Two tailnet addresses reach it, and neither is public:

- <https://your-app.example.ts.net> — a separate Tailscale node
  (`tailscaled-run4health.service`) fronting the app over HTTPS, no port
- <http://203.0.113.10:8770> — the plain address, kept working for
  bookmarks and home-screen shortcuts
