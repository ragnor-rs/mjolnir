#!/usr/bin/env python3
"""Cards on a board behind the port: a state is a list, and a number is board-relative.

The third implementation, and the first one whose tracker is not the code host.
Everything the two beside it get for free -- one number sequence shared with the
pull requests, a relation between two items, a keyword that closes an item on
merge -- is either absent here or means something else, so this is the module
that makes the capability query carry weight rather than answer yes fifteen
times.

What it implements, and what it deliberately does not:

  * **Twelve of the fifteen operations § 3 states.** Three have nothing behind
    them and are named once in `DELIBERATELY_ABSENT` below: there is no relation
    between two cards, no reference that closes a card when a branch lands, and
    therefore no automation to confirm off a merge. ⛔ Each of those is a
    property of the tracker and not a shortcut here -- the card moves because the
    procedure moves it, through `set_state`, which is exactly what
    `advance_on_merge`'s stated fallback says to do.
  * **The three checklist operations are present, and this is the first
    implementation where they are.** Both implementations beside this one leave
    them absent because an issue has no check-item object; a card has one, so the
    three fallbacks stop being the only behaviour anything has.
  * **A state is a list, and the list is resolved by name.** `lists: { resolve:
    by_name }` on this surface is what this module makes true: a `statuses` list
    here names the board's own lists (§ 4.2), and no list id is written anywhere.
    ⚠️ Two lists may carry one name and a list name may be empty, because Trello
    holds neither uniqueness nor presence for it -- both are refused with the key
    named rather than resolved by position.
  * **A card number is relative to its board**, which is the sharpest difference
    from the two implementations beside this one. `idShort` counts up per board,
    so the same number names a different card on another board and `tracker.board`
    is the whole of what makes a number mean anything. ⛔ And there is **no
    pull-request guard here, by construction rather than by omission**: the two
    modules next door need one because issues and pull requests share one
    sequence on the code host, while nothing but a card lives in this sequence.
  * **The number is read from the field and parsed from the URL, in that order.**
    Measured on live cards: the URL is `/c/<shortLink>/<number>-<slug>`, and one
    real interface over this tracker answers a card with no short-id field at all
    -- which is what `docs/configuration-surface.md`'s survey recorded. The
    reference documents `idShort` on the card object, so the field is preferred
    and the URL is the arm that stays correct for an answer that omits it, a
    `fields=` narrowed read included.
  * **Filing resolves the `initial` role, because a card cannot exist with no
    state.** `idList` is required to create one. The two implementations beside
    this one leave the column empty and let the filing role's own advance set it;
    here there is no such moment, so the list is the status § 4.2 maps to
    `initial` and a project that maps no `initial` role is refused with
    `statuses` named. ⚠️ That is the one place this tracker forces a question the
    other two could leave open.
  * **Every write that carries text is held to `policy.forbid_on_item` first.**
    § 3 states that a write may be forbidden by policy rather than by capability
    and that a role meets a refusal; this is the first implementation to carry
    one, and it is here rather than in the contract because the contract cannot
    tell which argument of an operation is text bound for an item. ⛔ A class the
    project names that this module has no form for **refuses the write** rather
    than passing it: a policy that cannot be answered is not a policy that was
    observed.
  * **`search_items` reads the board whole or refuses it.** The endpoint names no
    cursor, so there is no page to follow and nothing to truncate -- but a
    collection the host caps answers short with nothing saying so, which is the
    same defect the board implementation pays a cursor-follower to avoid. An
    answer that reaches the documented ceiling is refused.

Every call goes over HTTP with a key and a token, read from the environment and
⛔ **never written into a message**: the one surface a failure here is reported
on would otherwise carry the credential (§ 14). ⛔ **Through one named seam**,
`TRANSPORT`, which answers with the status rather than raising -- so a body, the
host's own `404` and a call that never reached the host are all three available
at every call site, and no second seam is needed for the paths that read a
failure.

The configuration arrives from the port through `bind`; nothing here resolves a
project for itself.

What this module has **not** been run against is a live board: the pair of
variables below is what a run needs and this repository's own shell holds
neither, so every shape below is read from the tracker's published reference or
measured through an interface that is not this one. Which is which, and the
three answers that are the reference's alone, are recorded in
`docs/configuration-surface.md`.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request

# The package's parent, appended rather than prepended: this module is imported
# as `adapters.trello`, so the contract beside it is not otherwise on the path,
# and putting it first would shadow a standard-library name.
_SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SCRIPTS not in sys.path:
    sys.path.append(_SCRIPTS)

import boundary  # noqa: E402
import port  # noqa: E402
from port import ConfigError, HostUnavailable  # noqa: E402

KIND = "trello"

# Where the tracker answers, and the two variables that address it. ⛔ A pair
# rather than one token, which is how this tracker is addressed: a list naming
# only the second would read as complete, and the shipped example's
# `environment.inherits` names both for that reason.
BASE = "https://api.trello.com/1"
KEY_VARIABLE = "TRELLO_KEY"
TOKEN_VARIABLE = "TRELLO_TOKEN"

# How long one call may take. Past this the call did not happen, which is a
# failure naming the request rather than an absence.
TIMEOUT = 30

# What the host answers when the thing asked for is not there, and when the key
# or the token is wrong. ⛔ Kept apart: the first is an absence a caller may act
# on, the second is this module's own address being wrong and is never read as a
# card that does not exist.
NOT_FOUND = 404
UNAUTHORISED = (401, 403)
RATE_LIMITED = 429

# The status this module uses for a call that never reached the host at all --
# a name that does not resolve, a socket that timed out. ⚠️ Not folded into the
# `>= 400` arm: a call that was refused by the host and a call the host never
# saw are two different facts, and only the first says anything about the card.
UNREACHED = 0

# What a collection answers at most. ⛔ Read as a ceiling to refuse at rather
# than a page to follow: the board's own card endpoint names no cursor, so an
# answer that exactly fills this is indistinguishable from one the host cut, and
# a short list answering a duplicate check reads exactly like a tracker holding
# nothing. ⚠️ A board that genuinely holds this many is refused too, which is
# the safe direction of the two.
COLLECTION_CEILING = 1000

# The two states a card itself has, which are **not** the project's states. A
# card is in a list and that is § 4.2's vocabulary; being archived is a separate
# fact the host holds, and both are reported rather than collapsed.
OPEN = "open"
ARCHIVED = "archived"

# What `set_field` may write, by the shape the host takes for it. ⛔ The card's
# own fields and nothing else: a value anywhere else on this tracker lives in a
# custom field, which needs a power-up on the board and whose write shape is
# unmeasured here -- so a facet pointing there is refused naming what it would
# need rather than written somewhere plausible. ⚠️ The live board the survey was
# taken from carries **no** custom field at all, which is why the one value
# § 4.5 names reaches this tracker as the card's own `due`.
TEXT, DATE, FLAG = "text", "date", "flag"
WRITABLE = {
    "name": TEXT,
    "desc": TEXT,
    "due": DATE,
    "start": DATE,
    "dueComplete": FLAG,
}

# The card fields another operation owns. ⛔ Refused by name with that operation
# named, rather than falling through to the refusal above: a facet pointing here
# is pointing at a value this procedure writes through a different question, and
# a refusal saying *no such field* would send somebody looking for a field that
# is right there.
OWNED_ELSEWHERE = {
    "idList": "set_state",
    "idLabels": "set_labels",
    "idMembers": "assign",
    "closed": "no operation -- archiving a card is not a state this procedure writes",
}

# What a date column holds. ⛔ Held here rather than left to the host: § 4.5's
# date is a date and this field is a date-time, so the one shape that is not
# invented is the start of that day in the host's own zone -- and an unparseable
# value is refused naming the field rather than coming back as the host's
# complaint about a scalar.
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
START_OF_DAY = "T00:00:00.000Z"

# What a value this module puts into a request **path** may not carry. ⛔ One
# grammar for the two of them -- the board the configuration states and the
# member a role names -- because the failure is the same: one of these characters
# addresses an endpoint other than the one the call means, and the host answers
# **that** endpoint rather than refusing.
#
# ⛔ **A forbidden set and not an allowed one**, which is the narrower claim and
# the only correct one. An allow-list of what an id may contain refuses the
# `<placeholder>` forms the shipped examples carry -- measured on this
# tracker's own example, whose board is a placeholder and which is this
# implementation's suite fixture -- and it would be refusing for a reason it
# could not state, since a bracket in a path segment is answered by the host
# visibly. These four are the ones that are *not* answered visibly: three
# delimiters that end the path segment, and the escape that can spell the first
# of them.
#
# ⚠️ Every id the host itself hands back goes into a path too and is held to
# none of this: those came out of an answer this module read, so holding them
# would be checking the host against itself.
REDIRECTS_THE_CALL = re.compile(r"[/?#%]")

# A card's URL, and the number inside it. ⚠️ Measured on live cards: the slug is
# percent-encoded wherever the title is not ASCII, so the number is read as the
# digits that open the last path segment rather than by splitting on a dash --
# a title that opens with a year would otherwise take the slug's digits.
CARD_NUMBER_IN_URL = re.compile(r"/c/[^/]+/(?P<number>\d+)(?:-|$)")

# --- what a policy bars, and the form each class has ------------------------
#
# ⛔ One form per class the surface states, each a shape rather than a word
# list, and ⛔ nothing here matched by how a sentence reads: a class decided by
# meaning is a guard whose refusals cannot be argued with.
#
# ⚠️ `credentials` is not given a form here at all. § 14's own arm already
# carries one, it binds regardless of configuration, and a second grammar for
# the same class is two statements allowed to disagree -- so this reads that one.

FENCE = re.compile(r"^\s*(?:```|~~~)", re.MULTILINE)

# A path with a separator in it and a file extension at the end, or one rooted
# at `/` or `./`. ⚠️ A URL's path matches this where it ends in a file, which is
# two findings for one span rather than a miss: both classes are barred and the
# refusal names each it found.
FILE_PATH = re.compile(
    r"(?:(?<![\w/])(?:\.{1,2}/|/)[\w.-]+(?:/[\w.-]+)*"
    r"|(?<![\w/])[\w.-]+(?:/[\w.-]+)+\.[A-Za-z][A-Za-z0-9]{0,7})(?![\w/])"
)

# ⚠️ The third of these collides with a file-and-line citation, and that is
# stated rather than tightened away: `a.b:12` is a host and a port and a file and
# a line in the same characters, and nothing lexical tells them apart. So the
# class named may be the wrong one of two -- which costs nothing where a project
# bars both, as the shipped example does, and fails closed where it bars one.
HOSTING = [
    re.compile(r"\b[a-z][a-z0-9+.-]*://", re.I),
    re.compile(r"(?<![\w.])\d{1,3}(?:\.\d{1,3}){3}(?![\w.])"),
    re.compile(r"\b[a-z0-9-]+(?:\.[a-z0-9-]+)+:\d{2,5}\b", re.I),
]


def _branch_name_form(prefixes: list[str]) -> re.Pattern:
    """A branch name, from the prefixes the project's own configuration states.

    ⛔ Derived rather than written: § 10 composes a branch name out of
    `work_item.type_branch_prefix`, so the prefixes a project states are exactly
    what one of its branch names can open with. A form written here would be a
    second statement of the same thing, wrong for every project whose prefixes
    are not the example's.
    """
    alternation = "|".join(re.escape(prefix) for prefix in sorted(set(prefixes)))
    return re.compile(rf"\b(?:{alternation})/[\w.-]+", re.I)


# --- the configuration, handed down -----------------------------------------
#
# ⛔ Never resolved here and never from the working directory, for § 3's reason:
# a process serving more than one project must address each one's own board.
_bound = None

# Resolved boards, keyed by the board the configuration named. Keyed rather than
# process-wide, for the reason the module next door records: two projects in one
# process have two boards. ⚠️ A board resolved here goes stale within a run -- a
# list added or a card filed seconds ago is absent from it -- so a name or a
# number that does not resolve re-reads the board once before refusing.
_boards: dict[str, dict] = {}


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
            "tracker.adapters.trello",
            "was asked for an operation before the port bound a configuration to "
            "it. Every operation is reached through `Port.invoke`, which binds "
            "first; a direct call bypasses the one place the project is stated.",
        )
    return _bound


def _board_id() -> str:
    """The board every call here addresses.

    The surface marks `tracker.board` `# required_when: tracker.kind = trello`,
    so a configuration that reached here states one; what is refused is a value
    that cannot address a board, since the host answers a malformed id and a
    board somebody else owns with the same `404` and only the first is a
    configuration this reader can name.
    """
    board = _configuration().get("tracker.board")
    if not board or not str(board).strip():
        raise ConfigError(
            "tracker.board",
            "states no board, so nothing here can be addressed. A card number is "
            "relative to its board, so this key is also what makes a number mean "
            "anything at all.",
        )
    board = str(board).strip()
    # ⛔ Held to a shape, because this value is interpolated into a **path**. An
    # id carrying a separator addresses a different endpoint than the one the
    # call means -- `a/b` turns the board's own list read into something else
    # entirely -- and the host would answer that other endpoint rather than
    # refuse. ⚠️ The two forms this tracker hands out are both plain: the long
    # id and the short link. A URL is the commonest thing to paste here and is
    # refused by name, since it carries the separators and nothing else would
    # say why the call went somewhere unexpected.
    found = REDIRECTS_THE_CALL.search(board)
    if found:
        raise ConfigError(
            "tracker.board",
            f"carries `{found.group(0)}` at character {found.start()}, which would "
            "address a different endpoint than the call means: this value is put "
            "into a request path. Both forms this tracker hands out are plain -- "
            "the long id and the short link out of the board's own URL -- so what "
            "usually lands here instead is the whole URL.",
        )
    return board


# --- the host, through one named seam ---------------------------------------


def _credentials() -> dict[str, str]:
    """The key and the token, from the environment.

    ⛔ A failure rather than an absence. § 3 holds a credential that is wrong
    apart from a capability that is missing, and a role must not take a stated
    fallback because a variable was unset: the fallback answers a tracker that
    **cannot**, never one this module could not reach.
    """
    key = os.environ.get(KEY_VARIABLE)
    token = os.environ.get(TOKEN_VARIABLE)
    missing = [
        name
        for name, value in ((KEY_VARIABLE, key), (TOKEN_VARIABLE, token))
        if not value
    ]
    if missing:
        raise HostUnavailable(
            f"the shell holds no {' and no '.join(missing)}, so no call to this "
            "tracker could be made. The pair addresses it together -- one without "
            "the other authenticates nothing -- and § 14 states that the project "
            "names them in `environment.inherits` rather than carrying a value."
        )
    return {"key": key, "token": token}


def _shown(method: str, path: str, params: dict) -> str:
    """One call, as a person could re-run it, with the credential named not shown.

    ⛔ The whole reason this exists. Every failure below quotes the call, and the
    call carries the key and the token: a message that printed them would publish
    the credential to the one surface the report is read on, which is § 14's rule
    about a refusal that quotes what it refused.
    """
    shown = {
        name: (f"<{KEY_VARIABLE}>" if name == "key" else f"<{TOKEN_VARIABLE}>")
        if name in ("key", "token")
        else value
        for name, value in params.items()
    }
    query = urllib.parse.urlencode(shown, doseq=True)
    return f"{method} {BASE}{path}" + (f"?{query}" if query else "")


def _urlopen_request(method: str, path: str, params: dict) -> tuple[int, str]:
    """One HTTP call, answering with its status rather than raising on one.

    ⛔ The status is **in the answer**, which is why this module needs one seam
    where the module next door needs two: the three answers a caller may have to
    tell apart -- a body, the host's own `404`, and a call that never reached the
    host -- are all available here without a second path that bypasses the first.

    ⚠️ `UNREACHED` rather than an exception for the last of those: a name that
    does not resolve and a socket that timed out are failures, but they are
    failures the *caller* has to be able to report against the call it made, and
    a traceback out of here is what the contract exists to keep away from a role.
    """
    query = urllib.parse.urlencode(params, doseq=True)
    request = urllib.request.Request(f"{BASE}{path}?{query}", method=method)
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as answer:
            return answer.status, answer.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as error:
        # The host answered, and its answer is the status. The body is read
        # because this tracker explains a refusal in it -- which limit was hit,
        # which field was wrong -- and that text is what a failure quotes.
        return error.code, error.read().decode("utf-8", "replace")
    except urllib.error.URLError as error:
        return UNREACHED, f"{type(error.reason).__name__}: {error.reason}"
    except (TimeoutError, socket.timeout):
        return UNREACHED, f"timed out after {TIMEOUT}s"


# The one seam. ⛔ Named, rather than left as a call this module makes directly:
# what earns a test here is a parse, an ordering or a guard over the host's
# answers, and every one of those is unreachable from a suite that cannot answer
# as the host. Rebound for the length of a case and restored, never for a
# process.
TRANSPORT = _urlopen_request


def _call(method: str, path: str, *, parse: bool = True, **params):
    """One host call whose answer is a body, with every other outcome a failure.

    ⛔ `port.HostUnavailable` rather than a class of this module's: the port
    turns it into a `failed` outcome, and a role must be able to tell a broken
    call from a missing capability without knowing which tracker answered.
    """
    params = dict(params)
    params.update(_credentials())
    shown = _shown(method, path, params)
    status, body = TRANSPORT(method, path, params)
    if status == UNREACHED:
        raise HostUnavailable(f"`{shown}` never reached the host: {body}")
    if status == RATE_LIMITED:
        raise HostUnavailable(
            f"`{shown}` was rate limited by the host ({body.strip() or 'no body'}). "
            "That is this credential's own budget rather than anything about the "
            "card, and a role must not read it as a tracker that cannot."
        )
    if status in UNAUTHORISED:
        raise HostUnavailable(
            f"`{shown}` was refused as unauthorised (HTTP {status}). The key and "
            "the token address this tracker together, and a board somebody else "
            "owns is invisible to a credential rather than refused by name -- so "
            "this is the address being wrong and never a card that is not there."
        )
    if status == NOT_FOUND:
        # ⚠️ Its own wording, because every id in a call here was read from the
        # board moments earlier: a `404` is the thing having gone between that
        # read and this call rather than a name nobody resolved, and the remedy
        # is a re-read rather than a correction to the configuration.
        raise HostUnavailable(
            f"`{shown}` answered {NOT_FOUND}. Every id in that call was read from "
            "the board, so this is the card, list or label having moved or been "
            "deleted since -- not a name that never resolved."
        )
    if status >= 400:
        raise HostUnavailable(
            f"`{shown}` failed with HTTP {status}: {body.strip() or 'no body'}"
        )
    if not parse:
        return body.strip()
    if not body.strip():
        raise HostUnavailable(f"`{shown}` answered with nothing where a body was expected")
    try:
        return json.loads(body)
    except ValueError as error:
        raise HostUnavailable(
            f"`{shown}` answered something that is not JSON ({error}), so the "
            "answer could not be read at all -- which is not the same as its "
            "being empty."
        ) from None


# ⛔ There is deliberately **no probe function here**, and the absence is the
# point: the module next door carries one because it has to ask the host whether
# a label exists, and the host's `404` is what *absent* looks like there. Every
# name resolved here is resolved against the board's own answer instead -- the
# lists, the labels and the members arrive in one read and a name outside them is
# refused from what was read, never by asking. ⚠️ So `NOT_FOUND` above is read in
# exactly one place, `_call`, where it is a failure like any other status.


# --- the board, resolved by name in one place -------------------------------


def _by_name(nodes: list) -> dict[str, list[dict]]:
    """`name -> every node carrying it`, as a list because a name is not unique.

    ⛔ A list per name and never one node. This tracker holds neither uniqueness
    nor presence for a list's or a label's name -- a default board ships six
    labels with no name at all -- so a mapping that kept one node per name would
    resolve an ambiguous name by whichever came last in the answer.
    """
    found: dict[str, list[dict]] = {}
    for node in nodes:
        name = node.get("name")
        if name is None:
            continue
        found.setdefault(str(name), []).append(node)
    return found


def _board_payload(board: str) -> dict:
    """Everything a name is resolved against, read in four calls.

    ⛔ The lists, the labels, the members and the cards, and every id in the
    answer is the host's: nothing here composes one, and the names are the
    configuration's -- which is the whole of `lists: { resolve: by_name }`.

    ⚠️ The cards are read with `filter=all` through the documented path form,
    rather than through the number-shaped overload of the same path segment: a
    number there resolves a card and a word there filters a list, which is one
    slot carrying two meanings and only the filter half is documented. The index
    is also the only way to reach an **archived** card by number.
    """
    lists = _call("GET", f"/boards/{board}/lists", filter="all", fields="id,name,closed,pos")
    labels = _call(
        "GET", f"/boards/{board}/labels", fields="id,name,color", limit=COLLECTION_CEILING
    )
    members = _call("GET", f"/boards/{board}/members", fields="id,username,fullName")
    # ⛔ Every field a search entry reports, and **not** the description: that is
    # one body per card for every card on the board, read to match on titles.
    # What makes the omission safe rather than silent is that the answer carries
    # no `body` key at all (`_shaped`), so an unread description cannot be read
    # as a card without one.
    cards = _call(
        "GET",
        f"/boards/{board}/cards/all",
        fields="id,idShort,name,closed,idList,idLabels,idMembers,url,shortUrl,due,dueComplete",
    )
    for what, nodes in (("lists", lists), ("labels", labels), ("cards", cards)):
        if isinstance(nodes, list) and len(nodes) >= COLLECTION_CEILING:
            raise HostUnavailable(
                f"the {what} of board `{board}` came back with {len(nodes)} node(s), "
                f"which is the {COLLECTION_CEILING} a collection answers at most. "
                "The endpoint names no cursor, so an answer that fills the ceiling "
                "cannot be told from one the host cut -- it is refused rather than "
                "returned short, a board that genuinely holds that many included."
            )
    return {
        "board": board,
        "lists": _by_name(lists),
        "labels": _by_name(labels),
        "members": {str(member.get("id")): member for member in members},
        "cards": cards,
        "by_number": {
            int(card["idShort"]): card
            for card in cards
            if isinstance(card.get("idShort"), int)
        },
    }


def _board(*, again: bool = False) -> dict:
    """The configured board, resolved once per address.

    `again=True` re-reads it, which is the one answer to a name or a number that
    does not resolve: a list, a label or a card created after this process
    started is absent from a board resolved before it existed, and refusing on a
    stale reading would be a refusal about the host's state at the wrong moment.
    """
    board = _board_id()
    if again or board not in _boards:
        _boards[board] = _board_payload(board)
    return _boards[board]


def _one(nodes: list[dict], name: str, *, what: str, key: str, board: dict) -> dict:
    """The single node a name resolves to, or a refusal naming the key.

    Three refusals, and ⛔ **the middle one is the reason this exists**: a name
    two nodes carry has no answer, and taking either would move a card to
    whichever column the host happened to list second.
    """
    if not nodes:
        known = ", ".join(sorted(board[what])) or "none"
        raise ConfigError(
            key,
            f"names the {what[:-1]} `{name}`, which board `{board['board']}` does "
            f"not have. Its {what} are: {known}. A {what[:-1]} is addressed by "
            "name here and the id is read from the board, so this is a name the "
            "board does not answer to rather than an id gone stale.",
        )
    if len(nodes) > 1:
        raise ConfigError(
            key,
            f"names the {what[:-1]} `{name}`, which board `{board['board']}` has "
            f"{len(nodes)} of. This tracker holds no uniqueness for the name, so "
            "there is no reading of which one was meant -- rename one on the "
            "board, or name one that is unambiguous.",
        )
    return nodes[0]


def _list_named(name: str, *, key: str = "statuses", again: bool = False) -> dict:
    """One of the board's lists, by name, re-reading the board before refusing."""
    board = _board(again=again)
    if str(name) not in board["lists"] and not again:
        return _list_named(name, key=key, again=True)
    return _one(board["lists"].get(str(name), []), str(name), what="lists", key=key, board=board)


def _label_named(name: str, *, key: str, again: bool = False) -> dict:
    """One of the board's labels, by name, re-reading the board before refusing."""
    board = _board(again=again)
    if str(name) not in board["labels"] and not again:
        return _label_named(name, key=key, again=True)
    return _one(board["labels"].get(str(name), []), str(name), what="labels", key=key, board=board)


def _card_for(number: int, *, again: bool = False) -> dict:
    """The card a number names on the configured board.

    ⛔ Resolved through the board's own index and never by handing the number to
    the host as an id: `idShort` counts up per board and is not an address this
    tracker accepts anywhere a card id is taken. ⚠️ Which is also why the board
    is re-read once before refusing -- a card filed seconds ago is absent from an
    index built before it existed, and `create_item` depends on exactly that.
    """
    board = _board(again=again)
    try:
        wanted = int(number)
    except (TypeError, ValueError):
        raise ConfigError(
            "tracker.operations.read_item",
            f"was asked for `{number!r}`, which is not a card number. A number "
            "here is the card's own count on its board, which is digits.",
        ) from None
    if wanted in board["by_number"]:
        return board["by_number"][wanted]
    if not again:
        return _card_for(number, again=True)
    raise HostUnavailable(
        f"board `{board['board']}` holds no card numbered {wanted}. A number here "
        "is relative to its board, so the same number names a different card "
        "elsewhere and this is the board `tracker.board` states rather than a "
        "number that exists nowhere."
    )


# --- what a policy bars ------------------------------------------------------


def policy_classes() -> list[str]:
    """What the bound configuration bars from reaching a card, in its own words."""
    stated = _configuration().get("tracker.policy.forbid_on_item") or []
    return [str(name) for name in stated]


def _branch_prefixes() -> list[str]:
    prefixes = _configuration().get("work_item.type_branch_prefix") or {}
    if isinstance(prefixes, dict):
        return [str(value) for value in prefixes.values() if str(value).strip()]
    return []


def forbidden(text: str, classes: list[str], prefixes: list[str]) -> list[str]:
    """Every barred class the text carries, named and ⛔ never quoted in full.

    One finding per class rather than one per span: what a role has to act on is
    *which* class reached the text, and a refusal that quoted each span would
    publish the credential it refused -- § 14's rule, which is also why the
    credentials class reads that module's own grammar rather than a second one.

    ⛔ A class this module has no form for comes back as a finding too. A policy
    that cannot be answered is not a policy that was observed, and the write is
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
                match = _branch_name_form(prefixes).search(text)
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


def _hold_to_policy(where: str, **texts: str) -> None:
    """Refuse a write whose text carries something the project bars from a card.

    ⛔ Before any call, so the refusal is a write that did not happen rather than
    one to undo. ⚠️ Keyed on the statement that bars it: this is the project
    saying what may reach an item, so the refusal sends a reader to
    `policy.forbid_on_item` and not to a capability that is working.
    """
    classes = policy_classes()
    if not classes:
        return
    prefixes = _branch_prefixes()
    findings = []
    for name, text in texts.items():
        if not text:
            continue
        for finding in forbidden(str(text), classes, prefixes):
            findings.append(f"{name}: {finding}")
    if findings:
        raise ConfigError(
            "tracker.policy.forbid_on_item",
            f"bars {', '.join(f'`{name}`' for name in classes)} from reaching a "
            f"card here, and the text `{where}` was about to write carries: "
            f"{'; '.join(findings)}. ⛔ The write does not happen and no span is "
            "quoted. Where the fact is needed and this surface may not hold it, "
            "it goes in the run report instead (§ 3).",
        )


# --- reading ----------------------------------------------------------------


def _list_of(card: dict, board: dict) -> dict | None:
    for nodes in board["lists"].values():
        for node in nodes:
            if node.get("id") == card.get("idList"):
                return node
    return None


def _labels_of(card: dict, board: dict) -> list[dict]:
    by_id = {
        node["id"]: node for nodes in board["labels"].values() for node in nodes
    }
    found = []
    for label in card.get("idLabels") or []:
        node = by_id.get(label)
        # ⚠️ A label the board's own list does not carry is kept with its id and
        # named unresolved rather than dropped. A label read as absent and a
        # label read as a shape nothing resolved are two different facts, and the
        # second silently became the first while this was a plain lookup.
        found.append(
            {"id": label, "name": node.get("name"), "color": node.get("color")}
            if node
            else {"id": label, "name": None, "unresolved": True}
        )
    return found


def _members_of(card: dict, board: dict) -> list[dict]:
    found = []
    for member in card.get("idMembers") or []:
        node = board["members"].get(member)
        found.append(
            {"id": member, "username": node.get("username"), "name": node.get("fullName")}
            if node
            else {"id": member, "username": None, "unresolved": True}
        )
    return found


def _shaped(card: dict, board: dict, *, checklists: list | None = None) -> dict:
    """One card, in the shape a role carries onward.

    ⚠️ `status` is the **list**, which is § 4.2's vocabulary here, and `state` is
    whether the card is archived, which is the host's own. The two are reported
    apart because they are two facts: a card in the project's terminal list is
    not archived, and an archived card is still in whichever list it was in.

    ⛔ **A field that was not read is left out rather than carried as `None`**,
    which is § 3's rule about an absent capability applied to a field of an
    answer: an unread description is never a card with no description, and an
    unread checklist is never an empty one. The index this board is searched
    through does not ask for a description -- one read per card for every card on
    the board, to match on titles -- so a search entry carries no `body` **key**,
    and a role that needs one reads the card. ⚠️ The first draft answered `None`
    for both, which is the shape a reader cannot tell from a card that has
    neither.
    """
    in_list = _list_of(card, board)
    shaped = {
        "number": card.get("idShort"),
        "id": card.get("id"),
        "title": card.get("name"),
        "status": in_list.get("name") if in_list else None,
        "list": {"id": in_list["id"], "name": in_list.get("name")} if in_list else None,
        "state": ARCHIVED if card.get("closed") else OPEN,
        "url": card.get("url") or card.get("shortUrl"),
        "labels": _labels_of(card, board),
        "assignees": _members_of(card, board),
        "due": card.get("due"),
        "due_complete": card.get("dueComplete"),
    }
    if "desc" in card:
        shaped["body"] = card["desc"]
    if checklists is not None:
        shaped["checklists"] = checklists
    return shaped


def read_item(number: int) -> dict:
    """The item's own facts, and its checklists in a call of its own.

    ⚠️ **Two calls, and the second one is deliberate.** This tracker will nest a
    card's checklists into the card read, and that nested collection carries a
    bound the answer does not say it hit -- so a card past it answers short and
    reads as a card with fewer check items than it has. The survey recorded a
    separate read for this tracker; the bound is why it stays one.

    ⛔ **No pull-request guard, and that is by construction.** Nothing but a card
    is numbered in this sequence, so there is no shape in which a pull request
    can arrive dressed as an item -- which is the opposite of the two
    implementations beside this one and is why neither's guard is copied here.
    """
    board = _board()
    index = _card_for(number)
    card = _call(
        "GET",
        f"/cards/{index['id']}",
        fields="id,idShort,name,desc,closed,idList,idLabels,idMembers,url,shortUrl,due,dueComplete",
    )
    return _shaped(card, board, checklists=_checklists(index["id"]))


def item_number(item: dict | int) -> int:
    """The identifier the branch name and the pull request carry.

    ⚠️ Makes **no host call**, so an `int` is returned as given.

    ⛔ **Two arms, in this order, and both are measured.** The reference
    documents `idShort` on a card, so it is read where the answer carries one; a
    real interface over this tracker answers a card with no short-id field at all
    -- which is the survey's own row -- and a `fields=` narrowed read is the same
    shape, so the URL is parsed where it does not. ⚠️ The URL's number is the
    digits that **open** the last path segment: the slug after them is
    percent-encoded wherever the title is not ASCII, and a split on the dash
    would take a title's own digits on an answer whose slug begins with a year.
    """
    if isinstance(item, int):
        return item
    short = item.get("idShort")
    if isinstance(short, int):
        return short
    if isinstance(short, str) and short.isdigit():
        return int(short)
    for key in ("url", "shortUrl"):
        found = CARD_NUMBER_IN_URL.search(str(item.get(key) or ""))
        if found:
            return int(found.group("number"))
    raise ConfigError(
        "tracker.operations.item_number",
        "was handed a card carrying neither a short id nor a URL with one in it, "
        "so the identifier a branch name and a pull request carry cannot be read "
        "from it. A role with neither stops rather than inventing one (§ 3).",
    )


def _checklists(card_id: str) -> list[dict]:
    """A card's checklists and their items, in the shape a role reads them."""
    answer = _call(
        "GET",
        f"/cards/{card_id}/checklists",
        fields="id,name,pos",
        checkItems="all",
        checkItem_fields="name,state,pos",
    )
    return [
        {
            "id": checklist.get("id"),
            "name": checklist.get("name"),
            "items": [
                {
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "checked": item.get("state") == "complete",
                }
                for item in checklist.get("checkItems") or []
            ],
        }
        for checklist in answer
    ]


def checklist_read(number: int) -> dict:
    """The item's check items, and which of them are ticked.

    Present here, and ⛔ **this is the first implementation where it is**: both
    modules beside this one leave it absent because an issue has no check-item
    object, so until now the stated fallback -- the role has no answer and says
    so -- was the only behaviour anything had.
    """
    card = _card_for(number)
    checklists = _checklists(card["id"])
    return {
        "number": item_number(card),
        "checklists": checklists,
        "items": [item for checklist in checklists for item in checklist["items"]],
    }


# --- searching the board -----------------------------------------------------

# What a query may filter on besides the terms and the labels. ⛔ A stated set
# rather than every key of the answer: a name outside it is refused, because a
# field query this tracker cannot answer must not come back as a card that does
# not match. ⚠️ Anything else on this tracker is a custom field, which needs a
# power-up and whose read shape is unmeasured here.
QUERYABLE = ("status", "state", "title")


def matches(entry: dict, words: list[str], labels: list[str], fields: dict) -> bool:
    """Whether one card answers the query.

    ⚠️ **Every term is a substring of the title, in any order and whatever the
    case** -- so `number 42` matches *item number 142* as well as *item number
    42*. That direction is deliberate: this is the duplicate check, and the
    failure that costs something is a near-duplicate the search did not surface,
    not a candidate the role reads and sets aside.

    ⛔ Matched on the title and never the body. A body is one read per card, and
    the layer that judges a candidate does that read itself.
    """
    title = (entry.get("title") or "").lower()
    if any(word not in title for word in words):
        return False
    carried = {label.get("name") for label in entry.get("labels") or []}
    if any(label not in carried for label in labels):
        return False
    for name, value in (fields or {}).items():
        if entry.get(name) != value:
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
    tracker means the list a card is in, whether it is archived, and its title.

    ⛔ **No state argument, by construction.** § 3 states the operation across
    every state the tracker holds: the index is read with `filter=all`, so the
    archived cards are in it, and nothing filters by list unless the caller asks
    for that column by name.

    ⛔ **The board is read whole or refused**, by the ceiling the index read
    holds -- so `at_limit` here is exact and says the **matches** were cut by the
    bound, never that the read was.

    ⛔ **An unknown label or an unknown field name is refused, never answered
    with an empty list.** Both come back empty from a board that holds the thing
    and from a board that does not, and this is the one search the filing role
    performs: the two readings are a duplicate check that found nothing and a
    duplicate check that never ran. ⚠️ A label is resolved against the board
    already read, which costs nothing, and ⚠️ an **ambiguous** label name is
    refused as well: two labels with one name would match two different sets.
    """
    board = _board()
    for name in fields or {}:
        if name not in QUERYABLE:
            raise ConfigError(
                f"tracker.operations.search_items.{name}",
                f"is not a field this tracker answers a query on. Queryable here "
                f"are: {', '.join(QUERYABLE)}. Anything else on a card is a custom "
                "field, which needs a power-up on the board and whose shape is "
                "unmeasured here -- so a query on it is refused rather than "
                "answered with the cards that do not match.",
            )
    for name in labels or []:
        _label_named(name, key="tracker.operations.search_items")
    entries = [_shaped(card, board) for card in board["cards"]]
    words = [word for word in (terms or "").lower().split() if word]
    matched = [
        entry for entry in entries if matches(entry, words, list(labels or []), fields or {})
    ]
    return {
        "terms": terms or "",
        "labels": list(labels or []),
        "fields": dict(fields or {}),
        "matched_on": "the title, the labels, the list and whether the card is archived",
        "scanned": len(entries),
        "limit": limit,
        "at_limit": len(matched) > limit,
        "items": matched[:limit],
    }


# --- writing -----------------------------------------------------------------


def _initial_list() -> dict:
    """The list a filing puts a card in, from the role § 4.2 maps to `initial`.

    ⛔ **Resolved rather than chosen, and required here alone.** A card cannot
    exist with no list, so unlike the two implementations beside this one there
    is no moment at which a filing leaves the state empty for the role's own
    advance to set. ⚠️ So a project that maps no `initial` role is refused with
    `statuses` named: § 4.2 lets a project map a subset, and this is the one
    tracker where that subset has to contain this member.
    """
    statuses = [
        status
        for status in (_configuration().get("statuses") or [])
        if status.get("role") == "initial"
    ]
    if not statuses:
        raise ConfigError(
            "statuses",
            "maps no `initial` role, so a filing here has no list to create the "
            "card in. A card cannot exist with no list on this tracker, which is "
            "why this role is required here and optional on the trackers whose "
            "items can sit with an empty status.",
        )
    if len(statuses) > 1:
        words = ", ".join(f"`{status.get('name')}`" for status in statuses)
        raise ConfigError(
            "statuses",
            f"maps the `initial` role to more than one status ({words}). § 4.2 maps "
            "a role to at most one status, and two lists leave a filing undefined.",
        )
    return _list_named(str(statuses[0].get("name")))


def create_item(title: str, body: str, labels: list[str] | None = None) -> dict:
    """A new card, from the body the filing role wrote.

    ⚠️ **The labels go on at creation, and that is the reference's answer rather
    than a measured one.** The survey's row for this tracker records a create
    followed by one attach per label, and the interface that row was taken from
    does exactly that -- but the card endpoint documents `idLabels` on the
    create, so one call is what this sends. ⛔ The read-back below is what makes
    the difference visible either way: a card that came back carrying fewer
    labels than were asked for is a failure naming them rather than a filing that
    looks finished.
    """
    _hold_to_policy("create_item", title=title, body=body)
    in_list = _initial_list()
    label_ids = [
        _label_named(name, key="tracker.operations.create_item")["id"]
        for name in labels or []
    ]
    params = {"idList": in_list["id"], "name": title, "desc": body or ""}
    if label_ids:
        params["idLabels"] = ",".join(label_ids)
    created = _call("POST", "/cards", **params)
    number = item_number(created)
    item = read_item(number)
    carried = {label.get("name") for label in item["labels"]}
    if set(labels or []) - carried:
        missing = ", ".join(sorted(set(labels or []) - carried))
        raise HostUnavailable(
            f"card {number} was created and came back carrying {len(carried)} of "
            f"the {len(set(labels or []))} label(s) asked for -- {missing} did not "
            "land. The card exists, so this is reported rather than retried: a "
            "second create would file the work twice."
        )
    return item


def set_state(number: int, *, status: str) -> dict:
    """Move the card to a list, by name.

    ⚠️ `status` is the **status word the port resolved from the role it was asked
    for** (§ 4.2) -- a role never names it and this adapter never guesses it. A
    word with no list on the board is refused with the key named rather than
    moved to the nearest column.

    ⛔ Idempotent, by reading before writing: a card already in the list is
    returned unwritten, so a role advancing to a role the item already holds
    spends no write.
    """
    in_list = _list_named(str(status))
    card = _card_for(number)
    if card.get("idList") == in_list["id"]:
        # ⛔ The same answer the written path gives, read back rather than
        # shaped from the index. An operation that answered two different
        # shapes depending on whether it wrote would make a role's handling
        # of its result depend on a fact the role did not ask about -- and
        # the index carries no description, so the no-op answer would be
        # missing a field the written one has. ⚠️ Idempotence is about not
        # spending a **write**; a read costs nothing a role has to know.
        return read_item(number)
    _call("PUT", f"/cards/{card['id']}", idList=in_list["id"])
    return read_item(number)


def set_field(number: int, field: str, value) -> dict:
    """A value written onto the card, where a facet states the field.

    The operation § 4.3's estimate and § 4.5's date reach this tracker through.
    ⛔ The card's own fields and nothing else, each shaped by what that field
    holds rather than by what the value is: a date handed to a text field is
    accepted by the host and read back by nobody.

    ⛔ A field another operation owns is refused naming that operation, and
    anything else is refused naming what it would need -- a custom field and the
    power-up behind it, whose write shape is unmeasured here.
    """
    key = f"tracker.fields.{field}"
    if field in OWNED_ELSEWHERE:
        raise ConfigError(
            key,
            f"is written by `{OWNED_ELSEWHERE[field]}` here, not by this "
            "operation. A facet pointing at it is pointing at a value this "
            "procedure writes through a different question.",
        )
    if field not in WRITABLE:
        raise ConfigError(
            key,
            f"is not a field of a card this tracker lets a value be written into. "
            f"Writable here are: {', '.join(sorted(WRITABLE))}. Anything else is a "
            "custom field, which needs a power-up on the board and whose write "
            "shape is unmeasured here -- so the value is refused rather than "
            "written somewhere plausible.",
        )
    kind = WRITABLE[field]
    if kind == DATE:
        if not ISO_DATE.match(str(value)):
            raise ConfigError(
                key,
                f"was handed `{value!r}` for a date field, which is not a date in "
                "`YYYY-MM-DD`. ⚠️ That is § 4.5's own form, and this field is a "
                "date-time: the value is sent as the start of that day in the "
                "host's own zone, which is the one time that is not invented.",
            )
        shaped = f"{value}{START_OF_DAY}"
    elif kind == FLAG:
        if not isinstance(value, bool):
            raise ConfigError(
                key,
                f"was handed `{value!r}` for a flag field, which is not a flag. A "
                "string reads as true whatever it says, which is the one shape "
                "this must not coerce.",
            )
        shaped = "true" if value else "false"
    else:
        shaped = str(value)
        _hold_to_policy("set_field", **{field: shaped})
    card = _card_for(number)
    _call("PUT", f"/cards/{card['id']}", **{field: shaped})
    return read_item(number)


def comment(number: int, body: str) -> dict:
    """A note on the item -- a gate result being the measured case.

    ⚠️ **Present, against the survey's own row for this tracker.** That row
    records no comment action at all, and one copy writes its gate result into
    the description because of it -- but this tracker holds comments as
    first-class actions on a card, measured through a live interface that reads
    them, writes them and names them in a board's own history. So the capability
    is declared and `comment`'s stated fallback is not what happens here.
    """
    _hold_to_policy("comment", body=body)
    card = _card_for(number)
    _call("POST", f"/cards/{card['id']}/actions/comments", text=body)
    return {"number": item_number(card), "url": card.get("url"), "commented": True}


def set_labels(number: int, labels: list[str]) -> dict:
    """Every label set in one call, so there is no partial set to report.

    ⛔ **Set, not add.** The whole array is written, so a card labelled `b` asked
    for `[a]` comes back carrying `a` alone rather than the union a per-label
    attach would leave.

    ⚠️ **The empty set is the one case that cannot be written that way**, and it
    is written explicitly rather than guessed: the host's array parameter has no
    stated form for *no values*, and sending an empty one is as likely to be
    ignored as honoured. So each label the card carries is removed by name, one
    call each, and the answer names the calls made -- a set left partial is
    reported rather than retried silently, which is this operation's own stated
    fallback and the right behaviour for the one arm that degrades to it.
    """
    wanted = {
        name: _label_named(name, key="tracker.operations.set_labels")["id"]
        for name in labels
    }
    card = _card_for(number)
    board = _board()
    carried = {label.get("name") for label in _labels_of(card, board) if label.get("name")}
    if carried == set(wanted):
        # ⛔ The same answer the written path gives, read back rather than
        # shaped from the index. An operation that answered two different
        # shapes depending on whether it wrote would make a role's handling
        # of its result depend on a fact the role did not ask about -- and
        # the index carries no description, so the no-op answer would be
        # missing a field the written one has. ⚠️ Idempotence is about not
        # spending a **write**; a read costs nothing a role has to know.
        return read_item(number)
    if wanted:
        _call("PUT", f"/cards/{card['id']}", idLabels=",".join(sorted(wanted.values())))
        return read_item(number)
    removed = []
    for label in card.get("idLabels") or []:
        _call("DELETE", f"/cards/{card['id']}/idLabels/{label}", parse=False)
        removed.append(label)
    item = read_item(number)
    if item["labels"]:
        raise HostUnavailable(
            f"card {item_number(card)} was asked for no labels, {len(removed)} "
            f"removal(s) were made and it still carries {len(item['labels'])}. The "
            "set is partial and is reported rather than retried, because a retry "
            "cannot tell a removal that failed from one that raced."
        )
    return item


def assign(number: int, who: str = "@me") -> dict:
    """The item assigned to the person the role acts for.

    ⚠️ This says *taken* and nothing more. Where every session authenticates as
    one account it cannot say **which** session holds the item, so a claim does
    not rest on it -- that is § 10's, and `assign`'s own stated fallback says as
    much.

    ⚠️ `@me` is the code host's spelling and this tracker's is `me`, so the one
    value every role passes is translated here rather than at each call site.
    """
    handle = "me" if who in ("@me", "me") else str(who).lstrip("@")
    # ⛔ Held to the same shape the board is, and for the same reason: this goes
    # into a request path. A handle carrying a separator reads a different
    # endpoint, and the member it came back with would be assigned to the card as
    # though it had been asked for.
    found = REDIRECTS_THE_CALL.search(handle)
    if found:
        raise ConfigError(
            "tracker.operations.assign",
            f"was asked to assign `{who}`, which carries `{found.group(0)}` at "
            f"character {found.start()} of the handle. A member is named by their "
            "own handle and this value is put into a request path, so that would "
            "read a different endpoint -- and whatever came back would be "
            "assigned to the card as though it had been asked for.",
        )
    member = _call("GET", f"/members/{handle}", fields="id,username")
    card = _card_for(number)
    if member.get("id") in (card.get("idMembers") or []):
        # ⛔ The same answer the written path gives, read back rather than
        # shaped from the index. An operation that answered two different
        # shapes depending on whether it wrote would make a role's handling
        # of its result depend on a fact the role did not ask about -- and
        # the index carries no description, so the no-op answer would be
        # missing a field the written one has. ⚠️ Idempotence is about not
        # spending a **write**; a read costs nothing a role has to know.
        return read_item(number)
    _call("POST", f"/cards/{card['id']}/idMembers", value=member["id"])
    return read_item(number)


def _named(checklists: list[dict]) -> str:
    """The checklists a card carries, by name, for a refusal that lists them.

    ⚠️ An unnamed checklist is shown as the empty string rather than skipped: a
    card can carry one, and a refusal listing fewer than the card has reads as a
    refusal about a different card.
    """
    return ", ".join(repr(one["name"] or "") for one in checklists) or "none"


def _checklist_for(card_id: str, named: str | None, *, create: bool) -> dict:
    """The checklist a check item belongs to, by name or by there being one.

    ⛔ Never guessed by position. A card with several checklists and no name
    given has no answer, and putting the item in the first one would file it
    somewhere nobody asked for -- so that is a refusal naming them.
    """
    checklists = _checklists(card_id)
    if named is not None:
        matching = [one for one in checklists if one["name"] == named]
        if len(matching) > 1:
            raise ConfigError(
                "tracker.operations.checklist_write",
                f"names the checklist `{named}`, which card `{card_id}` has "
                f"{len(matching)} of. This tracker holds no uniqueness for the "
                "name, so there is no reading of which was meant.",
            )
        if matching:
            return matching[0]
        if not create:
            raise ConfigError(
                "tracker.operations.checklist_item_delete",
                f"names the checklist `{named}`, which this card does not have. "
                f"Its checklists are: {_named(checklists)}.",
            )
        _hold_to_policy("checklist_write", checklist=named)
        created = _call("POST", "/checklists", idCard=card_id, name=named)
        return {"id": created["id"], "name": created.get("name"), "items": []}
    if len(checklists) == 1:
        return checklists[0]
    if not checklists:
        raise ConfigError(
            "tracker.operations.checklist_write",
            "was given no checklist to put the item in and the card has none. A "
            "check item needs a checklist to live on, so name one -- it is created "
            "where the card does not have it.",
        )
    raise ConfigError(
        "tracker.operations.checklist_write",
        f"was given no checklist to put the item in and the card has "
        f"{len(checklists)}: {_named(checklists)}. "
        "Name the one it belongs to; the first on the card is not an answer.",
    )


def _item_named(checklists: list[dict], name: str, within: str | None) -> tuple[dict, dict] | None:
    for checklist in checklists:
        if within is not None and checklist["name"] != within:
            continue
        for item in checklist["items"]:
            if item["name"] == name:
                return checklist, item
    return None


def checklist_write(
    number: int, item: str, *, checked: bool | None = None, checklist: str | None = None
) -> dict:
    """A check item added, or ticked.

    Both halves of § 3's row, decided by whether the card already carries an item
    of this name: it is ticked where it does and added where it does not. ⚠️ An
    item that is already there with no `checked` asked for is returned unwritten
    rather than added a second time -- two check items with one name is what a
    role would otherwise leave behind.
    """
    _hold_to_policy("checklist_write", item=item)
    card = _card_for(number)
    found = _item_named(_checklists(card["id"]), item, checklist)
    if found:
        holding, existing = found
        if checked is None or existing["checked"] == bool(checked):
            return {"number": item_number(card), "item": existing, "written": False}
        _call(
            "PUT",
            f"/cards/{card['id']}/checkItem/{existing['id']}",
            state="complete" if checked else "incomplete",
            parse=False,
        )
        return {
            "number": item_number(card),
            "item": dict(existing, checked=bool(checked)),
            "checklist": holding["name"],
            "written": True,
        }
    holding = _checklist_for(card["id"], checklist, create=True)
    params = {"name": item}
    if checked is not None:
        params["checked"] = "true" if checked else "false"
    created = _call("POST", f"/checklists/{holding['id']}/checkItems", **params)
    return {
        "number": item_number(card),
        "item": {
            "id": created.get("id"),
            "name": created.get("name"),
            "checked": created.get("state") == "complete",
        },
        "checklist": holding["name"],
        "written": True,
    }


def checklist_item_delete(number: int, item: str, *, checklist: str | None = None) -> dict:
    """A check item removed.

    ⚠️ **The one operation here the reference and the survey disagree about.**
    The survey's row records this as impossible on this tracker -- reword and tick
    instead -- and the interface it was taken from has no delete at all, while the
    checklist endpoint documents one. ⛔ It is implemented because the adapter
    speaks the endpoint rather than that interface, and the direction of the two
    mistakes decides it: an operation declared absent that exists leaves a role
    rewording for ever with nothing reporting it, while one declared present that
    does not comes back as a failure naming the call.
    """
    card = _card_for(number)
    found = _item_named(_checklists(card["id"]), item, checklist)
    if not found:
        raise ConfigError(
            "tracker.operations.checklist_item_delete",
            f"was asked to remove the check item `{item}`, which card "
            f"{item_number(card)} does not carry. An item that is not there is not "
            "an item this removed, and reporting it as removed would say the "
            "checklist holds something it never did.",
        )
    holding, existing = found
    _call(
        "DELETE",
        f"/checklists/{holding['id']}/checkItems/{existing['id']}",
        parse=False,
    )
    return {
        "number": item_number(card),
        "removed": existing["name"],
        "checklist": holding["name"],
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
    "checklist_read": checklist_read,
    "checklist_write": checklist_write,
    "checklist_item_delete": checklist_item_delete,
    # ⛔ The three operations this tracker has nothing to implement against are
    # named once, below, and read from there by the suite.
})

# The three the module docstring argues are absent because the tracker has
# nothing to implement them against: there is no relation between two cards, no
# reference that closes one when a branch lands, and so no automation to confirm
# off a merge. ⛔ Written once, here, and read by the suite rather than restated
# in it: a fourth absence would otherwise be an operation nobody noticed going
# missing.
DELIBERATELY_ABSENT = ("link_dependency", "link_for_close", "advance_on_merge")


def self_test() -> int:
    """This implementation's own suite, which lives in the module beside it.

    ⛔ **A module of its own**, for the reason the board implementation records:
    a file this size reaches the code host with no patch at all, and the gate
    that holds every added line to the deferral rule then refuses the change.

    ⚠️ The suite's module name opens with `_`, which is what keeps discovery from
    reading it as an implementation that names no kind.
    """
    from adapters import _trello_suite as suite

    return suite.self_test()


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Cards on a board behind the tracker port: its own suite.",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="hold this implementation to the shapes it was written against",
    )
    args = parser.parse_args(argv)
    if not args.self_test:
        parser.print_help()
        return 0
    print(f"Holding the `{KIND}` implementation to the shapes it was written against:")
    return self_test()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
