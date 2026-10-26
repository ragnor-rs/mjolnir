#!/usr/bin/env python3
"""One form per class `policy.forbid_on_item` states, for every implementation.

[`schema.md § 3`](../../config/schema.md#a-write-forbidden-by-policy-rather-than-by-capability)
states that a write may be forbidden by policy rather than by capability, and that
a role meeting one has a capability it may not use here. The forms that decide
whether a span belongs to a barred class live **here** rather than in an
implementation, for the reason the surface gives for everything else in this
toolkit: two implementations carrying one grammar are two statements allowed to
disagree, and the one that rots is whichever tracker nobody is looking at.

⛔ **The grammar is here; the refusal is not.** What a refusal says names the
thing a write was about to reach -- a card, an issue -- so each implementation
raises its own, keyed on `tracker.policy.forbid_on_item`. What they share is only
the question *does this text carry a barred class*.

⛔ **Nothing here is matched by how a sentence reads.** A class decided by
meaning is a guard whose refusals cannot be argued with, so every form below is a
shape.

⚠️ `credentials` is given no form here at all. § 14's own arm already carries
one, it binds regardless of configuration, and a second grammar for the same
class is the duplication this module exists to remove -- so this reads that one.

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

import boundary  # noqa: E402

FENCE = re.compile(r"^\s*(?:```|~~~)", re.MULTILINE)

# A path, in the three forms one reaches prose in: rooted at `/` or `./`, ending
# in a file extension, or ⛔ **two or more separators deep with neither** -- which
# is the commonest form a repository path takes in a sentence and which the first
# draft of this grammar missed entirely, its plant having had an extension. ⚠️ The
# depth is what keeps `and/or` and `yes/no` out: one separator is prose and two is
# a path. ⚠️ A URL's path matches this where it ends in a file, which is two
# findings for one span rather than a miss -- both classes are barred, and the
# refusal names each it found.
FILE_PATH = re.compile(
    r"(?:(?<![\w/])(?:\.{1,2}/|/)[\w.-]+(?:/[\w.-]+)*"
    r"|(?<![\w/])[\w.-]+(?:/[\w.-]+)+\.[A-Za-z][A-Za-z0-9]{0,7}"
    r"|(?<![\w/])[\w.-]+(?:/[\w.-]+){2,})(?![\w/])"
)

# ⚠️ The third of these collides with a file-and-line citation, and that is
# stated rather than tightened away: `a.b:12` is a host and a port and a file and
# a line in the same characters, and nothing lexical tells them apart. So the
# class named may be the wrong one of two -- which costs nothing where a project
# bars both, as the shipped examples do, and fails closed where it bars one.
HOSTING = [
    re.compile(r"\b[a-z][a-z0-9+.-]*://", re.I),
    re.compile(r"(?<![\w.])\d{1,3}(?:\.\d{1,3}){3}(?![\w.])"),
    re.compile(r"\b[a-z0-9-]+(?:\.[a-z0-9-]+)+:\d{2,5}\b", re.I),
]


def branch_name_form(prefixes: list[str]) -> re.Pattern:
    """A branch name, from the prefixes the project's own configuration states.

    ⛔ Derived rather than written: § 10 composes a branch name out of
    `work_item.type_branch_prefix`, so the prefixes a project states are exactly
    what one of its branch names can open with. A form written here would be a
    second statement of the same thing, wrong for every project whose prefixes
    are not one example's.
    """
    alternation = "|".join(re.escape(prefix) for prefix in sorted(set(prefixes)))
    return re.compile(rf"\b(?:{alternation})/[\w.-]+", re.I)


def forbidden(text: str, classes: list[str], prefixes: list[str]) -> list[str]:
    """Every barred class the text carries, named and ⛔ never quoted in full.

    One finding per class rather than one per span: what a role has to act on is
    *which* class reached the text, and a refusal that quoted each span would
    publish the credential it refused -- § 14's rule, which is also why the
    credentials class reads that module's own grammar rather than a second one.

    ⛔ A class no form here answers comes back as a finding too. A policy that
    cannot be answered is not a policy that was observed, and the write is
    refused rather than passed with a predicate unread (§ 11).
    """
    found = []
    for name in classes:
        if name == "credentials":
            shapes = boundary.credentials(text)
            if shapes:
                found.append(
                    f"`credentials`: {len(shapes)} credential shape(s) in the text, "
                    "read through § 14's own arm"
                )
        elif name == "source_code":
            if FENCE.search(text):
                found.append("`source_code`: a fenced block")
        elif name == "file_paths":
            match = FILE_PATH.search(text)
            if match:
                found.append(f"`file_paths`: a path at character {match.start()}")
        elif name == "hosting_details":
            for pattern in HOSTING:
                match = pattern.search(text)
                if match:
                    found.append(
                        f"`hosting_details`: an address at character {match.start()}"
                    )
                    break
        elif name == "branch_names":
            if not prefixes:
                found.append(
                    "`branch_names`: the project bars them and states no "
                    "`work_item.type_branch_prefix`, so what one looks like here "
                    "cannot be derived and the text cannot be held to it"
                )
            else:
                match = branch_name_form(prefixes).search(text)
                if match:
                    found.append(
                        f"`branch_names`: a branch name at character {match.start()}"
                    )
        else:
            found.append(
                f"`{name}`: a class this implementation has no form for, so a "
                "write cannot be known to observe it"
            )
    return found
