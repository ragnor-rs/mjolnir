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
BUDGET_SECONDS = 45

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
    nested: bool = False


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
        said += [
            f"kept {v.path} — {v.reason}" + (f" ({', '.join(v.paths)})" if v.paths else "")
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


def registered(root: str | Path) -> list[Registered]:
    """Every worktree this repository has, main and helper trees included and marked as such.

    ⛔ **Nothing is filtered out here.** A tree the sweep may not touch is still a tree the report
    names, by § 10's rule that a kept tree is named with what kept it -- and a helper tree dropped
    at this layer is a tree nothing ever mentions, which is how three of them outlived a merge on
    this repository with nothing reaping them.

    `nested` is `claim.a_work_tree`'s reading and not a second one: a tree the harness cut for a
    helper is not a work tree under either branch model, and the test is structural because a
    directory name belongs to whichever harness ships it.
    """
    proc = claim.git(root, "worktree", "list", "--porcelain")
    found: list[Registered] = []
    main_tree: str | None = None
    path: str | None = None
    branch: str | None = None
    for line in proc.stdout.splitlines() + [""]:
        if line.startswith("worktree "):
            if path is not None:
                found.append(_entry(path, branch, main_tree))
            path = line[len("worktree ") :].strip()
            branch = None
            if main_tree is None:
                main_tree = path
        elif line.startswith("branch "):
            ref = line[len("branch ") :].strip()
            if ref.startswith(claim.REFS_PREFIX):
                branch = ref[len(claim.REFS_PREFIX) :]
        elif line == "" and path is not None:
            found.append(_entry(path, branch, main_tree))
            path, branch = None, None
    return found


def _entry(path: str, branch: str | None, main_tree: str | None) -> Registered:
    main = main_tree is not None and os.path.realpath(path) == os.path.realpath(main_tree)
    nested = not main and main_tree is not None and not claim.a_work_tree(path, main_tree)
    return Registered(path=path, branch=branch, main=main, nested=nested)


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
        for candidate in candidates:
            if str(candidate) in ("", "."):
                continue
            try:
                if candidate.match(pattern):
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
    # ⛔ `--ignored=matching` and `--untracked-files=all`, and both are the rule rather than a
    # preference. The default collapses a directory whose whole content is ignored into the
    # *topmost* untracked directory above it, so a tree holding `a/b/cache/` is reported as
    # holding `a/` -- and then a `regenerable` entry naming the cache matches nothing, the tree is
    # kept forever, and the project's own statement is silently inert. Measured here, as a fixture
    # that declared its cache regenerable and was kept anyway.
    proc = claim.git(
        tree,
        "status",
        "--porcelain",
        "--ignored=matching",
        "--untracked-files=all",
        check=False,
    )
    if proc.returncode != 0:
        return [], [f"what `{tree}` holds could not be read: {proc.stderr.strip()}"]
    keeping: list[str] = []
    for line in proc.stdout.splitlines():
        if len(line) < 4:
            continue
        code, named = line[:2], line[3:].strip().strip('"')
        # A rename's two paths; the destination is the one in the tree.
        if " -> " in named:
            named = named.split(" -> ", 1)[1]
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
    remote: str = "origin",
    budget: float = BUDGET_SECONDS,
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
    standing = standing if standing is not None else claim.standing_in
    remove = remove if remove is not None else _remover(root, remote, delete_branch)

    report = Report()
    started = clock()
    trees = registered(root)
    for index, tree in enumerate(trees):
        if tree.main:
            continue
        if clock() - started >= budget:
            # ⛔ Everything from here on is unreached rather than clean, and the remaining entries
            # are named rather than counted alone.
            report.unreached = [t.path for t in trees[index:] if not t.main]
            break
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

    if tree.nested:
        return kept(
            "a tree the harness cut for a helper, which is not a work tree under either branch "
            "model and is not this sweep's to remove"
        )
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
    try:
        report = run(
            loaded.code_root,
            list(loaded.get("branch_model.regenerable") or []),
            str(loaded.get("host.landing.delete_branch") or ""),
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
        if not isinstance(timeout, int) or timeout <= BUDGET_SECONDS:
            problems.append(
                f"a `{CARRIER_EVENT}` handler calling {mine} states a timeout of {timeout!r}, "
                f"which is not longer than this module's own budget of {BUDGET_SECONDS}s. The "
                "harness would kill the run before it could say what it did not reach."
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


def _landed_world(tmp: str) -> tuple[str, str, str]:
    """A clone holding one tree whose branch has **landed** by the content arm.

    The shape a squash leaves: the branch carries commits of its own and differs from the
    integration branch in nothing. ⚠️ Built without a host, deliberately -- that is the arm § 10
    makes the primary one, and the one a bare repository can supply.

    Returns `(root, branch, tree)`.
    """
    _origin, work = _world(tmp)
    branch, tree = "feature/1-landed", str(Path(tmp) / "landed-tree")
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
        report = sweep(work, [], "never", occupants=lambda _p: [])
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
        tree = str(Path(tmp) / "in-flight")
        claim.take(work, "feature/2-in-flight", tree)
        report = sweep(work, [], "never", occupants=lambda _p: [])
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
        unreadable = sweep(work, [], "never", read=lambda _b: half, occupants=lambda _p: [])
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
        read = lambda _b: claim.Status(  # noqa: E731
            True, "0" * 40, claim.Holder(), claim.Liveness(False, "fixture", landed=True), False
        )
        report = sweep(work, [], "never", read=read, occupants=lambda _p: [])
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
        gone = sweep(work, ["secret.env"], "never", read=read, occupants=lambda _p: [])
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
        read = lambda _b: claim.Status(  # noqa: E731
            True, "0" * 40, claim.Holder(), claim.Liveness(False, "fixture", landed=True), False
        )
        keeping, _unknown = precious(tree, [])
        suite.ok(
            "an ignored symlink is not precious, however it is ignored",
            keeping == [],
            str(keeping),
        )
        report = sweep(work, [], "never", read=read, occupants=lambda _p: [])
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
        read = lambda _b: claim.Status(  # noqa: E731
            True, "0" * 40, claim.Holder(), claim.Liveness(False, "fixture", landed=True), False
        )
        report = sweep(work, ["*"], "never", read=read, occupants=lambda _p: [])
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

    print("\nthe four trees that are never touched:")

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
        unreadable = sweep(work, [], "never", remove=remover, occupants=lambda _p: None)
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
            report = sweep(work, [], "never", remove=remover, occupants=lambda _p: [])
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
        gone = sweep(work, [], "never", occupants=lambda _p: [])
        suite.ok(
            "⛔ and a later session, standing outside it, removes the tree the pinned one left",
            not Path(tree).exists() and len(gone.removed) == 1,
            gone.report(),
        )

    with tempfile.TemporaryDirectory() as tmp:
        work, _branch, tree = _landed_world(tmp)
        nested = Path(work) / ".helpers" / "one"
        claim.git(work, "worktree", "add", "--quiet", "--detach", str(nested))
        remover = _never_removes()
        report = sweep(work, [], "never", remove=remover, occupants=lambda _p: [])
        suite.ok(
            "a tree the harness cut inside the checkout is named and not removed",
            nested.exists()
            and any(
                os.path.realpath(v.path) == os.path.realpath(nested)
                and "helper" in v.reason
                for v in report.kept
            ),
            report.report(),
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
        claim.take(work, "feature/5-quiet", str(Path(tmp) / "quiet"))
        live = claim.Status(
            True,
            "0" * 40,
            claim.Holder(),
            claim.Liveness(True, "an open pull request references the ref"),
            False,
        )
        ordinary = sweep(work, [], "never", read=lambda _b: live, occupants=lambda _p: [])
        suite.ok(
            "⚠️ while a tree whose branch is live says nothing at all, that being every tree "
            "somebody is working in",
            bool(ordinary.kept) and ordinary.message() == "",
            ordinary.message() or ordinary.report(),
        )
        # ⛔ The other half of the same table, and the one the quiet arm must not swallow: § 10
        # makes an orphaned candidate a person's call, so the sweep that finds one says so.
        orphaned = sweep(work, [], "never", occupants=lambda _p: [])
        suite.ok(
            "⛔ but an orphaned candidate is said, that being the reading § 10 asks about",
            "has not landed" in orphaned.message(),
            orphaned.message() or orphaned.report(),
        )

    print("\nthe published ref is `delete_branch`'s and nobody else's:")

    for stated, expected in (("procedure", False), ("host", True), ("never", True)):
        with tempfile.TemporaryDirectory() as tmp:
            work, branch, tree = _landed_world(tmp)
            report = sweep(work, [], stated, occupants=lambda _p: [])
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
            claim.take(work, f"feature/{index}-more", str(Path(tmp) / f"more-{index}"))
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
        tree = str(Path(tmp) / "kept")
        claim.take(work, "feature/4-kept", tree)
        asked: list[str] = []

        def read(branch: str):
            asked.append(branch)
            return claim.Status(
                True, "0" * 40, claim.Holder(), claim.Liveness(True, "a helper holds it"), False
            )

        first = sweep(work, [], "never", read=read, occupants=lambda _p: [])
        second = sweep(work, [], "never", read=read, occupants=lambda _p: [])
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
        try:
            report = sweep(
                loaded.code_root,
                list(loaded.get("branch_model.regenerable") or []),
                str(loaded.get("host.landing.delete_branch") or ""),
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
