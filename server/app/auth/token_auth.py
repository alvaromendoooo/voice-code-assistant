"""Shared-token auth for the IDE <-> backend WebSocket handshake.

This is local-development-grade auth (see docs/architecture/phase1-design.md), not a full
auth system: a single shared secret, configured on both sides out of band, checked before
a WebSocket connection is accepted.
"""

from __future__ import annotations

import os


def get_expected_token() -> str | None:
    """Read the shared secret from the environment.

    Returns None if no token is configured, which callers should treat as "auth
    disabled" (acceptable for local scaffolding, not for anything beyond it).
    """
    return os.environ.get("VCA_SHARED_TOKEN")


def is_token_valid(provided_token: str | None) -> bool:
    expected = get_expected_token()
    if expected is None:
        return True
    if provided_token is None:
        return False
    return provided_token == expected
