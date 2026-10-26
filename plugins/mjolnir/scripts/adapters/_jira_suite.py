#!/usr/bin/env python3
"""The issue implementation's suite: the shapes it was written against, as code.

⛔ **A module of its own rather than a mode of the implementation**, for the
reason the two suites beside it record: a single file carrying both reaches the
code host with no patch, and the gate that holds every added line to the
deferral rule refuses a change it cannot read. ⚠️ The name opens with `_` so that
discovery skips it -- a module in the port's `adapters/` package that names no
kind is refused rather than skipped, which is right for an implementation and
wrong for a suite.

What it holds, and what it cannot reach, are recorded in
`docs/single-source-of-truth.md` § Beside the contract. Nothing here restates
them.

⛔ **No item key is written as a literal anywhere in this file.** Every key is
composed from the project key the shipped example states, which is both the
house rule about identifiers that resolve on somebody's tracker and the reason
the fixture cannot drift from the configuration it is supposed to be a fixture
for.

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

from adapters import jira as under_test  # noqa: E402
from adapters.jira import (  # noqa: E402
    ACCOUNT_VARIABLE,
    ADAPTER,
    BLOCKS,
    DELIBERATELY_ABSENT,
    KIND,
    NOT_RENDERED,
    OWNED_ELSEWHERE,
    QUERYABLE,
    RENDERED,
    TOKEN_VARIABLE,
    _sites,
    as_document,
    as_query,
    as_text,
    assign,
    bind,
    comment,
    create_item,
    item_number,
    link_dependency,
    advance_on_merge,
    read_item,
    search_items,
    set_field,
    set_labels,
    set_state,
)

# What the suite puts in the shell so a call can be made at all, and ⛔ what no
# message may contain. ⚠️ **Both** of them: the token for the obvious reason, and
# the account because it is an address, which § 14 bars from a surface outside
# the project just as firmly. The values are recognisable on purpose -- one case
# fails a call and reads the message for them.
AN_ACCOUNT = "ACCOUNT-VALUE-THAT-MUST-NOT-APPEAR"
A_TOKEN = "TOKEN-VALUE-THAT-MUST-NOT-APPEAR"

# Who this credential is, and somebody else. ⛔ Opaque ids rather than names or
# addresses, which is what this tracker answers with and what `assign` writes.
ME = "account-0000-this-credential"
SOMEBODY = "account-0001-somebody-else"

# The interface path a failure message quotes, read from the implementation
# rather than written here: the version is part of the address, and a literal
# would stop matching the day it moves.
API_SHOWN = under_test.API

# The field catalogue this site answers with. ⛔ Every entry carries the whole
# production shape -- an id, a display name and a schema -- because the three
# things the implementation does with a field are resolve the name, read the id
# and shape by the type, and a fixture short of any of them leaves one unreached.
#
# ⚠️ The display names are deliberately **not** the ids: a field is addressed by
# name here and resolved per site, and a fixture whose names equalled its ids
# would let a guard that matched the caller's spelling read as correct.
FIELDS = [
    {"id": "summary", "name": "Summary", "schema": {"type": "string"}},
    {"id": "description", "name": "Description", "schema": {"type": "string"}},
    {"id": "duedate", "name": "Due date", "schema": {"type": "date"}},
    {"id": "timetracking", "name": "Time tracking", "schema": {"type": "timetracking"}},
    {"id": "priority", "name": "Priority", "schema": {"type": "priority"}},
    {"id": "labels", "name": "Labels", "schema": {"type": "array"}},
    {"id": "status", "name": "Status", "schema": {"type": "status"}},
    {"id": "assignee", "name": "Assignee", "schema": {"type": "user"}},
    # A custom field, with the site-specific id that is the whole reason a field
    # is addressed by name: readable by name, and refused for a write because
    # this implementation has no shape for its type.
    {"id": "customfield_10020", "name": "Sprint", "schema": {"type": "array"}},
    # A number field, which is shaped, so the refusal above is about the type
    # and not about the field being custom.
    {"id": "customfield_10030", "name": "Story points", "schema": {"type": "number"}},
]

# Two fields carrying one name, which this tracker allows and which has no
# reading. ⛔ Kept out of the default catalogue and added by the case that wants
# it: a fixture that always carried the ambiguity would make every other case
# assert the refusal instead of the behaviour.
TWINS = [
    {"id": "customfield_10040", "name": "Twinned", "schema": {"type": "number"}},
    {"id": "customfield_10041", "name": "Twinned", "schema": {"type": "number"}},
]

# A body using every shape the renderer carries, and one it does not. ⚠️ The
# second is the honest half: what is not rendered comes back as the text it was
# written as, which is lossy and **visible** rather than lossy and silent.
A_BODY = "\n".join([
    "## What this is",
    "",
    "A paragraph, which is the commonest block there is",
    "and which carries a second line.",
    "",
    "- the first thing",
    "- the second thing",
    "",
    "1. one step",
    "2. another step",
    "",
    "```python",
    "return 1",
    "```",
])

A_TABLE = "\n".join([
    "| one | two |",
    "|---|---|",
    "| a | b |",
])

# ⛔ One plant per class the surface states, and a green-side plant beside them:
# an exemption with nothing asserted to stay green is a guard that could be
# refusing everything and reading as correct.
PLANTS = {
    "source_code": "the fix is\n\n```python\nreturn 1\n```\n",
    "file_paths": "it is in plugins/mjolnir/scripts/adapters/jira.py",
    "hosting_details": "reachable at https://internal.example.invalid/admin",
    "branch_names": "landed on feat/5-a-thing yesterday",
}

# ⚠️ Assembled rather than written as a literal, for the reason § 14's own arm
# assembles its plants: a file carrying a token-shaped literal is a secret
# committed by the check that exists to stop that, and the host's own push
# protection refuses the push.
PLANTS["credentials"] = "the key is " + "gh" + "p_" + ("A" * 36)

STAYS_GREEN = (
    "The gate went red on the second predicate, so the item stays where it is "
    "and the person who wrote it has one thing to fix rather than four."
)

# The parameters a write carries that reach the **item** rather than the address.
# ⛔ The distinction is the whole of the policy sweep: a policy bars what an item
# holds, and the path a call is made to is not something an item holds.
TEXT_FIELDS = ("summary", "description")


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


def _statuses(configuration) -> list[dict]:
    return list(configuration.get("statuses") or [])


def _status_names(configuration) -> list[str]:
    return [str(status.get("name")) for status in _statuses(configuration)]


def _role_status(configuration, role: str) -> str | None:
    for status in _statuses(configuration):
        if status.get("role") == role:
            return str(status.get("name"))
    return None


def _category(configuration, name: str) -> str:
    """The tracker's own three-way category behind a project's status word.

    ⛔ Derived from the roles the example maps rather than written: `status` and
    `state` are reported apart by the implementation, and a fixture that gave
    every status one category would leave that distinction unasserted.
    """
    if name == _role_status(configuration, "initial"):
        return "new"
    if name == _role_status(configuration, "terminal"):
        return "done"
    return "indeterminate"


def _a_type(configuration) -> str:
    """One of the types the example states, for a filing to carry.

    ⛔ Read off § 4.1's own `values` rather than written here: the carrier is
    native on this tracker, so the word is the tracker's and the example is where
    this project's are stated.
    """
    values = configuration.get("work_item.type.values") or []
    return str(values[0]) if values else "Task"


# --- the host, as one seam ---------------------------------------------------
#
# ⛔ Routes in order, longest first where one path prefixes another. ⚠️ That
# ordering is a rule about this fake and is asserted below: `GET /issue/<key>`
# and `GET /issue/<key>/transitions` differ only in a suffix, and a fake that
# matched the shorter one first would answer a transition list as an issue -- the
# same shadowing the two suites beside this one record.

ROUTES = [
    ("GET", r"^/field$", "fields"),
    ("GET", r"^/myself$", "me"),
    ("GET", r"^/search/jql$", "search"),
    ("GET", r"^/issue/[^/]+/transitions$", "transitions"),
    ("POST", r"^/issue/[^/]+/transitions$", "transition"),
    ("POST", r"^/issue/[^/]+/comment$", "comment"),
    ("PUT", r"^/issue/[^/]+/assignee$", "assignee"),
    ("GET", r"^/issue/[^/]+$", "issue"),
    ("PUT", r"^/issue/[^/]+$", "update"),
    ("POST", r"^/issue$", "create"),
    ("POST", r"^/issueLink$", "link"),
]


def route(method: str, path: str) -> str | None:
    for verb, pattern, name in ROUTES:
        if verb == method and re.match(pattern, path):
            return name
    return None


class _Host:
    """A transport that answers as the host does, and records what was asked.

    ⛔ A fake rather than a mock: it answers by **which route was called** rather
    than by the order this module happens to call in, so a refactor that reorders
    calls does not redden it and a call that moves to the wrong object does.

    ⛔ **It keeps state, which the two fakes beside it do not need to.** Three
    properties of this implementation are only reachable through a write followed
    by a read -- the dependency direction, a set of labels that replaces rather
    than adds, and a transition that lands on the status it was matched by -- so
    the writes below mutate the stored items and the reads answer from them.
    ⚠️ **And the link is stored by the host's own rule rather than by the
    adapter's choice**: an entry on the outward issue carries `inwardIssue` and
    the other way round, which is what makes the direction a round trip can fail.
    """

    def __init__(self, configuration, answers: dict | None = None, issues=None):
        self.configuration = configuration
        self.answers = dict(answers or {})
        self.issues = {
            issue["key"]: issue
            for issue in (self._default_issues() if issues is None else issues)
        }
        self.fields = list(self.answers.pop("<fields>", FIELDS))
        self.changelog: dict[str, list[dict]] = dict(self.answers.pop("<changelog>", {}))
        self.filed = 0
        self.calls: list[str] = []
        self.sent: list[tuple[str, dict]] = []
        self.addressed: list[str] = []
        self.authorised: list[bool] = []

    # -- the items this site holds

    def key(self, number: int) -> str:
        return f"{self.configuration.get('tracker.project_key')}-{number}"

    def _issue(
        self,
        number: int,
        summary: str,
        *,
        status: str | None = None,
        labels=(),
        assignee: str | None = None,
        body: str | None = None,
        estimate: str | None = None,
    ) -> dict:
        names = _status_names(self.configuration)
        word = status or names[0]
        return {
            "id": str(10000 + number),
            "key": self.key(number),
            "fields": {
                "summary": summary,
                "description": as_document(A_BODY if body is None else body),
                "status": {
                    "name": word,
                    "statusCategory": {"key": _category(self.configuration, word)},
                },
                "issuetype": {"name": _a_type(self.configuration)},
                "priority": {"name": "Medium"},
                "labels": list(labels),
                "assignee": None if assignee is None else {
                    "accountId": assignee, "displayName": "Whoever"
                },
                "issuelinks": [],
                "timetracking": {} if estimate is None else {"originalEstimate": estimate},
                "duedate": None,
                "fixVersions": [],
                "created": "2026-10-01T00:00:00.000+0000",
                "updated": "2026-10-02T00:00:00.000+0000",
                "customfield_10020": [{"name": "a sprint"}],
                "customfield_10030": None,
            },
        }

    def _default_issues(self) -> list[dict]:
        names = _status_names(self.configuration)
        return [
            self._issue(1, "a first item", labels=["alpha"]),
            self._issue(
                2, "a second item", status=names[1] if len(names) > 1 else names[0]
            ),
            self._issue(3, "a third item", assignee=ME, estimate="2h"),
        ]

    def item(self, path: str) -> dict:
        wanted = path.split("/")[2]
        if wanted not in self.issues:
            raise AssertionError(
                f"this suite's host was asked for `{wanted}`, which it does not "
                "hold -- a call addressed an item no fixture states"
            )
        return self.issues[wanted]

    # -- the routes

    def _answer_issue(self, path: str, params: dict, _body) -> dict:
        issue = self.item(path)
        wanted = {name for name in str(params.get("fields") or "").split(",") if name}
        fields = (
            issue["fields"]
            if not wanted
            else {
                name: value for name, value in issue["fields"].items() if name in wanted
            }
        )
        answer = {"id": issue["id"], "key": issue["key"], "fields": fields}
        if "changelog" in str(params.get("expand") or ""):
            # ⚠️ Newest first, which is the one ordering this host's own
            # item-level history gives -- and the bound the operation reading it
            # states, since it is one page and not the whole log.
            answer["changelog"] = {
                "histories": list(self.changelog.get(issue["key"], []))
            }
        return answer

    def _answer_transitions(self, path: str, _params, _body) -> dict:
        issue = self.item(path)
        here = issue["fields"]["status"]["name"]
        offered = []
        for index, name in enumerate(_status_names(self.configuration)):
            if name == here:
                continue
            # ⛔ The transition's own name is deliberately **not** the status it
            # leads to. Every workflow is free to name a verb nothing like its
            # target, and a fixture whose two fields agreed would let an
            # implementation matching the wrong one read as correct.
            offered.append({
                "id": str(10 + index),
                "name": f"a verb {index}",
                "to": {
                    "name": name,
                    "statusCategory": {"key": _category(self.configuration, name)},
                },
                "hasScreen": False,
                "isAvailable": True,
            })
        return {"transitions": offered}

    def _do_transition(self, path: str, _params, body) -> None:
        issue = self.item(path)
        wanted = str(((body or {}).get("transition") or {}).get("id"))
        for move in self._answer_transitions(path, {}, None)["transitions"]:
            if move["id"] == wanted:
                issue["fields"]["status"] = {
                    "name": move["to"]["name"],
                    "statusCategory": move["to"]["statusCategory"],
                }
                return None
        raise AssertionError(
            f"this suite's host was asked for transition `{wanted}`, which it did "
            "not offer -- the id written was not one read"
        )

    def _do_update(self, path: str, _params, body) -> None:
        issue = self.item(path)
        for name, value in ((body or {}).get("fields") or {}).items():
            issue["fields"][name] = value
        return None

    def _do_assignee(self, path: str, _params, body) -> None:
        issue = self.item(path)
        account = (body or {}).get("accountId")
        issue["fields"]["assignee"] = (
            None if account is None else {"accountId": account, "displayName": "Whoever"}
        )
        return None

    def _do_create(self, _path, _params, body) -> dict:
        fields = (body or {}).get("fields") or {}
        self.filed += 1
        number = 100 + self.filed
        issue = self._issue(
            number,
            str(fields.get("summary") or ""),
            labels=list(fields.get("labels") or []),
        )
        issue["fields"]["description"] = fields.get("description")
        issue["fields"]["issuetype"] = {"name": str((fields.get("issuetype") or {}).get("name"))}
        self.issues[issue["key"]] = issue
        return {"id": issue["id"], "key": issue["key"], "self": "<the item's own address>"}

    def _do_link(self, _path, _params, body) -> None:
        """One link, stored by **this host's** rule and not by the adapter's.

        ⛔ The entry an issue carries names the *other* side, so the outward
        issue's entry holds `inwardIssue` and the inward issue's holds
        `outwardIssue`. Which is what makes the direction falsifiable: an adapter
        that swapped the two would write a link this stores the other way round,
        and the read-back would name the wrong item.
        """
        body = body or {}
        kind = (body.get("type") or {}).get("name")
        inward = (body.get("inwardIssue") or {}).get("key")
        outward = (body.get("outwardIssue") or {}).get("key")
        for key, side, other in ((outward, "inwardIssue", inward), (inward, "outwardIssue", outward)):
            if key not in self.issues:
                raise AssertionError(
                    f"this suite's host was asked to link `{key}`, which it does "
                    "not hold"
                )
            self.issues[key]["fields"]["issuelinks"].append({
                "id": f"link-{len(self.issues[key]['fields']['issuelinks']) + 1}",
                "type": {
                    "name": kind,
                    "inward": under_test.INWARD_READS,
                    "outward": under_test.OUTWARD_READS,
                },
                side: {
                    "key": other,
                    "fields": {"status": self.issues[other]["fields"]["status"]},
                },
            })
        return None

    def _answer_search(self, _path, params: dict, _body) -> dict:
        return {
            "issues": list(self.issues.values()),
            "isLast": True,
            "jql": params.get("jql"),
        }

    def defaults(self) -> dict:
        return {
            "fields": lambda *_: self.fields,
            "me": lambda *_: {"accountId": ME, "displayName": "This Credential"},
            "issue": self._answer_issue,
            "transitions": self._answer_transitions,
            "transition": self._do_transition,
            "update": self._do_update,
            "assignee": self._do_assignee,
            "comment": lambda *_: {"id": "comment-1"},
            "create": self._do_create,
            "link": self._do_link,
            "search": self._answer_search,
        }

    def __call__(
        self,
        method: str,
        path: str,
        params=None,
        body=None,
        *,
        where: str = "",
        auth: str = "",
    ) -> tuple[int, str]:
        # ⛔ Recorded rather than ignored. The address and the credential are
        # resolved above this seam, and a transport that was handed neither is
        # how a guard on either comes to be unreachable -- which is the defect
        # this suite found and the assertion below is what holds it.
        self.addressed.append(where)
        self.authorised.append(bool(auth))
        name = route(method, path)
        if name is None:
            raise AssertionError(
                f"this suite's host was called as `{method} {path}`, which no route "
                "of it names -- a call that moved to another object, or a route the "
                "fake has not grown yet"
            )
        self.calls.append(name)
        self.sent.append((name, {"path": path, "params": dict(params or {}), "body": body}))
        answer = self.answers.get(name, self.defaults()[name])
        if callable(answer):
            answer = answer(path, dict(params or {}), body)
        if isinstance(answer, tuple):
            return answer
        if answer is None:
            # The empty answer two of this host's writes give, which is a `204`
            # and not a body nobody sent.
            return 204, ""
        if isinstance(answer, str):
            return 200, answer
        return 200, json.dumps(answer)

    def writes(self) -> list[str]:
        reads = {"fields", "me", "issue", "transitions", "search"}
        return [call for call in self.calls if call not in reads]

    def sent_for(self, name: str) -> list[dict]:
        return [what for called, what in self.sent if called == name]


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

    def got(answer, key, default=None):
        """One key out of an operation's answer, or `default` where it failed."""
        return answer.get(key, default) if isinstance(answer, dict) else default

    def keys_of(answer, key) -> list:
        return [entry.get("key") for entry in (got(answer, key) or [])]

    def body_of(host, name) -> dict:
        made = host.sent_for(name)
        return (made[0]["body"] or {}) if made else {}

    def params_of(host, name) -> dict:
        made = host.sent_for(name)
        return made[0]["params"] if made else {}

    # The shell this suite runs its calls in. ⛔ Set here and restored at the
    # end: `_credentials` reads the environment, so without this every case
    # below would be asserting the same missing-variable failure.
    was_environment = {
        name: os.environ.get(name) for name in (ACCOUNT_VARIABLE, TOKEN_VARIABLE)
    }
    os.environ[ACCOUNT_VARIABLE], os.environ[TOKEN_VARIABLE] = AN_ACCOUNT, A_TOKEN

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
    _sites.clear()

    def host(answers: dict | None = None, issues=None) -> _Host:
        _sites.clear()
        return _Host(configuration, answers, issues)

    # ⛔ The status words, the project key and the type these cases use are read
    # off the example, never written here: a literal would be a second statement
    # of the same vocabulary and would rot the day the example is reworded.
    names = _status_names(configuration)
    project = str(configuration.get("tracker.project_key") or "")
    initial = _role_status(configuration, "initial")
    second = names[1] if len(names) > 1 else None
    third = names[2] if len(names) > 2 else None
    check(
        "the example states a project key, an `initial` role and two more statuses",
        bool(project) and bool(initial) and bool(second) and bool(third),
        f"states project={project!r} initial={initial!r} second={second!r} third={third!r}",
    )
    if not (project and initial and second and third):
        print(f"\n{failures} assertion(s) did not hold.")
        return 1

    def key(number: int) -> str:
        return f"{project}-{number}"

    def foreign(number: int) -> str:
        """A key of **another** project, composed rather than written.

        ⛔ No item key is a literal anywhere in this file: a quoted string of
        that shape reads as an identifier resolving on somebody's tracker, which
        the sweep in `tools/` forbids anywhere in the tree. Composing it from the
        example's own key is also what keeps this fixture from drifting away
        from the configuration it is a fixture for.
        """
        return f"{project}X-{number}"

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
    # ⛔ Read through `check`, not beside it. Discovery refuses a module in the
    # package it cannot import, so a stray file beside this one takes the
    # registry down -- and an uncaught refusal here ends the run on a traceback
    # where the verdict and the count belong.
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
    # ⛔ The claim about this kind that cannot be read off the absence list in
    # general: there is no closing keyword here, so this is the first
    # implementation to leave `link_for_close` absent while implementing the
    # advance that follows a merge.
    check(
        "`link_for_close` is absent while `advance_on_merge` is implemented",
        "link_for_close" not in ADAPTER.operations
        and "advance_on_merge" in ADAPTER.operations,
    )
    absent_port = port.Port(configuration, adapter=ADAPTER, stated=stated)
    outcomes = {name: absent_port.invoke(name) for name in DELIBERATELY_ABSENT}
    check(
        "each absent operation comes back as the surface's stated fallback",
        all(
            not outcome.performed and not outcome.failed and outcome.detail == stated[name]
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

    # --- the identifier, and the project guard ------------------------------
    check("a key is the identifier, returned as given", item_number(key(7)) == key(7))
    check(
        "and is read off an item the same way",
        item_number({"key": key(8)}) == key(8),
        f"read {ran(lambda: item_number({'key': key(8)}))!r}",
    )
    reported = refused(lambda: item_number({"id": "10001"}))
    check(
        "an item carrying no key is refused, naming the operation",
        reported == "tracker.operations.item_number",
        f"reported {reported!r}",
    )
    reported = refused(lambda: item_number(7))
    check(
        "and a bare number is refused too, this tracker having no such identifier",
        reported == "tracker.operations.item_number",
        f"reported {reported!r}",
    )
    silent = host()
    with_host(silent, lambda: (item_number(key(7)), item_number({"key": key(8)})))
    check("and none of that reaches the host", silent.calls == [], f"called {silent.calls}")

    # ⛔ The guard this tracker needs, and the direction that matters: a key from
    # another project resolves site-wide, so the refusal has to come **before**
    # the call rather than from the host.
    elsewhere_project = host()
    reported = with_host(
        elsewhere_project, lambda: refused(lambda: read_item(foreign(1)))
    )
    check(
        "a key from another project is refused, naming `tracker.project_key`",
        reported == "tracker.project_key" and elsewhere_project.calls == [],
        f"reported {reported!r} after {elsewhere_project.calls}",
    )
    shapeless = host()
    reported = with_host(shapeless, lambda: refused(lambda: read_item("not-a-key")))
    check(
        "a value that is not a key is refused before any call, naming the operation",
        reported == "tracker.operations.read_item" and shapeless.calls == [],
        f"reported {reported!r} after {shapeless.calls}",
    )
    # ⛔ And the guard covers the **writes**, which is the whole reason every
    # operation resolves its key through `read_item` first.
    for label, call in (
        ("comment", lambda: comment(foreign(1), "a note")),
        ("set_labels", lambda: set_labels(foreign(1), ["alpha"])),
        ("assign", lambda: assign(foreign(1))),
        ("set_state", lambda: set_state(foreign(1), status=second)),
        ("link_dependency", lambda: link_dependency(foreign(1), key(1))),
        ("advance_on_merge", lambda: advance_on_merge(foreign(1))),
    ):
        guarded = host()
        reported = with_host(guarded, lambda call=call: refused(call))
        check(
            f"`{label}` refuses another project's key before it writes anything",
            reported == "tracker.project_key" and not guarded.writes(),
            f"reported {reported!r} after {guarded.calls}",
        )

    # --- reading --------------------------------------------------------------
    reading = host()
    item = with_host(reading, lambda: read_item(key(1)))
    check(
        "an item's status is the project's own word, which is § 4.2's vocabulary",
        got(item, "status") == initial,
        f"read {item!r}",
    )
    check(
        "and the tracker's own category behind it is reported apart, never as the status",
        got(item, "state") == "new",
        f"read {got(item, 'state')!r}",
    )
    check(
        "the body comes back as text, the host holding it as a document",
        got(item, "body") == A_BODY,
        f"read {got(item, 'body')!r}",
    )
    check(
        "and one call does it",
        reading.calls.count("issue") == 1,
        f"called {reading.calls}",
    )
    # ⛔ The seam is handed the address and the credential rather than resolving
    # them. Measured on this module's first draft, where both were resolved
    # inside the transport: every guard on either was then a guard a substituted
    # transport walked past, and three refusals this suite asserts happened after
    # the call rather than before it.
    check(
        "the transport is handed the configured site rather than composing one",
        elsewhere_project.addressed == []
        and reading.addressed == [str(configuration.get("tracker.site"))],
        f"addressed {reading.addressed!r}",
    )
    check(
        "and is handed a credential it did not read for itself",
        reading.authorised == [True],
        f"authorised {reading.authorised!r}",
    )
    check(
        "a field nobody asked for is absent from the answer, never carried as None",
        "fields" not in (item if isinstance(item, dict) else {}),
        f"carried {sorted(item) if isinstance(item, dict) else item!r}",
    )
    named = with_host(host(), lambda: read_item(key(1), fields=["Sprint"]))
    check(
        "a named field is answered under the name it was asked with, not the site's id",
        list((got(named, "fields") or {})) == ["Sprint"]
        and got(named, "fields")["Sprint"] == [{"name": "a sprint"}],
        f"read {got(named, 'fields')!r}",
    )
    rereading = host()
    reported = with_host(
        rereading, lambda: refused(lambda: read_item(key(1), fields=["No such field"]))
    )
    check(
        "a field name the site does not have re-reads the catalogue once, then refuses",
        reported == "tracker.operations.read_item" and rereading.calls.count("fields") == 2,
        f"reported {reported!r} after {rereading.calls}",
    )
    twinned = host({"<fields>": FIELDS + TWINS})
    reported = with_host(
        twinned, lambda: refused(lambda: read_item(key(1), fields=["Twinned"]))
    )
    check(
        "a field name two fields carry is refused rather than resolved by position",
        reported == "tracker.operations.read_item",
        f"reported {reported!r}",
    )

    # --- the document, both ways ----------------------------------------------
    rendered = as_document(A_BODY)
    shapes = [node.get("type") for node in rendered["content"]]
    check(
        "a body is rendered as the document shapes this module carries and no others",
        set(shapes) <= set(RENDERED) and set(shapes) == set(RENDERED),
        f"rendered {shapes!r} against {list(RENDERED)!r}",
    )
    check(
        "and a round trip through the document gives the body back",
        as_text(rendered) == A_BODY,
        f"came back {as_text(rendered)!r}",
    )
    # ⚠️ The honest half, asserted rather than claimed: a shape the renderer does
    # not carry keeps the reader's **words** and loses their shape.
    table = as_document(A_TABLE)
    check(
        "a shape this module does not render carries no node of its own",
        all(node.get("type") == "paragraph" for node in table["content"]),
        f"rendered {[node.get('type') for node in table['content']]!r}",
    )
    check(
        "and its text survives, so the loss is visible to whoever reads the item",
        as_text(table) == A_TABLE,
        f"came back {as_text(table)!r}",
    )
    check(
        "the module names what it does not render, so the loss is stated somewhere",
        bool(NOT_RENDERED),
    )

    # --- `set_state`: the transition that leads to the status ----------------
    moved = host()
    answered = with_host(moved, lambda: set_state(key(1), status=second))
    check(
        "an advance reads the item, reads the transitions, then writes one",
        moved.calls.count("transition") == 1
        and moved.calls.index("issue") < moved.calls.index("transitions")
        < moved.calls.index("transition"),
        f"called {moved.calls}",
    )
    check(
        "carrying the transition's own id, read from the host rather than composed",
        str((body_of(moved, "transition").get("transition") or {}).get("id"))
        == str(10 + names.index(second)),
        f"sent {moved.sent_for('transition')!r}",
    )
    check(
        "and the item comes back in the status that was asked for",
        got(answered, "status") == second,
        f"read {got(answered, 'status')!r}",
    )
    already = host()
    with_host(already, lambda: set_state(key(1), status=initial))
    check(
        "an advance to the status the item already holds writes nothing",
        not already.writes(),
        f"called {already.calls}",
    )
    # ⛔ The sharp plant: a transition whose own **name** is the status asked for
    # and which leads somewhere else. Matching the name would take it.
    misleading = host({
        "transitions": {"transitions": [{
            "id": "99",
            "name": second,
            "to": {"name": third, "statusCategory": {"key": "indeterminate"}},
            "hasScreen": False,
            "isAvailable": True,
        }]},
    })
    reported = with_host(misleading, lambda: refused(lambda: set_state(key(1), status=second)))
    check(
        "a transition named after the status but leading elsewhere is not taken",
        reported == "statuses" and not misleading.writes(),
        f"reported {reported!r} after {misleading.calls}",
    )
    unreachable = host({"transitions": {"transitions": []}})
    reported = with_host(
        unreachable, lambda: refused(lambda: set_state(key(1), status=second))
    )
    check(
        "a status no transition reaches is refused naming `statuses`, never moved near",
        reported == "statuses" and not unreachable.writes(),
        f"reported {reported!r} after {unreachable.calls}",
    )
    twice_over = host({
        "transitions": {"transitions": [
            {
                "id": str(identifier),
                "name": f"a verb {identifier}",
                "to": {"name": second, "statusCategory": {"key": "indeterminate"}},
                "hasScreen": False,
                "isAvailable": True,
            }
            for identifier in (41, 42)
        ]},
    })
    reported = with_host(
        twice_over, lambda: refused(lambda: set_state(key(1), status=second))
    )
    check(
        "two transitions to one status are refused rather than resolved by order",
        reported == "statuses" and not twice_over.writes(),
        f"reported {reported!r} after {twice_over.calls}",
    )

    # --- `create_item` --------------------------------------------------------
    typeless = host()
    reported = with_host(typeless, lambda: refused(lambda: create_item("a title", "a body")))
    check(
        "a filing with no type is refused naming `work_item.type`, before any call",
        reported == "work_item.type" and typeless.calls == [],
        f"reported {reported!r} after {typeless.calls}",
    )
    filed = host()
    created = with_host(
        filed,
        lambda: create_item("a title", A_BODY, ["alpha", "beta"], type=_a_type(configuration)),
    )
    sent_fields = body_of(filed, "create").get("fields") or {}
    check(
        "a filing names the project, the type and the labels in one call",
        (sent_fields.get("project") or {}).get("key") == project
        and (sent_fields.get("issuetype") or {}).get("name") == _a_type(configuration)
        and sent_fields.get("labels") == ["alpha", "beta"]
        and filed.calls.count("create") == 1,
        f"sent {sent_fields!r}",
    )
    check(
        "with the body sent as a document rather than as a string",
        isinstance(sent_fields.get("description"), dict)
        and sent_fields["description"].get("type") == "doc",
        f"sent {sent_fields.get('description')!r}",
    )
    check(
        "and the item is read back, so what a role carries on is a read item",
        got(created, "key") and got(created, "title") == "a title",
        f"read {created!r}",
    )
    short = host({"create": {"id": "10404", "key": key(1)}})
    reported = with_host(
        short,
        lambda: unavailable(
            lambda: create_item("a title", "a body", ["gamma"], type=_a_type(configuration))
        ),
    )
    check(
        "a create that came back short of its labels is reported, naming them",
        reported is not None and "gamma" in reported and "did not land" in reported,
        f"got {reported!r}",
    )
    check(
        "and is never retried, because a second create would file the work twice",
        short.calls.count("create") == 1,
        f"called {short.calls}",
    )
    spaced = host()
    reported = with_host(
        spaced,
        lambda: refused(
            lambda: create_item("a title", "a body", ["two words"], type=_a_type(configuration))
        ),
    )
    check(
        "a label carrying whitespace is refused before any call, this host taking one word",
        reported == "tracker.operations.set_labels" and spaced.calls == [],
        f"reported {reported!r} after {spaced.calls}",
    )

    # --- `set_labels`: set, not add ------------------------------------------
    relabelled = host()
    answered = with_host(relabelled, lambda: set_labels(key(1), ["beta"]))
    check(
        "a set of labels is written whole, so what the item carried is not kept",
        (body_of(relabelled, "update").get("fields") or {}).get("labels") == ["beta"]
        and got(answered, "labels") == ["beta"],
        f"sent {relabelled.sent_for('update')!r} and read {got(answered, 'labels')!r}",
    )
    same = host()
    with_host(same, lambda: set_labels(key(1), ["alpha"]))
    check(
        "the set the item already carries writes nothing",
        not same.writes(),
        f"called {same.calls}",
    )
    cleared = host()
    answered = with_host(cleared, lambda: set_labels(key(1), []))
    check(
        "the empty set is one ordinary write here, where the card tracker has no form for it",
        (body_of(cleared, "update").get("fields") or {}).get("labels") == []
        and cleared.calls.count("update") == 1
        and got(answered, "labels") == [],
        f"sent {cleared.sent_for('update')!r}",
    )

    # --- `set_field`: the field's own type decides the value -----------------
    dated = host()
    with_host(dated, lambda: set_field(key(1), "Due date", "2026-10-22"))
    check(
        "a date field is written by the site's own id, in § 4.5's own form",
        (body_of(dated, "update").get("fields") or {}).get("duedate") == "2026-10-22",
        f"sent {dated.sent_for('update')!r}",
    )
    loose = host()
    reported = with_host(loose, lambda: refused(lambda: set_field(key(1), "Due date", "soon")))
    check(
        "a date that is not that form is refused naming the field, before any write",
        reported == "tracker.fields.Due date" and not loose.writes(),
        f"reported {reported!r} after {loose.calls}",
    )
    estimated = host()
    with_host(estimated, lambda: set_field(key(1), "Time tracking", "4h"))
    check(
        "§ 4.3's estimate is written as a member of the composite field, not as a scalar",
        (body_of(estimated, "update").get("fields") or {}).get("timetracking")
        == {"originalEstimate": "4h"},
        f"sent {estimated.sent_for('update')!r}",
    )
    bare = host()
    reported = with_host(bare, lambda: refused(lambda: set_field(key(1), "Time tracking", 4)))
    check(
        "a bare number for a duration is refused, the unit being the project's and not the site's",
        reported == "tracker.fields.Time tracking" and not bare.writes(),
        f"reported {reported!r}",
    )
    ranked = host()
    with_host(ranked, lambda: set_field(key(1), "Priority", "High"))
    check(
        "§ 4.6's priority is written as the named value this host takes",
        (body_of(ranked, "update").get("fields") or {}).get("priority") == {"name": "High"},
        f"sent {ranked.sent_for('update')!r}",
    )
    pointed = host()
    with_host(pointed, lambda: set_field(key(1), "Story points", 3))
    check(
        "a number field takes the number itself",
        (body_of(pointed, "update").get("fields") or {}).get("customfield_10030") == 3,
        f"sent {pointed.sent_for('update')!r}",
    )
    worded = host()
    reported = with_host(worded, lambda: refused(lambda: set_field(key(1), "Story points", "3")))
    check(
        "while a string handed to one is refused rather than sent for the host to reject",
        reported == "tracker.fields.Story points" and not worded.writes(),
        f"reported {reported!r}",
    )
    unshaped = host()
    reported = with_host(unshaped, lambda: refused(lambda: set_field(key(1), "Sprint", "a sprint")))
    check(
        "a field type this module has no shape for is refused, naming the field",
        reported == "tracker.fields.Sprint" and not unshaped.writes(),
        f"reported {reported!r}",
    )
    bodied = host()
    with_host(bodied, lambda: set_field(key(1), "Description", A_BODY))
    check(
        "the body field is written as a document, which is what makes a rewrite possible",
        isinstance((body_of(bodied, "update").get("fields") or {}).get("description"), dict),
        f"sent {bodied.sent_for('update')!r}",
    )
    # ⛔ Each field another operation owns, refused by the **id** it resolves to
    # rather than by the name the caller used.
    owners = {
        "Labels": "labels", "Status": "status", "Assignee": "assignee",
    }
    for name, identifier in owners.items():
        owned = host()
        reported = with_host(
            owned, lambda name=name: refused(lambda: set_field(key(1), name, "x"))
        )
        check(
            f"`{name}` is refused for a write, naming the operation that owns `{identifier}`",
            reported == f"tracker.fields.{name}" and not owned.writes(),
            f"reported {reported!r}",
        )
    check(
        "and every id this module says is owned elsewhere names an operation",
        all(bool(owner) for owner in OWNED_ELSEWHERE.values()),
        f"owns {OWNED_ELSEWHERE!r}",
    )

    # --- `comment`, `assign` --------------------------------------------------
    noted = host()
    answered = with_host(noted, lambda: comment(key(1), STAYS_GREEN))
    check(
        "a comment is posted as a document on the item this tracker holds it on",
        noted.calls.count("comment") == 1
        and as_text(body_of(noted, "comment").get("body")) == STAYS_GREEN,
        f"sent {noted.sent_for('comment')!r}",
    )
    check(
        "and the answer names the item rather than the call",
        got(answered, "commented") is True and got(answered, "key") == key(1),
        f"got {answered!r}",
    )
    taken = host()
    with_host(taken, lambda: assign(key(1)))
    check(
        "`@me` is resolved through the site's own answer and written as an account id",
        "me" in taken.calls and body_of(taken, "assignee").get("accountId") == ME,
        f"called {taken.calls} sending {taken.sent_for('assignee')!r}",
    )
    held = host()
    with_host(held, lambda: assign(key(3)))
    check(
        "and an item the account already holds is not assigned again",
        "assignee" not in held.calls,
        f"called {held.calls}",
    )

    # --- the dependency, asserted as a round trip ----------------------------
    #
    # ⛔ The direction is **not** read off the call. The host stores a link by its
    # own rule -- the entry an issue carries names the other side -- so an
    # implementation that swapped inward and outward would write a link that
    # reads back the wrong way round, and these three cases are what catches it.
    linked = host()

    def _link_and_read():
        link_dependency(key(1), key(2))
        return read_item(key(1)), read_item(key(2))

    answered = with_host(linked, _link_and_read)
    blocked, blocker = answered if isinstance(answered, tuple) else ({}, {})
    check(
        "the call puts the item that BLOCKS in the inward position",
        (body_of(linked, "link").get("inwardIssue") or {}).get("key") == key(2)
        and (body_of(linked, "link").get("outwardIssue") or {}).get("key") == key(1),
        f"sent {linked.sent_for('link')!r}",
    )
    check(
        "which is the opposite of the link type's own inward wording",
        under_test.INWARD_READS != under_test.OUTWARD_READS
        and body_of(linked, "link").get("type") == {"name": BLOCKS},
        f"the type reads inward {under_test.INWARD_READS!r}",
    )
    check(
        "and the blocked item reads the blocker back under `blocked_by`",
        keys_of(blocked, "blocked_by") == [key(2)] and keys_of(blocked, "blocks") == [],
        f"read blocked_by {keys_of(blocked, 'blocked_by')!r} blocks {keys_of(blocked, 'blocks')!r}",
    )
    check(
        "while the blocker reads the other item under `blocks`",
        keys_of(blocker, "blocks") == [key(1)] and keys_of(blocker, "blocked_by") == [],
        f"read blocks {keys_of(blocker, 'blocks')!r}",
    )
    other_link = host(issues=None)
    other_link.issues[key(1)]["fields"]["issuelinks"] = [{
        "id": "link-9",
        "type": {"name": "Relates", "inward": "relates to", "outward": "relates to"},
        "outwardIssue": {
            "key": key(2),
            "fields": {"status": {"name": initial, "statusCategory": {"key": "new"}}},
        },
    }]
    item = with_host(other_link, lambda: read_item(key(1)))
    check(
        "a link of another type is neither a blocker nor a thing blocked",
        keys_of(item, "blocked_by") == []
        and keys_of(item, "blocks") == []
        and keys_of(item, "links") == [key(2)],
        f"read {got(item, 'links')!r}",
    )

    # --- searching ------------------------------------------------------------
    #
    # ⛔ The query is bounded by the project, and that is the **host's** rule
    # rather than a convenience: a query with no restriction is refused outright.
    query = as_query(project, None, None, None)
    check(
        "every query is bounded by the project, which is what this host requires",
        query.startswith(f'project = "{project}"'),
        f"composed {query!r}",
    )
    check(
        "and carries no status restriction, the operation being across every state",
        "status" not in query,
        f"composed {query!r}",
    )
    with_terms = as_query(project, "two words", ["alpha"], {"status": initial})
    check(
        "terms, labels and a field each become a clause of their own",
        with_terms.count("summary ~") == 2
        and 'labels = "alpha"' in with_terms
        and f'status = "{initial}"' in with_terms,
        f"composed {with_terms!r}",
    )
    for what, value in (
        ("a term", {"terms": 'a " quote'}),
        ("a label", {"labels": ['a " quote']}),
        ("a field value", {"fields": {"status": 'a " quote'}}),
    ):
        broken_query = host()
        reported = with_host(
            broken_query, lambda value=value: refused(lambda: search_items(**value))
        )
        check(
            f"{what} that would end its operand is refused, before any call",
            reported == "tracker.operations.search_items" and broken_query.calls == [],
            f"reported {reported!r} after {broken_query.calls}",
        )
    unqueryable = host()
    reported = with_host(
        unqueryable, lambda: refused(lambda: search_items(fields={"Sprint": "a sprint"}))
    )
    check(
        "a field this tracker is not queried on here is refused, never answered empty",
        reported == "tracker.operations.search_items.Sprint" and unqueryable.calls == [],
        f"reported {reported!r}",
    )
    searched = host()
    answered = with_host(searched, lambda: search_items())
    check(
        "a search answers the items the host gave, in the shape a read gives them",
        len(got(answered, "items") or []) == 3
        and all(entry.get("key") for entry in got(answered, "items") or []),
        f"answered {answered!r}",
    )
    check(
        "and says which query it sent, so a record of it is a record of what was asked",
        got(answered, "jql") == as_query(project, "", [], {}),
        f"answered {got(answered, 'jql')!r}",
    )
    # ⛔ The cursor is followed. A first page that fills reads as a complete
    # answer, which is the measured defect the board implementation pays for too.
    pages = {"calls": 0}

    def _two_pages(_path, params, _body):
        pages["calls"] += 1
        if not params.get("nextPageToken"):
            return {
                "issues": [host_with_pages.issues[key(1)]],
                "isLast": False,
                "nextPageToken": "a-token",
            }
        return {"issues": [host_with_pages.issues[key(2)]], "isLast": True}

    host_with_pages = host({"search": _two_pages})
    answered = with_host(host_with_pages, lambda: search_items())
    check(
        "a search that answers with a cursor is followed to the end",
        pages["calls"] == 2
        and [entry.get("key") for entry in got(answered, "items") or []] == [key(1), key(2)]
        and got(answered, "pages") == 2,
        f"made {pages['calls']} call(s) for {answered!r}",
    )
    bounded = host()
    answered = with_host(bounded, lambda: search_items(limit=2))
    check(
        "the caller's own bound cuts the answer and is reported as having done so",
        len(got(answered, "items") or []) == 2 and got(answered, "at_limit") is True,
        f"answered {answered!r}",
    )
    check(
        "every field this module says it answers a query on becomes a clause",
        all(
            f"{name} = " in as_query(project, None, None, {name: "x"})
            for name in QUERYABLE
        ),
        f"states {QUERYABLE!r}",
    )

    # --- `advance_on_merge`: the tracker's half of the question ---------------
    def _history(account: str) -> dict:
        return {key(1): [{
            "created": "2026-10-03T00:00:00.000+0000",
            "author": {"accountId": account},
            "items": [{"field": "status", "fromString": initial, "toString": second}],
        }]}

    somebody = host({"<changelog>": _history(SOMEBODY)})
    answered = with_host(somebody, lambda: advance_on_merge(key(1)))
    check(
        "a status change by something other than this credential reads as advanced",
        got(answered, "advanced") is True
        and (got(answered, "moved") or {}).get("to") == second,
        f"got {answered!r}",
    )
    mine = host({"<changelog>": _history(ME)})
    answered = with_host(mine, lambda: advance_on_merge(key(1)))
    check(
        "a change this credential made does not, which is the procedure's own write",
        got(answered, "advanced") is False and got(answered, "moved") is not None,
        f"got {answered!r}",
    )
    nothing = host()
    answered = with_host(nothing, lambda: advance_on_merge(key(1)))
    check(
        "an item nothing moved reads as not advanced, with its status still reported",
        got(answered, "advanced") is False
        and got(answered, "moved") is None
        and got(answered, "status") == initial,
        f"got {answered!r}",
    )
    check(
        "and the answer states the bound rather than claiming an automation fired",
        "cannot see the merge" in str(got(answered, "bound")),
        f"stated {got(answered, 'bound')!r}",
    )

    # --- the site, which is half the address ---------------------------------
    for value, what in (
        ("https://<site>/jira/", "a site carrying a path"),
        ("<site>", "a value that is not an address"),
        ("", "no site at all"),
    ):
        elsewhere = _example_configuration()
        elsewhere.data["tracker"]["site"] = value
        bind(elsewhere)
        addressed = host()
        reported = with_host(addressed, lambda: refused(lambda: read_item(key(1))))
        check(
            f"{what} is refused, naming the key, before any call",
            reported == "tracker.site" and addressed.calls == [],
            f"reported {reported!r} after {addressed.calls}",
        )
    bind(configuration)

    # --- the credential, and the one surface a failure is read on ------------
    os.environ.pop(ACCOUNT_VARIABLE)
    os.environ.pop(TOKEN_VARIABLE)
    bare_shell = host()
    reported = with_host(bare_shell, lambda: unavailable(lambda: read_item(key(1))))
    check(
        "a shell holding neither variable is a failure naming both, before any call",
        reported is not None
        and ACCOUNT_VARIABLE in reported
        and TOKEN_VARIABLE in reported
        and bare_shell.calls == [],
        f"got {reported!r} after {bare_shell.calls}",
    )
    os.environ[ACCOUNT_VARIABLE] = AN_ACCOUNT
    # ⚠️ One of the two, which is the arm that matters: the pair addresses this
    # tracker **together**, so a shell holding the token alone is as unable to
    # make a call as one holding neither -- and only this arm would read as
    # *nearly configured* to somebody looking at the shell.
    half_shell = host()
    reported = with_host(half_shell, lambda: unavailable(lambda: read_item(key(1))))
    check(
        "and a shell holding one of them is a failure too, naming the one it lacks",
        reported is not None
        and TOKEN_VARIABLE in reported
        and ACCOUNT_VARIABLE not in reported
        and half_shell.calls == [],
        f"got {reported!r} after {half_shell.calls}",
    )
    os.environ[TOKEN_VARIABLE] = A_TOKEN

    for status, what, expected in (
        (429, "rate limited", "budget"),
        (401, "unauthorised", "address being wrong"),
        (403, "forbidden", "address being wrong"),
        (404, "not found", "one answer for two facts"),
        (500, "a server error", "failed with HTTP 500"),
        (0, "a call that never reached the host", "never reached the host"),
    ):
        answering = host({"issue": (status, '{"errorMessages":["x"]}')})
        reported = with_host(answering, lambda: unavailable(lambda: read_item(key(1))))
        check(
            f"{what} comes back as a failure saying so",
            reported is not None and expected in reported,
            f"got {reported!r}",
        )
    # ⛔ The one assertion that is about the report rather than the call: every
    # message quotes the call, and the pair is what must not be in it -- the
    # token for the obvious reason and the account because it is an address.
    answering = host({"issue": (500, "no")})
    reported = with_host(answering, lambda: unavailable(lambda: read_item(key(1))))
    check(
        "and no failure message carries the account or the token, only their names",
        reported is not None
        and AN_ACCOUNT not in reported
        and A_TOKEN not in reported
        and f"{API_SHOWN}/issue/" in reported,
        "a message carried a value" if reported and A_TOKEN in reported else f"got {reported!r}",
    )
    empty = host({"issue": (200, "   ")})
    reported = with_host(empty, lambda: unavailable(lambda: read_item(key(1))))
    check(
        "an answer with no body where one belongs is a failure rather than a None read on",
        reported is not None,
        f"got {reported!r}",
    )

    # --- the policy, which is the one half of the port a project states ------
    #
    # ⚠️ The shipped example for this kind bars nothing, which is a stated
    # decision rather than an omission -- so the classes are added to a copy of
    # it here. ⛔ Without this the guard would be unreachable from any case, and
    # an unreachable guard reads exactly like one that works.
    barring = _example_configuration()
    classes = sorted(PLANTS)
    barring.data["tracker"]["policy"] = {"forbid_on_item": classes}
    bind(barring)
    prefixes = [
        str(value)
        for value in (barring.get("work_item.type_branch_prefix") or {}).values()
    ]
    for name, planted in PLANTS.items():
        found = [
            finding
            for finding in under_test.forbidden(planted, classes, prefixes)
            if finding.startswith(f"`{name}`")
        ]
        check(f"the guard reddens on a planted `{name}`", bool(found), f"found {found!r}")
    check(
        "and stays green on a body that carries none of them",
        under_test.forbidden(STAYS_GREEN, classes, prefixes) == [],
        f"found {under_test.forbidden(STAYS_GREEN, classes, prefixes)!r}",
    )
    for label, call in (
        ("create_item", lambda: create_item(
            "a title", PLANTS["branch_names"], type=_a_type(configuration)
        )),
        ("comment", lambda: comment(key(1), PLANTS["branch_names"])),
        ("set_field", lambda: set_field(key(1), "Description", PLANTS["branch_names"])),
    ):
        guarded = host()
        reported = with_host(guarded, lambda call=call: refused(call))
        check(
            f"`{label}` refuses a barred span, naming the key that bars it",
            reported == "tracker.policy.forbid_on_item" and not guarded.writes(),
            f"reported {reported!r} after {guarded.calls}",
        )
    # A pass over every write that carries a person's text, inspecting what
    # reached the item rather than what was handed in.
    sweeping = host()
    with_host(sweeping, lambda: (
        create_item("a clean title", STAYS_GREEN, ["alpha"], type=_a_type(configuration)),
        set_state(key(1), status=second),
        set_field(key(1), "Description", STAYS_GREEN),
        comment(key(1), STAYS_GREEN),
        set_labels(key(1), ["beta"]),
        assign(key(1)),
    ))
    carried = []
    for name, what in sweeping.sent:
        fields = ((what.get("body") or {}).get("fields") or {})
        for field, value in list(fields.items()) + [("body", (what.get("body") or {}).get("body"))]:
            if field not in TEXT_FIELDS + ("body",) or value is None:
                continue
            text = as_text(value) if isinstance(value, dict) else str(value)
            if under_test.forbidden(text, classes, prefixes):
                carried.append((name, field, text))
    check(
        "a pass of every write sends nothing barred in the text that reaches the item",
        not carried,
        f"sent {carried!r}",
    )
    check(
        "and that pass did reach the host, so the sweep is over calls that were made",
        len(sweeping.writes()) >= 5,
        f"made {sweeping.writes()!r}",
    )
    bind(configuration)

    # --- this fake's own rule ------------------------------------------------
    check(
        "a transition list is not answered as an issue, which the route order decides",
        route("GET", f"/issue/{key(1)}/transitions") == "transitions"
        and route("GET", f"/issue/{key(1)}") == "issue"
        and route("PUT", f"/issue/{key(1)}/assignee") == "assignee"
        and route("PUT", f"/issue/{key(1)}") == "update"
        and route("POST", f"/issue/{key(1)}/comment") == "comment"
        and route("POST", "/issue") == "create",
        f"routed {route('GET', f'/issue/{key(1)}/transitions')!r}",
    )
    check(
        "and a call to a route the fake does not name is an error rather than an answer",
        isinstance(
            ran(lambda: _Host(configuration)("GET", "/nowhere", {}, None)).get("<raised>"), str
        ),
    )

    # ⛔ The module and the shell left as they were found. This suite binds a
    # configuration, resolves a site against a substituted host and writes two
    # variables; a run inside a longer process -- which is what the gate's runner
    # is -- would otherwise leave an example's site cached behind a real role's
    # first call, and a credential-shaped value in the environment.
    bind(None)
    _sites.clear()
    for name, value in was_environment.items():
        if value is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = value

    if failures:
        print(f"\n{failures} assertion(s) did not hold.")
    return 1 if failures else 0
