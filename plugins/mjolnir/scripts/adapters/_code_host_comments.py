#!/usr/bin/env python3
"""An issue's comments on the code host, for the two kinds that reach them.

Plain issues, and a board whose cards are views over issues: the address and the
field names are here once, for the reason `_code_host_dependency.py` beside this
one gives. The transport and the pull-request guard are each caller's.

⚠️ The module name opens with `_` so the port's discovery skips it.
"""

from __future__ import annotations

import os
import sys

_SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SCRIPTS not in sys.path:
    sys.path.append(_SCRIPTS)

from adapters import _comments  # noqa: E402


def comments_path(repo: str, number: int) -> str:
    """Where this host keeps one issue's comments, oldest first."""
    return f"repos/{repo}/issues/{number}/comments?per_page=100"


def comments_of(answered, path: str) -> list[dict]:
    """Every comment out of what the host answered, its pages already merged."""
    return [
        _comments.comment(
            path,
            identifier=entry.get("id"),
            author=entry["user"].get("login")
            if isinstance(entry.get("user"), dict) else None,
            created=entry.get("created_at"),
            edited=entry.get("updated_at"),
            url=entry.get("html_url"),
            body=entry.get("body"),
        )
        for entry in _comments.listed(answered, path)
    ]
