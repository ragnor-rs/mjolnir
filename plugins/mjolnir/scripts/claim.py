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
from dataclasses import dataclass, field
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


class ClaimError(RuntimeError):
    """A refusal, or a failure to read the store the claim lives in."""


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
    was unreachable."""

    live: bool
    reason: str
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


def read_liveness(
    root: str | Path, remote: str, branch: str, integration: str, ref_sha: str
) -> Liveness:
    unestablished: list[str] = []

    # Arm 1: the ref carries work of its own. Needs the ref's sha locally to compare, so it is
    # fetched into a detached name rather than onto any branch.
    git(root, "fetch", "--quiet", remote, f"{REFS_PREFIX}{branch}", check=False)
    integration_sha = git(root, "rev-parse", integration, check=False)
    if integration_sha.returncode == 0:
        ancestor = git(
            root,
            "merge-base",
            "--is-ancestor",
            ref_sha,
            integration_sha.stdout.strip(),
            check=False,
        )
        if ancestor.returncode == 1:
            return Liveness(True, "the ref carries commits beyond the integration branch")
        if ancestor.returncode not in (0, 1):
            unestablished.append("whether the ref carries its own commits")
    else:
        unestablished.append(f"the integration branch `{integration}` could not be resolved")

    # Arm 2: a tree on this machine, with someone in it.
    tree = tree_for_branch(root, branch)
    if tree:
        occupied = process_in(tree)
        if occupied:
            return Liveness(True, f"a live process is working at or below {tree}")
        if occupied is None:
            unestablished.append("whether a process occupies the tree holding this branch")

    # Arm 3: an open pull request. Needs the host, so its absence is named rather than assumed.
    url = remote_url(root, remote)
    slug = host_slug(url) if url else None
    if slug and shutil.which("gh"):
        proc = subprocess.run(
            ["gh", "pr", "list", "--repo", slug, "--head", branch, "--state", "open", "--json", "number"],
            capture_output=True,
            text=True,
        )
        if proc.returncode == 0:
            try:
                if json.loads(proc.stdout or "[]"):
                    return Liveness(True, "an open pull request references the ref")
            except json.JSONDecodeError:
                unestablished.append("whether an open pull request references the ref")
        else:
            unestablished.append("whether an open pull request references the ref")
    else:
        unestablished.append("whether an open pull request references the ref")

    return Liveness(False, "no arm of the liveness test answered yes", unestablished)


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
            if self.liveness.live:
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
    return Status(
        taken=True,
        ref_sha=sha,
        holder=host_record(root, remote, branch),
        liveness=read_liveness(root, remote, branch, integration, sha),
        local_only=False,
    )


def take(
    root: str | Path,
    branch: str,
    tree: str,
    remote: str = "origin",
    integration: str | None = None,
    *,
    _lease: bool = True,
    _require_created: bool = True,
    _release_on_tree_failure: bool = True,
) -> str:
    """Claim the item, then cut the tree. Raises `ClaimError` on a refusal.

    The three underscore arguments exist for `--self-test` and for nothing else: they are how the
    suite plants each arm away in turn, to show that the race is held by the arm it is attributed
    to and that the no-residue rule is held by the release rather than by luck.
    """
    integration = integration_branch(root, remote, integration)
    base = git(root, "rev-parse", integration).stdout.strip()
    url = remote_url(root, remote)
    published = False

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

    # The local half. Atomic too, but only against this machine -- which is why it is second.
    cut = git(root, "worktree", "add", str(tree), "-b", branch, base, check=False)
    if cut.returncode != 0:
        if published and _release_on_tree_failure:
            git(root, "push", remote, "--delete", branch, check=False)
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
    """
    if not force and remote_url(root, remote):
        held = status(root, branch, remote, integration)
        if held.taken and held.liveness and held.liveness.live and not tree_for_branch(root, branch):
            raise ClaimError(
                f"refused: the claim on `{branch}` is live and is not held in a tree here.\n"
                f"{held.report()}\n"
                "Breaking a live claim is a person's call: pass --force to say so."
            )

    done = []
    if remote_url(root, remote):
        proc = git(root, "push", remote, "--delete", branch, check=False)
        done.append("ref deleted" if proc.returncode == 0 else "ref was already gone")

    held = tree or tree_for_branch(root, branch)
    if held and Path(held).exists():
        git(root, "worktree", "remove", held, "--force", check=False)
        done.append(f"tree {held} removed")
    git(root, "worktree", "prune", check=False)

    if git(root, "rev-parse", "--verify", "--quiet", REFS_PREFIX + branch, check=False).returncode == 0:
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
    subprocess.run(["git", "clone", "--quiet", str(origin), str(seed)], check=True)
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

        # § 5's predicate, over the same store and no second one.
        free_before, _ = claim_free(two, "feature/x")
        free_other, _ = claim_free(two, "feature/never-taken")
        suite.ok("`claim_free` reads the taken ref as taken", not free_before)
        suite.ok("`claim_free` reads an unclaimed name as free", free_other)

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
        suite.ok("while the clone that holds the tree releases it with no force",
                 "ref deleted" in release(one, "feature/s2", str(Path(tmp) / "t3")))

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
        subprocess.run(["git", "clone", "--quiet", str(orphanage), str(blank)], check=True)
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


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--self-test", action="store_true", help="plant a violation per check, then hold the rule")
    sub = parser.add_subparsers(dest="command")

    for name, help_text in (
        ("take", "claim the item: publish the ref, then cut the tree"),
        ("release", "give the claim up: the ref, the tree, the local branch"),
        ("status", "who holds it, since when, and whether it is live"),
    ):
        node = sub.add_parser(name, help=help_text)
        node.add_argument("--repo-root", required=True, help="the code root, stated and never inherited")
        node.add_argument("--branch", required=True)
        node.add_argument("--remote", default="origin")
        node.add_argument(
            "--integration",
            default=None,
            help="override; derived from the remote's default branch when omitted",
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
        if args.command == "take":
            print(take(args.repo_root, args.branch, args.tree, args.remote, args.integration))
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
            print(status(args.repo_root, args.branch, args.remote, args.integration).report())
    except ClaimError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
