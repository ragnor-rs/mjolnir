#!/usr/bin/env python3
"""Plain GitHub issues behind the port: no board, no status field, no `in_flight`.

The cheapest real tracker there is, and what a new adopter has on their first
day. It is also what this repository runs on, which is the whole reason this
adapter exists first: a surface nothing stands on is a surface whose holes are
nobody's problem.

What it implements, and what it deliberately does not:

  * **Not every operation § 3 states**, and the ones it leaves are named once in
    `DELIBERATELY_ABSENT` below, with the reason beside each there rather than
    here. ⛔ No count of them is carried and no subset is named: the list is
    closed and stated once, in § 3, and either shape here would be wrong the next
    time it grows. What happened when this bullet named one is recorded with the
    list itself.
  * **`set_state` writes `open` or `closed` and refuses any other word.** A
    project whose `statuses` name a third state has written something plain
    issues cannot hold, and that is a statement the surface has to answer rather
    than a value to coerce. ⚠️ Whether the procedure may make the move at all is
    `advance_to`'s business one layer up (§ 4.2's writer), never this module's.
  * **`link_dependency` posts a relation, never a `Depends on #N` line.** Keyed
    on the blocker's **internal id** and posted on the *blocked* item, which is
    the inversion `docs/configuration-surface.md` measured. A prose line is what
    the stated fallback does where the capability is absent; here it is present,
    and writing both would be two statements allowed to disagree.
  * **`read_blockers` reads the same relation back, paged whole.** It is what the
    readiness gate's blocker predicate has as a source, and the one thing it does
    not do is decide: each blocker comes back with the host's own state word and
    the repository it lives in, because which bar a blocker is held to depends on
    what it produced and that is the gate's question. ⚠️ An item with no recorded
    blocker is a real answer here; a tracker that *cannot* be asked is the absent
    case and belongs to the port.
  * **`advance_on_merge` confirms rather than asserts.** The host's own
    automation closes an issue when a pull request carrying a closing reference
    merges, so the capability is present and the procedure does not make the
    move itself. The callable therefore *asks the host what happened* and reports
    whether it actually did it -- a declaration nothing can observe would leave a
    role unable to tell automation that worked from automation that was never
    wired.
  * **`search_items` answers across both states and takes no state argument.**
    It is the one read here that needs no pull-request guard, because the host's
    issue search excludes them outright -- measured, not assumed, and stated on
    the operation itself. What it does guard is the two ways an empty answer
    lies: a state qualifier hidden in the terms, and a label the repository does
    not have.
  * **Every operation taking an item number resolves it through `read_item`
    first**, which is what makes the pull-request guard there cover them rather
    than cover one. ⚠️ Measured: an earlier draft claimed that coverage while
    `comment` and `link_dependency` went straight to the host, so both could
    write against a pull request. The ones that make no call at all are named as
    such where they are defined.

Every call goes through `gh`, which holds the credential and the host's base URL,
so an enterprise host needs no key here. The configuration arrives from the port
through `bind`; nothing here resolves a project for itself.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys

# The package's parent, appended rather than prepended: this module is imported
# as `adapters.github_issues`, so the contract beside it is not otherwise on the
# path, and putting it first would shadow a standard-library name.
_SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SCRIPTS not in sys.path:
    sys.path.append(_SCRIPTS)

import port  # noqa: E402

from adapters import _code_host_dependency as relation  # noqa: E402

KIND = "github-issues"

# The two states plain issues have. Written here because they are the host's
# vocabulary rather than the project's: a `statuses` list is free to choose which
# of them it maps and to which role (§ 4.2), and free to leave one out, but it
# cannot invent a third and have this tracker hold it.
OPEN = "open"
CLOSED = "closed"

# A term that would narrow the states searched. ⛔ Refused rather than honoured:
# the search operation is stated across **every** state the tracker holds, and a
# query carrying one of these silently answers for one of them -- measured,
# `--search "prose width state:closed"` came back with the two closed items and
# dropped the four open ones, with `--state all` still on the command line. A
# duplicate check narrowed to one state is the failure § 2's absence-of-signal
# rule describes, and it looks exactly like a clean answer.
#
# Deliberately a shade over-broad -- a leading `-`, any spacing -- because the
# wrong direction here is the silent one, and the words are refused by name.
STATE_QUALIFIER = re.compile(r"-?\b(?:state|is)\s*:\s*(?:open|closed)\b", re.IGNORECASE)

# What the host's client writes to stderr when the thing asked for is not there.
# ⛔ Carried as a constant rather than spelled into a condition, because *absent*
# and *could not be established* are two different answers here and this string is
# the whole of what separates them.
NOT_FOUND = "(HTTP 404)"

# What a search with no terms is ordered by. The keyword-independent layer of the
# duplicate check reads titles rather than matches, so it asks for the most
# recently updated under a bound; the host's own default order is relevance,
# which means nothing to a query with no terms in it.
RECENT_FIRST = "sort:updated-desc"

# The configuration the port last handed down, and the only place one comes from.
# ⛔ Never resolved here, and never from the working directory: which repository
# an item lives in is `host.repo`'s to say (§ 2), and a process serving more than
# one project -- which the adoption-readiness run already is -- must address each
# one's own. An earlier draft read it from the invocation directory and cached it
# process-wide, which pinned every later project to the first one's repository.
_bound = None


def bind(configuration) -> None:
    """Take the configuration for the operation about to run.

    `Port.invoke` calls this before every operation, so it is per call rather
    than per process and switching projects needs no reset.
    """
    global _bound
    _bound = configuration


def _repo() -> str:
    """The repository the bound configuration addresses.

    The surface marks `host.repo` `# required`, so a configuration that reached
    here states one; what this refuses is the shape, which nothing else checks.
    """
    if _bound is None:
        raise port.ConfigError(
            "tracker.adapters.github_issues",
            "was asked for an operation before the port bound a configuration to "
            "it. Every operation is reached through `Port.invoke`, which binds "
            "first; a direct call bypasses the one place the project is stated.",
        )
    repo = _bound.get("host.repo")
    if repo.count("/") != 1:
        raise port.ConfigError(
            "host.repo",
            f"is `{repo}`, which is not `owner/name`. Plain issues live in one "
            "repository and every call here addresses it by that pair, so a URL "
            "or a bare name has no reading this tracker could act on.",
        )
    return repo


def _subprocess_gh(args: list[str], parse: bool):
    """One host call. Every failure comes back as the contract's own exception.

    ⛔ `port.HostUnavailable` rather than a class of this module's: the port
    turns it into a `failed` outcome, and a role must be able to tell a broken
    call from a missing capability without knowing which tracker answered. The
    command is in every message, so a failure is reproducible by hand.
    """
    shown = "gh " + " ".join(args)
    try:
        done = subprocess.run(
            ["gh"] + args, capture_output=True, text=True, timeout=30, check=True
        )
    except FileNotFoundError:
        raise port.HostUnavailable(f"`gh` is not on PATH, so `{shown}` could not run") from None
    except subprocess.TimeoutExpired:
        raise port.HostUnavailable(f"`{shown}` timed out after 30s") from None
    except subprocess.CalledProcessError as error:
        raise port.HostUnavailable(
            f"`{shown}` failed: {error.stderr.strip() or 'no stderr'}"
        ) from None
    if not parse:
        return done.stdout.strip()
    # ⚠️ An empty body is refused rather than parsed to `None`. It used to become
    # `null`, and the next `.get` on it raised an `AttributeError` -- a traceback
    # where a verdict belongs, from the one path meant to report cleanly.
    if not done.stdout.strip():
        raise port.HostUnavailable(f"`{shown}` answered with nothing where a body was expected")
    # ⛔ And a body that is not one document is refused here too, for the reason
    # `_code_host_dependency.blockers_of` states.
    try:
        return json.loads(done.stdout)
    except ValueError as error:
        raise port.HostUnavailable(
            f"`{shown}` answered something that is not one JSON document "
            f"({error}). An unreadable answer is not the same as a clean one."
        ) from None


# The named seam, as the implementations after this one have. ⚠️ Added later than
# they were, and the reason is the suite beside this module: the refusals above
# are this function's own, and a suite that substitutes `_gh` replaces the thing
# that raises them. With the seam, they are reachable.
TRANSPORT = _subprocess_gh


def _gh(args: list[str], *, parse: bool = True):
    return TRANSPORT(args, parse)


# --- the operations ---------------------------------------------------------
#
# Each takes what a role already has and returns what a role can carry onward.
# None of them reads a capability: being here *is* the declaration (§ 3).


def read_item(number: int) -> dict:
    """The item's own facts, in one call.

    ⛔ **Guarded against a pull request number.** Issues and pull requests share
    one number sequence on this host, and the issue lookup *answers for a pull
    request* rather than refusing: measured on this repository, asking for item
    111 returned pull request 111 with `state: MERGED`. Every operation here that
    **calls the host** resolves its number through this function, which is what
    makes one guard cover all of them; the two that make no call are named as
    such where they are defined. The writes among them are why: the alternative
    was a comment posted on a pull request and a dependency relation recorded
    against one, neither of them erroring.

    The `url` path is what separates the two; the state word cannot, because a
    reopened pull request and an open issue both read `OPEN`. ⚠️ An answer
    carrying no `url` is refused rather than passed: the absent signal used to
    read as *not a pull request*, which is the green answer from the one guard
    everything else leans on.

    ⛔ **And the argument has to be a number before it reaches the client**, which
    is the sibling kind's refusal for the sibling kind's reason and one more of
    this one's own: the client documents its argument as a number *or a URL*, and
    a URL names its own repository and wins over `--repo`. So an argument that is
    not a number had this function validating an item in another repository while
    every write below addressed the configured one -- the two halves of a call
    addressing different things, which is the defect the answer's own number was
    normalised against.
    """
    # ⚠️ Decimal digits, for the reason the sibling kind's guard states: a
    # superscript answers `isdigit` and then raises in `int`.
    # ⚠️ Positive, for `item_number`'s own reason. A negative reaches the client
    # as a flag rather than an argument.
    addressed = number if isinstance(number, int) and not isinstance(number, bool) else None
    if addressed is None and isinstance(number, str) and number.isdecimal():
        addressed = int(number)
    if addressed is not None and addressed <= 0:
        addressed = None
    if addressed is None:
        raise port.ConfigError(
            "tracker.operations.read_item",
            f"was handed {number!r}, which is not an item number. This tracker "
            "numbers its items, and the client would read an address of another "
            "shape as naming a repository of its own -- so it is refused here "
            "rather than answering about an item nobody asked for.",
        )
    item = _gh([
        "issue", "view", str(addressed), "--repo", _repo(),
        "--json", "number,title,body,state,labels,assignees,url",
    ])
    # ⚠️ A bool is an `int`, so the arm says so: `true` in that field passed a
    # type test and propagated as this item's identifier, into every path and
    # every write composed from it.
    answered = item.get("number")
    if not isinstance(answered, int) or isinstance(answered, bool) \
            or answered <= 0:
        raise port.HostUnavailable(
            f"`gh issue view {addressed}` answered with no number, so what it "
            "answered for could not be established. Every operation here that "
            "calls the host reads its own identifier back off this answer, and a "
            "subscript on a missing one is the traceback § 3 states an outcome "
            "instead of."
        )
    url = item.get("url")
    if not url:
        raise port.HostUnavailable(
            f"`gh issue view {addressed}` answered with no `url`, so whether "
            f"#{addressed} is an item or a pull request cannot be told. An "
            "unreadable answer is not the same as a clean one."
        )
    if "/pull/" in url:
        raise port.HostUnavailable(
            f"`gh issue view {addressed}` answered with pull request #{addressed} "
            f"({url}), not a work item -- the host numbers both in one sequence. "
            "A role holding a pull request number has the wrong identifier, which "
            "is a different fault from an item that does not exist."
        )
    return item


def _label_exists(repo: str, label: str) -> bool:
    """Whether the repository has this label, asked for by name.

    ⛔ Not `_gh`, because the interesting answer here is a **failure**: the host's
    `404` is what *absent* looks like, and `_gh` turns every non-zero exit into
    the same refusal. So the three cases are separated here -- present, absent,
    and could-not-be-established -- and only the third raises.
    """
    done = subprocess.run(
        ["gh", "api", f"repos/{repo}/labels/{label}", "--jq", ".name"],
        capture_output=True, text=True, timeout=30,
    )
    if done.returncode == 0:
        return True
    # ⚠️ Measured: the host's own body lands on stdout and `gh` writes `(HTTP 404)`
    # to stderr, so this matches the latter rather than hunting `404` anywhere in
    # either -- a digit sequence in an unrelated message would otherwise read as
    # *absent*, which is the reading that invents an answer.
    if NOT_FOUND in done.stderr:
        return False
    raise port.HostUnavailable(
        f"`gh api repos/{repo}/labels/{label}` failed with neither a label nor a "
        f"`404`: {done.stderr.strip() or 'no stderr'}. Whether this repository has "
        "that label could not be established, which is not the same as it not "
        "having it."
    )


def search_items(
    terms: str | None = None, *, labels: list[str] | None = None, limit: int = 100
) -> dict:
    """The items a query matches, in both shapes § 3 states, across both states.

    **Terms, or a field's value with no terms at all, or both.** Plain issues
    have one field worth filtering on -- the labels classification rides -- so
    the keyword-independent layer of the duplicate check filters by those and
    falls back to recency where it has none.

    ⛔ **No state argument, by construction.** § 3 states the operation across
    every state the tracker holds and the filing role is forbidden from
    narrowing, so `--state all` is not a default here but the only thing this
    passes; there is no parameter to get wrong. The one way state could still be
    narrowed is a qualifier smuggled in with the terms, which `STATE_QUALIFIER`
    refuses.

    ⚠️ **No pull-request guard, and that is measured rather than assumed.**
    Every other read here needs one because the two share a number sequence, but
    the host's *issue search* excludes pull requests: searching the exact title
    of pull request #120 answers with nothing, while the same terms through the
    pull-request listing answer with #120. So there is no shape here in which a
    pull request can arrive dressed as an item, and a guard would be asserting
    something this operation cannot be handed.

    ⛔ **An unknown label is refused, not answered with an empty list.** The host
    answers `[]` for a label that does not exist and `[]` for a label nothing
    carries, with exit 0 and no warning in either -- and this is the one search
    the filing role performs, so the two readings are a duplicate check that
    found nothing and a duplicate check that never ran. The labels are only
    checked where the answer *is* empty: a hit proves the label exists and spends
    no call proving it.

    ⚠️ **Each label is asked for by name rather than looked up in a listing.** A
    listing takes a bound, and a label past that bound comes back absent from an
    answer that reports no truncation -- so the guard would call a label the
    repository *has* unknown and refuse a search that was fine. Measured by
    shrinking the bound, which is what a repository with more labels than the
    bound does by itself. ⛔ And three answers, not two: present, absent by the
    host's own `404`, and **unestablished**, which is reported as a failure rather
    than folded into either.

    The answer carries its own bound, because the layer that uses it is required
    to report one. ⚠️ `at_limit` says the host had at least this many, never that
    it had more -- a result that exactly fills the bound is indistinguishable
    from one the bound cut, and the honest reading of it is *this answer may be
    short*.

    Items come back in the host's own field names, the ones `read_item` returns,
    so a candidate moves from this answer into that one with nothing renamed.
    `body` is **not** among them: judging a candidate means reading its body, and
    that is a `read_item` per candidate rather than a list call pulling every
    body in the backlog.
    """
    repo = _repo()
    query = (terms or "").strip()
    if query and STATE_QUALIFIER.search(query):
        raise port.ConfigError(
            "tracker.operations.search_items",
            f"was asked for `{query}`, whose state qualifier would narrow the "
            "search to one state. The operation is stated across every state the "
            "tracker holds -- a closed item answers the duplicate question as "
            "well as an open one, and an idea raised and dropped is the duplicate "
            "most worth finding. Drop the qualifier; the states are already all "
            "of them.",
        )
    args = [
        "issue", "list", "--repo", repo,
        "--state", "all",
        "--limit", str(limit),
        "--json", "number,title,state,labels,updatedAt,url",
    ]
    for label in labels or []:
        args += ["--label", label]
    args += ["--search", query or RECENT_FIRST]
    items = _gh(args)
    if labels and not items:
        unknown = [label for label in labels if not _label_exists(repo, label)]
        if unknown:
            raise port.HostUnavailable(
                f"`gh issue list --label {' --label '.join(labels)}` answered with "
                f"nothing, and {', '.join(repr(label) for label in unknown)} is not "
                f"a label {repo} has -- so the empty answer is this search never "
                "running, not this tracker holding no such item."
            )
    return {
        # ⚠️ The query as **sent**, not as handed in: the filing role records every
        # query against its hit count, and a record of the unstripped argument is a
        # record of something the host was never asked.
        "terms": query or RECENT_FIRST,
        "labels": list(labels or []),
        "limit": limit,
        "at_limit": len(items) >= limit,
        "items": items,
    }


def create_item(title: str, body: str, labels: list[str] | None = None) -> dict:
    """A new item, from the body the filing role wrote.

    Labels go on at creation -- one call, unlike the tracker that cannot set them
    until the card exists. The number is taken from the URL the host returns and
    the item is then read back, so what a role carries onward is the same shape
    `read_item` gives it and `item_number` can read either.
    """
    args = ["issue", "create", "--repo", _repo(), "--title", title, "--body", body]
    for label in labels or []:
        args += ["--label", label]
    url = _gh(args, parse=False)
    tail = url.rstrip("/").rsplit("/", 1)[-1]
    if not tail.isdecimal() or int(tail) <= 0:
        # A keyed refusal rather than a bare `ValueError` out of `int()`: the
        # host answered, so this is its answer not matching its documented shape.
        raise port.HostUnavailable(
            f"`gh issue create` answered `{url!r}`, whose last path segment is not "
            "a number, so the created item cannot be addressed."
        )
    return read_item(int(tail))


def item_number(item: dict | int | str, *, operation: str = "item_number") -> int:
    """The identifier the branch name and the pull request carry.

    ⚠️ Makes **no host call**, so the pull-request guard does not apply: an
    `int` is returned as given. A role that hands this a pull request number gets
    it back, which is correct -- the operation reads an identifier out of what it
    was given and never asserts the thing exists.

    Plain issues have a short number and it is the same one everywhere, so there
    is no URL to parse for want of a short-id field.

    ⛔ **A string is one of the shapes this is handed**, the port passing every
    value from an invocation as text. The first form subscripted anything that was
    not an `int`, so the ordinary CLI shape came back as a `TypeError` -- a
    traceback from the one operation that cannot fail for any other reason.
    """
    # ⛔ Positive, because this host numbers from one, which the shared
    # dependency grammar's own arm reads them for: `#0` and a negative name no
    # item, and `link_for_close` below would compose a reference out of either.
    # ⚠️ A mapping only where it carries a number this can read: the first form
    # subscripted every one of them, so an item answering no `number` arrived as
    # a `KeyError` and one answering a word as a `ValueError` -- the traceback the
    # arms above were given a refusal for, from the same operation.
    for handed in (item, item.get("number") if isinstance(item, dict) else None):
        if isinstance(handed, int) and not isinstance(handed, bool) and handed > 0:
            return handed
        if isinstance(handed, str) and handed.strip().isdecimal() \
                and int(handed.strip()) > 0:
            return int(handed.strip())
    raise port.ConfigError(
        f"tracker.operations.{operation}",
        f"was handed {item!r}, which carries no item number. This operation reads "
        "an identifier out of what it was given and makes no call, so there is "
        "nothing to resolve a value of another shape against.",
    )


def set_state(number: int, *, status: str) -> dict:
    """Write one of the host's two states.

    ⚠️ `status` is the **status word the port resolved from the role it was
    asked for** (§ 4.2) -- a role never names it and this adapter never guesses
    it. A word that is neither of the two is a configuration this tracker cannot
    hold, refused with the key named rather than coerced to the nearer state.
    """
    # ⛔ Refused before anything is read or written. A word this tracker has no
    # room for is a defect in the text, not a value to coerce to the nearer
    # state, and checking it first keeps a mis-mapped project from spending a
    # host call to find out.
    if status not in (OPEN, CLOSED):
        raise port.ConfigError(
            "statuses",
            f"names `{status}`, which plain issues cannot hold: an issue is "
            f"`{OPEN}` or `{CLOSED}` and there is no status field to carry a "
            "third word. Map the roles this project needs onto those two, or "
            "state a tracker that has more states.",
        )
    # ⛔ Idempotent, by reading before writing -- which is also the pull-request
    # guard for this operation. The host's two verbs are transitions rather than
    # assignments: closing a closed item and reopening an open one both **fail**,
    # so a role advancing to a role the item already holds would get a failure
    # for something that had in fact already happened.
    item = read_item(number)
    if item["state"].lower() == status:
        return item
    verb = "close" if status == CLOSED else "reopen"
    _gh(["issue", verb, str(item["number"]), "--repo", _repo()], parse=False)
    return read_item(item["number"])


def comment(number: int, body: str) -> dict:
    """A note on the item -- a gate result being the measured case.

    Read first, so the pull-request guard covers this too: a comment is a write,
    and posting one on a pull request because the numbers share a sequence is the
    failure the guard exists for.
    """
    item = read_item(number)
    _gh(
        ["issue", "comment", str(item["number"]), "--repo", _repo(), "--body", body],
        parse=False,
    )
    return {"number": item["number"], "url": item["url"], "commented": True}


def set_labels(number: int, labels: list[str]) -> dict:
    """Every label in one call, so there is no partial set to report.

    ⛔ **Set, not add.** The host's verbs are `--add-label` and
    `--remove-label`, so adding alone would leave whatever was already there and
    `set_labels(n, ["a"])` on an item labelled `b` would answer `[a, b]` -- a
    role asking for a set and getting a union. Both verbs go in **one** `gh`
    call, which is what the operation asks for and what keeps a partial set from
    existing at all: there is no window in which the additions have landed and
    the removals have not.
    """
    wanted = set(labels)
    item = read_item(number)
    current = {label["name"] for label in item["labels"]}
    if wanted == current:
        return item
    args = ["issue", "edit", str(item["number"]), "--repo", _repo()]
    for label in sorted(wanted - current):
        args += ["--add-label", label]
    for label in sorted(current - wanted):
        args += ["--remove-label", label]
    _gh(args, parse=False)
    return read_item(item["number"])


def assign(number: int, who: str = "@me") -> dict:
    """The item assigned to the person the role acts for.

    ⚠️ This says *taken* and nothing more. Where every session authenticates as
    one account it cannot say **which** session holds the item, so a claim does
    not rest on it -- that is #70's, and `assign`'s own stated fallback says as
    much.

    ⛔ **Read first, like every other write here.** This was the one operation
    that wrote before it read, so neither the pull-request guard nor the argument
    guard covered it: an argument the client reads as naming its own repository
    had the assignment land there, and the read that would have refused it ran
    afterwards.
    """
    item = read_item(number)
    _gh(
        ["issue", "edit", str(item["number"]), "--repo", _repo(), "--add-assignee", who],
        parse=False,
    )
    return read_item(item["number"])


def link_dependency(blocked: int, blocked_by: int) -> dict:
    """One item recorded as blocked by another, as a relation.

    Two measured properties, both easy to get backwards:

    - the call is posted on the **blocked** item, not on the blocker;
    - its body carries the blocker's **internal id**, not its number. The two
      are different integers and the wrong one either errors or, worse,
      addresses an unrelated issue.

    ⚠️ The relation bumps neither item's `updated_at`, so nothing that polls for
    modified issues can see it afterwards. That is why the close-out role reads
    the graph in full rather than asking what changed.

    ⛔ **Both numbers go through `read_item` first.** The id lookup below uses the
    REST issues endpoint, which answers for pull requests too, so without this a
    pull request number recorded a real relation against a pull request and
    returned as though it had worked. This is a write, and it was the worst of
    the two the guard was missing.
    """
    repo = _repo()
    # ⛔ The numbers in the answer are the host's and never the arguments, for
    # `read_blockers`'s reason one function down: the port passes every value
    # from an invocation as text, and the two guard reads already hold the
    # host's own integers.
    blocked_item, blocker_item = read_item(blocked), read_item(blocked_by)
    blocker_id = _gh(
        ["api", relation.issue_path(repo, blocker_item["number"]), "--jq", ".id"],
        parse=False,
    )
    _gh([
        "api", "--method", "POST",
        relation.blocked_by_path(repo, blocked_item["number"]),
        "-F", f"issue_id={blocker_id}",
    ])
    return {
        "blocked": blocked_item["number"],
        "blocked_by": blocker_item["number"],
        "blocker_id": int(blocker_id),
    }


def read_blockers(number: int) -> dict:
    """The items this one is recorded as blocked by, each with its own state.

    The read half of `link_dependency`, on the same endpoint and the same object:
    a relation is posted on the **blocked** item, so this reads that item's own
    dependencies rather than searching for what points at it.

    ⛔ **Every page, not the first one**, for the reason
    `_code_host_dependency.blockers_of` states.

    ⚠️ **Read through `read_item` first**, so the pull-request guard covers this
    too: the path is the issues one, which answers for a pull request as well, and
    a blocker list read off a pull request is an answer about the wrong object.

    ⚠️ An empty answer is an item with no recorded blocker, which is a real
    answer here -- the capability is present. A tracker that *cannot* be asked is
    the absent case, and the port reports that rather than this.

    ⛔ The address and the shape of one entry come from the module the board's
    implementation shares with this one: both kinds reach the same host, and two
    copies of one grammar are two statements allowed to disagree.

    ⛔ **The number in the answer is the host's and never the argument.** The
    port passes every value from an invocation as text, so echoing the argument
    put a string beside blocker entries carrying integers -- one answer, two types
    for one field name, and a consumer keying a dict on either mismatches in
    silence. ⚠️ The guard read above already holds the host's own integer, so this
    costs no call.
    """
    item = read_item(number)
    # ⚠️ The path takes the host's own number too, not the argument: the guard
    # read above normalises one and leaving the other raw had the two halves of
    # one call addressing different things.
    path = relation.blocked_by_path(_repo(), item["number"])
    return {
        "number": item["number"],
        "blockers": relation.blockers_of(_gh(["api", "--paginate", path]), path),
    }


def link_for_close(number: int) -> str:
    """The reference that closes the item when the branch lands.

    Declarative: the text goes in the pull request body and the host does the
    rest on merge. Returned rather than written, because the body belongs to the
    role opening the pull request and this adapter has no business composing it.

    ⚠️ Makes **no host call**, so the pull-request guard does not apply here
    either -- this composes a string out of the number it was given and asserts
    nothing about what that number names.

    ⛔ **The number is held to a decimal integer anyway**, which is the one thing
    this can get wrong silently: every other operation's bad argument comes back
    as a refusal from the host, while this one composes a reference the host will
    never resolve and nothing reports that it did not. ⚠️ Measured on a non-ASCII
    decimal digit, which `isdecimal` admits and the host does not.
    """
    return f"Closes #{item_number(number, operation='link_for_close')}"


# What closed an item, and whether that thing merged. ⚠️ The state word alone
# cannot answer this: measured on a probe item closed by hand, reading only the
# state reported the host's automation as having fired when nothing had merged.
# `includeClosedPrs` is needed because a pull request that closed an item is
# itself closed by then.
CLOSED_BY_QUERY = """
query($owner:String!, $name:String!, $number:Int!) {
  repository(owner:$owner, name:$name) {
    issue(number:$number) {
      state
      closedByPullRequestsReferences(first:10, includeClosedPrs:true) {
        nodes { number merged mergeCommit { oid } }
      }
    }
  }
}
"""


def advance_on_merge(number: int) -> dict:
    """Whether the host's own automation moved the item off a merge.

    A confirmation and not an assertion: the capability being present means the
    procedure does **not** call `set_state` itself, and the only honest way to
    report that is to ask the host what happened. `advanced: false` is a real
    answer -- the closing reference was missing from the body, or the pull
    request was closed rather than merged -- and it is one a role can act on,
    which a no-op declaration would have hidden.

    ⛔ **Closed is not advanced.** The move is reported only where a pull request
    that closed this item actually merged, and `merged_by` names it. An item
    somebody closed by hand is `advanced: false` with `state: CLOSED`, which is
    the answer a role needs: the item is off the board, and the automation this
    capability claims did not do it.
    """
    repo = _repo()
    # Read first, so this operation is guarded too. The query below addresses
    # `issue(number:)`, which answers null for a pull request rather than
    # refusing, and null is indistinguishable here from an item that is not
    # there -- so the clearer refusal has to come from the guard.
    # ⛔ And the number the query and the answer carry is the **host's**, read off
    # that guard's own answer rather than taken from the argument: the port passes
    # every value as text, and a typed GraphQL variable built from the argument is
    # the half of one call that disagrees with the other.
    addressed = read_item(number)["number"]
    owner, name = repo.split("/")
    issue = _gh([
        "api", "graphql", "-f", f"query={CLOSED_BY_QUERY}",
        "-f", f"owner={owner}", "-f", f"name={name}", "-F", f"number={addressed}",
    ])["data"]["repository"]["issue"]
    if issue is None:
        raise port.HostUnavailable(
            f"`gh api graphql` (closedByPullRequestsReferences) answered null for "
            f"#{addressed} in {repo}, so what closed it could not be read."
        )
    merged = [
        node for node in issue["closedByPullRequestsReferences"]["nodes"] if node["merged"]
    ]
    return {
        "number": addressed,
        "advanced": issue["state"].lower() == CLOSED and bool(merged),
        "state": issue["state"],
        "merged_by": [
            {"pull_request": node["number"], "commit": (node["mergeCommit"] or {}).get("oid")}
            for node in merged
        ],
    }


def self_test() -> int:
    """This implementation's suite, which lives in the module beside it.

    ⛔ **Scoped to the relation between two work items, and the scope is printed
    by every run** rather than left in a docstring: this module had no suite at
    all until those operations landed, and a suite that exists reads as a module
    that is held. What the rest of it is held by is still the port's own contract
    and a reader, and the run says so in both directions.

    ⚠️ The suite's module name opens with `_`, which is what keeps discovery from
    reading it as an implementation that names no kind.
    """
    from adapters import _github_issues_suite as suite

    return suite.self_test()


ADAPTER = port.Adapter(binder=bind, operations={
    "read_item": read_item,
    "search_items": search_items,
    "create_item": create_item,
    "item_number": item_number,
    "set_state": set_state,
    "comment": comment,
    "set_labels": set_labels,
    "assign": assign,
    "link_dependency": link_dependency,
    "read_blockers": read_blockers,
    "link_for_close": link_for_close,
    "advance_on_merge": advance_on_merge,
    # ⛔ The operations this tracker has nothing to implement against are named
    # once, below, and read from there by the suite.
})

# The ones absent because the tracker has nothing to implement them against, each
# with its reason:
#
#   * the checklist operations, because plain issues have no check-item
#     object at all -- a task list is markdown inside the body, which is precisely
#     what `checklist_write`'s stated fallback already says to do, so implementing
#     them against body text would dress the fallback up as a capability and cost
#     a role the knowledge that it is reading prose;
#   * `set_field`, for the same kind of reason one object up: an issue here has no
#     field of its own to write, and what another tracker keeps in a field -- an
#     estimate, a date, a code root -- reaches a plain issue as a label or as body
#     text, which is that operation's own stated fallback.
#
# ⛔ Written once, here, and read by the suite rather than restated in it: one more
# absence would otherwise be an operation nobody noticed going missing -- which is
# exactly what happened to `set_field`, absent while the docstring said *except
# the checklist ones*.
DELIBERATELY_ABSENT = (
    "set_field",
    "checklist_read",
    "checklist_write",
    "checklist_item_delete",
)
