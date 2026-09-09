"""Accounts, passwords and sessions.

Passwords are hashed with scrypt from the standard library — deliberately
slow and salted per person, so the stored value is useless to anyone who
gets hold of the database. The session cookie is a random token; only its
hash is stored, so the same leak cannot be replayed as a login either.
"""
from __future__ import annotations

import hashlib
import hmac
import re
import secrets

from . import db

MIN_PASSWORD = 8
MAX_PEOPLE = 50
COLORS = ["#4ade80", "#5b8cff", "#f59e0b", "#a78bfa", "#f472b6", "#22d3ee"]
# Deliberately loose: enough to catch a typo, not to police what is valid.
EMAIL = re.compile(r"^[^@\s]+@[^@\s.]+(\.[^@\s.]+)+$")

# scrypt cost. n=2**14 keeps a single check around a tenth of a second here,
# which is slow for an attacker and unnoticeable for a person signing in.
_N, _R, _P = 2**14, 8, 1


class AccountError(Exception):
    pass


# ── names and addresses ────────────────────────────────────────────────
def normalise(email: str) -> str:
    return " ".join(email.split()).lower()[:120]


def tidy_name(name: str) -> str:
    """Capitalise only when they typed it all in lower case, so "angel"
    becomes "Angel" while "Ángel de la Cruz" is left exactly as written."""
    name = " ".join(name.split())[:40]
    if name and name == name.lower():
        name = " ".join(w[:1].upper() + w[1:] for w in name.split())
    return name


# ── passwords ──────────────────────────────────────────────────────────
def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    key = hashlib.scrypt(password.encode(), salt=salt, n=_N, r=_R, p=_P, dklen=32)
    return f"scrypt${_N}${_R}${_P}${salt.hex()}${key.hex()}"


def check_password(password: str, stored: str | None) -> bool:
    if not stored:
        return False
    try:
        scheme, n, r, p, salt, expected = stored.split("$")
        if scheme != "scrypt":
            return False
        key = hashlib.scrypt(
            password.encode(), salt=bytes.fromhex(salt),
            n=int(n), r=int(r), p=int(p), dklen=len(expected) // 2,
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(key.hex(), expected)


def _check_new_password(password: str) -> None:
    if len(password) < MIN_PASSWORD:
        raise AccountError(f"Use at least {MIN_PASSWORD} characters.")


# ── people ─────────────────────────────────────────────────────────────
def get(email: str) -> dict | None:
    with db.connect() as con:
        row = con.execute(
            "SELECT email, name, color, lang FROM people WHERE email = ?", (normalise(email),)
        ).fetchone()
    return dict(row) if row else None


def sign_up(name: str, email: str, password: str) -> dict:
    """Create an account, or claim one migrated from before passwords existed.

    Claiming is safe here because the shared password already stands in front
    of the whole app: nobody reaches this form without it.
    """
    email, name = normalise(email), tidy_name(name)
    if not name:
        raise AccountError("Type the name you want to be called.")
    if not EMAIL.match(email):
        raise AccountError("That doesn't look like an email address.")
    _check_new_password(password)

    with db.connect() as con:
        row = con.execute(
            "SELECT email, password_hash FROM people WHERE email = ?", (email,)
        ).fetchone()
        if row and row["password_hash"]:
            raise AccountError("That email already has an account. Sign in instead.")
        if row:
            con.execute(
                "UPDATE people SET name = ?, password_hash = ? WHERE email = ?",
                (name, hash_password(password), email),
            )
        else:
            count = con.execute("SELECT COUNT(*) AS n FROM people").fetchone()["n"]
            if count >= MAX_PEOPLE:
                raise AccountError("This app is full.")
            con.execute(
                "INSERT INTO people (email, name, color, password_hash) VALUES (?,?,?,?)",
                (email, name, COLORS[count % len(COLORS)], hash_password(password)),
            )
    return get(email)


def sign_in(email: str, password: str) -> dict:
    email = normalise(email)
    with db.connect() as con:
        row = con.execute(
            "SELECT email, password_hash FROM people WHERE email = ?", (email,)
        ).fetchone()
    if row and not row["password_hash"]:
        raise AccountError("This account has no password yet — use Create account.")
    # One message for both cases, so this can't be used to discover who has
    # an account here.
    if not row or not check_password(password, row["password_hash"]):
        raise AccountError("Wrong email or password.")
    return get(email)


def set_name(email: str, name: str) -> dict | None:
    name = tidy_name(name)
    if not name:
        raise AccountError("Type the name you want to be called.")
    with db.connect() as con:
        con.execute("UPDATE people SET name = ? WHERE email = ?", (name, normalise(email)))
    return get(email)


def set_lang(email: str, lang: str) -> dict | None:
    from . import i18n

    with db.connect() as con:
        con.execute(
            "UPDATE people SET lang = ? WHERE email = ?",
            (i18n.normalise(lang), normalise(email)),
        )
    return get(email)


def change_password(email: str, current: str, new: str) -> None:
    email = normalise(email)
    with db.connect() as con:
        row = con.execute(
            "SELECT password_hash FROM people WHERE email = ?", (email,)
        ).fetchone()
    if not row or not check_password(current, row["password_hash"]):
        raise AccountError("That's not your current password.")
    _check_new_password(new)
    with db.connect() as con:
        con.execute(
            "UPDATE people SET password_hash = ? WHERE email = ?",
            (hash_password(new), email),
        )
        # Every other browser is signed out; a password change should end
        # sessions someone else might be holding.
        con.execute("DELETE FROM sessions WHERE email = ?", (email,))


def export(email: str) -> dict:
    """Everything the app holds about one person, in one file.

    Offered before deleting, because plenty of people who reach for delete
    actually want to take their record with them, not lose it.
    """
    email = normalise(email)
    with db.connect() as con:
        person = con.execute(
            "SELECT email, name, color, lang, created_at FROM people WHERE email = ?",
            (email,),
        ).fetchone()
        ticks = con.execute(
            "SELECT item, done_at FROM done WHERE email = ? ORDER BY done_at", (email,)
        ).fetchall()
        sessions = con.execute(
            "SELECT created_at, last_seen FROM sessions WHERE email = ?", (email,)
        ).fetchall()
    if not person:
        raise AccountError("No such account.")
    return {
        "account": dict(person),
        "completed_sessions": [dict(r) for r in ticks],
        "signed_in_browsers": [dict(r) for r in sessions],
        "note": "Your password is not here. It is stored hashed and cannot be read back.",
    }


def delete(email: str) -> None:
    """Removes the account and everything attached to it.

    The foreign keys carry the sessions and the ticks with it — see
    db.connect(), which turns them on for every connection.
    """
    with db.connect() as con:
        con.execute("DELETE FROM people WHERE email = ?", (normalise(email),))


# ── sessions ───────────────────────────────────────────────────────────
def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def start_session(email: str) -> str:
    token = secrets.token_urlsafe(32)
    with db.connect() as con:
        con.execute(
            "INSERT INTO sessions (token_hash, email) VALUES (?, ?)",
            (_hash_token(token), normalise(email)),
        )
    return token


def whoami(token: str | None) -> dict | None:
    if not token:
        return None
    with db.connect() as con:
        row = con.execute(
            """SELECT p.email, p.name, p.color, p.lang FROM sessions s
               JOIN people p ON p.email = s.email
               WHERE s.token_hash = ?""",
            (_hash_token(token),),
        ).fetchone()
        if row:
            con.execute(
                "UPDATE sessions SET last_seen = datetime('now') WHERE token_hash = ?",
                (_hash_token(token),),
            )
    return dict(row) if row else None


def end_session(token: str | None) -> None:
    if not token:
        return
    with db.connect() as con:
        con.execute("DELETE FROM sessions WHERE token_hash = ?", (_hash_token(token),))
