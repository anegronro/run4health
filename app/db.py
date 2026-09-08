"""The database: one SQLite file, opened per request.

SQLite rather than a server because the whole app runs on one small box and
one file is something you can copy, back up and restore without ceremony.
The JSON files it replaces could not survive two writes at once, and had no
history at all.
"""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PATH = Path(os.environ.get("FITNESS_DB", ROOT / "data" / "app.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS people (
  email          TEXT PRIMARY KEY,
  name           TEXT NOT NULL,
  color          TEXT NOT NULL,
  password_hash  TEXT,                       -- NULL until the account is claimed
  created_at     TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sessions (
  token_hash  TEXT PRIMARY KEY,              -- the raw token never touches disk
  email       TEXT NOT NULL REFERENCES people(email) ON DELETE CASCADE,
  created_at  TEXT NOT NULL DEFAULT (datetime('now')),
  last_seen   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS sessions_email ON sessions(email);

CREATE TABLE IF NOT EXISTS done (
  email    TEXT NOT NULL REFERENCES people(email) ON DELETE CASCADE,
  item     TEXT NOT NULL,                    -- "10k/w1/d2"
  done_at  TEXT NOT NULL DEFAULT (datetime('now')),
  PRIMARY KEY (email, item)
);
"""


def connect() -> sqlite3.Connection:
    PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(PATH, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    # WAL lets a reader and a writer coexist instead of blocking each other.
    con.execute("PRAGMA journal_mode = WAL")
    con.execute("PRAGMA synchronous = NORMAL")
    return con


def setup() -> None:
    with connect() as con:
        con.executescript(SCHEMA)
