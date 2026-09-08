# run4health

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

A `reps` field that is nothing but a distance — `5 km`, `400 m`, `8 mi` — is
counted toward the week's mileage, so a program can be written in whichever
unit suits it. Everything is summed in kilometres and shown in miles.

A week lists all seven days, rest included, so the plan reads as a calendar.
The `slug` (the URL) comes from the file name.

## Included programs

| Program | Length | Days | For |
|---|---|---|---|
| Zero to 5K | 8 weeks | 3/week | No running background |
| 10K in 10 weeks | 10 weeks | 4/week | Already running 5 km |
| 8 miles in 8 weeks | 8 weeks | 4/week | Already running 10K |
| Half Marathon — 21K | 12 weeks | 4/week | Already running 10 km |

These are generic, well-built plans — they are not tailored to any individual.

Program pages chart the planned kilometres per week, read straight off the
exercises, so the down weeks are visible. Warm-ups and cool-downs are written
in minutes rather than kilometres, so they don't appear in that total.

## Completed sessions

Every training day carries a checkbox, and each day page has a "Mark as done"
button. Ticks live server-side, so a session ticked on the phone shows as
ticked on the Mac.

## Training log

The **Training log** tab (`/me`) shows miles run, sessions completed,
and a bar per week of each program you have started — solid for what you
ticked off, outline for what the week plans.

Distance is read off the exercises, so only what the plan writes as a
distance counts (`5 km`, `400 m`). A tempo run prescribed as "20 min"
contributes nothing rather than an invented number, and warm-up strides
don't count toward the session. Programs are written in kilometres; the log
shows miles with the kilometres beside them.

## Profiles

Everyone types their email once and the app remembers that browser for a
The sign-in screen asks for a name as well as an email, because no address
knows that angel is written Ángel. Typed all in lower case, the name gets its
capitals; typed with any of your own, it is left exactly as written. Neither
field is written to disk until both are valid, so a rejected form leaves
nothing behind.

The chip in the header opens an account screen that offers rather than
demands: back to where you were, change your name, or sign out. Signing out only forgets the
browser — the ticks stay, and it is also how you hand the app to someone
else, since the email screen comes back. A profile is
created the first time an address is used — there is nothing to set up.

**The email is not a password.** It is a label that keeps each person's
progress apart, not proof of who they are: anyone who gets in can type anyone
else's address and see their ticks. What keeps strangers out is the shared
password below.

`data/people.json` holds the profiles and `data/progress.json` the ticks, one
list per person. Both are kept out of git and out of the deploy sync, so
redeploying never clears them; `FITNESS_PEOPLE` and `FITNESS_PROGRESS`
override their paths.

## No subresources, no JavaScript

The stylesheet is inlined into every page and the photos are sent as `data:`
URIs; ticking a box is a plain form POST. This is deliberate. Content blockers
routinely let the HTML document through while blocking every subresource and
`fetch()` call from a host they don't recognise, which left the app rendering
as naked HTML with dead checkboxes. With nothing loaded separately and no
`fetch()`, there is nothing left for a blocker to break — and the app works
with JavaScript switched off.

The inlined photos come from `app/static/img/inline/`, deliberately smaller
than the originals, since an inlined image is re-sent with every page view and
never cached on its own.

## Getting in

`FITNESS_PASSWORD` puts one shared password in front of the whole app —
required now that it is published to the internet, since the email profiles
are not authentication. It lives in `/etc/fitness.env` on the server (mode
600, read by the unit's `EnvironmentFile`), never in this repo. Unset, the
gate is off, which is fine for purely local runs.

It is asked for on a page of our own, not through HTTP Basic Auth, whose
browser dialog cannot be styled. A browser that has answered holds a cookie
derived from the password with HMAC, so it cannot be forged and changing the
password signs everyone out.

To change it: edit `/etc/fitness.env` and `systemctl restart fitness`.

## Always on

`scripts/deploy_vps.sh` copies the app to the VPS and runs it under systemd as
`fitness.service`. Two tailnet addresses reach it, and neither is public:

- <https://your-server.example.ts.net:8443> — **public**, for
  people outside the tailnet, behind the shared password. Port 8443 keeps it
  clear of the Gatsby Funnel already on 443 of that name.
- <https://your-app.example.ts.net> — tailnet only, from a separate node
  (`tailscaled-run4health.service`). Tailscale never published a public DNS
  record for this second node, which is why the public URL uses the other
  hostname.
- <http://203.0.113.10:8770> — tailnet only, the plain address
