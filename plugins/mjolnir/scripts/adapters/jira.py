#!/usr/bin/env python3
"""Issues behind the port: the identifier is a key, and a state is a transition.

The fourth implementation, and the one whose tracker is a hosted service with the
code on another host entirely -- which is the case that proves tracker and host
are two axes rather than two names for one. Everything the two code-host
implementations get for free, this one has to ask for: the identifier is not a
number, the state is not a field anybody writes, and the merge the item is
supposed to move off happens somewhere this tracker cannot see.

What it implements, and what it deliberately does not:

  * **Not every operation § 3 states.** ⛔ No count of them is carried -- the
    list is closed and stated once, in § 3, and a number here would be wrong the
    next time it grows. They are named once in `DELIBERATELY_ABSENT` below: this
    tracker has no check-item object of its own, so the three checklist
    operations are prose in the description, which is precisely what their
    stated fallbacks already say to do; and ⛔ **no closing keyword
    exists**, so `link_for_close` has nothing to compose. A text that closed an
    item on merge would be this adapter inventing a mechanism the tracker does
    not have, and the stated fallback -- the item moves separately -- is the
    truth here rather than a degradation.
  * **The identifier is the project's key and a number, not a number.** `read_item`
    takes it, every write takes it, and `item_number` answers it. ⚠️ Which makes
    the one guard this tracker needs a **project** guard rather than a
    pull-request guard: a key is unique across the whole site, so a key from
    another project resolves and answers perfectly, and an operation handed one
    would read and write someone else's backlog. `tracker.project_key` is what
    that is held to, and every operation that takes a key resolves it through
    `read_item` first so the one guard covers all of them.
  * **A state is reached by a transition, and the transition is found by the
    status it leads to.** ⛔ Not by its own name: measured, a transition's `name`
    and its `to.name` are separate fields, and § 4.2's vocabulary is the status
    words -- so matching the transition's name would be matching the wrong half
    on every workflow whose verbs differ from its states. ⚠️ And what is
    reachable depends on the issue's **type**: measured on a live site, one type
    offered three statuses and another nine, out of nine the project defines. So
    a status word that exists in the project and is not reachable from where the
    item stands is refused with both readings stated, never moved to the nearest.
  * **`advance_on_merge` confirms, and what it can confirm is the tracker's half
    alone.** The merge is on the code host; this tracker sees a status change and
    who made it. So the operation answers whether something **other than this
    credential** moved the item, and says so in those words rather than claiming
    an automation fired. ⛔ Who that something was is not reported as automation
    or person: a script running under somebody's token is indistinguishable from
    the person, which is the published caution and not a guess.
  * **The dependency call's inward and outward sense is the opposite of the link
    type's own wording**, which is this tracker's sharpest trap. The type reads
    `name: Blocks`, `inward: is blocked by`, `outward: blocks`, and the call's
    `inwardIssue` is the issue that **blocks**. Read the wording and you file the
    dependency on the wrong item, and it reads as success. ⛔ So the direction is
    asserted by a round trip in the suite rather than by reading the call.
  * **`read_blockers` makes no call of its own.** The links arrive with the item,
    so the read half of that dependency is `read_item`'s answer narrowed to one
    side of one link type -- which is also why the project guard and the
    direction rule above hold here without being restated. ⚠️ Each blocker comes
    back with the project's own status word *and* the tracker's category behind
    it, and no verdict: which bar a blocker is held to depends on what it
    produced, and that is the readiness list's question rather than this
    module's.
  * **A body is a document, not a string.** This tracker's own interface takes
    rich text as a structured document, so `create_item`, `comment` and a write
    to a text field all go through one narrow renderer and one narrow reader.
    ⚠️ **Narrow, and stated:** headings, paragraphs, bullet and ordered lists and
    fenced code survive a round trip; a table, a nested list and every inline
    mark do not, and arrive as the text they were written as. A fuller renderer
    is a markdown parser, and inventing one here would be the implementation
    deciding what a project's template means.
  * **Every search is bounded, and it is the host that requires it.** Measured:
    a query with no restriction is refused outright -- *Unbounded JQL queries are
    not allowed here* -- so the project restriction is not a convenience but the
    only shape the host accepts, and it is also exactly the project guard above.
    ⚠️ Which is why the state qualifier the plain-issues implementation has to
    refuse is unreachable here: every term a caller gives is quoted into the
    query, and the quote guard is what makes that true.

Every call goes over HTTP with an account and a token, read from the environment
and ⛔ **never written into a message**: the credential travels in a header here
rather than in the query, so a message that quoted the call would not carry it --
but the account is an address and a message naming it would publish that, which
§ 14 bars just as firmly. ⛔ **Through one named seam**, `TRANSPORT`, which
answers with the status rather than raising, so a body, the host's own `404` and a
call that never reached the host are all three available at every call site.

The configuration arrives from the port through `bind`; nothing here resolves a
project for itself.

What this module has **not** been run against is a live site **through this
interface**: the two variables below are what a run needs and this repository's
own shell holds neither. Every shape below is read from the tracker's published
reference or measured through an interface that is not this one; which is which,
and the answers that are the reference's alone, are recorded in
`docs/configuration-surface.md`.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request

# The package's parent, appended rather than prepended: this module is imported
# as `adapters.jira`, so the contract beside it is not otherwise on the path, and
# putting it first would shadow a standard-library name.
_SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SCRIPTS not in sys.path:
    sys.path.append(_SCRIPTS)

import port  # noqa: E402
from adapters._policy import forbidden  # noqa: E402
from adapters import _search as coverage  # noqa: E402
from adapters import _comments  # noqa: E402
from port import ConfigError, HostUnavailable  # noqa: E402

KIND = "jira"

# Where this tracker's own interface lives under the site. ⛔ The version is part
# of the address rather than a setting: the document shape a body is written in
# below is this version's, and a project pointed at the older one would have its
# bodies accepted as literal text with no error anywhere.
API = "/rest/api/3"

# The two variables that address the site. ⛔ A pair rather than one token,
# because this tracker authenticates as a **person**: the credential and the
# account it belongs to are separate facts and one without the other
# authenticates nothing. ⚠️ Which is also the reason a project on this tracker
# tends to write `writer: never` throughout -- the same pair that makes a write
# possible is what makes it read as that person speaking.
ACCOUNT_VARIABLE = "JIRA_ACCOUNT"
TOKEN_VARIABLE = "JIRA_API_TOKEN"

# How long one call may take. Past this the call did not happen, which is a
# failure naming the request rather than an absence.
TIMEOUT = 30

# What the host answers when the thing asked for is not there, when the pair is
# wrong, and when this credential's budget is spent. ⛔ Kept apart: only the
# first says anything about the item.
NOT_FOUND = 404
UNAUTHORISED = (401, 403)
RATE_LIMITED = 429

# The status this module uses for a call that never reached the host at all -- a
# name that does not resolve, a socket that timed out. ⚠️ Not folded into the
# `>= 400` arm: a call the host refused and a call the host never saw are two
# different facts.
UNREACHED = 0

# An item's identifier on this tracker: the project's key, then its number.
# ⛔ Held to this shape before any call, because the value is interpolated into a
# request **path** and because the project half is the guard below. ⚠️ The
# project key is upper-case letters and digits by this tracker's own rule, and
# the number is the only part that counts up.
ITEM_KEY = re.compile(r"^(?P<project>[A-Z][A-Z0-9_]{0,9})-(?P<number>[1-9]\d*)$")

# What a label may not carry here. ⛔ Refused before the write: measured through
# an interface over this tracker, a label is one word and a space is not a
# separator the host splits on -- it is a value the host rejects, and the
# rejection names the whole field rather than the label that caused it.
SPACE = re.compile(r"\s")

# What a value put into a JQL string may not carry. ⛔ A forbidden set rather
# than an escape: a quote or a backslash in a term ends the quoted operand and
# the rest of the term becomes query, which the host then answers -- so the
# failure is a search that ran as something else rather than one that refused.
# ⚠️ Escaping would work and is not done, because the refusal is the narrower
# claim: a term carrying these characters is a caller mistake either way, and a
# duplicate check that quietly searched for something else is the one outcome
# this operation must not have.
BREAKS_THE_QUERY = re.compile(r"[\"\\\n\r]")

# What the project's own date facet looks like (§ 4.5), and what this tracker's
# date field takes -- the same form, which is why a date needs no shaping here
# and a date-time field would.
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# A duration this tracker parses. ⛔ A bare number is **refused** rather than
# sent: the host reads one as minutes under its default configuration and as
# something else under another, so a project's `4` would be four minutes on one
# site and four hours on the next -- and § 4.3's unit is the project's
# statement, not the site's.
DURATION = re.compile(r"^\d+(?:\.\d+)?[wdhm](?:\s+\d+(?:\.\d+)?[wdhm])*$")

# How many nodes a collection read here takes at a time, and ⛔ the cursor is
# **followed** rather than the first page read: the published interface pages
# every search, and a first page that fills reads as a complete answer -- which
# is the measured defect the board implementation pays a cursor-follower to
# avoid. ⚠️ A ceiling on the follow as well, because a runaway cursor is a loop
# this module cannot be interrupted out of.
PAGE = 100
PAGES_AT_MOST = 50

# What a search may filter on besides its terms and its labels. ⛔ A stated set
# rather than every field the site has: a field query this module cannot shape is
# refused, because the alternative is answering it with the items that do not
# match. ⚠️ Each of these is a JQL field name and a key of the shape `read_item`
# answers in, which is what lets a caller filter on what it just read.
QUERYABLE = ("status", "type", "priority")

# The texts a term is matched in, by § 3's names, and the clause this host matches
# each with. ⛔ Both natively: the host's text clause searches a field's words, so
# a body is matched by the query rather than by reading every description back.
# ⚠️ Before `tracker.search.texts` existed the summary alone was matched, which is
# what a project stating none keeps.
TEXT_CLAUSES = {"title": "summary", "body": "description"}
SEARCHED_BEFORE = ("title",)

# A clause name this host takes unquoted: a plain word, or a custom field's
# `cf[N]`. ⚠️ Anything else -- a display name with a space in it -- is quoted.
BARE_CLAUSE = re.compile(r"^(?:[A-Za-z_][A-Za-z0-9_]*|cf\[\d+\])$")

# What the operations above own, by the **id** this tracker gives the field.
# ⛔ Refused with that operation named, rather than falling through to the
# refusal below it: a facet pointing here is pointing at a value this procedure
# writes through a different question, and a refusal saying *no such field* would
# send somebody looking for a field that is right there.
#
# ⛔ Keyed on the id and not on the name the caller used, which is why the check
# happens **after** the field is resolved: a field's display name is whatever the
# site calls it -- a renamed one, or one in another language -- and a guard
# matching the caller's spelling would let the same field through under its
# local name.
OWNED_ELSEWHERE = {
    "status": "set_state",
    "labels": "set_labels",
    "assignee": "assign",
    "issuelinks": "link_dependency",
    "comment": "comment",
}

# The field types this module has a shape for, and ⛔ nothing else is written.
# A type absent from here is refused naming what it would need, rather than sent
# as a string the host accepts and nobody reads back: measured on the tracker
# beside this one, a date handed to a text field is stored and silently wrong.
TEXT, RICH, DATE, NUMBER, DURATION_FIELD, NAMED, OPTION, USER = (
    "text", "rich", "date", "number", "duration", "named", "option", "user",
)

# `schema.type` as this tracker's own field catalogue reports it, mapped to the
# shape a write takes. ⚠️ Read from the catalogue rather than from a list of
# field names, because every custom field's id is site-specific -- which is the
# whole reason a field is addressed by **name** here and resolved per site.
SHAPES = {
    "string": TEXT,
    "summary": TEXT,
    "description": RICH,
    "date": DATE,
    "number": NUMBER,
    "timetracking": DURATION_FIELD,
    "priority": NAMED,
    "issuetype": NAMED,
    "version": NAMED,
    # A resolution, written by the name the site gives it -- the field a move to a
    # finished status was found to need, stated in § 3's `transitions.fields`.
    "resolution": NAMED,
    "option": OPTION,
}

# What the catalogue calls a field holding several values, and the shape each
# **member** takes by the element type it states beside that. ⛔ A map of its own
# rather than the one above: a member and a scalar of one type are two shapes to
# establish, and an element absent from here is refused by name -- a sprint's is
# the ordinary case, the reference stating no shape for one.
LIST = "array"
ELEMENTS = {
    "component": NAMED,
    "version": NAMED,
    "option": OPTION,
    "user": USER,
    "string": TEXT,
}

# The member of the structure that names the value, per shape that has one, as a
# write takes it and as a read answers it. ⚠️ A user's two spellings differ: the
# reference writes one by `id` and the host answers `accountId`, one value.
IDENTIFIED_BY = {NAMED: "name", OPTION: "value", USER: "id"}
ANSWERED_AS = ("name", "value", "accountId")

# The parts a filing states through its own argument or its address, by id, which
# no extra field may write over.
FILED_ALREADY = ("project", "issuetype", "summary", "description")

# The fields whose `schema.type` is a plain string and whose content is a
# document. ⛔ Keyed by the field's **id**, for the reason the mapping above is:
# the catalogue reports this one and the summary as the same type, and only one
# of them is text.
RICH_FIELDS = ("description",)

# The link type a dependency is recorded as, and the two senses of it. ⛔ The
# name is what the call takes and the two descriptions are what the **reader**
# sees, and they run opposite ways: `INWARD_READS` is what the issue holding the
# link says about the other one. Written here, once, because getting it backwards
# files the dependency on the wrong item and reads as success.
BLOCKS = "Blocks"
INWARD_READS = "is blocked by"
OUTWARD_READS = "blocks"

# --- the configuration, handed down -----------------------------------------
#
# ⛔ Never resolved here and never from the working directory, for § 3's reason:
# a process serving more than one project must address each one's own site.
_bound = None

# What the site itself answers about its own shape, keyed by the site address.
# Keyed rather than process-wide, for the reason the modules beside this one
# record: two projects in one process may be on two sites. ⚠️ The field catalogue
# and the account this credential is are both per site and neither changes within
# a run, so each is read once; a **field** added seconds ago is the one thing
# that would be missed, and a name that does not resolve re-reads before refusing.
_sites: dict[str, dict] = {}


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
            "tracker.adapters.jira",
            "was asked for an operation before the port bound a configuration to "
            "it. Every operation is reached through `Port.invoke`, which binds "
            "first; a direct call bypasses the one place the project is stated.",
        )
    return _bound


def _site() -> str:
    """The site every call here addresses, with no trailing separator.

    The surface marks `tracker.site` `# required_when: tracker.kind = jira`, so a
    configuration that reached here states one. What is refused is a value that
    cannot address a site: this tracker's project key says **which project** and
    nothing at all about which site, so the two keys answer different halves of
    one address and neither is derivable from the other.
    """
    site = str(_configuration().get("tracker.site") or "").strip()
    if not site:
        raise ConfigError(
            "tracker.site",
            "states no site, so nothing here can be addressed. A project key "
            "names a project within a site and says nothing about which site, so "
            "this key is what makes a key mean anything at all.",
        )
    parsed = urllib.parse.urlsplit(site)
    if parsed.scheme not in ("https", "http") or not parsed.netloc:
        raise ConfigError(
            "tracker.site",
            f"is `{site}`, which is not a site address. It is the scheme and host "
            "this tracker answers on -- the form a browser is pointed at, with no "
            "path after it.",
        )
    if "@" in parsed.netloc:
        raise ConfigError(
            "tracker.site",
            "carries a credential in its host part. The account and the token are "
            f"read from `{ACCOUNT_VARIABLE}` and `{TOKEN_VARIABLE}`, and a value "
            "here would put one in a configuration file and in every message that "
            "quotes a call (§ 14).",
        )
    if parsed.path.strip("/") or parsed.query or parsed.fragment:
        raise ConfigError(
            "tracker.site",
            f"is `{site}`, which carries a path. This module appends the "
            f"interface's own path (`{API}`) to the site, so anything here would "
            "address an endpoint other than the one a call means -- and the host "
            "would answer **that** endpoint rather than refuse.",
        )
    return f"{parsed.scheme}://{parsed.netloc}"


def _project_key() -> str:
    """The project every key here has to belong to.

    ⛔ The guard, not a convenience. A key is unique across the whole site, so a
    key from another project resolves and answers; without this an operation
    handed one would read, comment on and transition someone else's backlog, and
    report having worked.
    """
    key = str(_configuration().get("tracker.project_key") or "").strip()
    if not key:
        raise ConfigError(
            "tracker.project_key",
            "states no project, so no key can be held to belonging to this one. "
            "Every key on this tracker resolves site-wide, which is what makes "
            "this the guard rather than a label.",
        )
    return key


# --- the host, through one named seam ---------------------------------------


def _credentials() -> str:
    """The authorisation header value, from the environment.

    ⛔ A failure rather than an absence. § 3 holds a credential that is wrong
    apart from a capability that is missing, and a role must not take a stated
    fallback because a variable was unset: the fallback answers a tracker that
    **cannot**, never one this module could not reach.
    """
    account = os.environ.get(ACCOUNT_VARIABLE)
    token = os.environ.get(TOKEN_VARIABLE)
    missing = [
        name
        for name, value in ((ACCOUNT_VARIABLE, account), (TOKEN_VARIABLE, token))
        if not value
    ]
    if missing:
        raise HostUnavailable(
            f"the shell holds no {' and no '.join(missing)}, so no call to this "
            "tracker could be made. The pair addresses it together -- this tracker "
            "authenticates as a person, so the token is that person's and means "
            "nothing without the account it belongs to -- and § 14 states that the "
            "project names them in `environment.inherits` rather than carrying a "
            "value."
        )
    pair = f"{account}:{token}".encode("utf-8")
    return "Basic " + base64.b64encode(pair).decode("ascii")


def _shown(method: str, path: str, params: dict | None = None) -> str:
    """One call, as a person could re-run it, carrying no credential.

    ⛔ Every failure below quotes the call, and on this tracker the pair travels
    in a header rather than in the query -- so what this has to keep out is not
    the token but the **account**, which is an address and which § 14 bars from a
    surface outside the project just as firmly. Neither reaches a message,
    because neither is in the string this builds.
    """
    query = urllib.parse.urlencode(params or {}, doseq=True)
    return f"{method} {API}{path}" + (f"?{query}" if query else "")


def _urlopen_request(
    method: str,
    path: str,
    params: dict | None = None,
    body: dict | None = None,
    *,
    where: str = "",
    auth: str = "",
) -> tuple[int, str]:
    """One HTTP call, answering with its status rather than raising on one.

    ⛔ The status is **in the answer**, which is what lets a caller tell a body,
    the host's own `404` and a call that never reached the host apart without a
    second path that bypasses the first.

    ⛔ **The address and the credential are handed in, not resolved here.** They
    were resolved here in the first draft, and the measured consequence is the
    reason they are not: this function is a *seam*, so every guard inside it is a
    guard the suite -- and any other transport -- walks straight past. A site
    carrying a path and a shell holding no token both read as *the call went out
    and the host answered* in that arrangement. ⚠️ The guards are in `_call`
    above the seam, which is where the implementation beside this one puts them
    for the same reason.
    """
    query = urllib.parse.urlencode(params or {}, doseq=True)
    url = f"{where}{API}{path}" + (f"?{query}" if query else "")
    data = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(url, data=data, method=method)
    request.add_header("Authorization", auth)
    request.add_header("Accept", "application/json")
    if data is not None:
        request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as answer:
            return answer.status, answer.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as error:
        # The host answered, and its answer is the status. The body is read
        # because this tracker explains a refusal in it -- which field was
        # rejected, which value is not allowed -- and that text is what a failure
        # quotes.
        return error.code, error.read().decode("utf-8", "replace")
    except urllib.error.URLError as error:
        return UNREACHED, f"{type(error.reason).__name__}: {error.reason}"
    except (TimeoutError, socket.timeout):
        return UNREACHED, f"timed out after {TIMEOUT}s"


# The one seam. ⛔ Named, rather than left as a call this module makes directly:
# what earns a test here is a parse, an ordering or a guard over the host's
# answers, and every one of those is unreachable from a suite that cannot answer
# as the host. Rebound for the length of a case and restored, never for a process.
TRANSPORT = _urlopen_request


def _call(method: str, path: str, *, params: dict | None = None, body: dict | None = None):
    """One host call whose answer is a body, with every other outcome a failure.

    ⛔ `port.HostUnavailable` rather than a class of this module's: the port
    turns it into a `failed` outcome, and a role must be able to tell a broken
    call from a missing capability without knowing which tracker answered.

    ⛔ **The address and the credential are resolved here, above the seam**, and
    the two refusals they carry therefore happen before anything is sent -- which
    is a claim about where a guard sits rather than about what it says. Measured:
    with both inside the transport, a site carrying a path and a shell holding no
    token each let the call proceed as far as whatever had replaced the seam.
    """
    where, auth = _site(), _credentials()
    shown = _shown(method, path, params)
    status, text = TRANSPORT(method, path, params, body, where=where, auth=auth)
    if status == UNREACHED:
        raise HostUnavailable(f"`{shown}` never reached the host: {text}")
    if status == RATE_LIMITED:
        raise HostUnavailable(
            f"`{shown}` was rate limited by the host ({text.strip() or 'no body'}). "
            "That is this credential's own budget rather than anything about the "
            "item, and a role must not read it as a tracker that cannot."
        )
    if status in UNAUTHORISED:
        raise HostUnavailable(
            f"`{shown}` was refused as unauthorised (HTTP {status}). The account "
            "and the token address this tracker together, and a project this "
            "account cannot see is invisible to it rather than refused by name -- "
            "so this is the address being wrong and never an item that is not "
            "there."
        )
    if status == NOT_FOUND:
        raise HostUnavailable(
            f"`{shown}` answered {NOT_FOUND}. On this tracker that is one answer "
            "for two facts -- the item is not there, or this account cannot see "
            "it -- and the host states no way to tell them apart, so neither is "
            "reported as the other."
        )
    if status >= 400:
        raise HostUnavailable(
            f"`{shown}` failed with HTTP {status}: {text.strip() or 'no body'}"
        )
    if not text.strip():
        # ⚠️ An empty body is an answer here rather than a fault: a transition
        # and an assignee write both answer `204` with nothing in them, and
        # parsing that to `None` would have the next `.get` raise where a verdict
        # belongs.
        return None
    try:
        return json.loads(text)
    except ValueError as error:
        raise HostUnavailable(
            f"`{shown}` answered something that is not JSON ({error}), so the "
            "answer could not be read at all -- which is not the same as its "
            "being empty."
        ) from None


# --- the site's own vocabulary, read once per address ------------------------


def _site_payload(site: str) -> dict:
    """What a name is resolved against: the field catalogue, and who we are.

    ⛔ Two reads rather than a guess at either. Every custom field's id is
    site-specific -- which is why § 4.3's estimate and § 4.5's date are addressed
    by **name** here and resolved against this -- and the account this credential
    authenticates as is what `advance_on_merge` compares an author to.

    ⚠️ The field catalogue is site-wide and carries every field of every project,
    so a name resolving here does not mean the field is on **this** project's
    screens. That is the host's to refuse at the write, and it refuses it by
    name; resolving the id is all this can establish.
    """
    fields = _call("GET", "/field") or []
    by_name: dict[str, list[dict]] = {}
    by_id: dict[str, dict] = {}
    for field in fields:
        name = field.get("name")
        if name is not None:
            by_name.setdefault(str(name), []).append(field)
        if field.get("id") is not None:
            by_id[str(field["id"])] = field
    return {
        "site": site,
        "fields": by_name,
        "ids": by_id,
        "me": _call("GET", "/myself") or {},
    }


def _site_facts(*, again: bool = False) -> dict:
    site = _site()
    if again or site not in _sites:
        _sites[site] = _site_payload(site)
    return _sites[site]


def _field_named(name: str, *, key: str, again: bool = False) -> dict:
    """The one field a name resolves to, or a refusal naming the key.

    ⛔ **A display name or the field's own id**, whichever the configuration
    states: § 3's one name that serves every operation. The two differ for most
    fields -- `Fix versions` against `fixVersions` -- and a project may state
    either, so both are resolved here and every operation reaches the field
    through this one lookup.

    Three refusals, and ⛔ **the middle one is why this exists**: this tracker
    holds no uniqueness for a field's name, so two fields may carry one, and
    writing to either would write a value a reader of the other never sees. A
    name that is one field's id and another field's display name is the same
    case and refused the same way.
    """
    facts = _site_facts(again=again)
    found = list(facts["fields"].get(str(name), []))
    by_id = (facts.get("ids") or {}).get(str(name))
    if by_id is not None and all(one.get("id") != by_id.get("id") for one in found):
        found.append(by_id)
    if not found and not again:
        # A field created after this process started is absent from a catalogue
        # read before it existed, so the re-read happens before the refusal.
        return _field_named(name, key=key, again=True)
    if not found:
        raise ConfigError(
            key,
            f"names the field `{name}`, which this site has none of, by display "
            "name or by id. A field is resolved against the site's own catalogue, "
            "so this is a name the site does not answer to, and nothing was sent "
            "under it.",
        )
    if len(found) > 1:
        raise ConfigError(
            key,
            f"names the field `{name}`, which {len(found)} fields on this site "
            "answer to, by display name or by id. This tracker holds no "
            "uniqueness for a field's name, so there is no reading of which one "
            "was meant -- name one that is unambiguous, or rename one on the site.",
        )
    return found[0]


# --- what a policy bars ------------------------------------------------------
#
# ⛔ The forms are in `_policy` beside this module, shared with the
# implementation next door; what is here is the refusal, whose wording names an
# **issue** because that is the half that is this tracker's.


def policy_classes() -> list[str]:
    """What the bound configuration bars from reaching an item, in its own words."""
    stated = _configuration().get("tracker.policy.forbid_on_item") or []
    return [str(name) for name in stated]


def _branch_prefixes() -> list[str]:
    prefixes = _configuration().get("work_item.type_branch_prefix") or {}
    if isinstance(prefixes, dict):
        return [str(value) for value in prefixes.values() if str(value).strip()]
    return []


def _hold_to_policy(where: str, **texts: str) -> None:
    """Refuse a write whose text carries something the project bars from an item.

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
            f"bars {', '.join(f'`{name}`' for name in classes)} from reaching an "
            f"item here, and the text `{where}` was about to write carries: "
            f"{'; '.join(findings)}. ⛔ The write does not happen and no span is "
            "quoted. Where the fact is needed and this surface may not hold it, "
            "it goes in the run report instead (§ 3).",
        )


# --- a body is a document ----------------------------------------------------
#
# ⛔ One renderer and one reader, both narrow and both stated. This tracker's
# interface takes rich text as a structured document, so there is no shape in
# which a markdown body is simply sent -- and a fuller renderer is a markdown
# parser, which is this module deciding what a project's template means.

HEADING = re.compile(r"^(?P<hashes>#{1,6})\s+(?P<text>.*)$")
BULLET = re.compile(r"^[-*]\s+(?P<text>.*)$")
ORDERED = re.compile(r"^\d+[.)]\s+(?P<text>.*)$")
FENCE_LINE = re.compile(r"^\s*(?:```|~~~)(?P<language>[\w+-]*)\s*$")

# What the renderer carries and what it does not, named here and read by the
# suite rather than restated in it. ⚠️ A document shape added without a line in
# this pair is a shape nothing asserts a round trip for.
RENDERED = ("heading", "paragraph", "bulletList", "orderedList", "codeBlock")
NOT_RENDERED = (
    "a table",
    "a nested list",
    "every inline mark -- bold, a link, inline code",
)


# The nodes whose words sit in an attribute rather than in a child, by the
# attributes that carry them. A reading that skipped these would lose who a
# comment names and what it links to.
SAID_IN_ATTRIBUTES = {
    "mention": ("text", "id"),
    "emoji": ("text", "shortName"),
    "inlineCard": ("url",),
    "blockCard": ("url",),
    "embedCard": ("url",),
    "status": ("text",),
    "date": ("timestamp",),
}


def _paragraph(text: str) -> dict:
    return {"type": "paragraph", "content": [{"type": "text", "text": text}]} if text else {
        "type": "paragraph"
    }


def _list_item(text: str) -> dict:
    return {"type": "listItem", "content": [_paragraph(text)]}


def as_document(text: str) -> dict:
    """A body, as the document this tracker's interface takes.

    ⚠️ Blank-line separated blocks, each read as the one shape its first line
    announces. What survives a round trip is `RENDERED` above; everything else
    arrives as the text it was written as, which is **lossy and visible** rather
    than lossy and silent -- a reader sees the markdown they wrote.
    """
    content: list[dict] = []
    lines = (text or "").splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        fence = FENCE_LINE.match(line)
        if fence:
            index += 1
            held = []
            while index < len(lines) and not FENCE_LINE.match(lines[index]):
                held.append(lines[index])
                index += 1
            index += 1  # the closing fence, or the end of the text
            node = {"type": "codeBlock", "content": [
                {"type": "text", "text": "\n".join(held)}
            ]} if held else {"type": "codeBlock"}
            if fence.group("language"):
                node["attrs"] = {"language": fence.group("language")}
            content.append(node)
            continue
        heading = HEADING.match(line)
        if heading:
            content.append({
                "type": "heading",
                "attrs": {"level": len(heading.group("hashes"))},
                "content": [{"type": "text", "text": heading.group("text")}],
            })
            index += 1
            continue
        for pattern, kind in ((BULLET, "bulletList"), (ORDERED, "orderedList")):
            match = pattern.match(line)
            if not match:
                continue
            items = []
            while index < len(lines):
                nested = pattern.match(lines[index])
                if not nested:
                    break
                items.append(_list_item(nested.group("text")))
                index += 1
            content.append({"type": kind, "content": items})
            break
        else:
            held = []
            while index < len(lines) and lines[index].strip():
                if HEADING.match(lines[index]) or FENCE_LINE.match(lines[index]):
                    break
                if BULLET.match(lines[index]) or ORDERED.match(lines[index]):
                    break
                held.append(lines[index])
                index += 1
            if held:
                content.append(_paragraph("\n".join(held)))
            else:
                index += 1
    return {"type": "doc", "version": 1, "content": content}


def as_text(node) -> str:
    """A document, back as the body it was written as.

    ⛔ The inverse of `as_document` over `RENDERED` and nothing more. A node this
    does not know is read for its text and nothing else, which is the one
    direction that cannot lose a reader's words -- ⚠️ it loses their *shape*, and
    a round trip through a shape this module does not render is not the body that
    went in.
    """
    if isinstance(node, str):
        return node
    if not isinstance(node, dict):
        return ""
    kind = node.get("type")
    children = node.get("content") or []
    if kind == "text":
        return str(node.get("text") or "")
    if kind == "hardBreak":
        return "\n"
    if not children and isinstance(kind, str) and kind in SAID_IN_ATTRIBUTES:
        attributes = node.get("attrs") or {}
        said = (attributes.get(name) for name in SAID_IN_ATTRIBUTES[kind])
        return next((str(value) for value in said if value), "")
    if kind == "heading":
        level = int((node.get("attrs") or {}).get("level") or 1)
        return "#" * level + " " + "".join(as_text(child) for child in children)
    if kind == "codeBlock":
        language = str((node.get("attrs") or {}).get("language") or "")
        body = "".join(as_text(child) for child in children)
        return f"```{language}\n{body}\n```"
    if kind in ("bulletList", "orderedList"):
        marker = "- " if kind == "bulletList" else None
        rendered = []
        for position, child in enumerate(children, start=1):
            text = "".join(as_text(grandchild) for grandchild in child.get("content") or [])
            rendered.append((marker or f"{position}. ") + text)
        return "\n".join(rendered)
    if kind == "listItem":
        return "\n".join(as_text(child) for child in children)
    if kind == "doc":
        return "\n\n".join(as_text(child) for child in children)
    return "".join(as_text(child) for child in children)


# --- reading ----------------------------------------------------------------

# Every field a read asks for by its own name. ⛔ Narrowed rather than `*all`:
# the catalogue carries every field of every project on the site, and a read of
# all of them is a page of values no role asked for. ⚠️ `issuelinks` is in it
# because the dependency direction is read from there and nowhere else.
READ_FIELDS = (
    "summary,description,status,issuetype,priority,labels,assignee,issuelinks,"
    "timetracking,duedate,fixVersions,created,updated"
)


def _held_to_project(key: str, *, operation: str = "read_item") -> tuple[str, str]:
    """A key, held to its shape and to this project. ⛔ Before any call.

    Two refusals, and the second is this tracker's own guard. A key that is not
    this shape would be interpolated into a request path and address an endpoint
    other than the one the call means; a key of another **project** is perfectly
    valid here and resolves site-wide, so an operation handed one would work on
    somebody else's backlog and report success.
    """
    found = ITEM_KEY.match(str(key).strip())
    if not found:
        raise ConfigError(
            f"tracker.operations.{operation}",
            f"was asked for `{key!r}`, which is not an item key. An identifier on "
            "this tracker is the project's key and the item's number, and this "
            "value is put into a request path -- so anything else would address "
            "an endpoint other than the one the call means.",
        )
    project = _project_key()
    if found.group("project") != project:
        raise ConfigError(
            "tracker.project_key",
            f"states `{project}` and the key `{key}` belongs to "
            f"`{found.group('project')}`. A key resolves across the whole site "
            "here, so this one would have answered -- from another project's "
            "backlog, with every write landing there.",
        )
    return found.group("project"), found.group("number")


def _addressed(key: str, *, operation: str = "read_item") -> str:
    """The key a request path carries: held to its shape, and canonical.

    ⛔ **Every path this module builds goes through here and never through the
    argument.** The guard above matches on a stripped value, so a padded key
    passes it and then reached a path raw -- the guard holding one value while the
    call addressed another, which is the defect the code-host kinds normalise
    their numbers against. ⚠️ Worse than a misaddress on a live site: a path
    carrying a space raises inside the client, below every exception the port
    states an outcome for.

    ⚠️ Costs no call. The shape is the whole of what it reads.
    """
    project, number = _held_to_project(key, operation=operation)
    return f"{project}-{number}"


def _links_of(issue: dict) -> dict:
    """What this item is blocked by, what it blocks, and what else it relates to.

    ⛔ **The sense is read from which side the entry carries, never from the type's
    own wording**, and that is the inversion this tracker is sharpest about: an
    entry holding `inwardIssue` means the *other* issue is the inward one, so
    this item reads as the type's `inward` description **towards** it -- for
    `Blocks` that is *is blocked by*. An entry holding `outwardIssue` reads the
    other way. ⚠️ Getting this backwards reports a blocker as a thing blocked,
    and a readiness gate then starts an item whose dependency has not landed.
    """
    blocked_by, blocks, other = [], [], []
    for link in issue.get("fields", {}).get("issuelinks") or []:
        kind = (link.get("type") or {}).get("name")
        inward, outward = link.get("inwardIssue"), link.get("outwardIssue")
        side = inward or outward or {}
        status = ((side.get("fields") or {}).get("status") or {})
        entry = {
            "key": side.get("key"),
            "type": kind,
            "status": status.get("name"),
            # ⚠️ Both, and apart, for `_shaped`'s own reason one field over: the
            # word is this project's vocabulary (§ 4.2) and the category is the
            # tracker's three-way behind it. A readiness check needs the half
            # every project on this tracker shares, and a role advancing a state
            # needs the word -- so neither is derived from the other here.
            "state": (status.get("statusCategory") or {}).get("key"),
            # ⚠️ Carried because a role reporting a blocker would otherwise need a
            # second call per entry to name it, which the code-host entries do not
            # — the link payload already holds the summary, and the address is
            # composed from the key exactly as `_shaped` composes an item's own.
            # ⛔ **And the address only where there is a key to compose it from**,
            # by the rule the shared code-host grammar states for a repository
            # address: a guess at a segment is a link a role prints and a person
            # clicks, while `None` says the answer did not state one.
            "title": (side.get("fields") or {}).get("summary"),
            "url": f"{_site()}/browse/{side['key']}" if side.get("key") else None,
        }
        if kind == BLOCKS and inward:
            blocked_by.append(entry)
        elif kind == BLOCKS and outward:
            blocks.append(entry)
        else:
            # ⚠️ The side is carried as well as the sentence, because the
            # relation names a project maps (§ 3) are keyed on it: the sentence
            # is the tracker's wording, and two types may share one.
            entry["side"] = "inward" if inward else "outward"
            entry["reads"] = (
                f"this item {(link.get('type') or {}).get('inward')} it"
                if inward
                else f"this item {(link.get('type') or {}).get('outward')} it"
            )
            other.append(entry)
    return {"blocked_by": blocked_by, "blocks": blocks, "links": other}


def _shaped(issue: dict, *, named: dict | None = None) -> dict:
    """One item, in the shape a role carries onward.

    ⚠️ `status` is the project's own vocabulary (§ 4.2) and `state` is the
    tracker's three-way category behind it. The two are reported apart because
    they are two facts: a project may have four statuses in the middle category,
    and a role asking *has this finished* reads the category while a role
    advancing a state reads the word.

    ⛔ **A field that was not read is left out rather than carried as `None`**,
    which is § 3's rule about an absent capability applied to a field of an
    answer: an unread description is never an item with no description.
    """
    fields = issue.get("fields") or {}
    status = fields.get("status") or {}
    shaped = {
        "key": issue.get("key"),
        "id": issue.get("id"),
        "title": fields.get("summary"),
        "status": status.get("name"),
        "state": (status.get("statusCategory") or {}).get("key"),
        "type": (fields.get("issuetype") or {}).get("name"),
        "priority": (fields.get("priority") or {}).get("name"),
        "labels": list(fields.get("labels") or []),
        "url": f"{_site()}/browse/{issue.get('key')}",
    }
    if "description" in fields:
        shaped["body"] = as_text(fields.get("description"))
    if "assignee" in fields:
        who = fields.get("assignee") or None
        shaped["assignees"] = (
            [{"id": who.get("accountId"), "name": who.get("displayName")}] if who else []
        )
    if "timetracking" in fields:
        shaped["estimate"] = (fields.get("timetracking") or {}).get("originalEstimate")
    if "duedate" in fields:
        shaped["due"] = fields.get("duedate")
    if "fixVersions" in fields:
        shaped["versions"] = [
            version.get("name") for version in fields.get("fixVersions") or []
        ]
    if "issuelinks" in fields:
        shaped.update(_links_of(issue))
    if named:
        shaped["fields"] = named
    return shaped


def _named_values(issue: dict, names: list[str]) -> dict:
    """The named fields a caller asked for, keyed by the name it asked with.

    ⛔ Keyed by **name** and never by the site's own id. A readiness predicate
    states a field by name (§ 5), the id is site-specific, and an answer keyed on
    the id would make the predicate's own statement unreadable against it.
    """
    fields = issue.get("fields") or {}
    found = {}
    for name in names:
        field = _field_named(name, key="tracker.operations.read_item")
        found[name] = fields.get(field["id"])
    return found


def read_item(key: str, *, fields: list[str] | None = None) -> dict:
    """The item's own facts, in one call.

    ⛔ **The project guard runs first**, before anything is read: this is the
    operation every other one resolves a key through, which is what makes one
    guard cover all of them rather than one.

    ⚠️ `fields` names **extra** fields by the name the site gives them -- a
    sprint, a fix version, whatever a readiness predicate states -- and each one
    costs a catalogue read the first time and nothing after. The item's own facts
    are always read.
    """
    addressed = _addressed(key)
    asked = READ_FIELDS
    named = None
    if fields:
        ids = [
            _field_named(name, key="tracker.operations.read_item")["id"]
            for name in fields
        ]
        asked = asked + "," + ",".join(ids)
    issue = _call("GET", f"/issue/{addressed}", params={"fields": asked})
    if not isinstance(issue, dict) or not issue.get("key"):
        raise HostUnavailable(
            f"`GET {API}/issue/{addressed}` answered with no key, so whether that "
            "item is there could not be established. An unreadable answer is not "
            "the same as a clean one."
        )
    if fields:
        named = _named_values(issue, list(fields))
    return _shaped(issue, named=named)


def item_number(item: dict | str) -> str:
    """The identifier the branch name and the pull request carry.

    ⚠️ Makes **no host call**, so a string is returned as given -- held to the
    key shape, because this is the value a branch name is composed from and a
    branch name is the thing nobody goes back and corrects.

    ⛔ **A key and not a number**, which is the difference from every
    implementation beside this one. The project half travels with it: `tree_dir`
    composes a leaf out of it, and a key carrying its own separator is the
    leading half of that leaf rather than something to parse back out (§ 10).
    """
    if isinstance(item, str):
        value = item.strip()
    elif isinstance(item, dict):
        value = str(item.get("key") or "").strip()
    else:
        value = ""
    if not ITEM_KEY.match(value):
        raise ConfigError(
            "tracker.operations.item_number",
            f"was handed `{item!r}`, which carries no item key, so the identifier "
            "a branch name and a pull request carry cannot be read from it. A "
            "role with neither stops rather than inventing one (§ 3).",
        )
    return value


# --- searching ---------------------------------------------------------------


def _quoted(value: str, *, what: str) -> str:
    """One value, as a JQL operand. ⛔ Refused rather than escaped.

    A quote or a backslash ends the operand and turns the rest of the value into
    query, which the host then **answers** -- so the failure is a search that ran
    as something other than what was asked, which is indistinguishable from a
    clean answer. That is the one outcome the duplicate check must not have.
    """
    text = str(value)
    found = BREAKS_THE_QUERY.search(text)
    if found:
        raise ConfigError(
            "tracker.operations.search_items",
            f"was given {what} carrying `{found.group(0)!r}` at character "
            f"{found.start()}, which would end the quoted operand it is written "
            "into and turn the rest of the value into query. The host answers "
            "that query rather than refusing it, so this is refused here instead.",
        )
    return f'"{text}"'


def as_query(
    project: str,
    terms: str | None,
    labels: list[str] | None,
    fields: dict | None,
    *,
    texts: list[str] | tuple = ("summary",),
) -> str:
    """The query one search sends, bounded by the project.

    ⛔ **The project restriction is not a convenience.** Measured: a query with
    no restriction at all is refused by the host -- *Unbounded JQL queries are
    not allowed here* -- so this is the only shape the host accepts, and it is
    the same restriction the key guard applies one call over.

    ⛔ **No state restriction, by construction.** § 3 states the operation across
    every state the tracker holds, so nothing here filters on status unless the
    caller asked for that status by name. ⚠️ The state qualifier the plain-issues
    implementation has to refuse cannot arrive here: every term is quoted into an
    operand, and `_quoted` is what makes that true.
    """
    clauses = [f"project = {_quoted(project, what='the project key')}"]
    for word in (terms or "").split():
        # ⛔ A term matches in **any** searched text (§ 3), so the texts are one
        # disjunction per term and the terms stay a conjunction.
        either = [f"{text} ~ {_quoted(word, what='a term')}" for text in texts]
        clauses.append(either[0] if len(either) == 1 else f"({' OR '.join(either)})")
    for label in labels or []:
        clauses.append(f"labels = {_quoted(label, what='a label')}")
    for name, value in (fields or {}).items():
        clauses.append(f"{name} = {_quoted(value, what=f'the field `{name}`')}")
    return " AND ".join(clauses) + " ORDER BY updated DESC"


def search_items(
    terms: str | None = None,
    *,
    labels: list[str] | None = None,
    fields: dict | None = None,
    limit: int = 100,
) -> dict:
    """The items a query matches, across every state the tracker holds.

    **Terms, or a field's value with no terms at all, or both** -- which on this
    tracker means the status, the type and the priority, each a field the host
    queries natively rather than a value this module filters after the fact.

    ⛔ **The cursor is followed**, not read once. The host pages every search and
    an answer that fills a page says nothing about whether more exist; a short
    list answering a duplicate check reads exactly like a tracker holding
    nothing. ⚠️ The follow has a ceiling of its own, and reaching it is reported
    as `at_limit` rather than returned quietly.

    ⛔ **An unknown field name is refused, never answered with an empty list.** A
    field this module cannot shape and a field nothing matches both come back
    empty, and this is the one search the filing role performs: the two readings
    are a duplicate check that found nothing and a duplicate check that never
    ran. ⚠️ A **label** is not checked for existence, and that is the honest
    difference from the implementation next door: this host answers an unknown
    label with a refusal naming it rather than with an empty list, so the
    distinction it has to buy with an extra call arrives here for free.

    ⛔ **The texts a term is matched in are `tracker.search.texts`** (§ 3), each
    by the host's own text clause, and the answer names what it searched. ⛔ **A
    field beyond the three above is admitted by `tracker.search.fields` alone**,
    resolved by name against the site's own catalogue and queried by the clause
    name the catalogue states for it -- so a field holding several values, a
    component's or a custom one's, is asked about natively and matches when any
    of its values is the one asked for. A listed field the site does not have, or
    holds and marks unsearchable, is refused naming the list. ⚠️ The catalogue's
    `searchable` and `clauseNames` are read from the published reference and not
    yet from a live site.
    """
    admitted = coverage.stated_fields(_configuration())
    asked: dict = {}
    for name, value in (fields or {}).items():
        if name in QUERYABLE:
            asked[name] = value
        elif name in admitted:
            asked[_clause_for(name)] = value
        else:
            raise coverage.not_admitted(name, QUERYABLE)
    searched, missed = coverage.coverage(
        _configuration(),
        reachable=tuple(TEXT_CLAUSES),
        default=SEARCHED_BEFORE,
        terms=bool((terms or "").split()),
    )
    jql = as_query(
        _project_key(), terms, labels, asked or None,
        texts=[TEXT_CLAUSES[text] for text in searched],
    )
    found: list[dict] = []
    token, pages, cut = None, 0, False
    while True:
        params = {"jql": jql, "maxResults": min(PAGE, limit), "fields": READ_FIELDS}
        if token:
            params["nextPageToken"] = token
        answer = _call("GET", "/search/jql", params=params) or {}
        found += [_shaped(issue) for issue in answer.get("issues") or []]
        pages += 1
        token = answer.get("nextPageToken")
        if answer.get("isLast") or not token or len(found) >= limit:
            break
        if pages >= PAGES_AT_MOST:
            cut = True
            break
    return coverage.reported({
        "jql": jql,
        "terms": terms or "",
        "labels": list(labels or []),
        "fields": dict(fields or {}),
        "limit": limit,
        "pages": pages,
        # ⚠️ Two ways the answer can be short and both are said: the caller's own
        # bound, and this module's ceiling on how far it follows the cursor.
        "at_limit": len(found) >= limit or cut,
        "items": found[:limit],
    }, searched, missed)


def _clause_for(name: str, *, key: str = coverage.FIELDS_KEY) -> str:
    """The clause a configured field is queried by, from the site's catalogue.

    ⛔ Refused naming the key that stated the field -- `tracker.search.fields` for
    a search, `work_item.grouping.field` for a grouping read -- where the site has
    no such field, has two, marks it unsearchable or states no clause for it:
    each a field nothing could ask about, which an empty answer must not stand in
    for. ⚠️ The clause is the catalogue's and never the configured spelling: a
    field's display name, its id and its clause name are three strings here
    (`Fix versions`, `fixVersions`, `fixVersion`), and only the last is what a
    query names it by.
    """
    found = _field_named(name, key=key)
    if found.get("searchable") is False:
        raise coverage.unqueryable(name, "this site marks it unsearchable.", key=key)
    clauses = [str(clause) for clause in found.get("clauseNames") or [] if clause]
    if not clauses:
        raise coverage.unqueryable(
            name, "this site states no clause a query names it by.", key=key
        )
    clause = clauses[0]
    return clause if BARE_CLAUSE.match(clause) else _quoted(clause, what="a field's clause")


# --- writing -----------------------------------------------------------------


def _held_labels(labels: list[str]) -> list[str]:
    """Labels, held to what this tracker's own field accepts. ⛔ Before the write.

    A label here is one word. The host rejects a value carrying whitespace and
    names the whole field rather than the label that caused it, so a set of five
    with one bad member fails as *labels* -- which is a refusal nobody can act on
    without this.
    """
    held = []
    for label in labels:
        text = str(label)
        if not text.strip():
            raise ConfigError(
                "tracker.operations.set_labels",
                "was given an empty label. The host takes a list of words and an "
                "empty one is not a word; a set carrying it fails naming the "
                "whole field rather than the member.",
            )
        found = SPACE.search(text)
        if found:
            raise ConfigError(
                "tracker.operations.set_labels",
                f"was given the label `{text}`, which carries whitespace at "
                f"character {found.start()}. A label on this tracker is one word: "
                "the host refuses the value and its refusal names the field, not "
                "the label -- so a set of several would fail with nothing saying "
                "which member was wrong.",
            )
        held.append(text)
    return held


def _as_list(value, *, guard: str) -> list:
    """Several values, however the caller could hand them over.

    The port's command line passes every value as text, so a list arrives there
    as its JSON form. ⛔ Text that is not one is **one** value and never split: a
    separator is a character a component's own name may carry.
    """
    if isinstance(value, (list, tuple)):
        return list(value)
    if isinstance(value, str) and value.strip().startswith("["):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            raise ConfigError(
                guard,
                "was handed text that opens a list and is not one. A list is "
                "written in its JSON form; a single value is written bare, and one "
                "whose own name opens with a bracket goes inside a list.",
            ) from None
    return [value]


def _shaped_list(found: dict, value, *, guard: str, named: str, where: str) -> list:
    """Every member of a list field, by the element type the site states."""
    element = (found.get("schema") or {}).get("items")
    shape = ELEMENTS.get(str(element))
    if shape is None:
        raise ConfigError(
            guard,
            f"is a list of `{element}` on this site, and this implementation has no "
            f"shape for one. Shaped here are lists of: "
            f"{', '.join(sorted(ELEMENTS))}.",
        )
    members = _as_list(value, guard=guard)
    for member in members:
        if not isinstance(member, str) or not member.strip():
            raise ConfigError(
                guard,
                f"was handed {member!r} as a member of a list of `{element}`. Each "
                "member is text: a name, an option, an account id or a word.",
            )
    if shape == TEXT:
        for member in members:
            _hold_to_policy(where, **{named: member})
        return members
    return [{IDENTIFIED_BY[shape]: member} for member in members]


def _shaped_value(found: dict, value, *, guard: str, named: str, where: str):
    """One value, in the shape the resolved field's own type takes."""
    if found["id"] in OWNED_ELSEWHERE:
        raise ConfigError(
            guard,
            f"resolves to `{found['id']}`, which is written by "
            f"`{OWNED_ELSEWHERE[found['id']]}` here and not by this operation. A "
            "facet pointing at it is pointing at a value this procedure writes "
            "through a different question.",
        )
    schema = (found.get("schema") or {}).get("type")
    if schema == LIST:
        return _shaped_list(found, value, guard=guard, named=named, where=where)
    shape = RICH if found["id"] in RICH_FIELDS else SHAPES.get(str(schema))
    if shape is None:
        raise ConfigError(
            guard,
            f"is a `{schema}` field on this site, and this implementation has no "
            f"shape for one. Shaped here are: {', '.join(sorted(SHAPES))}. A value "
            "sent in a shape nobody measured is accepted by the host as often as "
            "it is refused, and the accepted half is written where no reader looks.",
        )
    if isinstance(value, (list, tuple, dict)):
        raise ConfigError(
            guard,
            f"was handed {type(value).__name__} for a `{schema}` field, which holds "
            "one value. The host would be sent that structure's own spelling as "
            "though somebody had written it.",
        )
    if shape == DATE:
        if not ISO_DATE.match(str(value)):
            raise ConfigError(
                guard,
                f"was handed `{value!r}` for a date field, which is not a date in "
                "`YYYY-MM-DD`. ⚠️ That is § 4.5's own form and this field takes "
                "the same one, so there is nothing to convert and nothing to "
                "invent.",
            )
        shaped = str(value)
    elif shape == NUMBER:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ConfigError(
                guard,
                f"was handed `{value!r}` for a number field. A string reaches this "
                "host as a value it refuses, and a flag reaches it as 1 or 0 -- "
                "which it accepts.",
            )
        shaped = value
    elif shape == DURATION_FIELD:
        text = str(value).strip()
        if not DURATION.match(text):
            raise ConfigError(
                guard,
                f"was handed `{value!r}` for a duration field, which is not a "
                "duration this tracker parses -- `4h`, `2d`, `1w 2d`. ⛔ A bare "
                "number is refused rather than sent: this host reads one as "
                "minutes under its default configuration and otherwise under "
                "another, so the unit § 4.3 states would be decided by the site.",
            )
        # ⚠️ The estimate is a member of a composite field rather than a scalar,
        # which is why the shape is a mapping and not the string. The remaining
        # estimate is deliberately not written beside it: that is a measurement
        # of work left, and § 4.3 forbids moving a number between the bound and
        # the measurement in either direction.
        shaped = {"originalEstimate": text}
    elif shape == NAMED:
        shaped = {"name": str(value)}
    elif shape == OPTION:
        shaped = {"value": str(value)}
    elif shape == RICH:
        _hold_to_policy(where, **{named: str(value)})
        shaped = as_document(str(value))
    else:
        shaped = str(value)
        _hold_to_policy(where, **{named: shaped})
    return shaped


def _not_landed(wanted: dict, item: dict) -> str:
    """Which members of which list did not read back, in words; empty for none.

    ⚠️ Compared without case, because this host matches a name that way and
    answers with its own spelling.
    """
    held = item.get("fields") or {}
    short = []
    for name, shaped in wanted.items():
        if not isinstance(shaped, list):
            continue
        back = set()
        for one in held.get(name) or []:
            if isinstance(one, dict):
                back.update(
                    str(one[part]).casefold()
                    for part in ANSWERED_AS if one.get(part) is not None
                )
            else:
                back.add(str(one).casefold())
        for one in shaped:
            member = next(iter(one.values())) if isinstance(one, dict) else one
            if str(member).casefold() not in back:
                short.append(f"`{member}` in `{name}`")
    return ", ".join(short)


def _create_fields(stated) -> dict:
    """What a filing sends beside its own parts: `{name: (id, shaped)}` (§ 3).

    ⛔ Every refusal here is before the create, so a filing the site would refuse
    for a field nobody supplied is not made. The filing's own value wins over the
    configured one, which is a default for every item rather than a fact about
    this one.
    """
    if isinstance(stated, str):
        try:
            stated = json.loads(stated)
        except json.JSONDecodeError:
            stated = None
        if not isinstance(stated, dict):
            raise ConfigError(
                "tracker.operations.create_item",
                "was handed fields as text that is not a mapping in its JSON form.",
            )
    wanted = {}
    for entry in _configuration().get("tracker.create_fields") or []:
        wanted[str(entry["field"])] = ("tracker.create_fields", entry.get("value"))
    for name, value in (stated or {}).items():
        wanted[str(name)] = (f"tracker.fields.{name}", value)
    unsupplied = [name for name, (_, value) in wanted.items() if value is None]
    if unsupplied:
        raise ConfigError(
            "tracker.create_fields",
            f"requires {', '.join(f'`{name}`' for name in unsupplied)} on every "
            "filing and states no value, and this filing states none either. The "
            "create is not sent.",
        )
    shaped = {}
    for name, (guard, value) in wanted.items():
        found = _field_named(name, key=guard)
        if found["id"] in FILED_ALREADY:
            raise ConfigError(
                guard,
                f"names `{name}`, which resolves to `{found['id']}` -- a part the "
                "filing already states through its own argument or this "
                "configuration's address.",
            )
        shaped[name] = (
            found["id"],
            _shaped_value(found, value, guard=guard, named=name, where="create_item"),
        )
    return shaped


def create_item(
    title: str,
    body: str,
    labels: list[str] | None = None,
    type: str | None = None,
    fields: dict | None = None,
) -> dict:
    """A new item, from the body the filing role wrote.

    ⛔ **A type is required here, and this is the one place this tracker forces a
    question the code-host implementations leave open.** The host will not create
    an item without one, so a filing that states none is refused with
    `work_item.type` named rather than filed as whichever type the project
    happens to list first. ⚠️ § 4.1's carrier on this tracker is `native`, which
    is why the value is the tracker's own word and the refusal points at the
    facet that carries it.

    ⚠️ The labels go on at creation, which is the reference's own shape. The
    read-back below is what makes a difference visible either way: an item that
    came back carrying fewer labels than were asked for is a failure naming them
    rather than a filing that looks finished.

    ⚠️ So do the fields § 3's `create_fields` and this filing state, by name: a
    site that requires one refuses the create without it, so writing it
    afterwards is not available.
    """
    _hold_to_policy("create_item", title=title, body=body)
    if not (type and str(type).strip()):
        raise ConfigError(
            "work_item.type",
            "states no type for this filing, and an item cannot be created "
            "without one on this tracker. § 4.1 carries the type natively here, "
            "so the value is one of the tracker's own words -- and a filing that "
            "picked one would be choosing what the work is.",
        )
    wanted = _held_labels(
        _as_list(labels, guard="tracker.operations.create_item") if labels else []
    )
    extra = _create_fields(fields)
    sent = {
        "project": {"key": _project_key()},
        "issuetype": {"name": str(type)},
        "summary": title,
        "description": as_document(body),
    }
    if wanted:
        sent["labels"] = wanted
    sent.update(dict(extra.values()))
    created = _call("POST", "/issue", body={"fields": sent}) or {}
    key = item_number(created)
    item = read_item(key, fields=list(extra) or None)
    missing = set(wanted) - set(item["labels"])
    if missing:
        raise HostUnavailable(
            f"item {key} was created and came back carrying {len(item['labels'])} "
            f"of the {len(wanted)} label(s) asked for -- "
            f"{', '.join(sorted(missing))} did not land. The item exists, so this "
            "is reported rather than retried: a second create would file the work "
            "twice."
        )
    short = _not_landed({name: shaped for name, (_, shaped) in extra.items()}, item)
    if short:
        raise HostUnavailable(
            f"item {key} was created and came back without {short}. The item "
            "exists, so this is reported rather than retried: a second create "
            "would file the work twice."
        )
    return item


def transitions(key: str, *, with_fields: bool = False) -> list[dict]:
    """Every move this item can make right now, with the status each leads to.

    ⚠️ Right **now**, for this account: what is on offer depends on the item's
    type, on where it stands and on what the workflow lets this credential do.
    Measured on a live site, one type offered three of the project's nine
    statuses and another offered all nine.

    `with_fields` asks the host for the fields each move offers, keyed by the
    field's id. ⚠️ Asked for only where a move states fields to carry, so a
    project stating none makes exactly the call it made before that key existed.
    """
    params = {"expand": "transitions.fields"} if with_fields else None
    answer = _call(
        "GET",
        f"/issue/{_addressed(key, operation='transitions')}/transitions",
        params=params,
    ) or {}
    return list(answer.get("transitions") or [])


# § 3's statement of the fields a move to a status carries.
MOVE_FIELDS = "tracker.transitions.fields"


def _move_fields(status: str) -> list[tuple[str, object]]:
    """The fields and values this project states for a move to one status (§ 3)."""
    return [
        (str(entry["field"]), entry.get("value"))
        for entry in _configuration().get(MOVE_FIELDS) or []
        if isinstance(entry, dict) and str(entry.get("status")) == str(status)
    ]


def _outside_allowed(offered: dict, shaped) -> str | None:
    """The values a move takes in one field where `shaped` is not among them.

    ⚠️ Only where the move lists the values it takes and the value is a named
    one: a field listing none takes whatever its type takes, which
    `_shaped_value` has already held.
    """
    allowed = offered.get("allowedValues") if isinstance(offered, dict) else None
    if not isinstance(allowed, list) or not isinstance(shaped, dict) or len(shaped) != 1:
        return None
    member = str(next(iter(shaped.values()))).casefold()
    named = sorted({
        str(one[part])
        for one in allowed if isinstance(one, dict)
        for part in ANSWERED_AS if one.get(part) is not None
    })
    if member in {name.casefold() for name in named}:
        return None
    return ", ".join(named) or "nothing at all"


def _move_body(status: str, move: dict, wanted: list, key: str) -> dict:
    """`{id: shaped}` for each stated field, every refusal made before the move."""
    offered = move.get("fields") if isinstance(move.get("fields"), dict) else {}
    body = {}
    for name, value in wanted:
        guard = f"{MOVE_FIELDS}.{name}"
        found = _field_named(name, key=guard)
        if found["id"] not in offered:
            raise ConfigError(
                MOVE_FIELDS,
                f"states `{name}` for a move to `{status}`, and the transition "
                f"that reaches it from where item {key} stands does not offer "
                f"that field. Offered: "
                f"{', '.join(sorted(map(str, offered))) or 'no field at all'}. "
                "⛔ The move is not made: the host would refuse the field or drop "
                "it, and either way the item would reach the status without what "
                "the project says the move carries.",
            )
        shaped = _shaped_value(found, value, guard=guard, named=name, where="set_state")
        outside = _outside_allowed(offered[found["id"]], shaped)
        if outside is not None:
            raise ConfigError(
                MOVE_FIELDS,
                f"states `{value}` in `{name}` for a move to `{status}`, which that "
                f"transition does not take. It takes: {outside}. The move is not made.",
            )
        body[found["id"]] = shaped
    return body


def _not_held(wanted: dict, item: dict) -> str:
    """Which stated fields did not read back as written, in words; empty for none.

    ⚠️ A named value is compared without case, because this host matches a name
    that way and answers with its own spelling.
    """
    held = item.get("fields") or {}
    short = []
    for name, shaped in wanted.items():
        back = held.get(name)
        if isinstance(shaped, list):
            missing = _not_landed({name: shaped}, item)
            landed = not missing
        elif isinstance(shaped, dict) and shaped.get("type") == "doc":
            landed = back is not None and as_text(back) == as_text(shaped)
        elif isinstance(shaped, dict) and set(shaped) & set(IDENTIFIED_BY.values()):
            member = str(next(iter(shaped.values()))).casefold()
            landed = isinstance(back, dict) and member in {
                str(back[part]).casefold()
                for part in ANSWERED_AS if back.get(part) is not None
            }
        elif isinstance(shaped, dict):
            landed = isinstance(back, dict) and all(
                back.get(part) == value for part, value in shaped.items()
            )
        else:
            landed = back == shaped
        if not landed:
            short.append(f"`{name}`")
    return ", ".join(short)


def set_state(key: str, *, status: str) -> dict:
    """Move the item by the transition that leads to a status, found by name.

    ⚠️ `status` is the **status word the port resolved from the role it was asked
    for** (§ 4.2) -- a role never names it and this adapter never guesses it.

    ⛔ **Matched on the status a transition leads to, never on the transition's
    own name.** The two are separate fields and a workflow is free to name a verb
    nothing like its target; § 4.2's vocabulary is the statuses, so matching the
    verb would match the wrong half wherever they differ.

    ⛔ Idempotent, by reading before writing: an item already in that status is
    returned unwritten, so a role advancing to a role the item already holds
    spends no write -- and does not meet a workflow that offers no transition
    from a status to itself.

    ⛔ **The move carries the fields § 3's `transitions.fields` states for this
    status, and nothing else.** Each is resolved by name, held to the fields the
    transition offers and the values it takes, and shaped by its type -- all
    before the move, so a refusal is a move that did not happen. The item is then
    read back with its status and every stated field, and a field that did not
    land is reported rather than the move retried: the status has moved either
    way.
    """
    item = read_item(key)
    if item["status"] == str(status):
        return item
    wanted = _move_fields(status)
    offered = transitions(key, with_fields=bool(wanted))
    matching = [
        move for move in offered if ((move.get("to") or {}).get("name")) == str(status)
    ]
    if len(matching) > 1:
        raise ConfigError(
            "statuses",
            f"names `{status}`, which {len(matching)} transitions from "
            f"`{item['status']}` lead to on this item. There is no reading of "
            "which was meant, and taking either would move the item by a verb "
            "nobody chose.",
        )
    if not matching:
        reachable = sorted(
            {
                str((move.get("to") or {}).get("name"))
                for move in offered
                if (move.get("to") or {}).get("name")
            }
        )
        raise ConfigError(
            "statuses",
            f"names `{status}`, which no transition from `{item['status']}` "
            f"reaches on item {key}. Reachable from here: "
            f"{', '.join(reachable) or 'nothing at all'}. ⚠️ Two readings and "
            "neither is assumed: the project may state a word this tracker does "
            "not have, or the word may be real and the workflow may not allow "
            "this move from this status for this type -- which is a fact about "
            "the type, since what a workflow offers differs between them.",
        )
    move = matching[0]
    fields = _move_body(status, move, wanted, key)
    body = {"transition": {"id": move.get("id")}}
    if fields:
        body["fields"] = fields
    # ⚠️ A transition whose screen requires a field this project states nothing
    # for comes back as a failure naming the transition. Nothing is invented for
    # it: a value this module chose would be written onto the item as though
    # somebody had chosen it, so the remedy is the project stating the field.
    _call("POST", f"/issue/{_addressed(key)}/transitions", body=body)
    if not wanted:
        return read_item(key)
    names = [name for name, _ in wanted]
    moved = read_item(key, fields=names)
    short = _not_held(
        {name: fields[_field_named(name, key=MOVE_FIELDS)["id"]] for name in names},
        moved,
    )
    if moved.get("status") != str(status) or short:
        raise HostUnavailable(
            f"item {key} was moved and read back in `{moved.get('status')}`"
            f"{', without ' + short if short else ''}, where the move was to "
            f"`{status}` carrying {', '.join(f'`{name}`' for name in names)}. ⛔ "
            "Reported rather than retried: a second move from wherever the item "
            "now stands is a different transition."
        )
    return moved


def set_field(key: str, field: str, value) -> dict:
    """A value written onto the item, where a facet states the field.

    The operation § 4.3's estimate, § 4.5's date and § 4.6's priority reach this
    tracker through -- each addressed by **name** and resolved to this site's own
    id, because every custom field's id is site-specific.

    ⛔ The shape is decided by the field's own type and never by what the value
    is: a date handed to a text field is accepted by the host and read back by
    nobody. A type this module has no shape for is refused naming it.

    ⛔ **A list is replaced, not added to** (§ 3): the call carries the whole list
    and the host keeps what it carries, so an empty one clears the field.
    """
    guard = f"tracker.fields.{field}"
    found = _field_named(field, key=guard)
    shaped = _shaped_value(found, value, guard=guard, named=field, where="set_field")
    read_item(key)
    _call("PUT", f"/issue/{_addressed(key)}", body={"fields": {found["id"]: shaped}})
    if not isinstance(shaped, list):
        return read_item(key)
    item = read_item(key, fields=[field])
    missing = _not_landed({field: shaped}, item)
    if missing:
        raise HostUnavailable(
            f"item {key} was written and came back without {missing}. ⛔ The write "
            "replaces the list, so what it held before is gone either way."
        )
    return item


def comment(key: str, body: str) -> dict:
    """A note on the item -- a gate result being the measured case.

    Read first, so the project guard covers this too: a comment is a write, and
    posting one onto another project's backlog because a key resolves site-wide
    is the failure that guard exists for.
    """
    _hold_to_policy("comment", body=body)
    item = read_item(key)
    posted = _call("POST", f"/issue/{_addressed(key)}/comment", body={"body": as_document(body)}) or {}
    return {
        "key": item["key"],
        "url": item["url"],
        "comment": posted.get("id"),
        "commented": True,
    }


def read_comments(key: str) -> dict:
    """The item's comments, every page of them, each with its writer and time.

    ⛔ **Held to the host's own total, and to a total that did not move.** The
    pages are offsets, so a comment removed between two of them shifts the rest by
    one and the reading skips an entry. A page that comes back empty early, a
    moved total or a repeated entry is a failed read.

    ⚠️ A comment this account may not see is absent from the host's answer, so
    nothing here can report it.

    ⚠️ A body this operation returns is data (§ 11), and it is `as_text`'s
    reading of a document: its words, without every shape.
    """
    item = read_item(key)
    path = f"/issue/{_addressed(key)}/comment"
    entries: list[dict] = []
    total = None
    for _ in range(PAGES_AT_MOST):
        answer = _call("GET", path, params={
            "startAt": len(entries), "maxResults": PAGE, "orderBy": "created",
        })
        answer = answer if isinstance(answer, dict) else {}
        page = _comments.listed(answer.get("comments"), path)
        stated = answer.get("total")
        if not isinstance(stated, int) or isinstance(stated, bool):
            raise HostUnavailable(
                f"`{path}` answered with no total, so whether every comment was "
                "read could not be established."
            )
        if total is not None and stated != total:
            raise HostUnavailable(
                f"`{path}` stated {total} comments and then {stated}, so the list "
                "moved while it was read. Read it again."
            )
        total = stated
        entries += page
        if len(entries) >= total or not page:
            break
    if len(entries) != total or len({str(one.get("id")) for one in entries}) != total:
        raise HostUnavailable(
            f"`{path}` states {total} comments and {len(entries)} were read, or one "
            "was read twice. A short list is not returned as a whole one."
        )
    for entry in entries:
        # ⛔ Before `as_text`, which answers the empty string for a shape it
        # cannot read -- a comment that says nothing, where one went unread.
        body = entry.get("body")
        if not isinstance(body, str) and not (
            isinstance(body, dict) and body.get("type") == "doc"
        ):
            raise HostUnavailable(
                f"`{path}` answered comment {entry.get('id')!r} with no readable "
                "text, so the comments went unread."
            )
    return {"key": item["key"], "comments": [
        _comments.comment(
            path,
            identifier=entry.get("id"),
            author=(entry["author"].get("displayName") or entry["author"].get("accountId"))
            if isinstance(entry.get("author"), dict) else None,
            created=entry.get("created"),
            edited=entry.get("updated"),
            url=f"{item['url']}?focusedCommentId={entry.get('id')}" if item.get("url") else None,
            body=as_text(entry.get("body")),
        )
        for entry in entries
    ]}


def set_labels(key: str, labels: list[str]) -> dict:
    """Every label set in one call, so there is no partial set to report.

    ⛔ **Set, not add.** The host takes the whole list for this field, so an item
    labelled `b` asked for `[a]` comes back carrying `a` alone rather than the
    union a per-label call would leave. ⚠️ Which also makes the empty set
    ordinary here rather than the one arm that degrades: an empty list is a value
    this field takes, where the tracker next door has no form for it at all.
    """
    wanted = _held_labels(list(labels))
    item = read_item(key)
    if set(item["labels"]) == set(wanted):
        return item
    _call("PUT", f"/issue/{_addressed(key)}", body={"fields": {"labels": wanted}})
    return read_item(key)


def assign(key: str, who: str = "@me") -> dict:
    """The item assigned to the person the role acts for.

    ⚠️ This says *taken* and nothing more. Where every session authenticates as
    one account it cannot say **which** session holds the item, so a claim does
    not rest on it -- that is § 10's, and `assign`'s own stated fallback says as
    much.

    ⛔ **The address is an account id, never a name or an address.** This tracker
    stopped answering to either: a display name is not unique and an email is not
    exposed, so `@me` is resolved through the site's own answer about this
    credential and anything else is taken as an id the caller already read from
    the host. ⚠️ Which is why there is no handle guard here of the kind the
    tracker next door needs: an id this module puts into a body came out of an
    answer it read, and holding it would be checking the host against itself.
    """
    item = read_item(key)
    if who in ("@me", "me"):
        account = str((_site_facts()["me"] or {}).get("accountId") or "")
        if not account:
            raise HostUnavailable(
                f"`GET {API}/myself` answered with no account id, so who this "
                "credential is could not be established -- which is not the same "
                "as the item having no assignee."
            )
    else:
        account = str(who)
    if [one for one in item.get("assignees") or [] if one.get("id") == account]:
        # ⛔ The same answer the written path gives, read back rather than shaped
        # from what was already in hand. An operation answering two shapes
        # depending on whether it wrote would make a role's handling of the
        # result depend on a fact it did not ask about.
        return item
    _call("PUT", f"/issue/{_addressed(key)}/assignee", body={"accountId": account})
    return read_item(key)


def link_dependency(blocked: str, blocked_by: str) -> dict:
    """One item recorded as blocked by another, as a relation.

    ⛔ **The call's `inwardIssue` is the item that BLOCKS**, which is the
    opposite of what the link type's own wording reads as: the type states
    `inward: is blocked by`, so the obvious reading puts the blocked item there
    -- and the call succeeds, recording the dependency the wrong way round.
    Nothing in the answer says so.

    ⚠️ So the direction is held by a **round trip** rather than by this docstring
    or by reading the call: the suite writes a link and asserts the blocker comes
    back under `blocked_by` on the blocked item.

    ⛔ Both keys go through `read_item` first, so the project guard covers the
    write: a key from another project would record a real relation in somebody
    else's backlog and answer as though it had worked.
    """
    # ⛔ The keys the body and the answer carry are the ones the reads answered
    # with, not the arguments. ⚠️ A **body** and not a path, which is why the
    # sweep that routed every path through `_addressed` did not reach this one:
    # the same two-halves defect, one field shape over.
    on_blocked = read_item(blocked)["key"]
    on_blocker = read_item(blocked_by)["key"]
    _call(
        "POST",
        "/issueLink",
        body={
            "type": {"name": BLOCKS},
            "inwardIssue": {"key": on_blocker},
            "outwardIssue": {"key": on_blocked},
        },
    )
    return {
        "blocked": on_blocked,
        "blocked_by": on_blocker,
        "type": BLOCKS,
        # ⚠️ Carried in the answer because the two are what a reader has to check
        # the direction against, and they run opposite ways.
        "reads": f"{on_blocked} {INWARD_READS} {on_blocker}, {on_blocker} "
        f"{OUTWARD_READS} {on_blocked}",
    }


def read_blockers(key: str) -> dict:
    """The items this one is recorded as blocked by, each with its own state.

    The read half of `link_dependency`, and ⛔ **it makes no call of its own**: the
    links arrive with the item, so this is `read_item`'s own answer narrowed to
    one side of one link type rather than a second request that could disagree
    with it. The project guard and the direction rule therefore both hold here
    without being restated.

    ⛔ **Which side is a blocker is `_links_of`'s reading and not this
    function's.** The sense is read from which side an entry carries, never from
    the link type's wording -- the inversion this tracker is sharpest about -- so
    narrowing here is a key lookup and nothing more.

    ⛔ **No verdict.** Each blocker comes back with the project's own status word
    and the tracker's category behind it, because which bar a blocker is held to
    depends on what it produced and that is § 5's question.

    ⚠️ **And what this tracker cannot answer here is *why* a blocker closed**, which
    the code-host entries carry. The resolution is not in a link payload, and this
    operation makes no call of its own -- so a blocker abandoned and one finished
    both arrive in the category that means neither, and the honest answer is that
    the field is absent rather than empty. ⛔ A reader of a blocker on this tracker
    therefore has the category and not what it produced, which is § 2's
    absence-of-signal rule stated where it bites rather than left to be found.

    ⛔ **An answer that did not carry the links at all is a failed call, never an
    item with no blocker.** `_shaped` sets the key only where the field was there,
    so reading it with a default answered the same for an unread field and an
    empty one -- absence of signal turned into *no blockers*, which is the failure
    the code-host path in this toolkit is guarded against and the one a readiness
    gate cannot survive.
    """
    item = read_item(key)
    if "blocked_by" not in item:
        raise HostUnavailable(
            f"the answer for {key} carried no links field, so what it is blocked "
            "by could not be read. An unreadable answer is not the same as an "
            "item with no recorded blocker."
        )
    # ⛔ The key in the answer is the item's own and never the argument, which is
    # the rule the code-host paths carry for their numbers: every value from an
    # invocation arrives as text, and a key echoed back is the caller's spelling
    # rather than the tracker's.
    return {"key": item["key"], "blockers": list(item["blocked_by"])}


def _relation(name: str) -> tuple[str, str | None]:
    """The link type and side the project maps one relation name onto (§ 3).

    ⛔ **A name the project does not map is refused, never defaulted**, so a
    project stating no `relations` links nothing and files as it did before the
    key existed. ⛔ **And a name mapped onto the dependency's own type is refused
    before anything is sent**: that link is `read_blockers`'s, and the same link
    read as a relation would hand a readiness gate a blocker it cannot see, or a
    relation it would hold an item back on.
    """
    mapped = (_configuration().get("tracker.relations") or {}).get(name)
    if not isinstance(mapped, dict):
        raise ConfigError(
            f"tracker.relations.{name}",
            "is not a relation this project maps, so nothing is linked. A role "
            "links only what `tracker.relations` names, and keeps any other "
            "relation as prose in the body (§ 3).",
        )
    if mapped.get("type") == BLOCKS:
        raise ConfigError(
            f"tracker.relations.{name}.type",
            f"is `{BLOCKS}`, the type a dependency is written as. That link is "
            "`link_dependency`'s, and a relation never answers a readiness check "
            "(§ 3).",
        )
    return mapped["type"], mapped.get("side")


def link_relation(item: str, other: str, relation: str) -> dict:
    """One item recorded as standing in a non-blocking relation to another.

    ⛔ **The side is what `item` reads, and the call's positions run the other
    way** -- the inversion `link_dependency` documents: the issue a call puts in
    `outwardIssue` is the one that reads the type's **inward** wording. So an
    item reading `inward` goes in the outward position, and the suite holds that
    by reading the link back from both ends rather than by reading this call.

    ⚠️ A type worded the same both ways states no side and is written as
    `outward`: either position reads the same there, and the read-back answers
    with the unsided name from either end.

    ⛔ Both keys go through `read_item` first, so the project guard covers the
    write exactly as it covers the dependency's.
    """
    kind, side = _relation(relation)
    on_item = read_item(item)["key"]
    on_other = read_item(other)["key"]
    reads_inward = side == "inward"
    _call(
        "POST",
        "/issueLink",
        body={
            "type": {"name": kind},
            "inwardIssue": {"key": on_other if reads_inward else on_item},
            "outwardIssue": {"key": on_item if reads_inward else on_other},
        },
    )
    return {"item": on_item, "other": on_other, "relation": relation}


def read_relations(key: str) -> dict:
    """The items this one is related to, each under the project's own name.

    The read half of `link_relation`, and ⛔ **it makes no call of its own**, for
    `read_blockers`'s reason: the links arrive with the item, and which side an
    entry is read from is `_links_of`'s reading rather than a second one here.

    ⛔ **The dependency's own type never appears here**: `_links_of` sorts it into
    the blocker lists before anything reaches `links`, so this answer and
    `read_blockers`'s cannot both carry one link.

    ⚠️ **A link of a type the project maps no name for is carried under
    `unnamed`**, with the wording the tracker gave it -- never dropped, which
    would read as fewer relations than the item has, and never assigned the
    nearest name, which would read as a relation nobody made.

    ⛔ **An answer that did not carry the links at all is a failed call**, by
    `read_blockers`'s rule: unread is not none.
    """
    item = read_item(key)
    if "links" not in item:
        raise HostUnavailable(
            f"the answer for {key} carried no links field, so what it is related "
            "to could not be read. An unreadable answer is not the same as an "
            "item with no recorded relation."
        )
    names = {}
    for name, mapped in (_configuration().get("tracker.relations") or {}).items():
        if isinstance(mapped, dict) and mapped.get("type") != BLOCKS:
            for side in ((mapped.get("side"),) if mapped.get("side") else ("inward", "outward")):
                names[(mapped.get("type"), side)] = name
    named, unnamed = [], []
    for link in item["links"]:
        entry = {name: link.get(name) for name in ("key", "title", "url", "status", "state")}
        relation = names.get((link.get("type"), link.get("side")))
        if relation is None:
            unnamed.append({**entry, "reads": link.get("reads")})
        else:
            named.append({**entry, "relation": relation})
    return {"key": item["key"], "relations": named, "unnamed": unnamed}


def advance_on_merge(key: str) -> dict:
    """Whether something other than this credential moved the item.

    ⛔ **A confirmation and not an assertion**, as on the code host: the
    capability being present means the procedure does not call `set_state`
    itself, and the only honest way to report that is to ask what happened.

    ⛔ **And what this tracker can answer is its own half alone.** The merge is
    on another host entirely, so there is no reference here that ties a status
    change to one: what this reports is the last status change and whether its
    author is this credential. `advanced: false` is a real answer -- nothing
    moved it, or this procedure did -- and a role can act on it.

    ⛔ **Who moved it is not reported as automation or as a person.** A script
    running under somebody's token is indistinguishable from that person in the
    answer, which is the published caution; naming one would be a guess dressed
    as a reading.

    ⚠️ The history is read through the item's own newest page, which is the one
    page this host sorts newest-first -- so the **last** change is what this
    establishes and a longer history is not read. That is the bound this question
    needs and it is stated rather than widened.
    """
    item = read_item(key)
    me = str((_site_facts()["me"] or {}).get("accountId") or "")
    issue = _call("GET", f"/issue/{_addressed(key)}", params={"expand": "changelog", "fields": "status"})
    history = ((issue or {}).get("changelog") or {}).get("histories") or []
    moved = None
    for entry in history:
        for change in entry.get("items") or []:
            if change.get("field") == "status":
                moved = {
                    "at": entry.get("created"),
                    "by": (entry.get("author") or {}).get("accountId"),
                    "from": change.get("fromString"),
                    "to": change.get("toString"),
                }
                break
        if moved:
            break
    return {
        # ⛔ The item's own key, not the argument's spelling, which is this
        # module's rule.
        "key": item["key"],
        "status": item["status"],
        "state": item["state"],
        "advanced": bool(moved) and moved.get("by") != me,
        "moved": moved,
        "bound": "this tracker cannot see the merge, which is on the code host "
        "(§ 2); what it answers is whether the last status change was made by "
        "something other than this credential, and it cannot tell an automation "
        "from a person",
    }


def grouping_items(value: str, *, grouping: dict) -> dict:
    """The items this project holds in one grouping, by one bounded query.

    ⛔ **One query rather than a read per item**, and the field is the
    configuration's: § 4.8 says where a grouping is held here, so the clause is
    built from that name and the host resolves it. ⚠️ The project bound is
    `as_query`'s and not a narrowing of its own -- an unbounded query is refused
    by this host outright, which is the same restriction every search here
    carries.

    ⛔ **Across every state**, which is what § 33 reads this set for: a release
    held by an item somebody finished by hand is still a fact about the release,
    and a set narrowed to the unfinished ones would answer *nothing is short*
    for a release whose every item had moved.

    ⛔ **A carrier with no field to query is refused with the key named**, which
    is `set_field`'s answer for a type this module has no shape for: a grouping
    this project keeps nowhere a query can reach is a defect in the text rather
    than an operation that is missing.

    ⚠️ **The cursor is followed under this module's own ceiling**, as a search is,
    and reaching it is reported as `at_limit` rather than returned quietly -- a
    release's set cut by a page bound and reported as whole is the one reading
    the precondition above it cannot survive.
    """
    carrier = (grouping or {}).get("carrier")
    if carrier == "field":
        # ⛔ Resolved, never put into the query as configured: § 3's one name is a
        # display name or an id, and the query names the field by neither.
        clause = {
            _clause_for(str((grouping or {}).get("field")), key="work_item.grouping.field"):
                value
        }
        labels: list[str] = []
    elif carrier == "label":
        clause = {}
        labels = [f"{(grouping or {}).get('label_prefix') or ''}{value}"]
    else:
        raise ConfigError(
            "work_item.grouping.carrier",
            f"is {carrier!r}, and a grouping here is read by a query: a field this "
            "project names, or a label. A carrier with nothing for a clause to "
            "name is a configuration this implementation cannot address rather "
            "than an operation it is missing.",
        )
    # ⛔ Built through the same composer every search uses, so the quoting and the
    # project bound are one statement rather than two: a clause assembled here
    # would be a second query grammar allowed to disagree about both.
    jql = as_query(_project_key(), None, labels, clause or None)
    found: list[dict] = []
    token, pages, cut = None, 0, False
    while True:
        params = {"jql": jql, "maxResults": PAGE, "fields": READ_FIELDS}
        if token:
            params["nextPageToken"] = token
        answer = _call("GET", "/search/jql", params=params) or {}
        found += [_shaped(issue) for issue in answer.get("issues") or []]
        pages += 1
        token = answer.get("nextPageToken")
        if answer.get("isLast") or not token:
            break
        if pages >= PAGES_AT_MOST:
            cut = True
            break
    return {
        "grouping": (grouping or {}).get("name"),
        "value": value,
        "jql": jql,
        "pages": pages,
        "at_limit": cut,
        "items": found,
    }


def read_vocabulary() -> dict:
    """What this project states its own words are, before a configuration exists.

    ⛔ **The statuses are read per issue type and flattened once**, because this
    tracker states them that way: a project's workflow can give two types two
    different state sets, and a reading that took one type's would state a
    vocabulary the other half of the backlog cannot hold. ⚠️ The order is the
    host's own within each type, and the flattening keeps first appearance --
    which is the closest thing to *a project's order* this tracker publishes.

    ⛔ **The label set is *unestablished*, and that is this tracker's shape.** A
    label here is site-wide rather than a project's, so there is no set a project
    states -- and answering with the site's would hand a setup step every label
    anybody on the instance has ever used, as though they were this project's
    convention.
    """
    reading: dict[str, dict] = {}
    key = None
    try:
        key = _project_key()
        statuses = _call("GET", f"/project/{key}/statuses")
    except (ConfigError, HostUnavailable) as error:
        statuses = None
        reading["statuses"] = {
            "answer": port.VOCABULARY_UNESTABLISHED,
            "values": None,
            "because":
                f"this project's statuses could not be read: {error}. ⛔ Not read "
                "as a project with no states",
        }
    if statuses is not None:
        words: list[str] = []
        for a_type in statuses if isinstance(statuses, list) else []:
            for status in (a_type.get("statuses") or []):
                name = status.get("name")
                if name and name not in words:
                    words.append(name)
        reading["statuses"] = {
            "answer": port.VOCABULARY_READ if words else port.VOCABULARY_NONE,
            "values": words,
            "because":
                f"{len(words)} status word(s) across the issue types of {key}, "
                "in the order this tracker states them"
                if words else
                f"{key} states no status at all, which is a project whose "
                "workflow has none rather than a reading that failed",
        }

    try:
        project = _call("GET", f"/project/{key}") if key else None
    except (ConfigError, HostUnavailable) as error:
        project = None
        reading["types"] = {
            "answer": port.VOCABULARY_UNESTABLISHED,
            "values": None,
            "because":
                f"this project's issue types could not be read: {error}. ⛔ Not "
                "read as a project with no types",
        }
    if project is not None:
        types = [
            one.get("name") for one in (project.get("issueTypes") or [])
            if one.get("name")
        ]
        reading["types"] = {
            "answer": port.VOCABULARY_READ if types else port.VOCABULARY_NONE,
            "values": types,
            "because":
                f"{len(types)} native issue type(s) on {key}, so § 4.1's carrier "
                "is this tracker's own type rather than a label convention"
                if types else
                f"{key} states no issue type, which no project on this tracker "
                "ordinarily does -- read as stated rather than as a failure",
        }
    elif "types" not in reading:  # pragma: no cover -- no key to ask with
        reading["types"] = {
            "answer": port.VOCABULARY_UNESTABLISHED,
            "values": None,
            "because": "there is no project key to ask about yet",
        }

    reading["labels"] = {
        "answer": port.VOCABULARY_UNESTABLISHED,
        "values": None,
        "because":
            "a label here belongs to the whole site rather than to a project, so "
            "there is no set this project states. ⛔ Not read as a project with "
            "no labels: answering with the site's would offer every label anybody "
            "on the instance has used as this project's own convention",
    }
    return reading


ADAPTER = port.Adapter(binder=bind, operations={
    "read_vocabulary": read_vocabulary,
    "read_item": read_item,
    "search_items": search_items,
    "create_item": create_item,
    "item_number": item_number,
    "set_state": set_state,
    "set_field": set_field,
    "comment": comment,
    "read_comments": read_comments,
    "set_labels": set_labels,
    "assign": assign,
    "link_dependency": link_dependency,
    "read_blockers": read_blockers,
    "link_relation": link_relation,
    "read_relations": read_relations,
    "advance_on_merge": advance_on_merge,
    "grouping_items": grouping_items,
    # ⛔ The operations this tracker has nothing to implement against are named
    # once, below, and read from there by the suite.
})

# The ones the module docstring argues are absent because the tracker has nothing
# to implement them against: there is no check-item object, so the checklist
# operations are prose in the description -- which is what their fallbacks already
# say -- and no keyword in a pull request closes an item here, so
# `link_for_close` has nothing to compose. ⛔ Written once, here, and read by the
# suite rather than restated in it: an absence added here would otherwise be an
# operation nobody noticed going missing.
#
# `mark_grouping_released` is the measured one, and it is the absence § 33's
# fallback was written against: the grouping here is a **field's value** -- the
# shape the example beside this module carries -- and a field value is not an
# object anything can mark released. The step is a link handed to a person, every
# release, which is what the surveyed copy of this procedure already does.
# ⚠️ **What would change it is a project holding its release scope in this
# tracker's own version object instead**, which is a different carrier and a
# different endpoint; until one does, an implementation here would be answering
# for a shape nothing measured.
# `read_closing_change` is `link_for_close`'s absence read from the other side and
# is absent for the same measured reason: nothing on this tracker relates an item
# to the change that closed it. What a surveyed installation shows under an item is
# written there by a code-host integration somebody installed, which is a fact
# about that installation rather than about this tracker -- so an implementation
# here would answer for a shape nothing measured, and answer *no change* about
# every project that has not installed it.
#
# `read_closing_list` is absent with them: no text in a change closes an item
# here, so no merge has a list of what it will close.
#
# `create_grouping` is `mark_grouping_released`'s absence one act earlier, on the
# same argument: the grouping here is a **field's value**, which is the shape the
# example beside this module carries, and a field's value is not an object
# anything creates. A project would add the value to the field's own allowed set,
# which is a configuration of the tracker rather than a write about one grouping.
# ⚠️ **What would change it is a project holding its order of work in this
# tracker's own sprint or version object**, which is a different carrier and a
# different endpoint -- the same condition the release mark already names.
DELIBERATELY_ABSENT = (
    "link_for_close",
    "read_closing_change",
    "read_closing_list",
    "mark_grouping_released",
    "create_grouping",
    "checklist_read",
    "checklist_write",
    "checklist_item_delete",
)


def self_test() -> int:
    """This implementation's own suite, which lives in the module beside it.

    ⛔ **A module of its own**, for the reason the two implementations beside
    this one record: a file this size reaches the code host with no patch at all,
    and the gate that holds every added line to the deferral rule then refuses
    the change.

    ⚠️ The suite's module name opens with `_`, which is what keeps discovery from
    reading it as an implementation that names no kind.
    """
    from adapters import _jira_suite as suite

    return suite.self_test()


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Issues on a hosted tracker behind the port: its own suite.",
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
