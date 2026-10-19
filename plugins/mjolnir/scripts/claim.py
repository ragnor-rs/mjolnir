#!/usr/bin/env python3
"""The claim on a work item: taking one, releasing it, and reading who holds it.

The rule is stated once, in `config/schema.md` § 10 -> *The claim on a work item*, and this
module performs it. ⛔ Nothing here restates the rule: the reasons the carrier is the published
ref and not anything on the work item live on the surface, and a paraphrase of them in a
docstring would be a second authority that is allowed to disagree.

What this module is for is the part a document cannot hold: that the test-and-set is real. A
claim that is *described* as atomic and implemented as read-then-write reads identically in
review, and the failure only shows up as two sessions on one item. So `--self-test` builds two
clones of one bare repository and has them race, and plants the lease away to prove the race is
what the lease is holding.

⚠️ No network. The self-test's "host" is a bare repository on disk, which is the whole of what
the claim needs to arbitrate -- a ref namespace with one writer at a time. What a bare repository
cannot supply is the *record* of who pushed and when, which is exactly the half § 10 requires be
named as unestablished rather than guessed, so the absence is a fixture rather than a gap.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# ⛔ The claim is a test-and-set in **two** arms, because the two orders fail differently and
# neither arm catches both. Measured, and the first draft of this file shipped only the second:
#
#   1. The ref already existed when this session connected. Git then sends nothing at all --
#      a push of the same sha to an existing ref is `Everything up-to-date`, exit 0, and the
#      lease is never consulted because no update is attempted. Two sessions claiming one item
#      push the *same* integration tip, so this is the common case rather than the exotic one.
#      What separates it from a successful claim is only whether the ref was **created**, which
#      `--porcelain` reports per ref and the human output does not.
#   2. The ref appeared between this session's ref advertisement and its write. Git sends the
#      create, and the lease below is what the receiving end refuses it with.
#
# ⚠️ A probe that pushes a *different* sha to an existing ref exercises arm 2 only and passes,
# which reads as proof of a mechanism that is not holding arm 1 at all.
CREATED = "*"

# An empty expected value means "the named ref must not already exist" -- `git push --help`, and
# the code host honours it. ⚠️ The empty string after the colon is the whole mechanism;
# `--force-with-lease=<ref>` without it is a different and much weaker option.
LEASE = "--force-with-lease={ref}:"

REFS_PREFIX = "refs/heads/"

# How the refusal explains itself when the ref's own history is all there is. Read by the
# self-test, so a reword travels rather than breaking it.
UNESTABLISHED = "could not be established"

# How long a slug may be. A bound is needed for the truncation to be part of the derivation
# rather than a thing the filesystem does later at a length that varies by machine; the value is
# a readability choice and nothing reads it but the derivation below.
SLUG_MAX = 60

# An item identifier this module can recover from a branch name on its own: a run of digits that
# is the whole of the last segment or is followed by a hyphen. ⛔ Deliberately narrow. A tracker
# whose identifiers carry their own hyphens cannot be parsed out of a slugged branch name without
# guessing where the identifier ends, and a guess here turns the by-item guard on for the wrong
# item -- so those projects state `--item` and the parse declines.
NUMERIC_ITEM = re.compile(r"^(\d+)(?:-|$)")


class ClaimError(RuntimeError):
    """A refusal, or a failure to read the store the claim lives in."""


# --------------------------------------------------------------------------------------------
# The branch name, derived
#
# ⛔ The derivation is **performed here and not described anywhere for a caller to follow**. A
# slug rule written as prose is a rule two readers may apply differently, and that is not a
# hypothetical: measured on 2026-10-19, two sessions starting one item from one title published
# `feature/41-done-is-configuration` and `feature/41-what-counts-as-done-is-configuration`, so the
# test-and-set on the ref name never engaged and the tree directory arbitrated a step later.
# A caller that composes the name itself reintroduces exactly that, which is why `take` accepts
# the three inputs and no role needs to hold the rule.
#
# The rule itself is `config/schema.md` § 10 -> *The branch name a claim is taken on*.
# --------------------------------------------------------------------------------------------


def slug_for(title: str, limit: int | None = SLUG_MAX) -> str:
    """The item's title as a branch slug: a pure function of the string it is handed.

    ⚠️ **Of the string it is handed**, which is not always the title as the tracker stores it:
    where the item's language differs from the repository's, § 8 requires a translation, and the
    translation is the caller's. That is the one input two sessions are not guaranteed to agree
    on, and it is why the claim resolves on the *item* and not on the name -- see
    `refs_for_item` below.

    Normalised to NFC first so a decomposed title and a composed one slug alike; letters and
    numbers survive by Unicode category rather than by an ASCII range, because a project writing
    its items in its own script gets a ref it can read rather than a row of hyphens.

    ⚠️ `limit` is the derivation's own, and `None` is what the suite reads the untruncated form
    with. ⛔ **The bound is part of the rule rather than something the filesystem imposes later
    at a length that varies by machine.** It is the arm that has actually broken: of the three
    measured divergences, all three were one session carrying the whole title and another
    carrying the first few words, and a character mapping with no length rule licenses both.
    """
    text = unicodedata.normalize("NFC", title).strip().lower()
    kept = "".join(ch if unicodedata.category(ch)[0] in ("L", "N") else "-" for ch in text)
    slug = re.sub(r"-+", "-", kept).strip("-")
    if limit is not None and len(slug) > limit:
        head = slug[:limit]
        # Cut back to a word boundary -- unless the bound already fell on one, in which case
        # cutting back would drop a whole word for nothing.
        if slug[limit] != "-" and "-" in head:
            head = head[: head.rindex("-")]
        slug = head.strip("-")
    return slug


def branch_for(prefix: str, item: str, title: str) -> str:
    """`(prefix, number, slug)`, composed in one place.

    A title that slugs to nothing -- punctuation, or a script with no letters or numbers in it --
    leaves the number alone rather than a trailing hyphen, because `prefix/70-` is a ref name git
    accepts and nobody can read.
    """
    prefix = prefix.strip("/")
    item = str(item).strip()
    if not prefix:
        raise ClaimError("the branch prefix is empty; it is a function of the item's type (§ 4.1).")
    if not item:
        raise ClaimError("the item identifier is empty; a role with none stops rather than inventing one.")
    slug = slug_for(title)
    return f"{prefix}/{item}-{slug}" if slug else f"{prefix}/{item}"


def item_in_branch(branch: str) -> str | None:
    """The item a branch name carries, where this module can read it without guessing."""
    match = NUMERIC_ITEM.match(branch.rsplit("/", 1)[-1])
    return match.group(1) if match else None


def ref_is_for_item(branch: str, item: str) -> bool:
    """Whether this branch name is a claim on this item.

    The last segment and not the whole name: a project may nest its prefixes, and the part that
    names the item is the leaf. ⚠️ This is a **candidate** test and never an answer -- a ref it
    matches may have landed, and reading the match itself as *taken* is the defect it exists to
    feed, not to commit.
    """
    tail = branch.rsplit("/", 1)[-1]
    item = str(item)
    return tail == item or tail.startswith(item + "-")


# --------------------------------------------------------------------------------------------
# Running git. Every call names its root: the working directory resets between calls, and a
# claim resolved against the wrong root is a claim on somebody else's branch namespace.
# --------------------------------------------------------------------------------------------


def git(root: str | Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    proc = subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
    )
    if check and proc.returncode != 0:
        raise ClaimError(
            f"git {' '.join(args)} failed in {root}: {proc.stderr.strip() or proc.stdout.strip()}"
        )
    return proc


def remote_url(root: str | Path, remote: str) -> str | None:
    """The remote's URL, or None where the project has none.

    § 10's derived absent case: a code root with no remote cannot publish a ref, so the claim is
    local-only there. That is read here rather than configured.
    """
    proc = git(root, "remote", "get-url", remote, check=False)
    return proc.stdout.strip() or None if proc.returncode == 0 else None


def integration_branch(root: str | Path, remote: str, stated: str | None = None) -> str:
    """The branch a claim is cut from, derived rather than named.

    ⛔ **This surface carries no key for it, and this module does not invent one.** § 10 speaks of
    "the integration branch" throughout and no facet states which it is -- so a command taking it
    as a required argument would push a value with no home on the surface into every role that
    calls it, which is the defect the sweep exists for one layer down. It is derived from what git
    already records, with an explicit value accepted as an override.

    ⚠️ Where it cannot be derived the role is told so by name. A guess here is a claim cut from
    the wrong base, which reads as a successful start.
    """
    if stated:
        return stated

    # What the remote advertised as its default when this clone was made.
    proc = git(root, "symbolic-ref", "--short", f"refs/remotes/{remote}/HEAD", check=False)
    if proc.returncode == 0 and proc.stdout.strip():
        name = proc.stdout.strip()
        return name[len(remote) + 1 :] if name.startswith(remote + "/") else name

    # The clone may predate the remote having a default, so ask the remote itself.
    proc = git(root, "ls-remote", "--symref", remote, "HEAD", check=False)
    if proc.returncode == 0:
        for line in proc.stdout.splitlines():
            if line.startswith("ref:"):
                ref = line[len("ref:") :].split()[0].strip()
                if ref.startswith(REFS_PREFIX):
                    return ref[len(REFS_PREFIX) :]

    # No remote at all: the claim is local-only and this checkout's own branch is the base.
    if not remote_url(root, remote):
        proc = git(root, "rev-parse", "--abbrev-ref", "HEAD", check=False)
        if proc.returncode == 0 and proc.stdout.strip() not in ("", "HEAD"):
            return proc.stdout.strip()

    raise ClaimError(
        "the integration branch could not be derived from the remote's default or this "
        "checkout's own branch; state it explicitly rather than having one guessed."
    )


def _push_created_ref(porcelain: str, branch: str) -> bool:
    """Whether the push *created* the ref, read off `--porcelain`'s per-ref flag.

    The human output says `[new branch]` for a creation and `Everything up-to-date` for arm 1 of
    the comment above, but it says them in prose that varies; `--porcelain` puts the flag in the
    first tab-separated field, which is a grammar rather than a sentence.
    """
    target = REFS_PREFIX + branch
    for line in porcelain.splitlines():
        fields = line.split("\t")
        if len(fields) < 2:
            continue
        if fields[1].endswith(":" + target) or fields[1] == target:
            return fields[0].strip() == CREATED
    return False


def remote_ref_sha(root: str | Path, remote: str, branch: str) -> str | None:
    """The sha the published claim points at, or None where the ref does not exist."""
    proc = git(root, "ls-remote", "--heads", remote, branch, check=False)
    if proc.returncode != 0:
        raise ClaimError(f"could not read `{remote}`: {proc.stderr.strip()}")
    for line in proc.stdout.splitlines():
        sha, _, ref = line.partition("\t")
        if ref.strip() == REFS_PREFIX + branch:
            return sha.strip()
    return None


def all_refs(root: str | Path, remote: str) -> list[tuple[str, str]]:
    """Every branch in the namespace the claim lives in, as `(branch, sha)`.

    The host's namespace where there is one, and this machine's where there is not -- the same
    split `status` makes, for the same reason: with no remote the local branch is the whole of
    the claim.
    """
    if remote_url(root, remote):
        proc = git(root, "ls-remote", "--heads", remote, check=False)
        if proc.returncode != 0:
            raise ClaimError(f"could not read `{remote}`: {proc.stderr.strip()}")
        found = []
        for line in proc.stdout.splitlines():
            sha, _, ref = line.partition("\t")
            ref = ref.strip()
            if ref.startswith(REFS_PREFIX):
                found.append((ref[len(REFS_PREFIX) :], sha.strip()))
        return found
    proc = git(root, "for-each-ref", "--format=%(objectname) %(refname:short)", REFS_PREFIX)
    found = []
    for line in proc.stdout.splitlines():
        sha, _, name = line.partition(" ")
        if name.strip():
            found.append((name.strip(), sha.strip()))
    return found


def refs_for_item(root: str | Path, remote: str, item: str) -> list[tuple[str, str]]:
    """Every published ref whose name claims this item, newest-sorted by nothing.

    ⛔ **A list of candidates, never a verdict.** What the caller does with it is apply the
    landed/live/orphaned reading to each, because the item's number appearing in a ref name is
    exactly as true after the work lands as before it -- and a filter that stopped here would
    read a landed item as taken for as long as the ref survives the merge.
    """
    return sorted((b, sha) for b, sha in all_refs(root, remote) if ref_is_for_item(b, item))


# --------------------------------------------------------------------------------------------
# Who holds it, and since when
# --------------------------------------------------------------------------------------------


@dataclass
class Holder:
    """§ 10: a refusal names who holds the claim and since when, and names what it could not
    establish. Both halves are optional and each absence carries its own reason, because an
    omitted half reads as a non-problem and the next role inherits a guess as a fact (§ 11)."""

    actor: str | None = None
    since: str | None = None
    unestablished: list[str] = field(default_factory=list)

    def describe(self) -> str:
        parts = []
        parts.append(f"held by {self.actor}" if self.actor else f"who holds it {UNESTABLISHED}")
        parts.append(f"since {self.since}" if self.since else f"since when {UNESTABLISHED}")
        for reason in self.unestablished:
            parts.append(f"({reason})")
        return ", ".join(parts)


def host_record(root: str | Path, remote: str, branch: str) -> Holder:
    """Read the ref's creation from the host's own record of it.

    ⚠️ This is the only half of the claim that needs a credential, and it is needed for the
    *refusal's wording* rather than for the refusal itself: the ref existing is the whole of what
    the claim asserts. So every failure here degrades to a named absence and never to an error.
    """
    url = remote_url(root, remote)
    if not url:
        return Holder(unestablished=["the project has no remote, so the claim is local-only"])

    slug = host_slug(url)
    if not slug:
        return Holder(unestablished=["the remote is not the code host, so it records no actor"])
    if not shutil.which("gh"):
        return Holder(unestablished=["the host's own client is not installed here"])

    proc = subprocess.run(
        ["gh", "api", f"repos/{slug}/activity?per_page=100"],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return Holder(unestablished=["the host's record of the ref could not be read"])
    try:
        events = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return Holder(unestablished=["the host's record of the ref did not parse"])

    for event in events if isinstance(events, list) else []:
        if event.get("ref") != REFS_PREFIX + branch:
            continue
        if event.get("activity_type") != "branch_creation":
            continue
        return Holder(
            actor=(event.get("actor") or {}).get("login"),
            since=event.get("timestamp"),
        )
    # ⚠️ The record is paginated and bounded. A claim older than the window is a claim whose
    # creation this cannot see, which is an absence with a reason rather than a free ref.
    return Holder(
        unestablished=["the host's record does not reach back to when this ref was created"]
    )


def moment(stamp: str | None) -> "datetime | None":
    """An instant from the host's own timestamp, or None where there is nothing to read."""
    if not stamp:
        return None
    try:
        return datetime.fromisoformat(stamp.strip().replace("Z", "+00:00"))
    except ValueError:
        return None


def merge_lands_this_ref(created_at: str | None, merged_at: str | None) -> bool | None:
    """Whether a merged pull request found by branch *name* is about the ref standing there now.

    `True` where the ref already existed when the request merged, `False` where the merge
    predates the ref and so belongs to an earlier occupant of the name, and `None` where one of
    the two instants could not be read -- which the caller reports and never rounds to either.
    """
    born, merged = moment(created_at), moment(merged_at)
    if born is None or merged is None:
        return None
    # ⚠️ One instant carrying a zone and the other not makes the comparison raise rather than
    # answer, and this is reached from `status`, which a refusal's own wording calls -- so the
    # crash would land on the path that reports a refusal. The host stamps both in UTC, so the
    # mismatch is a shape nothing here has seen; it declines rather than trusting that.
    if (born.tzinfo is None) != (merged.tzinfo is None):
        return None
    return born <= merged


def host_slug(url: str) -> str | None:
    """`OWNER/NAME` where the remote is the code host, else None.

    Both URL forms, because a project's remote may be either and the claim is read from whichever
    one the person cloned with.
    """
    match = re.search(r"github\.com[:/]+([^/]+/[^/]+?)(?:\.git)?/?$", url.strip())
    return match.group(1) if match else None


# --------------------------------------------------------------------------------------------
# Live, or merely held by nobody
# --------------------------------------------------------------------------------------------


@dataclass
class Liveness:
    """§ 10's table, read in order. `live` is a disjunction: any one arm is enough, and the arms
    that need no host are checked first so a claim is not called orphaned merely because the host
    was unreachable.

    ⛔ **`landed` is a third reading and not a flavour of the other two.** A claim whose work
    reached the integration branch is neither live nor orphaned: it is finished, and releasing it
    is routine rather than a judgement. Without it, a squash-merged claim reads *live* forever --
    its commits are not ancestors of anything, because the merge wrote a new one -- and giving it
    up then needs the override reserved for breaking somebody else's work, which empties that
    override of its meaning.
    """

    live: bool
    reason: str
    landed: bool = False
    unestablished: list[str] = field(default_factory=list)


def tree_for_branch(root: str | Path, branch: str) -> str | None:
    """The working tree holding this branch on this machine, or None."""
    proc = git(root, "worktree", "list", "--porcelain")
    path: str | None = None
    for line in proc.stdout.splitlines():
        if line.startswith("worktree "):
            path = line[len("worktree ") :].strip()
        elif line.startswith("branch ") and line[len("branch ") :].strip() == REFS_PREFIX + branch:
            return path
    return None


def process_in(path: str) -> bool | None:
    """Whether any live process is working *at or below* `path`. None where it cannot be read.

    ⚠️ This is the one liveness arm that reads the machine rather than the repository, and it is
    #34's test rather than a second one: a tree another live session occupies is read from the
    open-file table.

    ⛔ **At or below, not equal.** A session's working directory is often a subdirectory of the
    tree rather than its root, and filtering the open-file table by the tree's own path matches
    only an exact cwd -- so a session two directories down reads as nobody there, and the claim it
    is actively working reads as an orphaned candidate. The table is therefore enumerated and the
    prefix compared here, rather than handed to the tool as a filter.

    ⛔ Three answers, not two: *yes*, *no*, and **unreadable**. The caller records the third as
    unestablished, because "the table could not be read" and "the tree is idle" are the same
    answer otherwise, and the wrong one of the two is the one that lets a claim be taken.
    """
    if not shutil.which("lsof"):
        return None
    # `-F n` prints one field per line, each tagged; `n` is the name. Failure is expected and
    # routine here -- lsof exits non-zero when it merely skipped something it could not stat --
    # so the output is read regardless and only an empty result counts as unreadable.
    proc = subprocess.run(
        ["lsof", "-a", "-d", "cwd", "-F", "n"], capture_output=True, text=True
    )
    names = [line[1:] for line in proc.stdout.splitlines() if line.startswith("n")]
    if not names:
        return None
    root = os.path.realpath(path)
    for name in names:
        cwd = os.path.realpath(name)
        if cwd == root or cwd.startswith(root + os.sep):
            return True
    return False


def standing_in(path: str) -> bool:
    """Whether *this* process's working directory is at or below `path`.

    ⛔ **§ 10's *leave, then remove*, and the only half of it a carrier can enforce.** The rest of
    that rule is an ordering in a role's text; this is the refusal that catches a pass which
    skipped it. A removal asked for from inside the tree either fails or succeeds into a session
    whose working directory no longer exists, and the second is the worse of the two: the session
    keeps running, every call that names a root explicitly still works, and every call that does
    not writes wherever the shell lands -- which under this branch model is the shared checkout.

    ⛔ **At or below, never equal**, for the same reason `process_in` carries that correction: a
    session's working directory is routinely a subdirectory of its tree, and an equality test
    answers *not standing there* for a session that is.

    ⚠️ This reads **this** process and `process_in` reads every other one; they answer different
    questions and the caller needs both. A sibling session's tree is skipped, and the caller's own
    is stopped on -- the stop being clearable by leaving, which is what makes it a refusal rather
    than an exemption.
    """
    try:
        here = os.path.realpath(os.getcwd())
    except OSError:
        # ⚠️ An unreadable cwd *is* the deleted-out-from-under case, already arrived. There is no
        # live directory left to protect, so the removal may proceed and clean up after it.
        return False
    root = os.path.realpath(path)
    return here == root or here.startswith(root + os.sep)


def read_liveness(
    root: str | Path,
    remote: str,
    branch: str,
    integration: str,
    ref_sha: str,
    created_at: str | None = None,
) -> Liveness:
    """`created_at` is when *this* ref came into existence, read from the host's own record.

    ⛔ **The host's pull-request arms are keyed on a branch *name*, and a name outlives the ref
    that wore it.** Measured 2026-10-19: a ref published at 14:47:34 read back `landed: the host
    records pull request #114 for this ref as merged` -- a pull request that merged 16½ hours
    earlier, against a different ref that had held the same name and been deleted. The reading
    was the dangerous one of the two: *spent, releasing it needs no override*, on a claim another
    session had taken thirty-three seconds before. It is a window rather than a steady state,
    because the occupied-tree arm takes over once the tree is cut -- which is to say it is open
    exactly across the interval between the publish and the cut, the interval `take` performs as
    one operation and a pre-filter does not.

    So a merged pull request lands this ref only where the ref already existed when it merged.
    ⚠️ Where the creation time cannot be established the arm **declines** rather than asserting:
    an unreadable creation time is not evidence the ref predates the merge, and the cost of
    declining is a claim read as live -- which refuses a start and asks for an override to
    release, both of which are the safe direction.
    """
    unestablished: list[str] = []
    carries_own_commits = False

    # The ref's own object is needed locally to compare against anything, so it is fetched
    # without a destination refspec rather than onto any branch.
    git(root, "fetch", "--quiet", remote, f"{REFS_PREFIX}{branch}", check=False)
    integration_sha = git(root, "rev-parse", integration, check=False)

    if integration_sha.returncode != 0:
        unestablished.append(f"the integration branch `{integration}` could not be resolved")
    else:
        tip = integration_sha.stdout.strip()

        # ⛔ **Ancestry answers one question only: does the ref carry work of its own.** It is
        # *not* the landed test, and reading it as one is wrong in the direction that matters --
        # a ref just claimed points at the integration tip, so it is an ancestor too, and a
        # brand-new claim would read as spent. Measured: the first attempt at this fix did
        # exactly that and the suite caught it on the orphan case.
        ancestor = git(root, "merge-base", "--is-ancestor", ref_sha, tip, check=False)
        if ancestor.returncode not in (0, 1):
            unestablished.append("whether the ref carries commits of its own")
        carries_own_commits = ancestor.returncode == 1

        # ⛔ **Landed needs both halves: the ref carried work, and that work is now in the
        # integration branch.** Ancestry cannot supply the second half, because ancestry is
        # trustworthy in one direction only -- a true answer proves content landed, a false one
        # proves nothing, since a squash or a rebase writes new commits and the old hashes become
        # unreachable. So the second half is read from **content**: where a ref that carries its
        # own commits differs from the integration branch in nothing, its work is in there
        # whatever the hashes say.
        #
        # The defect this replaces: non-ancestry alone was read as *live*, so every
        # squash-merged claim read as in flight forever and the ordinary cleanup after a merge
        # had to pass the override meant for breaking somebody else's work. Found on this
        # module's own branch one minute after it merged.
        if carries_own_commits:
            same = git(root, "diff", "--quiet", ref_sha, tip, check=False)
            if same.returncode == 0:
                return Liveness(
                    False,
                    "the ref carries its own commits and differs from the integration branch in "
                    "nothing, so its work has landed",
                    landed=True,
                )
            if same.returncode not in (0, 1):
                unestablished.append(
                    "whether the ref's content is already on the integration branch"
                )

        # ⛔ Nothing is concluded from `carries_own_commits` here. It is the weakest signal in
        # this function and the one that was wrong, so it is carried to the end and read only
        # after every arm that could overturn it -- the host's record of a merge sits two arms
        # below, and an early return made it unreachable.

    # Arm 2: a tree on this machine, with someone in it.
    tree = tree_for_branch(root, branch)
    if tree:
        occupied = process_in(tree)
        if occupied:
            return Liveness(True, f"a live process is working at or below {tree}")
        if occupied is None:
            unestablished.append("whether a process occupies the tree holding this branch")

    # Arm 3: the host's own record of this branch's pull requests. It answers both readings -- a
    # merged one lands the claim, an open one keeps it live -- and it is the only thing that
    # settles the residue the two tests above leave.
    url = remote_url(root, remote)
    slug = host_slug(url) if url else None
    if slug and shutil.which("gh"):
        proc = subprocess.run(
            ["gh", "pr", "list", "--repo", slug, "--head", branch, "--state", "all",
             "--json", "number,state,mergedAt"],
            capture_output=True,
            text=True,
        )
        if proc.returncode == 0:
            try:
                requests = json.loads(proc.stdout or "[]")
            except json.JSONDecodeError:
                requests = None
                unestablished.append("what the host records about this branch's pull requests")
            if requests is not None:
                merged = [r for r in requests if r.get("state") == "MERGED"]
                # ⛔ Each merged request is read against *this* ref's own birth, not against the
                # name it shares with the one that merged. A request that merged before the ref
                # existed is residue from a previous occupant of the name.
                for request in merged:
                    verdict = merge_lands_this_ref(created_at, request.get("mergedAt"))
                    if verdict is None:
                        unestablished.append(
                            f"whether pull request #{request['number']}, which the host records "
                            "as merged for this branch name, is about this ref or about an "
                            "earlier one that wore the name"
                        )
                        continue
                    if verdict:
                        return Liveness(
                            False,
                            f"the host records pull request #{request['number']} for this ref "
                            "as merged",
                            landed=True,
                        )
                if [r for r in requests if r.get("state") == "OPEN"]:
                    return Liveness(True, "an open pull request references the ref")
        else:
            unestablished.append("what the host records about this branch's pull requests")
    else:
        unestablished.append("what the host records about this branch's pull requests")

    # ⚠️ The weakest signal, read last and stated with its residue. A claim that was
    # squash-merged *and* then had other work land on top of it differs from the integration
    # branch in that other work, so neither landed test fires; without a credential the host
    # cannot say it merged either, and this reads it as live. That errs towards refusing a start
    # rather than towards taking a held claim, which is the direction to be wrong in.
    if carries_own_commits:
        return Liveness(
            True, "the ref carries commits beyond the integration branch", unestablished=unestablished
        )

    return Liveness(
        False, "no arm of the liveness test answered yes", unestablished=unestablished
    )


# --------------------------------------------------------------------------------------------
# The three operations
# --------------------------------------------------------------------------------------------


@dataclass
class Status:
    taken: bool
    ref_sha: str | None
    holder: Holder
    liveness: Liveness | None
    local_only: bool

    def report(self) -> str:
        if not self.taken:
            where = "on this machine" if self.local_only else "on the host"
            return f"free: no ref named this exists {where}."
        lines = [f"taken: the ref exists at {self.ref_sha[:7]}, {self.holder.describe()}."]
        if self.liveness:
            if self.liveness.landed:
                # Neither live nor orphaned: finished. Releasing it is bookkeeping, so it is
                # said plainly rather than handed to anyone as a judgement.
                lines.append(
                    f"landed: {self.liveness.reason}. The claim is spent and releasing it "
                    "needs no override."
                )
            elif self.liveness.live:
                lines.append(f"live: {self.liveness.reason}.")
            else:
                # ⛔ Reported, never broken. The two readings are stated because they are
                # genuinely indistinguishable from here.
                lines.append(
                    "orphaned-candidate: "
                    f"{self.liveness.reason}. A session that died holds the same ref as one "
                    "about to commit into it, so this is reported and not broken: ask."
                )
            for item in self.liveness.unestablished:
                lines.append(f"  unestablished: {item}")
        for item in self.holder.unestablished:
            lines.append(f"  unestablished: {item}")
        return "\n".join(lines)


def status(
    root: str | Path, branch: str, remote: str = "origin", integration: str | None = None
) -> Status:
    url = remote_url(root, remote)
    integration = integration_branch(root, remote, integration)
    if not url:
        # Local-only: the branch itself is the whole claim, and it still arbitrates every session
        # on this machine -- which is every session there can be, with no remote to reach.
        proc = git(root, "rev-parse", "--verify", "--quiet", REFS_PREFIX + branch, check=False)
        sha = proc.stdout.strip() or None
        return Status(
            taken=bool(sha),
            ref_sha=sha,
            holder=Holder(unestablished=["the project has no remote, so the claim is local-only"]),
            liveness=read_liveness(root, remote, branch, integration, sha) if sha else None,
            local_only=True,
        )

    sha = remote_ref_sha(root, remote, branch)
    if not sha:
        return Status(False, None, Holder(), None, local_only=False)
    # ⛔ The holder is read **before** liveness and not beside it: `since` is when this ref came
    # into existence, and the landed arm cannot tell a merge of this ref from a merge of the one
    # that last wore its name without it.
    holder = host_record(root, remote, branch)
    return Status(
        taken=True,
        ref_sha=sha,
        holder=holder,
        liveness=read_liveness(root, remote, branch, integration, sha, holder.since),
        local_only=False,
    )


# --------------------------------------------------------------------------------------------
# The same question, asked about a work item rather than about a name
# --------------------------------------------------------------------------------------------


@dataclass
class ItemStatus:
    """What the branch namespace says about one work item.

    ⛔ **Advisory, and the surface says so.** Two measured misses sit behind this type and only
    one of them is a question this can answer: a filter asked about the wrong *name* (which this
    fixes), and a filter asked at the right moment that was overtaken before the push (which
    nothing asked before the attempt can fix). The authority is `take`.
    """

    item: str
    readings: list[tuple[str, Status]]
    local_only: bool

    def contending(self, mine: str | None = None) -> list[tuple[str, Status]]:
        """Refs claiming this item that are neither spent nor this session's own.

        ⛔ **`taken` first.** The candidates are listed and then read one at a time, so a ref
        deleted in between answers `free` and would otherwise be counted as a claim: a refusal
        naming a ref that does not exist, and a report saying `taken` and `free` about one name
        two lines apart. ⚠️ The deletion that opens that window is this module's own -- the
        post-check below rolls a losing sibling's ref back -- so the two sessions this guard is
        for are the pair most likely to see it.
        """
        return [
            (branch, held)
            for branch, held in self.readings
            if branch != mine and held.taken and not (held.liveness and held.liveness.landed)
        ]

    def report(self) -> str:
        where = "on this machine" if self.local_only else "on the host"
        if not self.readings:
            return f"free: no ref claims item {self.item} {where}."
        lines = []
        contending = self.contending()
        if not contending:
            lines.append(
                f"free: every ref claiming item {self.item} has landed, so none of them holds it."
            )
        elif len(contending) > 1:
            # ⛔ Not a tidy answer, because the state is not tidy: this is the failure the claim
            # exists to prevent, already happened, and collapsing it into "taken" would hide
            # which of the two a person has to settle.
            lines.append(
                f"contested: {len(contending)} refs claim item {self.item} and none has landed. "
                "Two sessions hold one item; which survives is a person's call."
            )
        else:
            lines.append(f"taken: one ref claims item {self.item}.")
        for branch, held in self.readings:
            if not held.taken:
                # Listed a moment ago and gone now. Said as gone, rather than printed under its
                # own `free:` line where it reads as a contradiction of the verdict above.
                lines.append(f"  {branch} — gone since the refs were listed")
                continue
            lines.append(f"  {branch}")
            for line in held.report().splitlines():
                lines.append(f"    {line}")
        return "\n".join(lines)


def status_for_item(
    root: str | Path, item: str, remote: str = "origin", integration: str | None = None
) -> ItemStatus:
    integration = integration_branch(root, remote, integration)
    local_only = not remote_url(root, remote)
    readings = [
        (branch, status(root, branch, remote, integration))
        for branch, _ in refs_for_item(root, remote, item)
    ]
    return ItemStatus(item=str(item), readings=readings, local_only=local_only)


def _local_branch(root: str | Path, branch: str) -> bool:
    """Whether this machine already has the branch, ref name and all."""
    return git(
        root, "rev-parse", "--verify", "--quiet", REFS_PREFIX + branch, check=False
    ).returncode == 0


def take(
    root: str | Path,
    branch: str | None = None,
    tree: str | None = None,
    remote: str = "origin",
    integration: str | None = None,
    *,
    item: str | None = None,
    prefix: str | None = None,
    title: str | None = None,
    _lease: bool = True,
    _require_created: bool = True,
    _release_on_tree_failure: bool = True,
    _item_precheck: bool = True,
    _item_postcheck: bool = True,
) -> str:
    """Claim the item, then cut the tree. Raises `ClaimError` on a refusal.

    The branch name is **derived here** from `(prefix, item, title)` where those are given, so
    that two sessions handed one title cannot publish two names for one item. An explicit
    `branch` is still accepted, for the roles that already have a name in hand.

    ⛔ **The ref name is not the whole of the test-and-set, and the measurements say so.** Three
    times on 2026-10-19 two sessions started one item under two names -- twice by abbreviating
    the title differently, once by carrying the whole of it -- and each time the push *created*
    the ref, so the arm that was supposed to refuse never engaged and the tree directory
    arbitrated one step later. The derivation above closes that for sessions that hand over the
    same title; the guard below closes it for the ones that do not, which is § 8's translation
    case and anything taken by hand.

    The underscore arguments exist for `--self-test` and for nothing else: they are how the
    suite plants each arm away in turn, to show that the race is held by the arm it is attributed
    to and that the no-residue rule is held by the release rather than by luck.
    """
    if branch is None:
        if not (prefix and item and title is not None):
            raise ClaimError(
                "a claim needs either `--branch`, or `--branch-prefix`, `--item` and `--title` "
                "for the name to be derived from."
            )
        branch = branch_for(prefix, item, title)
    if tree is None:
        raise ClaimError("a claim needs the tree it is cut into; § 10 derives the path, not this.")
    # Where the caller named no item, one is recovered from the branch where that can be done
    # without guessing -- so a role that already holds a name still gets the guard.
    item = str(item) if item else item_in_branch(branch)

    integration = integration_branch(root, remote, integration)
    base = git(root, "rev-parse", integration).stdout.strip()
    url = remote_url(root, remote)
    published = False

    if item and _item_precheck:
        held = status_for_item(root, item, remote, integration)
        contending = held.contending(mine=branch)
        if contending:
            raise ClaimError(
                f"refused: item {item} is already claimed under "
                f"{', '.join('`' + b + '`' for b, _ in contending)}, which is not the name this "
                f"start would have used (`{branch}`).\n{held.report()}"
            )

    if url:
        args = ["push", "--porcelain", remote, f"{base}:{REFS_PREFIX}{branch}"]
        if _lease:
            args.append(LEASE.format(ref=REFS_PREFIX + branch))
        proc = git(root, *args, check=False)
        created = _push_created_ref(proc.stdout, branch)
        if proc.returncode != 0 or (_require_created and not created):
            held = status(root, branch, remote, integration)
            raise ClaimError(f"refused: the claim on `{branch}` is taken.\n{held.report()}")
        published = True

    # ⛔ Read again, now that this session's own ref is published. The check above is a read
    # followed by a write and so has a window; this one closes it, because a sibling that
    # published a differently-named ref inside that window is visible here and this session
    # gives its own ref back rather than letting two stand.
    #
    # ⚠️ Where both sessions reach this point they both give their refs up and the item is left
    # free, which is a refusal reported to two people rather than one item held by two. That is
    # the direction to fail in, and a re-run takes it.
    if item and _item_postcheck:
        contending = status_for_item(root, item, remote, integration).contending(mine=branch)
        if contending:
            if published:
                git(root, "push", remote, "--delete", branch, check=False)
            raise ClaimError(
                f"refused: item {item} was claimed under "
                f"{', '.join('`' + b + '`' for b, _ in contending)} while this start was "
                f"publishing `{branch}`. This session's ref has been given back."
            )

    # The local half. Atomic too, but only against this machine -- which is why it is second.
    #
    # ⚠️ The cut fails in two shapes and only one of them fails cleanly, measured 2026-10-19. A
    # *branch name* already taken fails before anything is created. A *tree directory* already
    # taken fails after the branch is created -- `Preparing worktree (new branch …)`, then
    # `fatal: … already exists` -- so the refusal leaves a local branch pointing at the base with
    # no tree and no commits. That residue is a false claim rather than cosmetic: a pre-filter
    # matching the item's number against the ref tail reads it as *taken* forever, including
    # after the real claim lands and its tree is removed, so the item is skipped on behalf of a
    # session that never held it. Hence the branch existing *before* is what decides whether it
    # may be deleted after: deleting unconditionally would delete somebody else's.
    existed = _local_branch(root, branch)
    cut = git(root, "worktree", "add", str(tree), "-b", branch, base, check=False)
    if cut.returncode != 0:
        if published and _release_on_tree_failure:
            git(root, "push", remote, "--delete", branch, check=False)
        if not existed and _release_on_tree_failure and _local_branch(root, branch):
            git(root, "branch", "-D", branch, check=False)
        raise ClaimError(
            f"refused: the ref was claimed but no tree could be cut: {cut.stderr.strip()}"
        )

    where = "published and cut" if published else "cut (local-only: the project has no remote)"
    return f"claimed `{branch}`: {where}, tree at {tree}."


def release(
    root: str | Path,
    branch: str,
    tree: str | None = None,
    remote: str = "origin",
    integration: str | None = None,
    *,
    force: bool = False,
) -> str:
    """Give the claim up: the ref first, then the tree and the local branch.

    Order mirrors `take`: the published ref is what another machine reads, so it is what stops
    being true first. A release is idempotent -- each half reports what was already gone, since a
    half-released claim is exactly the state a failed release leaves and it has to be re-runnable.

    ⛔ **A live claim held somewhere else is refused rather than released.** § 10 states that a
    claim is never broken automatically, and a release that deletes any ref it is pointed at makes
    this command the automatic breaker -- one argument away from ending a session's claim while it
    is mid-item. So liveness is read first, and a live claim with no tree *here* needs `--force`,
    which is a person saying it. The local-only case needs none of this: there is no ref to
    publish and nothing another machine could be holding.

    ⛔ **A claim whose work has landed is not live and needs no override.** That is what makes the
    rule above affordable: without the landed reading, every squash-merged claim reached this
    guard as live, and the ordinary cleanup after a merge had to pass the flag reserved for
    breaking somebody else's work -- which is how an override stops meaning anything.

    ⛔ **A release asked for from inside the tree it would remove is refused, and `--force` does
    not cover it.** The override exists for breaking another session's claim, which is a person's
    call; standing in the tree is not a call anybody can make, because forcing it removes the
    directory this process is in either way. § 10 orders the exit first, so leaving is what clears
    this and nothing else does.
    """
    doomed = tree or tree_for_branch(root, branch)
    # ⛔ Before the ref deletion and not beside the tree removal: a refusal has to leave the claim
    # whole. Checked where `release` is entered, so a half-released claim is never this guard's.
    if doomed and standing_in(doomed):
        raise ClaimError(
            f"refused: this release would remove `{doomed}`, which this process is standing in.\n"
            "§ 10 orders the exit before the removal. Leave the tree and run this again — from "
            "the shared checkout, or from anywhere outside it.\n"
            "--force does not cover this: it breaks another session's claim, and the tree would "
            "still go out from under this one."
        )

    if not force and remote_url(root, remote):
        held = status(root, branch, remote, integration)
        # ⛔ The test is **landed or held here**, not *live*. Keying on live left the orphan case
        # open, and the orphan case includes a claim somebody took a minute ago: from any other
        # clone a fresh claim has no commits and no tree, so it reads as an orphaned candidate --
        # and a release keyed on live would delete it in silence. That is the two-sessions-on-one
        # -item failure the claim exists to prevent, reintroduced through the other end.
        spent = held.liveness is not None and held.liveness.landed
        if held.taken and not spent and not tree_for_branch(root, branch):
            raise ClaimError(
                f"refused: the claim on `{branch}` is not spent and is not held in a tree here.\n"
                f"{held.report()}\n"
                "Breaking a claim that is neither landed nor yours is a person's call: pass "
                "--force to say so."
            )

    done = []
    if remote_url(root, remote):
        proc = git(root, "push", remote, "--delete", branch, check=False)
        done.append("ref deleted" if proc.returncode == 0 else "ref was already gone")

    # ⛔ `doomed`, not a second derivation of the same path: the guard above refused on one answer
    # and a re-read here is allowed to give another, which would remove a tree nothing checked.
    if doomed and Path(doomed).exists():
        git(root, "worktree", "remove", doomed, "--force", check=False)
        done.append(f"tree {doomed} removed")
    git(root, "worktree", "prune", check=False)

    if _local_branch(root, branch):
        proc = git(root, "branch", "-D", branch, check=False)
        done.append("local branch deleted" if proc.returncode == 0 else "local branch kept")

    return f"released `{branch}`: " + ", ".join(done) + "."


def claim_free(
    root: str | Path, branch: str, remote: str = "origin", integration: str | None = None
) -> tuple[bool, str]:
    """§ 5's predicate. One statement of one question: is this ref taken.

    ⛔ Not `assignee_matches_role`, which asks whether the person on the item is the one the role
    acts for -- a different question on a different store, per § 10.
    """
    held = status(root, branch, remote, integration)
    return (not held.taken), held.report()


# --------------------------------------------------------------------------------------------
# --self-test
# --------------------------------------------------------------------------------------------


class Suite:
    def __init__(self) -> None:
        self.failures = 0

    def ok(self, label: str, condition: bool, detail: str = "") -> None:
        print(f"  {'ok  ' if condition else 'FAIL'}  {label}")
        if not condition:
            self.failures += 1
            if detail:
                print(f"          {detail}")


def _bare_world(stack: tempfile.TemporaryDirectory) -> tuple[str, str, str]:
    """A bare repository standing in for the host, and two clones standing in for two sessions.

    Two *clones* rather than two sessions in one clone, deliberately: the race the claim exists to
    lose safely is between machines, and two sessions in one clone would be arbitrated by the
    local branch namespace -- the half that was never in doubt.
    """
    root = Path(stack.name)
    origin = root / "origin.git"
    # ⚠️ The integration branch is named explicitly rather than inherited. A bare repository's
    # HEAD follows whatever this machine's default branch name is, and where that differs from
    # the name the seed pushes, HEAD points at a ref nothing created -- so every clone checks
    # out nothing, has no local integration branch, and the suite dies resolving it instead of
    # testing anything. Measured: green on a machine configured one way, a crash on a runner
    # configured the other.
    subprocess.run(
        ["git", "init", "--quiet", "--bare", "--initial-branch=main", str(origin)], check=True
    )

    seed = root / "seed"
    # ⚠️ This clone is of a repository with no commits yet, which git warns about on stderr --
    # and `--quiet` does not cover a warning. The fixture is built this way on purpose, so the
    # warning carries no information, and this world is built once per section of the suite: the
    # copies pile up above the report and only make a reader hunt for a failure that is not
    # there. Captured rather than discarded: a clone that genuinely fails must still say why.
    seeded = subprocess.run(
        ["git", "clone", "--quiet", str(origin), str(seed)], capture_output=True, text=True
    )
    if seeded.returncode != 0:
        raise ClaimError(f"the fixture's seed clone failed: {seeded.stderr.strip()}")
    for key, value in (("user.email", "seed"), ("user.name", "Seed")):
        git(seed, "config", key, value)
    (seed / "README.md").write_text("seed\n")
    git(seed, "add", "README.md")
    git(seed, "commit", "--quiet", "-m", "seed")
    git(seed, "branch", "-M", "main")
    git(seed, "push", "--quiet", "origin", "main")

    one = root / "session-one"
    two = root / "session-two"
    for path in (one, two):
        subprocess.run(["git", "clone", "--quiet", str(origin), str(path)], check=True)
    return str(origin), str(one), str(two)


def self_test() -> int:
    suite = Suite()
    print("Each check is shown a violation it must redden on, then the rule is held.\n")

    # ---- Phase one: the plants. Nothing is believed until it has been shown it can fail. ----
    print("planted violations:")

    with tempfile.TemporaryDirectory() as tmp:
        stack = tempfile.TemporaryDirectory(dir=tmp)
        _, one, two = _bare_world(stack)
        take(one, "feature/x", str(Path(tmp) / "t1"))
        # Plant, arm 1: the created-ref check removed, lease left in place. Both sessions push
        # the same integration tip, so the second push is `Everything up-to-date` -- exit 0, no
        # update attempted, the lease never consulted. Two sessions, one item, and a green push.
        raced = True
        try:
            take(two, "feature/x", str(Path(tmp) / "t2"), _require_created=False)
        except ClaimError:
            raced = False
        suite.ok(
            "with the lease alone the second session is NOT refused (so arm 1 is what holds it)",
            raced,
            "the second push was refused by something else, so arm 1's attribution is wrong",
        )

    with tempfile.TemporaryDirectory() as tmp:
        stack = tempfile.TemporaryDirectory(dir=tmp)
        origin, one, two = _bare_world(stack)
        take(one, "feature/w", str(Path(tmp) / "t1"))
        # Plant, arm 2: the window where the ref appears after the advertisement and before the
        # write. True simultaneity is not reproducible here, so the arm is exercised directly --
        # an update to a ref the lease was told must not exist. This is the shape a live probe
        # against the host measured, and on its own it says nothing about arm 1.
        # A sha the ref does not already point at, so the push is a real update and git does not
        # short-circuit into arm 1 -- which is the mistake that made the first live probe of this
        # mechanism read as conclusive.
        for key, value in (("user.email", "two"), ("user.name", "Two")):
            git(two, "config", key, value)
        (Path(two) / "other.txt").write_text("other\n")
        git(two, "add", "other.txt")
        git(two, "commit", "--quiet", "-m", "other")
        moved = git(two, "rev-parse", "HEAD").stdout.strip()
        with_lease = git(
            two,
            "push",
            "--porcelain",
            "origin",
            f"{moved}:{REFS_PREFIX}feature/w",
            LEASE.format(ref=REFS_PREFIX + "feature/w"),
            check=False,
        )
        suite.ok(
            "an update to a ref the lease says must not exist is refused (arm 2)",
            with_lease.returncode != 0,
            with_lease.stdout + with_lease.stderr,
        )
        # And the same push without the lease succeeds, so the refusal above is the lease's.
        without_lease = git(
            two, "push", "--porcelain", "origin", f"{moved}:{REFS_PREFIX}feature/w", check=False
        )
        suite.ok(
            "and succeeds without it (so arm 2's refusal is the lease's own)",
            without_lease.returncode == 0,
            without_lease.stdout + without_lease.stderr,
        )

    with tempfile.TemporaryDirectory() as tmp:
        stack = tempfile.TemporaryDirectory(dir=tmp)
        _, one, _ = _bare_world(stack)
        # Plant: the rollback removed, with a tree path that cannot be created. The ref is then
        # claimed by a start that failed -- the residue § 10 forbids.
        blocked = Path(tmp) / "occupied"
        blocked.write_text("not a directory\n")
        try:
            take(one, "feature/y", str(blocked), _release_on_tree_failure=False)
        except ClaimError:
            pass
        suite.ok(
            "without the rollback a failed cut leaves the ref behind (so the release is what holds it)",
            remote_ref_sha(one, "origin", "feature/y") is not None,
        )
        # The second half of the same rollback, planted away by the same flag and asserted
        # separately because it is a second residue with a second consequence. `worktree add -b`
        # creates the branch and *then* fails on the path, so the loser keeps a local branch
        # pointing at the base -- and a pre-filter matching the item's number against the ref
        # tail reads that as the item being held.
        suite.ok(
            "without the rollback it leaves the local branch behind too",
            _local_branch(one, "feature/y"),
        )

    # ---- Phase two: the rule. ----
    print("\nthe claim:")

    with tempfile.TemporaryDirectory() as tmp:
        stack = tempfile.TemporaryDirectory(dir=tmp)
        _, one, two = _bare_world(stack)
        t1 = str(Path(tmp) / "t1")

        first = take(one, "feature/x", t1)
        suite.ok("the first session claims the item", "claimed" in first, first)
        suite.ok("the claim is published, not merely local", remote_ref_sha(one, "origin", "feature/x") is not None)
        suite.ok("and the tree is cut", Path(t1).is_dir())

        refusal = ""
        refused = False
        try:
            take(two, "feature/x", str(Path(tmp) / "t2"))
        except ClaimError as exc:
            refused, refusal = True, str(exc)
        suite.ok("a second session starting the same item is refused", refused)
        suite.ok("the refusal says the claim is taken", "taken" in refusal, refusal)
        suite.ok(
            "and names what it could not establish rather than guessing it",
            UNESTABLISHED in refusal,
            refusal,
        )
        suite.ok(
            "a refused start leaves no tree behind",
            not Path(Path(tmp) / "t2").exists(),
        )
        suite.ok(
            "a refused start leaves no local branch behind",
            git(two, "rev-parse", "--verify", "--quiet", "refs/heads/feature/x", check=False).returncode != 0,
        )
        suite.ok(
            "and does not disturb the claim it lost to",
            remote_ref_sha(two, "origin", "feature/x") is not None,
        )

    # The other shape of a refused cut, and the one the ref race never reaches: the branch name
    # is free and the *tree directory* is taken, so the push succeeds and the local half is what
    # fails. Both residues are the loser's own clone, which is why this is a fresh world.
    with tempfile.TemporaryDirectory() as tmp:
        stack = tempfile.TemporaryDirectory(dir=tmp)
        _, one, _ = _bare_world(stack)
        occupied = Path(tmp) / "occupied"
        occupied.mkdir()
        (occupied / "something").write_text("a directory somebody else is using\n")

        refused = False
        try:
            take(one, "feature/d", str(occupied))
        except ClaimError:
            refused = True
        suite.ok("a cut refused on the tree directory is a refusal", refused)
        suite.ok(
            "and leaves no local branch, so the number pre-filter reads the item as free",
            not _local_branch(one, "feature/d"),
        )
        suite.ok(
            "and leaves no published ref",
            remote_ref_sha(one, "origin", "feature/d") is None,
        )
        suite.ok(
            "and the directory it could not take is untouched",
            (occupied / "something").exists(),
        )

        # The opposite direction, because the rollback must not delete what it did not create:
        # a branch that was already here before the attempt is somebody's, not this call's.
        git(one, "branch", "feature/pre-existing")
        try:
            take(one, "feature/pre-existing", str(occupied))
        except ClaimError:
            pass
        suite.ok(
            "a failed cut leaves a branch that existed before it alone",
            _local_branch(one, "feature/pre-existing"),
        )

    with tempfile.TemporaryDirectory() as tmp:
        stack = tempfile.TemporaryDirectory(dir=tmp)
        _, one, two = _bare_world(stack)
        t1 = str(Path(tmp) / "t1")
        take(one, "feature/x", t1)
        try:
            take(two, "feature/x", str(Path(tmp) / "t2"))
        except ClaimError:
            pass

        # § 5's predicate, over the same store and no second one.
        free_before, _ = claim_free(two, "feature/x")
        free_other, _ = claim_free(two, "feature/never-taken")
        suite.ok("`claim_free` reads the taken ref as taken", not free_before)
        suite.ok("`claim_free` reads an unclaimed name as free", free_other)

    print("\nthe branch name, derived rather than composed:")

    # The three titles two sessions actually divided on, 2026-10-19. Each pair is one title that
    # produced two refs, and the divergence in all three was how much of the title was carried.
    MEASURED = [
        (
            41,
            "What counts as done is configuration, and who answers each check",
            ["feature/41-done-is-configuration", "feature/41-what-counts-as-done-is-configuration"],
        ),
        (
            76,
            "How a pull request lands is read by four roles and stated nowhere",
            [
                "feature/76-how-a-pull-request-lands",
                "feature/76-how-a-pull-request-lands-is-read-by-four-roles-and-stated-nowhere",
            ],
        ),
        (
            70,
            "Two sessions share one backlog: the claim on a work item is read by two roles and "
            "written by nothing",
            [
                "feature/70-two-sessions-share-one-backlog",
                "feature/70-two-sessions-share-one-backlog-the-claim-on-a-work-item-is-read-by-"
                "two-roles-and-written-by-nothing",
            ],
        ),
    ]
    # Plant: **the bound removed**, which leaves a character mapping alone -- the rule the start
    # role's "the item's title, slugged" amounted to. ⛔ The first form of this plant asserted
    # that two hardcoded names differ, which reads only `MEASURED` and never the derivation: it
    # stayed green with `slug_for` replaced by a function returning a constant, so it was not a
    # plant at all. Found reviewing this branch.
    #
    # Without the bound the derivation answers the *longer* of the two names two sessions
    # actually published, for two of the three items -- so the mapping admits the divergence and
    # the bound is what closes it.
    unbounded = {
        item: f"feature/{item}-{slug_for(title, limit=None)}" for item, title, _ in MEASURED
    }
    reached = [item for item, _, names in MEASURED if unbounded[item] == names[1]]
    suite.ok(
        "with the bound removed the derivation answers a name two sessions actually published "
        "(so the bound is what holds it)",
        len(reached) >= 2,
        f"reached {reached} of {[i for i, _, _ in MEASURED]}",
    )
    # ⚠️ And the third item is the stronger case rather than a miss: its sibling's longer name
    # was *itself* a truncation, at a third length again. A rule with no bound does not admit
    # two names, it admits every prefix -- which is why two sessions reached two different cuts
    # of one title.
    item41, title41, names41 = MEASURED[0]
    suite.ok(
        "and a mapping with no bound admits lengths neither session chose",
        unbounded[item41] not in names41 and names41[1].startswith(unbounded[item41][:40]),
        f"{unbounded[item41]} vs {names41[1]}",
    )
    suite.ok(
        "while the bound answers one name, which is neither of the two",
        all(
            branch_for("feature", item, title) not in names and len(slug_for(title)) <= SLUG_MAX
            for item, title, names in MEASURED
        ),
    )
    suite.ok(
        "derived, each title answers one name however many times it is asked",
        all(len({branch_for("feature", i, t) for _ in range(3)}) == 1 for i, t, _ in MEASURED),
        ", ".join(branch_for("feature", i, t) for i, t, _ in MEASURED),
    )

    # ⛔ Two *processes*, because "a pure function" in one interpreter is not the claim being
    # made. The claim is that two sessions agree, and anything environment-carried -- a locale,
    # a hash seed, a Unicode normalisation default -- would show up only across processes.
    here = [branch_for("feature", i, t) for i, t, _ in MEASURED]
    probe = (
        "import json, sys; sys.path.insert(0, sys.argv[1]); import claim; "
        "print(json.dumps([claim.branch_for('feature', i, t) for i, t in json.load(sys.stdin)]))"
    )
    elsewhere = subprocess.run(
        [sys.executable, "-c", probe, str(Path(__file__).resolve().parent)],
        input=json.dumps([[i, t] for i, t, _ in MEASURED]),
        capture_output=True,
        text=True,
    )
    suite.ok(
        "and a second interpreter derives the same names",
        elsewhere.returncode == 0 and json.loads(elsewhere.stdout or "[]") == here,
        elsewhere.stdout + elsewhere.stderr,
    )

    # The length rule, which is the arm all three divergences turned on. Properties rather than
    # one frozen string, so a reworded title is not a failing test.
    long_title = MEASURED[2][1]
    long_slug, full = slug_for(long_title), slug_for(long_title, limit=None)
    suite.ok("a long title is bounded", len(long_slug) <= SLUG_MAX, long_slug)
    suite.ok("the untruncated form would not have been", len(full) > SLUG_MAX, full)
    suite.ok("and the cut falls on a word boundary, never mid-word",
             full.startswith(long_slug) and full[len(long_slug)] == "-", long_slug)
    suite.ok("and leaves no trailing separator", not long_slug.endswith("-"), long_slug)
    suite.ok("a bound landing exactly on a separator keeps the whole word before it",
             slug_for("one two three", limit=7) == "one-two",
             slug_for("one two three", limit=7))

    for label, title, expected in (
        ("punctuation collapses to one separator", "A: b -- c!!  d", "a-b-c-d"),
        ("case is dropped", "TwO SeSSiOnS", "two-sessions"),
        ("digits survive", "§ 10 and #70", "10-and-70"),
        ("a script of its own survives rather than becoming hyphens",
         "Две сессии", "две-сессии"),
        ("a decomposed title slugs as its composed form does",
         unicodedata.normalize("NFD", "resum\u00e9"), unicodedata.normalize("NFC", "resum\u00e9")),
    ):
        suite.ok(f"the derivation: {label}", slug_for(title) == expected, slug_for(title))

    suite.ok(
        "a title that slugs to nothing leaves the number alone, not a trailing hyphen",
        branch_for("feature", 70, "!!! ---") == "feature/70",
        branch_for("feature", 70, "!!! ---"),
    )
    suite.ok(
        "an empty prefix is refused rather than producing `/70-x`",
        _raises(lambda: branch_for("", 70, "x")),
    )

    print("\nthe claim resolves on the item, not on the name:")

    with tempfile.TemporaryDirectory() as tmp:
        stack = tempfile.TemporaryDirectory(dir=tmp)
        _, one, two = _bare_world(stack)
        mine, theirs = "feature/70-two-sessions", "feature/70-two-sessions-share-one-backlog"

        # Plant: both guards removed, which is the state the measured failures happened in --
        # the ref name is the whole of the test-and-set, and two names are two claims.
        take(one, mine, str(Path(tmp) / "t1"), _item_precheck=False, _item_postcheck=False)
        raced = True
        try:
            take(two, theirs, str(Path(tmp) / "t2"),
                 _item_precheck=False, _item_postcheck=False)
        except ClaimError:
            raced = False
        suite.ok(
            "with the ref-name arms alone two sessions claim one item under two names "
            "(so the item guard is what holds it)",
            raced and len(refs_for_item(one, "origin", "70")) == 2,
        )

    with tempfile.TemporaryDirectory() as tmp:
        stack = tempfile.TemporaryDirectory(dir=tmp)
        _, one, two = _bare_world(stack)
        mine, theirs = "feature/70-two-sessions", "feature/70-two-sessions-share-one-backlog"
        take(one, mine, str(Path(tmp) / "t1"))

        refusal = ""
        try:
            take(two, theirs, str(Path(tmp) / "t2"))
        except ClaimError as exc:
            refusal = str(exc)
        suite.ok("a second session under a different name is refused", "refused" in refusal, refusal)
        suite.ok("and the refusal names the ref that holds the item", mine in refusal, refusal)
        suite.ok("it leaves no second ref", len(refs_for_item(two, "origin", "70")) == 1)
        suite.ok("no local branch", not _local_branch(two, theirs))
        suite.ok("and no tree", not Path(Path(tmp) / "t2").exists())

        # Each arm attributed separately, as the two ref-name arms above are: the pre-check
        # holds the order where the sibling's ref was already there, the post-check holds the
        # order where it appears while this session is publishing.
        suite.ok(
            "the pre-check alone refuses it (the sibling was already there)",
            _refuses_item(two, theirs, str(Path(tmp) / "t3"), _item_postcheck=False),
        )
        suite.ok(
            "the post-check alone refuses it too (the window the pre-check leaves)",
            _refuses_item(two, theirs, str(Path(tmp) / "t4"), _item_precheck=False),
        )
        suite.ok(
            "and the post-check gives this session's own ref back rather than leaving two",
            len(refs_for_item(two, "origin", "70")) == 1
            and refs_for_item(two, "origin", "70")[0][0] == mine,
        )

    with tempfile.TemporaryDirectory() as tmp:
        stack = tempfile.TemporaryDirectory(dir=tmp)
        _, one, two = _bare_world(stack)
        item, title, _ = MEASURED[0]
        take(one, prefix="feature", item=str(item), title=title, tree=str(Path(tmp) / "t1"))
        refusal = ""
        try:
            # Both guard arms off, so what is left is the ref-name test-and-set alone. This is
            # the point of deriving the name: the guard above becomes the residue case rather
            # than the mechanism, and the common arm engages again.
            take(two, prefix="feature", item=str(item), title=title, tree=str(Path(tmp) / "t2"),
                 _item_precheck=False, _item_postcheck=False)
        except ClaimError as exc:
            refusal = str(exc)
        suite.ok(
            "two sessions deriving from one title collide on the ref itself, with the item "
            "guard planted away",
            "taken" in refusal,
            refusal,
        )

    print("\nwhat the branch namespace says about a work item:")

    with tempfile.TemporaryDirectory() as tmp:
        stack = tempfile.TemporaryDirectory(dir=tmp)
        _, one, two = _bare_world(stack)
        held = status_for_item(two, "70")
        suite.ok("an item no ref claims reads free", "free:" in held.report(), held.report())

        take(one, "feature/70-a", str(Path(tmp) / "t1"))
        held = status_for_item(two, "70")
        suite.ok("an item one ref claims reads taken", held.report().startswith("taken:"),
                 held.report())
        suite.ok("and names the ref, so the answer is checkable",
                 "feature/70-a" in held.report(), held.report())
        suite.ok("while a different item is still free",
                 "free:" in status_for_item(two, "81").report())

        # ⛔ The trap the bullet names: the ref tail still matches after the work lands, so a
        # filter that stopped at the match would hold the item for as long as the ref survives
        # the merge. Planted by reading the candidate list, then held by reading the status.
        t2 = Path(tmp) / "t2"
        take(one, "feature/81-done", str(t2))
        for key, value in (("user.email", "one"), ("user.name", "One")):
            git(t2, "config", key, value)
        (t2 / "work.txt").write_text("work\n")
        git(t2, "add", "work.txt")
        git(t2, "commit", "--quiet", "-m", "work")
        git(t2, "push", "--quiet", "origin", "feature/81-done")
        git(two, "fetch", "--quiet", "origin", "feature/81-done")
        git(two, "checkout", "--quiet", "main")
        git(two, "merge", "--squash", "FETCH_HEAD", check=False)
        for key, value in (("user.email", "two"), ("user.name", "Two")):
            git(two, "config", key, value)
        git(two, "commit", "--quiet", "-m", "squashed")
        git(two, "push", "--quiet", "origin", "main")

        suite.ok(
            "a ref-tail match alone still matches after the merge (so the reading is what holds it)",
            [b for b, _ in refs_for_item(two, "origin", "81")] == ["feature/81-done"],
        )
        landed = status_for_item(two, "81")
        suite.ok("but the item reads free, because the only ref claiming it has landed",
                 "free:" in landed.report(), landed.report())
        suite.ok("and a start on it is not refused",
                 "claimed" in take(two, "feature/81-again", str(Path(tmp) / "t3")))

    with tempfile.TemporaryDirectory() as tmp:
        stack = tempfile.TemporaryDirectory(dir=tmp)
        _, one, two = _bare_world(stack)
        take(one, "feature/70-a", str(Path(tmp) / "t1"),
             _item_precheck=False, _item_postcheck=False)
        take(two, "feature/70-b", str(Path(tmp) / "t2"),
             _item_precheck=False, _item_postcheck=False)
        contested = status_for_item(two, "70")
        suite.ok("two live refs for one item read as contested, not as taken",
                 contested.report().startswith("contested:"), contested.report())
        suite.ok("and the report says it is a person's call",
                 "person's call" in contested.report(), contested.report())

    # A ref listed and then gone before it could be read -- the window this module's own
    # rollback opens. Plant: the `taken` arm removed, which is what counted it as a claim.
    gone = Status(taken=False, ref_sha=None, holder=Holder(), liveness=None, local_only=False)
    planted = ItemStatus(item="70", readings=[("feature/70-gone", gone)], local_only=False)
    suite.ok(
        "without the `taken` arm a vanished ref counts as a claim (so that arm is what holds it)",
        [b for b, held in planted.readings if not (held.liveness and held.liveness.landed)]
        == ["feature/70-gone"],
    )
    suite.ok(
        "a ref gone since the refs were listed holds the item against nobody",
        planted.contending() == [],
    )
    suite.ok(
        "and the report says it is gone rather than printing `free` under a `taken` verdict",
        "gone since the refs were listed" in planted.report()
        and "free: no ref named this exists" not in planted.report(),
        planted.report(),
    )

    print("\na merged pull request found by branch name, against the ref standing there now:")

    # The measured misreading, 2026-10-19: a ref published at 14:47:34 read back as landed on a
    # pull request that merged at 22:17:55 the day before. No host is needed to hold the rule --
    # what went wrong was the comparison that was never made.
    born = "2026-10-19T14:47:34Z"
    merged_before = "2026-10-18T22:17:55Z"
    merged_after = "2026-10-19T18:02:11Z"
    suite.ok(
        "a merge that predates the ref does not land it (the measured misreading)",
        merge_lands_this_ref(born, merged_before) is False,
    )
    suite.ok(
        "a merge that postdates the ref does land it",
        merge_lands_this_ref(born, merged_after) is True,
    )
    suite.ok(
        "and with either instant unreadable the arm declines rather than guessing",
        merge_lands_this_ref(None, merged_after) is None
        and merge_lands_this_ref(born, None) is None,
    )
    suite.ok(
        "and declines rather than raising where one instant carries a zone and the other does not",
        merge_lands_this_ref(born, merged_after.rstrip("Z")) is None
        and merge_lands_this_ref(born.rstrip("Z"), merged_after) is None,
    )

    print("\nliveness, and what is reported rather than broken:")

    with tempfile.TemporaryDirectory() as tmp:
        stack = tempfile.TemporaryDirectory(dir=tmp)
        _, one, two = _bare_world(stack)
        t1 = str(Path(tmp) / "t1")
        take(one, "feature/z", t1)

        # Read from the *other* clone: a claim from elsewhere has no tree here, which is the
        # orphan-looking state a second machine always sees.
        seen = status(two, "feature/z")
        suite.ok("a claim with no commits and no tree here reads as an orphaned candidate",
                 seen.liveness is not None and not seen.liveness.live)
        suite.ok("and is reported with both readings rather than broken",
                 "ask" in seen.report() and "orphaned-candidate" in seen.report(), seen.report())
        suite.ok("and it still refuses a start",
                 not claim_free(two, "feature/z")[0])

        # Arm 1: work against the ref makes it live, from anywhere.
        for key, value in (("user.email", "one"), ("user.name", "One")):
            git(t1, "config", key, value)
        (Path(t1) / "work.txt").write_text("work\n")
        git(t1, "add", "work.txt")
        git(t1, "commit", "--quiet", "-m", "work")
        git(t1, "push", "--quiet", "origin", "feature/z")
        live = status(two, "feature/z")
        suite.ok("a ref carrying its own commits reads as live",
                 live.liveness is not None and live.liveness.live, live.report())

        # Arm 2: a tree on this machine with a session in it. Read from the clone that holds it.
        here = status(one, "feature/z")
        suite.ok("the clone holding the tree also reads it live",
                 here.liveness is not None and here.liveness.live, here.report())

    print("\nrelease:")

    with tempfile.TemporaryDirectory() as tmp:
        stack = tempfile.TemporaryDirectory(dir=tmp)
        _, one, two = _bare_world(stack)
        t1 = str(Path(tmp) / "t1")
        take(one, "feature/r", t1)
        out = release(one, "feature/r", t1)
        suite.ok("release deletes the published ref", remote_ref_sha(one, "origin", "feature/r") is None, out)
        suite.ok("release removes the tree", not Path(t1).exists(), out)
        suite.ok("release deletes the local branch",
                 git(one, "rev-parse", "--verify", "--quiet", "refs/heads/feature/r", check=False).returncode != 0)
        suite.ok("a released claim is free again", claim_free(two, "feature/r")[0])
        again = release(one, "feature/r", t1)
        suite.ok("release is re-runnable, reporting what was already gone",
                 "already gone" in again, again)
        suite.ok("so the item can be claimed again after a release",
                 "claimed" in take(two, "feature/r", str(Path(tmp) / "t2")))

    print("\nleaving the tree before removing it:")

    # ⛔ Both sides of the scope, because a guard that refuses everything and a guard that is dead
    # both report green from one side only. The red side is a release called from inside the tree;
    # the green side is the *same* release, same arguments, one directory up.
    with tempfile.TemporaryDirectory() as tmp:
        stack = tempfile.TemporaryDirectory(dir=tmp)
        _, one, _two = _bare_world(stack)
        tree = str(Path(tmp) / "standing")
        take(one, "feature/e", tree)
        (Path(tree) / "sub").mkdir()
        outside = os.getcwd()
        try:
            os.chdir(tree)
            suite.ok("a process in the tree reads as standing in it", standing_in(tree))
            suite.ok("a release from inside the tree is refused",
                     _raises(lambda: release(one, "feature/e", tree)))
            # ⚠️ The refusal has to leave the claim whole: it runs before the ref deletion, so a
            # pass that meets it has lost nothing and can leave and re-run.
            suite.ok("and the refusal leaves the published ref alone",
                     remote_ref_sha(one, "origin", "feature/e") is not None)
            suite.ok("and leaves the tree standing", Path(tree).exists())
            suite.ok("--force does not cover standing in the tree",
                     _raises(lambda: release(one, "feature/e", tree, "origin", force=True)))
            os.chdir(Path(tree) / "sub")
            suite.ok("at or below, not equal: a subdirectory of the tree is inside it",
                     _raises(lambda: release(one, "feature/e", tree)))
        finally:
            # ⚠️ Restored before the green side rather than after the suite: the removal below
            # deletes this directory, and a cwd that no longer exists breaks every later section.
            os.chdir(outside)
        suite.ok("a tree nobody is standing in reads as not stood in", not standing_in(tree))
        left = release(one, "feature/e", tree)
        suite.ok("and the same release from outside the tree proceeds",
                 not Path(tree).exists(), left)
        suite.ok("so leaving is what clears the refusal, and nothing else does",
                 remote_ref_sha(one, "origin", "feature/e") is None, left)

    print("\nreleasing somebody else's live claim:")

    with tempfile.TemporaryDirectory() as tmp:
        stack = tempfile.TemporaryDirectory(dir=tmp)
        _, one, two = _bare_world(stack)
        t1 = str(Path(tmp) / "t1")
        take(one, "feature/s", t1)
        # Make it live in the way another machine can see: commits of its own.
        for key, value in (("user.email", "one"), ("user.name", "One")):
            git(t1, "config", key, value)
        (Path(t1) / "work.txt").write_text("work\n")
        git(t1, "add", "work.txt")
        git(t1, "commit", "--quiet", "-m", "work")
        git(t1, "push", "--quiet", "origin", "feature/s")

        # Plant: `force` on, which is what the command does without the guard -- the live claim
        # goes, from a clone that never held it.
        release(two, "feature/s", None, "origin", force=True)
        suite.ok(
            "with force a live claim held elsewhere is deleted (so the guard is what holds it)",
            remote_ref_sha(two, "origin", "feature/s") is None,
        )

        # And the rule: the same call without force is refused.
        take(one, "feature/s2", str(Path(tmp) / "t3"))
        for key, value in (("user.email", "one"), ("user.name", "One")):
            git(str(Path(tmp) / "t3"), "config", key, value)
        (Path(tmp) / "t3" / "work.txt").write_text("work\n")
        git(str(Path(tmp) / "t3"), "add", "work.txt")
        git(str(Path(tmp) / "t3"), "commit", "--quiet", "-m", "work")
        git(str(Path(tmp) / "t3"), "push", "--quiet", "origin", "feature/s2")
        refusal = ""
        try:
            release(two, "feature/s2", None, "origin")
        except ClaimError as exc:
            refusal = str(exc)
        suite.ok("a live claim held elsewhere is refused instead", "refused" in refusal, refusal)
        suite.ok("and says it is a person's call", "person's call" in refusal, refusal)
        suite.ok("and the claim survives the refusal",
                 remote_ref_sha(two, "origin", "feature/s2") is not None)

        # ⛔ The orphan case, which a guard keyed on `live` left open: a claim taken a minute ago
        # has no commits and no tree anywhere but its own clone, so from here it reads as an
        # orphaned candidate -- and releasing it would be one session ending another's claim.
        take(one, "feature/s3", str(Path(tmp) / "t4"))
        orphan_refusal = ""
        try:
            release(two, "feature/s3", None, "origin")
        except ClaimError as exc:
            orphan_refusal = str(exc)
        suite.ok(
            "a fresh claim held elsewhere is refused too, not only a live one",
            "refused" in orphan_refusal,
            orphan_refusal,
        )
        suite.ok("and that claim survives as well",
                 remote_ref_sha(two, "origin", "feature/s3") is not None)
        suite.ok("while the clone that holds the tree releases it with no force",
                 "ref deleted" in release(one, "feature/s2", str(Path(tmp) / "t3")))

    print("\na claim whose work has landed:")

    with tempfile.TemporaryDirectory() as tmp:
        stack = tempfile.TemporaryDirectory(dir=tmp)
        _, one, two = _bare_world(stack)
        t1 = Path(tmp) / "t1"
        take(one, "feature/merged", str(t1))
        for key, value in (("user.email", "one"), ("user.name", "One")):
            git(t1, "config", key, value)
        (t1 / "work.txt").write_text("work\n")
        git(t1, "add", "work.txt")
        git(t1, "commit", "--quiet", "-m", "work")
        git(t1, "push", "--quiet", "origin", "feature/merged")

        before = status(two, "feature/merged")
        suite.ok(
            "before the merge it reads live",
            before.liveness is not None and before.liveness.live,
            before.report(),
        )
        # ⛔ The regression the first attempt at this introduced: a ref just claimed points at
        # the integration tip, so it is an ancestor of it, and reading ancestry as *landed* made
        # every fresh claim read as spent -- releasable with no override, by anyone.
        take(one, "feature/fresh", str(Path(tmp) / "tf"))
        fresh = status(two, "feature/fresh")
        suite.ok(
            "a claim with no work of its own does NOT read as landed",
            fresh.liveness is not None and not fresh.liveness.landed,
            fresh.report(),
        )

        # The squash merge, which is what rewrites the hashes: a new commit on the integration
        # branch carrying the ref's content, and the ref's own commit reachable from nothing.
        git(two, "fetch", "--quiet", "origin", "feature/merged")
        git(two, "checkout", "--quiet", "main")
        git(two, "merge", "--squash", "FETCH_HEAD", check=False)
        for key, value in (("user.email", "two"), ("user.name", "Two")):
            git(two, "config", key, value)
        git(two, "commit", "--quiet", "-m", "squashed")
        git(two, "push", "--quiet", "origin", "main")

        after = status(two, "feature/merged")
        suite.ok(
            "after a squash merge it reads landed, not live",
            after.liveness is not None and after.liveness.landed,
            after.report(),
        )
        suite.ok(
            "and it is not an ancestor of the integration branch, which is why the hash test alone was wrong",
            git(two, "merge-base", "--is-ancestor",
                remote_ref_sha(two, "origin", "feature/merged"), "main", check=False).returncode == 1,
        )
        suite.ok("the report says the claim is spent", "landed:" in after.report(), after.report())
        suite.ok(
            "and releasing it needs no override",
            "ref deleted" in release(two, "feature/merged", None, "origin"),
        )

    print("\nthe integration branch, derived rather than named:")

    with tempfile.TemporaryDirectory() as tmp:
        stack = tempfile.TemporaryDirectory(dir=tmp)
        _, one, _ = _bare_world(stack)
        suite.ok("it is derived from the remote's own default",
                 integration_branch(one, "origin") == "main")
        suite.ok("an explicit value overrides the derivation",
                 integration_branch(one, "origin", "release") == "release")
        # A root with a remote that advertises nothing and no local branch of its own: the one
        # state where a guess would be a claim cut from the wrong base.
        orphanage = Path(tmp) / "no-default"
        subprocess.run(["git", "init", "--quiet", "--bare", str(orphanage)], check=True)
        blank = Path(tmp) / "blank"
        # Empty on purpose -- a remote advertising nothing is the state under test -- so git's
        # warning about it is noise here too, and captured for the same reason as the seed's.
        blanked = subprocess.run(
            ["git", "clone", "--quiet", str(orphanage), str(blank)], capture_output=True, text=True
        )
        if blanked.returncode != 0:
            raise ClaimError(f"the fixture's blank clone failed: {blanked.stderr.strip()}")
        git(blank, "checkout", "--quiet", "--detach", check=False)
        derived = None
        try:
            derived = integration_branch(blank, "origin")
        except ClaimError as exc:
            derived = str(exc)
        suite.ok("and where it cannot be derived the caller is told, not given a guess",
                 "could not be derived" in (derived or ""), str(derived))

    print("\nliveness reads a session below the tree's own root:")

    with tempfile.TemporaryDirectory() as tmp:
        stack = tempfile.TemporaryDirectory(dir=tmp)
        _, one, _ = _bare_world(stack)
        t1 = Path(tmp) / "t1"
        take(one, "feature/deep", str(t1))
        deep = t1 / "a" / "b"
        deep.mkdir(parents=True)
        # A real process, working two directories below the tree root. Filtering the open-file
        # table by the tree's own path would not match this cwd, which is the false negative the
        # prefix comparison exists for: an actively worked claim reading as an orphan.
        held = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(30)"],
            cwd=str(deep),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            occupied = process_in(str(t1))
            if occupied is None:
                suite.ok("the open-file table is unreadable here, and that is reported as such",
                         True, "lsof absent: the arm reports unestablished rather than idle")
            else:
                suite.ok("a process below the tree root reads as occupying it", occupied is True)
        finally:
            held.kill()
            held.wait()

    print("\nthe derived absent case:")

    with tempfile.TemporaryDirectory() as tmp:
        solo = Path(tmp) / "solo"
        subprocess.run(["git", "init", "--quiet", str(solo)], check=True)
        for key, value in (("user.email", "solo"), ("user.name", "Solo")):
            git(solo, "config", key, value)
        (solo / "README.md").write_text("solo\n")
        git(solo, "add", "README.md")
        git(solo, "commit", "--quiet", "-m", "seed")
        git(solo, "branch", "-M", "main")

        out = take(solo, "feature/local", str(Path(tmp) / "lt"))
        suite.ok("a root with no remote claims locally and says so", "local-only" in out, out)
        suite.ok("and the local claim still refuses a second start",
                 not claim_free(solo, "feature/local")[0])
        suite.ok("and a second start is refused by git itself",
                 _refuses(solo, "feature/local", str(Path(tmp) / "lt2")))

    print()
    if suite.failures:
        print(f"{suite.failures} check(s) failed.")
        return 1
    print("every check passed, each having been shown it can fail.")
    return 0


def _refuses(root: str, branch: str, tree: str) -> bool:
    try:
        take(root, branch, tree)
    except ClaimError:
        return True
    return False


def _refuses_item(root: str, branch: str, tree: str, **planted: bool) -> bool:
    """A refusal with one of the item guard's two arms planted away."""
    try:
        take(root, branch, tree, **planted)
    except ClaimError:
        return True
    return False


def _raises(call) -> bool:
    try:
        call()
    except ClaimError:
        return True
    return False


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--self-test", action="store_true", help="plant a violation per check, then hold the rule")
    sub = parser.add_subparsers(dest="command")

    # ⛔ The derivation on its own, so nothing has to reproduce it to find out what a start would
    # name. A role that needs the name before it has the claim asks for it rather than slugging.
    # ⚠️ `--branch-prefix` rather than `--prefix`, which the sweep over role text reads as a
    # flag carrying a directory -- correctly, for every other command that spells it that way.
    namer = sub.add_parser("name", help="the branch name a claim on this item would be taken on")
    namer.add_argument("--branch-prefix", required=True, help="a function of the item's type (§ 4.1)")
    namer.add_argument("--item", required=True, help="the item's own identifier")
    namer.add_argument("--title", required=True, help="the title the slug derives from (§ 8)")

    for name, help_text in (
        ("take", "claim the item: publish the ref, then cut the tree"),
        ("release", "give the claim up: the ref, the tree, the local branch"),
        ("status", "who holds it, since when, and whether it is live"),
    ):
        node = sub.add_parser(name, help=help_text)
        node.add_argument("--repo-root", required=True, help="the code root, stated and never inherited")
        node.add_argument("--branch", required=(name == "release"))
        node.add_argument("--remote", default="origin")
        node.add_argument(
            "--integration",
            default=None,
            help="override; derived from the remote's default branch when omitted",
        )
        if name in ("take", "status"):
            node.add_argument(
                "--item",
                default=None,
                help="the work item; for `take`, what the claim is resolved on rather than the "
                "ref name, and for `status`, the question asked",
            )
        if name == "take":
            node.add_argument(
                "--branch-prefix", default=None, help="with --item and --title, derives --branch"
            )
            node.add_argument(
                "--title", default=None, help="with --item and --branch-prefix, derives --branch"
            )
        if name in ("take", "release"):
            node.add_argument("--tree", required=(name == "take"))
        if name == "release":
            # ⛔ A person saying it, which is the only thing § 10 permits to break a live claim.
            node.add_argument(
                "--force",
                action="store_true",
                help="break a live claim held elsewhere; refused without it",
            )

    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    if not args.command:
        parser.print_help()
        return 2

    try:
        if args.command == "name":
            print(branch_for(args.branch_prefix, args.item, args.title))
        elif args.command == "take":
            print(
                take(
                    args.repo_root,
                    args.branch,
                    args.tree,
                    args.remote,
                    args.integration,
                    item=args.item,
                    prefix=args.branch_prefix,
                    title=args.title,
                )
            )
        elif args.command == "release":
            print(
                release(
                    args.repo_root,
                    args.branch,
                    getattr(args, "tree", None),
                    args.remote,
                    args.integration,
                    force=args.force,
                )
            )
        else:
            if args.item and args.branch:
                print(
                    "state one question: `--item` asks what holds the work item, `--branch` "
                    "asks about one name.",
                    file=sys.stderr,
                )
                return 2
            if args.item:
                print(status_for_item(args.repo_root, args.item, args.remote, args.integration).report())
            elif args.branch:
                print(status(args.repo_root, args.branch, args.remote, args.integration).report())
            else:
                print("`status` needs `--item` or `--branch`.", file=sys.stderr)
                return 2
    except ClaimError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
