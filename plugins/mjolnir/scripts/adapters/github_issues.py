#!/usr/bin/env python3
"""Plain GitHub issues behind the port: no board, no status field, no `in_flight`.

The cheapest real tracker there is, and what a new adopter has on their first
day. It is also what this repository runs on, which is the whole reason this
adapter exists first: a surface nothing stands on is a surface whose holes are
nobody's problem.

What it implements, and what it deliberately does not:

  * **Ten of the thirteen operations** § 3 states. The three it leaves alone are
    the checklist ones, and that absence is a fact about the tracker rather than
    a shortcut here -- plain issues have no check-item object at all. A task list
    is markdown inside the body, which is *precisely* what `checklist_write`'s
    stated fallback already says to do, so implementing them against body text
    would dress the fallback up as a capability and cost a role the knowledge
    that it is reading prose.
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
  * **`advance_on_merge` confirms rather than asserts.** The host's own
    automation closes an issue when a pull request carrying a closing reference
    merges, so the capability is present and the procedure does not make the
    move itself. The callable therefore *reads the item back* and reports
    whether the host actually did it -- a declaration nothing can observe would
    leave a role unable to tell automation that worked from automation that was
    never wired.

Every call goes through `gh`, which holds the credential and the host's base URL,
so an enterprise host needs no key here.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config  # noqa: E402
import port  # noqa: E402

KIND = "github-issues"

# The two states plain issues have. Written here because they are the host's
# vocabulary rather than the project's: a `statuses` list is free to choose which
# of them it maps and to which role (§ 4.2), and free to leave one out, but it
# cannot invent a third and have this tracker hold it.
OPEN = "open"
CLOSED = "closed"

# Resolved once per process. Several operations read the item back after writing
# it, so a single role call reaches `_repo()` three or four times, and each one
# was re-reading and re-validating the whole configuration from disk. A role's
# configuration does not change underneath it, so one read is the right number.
_cached_repo: str | None = None


class HostError(Exception):
    """The host did not answer.

    ⚠️ Deliberately **not** an absent capability. An absence is a stated
    decision that comes back as an `Outcome` naming its fallback; this is the
    network, the credential or the repository being wrong, and a role that
    treated the two alike would report a missing feature where it should report a
    broken call. The command is named in the message so the failure is
    reproducible by hand.
    """


def _repo() -> str:
    """The repository the configuration addresses, read once per call chain.

    ⛔ Read from the configuration rather than from the working tree's remote.
    A role runs in a worktree whose remote happens to agree today; `host.repo` is
    the statement the project actually made, and the two differing is exactly the
    case a fork or a mirror produces.
    """
    global _cached_repo
    if _cached_repo is not None:
        return _cached_repo
    configuration = config.load(os.environ.get("MJOLNIR_SKILLS_ROOT", "."))
    repo = configuration.get("host.repo")
    if not repo:
        raise config.ConfigError(
            "host.repo",
            "is not stated, so there is no repository to address the tracker "
            "against. Plain issues live in a repository: the tracker and the "
            "code host are the same system here, and this is the one key that "
            "says which one.",
        )
    _cached_repo = repo
    return repo


def _gh(args: list[str], *, parse: bool = True):
    try:
        done = subprocess.run(
            ["gh"] + args, capture_output=True, text=True, timeout=30, check=True
        )
    except FileNotFoundError:
        raise HostError(f"`gh` is not on PATH, so `gh {' '.join(args)}` could not run") from None
    except subprocess.TimeoutExpired:
        raise HostError(f"`gh {' '.join(args)}` timed out after 30s") from None
    except subprocess.CalledProcessError as error:
        raise HostError(
            f"`gh {' '.join(args)}` failed: {error.stderr.strip() or 'no stderr'}"
        ) from None
    if not parse:
        return done.stdout.strip()
    return json.loads(done.stdout or "null")


# --- the operations ---------------------------------------------------------
#
# Each takes what a role already has and returns what a role can carry onward.
# None of them reads a capability: being here *is* the declaration (§ 3).


def read_item(number: int) -> dict:
    """The item's own facts, in one call.

    ⛔ **Guarded against a pull request number.** Issues and pull requests share
    one number sequence on this host, and the issue lookup *answers for a pull
    request* rather than refusing: measured on this repository, asking for item
    111 returned pull request 111 with `state: MERGED`. Every operation in this
    module reads the item back, so without this guard a role that passed a pull
    request number would get a confident wrong answer from all of them --
    `advance_on_merge` worst of all, since a merged pull request is not a closed
    item and the state word is one the surface's `statuses` never contains.

    The `url` path is what separates them; the state word cannot, because a
    reopened pull request and an open issue both read `OPEN`.
    """
    item = _gh([
        "issue", "view", str(number), "--repo", _repo(),
        "--json", "number,title,body,state,labels,assignees,url",
    ])
    if "/pull/" in item.get("url", ""):
        raise HostError(
            f"#{number} is a pull request, not a work item -- the host numbers "
            "both in one sequence and answered the item lookup with the pull "
            f"request ({item['url']}). A role holding a pull request number has "
            "the wrong identifier, which is a different fault from an item that "
            "does not exist."
        )
    return item


def create_item(title: str, body: str, labels: list[str] | None = None) -> dict:
    """A new item, from the body the filing role wrote.

    Labels go on at creation -- one call, unlike the tracker that cannot set them
    until the card exists. The created item is read back rather than parsed out of
    the returned URL, so what a role carries onward is the same shape
    `read_item` gives it and `item_number` can read either.
    """
    args = ["issue", "create", "--repo", _repo(), "--title", title, "--body", body]
    for label in labels or []:
        args += ["--label", label]
    url = _gh(args, parse=False)
    return read_item(int(url.rstrip("/").rsplit("/", 1)[-1]))


def item_number(item: dict | int) -> int:
    """The identifier the branch name and the pull request carry.

    Plain issues have a short number and it is the same one everywhere -- no
    parsing a URL for want of a short-id field. An `int` is accepted so a role
    holding only the number it was given can ask without first reading the item.
    """
    return item if isinstance(item, int) else int(item["number"])


def set_state(number: int, *, status: str) -> dict:
    """Write one of the host's two states.

    ⚠️ `status` is the **status word the port resolved from the role it was
    asked for** (§ 4.2) -- a role never names it and this adapter never guesses
    it. A word that is neither of the two is a configuration this tracker cannot
    hold, refused with the key named rather than coerced to the nearer state.
    """
    if status in (OPEN, CLOSED):
        # ⛔ Idempotent, by reading before writing. The host's two verbs are
        # transitions rather than assignments: closing a closed item and
        # reopening an open one both **fail**, so a role advancing to a role the
        # item already holds would get a host error where the operation had in
        # fact already happened. A `set_` operation that cannot be asked twice
        # is one every caller has to guard, so it is guarded once, here.
        item = read_item(number)
        if item["state"].lower() == status:
            return item
    if status == CLOSED:
        _gh(["issue", "close", str(number), "--repo", _repo()], parse=False)
    elif status == OPEN:
        _gh(["issue", "reopen", str(number), "--repo", _repo()], parse=False)
    else:
        raise config.ConfigError(
            "statuses",
            f"names `{status}`, which plain issues cannot hold: an issue is "
            f"`{OPEN}` or `{CLOSED}` and there is no status field to carry a "
            "third word. Map the roles this project needs onto those two, or "
            "state a tracker that has more states.",
        )
    return read_item(number)


def comment(number: int, body: str) -> dict:
    """A note on the item -- one call, and a gate result is the measured case."""
    _gh(["issue", "comment", str(number), "--repo", _repo(), "--body", body], parse=False)
    return {"number": number, "commented": True}


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
    current = {label["name"] for label in read_item(number)["labels"]}
    if wanted == current:
        return read_item(number)
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
    one account it cannot say **which** session holds the item, so a claim does
    not rest on it -- that is #70's, and `assign`'s own stated fallback says as
    much.
    """
    _gh(["issue", "edit", str(number), "--repo", _repo(), "--add-assignee", who], parse=False)
    return read_item(number)


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
    """
    repo = _repo()
    blocker_id = _gh(["api", f"repos/{repo}/issues/{blocked_by}", "--jq", ".id"], parse=False)
    _gh([
        "api", "--method", "POST",
        f"repos/{repo}/issues/{blocked}/dependencies/blocked_by",
        "-F", f"issue_id={blocker_id}",
    ])
    return {"blocked": blocked, "blocked_by": blocked_by, "blocker_id": int(blocker_id)}


def link_for_close(number: int) -> str:
    """The reference that closes the item when the branch lands.

    Declarative: the text goes in the pull request body and the host does the
    rest on merge. Returned rather than written, because the body belongs to the
    role opening the pull request and this adapter has no business composing it.
    """
    return f"Closes #{number}"


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
    owner, name = _repo().split("/")
    issue = _gh([
        "api", "graphql", "-f", f"query={CLOSED_BY_QUERY}",
        "-f", f"owner={owner}", "-f", f"name={name}", "-F", f"number={number}",
    ])["data"]["repository"]["issue"]
    if issue is None:
        raise HostError(f"#{number} is not an item in {_repo()}")
    merged = [
        node for node in issue["closedByPullRequestsReferences"]["nodes"] if node["merged"]
    ]
    return {
        "number": number,
        "advanced": issue["state"].lower() == CLOSED and bool(merged),
        "state": issue["state"],
        "merged_by": [
            {"pull_request": node["number"], "commit": (node["mergeCommit"] or {}).get("oid")}
            for node in merged
        ],
    }


ADAPTER = port.Adapter({
    "read_item": read_item,
    "create_item": create_item,
    "item_number": item_number,
    "set_state": set_state,
    "comment": comment,
    "set_labels": set_labels,
    "assign": assign,
    "link_dependency": link_dependency,
    "link_for_close": link_for_close,
    "advance_on_merge": advance_on_merge,
    # ⛔ No `checklist_read`, `checklist_write` or `checklist_item_delete`. See
    # the module docstring: plain issues have no check-item object, and the three
    # stated fallbacks are already the right behaviour rather than a degradation.
})
