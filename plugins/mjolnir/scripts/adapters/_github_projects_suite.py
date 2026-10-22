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
        "Item": _issue_payload(),
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

    def _answer_for(self, name: str):
        for table in (self.answers, self.defaults):
            if name in table:
                return table[name]
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
        and discovered is not port.TRACKERLESS
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
    check(
        "a value that can travel as a variable does, rather than as the input object "
        "the host refuses",
        all(
            f"${variable}:" in document and "ProjectV2FieldValue" not in document
            for document, variables in [WRITES[kind]("x") for kind in (SINGLE_SELECT, TEXT, DATE)]
            for variable in variables
        ),
    )
    number_document, number_variables = WRITES[NUMBER](2.5)
    check(
        "and the one that cannot is formatted in as a number, with nothing quotable left",
        not number_variables and "value:{number:2.5}" in number_document,
        f"built {number_document.strip().splitlines()[-4:]!r}",
    )
    check(
        "a number that is not finite is refused rather than formatted into a request",
        refused(lambda: WRITES[NUMBER](float("inf"))) == "tracker.project.field",
        f"reported {refused(lambda: WRITES[NUMBER](float('inf')))!r}",
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

    check(
        "`item_number` and `link_for_close` reach the host at all",
        item_number(12) == 12 and item_number({"number": 13}) == 13
        and link_for_close(14) == "Closes #14",
    )
    silent = _Host({})
    with_host(silent, lambda: (item_number(12), link_for_close(12)))
    check("without making a host call", silent.calls == [], f"called {silent.calls}")

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


