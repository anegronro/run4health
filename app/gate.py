"""Shared password in front of the whole app.

Once the app is published to the internet the private network stops being the
boundary, so one password guards everything. It is asked for on a normal page
of our own rather than through HTTP Basic Auth, whose browser dialog is both
ugly and impossible to style.

Off unless FITNESS_PASSWORD is set.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse

COOKIE = "gate"
A_YEAR = 60 * 60 * 24 * 365
OPEN_PATHS = {"/health", "/enter", "/share.jpg", "/privacy", "/gone"}


def password() -> str:
    return os.environ.get("FITNESS_PASSWORD", "").strip()


def token(secret: str) -> str:
    """What a browser holds once it has proved it knows the password.

    Derived from the password, so changing the password logs everyone out.
    """
    return hmac.new(secret.encode(), b"fitness-gate-v1", hashlib.sha256).hexdigest()


def check(supplied: str, secret: str) -> bool:
    # Constant-time: a plain == leaks the answer one character at a time to
    # anyone who can measure the response.
    return secrets.compare_digest(supplied.strip(), secret)


class Gate(BaseHTTPMiddleware):
    def __init__(self, app, secret: str, render):
        super().__init__(app)
        self.secret = secret
        self.token = token(secret)
        self.render = render

    async def dispatch(self, request, call_next):
        if request.url.path in OPEN_PATHS:
            return await call_next(request)
        held = request.cookies.get(COOKIE, "")
        if secrets.compare_digest(held, self.token):
            return await call_next(request)
        # The bare URL answers 200 with the password page rather than
        # redirecting: the crawlers that build link previews often don't
        # follow redirects, and a shared link has to preview as itself.
        if request.url.path == "/":
            return self.render(request, "/")
        from urllib.parse import quote

        return RedirectResponse(
            f"/enter?back={quote(request.url.path, safe='')}", status_code=303
        )


def install(app, render) -> bool:
    secret = password()
    if not secret:
        return False
    app.add_middleware(Gate, secret=secret, render=render)
    return True
