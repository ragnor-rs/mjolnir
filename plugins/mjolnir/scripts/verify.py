#!/usr/bin/env python3
"""What a deployed item is judged against, and the record a person is handed.

`verify` (§ 39) is one fact with one reader, and ⛔ **the reader is this module
rather than the role**: the role that accepts a deployed item would otherwise
carry a per-target command, a baseline ref and a list of widths, which is a role
per project. So the skill carries none of those and asks here instead.

⛔ **What this module states nothing about is `../config/schema.md § 39`'s own
rules, cited and not copied here.** What it owns is the part none of its readers
should perform twice:

  * **Resolving a target**, by the name § 33 keys the deploy list on, to the
    command that prints the commit it serves and the repository that command
    runs in. A name no target carries is refused at the load, so what is left
    here is a target the project states and no entry for.
  * **Reading the commit**, by running that command where the entry says. ⛔ Off
    a file inside the running target, never off an artefact digest and never off
    the integration branch -- which is the rule § 39 states and this module
    performs by having no other source.
  * **The record's shape**: every criterion carrying a reading, the environment,
    the instrument and a date, or reported **unanswerable with whose it is to
    supply**. A criterion missing any of those is refused rather than rendered,
    because a record with a hole in it is what a release is then held up or let
    through on.
  * **The one arithmetic this facet has**: ⛔ a reading taken before the commit
    the target serves cannot accept the item that commit changed. Refused,
    naming both stamps.
  * **The verdict it may not give.** The readings are what is true now; the
    verdict is the status move, which § 4.2 gives to `orderer`. ⛔ This module
    asks for no status at all, and the suite below asserts that the role is
    refused that write however it asks.

⛔ **And it files nothing, fixes nothing and writes no status.** Residue is
carried through to the report in one line; the step back a failing criterion owes
is § 32's, asked for through the port's own `--revert-on` and never invented
here.

Usage:
    verify.py [--skills-root DIR]          what this project states, per target
    verify.py plan --target NAME           what a pass against that target reads
    verify.py commit --target NAME         the commit that target serves, read
                                           by running the project's own command
    verify.py record --target NAME         the record, held to its own shape and
      --item N --readings FILE             to the commit the target serves
    verify.py --self-test                  assert every answer against planted
                                           trees, then report this project's own

Exit status, and ⛔ **four values rather than two**: 0 the answer was produced,
1 the answer cannot be given and names why -- a record that does not hold is one
of those, 2 the configuration could not be read, 3 this project judges nothing on
a deploy target. ⚠️ The last is § 11's rule at a command line: *no answer*
collapsed into 0 reads as an item that was accepted, and into 1 as a project
whose readings are all wrong.

⚠️ **A project stating no configuration at all reaches 3 as well**, and that is a
deliberate collapse rather than an oversight: what a consumer asks is whether
there is a judgement to take, and there is not either way. What separates them is
the report, which names which of the two it met.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import config  # noqa: E402 -- the one reader of the surface

# ⛔ The exit status this module reserves for the project's stated absence, named
# for the reason `release.py` names its own: a reader comparing against a literal
# would be comparing against a number, and the number is the least readable part
# of the contract it carries.
NO_JUDGEMENT = 3

# § 32's trigger a failing criterion steps the item back on. ⛔ **Named here and
# performed nowhere in this module**: the ask goes through the port, which reads
# the project's own `reversals` and refuses where it rules no edge. What this
# constant is for is that the role never spells the trigger itself -- a role that
# composed the word would be inventing the edge § 32 says is configured.
REJECTED = "acceptance_rejected"

# § 4.2's role an acceptance is about, and the writer it belongs to. ⛔ Read for
# the **refusal** and never for a write: this module asks for no status, and what
# these two are for is the suite below asserting that the guard holds against
# every writer a role could ask as.
ACCEPTED_ROLE = "accepted"
ORDERER = "orderer"

# The buckets § 39 states a criterion falls in, and what each one owes the record.
# ⛔ A closed set, and a bucket outside it is refused: a criterion classified as
# something no reader knows is a criterion nothing holds, which is the state the
# whole record exists to prevent.
#
# ⚠️ The readings are owed by three of the four. The fourth owes an **owner**
# instead and owes no reading at all -- a criterion with no referent has nothing
# to measure, and demanding one would be asking a pass to invent the thing it is
# reporting the absence of.
MEASURED = ("reading", "environment", "instrument", "at")
BUCKETS = {
    "on_target": MEASURED,
    "elsewhere": MEASURED + ("why_not_the_target",),
    "later_target": MEASURED,
    "no_referent": ("owner",),
}

# ⛔ The one bucket that holds the item whatever the measurable half says, and the
# one that does not. § 39 rules the third bucket **does not** split the item: a
# criterion that cannot be met until a later target runs stays on the item and
# the item is still accepted, because § 33's precondition refuses to carry an
# unaccepted item and the two together would deadlock.
HOLDS_THE_ITEM = ("no_referent",)


class CannotAnswer(Exception):
    """The answer cannot be given, and the message says what is missing."""


# --- the facet, resolved ----------------------------------------------------


def stated(resolved) -> dict | None:
    """§ 39's facet as this project states it, or `None` where it states none."""
    return resolved.verify()


def _target(resolved, name: str) -> dict:
    """One § 33 target by name, with § 39's command for it.

    ⛔ **The target list is § 33's and this module carries no vocabulary of its
    own.** A name no entry carries is a stop listing the names the project
    states -- the same resolution § 31's `refused_on` makes against the same
    list, so a reader meets one answer about target names and not two.

    ⚠️ **A target the project deploys to and states no command for is its own
    answer**: no pass may be taken against it, which § 39 makes a reading of the
    configuration rather than a fault. Reported with the targets that do carry
    one, so the reply can say which.
    """
    entries = [
        entry
        for entry in (resolved.get("deploy") or [])
        if isinstance(entry, dict) and entry.get("name") == name
    ]
    if not entries:
        named = [
            entry.get("name")
            for entry in (resolved.get("deploy") or [])
            if isinstance(entry, dict)
        ]
        raise CannotAnswer(
            f"`{name}` is no target this project deploys to (§ 33). The targets "
            f"it states are: {', '.join(repr(one) for one in named) or 'none'}."
        )
    facet = stated(resolved) or {}
    command = (facet.get("identity") or {}).get(name)
    if not command:
        judged = sorted(facet.get("identity") or {})
        raise CannotAnswer(
            f"this project states no `verify.identity` command for the `{name}` "
            "target, so no acceptance pass may be taken against it (§ 39). The "
            f"targets it judges on are: {', '.join(repr(one) for one in judged) or 'none'}."
        )
    entry = dict(entries[0])
    entry["identity_command"] = command
    return entry


def plan(resolved, name: str) -> dict:
    """What a pass against one target reads, with nothing run.

    ⛔ **Nothing is invoked here**, which is what makes this answerable before a
    person is asked for anything: the command that would read the commit, the
    repository it runs in, the baseline both sides of the comparison are built
    from and the widths a handover may name.
    """
    facet = stated(resolved)
    if facet is None:
        raise CannotAnswer(
            "this project judges nothing on a deploy target "
            "(`verify.carrier: none`), so there is no plan to take (§ 39)."
        )
    entry = _target(resolved, name)
    root = resolved.code_root(entry.get("code_root"))
    return {
        "target": name,
        "not_live": entry.get("not_live"),
        "code_root": entry.get("code_root"),
        "root": root,
        "identity_command": entry["identity_command"],
        "baseline": dict(facet["baseline"]),
        "breakpoints": list(facet["breakpoints"]),
        # ⛔ Named rather than composed by whoever reads this: the step back a
        # failing criterion owes is § 32's trigger, asked for through the port.
        "rejection_trigger": REJECTED,
        "rules_rejection": any(
            isinstance(rule, dict) and rule.get("trigger") == REJECTED
            for rule in (resolved.get("reversals") or [])
        ),
    }


# --- the commit a target serves ---------------------------------------------


def _ran(command: str, root: str) -> subprocess.CompletedProcess:
    """Run a project's own command in a root, whole and unprefixed.

    ⚠️ Through the shell because the command is stated whole: § 33's rule for an
    invocation is this one's too -- nothing is prefixed to it and nothing is read
    out of it but what it printed.
    """
    return subprocess.run(
        command, shell=True, cwd=root, capture_output=True, text=True, timeout=120
    )


def served_commit(resolved, name: str) -> dict:
    """The commit a target serves, read by running the project's own command.

    ⛔ **This is the only source**, which is how § 39's two wrong readings are
    refused without a key: there is nowhere here for an artefact digest or a
    branch head to come from.

    ⚠️ **A command that printed nothing is unestablished and never *the same
    commit***. What it exited with is carried through, because a command that
    failed and a target serving nothing are different answers and only one of
    them is about the item.
    """
    answer = plan(resolved, name)
    try:
        ran = _ran(answer["identity_command"], answer["root"])
    except (OSError, subprocess.SubprocessError) as broken:
        raise CannotAnswer(
            f"the command reading the commit the `{name}` target serves could not "
            f"be run in {answer['root']!r}: {broken}."
        ) from None
    printed = ran.stdout.strip()
    out = {
        "target": name,
        "root": answer["root"],
        "command": answer["identity_command"],
        "exit_status": ran.returncode,
        "commit": printed or None,
        "stderr": ran.stderr.strip() or None,
    }
    if ran.returncode != 0 or not printed:
        out["unestablished"] = (
            "the command did not print a commit, so what this target serves is "
            "**unestablished** rather than unchanged (§ 11). A reading taken "
            "against it would be a reading about nothing."
        )
    return out


def _committed_at(root: str, commit: str) -> str:
    """The stamp of one commit, read out of the repository the target's act is in.

    ⛔ **Read rather than handed in.** The arithmetic below is the whole of what
    makes a reading defensible against the thing it measured, and a stamp a
    caller supplied is a stamp the caller could have chosen.
    """
    try:
        ran = subprocess.run(
            ["git", "-C", root, "show", "-s", "--format=%cI", commit],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError) as broken:
        raise CannotAnswer(
            f"the stamp of {commit!r} could not be read in {root!r}: {broken}."
        ) from None
    if ran.returncode != 0 or not ran.stdout.strip():
        raise CannotAnswer(
            f"{root!r} does not answer for the commit {commit!r}, so when the "
            "code under judgement arrived is **unestablished** (§ 11) and no "
            "reading can be held against it: "
            f"{ran.stderr.strip() or 'nothing was printed'}."
        )
    return ran.stdout.strip()


def _stamp(value: object, where: str) -> datetime.datetime:
    """One stamp, parsed, or a refusal naming where it was written.

    ⚠️ A date with no zone is refused rather than assumed local: two readings
    written in two places and compared as naive stamps is an ordering nobody
    stated, and the comparison below is what a verdict rests on.
    """
    if not isinstance(value, str) or not value.strip():
        raise CannotAnswer(f"{where} carries no date, and a reading owes one (§ 39).")
    try:
        parsed = datetime.datetime.fromisoformat(value.strip())
    except ValueError:
        raise CannotAnswer(
            f"{where} is {value!r}, which is no date this module can read. Write "
            "it as an ISO 8601 stamp carrying its offset."
        ) from None
    if parsed.tzinfo is None:
        raise CannotAnswer(
            f"{where} is {value!r}, which carries no offset. Two readings "
            "compared as naive stamps are ordered by nothing, and the comparison "
            "against the commit the target serves is what a verdict rests on."
        )
    return parsed


# --- the record -------------------------------------------------------------


def record(resolved, name: str, item: str, readings: dict) -> dict:
    """The record one pass produces, held to its shape and to the commit.

    ⛔ **Refused rather than rendered with a hole in it.** What a release is held
    up or let through on is this record, so a criterion missing its instrument or
    its date is a refusal naming the criterion -- not a row with a blank cell.

    ⚠️ **What comes back is readings and a standing, never a verdict.** `holds`
    says whether anything in the record stops the item being accepted; who
    accepts it is `orderer`'s, and `waits_on` carries that in as many words so
    the role's report cannot quietly read as the move having been made.
    """
    answer = plan(resolved, name)
    served = served_commit(resolved, name)
    if served.get("unestablished"):
        raise CannotAnswer(served["unestablished"])
    at = _committed_at(answer["root"], served["commit"])
    commit_stamp = _stamp(at, f"the commit {served['commit']!r}")

    criteria = readings.get("criteria")
    if not isinstance(criteria, list) or not criteria:
        raise CannotAnswer(
            "the readings state no criteria, and a record over no criterion is a "
            "record of nothing (§ 39). An item whose own acceptance section is "
            "empty is reported as stating none rather than passed."
        )

    held: list[dict] = []
    holding: list[str] = []
    for index, entry in enumerate(criteria):
        where = f"criteria[{index}]"
        if not isinstance(entry, dict):
            raise CannotAnswer(f"{where} is not a mapping.")
        criterion = entry.get("criterion")
        if not isinstance(criterion, str) or not criterion.strip():
            raise CannotAnswer(f"{where} states no criterion it is about.")
        bucket = entry.get("bucket")
        if bucket not in BUCKETS:
            raise CannotAnswer(
                f"{where} is classified {bucket!r}; § 39 states "
                f"{' | '.join(sorted(BUCKETS))}."
            )
        for key in BUCKETS[bucket]:
            value = entry.get(key)
            if not isinstance(value, str) or not value.strip():
                raise CannotAnswer(
                    f"{where} is classified `{bucket}` and states no {key!r}, "
                    "which § 39 makes part of what a criterion in that bucket "
                    "carries."
                )
        row = {
            "criterion": criterion,
            "bucket": bucket,
            **{key: entry[key].strip() for key in BUCKETS[bucket]},
        }
        if "at" in row:
            taken = _stamp(row["at"], f"{where}'s date")
            # ⛔ The one arithmetic this facet has. A reading taken before the
            # commit the target serves is a measurement of code the target was
            # not yet running, so it cannot accept the item that commit changed.
            if taken < commit_stamp:
                raise CannotAnswer(
                    f"{where} was read at {row['at']} and the `{name}` target "
                    f"serves {served['commit']} from {at}. A reading taken "
                    "before the commit it is about cannot accept the item that "
                    "commit changed (§ 39): take it again against the commit "
                    "the target is serving now."
                )
        if bucket in HOLDS_THE_ITEM:
            holding.append(criterion)
        held.append(row)

    # ⛔ The content-parity pair is a **reading** the record carries and not a
    # precondition this module asserts: two copies differing in their data is a
    # diff nobody can attribute, and what makes that visible is the pair being
    # on the record where a reader meets it.
    parity = readings.get("parity")
    if not isinstance(parity, dict) or set(parity) != {"baseline", "subject"}:
        raise CannotAnswer(
            "the readings carry no content-parity pair. § 39 makes it a reading "
            "the record states -- `parity: {baseline: <n>, subject: <n>}` -- "
            "because a comparison whose two sides differ in their data is a diff "
            "nobody can attribute."
        )
    for side in ("baseline", "subject"):
        if isinstance(parity[side], bool) or not isinstance(parity[side], int):
            raise CannotAnswer(f"the parity pair's {side!r} count is not a number.")

    # ⚠️ Stated where a fixture was stood up and omitted where none was, which is
    # § 39's own shape: a provisioning run owes its checksum pair and that nothing
    # was left, and ⛔ a fixture left behind holds the item rather than being
    # reported beside a clean record.
    provisioned = readings.get("provisioned")
    if provisioned is not None:
        if not isinstance(provisioned, dict):
            raise CannotAnswer("`provisioned` is not a mapping.")
        for key in ("before", "after", "left"):
            if key not in provisioned:
                raise CannotAnswer(
                    f"`provisioned` states no {key!r}; a provisioning run owes "
                    "its checksum pair and the count it left behind (§ 39)."
                )
        if isinstance(provisioned["left"], bool) or not isinstance(
            provisioned["left"], int
        ):
            raise CannotAnswer("`provisioned.left` is not a number.")
        if provisioned["left"]:
            holding.append(
                f"{provisioned['left']} fixture(s) left behind by the "
                "provisioning run"
            )

    out = {
        "item": str(item),
        "target": name,
        "not_live": answer["not_live"],
        "root": answer["root"],
        "commit": served["commit"],
        "committed_at": at,
        "baseline": dict(answer["baseline"]),
        "breakpoints": list(answer["breakpoints"]),
        "criteria": held,
        "parity": {"baseline": parity["baseline"], "subject": parity["subject"]},
        "parity_matches": parity["baseline"] == parity["subject"],
        "provisioned": dict(provisioned) if provisioned is not None else None,
        # ⚠️ Carried through in one line each and ⛔ **not filed**: opening an item
        # for a defect belonging to no item is the person's call (§ 39).
        "residue": [
            " ".join(str(line).split())
            for line in (readings.get("residue") or [])
        ],
        "holding": holding,
        "holds": not holding,
        # ⛔ The standing, said in as many words so that no reader of this record
        # takes it for the move. § 4.2 gives the write to `orderer` and this
        # module asks for no status at all.
        "waits_on": (
            f"the `{ACCEPTED_ROLE}` role is written by `{ORDERER}` (§ 4.2), so "
            "this record is readings and the move waits on that person's word."
        ),
        "rejection": {
            "trigger": REJECTED,
            "rules_it": answer["rules_rejection"],
            # ⛔ Named and not performed: the ask goes through the port, which is
            # the only route to § 32's edge.
            "asked_through": "port.py --revert-on",
        },
    }
    return out


# --- the report -------------------------------------------------------------


def report(resolved) -> dict:
    """What this project states, per target, with nothing run."""
    facet = stated(resolved)
    targets = [
        entry.get("name")
        for entry in (resolved.get("deploy") or [])
        if isinstance(entry, dict)
    ]
    if facet is None:
        return {
            "judges": None,
            "targets": targets,
            "unavailable": [
                line for line in resolved.unavailable() if "verify.carrier" in line
            ],
        }
    judged = sorted(facet["identity"])
    return {
        "judges": judged,
        "targets": targets,
        # ⚠️ Reported rather than refused: a target this project deploys to and
        # judges nothing on is § 39's own shape, and the role says which.
        "not_judged": [name for name in targets if name not in judged],
        "baseline": dict(facet["baseline"]),
        "breakpoints": list(facet["breakpoints"]),
        "rejection_trigger": REJECTED,
    }


# --- self-test --------------------------------------------------------------
#
# The acceptance check of the work item this carrier was built for, run as code:
# the record's shape held in both directions, the one arithmetic asserted against
# a real repository, the writer refusal asserted against the port rather than
# described, and the project's own stated absence reported as an absence.


def _a_tree(files: dict[str, str]) -> str:
    root = tempfile.mkdtemp(prefix="verify-suite-")
    for name, text in files.items():
        full = os.path.join(root, name)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as handle:
            handle.write(text)
    return root


def _git(root: str, *args: str, **env) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", root, *args],
        capture_output=True,
        text=True,
        timeout=60,
        env={
            **os.environ,
            "GIT_AUTHOR_NAME": "suite",
            "GIT_AUTHOR_EMAIL": "suite@invalid",
            "GIT_COMMITTER_NAME": "suite",
            "GIT_COMMITTER_EMAIL": "suite@invalid",
            **env,
        },
    )


def _a_repository(stamp: str) -> tuple[str, str]:
    """A tree with one commit, made at a stated time, and that commit's name.

    ⛔ A real repository rather than a stubbed stamp reader: the arithmetic this
    suite is about compares a reading against a **commit's own** date, and a fake
    at the stamp seam would assert the comparison against a value the suite
    chose -- which is the arm, not the subject.

    ⚠️ **The committer date and not the author one**, which is the stamp this
    module reads: `--date` sets the author's, so a fixture that set only that
    would have planted a commit whose arrival time was *now* -- and every arm
    below would then have asserted against the clock. Measured: the first form of
    this helper did exactly that.
    """
    root = _a_tree({"served.txt": "a\n"})
    _git(root, "init", "-q")
    made = _git(
        root,
        "-c",
        "user.name=suite",
        "-c",
        "user.email=suite@invalid",
        "commit",
        "-q",
        "--allow-empty",
        "--date",
        stamp,
        "-m",
        "the commit the target serves",
        GIT_COMMITTER_DATE=stamp,
    )
    if made.returncode != 0:
        raise RuntimeError(f"the suite could not make a commit: {made.stderr}")
    named = _git(root, "rev-parse", "HEAD")
    return root, named.stdout.strip()


class _Stated:
    """A project's stated facets and roots, with no configuration file.

    ⛔ A stand-in at the accessor seam rather than at the reader's: what this
    module reads is `verify()`, `get()`, `code_root()` and `unavailable()`, so a
    fake answering those four replaces exactly what it has to and leaves every
    rule the reader performs -- the target-name resolution, the width type, the
    baseline's two halves -- where it is. ⚠️ Which is why the suite also loads a
    planted facet **through the reader**, in the arm asserting that a
    configuration this module accepts is one the reader does.
    """

    def __init__(self, root: str, *, facet=None, deploy=None, reversals=()):
        self._root = root
        self._facet = facet
        self._deploy = deploy or []
        self._reversals = list(reversals)

    def verify(self):
        return dict(self._facet) if self._facet else None

    def get(self, key):
        if key == "deploy":
            return self._deploy
        if key == "reversals":
            return self._reversals
        raise AssertionError(f"the suite's stand-in was asked for {key!r}")

    def code_root(self, name=None):
        return self._root

    def unavailable(self):
        return ["Nothing is judged on a deploy target (`verify.carrier: none`)."]


def self_test() -> int:
    failures = []

    def check(label: str, held: bool, detail: str = "") -> None:
        print(f"  {'ok  ' if held else 'FAIL'}  {label}" + (
            "" if held else f": {detail}"))
        if not held:
            failures.append(label)

    def refused(call) -> str | None:
        try:
            call()
        except CannotAnswer as answer:
            return str(answer)
        return None

    # ⛔ Every green-side call goes through this rather than being made directly.
    # An arm has to survive the defect it tests: a refusal raised where this
    # suite expected an answer would otherwise stop the run at that line and take
    # every arm after it with it -- reported as one red where the truth is one red
    # and a dozen unrun. ⚠️ `None` comes back, and each caller guards on it.
    def produced(label: str, call):
        try:
            return call()
        except CannotAnswer as answer:
            check(label, False, f"refused on {answer}")
            return None

    # The commit's own date, and a reading on either side of it. ⚠️ Fixed stamps
    # rather than *now*, because what is asserted is an ordering and a suite that
    # read the clock would assert whichever side the clock fell on.
    made_at = "2026-03-01T12:00:00+00:00"
    after = "2026-03-01T12:00:01+00:00"
    before = "2026-03-01T11:59:59+00:00"

    try:
        root, commit = _a_repository(made_at)
    except (RuntimeError, OSError, subprocess.SubprocessError) as broken:
        print(f"  --    this suite needs a repository it can make: {broken}")
        return 1

    def a_facet(**overrides):
        facet = {
            "identity": {"a-target": f"echo {commit}"},
            "baseline": {"ref": "a-ref", "harness": "/a/durable/path"},
            "breakpoints": [640],
        }
        facet.update(overrides)
        return facet

    def a_project(**overrides):
        return _Stated(
            root,
            facet=a_facet(**overrides),
            deploy=[{"name": "a-target", "not_live": True}],
            reversals=[{"trigger": REJECTED, "to_role": "ready", "writer": ORDERER}],
        )

    def a_criterion(**overrides):
        row = {
            "criterion": "the page carries the component",
            "bucket": "on_target",
            "reading": "the served fragment's digest matches the reference",
            "environment": "the target itself",
            "instrument": "a digest of the served fragment",
            "at": after,
        }
        row.update(overrides)
        return row

    def some_readings(**overrides):
        readings = {
            "criteria": [a_criterion()],
            "parity": {"baseline": 7, "subject": 7},
        }
        readings.update(overrides)
        return readings

    print("What a target resolves to, and the two answers that are not a fault:")
    answer = plan(a_project(), "a-target")
    check("a target the project judges on resolves to its own command",
          answer["identity_command"] == f"echo {commit}",
          f"resolved {answer['identity_command']!r}")
    check("and the baseline and the widths come with it",
          answer["baseline"]["harness"] == "/a/durable/path"
          and answer["breakpoints"] == [640],
          f"resolved {answer!r}")
    check("the step back's trigger is named rather than left to be composed",
          answer["rejection_trigger"] == REJECTED and answer["rules_rejection"],
          f"answered {answer['rejection_trigger']!r}")
    said = refused(lambda: plan(a_project(), "another-target"))
    check("a name no target carries is refused, listing the ones that exist",
          said is not None and "a-target" in said,
          f"said {said!r}")
    # ⚠️ The second answer that is not a fault: a target this project deploys to
    # and judges nothing on. § 39 makes it a reading of the configuration.
    judging_elsewhere = _Stated(
        root,
        facet=a_facet(identity={"a-second-target": "echo x"}),
        deploy=[{"name": "a-target"}, {"name": "a-second-target"}],
    )
    said = refused(lambda: plan(judging_elsewhere, "a-target"))
    check("a target with no command is refused as one no pass may be taken against",
          said is not None and "no acceptance pass may be taken" in said,
          f"said {said!r}")
    check("and the refusal names the targets this project does judge on",
          said is not None and "a-second-target" in said,
          f"said {said!r}")

    print("\nThe commit a target serves, and the readings that are not it:")
    served = served_commit(a_project(), "a-target")
    check("the commit comes back from the project's own command",
          served["commit"] == commit, f"read {served['commit']!r}")
    check("and nothing else is read for it",
          served["command"] == f"echo {commit}", f"ran {served['command']!r}")
    # ⛔ A command that printed nothing is **unestablished**, never *unchanged*.
    silent = served_commit(a_project(identity={"a-target": "true"}), "a-target")
    check("a command that printed nothing reports unestablished, not a commit",
          silent["commit"] is None and "unestablished" in silent["unestablished"],
          f"answered {silent!r}")
    failed = served_commit(a_project(identity={"a-target": "exit 3"}), "a-target")
    check("and a command that failed carries its own status through",
          failed["exit_status"] == 3 and failed.get("unestablished"),
          f"answered {failed!r}")

    print("\nThe record's shape, held in both directions:")
    made = record(a_project(), "a-target", "1", some_readings())
    check("a record whose criteria are complete holds",
          made["holds"] and made["criteria"][0]["instrument"],
          f"answered {made!r}")
    check("and it carries the commit it was taken against, with its date",
          made["commit"] == commit and made["committed_at"],
          f"answered {made['commit']!r} at {made.get('committed_at')!r}")
    check("and the parity pair is on the record rather than asserted away",
          made["parity"] == {"baseline": 7, "subject": 7} and made["parity_matches"],
          f"answered {made['parity']!r}")
    check("and the record says in as many words whose the move is",
          ORDERER in made["waits_on"] and ACCEPTED_ROLE in made["waits_on"],
          f"said {made['waits_on']!r}")
    # ⛔ The four keys a measured criterion owes, each dropped on its own: a
    # record rendered with one of them blank is what a release is then let
    # through on.
    for key in MEASURED:
        said = refused(lambda key=key: record(
            a_project(), "a-target", "1",
            some_readings(criteria=[{
                field: value for field, value in a_criterion().items()
                if field != key
            }]),
        ))
        check(f"a criterion stating no {key!r} is refused rather than rendered",
              said is not None and key in said, f"said {said!r}")
    said = refused(lambda: record(
        a_project(), "a-target", "1",
        some_readings(criteria=[a_criterion(bucket="a-bucket")]),
    ))
    check("a bucket outside the four is refused, naming the four",
          said is not None and "no_referent" in said, f"said {said!r}")
    said = refused(lambda: record(
        a_project(), "a-target", "1", some_readings(criteria=[]),
    ))
    check("a record over no criterion at all is refused",
          said is not None and "record of nothing" in said, f"said {said!r}")
    said = refused(lambda: record(
        a_project(), "a-target", "1", {"criteria": [a_criterion()]},
    ))
    check("readings carrying no parity pair are refused",
          said is not None and "content-parity" in said, f"said {said!r}")

    print("\nThe two buckets that are answers rather than readings:")
    # ⛔ A criterion with no referent owes an owner and no reading, and it holds
    # the item whatever the measurable half says.
    unanswerable = record(a_project(), "a-target", "1", some_readings(criteria=[
        a_criterion(),
        {"criterion": "it matches the drawing nobody drew",
         "bucket": "no_referent",
         "owner": "whoever owns the design source"},
    ]))
    check("a criterion with no referent is reported with whose it is to supply",
          unanswerable["criteria"][1]["owner"] == "whoever owns the design source",
          f"answered {unanswerable['criteria'][1]!r}")
    check("and it holds the item rather than being reported beside a clean record",
          not unanswerable["holds"] and unanswerable["holding"],
          f"answered holds={unanswerable['holds']!r}")
    said = refused(lambda: record(
        a_project(), "a-target", "1", some_readings(criteria=[
            {"criterion": "a criterion", "bucket": "no_referent"},
        ]),
    ))
    check("and one stating no owner is refused rather than reported unowned",
          said is not None and "owner" in said, f"said {said!r}")
    # ⛔ The bucket that does **not** hold the item, which is § 39's deadlock
    # ruling: a criterion that cannot be met until a later target runs stays on
    # the item and the item is still accepted.
    later = record(a_project(), "a-target", "1", some_readings(criteria=[
        a_criterion(bucket="later_target",
                    reading="unmeasurable until the release runs",
                    environment="the release target",
                    instrument="the release's own run"),
    ]))
    check("a criterion not measurable until a later target does not hold the item",
          later["holds"], f"answered holds={later['holds']!r}, {later['holding']!r}")
    # ⛔ And the bucket that owes a fifth field: why the target could not be it.
    said = refused(lambda: record(
        a_project(), "a-target", "1",
        some_readings(criteria=[a_criterion(bucket="elsewhere")]),
    ))
    check("a criterion measured elsewhere owes why the target could not be it",
          said is not None and "why_not_the_target" in said, f"said {said!r}")

    print("\nThe one arithmetic, asserted against a real commit:")
    said = refused(lambda: record(
        a_project(), "a-target", "1",
        some_readings(criteria=[a_criterion(at=before)]),
    ))
    check("a reading taken before the commit the target serves is refused",
          said is not None and "cannot accept the item that commit changed" in said,
          f"said {said!r}")
    check("and the refusal names both stamps rather than only that it refused",
          said is not None and before in said and commit in said,
          f"said {said!r}")
    # ⚠️ The green side, which the plant above would redden either way: a reading
    # taken at the commit's own second is not before it.
    same = record(a_project(), "a-target", "1",
                  some_readings(criteria=[a_criterion(at=made_at)]))
    check("a reading taken at the commit's own stamp holds",
          same["holds"], f"answered {same['holding']!r}")
    said = refused(lambda: record(
        a_project(), "a-target", "1",
        some_readings(criteria=[a_criterion(at="2026-03-01 12:00:01")]),
    ))
    check("a date carrying no offset is refused rather than read as local",
          said is not None and "offset" in said, f"said {said!r}")
    # ⛔ And the stamp is read rather than handed in: a commit the repository
    # does not answer for is unestablished, never *now*.
    said = refused(lambda: record(
        a_project(identity={"a-target": "echo " + "0" * 40}),
        "a-target", "1", some_readings(),
    ))
    check("a commit the repository does not answer for is unestablished",
          said is not None and "unestablished" in said, f"said {said!r}")

    print("\nThe provisioning pair, and the fixture that holds the item:")
    clean = record(a_project(), "a-target", "1", some_readings(
        provisioned={"before": "aaa", "after": "aaa", "left": 0}))
    check("a provisioning run reports its checksum pair and holds nothing",
          clean["holds"] and clean["provisioned"]["before"] == "aaa",
          f"answered {clean['provisioned']!r}")
    left = record(a_project(), "a-target", "1", some_readings(
        provisioned={"before": "aaa", "after": "bbb", "left": 2}))
    check("and a fixture left behind holds the item",
          not left["holds"] and any("fixture" in line for line in left["holding"]),
          f"answered {left['holding']!r}")
    said = refused(lambda: record(
        a_project(), "a-target", "1",
        some_readings(provisioned={"before": "aaa"}),
    ))
    check("a provisioning run stating no checksum pair is refused",
          said is not None and "checksum pair" in said, f"said {said!r}")

    print("\nResidue is carried and never filed:")
    carried = record(a_project(), "a-target", "1", some_readings(
        residue=["a defect belonging to no item"]))
    check("residue reaches the record in one line",
          carried["residue"] == ["a defect belonging to no item"],
          f"answered {carried['residue']!r}")
    check("and it does not hold the item, opening one being the person's call",
          carried["holds"], f"answered holds={carried['holds']!r}")

    print("\nThe verdict this module may not give:")
    # ⛔ Asserted against the port rather than described: § 4.2 gives the
    # `accepted` role to `orderer`, so what has to hold is that an ask made as
    # anything else is refused -- including as the procedure, which is what every
    # role but § 33's asks as.
    try:
        import port as the_port
    except ImportError as broken:  # pragma: no cover -- a sibling module
        check("the port is importable, so the writer arms have a subject", False,
              str(broken))
    else:
        statuses = [
            {"name": "open", "role": "initial", "writer": "procedure"},
            {"name": "accepted", "role": ACCEPTED_ROLE, "writer": ORDERER},
        ]

        class _Config:
            def get(self, key):
                return statuses if key == "statuses" else None

        spec = the_port.port_spec()
        asking = the_port.Port(
            _Config(),
            spec,
            adapter=the_port.Adapter(),
            # ⚠️ The surface's own fallbacks, read through the port rather than
            # stubbed: an operation the surface has renamed must stop this arm
            # rather than have it assert a guard around a capability that is no
            # longer declared.
            stated=the_port.surface_operations(),
        )
        for writer in ("procedure", "deploy", "automation", "sweep"):
            outcome = asking.advance_to(ACCEPTED_ROLE, "1", as_writer=writer)
            check(
                f"an ask for the accepted role made as `{writer}` is refused",
                outcome.refused and not outcome.performed,
                f"answered {str(outcome)!r}",
            )
        check(
            "and the refusal names the writer the configuration states",
            ORDERER in str(asking.advance_to(ACCEPTED_ROLE, "1", as_writer="procedure")),
            f"said {str(asking.advance_to(ACCEPTED_ROLE, '1'))!r}",
        )
        # ⛔ **And there is no writer it could ask as**, which is the arm that
        # makes this a bar rather than a wrong-writer mistake. § 4.2 closes the
        # set an ask may be *made* as to the procedure and the deploy, and the
        # configured writer here is neither -- so the two never meet, and naming
        # the configured writer is refused before the configuration is read at
        # all, as a claim to be somebody. ⚠️ Measured rather than assumed: the
        # first form of this suite asserted the opposite and reddened here.
        claimed = asking.advance_to(ACCEPTED_ROLE, "1", as_writer=ORDERER)
        check(
            "and naming the configured writer is refused too, as a claim to be it",
            claimed.refused and ORDERER in str(claimed),
            f"answered {str(claimed)!r}",
        )
        # ⚠️ The green side, so that the four arms above are about **this role**
        # and not about every move being refused: a role the procedure does write
        # goes through the same guard and is not refused.
        permitted = asking.advance_to("initial", "1")
        check(
            "while a role the procedure does write is not refused by the guard",
            not permitted.refused,
            f"answered {str(permitted)!r}",
        )
    # ⛔ And this module itself never asks: the record carries the standing and
    # names no status word at all.
    check(
        "the record names no status word, carrying the standing instead",
        "set_state" not in json.dumps(made) and made["waits_on"],
        f"answered {made!r}",
    )

    print("\nWhat a planted facet reads as through the reader, not only here:")
    # ⚠️ The arm that keeps the stand-in honest: a facet this module accepts has
    # to be one the reader accepts too, which is where every rule the reader
    # performs is asserted rather than bypassed.
    loaded = None
    try:
        with open(config.SURFACE, encoding="utf-8") as handle:
            facts = config.surface_facts(handle.read())
        for path in config._examples():
            with open(path, encoding="utf-8") as handle:
                data = config._load_yaml(handle.read(), config.CONFIG_PATH)
            if config._get(data, "verify.carrier") == "list":
                loaded = config._resolve(data, config.EXAMPLES, facts, False)
                break
    except config.ConfigError as broken:
        check("a shipped example states the facet and loads", False, str(broken))
    check(
        "a shipped example states a judgement, so this arm has a subject",
        loaded is not None,
        "no example states `verify.carrier: list`",
    )
    if loaded is not None:
        answered = report(loaded)
        check("the report names the targets this project judges on",
              answered["judges"] and set(answered["judges"]) <= set(answered["targets"]),
              f"answered {answered!r}")
        check("and the targets it judges nothing on, rather than leaving them out",
              answered["not_judged"] is not None,
              f"answered {answered!r}")

    print("\nThis project's own answer, which is the absence:")
    try:
        own = config.load(".")
    except config.ConfigError as broken:
        print(f"  --    this project's configuration did not resolve: {broken}")
    else:
        answered = report(own)
        if answered["judges"] is None:
            check("this project reports no judgement rather than an empty one",
                  answered["unavailable"],
                  f"answered {answered!r}")
        else:
            check("this project states a judgement, and it resolves",
                  bool(answered["judges"]), f"answered {answered!r}")

    if failures:
        print(f"\n{len(failures)} assertion(s) did not hold.")
    return 1 if failures else 0


# --- entry point -----------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("what", nargs="?", choices=["plan", "commit", "record"])
    parser.add_argument("--skills-root", default=None)
    parser.add_argument("--target", help="the `deploy` entry's own name")
    parser.add_argument("--item", help="the work item the readings are about")
    parser.add_argument(
        "--readings",
        help="a file stating the criteria, the parity pair and any residue",
    )
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        print("Holding the acceptance carrier to the surface and to a repository:")
        return self_test()

    try:
        resolved = config.load(args.skills_root or ".")
    except config.ConfigError as broken:
        print(str(broken), file=sys.stderr)
        return 2

    # ⛔ The stated absence answers first and with its own status, before any
    # argument is read: what a consumer asks is whether there is a judgement to
    # take, and an absence reported as a failure reads as readings that are all
    # wrong.
    if stated(resolved) is None:
        print(json.dumps(report(resolved), indent=2, ensure_ascii=False))
        return NO_JUDGEMENT

    if args.what is None:
        print(json.dumps(report(resolved), indent=2, ensure_ascii=False))
        return 0

    if not args.target:
        print("`--target` names the `deploy` entry this pass is about.",
              file=sys.stderr)
        return 2

    try:
        if args.what == "plan":
            answer = plan(resolved, args.target)
        elif args.what == "commit":
            answer = served_commit(resolved, args.target)
        else:
            if not (args.item and args.readings):
                print("`record` wants `--item` and `--readings`.", file=sys.stderr)
                return 2
            with open(args.readings, encoding="utf-8") as handle:
                readings = config._load_yaml(handle.read(), args.readings)
            answer = record(resolved, args.target, args.item, readings)
    except CannotAnswer as refusal:
        print(json.dumps({"answered": False, "because": str(refusal)},
                         indent=2, ensure_ascii=False))
        return 1
    except config.ConfigError as broken:
        print(str(broken), file=sys.stderr)
        return 2

    print(json.dumps(answer, indent=2, ensure_ascii=False, default=str))
    if args.what == "commit" and answer.get("unestablished"):
        return 1
    if args.what == "record" and not answer["holds"]:
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover -- the entry point
    sys.exit(main(sys.argv[1:]))
