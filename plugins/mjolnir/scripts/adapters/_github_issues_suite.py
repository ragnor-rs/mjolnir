#!/usr/bin/env python3
"""The plain-issues implementation's own suite -- the dependency half of it.

⛔ **Scoped to the relation between two work items**, plus the operations this
change's own rule reaches beyond it: the number in an answer is the host's and not
the argument, so the assignment that wrote before it read, the operations that
build a call out of their argument, and the ones that make no call and therefore
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
    read_vocabulary,
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
    "grouping_items",
    "create_grouping",
    "mark_grouping_released",
    "read_closing_change",
    "read_vocabulary",
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
    # ⛔ Stripped as well as lowered, for the shaping's own stated reason.
    padded = _Host({"/dependencies/blocked_by": [
        dict(_recorded([(13, "closed", A_REPO, "completed")])[0],
             state="  CLOSED  ", state_reason="  COMPLETED  ")
    ]})
    shaped = (with_host(padded, lambda: read_blockers(BLOCKED)) or {}).get("blockers")
    check(
        "a padded state and reason arrive as the host's own words, not as padding",
        [(entry.get("state"), entry.get("state_reason"))
         for entry in shaped or []] == [("closed", "completed")],
        f"answered {shaped!r}",
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
        # ⚠️ A bool is an `int`, so a number answered as one names no item while
        # passing a type test.
        ("an item whose number is `true`",
         [dict(_recorded([(13, "open", A_REPO, None)])[0], number=True)]),
        # ⚠️ And this host numbers from one, so neither of these names an item.
        ("an item numbered zero",
         [dict(_recorded([(13, "open", A_REPO, None)])[0], number=0)]),
        ("an item numbered below zero",
         [dict(_recorded([(13, "open", A_REPO, None)])[0], number=-13)]),
        # ⛔ And the reason, for the arm's own stated reason.
        ("an item whose closed reason is not a word",
         [dict(_recorded([(13, "closed", A_REPO, "completed")])[0], state_reason=7)]),
        ("an item whose closed reason is the empty word",
         [dict(_recorded([(13, "closed", A_REPO, "completed")])[0], state_reason="  ")]),
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
    # ⚠️ And the two this host numbers from one rules out, on the argument as
    # well as on its own answer: `#0` and a negative name no item, and a negative
    # reaches the client as a flag rather than as an argument.
    for handed in (
        "not-a-number",
        True,
        1.9,
        " 11 ",
        "²",
        0,
        -13,
        "0",
        "-13",
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
    # ⚠️ One per shape the guard holds, the bool among them because it is an
    # `int` and passed a type test while naming no item.
    # ⚠️ And the two a host counting from one cannot mean: an answer of `0` or a
    # negative names no item, and either shaped into this item's identifier would
    # reach every path and every write composed from it.
    for label, answered in (
        ("carrying no number", {}),
        ("answering `true` for one", {"number": True}),
        ("answering zero", {"number": 0}),
        ("answering below zero", {"number": -13}),
    ):
        numberless = _Host({"issue view": dict({
            "title": "an answer with no number",
            "url": f"https://e.invalid/{A_REPO}/issues/{BLOCKED}",
            "state": "OPEN", "labels": [], "assignees": [], "body": "",
        }, **answered)})
        reported = with_host(
            numberless, lambda: unavailable(lambda: read_blockers(BLOCKED))
        )
        check(
            f"an answer {label} is a failed call, not a subscript on nothing",
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
    # ⛔ One per shape that carries no number it can read, the arm each falls out
    # of being its own. ⚠️ The mapping rows reached a `KeyError` and a
    # `ValueError` from the operation whose only stated failure is this refusal.
    refusals = {
        label: refused(lambda handed=handed: under_test.item_number(handed))
        for label, handed in (
            ("text that is no number", "not-a-number"),
            ("a mapping with no `number`", {}),
            ("a mapping whose `number` is a word", {"number": "abc"}),
            ("a bool", True),
            ("a value of another shape", 3.0),
            ("zero, which names no item on a host counting from one", 0),
            ("a negative", -13),
            ("a mapping carrying zero", {"number": 0}),
            ("text carrying a negative", "-13"),
        )
    }
    check(
        "and every shape carrying no readable number is refused, naming the operation",
        set(refusals.values()) == {"tracker.operations.item_number"},
        f"reported {refusals!r}",
    )
    composed = [ran(lambda handed=handed: under_test.link_for_close(handed))
                for handed in (14, "١١")]
    check(
        "the closing reference carries a number the host can resolve, not the argument",
        composed == ["Closes #14", "Closes #11"],
        f"composed {composed!r}",
    )
    check(
        "and names itself where what it was handed carries no number",
        refused(lambda: under_test.link_for_close("not-a-number"))
        == "tracker.operations.link_for_close",
        f"reported {refused(lambda: under_test.link_for_close('not-a-number'))!r}",
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

    # --- § 33's publishing half: the milestone, by title ----------------------
    #
    # ⛔ Addressed by **title** and never by number: § 4.8's value is the word on
    # the item, and this host's milestone number is its own. Every arm below is
    # about which object a call reaches, which is this suite's own scope.
    A_RELEASE = "a release"
    HELD = [
        {"title": A_RELEASE, "number": 3, "state": "open"},
        {"title": "another release", "number": 4, "state": "closed"},
    ]
    MILESTONE = {"carrier": "native_milestone", "name": "grouping"}

    def _with_milestones(held, *, listed=None, patched=None):
        answers = {"/milestones?state=all": list(held)}
        if listed is not None:
            answers["issue list"] = listed
        if patched is not None:
            answers["milestones/"] = patched
        return _Host(answers=answers)

    # ⛔ A carrier plain issues have no object for is a **defect in the text**,
    # refused with the key named -- `set_state`'s answer for a status word this
    # tracker cannot hold, one facet over. ⚠️ Both operations, because each
    # addresses the milestone and a guard on one would read as covering both.
    for operation, call in (
        ("grouping_items",
         lambda: under_test.grouping_items(A_RELEASE, grouping={"carrier": "label"})),
        ("mark_grouping_released",
         lambda: under_test.mark_grouping_released(
             A_RELEASE, grouping={"carrier": "label"})),
    ):
        where = with_host(_with_milestones(HELD), lambda: refused(call))
        check(
            f"`{operation}` on a carrier plain issues cannot hold is refused, "
            "naming the key",
            where == "work_item.grouping.carrier",
            f"reported {where!r}",
        )

    # ⛔ The listing is asked across **both** states, which is this host's own
    # trap: it defaults to the open ones, so a release already marked would come
    # back absent and read as *no such milestone* rather than as already closed.
    reading = _with_milestones(HELD, listed=[_issue(BLOCKED)])
    read = with_host(reading, lambda: under_test.grouping_items(
        "another release", grouping=MILESTONE))
    asked = [args for args in reading.sent if any("milestones" in a for a in args)]
    check(
        "the milestone listing is asked across both states, so a marked release is "
        "found rather than absent",
        bool(asked)
        and all("state=all" in " ".join(args) for args in asked)
        and read.get("value") == "another release",
        f"sent {asked!r}, read {read!r}",
    )
    # ⛔ And the items are asked for across both states too: a release held by an
    # item somebody closed by hand is still a fact about the release, and a set
    # narrowed to the open ones answers *nothing is short* for one whose every
    # item had moved.
    listed = [args for args in reading.sent if args[:2] == ["issue", "list"]]
    check(
        "the items in a milestone are asked for by its title, across both states",
        bool(listed)
        and all(
            "--milestone" in args
            and args[args.index("--milestone") + 1] == "another release"
            and "all" in args
            for args in listed
        ),
        f"sent {listed!r}",
    )
    # ⛔ A value no milestone answers to is refused **by name** and never answered
    # with an empty set: an empty set is what a release holding nothing looks
    # like, and § 33 reads a bar off that set.
    missing = with_host(
        _with_milestones(HELD, listed=[]),
        lambda: refused(
            lambda: under_test.grouping_items(
                "a release nothing holds", grouping=MILESTONE)
        ),
    )
    check(
        "a grouping value no milestone answers to is refused, not answered with an "
        "empty set",
        missing == "work_item.grouping",
        f"reported {missing!r}",
    )
    # ⛔ And an ambiguous fold is refused rather than resolved: closing the wrong
    # release is not recoverable, so two titles a project cannot tell apart stop
    # the ask.
    ambiguous = with_host(
        _with_milestones([
            {"title": "A Release", "number": 5, "state": "open"},
            {"title": "a release", "number": 6, "state": "open"},
        ]),
        lambda: refused(
            lambda: under_test.mark_grouping_released("A RELEASE", grouping=MILESTONE)
        ),
    )
    check(
        "two milestones one value folds onto is refused rather than resolved",
        ambiguous == "work_item.grouping",
        f"reported {ambiguous!r}",
    )
    # ⛔ The mark is a PATCH on the milestone's **own** number, which is the half
    # the title lookup exists to supply.
    marking = _with_milestones(
        HELD, patched={"title": A_RELEASE, "number": 3, "state": "closed"})
    marked = with_host(marking, lambda: under_test.mark_grouping_released(
        A_RELEASE, grouping=MILESTONE))
    wrote = [args for args in marking.sent if "PATCH" in args]
    check(
        "marking a release PATCHes the milestone's own number, and says it marked it",
        len(wrote) == 1
        and f"repos/{A_REPO}/milestones/3" in wrote[0]
        and "state=closed" in wrote[0]
        and marked.get("marked") is True
        and marked.get("already") is False,
        f"sent {wrote!r}, answered {marked!r}",
    )
    # ⛔ Idempotent by reading first, which is `set_state`'s rule at the one object
    # a deploy touches that is not an item: a run retried after a failure partway
    # through would otherwise write a release twice.
    again = _with_milestones(HELD)
    answered = with_host(again, lambda: under_test.mark_grouping_released(
        "another release", grouping=MILESTONE))
    check(
        "a release already marked is left alone and reported as already marked",
        not [args for args in again.sent if "PATCH" in args]
        and answered.get("marked") is False
        and answered.get("already") is True,
        f"sent {again.sent!r}, answered {answered!r}",
    )

    # --- § 39's bootstrap half: a milestone brought into existence ------------
    #
    # ⛔ A carrier plain issues have no object for is refused here as it is for the
    # two operations above, and it is asserted rather than assumed: this one
    # *writes*, so a guard that was there for the reads and not for the create
    # would be the half that matters.
    where = with_host(
        _with_milestones(HELD),
        lambda: refused(
            lambda: under_test.create_grouping(A_RELEASE, grouping={"carrier": "label"})
        ),
    )
    check(
        "`create_grouping` on a carrier plain issues cannot hold is refused, naming "
        "the key",
        where == "work_item.grouping.carrier",
        f"reported {where!r}",
    )
    # ⛔ A title no milestone answers to is POSTed, which is the one direction
    # `_held_milestone` exists to separate from the refusal the reads take.
    making = _with_milestones(
        HELD, patched={"title": "a new release", "number": 7, "state": "open"})
    making.answers["milestones"] = {"title": "a new release", "number": 7, "state": "open"}
    made = with_host(making, lambda: under_test.create_grouping(
        "a new release", grouping=MILESTONE))
    posted = [args for args in making.sent if "POST" in args]
    check(
        "a grouping no milestone answers to is POSTed and reported as created",
        len(posted) == 1
        and f"repos/{A_REPO}/milestones" in posted[0]
        and "title=a new release" in posted[0]
        and made.get("created") is True
        and made.get("already") is False,
        f"sent {posted!r}, answered {made!r}",
    )
    # ⛔ Idempotent by reading first, which is `mark_grouping_released`'s rule at
    # the same object: a run retried after a failure partway through would
    # otherwise create a second milestone under one title.
    # ⚠️ **The one already held is the `closed` one**, which is the arm that
    # matters: a create that reopened it would be making a release's own mark on
    # the strength of a name collision.
    standing = _with_milestones(HELD)
    found = with_host(standing, lambda: under_test.create_grouping(
        "another release", grouping=MILESTONE))
    check(
        "a grouping already held is answered as found, writing nothing and reopening "
        "nothing",
        not [args for args in standing.sent if "POST" in args or "PATCH" in args]
        and found.get("created") is False
        and found.get("already") is True
        and str(found.get("state")) == "closed",
        f"sent {standing.sent!r}, answered {found!r}",
    )
    # ⛔ And the ambiguous fold still refuses here, which is the whole reason the
    # absent answer is a value and the unnameable one is a refusal: a create that
    # caught both would answer *already there* about a grouping it cannot name.
    folded = with_host(
        _with_milestones([
            {"title": "A Release", "number": 5, "state": "open"},
            {"title": "a release", "number": 6, "state": "open"},
        ]),
        lambda: refused(
            lambda: under_test.create_grouping("A RELEASE", grouping=MILESTONE)
        ),
    )
    check(
        "a title two milestones fold onto is refused by `create_grouping` rather "
        "than read as already there",
        folded == "work_item.grouping",
        f"reported {folded!r}",
    )

    # --- the landed record: which change closed an item -----------------------
    #
    # ⛔ The **last** reference is the closing one and every reference comes back
    # beside it, which is the choice made once here rather than in each consumer.
    closed_by = _Host({"closedByPullRequestsReferences": {
        "data": {"repository": {"issue": {
            "state": "CLOSED",
            "closedByPullRequestsReferences": {"nodes": [
                {"number": 19, "merged": False, "mergeCommit": None},
                {"number": 20, "merged": True, "mergeCommit": {"oid": "abc1234"}},
            ]},
        }}},
    }})
    landed = with_host(closed_by, lambda: under_test.read_closing_change(BLOCKED))
    check(
        "the closing change is the last reference the host names, with its commit "
        "and every reference beside it",
        landed.get("change") == 20
        and landed.get("commit") == "abc1234"
        and landed.get("merged") is True
        and [one["change"] for one in landed.get("references") or []] == [19, 20],
        f"answered {landed!r}",
    )
    # ⛔ An item with no reference is a real answer and not an absence: the
    # capability is present and the host holds nothing, which is an item somebody
    # closed by hand. ⚠️ The state comes back either way, so a role can tell that
    # case from an open one.
    by_hand = _Host({"closedByPullRequestsReferences": {
        "data": {"repository": {"issue": {
            "state": "CLOSED",
            "closedByPullRequestsReferences": {"nodes": []},
        }}},
    }})
    unlinked = with_host(by_hand, lambda: under_test.read_closing_change(BLOCKED))
    check(
        "an item no change closed answers with no change rather than refusing",
        unlinked.get("change") is None
        and unlinked.get("commit") is None
        and unlinked.get("references") == []
        and unlinked.get("state") == "CLOSED",
        f"answered {unlinked!r}",
    )
    # ⛔ A merged reference the host gives no commit for is handed on as null and
    # never filled in from somewhere else: the commit is the host's, so a null
    # there is the host declining to answer.
    commitless = _Host({"closedByPullRequestsReferences": {
        "data": {"repository": {"issue": {
            "state": "CLOSED",
            "closedByPullRequestsReferences": {"nodes": [
                {"number": 21, "merged": True, "mergeCommit": None},
            ]},
        }}},
    }})
    partial = with_host(commitless, lambda: under_test.read_closing_change(BLOCKED))
    check(
        "a merged change the host gives no commit for is reported as it reads",
        partial.get("change") == 21
        and partial.get("merged") is True
        and partial.get("commit") is None,
        f"answered {partial!r}",
    )
    # ⛔ Read through the guard, so a pull request number is refused before the
    # query -- the number this operation is keyed on naming the wrong object is
    # the one way its answer is wrong and reads right.
    as_change = _Host(issues={
        BLOCKED: dict(_issue(BLOCKED), url=f"https://e.invalid/{A_REPO}/pull/{BLOCKED}"),
    })
    with_host(as_change,
              lambda: unavailable(lambda: under_test.read_closing_change(BLOCKED)))
    check(
        "a pull request is refused before the closing change is asked for",
        not [args for args in as_change.sent if "graphql" in " ".join(args)],
        f"sent {as_change.sent!r}",
    )

    # --- the vocabularies this tracker states, before a configuration --------
    #
    # ⛔ Three decisions, each silent if it is wrong: the status pair is this
    # host's own and is **not** a call, a label listing that did not answer is
    # unestablished rather than a repository with no labels, and the type
    # vocabulary is unestablished rather than `none` -- this host stating it
    # above the repository, where there is no read here that answers for one.
    labelled = _Host({"label list": [{"name": "P: Highest"}, {"name": "infra"}]})
    vocabulary = with_host(labelled, read_vocabulary) or {}
    statuses = vocabulary.get("statuses") or {}
    labels = vocabulary.get("labels") or {}
    types = vocabulary.get("types") or {}
    check(
        "the status words are the host's own two, read without asking the host",
        statuses.get("answer") == port.VOCABULARY_READ
        and statuses.get("values") == ["open", "closed"],
        f"answered {statuses!r}",
    )
    check(
        "the label set is this repository's own, read through the client",
        labels.get("answer") == port.VOCABULARY_READ
        and labels.get("values") == ["P: Highest", "infra"]
        and labelled.calls.count("label list") == 1,
        f"answered {labels!r} after {labelled.calls!r}",
    )
    check(
        "the type vocabulary is unestablished rather than `none`",
        types.get("answer") == port.VOCABULARY_UNESTABLISHED
        and types.get("values") is None,
        f"answered {types!r}",
    )
    # ⛔ And the two directions a label listing can be empty, which § 2's rule is
    # exactly about: a repository with no label at all, and a host that did not
    # answer. ⚠️ Both read as `values: []`-shaped to a caller that only looked at
    # the list, which is why the answer word is what a consumer reads.
    bare = _Host({"label list": []})
    reading = (with_host(bare, read_vocabulary) or {}).get("labels") or {}
    check(
        "a repository with no label at all is stated rather than unestablished",
        reading.get("answer") == port.VOCABULARY_NONE and reading.get("values") == [],
        f"answered {reading!r}",
    )
    silent = _Host({"label list": HostUnavailable("the host did not answer")})
    reading = (with_host(silent, read_vocabulary) or {}).get("labels") or {}
    check(
        "a host that did not answer leaves the labels unestablished, not empty",
        reading.get("answer") == port.VOCABULARY_UNESTABLISHED
        and reading.get("values") is None,
        f"answered {reading!r}",
    )
    check(
        "and the statuses still answer, not depending on that call",
        ((with_host(silent, read_vocabulary) or {}).get("statuses") or {}).get(
            "answer") == port.VOCABULARY_READ,
        "the status reading was taken down with the label call",
    )
    # ⛔ And the same for a slug this adapter refuses: a configuration's own
    # refusal is a reason the labels are unestablished, not a reason the whole
    # read fails. ⚠️ Rebound here and put back below, since the refusal is
    # `_repo`'s and comes from the bound configuration rather than from the host.
    bind({"host.repo": "not-a-slug"})
    reading = (with_host(labelled, read_vocabulary) or {})
    check(
        "a slug this adapter cannot address leaves the labels unestablished",
        (reading.get("labels") or {}).get("answer")
        == port.VOCABULARY_UNESTABLISHED
        and (reading.get("statuses") or {}).get("answer") == port.VOCABULARY_READ,
        f"answered {reading!r}",
    )
    bind({"host.repo": A_REPO})

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
