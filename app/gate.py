"""Shared password in front of the whole app.

Once the app is published to the internet, the private network stops being
the boundary. This is one password for the whole group — it decides who gets
in at all; the email profiles inside only decide whose ticks are whose.

Off unless FITNESS_BASIC_AUTH is set, as "user:password".
"""
from __future__ import annotations

import base64
import binascii
import os
import secrets

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import PlainTextResponse

OPEN_PATHS = {"/health"}


class BasicAuth(BaseHTTPMiddleware):
    def __init__(self, app, credentials: str):
        super().__init__(app)
        user, _, password = credentials.partition(":")
        self.expected = f"{user}:{password}"

    async def dispatch(self, request, call_next):
        if request.url.path in OPEN_PATHS:
            return await call_next(request)
        header = request.headers.get("authorization", "")
        scheme, _, token = header.partition(" ")
        if scheme.lower() == "basic":
            try:
                supplied = base64.b64decode(token).decode("utf-8")
            except (binascii.Error, UnicodeDecodeError):
                supplied = ""
            # Constant-time: a plain == leaks the password one character at a
            # time to anyone who can measure the response.
            if secrets.compare_digest(supplied, self.expected):
                return await call_next(request)
        return PlainTextResponse(
            "Authentication required.",
            status_code=401,
            headers={"WWW-Authenticate": 'Basic realm="Programs", charset="UTF-8"'},
        )


def install(app) -> bool:
    credentials = os.environ.get("FITNESS_BASIC_AUTH", "").strip()
    if not credentials or ":" not in credentials:
        return False
    app.add_middleware(BasicAuth, credentials=credentials)
    return True
