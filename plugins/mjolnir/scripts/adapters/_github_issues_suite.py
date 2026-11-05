#!/usr/bin/env python3
"""The plain-issues implementation's own suite -- the dependency half of it.

⛔ **Scoped, and the scope is printed by every run rather than left to this
docstring.** This module is the kind this repository itself configures, and until
the dependency operations landed it had no suite at all: `adapter_suites.py`
reported it as *no suite -- reported rather than failed*, which is a stated
absence and was the honest answer while nothing here was asserted. ⚠️ **A suite
that exists reads as a module that is held**, so the one thing this file must not
do is let `read_item`, `search_items`, `create_item`, `set_state`, `comment`,
`set_labels`, `assign`, `link_for_close` or `advance_on_merge` read as covered.
They are not. What is covered is the relation between two work items -- the write,
the read, and the grammar the board's implementation shares with this one -- and
the run says so.

⚠️ **There is no named transport seam in the module beside this one**, unlike the
two implementations that came after it, so what this suite substitutes is `_gh`
itself. ⛔ The consequence is named rather than left to be discovered: `_gh`'s own
refusals -- a client that is not there, a timeout, a non-zero exit, an empty body
where one was expected -- are **not** exercised by anything here, because the
substitution replaces the function that raises them. Giving this module a seam of
its own is its implementation item's and not this one's.

⚠️ The module name opens with `_` so the port's discovery skips it: a module in
`adapters/` that names no kind is refused rather than skipped, which is right for
an implementation and wrong for a suite beside one.
"""

from __future__ import annotations

import os
import sys

_SUITE_SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SUITE_SCRIPTS not in sys.path:
    sys.path.append(_SUITE_SCRIPTS)

import port  # noqa: E402
from config import ConfigError  # noqa: E402
from port import HostUnavailable  # noqa: E402

from adapters import _code_host_dependency as relation  # noqa: E402
from adapters import github_issues as under_test  # noqa: E402
from adapters.github_issues import (  # noqa: E402
    ADAPTER,
    DELIBERATELY_ABSENT,
    KIND,
    bind,
    link_dependency,
    read_blockers,
)

# The repository this suite's calls address. ⛔ A shape the sweep in `tools/`
# cannot read as a real slug and nothing resolves: what is asserted here is which
# object a call addresses, never that a repository exists.
A_REPO = "an-owner/a-name"

# The item under test and the two it is related to. ⛔ Distinct integers, and the
# two halves of a write run opposite ways -- the id is looked up on the blocker
# and the relation is posted on the blocked item -- so a fixture reusing one
# number would pass an implementation that swapped them.
BLOCKED, BLOCKER = 11, 12

# What the host answers for an issue, narrowed to the fields the guard and the
# answer actually read. ⚠️ The `url` carries the issues path on purpose: it is the
# whole of what separates an item from a pull request here, and a fixture without
# it would exercise the refusal rather than the passing path.
def _issue(number: int) -> dict:
    return {
        "number": number,
        "title": f"an item, #{number}",
        "body": "",
        "state": "OPEN",
        "labels": [],
        "assignees": [],
        "url": f"https://example.invalid/{A_REPO}/issues/{number}",
    }


def _recorded(entries: list[tuple[int, str, str, str | None]]) -> list[dict]:
    """The host's own answer for the dependencies endpoint: plain issue objects.

    ⛔ Every entry carries its repository address and the host's own reason for
    its state -- the two halves a bare number and a bare state word lose. A
    relation is recordable across repositories, and an item abandoned rather than
    finished is closed with a reason that says so.
    """
    return [
        {
            "number": number,
            "state": state,
            "state_reason": reason,
            "title": f"a recorded blocker, #{number}",
            "html_url": f"https://example.invalid/{repo}/issues/{number}",
            "repository_url": f"https://api.example.invalid/repos/{repo}",
        }
        for number, state, repo, reason in entries
    ]


class _Host:
    """A transport that answers as the host does, and records what was asked.

    ⛔ A fake rather than a mock: it answers by **what was asked for** -- the
    client's subcommand, or the path of a REST call -- rather than by the order
    this module happens to call in, so a refactor that reorders calls does not
    redden it and a call that moves to the wrong object does.
    """

    def __init__(self, answers: dict | None = None, *, issues: dict | None = None):
        self.answers = answers or {}
        self.issues = issues if issues is not None else {
            BLOCKED: _issue(BLOCKED), BLOCKER: _issue(BLOCKER),
        }
        self.calls: list[str] = []
        self.sent: list[list[str]] = []

    def __call__(self, args: list[str], *, parse: bool = True):
        self.calls.append(" ".join(args[:2]))
        self.sent.append(list(args))
        for key, answer in self.answers.items():
            if key in " ".join(args):
                if isinstance(answer, Exception):
                    raise answer
                return answer
        if args[:2] == ["issue", "view"]:
            number = int(args[2])
            if number not in self.issues:
                raise HostUnavailable(f"this suite's host holds no #{number}")
            return self.issues[number]
        if args[0] == "api" and args[-1].endswith("/dependencies/blocked_by"):
            return []
        if args[0] == "api":
            return 4321
        raise AssertionError(f"this suite's host was asked for {args!r}")


def self_test() -> int:
    failures = 0

    def check(label: str, condition: bool, detail: str = "") -> None:
        nonlocal failures
        if condition:
            print(f"  ok    {label}")
        else:
            failures += 1
            print(f"  FAIL  {label}{': ' + detail if detail else ''}")

    # ⛔ All three catch **everything**, each reporting the other outcomes as
    # themselves rather than letting them out: a deliberate break that raises the
    # wrong kind must redden a line rather than kill the run on a traceback where
    # a verdict belongs.
    def refused(call) -> str | None:
        try:
            call()
        except ConfigError as error:
            return error.key
        except Exception as error:
            return f"<{type(error).__name__}: {error}>"
        return None

    def unavailable(call) -> str | None:
        try:
            call()
        except HostUnavailable as error:
            return str(error)
        except Exception as error:
            return f"<{type(error).__name__}: {error}>"
        return None

    def ran(call):
        try:
            return call()
        except Exception as error:
            return {"<raised>": f"{type(error).__name__}: {error}"}

    def with_host(host, call):
        was = under_test._gh
        under_test._gh = host
        try:
            return ran(call)
        finally:
            under_test._gh = was

    print(f"  --    `{KIND}`: the relation between two work items, and nothing else "
          "in this implementation")

    bind(port.Configuration({"host.repo": A_REPO})
         if hasattr(port, "Configuration") else {"host.repo": A_REPO})

    # --- the read, which is what § 5's blocker predicate has as a source ------
    elsewhere = "another-owner/another-name"
    recorded = _Host({"/dependencies/blocked_by": _recorded([
        (BLOCKER, "closed", A_REPO, "completed"),
        (13, "open", elsewhere, None),
        (14, "closed", A_REPO, "not_planned"),
    ])})
    answered = with_host(recorded, lambda: read_blockers(BLOCKED))
    blockers = answered.get("blockers") if isinstance(answered, dict) else None

    # ⛔ Every field read with `.get` and never by subscript, so an assertion
    # about a missing field is not the thing that cannot survive one.
    def field(name: str) -> list:
        return [entry.get(name) for entry in blockers or [{}]]

    check(
        "`read_blockers` answers every recorded blocker with the host's own state word",
        list(zip(field("number"), field("state")))
        == [(BLOCKER, "closed"), (13, "open"), (14, "closed")],
        f"answered {blockers!r}",
    )
    check(
        "and the repository each blocker is in, which a bare number loses",
        field("repo") == [A_REPO, elsewhere, A_REPO],
        f"answered {field('repo')!r}",
    )
    check(
        "and the host's own reason for a closed state, so an abandoned blocker is "
        "not an achieved one",
        field("state_reason") == ["completed", None, "not_planned"],
        f"answered {field('state_reason')!r}",
    )
    check(
        "and nothing beyond the fields the operation states, at either level",
        set(answered or {}) == {"number", "blockers"}
        and all(
            set(entry) == {"number", "state", "state_reason", "title", "url", "repo"}
            for entry in blockers or [{}]
        ),
        f"answered {sorted(answered or {})!r} over {sorted((blockers or [{}])[0])!r}",
    )
    # ⛔ The number is the **host's** and never the argument. The port passes every
    # value from an invocation as text, so an echoed argument puts a string beside
    # blocker entries carrying integers -- one answer, two types for one field.
    echoed = with_host(recorded, lambda: read_blockers(str(BLOCKED)))
    check(
        "the item's own number is the host's integer even where the argument was text",
        isinstance((echoed or {}).get("number"), int)
        and (echoed or {}).get("number") == BLOCKED,
        f"answered {(echoed or {}).get('number')!r}",
    )
    # ⛔ Every page, and the endpoint as a literal. ⚠️ The paging flag is asserted
    # on the **call** rather than inferred from the answer: this fake merges
    # nothing, so an implementation reading one page passes every case above.
    # ⚠️ **A host of its own**, measured on this case's first form: it shared the
    # one above, which by then had answered a second read, so the assertion saw
    # two identical calls and reddened for the suite's own bookkeeping rather than
    # for anything the module did.
    once = _Host({"/dependencies/blocked_by": _recorded([])})
    with_host(once, lambda: read_blockers(BLOCKED))
    read = [args for args in once.sent if args[:2] == ["api", "--paginate"]]
    check(
        "asked for at the endpoint this host keeps the relation on, every page",
        read == [[
            "api", "--paginate",
            f"repos/{A_REPO}/issues/{BLOCKED}/dependencies/blocked_by",
        ]],
        f"called {read!r}",
    )
    # ⛔ An answer the shared grammar cannot read is a failed outcome and never a
    # traceback -- the client's own help says each page is a separate array and an
    # outer wrapper is opt-in, so both shapes its merging could become are held.
    for label, planted in (
        ("an object where an array belongs", {"total_count": 1}),
        ("an array whose entry is not an item", ["#13"]),
    ):
        malformed = _Host({"/dependencies/blocked_by": planted})
        reported = with_host(malformed, lambda: unavailable(lambda: read_blockers(BLOCKED)))
        check(
            f"and {label} is a failed call naming the call that made it",
            reported is not None
            and relation.blocked_by_path(A_REPO, BLOCKED) in reported,
            f"got {reported!r}",
        )
    # ⛔ The guard, in the direction that matters: the path is the issues one,
    # which answers for a pull request here, so a blocker list read with a pull
    # request number is an answer about the wrong object -- and the refusal has to
    # land before the relation is read.
    a_pull_request = _Host(issues={BLOCKED: dict(
        _issue(BLOCKED), url=f"https://example.invalid/{A_REPO}/pull/{BLOCKED}")})
    reported = with_host(a_pull_request, lambda: unavailable(lambda: read_blockers(BLOCKED)))
    check(
        "a pull request number is refused before the relation is read",
        reported is not None and "pull request" in reported
        and a_pull_request.calls == ["issue view"],
        f"got {reported!r} after {a_pull_request.calls}",
    )
    # ⛔ And an answer with no `url` is refused rather than passed: the absent
    # signal used to read as *not a pull request*, which is the green answer from
    # the one guard everything else leans on.
    no_url = _Host(issues={BLOCKED: {k: v for k, v in _issue(BLOCKED).items()
                                     if k != "url"}})
    reported = with_host(no_url, lambda: unavailable(lambda: read_blockers(BLOCKED)))
    check(
        "and an answer carrying no address is refused rather than read as an item",
        reported is not None and "url" in reported,
        f"got {reported!r}",
    )

    # --- the write, and which object each half of it addresses ----------------
    #
    # ⛔ The two halves run opposite ways: the id is looked up on the **blocker**
    # and the relation is posted on the **blocked** item. Swap them and the call
    # still succeeds, recording a real relation the wrong way round -- and the
    # predicate above then holds the wrong item.
    written = _Host()
    with_host(written, lambda: link_dependency(BLOCKED, BLOCKER))
    posted = [args for args in written.sent if "--method" in args]
    looked_up = [args for args in written.sent if "--jq" in args]
    check(
        "the relation is posted on the blocked item and the id read off the blocker",
        len(posted) == 1 and len(looked_up) == 1
        and relation.blocked_by_path(A_REPO, BLOCKED) in posted[0]
        and relation.issue_path(A_REPO, BLOCKER) in looked_up[0],
        f"posted {posted!r} after looking up {looked_up!r}",
    )
    check(
        "and the body carries the blocker's internal id, not its number",
        any(part == "issue_id=4321" for args in posted for part in args),
        f"sent {posted!r}",
    )
    # ⛔ Both numbers go through the guard first, which is what keeps a relation
    # off a pull request: this is a write, and it was the worst of the two the
    # guard was once missing.
    for label, holding in (
        ("the blocked item", {BLOCKED: dict(_issue(BLOCKED),
                                            url=f"https://e.invalid/{A_REPO}/pull/{BLOCKED}"),
                              BLOCKER: _issue(BLOCKER)}),
        ("the blocker", {BLOCKED: _issue(BLOCKED),
                         BLOCKER: dict(_issue(BLOCKER),
                                       url=f"https://e.invalid/{A_REPO}/pull/{BLOCKER}")}),
    ):
        guarded = _Host(issues=holding)
        with_host(guarded, lambda: unavailable(lambda: link_dependency(BLOCKED, BLOCKER)))
        check(
            f"a pull request as {label} is refused before anything is written",
            not [args for args in guarded.sent if "--method" in args],
            f"sent {guarded.sent!r}",
        )

    # --- the operation set, against what the surface states -------------------
    #
    # ⛔ Asserted as a **relation** and never as a list or a count: what the
    # surface states minus what this module implements is exactly the set the
    # module itself names as deliberately absent. ⚠️ This is the arm that caught
    # the module's own docstring overstating what it implements -- a fourth
    # operation was absent while the sentence said *except the checklist ones* --
    # so neither side of this comparison is spelled here.
    stated = set(port.surface_operations())
    absent = stated - set(ADAPTER.operations)
    check(
        "what the surface states and this module leaves is exactly what it declares absent",
        absent == set(DELIBERATELY_ABSENT),
        f"absent: {sorted(absent)} against declared {sorted(DELIBERATELY_ABSENT)}",
    )
    check(
        "and the relation's own two are among the implemented ones",
        {"link_dependency", "read_blockers"} <= set(ADAPTER.operations),
        f"implements {sorted(ADAPTER.operations)}",
    )

    print(
        "  --    not covered here, and stated rather than implied: reading an item, "
        "searching, filing, states, comments, labels, the assignee, the closing "
        "reference, the advance off a merge, and `_gh`'s own refusals"
    )
    if failures:
        print(f"\n{failures} assertion(s) did not hold.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(self_test())
