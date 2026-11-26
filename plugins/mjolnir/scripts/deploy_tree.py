#!/usr/bin/env python3
"""What a deploy's tree is held to, read without writing anything.

`tree` (§ 33 → What the tree must be, for the deploy and for the advance) is a
list on a deploy target, and this module is what reads it against a tree. ⛔ **The
conditions, their meaning and what each one holds are the surface's**, read
through the one reader of it; what is here is the readings, taken in the directory
the target's command runs in.

What it owns is the part a role should not perform by eye:

  * **A reading that writes nothing**, git's own bookkeeping included: no fetch,
    no pull, and no index refresh as a side effect of asking for a status.
  * **A condition that could not be read is not met.** A tree nothing could read
    reads exactly like a tree that met everything otherwise (§ 11).
  * **What each failure holds**, so the deploying role reads one answer for the
    preflight and one for the advance rather than re-deriving either.

Usage:
    deploy_tree.py --target NAME [--at-commit REV] [--skills-root DIR]
    deploy_tree.py --self-test

Exit status: 0 every condition met, 1 the deploy is held, 2 the configuration
could not answer, 3 this target states no tree condition, 4 the deploy may run and
the advance is held. ⚠️ The last two are their own values for `live_data.py`'s
reason: *no condition* collapsed into 0 reads as conditions met, and a held
advance collapsed into 1 reads as a deploy that may not run.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import config  # noqa: E402 -- the one reader of the surface

NO_CONDITION = 3
ADVANCE_HELD = 4

# Which of § 33's `holds` values stop which act. ⛔ The vocabulary itself is the
# surface's and the reader holds an entry to it; what is here is the meaning of
# each member for the two answers this module gives.
STOPS_DEPLOY = {"deploy", "both"}
STOPS_ADVANCE = {"advance", "both"}


def _git(directory: str, *args: str) -> tuple[int, str]:
    """One read-only git call in `directory`, its status and its output.

    ⛔ `GIT_OPTIONAL_LOCKS=0` is what keeps a status from refreshing the index,
    which is a write the preflight may not make (§ 33).
    """
    env = {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}
    try:
        done = subprocess.run(
            ["git", "-C", directory, *args],
            capture_output=True, text=True, env=env, check=False,
        )
    except OSError as error:
        return 127, str(error)
    return done.returncode, (done.stdout if done.returncode == 0 else done.stderr).strip()


def _head(directory: str) -> tuple[str | None, str]:
    code, out = _git(directory, "rev-parse", "--verify", "--quiet", "HEAD")
    if code != 0:
        return None, "the tree's commit could not be read"
    return out, ""


def _clean(directory: str, _stated: dict, _at_commit) -> tuple[bool | None, str]:
    code, out = _git(directory, "status", "--porcelain", "--untracked-files=all")
    if code != 0:
        return None, f"the tree's status could not be read: {out}"
    changed = [line[3:] for line in out.splitlines() if line.strip()]
    if not changed:
        return True, "no change"
    shown = ", ".join(changed[:5]) + (f", and {len(changed) - 5} more" if len(changed) > 5 else "")
    return False, f"{len(changed)} change(s): {shown}"


def _on_branch(directory: str, stated: dict, _at_commit) -> tuple[bool | None, str]:
    code, out = _git(directory, "symbolic-ref", "--quiet", "--short", "HEAD")
    if code != 0:
        head, why = _head(directory)
        return (False, f"a detached commit, {head}") if head else (None, why)
    if out == stated["branch"]:
        return True, f"on {out}"
    return False, f"on {out}, where {stated['branch']} is required"


def _at_remote_tip(directory: str, _stated: dict, _at_commit) -> tuple[bool | None, str]:
    head, why = _head(directory)
    if head is None:
        return None, why
    code, upstream = _git(
        directory, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"
    )
    if code != 0:
        return False, "the branch has no upstream, so there is no remote tip to be at"
    code, tip = _git(directory, "rev-parse", "--verify", "--quiet", "@{upstream}")
    if code != 0:
        return None, f"the upstream {upstream} could not be read"
    if head == tip:
        return True, f"at {upstream} as last fetched, {tip}"
    return False, f"at {head}, where {upstream} as last fetched is {tip}"


def _primary_checkout(directory: str, _stated: dict, _at_commit) -> tuple[bool | None, str]:
    code, own = _git(directory, "rev-parse", "--git-dir")
    code_common, common = _git(directory, "rev-parse", "--git-common-dir")
    if code != 0 or code_common != 0:
        return None, "where the tree's repository is could not be read"
    own = os.path.realpath(os.path.join(directory, own))
    common = os.path.realpath(os.path.join(directory, common))
    if own == common:
        return True, "the primary checkout"
    return False, f"a linked tree of the checkout whose repository is {common}"


def _at_commit(directory: str, _stated: dict, at_commit) -> tuple[bool | None, str]:
    if not at_commit:
        return False, "the invocation named no commit for the tree to be at"
    head, why = _head(directory)
    if head is None:
        return None, why
    code, wanted = _git(directory, "rev-parse", "--verify", "--quiet", f"{at_commit}^{{commit}}")
    if code != 0:
        return None, f"the invocation names {at_commit!r}, which this repository does not resolve"
    if head == wanted:
        return True, f"at {wanted}"
    return False, f"at {head}, where {wanted} is required"


# One reading per member of § 33's `condition` alternation. ⛔ The self-test holds
# this table to the surface in both directions, so a member added there without a
# reading here reddens rather than reading as met.
READINGS = {
    "clean": _clean,
    "on_branch": _on_branch,
    "at_remote_tip": _at_remote_tip,
    "primary_checkout": _primary_checkout,
    "at_commit": _at_commit,
}


def read(configuration, target: str, at_commit: str | None = None) -> dict:
    """Every condition `target` states, read against the tree its command runs in."""
    resolved = configuration.deploy_target(target)
    conditions = resolved.get("tree") or []
    answer = {
        "target": target,
        "directory": resolved.get("runs_at"),
        "conditions": [],
        "deploy_held": False,
        "advance_held": False,
        "report": [],
    }
    if not conditions:
        answer["report"].append(
            "This target states no tree condition (§ 33), so nothing is held on the "
            "tree; what is uncommitted is reported by the preflight and holds nothing."
        )
        return answer
    directory = resolved.get("runs_at")
    reachable = (
        resolved.get("reached_by") == "command"
        and resolved.get("reachable") is True
        and isinstance(directory, str)
    )
    for stated in conditions:
        if reachable:
            met, held = READINGS[stated["condition"]](directory, stated, at_commit)
        else:
            met, held = None, f"the directory the command runs in, {directory!r}, could not be read"
        stops = []
        if met is not True:
            if stated["holds"] in STOPS_DEPLOY:
                stops.append("deploy")
                answer["deploy_held"] = True
            if stated["holds"] in STOPS_ADVANCE:
                stops.append("advance")
                answer["advance_held"] = True
        answer["conditions"].append({
            "condition": stated["condition"],
            **({"branch": stated["branch"]} if "branch" in stated else {}),
            "holds": stated["holds"],
            # ⛔ Three-valued, and `None` is never read as met: § 11.
            "met": met,
            "held": held,
            "stops": stops,
        })
    if any(one["condition"] == "at_remote_tip" for one in answer["conditions"]):
        answer["report"].append(
            "The remote tip is read as last fetched: nothing here fetches, and bringing "
            "the tree up to date is the project's own command (§ 33)."
        )
    if any(one["met"] is None for one in answer["conditions"]):
        answer["report"].append(
            "A condition that could not be read is reported as not met (§ 11)."
        )
    return answer


def _status(answer: dict) -> int:
    if not answer["conditions"]:
        return NO_CONDITION
    if answer["deploy_held"]:
        return 1
    if answer["advance_held"]:
        return ADVANCE_HELD
    return 0


# --- the suite -------------------------------------------------------------


class _Stated:
    """A configuration answering only what this module reads.

    ⛔ At the accessor seam, for `live_data.py`'s reason: every arm below is about
    what this module reads in a tree, and what holds the list's own shape is the
    reader's suite, where the refusals are.
    """

    def __init__(self, tree, directory, *, reached_by="command", reachable=True):
        self._tree = tree
        self._directory = directory
        self._reached_by = reached_by
        self._reachable = reachable

    def deploy_target(self, target):
        return {
            "target": target,
            "reached_by": self._reached_by,
            "runs_at": self._directory,
            "reachable": self._reachable,
            "tree": [dict(one) for one in self._tree],
        }


def _sh(directory: str, *args: str) -> str:
    done = subprocess.run(
        ["git", "-c", "user.name=suite", "-c", "user.email=suite@example.invalid",
         "-c", "init.defaultBranch=main", "-C", directory, *args],
        capture_output=True, text=True, check=True,
    )
    return done.stdout.strip()


def _a_repository() -> tuple[str, str]:
    """A primary checkout on `main` with one commit, tracking a bare remote at it."""
    scratch = tempfile.mkdtemp(prefix="mjolnir-deploy-tree-")
    remote = os.path.join(scratch, "remote.git")
    tree = os.path.join(scratch, "tree")
    os.makedirs(remote)
    os.makedirs(tree)
    _sh(remote, "init", "--bare", "--quiet")
    _sh(tree, "init", "--quiet")
    with open(os.path.join(tree, "a-file"), "w", encoding="utf-8") as handle:
        handle.write("one\n")
    _sh(tree, "add", "a-file")
    _sh(tree, "commit", "--quiet", "-m", "one")
    _sh(tree, "remote", "add", "origin", remote)
    _sh(tree, "push", "--quiet", "-u", "origin", "main")
    return scratch, tree


def _one(condition: str, holds: str = "deploy", **more) -> dict:
    return {"condition": condition, "holds": holds, **more}


def self_test() -> int:
    failures = 0

    def check(label: str, held: bool, saw: str = "") -> None:
        nonlocal failures
        if held:
            print(f"  ok    {label}")
        else:
            failures += 1
            print(f"  FAIL  {label}: {saw}")

    def first(answer: dict) -> dict:
        return answer["conditions"][0] if answer["conditions"] else {}

    print("The readings, one per condition the surface states:")
    with open(config.SURFACE, encoding="utf-8") as handle:
        facts = config.surface_facts(handle.read())
    stated = facts["enums"].get("deploy.tree.condition") or []
    check(
        "every condition § 33 states has a reading here, and nothing else does",
        sorted(stated) == sorted(READINGS),
        f"the surface states {stated!r}, this module reads {sorted(READINGS)!r}",
    )

    scratch, tree = _a_repository()
    try:
        head = _sh(tree, "rev-parse", "HEAD")
        for label, condition, met in (
            ("a clean tree meets `clean`", _one("clean"), True),
            ("a tree on the named branch meets `on_branch`",
             _one("on_branch", branch="main"), True),
            ("a tree at its upstream meets `at_remote_tip`", _one("at_remote_tip"), True),
            ("the primary checkout meets `primary_checkout`", _one("primary_checkout"), True),
            ("a tree at the commit named meets `at_commit`", _one("at_commit"), True),
            ("a tree on another branch does not meet `on_branch`",
             _one("on_branch", branch="release"), False),
        ):
            got = read(_Stated([condition], tree), "a-target", at_commit=head)
            check(label, first(got).get("met") is met, f"answered {got!r}")

        got = read(_Stated([_one("on_branch", branch="release")], tree), "a-target")
        check(
            "a condition not met names what the tree held",
            "on main" in first(got).get("held", "") and "release" in first(got)["held"],
            f"answered {got!r}",
        )
        got = read(_Stated([_one("at_commit")], tree), "a-target")
        check(
            "an invocation naming no commit does not meet `at_commit`",
            first(got).get("met") is False and "no commit" in first(got)["held"],
            f"answered {got!r}",
        )
        got = read(_Stated([_one("at_commit")], tree), "a-target", at_commit="no-such-rev")
        check(
            "a commit the repository does not resolve is unread, never met",
            first(got).get("met") is None and got["deploy_held"], f"answered {got!r}",
        )

        # ⛔ The write the reading may not make, asserted on the index itself: a
        # status that saw a tracked file's stat change would rewrite it.
        index = os.path.join(tree, ".git", "index")
        with open(index, "rb") as handle:
            before = handle.read()
        stamp = os.stat(index).st_mtime_ns
        os.utime(os.path.join(tree, "a-file"), ns=(stamp + 10**9, stamp + 10**9))
        read(_Stated([_one("clean")], tree), "a-target")
        with open(index, "rb") as handle:
            after = handle.read()
        check(
            "reading the status leaves the index as it was",
            before == after and os.stat(index).st_mtime_ns == stamp,
            "the index was rewritten",
        )

        with open(os.path.join(tree, "untracked"), "w", encoding="utf-8") as handle:
            handle.write("new\n")
        got = read(_Stated([_one("clean")], tree), "a-target")
        check(
            "an untracked file means the tree is not clean, and it is named",
            first(got).get("met") is False and "untracked" in first(got)["held"],
            f"answered {got!r}",
        )
        os.remove(os.path.join(tree, "untracked"))

        with open(os.path.join(tree, "a-file"), "a", encoding="utf-8") as handle:
            handle.write("two\n")
        _sh(tree, "commit", "--quiet", "-am", "two")
        got = read(_Stated([_one("at_remote_tip")], tree), "a-target")
        check(
            "a commit ahead of the upstream does not meet `at_remote_tip`, both named",
            first(got).get("met") is False and "origin/main" in first(got)["held"],
            f"answered {got!r}",
        )
        check(
            "and the report says the tip was read as last fetched",
            any("last fetched" in line for line in got["report"]), f"answered {got!r}",
        )
        got = read(_Stated([_one("at_commit")], tree), "a-target", at_commit=head)
        check(
            "a tree moved past the commit named does not meet `at_commit`",
            first(got).get("met") is False, f"answered {got!r}",
        )

        _sh(tree, "checkout", "--quiet", "-b", "local-only")
        got = read(_Stated([_one("at_remote_tip")], tree), "a-target")
        check(
            "a branch with no upstream does not meet `at_remote_tip`",
            first(got).get("met") is False and "no upstream" in first(got)["held"],
            f"answered {got!r}",
        )
        _sh(tree, "checkout", "--quiet", "--detach")
        got = read(_Stated([_one("on_branch", branch="main")], tree), "a-target")
        check(
            "a detached commit does not meet `on_branch`, and says it is detached",
            first(got).get("met") is False and "detached" in first(got)["held"],
            f"answered {got!r}",
        )
        _sh(tree, "checkout", "--quiet", "main")

        linked = os.path.join(scratch, "linked")
        _sh(tree, "worktree", "add", "--quiet", linked, "-b", "linked")
        got = read(_Stated([_one("primary_checkout")], linked), "a-target")
        check(
            "a linked tree does not meet `primary_checkout`",
            first(got).get("met") is False and "linked tree" in first(got)["held"],
            f"answered {got!r}",
        )

        print("\nWhat a condition not met holds:")
        dirty = os.path.join(tree, "dirty")
        with open(dirty, "w", encoding="utf-8") as handle:
            handle.write("x\n")
        for holds, deploy, advance, status in (
            ("deploy", True, False, 1),
            ("advance", False, True, ADVANCE_HELD),
            ("both", True, True, 1),
        ):
            got = read(_Stated([_one("clean", holds)], tree), "a-target")
            check(
                f"`holds: {holds}` holds the deploy {deploy} and the advance {advance}",
                got["deploy_held"] is deploy and got["advance_held"] is advance
                and _status(got) == status,
                f"answered {got!r}",
            )
        os.remove(dirty)
        got = read(_Stated([_one("clean", "both")], tree), "a-target")
        check(
            "every condition met holds nothing",
            not got["deploy_held"] and not got["advance_held"] and _status(got) == 0,
            f"answered {got!r}",
        )
    finally:
        shutil.rmtree(scratch, ignore_errors=True)

    print("\nWhat could not be read, and what states nothing:")
    got = read(_Stated([_one("clean", "advance")], "/nonexistent", reachable=False), "a-target")
    check(
        "a directory that could not be read leaves every condition unread and held",
        first(got).get("met") is None and got["advance_held"] and not got["deploy_held"],
        f"answered {got!r}",
    )
    outside = tempfile.mkdtemp(prefix="mjolnir-deploy-tree-")
    try:
        got = read(_Stated([_one("clean")], outside), "a-target")
        check(
            "a directory that is no repository is unread, never clean",
            first(got).get("met") is None and got["deploy_held"], f"answered {got!r}",
        )
    finally:
        shutil.rmtree(outside, ignore_errors=True)
    got = read(_Stated([], "/nonexistent"), "a-target")
    check(
        "a target stating no condition answers its own status, not a pass",
        got["conditions"] == [] and _status(got) == NO_CONDITION and got["report"],
        f"answered {got!r}",
    )

    print("\nAnd this project's own configuration:")
    try:
        resolved = config.load(config.REPO_ROOT)
        targets = resolved.get("deploy") or []
        check(
            "this project states no deploy target, so it states no tree condition",
            not targets, f"states {len(targets)} target(s)",
        )
    except config.ConfigError as error:
        failures += 1
        print(f"  FAIL  this repository's own configuration: {error}")

    print("\n" + ("All green." if not failures else f"{failures} failure(s)."))
    return 1 if failures else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(add_help=True, description=__doc__)
    parser.add_argument("--target", help="the § 33 target whose tree is read")
    parser.add_argument(
        "--at-commit",
        metavar="REV",
        help="the commit the invocation names, which `at_commit` holds the tree to. "
        "Omitted, that condition is not met",
    )
    parser.add_argument("--skills-root", default=None)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()
    if not args.target:
        parser.error("--target is required: a tree condition belongs to one § 33 target")
    try:
        resolved = config.load(args.skills_root or os.getcwd())
        answer = read(resolved, args.target, args.at_commit)
    except config.ConfigError as error:
        print(json.dumps({"error": str(error)}, indent=2, ensure_ascii=False))
        return 2
    print(json.dumps(answer, indent=2, ensure_ascii=False))
    return _status(answer)


if __name__ == "__main__":
    sys.exit(main())
