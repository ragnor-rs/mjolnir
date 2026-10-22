#!/usr/bin/env python3
"""A board behind the port: items are issues, and the state is a field on a card.

The tracker the copies this toolkit was extracted from used most, and the one
whose shapes were the hardest to read off those copies: a status is not a word on
the item but an **option id** of a **field id** of a **project id**, and all three
of those were copy-pasted around rather than resolved.

What it implements, and what it deliberately does not:

  * **Every operation § 3 states except the three checklist ones.** A task list on
    an issue is markdown inside the body -- there is no check-item object to read,
    tick or delete -- so the three stated fallbacks are already the right
    behaviour and implementing them against body text would dress a fallback up
    as a capability. The same absence as the plain-issues implementation beside
    this one, and for the same reason rather than by copying it.
  * **`set_state` writes the board's column and never the issue's own state.**
    That is what the tracker holds: a card's status is a single-select value, and
    an issue being open or closed is a different fact the host's own automation
    writes. ⚠️ A `statuses` list here maps the **board's option names** (§ 4.2),
    so a word with no option on the board is refused with the key named rather
    than coerced to the nearest column.
  * **Ids are resolved by name, in one place, and none is written anywhere.**
    [`resolve`](#) is `by_name` on this surface and this is the module that makes
    that true: the project id, every field id and every option id come from one
    query keyed on the configured `project.owner` and `project.number`, and the
    names come from the configuration. ⛔ The self-test sweeps every shipped
    carrier for an id shape, because the measured defect was a four-line table of
    option ids pasted verbatim into three skills and the same ids inlined again in
    four mutations.
  * **Every list is read whole or refused, never returned short.** A board past
    its first page is the measured case: the host's pagination flag follows
    top-level pages and not a nested items connection, so a first-page query is a
    ceiling and **a round total is the signature of an unfollowed cursor**. One
    cursor-follower reads every connection this module pages, and one guard
    refuses a connection that claims a next page where this module cannot follow
    one. ⛔ Neither ever truncates quietly: a short answer to a duplicate check
    reads exactly like a tracker with nothing in it.
  * **Two fields in one read, by reading them all at once.** Asking for a field
    *by name* twice in one query is refused by the host -- measured, `fieldValueByName`
    twice in one selection comes back `fieldConflict: Field 'fieldValueByName'
    has an argument conflict`, and an alias on each is what makes it legal. So
    this module asks for none of them by name: it reads the card's whole
    `fieldValues` connection once and keys the answer on each value's own field
    name, which has no alias to get wrong and costs one request rather than one
    per field. ⛔ The self-test holds the queries to carrying no by-name field
    read, which is where that decision would otherwise rot back.
  * **`link_dependency` posts a relation on the *blocked* item, keyed on the
    blocker's internal id** -- the same REST shape plain issues take, because a
    board is a view over issues and the dependency is a fact about the issues.
  * **`advance_on_merge` confirms and never asserts.** Two automations can move a
    card -- the host closing the issue off a merged pull request's closing
    reference, and the board's own workflow setting a column when an issue closes
    -- so this asks what happened and reports the issue's state, the card's column
    and which merged pull request closed it. ⚠️ A board whose workflow is not
    enabled leaves the column where it was with the issue closed, which the answer
    shows rather than hides.
  * **The pull-request guard is the host's own typename.** Issues and pull
    requests share one number sequence here, and `issueOrPullRequest` answers
    which of the two a number names -- measured, a merged pull request's number
    comes back `__typename: PullRequest` with `state: MERGED`, a word no
    `statuses` list contains. Every operation taking a number resolves it through
    `read_item` first, which is what makes one guard cover all of them rather
    than cover one.

Every call goes through `gh`, which holds the credential and the host's base URL.
⛔ **Through one named seam**, `TRANSPORT`: the decisions worth testing here are
parses and orderings over the host's answers, and a suite that cannot hand this
module an answer would have to reach the live board to exercise any of them.

The configuration arrives from the port through `bind`; nothing here resolves a
project for itself.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys

# The package's parent, appended rather than prepended: this module is imported
# as `adapters.github_projects`, so the contract beside it is not otherwise on
# the path, and putting it first would shadow a standard-library name.
_SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SCRIPTS not in sys.path:
    sys.path.append(_SCRIPTS)

import config  # noqa: E402
import port  # noqa: E402
from port import ConfigError, HostUnavailable  # noqa: E402

KIND = "github-projects"

# How many nodes a page asks for. ⚠️ Not a ceiling on what is read -- the
# follower below reads every page -- but the host's own maximum for one
# connection, so a smaller number here costs requests and changes no answer.
PAGE = 100

# A bound on the follower, so a host that keeps claiming another page is a
# refusal rather than a process nobody can stop. ⛔ Set far above any real board:
# a run that reaches it has met a defect, not a big project.
MAX_PAGES = 200

# The configured status column's name, and the only key this module needs that
# the surface marks neither required nor absent-with-a-reason: § 3 states that a
# board whose states nobody moves needs no mapping, so an absent one cannot be
# told from an oversight at configuration time and is refused here instead --
# where a move is actually being asked for.
STATUS_FIELD_NAME = "tracker.status_field.name"

# What `set_field` can write, by the field's own `dataType`. Everything else on a
# board is either host-managed -- the title, the labels, the assignees, the
# repository, the linked pull requests, the created and updated stamps -- or an
# iteration, which is addressed by an iteration id rather than a value.
TEXT, NUMBER, DATE, SINGLE_SELECT = "TEXT", "NUMBER", "DATE", "SINGLE_SELECT"
WRITABLE = (TEXT, NUMBER, DATE, SINGLE_SELECT)

# What the host's client writes to stderr when the thing asked for is not there.
NOT_FOUND = "(HTTP 404)"

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

# The configuration the port last handed down, and the only place one comes from.
# ⛔ Never resolved here and never from the working directory, for § 3's reason:
# a process serving more than one project must address each one's own board.
_bound = None

# Resolved boards, keyed by the **address** they were resolved from. Keyed rather
# than process-wide: two projects in one process have two boards, and an earlier
# implementation of the tracker next door cached one and pinned every later
# project to the first one's repository. ⚠️ A board resolved here can go stale
# within a run -- a column added seconds ago is absent from it -- so a name that
# does not resolve re-reads the board once before refusing.
_boards: dict[tuple[str, int], dict] = {}


def bind(configuration) -> None:
    """Take the configuration for the operation about to run.

    `Port.invoke` calls this before every operation, so it is per call rather
    than per process and switching projects needs no reset.
    """
    global _bound
    _bound = configuration


def _configuration():
    if _bound is None:
        raise ConfigError(
            "tracker.adapters.github_projects",
            "was asked for an operation before the port bound a configuration "
            "to it. Every operation is reached through `Port.invoke`, which "
            "binds first; a direct call bypasses the one place the project is "
            "stated.",
        )
    return _bound


def _repo() -> str:
    """The repository the issues behind the cards live in.

    A board can hold cards from several repositories, and this is the one the
    procedure files into and addresses an item by number in -- `host.repo`, which
    § 2 marks required. What is refused here is the shape, which nothing else
    checks.
    """
    repo = _configuration().get("host.repo")
    if not repo or str(repo).count("/") != 1:
        raise ConfigError(
            "host.repo",
            f"is `{repo}`, which is not `owner/name`. An item here is an issue in "
            "one repository with a card on the board, and every call addresses "
            "that repository by the pair, so a URL or a bare name has no reading "
            "this tracker could act on.",
        )
    return str(repo)


def _address() -> tuple[str, int]:
    """The board's own address: the owner it sits under and its number.

    Both are marked `required_when: tracker.kind = github-projects` on the
    surface, so a configuration that reached here states them; what is refused is
    a number that is not one, since the host's query takes an `Int` and a string
    would come back as a syntax error from the host rather than as a configuration
    this reader can name.
    """
    configuration = _configuration()
    owner = configuration.get("tracker.project.owner")
    number = configuration.get("tracker.project.number")
    if not owner:
        raise ConfigError(
            "tracker.project.owner",
            "states no owner, so the board cannot be addressed. It is the user or "
            "organisation the project sits under, not the repository's owner, and "
            "the two differ wherever a board spans repositories.",
        )
    try:
        number = int(number)
    except (TypeError, ValueError):
        raise ConfigError(
            "tracker.project.number",
            f"is `{number}`, which is not a project number. It is the small "
            "integer in the board's own URL -- never its node id, which this "
            "module resolves and nothing configures.",
        ) from None
    return str(owner), number


# --- the host, through one named seam ---------------------------------------


def _subprocess_gh(args: list[str], parse: bool):
    """One host call. Every failure comes back as the contract's own exception.

    ⛔ `port.HostUnavailable` rather than a class of this module's: the port turns
    it into a `failed` outcome, and a role must be able to tell a broken call from
    a missing capability without knowing which tracker answered. The command is in
    every message, so a failure is reproducible by hand.
    """
    shown = "gh " + " ".join(args)
    try:
        done = subprocess.run(
            ["gh"] + args, capture_output=True, text=True, timeout=60, check=True
        )
    except FileNotFoundError:
        raise HostUnavailable(f"`gh` is not on PATH, so `{shown}` could not run") from None
    except subprocess.TimeoutExpired:
        raise HostUnavailable(f"`{shown}` timed out after 60s") from None
    except subprocess.CalledProcessError as error:
        raise HostUnavailable(
            f"`{shown}` failed: {error.stderr.strip() or 'no stderr'}"
        ) from None
    if not parse:
        return done.stdout.strip()
    if not done.stdout.strip():
        raise HostUnavailable(f"`{shown}` answered with nothing where a body was expected")
    return json.loads(done.stdout)


def _subprocess_probe(args: list[str]):
    """One host call whose **failure** is the answer, as its three parts.

    ⛔ Separate from `_subprocess_gh` because that one turns every non-zero exit
    into the same refusal, and the one caller here needs three answers apart:
    present, absent by the host's own `404`, and could-not-be-established.
    """
    shown = "gh " + " ".join(args)
    try:
        done = subprocess.run(["gh"] + args, capture_output=True, text=True, timeout=30)
    except FileNotFoundError:
        raise HostUnavailable(f"`gh` is not on PATH, so `{shown}` could not run") from None
    except subprocess.TimeoutExpired:
        raise HostUnavailable(f"`{shown}` timed out after 30s") from None
    return done.returncode, done.stdout, done.stderr


# The two seams. ⛔ Named, rather than left as calls this module makes directly:
# what earns a test here is a parse, an ordering or a guard over the host's
# answers, and every one of those is unreachable from a suite that cannot answer
# as the host. ⚠️ **Both** of them, because one caller reads a failure rather than
# a body -- a path that went straight to the client would reach the live host
# from a suite that believes it reaches nothing. Rebound for the length of a case
# and restored, never for a process.
TRANSPORT = _subprocess_gh
PROBE = _subprocess_probe


def _gh(args: list[str], *, parse: bool = True):
    return TRANSPORT(args, parse)


def _graphql(query: str, **variables):
    """One GraphQL request, with its variables typed as the host's client wants.

    ⚠️ A variable whose value is `None` is **left off** rather than sent empty: an
    optional cursor is absent on the first page, and `-f after=` would send the
    empty string, which is a cursor the host rejects rather than no cursor at all.

    ⛔ An answer carrying an `errors` array is a failure even where the client
    exited zero. The client does exit non-zero on a GraphQL error -- measured, a
    project number nothing resolves comes back `NOT_FOUND` with exit 1 -- so this
    is the arm that stays correct if that ever stops being true, and it is the arm
    a substituted transport reaches.
    """
    args = ["api", "graphql", "-f", f"query={query}"]
    for name, value in variables.items():
        if value is None:
            continue
        flag = "-F" if isinstance(value, (int, float, bool)) else "-f"
        args += [flag, f"{name}={value}"]
    answer = _gh(args)
    if isinstance(answer, dict) and answer.get("errors"):
        messages = "; ".join(
            str(error.get("message", error)) for error in answer["errors"]
        )
        raise HostUnavailable(
            f"the host answered a GraphQL error rather than data: {messages}"
        )
    return answer["data"]


# --- reading a list whole, or refusing it -----------------------------------


def _whole(connection: dict, what: str) -> list:
    """Every node of a connection this module asks for in one page.

    ⛔ A connection that claims another page is **refused**, because there is no
    cursor to follow in the shape it was asked in -- it is nested inside a single
    object rather than paged on its own. Returning the short list would be the
    silent truncation this module exists not to do: a duplicate check reads an
    answer that is missing items exactly as it reads a tracker that holds none.
    """
    if connection is None:
        raise HostUnavailable(
            f"the host answered no connection where {what} was expected, so the "
            "list could not be read at all -- which is not the same as its being "
            "empty."
        )
    nodes = connection.get("nodes") or []
    info = connection.get("pageInfo") or {}
    if info.get("hasNextPage"):
        raise HostUnavailable(
            f"{what} came back with {len(nodes)} node(s) and the host saying it "
            "has more, in a shape this module asks for in one page. The answer is "
            "refused rather than returned short."
        )
    return nodes


def _paged(fetch, what: str, first: dict | None = None) -> list:
    """Every node of a paged connection, following its cursor to the end.

    `fetch(cursor)` asks the host for one page and returns the connection, and
    `first` is a page already in hand -- the connection that arrived inside an
    answer this module had to make anyway. ⚠️ Without it the first page is asked
    for twice: measured on the board's own resolution, which read the project and
    then re-read it to get at page one of its fields.

    ⚠️ The
    measured defect this exists for: a first-page query reads as a complete
    answer, and the host's own paginate flag follows top-level pages rather than a
    nested items connection -- so a board that has passed the page size answers
    with a round number of items and nothing says so.

    ⛔ Three refusals rather than a short list: a page that claims a successor and
    names no cursor, a cursor the host repeats, and more pages than any real board
    has. Each of them is a loop or a truncation, and both read as data.
    """
    nodes: list = []
    cursor, seen, pages = None, set(), 0
    # The page in hand is used once and then dropped, so an empty first page that
    # claims a successor still goes to the host for the next one.
    page, first = first, None
    while True:
        connection, page = (page, None) if page is not None else (fetch(cursor), None)
        if connection is None:
            raise HostUnavailable(
                f"the host answered no connection where {what} was expected."
            )
        nodes.extend(connection.get("nodes") or [])
        info = connection.get("pageInfo") or {}
        if not info.get("hasNextPage"):
            return nodes
        cursor = info.get("endCursor")
        if not cursor:
            raise HostUnavailable(
                f"{what}: the host says there is another page and named no cursor, "
                f"after {len(nodes)} node(s). The answer is refused rather than "
                "returned short -- a list cut here reads as a complete one."
            )
        if cursor in seen:
            raise HostUnavailable(
                f"{what}: the host handed back a cursor it had already given, so "
                "following it would read the same page forever."
            )
        seen.add(cursor)
        pages += 1
        if pages > MAX_PAGES:
            raise HostUnavailable(
                f"{what}: more than {MAX_PAGES} pages of {PAGE}, which is past any "
                "real board and reads as a cursor that never ends."
            )


# --- the board, resolved by name in one place -------------------------------

BOARD_QUERY = """
query Board($owner:String!, $number:Int!, $after:String) {
  repositoryOwner(login:$owner) {
    __typename
    ... on User { projectV2(number:$number) { ...boardFacts } }
    ... on Organization { projectV2(number:$number) { ...boardFacts } }
  }
}
fragment boardFacts on ProjectV2 {
  id
  number
  title
  fields(first:100, after:$after) {
    pageInfo { hasNextPage endCursor }
    nodes {
      __typename
      ... on ProjectV2FieldCommon { id name dataType }
      ... on ProjectV2SingleSelectField { id name options { id name } }
      ... on ProjectV2IterationField {
        id
        name
        configuration { iterations { id title } }
      }
    }
  }
}
"""


def _board_payload(owner: str, number: int, cursor):
    """One page of the board's own facts, as the host answers them.

    ⛔ Addressed through `repositoryOwner` with a fragment on each of the two
    owner kinds, rather than by asking whether the owner is a user or an
    organisation first. The surface states one `project.owner` and does not say
    which kind it is -- measured, asking `user(login:)` for an organisation's
    login answers an error rather than null, so a guess costs a failed call and a
    wrong refusal.
    """
    owned = _graphql(BOARD_QUERY, owner=owner, number=number, after=cursor)["repositoryOwner"]
    if owned is None:
        raise HostUnavailable(
            f"no user or organisation named `{owner}` answers on this host, so "
            "`tracker.project.owner` addresses nothing."
        )
    board = owned.get("projectV2")
    if board is None:
        raise HostUnavailable(
            f"`{owner}` has no project number {number} this credential can see. "
            "That is the board's own number from its URL, and a board somebody "
            "else owns is invisible rather than refused."
        )
    return board


def index_fields(nodes: list) -> dict[str, dict]:
    """`field name -> the field's own facts`, as the host stated them.

    ⛔ Every id in the answer is the host's. Nothing here composes one, and the
    names are the configuration's -- which is the whole of `resolve: by_name`.

    A single-select field carries its options by name, and an iteration field its
    iterations by title, for the same reason: both are addressed by id in a write
    and named by a person everywhere else.
    """
    fields: dict[str, dict] = {}
    for node in nodes:
        name = node.get("name")
        if not name:
            continue
        options = {
            option["name"]: option["id"] for option in (node.get("options") or [])
        }
        iterations = {
            iteration["title"]: iteration["id"]
            for iteration in ((node.get("configuration") or {}).get("iterations") or [])
        }
        fields[name] = {
            "id": node.get("id"),
            "name": name,
            "data_type": node.get("dataType"),
            "options": options,
            "iterations": iterations,
        }
    return fields


def _resolve_board(owner: str, number: int) -> dict:
    board = _board_payload(owner, number, None)
    nodes = _paged(
        lambda cursor: _board_payload(owner, number, cursor)["fields"],
        what=f"the fields of project {number}",
        first=board["fields"],
    )
    return {
        "id": board["id"],
        "number": board.get("number", number),
        "owner": owner,
        "fields": index_fields(nodes),
    }


def _board(*, again: bool = False) -> dict:
    """The configured board, resolved once per address.

    `again=True` re-reads it, which is the one answer to a name that does not
    resolve: a column or an option added after this process started is absent from
    a board resolved before it existed, and refusing on a stale reading would be a
    refusal about the host's state at the wrong moment.
    """
    owner, number = _address()
    if again or (owner, number) not in _boards:
        _boards[(owner, number)] = _resolve_board(owner, number)
    return _boards[(owner, number)]


def _field(name: str, *, key: str) -> dict:
    """One of the board's fields, by name, re-reading the board before refusing."""
    board = _board()
    if name not in board["fields"]:
        board = _board(again=True)
    if name not in board["fields"]:
        raise ConfigError(
            key,
            f"names the field `{name}`, which project {board['number']} does not "
            f"have. Its fields are: {', '.join(sorted(board['fields'])) or 'none'}. "
            "A field is addressed by name here and the id is read from the board, "
            "so this is a name the board does not answer to rather than an id gone "
            "stale.",
        )
    return board["fields"][name]


def _status_field() -> dict:
    """The field a status lives in, named by the configuration.

    ⛔ Not defaulted. § 3 states `status_field` is deliberately not required --
    a project whose states nobody moves needs no mapping -- so an absent name is a
    legitimate configuration right up to the moment a move is asked for, which is
    here. The refusal names the key rather than guessing a column, because a board
    can hold several single-select fields and writing the wrong one moves the card
    somewhere nobody asked for.
    """
    name = _configuration().get(STATUS_FIELD_NAME)
    if not name:
        raise ConfigError(
            STATUS_FIELD_NAME,
            "states no field, so there is no column to write a status into. A "
            "board holds its states in a field of its own and § 4.2's `statuses` "
            "name that field's options, so the move cannot be made from the status "
            "words alone.",
        )
    return _field(str(name), key=STATUS_FIELD_NAME)


def _option_id(field: dict, word: str) -> str:
    """The option id for a status word, by name.

    ⚠️ Refused with `statuses` named, the way the implementation next door refuses
    a word plain issues cannot hold: a word with no option on the board is a
    mapping this tracker cannot carry, and coercing it to the nearest column is a
    card moved somewhere nobody asked for.
    """
    if word in field["options"]:
        return field["options"][word]
    refreshed = _field(field["name"], key=STATUS_FIELD_NAME)
    if word in refreshed["options"]:
        return refreshed["options"][word]
    raise ConfigError(
        "statuses",
        f"names `{word}`, which the `{field['name']}` field has no option for. Its "
        f"options are: {', '.join(sorted(refreshed['options'])) or 'none'}. A "
        "status here is one of that field's options by name; add the column to the "
        "board or map the role onto an option it already has.",
    )


# --- the item ---------------------------------------------------------------

ITEM_QUERY = """
query Item($owner:String!, $name:String!, $number:Int!) {
  repository(owner:$owner, name:$name) {
    issueOrPullRequest(number:$number) {
      __typename
      ... on Issue {
        id
        number
        title
        body
        state
        url
        labels(first:100) { pageInfo { hasNextPage endCursor } nodes { name } }
        assignees(first:100) { pageInfo { hasNextPage endCursor } nodes { login } }
        projectItems(first:100, includeArchived:true) {
          pageInfo { hasNextPage endCursor }
          nodes {
            id
            isArchived
            project { number }
            fieldValues(first:100) {
              pageInfo { hasNextPage endCursor }
              nodes { ...valueFacts }
            }
          }
        }
      }
    }
  }
}
fragment valueFacts on ProjectV2ItemFieldValue {
  __typename
  ... on ProjectV2ItemFieldSingleSelectValue {
    name
    optionId
    field { ... on ProjectV2FieldCommon { name } }
  }
  ... on ProjectV2ItemFieldTextValue {
    text
    field { ... on ProjectV2FieldCommon { name } }
  }
  ... on ProjectV2ItemFieldNumberValue {
    number
    field { ... on ProjectV2FieldCommon { name } }
  }
  ... on ProjectV2ItemFieldDateValue {
    date
    field { ... on ProjectV2FieldCommon { name } }
  }
  ... on ProjectV2ItemFieldIterationValue {
    title
    iterationId
    field { ... on ProjectV2FieldCommon { name } }
  }
}
"""

# What each value type carries its value in. ⛔ Read as a mapping rather than a
# chain of conditions, because the defect it replaces is a missing arm reading as
# an empty field: a value type nobody mapped came back as *no value*, which is the
# answer a card with an empty column gives.
VALUE_KEYS = {
    "ProjectV2ItemFieldSingleSelectValue": "name",
    "ProjectV2ItemFieldTextValue": "text",
    "ProjectV2ItemFieldNumberValue": "number",
    "ProjectV2ItemFieldDateValue": "date",
    "ProjectV2ItemFieldIterationValue": "title",
}


def values_by_field(nodes: list) -> dict[str, object]:
    """`field name -> the value on this card`, every field from one read.

    ⛔ This is the answer to the host's refusal of two by-name field reads in one
    query: nothing here asks for a field by name, so there is no alias to get
    wrong and two fields cost one request rather than two.

    ⚠️ A value whose type this module does not map is carried as the typename
    rather than dropped. A field read as absent and a field read as a shape nobody
    mapped are two different facts, and the second one silently became the first
    when the mapping was a chain of conditions.
    """
    values: dict[str, object] = {}
    for node in nodes:
        name = (node.get("field") or {}).get("name")
        if not name:
            continue
        typename = node.get("__typename")
        if typename in VALUE_KEYS:
            values[name] = node.get(VALUE_KEYS[typename])
        else:
            values[name] = {"unmapped": typename}
    return values


def _card(item: dict, number: int) -> dict | None:
    """The card this item has on the configured board, or `None` for no card.

    ⛔ An issue with no card is a fact and not a failure: it is on the host and off
    the board, which is what a role sees between a filing that could not finish
    and an item somebody added by hand. Every operation that needs a card says so
    where it needs one.
    """
    _, wanted = _address()
    cards = _whole(item.get("projectItems"), f"the cards of item #{number}")
    for card in cards:
        if (card.get("project") or {}).get("number") == wanted:
            return card
    return None


def read_item(number: int) -> dict:
    """The item's own facts and its card's, in one call.

    ⛔ **Guarded against a pull request number**, by the host's own typename
    rather than by sniffing a URL: `issueOrPullRequest` says which of the two a
    number names, and the two share one sequence here. Measured on a live
    repository -- a merged pull request's number answers `__typename:
    PullRequest`, `state: MERGED`, a word no `statuses` list contains. Every
    operation here that takes a number resolves it through this function, which is
    what makes one guard cover all of them; three of them write.

    ⚠️ A number the repository does not have answers `null` **and** a `NOT_FOUND`
    error, so it arrives as a failed call rather than here. The `null` arm below is
    the one that stays correct if that stops being true.
    """
    owner, name = _repo().split("/")
    answer = _graphql(ITEM_QUERY, owner=owner, name=name, number=int(number))
    found = (answer.get("repository") or {}).get("issueOrPullRequest")
    if found is None:
        raise HostUnavailable(
            f"the host answered nothing for #{number} in {owner}/{name}, so "
            "whether it is an item, a pull request or absent could not be told. An "
            "unreadable answer is not the same as a clean one."
        )
    typename = found.get("__typename")
    if typename != "Issue":
        raise HostUnavailable(
            f"#{number} in {owner}/{name} is a {typename} and not a work item -- "
            "the host numbers both in one sequence. A role holding a pull request "
            "number has the wrong identifier, which is a different fault from an "
            "item that does not exist."
        )
    card = _card(found, number)
    fields = (
        values_by_field(_whole(card.get("fieldValues"), f"the fields of #{number}'s card"))
        if card
        else {}
    )
    status_name = _configuration().get(STATUS_FIELD_NAME)
    return {
        "number": found["number"],
        "title": found.get("title"),
        "body": found.get("body"),
        "state": found.get("state"),
        "url": found.get("url"),
        "id": found.get("id"),
        "labels": _whole(found.get("labels"), f"the labels of #{number}"),
        "assignees": _whole(found.get("assignees"), f"the assignees of #{number}"),
        "on_board": card is not None,
        "card": {"id": card["id"], "archived": card.get("isArchived")} if card else None,
        "fields": fields,
        # ⚠️ `None` where the configuration names no status field, which reads
        # apart from `None` for a card whose column is empty only by asking the
        # configuration -- so both are reported rather than collapsed.
        "status": fields.get(str(status_name)) if status_name else None,
    }


def item_number(item: dict | int) -> int:
    """The identifier the branch name and the pull request carry.

    ⚠️ Makes **no host call**, so the pull-request guard does not apply: an `int`
    is returned as given. The card's node id is not this -- a branch name and a
    pull request body carry the issue's number, and the card is addressed by id
    only inside this module.
    """
    return item if isinstance(item, int) else int(item["number"])


# --- searching the board ----------------------------------------------------

ITEMS_QUERY = """
query Items($owner:String!, $number:Int!, $after:String) {
  repositoryOwner(login:$owner) {
    ... on User { projectV2(number:$number) { items(first:100, after:$after) { ...itemPage } } }
    ... on Organization {
      projectV2(number:$number) { items(first:100, after:$after) { ...itemPage } }
    }
  }
}
fragment itemPage on ProjectV2ItemConnection {
  totalCount
  pageInfo { hasNextPage endCursor }
  nodes {
    id
    isArchived
    type
    content {
      __typename
      ... on Issue {
        number
        title
        state
        url
        labels(first:100) { pageInfo { hasNextPage endCursor } nodes { name } }
      }
      ... on PullRequest { number title state url }
      ... on DraftIssue { title }
    }
    fieldValues(first:100) {
      pageInfo { hasNextPage endCursor }
      nodes { ...valueFacts }
    }
  }
}
fragment valueFacts on ProjectV2ItemFieldValue {
  __typename
  ... on ProjectV2ItemFieldSingleSelectValue {
    name
    optionId
    field { ... on ProjectV2FieldCommon { name } }
  }
  ... on ProjectV2ItemFieldTextValue {
    text
    field { ... on ProjectV2FieldCommon { name } }
  }
  ... on ProjectV2ItemFieldNumberValue {
    number
    field { ... on ProjectV2FieldCommon { name } }
  }
  ... on ProjectV2ItemFieldDateValue {
    date
    field { ... on ProjectV2FieldCommon { name } }
  }
  ... on ProjectV2ItemFieldIterationValue {
    title
    iterationId
    field { ... on ProjectV2FieldCommon { name } }
  }
}
"""

# What a card's content is, by the host's typename. A board holds all three, and
# only the first is addressable by the number a role carries.
CONTENT_KINDS = {
    "Issue": "issue",
    "PullRequest": "pull_request",
    "DraftIssue": "draft",
}


def card_entry(node: dict, status_field: str | None) -> dict:
    """One card, in the shape a candidate is judged in.

    ⚠️ A draft card and a pull request card are carried with their kind named and
    **no number**, rather than dropped: a draft saying the same thing as the item
    about to be filed is the duplicate most worth finding, and a list that quietly
    omits it answers the duplicate question wrongly. A role reads `kind` to know
    what it can address.
    """
    content = node.get("content") or {}
    typename = content.get("__typename")
    fields = values_by_field(_whole(node.get("fieldValues"), "a card's fields"))
    labels = (
        _whole(content.get("labels"), f"the labels of #{content.get('number')}")
        if "labels" in content
        else []
    )
    return {
        "kind": CONTENT_KINDS.get(typename, typename),
        "number": content.get("number"),
        "title": content.get("title"),
        "state": content.get("state"),
        "url": content.get("url"),
        "labels": labels,
        "card": {"id": node.get("id"), "archived": node.get("isArchived")},
        "fields": fields,
        "status": fields.get(status_field) if status_field else None,
    }


def matches(entry: dict, words: list[str], labels: list[str], fields: dict) -> bool:
    """Whether one card answers the query.

    ⛔ Matched on the title and the card's own field values, which is what a board
    read gives: a body is one read per card and the layer that judges a candidate
    does that read itself. ⚠️ Stated on the answer as `matched_on`, so a filing
    role reporting a duplicate check reports what the check covered rather than
    what a reader assumes it did.

    ⚠️ **Every term is a substring, in any order and whatever the case** -- so
    `number 42` matches *item number 142* as well as *item number 42*. That
    direction is deliberate: this is the duplicate check, and the failure that
    costs something is a near-duplicate the search did not surface, not a
    candidate the role reads and sets aside.
    """
    title = (entry.get("title") or "").lower()
    if any(word not in title for word in words):
        return False
    carried = {label.get("name") for label in entry.get("labels") or []}
    if any(label not in carried for label in labels):
        return False
    for name, value in (fields or {}).items():
        if entry["fields"].get(name) != value:
            return False
    return True


def search_items(
    terms: str | None = None,
    *,
    labels: list[str] | None = None,
    fields: dict | None = None,
    limit: int = 100,
) -> dict:
    """The cards a query matches, across every state the board holds.

    **Terms, or a field's value with no terms at all, or both** -- which on this
    tracker is the board's own columns, so a field's value is a first-class query
    rather than a label standing in for one.

    ⛔ **No state argument, by construction.** § 3 states the operation across
    every state the tracker holds: the whole board is read and nothing filters by
    status unless the caller asks for that column by name.

    ⛔ **The board is read whole.** Every page is followed, so `at_limit` here is
    exact -- it says the **matches** were cut by the bound, never that the read
    was. ⚠️ That is the one place this answer differs from the implementation next
    door, which cannot tell a result that fills the bound from one the bound cut.

    ⛔ **An unknown field name or an unknown label is refused, never answered with
    an empty list.** Both come back empty from a board that holds the thing and
    from a board that does not, and this is the one search the filing role
    performs: the two readings are a duplicate check that found nothing and a
    duplicate check that never ran. ⚠️ The labels are checked only where the
    answer *is* empty -- a hit proves the label exists and spends no call proving
    it -- while a field name is checked against the board already resolved, which
    costs nothing.
    """
    owner, number = _address()
    status_field = _configuration().get(STATUS_FIELD_NAME)
    status_field = str(status_field) if status_field else None
    for name in (fields or {}):
        _field(name, key=f"tracker.project.field.{name}")
    nodes = _paged(
        lambda cursor: _page(owner, number, cursor),
        what=f"the items of project {number}",
    )
    entries = [card_entry(node, status_field) for node in nodes]
    words = [word for word in (terms or "").lower().split() if word]
    matched = [entry for entry in entries if matches(entry, words, labels or [], fields or {})]
    if labels and not matched:
        unknown = [label for label in labels if not _label_exists(_repo(), label)]
        if unknown:
            raise HostUnavailable(
                f"nothing on project {number} carries "
                f"{', '.join(repr(label) for label in labels)}, and "
                f"{', '.join(repr(label) for label in unknown)} is not a label "
                f"{_repo()} has -- so the empty answer is this search never "
                "running, not this board holding no such item."
            )
    return {
        "terms": terms or "",
        "labels": list(labels or []),
        "fields": dict(fields or {}),
        "matched_on": "title, labels and field values",
        "scanned": len(entries),
        "limit": limit,
        "at_limit": len(matched) > limit,
        "items": matched[:limit],
    }


def _page(owner: str, number: int, cursor):
    owned = _graphql(ITEMS_QUERY, owner=owner, number=number, after=cursor)["repositoryOwner"]
    if owned is None or owned.get("projectV2") is None:
        raise HostUnavailable(
            f"`{owner}` has no project number {number} this credential can see, so "
            "its items could not be read."
        )
    return owned["projectV2"]["items"]


def _label_exists(repo: str, label: str) -> bool:
    """Whether the repository has this label, asked for by name.

    ⛔ Not through `_gh`, because the interesting answer here is a **failure**: the
    host's `404` is what *absent* looks like. So the three cases are separated --
    present, absent, and could-not-be-established -- and only the third raises.

    ⚠️ Asked for by name rather than looked up in a listing: a listing takes a
    bound, and a label past that bound comes back absent from an answer that
    reports no truncation.
    """
    code, _body, stderr = PROBE(["api", f"repos/{repo}/labels/{label}", "--jq", ".name"])
    if code == 0:
        return True
    if NOT_FOUND in stderr:
        return False
    raise HostUnavailable(
        f"`gh api repos/{repo}/labels/{label}` failed with neither a label nor a "
        f"`404`: {stderr.strip() or 'no stderr'}. Whether this repository has "
        "that label could not be established, which is not the same as it not "
        "having it."
    )


# --- writing ----------------------------------------------------------------

ADD_CARD = """
mutation AddCard($project:ID!, $content:ID!) {
  addProjectV2ItemById(input:{projectId:$project, contentId:$content}) {
    item { id }
  }
}
"""

SET_VALUE = """
mutation SetValue($project:ID!, $card:ID!, $field:ID!, $value:ProjectV2FieldValue!) {
  updateProjectV2ItemFieldValue(
    input:{projectId:$project, itemId:$card, fieldId:$field, value:$value}
  ) {
    projectV2Item { id }
  }
}
"""


def create_item(title: str, body: str, labels: list[str] | None = None) -> dict:
    """A new item: the issue, then its card on the board.

    ⚠️ **Two writes, and the first one is what makes the item exist.** A card that
    cannot be added leaves an item on the host and off the board -- which is the
    filing role's own rule that an item exists the moment `create_item` returns,
    so the failure is reported and the create is never retried.

    ⛔ **No status is written here.** The copies measured did create, add and set
    status in one step; the port splits the last one off because a status is asked
    for by **role** (§ 4.2) and this operation has no role to resolve -- the filing
    role's own advance does that, through `set_state`, and a card this leaves with
    an empty column is a card whose status nobody has claimed yet.
    """
    args = ["issue", "create", "--repo", _repo(), "--title", title, "--body", body]
    for label in labels or []:
        args += ["--label", label]
    url = _gh(args, parse=False)
    tail = str(url).rstrip("/").rsplit("/", 1)[-1]
    if not tail.isdigit():
        raise HostUnavailable(
            f"`gh issue create` answered `{url!r}`, whose last path segment is not "
            "a number, so the created item cannot be addressed."
        )
    item = read_item(int(tail))
    if not item["on_board"]:
        _graphql(ADD_CARD, project=_board()["id"], content=item["id"])
        item = read_item(int(tail))
    return item


def _require_card(item: dict) -> str:
    owner, number = _address()
    if not item["on_board"]:
        raise HostUnavailable(
            f"#{item['number']} has no card on project {number} under `{owner}`, so "
            "there is no column to write. Adding it to the board is a different act "
            "from moving it, and this operation does not take one for the other: "
            "file through `create_item`, or add the existing item to the board."
        )
    return item["card"]["id"]


def set_state(number: int, *, status: str) -> dict:
    """Move the card to a column, by name.

    ⚠️ `status` is the **status word the port resolved from the role it was asked
    for** (§ 4.2) -- a role never names it and this adapter never guesses it.

    ⛔ **The board's column, never the issue's own state.** An issue being open or
    closed is a different fact on this tracker, written by the host's automation
    off a merged pull request; a `statuses` list here names this field's options.

    ⛔ Idempotent, by reading before writing -- which is also the pull-request
    guard for this operation. A card already in the column is returned unwritten,
    so a role advancing to a role the item already holds spends no write.
    """
    field = _status_field()
    option = _option_id(field, status)
    item = read_item(number)
    if item["status"] == status:
        return item
    card = _require_card(item)
    _graphql(
        SET_VALUE,
        project=_board()["id"],
        card=card,
        field=field["id"],
        value=json.dumps({"singleSelectOptionId": option}),
    )
    return read_item(number)


def set_field(number: int, field: str, value) -> dict:
    """A value written onto the card, where a facet states the column.

    The operation § 4.3's estimate and § 4.5's date reach a board through. ⛔ The
    column is addressed **by name** like every other id here, and the value's shape
    is taken from the field's own `dataType` rather than from the value handed in:
    a number written into a text column is accepted by the host and read back by
    nobody.

    ⛔ A column the host writes itself -- the title, the labels, the assignees, the
    repository, the stamps -- is refused naming it and its type, because a facet
    pointing there is pointing at a value this procedure cannot own.
    """
    column = _field(field, key=f"tracker.project.field.{field}")
    kind = column["data_type"]
    if kind not in WRITABLE:
        raise ConfigError(
            f"tracker.project.field.{field}",
            f"is a `{kind}` field, which this tracker does not let a value be "
            f"written into. Writable here are: {', '.join(WRITABLE)}. A facet "
            "pointing at this column is pointing at something the host maintains, "
            "and the value belongs in a column of its own.",
        )
    if kind == SINGLE_SELECT:
        shaped = {"singleSelectOptionId": _option_id(column, str(value))}
    elif kind == NUMBER:
        try:
            shaped = {"number": float(value)}
        except (TypeError, ValueError):
            raise ConfigError(
                f"tracker.project.field.{field}",
                f"is a `{kind}` field and was handed `{value!r}`, which is not a "
                "number. The column's own type is what the value is shaped to, so "
                "this is a facet writing the wrong kind of thing rather than a host "
                "refusal.",
            ) from None
    elif kind == DATE:
        shaped = {"date": str(value)}
    else:
        shaped = {"text": str(value)}
    item = read_item(number)
    card = _require_card(item)
    _graphql(
        SET_VALUE,
        project=_board()["id"],
        card=card,
        field=column["id"],
        value=json.dumps(shaped),
    )
    return read_item(number)


def comment(number: int, body: str) -> dict:
    """A note on the item -- a gate result being the measured case.

    Read first, so the pull-request guard covers this too: a comment is a write,
    and posting one on a pull request because the numbers share a sequence is the
    failure the guard exists for.
    """
    item = read_item(number)
    _gh(
        ["issue", "comment", str(number), "--repo", _repo(), "--body", body],
        parse=False,
    )
    return {"number": item["number"], "url": item["url"], "commented": True}


def set_labels(number: int, labels: list[str]) -> dict:
    """Every label in one call, so there is no partial set to report.

    ⛔ **Set, not add**, and both verbs in one call: the host's are `--add-label`
    and `--remove-label`, so adding alone would answer a union where a role asked
    for a set. The labels live on the issue rather than on the card -- the board's
    own `Labels` column is a view of them and is not writable.
    """
    wanted = set(labels)
    item = read_item(number)
    current = {label["name"] for label in item["labels"]}
    if wanted == current:
        return item
    args = ["issue", "edit", str(number), "--repo", _repo()]
    for label in sorted(wanted - current):
        args += ["--add-label", label]
    for label in sorted(current - wanted):
        args += ["--remove-label", label]
    _gh(args, parse=False)
    return read_item(number)


def assign(number: int, who: str = "@me") -> dict:
    """The item assigned to the person the role acts for.

    ⚠️ This says *taken* and nothing more. Where every session authenticates as
    one account it cannot say **which** session holds the item, so a claim does not
    rest on it -- that is § 10's, and `assign`'s own stated fallback says as much.
    """
    read_item(number)
    _gh(
        ["issue", "edit", str(number), "--repo", _repo(), "--add-assignee", who],
        parse=False,
    )
    return read_item(number)


def link_dependency(blocked: int, blocked_by: int) -> dict:
    """One item recorded as blocked by another, as a relation.

    The board holds no relation of its own: a dependency here is a fact about the
    two issues, in the host's own dependencies API. Two measured properties, both
    easy to get backwards:

    - the call is posted on the **blocked** item, not on the blocker;
    - its body carries the blocker's **internal id**, not its number. The two are
      different integers and the wrong one either errors or, worse, addresses an
      unrelated issue.

    ⚠️ The relation bumps neither item's `updated_at`, so nothing that polls for
    modified issues can see it afterwards.

    ⛔ **Both numbers go through `read_item` first**, because the REST endpoint the
    id lookup uses answers for pull requests too: without the guard a pull request
    number records a real relation against a pull request and returns as though it
    had worked.
    """
    repo = _repo()
    read_item(blocked)
    read_item(blocked_by)
    blocker_id = _gh(
        ["api", f"repos/{repo}/issues/{blocked_by}", "--jq", ".id"], parse=False
    )
    _gh([
        "api", "--method", "POST",
        f"repos/{repo}/issues/{blocked}/dependencies/blocked_by",
        "-F", f"issue_id={blocker_id}",
    ])
    return {"blocked": blocked, "blocked_by": blocked_by, "blocker_id": int(blocker_id)}


def link_for_close(number: int) -> str:
    """The reference that closes the item when the branch lands.

    Declarative: the text goes in the pull request body and the host does the rest
    on merge. Returned rather than written, because the body belongs to the role
    opening the pull request.

    ⚠️ Makes **no host call**, so the pull-request guard does not apply here -- it
    composes a string out of the number it was given and asserts nothing about what
    that number names.
    """
    return f"Closes #{number}"


CLOSED_BY_QUERY = """
query ClosedBy($owner:String!, $name:String!, $number:Int!) {
  repository(owner:$owner, name:$name) {
    issue(number:$number) {
      state
      closedByPullRequestsReferences(first:10, includeClosedPrs:true) {
        pageInfo { hasNextPage endCursor }
        nodes { number merged mergeCommit { oid } }
      }
    }
  }
}
"""


def advance_on_merge(number: int) -> dict:
    """What the host's and the board's own automation did off the merge.

    A confirmation and not an assertion. Two automations can move an item here and
    they are not the same one: the host closes the issue off a closing reference in
    a merged pull request, and the **board's** workflow sets a column when an issue
    closes. So this reports three facts and judges one -- the issue's state, the
    card's column, and which merged pull request closed it.

    ⛔ **Closed is not advanced.** The move is reported only where a pull request
    that closed this item actually merged. An item somebody closed by hand is
    `advanced: false` with the state named, which is the answer a role needs.

    ⚠️ **Whether the *column* moved is the role's to read**, against its own
    `statuses` mapping: a board whose workflow is not enabled leaves the column
    where it was with the issue closed, and that shows here as a status this
    answer carries rather than as a move this operation claims.
    """
    item = read_item(number)
    owner, name = _repo().split("/")
    issue = (
        _graphql(CLOSED_BY_QUERY, owner=owner, name=name, number=int(number))
        .get("repository", {})
        .get("issue")
    )
    if issue is None:
        raise HostUnavailable(
            f"the host answered null for #{number} in {owner}/{name} when asked "
            "what closed it, so the automation's work could not be read."
        )
    merged = [
        node
        for node in _whole(
            issue.get("closedByPullRequestsReferences"),
            f"the pull requests that closed #{number}",
        )
        if node.get("merged")
    ]
    return {
        "number": number,
        "advanced": str(issue.get("state", "")).lower() == "closed" and bool(merged),
        "state": issue.get("state"),
        "status": item["status"],
        "on_board": item["on_board"],
        "merged_by": [
            {"pull_request": node["number"], "commit": (node.get("mergeCommit") or {}).get("oid")}
            for node in merged
        ],
    }


ADAPTER = port.Adapter(binder=bind, operations={
    "read_item": read_item,
    "search_items": search_items,
    "create_item": create_item,
    "item_number": item_number,
    "set_state": set_state,
    "set_field": set_field,
    "comment": comment,
    "set_labels": set_labels,
    "assign": assign,
    "link_dependency": link_dependency,
    "link_for_close": link_for_close,
    "advance_on_merge": advance_on_merge,
    # ⛔ No `checklist_read`, `checklist_write` or `checklist_item_delete`: an
    # issue has no check-item object, and a board column is not one either. See
    # the module docstring.
})

# The three the module docstring argues are absent because the tracker has
# nothing to implement them against. ⛔ Written once, here, and read by the
# self-test's completeness check rather than restated in it: a fourth absence
# would otherwise be an operation nobody noticed going missing.
DELIBERATELY_ABSENT = ("checklist_read", "checklist_write", "checklist_item_delete")


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
        "SetValue": {"updateProjectV2ItemFieldValue": {"projectV2Item": {"id": "PVTI_card"}}},
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
        global TRANSPORT
        was = TRANSPORT
        TRANSPORT = host
        try:
            return ran(call)
        finally:
            TRANSPORT = was

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
    documents = [BOARD_QUERY, ITEM_QUERY, ITEMS_QUERY, CLOSED_BY_QUERY, ADD_CARD, SET_VALUE]
    check(
        "no query asks for a field by name, which is the shape the host refuses twice over",
        not any("fieldValueByName" in document for document in documents),
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
    _boards.clear()
    moved = _Host(
        {
            "Board": _board_payload_for(_page_of(FIELD_NODES)),
            "Item": _issue_payload(7, status="Todo"),
            "SetValue": {"updateProjectV2ItemFieldValue": {"projectV2Item": {"id": "PVTI_card"}}},
        }
    )
    with_host(moved, lambda: set_state(7, status="In Progress"))
    check(
        "an advance reads the item before it writes the column",
        moved.calls.index("Item") < moved.calls.index("SetValue"),
        f"called {moved.calls}",
    )
    written = next(
        call for call in moved.calls if call == "SetValue"
    )
    check("and writes it once", moved.calls.count("SetValue") == 1, f"called {moved.calls}")
    check("naming the mutation the host answers", written == "SetValue")

    _boards.clear()
    already = _Host(
        {
            "Board": _board_payload_for(_page_of(FIELD_NODES)),
            "Item": _issue_payload(7, status="In Progress"),
        }
    )
    with_host(already, lambda: set_state(7, status="In Progress"))
    check(
        "an advance to the column the card already holds writes nothing",
        "SetValue" not in already.calls,
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
        "SetValue" not in unknown.calls,
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
    for column, value, shape in (
        ("Estimate", 3, "number"),
        ("Due", "2026-10-22", "date"),
        ("Notes", "a note", "text"),
        ("Status", "Done", "singleSelectOptionId"),
    ):
        _boards.clear()
        host = _Host(
            {
                "Board": _board_payload_for(_page_of(FIELD_NODES)),
                "Item": _issue_payload(7),
                "SetValue": {
                    "updateProjectV2ItemFieldValue": {"projectV2Item": {"id": "PVTI_card"}}
                },
            }
        )
        sent: list[str] = []
        recording = host.__call__

        def transport(args, parse=True, recording=recording, sent=sent):
            sent.extend(part for part in args if part.startswith("value="))
            return recording(args, parse)

        with_host(transport, lambda column=column, value=value: set_field(7, column, value))
        check(
            f"a `{shape}` column is written in the shape its own type takes",
            any(shape in part for part in sent),
            f"sent {sent!r}",
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
        reported == "tracker.project.field.Estimate" and "SetValue" not in host.calls,
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
        global PROBE
        was = PROBE
        PROBE = lambda args: answer
        try:
            return call()
        finally:
            PROBE = was

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
        "SetValue" not in host.calls,
        f"called {host.calls}",
    )

    # ⛔ The module left as the port found it. This suite binds a configuration
    # and resolves boards against a substituted host; a run inside a longer
    # process -- which is what the gate's runner is -- would otherwise leave an
    # example's address cached behind a real role's first call.
    global _bound
    _bound = None
    _boards.clear()

    if failures:
        print(f"\n{failures} assertion(s) did not hold.")
    return 1 if failures else 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="A board behind the tracker port: its own suite.",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="hold this implementation to the shapes the board answers in",
    )
    args = parser.parse_args(argv)
    if not args.self_test:
        parser.print_help()
        return 0
    print(f"Holding the `{KIND}` implementation to the shapes it was measured against:")
    return self_test()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
