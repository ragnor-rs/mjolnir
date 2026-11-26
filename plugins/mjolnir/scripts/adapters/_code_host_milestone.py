#!/usr/bin/env python3
"""Which milestone a grouping's value names, for the kinds that reach one host.

Plain issues and a board over them address the same milestones, so the matching
lives here once, for the reason `_code_host_dependency.py` beside this one gives.
The transport is the caller's. ⚠️ The module name opens with `_` so the port's
discovery skips it.
"""

from __future__ import annotations

import os
import sys

_SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SCRIPTS not in sys.path:
    sys.path.append(_SCRIPTS)

import port  # noqa: E402

KEY = "work_item.grouping"


def held(milestones: list, value: str, repo: str) -> dict | None:
    """The milestone `value` names among those `repo` holds, or `None` for none.

    ⛔ **Matched on the title and never on the number.** § 4.8's value is the
    project's own word for the grouping -- the word on the item -- and the
    number is this host's internal one, so a reader that took the value for a
    number would address a different milestone whenever the two disagreed.
    ⚠️ Exactly, then case-insensitively, and ⛔ an ambiguous fold is refused
    rather than resolved: two milestones a project cannot tell apart is a
    defect in the text, and closing the wrong release is not recoverable.

    ⚠️ The caller hands over the milestones of **both** states, this host's
    listing defaulting to the open ones.
    """
    exact = [one for one in milestones if one.get("title") == value]
    if len(exact) == 1:
        return exact[0]
    folded = [
        one
        for one in milestones
        if str(one.get("title", "")).casefold() == str(value).casefold()
    ]
    if len(folded) == 1:
        return folded[0]
    if not folded:
        return None
    raise port.ConfigError(
        KEY,
        f"names the grouping {value!r}, which {len(folded)} milestones in {repo} "
        "answer to once case is set aside. Which one a release closes is not this "
        "implementation's to choose.",
    )


def named(milestones: list, value: str, repo: str) -> dict:
    """The milestone `value` names, refusing where `repo` holds none.

    ⛔ Refused by name rather than answered with an empty set: a set of nothing is
    what a release holding nothing looks like, and § 33 reads a bar off that set.
    """
    found = held(milestones, value, repo)
    if found is None:
        raise port.ConfigError(
            KEY,
            f"names the grouping {value!r}, which is not a milestone {repo} "
            "holds. The value is the word on the item and the milestone is "
            "addressed by its title, so a grouping this repository has no "
            "milestone for is a defect in the text rather than a capability that "
            "is absent.",
        )
    return found
