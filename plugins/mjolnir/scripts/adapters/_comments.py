#!/usr/bin/env python3
"""What one read comment is, for every implementation that answers with them.

[`schema.md § 3 → An item's comments`](../../config/schema.md#an-items-comments-and-what-an-unread-one-is)
states the read. The shape of one entry is here once, for the reason `_policy.py`
beside this one gives; how a tracker pages its own comments is that tracker's.

⛔ **An entry that cannot be read fails the whole read.** A list short by one is
the shape that reads as a complete one, and the missing comment is the decision
nobody sees.

⚠️ The module name opens with `_` so the port's discovery skips it.
"""

from __future__ import annotations

import os
import sys

_SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SCRIPTS not in sys.path:
    sys.path.append(_SCRIPTS)

import port  # noqa: E402


def listed(answered, path: str) -> list[dict]:
    """The entries of one answer, or a failed read where it is not a list of them."""
    if not isinstance(answered, list):
        raise port.HostUnavailable(
            f"`{path}` answered with {type(answered).__name__} where a list of "
            "comments was expected, so the comments went unread. That is not an "
            "item with none."
        )
    for index, entry in enumerate(answered):
        if not isinstance(entry, dict):
            raise port.HostUnavailable(
                f"`{path}` answered a list whose entry at position {index} is "
                f"{type(entry).__name__} and not a comment, so the comments went "
                "unread. That is not an item with none."
            )
    return answered


def _word(value) -> str | None:
    return value if isinstance(value, str) and value.strip() else None


def comment(path: str, *, identifier, author, created, edited, url, body) -> dict:
    """One comment: who wrote it, when, whether it changed since, and what it says.

    `author` is `None` where the tracker states no writer -- a removed account --
    and that is an answer. A time or a text that is not there is not.

    `edited` is `None` where the comment still reads as it was first written.
    """
    at, changed = _word(created), _word(edited)
    if at is None or not isinstance(body, str):
        missing = "time" if at is None else "text"
        raise port.HostUnavailable(
            f"`{path}` answered comment {identifier!r} with no readable {missing}, "
            "so the comments went unread. That is not an item with none."
        )
    return {
        "id": identifier,
        "author": _word(author),
        "created": at,
        "edited": changed if changed != at else None,
        "url": _word(url),
        "body": body,
    }
