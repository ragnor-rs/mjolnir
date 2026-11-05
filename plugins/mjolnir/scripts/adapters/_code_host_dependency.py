#!/usr/bin/env python3
"""The code host's own dependency relation, for the implementations that reach it.

[`schema.md § 3 → An edge is a relation`](../../config/schema.md#an-edge-is-a-relation-and-a-body-keeps-the-reasoning-about-it)
makes a dependency between two work items a port operation with a form stated per
tracker. Two kinds here answer it through the **same** host: plain issues, and a
board, which holds no relation of its own because a card is a view over an issue
and the dependency is a fact about the issues.

So the address and the shape of the answer live here rather than in either
module, for the reason `_policy.py` beside this one gives for a grammar two
implementations share: two copies are two statements allowed to disagree, and the
one that rots is whichever kind nobody is looking at. ⚠️ The measured instance is
not hypothetical — the sides of this relation are easy to get backwards, and a
copy that inverted one while the other stayed right would be a readiness gate
answering differently per kind on one host.

⛔ **The address, the shaping and the refusal on an answer neither can be read
from are here; the call and the guard are not.** Which transport a module speaks
through is its own, and so is the pull-request guard every operation routes
through — those name the thing they were about to reach. What the two share is
where the relation lives, what one of its entries means, and what an entry that
cannot be read is.

⚠️ The module name opens with `_` so the port's discovery skips it: a module in
`adapters/` that names no kind is refused rather than skipped, which is right for
an implementation and wrong for a grammar two of them share.
"""

from __future__ import annotations

import os
import re
import sys

_SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SCRIPTS not in sys.path:
    sys.path.append(_SCRIPTS)

import port  # noqa: E402

# A repository's own address, as this host writes it in an answer: a base, the
# collection segment, and **exactly two** segments after it. ⛔ Anchored at both
# ends rather than counted from the right, which is the guard's whole substance:
# the first form of it took the last two segments of whatever it was given and
# tested the arity of that split, and a split on a string containing any slash at
# all has more than one part -- so the guard was dead for every shape but a bare
# word. Measured, on this module's own first form: `.../repos` answered
# `api.github.com/repos`, `.../repos/o/n/issues/13` answered `issues/13`, and
# `https://api.github.com/` answered `/api.github.com`. ⚠️ Each of those is a
# plausible-looking repository address rather than a refusal, which is the worse
# direction: `None` says *this answer did not state one*, while `issues/13` sends
# a role to a repository of that name.
REPOSITORY_URL = re.compile(r"/repos/(?P<owner>[\w.-]+)/(?P<name>[\w.-]+)/?$")

def _word(value) -> str:
    """One field of a host answer, as a string, whatever the host put there.

    ⚠️ Not a convenience: an entry is outside this procedure, so a field this
    shaping treats as a word may arrive as a number or a null. The first form
    guarded one field of three and let the other two out as attribute and type
    errors, which `blockers_of` below states is never what an unreadable answer
    becomes.
    """
    return value if isinstance(value, str) else ""


# The relation is recorded on the **blocked** item, and this is the one place
# that is written down for this host. ⛔ Posting it on the blocker records a real
# relation the wrong way round and answers as though it had worked -- the
# inversion `docs/configuration-surface.md` measured -- so the path builder takes
# the blocked item by name rather than taking two numbers in an order a caller
# could swap.
def blocked_by_path(repo: str, blocked: int | str) -> str:
    """Where this host keeps what one item is blocked by."""
    return f"repos/{repo}/issues/{blocked}/dependencies/blocked_by"


def issue_path(repo: str, number: int | str) -> str:
    """One issue, by the address the id lookup for a relation needs.

    ⚠️ Here rather than in each module because the write keys on the blocker's
    **internal id** and not on its number, so both implementations have to look
    one up before they can post anything -- and the two integers are easy to
    confuse, the wrong one either erroring or addressing an unrelated issue.
    """
    return f"repos/{repo}/issues/{number}"


def blocker(entry: dict) -> dict:
    """One recorded blocker, in the shape a readiness check can read.

    ⛔ **The repository is carried per blocker and never assumed to be the
    configured one.** This host records a relation across repositories, and a
    board draws its cards from more than one, so a bare number sends a role
    looking for `#13` in the wrong backlog -- where the wrong `#13` answers
    perfectly rather than failing. ⚠️ Derived from the answer's own repository
    address, matched whole by `REPOSITORY_URL` above: the configured repository is
    where the *blocked* item lives, which is a different fact. ⛔ **An address
    this host did not write is `None` and never a guess at two of its segments**,
    for the reason stated on that pattern.

    ⛔ **The state is the host's own word and no verdict is derived from it.**
    Which of § 5's two bars a blocker is held to depends on what that blocker
    produced, so a `blocked`/`ready` answer here would be an implementation
    deciding a predicate it cannot see the inputs of. ⚠️ On the board that also
    means the **issue's** state rather than the card's column: a column is one
    project's own vocabulary (§ 4.2), and a predicate answered in it would be
    answered in a word no other project shares.

    ⚠️ **Lowered, and that is deliberate rather than tidying** -- the plain-issues
    module names this host's two states as lower-case constants and compares in
    them, so an answer in the host's own case would be the one shape in that
    module a caller has to `.lower()` for itself. ⛔ **`read_item` keeps the
    host's case** because what matches a project's `statuses` vocabulary is
    matched elsewhere and a role advancing a state reads that word; the two are
    one fact in two cases, and this is the half a predicate reads.

    ⛔ **Why the closed state is not the whole answer**: this host records *why* an
    item closed, and a blocker abandoned rather than finished is `closed` with a
    reason that says so. § 5's bar is what the dependency **produced**, so an
    implementation answering `closed` alone hands a gate a blocker that looks
    satisfied and produced nothing. ⚠️ Measured on this repository's own backlog,
    which holds items closed that way -- dormant only because no live item rests
    on one today. The reason is carried as the host states it and judged nowhere
    here.
    """
    # ⛔ Every field read for its own type and none assumed to be a string. A
    # host answer is outside this procedure, and an entry carrying a number where
    # a word belongs reached the operator as an attribute error -- which is the
    # traceback the port states three answers instead of.
    address = REPOSITORY_URL.search(_word(entry.get("repository_url")))
    return {
        "number": entry.get("number"),
        "state": _word(entry.get("state")).lower(),
        "state_reason": _word(entry.get("state_reason")).lower() or None,
        "title": entry.get("title"),
        "url": entry.get("html_url"),
        "repo": f"{address['owner']}/{address['name']}" if address else None,
    }


def blockers_of(answered, path: str) -> list[dict]:
    """Every recorded blocker out of what the host answered, shape held first.

    ⛔ **An answer this function cannot read is a *failed* operation and never a
    traceback.** The client is asked for every page and merges them into one
    array, which is undocumented behaviour its own help contradicts -- it states
    that each page is a separate array and that an outer wrapper is opt-in. So the
    two shapes that behaviour could become are held here rather than iterated
    over: a body that is not an array at all, and an array whose entries are not
    items. ⚠️ Measured on the shapes rather than on the client: unmerged pages
    reach the reader as a parse error and a wrapped object reaches it as an
    attribute error on a string, and both arrive where the port states three
    answers and no traceback.

    ⚠️ The path is named in the refusal so a reader can reproduce the call. It is
    the whole of what this function knows about where the answer came from --
    which client spoke is the caller's, and this grammar is shared by two.
    """
    if not isinstance(answered, list):
        raise port.HostUnavailable(
            f"`{path}` answered with {type(answered).__name__} where an array of "
            "items was expected, so what this item is blocked by could not be "
            "read. An unreadable answer is not the same as an item with no "
            "recorded blocker."
        )
    unreadable = [index for index, entry in enumerate(answered)
                  if not isinstance(entry, dict)]
    if unreadable:
        raise port.HostUnavailable(
            f"`{path}` answered an array whose entry at position {unreadable[0]} "
            f"is {type(answered[unreadable[0]]).__name__} and not an item, so the "
            f"{len(answered)} recorded blocker(s) could not be read."
        )
    return [blocker(entry) for entry in answered]
