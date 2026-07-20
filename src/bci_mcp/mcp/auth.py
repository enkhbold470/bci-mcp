"""Optional bearer-token auth for the HTTP transports.

Set ``MCP_AUTH_TOKEN`` and every HTTP request (except ``GET /health``) must
carry ``Authorization: Bearer <token>``. Unset, the middleware passes
everything through unchanged, so local stdio/dev setups are unaffected.
"""
from __future__ import annotations

import hmac
import os

_EXEMPT_PATHS = frozenset({"/health"})


def configured_token() -> str | None:
    """The shared secret from the environment, or None when auth is disabled."""
    return os.environ.get("MCP_AUTH_TOKEN") or None


class TokenAuthMiddleware:
    """Pure-ASGI middleware enforcing a static bearer token when configured.

    The token is read from the environment per-request (unless given
    explicitly), so it works regardless of import order relative to
    deployment env setup.
    """

    def __init__(self, app, token: str | None = None) -> None:  # noqa: ANN001
        self.app = app
        self._token = token

    async def __call__(self, scope, receive, send) -> None:  # noqa: ANN001
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        token = self._token if self._token is not None else configured_token()
        if not token or scope.get("path") in _EXEMPT_PATHS:
            await self.app(scope, receive, send)
            return
        provided = ""
        for key, value in scope.get("headers", []):
            if key == b"authorization":
                provided = value.decode("latin-1")
                break
        auth_scheme, _, credential = provided.partition(" ")
        if auth_scheme.lower() == "bearer" and hmac.compare_digest(
                credential.strip(), token):
            await self.app(scope, receive, send)
            return
        await send({
            "type": "http.response.start",
            "status": 401,
            "headers": [(b"content-type", b"application/json"),
                        (b"www-authenticate", b"Bearer")],
        })
        await send({"type": "http.response.body",
                    "body": b'{"error": "unauthorized"}'})
