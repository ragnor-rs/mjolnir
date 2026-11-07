#!/usr/bin/env python3
"""The plain-issues implementation's own suite -- the dependency half of it.

⛔ **Scoped to the relation between two work items**, plus the operations this
change's own rule reaches beyond it: the number in an answer is the host's and not
the argument, so the assignment that wrote before it read, the writes that
addressed the argument, and the operations that make no call and therefore
normalise nothing are all here. The **uncovered** side of that scope is derived and
printed by every run: the run subtracts what it covers from what the module
implements, so an operation added to the module moves the statement instead of
making it stale. ⚠️ **The covered side is a claim and not a
measurement** -- `COVERED` below is written by hand, nothing holds it to what the
run actually exercises, and the print says so.
⚠️ **A suite that exists reads as a module that is held**, which this module is
not -- until the dependency operations landed it had no suite at all, and
`adapter_suites.py` reported that as a stated absence, which was the honest
answer while nothing here was asserted.

⚠️ **The module beside this one grew its named transport seam later than the
implementations after it did**, and it grew it for this suite. ⛔ **Two seams are
substituted here and the depth of each is the point**: the named one stands in
for the whole client, which is where an operation's own orderings and guards are
assertable -- and which *replaces* the parse, so a case written against it sees
none of the refusals the client function itself raises. Those are reached one
level deeper. ⚠️ What is still exercised by nothing is a call that times out and
a client that is not on the path.

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
from port import ConfigError, HostUnavailable  # noqa: E402

from adapters import _code_host_dependency as relation  # noqa: E402
from adapters import github_issues as under_test  # noqa: E402
from adapters.github_issues import (  # noqa: E402
    ADAPTER,
    DELIBERATELY_ABSENT,
    KIND,
    advance_on_merge,
    bind,
    link_dependency,
    read_blockers,
)

# The repository this suite's calls address. ⛔ A shape the sweep in `tools/`
# cannot read as a real slug and nothing resolves: what is asserted here is which
# object a call addresses, never that a repository exists.
A_REPO = "an-owner/a-name"

# The operations this suite exercises. ⛔ The one list, and the run subtracts it
# from what the module implements rather than carrying a second list of what it
# leaves: two lists are two statements allowed to disagree, and the hand-written
# one had already dropped an operation.
COVERED = {
    "link_dependency",
    "read_blockers",
    "advance_on_merge",
    "assign",
    "comment",
    "item_number",
    "link_for_close",
    "set_labels",
    "set_state",
}

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

    def __call__(self, args: list[str], parse: bool = True):
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

    # ⛔ Each catches **everything**, reporting the other outcomes as itself
    # rather than letting them out: a deliberate break that raises the wrong kind
    # must redden a line rather than kill the run on a traceback where a verdict
    # belongs.
    def unavailable(call) -> str | None:
        try:
            call()
        except HostUnavailable as error:
            return str(error)
        except Exception as error:
            return f"<{type(error).__name__}: {error}>"
        return None

    def refused(call) -> str | None:
        """The key a call refuses on, or None where it returns instead."""
        try:
            call()
        except ConfigError as error:
            return error.key
        except Exception as error:
            return f"<{type(error).__name__}: {error}>"
        return None

    def ran(call):
        try:
            return call()
        except Exception as error:
            return {"<raised>": f"{type(error).__name__}: {error}"}

    def with_host(host, call):
        """The named seam, which is where an operation's own answers come from."""
        was = under_test.TRANSPORT
        under_test.TRANSPORT = host
        try:
            return ran(call)
        finally:
            under_test.TRANSPORT = was

    def with_client(printed: str, call):
        """One level deeper, for the refusals the client function itself raises.

        The depth of each seam, and why these refusals need this one, is the
        module docstring's.
        """
        was = under_test.subprocess

        class _Answered:
            stdout, stderr, returncode = printed, "", 0

        class _Client:
            TimeoutExpired = was.TimeoutExpired
            CalledProcessError = was.CalledProcessError

            @staticmethod
            def run(*arguments, **keywords):
                return _Answered()

        under_test.subprocess = _Client
        try:
            return call()
        finally:
            under_test.subprocess = was

    print(f"  --    `{KIND}`: the relation between two work items, and the "
          "operations beyond it that carry an identifier")

    bind({"host.repo": A_REPO})

    # --- the read, which is what § 5's blocker predicate has as a source ------
    elsewhere = "another-owner/another-name"
    # ⚠️ One entry carries the host's word in another case, so the normalisation
    # this answer is documented to perform is asserted rather than assumed: with
    # every fixture word already lower-case, dropping the lowering kept the suite
    # green and the case named the state word in its own label.
    recorded = _Host({"/dependencies/blocked_by": _recorded([
        (BLOCKER, "CLOSED", A_REPO, "COMPLETED"),
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
        "`read_blockers` answers every recorded blocker with the host's state word, lowered",
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
        "and the host's own reason for a closed state, lowered too, so an abandoned "
        "blocker is not an achieved one",
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
        # ⛔ One per field § 5 needs to apply a bar at all: the state, or an entry
        # answered as neither open nor closed, and the identifier, for the reason
        # the shared grammar states.
        ("an item whose state is not a word",
         [dict(_recorded([(13, "open", A_REPO, None)])[0], state=None)]),
        ("an item whose number is not a number",
         [dict(_recorded([(13, "open", A_REPO, None)])[0], number=None)]),
        # ⚠️ The empty word, which is a string and is what the arm's own reason
        # names: a blocker reported as neither open nor closed. The first form of
        # the arm tested the type alone and admitted it.
        ("an item whose state is the empty word",
         [dict(_recorded([(13, "open", A_REPO, None)])[0], state="  ")]),
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
    # ⛔ The write's answer carries the host's numbers too, not the arguments.
    # ⚠️ Measured as the sibling of the read's own case: the rule was written for
    # `read_blockers` and left unapplied here, so one relation answered with two
    # types for one field name while the suite held only the read.
    written_text = _Host()
    answered = with_host(
        written_text, lambda: link_dependency(str(BLOCKED), str(BLOCKER))
    )
    check(
        "the write answers with the host's own numbers even where the arguments were text",
        isinstance((answered or {}).get("blocked"), int)
        and isinstance((answered or {}).get("blocked_by"), int)
        and ((answered or {}).get("blocked"), (answered or {}).get("blocked_by"))
        == (BLOCKED, BLOCKER),
        f"answered {answered!r}",
    )

    # --- the client's own refusals, where this change widened them ------------
    #
    # ⛔ A body that is not one JSON document is a failed call and never a
    # traceback, for the reason the client function's own comment states.
    # ⚠️ Through the deeper seam, per the module docstring.
    for label, printed, expected in (
        ("pages that were not merged", '[{"number": 1}]\n[{"number": 2}]\n',
         "not one JSON document"),
        ("a body that is not JSON at all", "not json\n", "not one JSON document"),
        ("an empty body", "", "nothing where a body was expected"),
    ):
        reported = unavailable(
            lambda printed=printed: with_client(
                printed, lambda: under_test._gh(["api", "a-path"])
            )
        )
        check(
            f"{label} is a failed call rather than a traceback",
            reported is not None and expected in reported,
            f"got {reported!r}",
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

    # ⛔ An argument that is not a number is refused before any call, this kind's
    # client documenting its argument as a number **or a URL** -- and a URL names
    # a repository of its own and wins over `--repo`. ⚠️ So the shape that matters
    # most here is the one the sibling kind has no equivalent of: without the
    # guard this read validated an item in another repository while the write
    # below addressed the configured one, which is the two-halves-of-one-call
    # defect the answer's own number was normalised against. The other shapes are
    # the sibling's, for the sibling's reason.
    for handed in (
        "not-a-number",
        True,
        1.9,
        " 11 ",
        "²",
        f"https://github.com/{elsewhere}/issues/{BLOCKED}",
    ):
        shapeless = _Host()
        reported = with_host(
            shapeless, lambda handed=handed: refused(lambda: read_blockers(handed))
        )
        check(
            f"{handed!r} is refused as an item number, before any call",
            reported == "tracker.operations.read_item"
            and shapeless.calls == [] and shapeless.sent == [],
            f"reported {reported!r} after {shapeless.calls} and {shapeless.sent}",
        )
    check(
        "while the two shapes a number does arrive in are accepted",
        all(
            isinstance(
                (with_host(_Host(), lambda handed=handed: read_blockers(handed))
                 or {}).get("number"),
                int,
            )
            for handed in (BLOCKED, str(BLOCKED))
        ),
        "an integer or a string of digits was refused",
    )
    # ⛔ Beyond the relation, and here because this change's own rule reaches it:
    # the number in an answer is the host's, so an operation building a query
    # variable or a path from its argument is the other half of that rule and
    # nothing else held it. ⚠️ Every case this kind had handed an integer, where an
    # echo and a read are the same value.
    confirming = _Host({"closedByPullRequestsReferences": {
        "data": {"repository": {"issue": {
            "state": "CLOSED",
            "closedByPullRequestsReferences": {
                "nodes": [{"number": 20, "merged": True, "mergeCommit": {"oid": "abc123"}}],
            },
        }}},
    }})
    confirmed = with_host(confirming, lambda: advance_on_merge(str(BLOCKED)))
    check(
        "the merge confirmation answers the host's own number where the argument was text",
        isinstance((confirmed or {}).get("number"), int)
        and (confirmed or {}).get("number") == BLOCKED,
        f"answered {(confirmed or {}).get('number')!r}",
    )
    # ⛔ **No case here for where the query variable came from, and that is the
    # finding rather than an omission**: this kind builds it with an f-string, so
    # the argument's text and the host's integer render identically and nothing a
    # suite can read tells them apart. The first form of this assertion compared
    # the rendered part and stayed green with the mechanism reverted. What is
    # observable is the answered number, above. ⚠️ The sibling kind passes the
    # value to its client rather than rendering it, so the flag it chooses is the
    # observable there and its own suite holds it.

    # --- the operations the argument rule reaches beyond the relation ----------
    #
    # ⛔ Here because this change's own rule reaches them and nothing else held
    # them: an operation that writes before it reads is outside the guard the
    # module's docstring claims covers every one, and an identifier composed from
    # an argument rather than normalised is the same two-halves defect one step
    # removed.
    taken = _Host(issues={
        BLOCKED: dict(_issue(BLOCKED), url=f"https://e.invalid/{A_REPO}/pull/{BLOCKED}"),
    })
    with_host(taken, lambda: unavailable(lambda: under_test.assign(BLOCKED)))
    check(
        "a pull request is refused before the assignment is written, not after",
        not [args for args in taken.sent if "--add-assignee" in args],
        f"sent {taken.sent!r}",
    )
    numberless = _Host({"issue view": {
        "title": "an answer with no number",
        "url": f"https://e.invalid/{A_REPO}/issues/{BLOCKED}",
        "state": "OPEN", "labels": [], "assignees": [], "body": "",
    }})
    reported = with_host(
        numberless, lambda: unavailable(lambda: read_blockers(BLOCKED))
    )
    check(
        "an answer carrying no number is a failed call, not a subscript on nothing",
        reported is not None and "no number" in reported,
        f"got {reported!r}",
    )
    # ⛔ The identifier operation makes no call, so what it is handed is all it
    # has. ⚠️ A string is the shape the port passes, and the first form
    # subscripted it -- a traceback from the one operation that cannot fail for
    # any other reason. The non-ASCII decimal digit is the one `isdecimal` admits
    # and the host does not resolve, so normalising is what makes the reference
    # the next row asserts a reference the host can read.
    # ⚠️ Every call through `ran`, so a shape that raises reddens a line rather
    # than killing the run -- which is what the first form of these did, and a
    # traceback is not a verdict.
    read_shapes = [
        ran(lambda handed=handed: under_test.item_number(handed))
        for handed in (BLOCKED, str(BLOCKED), f"  {BLOCKED}  ", "١١", {"number": BLOCKED})
    ]
    check(
        "the identifier operation reads a number out of every shape the port passes",
        read_shapes == [BLOCKED, BLOCKED, BLOCKED, 11, BLOCKED],
        f"read {read_shapes!r}",
    )
    reported = refused(lambda: under_test.item_number("not-a-number"))
    check(
        "and refuses a shape carrying no number rather than raising from a subscript",
        reported == "tracker.operations.item_number",
        f"reported {reported!r}",
    )
    composed = ran(lambda: under_test.link_for_close("١١"))
    check(
        "the closing reference carries a number the host can resolve, not the argument",
        composed == "Closes #11",
        f"composed {composed!r}",
    )
    # ⛔ And every write addresses the number the host answered with. ⚠️ Asked
    # with a **zero-padded** decimal, which is the observable shape: the guard
    # accepts it and normalises it, while `str()` of the argument and of the
    # host's integer differ -- with an unpadded argument the two render
    # identically and a case cannot tell the mechanism from its absence.
    padded = _Host()
    with_host(padded, lambda: under_test.assign(f"0{BLOCKED}"))
    written = [args for args in padded.sent if "--add-assignee" in args]
    check(
        "the assignment addresses the host's own number, not the argument's spelling",
        written and all(str(BLOCKED) in args and f"0{BLOCKED}" not in args
                        for args in written),
        f"sent {written!r}",
    )
    # ⛔ One per write, because each builds its own call and the rule is per call.
    # ⚠️ `set_labels` asks for a label the fixture does not carry: asking for the
    # ones it has returns on the operation's own short-circuit before any write.
    for operation, call, mark in (
        ("comment", lambda: under_test.comment(f"0{BLOCKED}", "a note"), "--body"),
        ("set_state", lambda: under_test.set_state(f"0{BLOCKED}", status="closed"), "close"),
        ("set_labels", lambda: under_test.set_labels(f"0{BLOCKED}", ["infra"]), "--add-label"),
    ):
        writing = _Host()
        with_host(writing, call)
        wrote = [args for args in writing.sent if mark in args]
        check(
            f"and so does `{operation}`",
            bool(wrote) and all(str(BLOCKED) in args and f"0{BLOCKED}" not in args
                                for args in wrote),
            f"sent {writing.sent!r}",
        )

    # --- the operation set, against what the surface states -------------------
    #
    # ⛔ Asserted as a **relation** and never as a list or a count: what the
    # surface states minus what this module implements is exactly the set the
    # module itself names as deliberately absent. ⚠️ This is the arm that caught
    # the module's own docstring overstating what it implements -- an operation
    # was absent while the sentence said *except the checklist ones* -- so neither
    # side of this comparison is spelled here.
    stated = set(port.surface_operations())
    absent = stated - set(ADAPTER.operations)
    check(
        "what the surface states and this module leaves is exactly what it declares absent",
        absent == set(DELIBERATELY_ABSENT),
        f"absent: {sorted(absent)} against declared {sorted(DELIBERATELY_ABSENT)}",
    )
    check(
        "and everything this suite claims to cover is an operation the module has",
        COVERED <= set(ADAPTER.operations),
        f"claims {sorted(COVERED)} against {sorted(ADAPTER.operations)}",
    )

    # ⛔ The uncovered side is derived and never enumerated: what the module
    # implements minus what `COVERED` claims. ⚠️ The first form of this line was a
    # hand-written list and had already dropped an operation the module
    # implements -- which is the omission the docstring above forbids, in the
    # sentence that forbids it.
    # ⚠️ The arm above catches only a name the module does not implement at all;
    # what else `COVERED` is and is not is the module docstring's.
    print(
        "  --    not covered here, and stated rather than implied: "
        + ", ".join(f"`{name}`"
                    for name in sorted(set(ADAPTER.operations) - COVERED))
    )
    if failures:
        print(f"\n{failures} assertion(s) did not hold.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(self_test())
