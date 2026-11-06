#!/usr/bin/env python3
"""The board implementation's suite: the shapes it was measured against, as code.

⛔ **A module of its own rather than a mode of the implementation**, and the host
decided that: a single file carrying both reaches the code host with **no patch**,
and the gate that holds every added line to the deferral rule refuses a change it
cannot read. ⚠️ The name opens with `_` so that discovery skips it -- a module in
the port's `adapters/` package that names no kind is refused rather than skipped,
which is exactly right for an implementation and exactly wrong for a suite.

What it holds, and the one kind of plant it cannot carry, are recorded in
`docs/single-source-of-truth.md` § Beside the contract. Nothing here restates
them.

The implementation is imported by **name** for everything the cases call, and
through the **module** for the two seams they substitute: rebinding a name this
module imported would leave the implementation calling its own.
"""

from __future__ import annotations

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

# ⚠️ Not `board`: a case below names a resolved board that, so the module alias
# has to be the thing under test rather than the thing it answers about.
from adapters import _code_host_dependency as relation  # noqa: E402
from adapters import github_projects as under_test  # noqa: E402
from adapters.github_projects import (  # noqa: E402
    ADAPTER,
    ADD_CARD,
    BOARD_QUERY,
    CLOSED_BY_QUERY,
    DATE,
    DELIBERATELY_ABSENT,
    ITEMS_QUERY,
    ITEM_QUERY,
    KIND,
    NOT_FOUND,
    NUMBER,
    SET_DATE,
    SET_NUMBER,
    SET_OPTION,
    SET_TEXT,
    SINGLE_SELECT,
    STATUS_FIELD_NAME,
    VALUE_FACTS,
    TEXT,
    WRITABLE,
    WRITES,
    _SCRIPTS,
    _board,
    _boards,
    _paged,
    _status_field,
    _whole,
    advance_on_merge,
    assign,
    bind,
    comment,
    create_item,
    index_fields,
    item_number,
    link_dependency,
    link_for_close,
    matches,
    read_blockers,
    read_item,
    search_items,
    set_field,
    set_labels,
    set_state,
    values_by_field,
)

# The id shapes this host hands out for a board, its fields, its cards and a
# single-select option. ⛔ Carried here as a **grammar to forbid**, never as a
# value: the sweep in the self-test holds every shipped carrier to containing
# none of them, which is the mechanical half of `resolve: by_name`.
ID_SHAPES = (
    re.compile(r"\bPVT_[A-Za-z0-9_-]{6,}"),      # a project
    re.compile(r"\bPVTF_[A-Za-z0-9_-]{6,}"),     # a field
    re.compile(r"\bPVTSSF_[A-Za-z0-9_-]{6,}"),   # a single-select field
    re.compile(r"\bPVTI_[A-Za-z0-9_-]{6,}"),     # a card
    re.compile(r"(?<![0-9a-zA-Z])[0-9a-f]{8}(?![0-9a-zA-Z])"),  # an option id
)

# --- self-test --------------------------------------------------------------
#
# The work item's acceptance check, run as code, and nothing that needs the live
# board: the ids resolved by name, a board past one page read whole, two fields
# out of one read, and every guard and ordering that could put a write on the
# wrong object. What the suite cannot answer is what the host does with a
# payload, which is the live run the work item's record carries.


def _example_configuration():
    """The shipped example for this kind, as the fixture.

    ⛔ Named from `KIND` rather than spelled: this module is the one place a
    tracker's name belongs, and the example beside it is the configuration a
    project of this kind actually writes -- a hand-built fixture here would be a
    second statement of the same block, allowed to disagree with it.
    """
    path = os.path.join(config.EXAMPLES, f"{KIND}.yaml")
    with open(path, encoding="utf-8") as handle:
        return config.load_text(handle.read(), config.EXAMPLES)


# A board's fields as the host answers them, carrying the whole production shape
# -- the host-managed columns included, because a fixture holding only what the
# code reads is a fixture testing itself. The ids are this suite's own and
# resolve nowhere; what matters is that every id the code uses comes from here.
FIELD_NODES = [
    {"__typename": "ProjectV2Field", "id": "PVTF_title", "name": "Title", "dataType": "TITLE"},
    {
        "__typename": "ProjectV2Field",
        "id": "PVTF_assignees",
        "name": "Assignees",
        "dataType": "ASSIGNEES",
    },
    {
        "__typename": "ProjectV2SingleSelectField",
        "id": "PVTSSF_status",
        "name": "Status",
        "dataType": "SINGLE_SELECT",
        "options": [
            {"id": "aaaaaaa1", "name": "Todo"},
            {"id": "aaaaaaa2", "name": "In Progress"},
            {"id": "aaaaaaa3", "name": "Merged"},
            {"id": "aaaaaaa4", "name": "Done"},
        ],
    },
    {"__typename": "ProjectV2Field", "id": "PVTF_labels", "name": "Labels", "dataType": "LABELS"},
    {
        "__typename": "ProjectV2Field",
        "id": "PVTF_estimate",
        "name": "Estimate",
        "dataType": "NUMBER",
    },
    {"__typename": "ProjectV2Field", "id": "PVTF_due", "name": "Due", "dataType": "DATE"},
    {"__typename": "ProjectV2Field", "id": "PVTF_notes", "name": "Notes", "dataType": "TEXT"},
    {
        "__typename": "ProjectV2IterationField",
        "id": "PVTIF_sprint",
        "name": "Sprint",
        "dataType": "ITERATION",
        "configuration": {"iterations": [{"id": "iter-1", "title": "Sprint 1"}]},
    },
]


def _value_nodes(status: str | None = "Todo") -> list:
    """A card's field values, one of each type this module maps."""
    nodes = [
        {
            "__typename": "ProjectV2ItemFieldTextValue",
            "text": "a card",
            "field": {"name": "Title"},
        },
        {
            "__typename": "ProjectV2ItemFieldNumberValue",
            "number": 3.0,
            "field": {"name": "Estimate"},
        },
        {
            "__typename": "ProjectV2ItemFieldDateValue",
            "date": "2026-10-22",
            "field": {"name": "Due"},
        },
        {
            "__typename": "ProjectV2ItemFieldIterationValue",
            "title": "Sprint 1",
            "iterationId": "iter-1",
            "field": {"name": "Sprint"},
        },
        {
            "__typename": "ProjectV2ItemFieldUnknownValue",
            "field": {"name": "Something new"},
        },
    ]
    if status is not None:
        nodes.insert(
            0,
            {
                "__typename": "ProjectV2ItemFieldSingleSelectValue",
                "name": status,
                "optionId": "aaaaaaa1",
                "field": {"name": "Status"},
            },
        )
    return nodes


def _page_of(nodes: list, *, more: bool = False, cursor: str | None = None) -> dict:
    return {
        "totalCount": len(nodes),
        "pageInfo": {"hasNextPage": more, "endCursor": cursor},
        "nodes": nodes,
    }


def _issue_payload(
    number: int = 7,
    *,
    typename: str = "Issue",
    status: str | None = "Todo",
    on_board: bool = True,
    project_number: int = 0,
) -> dict:
    """What `ITEM_QUERY` answers, in the shape the host answers it.

    ⛔ A pull request answers in the **same** shape with a different typename, and
    not as a stub. Measured on this suite itself: a thinner pull-request payload
    made every *wrote nothing against it* assertion pass for the wrong reason --
    with the guard deleted the call still failed, on a connection the stub did not
    carry, so four assertions about a write being refused were green against a
    missing fixture rather than against the guard.
    """
    cards = []
    if on_board:
        cards.append({
            "id": "PVTI_card",
            "isArchived": False,
            "project": {"number": project_number},
            "fieldValues": _page_of(_value_nodes(status)),
        })
    return {
        "repository": {
            "issueOrPullRequest": {
                "__typename": typename,
                "id": "I_issue",
                "number": number,
                "title": "an item",
                "body": "what it is",
                "state": "OPEN",
                "url": f"https://example.invalid/issues/{number}",
                "labels": _page_of([{"name": "port"}]),
                "assignees": _page_of([{"login": "somebody"}]),
                "projectItems": _page_of(cards),
            }
        }
    }


def _board_payload_for(fields_page: dict) -> dict:
    return {
        "repositoryOwner": {
            "__typename": "User",
            "projectV2": {"id": "PVT_board", "number": 0, "title": "a board", "fields": fields_page},
        }
    }


def _item_card(number: int, title: str, status: str = "Todo", kind: str = "Issue") -> dict:
    content = {"__typename": kind, "title": title}
    if kind != "DraftIssue":
        content.update({
            "number": number,
            "state": "OPEN",
            "url": f"https://example.invalid/issues/{number}",
        })
    if kind == "Issue":
        content["labels"] = _page_of([{"name": "port"}])
    return {
        "id": f"PVTI_{number}",
        "isArchived": False,
        "type": "ISSUE" if kind == "Issue" else kind.upper(),
        "content": content,
        "fieldValues": _page_of(_value_nodes(status)),
    }


def _dependencies_page(entries: list[tuple[int, str, str, str | None]]) -> list[dict]:
    """The host's own answer for the dependencies endpoint: plain issue objects.

    ⚠️ A different shape from everything else this fake answers, and that is the
    fact rather than an inconsistency: the board is the query interface and the
    relation is REST, so the two halves of a dependency are read off two
    interfaces.

    ⛔ **Every entry carries its repository address**, because that is the half a
    bare number loses: a relation is recordable across repositories, a board draws
    its cards from more than one, and the wrong `#13` answers perfectly. A fixture
    that left it out would let an implementation assuming the configured
    repository read as correct.

    ⛔ **And every entry carries the host's own reason for its state**, which is
    the half a closed state loses: an item abandoned rather than finished is
    closed, and § 5's bar is what the dependency produced. A fixture whose closed
    entries were all finished would let an implementation dropping the reason read
    as correct -- measured on this repository's own backlog, which holds items
    closed that way.
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


def _asked_for(args: list[str], default: int = 7) -> int:
    """The item number a call carried, read off the call itself.

    The client passes a typed variable as `number=11`, so this is what lets the
    fake answer for the object that was asked for rather than for one constant.
    """
    for part in args:
        if part.startswith("number="):
            return int(part.split("=", 1)[1])
    return default


def _default_answers() -> dict:
    """An answer for every call this module can make.

    ⛔ **A fake answers everything the host would**, and a case states only what
    it wants to differ. Measured on this suite: fakes that carried just the calls
    the passing path makes turned two deliberate breaks into a traceback inside
    the operation -- so an assertion about *what was called* died before it could
    report, and both cases read as green. A fake that refuses an unexpected call
    cannot tell a behaviour that moved from a fixture that is thin.
    """
    return {
        "Board": _board_payload_for(_page_of(FIELD_NODES)),
        # ⛔ Answers for the number that was **asked for**, not one canned number
        # for every ask. ⚠️ Measured: while it answered a fixed number, an
        # implementation that read a number back off this answer and used it
        # addressed that one instead — so a case about which object a call
        # addresses was asserting the fixture's constant. A case that wants a
        # particular item still overrides this key.
        "Item": lambda args: _issue_payload(_asked_for(args)),
        "Items": {"repositoryOwner": {"projectV2": {"items": _page_of([])}}},
        # Prefix-matched across the four documents a value is written through,
        # which all answer in the same shape.
        "Set": {"updateProjectV2ItemFieldValue": {"projectV2Item": {"id": "PVTI_card"}}},
        "AddCard": {"addProjectV2ItemById": {"item": {"id": "PVTI_card"}}},
        "ClosedBy": {
            "repository": {
                "issue": {"state": "OPEN", "closedByPullRequestsReferences": _page_of([])}
            }
        },
        "issue create": "https://example.invalid/issues/31",
        "issue comment": "",
        "issue edit": "",
        # ⚠️ Named by the **paging flag** rather than by the path, because
        # `args[:2]` is what this fake reads and the path is the third word --
        # which holds while this is the one paged REST read in the module. A
        # second one would need the fake to name a call by what it addresses, and
        # this comment is where that shows up.
        #
        # ⚠️ **Its position among the keys is not load-bearing**, and the first
        # form of this comment claimed it was: `_answer_for` tries every exact
        # match across both tables before any prefix, this name is exactly what
        # `_name` returns for the paged call, and it is a prefix of nothing else.
        # Reproduced by moving it after `api` and watching the suite stay green --
        # a comment asserting an ordering nothing depends on is the restated-fact
        # class one layer down.
        "api --paginate": _dependencies_page([]),
        # Prefix-matched: the dependency lookup addresses one issue by path, and
        # the relation itself is posted with `--method`.
        "api": 4321,
    }


class _Host:
    """A transport that answers as the host does, and records what was asked.

    ⛔ A fake rather than a mock: it answers by **what was asked for** -- the
    operation name in a GraphQL document, or the subcommand of a client call --
    rather than by the order this module happens to call in, so a refactor that
    reorders calls does not redden it and a call that moves to the wrong object
    does.

    A name is matched exactly, then by prefix, then against the default answers
    above; what a case passes in `answers` is what it wants to differ from the
    host answering normally.
    """

    def __init__(self, answers: dict, *, pages: dict | None = None):
        self.answers = answers
        self.pages = pages or {}
        self.defaults = _default_answers()
        self.calls: list[str] = []
        self.sent: list[list[str]] = []

    def _answer_for(self, name: str):
        # ⛔ Every exact match first, across both tables, and only then a prefix
        # one. ⚠️ Measured on this fake rather than on the module: the document
        # names are `Item` and `Items`, so a case overriding `Item` had its
        # override answer a call for `Items` by prefix -- the item payload where a
        # page of cards belongs, silently, in the one direction a case cannot see.
        for table in (self.answers, self.defaults):
            if name in table:
                return table[name]
        for table in (self.answers, self.defaults):
            for key, answer in table.items():
                if name.startswith(key):
                    return answer
        raise HostUnavailable(
            f"this suite's host was asked for `{name}`, which it has no answer for"
        )

    # A document's operation name, which is what this fake answers by. ⚠️ Read
    # with a pattern rather than by splitting the string: the documents are
    # written starting on their own line, so a split on the first bracket
    # carried the newline and the keyword into the name.
    OPERATION = re.compile(r"\b(?:query|mutation)\s+(?P<name>[A-Za-z][A-Za-z0-9_]*)")

    def _name(self, args: list[str]) -> str:
        if args[:2] == ["api", "graphql"]:
            document = next(part for part in args if part.startswith("query="))
            found = self.OPERATION.search(document)
            if not found:
                raise AssertionError(f"this suite's host cannot name {document[:40]!r}")
            return found.group("name")
        return " ".join(args[:2])

    def __call__(self, args: list[str], parse: bool = True):
        name = self._name(args)
        self.calls.append(name)
        # ⚠️ The whole call beside the name it answers by. The name is
        # `args[:2]`, which is the right key for a fake that must not care about
        # argument order -- and it loses a path that sits behind a flag, so a
        # write's own address is unassertable from `calls` alone. Measured: the
        # relation is posted with `--method` in front of its path, so every
        # dependency write read as the same call.
        self.sent.append(list(args))
        after = next(
            (part.split("=", 1)[1] for part in args if part.startswith("after=")), None
        )
        if name in self.pages:
            return self._envelope(self.pages[name](after))
        answer = self._answer_for(name)
        return self._envelope(answer(args) if callable(answer) else answer)

    @staticmethod
    def _envelope(answer):
        """The host's own wrapper around a GraphQL answer.

        ⚠️ Added here rather than written into every fixture: the client hands
        back `{"data": ...}`, and a fake that answered the inner half would be a
        fake of something no host returns -- the arm that reads an `errors` array
        would then be unreachable. A fixture that states the whole envelope is
        passed through, which is how the error case states both halves.
        """
        if isinstance(answer, dict) and ("data" in answer or "errors" in answer):
            return answer
        if isinstance(answer, dict):
            return {"data": answer}
        return answer


def _carrier_texts() -> list[str]:
    """Every shipped carrier's text, for the sweep the first acceptance item asks.

    A carrier is a skill, a command or a hook (§ 7), and what this sweeps is the
    text a role reads -- the place the measured id tables were pasted into. ⚠️ The
    roots are matched by shape rather than listed, which is the grammar the gate in
    `tools/` already reads carrier roots with.
    """
    root = os.path.dirname(os.path.dirname(os.path.dirname(_SCRIPTS)))
    found = []
    for base, directories, names in os.walk(root):
        if ".git" in base.split(os.sep):
            directories[:] = [name for name in directories if name != ".git"]
            continue
        parts = base.split(os.sep)
        if not any(part in ("skills", "commands", "hooks") for part in parts):
            continue
        for name in names:
            if name.endswith((".md", ".sh", ".json", ".yaml", ".yml")):
                found.append(os.path.join(base, name))
    return found


def names_an_id(text: str) -> list[str]:
    """Every board id shape the text carries, in the spellings the host hands out."""
    return [match.group(0) for shape in ID_SHAPES for match in shape.finditer(text)]


def self_test() -> int:
    failures = 0

    def check(label: str, condition: bool, detail: str = "") -> None:
        nonlocal failures
        if condition:
            print(f"  ok    {label}")
        else:
            failures += 1
            print(f"  FAIL  {label}{': ' + detail if detail else ''}")

    # ⛔ Both helpers catch **everything**, each reporting the other outcomes as
    # themselves rather than letting them out. A deliberate break that made an
    # operation raise the other kind of exception killed the run on a traceback
    # where a verdict belongs -- the same defect the port's own suite records one
    # file over, and the reason this gate must always print a count.
    def refused(call) -> str | None:
        """The key a call refuses on, or None where it returns instead."""
        try:
            call()
        except ConfigError as error:
            return error.key
        except Exception as error:
            return f"<{type(error).__name__}: {error}>"
        return None

    def unavailable(call) -> str | None:
        """The host failure a call reports, or None where it returns instead."""
        try:
            call()
        except HostUnavailable as error:
            return str(error)
        except Exception as error:
            return f"<{type(error).__name__}: {error}>"
        return None

    def ran(call):
        """A call expected to go through, with any exception reported as a value.

        The cases below assert on *what was called*; an operation that raised
        where it should not have is a FAIL in the assertion that reads the calls,
        and must not be a traceback that stops the count.
        """
        try:
            return call()
        except Exception as error:
            return {"<raised>": f"{type(error).__name__}: {error}"}

    def with_host(host, call):
        """Run one call against a substituted transport, restoring it after.

        ⛔ Through `ran`, so a case whose operation raises reports in the
        assertion that reads it rather than ending the run. The two helpers above
        catch first where a case is *about* a refusal, so nothing is hidden: what
        this adds is a verdict for the case that was not expecting one.
        """
        was = under_test.TRANSPORT
        under_test.TRANSPORT = host
        try:
            return ran(call)
        finally:
            under_test.TRANSPORT = was

    # The fixture configuration, and the registry entry this module is.
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

    # --- the operation list, against the surface the port reads -------------
    stated = port.surface_operations()
    check(
        "every operation the surface states is implemented or deliberately absent",
        set(stated) - set(ADAPTER.operations) == set(DELIBERATELY_ABSENT),
        f"unimplemented and unaccounted for: "
        f"{sorted(set(stated) - set(ADAPTER.operations) - set(DELIBERATELY_ABSENT))}",
    )
    check(
        "and nothing is implemented that the surface does not state",
        not set(ADAPTER.operations) - set(stated),
        f"implements {sorted(set(ADAPTER.operations) - set(stated))}",
    )
    # ⚠️ Compared by the operations it declares rather than by identity: under
    # `--self-test` this module runs as `__main__` and discovery imports it a
    # second time as a package member, so the two `ADAPTER` objects are different
    # objects stating the same thing -- the caveat `adapters/__init__.py` records.
    discovered = port.Port(configuration).adapter
    check(
        "the port resolves an implementation of this kind, declaring these operations",
        discovered is not None
        and discovered is not port.UNCONFIGURED
        and sorted(discovered.operations) == sorted(ADAPTER.operations),
        f"resolved {discovered!r}",
    )

    # --- ids resolved by name, in one place ---------------------------------
    fields = index_fields(FIELD_NODES)
    check(
        "a field's id is the one the board answered, resolved by its name",
        fields["Status"]["id"] == "PVTSSF_status"
        and fields["Status"]["options"]["In Progress"] == "aaaaaaa2",
        f"resolved {fields.get('Status')!r}",
    )
    check(
        "and an iteration is resolved by its title, for the same reason",
        fields["Sprint"]["iterations"] == {"Sprint 1": "iter-1"},
        f"resolved {fields['Sprint']['iterations']!r}",
    )
    check(
        "a host-managed column keeps its type, so a write into it can be refused",
        fields["Labels"]["data_type"] == "LABELS" and fields["Estimate"]["data_type"] == NUMBER,
    )

    # The sweep the first acceptance item asks for, with a plant per id shape so
    # that each spelling is asserted to redden rather than assumed to.
    carriers = _carrier_texts()
    check("the sweep for ids reaches at least one carrier text", bool(carriers))
    carrying = []
    for path in carriers:
        with open(path, encoding="utf-8") as handle:
            found = names_an_id(handle.read())
        if found:
            carrying.append((os.path.relpath(path, os.path.dirname(_SCRIPTS)), found[:3]))
    check("no shipped carrier names a board, field, card or option id", not carrying, f"{carrying}")
    for planted, what in (
        ("PVT_kwDOAbCdEf4AaBcD", "a project id"),
        ("PVTF_lADOAbCdEf4AaBcDzgAbCdEf", "a field id"),
        ("PVTSSF_lADOAbCdEf4AaBcDzgAbCdEf", "a single-select field id"),
        ("PVTI_lADOAbCdEf4AaBcDzgAbCdEf", "a card id"),
        ("47fc9ee4", "an option id"),
    ):
        text = f"| Status | In Progress | `{planted}` |\n"
        check(
            f"the sweep reddens on {what}",
            names_an_id(text) == [planted],
            f"found {names_an_id(text)!r}",
        )
    check(
        "and stays green on prose that merely talks about ids",
        not names_an_id(
            "The option id is read from the board by name, never written here, and "
            "a status word like Todo carries no id at all.\n"
        ),
    )

    # --- a board past one page, read whole ----------------------------------
    pages = [
        _page_of([{"name": f"field {index}", "id": f"PVTF_{index}"}], more=True, cursor=f"c{index}")
        for index in range(3)
    ]
    pages.append(_page_of([{"name": "last", "id": "PVTF_last"}]))
    read = _paged(lambda cursor: pages[0 if cursor is None else int(cursor[1:]) + 1], what="pages")
    check(
        "a connection past one page is read whole, every page followed",
        len(read) == 4 and read[-1]["name"] == "last",
        f"read {len(read)} node(s)",
    )
    short = unavailable(
        lambda: _paged(lambda cursor: _page_of([{"name": "one"}], more=True), what="a short answer")
    )
    check(
        "a page claiming a successor and naming no cursor is refused, not returned short",
        short is not None and "refused rather than returned short" in short,
        f"got {short!r}",
    )
    repeated = unavailable(
        lambda: _paged(
            lambda cursor: _page_of([{"name": "one"}], more=True, cursor="same"),
            what="a repeated cursor",
        )
    )
    check(
        "a cursor the host repeats is refused rather than followed forever",
        repeated is not None and "already given" in repeated,
        f"got {repeated!r}",
    )
    # ⚠️ A cursor that is new every time, not one derived from the last: a
    # derived one repeated itself and this case reddened on the repeat guard
    # above instead of on the bound, which is a case believed and unexercised.
    forever = {"n": 0}

    def _never_ends(cursor, forever=forever):
        forever["n"] += 1
        return _page_of([{"name": "one"}], more=True, cursor=f"c{forever['n']}")

    endless = unavailable(lambda: _paged(_never_ends, what="an endless cursor"))
    check(
        "and a cursor that never ends is bounded rather than spun on",
        endless is not None and "past any real board" in endless,
        f"got {endless!r}",
    )
    truncated = unavailable(
        lambda: _whole(_page_of([{"name": "one"}], more=True), "a nested list")
    )
    check(
        "a nested list the host says it has more of is refused, never truncated",
        truncated is not None and "refused rather than returned short" in truncated,
        f"got {truncated!r}",
    )

    # The board read as an operation does it, across two pages, through the seam.
    board_pages = {
        "Board": lambda after: _board_payload_for(
            _page_of(FIELD_NODES[:4], more=True, cursor="page-2")
            if after is None
            else _page_of(FIELD_NODES[4:])
        )
    }
    _boards.clear()
    counting = _Host({}, pages=board_pages)
    board = with_host(counting, lambda: _board())
    check(
        "the board's own fields are read across pages and keyed by name",
        set(board["fields"]) == {node["name"] for node in FIELD_NODES},
        f"read {sorted(board['fields'])}",
    )
    check(
        "and page one is asked for once, not again to get at the fields inside it",
        counting.calls == ["Board", "Board"],
        f"called {counting.calls}",
    )
    _boards.clear()
    cached = _Host({}, pages=board_pages)
    with_host(cached, lambda: (_board(), _board(), _board()))
    check(
        "a board resolved once is not resolved again for the same address",
        cached.calls == ["Board", "Board"],
        f"called {cached.calls}",
    )

    # --- two fields out of one read -----------------------------------------
    values = values_by_field(_value_nodes())
    check(
        "two fields come back from one read, keyed by their own names",
        values["Status"] == "Todo" and values["Estimate"] == 3.0 and values["Due"] == "2026-10-22",
        f"read {values!r}",
    )
    check(
        "every value type this module maps is read, the iteration included",
        values["Title"] == "a card" and values["Sprint"] == "Sprint 1",
        f"read {values!r}",
    )
    check(
        "a value type nobody mapped is carried as unmapped rather than as absent",
        values["Something new"] == {"unmapped": "ProjectV2ItemFieldUnknownValue"},
        f"read {values.get('Something new')!r}",
    )
    documents = [
        BOARD_QUERY, ITEM_QUERY, ITEMS_QUERY, CLOSED_BY_QUERY, ADD_CARD,
        SET_OPTION, SET_TEXT, SET_NUMBER, SET_DATE,
    ]
    check(
        "no query asks for a field by name, which is the shape the host refuses twice over",
        not any("fieldValueByName" in document for document in documents),
    )
    # ⛔ One statement of the value selection, formatted into both queries that
    # read values. A second copy is the class this change's own review reads a
    # diff for: the copy that drifts is whichever query nobody was looking at, and
    # a value type added to one and missing from the other reads as a column with
    # no value rather than as an omission.
    check(
        "the value selection is stated once and used by both queries that read values",
        VALUE_FACTS in ITEM_QUERY
        and VALUE_FACTS in ITEMS_QUERY
        and ITEM_QUERY.count("fragment valueFacts") == 1
        and ITEMS_QUERY.count("fragment valueFacts") == 1,
        f"{ITEM_QUERY.count('fragment valueFacts')} and "
        f"{ITEMS_QUERY.count('fragment valueFacts')} copies",
    )
    # And the fake's own shadowing rule, which is about this suite rather than the
    # module: `Item` is a prefix of `Items`.
    shadowing = _Host({"Item": {"marker": "the override"}})
    check(
        "an override for one document does not answer a call for another it prefixes",
        shadowing._answer_for("Items") is not shadowing.answers["Item"]
        and shadowing._answer_for("Item") is shadowing.answers["Item"],
        f"answered {shadowing._answer_for('Items')!r}",
    )
    check(
        "a value that can travel as a variable does, rather than as the input object "
        "the host refuses",
        all(
            f"${variable}:" in document and "ProjectV2FieldValue" not in document
            for kind, (document, variable) in WRITES.items()
            if variable is not None
        ),
    )
    number_document, number_variable = WRITES[NUMBER]
    check(
        "and the one that cannot carries no variable, taking the value into its document",
        number_variable is None and "value:{number:%(number)s}" in number_document,
        f"built {number_document.strip().splitlines()[-5:]!r}",
    )
    # ⛔ The two refusals a number column states, asked of the shaping rather than
    # of the write: the value is formatted into a request, so a word the host would
    # read as a syntax error must be refused before anything is built -- and the
    # refusal names the column, which the write itself could not.
    for value, what in ((float("inf"), "a value that is not finite"), ("three", "a word")):
        reported = refused(
            lambda value=value: under_test._as_number(value, key="tracker.project.field.Estimate")
        )
        check(
            f"{what} handed to a number column is refused, naming the column",
            reported == "tracker.project.field.Estimate",
            f"reported {reported!r}",
        )
    reported = refused(
        lambda: under_test._as_date("tomorrow", key="tracker.project.field.Due")
    )
    check(
        "and a date that is not the host's own form is refused, naming the column",
        reported == "tracker.project.field.Due",
        f"reported {reported!r}",
    )
    check(
        "while the form the host takes is passed through",
        under_test._as_date("2026-10-23", key="k") == "2026-10-23",
    )
    # ⛔ A float variable is refused before any call. The client has no typed form
    # for one -- measured against the live host -- so a caller reaching here would
    # otherwise get the host's refusal for a reason nothing in the module explains.
    silent_host = _Host({})
    reported = with_host(
        silent_host,
        lambda: refused(lambda: under_test._graphql("query X { x }", thing=1.5)),
    )
    check(
        "a float handed in as a variable is refused, naming the operation, before any call",
        reported == "tracker.operations.thing" and silent_host.calls == [],
        f"reported {reported!r} after {silent_host.calls}",
    )
    check(
        "and every type this module calls writable has something to write it",
        set(WRITES) == set(WRITABLE),
        f"writes {sorted(WRITES)} of {sorted(WRITABLE)}",
    )

    # --- the guard, and what must not have happened -------------------------
    _boards.clear()
    for typename in ("PullRequest",):
        host = _Host({"Item": _issue_payload(11, typename=typename)})
        reported = with_host(host, lambda: unavailable(lambda: read_item(11)))
        check(
            f"a number naming a {typename} is refused, naming what it is",
            reported is not None and typename in reported,
            f"got {reported!r}",
        )
        for operation, call in (
            ("comment", lambda: comment(11, "a note")),
            # ⚠️ A set that **differs** from the fixture's labels. Asking for the
            # labels it already carries made this case pass on the operation's
            # own short-circuit rather than on the guard -- measured by deleting
            # the guard and watching this one assertion stay green.
            ("set_labels", lambda: set_labels(11, ["infra"])),
            ("assign", lambda: assign(11)),
            ("link_dependency", lambda: link_dependency(11, 12)),
        ):
            host = _Host({"Item": _issue_payload(11, typename=typename)})
            with_host(host, lambda: unavailable(call))
            check(
                f"and `{operation}` wrote nothing against it -- the refusal lands "
                "before the write",
                host.calls == ["Item"],
                f"called {host.calls}",
            )

    # ⛔ And every write addresses the number the host answered with rather than
    # the argument's spelling. ⚠️ Asked with a **zero-padded** decimal, which is
    # the observable shape: the guard accepts it and normalises it, while `str()`
    # of the argument and of the host's integer differ -- with an unpadded
    # argument the two render identically and a case cannot tell the mechanism
    # from its absence.
    for operation, call, mark in (
        ("assign", lambda: assign("011"), "--add-assignee"),
        ("comment", lambda: comment("011", "a note"), "--body"),
    ):
        _boards.clear()
        padded = _Host({
            "Board": _board_payload_for(_page_of(FIELD_NODES)),
            "Item": _issue_payload(11),
        })
        with_host(padded, call)
        written = [args for args in padded.sent if mark in args]
        check(
            f"`{operation}` addresses the host's own number, not the argument's spelling",
            bool(written) and all("11" in args and "011" not in args for args in written),
            f"sent {written!r}",
        )

    check(
        "`item_number` and `link_for_close` reach the host at all",
        item_number(12) == 12 and item_number({"number": 13}) == 13
        and link_for_close(14) == "Closes #14",
    )
    silent = _Host({})
    with_host(silent, lambda: (item_number(12), link_for_close(12)))
    check("without making a host call", silent.calls == [], f"called {silent.calls}")

    # --- `link_dependency`: which object each half of the write addresses -----
    #
    # ⛔ The two halves run opposite ways and nothing held them for this kind: the
    # id is looked up on the **blocker** and the relation is posted on the
    # **blocked** item. Swap them and the call still succeeds, recording a real
    # relation the wrong way round — and the readiness gate reading it then starts
    # the item that is actually blocked. ⚠️ Asserted off the calls as sent rather
    # than off the names, because the posted path sits behind a flag.
    _boards.clear()
    own_repo = str(configuration.get("host.repo") or "")
    written = _Host({})
    with_host(written, lambda: link_dependency(11, 12))
    posted = [args for args in written.sent if args[:1] == ["api"] and "--method" in args]
    looked_up = [
        args for args in written.sent if args[:1] == ["api"] and "--jq" in args
    ]
    check(
        "the relation is posted on the blocked item and the id read off the blocker",
        len(posted) == 1 and len(looked_up) == 1
        and relation.blocked_by_path(own_repo, 11) in posted[0]
        and relation.issue_path(own_repo, 12) in looked_up[0],
        f"posted {posted!r} after looking up {looked_up!r}",
    )

    # --- `read_blockers`: the source the readiness gate's blocker check has ---
    #
    # ⛔ The relation is a fact about the issues and not about the card, so this
    # reads REST while every other read here reads the query interface. What the
    # cases below hold is the three things a gate would be wrong about: which
    # repository a blocker is in, which state word it carries, and whether the
    # answer is the first page or all of them.
    _boards.clear()
    elsewhere = "another-owner/another-name"
    recorded = _Host({
        "api --paginate": _dependencies_page([
            (12, "closed", own_repo, "completed"),
            (13, "open", elsewhere, None),
            (14, "closed", own_repo, "not_planned"),
        ]),
    })
    answered = with_host(recorded, lambda: read_blockers(11))
    blockers = answered.get("blockers") if isinstance(answered, dict) else None

    # ⛔ Every field read with `.get` and never by subscript. ⚠️ Measured on this
    # block's own first form: a plant that dropped a field killed the run with a
    # `KeyError` where a verdict belongs, which is the shape the suite beside this
    # one records -- an assertion about a missing field cannot be the thing that
    # cannot survive it.
    def field(name: str) -> list:
        return [entry.get(name) for entry in blockers or [{}]]

    check(
        "`read_blockers` answers every recorded blocker with the host's own state word",
        list(zip(field("number"), field("state")))
        == [(12, "closed"), (13, "open"), (14, "closed")],
        f"answered {blockers!r}",
    )
    check(
        "and the repository each blocker is in, which a bare number loses",
        field("repo") == [own_repo, elsewhere, own_repo],
        f"answered {field('repo')!r}",
    )
    # ⛔ The reason beside the state, which is the half a closed state loses: #12
    # and #14 are both `closed` and only one of them produced anything, and § 5's
    # bar is what the dependency produced. An implementation dropping this answers
    # the two identically.
    check(
        "and the host's own reason for a closed state, so an abandoned blocker is "
        "not an achieved one",
        field("state_reason") == ["completed", None, "not_planned"],
        f"answered {field('state_reason')!r}",
    )
    # ⛔ The answer's keys, exactly, at **both** levels -- and that is the arm this
    # case was rewritten for. The first form asserted that a hardcoded set of
    # verdict words was absent from the top level, which `{"number","blockers"}`
    # cannot contain and an empty dict satisfies: near-vacuous, and blind to the
    # place a verdict would actually be derived, which is the entry. Reproduced by
    # making the shared shaping derive one and watching the old assertion pass.
    # ⚠️ What is asserted is that the two levels carry these fields and no
    # others, so an added key reddens whichever level grew it.
    check(
        "and nothing beyond the fields the operation states, at either level",
        set(answered or {}) == {"number", "blockers"}
        and all(
            set(entry) == {"number", "state", "state_reason", "title", "url", "repo"}
            for entry in blockers or [{}]
        ),
        f"answered {sorted(answered or {})!r} over "
        f"{sorted((blockers or [{}])[0])!r}",
    )
    # ⛔ The paging flag is asserted on the **call**, not inferred from the answer:
    # the fake merges nothing, so an implementation reading one page would pass
    # every case above while shortening a real answer. ⚠️ Measured as the residue
    # of this fake rather than hidden -- what the client does with the flag is the
    # client's, and this holds that the flag is there to be acted on.
    paged = [call for call in recorded.calls if call.startswith("api")]
    check(
        "and asks for every page rather than the first",
        paged == ["api --paginate"],
        f"called {paged!r}",
    )
    # ⛔ The endpoint itself, as a literal. ⚠️ The direction case below compares
    # the call against the production helper, so it holds which object each half
    # addresses and says nothing about the address -- an endpoint renamed to
    # something that does not exist passed every case here, measured. ⚠️ The
    # sibling kind shares this helper and states the literal in its own suite, so
    # a rename reddens in both: one assertion per kind, which is what the shared
    # helper cannot give.
    read = [args for args in recorded.sent if args[:2] == ["api", "--paginate"]]
    check(
        "at the endpoint this host keeps the relation on, written out here once",
        read == [["api", "--paginate", f"repos/{own_repo}/issues/11/dependencies/blocked_by"]],
        f"called {read!r}",
    )
    # ⛔ An answer the shared grammar cannot read is a failed outcome and not a
    # traceback, which is the contract § 3 states. Two shapes, because the client's
    # own help says each page is a separate array and an outer wrapper is opt-in --
    # so both are shapes its merging could become.
    for label, planted in (
        ("an object where an array belongs", {"total_count": 1}),
        ("an array whose entry is not an item", ["#13"]),
    ):
        malformed = _Host({"api --paginate": planted})
        reported = with_host(malformed, lambda: unavailable(lambda: read_blockers(11)))
        check(
            f"and {label} is a failed call naming the call that made it",
            # ⚠️ The path through the production helper rather than as a literal:
            # the case above is what holds the literal, and spelling it here too
            # would make an endpoint rename redden three cases by one route.
            reported is not None and relation.blocked_by_path(own_repo, 11) in reported,
            f"got {reported!r}",
        )
    # ⛔ The guard, in the direction that matters: the path is the issues one,
    # which answers for a pull request, so a blocker list read with a pull request
    # number is an answer about the wrong object.
    guarded = _Host({"Item": _issue_payload(11, typename="PullRequest")})
    reported = with_host(guarded, lambda: unavailable(lambda: read_blockers(11)))
    check(
        "a pull request number is refused before the relation is read",
        reported is not None and "PullRequest" in reported
        and guarded.calls == ["Item"],
        f"got {reported!r} after {guarded.calls}",
    )
    # ⛔ And a value that is not a number at all is refused as a configuration
    # rather than let out as a `ValueError`, every operation here routing through
    # the same guard. The port catches the contract's own exceptions and nothing
    # else, so this is the difference between a reported refusal and a traceback.
    # ⚠️ The shapes are the ones `int()` accepts and an item number is not, that
    # being the guard's first form: a bool addresses item 1, a float addresses its
    # floor, a padded string addresses the number inside it, and a superscript
    # answers `isdigit` and then raises in `int` -- while the refusal's own
    # message says a value that is not a number addresses nothing.
    for handed in ("not-a-number", True, 1.9, " 11 ", "²"):
        shapeless = _Host({})
        reported = with_host(
            shapeless, lambda handed=handed: refused(lambda: read_blockers(handed))
        )
        check(
            f"{handed!r} is refused as an item number, before any call",
            reported == "tracker.operations.read_item" and shapeless.calls == [],
            f"reported {reported!r} after {shapeless.calls}",
        )
    check(
        "while the two shapes a number does arrive in are accepted",
        all(
            isinstance(
                (with_host(_Host({}), lambda handed=handed: read_blockers(handed))
                 or {}).get("number"),
                int,
            )
            for handed in (11, "11")
        ),
        "an integer or a string of digits was refused",
    )
    # ⛔ The repository address is matched whole, and this is the arm that holds
    # it: the guard's first form tested the arity of a split and was dead for
    # every input containing a slash, so a truncated or unexpected address came
    # back as a plausible-looking repository instead of as nothing. ⚠️ Asserted
    # through the shared module directly -- it is a pure shaping with no host in
    # it, and the alternative is a fixture per malformed address.
    misread = [
        address for address in (
            "https://api.example.invalid/repos",
            "https://api.example.invalid/",
            "https://api.example.invalid/repos/o/n/issues/13",
        )
        if relation.blocker({"repository_url": address})["repo"] is not None
    ]
    check(
        "an address this host did not write answers no repository rather than a guess",
        not misread
        and relation.blocker(
            {"repository_url": "https://api.example.invalid/repos/o/n/"}
        )["repo"] == "o/n",
        f"read a repository out of {misread!r}",
    )

    # --- `set_state`: the column, by name, read before written --------------
    #
    # A write is recognised by the document it goes through, one per value kind.
    def writes(host) -> list[str]:
        return [call for call in host.calls if call.startswith("Set")]

    _boards.clear()
    moved = _Host({"Item": _issue_payload(7, status="Todo")})
    with_host(moved, lambda: set_state(7, status="In Progress"))
    check(
        "an advance reads the item before it writes the column",
        writes(moved) and moved.calls.index("Item") < moved.calls.index(writes(moved)[0]),
        f"called {moved.calls}",
    )
    check("and writes it once", len(writes(moved)) == 1, f"called {moved.calls}")
    check(
        "through the document that writes an option, which is what a column of states holds",
        writes(moved) == ["SetOption"],
        f"wrote through {writes(moved)}",
    )

    _boards.clear()
    already = _Host({"Item": _issue_payload(7, status="In Progress")})
    with_host(already, lambda: set_state(7, status="In Progress"))
    check(
        "an advance to the column the card already holds writes nothing",
        not writes(already),
        f"called {already.calls}",
    )

    _boards.clear()
    unknown = _Host(
        {
            "Board": _board_payload_for(_page_of(FIELD_NODES)),
            "Item": _issue_payload(7),
        }
    )
    reported = with_host(unknown, lambda: refused(lambda: set_state(7, status="Shipped")))
    check(
        "a status word the board has no option for is refused, naming `statuses`",
        reported == "statuses",
        f"reported {reported!r}",
    )
    check(
        "and nothing was written for it",
        not writes(unknown),
        f"called {unknown.calls}",
    )

    _boards.clear()
    off_board = _Host(
        {
            "Board": _board_payload_for(_page_of(FIELD_NODES)),
            "Item": _issue_payload(7, on_board=False),
        }
    )
    reported = with_host(off_board, lambda: unavailable(lambda: set_state(7, status="Todo")))
    check(
        "an item with no card is refused with the remedy named, never added silently",
        reported is not None and "no card" in reported and "AddCard" not in off_board.calls,
        f"got {reported!r} after {off_board.calls}",
    )

    # A card on another board is not this board's card, which is the one thing
    # `projectItems` cannot be trusted to answer by itself.
    _boards.clear()
    elsewhere = _Host(
        {
            "Board": _board_payload_for(_page_of(FIELD_NODES)),
            "Item": _issue_payload(7, project_number=99),
        }
    )
    item = with_host(elsewhere, lambda: read_item(7))
    check(
        "a card on a different board is not read as this board's",
        item["on_board"] is False and item["status"] is None,
        f"read {item['card']!r}",
    )

    # --- the status field, and the key that has to be stated ----------------
    no_field = _example_configuration()
    no_field.data["tracker"].pop("status_field", None)
    bind(no_field)
    _boards.clear()
    reported = refused(lambda: _status_field())
    check(
        "a configuration naming no status field refuses the move, naming the key",
        reported == STATUS_FIELD_NAME,
        f"reported {reported!r}",
    )
    bind(configuration)

    # --- `set_field`: the column's own type decides the value ---------------
    #
    # ⛔ Asserted on the **document** and the **variable** the host is handed, not
    # on a value this suite rebuilt: the measured defect was a value sent as one
    # string where the host wants a typed input, and a case reading the string
    # back would have called that correct.
    for column, value, document, variable, sent_as in (
        # ⚠️ The number carries no variable at all, so what this case reads is the
        # document the host was handed: that is where the value is.
        ("Estimate", 3, "SetNumber", "number:3.0", None),
        ("Due", "2026-10-22", "SetDate", "date", "2026-10-22"),
        ("Notes", "a note", "SetText", "text", "a note"),
        ("Status", "Done", "SetOption", "option", "aaaaaaa4"),
    ):
        _boards.clear()
        host = _Host({"Item": _issue_payload(7)})
        sent: list[str] = []
        recording = host.__call__

        # ⚠️ Recorded from the **write** call only. A filter on the variable name
        # alone also caught the project's own number and the item's, which are
        # `number=` on two reads -- so the case read three values where one was
        # sent and reported a defect that was its own.
        def transport(
            args, parse=True, recording=recording, sent=sent,
            variable=variable, document=document, sent_as=sent_as,
        ):
            if any(document in part for part in args):
                sent.extend(
                    part for part in args
                    if part.startswith(f"{variable}=")
                    or (sent_as is None and variable in part)
                )
            return recording(args, parse)

        with_host(transport, lambda column=column, value=value: set_field(7, column, value))
        carried = f"{variable}={sent_as}" if sent_as is not None else variable
        check(
            f"a `{column}` column goes through `{document}`, carrying `{carried}`",
            writes(host) == [document]
            and len(sent) == 1
            and (sent == [carried] if sent_as is not None else variable in sent[0]),
            f"wrote through {writes(host)} carrying {sent!r}",
        )

    _boards.clear()
    host = _Host({"Board": _board_payload_for(_page_of(FIELD_NODES)), "Item": _issue_payload(7)})
    reported = with_host(host, lambda: refused(lambda: set_field(7, "Labels", "port")))
    check(
        "a host-managed column is refused for a write, naming the column",
        reported == "tracker.project.field.Labels",
        f"reported {reported!r}",
    )
    _boards.clear()
    host = _Host({"Board": _board_payload_for(_page_of(FIELD_NODES)), "Item": _issue_payload(7)})
    reported = with_host(host, lambda: refused(lambda: set_field(7, "Nowhere", 1)))
    check(
        "a column the board does not have is refused, naming it",
        reported == "tracker.project.field.Nowhere",
        f"reported {reported!r}",
    )
    _boards.clear()
    host = _Host({"Board": _board_payload_for(_page_of(FIELD_NODES)), "Item": _issue_payload(7)})
    reported = with_host(host, lambda: refused(lambda: set_field(7, "Estimate", "three")))
    check(
        "and a value the column's type cannot hold is refused before any write",
        reported == "tracker.project.field.Estimate" and not writes(host),
        f"reported {reported!r} after {host.calls}",
    )
    # ⛔ A column of options that is **not** the status column refuses on the
    # facet that points at it, never on `statuses`. A resolution that always named
    # the status key sent somebody to the wrong part of their configuration for
    # every column but one.
    _boards.clear()
    host = _Host({"Item": _issue_payload(7)})
    reported = with_host(host, lambda: refused(lambda: set_field(7, "Status", "Shipped")))
    check(
        "an option no column has is refused on the key the caller named, not on `statuses`",
        reported == "tracker.project.field.Status" and not writes(host),
        f"reported {reported!r} after {host.calls}",
    )

    # --- searching the board ------------------------------------------------
    _boards.clear()
    cards = [_item_card(index, f"item number {index}") for index in range(1, 151)]
    cards.append(_item_card(151, "a draft saying the same thing", kind="DraftIssue"))
    search_pages = {
        "Board": lambda after: _board_payload_for(_page_of(FIELD_NODES)),
        "Items": lambda after: {
            "repositoryOwner": {
                "projectV2": {
                    "items": _page_of(cards[:100], more=True, cursor="page-2")
                    if after is None
                    else _page_of(cards[100:])
                }
            }
        },
    }
    answer = with_host(_Host({}, pages=search_pages), lambda: search_items())
    check(
        "a board past one page is searched whole, not to the first page's ceiling",
        answer["scanned"] == len(cards) and len(answer["items"]) == 100,
        f"scanned {answer['scanned']}",
    )
    check(
        "and the bound it reports is about the matches, which it can state exactly",
        answer["at_limit"] is True and answer["limit"] == 100,
        f"reported {answer['at_limit']!r}",
    )
    check(
        "a draft card is carried with its kind and no number, rather than dropped",
        any(entry["kind"] == "draft" and entry["number"] is None for entry in answer["items"])
        or any(entry["kind"] == "draft" for entry in
               with_host(_Host({}, pages=search_pages),
                         lambda: search_items(terms="draft"))["items"]),
    )
    terms = with_host(
        _Host({}, pages=search_pages), lambda: search_items(terms="42 number")
    )
    check(
        "every term is a substring of the title, in any order -- the recall a "
        "duplicate check wants",
        [entry["number"] for entry in terms["items"]] == [42, 142],
        f"matched {[entry['number'] for entry in terms['items']]}",
    )
    upper = with_host(
        _Host({}, pages=search_pages), lambda: search_items(terms="NUMBER 42")
    )
    check(
        "and the case of neither side decides it",
        [entry["number"] for entry in upper["items"]] == [42, 142],
        f"matched {[entry['number'] for entry in upper['items']]}",
    )
    nothing = with_host(
        _Host({}, pages=search_pages), lambda: search_items(terms="number 999")
    )
    check(
        "a term nothing carries answers empty, which is what makes the matching bite",
        nothing["items"] == [] and nothing["scanned"] == len(cards),
        f"matched {len(nothing['items'])} of {nothing['scanned']}",
    )
    by_field = with_host(
        _Host({}, pages=search_pages), lambda: search_items(fields={"Status": "Todo"})
    )
    check(
        "a field's value with no terms at all is a query of its own",
        by_field["scanned"] == len(cards) and len(by_field["items"]) == 100,
        f"matched {len(by_field['items'])}",
    )
    none_match = with_host(
        _Host({}, pages=search_pages), lambda: search_items(fields={"Status": "Merged"})
    )
    check(
        "and a column nothing is in answers empty rather than matching everything",
        none_match["items"] == [],
        f"matched {len(none_match['items'])}",
    )
    _boards.clear()
    reported = with_host(
        _Host({}, pages=search_pages),
        lambda: refused(lambda: search_items(fields={"Nowhere": "x"})),
    )
    check(
        "a field name the board does not have is refused, never answered empty",
        reported == "tracker.project.field.Nowhere",
        f"reported {reported!r}",
    )

    # The label guard, through the second seam -- the one path that reads a
    # failure rather than a body. ⚠️ Each of the three answers is a different
    # fact, and the empty one is the only reading that lies.
    def with_probe(answer, call):
        was = under_test.PROBE
        under_test.PROBE = lambda args: answer
        try:
            return call()
        finally:
            under_test.PROBE = was

    _boards.clear()
    absent = with_probe(
        (1, "", f"gh: Not Found {NOT_FOUND}"),
        lambda: with_host(
            _Host({}, pages=search_pages),
            lambda: unavailable(lambda: search_items(labels=["nothing-carries-this"])),
        ),
    )
    check(
        "an empty answer under a label the repository does not have is refused",
        absent is not None and "never running" in absent,
        f"got {absent!r}",
    )
    _boards.clear()
    real = with_probe(
        (0, "a-real-label\n", ""),
        lambda: with_host(
            _Host({}, pages=search_pages),
            lambda: search_items(labels=["a-real-label"]),
        ),
    )
    check(
        "while an empty answer under a label it does have is an answer",
        isinstance(real, dict) and real["items"] == [] and real["scanned"] == len(cards),
        f"got {real!r}",
    )
    _boards.clear()
    unestablished = with_probe(
        (1, "", "502 Bad Gateway"),
        lambda: with_host(
            _Host({}, pages=search_pages),
            lambda: unavailable(lambda: search_items(labels=["unknowable"])),
        ),
    )
    check(
        "and a label that could not be established is neither of those two",
        unestablished is not None and "could not be established" in unestablished,
        f"got {unestablished!r}",
    )

    # --- the host answering an error, and the arm that catches it -----------
    _boards.clear()
    erroring = _Host({"Item": {"data": {"repository": None}, "errors": [{"message": "bad credentials"}]}})
    reported = with_host(erroring, lambda: unavailable(lambda: read_item(7)))
    check(
        "a GraphQL error is a failed call, not an answer, even with data beside it",
        reported is not None and "bad credentials" in reported,
        f"got {reported!r}",
    )

    # --- `advance_on_merge`: three facts, one judgement ---------------------
    _boards.clear()
    merged_answer = {
        "repository": {
            "issue": {
                "state": "CLOSED",
                "closedByPullRequestsReferences": _page_of(
                    [{"number": 20, "merged": True, "mergeCommit": {"oid": "abc123"}}]
                ),
            }
        }
    }
    host = _Host({
        "Board": _board_payload_for(_page_of(FIELD_NODES)),
        "Item": _issue_payload(7, status="Merged"),
        "ClosedBy": merged_answer,
    })
    answered = with_host(host, lambda: advance_on_merge(7))
    check(
        "an item closed by a merged pull request reads as advanced, with the column reported",
        answered["advanced"] is True
        and answered["status"] == "Merged"
        and answered["merged_by"] == [{"pull_request": 20, "commit": "abc123"}],
        f"answered {answered!r}",
    )
    by_hand = dict(merged_answer["repository"]["issue"])
    by_hand["closedByPullRequestsReferences"] = _page_of(
        [{"number": 21, "merged": False, "mergeCommit": None}]
    )
    host = _Host({
        "Board": _board_payload_for(_page_of(FIELD_NODES)),
        "Item": _issue_payload(7, status="Todo"),
        "ClosedBy": {"repository": {"issue": by_hand}},
    })
    answered = with_host(host, lambda: advance_on_merge(7))
    check(
        "an item closed with nothing merged is not advanced, and says what state it is in",
        answered["advanced"] is False and answered["state"] == "CLOSED",
        f"answered {answered!r}",
    )
    # ⛔ Asked with text, which is how the port passes every argument -- so the
    # number in the answer is the host's own and the typed query variable is built
    # from it rather than from what the caller spelled. ⚠️ Every case above hands
    # an integer, where an echo and a read are the same value.
    host = _Host({
        "Board": _board_payload_for(_page_of(FIELD_NODES)),
        "Item": _issue_payload(7, status="Merged"),
        "ClosedBy": merged_answer,
    })
    as_text = with_host(host, lambda: advance_on_merge("7"))
    check(
        "and asked with text it answers the host's own number, not the argument",
        isinstance((as_text or {}).get("number"), int)
        and (as_text or {}).get("number") == 7,
        f"answered {(as_text or {}).get('number')!r}",
    )
    # ⛔ And the variable goes out **typed**, which is the observable the sibling
    # kind does not have: the client picks its flag off the value's own type, so a
    # query variable built from the argument's text would be sent as an untyped
    # one against an `Int!` and refused by the host. ⚠️ Asserted on the flag and
    # not on the rendered value, which is identical either way.
    sent = [args for args in host.sent if "ClosedBy" in " ".join(args)]
    typed = [
        args[index - 1]
        for args in sent
        for index, part in enumerate(args)
        if part.startswith("number=")
    ]
    check(
        "and the query variable for it is sent typed rather than as text",
        typed == ["-F"],
        f"sent {typed!r} out of {sent!r}",
    )
    # ⛔ A repository the credential cannot see answers `repository: null`, and a
    # null is not an absent key -- so a default on the lookup does not apply to it
    # and the plain form raises an attribute error where this operation's own
    # refusal belongs. The arm is reachable through a transport that answers
    # without an error array, which is what a suite is.
    _boards.clear()
    host = _Host({
        "Item": _issue_payload(7),
        "ClosedBy": {"repository": None},
    })
    reported = with_host(host, lambda: unavailable(lambda: advance_on_merge(7)))
    check(
        "a repository that answers null is this operation's refusal, not a traceback",
        reported is not None and "could not be read" in reported,
        f"got {reported!r}",
    )

    # --- `create_item`: the issue, then the card ----------------------------
    _boards.clear()
    filed = {"n": 0}

    def _filed_item(args, filed=filed):
        filed["n"] += 1
        return _issue_payload(31, on_board=filed["n"] > 1)

    host = _Host({
        "Board": _board_payload_for(_page_of(FIELD_NODES)),
        "issue create": "https://example.invalid/issues/31",
        "Item": _filed_item,
        "AddCard": {"addProjectV2ItemById": {"item": {"id": "PVTI_card"}}},
    })
    created = with_host(host, lambda: create_item("a title", "a body", ["port"]))
    check(
        "a filing creates the issue, then adds the card, in that order",
        host.calls.index("issue create") < host.calls.index("AddCard")
        and created["on_board"] is True,
        f"called {host.calls}",
    )
    check(
        "and writes no status, which is the role's own advance to make",
        not writes(host),
        f"called {host.calls}",
    )

    # ⛔ The module left as the port found it. This suite binds a configuration
    # and resolves boards against a substituted host; a run inside a longer
    # process -- which is what the gate's runner is -- would otherwise leave an
    # example's address cached behind a real role's first call.
    bind(None)
    _boards.clear()

    if failures:
        print(f"\n{failures} assertion(s) did not hold.")
    return 1 if failures else 0


# ⛔ An entry point, for the reason the hosted tracker's suite beside this one
# states: a run that asserts nothing exits zero and reads as a held mechanism.
if __name__ == "__main__":
    sys.exit(self_test())


