#!/usr/bin/env python3
"""The card implementation's suite: the shapes it was written against, as code.

⛔ **A module of its own rather than a mode of the implementation**, for the
reason the board implementation's suite records: a single file carrying both
reaches the code host with no patch, and the gate that holds every added line to
the deferral rule refuses a change it cannot read. ⚠️ The name opens with `_` so
that discovery skips it -- a module in the port's `adapters/` package that names
no kind is refused rather than skipped, which is right for an implementation and
wrong for a suite.

What it holds, and what it cannot reach, are recorded in
`docs/single-source-of-truth.md` § Beside the contract. Nothing here restates
them.

The implementation is imported by **name** for everything the cases call, and
through the **module** for the one seam they substitute: rebinding a name this
module imported would leave the implementation calling its own.
"""

from __future__ import annotations

import json
import os
import re
import sys

_SUITE_SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SUITE_SCRIPTS not in sys.path:
    sys.path.append(_SUITE_SCRIPTS)

import config  # noqa: E402
import port  # noqa: E402
from config import ConfigError  # noqa: E402
from port import HostUnavailable  # noqa: E402

from adapters import trello as under_test  # noqa: E402
from adapters.trello import (  # noqa: E402
    ADAPTER,
    ARCHIVED,
    COLLECTION_CEILING,
    DELIBERATELY_ABSENT,
    KEY_VARIABLE,
    KIND,
    OPEN,
    OWNED_ELSEWHERE,
    QUERYABLE,
    START_OF_DAY,
    TOKEN_VARIABLE,
    WRITABLE,
    _boards,
    assign,
    bind,
    checklist_item_delete,
    checklist_read,
    checklist_write,
    comment,
    create_item,
    forbidden,
    item_number,
    matches,
    policy_classes,
    read_item,
    search_items,
    set_field,
    set_labels,
    set_state,
)

# What the suite puts in the shell so a call can be made at all, and ⛔ what no
# message may contain. The values are recognisable on purpose: one case fails a
# call and reads the message for them, because a report that quotes the
# credential publishes it to the one surface the report is read on (§ 14).
A_KEY = "KEY-VALUE-THAT-MUST-NOT-APPEAR"
A_TOKEN = "TOKEN-VALUE-THAT-MUST-NOT-APPEAR"

# The parameters a write carries that reach the **card** rather than the
# address. ⛔ The distinction is the whole of the last acceptance item: a policy
# bars what a card holds, and the path a call is made to is not something a card
# holds -- a URL path matches the file-path grammar by construction, so an
# assertion sweeping paths would redden on every call this module makes.
TEXT_PARAMETERS = ("name", "desc", "text")


# --- the fixtures ------------------------------------------------------------


def _example_configuration():
    """The shipped example for this kind, as the fixture.

    ⛔ Named from `KIND` rather than spelled: this package is the one place a
    tracker's name belongs, and the example beside it is the configuration a
    project of this kind actually writes -- a hand-built fixture here would be a
    second statement of the same block, allowed to disagree with it.
    """
    path = os.path.join(config.EXAMPLES, f"{KIND}.yaml")
    with open(path, encoding="utf-8") as handle:
        return config.load_text(handle.read(), config.EXAMPLES)


def _status_names(configuration) -> list[str]:
    return [str(status.get("name")) for status in configuration.get("statuses") or []]


def _role_status(configuration, role: str) -> str | None:
    for status in configuration.get("statuses") or []:
        if status.get("role") == role:
            return str(status.get("name"))
    return None


def _lists_for(configuration) -> list[dict]:
    """The board's lists, named from the example's own `statuses`.

    ⛔ Derived rather than written: a state here **is** a list, so the fixture's
    lists are the status words the shipped example states. A hand-written set
    would stop matching the day the example is reworded, and the suite would be
    resolving names no project writes.
    """
    return [
        {"id": f"list-{index}", "name": name, "closed": False, "pos": index * 100}
        for index, name in enumerate(_status_names(configuration))
    ]


LABELS = [
    {"id": "label-alpha", "name": "alpha", "color": "green"},
    {"id": "label-beta", "name": "beta", "color": "blue"},
    {"id": "label-gamma", "name": "gamma", "color": "red"},
]

MEMBERS = [{"id": "member-me", "username": "whoever", "fullName": "Who Ever"}]


def _card(
    number: int,
    name: str,
    *,
    in_list: str = "list-0",
    labels: list[str] | None = None,
    members: list[str] | None = None,
    closed: bool = False,
    short: bool = True,
) -> dict:
    """One card as the host answers it in a collection.

    ⛔ Carries the whole production shape rather than only what the code reads.
    ⚠️ `short=False` drops the short-id field, which is the answer one real
    interface over this tracker gives and the arm `item_number` parses the URL
    for -- a fixture that always carried the field would leave that arm
    unreachable while reading green.

    ⛔ **The URL's host is one that resolves nowhere, and the gate in `tools/`
    decided that rather than taste**: a card URL on the tracker's own host reads
    as an identifier that resolves on somebody's board, which is that project's
    fact and never this repository's. ⚠️ Measured on this file -- the first draft
    carried a real short link read off a live board, and the sweep named the line.
    What the cases are about is the **shape** `/c/<link>/<number>-<slug>`, which
    survives the host being changed.
    """
    card = {
        "id": f"card-{number}",
        "name": name,
        "desc": f"what card {number} is",
        "closed": closed,
        "idList": in_list,
        "idLabels": list(labels or []),
        "idMembers": list(members or []),
        "url": f"https://example.invalid/c/aaaa{number:04d}/{number}-a-card",
        "shortUrl": f"https://example.invalid/c/aaaa{number:04d}",
        "due": None,
        "dueComplete": False,
    }
    if short:
        card["idShort"] = number
    return card


CHECK_ITEMS = [
    {"id": "item-1", "name": "the first thing", "state": "incomplete", "pos": 1},
    {"id": "item-2", "name": "the second thing", "state": "complete", "pos": 2},
]

CHECKLISTS = [
    {"id": "checklist-1", "name": "acceptance", "pos": 1, "checkItems": CHECK_ITEMS}
]


# --- the host, as one seam ---------------------------------------------------
#
# ⛔ Routes in order, longest first where one path prefixes another. ⚠️ That
# ordering is a rule about this fake and is asserted below: `PUT /cards/<id>` and
# `PUT /cards/<id>/checkItem/<id>` differ only in a suffix, and a fake that
# matched the shorter one first would answer a tick as a card update -- the same
# shadowing the board implementation's suite records between `Item` and `Items`.

ROUTES = [
    ("GET", r"^/boards/[^/]+/lists$", "lists"),
    ("GET", r"^/boards/[^/]+/labels$", "labels"),
    ("GET", r"^/boards/[^/]+/members$", "members"),
    ("GET", r"^/boards/[^/]+/cards/all$", "cards"),
    ("GET", r"^/cards/[^/]+/checklists$", "checklists"),
    ("GET", r"^/cards/[^/]+$", "card"),
    ("POST", r"^/cards$", "create"),
    ("POST", r"^/cards/[^/]+/actions/comments$", "comment"),
    ("POST", r"^/cards/[^/]+/idMembers$", "add member"),
    ("PUT", r"^/cards/[^/]+/checkItem/[^/]+$", "tick"),
    ("PUT", r"^/cards/[^/]+$", "update"),
    ("DELETE", r"^/cards/[^/]+/idLabels/[^/]+$", "detach label"),
    ("GET", r"^/members/[^/]+$", "me"),
    ("POST", r"^/checklists$", "new checklist"),
    ("POST", r"^/checklists/[^/]+/checkItems$", "add item"),
    ("DELETE", r"^/checklists/[^/]+/checkItems/[^/]+$", "delete item"),
]


def route(method: str, path: str) -> str | None:
    for verb, pattern, name in ROUTES:
        if verb == method and re.match(pattern, path):
            return name
    return None


class _Host:
    """A transport that answers as the host does, and records what was asked.

    ⛔ A fake rather than a mock: it answers by **which route was called**
    rather than by the order this module happens to call in, so a refactor that
    reorders calls does not redden it and a call that moves to the wrong object
    does.

    ⛔ **It answers every route the host would**, and a case states only what it
    wants to differ. The board implementation's suite paid for that rule twice:
    a fake carrying only the calls the passing path makes turns a deliberate
    break into a traceback inside the operation, so an assertion about *what was
    called* dies before it can report and the case reads as green.
    """

    def __init__(self, configuration, answers: dict | None = None):
        self.configuration = configuration
        self.answers = dict(answers or {})
        self.calls: list[str] = []
        self.sent: list[tuple[str, dict]] = []

    def index(self) -> list[dict]:
        """The cards the board answers with, whether a case overrode them or not.

        ⛔ Read by the single-card route as well, so the two always agree. ⚠️
        Measured on this suite: a `card` default that built its own answer
        contradicted the index a case had overridden, so an archived card read
        back open and the assertion about it was green against the fake rather
        than against the module.
        """
        return self.answers.get("cards", [
            _card(1, "a first card", labels=["label-beta"]),
            _card(2, "a second card", in_list="list-1"),
            _card(3, "an archived card", closed=True),
        ])

    def _one_card(self, path: str, _params: dict) -> dict:
        wanted = path.split("/")[2]
        for card in self.index():
            if card["id"] == wanted:
                return card
        raise AssertionError(
            f"this suite's host was asked for `{wanted}`, which its own index does "
            "not hold -- the fake's two answers about one card disagree"
        )

    def defaults(self) -> dict:
        return {
            "lists": _lists_for(self.configuration),
            "labels": LABELS,
            "members": MEMBERS,
            "cards": self.index(),
            "card": self._one_card,
            "checklists": CHECKLISTS,
            "create": _card(4, "a filed card"),
            "comment": {"id": "action-1"},
            "add member": {"id": "card-1"},
            "tick": {"id": "item-1"},
            "update": {"id": "card-1"},
            "detach label": "",
            "me": MEMBERS[0],
            "new checklist": {"id": "checklist-2", "name": "acceptance"},
            "add item": {"id": "item-3", "name": "a new thing", "state": "incomplete"},
            "delete item": {"_value": {}},
        }

    def __call__(self, method: str, path: str, params: dict) -> tuple[int, str]:
        name = route(method, path)
        if name is None:
            raise AssertionError(
                f"this suite's host was called as `{method} {path}`, which no route "
                "of it names -- a call that moved to another object, or a route the "
                "fake has not grown yet"
            )
        self.calls.append(name)
        self.sent.append((name, dict(params)))
        answer = self.answers.get(name, self.defaults()[name])
        if callable(answer):
            answer = answer(path, params)
        if isinstance(answer, tuple):
            return answer
        if isinstance(answer, str):
            return 200, answer
        return 200, json.dumps(self._narrowed(answer, params))

    @staticmethod
    def _narrowed(answer, params: dict):
        """The answer cut to the fields the call asked for, as the host cuts it.

        ⛔ Not fidelity for its own sake: `fields=` is load-bearing here, because
        the index this board is searched through deliberately does **not** ask
        for a description and the answer's shape is what says so. ⚠️ Measured on
        this suite -- a fake that answered the whole card made the assertion
        about an unread field unholdable, and it read green against the fixture.

        `checkItems` is kept where the call asked for it: it is a nested
        collection of its own rather than one of `fields`.
        """
        wanted = str(params.get("fields") or "").split(",")
        wanted = {name for name in wanted if name}
        if not wanted:
            return answer
        if params.get("checkItems"):
            wanted.add("checkItems")

        def cut(node):
            if not isinstance(node, dict):
                return node
            return {key: value for key, value in node.items() if key in wanted}

        return [cut(node) for node in answer] if isinstance(answer, list) else cut(answer)

    def writes(self) -> list[str]:
        reads = {"lists", "labels", "members", "cards", "card", "checklists", "me"}
        return [call for call in self.calls if call not in reads]

    def params_for(self, name: str) -> list[dict]:
        return [params for called, params in self.sent if called == name]


# --- what a planted span is, per class --------------------------------------
#
# ⛔ One plant per class the surface states, and a green-side plant beside them:
# an exemption with nothing asserted to stay green is a guard that could be
# refusing everything and reading as correct.

PLANTS = {
    "source_code": "the fix is\n\n```python\nreturn 1\n```\n",
    "file_paths": "it is in plugins/mjolnir/scripts/adapters/trello.py",
    "hosting_details": "reachable at https://internal.example.invalid/admin",
    "branch_names": "landed on feat/5-a-thing yesterday",
}

# ⚠️ Assembled rather than written as a literal, for the reason § 14's own arm
# assembles its plants: a file carrying a token-shaped literal is a secret
# committed by the check that exists to stop that, and the host's own push
# protection refuses the push.
PLANTS["credentials"] = "the key is " + "gh" + "p_" + ("A" * 36)

STAYS_GREEN = (
    "The gate went red on the second predicate, so the card stays where it is "
    "and the person who wrote it has one thing to fix rather than four."
)


# --- self-test ---------------------------------------------------------------


def self_test() -> int:
    failures = 0

    def check(label: str, condition: bool, detail: str = "") -> None:
        nonlocal failures
        if condition:
            print(f"  ok    {label}")
        else:
            failures += 1
            print(f"  FAIL  {label}{': ' + detail if detail else ''}")

    # ⛔ All three helpers catch **everything**, each reporting the other
    # outcomes as themselves rather than letting them out. A deliberate break
    # that made an operation raise the other kind of exception killed the run on
    # a traceback where a verdict belongs -- the defect the port's own suite
    # records, and the reason this gate must always print a count.
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
        was = under_test.TRANSPORT
        under_test.TRANSPORT = host
        try:
            return ran(call)
        finally:
            under_test.TRANSPORT = was

    # ⛔ Four readers, and none of these is a convenience. Every one of them
    # exists because a **break** proved the direct form ends the run instead of
    # reporting: a value computed inside an assertion raises where the
    # comparison is written, and `ran` hands back a dict naming what was raised
    # -- which is a dict, so a direct subscript on it raises in turn. ⚠️
    # Measured by removing `item_number`'s URL arm: the suite exited non-zero
    # having printed no failure at all, which is the one shape this gate must
    # never take.

    def number(item):
        """`item_number`'s answer, with a refusal reported as a value."""
        try:
            return item_number(item)
        except Exception as error:
            return f"<{type(error).__name__}: {error}>"

    def got(answer, key, default=None):
        """One key out of an operation's answer, or `default` where it failed."""
        return answer.get(key, default) if isinstance(answer, dict) else default

    def entries(answer) -> list:
        return got(answer, "items") or []

    def sent(host, name) -> dict:
        """The parameters of the first call to a route, or `{}` where none was made."""
        made = host.params_for(name)
        return made[0] if made else {}

    # The shell this suite runs its calls in. ⛔ Set here and restored at the
    # end: `_credentials` reads the environment, so without this every case
    # below would be asserting the same missing-variable failure.
    was_environment = {
        name: os.environ.get(name) for name in (KEY_VARIABLE, TOKEN_VARIABLE)
    }
    os.environ[KEY_VARIABLE], os.environ[TOKEN_VARIABLE] = A_KEY, A_TOKEN

    try:
        configuration = _example_configuration()
        broken = None
    except Exception as error:  # the example is this suite's one input
        configuration, broken = None, f"{type(error).__name__}: {error}"
    check(f"the shipped example for `{KIND}` loads", configuration is not None, broken or "")
    if configuration is None:
        print(f"\n{failures} assertion(s) did not hold.")
        return 1
    check(
        "and states this kind, so the fixture is the configuration a project writes",
        configuration.tracker_kind == KIND,
        f"states {configuration.tracker_kind!r}",
    )
    bind(configuration)
    _boards.clear()

    def host(answers: dict | None = None) -> _Host:
        _boards.clear()
        return _Host(configuration, answers)

    # ⛔ The status words and the list ids these cases move between are read off
    # the example and the fixture derived from it, never written here: a state is
    # a list, so a literal would be a third statement of the same names and
    # would rot the day the example is reworded.
    board_lists = _lists_for(configuration)
    initial = _role_status(configuration, "initial")
    second = board_lists[1]["name"] if len(board_lists) > 1 else None
    check(
        "the example states an `initial` role and a second list to advance into",
        bool(initial) and bool(second) and initial != second,
        f"states initial={initial!r}, second={second!r}",
    )
    if not (initial and second):
        print(f"\n{failures} assertion(s) did not hold.")
        return 1

    # --- the operation list, against the surface the port reads -------------
    stated = port.surface_operations()
    check(
        "every operation the surface states is implemented or deliberately absent",
        set(stated) - set(ADAPTER.operations) == set(DELIBERATELY_ABSENT),
        "unimplemented and unaccounted for: "
        f"{sorted(set(stated) - set(ADAPTER.operations) - set(DELIBERATELY_ABSENT))}",
    )
    check(
        "and nothing is implemented that the surface does not state",
        not set(ADAPTER.operations) - set(stated),
        f"implements {sorted(set(ADAPTER.operations) - set(stated))}",
    )
    # ⚠️ Compared by the operations it declares rather than by identity: under
    # `--self-test` this module runs as `__main__` and discovery imports it a
    # second time as a package member, so the two `ADAPTER` objects are
    # different objects stating the same thing.
    # ⛔ Read through `check`, not beside it. Discovery refuses a module in the
    # package it cannot import, so a stray file beside this one takes the
    # registry down -- and an uncaught refusal here ends the run on a traceback
    # where the verdict and the count belong. ⚠️ Measured on this suite: a
    # scratch file left in `adapters/` killed every assertion after this line
    # and the run reported no failures at all, which is the one shape every
    # check in this repository is written against.
    try:
        discovered, unresolved = port.Port(configuration).adapter, None
    except ConfigError as error:
        discovered, unresolved = None, str(error)
    check(
        "the port resolves an implementation of this kind, declaring these operations",
        discovered is not None
        and discovered is not port.TRACKERLESS
        and sorted(discovered.operations) == sorted(ADAPTER.operations),
        unresolved or f"resolved {discovered!r}",
    )
    # ⛔ The three checklist operations are **present** here, which is the one
    # claim about this implementation that cannot be read off the absence list:
    # both implementations beside it leave them absent, so until now the stated
    # fallbacks were the only behaviour anything had.
    check(
        "the three checklist operations are implemented, which no other kind does",
        all(
            name in ADAPTER.operations
            for name in ("checklist_read", "checklist_write", "checklist_item_delete")
        ),
    )

    # The first acceptance item: each absent operation produces its stated
    # fallback and no error. ⛔ Asked through the port rather than of the module,
    # because the fallback text is the surface's and the port is what resolves
    # it -- a case that checked the names alone would prove nothing about what a
    # role meeting one is told.
    absent_port = port.Port(configuration, adapter=ADAPTER, stated=stated)
    outcomes = {name: absent_port.invoke(name) for name in DELIBERATELY_ABSENT}
    check(
        "each absent operation comes back as the surface's stated fallback",
        all(
            not outcome.performed
            and not outcome.failed
            and outcome.detail == stated[name]
            for name, outcome in outcomes.items()
        ),
        f"got {[str(outcome) for outcome in outcomes.values()]!r}",
    )
    check(
        "and the capability query answers no for each of them",
        not any(absent_port.implements(name) for name in DELIBERATELY_ABSENT),
    )
    check(
        "while every operation this tracker does have reads as present",
        all(absent_port.implements(name) for name in ADAPTER.operations),
    )

    # --- the number: the field, then the URL --------------------------------
    check("an int is the number, with no host call to make it one", number(7) == 7)
    short_and_url = {"idShort": 42, "url": "https://example.invalid/c/abc/99-x"}
    check(
        "a card carrying a short id answers from the field, not from its URL",
        number(short_and_url) == 42,
        f"read {number(short_and_url)!r}",
    )
    # ⚠️ The measured shape: a card whose title is not ASCII has a
    # percent-encoded slug, and one real interface over this tracker answers a
    # card with no short-id field at all.
    cyrillic = {
        "url": "https://example.invalid/c/aShortLink/75-%D0%B4%D0%B0%D1%88%D0%B1%D0%BE%D1%80%D0%B4"
    }
    check(
        "a card with no short id has its number parsed out of the URL",
        number(cyrillic) == 75,
        f"read {number(cyrillic)!r}",
    )
    digits = {"url": "https://example.invalid/c/abc1234/75-2026-plan"}
    check(
        "and a slug that opens with digits of its own does not displace it",
        number(digits) == 75,
        f"read {number(digits)!r}",
    )
    link_only = {"shortUrl": "https://example.invalid/c/abc1234/8"}
    check(
        "the short link alone answers too, which is the narrowed read's shape",
        number(link_only) == 8,
        f"read {number(link_only)!r}",
    )
    reported = refused(lambda: item_number({"id": "card-1"}))
    check(
        "a card carrying neither is refused, naming the operation",
        reported == "tracker.operations.item_number",
        f"reported {reported!r}",
    )
    silent = host()
    with_host(silent, lambda: (item_number(7), item_number({"idShort": 8})))
    check("and none of that reaches the host", silent.calls == [], f"called {silent.calls}")

    # --- the board, resolved by name, once ----------------------------------
    reading = host()
    item = with_host(reading, lambda: read_item(1))
    check(
        "a card's status is the list it is in, which is this tracker's state vocabulary",
        isinstance(item, dict) and item.get("status") == initial,
        f"read {item!r}",
    )
    check(
        "and whether it is archived is reported apart, never as the status",
        item.get("state") == OPEN,
        f"read {item.get('state')!r}",
    )
    archived = with_host(host(), lambda: read_item(3))
    check(
        "an archived card says so and keeps the list it was in",
        archived.get("state") == ARCHIVED and archived.get("status") == initial,
        f"read {archived.get('state')!r} in {archived.get('status')!r}",
    )
    check(
        "the checklists are read in a call of their own, not nested into the card",
        reading.calls.count("checklists") == 1 and reading.calls.count("card") == 1,
        f"called {reading.calls}",
    )
    check(
        "a label the card carries is resolved to its name from the board's own answer",
        [label.get("name") for label in (got(item, "labels") or [])] == ["beta"],
        f"read {item['labels']!r}",
    )
    stale = host({"cards": [_card(1, "a first card", labels=["label-gone"])]})
    item = with_host(stale, lambda: read_item(1))
    check(
        "a label id the board's list does not carry is kept and named unresolved",
        (got(item, "labels") or []) == [{"id": "label-beta", "name": "beta", "color": "blue"}]
        or (got(item, "labels") or [])[0].get("unresolved") is True,
        f"read {item['labels']!r}",
    )
    twice = host()
    with_host(twice, lambda: (read_item(1), read_item(2)))
    check(
        "a board resolved once is not resolved again for the same address",
        twice.calls.count("lists") == 1 and twice.calls.count("cards") == 1,
        f"called {twice.calls}",
    )

    # A name that does not resolve re-reads the board once before refusing,
    # because a list added after this process started is absent from an index
    # built before it existed.
    rereading = host()
    with_host(rereading, lambda: refused(lambda: set_state(1, status="no such list")))
    check(
        "a list name that does not resolve re-reads the board once, then refuses",
        rereading.calls.count("lists") == 2,
        f"called {rereading.calls}",
    )
    reported = with_host(
        host(), lambda: refused(lambda: set_state(1, status="no such list"))
    )
    check(
        "and the refusal names `statuses`, which is where a status word comes from",
        reported == "statuses",
        f"reported {reported!r}",
    )
    ambiguous = host(
        {"lists": _lists_for(configuration) + [
            {"id": "list-twin", "name": initial, "closed": False, "pos": 999}
        ]}
    )
    reported = with_host(ambiguous, lambda: refused(lambda: set_state(1, status=initial)))
    check(
        "a list name two lists carry is refused rather than resolved by position",
        reported == "statuses" and not ambiguous.writes(),
        f"reported {reported!r} after {ambiguous.calls}",
    )

    # The ceiling: an answer that fills it is refused rather than returned short.
    at_ceiling = host(
        {"cards": [_card(n, f"card {n}") for n in range(1, COLLECTION_CEILING + 1)]}
    )
    reported = with_host(at_ceiling, lambda: unavailable(lambda: read_item(1)))
    check(
        "a collection answering at the host's ceiling is refused, never returned short",
        reported is not None and "refused rather than" in reported,
        f"got {reported!r}",
    )
    below = host({"cards": [_card(n, f"card {n}") for n in range(1, COLLECTION_CEILING)]})
    answered = with_host(below, lambda: read_item(1))
    check(
        "while one node below it is an answer, so the guard is the ceiling and not the size",
        isinstance(answered, dict) and answered.get("number") == 1,
        f"got {answered!r}",
    )

    missing = host()
    reported = with_host(missing, lambda: unavailable(lambda: read_item(99)))
    check(
        "a number the board does not hold is refused, naming the board it is relative to",
        reported is not None and "relative to its board" in reported,
        f"got {reported!r}",
    )
    check(
        "after one re-read, which is what a card filed seconds ago needs",
        missing.calls.count("cards") == 2,
        f"called {missing.calls}",
    )

    # --- `set_state`: the list, by name, read before written ----------------
    moved = host()
    with_host(moved, lambda: set_state(1, status=second))
    check(
        "an advance reads the card before it writes the list",
        "update" in moved.calls and moved.calls.index("cards") < moved.calls.index("update"),
        f"called {moved.calls}",
    )
    check("and writes once", moved.calls.count("update") == 1, f"called {moved.calls}")
    check(
        "carrying the list's own id, read from the board rather than composed",
        sent(moved, "update").get("idList") == board_lists[1]["id"],
        f"sent {moved.params_for('update')!r}",
    )
    already = host()
    with_host(already, lambda: set_state(1, status=initial))
    check(
        "an advance to the list the card is already in writes nothing",
        not already.writes(),
        f"called {already.calls}",
    )

    # --- `create_item`: the list the `initial` role maps to ------------------
    filed = host()
    created = with_host(filed, lambda: create_item("a title", "a body", ["alpha", "beta", "gamma"]))
    check(
        "a filing creates the card in the list the `initial` role maps to",
        sent(filed, "create").get("idList") == "list-0",
        f"sent {filed.params_for('create')!r}",
    )
    # The second acceptance item. ⛔ Read back off the card rather than off the
    # request: a create that was *sent* three labels and came back with two is
    # the failure this item is about, and a case reading the request alone would
    # have called it correct.
    created_labels = host({
        "create": _card(4, "a filed card", labels=["label-alpha", "label-beta", "label-gamma"]),
        "cards": [_card(4, "a filed card", labels=["label-alpha", "label-beta", "label-gamma"])],
        "card": _card(4, "a filed card", labels=["label-alpha", "label-beta", "label-gamma"]),
    })
    created = with_host(
        created_labels, lambda: create_item("a title", "a body", ["alpha", "beta", "gamma"])
    )
    check(
        "a card created with three labels comes back carrying three labels",
        isinstance(created, dict)
        and sorted(label["name"] for label in (got(created, "labels") or [])) == ["alpha", "beta", "gamma"],
        f"read {created!r}",
    )
    check(
        "set in one call, with the three ids read from the board",
        created_labels.calls.count("create") == 1
        and sorted(str(sent(created_labels, "create").get("idLabels", "")).split(","))
        == ["label-alpha", "label-beta", "label-gamma"],
        f"sent {created_labels.params_for('create')!r}",
    )
    # The third acceptance item, on the arm that makes it bite: the create's own
    # answer carries no short id, so the number comes out of the URL.
    no_short = host({
        "create": _card(4, "a filed card", short=False),
        "cards": [_card(4, "a filed card")],
    })
    created = with_host(no_short, lambda: create_item("a title", "a body"))
    check(
        "the number of a created card is recovered where its answer carries no short id",
        isinstance(created, dict) and created.get("number") == 4,
        f"read {created!r}",
    )
    short_lived = host({
        "create": _card(4, "a filed card", labels=["label-alpha"]),
        "cards": [_card(4, "a filed card")],
        "card": _card(4, "a filed card"),
    })
    reported = with_host(
        short_lived, lambda: unavailable(lambda: create_item("a title", "a body", ["alpha"]))
    )
    check(
        "a create that came back short of its labels is reported, naming them",
        reported is not None and "alpha" in reported and "did not land" in reported,
        f"got {reported!r}",
    )
    check(
        "and is never retried, because a second create would file the work twice",
        short_lived.calls.count("create") == 1,
        f"called {short_lived.calls}",
    )
    no_initial = _example_configuration()
    no_initial.data["statuses"] = [
        status for status in no_initial.data["statuses"] if status.get("role") != "initial"
    ]
    bind(no_initial)
    stateless = host()
    reported = with_host(stateless, lambda: refused(lambda: create_item("a title", "a body")))
    check(
        "a project mapping no `initial` role cannot file here, and is refused naming `statuses`",
        reported == "statuses" and "create" not in stateless.calls,
        f"reported {reported!r} after {stateless.calls}",
    )
    bind(configuration)

    # --- `set_labels`: set, not union, and the one arm that degrades ---------
    relabelled = host()
    with_host(relabelled, lambda: set_labels(1, ["alpha"]))
    check(
        "a set of labels is written whole, so what the card carried is not kept",
        sent(relabelled, "update").get("idLabels") == "label-alpha",
        f"sent {relabelled.params_for('update')!r}",
    )
    same = host()
    with_host(same, lambda: set_labels(1, ["beta"]))
    check(
        "the set the card already carries writes nothing",
        not same.writes(),
        f"called {same.calls}",
    )
    cleared = host({
        "cards": [_card(1, "a first card", labels=["label-alpha", "label-beta"])],
        "card": _card(1, "a first card"),
    })
    with_host(cleared, lambda: set_labels(1, []))
    check(
        "the empty set is written as one removal per label rather than as an empty array",
        cleared.calls.count("detach label") == 2 and "update" not in cleared.calls,
        f"called {cleared.calls}",
    )
    partial = host({
        "cards": [_card(1, "a first card", labels=["label-alpha"])],
        "card": _card(1, "a first card", labels=["label-alpha"]),
    })
    reported = with_host(partial, lambda: unavailable(lambda: set_labels(1, [])))
    check(
        "a removal that left the set partial is reported rather than retried",
        reported is not None and "partial" in reported,
        f"got {reported!r}",
    )
    unknown = host()
    reported = with_host(unknown, lambda: refused(lambda: set_labels(1, ["no such label"])))
    check(
        "a label name the board does not have is refused, never written",
        reported == "tracker.operations.set_labels" and not unknown.writes(),
        f"reported {reported!r} after {unknown.calls}",
    )

    # --- `set_field`: the field's own shape decides the value ---------------
    dated = host()
    with_host(dated, lambda: set_field(1, "due", "2026-10-22"))
    check(
        "a date field is sent as the start of that day, which is the one time not invented",
        sent(dated, "update").get("due") == f"2026-10-22{START_OF_DAY}",
        f"sent {dated.params_for('update')!r}",
    )
    loose = host()
    reported = with_host(loose, lambda: refused(lambda: set_field(1, "due", "tomorrow")))
    check(
        "a date that is not § 4.5's form is refused naming the field, before any write",
        reported == "tracker.fields.due" and not loose.writes(),
        f"reported {reported!r} after {loose.calls}",
    )
    flagged = host()
    reported = with_host(flagged, lambda: refused(lambda: set_field(1, "dueComplete", "yes")))
    check(
        "a word handed to a flag field is refused rather than read as true",
        reported == "tracker.fields.dueComplete" and not flagged.writes(),
        f"reported {reported!r}",
    )
    ok_flag = host()
    with_host(ok_flag, lambda: set_field(1, "dueComplete", True))
    check(
        "while a flag itself is written",
        sent(ok_flag, "update").get("dueComplete") == "true",
        f"sent {ok_flag.params_for('update')!r}",
    )
    for field, owner in OWNED_ELSEWHERE.items():
        reported = with_host(host(), lambda field=field: refused(lambda: set_field(1, field, "x")))
        check(
            f"`{field}` is refused for a write, naming what owns it",
            reported == f"tracker.fields.{field}",
            f"reported {reported!r}",
        )
    reported = with_host(host(), lambda: refused(lambda: set_field(1, "Story points", 3)))
    check(
        "a field the card does not have is refused, naming what it would need",
        reported == "tracker.fields.Story points",
        f"reported {reported!r}",
    )
    check(
        "and every field this module calls writable has a shape to write it in",
        set(WRITABLE) and not set(WRITABLE) & set(OWNED_ELSEWHERE),
        f"writable {sorted(WRITABLE)} overlaps {sorted(set(WRITABLE) & set(OWNED_ELSEWHERE))}",
    )

    # --- `comment`, `assign` -------------------------------------------------
    noted = host()
    with_host(noted, lambda: comment(1, "the gate went red on the second predicate"))
    check(
        "a comment is posted on the card, which this tracker holds as an action",
        noted.calls.count("comment") == 1
        and sent(noted, "comment").get("text")
        == "the gate went red on the second predicate",
        f"called {noted.calls} sending {noted.params_for('comment')!r}",
    )
    taken = host()
    with_host(taken, lambda: assign(1))
    check(
        "`@me` is translated to this tracker's own spelling before the member is read",
        "me" in taken.calls and sent(taken, "add member").get("value") == "member-me",
        f"called {taken.calls} sending {taken.params_for('add member')!r}",
    )
    held = host({"cards": [_card(1, "a first card", members=["member-me"])]})
    with_host(held, lambda: assign(1))
    check(
        "and a card the member already holds is not assigned again",
        "add member" not in held.calls,
        f"called {held.calls}",
    )

    # --- the checklists, which no other implementation has ------------------
    listed = with_host(host(), lambda: checklist_read(1))
    check(
        "the check items come back with which of them are ticked",
        isinstance(listed, dict)
        and [(item["name"], item["checked"]) for item in entries(listed)]
        == [("the first thing", False), ("the second thing", True)],
        f"read {listed!r}",
    )
    ticked = host()
    answered = with_host(ticked, lambda: checklist_write(1, "the first thing", checked=True))
    check(
        "an item the card already carries is ticked rather than added again",
        ticked.calls.count("tick") == 1 and "add item" not in ticked.calls,
        f"called {ticked.calls}",
    )
    check(
        "through the state the host takes, not a flag of this module's own",
        sent(ticked, "tick").get("state") == "complete",
        f"sent {ticked.params_for('tick')!r}",
    )
    unchanged = host()
    answered = with_host(unchanged, lambda: checklist_write(1, "the second thing", checked=True))
    check(
        "an item already in that state is returned unwritten",
        isinstance(answered, dict) and answered.get("written") is False
        and not unchanged.writes(),
        f"got {answered!r} after {unchanged.calls}",
    )
    added = host()
    with_host(added, lambda: checklist_write(1, "a new thing"))
    check(
        "an item the card does not carry is added to its only checklist",
        added.calls.count("add item") == 1 and "new checklist" not in added.calls,
        f"called {added.calls}",
    )
    several = host({
        "checklists": CHECKLISTS + [
            {"id": "checklist-2", "name": "reproduction", "pos": 2, "checkItems": []}
        ]
    })
    reported = with_host(several, lambda: refused(lambda: checklist_write(1, "a new thing")))
    check(
        "a card with several checklists and none named is refused, never guessed by position",
        reported == "tracker.operations.checklist_write" and not several.writes(),
        f"reported {reported!r} after {several.calls}",
    )
    none_yet = host({"checklists": []})
    with_host(none_yet, lambda: checklist_write(1, "a new thing", checklist="acceptance"))
    check(
        "a named checklist the card lacks is created, then the item added, in that order",
        none_yet.calls.index("new checklist") < none_yet.calls.index("add item"),
        f"called {none_yet.calls}",
    )
    bare = host({"checklists": []})
    reported = with_host(bare, lambda: refused(lambda: checklist_write(1, "a new thing")))
    check(
        "while a card with no checklist and no name given is refused with the remedy named",
        reported == "tracker.operations.checklist_write" and not bare.writes(),
        f"reported {reported!r}",
    )
    removed = host()
    answered = with_host(removed, lambda: checklist_item_delete(1, "the first thing"))
    check(
        "a check item is removed through its checklist, which is where the host takes it",
        removed.calls.count("delete item") == 1,
        f"called {removed.calls}",
    )
    reported = with_host(
        host(), lambda: refused(lambda: checklist_item_delete(1, "never there"))
    )
    check(
        "and an item the card does not carry is refused rather than reported as removed",
        reported == "tracker.operations.checklist_item_delete",
        f"reported {reported!r}",
    )

    # --- searching ----------------------------------------------------------
    searched = with_host(host(), lambda: search_items())
    check(
        "the board is searched across every state it holds, the archived card included",
        got(searched, "scanned") == 3
        and any(entry["state"] == ARCHIVED for entry in entries(searched)),
        f"scanned {searched!r}",
    )
    terms = with_host(host(), lambda: search_items(terms="CARD first"))
    check(
        "every term is a substring of the title, in any order and whatever the case",
        [entry["number"] for entry in entries(terms)] == [1],
        f"matched {[entry['number'] for entry in terms['items']]}",
    )
    by_list = with_host(host(), lambda: search_items(fields={"status": second}))
    check(
        "a field's value with no terms at all is a query of its own",
        [entry["number"] for entry in entries(by_list)] == [2],
        f"matched {[entry['number'] for entry in by_list['items']]}",
    )
    by_label = with_host(host(), lambda: search_items(labels=["beta"]))
    check(
        "and a label is matched by the name the board gives it",
        [entry["number"] for entry in entries(by_label)] == [1],
        f"matched {[entry['number'] for entry in by_label['items']]}",
    )
    empty = with_host(host(), lambda: search_items(labels=["gamma"]))
    check(
        "a label nothing carries answers empty, which is what makes the matching bite",
        entries(empty) == [] and got(empty, "scanned") == 3,
        f"matched {len(empty['items'])} of {empty['scanned']}",
    )
    reported = with_host(host(), lambda: refused(lambda: search_items(labels=["no such label"])))
    check(
        "while a label the board does not have is refused, never answered empty",
        reported == "tracker.operations.search_items",
        f"reported {reported!r}",
    )
    reported = with_host(
        host(), lambda: refused(lambda: search_items(fields={"Story points": 3}))
    )
    check(
        "and a field this tracker cannot answer a query on is refused, naming it",
        reported == "tracker.operations.search_items.Story points",
        f"reported {reported!r}",
    )
    bounded = host({"cards": [_card(n, "a card") for n in range(1, 6)]})
    answered = with_host(bounded, lambda: search_items(limit=2))
    check(
        "the bound is about the matches and is exact, the board having been read whole",
        got(answered, "at_limit") is True and len(entries(answered)) == 2 and got(answered, "scanned") == 5,
        f"answered {answered['at_limit']!r} with {len(answered['items'])} of {answered['scanned']}",
    )
    # ⛔ A field that was not read is **absent from the answer**, not `None`. The
    # index is read without descriptions -- one body per card for every card on
    # the board -- so a search entry carries no `body` key, while the card read
    # does. ⚠️ The first draft answered `None` for both, which a role cannot tell
    # from a card that has no description and no checklist.
    searched_one = entries(with_host(host(), lambda: search_items()))[0]
    read_one = with_host(host(), lambda: read_item(1))
    check(
        "a field the read did not ask for is left out of the answer, never carried as None",
        "body" not in searched_one and "checklists" not in searched_one,
        f"carried {sorted(searched_one)!r}",
    )
    check(
        "while the read that does ask for them carries both",
        "body" in read_one and "checklists" in read_one,
        f"carried {sorted(read_one) if isinstance(read_one, dict) else read_one!r}",
    )
    # ⛔ One shape per operation, whether it wrote or not. An operation answering
    # two shapes would make a role's handling of the result depend on a fact it
    # did not ask about -- and the index carries no description, so the unwritten
    # answer would be short of a field the written one has.
    wrote = with_host(host(), lambda: set_state(1, status=second))
    did_not = with_host(host(), lambda: set_state(1, status=initial))
    check(
        "an operation answers in one shape whether it wrote or not",
        isinstance(wrote, dict) and isinstance(did_not, dict)
        and sorted(wrote) == sorted(did_not),
        f"wrote {sorted(wrote) if isinstance(wrote, dict) else wrote!r} against "
        f"{sorted(did_not) if isinstance(did_not, dict) else did_not!r}",
    )

    # ⛔ The queryable set is held to being answerable rather than merely stated:
    # each name is put to the matcher against a card read off the index, so a
    # name added to the list with nothing reading it reddens here instead of
    # answering every query with the cards that do not match.
    found = entries(with_host(host(), lambda: search_items()))
    one = found[0] if found else {}
    check(
        "every field this module says it answers a query on is one the matcher reads",
        all(matches(one, [], [], {name: one.get(name)}) for name in QUERYABLE),
        f"states {QUERYABLE!r} of which "
        f"{[name for name in QUERYABLE if not matches(one, [], [], {name: one.get(name)})]} "
        "answer nothing",
    )

    # --- what reaches a request path ----------------------------------------
    #
    # ⛔ Two values this module interpolates into a path, held to a shape. A
    # separator in either addresses an endpoint other than the one the call
    # means, and the host answers **that** endpoint rather than refusing -- so
    # the refusal has to be here, before the call, and the assertion reads that
    # no call was made at all.
    for value, where in (
        ("https://example.invalid/b/abc/a-board", "a URL pasted where a board id goes"),
        ("some/board", "an id carrying a separator"),
    ):
        elsewhere = _example_configuration()
        elsewhere.data["tracker"]["board"] = value
        bind(elsewhere)
        addressed = host()
        reported = with_host(addressed, lambda: refused(lambda: read_item(1)))
        check(
            f"{where} is refused, naming the key, before any call",
            reported == "tracker.board" and addressed.calls == [],
            f"reported {reported!r} after {addressed.calls}",
        )
    bind(configuration)
    for value in ("somebody/else", "../members/somebody"):
        addressed = host()
        reported = with_host(
            addressed, lambda value=value: refused(lambda: assign(1, value))
        )
        check(
            f"an assignee handle of `{value}` is refused, naming the operation",
            reported == "tracker.operations.assign" and "me" not in addressed.calls,
            f"reported {reported!r} after {addressed.calls}",
        )

    # --- the credential, and the one surface a failure is read on -----------
    os.environ.pop(KEY_VARIABLE)
    bare_shell = host()
    reported = with_host(bare_shell, lambda: unavailable(lambda: read_item(1)))
    check(
        "a shell holding neither variable is a failure naming them, before any call",
        reported is not None and KEY_VARIABLE in reported and bare_shell.calls == [],
        f"got {reported!r} after {bare_shell.calls}",
    )
    os.environ[KEY_VARIABLE] = A_KEY

    for status, what, expected in (
        (429, "rate limited", "budget"),
        (401, "unauthorised", "address being wrong"),
        (403, "forbidden", "address being wrong"),
        (404, "not found", "read from the board"),
        (500, "a server error", "failed with HTTP 500"),
        (0, "a call that never reached the host", "never reached the host"),
    ):
        answering = host({"lists": (status, '{"error":"x"}')})
        reported = with_host(answering, lambda: unavailable(lambda: read_item(1)))
        check(
            f"{what} comes back as a failure saying so",
            reported is not None and expected in reported,
            f"got {reported!r}",
        )
    # ⛔ The one assertion that is about the report rather than the call: every
    # message above quotes the call, and the call carries the pair.
    answering = host({"lists": (500, "no")})
    reported = with_host(answering, lambda: unavailable(lambda: read_item(1)))
    check(
        "and no failure message carries the key or the token, only their names",
        reported is not None
        and A_KEY not in reported
        and A_TOKEN not in reported
        and KEY_VARIABLE in reported
        and TOKEN_VARIABLE in reported,
        "a message carried the value" if reported and A_KEY in reported else f"got {reported!r}",
    )

    # --- the policy, which is the one half of the port a project states -----
    classes = policy_classes()
    check(
        "the shipped example bars something from reaching a card, so this is reachable",
        bool(classes),
        f"bars {classes!r}",
    )
    prefixes = [
        str(value)
        for value in (configuration.get("work_item.type_branch_prefix") or {}).values()
    ]
    for name, planted in PLANTS.items():
        check(
            f"the guard reddens on a planted `{name}`",
            [
                finding
                for finding in forbidden(planted, classes, prefixes)
                if finding.startswith(f"`{name}`")
            ],
            f"found {forbidden(planted, classes, prefixes)!r}",
        )
    # ⛔ The green side, asserted rather than assumed: a guard refusing
    # everything reads exactly like one that works.
    check(
        "and stays green on a body that carries none of them",
        forbidden(STAYS_GREEN, classes, prefixes) == [],
        f"found {forbidden(STAYS_GREEN, classes, prefixes)!r}",
    )
    check(
        "a class this implementation has no form for is a finding, not a pass",
        forbidden(STAYS_GREEN, ["telepathy"], prefixes),
        "a class nothing can decide read as observed",
    )
    check(
        "and `branch_names` with no prefix stated is a finding too, for the same reason",
        forbidden(STAYS_GREEN, ["branch_names"], []),
        "a bar nothing could derive a form for read as observed",
    )
    # Every write that carries text refuses a planted span, and the write does
    # not happen. ⛔ Four operations, because those are the four that carry text
    # a person wrote; the rest carry ids read from the board.
    planted = PLANTS["branch_names"]
    for label, call in (
        ("create_item", lambda: create_item("a title", planted)),
        ("comment", lambda: comment(1, planted)),
        ("set_field", lambda: set_field(1, "desc", planted)),
        ("checklist_write", lambda: checklist_write(1, planted)),
    ):
        guarded = host()
        reported = with_host(guarded, lambda call=call: refused(call))
        check(
            f"`{label}` refuses a barred span, naming the key that bars it",
            reported == "tracker.policy.forbid_on_item" and not guarded.writes(),
            f"reported {reported!r} after {guarded.calls}",
        )
    # The last acceptance item, as far as a suite can answer it: a pass over
    # every write, inspecting the parameters that reach the card.
    # ⚠️ The filed card is in the index this fixture answers with, because the
    # read-back after a create is what establishes the card exists: an index
    # without it fails the first call and the six writes after it never run --
    # measured, and the assertion below is what reports that rather than the
    # sweep passing over one call.
    sweeping = host({
        "checklists": [],
        "cards": [
            _card(1, "a first card", labels=["label-beta"]),
            _card(2, "a second card", in_list=board_lists[1]["id"]),
            _card(4, "a filed card", labels=["label-alpha"]),
        ],
    })
    with_host(sweeping, lambda: (
        create_item("a clean title", STAYS_GREEN, ["alpha"]),
        set_state(1, status=second),
        set_field(1, "desc", STAYS_GREEN),
        comment(1, STAYS_GREEN),
        set_labels(1, ["alpha"]),
        assign(1),
        checklist_write(1, "a clean item", checklist="acceptance"),
    ))
    carried = [
        (name, key, value)
        for name, params in sweeping.sent
        for key, value in params.items()
        if key in TEXT_PARAMETERS and isinstance(value, str)
        and forbidden(value, classes, prefixes)
    ]
    check(
        "a pass of every write sends nothing barred in the parameters that reach the card",
        not carried,
        f"sent {carried!r}",
    )
    check(
        "and that pass did reach the host, so the sweep is over calls that were made",
        len([name for name, _ in sweeping.sent if name in sweeping.writes()]) >= 6,
        f"made {sweeping.writes()!r}",
    )

    # --- this fake's own rule ------------------------------------------------
    check(
        "a tick is not answered as a card update, which the route order is what decides",
        route("PUT", "/cards/card-1/checkItem/item-1") == "tick"
        and route("PUT", "/cards/card-1") == "update"
        and route("GET", "/cards/card-1/checklists") == "checklists"
        and route("GET", "/cards/card-1") == "card",
        f"routed {route('PUT', '/cards/card-1/checkItem/item-1')!r}",
    )
    check(
        "and a call to a route the fake does not name is an error rather than an answer",
        isinstance(
            ran(lambda: _Host(configuration)("GET", "/nowhere", {})).get("<raised>"), str
        ),
    )

    # ⛔ The module and the shell left as they were found. This suite binds a
    # configuration, resolves boards against a substituted host and writes two
    # variables; a run inside a longer process -- which is what the gate's
    # runner is -- would otherwise leave an example's board cached behind a real
    # role's first call, and a credential-shaped value in the environment.
    bind(None)
    _boards.clear()
    for name, value in was_environment.items():
        if value is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = value

    if failures:
        print(f"\n{failures} assertion(s) did not hold.")
    return 1 if failures else 0
