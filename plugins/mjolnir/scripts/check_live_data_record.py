#!/usr/bin/env python3
"""Hold a change to the record of what a live store was already made to be.

The rule is `plugins/mjolnir/config/schema.md § 35 → A record of the store's
state is never rewritten`, which states it and carries the reasoning. Neither is
restated here. ⛔ What this file performs is the one comparison:

  every path a live target's own `record` command prints, against what this
  change **modifies or deletes** -- and a change touching one of them fails
  naming the file. An applied write is no longer an instruction; it is the record
  of what the store was made to be, and editing it leaves every later reader
  believing a state the store never passed through.

⛔ Every value is **read from the configuration**: which targets have a step,
which of them are live, and the command that prints each one's released set.
Nothing of any project is written in this file, and a project whose targets carry
no `live_data_step` has no subject here -- which is reported as *no subject*
rather than as a verdict, because a check that holds nothing reports green.

⛔ **A `record` command that could not be run leaves the change reported
unchecked rather than passed**, which is § 2's rule that absence of signal is not
an answer, met at the one gate whose silence would read as a clean diff.

⚠️ **Read from live targets only.** A target the configuration states is not live
is a store the session is the only user of and can rebuild, so the files applied
to it are still editable -- and a target is live unless the configuration says
otherwise, so the strict direction is what an unclassified one gets.

⚠️ It needs no store, no credential and no connection: what it runs is the
project's own listing command, which § 35 states prints paths. That is the whole
of what this file claims -- **it never reads a store and never asks what is
applied to one.**

What is deliberately not held is stated once, with the rule, in
docs/single-source-of-truth.md#a-released-write-against-the-change-that-would-rewrite-it.

Usage:
    check_live_data_record.py                 hold this change
    check_live_data_record.py --self-test     assert the check reddens on each
                                              planted violation and stays green
                                              on each planted exemption, then stop
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import check_e2e_register as sibling  # noqa: E402 -- the one base derivation
import config as reader  # noqa: E402 -- the one reader of the surface

# ⛔ The diff filter, and the letters it does **not** carry: a path the change
# *adds* is a new write and is exactly what this rule permits. What is forbidden
# is editing or removing something already applied, which is `M` and `D`.
#
# ⚠️ **The cost of the other reading is a false refusal, measured against a real
# project's plausible listing command.** One surveyed carrier detects its pending
# writes as *the paths added since the last release tag* — and an adopter who
# wrote that as its `record` would be printing the branch's own new writes. With
# `A` in this filter, that mis-written command refuses every change the facet
# exists for; without it, the command is simply harmless. ⛔ So the letter is left
# out deliberately and the arm that holds it out is a planted listing command
# naming a path the change adds, not a comparison against this string.
FORBIDDEN_FILTER = "MD"

# ⛔ **Rename detection off, and this is the one flag the rule cannot be read
# without.** A rename is a deletion of the released path spelled as something
# else, and `git diff --name-only` reports one by its **destination alone** — so
# with detection on, moving an applied write leaves the released path in no
# answer and the change reads clean. ⚠️ Reproduced before this flag was added:
# `--name-status` came back `R100 store/0001.sql store/0009.sql` while
# `--name-only` printed the destination and nothing else, and the arm planting a
# rename was green. Off, the same change reports the deletion `D` catches.
NO_RENAMES = "--no-renames"


class Unreadable(RuntimeError):
    """Something this check needs could not be established.

    ⛔ Never a pass. A base it cannot find and a listing command that would not
    run each leave the comparison holding nothing, which is the one state a check
    may not report as green.
    """


def _stepped(configuration: reader.Config) -> list[dict]:
    """Every live target carrying a step, with the command that lists its set.

    ⚠️ The liveness reading is the accessor's rather than a second one here, so a
    change to what *live* means moves in one place (§ 35).
    """
    out = []
    for entry in configuration.get("deploy") or ():
        if not isinstance(entry, dict):
            continue
        read = configuration.live_data_step(entry.get("name"))
        if read["found"] is None or not read["reads_record"]:
            continue
        out.append({"target": entry["name"], "record": read["found"]["record"]})
    return out


def _released(root: str, command: str) -> set[str]:
    """The paths one listing command prints, one per line.

    ⛔ A command that could not be run, or that failed, is a refusal naming it --
    never an empty set, which would read as a store with nothing applied to it.
    """
    try:
        done = subprocess.run(
            command, shell=True, cwd=root, capture_output=True, text=True,
        )
    except OSError as error:
        raise Unreadable(
            f"the listing command `{command}` could not be started: "
            f"{error.__class__.__name__}: {error}"
        ) from error
    if done.returncode != 0:
        raise Unreadable(
            f"the listing command `{command}` exited {done.returncode}, so what "
            "this store already holds is unestablished and the change is "
            f"unchecked rather than clean: {(done.stderr or done.stdout).strip()}"
        )
    return {line.strip() for line in done.stdout.splitlines() if line.strip()}


def _rewritten(root: str, base: str) -> set[str]:
    """Every path this change modifies or deletes, a rename counting as a deletion."""
    diff = subprocess.run(
        ["git", "-C", root, "-c", "core.quotePath=false", "diff", "--name-only",
         NO_RENAMES, f"--diff-filter={FORBIDDEN_FILTER}", base],
        capture_output=True, text=True, check=False,
    )
    if diff.returncode != 0:
        raise Unreadable(
            f"the diff against `{base[:12]}` could not be read: {diff.stderr.strip()}"
        )
    return {line for line in diff.stdout.splitlines() if line}


def held(stepped: list[dict], released: dict[str, set[str]], rewritten: set[str]) -> list[str]:
    """The problems, one line per file, naming the target it is released to.

    ⛔ **The file and not the count**, which § 35 states: a run reporting *three
    released writes were rewritten* has told a reader nothing they can act on,
    and the remedy is a new write rather than a smaller edit of an old one.
    """
    problems = []
    for entry in stepped:
        for path in sorted(released.get(entry["target"], ()) & rewritten):
            problems.append(
                f"{path}: already applied to the live store `{entry['target']}` "
                "serves, and this change rewrites or removes it. ⛔ An applied "
                "write is the record of what the store was made to be (§ 35) — "
                "the correction is a further write, never an edit of this one."
            )
    return problems


def run(root: str, base: str | None = None) -> tuple[int, list[str]]:
    configuration = reader.load(root)
    stepped = _stepped(configuration)
    report = []
    if not stepped:
        report.append(
            "No live target here carries a live data step, so this check holds "
            "nothing. ⛔ Not a clean diff: there is no released set to compare "
            "against (§ 35)."
        )
        return 0, report
    code_root = configuration.code_root()
    released = {
        entry["target"]: _released(code_root, entry["record"]) for entry in stepped
    }
    rewritten = _rewritten(root, base or sibling.merge_base(root, sibling.integration(root)))
    for entry in stepped:
        report.append(
            f"{entry['target']}: {len(released[entry['target']])} path(s) already "
            f"applied, listed by `{entry['record']}`."
        )
    problems = held(stepped, released, rewritten)
    for line in problems:
        report.append(f"  - {line}")
    return (1 if problems else 0), report


# --- the suite -------------------------------------------------------------


class _Stated:
    """A configuration answering only what this check reads."""

    def __init__(self, targets, root):
        self._targets = targets
        self._root = root

    def code_root(self):
        return self._root

    def get(self, path, default=None):
        return self._targets if path == "deploy" else default

    def live_data_step(self, target):
        for entry in self._targets:
            if entry.get("name") != target:
                continue
            block = entry.get("live_data_step")
            return {
                "target": dict(entry),
                "found": dict(block) if isinstance(block, dict) else None,
                "reads_record": entry.get("not_live") is False,
                "names": [target],
                "report": [],
            }
        return {"target": None, "found": None, "reads_record": False,
                "names": [], "report": []}


def _a_target(name="a-target", *, not_live=False, record="./released", stepped=True):
    entry = {"name": name, "not_live": not_live, "invoke": "command",
             "command": "a-command", "advances": "none"}
    if stepped:
        entry["live_data_step"] = {
            "backup": {"run": "./dump", "verify": "./read-back"},
            "apply": "./write", "apply_by": "person",
            "order": "before_invoke", "record": record,
        }
    return entry


def self_test() -> int:
    failures = 0

    def check(label: str, ok: bool, saw: str = "") -> None:
        nonlocal failures
        if ok:
            print(f"  ok    {label}")
        else:
            failures += 1
            print(f"  FAIL  {label}" + (f": {saw}" if saw else ""))

    print("The comparison, which is the whole of this check:")
    stepped = [{"target": "a-target", "record": "./released"}]
    released = {"a-target": {"store/0001.sql", "store/0002.sql"}}
    check(
        "a change rewriting an applied write is a problem naming the file",
        [
            line for line in held(stepped, released, {"store/0001.sql"})
            if "store/0001.sql" in line
        ],
    )
    check(
        "and the problem names the target the store serves",
        "a-target" in " ".join(held(stepped, released, {"store/0001.sql"})),
    )
    check(
        "a change deleting one is the same problem, the filter carrying `D`",
        "D" in FORBIDDEN_FILTER and "M" in FORBIDDEN_FILTER,
    )
    # ⛔ The green side, and the one it matters most on: a **new** write is what
    # this rule exists to leave alone.
    check(
        "a change adding a write that is not applied yet is no problem",
        held(stepped, released, {"store/0003.sql"}) == [],
        f"found {held(stepped, released, {'store/0003.sql'})!r}",
    )
    check(
        "a change touching nothing applied is no problem",
        held(stepped, released, {"README.md"}) == [],
    )

    print("\nWhich targets are read, and which are left alone:")
    tree = tempfile.mkdtemp(prefix="mjolnir-record-")
    check(
        "a live target carrying a step is read",
        [entry["target"] for entry in _stepped(_Stated([_a_target()], tree))]
        == ["a-target"],
    )
    # ⛔ § 35's liveness pairing: a store the session is the only user of can be
    # rebuilt, so its applied writes are still editable.
    check(
        "a target the session is the only user of is not read",
        _stepped(_Stated([_a_target(not_live=True)], tree)) == [],
    )
    check(
        "a target carrying no step is not read",
        _stepped(_Stated([_a_target(stepped=False)], tree)) == [],
    )
    check(
        "and a project with two targets, one of each, reads one",
        [
            entry["target"] for entry in _stepped(_Stated(
                [_a_target(name="free", not_live=True),
                 _a_target(name="served")], tree))
        ] == ["served"],
    )

    print("\nWhat a listing command that will not answer does:")
    scripts = tempfile.mkdtemp(prefix="mjolnir-record-cmd-")
    for name, body in (
        ("released", "#!/bin/sh\nprintf 'store/0001.sql\\nstore/0002.sql\\n'\n"),
        ("broken", "#!/bin/sh\necho 'no such store' >&2\nexit 2\n"),
    ):
        full = os.path.join(scripts, name)
        with open(full, "w", encoding="utf-8") as handle:
            handle.write(body)
        os.chmod(full, 0o755)
    check(
        "a listing command that answers gives its paths",
        _released(scripts, "./released") == {"store/0001.sql", "store/0002.sql"},
        f"listed {_released(scripts, './released')!r}",
    )
    # ⛔ The direction that matters: an empty set would read as a store with
    # nothing applied to it, which is a clean diff for every change there is.
    for label, command in (
        ("one that exits non-zero", "./broken"),
        ("one that is not there at all", "./a-command-nothing-states"),
    ):
        answered = None
        try:
            answered = _released(scripts, command)
        except Unreadable as error:
            answered = error
        check(
            f"{label} is a refusal rather than an empty set",
            isinstance(answered, Unreadable)
            and "unestablished" in str(answered),
            f"answered {answered!r}",
        )

    print("\nThe plumbing, against a repository this suite builds:")
    # ⛔ The arms above are in memory and prove nothing about the diff, which is
    # where a convincing false green lives — the sibling check this module takes
    # its base derivation from says so about its own. ⚠️ So one change is made for
    # real, in a repository with a base commit, and read back through `run`.
    repo = tempfile.mkdtemp(prefix="mjolnir-record-repo-")
    for args in (
        ("init", "-q", "-b", "main"),
        # ⚠️ No `@` in the identity, and not for tidiness: the names sweep reads
        # anything shaped like an address as a project's own fact, and refused this
        # file for carrying one. Git takes the string as written.
        ("config", "user.email", "the-suite"),
        ("config", "user.name", "the suite"),
    ):
        subprocess.run(["git", "-C", repo, *args], check=True, capture_output=True)
    os.makedirs(os.path.join(repo, "store"), exist_ok=True)
    for name, text in (
        ("store/0001.sql", "the first write\n"),
        ("store/0002.sql", "the second write\n"),
        ("README.md", "a file nothing applied\n"),
    ):
        with open(os.path.join(repo, name), "w", encoding="utf-8") as handle:
            handle.write(text)
    lister = os.path.join(repo, "released")
    with open(lister, "w", encoding="utf-8") as handle:
        handle.write("#!/bin/sh\nprintf 'store/0001.sql\\nstore/0002.sql\\n'\n")
    os.chmod(lister, 0o755)
    subprocess.run(["git", "-C", repo, "add", "-A"], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", repo, "commit", "-qm", "the base"], check=True, capture_output=True
    )
    base = subprocess.run(
        ["git", "-C", repo, "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()

    def _run_against(targets):
        saved = reader.load
        reader.load = lambda _root: _Stated(targets, repo)
        try:
            return run(repo, base)
        finally:
            reader.load = saved

    # ⚠️ A path the change *adds*, read first: it has to stay green, and an arm
    # that only ever planted a rewrite would not have said so.
    with open(os.path.join(repo, "store/0003.sql"), "w", encoding="utf-8") as handle:
        handle.write("a write nobody applied yet\n")
    subprocess.run(["git", "-C", repo, "add", "-A"], check=True, capture_output=True)
    status, report = _run_against([_a_target()])
    check(
        "a change adding a new write is green through the real diff",
        status == 0 and not [line for line in report if line.startswith("  - ")],
        f"answered {status} {report!r}",
    )
    # ⛔ The false-refusal bound on the diff filter, planted so that it bites: the
    # listing command names the path this change **adds**, which is what an
    # adopter who wrote their *pending* detection into `record` would produce.
    # ⚠️ Written first as a comparison against `FORBIDDEN_FILTER` itself, which
    # asserted the constant rather than the behaviour -- and the intersection was
    # empty either way, so planting the letter in left the arm green.
    naming_the_new = os.path.join(repo, "lists-the-new-one")
    with open(naming_the_new, "w", encoding="utf-8") as handle:
        handle.write("#!/bin/sh\nprintf 'store/0001.sql\\nstore/0003.sql\\n'\n")
    os.chmod(naming_the_new, 0o755)
    status, report = _run_against([_a_target(record="./lists-the-new-one")])
    check(
        "a listing command naming the path this change adds does not refuse it",
        status == 0 and not [line for line in report if line.startswith("  - ")],
        f"answered {status} {report!r}",
    )
    with open(os.path.join(repo, "store/0001.sql"), "w", encoding="utf-8") as handle:
        handle.write("the first write, edited\n")
    status, report = _run_against([_a_target()])
    check(
        "a change rewriting an applied write is red through the real diff",
        status == 1 and any("store/0001.sql" in line for line in report),
        f"answered {status} {report!r}",
    )
    # ⛔ And the same change against a target the session is the only user of,
    # which is the liveness pairing read through the plumbing rather than through
    # `_stepped` alone.
    status, report = _run_against([_a_target(not_live=True)])
    check(
        "while the same change against a target nobody else uses is green",
        status == 0 and "holds nothing" in " ".join(report),
        f"answered {status} {report!r}",
    )
    os.remove(os.path.join(repo, "store/0002.sql"))
    status, report = _run_against([_a_target()])
    check(
        "a change deleting an applied write is red too",
        status == 1 and any("store/0002.sql" in line for line in report),
        f"answered {status} {report!r}",
    )
    # ⛔ The evasion a deletion-and-addition is spelled as, and the one this check
    # was first written blind to: `git diff --name-only` reports a rename by its
    # **destination** alone, so the released path is in no answer and the change
    # reads clean. ⚠️ Reproduced before the fix: `R100 store/0001.sql
    # store/0009.sql` came back from `--name-status` while `--name-only` printed
    # `store/0009.sql` and nothing else.
    subprocess.run(["git", "-C", repo, "checkout", "-q", "--", "."], check=True,
                   capture_output=True)
    subprocess.run(["git", "-C", repo, "mv", "store/0001.sql", "store/0100.sql"],
                   check=True, capture_output=True)
    status, report = _run_against([_a_target()])
    check(
        "a change renaming an applied write is red, naming the path it was applied under",
        status == 1 and any("store/0001.sql" in line for line in report),
        f"answered {status} {report!r}",
    )

    print("\nAnd a project with no subject here:")
    status, report = run(reader.REPO_ROOT)
    check(
        "this project states no deploy target, so the check holds nothing and is green",
        status == 0 and any("holds nothing" in line for line in report),
        f"answered {status} {report!r}",
    )
    check(
        "and says so rather than reporting a clean diff",
        any("Not a clean diff" in line for line in report),
        f"answered {report!r}",
    )

    print("\n" + ("All green." if not failures else f"{failures} failure(s)."))
    return 1 if failures else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(add_help=True, description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--base", default=None, help="the ref this change is against")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    try:
        status, report = run(os.getcwd(), args.base)
    except (Unreadable, sibling.Unreadable) as error:
        print(f"unchecked: {error}")
        return 2
    except reader.ConfigError as error:
        print(f"the configuration could not be read: {error}")
        return 2
    for line in report:
        print(line)
    print(
        "A released write is the record of what the store was made to be."
        if not status
        else f"{sum(1 for line in report if line.startswith('  - '))} problem(s)."
    )
    return status


if __name__ == "__main__":
    sys.exit(main())
