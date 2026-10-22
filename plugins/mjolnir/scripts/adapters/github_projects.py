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

# One document per value kind, each taking the value as a **typed scalar**.
#
# ⛔ Measured against the live host: handing the whole value object in as one
# variable is refused -- `Variable $value of type ProjectV2FieldValue! was
# provided invalid value` -- because the client sends a variable as a string and
# the host wants an input object. ⚠️ And the fix is not to build the input by
# pasting the value into the document: a scalar variable per kind lets the host do
# the typing and leaves nothing to quote. So the column's own `dataType` chooses
# the document, which is the same dispatch `WRITES` below states once.
_SET_VALUE = """
mutation %(name)s($project:ID!, $card:ID!, $field:ID!, $%(variable)s:%(type)s!) {
  updateProjectV2ItemFieldValue(
    input:{
      projectId:$project, itemId:$card, fieldId:$field,
      value:{%(key)s:$%(variable)s}
    }
  ) {
    projectV2Item { id }
  }
}
"""

SET_OPTION = _SET_VALUE % {
    "name": "SetOption", "variable": "option", "type": "String",
    "key": "singleSelectOptionId",
}
SET_TEXT = _SET_VALUE % {"name": "SetText", "variable": "text", "type": "String", "key": "text"}
SET_DATE = _SET_VALUE % {"name": "SetDate", "variable": "date", "type": "Date", "key": "date"}

# ⛔ The one value that cannot travel as a variable at all. Measured against the
# live host: the client's typed field parses an integer and leaves anything else a
# **string**, so `Float!` comes back as *provided invalid value* -- and the
# untyped field is a string by definition. So the number is formatted into the
# document, which is safe for exactly one reason and it is not a general one: the
# value is a `float` by then, so it cannot carry a quote, a brace or a second
# field, and a non-finite one is refused rather than formatted.
SET_NUMBER = """
mutation SetNumber($project:ID!, $card:ID!, $field:ID!) {
  updateProjectV2ItemFieldValue(
    input:{
      projectId:$project, itemId:$card, fieldId:$field,
      value:{number:%(number)s}
    }
  ) {
    projectV2Item { id }
  }
}
"""


def _write_option(value):
    return SET_OPTION, {"option": value}


def _write_text(value):
    return SET_TEXT, {"text": value}


def _write_date(value):
    return SET_DATE, {"date": value}


def _write_number(value):
    number = float(value)
    if number != number or number in (float("inf"), float("-inf")):
        raise ConfigError(
            "tracker.project.field",
            f"was handed `{value!r}` for a number column, which is not a finite "
            "number. The value is formatted into the request, and a word the host "
            "would read as a syntax error is refused here instead.",
        )
    return SET_NUMBER % {"number": repr(number)}, {}


# `dataType -> what writes it`. ⛔ A mapping rather than a chain, for the reason
# the value **reader** is one: a kind with no arm reads as a column nobody can
# write, and the refusal has to name the type rather than fall through to the text
# form and write something plausible.
WRITES = {
    SINGLE_SELECT: _write_option,
    TEXT: _write_text,
    NUMBER: _write_number,
    DATE: _write_date,
}


def _write_value(card: str, field: dict, value) -> None:
    """One field value written, in the shape the column's own type takes."""
    document, variables = WRITES[field["data_type"]](value)
    _graphql(
        document,
        project=_board()["id"],
        card=card,
        field=field["id"],
        **variables,
    )


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
    _write_value(card, field, option)
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
        shaped = _option_id(column, str(value))
    elif kind == NUMBER:
        try:
            shaped = float(value)
        except (TypeError, ValueError):
            raise ConfigError(
                f"tracker.project.field.{field}",
                f"is a `{kind}` field and was handed `{value!r}`, which is not a "
                "number. The column's own type is what the value is shaped to, so "
                "this is a facet writing the wrong kind of thing rather than a host "
                "refusal.",
            ) from None
    elif kind == DATE:
        shaped = str(value)
    else:
        shaped = str(value)
    item = read_item(number)
    card = _require_card(item)
    _write_value(card, column, shaped)
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



def self_test() -> int:
    """This implementation's own suite, which lives in the module beside it.

    ⛔ **A module of its own, and the host decided that rather than taste**: a file
    this size reaches the code host with **no patch at all**, and the gate that
    holds every added line to the deferral rule then refuses the change -- a marker
    in a file nothing read is not an absence of markers. Measured on this
    implementation's own first change, where the host supplied a patch for every
    other file in it.

    ⚠️ The suite's module name opens with `_`, which is what keeps discovery from
    reading it as an implementation that names no kind.
    """
    from adapters import _github_projects_suite as suite

    return suite.self_test()


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
