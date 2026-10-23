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

# How long a slug may be. A bound is needed for the cut to be part of the derivation rather than
# a thing the filesystem does later at a length that varies by machine; the value is a readability
# choice and nothing reads it but the derivation below. ⚠️ It bounds the **slug**, and the tree's
# leaf and the branch's last segment carry `<identifier>-` in front of it, so a leaf runs a few
# characters longer than this.
SLUG_MAX = 18

# The words the derivation drops before it starts counting, so that what survives the bound is
# the title's own nouns and verbs rather than its first four articles and prepositions.
#
# ⛔ **This is a list of function words in one language and not a general rule**, which is the one
# thing about it worth stating rather than discovering: § 8 has the slug derived from the title as
# the *repository's* language writes it, and for a repository writing its items in another
# language nothing here matches, nothing is dropped, and the bound alone applies. That is a
# weaker derivation in that case and not a broken one -- the result is still a pure function of
# the string, which is the whole of what two sessions have to agree on.
#
# ⚠️ It is deliberately **not** on the configuration surface. A per-project list would put a
# cosmetic choice in every adopter's configuration file and give two sessions reading two
# configurations two spellings of one item's branch, which is the defect this derivation exists
# to close rather than a feature.
#
# ⛔ Negations are not here. `no`, `not`, `nothing` and `never` carry the whole meaning of a great
# many titles, and a slug that drops them names the opposite of its item.
MINOR_WORDS = frozenset(
    """
    a an the this that these those it its their
    and or nor but so if than then as
    of to in on at by for from with into onto over under through
    about after before between against per
    is are was were be been being am
    has have had do does did can could will would may might must should
    which who whom whose what when where how why there here
    """.split()
)

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


def slug_for(
    title: str, limit: int | None = SLUG_MAX, minor: frozenset[str] = MINOR_WORDS
) -> str:
    """The item's title as a branch slug: a pure function of the string it is handed.

    ⚠️ **Of the string it is handed**, which is not always the title as the tracker stores it:
    where the item's language differs from the repository's, § 8 requires a translation, and the
    translation is the caller's. That is the one input two sessions are not guaranteed to agree
    on, and it is why the claim resolves on the *item* and not on the name -- see
    `refs_for_item` below.

    Normalised to NFC first so a decomposed title and a composed one slug alike; letters and
    numbers survive by Unicode category rather than by an ASCII range, because a project writing
    its items in its own script gets a ref it can read rather than a row of hyphens.

    ⛔ **Words are selected, and never cut.** The bound is spent on whole words of the title --
    its function words (`minor`) dropped first, a word already taken not taken twice, and words
    added in the title's own order while the next one still fits. A title whose *first* surviving
    word is longer than the bound keeps that word whole and overruns, because a slug holding half
    a word is less readable than a long one and the overrun is bounded by the title.

    ⚠️ `limit` is the derivation's own and `minor` is too; `None` and the empty set are what the
    suite reads the unbounded and unselected forms with. ⛔ **The bound is part of the rule
    rather than something the filesystem imposes later at a length that varies by machine.** It
    is the arm that has actually broken: of the three measured divergences, all three were one
    session carrying the whole title and another carrying the first few words, and a character
    mapping with no length rule licenses both.
    """
    text = unicodedata.normalize("NFC", title).strip().lower()
    kept = "".join(ch if unicodedata.category(ch)[0] in ("L", "N") else "-" for ch in text)
    every = [word for word in re.sub(r"-+", "-", kept).strip("-").split("-") if word]
    # A single character is dropped with the function words: it is what a possessive or a
    # contraction leaves behind once the apostrophe has become a separator (`host's` -> `host`,
    # `s`), and it carries nothing.
    major: list[str] = []
    for word in every:
        if len(word) > 1 and word not in minor and word not in major:
            major.append(word)
    # ⚠️ The fallback is the arm that keeps a short title from slugging to nothing: `A: b -- c`
    # and a title that is all function words have no major word at all, and the number alone is
    # a worse answer than the title's own words.
    chosen = major or every
    if not chosen:
        return ""
    if limit is None:
        return "-".join(chosen)
    slug = chosen[0]
    for word in chosen[1:]:
        if len(slug) + 1 + len(word) > limit:
            break
        slug = f"{slug}-{word}"
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


def tree_for(tree_dir: str | Path, item: str, title: str) -> Path:
    """`(tree_dir, number, slug)` — the tree's path, composed where the branch name is.

    ⛔ **The identifier leads and the slug follows**, and that ordering is the whole of what the
    earlier leaf rule protected. A leaf of `<item>` alone was chosen so the directory would keep
    answering *is this item being worked* across a reworded title; `<item>-<slug>` keeps that
    answerable on the `<item>-` prefix, which is the form anything asking the directory has to
    match on anyway -- a leaf is a candidate test and never the answer, because the ref arbitrates
    (`refs_for_item`), exactly as `ref_is_for_item` is a candidate test over ref names.

    ⚠️ **It carries no divergence the branch name does not already carry.** The slug is
    `slug_for`'s, not a second rule and not prose for a role to apply: two sessions handed one
    title derive one leaf, and two sessions handed two titles already derive two *branch names*,
    which is the thing the ref refuses. A reword between two starts is therefore a second name
    before it is a second directory, and the refusal lands on the name.

    A title that slugs to nothing leaves the identifier alone, as `branch_for` does: `70-` is a
    directory nobody can read.

    ⛔ **An item is required here, and a branch with no item passes its path instead.** Deriving
    from an empty identifier would put every such branch in one directory.
    """
    item = str(item).strip()
    if not str(tree_dir).strip():
        raise ClaimError(
            "the tree directory is empty; it is `branch_model.tree_dir` (§ 10) and not a value "
            "this module defaults."
        )
    if not item:
        raise ClaimError(
            "the tree cannot be derived without the item; a branch carrying no item states "
            "`--tree` instead."
        )
    slug = slug_for(title)
    return Path(tree_dir) / (f"{item}-{slug}" if slug else item)


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


def a_work_tree(path: str, main_tree: str) -> bool:
    """Is this registered worktree one a role could be working an item in?

    ⛔ **A tree the harness cut for a helper is not a work tree**, and § 10's
    session reading does not separate them: that reading tells a helper *process*
    holding a directory from a session working in it, and this is a helper
    *tree*, registered in the repository by whatever spawned it.

    ⚠️ **Nesting is the test, because naming is not available.** § 10 refuses a
    list of process names for the process case -- a helper belongs to whichever
    harness ships it, so naming one puts a project's value in shared code -- and
    a directory name is the same value under a different spelling. What is
    structural instead: the main checkout is a work tree under `in_place`, where
    the branch is held in the checkout itself; a tree cut at `tree_dir` is one
    under `worktree`, and that is a location outside the checkout's own tree. A
    registered worktree *nested below* the main checkout is therefore neither, in
    either model.

    ⚠️ **It fails in the direction that keeps a tree.** A project whose trees did
    live inside its checkout would resolve none of them here and would name the
    tree explicitly instead, which `take` already requires and `release` already
    accepts -- a tree not found rather than the wrong tree removed.
    """
    here, main = os.path.realpath(path), os.path.realpath(main_tree)
    if here == main:
        return True
    return not here.startswith(main + os.sep)


def tree_for_branch(root: str | Path, branch: str) -> str | None:
    """The working tree holding this branch on this machine, or None.

    ⛔ A helper's tree is not an answer here. `git worktree list` reports every
    registered worktree, which includes the per-agent trees a harness cuts inside
    the checkout, and this function's answer is what `release` removes: pointed
    at a finished helper's tree it removed it as though it were the item's, and
    at a live one it demanded the override § 10 reserves for breaking another
    session's work. `a_work_tree` above states which is which.
    """
    proc = git(root, "worktree", "list", "--porcelain")
    # ⚠️ The first entry is the main worktree, which is what the nesting test is
    # taken against -- rather than `root`, which may be any worktree of the
    # repository, including the one this process is standing in.
    main_tree: str | None = None
    path: str | None = None
    for line in proc.stdout.splitlines():
        if line.startswith("worktree "):
            path = line[len("worktree ") :].strip()
            if main_tree is None:
                main_tree = path
        elif line.startswith("branch ") and line[len("branch ") :].strip() == REFS_PREFIX + branch:
            # A branch is checked out in at most one worktree, so this is the
            # only candidate and there is nothing further to read.
            if path and main_tree and a_work_tree(path, main_tree):
                return path
            return None
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
    not writes wherever the shell lands -- the directory the session was launched in, which under
    this branch model is the shared checkout.

    ⛔ **At or below, never equal**, for the same reason `process_in` carries that correction: a
    session's working directory is routinely a subdirectory of its tree, and an equality test
    answers *not standing there* for a session that is.

    ⚠️ This reads **this** process and `process_in` reads every other one. They answer different
    questions and `release` takes both: the caller's own tree is stopped on, with the stop
    clearable by leaving, and a sibling's is refused until that session is done. ⛔ **Neither
    substitutes for the other** -- this one cannot see a sibling, and `process_in` cannot tell the
    caller apart from one, so a release holding only `process_in` would refuse itself forever.
    """
    try:
        here = os.path.realpath(os.getcwd())
    except OSError:
        # ⚠️ An unreadable cwd *is* the deleted-out-from-under case, already arrived. There is no
        # live directory left to protect, so the removal may proceed and clean up after it.
        return False
    root = os.path.realpath(path)
    return here == root or here.startswith(root + os.sep)


def own_session_ids() -> set[int]:
    """The POSIX sessions this run spans: this process's, and every ancestor's.

    ⛔ **This process's own session is not enough, and assuming it was shipped a fix that did not
    fix the measured case.** Measured 2026-10-19: the harness runs each command in a session of
    its own, so the caller is the odd one out rather than the helper -- the keep-awake process sat
    in session 29936 with the harness that spawned it, while the release sat in 30947, newly made
    for that one call. Comparing the two said *another session* about a sibling of the caller.

    ⚠️ **So the run is the ancestor chain, not the process.** Walking it collects the harness's
    session along the way, which is the one anything the harness started will be in.

    ⛔ **The failure direction is deliberate.** An ancestor that cannot be read stops the walk, so
    the set is smaller, so more processes read as foreign -- which refuses a removal rather than
    performing one. ⚠️ And what a too-large set can misread is another run's *helper*, never its
    work: a sibling doing work holds a session of its own, made the same way this caller's was,
    and no ancestor of this process is in it.
    """
    ids: set[int] = set()
    pid = os.getpid()
    seen: set[int] = set()
    while pid > 1 and pid not in seen:
        seen.add(pid)
        try:
            ids.add(os.getsid(pid))
        except OSError:
            pass
        proc = subprocess.run(
            ["ps", "-o", "ppid=", "-p", str(pid)], capture_output=True, text=True
        )
        parent = proc.stdout.strip()
        if not parent.isdigit():
            break
        pid = int(parent)
    return ids


def foreign_occupants(path: str) -> list[tuple[int, str]] | None:
    """Live processes of **another session** working at or below `path`. None where unreadable.

    ⛔ **Occupancy is not "any process holding this working directory", which is what `release`
    shipped first and what refused its own cleanup inside the hour.** Measured 2026-10-19: a
    `caffeinate` the harness had started *while* the session was in its tree still carried that
    directory after the session left, so the tree read as occupied by a process holding an
    inherited descriptor and doing nothing. The refusal was correct on its own terms and wrong
    about the world, and the override reserved for destroying somebody's work had to be passed to
    clean up a tree nobody was in -- which is how an override stops meaning anything.

    ⛔ **The distinction is the POSIX session, which is what *another live session* already
    says** -- but of the **run** rather than of this process, which is `own_session_ids`'s whole
    subject and the correction that made this work on the case it was written for. A helper the
    run started sits in a session this run spans; a separate run -- another terminal, another
    agent -- does not. ⚠️ **The working directory alone cannot carry it**: a
    session doing work and an abandoned helper are identical in the open-file table, the
    directory being the only tie either has. So the reading is on identity, not on behaviour.

    ⛔ **And a list of process names is not the answer.** `caffeinate` is one harness's helper and
    the next ships something else, so a carrier naming it would be a project's value in shared
    code -- which this repository's own sweep refuses.

    ⚠️ **Returns the occupants rather than a verdict.** A refusal that cannot say *who* costs the
    reader an `lsof` of their own, which is exactly what the measured incident cost.
    """
    if not shutil.which("lsof"):
        return None
    proc = subprocess.run(
        ["lsof", "-a", "-d", "cwd", "-F", "pcn"], capture_output=True, text=True
    )
    root = os.path.realpath(path)
    mine = own_session_ids()
    found: list[tuple[int, str]] = []
    pid: int | None = None
    command = ""
    read_any = False
    for line in proc.stdout.splitlines():
        tag, value = line[:1], line[1:]
        if tag == "p":
            pid = int(value) if value.isdigit() else None
            command = ""
        elif tag == "c":
            command = value
        elif tag == "n" and pid is not None:
            read_any = True
            cwd = os.path.realpath(value)
            if cwd != root and not cwd.startswith(root + os.sep):
                continue
            try:
                theirs = os.getsid(pid)
            except ProcessLookupError:
                # ⚠️ Gone between the listing and the question: not an occupant.
                continue
            except OSError:
                # ⛔ Unaskable is not absent. A process we may not ask about counts, for the same
                # reason an unreadable table does -- the failure direction here deletes a tree.
                found.append((pid, command))
                continue
            if theirs not in mine:
                found.append((pid, command))
    if not read_any:
        return None
    return found


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
    tree_dir: str | None = None,
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

    **The tree's path is derived the same way**, from `(tree_dir, item, title)`, and for the same
    reason: the leaf carries a slug, and a leaf slugged by a role rather than by `slug_for` is the
    divergence the branch derivation exists to close, reintroduced one argument over. An explicit
    `tree` is still accepted — it is what a branch carrying no item uses, and `tree_dir` is the
    configured directory rather than a path.

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
    if tree is not None and tree_dir is not None:
        raise ClaimError(
            "state one: `--tree-dir` is the configured directory and the leaf is derived, "
            "`--tree` is the whole path stated."
        )
    if tree is None and tree_dir is not None:
        if not (item and title is not None):
            raise ClaimError(
                "deriving the tree needs `--item` and `--title`; a branch carrying no item "
                "states `--tree` instead."
            )
        tree = str(tree_for(tree_dir, item, title))
    if tree is None:
        raise ClaimError(
            "a claim needs the tree it is cut into: `--tree-dir` for § 10's derived path, or "
            "`--tree` where the path is stated."
        )
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
    keep_ref: bool = False,
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

    ⛔ **A tree a *sibling* session is working in is refused too, and `--force` does cover that
    one.** The two refusals are deliberately asymmetric: nothing the caller can do clears its own
    occupancy except leaving, while a sibling's is a person's call -- the same call `--force`
    already names. ⚠️ **What it costs is stated in the refusal rather than left to the flag**,
    because forcing here destroys whatever the tree holds that git does not track, and everywhere
    else `--force` costs only a ref.

    ⛔ **`keep_ref` gives up everything but the published ref.** Who deletes a branch on the host
    is § 2's `delete_branch` and nothing else, and under `never` nobody does -- so a release that
    took the ref regardless would undo a stated value from the one step whose business is the
    tree. ⚠️ **It costs the claim nothing, which is the whole reason the option is affordable**:
    `status` reads a claim whose work has landed as spent whether or not its ref is still
    standing, so the item is free again either way and a kept ref holds nothing against anybody.
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

    # ⛔ The caller is not the only session that can be in the tree, and the claim guard below
    # does not reach a sibling: `spent` short-circuits it, so a *landed* claim whose tree somebody
    # else is working in fell through both and was removed with `--force`. § 10 keeps a tree
    # another live session occupies, and what it costs that session is not a ref but everything
    # in the tree git does not track.
    if doomed and not force and Path(doomed).exists():
        # ⛔ Another *session*, not any process: this run's own helpers inherit the tree's
        # directory and outlive its use of the tree, and counting them refused this command's
        # own cleanup. `foreign_occupants` carries that reading and the measurement behind it.
        occupants = foreign_occupants(doomed)
        # ⛔ Three answers, not two, and the two that are not "nobody" both refuse. An unreadable
        # open-file table is *unestablished*, never *idle* -- the arm's own rule, and here the
        # direction that matters, since reading it as idle removes the tree it could not clear.
        if occupants is None:
            raise ClaimError(
                f"refused: whether another session is working in `{doomed}` could not be read, "
                "and unreadable is not idle.\n"
                "The machine's open-file table was unavailable, so the reading that protects a "
                "sibling session could not be taken. Pass --force to remove the tree regardless."
            )
        if occupants:
            who = ", ".join(f"{command} ({pid})" for pid, command in occupants)
            raise ClaimError(
                f"refused: another session is working at or below `{doomed}`, which this release "
                f"would remove: {who}.\n"
                "§ 10 keeps a tree another session occupies. Wait for that session to finish, or "
                "pass --force — which here destroys whatever the tree holds that git does not "
                "track, not only a ref."
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
        if keep_ref:
            done.append("ref kept")
        else:
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
    # Plant: **the bound removed**, which leaves the word mapping alone -- the rule the start
    # role's "the item's title, slugged" amounted to. ⛔ The first form of this plant asserted
    # that two hardcoded names differ, which reads only `MEASURED` and never the derivation: it
    # stayed green with `slug_for` replaced by a function returning a constant, so it was not a
    # plant at all. Found reviewing the branch that wrote it.
    #
    # ⚠️ The plant is read on **length** and no longer on a name a sibling published, because
    # the derivation now drops a title's function words and so answers neither of the two
    # spellings the divergence was measured in. What the pair of published names is still
    # evidence for is the thing they had in common: every one of them is longer than the bound,
    # in both of each item's two spellings, so a rule with no bound admits all six and the
    # bound admits none -- and the assertion below is reached rather than vacuous because the
    # unbounded form of each title overruns it.
    unbounded = {item: slug_for(title, limit=None) for item, title, _ in MEASURED}
    published = [
        name.split("/", 1)[1][len(str(item)) + 1 :] for item, _, names in MEASURED for name in names
    ]
    suite.ok(
        "every slug two sessions actually published is longer than the bound, so a rule with no "
        "bound is what admitted them",
        all(len(slug) > SLUG_MAX for slug in published),
        ", ".join(f"{len(s)}:{s}" for s in published),
    )
    suite.ok(
        "and with the bound removed this derivation overruns it too (so the bound is what holds "
        "the length rather than the title being short)",
        all(len(slug) > SLUG_MAX for slug in unbounded.values()),
        ", ".join(f"{len(s)}:{s}" for s in unbounded.values()),
    )
    suite.ok(
        "while the derivation's own answer is within it, for every measured title",
        all(len(slug_for(title)) <= SLUG_MAX for _, title, _ in MEASURED),
        ", ".join(slug_for(title) for _, title, _ in MEASURED),
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
    suite.ok("the unbounded form would not have been", len(full) > SLUG_MAX, full)
    suite.ok("and leaves no trailing separator", not long_slug.endswith("-"), long_slug)
    suite.ok("a word that will not fit ends the slug, and the bound can be reached exactly",
             slug_for("one two three", limit=7) == "one-two",
             slug_for("one two three", limit=7))

    # The word rule, which is what the bound is spent on. ⚠️ `minor=frozenset()` reads a title's
    # own vocabulary out of the derivation itself, so these are assertions about the title rather
    # than about a word list written out a second time here.
    vocabulary = {
        item: slug_for(title, limit=None, minor=frozenset()).split("-")
        for item, title, _ in MEASURED
    }
    # Plant: **a character cut at the same bound** -- the rule before words were selected, and
    # what every reading of "the title, slugged" licenses. ⚠️ Asserted over the three titles
    # rather than one, because a cut lands mid-word only where the bound does not happen to fall
    # on a separator, and for two of these three it does.
    halved = [
        item
        for item, title, _ in MEASURED
        if slug_for(title, limit=None)[:SLUG_MAX].rsplit("-", 1)[-1] not in vocabulary[item]
    ]
    suite.ok(
        "a character cut at the same bound ends on half a word (so selecting whole words is "
        "what holds it)",
        bool(halved),
        ", ".join(slug_for(t, limit=None)[:SLUG_MAX] for i, t, _ in MEASURED if i in halved),
    )
    suite.ok(
        "while every segment the derivation answers is a whole word of its title",
        all(
            segment in vocabulary[item]
            for item, title, _ in MEASURED
            for segment in slug_for(title).split("-")
        ),
        ", ".join(slug_for(title) for _, title, _ in MEASURED),
    )
    suite.ok(
        "and a single word longer than the bound stands whole rather than halved",
        slug_for("Incomprehensibility") == "incomprehensibility",
        slug_for("Incomprehensibility"),
    )

    # Plant: **the function words kept**, which is the same bound spent on a title's articles and
    # prepositions instead of its nouns and verbs.
    unselected = [slug_for(title, minor=frozenset()) for _, title, _ in MEASURED]
    suite.ok(
        "with the function words kept, the bound is spent on them (so dropping them is what "
        "fits the title's own words in)",
        any(set(slug.split("-")) & MINOR_WORDS for slug in unselected),
        ", ".join(unselected),
    )
    suite.ok(
        "while the derivation's answer carries none of them",
        not any(set(slug_for(title).split("-")) & MINOR_WORDS for _, title, _ in MEASURED),
        ", ".join(slug_for(title) for _, title, _ in MEASURED),
    )

    for label, title, limit, expected in (
        ("punctuation collapses to one separator",
         "Two:  sessions -- share!!  backlog", None, "two-sessions-share-backlog"),
        ("case is dropped", "TwO SeSSiOnS", SLUG_MAX, "two-sessions"),
        ("digits survive, and the function word between them does not",
         "§ 10 and #70", SLUG_MAX, "10-70"),
        ("a word the title repeats is not carried twice",
         "A run, and a run cancelled", None, "run-cancelled"),
        ("a title whose every candidate is one character keeps the words it has",
         "A: b -- c!!  d", SLUG_MAX, "a-b-c-d"),
        ("and so does a title that is all function words", "Of the and", SLUG_MAX, "of-the-and"),
        ("a second script carries no function word this list knows, so the bound alone applies",
         "Две сессии делят один бэклог", SLUG_MAX, "две-сессии-делят"),
        ("a script of its own survives rather than becoming hyphens",
         "Две сессии", SLUG_MAX, "две-сессии"),
        ("a decomposed title slugs as its composed form does",
         unicodedata.normalize("NFD", "resum\u00e9"), SLUG_MAX,
         unicodedata.normalize("NFC", "resum\u00e9")),
    ):
        answered = slug_for(title, limit=limit)
        suite.ok(f"the derivation: {label}", answered == expected, answered)

    suite.ok(
        "a title that slugs to nothing leaves the number alone, not a trailing hyphen",
        branch_for("feature", 70, "!!! ---") == "feature/70",
        branch_for("feature", 70, "!!! ---"),
    )
    suite.ok(
        "an empty prefix is refused rather than producing `/70-x`",
        _raises(lambda: branch_for("", 70, "x")),
    )

    print("\nthe tree's leaf, derived rather than composed:")

    # The leaf is `<item>-<slug>`. What the earlier rule -- a leaf of the identifier alone --
    # protected is that the *directory* keeps answering "is this item being worked" across a
    # reworded title, so these are the properties: the identifier leads, the leaf is the branch's
    # own tail rather than a second slug rule, and the shipped candidate test answers for both of
    # two leaves one item could be started under.
    TREES = "../p-trees"
    # ⚠️ A reword of the title's **opening**, because the bound is spent on a title's first few
    # words: a reword that leaves those alone -- a subtitle added, a tail rewritten -- now answers
    # one leaf rather than two, which is the direction that helps the directory keep answering
    # whose it is and is why the question is asked on the prefix either way.
    REWORDED = ("Two sessions share one backlog", "One backlog, shared by two sessions")
    leaves = [tree_for(TREES, 70, title).name for title in REWORDED]

    # Plant: the two halves composed the other way round, `<slug>-<item>` -- the form that reads
    # better in an `ls`, which is why the ordering is asserted rather than assumed. Built from the
    # same `slug_for` and handed to the same shipped test, so what reddens is the ordering.
    suite.ok(
        "with the slug leading, no shipped test can tell whose directory it is (so the ordering "
        "is what holds it)",
        not any(ref_is_for_item(f"{slug_for(title)}-70", "70") for title in REWORDED),
        ", ".join(f"{slug_for(title)}-70" for title in REWORDED),
    )
    suite.ok(
        "a reword gives two leaves, which is why the question is asked on the prefix",
        leaves[0] != leaves[1],
        ", ".join(leaves),
    )
    suite.ok(
        "and `ref_is_for_item` answers for both of them, as it does for the ref names",
        all(ref_is_for_item(leaf, "70") for leaf in leaves),
        ", ".join(leaves),
    )
    suite.ok(
        "the leaf is the branch's own tail -- one derivation and not two",
        all(
            tree_for(TREES, item, title).name == branch_for("feature", item, title).rsplit("/", 1)[-1]
            for item, title, _ in MEASURED
        ),
        ", ".join(tree_for(TREES, i, t).name for i, t, _ in MEASURED),
    )
    suite.ok(
        "the configured directory is joined and never slugged into the leaf",
        tree_for("../p-trees", 70, "A title") == Path("../p-trees/70-title"),
        str(tree_for("../p-trees", 70, "A title")),
    )
    suite.ok(
        "a title that slugs to nothing leaves the identifier alone, not `70-`",
        tree_for(TREES, 70, "!!! ---").name == "70",
        tree_for(TREES, 70, "!!! ---").name,
    )
    suite.ok(
        "no item is refused, rather than collecting every such branch in one directory",
        _raises(lambda: tree_for(TREES, "", "A title")),
    )
    suite.ok(
        "and an empty `tree_dir` is refused rather than defaulted to somewhere",
        _raises(lambda: tree_for("", 70, "A title")),
    )

    print("\n`take` cuts the tree at the derived path:")

    with tempfile.TemporaryDirectory() as tmp:
        stack = tempfile.TemporaryDirectory(dir=tmp)
        _, one, _ = _bare_world(stack)
        trees, title = Path(tmp) / "trees", "Two sessions share one backlog"
        said = take(
            one, None, None, item="70", prefix="feature", title=title, tree_dir=str(trees)
        )
        # ⚠️ The derivation rather than a frozen string: what this arm holds is that `take` cut
        # the tree where `tree_for` says, and the spelling itself is held by the assertions above.
        cut = tree_for(trees, "70", title)
        suite.ok("the tree is cut where the derivation says", cut.is_dir(), said)
        suite.ok("and the report names that path, which is the path to enter", str(cut) in said, said)
        suite.ok(
            "end to end, the leaf and the branch's tail are the one string",
            cut.name == branch_for("feature", "70", title).rsplit("/", 1)[-1],
            cut.name,
        )
        both = _message(
            lambda: take(
                one, None, str(trees / "stated"), item="71", prefix="feature", title=title,
                tree_dir=str(trees),
            )
        )
        suite.ok(
            "stating the directory and the path together is refused",
            both is not None and "state one" in both,
            both or "it was accepted",
        )
        neither = _message(
            lambda: take(one, None, None, item="71", prefix="feature", title=title)
        )
        suite.ok(
            "stating neither is refused, and the refusal names both forms",
            neither is not None and "--tree-dir" in neither and "--tree" in neither,
            neither or "it was accepted",
        )
        no_item = _message(lambda: take(one, "feature/a-branch-with-no-item", tree_dir=str(trees)))
        suite.ok(
            "a branch carrying no item derives no leaf, and is told to state the path",
            no_item is not None and "--tree" in no_item,
            no_item or "it was accepted",
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
            # ⛔ On the message, not on the fact of a refusal. The caller is also a live process
            # at or below the tree, so the sibling guard below would refuse here too -- and with
            # `standing_in` dead these three assertions passed on *its* refusal, proving nothing
            # about the arm they are named for. Measured while adding that guard.
            suite.ok("a release from inside the tree is refused, as the caller and not a sibling",
                     "standing in" in (_message(
                         lambda: release(one, "feature/e", tree)) or ""))
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

    print("\na tree a sibling session is working in:")

    # ⛔ A real second process, not a stubbed reading: the defect was that `release` consulted the
    # caller's cwd and nothing else, and only another live process proves the second reading is
    # wired. Both sides again -- occupied refuses, unoccupied proceeds.
    with tempfile.TemporaryDirectory() as tmp:
        stack = tempfile.TemporaryDirectory(dir=tmp)
        _, one, _two = _bare_world(stack)
        tree = str(Path(tmp) / "sibling")
        take(one, "feature/sib", tree)
        # ⛔ `start_new_session` is the whole point: without it the child shares this process's
        # session and is this run's own helper, which is the case below. A sibling is a separate
        # session, and only setsid makes the fixture one.
        held = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(30)"],
            cwd=tree,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        try:
            seen = foreign_occupants(tree)
            seen = None if seen is None else (len(seen) > 0)
            if seen is None:
                # ⚠️ No open-file table here. That is the third answer, and it must refuse too --
                # which is the arm this branch asserts instead.
                suite.ok("unreadable is not idle: the release refuses rather than removing",
                         _raises(lambda: release(one, "feature/sib", tree)))
                suite.ok("and --force removes it regardless",
                         "ref deleted" in release(one, "feature/sib", tree, "origin", force=True))
            else:
                suite.ok("a sibling process in the tree is seen", seen is True)
                suite.ok("a release over a tree a sibling occupies is refused",
                         _raises(lambda: release(one, "feature/sib", tree)))
                suite.ok("and the refusal leaves the tree and the ref alone",
                         Path(tree).exists()
                         and remote_ref_sha(one, "origin", "feature/sib") is not None)
                suite.ok("⛔ the refusal says what forcing would cost, not just that it is refused",
                         "git does not track" in (_message(
                             lambda: release(one, "feature/sib", tree)) or ""))
                # ⛔ And *who*. The measured incident cost an `lsof` by hand to find out that the
                # occupant was a keep-awake helper and not a session; a refusal that cannot name
                # the occupant hands that cost to every reader.
                suite.ok("and names the occupant, so the reader need not run lsof themselves",
                         str(held.pid) in (_message(
                             lambda: release(one, "feature/sib", tree)) or ""))
                suite.ok("--force does cover a sibling, unlike the caller's own tree",
                         "ref deleted" in release(one, "feature/sib", tree, "origin", force=True))
        finally:
            held.kill()
            held.wait()

    print("\nthis run's own helper holding the tree's directory:")

    # ⛔ The measured incident, planted: a `caffeinate` the harness started while the session was
    # in its tree still held that directory after the session left, and the release of a tree
    # nobody was in was refused. The fixture is the same shape -- a child of this process, with
    # NO `start_new_session`, so it shares this session exactly as that helper did.
    with tempfile.TemporaryDirectory() as tmp:
        stack = tempfile.TemporaryDirectory(dir=tmp)
        _, one, _two = _bare_world(stack)
        tree = str(Path(tmp) / "helper")
        take(one, "feature/helper", tree)
        helper = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(30)"],
            cwd=tree,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            suite.ok("the open-file table does see it, which is why cwd alone was not enough",
                     process_in(tree) is not False)
            mine = foreign_occupants(tree)
            if mine is None:
                suite.ok("no open-file table here, so the distinction cannot be made either way",
                         True, "lsof absent")
            else:
                suite.ok("⛔ but a helper sharing this session is not another session",
                         mine == [], str(mine))
                # ⚠️ Through `_message` rather than called directly: with the session test
                # planted out this refuses, and an uncaught refusal kills the suite before the
                # sections below it run -- a plant has to redden its own check, not the file.
                refused = _message(lambda: release(one, "feature/helper", tree))
                suite.ok("so the release proceeds with no force, which is the bug this fixes",
                         refused is None and not Path(tree).exists(), refused or "")
        finally:
            helper.kill()
            helper.wait()

    print("\nthe real topology: the caller in its own session, the helper in the run's:")

    # ⛔ The fixture above is a child of this process and shares its session, which is NOT the
    # shape the incident had -- and believing it was is how a fix shipped green and left the case
    # broken. Measured: the harness gives each command a session of its own, so the *caller* is
    # the odd one out and the helper sits with the harness that spawned it.
    #
    # So the roles are inverted into a child here. This process plays the harness; a helper is
    # started in this session with the tree as its directory; and the reading is taken from a
    # grandchild in a session of its own, which is what a command run by the harness is. The
    # helper is then in an *ancestor's* session from the reader's point of view, exactly as the
    # keep-awake process was.
    with tempfile.TemporaryDirectory() as tmp:
        tree = Path(tmp) / "run"
        tree.mkdir()
        helper = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(30)"],
            cwd=str(tree),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            probe = (
                "import sys; sys.path.insert(0, %r); import claim, os; "
                "print(os.getsid(0)); print(claim.foreign_occupants(%r))"
                % (str(Path(__file__).resolve().parent), str(tree))
            )
            seen = subprocess.run(
                [sys.executable, "-c", probe],
                capture_output=True, text=True, start_new_session=True,
            )
            lines = seen.stdout.splitlines()
            if len(lines) != 2:
                suite.ok("the probe in its own session could not be run, and says so",
                         False, seen.stderr.strip() or seen.stdout.strip())
            else:
                suite.ok("the reader really is in a session of its own, as a harness's call is",
                         lines[0].strip() != str(os.getsid(0)), f"{lines[0]} vs {os.getsid(0)}")
                suite.ok("⛔ and a helper in an ancestor's session is not another session",
                         lines[1].strip() in ("[]", "None"), lines[1])
        finally:
            helper.kill()
            helper.wait()

    # The green side: the same release, same arguments, with nobody in the tree.
    with tempfile.TemporaryDirectory() as tmp:
        stack = tempfile.TemporaryDirectory(dir=tmp)
        _, one, _two = _bare_world(stack)
        tree = str(Path(tmp) / "empty")
        take(one, "feature/nosib", tree)
        suite.ok("nobody in the tree reads as unoccupied", process_in(tree) is not True)
        quiet = release(one, "feature/nosib", tree)
        suite.ok("and an unoccupied tree is released with no force",
                 not Path(tree).exists(), quiet)

    print("\na helper's tree is not a work tree:")

    # ⛔ Both sides, and the red one with a real nested worktree rather than a stubbed scan:
    # `git worktree list` is what reported the helper's tree as the item's, so a fixture that
    # did not register one would be asserting against this file's own idea of the output.
    with tempfile.TemporaryDirectory() as tmp:
        stack = tempfile.TemporaryDirectory(dir=tmp)
        _, one, _two = _bare_world(stack)

        here = git(one, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
        suite.ok("the main checkout is a work tree, which is the `in_place` reading",
                 tree_for_branch(one, here) is not None, here)

        outside = str(Path(tmp) / "wt" / "7")
        take(one, "feature/item-7", outside)
        # ⚠️ Compared as real paths: the temporary directory is reached through a symlink on one
        # of the two platforms this runs on, and git reports the resolved path either way.
        found = tree_for_branch(one, "feature/item-7")
        suite.ok("a tree cut outside the checkout, where `tree_dir` points, resolves",
                 found is not None and os.path.realpath(found) == os.path.realpath(outside),
                 str(found))
        release(one, "feature/item-7", outside)

        # The measured shape: a harness cuts a tree per helper inside the checkout, and the
        # helper checks out the branch it was sent to read. ⛔ The directory is named nothing in
        # particular on purpose -- the reading is about nesting, and a fixture spelling out one
        # harness's path would put that harness's value in this file, which is what § 10 refuses
        # for the process case and the same value under a different spelling.
        nested = Path(one) / "helpers" / "one"
        nested.parent.mkdir(parents=True, exist_ok=True)
        git(one, "worktree", "add", str(nested), "-b", "feature/item-7", "HEAD")
        suite.ok("⛔ and a tree nested below the checkout does not, whoever cut it",
                 tree_for_branch(one, "feature/item-7") is None,
                 str(tree_for_branch(one, "feature/item-7")))
        # ⛔ The answer above has to come from the reading rather than from the tree being
        # invisible: a fixture whose worktree never registered would assert the same thing for
        # the wrong reason, and pass with the reading deleted. So the scan is read directly.
        listed = git(one, "worktree", "list", "--porcelain").stdout
        suite.ok("and the scan did carry it, so the reading is what withheld it",
                 os.path.realpath(str(nested)) in listed
                 and f"branch {REFS_PREFIX}feature/item-7" in listed, listed)
        # ⚠️ Through `_message` so a refusal reddens this check rather than killing the suite.
        said = _message(lambda: release(one, "feature/item-7"))
        suite.ok("so the release that removed it as the item's tree removes nothing",
                 nested.exists(), said or "")

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
        take(one, "feature/91-merged", str(t1))
        for key, value in (("user.email", "one"), ("user.name", "One")):
            git(t1, "config", key, value)
        (t1 / "work.txt").write_text("work\n")
        git(t1, "add", "work.txt")
        git(t1, "commit", "--quiet", "-m", "work")
        git(t1, "push", "--quiet", "origin", "feature/91-merged")

        before = status(two, "feature/91-merged")
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
        git(two, "fetch", "--quiet", "origin", "feature/91-merged")
        git(two, "checkout", "--quiet", "main")
        git(two, "merge", "--squash", "FETCH_HEAD", check=False)
        for key, value in (("user.email", "two"), ("user.name", "Two")):
            git(two, "config", key, value)
        git(two, "commit", "--quiet", "-m", "squashed")
        git(two, "push", "--quiet", "origin", "main")

        after = status(two, "feature/91-merged")
        suite.ok(
            "after a squash merge it reads landed, not live",
            after.liveness is not None and after.liveness.landed,
            after.report(),
        )
        suite.ok(
            "and it is not an ancestor of the integration branch, which is why the hash test alone was wrong",
            git(two, "merge-base", "--is-ancestor",
                remote_ref_sha(two, "origin", "feature/91-merged"), "main", check=False).returncode == 1,
        )
        suite.ok("the report says the claim is spent", "landed:" in after.report(), after.report())

        # ⛔ What makes `--keep-ref` affordable, asserted rather than argued. Under § 2's
        # `delete_branch: never` the branch stays on the host, so this is the state the option
        # leaves behind: a ref standing on an item the loop still has to be able to claim again.
        # ⛔ A landed claim is the only state this is testable in, which is why the arms are here
        # and not beside the other release arms.
        kept = release(two, "feature/91-merged", None, "origin", keep_ref=True)
        suite.ok("--keep-ref reports the ref kept rather than deleted", "ref kept" in kept, kept)
        suite.ok(
            "and the ref really is still standing, so the arm is not reading its own report",
            remote_ref_sha(two, "origin", "feature/91-merged") is not None,
        )
        # ⛔ The item question and not the name question, and the difference is the whole of what
        # this option costs. `status_for_item` reads a landed ref as claiming nothing, so the work
        # item is takeable again with the ref still standing. ⚠️ `claim_free` is keyed on one
        # *name* and answers *taken* for as long as a ref of that name exists — which is the true
        # answer to the question it was asked, and the arm below holds it rather than hiding it.
        kept_item = status_for_item(two, "91")
        suite.ok(
            "⛔ and the work item is free regardless, the landed ref claiming nothing",
            not kept_item.contending(),
            kept_item.report(),
        )
        suite.ok(
            "while the name question still answers taken, the ref being there",
            not claim_free(two, "feature/91-merged")[0],
            claim_free(two, "feature/91-merged")[1],
        )
        # ⛔ The control, without which the item arm above is consistent with `--keep-ref` freeing
        # an item by itself: a ref on a claim that has NOT landed still holds its item, so the
        # reading above belongs to the landing and not to this option.
        suite.ok(
            "while a ref on a claim that has not landed still holds its item",
            not claim_free(two, "feature/fresh")[0],
            claim_free(two, "feature/fresh")[1],
        )
        suite.ok(
            "and releasing it needs no override",
            "ref deleted" in release(two, "feature/91-merged", None, "origin"),
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


def _message(call) -> str | None:
    """The refusal's text, for an assertion about what a refusal *says* rather than that it fired.

    ⚠️ A guard that refuses without naming the cost is half a guard here: the sibling arm's whole
    remedy is a person deciding, and they cannot decide from the word "refused".
    """
    try:
        call()
    except ClaimError as exc:
        return str(exc)
    return None


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
            # ⛔ Not required for `take` any more, and the refusal moved into `take` itself rather
            # than being dropped: one of `--tree-dir` and `--tree` is needed, which argparse states
            # as neither-required and the carrier states as a refusal naming both forms.
            node.add_argument("--tree", required=False)
        if name == "take":
            node.add_argument(
                "--tree-dir",
                default=None,
                help="`branch_model.tree_dir` (§ 10); with --item and --title, derives --tree",
            )
        if name == "release":
            # ⛔ A person saying it, which is the only thing § 10 permits to break a live claim.
            node.add_argument(
                "--force",
                action="store_true",
                help="break a live claim held elsewhere; refused without it",
            )
            # ⛔ Not a second spelling of --force. This one costs the claim nothing: § 2's
            # `delete_branch` decides who deletes a branch on the host, and under `never`
            # nobody does.
            node.add_argument(
                "--keep-ref",
                action="store_true",
                help="give up the tree and the local branch, leaving the published ref standing",
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
                    tree_dir=args.tree_dir,
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
                    keep_ref=args.keep_ref,
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
