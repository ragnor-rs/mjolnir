#!/usr/bin/env python3
"""The sweep that removes a working tree whose branch has landed.

The rule is stated once, in `config/schema.md` § 10 -> *Pruning a tree whose branch has landed*,
and this module performs the second of the two carriers that section states: the one on the event
that opens a session, for every landing the pass that merged could not reach. ⛔ Nothing here
restates the rule, and ⛔ **nothing here is a second reading of *has this landed*** -- that reading
is the claim's, performed by `claim.py`, and this module imports it rather than asking git itself.
A second oracle for the same question is two answers allowed to disagree, and the disagreement
would be resolved by deleting a tree.

What this module is for is the part the claim's own carrier has no business holding: which trees a
sweep may look at, what makes a tree too precious to remove however clean it reads, and what a
bounded run owes a reader about the trees it never got to.

⛔ **The destructive half is what the suite is written against.** A sweep that removes nothing
passes every red-side check there is, so each arm below has a **must-remove** plant beside its
must-keep one, and the preciousness oracle's exemptions were each verified by disabling the
exemption and watching the plant redden.

⚠️ No network in the suite. The landed reading's content arm answers from two local repositories,
which is the whole of what a landed branch is from a sweep's point of view; what a bare repository
cannot supply is the host's record of a merged pull request, which is the arm § 10 already requires
be named as unestablished rather than guessed.

Usage:
    prune.py hook                      answer a SessionStart payload on stdin
    prune.py sweep --skills-root .     sweep this project's trees and report
    prune.py --self-test               plant a violation per rule, then hold the rule
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import shutil
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import claim  # noqa: E402

SURFACE = Path(__file__).resolve().parent.parent / "config" / "schema.md"
CARRIER = Path(__file__).resolve().parent.parent / "hooks" / "hooks.json"
CARRIER_EVENT = "SessionStart"

# The subsection this script is the carrier for, by the anchor the code host would give its
# heading -- the same bargain every citation of the surface makes: a reword that keeps the anchor
# costs this file nothing, and one that does not reddens here.
ANCHOR = "pruning-a-tree-whose-branch-has-landed"

# ⛔ The wall-clock bound, and it is **procedure rather than configuration**: what it exists to
# stay inside is the timeout on the hook entry in `hooks.json`, which is this plugin's value and
# not a project's. A per-tree cost is one host lookup, so a machine carrying nine trees outruns
# anything a project would have picked anyway.
#
# ⚠️ **The hazard it covers is not slowness.** A carrier killed on the harness's timeout emits
# nothing at all, so a half-finished sweep reads as a finished one -- which is the shape § 7 names
# as irreducible from inside a guard. Stopping early and *saying* so is the only form of that a
# carrier can hold, and the suite asserts this value is under the timeout the carrier registers.
BUDGET_SECONDS = 40

# ⛔ What one tree is allowed to cost, held back from the budget so the bound is real rather than
# checked between trees alone. A tree's own work is two host lookups, a fetch, a read of the
# machine's open-file table and then the release, which repeats the reading — so this is the
# measured worst case rounded up, not a guess at a typical one.
#
# ⚠️ **What it does not close is stated with it**: none of those calls carries a timeout of its
# own, so a tree whose lookups hang still outruns the event's limit. The reserve makes that the
# rare case instead of the ordinary one, and nothing outside those calls can close it.
RESERVE_SECONDS = 15

# Where `delete_branch` puts the published ref's deletion. ⛔ Read from § 2 and never defaulted:
# the other two values are a project saying the ref is somebody else's, and asking for a deletion
# under either is the refused second deletion § 2 measured.
PROCEDURE_DELETES = "procedure"


@dataclass
class Registered:
    """One entry of `git worktree list`, as the sweep has to tell them apart."""

    path: str
    branch: str | None
    main: bool = False
    outside: bool = False
    prunable: bool = False
    locked: bool = False


@dataclass
class Verdict:
    """What the sweep decided about one tree, and why.

    ⛔ **`reason` is not optional and has no default.** § 10 requires a kept tree to be named with
    what kept it: a reader cannot rescue a file the report does not mention, and a sweep that keeps
    trees for reasons it does not state is indistinguishable from one that has stopped working.
    """

    path: str
    branch: str | None
    removed: bool
    reason: str
    paths: list[str] = field(default_factory=list)
    unestablished: list[str] = field(default_factory=list)
    # ⛔ Whether a person has something to do about this tree, and a field rather than a reading
    # of `reason`: the arms worth waking somebody for are a path they may want to rescue, a
    # question nothing could answer, and a removal that was refused -- and a carrier that found
    # those by matching its own prose would stop finding one the first time it was reworded.
    attention: bool = False


@dataclass
class Report:
    """What one sweep did, including what it did not reach.

    ⛔ **`unreached` is part of the answer rather than a diagnostic** (§ 11): a sweep that looked at
    two of nine trees and said nothing has reported that nine trees are in order.
    """

    verdicts: list[Verdict] = field(default_factory=list)
    unreached: list[str] = field(default_factory=list)
    unestablished: list[str] = field(default_factory=list)

    @property
    def removed(self) -> list[Verdict]:
        return [v for v in self.verdicts if v.removed]

    @property
    def kept(self) -> list[Verdict]:
        return [v for v in self.verdicts if not v.removed]

    def lines(self) -> list[str]:
        out = []
        for verdict in self.removed:
            out.append(f"removed {verdict.path} — {verdict.reason}")
        for verdict in self.kept:
            named = f" ({', '.join(verdict.paths)})" if verdict.paths else ""
            out.append(f"kept {verdict.path} — {verdict.reason}{named}")
        for verdict in self.verdicts:
            for item in verdict.unestablished:
                out.append(f"  unestablished: {item}")
        if self.unreached:
            # ⛔ The paths and not only the count. A count says a sweep stopped; the paths say
            # which trees a reader is still owed an answer about, and the next sweep is the only
            # thing that will give it.
            out.append(
                f"not looked at ({len(self.unreached)}, the budget of {BUDGET_SECONDS}s "
                f"ran out): {', '.join(self.unreached)}"
            )
        for item in self.unestablished:
            out.append(f"unestablished: {item}")
        return out

    def report(self) -> str:
        if not self.lines():
            return "no tree of this project has a landed branch to remove."
        return "\n".join(self.lines())

    def message(self) -> str:
        """The one-paragraph form a session's opening event carries, or empty for nothing to say.

        ⚠️ Empty where the sweep removed nothing and had nothing it could not establish: an event
        that fires on every session open may not narrate a no-op, and a tree kept because its
        branch has not landed is the ordinary state of a tree being worked in.
        """
        said = [f"removed {v.path} ({v.reason})" for v in self.removed]
        # ⛔ The paths **and** what could not be established, because § 11's rule has no quiet
        # form: an unestablished half that reached only the full report is one a person never saw,
        # and the full report is reachable from the person-run arm alone.
        said += [
            f"kept {v.path} — {v.reason}"
            + (f" ({', '.join(v.paths)})" if v.paths else "")
            + (f" [not established: {'; '.join(v.unestablished)}]" if v.unestablished else "")
            for v in self.kept
            if v.attention
        ]
        said += [f"not looked at: {', '.join(self.unreached)}"] if self.unreached else []
        said += [f"not established: {i}" for i in self.unestablished]
        if not said:
            return ""
        return "Landed trees: " + "; ".join(said) + f". ({ANCHOR})"


# --------------------------------------------------------------------------------------------
# Which trees there are
# --------------------------------------------------------------------------------------------


def registered(root: str | Path, tree_dir: str | Path | None = None) -> list[Registered]:
    """Every worktree this repository has, each marked with what the sweep needs to tell it apart.

    ⛔ **Nothing is filtered out here.** A tree the sweep may not touch is still a tree the report
    names, by § 10's rule that a kept tree is named with what kept it -- and a tree dropped at this
    layer is a tree nothing ever mentions, which is how three helper trees outlived a merge on this
    repository with nothing reaping them.

    ⛔ **`outside` is read against the project's own `tree_dir` and not against the checkout.**
    Measured from both directions in one review: `claim.a_work_tree` answers *nesting below the
    main checkout*, which is the right question for a release pointed at one tree and the wrong one
    for a sweep that enumerates. Against it, a project whose `tree_dir` is **inside** its checkout
    -- which § 10 names as a measured placement -- has every one of its work trees read as a
    helper's and prunes nothing, while a worktree somebody cut by hand outside every tree directory
    is read as a candidate and has its branch and published ref deleted on a landed verdict.
    ⚠️ **The configured directory answers both**: a tree under it is this project's, whether or not
    that directory is inside the checkout, and a tree outside it is nobody's business here.

    ⛔ **`-z`, because a newline in a path is otherwise a record boundary.** Git's own
    documentation recommends it for exactly that, and the consequence was not cosmetic: a truncated
    path reaches the release as the tree to remove, where the ref deletion happens regardless and
    the removal silently fails.

    `prunable` and `locked` are read rather than ignored: the first is a registration whose
    directory is already gone, and the second is a tree git refuses to remove with one `--force`.
    """
    proc = claim.git(root, "worktree", "list", "--porcelain", "-z")
    found: list[Registered] = []
    main_tree: str | None = None
    path: str | None = None
    branch: str | None = None
    prunable = locked = False

    def flush() -> None:
        nonlocal path, branch, prunable, locked
        if path is not None:
            found.append(_entry(path, branch, main_tree, tree_dir, prunable, locked))
        path, branch, prunable, locked = None, None, False, False

    for field in proc.stdout.split("\0"):
        if field.startswith("worktree "):
            flush()
            path = field[len("worktree ") :]
            if main_tree is None:
                main_tree = path
        elif field.startswith("branch "):
            ref = field[len("branch ") :]
            if ref.startswith(claim.REFS_PREFIX):
                branch = ref[len(claim.REFS_PREFIX) :]
        elif field == "prunable" or field.startswith("prunable "):
            prunable = True
        elif field == "locked" or field.startswith("locked "):
            locked = True
    flush()
    return found


def _entry(
    path: str,
    branch: str | None,
    main_tree: str | None,
    tree_dir: str | Path | None,
    prunable: bool,
    locked: bool,
) -> Registered:
    main = main_tree is not None and os.path.realpath(path) == os.path.realpath(main_tree)
    if main:
        outside = False
    elif tree_dir is not None:
        outside = not _under(_resolve(tree_dir, main_tree), path)
    else:
        # ⚠️ **The fallback, for a caller that states no directory**, which the hook and the
        # person-run arm never are: the helper-tree reading the claim already performs. Weaker
        # than the configured answer in both directions — it cannot see a project whose trees are
        # nested, and it admits a worktree somebody cut by hand — and it is the reading this
        # carrier had before `tree_dir` was passed in, kept so that a caller with no configuration
        # to hand gets the old answer rather than an empty sweep.
        outside = main_tree is not None and not claim.a_work_tree(path, main_tree)
    return Registered(
        path=path,
        branch=branch,
        main=main,
        outside=outside,
        prunable=prunable,
        locked=locked,
    )


def _resolve(tree_dir: str | Path | None, main_tree: str | None) -> str | None:
    """`tree_dir` as a place, anchored on the **main checkout** and not on the caller's tree.

    ⛔ **The anchor is the rule and getting it wrong is silent.** § 10's `tree_dir` is where trees
    are cut relative to the checkout — `../<project>-trees` on the two measured placements — and
    the role that cuts them runs in that checkout. This carrier does not: it runs on the event that
    opens a session, and that session is routinely standing *in* one of the trees, where the
    configuration resolves to the tree itself.
    ⚠️ **Measured by running the shipped sweep on this repository**: joined to the tree rather than
    to the checkout, `../mjolnir-wt` resolved to a directory one level too deep that does not
    exist, so every real tree read as *outside* and the sweep became the no-op it exists to end.
    """
    if tree_dir is None:
        return None
    stated = str(tree_dir)
    if os.path.isabs(stated) or main_tree is None:
        return stated
    return os.path.normpath(os.path.join(main_tree, stated))


def _under(directory: str | Path | None, path: str) -> bool:
    """Whether `path` is at or below `directory`, both resolved. False where there is no directory.

    ⚠️ Realpaths on both sides, which is the one thing this comparison cannot skip: a tree
    directory reached through a symlinked parent -- the ordinary shape of a temporary directory on
    one of the two platforms measured -- compares unequal as text and equal as a place.
    """
    if directory is None:
        return False
    try:
        here, root = os.path.realpath(path), os.path.realpath(str(directory))
    except OSError:
        return False
    return here == root or here.startswith(root + os.sep)


# --------------------------------------------------------------------------------------------
# Clean is not disposability
# --------------------------------------------------------------------------------------------


def covered(path: str, patterns: list[str]) -> str | None:
    """The `regenerable` entry that covers this ignored path, or None.

    § 10 states the matching: each entry is a path matched with the shell's own glob rules, from
    the right, against the ignored path **and against each directory above it** -- so a bare name
    matches wherever it appears and an entry naming a directory covers everything beneath it.

    ⛔ A pattern this language cannot compare declines rather than raising, and declining means
    *not covered*, which keeps the tree. The direction is the whole point: an entry that fails to
    match exempts nothing, and the tree it was written to protect survives.
    """
    here = PurePosixPath(path.strip("/"))
    candidates = [here, *here.parents]
    for pattern in patterns:
        # ⛔ **A leading separator anchors the entry at the tree's own root**, which is the one
        # shape a project writes from habit and the one a right-anchored match silently ignores:
        # every ignore file in the world spells a root-relative directory `/build`, and an entry
        # that matched nothing at all would leave a project's stated value inert with the tree
        # kept forever and no sentence saying why.
        anchored = pattern.startswith("/")
        wanted = pattern.lstrip("/") if anchored else pattern
        for candidate in candidates:
            if str(candidate) in ("", "."):
                continue
            try:
                if candidate.match(wanted) and not (anchored and str(candidate) != wanted):
                    return pattern
            except ValueError:
                continue
    return None


def only_links(where: Path) -> bool:
    """Whether everything at `where` is a symlink, however deep.

    ⛔ **A symlink is never precious, however it is ignored** (§ 10). A tree preparation step that
    plants ignored symlinks into every tree it prepares makes every correctly prepared tree
    permanently precious under a literal reading of the oracle, and then nothing is ever pruned --
    while removing the tree unlinks them and loses not a byte.

    ⚠️ **The symlink test comes before the directory test**, which is the ordering the rule needs: a
    symlink *to* a directory answers `is_dir()` and would otherwise be walked through into whatever
    it points at -- material outside the tree, which no removal of the tree would touch and which a
    walk would nonetheless read as a reason to keep it.
    """
    if where.is_symlink():
        return True
    if where.is_dir():
        try:
            return all(only_links(child) for child in where.iterdir())
        except OSError:
            # Unreadable is not empty: the caller reads False as *something is in there*, which
            # keeps the tree.
            return False
    return False


def precious(tree: str, regenerable: list[str]) -> tuple[list[str], list[str]]:
    """`(the paths that make this tree precious, what could not be established)`.

    ⛔ **A porcelain status is not the oracle.** It does not report ignored files and a removal
    deletes them anyway: measured in one project, where a tree holding a session credential for an
    external service and a pulled-back output directory reported clean and lost both, and the
    credential could only be re-minted by an interactive login. So the oracle is
    tracked-or-untracked changes **plus** any ignored path that `regenerable` does not cover.

    ⛔ **A reading that fails is a reason to keep the tree and is returned as one.** A status that
    could not be taken and a tree with nothing in it are the same answer otherwise, and the wrong
    one of the two deletes data.
    """
    # ⛔ **`--untracked-files=all` is the load-bearing flag and the measurement says so.** Without
    # it a directory whose whole content is ignored collapses into the *topmost* untracked
    # directory above it, so a tree holding `a/b/cache/` is reported as holding `a/` -- and then a
    # `regenerable` entry naming the cache matches nothing, the tree is kept forever, and the
    # project's own statement is silently inert. Measured here as a fixture that declared its cache
    # regenerable and was kept anyway. ⚠️ **`--ignored=matching` is the cheaper of two correct
    # choices rather than the fix**: with the flag above in place, `traditional` reports
    # `a/b/cache/object` and `matching` reports `a/b/cache/`, and the parents walk in `covered`
    # resolves both -- what `matching` buys is a report naming the directory rather than every file
    # under it. Re-measured on this change, the first wording of this comment having credited the
    # wrong flag.
    #
    # ⛔ **`-z`, which is the only way these paths arrive unmangled.** Without it git quotes any
    # path outside ASCII as octal escapes, so a `regenerable` entry naming such a directory never
    # matches its own paths; and a newline in a path is a record boundary. With `-z` every record
    # is NUL-terminated and nothing is quoted.
    proc = claim.git(
        tree,
        "status",
        "--porcelain",
        "--ignored=matching",
        "--untracked-files=all",
        "-z",
        check=False,
    )
    if proc.returncode != 0:
        return [], [f"what `{tree}` holds could not be read: {proc.stderr.strip()}"]
    keeping: list[str] = []
    # ⛔ A rename or a copy carries **two** NUL-terminated paths and every other code carries one,
    # so the second is consumed here rather than being read as a record of its own. ⚠️ And the
    # split on ` -> ` this replaces was applied to every line, including ignored ones: an ignored
    # path whose own name contained that sequence was tested under a name that was not its own, so
    # the file the oracle exists for was neither matched nor named.
    records = [field for field in proc.stdout.split("\0") if field]
    index = 0
    while index < len(records):
        record = records[index]
        index += 1
        if len(record) < 4:
            continue
        code, named = record[:2], record[3:]
        if code and code[0] in ("R", "C"):
            # The original path, which is not what is in the tree now.
            index += 1
        if code != "!!":
            # Tracked or untracked: git already knows the path and nothing else does. This is the
            # half a porcelain status does answer, and it is kept whole rather than judged.
            keeping.append(named)
            continue
        if covered(named, regenerable):
            continue
        if only_links(Path(tree) / named):
            continue
        keeping.append(named)
    return keeping, []


def unpushed(tree: str, ref_sha: str | None) -> tuple[list[str], list[str]]:
    """`(the tree's commits the landed reading never saw, what could not be established)`.

    ⛔ **The oracle above reads files and a commit is not a file, which is how the worst defect of
    this carrier's first draft got past it.** Measured: a branch pushed, squash-merged, and then
    committed to once more without pushing reads **landed** -- the landed test is taken against the
    *published* ref, which is diff-equal to the integration branch -- while `git status` is empty,
    because the work is committed. The tree was removed and the local branch force-deleted, so the
    follow-up fix survived only as a dangling object.

    ⚠️ **Divergence in either direction keeps the tree**, not only being ahead: a tree whose branch
    somebody else has advanced is a tree whose content this reading did not answer about.

    ⛔ **An unreadable comparison keeps it too**, which is the same direction every other arm of
    this oracle fails in.
    """
    if not ref_sha:
        return [], ["which commit the landed reading was taken on"]
    head = claim.git(tree, "rev-parse", "HEAD", check=False)
    if head.returncode != 0:
        return [], [f"what `{tree}` has committed could not be read: {head.stderr.strip()}"]
    if head.stdout.strip() == ref_sha:
        return [], []
    carried = claim.git(tree, "log", "--oneline", f"{ref_sha}..HEAD", check=False)
    if carried.returncode != 0:
        return [], [
            f"whether `{tree}` carries commits the landed reading did not see "
            f"({carried.stderr.strip()})"
        ]
    lines = [line for line in carried.stdout.splitlines() if line.strip()]
    if lines:
        return lines, []
    # The tree is behind rather than ahead: no commit of its own, and still not the state the
    # reading answered about.
    return [], [
        f"`{tree}` is not at the commit the landed reading was taken on, and carries no commit "
        "of its own"
    ]


# --------------------------------------------------------------------------------------------
# The sweep
# --------------------------------------------------------------------------------------------


def _landed(root: str | Path, remote: str):
    """The default reading: the claim's own, asked per branch."""

    def read(branch: str):
        return claim.status(root, branch, remote)

    return read


def sweep(
    root: str | Path,
    regenerable: list[str],
    delete_branch: str,
    *,
    tree_dir: str | Path | None = None,
    here: str | None = None,
    remote: str = "origin",
    budget: float = BUDGET_SECONDS,
    reserve: float = RESERVE_SECONDS,
    clock=time.monotonic,
    read=None,
    occupants=None,
    remove=None,
    standing=None,
) -> Report:
    """Remove every tree whose branch has landed, and report what was kept and why.

    The injected callables are how the suite plants an arm away and how it asserts the arms are
    reached in the order the rule states; each defaults to the thing it stands in for. ⛔ **`read`
    is `claim.status` and not a reimplementation of it**, which is the whole of this module's
    relationship to *has this landed*.
    """
    read = read if read is not None else _landed(root, remote)
    occupants = occupants if occupants is not None else claim.foreign_occupants
    standing = standing if standing is not None else (lambda path: claim.standing_in(path, here))
    remove = remove if remove is not None else _remover(root, remote, delete_branch)

    report = Report()
    started = clock()
    try:
        trees = registered(root, tree_dir)
    except claim.ClaimError as error:
        # ⛔ The one failure that is the whole sweep's: with no list of trees there is nothing to
        # report per tree, and saying so is the only honest answer.
        report.unestablished.append(
            f"which trees this repository has: {' '.join(str(error).split())}"
        )
        return report
    for index, tree in enumerate(trees):
        if tree.main:
            continue
        # ⛔ **The reserve and not the budget**, because a bound tested only on entry lets a tree
        # start with a second to spare and then spend two host lookups, a fetch and a read of the
        # machine — after which the harness kills the run and it emits nothing, which is the exact
        # outcome the bound exists to convert into a sentence.
        if clock() - started >= budget - reserve:
            # ⛔ Everything from here on is unreached rather than clean, and the remaining entries
            # are named rather than counted alone.
            report.unreached = [t.path for t in trees[index:] if not t.main]
            break
        try:
            report.verdicts.append(
                _decide(
                    tree,
                    regenerable=regenerable,
                    read=read,
                    occupants=occupants,
                    standing=standing,
                    remove=remove,
                )
            )
        except Exception as error:  # noqa: BLE001 -- one tree's failure is not the sweep's
            # ⛔ **Contained per tree, and the reason is the record rather than the robustness.**
            # Measured: one tree's reading raising — a remote that cannot be reached, which is the
            # ordinary state of this hook on a dead network — unwound past the report and
            # discarded every verdict already produced, **including removals that had already
            # happened**, after which the session was told that nothing was examined and nothing
            # removed. A destructive act whose record is destroyed with the exception is worse
            # than the exception.
            report.verdicts.append(
                Verdict(
                    tree.path,
                    tree.branch,
                    False,
                    f"nothing could be established about it ({type(error).__name__})",
                    unestablished=[" ".join(str(error).split())],
                    attention=True,
                )
            )
    # ⚠️ Registrations whose directories are gone are cleared here rather than reported forever.
    # Nothing is at stake in one — the tree it named does not exist — and a sweep that left them
    # standing would say the same sentence about the same absence at every session open.
    if any(tree.prunable for tree in trees):
        claim.git(root, "worktree", "prune", check=False)
    return report


def _decide(
    tree: Registered,
    *,
    regenerable: list[str],
    read,
    occupants,
    standing,
    remove,
) -> Verdict:
    """One tree, in the order § 10 states -- and the order is part of the rule.

    The cheap local readings come before the one that reaches a host, and the caller's own tree is
    answered before anything else is asked about it: a tree this process is standing in is a
    **stop** rather than a skip, and nothing a sweep could learn about it changes that.
    """
    def kept(reason: str, **rest) -> Verdict:
        return Verdict(tree.path, tree.branch, False, reason, **rest)

    if tree.outside:
        return kept(
            "it is not under this project's tree directory, so it is not a tree this procedure "
            "cut and not this sweep's to remove"
        )
    if tree.prunable:
        # ⚠️ A registration whose directory is already gone. Bookkeeping rather than data, and
        # saying so every session is how a channel stops being read — so it is reported once in
        # the full report and the sweep's own `git worktree prune` clears it.
        return kept("its directory is already gone; the registration is what is left of it")
    if standing(tree.path):
        # ⛔ Stated as the stop it is, with what clears it: leaving. ⚠️ And where no exit is
        # available -- a session pinned to its tree when it was launched -- the skip is correct and
        # the tree is a later sweep's, which is the one case the wording was always right about.
        return kept(
            "this session is standing in it; leaving is what clears that, and where no exit is "
            "available a later sweep removes it"
        )
    if tree.branch is None:
        return kept(
            "no branch is checked out in it, so whether its work landed cannot be read",
            unestablished=["which branch this tree holds"],
            attention=True,
        )

    held = read(tree.branch)
    if held is None:
        return kept(
            "the claim on its branch could not be read",
            unestablished=[f"whether `{tree.branch}` has landed"],
            attention=True,
        )
    spent = held.liveness is not None and held.liveness.landed
    if not spent:
        # ⛔ Not landed covers three different states and the report says which: live, an orphaned
        # candidate, and a reading that failed. ⚠️ None of the three is removable here and only one
        # of them is a problem -- an orphaned candidate is a person's call, per § 10.
        reason = (
            held.liveness.reason
            if held.liveness is not None
            else "nothing could be read about its claim"
        )
        missing = list(held.liveness.unestablished) if held.liveness else []
        # ⛔ **Live is the one reading that owes a person nothing, and the line is § 10's own.** A
        # branch somebody is working is the ordinary state of a tree and narrating it on every
        # session open is how a channel stops being read. An **orphaned candidate** is the other
        # half of the same table and is a person's call -- the section says the sweep that finds
        # one states both readings and *asks* -- so it is said, and so is a reading that failed.
        # ⚠️ Either way the full report names the unestablished half; what this decides is only
        # whether the event that opens a session says it unprompted.
        return kept(
            f"its branch `{tree.branch}` has not landed: {reason}",
            unestablished=missing,
            attention=held.liveness is None or not held.liveness.live,
        )

    carried, unread = unpushed(tree.path, held.ref_sha)
    if carried or unread:
        # ⛔ Before the file oracle and not after it: this is the arm that answers about work git
        # already has, which is the half a status cannot see at all.
        return kept(
            "its branch has landed and the tree carries commits the landed reading never saw",
            paths=carried,
            unestablished=unread,
            attention=True,
        )

    keeping, unknown = precious(tree.path, regenerable)
    if keeping or unknown:
        # ⛔ Every path, and no cap on how many are listed. A bound here would be a sweep naming
        # twenty files and silently dropping the twenty-first, which reads to a person as the whole
        # of what the tree holds -- and the one file they needed to rescue is as likely to be past
        # the cut as before it.
        return kept(
            "its branch has landed and it holds files no rebuild writes again",
            paths=sorted(keeping),
            unestablished=unknown,
            attention=True,
        )

    there = occupants(tree.path)
    if there is None:
        return kept(
            "whether another session is working in it could not be read, and unreadable is not "
            "idle",
            unestablished=[f"who is working in `{tree.path}`"],
            attention=True,
        )
    if there:
        who = ", ".join(f"{command} ({pid})" for pid, command in there)
        return kept(f"another session is working at or below it: {who}")

    done, failed = remove(tree.branch, tree.path)
    if failed:
        # ⛔ Said on the event that opens a session rather than only to a run nobody reads: a
        # landed tree the removal refused is the one kept state that is neither ordinary nor
        # self-clearing, and a sweep that swallowed it would keep refusing in silence every time.
        return kept(
            f"its branch has landed and the release was refused: {failed}", attention=True
        )
    # ⛔ **The removal is read back, never inferred from the absence of a refusal.** Measured in
    # the carrier this calls: a `worktree remove` that fails is not raised and its success
    # sentence is appended anyway, so a locked tree -- which git refuses unless `--force` is given
    # twice -- produced *removed* for a tree still on disk whose published ref had already gone.
    # ⚠️ A destructive act reported as done when it was not is worse than a refusal, because
    # nothing comes back to it.
    if Path(tree.path).exists():
        return kept(
            "its branch has landed and the removal reported success while the tree is still "
            f"there — {done}",
            unestablished=[f"why `{tree.path}` could not be removed"],
            attention=True,
        )
    return Verdict(tree.path, tree.branch, True, done)


def _remover(root: str | Path, remote: str, delete_branch: str):
    """The removal, with `delete_branch` deciding whether the published ref is reached.

    ⛔ **Under `host` and under `never` the ref is not this carrier's**, and the two differ in why
    rather than in what happens here: under `host` it is already gone, and asking again is the
    second deletion § 2 measured as `422` and as a landing that reads unfinished; under `never` the
    project has said nobody deletes it. ⚠️ **A kept ref costs the loop nothing** -- a landed claim
    claims no work item -- so the arm is affordable rather than merely permitted.

    ⛔ **Never forced.** Every refusal `claim.release` can raise here is a tree the sweep has
    already decided it may not remove, or a reading the sweep could not take; forcing past either
    is the automatic claim-breaking § 10 forbids, and there is nobody present to override it.
    """

    def run(branch: str, tree: str) -> tuple[str, str | None]:
        try:
            return (
                claim.release(
                    root,
                    branch,
                    tree,
                    remote,
                    keep_ref=delete_branch != PROCEDURE_DELETES,
                ),
                None,
            )
        except claim.ClaimError as error:
            return "", " ".join(str(error).split())

    return run


# --------------------------------------------------------------------------------------------
# The event that opens a session
# --------------------------------------------------------------------------------------------


def shared_reader():
    """The configuration reader beside this script, or None where it is gone.

    ⛔ Read through it and never parsed here: a second reader is a second set of defaults, and two
    sets drift apart with nothing noticing.
    """
    try:
        import config  # noqa: PLC0415 -- the path is set at import time above
        return config
    except Exception:  # noqa: BLE001 -- a session must not be interrupted by this
        return None


def answer(payload: dict, *, run=None) -> dict:
    """The `SessionStart` answer for one payload.

    ⛔ **Silence in a project that states no configuration**, per § 7: this hook is addressed by its
    event and reaches every project the person who installed it opens. The one message such a
    project gets is the invitation, which the sibling hook on this event owns -- a second message
    here would be that exception being broken rather than used.

    ⛔ **And silence under `in_place`**: a project that cuts no tree has none to prune, which is a
    stated configuration rather than a sweep with nothing to do.

    ⚠️ **`systemMessage` and never `additionalContext`.** What the sweep has to say is addressed to
    the person -- a tree removed, or a path they may want to rescue -- and the context channel would
    hand it to a session that cannot act on it and then carry it into every reply.
    """
    reader = shared_reader()
    if reader is None:
        return {}
    cwd = str(payload.get("cwd") or ".")
    try:
        if not reader.configured(cwd):
            return {}
    except Exception:  # noqa: BLE001 -- an unreachable reader says nothing, as above
        return {}
    try:
        loaded = reader.load(cwd, check_paths=False)
    except Exception as error:  # noqa: BLE001 -- a stated configuration that does not resolve
        # ⚠️ Absent and unreadable are different answers and only the first is silent (§ 7): a
        # project whose file has a typo in it would otherwise read as a project that wrote none.
        return {"systemMessage": (
            f"Landed trees: this project's configuration did not resolve ({type(error).__name__}), "
            "so no tree was examined."
        )}
    if loaded.get("branch_model.kind") != "worktree":
        return {}
    run = run if run is not None else sweep
    stated = loaded.get("branch_model.tree_dir")
    try:
        report = run(
            loaded.code_root,
            list(loaded.get("branch_model.regenerable") or []),
            str(loaded.get("host.landing.delete_branch") or ""),
            # ⛔ The configured value as stated, resolved against the **main checkout** inside
            # the sweep — never joined to the code root here, which is the tree this session
            # happens to be standing in.
            tree_dir=stated,
            # ⛔ **The session's directory and not this process's.** The one stop between a live
            # session and the removal of its own tree is *standing in it*, and a hook runs in a
            # process of its own; every other hook in this plugin reads the session's directory
            # from the payload, and reading `getcwd()` here made that stop depend on an unstated
            # guarantee about where hooks are run.
            here=cwd,
        )
    except Exception as error:  # noqa: BLE001 -- nothing here may interrupt a session
        return {"systemMessage": (
            f"Landed trees: the sweep did not run ({type(error).__name__}), so no tree was "
            "examined and none was removed."
        )}
    said = report.message()
    return {"systemMessage": said} if said else {}


def hook(stream, out=None) -> int:
    """Answer one payload. ⛔ Interrupts nothing, whatever happens here."""
    out = out if out is not None else sys.stdout
    try:
        payload = json.load(stream)
        answered = answer(payload if isinstance(payload, dict) else {})
    except Exception:  # noqa: BLE001 -- a session must not be interrupted by this
        return 0
    if answered:
        print(json.dumps(answered), file=out)
    return 0


# --------------------------------------------------------------------------------------------
# The two checks that keep this carrier connected
# --------------------------------------------------------------------------------------------


def _anchor(heading: str) -> str:
    text = heading.strip().lower().replace("`", "")
    text = re.sub(r"[^\w\s-]", "", text)
    return text.replace(" ", "-")


def check_the_surface_still_states_this(text: str) -> list[str]:
    """The subsection this script is the carrier for is still there, by anchor."""
    anchors = {
        _anchor(line.lstrip("#").strip()) for line in text.splitlines() if line.startswith("#")
    }
    if ANCHOR not in anchors:
        return [
            f"this carrier cites `{ANCHOR}`, which is not a heading of the surface. Either the "
            "subsection was reworded or the rule it performs is gone."
        ]
    return []


def check_the_carrier_still_calls_this(text: str) -> list[str]:
    """`hooks.json` still registers this file on the event that opens a session.

    ⛔ **And the timeout it registers is still longer than the budget this module stops on.** The
    two are one mechanism: a budget at or above the timeout means the harness kills the run first,
    and a killed run emits nothing -- so the half-finished sweep reads as a finished one, which is
    the failure the budget exists to convert into a sentence.
    """
    try:
        carrier = json.loads(text)
    except json.JSONDecodeError as error:
        return [f"{CARRIER.name} is not readable as JSON ({error}), so nothing calls this."]
    mine = Path(__file__).name
    problems = []
    timeouts = []
    for group in (carrier.get("hooks") or {}).get(CARRIER_EVENT) or []:
        for item in group.get("hooks") or []:
            named = " ".join(
                [str(item.get("command") or "")] + [str(a) for a in (item.get("args") or [])]
            )
            if mine in named:
                timeouts.append(item.get("timeout"))
                if "${CLAUDE_PLUGIN_ROOT}" not in named:
                    problems.append(
                        f"a `{CARRIER_EVENT}` handler names {mine} by a path the plugin root does "
                        "not expand — it must be addressed through `${CLAUDE_PLUGIN_ROOT}`"
                    )
    if not timeouts:
        problems.append(
            f"{CARRIER.name} registers no {CARRIER_EVENT} hook calling {mine}, so every tree a "
            "merge outside this session left behind is reaped by nothing."
        )
    for timeout in timeouts:
        # ⛔ **A margin and not an inequality.** `timeout > budget` is satisfied by one second,
        # which leaves the last tree's own work -- two host lookups, a fetch and a read of the
        # machine -- outside the limit, and a run killed there emits nothing. What has to fit
        # inside the timeout is the budget *plus* what one tree is allowed to cost.
        if not isinstance(timeout, int) or timeout < BUDGET_SECONDS + RESERVE_SECONDS:
            problems.append(
                f"a `{CARRIER_EVENT}` handler calling {mine} states a timeout of {timeout!r}, "
                f"which does not cover this module's budget of {BUDGET_SECONDS}s plus the "
                f"{RESERVE_SECONDS}s it holds back for one tree. The harness would kill the run "
                "before it could say what it did not reach."
            )
    return problems


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


class _Place:
    """A directory with the one attribute `claim._bare_world` reads off its argument.

    ⚠️ Not a `TemporaryDirectory`, deliberately: one created inside a helper is finalised when the
    helper returns, which deletes the bare repository and every clone of it the moment the fixture
    is handed back. Measured here, as a claim whose integration branch could not be derived.
    """

    def __init__(self, name: str) -> None:
        self.name = name


def _world(tmp: str, named: str = "world") -> tuple[str, str]:
    """`(the bare origin, a clone of it)`, both living as long as `tmp` does."""
    where = Path(tmp) / named
    where.mkdir(parents=True, exist_ok=True)
    origin, one, _two = claim._bare_world(_Place(str(where)))  # noqa: SLF001 -- the sibling's own
    return origin, one


def _trees(tmp: str) -> str:
    """The directory this fixture's project states as `branch_model.tree_dir`."""
    where = Path(tmp) / "trees"
    where.mkdir(parents=True, exist_ok=True)
    return str(where)


def _landed_status(tree: str, landed: bool = True, live: bool = False, **rest) -> claim.Status:
    """A reading stubbed at the tree's **own** commit.

    ⛔ **The sha is the tree's HEAD and never a placeholder.** A stub carrying a sha the repository
    does not have cannot be compared against the tree, so the arm that keeps a tree carrying
    commits the landed reading never saw fires on every such fixture -- which is the guard working
    and the fixture lying. Measured on this change, where three fixtures stubbed `"0" * 40`.
    """
    head = claim.git(tree, "rev-parse", "HEAD", check=False).stdout.strip() or None
    return claim.Status(
        True,
        head,
        claim.Holder(),
        claim.Liveness(live, "fixture", landed=landed, **rest),
        False,
    )


def _landed_world(tmp: str) -> tuple[str, str, str]:
    """A clone holding one tree whose branch has **landed** by the content arm.

    The shape a squash leaves: the branch carries commits of its own and differs from the
    integration branch in nothing. ⚠️ Built without a host, deliberately -- that is the arm § 10
    makes the primary one, and the one a bare repository can supply.

    Returns `(root, branch, tree)`.
    """
    _origin, work = _world(tmp)
    branch, tree = "feature/1-landed", str(Path(_trees(tmp)) / "1-landed")
    claim.take(work, branch, tree)
    for key, value in (("user.email", "a-worker"), ("user.name", "A Worker")):
        claim.git(tree, "config", key, value)
        claim.git(work, "config", key, value)
    (Path(tree) / "landed.txt").write_text("the work\n")
    claim.git(tree, "add", "landed.txt")
    claim.git(tree, "commit", "--quiet", "-m", "the work")
    claim.git(tree, "push", "--quiet", "--force", "origin", f"HEAD:{claim.REFS_PREFIX}{branch}")
    # The same content arriving on the integration branch as a different commit, which is what a
    # squash does and what makes ancestry useless here.
    (Path(work) / "landed.txt").write_text("the work\n")
    claim.git(work, "add", "landed.txt")
    claim.git(work, "commit", "--quiet", "-m", "the work, squashed")
    claim.git(work, "push", "--quiet", "origin", "main")
    return work, branch, tree


def _never_removes():
    """A remover that records rather than removes, for the arms about ordering."""
    seen: list[str] = []

    def run(branch: str, tree: str) -> tuple[str, str | None]:
        seen.append(tree)
        return f"released `{branch}`", None

    run.seen = seen  # type: ignore[attr-defined]
    return run


def self_test() -> int:  # noqa: PLR0915 -- one assertion per rule, read top to bottom
    suite = Suite()
    print("Each rule is shown a violation it must redden on, then the rule is held.\n")

    print("the landed reading is the claim's, and a landed tree is removed:")

    with tempfile.TemporaryDirectory() as tmp:
        work, branch, tree = _landed_world(tmp)
        held = claim.status(work, branch, "origin")
        suite.ok(
            "the fixture's branch reads as landed by content, with no host asked",
            held.liveness is not None and held.liveness.landed,
            held.report(),
        )
        # ⛔ The must-remove side first: a sweep that removes nothing passes every keep-side check
        # there is, so this is the plant that makes the rest of the suite mean anything.
        report = sweep(work, [], "never", tree_dir=_trees(tmp), occupants=lambda _p: [])
        suite.ok(
            "a landed tree is removed, and the sweep says which",
            [os.path.realpath(v.path) for v in report.removed] == [os.path.realpath(tree)]
            and not Path(tree).exists(),
            report.report(),
        )
        suite.ok(
            "and the local branch goes with it, so the claim is not left held",
            not claim._local_branch(work, branch),  # noqa: SLF001 -- the sibling's own reading
        )

    with tempfile.TemporaryDirectory() as tmp:
        _origin, work = _world(tmp)
        tree = str(Path(_trees(tmp)) / "2-in-flight")
        claim.take(work, "feature/2-in-flight", tree)
        report = sweep(work, [], "never", tree_dir=_trees(tmp), occupants=lambda _p: [])
        suite.ok(
            "a branch that has not landed is never removed by the sweep",
            Path(tree).exists() and not report.removed,
            report.report(),
        )
        suite.ok(
            "and the report says which reading kept it, rather than that it was skipped",
            any("has not landed" in v.reason for v in report.kept),
            report.report(),
        )
        # ⛔ The arm § 10 cares about most: a branch whose landing could not be *established* reads
        # exactly like one that has not landed, and only one of the two is a sentence a reader can
        # act on. What the host could not answer is carried through rather than collapsed.
        half = claim.Status(
            True,
            "0" * 40,
            claim.Holder(),
            claim.Liveness(
                True,
                "the ref carries commits beyond the integration branch",
                unestablished=["what the host records about this branch's pull requests"],
            ),
            False,
        )
        unreadable = sweep(work, [], "never", tree_dir=_trees(tmp), read=lambda _b: half, occupants=lambda _p: [])
        suite.ok(
            "⛔ a branch whose landing the host could not answer for is kept, not removed",
            Path(tree).exists() and not unreadable.removed,
            unreadable.report(),
        )
        suite.ok(
            "and the report says which answer was missing rather than only that it was kept",
            "what the host records" in unreadable.report(),
            unreadable.report(),
        )

    print("\nclean is not disposability:")

    with tempfile.TemporaryDirectory() as tmp:
        work, _branch, tree = _landed_world(tmp)
        (Path(tree) / ".gitignore").write_text("secret.env\nbuild/\nlink\n")
        claim.git(tree, "add", ".gitignore")
        claim.git(tree, "commit", "--quiet", "-m", "ignore some things")
        (Path(tree) / "secret.env").write_text("a credential minted by hand\n")
        # ⛔ The committed `.gitignore` moves the branch off the integration tip, so the landed
        # reading is taken again rather than assumed: this fixture is about the oracle and must
        # not pass because the branch stopped reading as landed.
        read = lambda _b: _landed_status(tree)  # noqa: E731
        report = sweep(work, [], "never", tree_dir=_trees(tmp), read=read, occupants=lambda _p: [])
        suite.ok(
            "a tree holding an ignored file no rebuild writes again is kept",
            Path(tree).exists() and not report.removed,
            report.report(),
        )
        suite.ok(
            "and the file is named, so the reader can rescue it",
            any("secret.env" in p for v in report.kept for p in v.paths),
            report.report(),
        )
        # The planted exemption: with the same path declared regenerable the tree goes. This is
        # what makes the assertion above an assertion about the oracle rather than about `kept`
        # being the default.
        gone = sweep(work, ["secret.env"], "never", tree_dir=_trees(tmp), read=read, occupants=lambda _p: [])
        suite.ok(
            "⛔ and with that path declared regenerable the same tree is removed",
            not Path(tree).exists() and len(gone.removed) == 1,
            gone.report(),
        )

    with tempfile.TemporaryDirectory() as tmp:
        work, _branch, tree = _landed_world(tmp)
        (Path(tree) / ".gitignore").write_text("link\nlinks/\n")
        claim.git(tree, "add", ".gitignore")
        claim.git(tree, "commit", "--quiet", "-m", "ignore the links")
        outside = Path(tmp) / "outside"
        outside.mkdir()
        (outside / "material.txt").write_text("not in any tree\n")
        os.symlink(str(outside / "material.txt"), str(Path(tree) / "link"))
        (Path(tree) / "links").mkdir()
        os.symlink(str(outside), str(Path(tree) / "links" / "whole"))
        read = lambda _b: _landed_status(tree)  # noqa: E731
        keeping, _unknown = precious(tree, [])
        suite.ok(
            "an ignored symlink is not precious, however it is ignored",
            keeping == [],
            str(keeping),
        )
        report = sweep(work, [], "never", tree_dir=_trees(tmp), read=read, occupants=lambda _p: [])
        suite.ok(
            "so a tree holding only ignored symlinks is removed",
            not Path(tree).exists() and len(report.removed) == 1,
            report.report(),
        )
        suite.ok(
            "and what the symlink pointed at is untouched, which is why the exemption is safe",
            (outside / "material.txt").exists(),
        )

    with tempfile.TemporaryDirectory() as tmp:
        work, _branch, tree = _landed_world(tmp)
        (Path(tree) / ".gitignore").write_text("cache/\n")
        claim.git(tree, "add", ".gitignore")
        claim.git(tree, "commit", "--quiet", "-m", "ignore the cache")
        deep = Path(tree) / "a" / "b" / "cache"
        deep.mkdir(parents=True)
        (deep / "object").write_text("rebuilt on demand\n")
        suite.ok(
            "a bare name covers the path wherever it appears, per § 10's matching rule",
            covered("a/b/cache/object", ["cache"]) == "cache",
        )
        suite.ok(
            "and an entry naming a directory covers everything beneath it",
            covered("build/out/thing.o", ["build"]) == "build",
        )
        suite.ok(
            "while a name that matches nothing in the path covers nothing",
            covered("a/b/cache/object", ["dist"]) is None,
        )
        keeping, _unknown = precious(tree, ["cache"])
        suite.ok("so the tree reads as holding nothing precious", keeping == [], str(keeping))

    with tempfile.TemporaryDirectory() as tmp:
        work, _branch, tree = _landed_world(tmp)
        (Path(tree) / "uncommitted.txt").write_text("work nobody has committed\n")
        read = lambda _b: _landed_status(tree)  # noqa: E731
        report = sweep(work, ["*"], "never", tree_dir=_trees(tmp), read=read, occupants=lambda _p: [])
        suite.ok(
            "⛔ an untracked change keeps the tree even with everything declared regenerable",
            Path(tree).exists() and not report.removed,
            report.report(),
        )
        suite.ok(
            "and it is named, the regenerable list reaching ignored paths only",
            any("uncommitted.txt" in p for v in report.kept for p in v.paths),
            report.report(),
        )

    print("\nthe trees that are never touched:")

    with tempfile.TemporaryDirectory() as tmp:
        work, _branch, tree = _landed_world(tmp)
        remover = _never_removes()
        report = sweep(
            work, [], "never", read=lambda _b: None, remove=remover, occupants=lambda _p: []
        )
        suite.ok(
            "the main checkout is not a tree the sweep looks at at all",
            all(os.path.realpath(v.path) != os.path.realpath(work) for v in report.verdicts),
            report.report(),
        )
        suite.ok(
            "a claim that could not be read removes nothing, and says what was missing",
            not remover.seen and any(v.unestablished for v in report.kept),
            report.report(),
        )

    with tempfile.TemporaryDirectory() as tmp:
        work, _branch, tree = _landed_world(tmp)
        remover = _never_removes()
        report = sweep(
            work,
            [],
            "never",
            remove=remover,
            occupants=lambda _p: [(4242, "another-session")],
        )
        suite.ok(
            "a tree another live session occupies is kept, and nothing is asked to remove it",
            not remover.seen and Path(tree).exists(),
            report.report(),
        )
        suite.ok(
            "and the occupant is named, so the reader need not look it up",
            any("4242" in v.reason for v in report.kept),
            report.report(),
        )
        unreadable = sweep(work, [], "never", tree_dir=_trees(tmp), remove=remover, occupants=lambda _p: None)
        suite.ok(
            "⛔ an unreadable open-file table is unestablished and not idle, so the tree stays",
            not remover.seen and any(v.unestablished for v in unreadable.kept),
            unreadable.report(),
        )

    with tempfile.TemporaryDirectory() as tmp:
        work, _branch, tree = _landed_world(tmp)
        remover = _never_removes()
        # ⛔ The shipped reading and not a stub for it, and this process's own working directory
        # rather than an argument: a session pinned to its tree is a session whose cwd *is* the
        # tree, which is the whole of what `claim.standing_in` asks. A lambda here would assert
        # the sweep honours a verdict and say nothing about how that verdict is reached.
        here = os.getcwd()
        try:
            os.chdir(tree)
            report = sweep(work, [], "never", tree_dir=_trees(tmp), remove=remover, occupants=lambda _p: [])
        finally:
            os.chdir(here)
        suite.ok(
            "⛔ the caller's own tree is stopped on rather than removed, even though it landed",
            not remover.seen and Path(tree).exists(),
            report.report(),
        )
        suite.ok(
            "and the stop says what clears it — leaving, and a later sweep where there is no exit",
            any("standing in it" in v.reason and "later sweep" in v.reason for v in report.kept),
            report.report(),
        )
        # ⛔ The other end of the same proof, which is what makes it end to end rather than an
        # assertion about one call: the later session is this process once it has left, running
        # the identical sweep with nothing injected into the reading, and the tree goes.
        gone = sweep(work, [], "never", tree_dir=_trees(tmp), occupants=lambda _p: [])
        suite.ok(
            "⛔ and a later session, standing outside it, removes the tree the pinned one left",
            not Path(tree).exists() and len(gone.removed) == 1,
            gone.report(),
        )

    with tempfile.TemporaryDirectory() as tmp:
        work, _branch, _tree = _landed_world(tmp)
        helper = Path(work) / ".helpers" / "one"
        claim.git(work, "worktree", "add", "--quiet", "--detach", str(helper))
        outside = Path(tmp) / "by-hand"
        claim.git(work, "worktree", "add", "--quiet", "--detach", str(outside))
        report = sweep(work, [], "never", tree_dir=_trees(tmp), occupants=lambda _p: [])
        named = {os.path.realpath(v.path): v for v in report.kept}
        suite.ok(
            "⛔ a tree outside the stated tree directory is named and not removed, whether the "
            "harness cut it inside the checkout or a person cut it beside the checkout",
            helper.exists()
            and outside.exists()
            and all(
                os.path.realpath(p) in named
                and "not under this project's tree directory" in named[os.path.realpath(p)].reason
                for p in (helper, outside)
            ),
            report.report(),
        )
        suite.ok(
            "and neither prompts anybody, a tree nobody cut for an item being nobody's to act on",
            all(not named[os.path.realpath(p)].attention for p in (helper, outside)),
            report.message(),
        )

    # ⛔ **The anchor, which every fixture above misses by stating an absolute directory.** Found
    # by running the shipped sweep on this repository rather than by reading: a relative `tree_dir`
    # joined to the caller's own tree resolves one level too deep, every real tree reads as
    # outside, and the carrier becomes the no-op it exists to end.
    with tempfile.TemporaryDirectory() as tmp:
        work, _branch, tree = _landed_world(tmp)
        here = os.getcwd()
        try:
            # Standing in the tree, which is where this carrier's own session usually is.
            os.chdir(tree)
            resolved = _resolve("../../trees", claim.git(work, "rev-parse", "--show-toplevel").stdout.strip())
            suite.ok(
                "⛔ a relative tree directory resolves against the main checkout, not the caller",
                os.path.realpath(resolved) == os.path.realpath(_trees(tmp)),
                f"{resolved} vs {_trees(tmp)}",
            )
            found = registered(work, "../../trees")
            suite.ok(
                "so the project's own trees read as inside it, from a session standing in one",
                any(
                    os.path.realpath(t.path) == os.path.realpath(tree) and not t.outside
                    for t in found
                ),
                str([(t.path, t.outside) for t in found]),
            )
        finally:
            os.chdir(here)
        suite.ok(
            "and an absolute directory is taken as stated, which is what the fixtures above pass",
            _resolve(_trees(tmp), work) == _trees(tmp),
        )

    # ⛔ The other direction of the same scope, and the one a review found as a silent no-op: § 10
    # names a project that nests its trees **inside** its checkout, and the helper-tree reading
    # answers *not a work tree* for every one of them — so the sweep pruned nothing there and
    # reported each landed tree as a helper's, which is the one reason the surface keeps quiet.
    with tempfile.TemporaryDirectory() as tmp:
        _origin, work = _world(tmp)
        inside = Path(work) / ".worktrees"
        inside.mkdir()
        branch, tree = "feature/6-nested", str(inside / "6-nested")
        claim.take(work, branch, tree)
        for key, value in (("user.email", "n"), ("user.name", "N")):
            claim.git(tree, "config", key, value)
            claim.git(work, "config", key, value)
        (Path(tree) / "nested.txt").write_text("the work\n")
        claim.git(tree, "add", "nested.txt")
        claim.git(tree, "commit", "--quiet", "-m", "the work")
        claim.git(tree, "push", "--quiet", "--force", "origin", f"HEAD:{claim.REFS_PREFIX}{branch}")
        (Path(work) / "nested.txt").write_text("the work\n")
        claim.git(work, "add", "nested.txt")
        claim.git(work, "commit", "--quiet", "-m", "squashed")
        claim.git(work, "push", "--quiet", "origin", "main")
        under = sweep(work, [], "never", tree_dir=str(inside), occupants=lambda _p: [])
        suite.ok(
            "⛔ a tree under a tree directory that is itself inside the checkout is pruned, not "
            "read as a helper's",
            not Path(tree).exists() and len(under.removed) == 1,
            under.report(),
        )
        # And the fallback, which is what the sweep had before the directory was passed in: with
        # no directory stated the same tree reads as a helper's and is kept. Stated as the weaker
        # reading rather than left to look like a bug.
        _origin2, work2 = _world(tmp, "second")
        inside2 = Path(work2) / ".worktrees"
        inside2.mkdir()
        claim.take(work2, "feature/7-nested", str(inside2 / "7-nested"))
        blind = sweep(work2, [], "never", occupants=lambda _p: [])
        suite.ok(
            "while with no tree directory stated the helper-tree reading answers instead",
            any("not under this project's tree directory" in v.reason for v in blind.kept),
            blind.report(),
        )

    with tempfile.TemporaryDirectory() as tmp:
        work, _branch, tree = _landed_world(tmp)
        report = sweep(
            work,
            [],
            "never",
            remove=lambda _b, _t: ("", "refused: the tree holds something git does not track"),
            occupants=lambda _p: [],
        )
        suite.ok(
            "a landed tree whose release was refused is kept, and the refusal is carried through",
            Path(tree).exists() and any("refused" in v.reason for v in report.kept),
            report.report(),
        )
        suite.ok(
            "⛔ and it reaches the person, rather than being swallowed as an ordinary kept tree",
            "refused" in report.message(),
            report.message(),
        )

    with tempfile.TemporaryDirectory() as tmp:
        _origin, work = _world(tmp)
        claim.take(work, "feature/5-quiet", str(Path(_trees(tmp)) / "5-quiet"))
        live = claim.Status(
            True,
            "0" * 40,
            claim.Holder(),
            claim.Liveness(True, "an open pull request references the ref"),
            False,
        )
        ordinary = sweep(
            work, [], "never", tree_dir=_trees(tmp), read=lambda _b: live, occupants=lambda _p: []
        )
        suite.ok(
            "⚠️ while a tree whose branch is live says nothing at all, that being every tree "
            "somebody is working in",
            bool(ordinary.kept) and ordinary.message() == "",
            ordinary.message() or ordinary.report(),
        )
        # ⛔ The other half of the same table, and the one the quiet arm must not swallow: § 10
        # makes an orphaned candidate a person's call, so the sweep that finds one says so.
        orphaned = sweep(work, [], "never", tree_dir=_trees(tmp), occupants=lambda _p: [])
        suite.ok(
            "⛔ but an orphaned candidate is said, that being the reading § 10 asks about",
            "has not landed" in orphaned.message(),
            orphaned.message() or orphaned.report(),
        )

    print("\nthe published ref is `delete_branch`'s and nobody else's:")

    for stated, expected in (("procedure", False), ("host", True), ("never", True)):
        with tempfile.TemporaryDirectory() as tmp:
            work, branch, tree = _landed_world(tmp)
            report = sweep(work, [], stated, tree_dir=_trees(tmp), occupants=lambda _p: [])
            standing_ref = claim.remote_ref_sha(work, "origin", branch)
            suite.ok(
                f"under `{stated}` the published ref "
                + ("stands" if expected else "is deleted by this carrier"),
                (standing_ref is not None) == expected and len(report.removed) == 1,
                f"ref {'present' if standing_ref else 'gone'}; {report.report()}",
            )
            suite.ok(
                f"and under `{stated}` the tree and the local branch go either way",
                not Path(tree).exists()
                and not claim._local_branch(work, branch),  # noqa: SLF001
                report.report(),
            )

    print("\nbounded, and it says what it did not reach:")

    with tempfile.TemporaryDirectory() as tmp:
        work, _branch, _tree = _landed_world(tmp)
        for index in (2, 3):
            claim.take(work, f"feature/{index}-more", str(Path(_trees(tmp)) / f"{index}-more"))
        ticks = iter([0.0] + [100.0] * 20)
        remover = _never_removes()
        report = sweep(
            work,
            [],
            "never",
            budget=10,
            clock=lambda: next(ticks),
            remove=remover,
            occupants=lambda _p: [],
        )
        suite.ok(
            "a budget that runs out stops the sweep rather than overrunning the hook's timeout",
            not report.verdicts and not remover.seen,
            report.report(),
        )
        suite.ok(
            "and names every tree it did not look at, rather than reporting them in order",
            len(report.unreached) == 3,
            report.report(),
        )
        suite.ok(
            "and the count is in the report a reader sees",
            "not looked at" in report.report(),
            report.report(),
        )

    print("\na kept tree is re-examined, never remembered:")

    with tempfile.TemporaryDirectory() as tmp:
        _origin, work = _world(tmp)
        tree = str(Path(_trees(tmp)) / "4-kept")
        claim.take(work, "feature/4-kept", tree)
        asked: list[str] = []

        def read(branch: str):
            asked.append(branch)
            return claim.Status(
                True, "0" * 40, claim.Holder(), claim.Liveness(True, "a helper holds it"), False
            )

        first = sweep(work, [], "never", tree_dir=_trees(tmp), read=read, occupants=lambda _p: [])
        second = sweep(work, [], "never", tree_dir=_trees(tmp), read=read, occupants=lambda _p: [])
        suite.ok(
            "⛔ the second sweep reads the same tree again rather than recalling a verdict",
            len(asked) == 2,
            f"the reading was taken {len(asked)} time(s)",
        )
        suite.ok(
            "and reaches the same answer, there being no store for either run to disagree with",
            [v.reason for v in first.kept] == [v.reason for v in second.kept],
        )
        suite.ok(
            "and no sweep wrote anything into the tree it kept",
            sorted(p.name for p in Path(tree).iterdir()) == [".git", "README.md"],
            str(sorted(p.name for p in Path(tree).iterdir())),
        )

    print("\nthe event that opens a session:")

    with tempfile.TemporaryDirectory() as tmp:
        bare = Path(tmp) / "states-nothing"
        bare.mkdir()
        ran: list[str] = []
        said = answer({"cwd": str(bare)}, run=lambda *a, **k: ran.append("ran") or Report())
        suite.ok(
            "⛔ a project that states no configuration is answered with silence and not a report",
            said == {} and not ran,
            str(said),
        )

    with tempfile.TemporaryDirectory() as tmp:
        where = Path(tmp) / "in-place"
        (where / ".claude").mkdir(parents=True)
        shutil.copy(
            Path(__file__).resolve().parent.parent / "config" / "examples" / "none.yaml",
            where / ".claude" / "mjolnir.yaml",
        )
        ran = []
        said = answer({"cwd": str(where)}, run=lambda *a, **k: ran.append("ran") or Report())
        suite.ok(
            "⛔ and a project that cuts no tree is answered with silence, its key being null",
            said == {} and not ran,
            str(said),
        )

    with tempfile.TemporaryDirectory() as tmp:
        where = Path(tmp) / "broken"
        (where / ".claude").mkdir(parents=True)
        (where / ".claude" / "mjolnir.yaml").write_text("roots: [this is not a block]\n")
        said = answer({"cwd": str(where)})
        suite.ok(
            "⚠️ while a configuration that is stated and does not resolve is reported",
            "did not resolve" in str(said.get("systemMessage", "")),
            str(said),
        )

    with tempfile.TemporaryDirectory() as tmp:
        where = Path(tmp) / "configured"
        (where / ".claude").mkdir(parents=True)
        shipped = Path(__file__).resolve().parent.parent / "config" / "examples"
        shutil.copy(shipped / "github-issues.yaml", where / ".claude" / "mjolnir.yaml")
        quiet = answer({"cwd": str(where)}, run=lambda *a, **k: Report())
        suite.ok(
            "⚠️ a sweep with nothing to say says nothing, this event firing on every session",
            quiet == {},
            str(quiet),
        )
        loud = answer(
            {"cwd": str(where)},
            run=lambda *a, **k: Report(
                verdicts=[Verdict("/a/tree", "feature/9-x", True, "its branch landed")]
            ),
        )
        suite.ok(
            "⛔ and a sweep that removed a tree says so, to the person rather than into context",
            "systemMessage" in loud and "additionalContext" not in json.dumps(loud),
            str(loud),
        )
        failed = answer({"cwd": str(where)}, run=_raises)
        suite.ok(
            "a sweep that could not run reports that it examined nothing, and interrupts nothing",
            "did not run" in str(failed.get("systemMessage", "")),
            str(failed),
        )

    out = io.StringIO()
    code = hook(io.StringIO("not json at all"), out=out)
    suite.ok(
        "a payload that is not readable at all interrupts nothing and says nothing",
        code == 0 and out.getvalue() == "",
        out.getvalue(),
    )

    print("\nwork git already has, which a status cannot see:")

    # ⛔ The worst defect of this carrier's first draft, planted both ways. A branch pushed,
    # squash-merged and then committed to once more without pushing reads **landed** — the landed
    # test is taken against the published ref — while `git status` is empty, because the work is
    # committed. The tree was removed and the local branch force-deleted.
    with tempfile.TemporaryDirectory() as tmp:
        work, branch, tree = _landed_world(tmp)
        (Path(tree) / "followup.txt").write_text("a fix nobody pushed\n")
        claim.git(tree, "add", "followup.txt")
        claim.git(tree, "commit", "--quiet", "-m", "the follow-up fix")
        held = claim.status(work, branch, "origin")
        suite.ok(
            "the fixture is the dangerous shape: landed, clean, and carrying an unpushed commit",
            bool(held.liveness and held.liveness.landed)
            and claim.git(tree, "status", "--porcelain").stdout.strip() == ""
            and prune_precious_is_empty(tree),
            held.report(),
        )
        report = sweep(work, [], "never", tree_dir=_trees(tmp), occupants=lambda _p: [])
        suite.ok(
            "⛔ a landed tree carrying a commit the reading never saw is kept, not removed",
            Path(tree).exists() and not report.removed,
            report.report(),
        )
        suite.ok(
            "and the commit is named, so a reader can see what would have been lost",
            any("the follow-up fix" in p for v in report.kept for p in v.paths),
            report.report(),
        )
        suite.ok(
            "and it reaches the person rather than sitting in the full report alone",
            "never saw" in report.message(),
            report.message(),
        )

    # The must-remove counterpart: the identical fixture with nothing unpushed goes.
    with tempfile.TemporaryDirectory() as tmp:
        work, branch, tree = _landed_world(tmp)
        carried, unread = unpushed(tree, claim.remote_ref_sha(work, "origin", branch))
        suite.ok(
            "⛔ and with nothing unpushed the same reading finds no commit to keep it for",
            carried == [] and unread == [],
            f"{carried} {unread}",
        )
        gone = sweep(work, [], "never", tree_dir=_trees(tmp), occupants=lambda _p: [])
        suite.ok(
            "so the tree is removed, which is what makes the arm above an assertion",
            not Path(tree).exists() and len(gone.removed) == 1,
            gone.report(),
        )

    with tempfile.TemporaryDirectory() as tmp:
        work, branch, tree = _landed_world(tmp)
        behind = claim.git(tree, "rev-parse", "HEAD").stdout.strip()
        carried, unread = unpushed(tree, "0" * 40)
        suite.ok(
            "a comparison that cannot be made keeps the tree and says so",
            carried == [] and bool(unread),
            f"{carried} {unread}",
        )
        suite.ok(
            "and a reading taken on no commit at all is unestablished rather than clean",
            unpushed(tree, None) == ([], ["which commit the landed reading was taken on"]),
            str(unpushed(tree, None)),
        )
        suite.ok("the fixture's head was readable, so the arm above is the one asserted",
                 bool(behind))

    print("\nthe ref the host deleted on merge:")

    # ⛔ The second firing defect: under § 2's `delete_branch: host` the ref is gone by the time
    # any sweep runs, and a reading that answered *nothing could be established* made this carrier
    # a no-op on exactly the projects whose refs are tidied up for them.
    with tempfile.TemporaryDirectory() as tmp:
        work, branch, tree = _landed_world(tmp)
        claim.git(work, "push", "--quiet", "origin", "--delete", branch)
        held = claim.status(work, branch, "origin")
        suite.ok(
            "a ref the host deleted still answers *landed*, read from the branch on this machine",
            held.taken is False and bool(held.liveness and held.liveness.landed),
            held.report(),
        )
        suite.ok(
            "and the claim is still free, which is what every other caller keys on",
            not claim.claim_free(work, branch)[0] is False,
        )
        report = sweep(work, [], "host", tree_dir=_trees(tmp), occupants=lambda _p: [])
        suite.ok(
            "⛔ so the sweep prunes under `host` rather than doing nothing forever",
            not Path(tree).exists() and len(report.removed) == 1,
            report.report(),
        )

    print("\nthe oracle's own failure directions:")

    with tempfile.TemporaryDirectory() as tmp:
        keeping, unknown = precious(tmp, [])
        suite.ok(
            "⛔ a tree whose contents could not be read is unestablished, never empty",
            keeping == [] and len(unknown) == 1,
            f"{keeping} {unknown}",
        )
        work, _branch, tree = _landed_world(tmp)
        report = sweep(
            work,
            [],
            "never",
            tree_dir=_trees(tmp),
            read=lambda _b: _landed_status(tree),
            occupants=lambda _p: [],
            remove=lambda _b, _t: ("", None),
        )
        suite.ok(
            "and a removal that reported success while the tree is still there is not a removal",
            any("still there" in v.reason for v in report.kept) and not report.removed,
            report.report(),
        )
        suite.ok(
            "which reaches the person, a destructive act misreported being worse than a refusal",
            "still there" in report.message(),
            report.message(),
        )

    suite.ok(
        "an entry naming nothing exempts nothing, so the tree is kept",
        prune_covered_declines(),
    )
    suite.ok(
        "⛔ an entry anchored at the root matches there and nowhere else",
        covered("build/out", ["/build"]) == "/build"
        and covered("a/build/out", ["/build"]) is None
        and covered("a/build/out", ["build"]) == "build",
    )

    with tempfile.TemporaryDirectory() as tmp:
        shut = Path(tmp) / "shut"
        shut.mkdir()
        (shut / "f").write_text("x")
        os.chmod(shut, 0o000)
        try:
            readable = os.access(shut, os.R_OK)
            if readable:
                suite.ok(
                    "a directory this run cannot be stopped from reading, so the arm is unheld",
                    True,
                    "running with rights that ignore the mode",
                )
            else:
                suite.ok(
                    "⛔ an unreadable directory is not an empty one, so it is not all symlinks",
                    only_links(shut) is False,
                )
        finally:
            os.chmod(shut, 0o755)

    print("\nthe parse, where a path is not a plain word:")

    with tempfile.TemporaryDirectory() as tmp:
        work, _branch, tree = _landed_world(tmp)
        (Path(tree) / ".gitignore").write_text("*.keep\n")
        claim.git(tree, "add", ".gitignore")
        claim.git(tree, "commit", "--quiet", "-m", "ignore the keeps")
        # A path carrying the sequence the rename parse used to split on, and one outside ASCII
        # that git would quote without `-z`.
        (Path(tree) / "secret -> cache.keep").write_text("a credential\n")
        (Path(tree) / "café.keep").write_text("a credential\n")
        keeping, unknown = precious(tree, ["cache"])
        suite.ok(
            "⛔ an ignored path whose own name contains the rename separator is read whole",
            any("secret -> cache.keep" in p for p in keeping),
            f"{keeping} {unknown}",
        )
        suite.ok(
            "⛔ and a path outside ASCII arrives unquoted, so an entry naming it can match it",
            any("café" in p for p in keeping),
            f"{keeping} {unknown}",
        )
        suite.ok(
            "while the entry that names neither exempts neither",
            len(keeping) == 2,
            str(keeping),
        )
        exempt = precious(tree, ["*.keep"])
        suite.ok(
            "and an entry that does name them exempts both",
            exempt == ([], []),
            str(exempt),
        )

    with tempfile.TemporaryDirectory() as tmp:
        work, _branch, tree = _landed_world(tmp)
        spaced = str(Path(_trees(tmp)) / "8 a tree with spaces")
        claim.take(work, "feature/8-spaces", spaced)
        found = {os.path.realpath(t.path) for t in registered(work, _trees(tmp))}
        suite.ok(
            "a tree whose path carries spaces is one entry, not several",
            os.path.realpath(spaced) in found,
            str(sorted(found)),
        )
        shutil.rmtree(spaced)
        stale = [t for t in registered(work, _trees(tmp)) if t.prunable]
        suite.ok(
            "a registration whose directory is gone is read as prunable",
            len(stale) == 1,
            str([(t.path, t.prunable) for t in registered(work, _trees(tmp))]),
        )
        report = sweep(work, [], "never", tree_dir=_trees(tmp), occupants=lambda _p: [])
        suite.ok(
            "⛔ and the sweep clears the registration rather than saying the same sentence at "
            "every session open",
            not any(t.prunable for t in registered(work, _trees(tmp)))
            and not any(v.attention for v in report.kept),
            report.report(),
        )

    print("\none tree's failure is not the sweep's:")

    with tempfile.TemporaryDirectory() as tmp:
        work, branch, tree = _landed_world(tmp)
        second = str(Path(_trees(tmp)) / "9-second")
        claim.take(work, "feature/9-second", second)
        asked: list[str] = []

        def flaky(named: str):
            asked.append(named)
            if named == "feature/9-second":
                raise claim.ClaimError("could not read `origin`: the network is gone")
            return _landed_status(tree)

        report = sweep(work, [], "never", tree_dir=_trees(tmp), read=flaky, occupants=lambda _p: [])
        suite.ok(
            "⛔ a reading that raises for one tree leaves the other tree's verdict standing",
            len(report.verdicts) == 2 and len(asked) == 2,
            report.report(),
        )
        suite.ok(
            "and the removal that did happen is still reported, not discarded with the exception",
            not Path(tree).exists() and len(report.removed) == 1,
            report.report(),
        )
        suite.ok(
            "while the tree that raised is kept, named, and carries what could not be read",
            any("ClaimError" in v.reason and v.unestablished for v in report.kept),
            report.report(),
        )

    with tempfile.TemporaryDirectory() as tmp:
        _origin, work = _world(tmp)
        broken = sweep(str(Path(tmp) / "not-a-repository"), [], "never", tree_dir=_trees(tmp))
        suite.ok(
            "and a repository whose trees could not be listed at all says that and nothing else",
            not broken.verdicts and len(broken.unestablished) == 1,
            broken.report(),
        )

    print("\nthe session's own directory, and not this process's:")

    with tempfile.TemporaryDirectory() as tmp:
        work, _branch, tree = _landed_world(tmp)
        suite.ok(
            "⛔ the stop reads the directory it is handed, which is the session's",
            claim.standing_in(tree, here=tree) is True
            and claim.standing_in(tree, here=str(Path(tmp))) is False,
        )
        remover = _never_removes()
        held_back = sweep(
            work,
            [],
            "never",
            tree_dir=_trees(tmp),
            here=tree,
            remove=remover,
            occupants=lambda _p: [],
        )
        suite.ok(
            "so a session standing in its own tree holds it, whatever this process's cwd is",
            not remover.seen and Path(tree).exists(),
            held_back.report(),
        )
        elsewhere = sweep(
            work, [], "never", tree_dir=_trees(tmp), here=str(Path(tmp)), occupants=lambda _p: []
        )
        suite.ok(
            "⛔ and a session standing elsewhere removes the same tree",
            not Path(tree).exists() and len(elsewhere.removed) == 1,
            elsewhere.report(),
        )

    print("\nwhat the event hands the sweep, and what it emits:")

    with tempfile.TemporaryDirectory() as tmp:
        where = Path(tmp) / "configured"
        (where / ".claude").mkdir(parents=True)
        shipped = Path(__file__).resolve().parent.parent / "config" / "examples"
        shutil.copy(shipped / "github-issues.yaml", where / ".claude" / "mjolnir.yaml")
        # A repository, because the arm below runs the real sweep and a directory that is not one
        # answers *which trees this repository has* rather than answering about trees.
        claim.git(".", "init", "--quiet", str(where), check=False)
        handed: dict = {}

        def record(*args, **kwargs):
            handed["args"], handed["kwargs"] = args, kwargs
            return Report()

        answer({"cwd": str(where)}, run=record)
        suite.ok(
            "⛔ the configured regenerable list reaches the sweep, rather than a default",
            handed["args"][1] == [],
            str(handed.get("args")),
        )
        suite.ok(
            "⛔ and so does `delete_branch`, which decides whether a published ref is deleted",
            handed["args"][2] == "host",
            str(handed.get("args")),
        )
        suite.ok(
            "⛔ and the tree directory as the project states it, for the sweep to anchor on the "
            "main checkout rather than on whichever tree this session is standing in",
            handed["kwargs"]["tree_dir"] == "../<project>-trees",
            str(handed.get("kwargs")),
        )
        suite.ok(
            "⛔ and the session's own directory, which is the one stop that protects a live tree",
            handed["kwargs"]["here"] == str(where),
            str(handed.get("kwargs")),
        )
        out = io.StringIO()
        code = hook(
            io.StringIO(json.dumps({"hook_event_name": CARRIER_EVENT, "cwd": str(where)})), out=out
        )
        suite.ok(
            "a payload in a project that states no tree to prune emits nothing and interrupts "
            "nothing",
            code == 0 and out.getvalue() == "",
            out.getvalue(),
        )

    said = Report(
        verdicts=[
            Verdict(
                "/a/tree",
                "feature/9-x",
                False,
                "its branch has landed and it holds files no rebuild writes again",
                paths=["a.env"],
                unestablished=["what the host records"],
                attention=True,
            )
        ]
    )
    suite.ok(
        "⛔ the paths a reader may want to rescue are in the message, not the full report alone",
        "a.env" in said.message(),
        said.message(),
    )
    suite.ok(
        "⛔ and so is what could not be established, § 11 having no quiet form",
        "what the host records" in said.message(),
        said.message(),
    )
    quiet_arms = Report(
        verdicts=[
            Verdict("/t1", "b1", False, "another session is working at or below it: x (1)"),
            Verdict("/t2", None, False, "it is not under this project's tree directory"),
        ]
    )
    suite.ok(
        "while the arms the surface's own table keeps out of the event stay out of it",
        quiet_arms.message() == "" and len(quiet_arms.lines()) == 2,
        quiet_arms.message() or str(quiet_arms.lines()),
    )

    print("\nthe carrier and the surface:")

    surface = SURFACE.read_text(encoding="utf-8")
    suite.ok(
        "the surface still states the subsection this carrier performs",
        not check_the_surface_still_states_this(surface),
        "; ".join(check_the_surface_still_states_this(surface)),
    )
    suite.ok(
        "⛔ and it reddens when the heading it cites is gone",
        bool(check_the_surface_still_states_this(
            surface.replace("### Pruning a tree whose branch has landed", "### Something else")
        )),
    )
    carrier = CARRIER.read_text(encoding="utf-8")
    suite.ok(
        "the carrier still registers this script on the event that opens a session",
        not check_the_carrier_still_calls_this(carrier),
        "; ".join(check_the_carrier_still_calls_this(carrier)),
    )
    suite.ok(
        "⛔ and it reddens when the registration is gone",
        bool(check_the_carrier_still_calls_this(
            carrier.replace(Path(__file__).name, "something-else.py")
        )),
    )
    suite.ok(
        "⛔ and it reddens when the timeout stops covering this module's own budget",
        bool(check_the_carrier_still_calls_this(carrier.replace('"timeout": 60', '"timeout": 10'))),
    )

    print()
    if suite.failures:
        print(f"{suite.failures} check(s) failed.")
        return 1
    print("every check passed, each having been shown it can fail.")
    return 0


def _raises(*_args, **_kwargs):
    raise RuntimeError("a sweep that could not run")


def prune_precious_is_empty(tree: str) -> bool:
    """Whether the file oracle finds nothing — the half that cannot see a commit."""
    return precious(tree, []) == ([], [])


def prune_covered_declines() -> bool:
    """An entry this language cannot compare declines, which keeps the tree.

    ⚠️ Asserted through `covered` rather than against `PurePosixPath` directly: what matters is
    that the decline reaches the caller as *not covered*, and a test of the exception alone would
    pass with the `except` arm returning the pattern.
    """
    return covered("a/b", [""]) is None and covered("a/b", ["b"]) == "b"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--self-test", action="store_true", help="plant a violation per rule, then hold the rule"
    )
    sub = parser.add_subparsers(dest="arm")
    sub.add_parser("hook", help=f"answer a {CARRIER_EVENT} payload on stdin")
    sweeping = sub.add_parser("sweep", help="sweep this project's trees and report")
    sweeping.add_argument(
        "--skills-root", default=".", help="the root the configuration is resolved relative to"
    )

    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    if args.arm == "hook":
        return hook(sys.stdin)
    if args.arm == "sweep":
        reader = shared_reader()
        if reader is None:
            print("⛔ the configuration reader is not reachable, so no tree was examined.")
            return 1
        if not reader.configured(args.skills_root):
            print(
                "this project states no configuration, so there is nothing to sweep and no tree "
                "this procedure knows about."
            )
            return 0
        try:
            loaded = reader.load(args.skills_root, check_paths=False)
        except Exception as error:  # noqa: BLE001 -- a verdict rather than a traceback
            print(f"⛔ this project's configuration did not resolve, so no tree was examined: {error}")
            return 1
        if loaded.get("branch_model.kind") != "worktree":
            print("`branch_model.kind` is `in_place` here, so no tree is ever cut or pruned.")
            return 0
        stated = loaded.get("branch_model.tree_dir")
        try:
            report = sweep(
                loaded.code_root,
                list(loaded.get("branch_model.regenerable") or []),
                str(loaded.get("host.landing.delete_branch") or ""),
                tree_dir=stated,
            )
        except claim.ClaimError as error:
            print(f"⛔ the trees of this project could not be listed, so none was examined: {error}")
            return 1
        print(report.report())
        return 0
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
