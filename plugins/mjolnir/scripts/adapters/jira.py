#!/usr/bin/env python3
"""Issues behind the port: the identifier is a key, and a state is a transition.

The fourth implementation, and the one whose tracker is a hosted service with the
code on another host entirely -- which is the case that proves tracker and host
are two axes rather than two names for one. Everything the two code-host
implementations get for free, this one has to ask for: the identifier is not a
number, the state is not a field anybody writes, and the merge the item is
supposed to move off happens somewhere this tracker cannot see.

What it implements, and what it deliberately does not:

  * **Every operation § 3 states except four.** ⛔ No count of them is carried --
    the list is closed and stated once, in § 3, and a number here would be wrong
    the next time it grows. The four are named once in `DELIBERATELY_ABSENT`
    below: this tracker has no check-item object of its own, so the three
    checklist operations are prose in the description, which is precisely what
    their stated fallbacks already say to do; and ⛔ **no closing keyword
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
TEXT, RICH, DATE, NUMBER, DURATION_FIELD, NAMED, OPTION = (
    "text", "rich", "date", "number", "duration", "named", "option",
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
    "option": OPTION,
}

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
    for field in fields:
        name = field.get("name")
        if name is None:
            continue
        by_name.setdefault(str(name), []).append(field)
    return {"site": site, "fields": by_name, "me": _call("GET", "/myself") or {}}


def _site_facts(*, again: bool = False) -> dict:
    site = _site()
    if again or site not in _sites:
        _sites[site] = _site_payload(site)
    return _sites[site]


def _field_named(name: str, *, key: str, again: bool = False) -> dict:
    """The one field a name resolves to, or a refusal naming the key.

    Three refusals, and ⛔ **the middle one is why this exists**: this tracker
    holds no uniqueness for a field's name, so two fields may carry one, and
    writing to either would write a value a reader of the other never sees.
    """
    facts = _site_facts(again=again)
    found = facts["fields"].get(str(name), [])
    if not found and not again:
        # A field created after this process started is absent from a catalogue
        # read before it existed, so the re-read happens before the refusal.
        return _field_named(name, key=key, again=True)
    if not found:
        raise ConfigError(
            key,
            f"names the field `{name}`, which this site has none of. A field is "
            "addressed by name here and its id is read from the site's own "
            "catalogue, because every custom field's id is site-specific -- so "
            "this is a name the site does not answer to rather than an id gone "
            "stale.",
        )
    if len(found) > 1:
        raise ConfigError(
            key,
            f"names the field `{name}`, which this site has {len(found)} of. This "
            "tracker holds no uniqueness for a field's name, so there is no "
            "reading of which one was meant -- name one that is unambiguous, or "
            "rename one on the site.",
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


def _held_to_project(key: str) -> tuple[str, str]:
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
            "tracker.operations.read_item",
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
        entry = {
            "key": side.get("key"),
            "type": kind,
            "status": ((side.get("fields") or {}).get("status") or {}).get("name"),
        }
        if kind == BLOCKS and inward:
            blocked_by.append(entry)
        elif kind == BLOCKS and outward:
            blocks.append(entry)
        else:
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
    _held_to_project(key)
    asked = READ_FIELDS
    named = None
    if fields:
        ids = [
            _field_named(name, key="tracker.operations.read_item")["id"]
            for name in fields
        ]
        asked = asked + "," + ",".join(ids)
    issue = _call("GET", f"/issue/{key}", params={"fields": asked})
    if not isinstance(issue, dict) or not issue.get("key"):
        raise HostUnavailable(
            f"`GET {API}/issue/{key}` answered with no key, so whether that item "
            "is there could not be established. An unreadable answer is not the "
            "same as a clean one."
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
        clauses.append(f"summary ~ {_quoted(word, what='a term')}")
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
    """
    for name in fields or {}:
        if name not in QUERYABLE:
            raise ConfigError(
                f"tracker.operations.search_items.{name}",
                f"is not a field this tracker answers a query on here. Queryable "
                f"are: {', '.join(QUERYABLE)}. Anything else is a field whose "
                "query shape is site-specific -- a name resolves to an id per "
                "site, and two sites spell the same question differently -- so it "
                "is refused rather than answered with the items that do not match.",
            )
    jql = as_query(_project_key(), terms, labels, fields)
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
    return {
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
    }


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


def create_item(
    title: str, body: str, labels: list[str] | None = None, *, type: str | None = None
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
    wanted = _held_labels(list(labels or []))
    fields = {
        "project": {"key": _project_key()},
        "issuetype": {"name": str(type)},
        "summary": title,
        "description": as_document(body),
    }
    if wanted:
        fields["labels"] = wanted
    created = _call("POST", "/issue", body={"fields": fields}) or {}
    key = item_number(created)
    item = read_item(key)
    missing = set(wanted) - set(item["labels"])
    if missing:
        raise HostUnavailable(
            f"item {key} was created and came back carrying {len(item['labels'])} "
            f"of the {len(wanted)} label(s) asked for -- "
            f"{', '.join(sorted(missing))} did not land. The item exists, so this "
            "is reported rather than retried: a second create would file the work "
            "twice."
        )
    return item


def transitions(key: str) -> list[dict]:
    """Every move this item can make right now, with the status each leads to.

    ⚠️ Right **now**, for this account: what is on offer depends on the item's
    type, on where it stands and on what the workflow lets this credential do.
    Measured on a live site, one type offered three of the project's nine
    statuses and another offered all nine.
    """
    answer = _call("GET", f"/issue/{key}/transitions") or {}
    return list(answer.get("transitions") or [])


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
    """
    item = read_item(key)
    if item["status"] == str(status):
        return item
    offered = transitions(key)
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
    # ⚠️ A transition the host marks as having a screen may require a field to be
    # filled as part of the move. Nothing is sent with it: a value this module
    # invented would be written onto the item as though somebody had chosen it,
    # so a screen with a required field comes back as a failure naming the
    # transition -- which is the remedy being a person's rather than a default's.
    _call("POST", f"/issue/{key}/transitions", body={"transition": {"id": move.get("id")}})
    return read_item(key)


def set_field(key: str, field: str, value) -> dict:
    """A value written onto the item, where a facet states the field.

    The operation § 4.3's estimate, § 4.5's date and § 4.6's priority reach this
    tracker through -- each addressed by **name** and resolved to this site's own
    id, because every custom field's id is site-specific.

    ⛔ The shape is decided by the field's own type and never by what the value
    is: a date handed to a text field is accepted by the host and read back by
    nobody. A type this module has no shape for is refused naming it.
    """
    guard = f"tracker.fields.{field}"
    found = _field_named(field, key=guard)
    if found["id"] in OWNED_ELSEWHERE:
        raise ConfigError(
            guard,
            f"resolves to `{found['id']}`, which is written by "
            f"`{OWNED_ELSEWHERE[found['id']]}` here and not by this operation. A "
            "facet pointing at it is pointing at a value this procedure writes "
            "through a different question.",
        )
    schema = (found.get("schema") or {}).get("type")
    shape = RICH if found["id"] in RICH_FIELDS else SHAPES.get(str(schema))
    if shape is None:
        raise ConfigError(
            guard,
            f"is a `{schema}` field on this site, and this implementation has no "
            f"shape for one. Shaped here are: {', '.join(sorted(SHAPES))}. A value "
            "sent in a shape nobody measured is accepted by the host as often as "
            "it is refused, and the accepted half is written where no reader looks.",
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
        _hold_to_policy("set_field", **{field: str(value)})
        shaped = as_document(str(value))
    else:
        shaped = str(value)
        _hold_to_policy("set_field", **{field: shaped})
    read_item(key)
    _call("PUT", f"/issue/{key}", body={"fields": {found["id"]: shaped}})
    return read_item(key)


def comment(key: str, body: str) -> dict:
    """A note on the item -- a gate result being the measured case.

    Read first, so the project guard covers this too: a comment is a write, and
    posting one onto another project's backlog because a key resolves site-wide
    is the failure that guard exists for.
    """
    _hold_to_policy("comment", body=body)
    item = read_item(key)
    posted = _call("POST", f"/issue/{key}/comment", body={"body": as_document(body)}) or {}
    return {
        "key": item["key"],
        "url": item["url"],
        "comment": posted.get("id"),
        "commented": True,
    }


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
    _call("PUT", f"/issue/{key}", body={"fields": {"labels": wanted}})
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
    _call("PUT", f"/issue/{key}/assignee", body={"accountId": account})
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
    read_item(blocked)
    read_item(blocked_by)
    _call(
        "POST",
        "/issueLink",
        body={
            "type": {"name": BLOCKS},
            "inwardIssue": {"key": blocked_by},
            "outwardIssue": {"key": blocked},
        },
    )
    return {
        "blocked": blocked,
        "blocked_by": blocked_by,
        "type": BLOCKS,
        # ⚠️ Carried in the answer because the two are what a reader has to check
        # the direction against, and they run opposite ways.
        "reads": f"{blocked} {INWARD_READS} {blocked_by}, {blocked_by} "
        f"{OUTWARD_READS} {blocked}",
    }


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
    issue = _call("GET", f"/issue/{key}", params={"expand": "changelog", "fields": "status"})
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
        "key": key,
        "status": item["status"],
        "state": item["state"],
        "advanced": bool(moved) and moved.get("by") != me,
        "moved": moved,
        "bound": "this tracker cannot see the merge, which is on the code host "
        "(§ 2); what it answers is whether the last status change was made by "
        "something other than this credential, and it cannot tell an automation "
        "from a person",
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
    "advance_on_merge": advance_on_merge,
    # ⛔ The four operations this tracker has nothing to implement against are
    # named once, below, and read from there by the suite.
})

# The four the module docstring argues are absent because the tracker has nothing
# to implement them against: there is no check-item object, so the three
# checklist operations are prose in the description -- which is what their
# fallbacks already say -- and no keyword in a pull request closes an item here,
# so `link_for_close` has nothing to compose. ⛔ Written once, here, and read by
# the suite rather than restated in it: a fifth absence would otherwise be an
# operation nobody noticed going missing.
DELIBERATELY_ABSENT = (
    "link_for_close",
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
