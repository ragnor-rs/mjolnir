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

⛔ **The address and the shaping are here; the call, the guard and the refusal are
not.** Which transport a module speaks through is its own — one goes straight out,
the other through a named seam its suite substitutes — and what a refusal says
names the thing it was about to reach, a card or an issue. What the two share is
only *where the relation lives* and *what one of its entries means*.

⚠️ The module name opens with `_` so the port's discovery skips it: a module in
`adapters/` that names no kind is refused rather than skipped, which is right for
an implementation and wrong for a grammar two of them share.
"""

from __future__ import annotations

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
    address: the configured repository is where the *blocked* item lives, which is
    a different fact.

    ⛔ **The state is the host's own word, lowered, and no verdict is derived from
    it.** Which of § 5's two bars a blocker is held to depends on what that
    blocker produced, so a `blocked`/`ready` answer here would be an
    implementation deciding a predicate it cannot see the inputs of. ⚠️ On the
    board that also means the **issue's** state rather than the card's column: a
    column is one project's own vocabulary (§ 4.2), and a predicate answered in it
    would be answered in a word no other project shares.
    """
    address = (entry.get("repository_url") or "").rstrip("/").rsplit("/", 2)
    return {
        "number": entry.get("number"),
        "state": (entry.get("state") or "").lower(),
        "title": entry.get("title"),
        "url": entry.get("html_url"),
        "repo": "/".join(address[-2:]) if len(address) >= 2 else None,
    }
