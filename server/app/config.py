"""Loads the repo-root .env file (one level above server/) into the environment.

The .env file lives outside server/ deliberately, alongside the client, since both
sides of this project may eventually need shared local config. It is gitignored at
the repo root.
"""

from __future__ import annotations

from pathlib import Path

import truststore
from dotenv import load_dotenv

REPO_ROOT_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"


def load_environment() -> None:
    load_dotenv(dotenv_path=REPO_ROOT_ENV_PATH, override=False)

    # Some local/corporate network setups intercept TLS with a CA that's in the OS
    # trust store but not in Python's bundled certifi store, which breaks outbound
    # HTTPS calls to LLM providers (e.g. Gemini). truststore patches ssl.SSLContext
    # process-wide to defer to the OS trust store instead.
    truststore.inject_into_ssl()
