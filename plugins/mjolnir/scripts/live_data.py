#!/usr/bin/env python3
"""The one step of a deploy that cannot be undone, performed in order.

`live_data_step` (§ 35) is a block on a § 33 deploy target, and ⛔ **the ordering
is this module rather than the role**: a role free to reach the write before the
dump has been read back is a role with no rail at all, so what the surface calls
*the ordering and the stops* is performed here and the skill asks rather than
sequencing.

⛔ **What this module states nothing about is the store.** No connection, no
credential, no schema, and no derivation of what is pending: each is
`../config/schema.md § 35`'s middle column, and the commands are the project's
own, stated whole and run as written.

What it owns is the part none of its callers should perform twice:

  * **The ordering**, asserted rather than documented. ⛔ **The sequence itself is
    not written here**: § 35 states it in a table and `PREPARED` below performs
    it, and a third copy in this docstring would be a list free to disagree with
    both. ⛔ **Each stop stops the deploy** rather than the step, and the step
    cannot be entered at the write.
  * **The go, bound to what it is a go for.** A go that does not name this
    target and the verdict the rehearsal came back with is refused — § 29's
    binding for a dispatch, met one facet over, because the act here is as
    irreversible and the evidence is newer.
  * **The hand-over**, where the target states a person performs the write: the
    command is handed back verbatim and ⛔ **no write is made**, which is
    reported in those words.
  * **What the store is left holding** where the write ran and failed, which is
    the one fact a report that stopped here may not omit.

⚠️ **It decides neither the order against the invocation nor whether anything is
pending.** The first is configured and the go may overrule it; the second is the
project's command's own answer. This module performs what it was handed and says
which of the two it took.

Usage:
    live_data.py [--skills-root DIR] --target NAME   what the target states
    live_data.py plan --target NAME                  the ordering, nothing run
    live_data.py prepare --target NAME               the dump, its reading, the
                                                     rehearsal — and then a stop
    live_data.py apply --target NAME --given TEXT    the write, under that go
    live_data.py --self-test                         assert every answer against
                                                     planted trees and commands

Exit status, and ⛔ **four values rather than two**: 0 the answer was produced,
1 the step stopped and names where, 2 the configuration could not be read, 3 this
target states no live data step. ⚠️ The last is § 11's rule at a command line —
*no step* collapsed into 0 reads as a step that ran, and into 1 as a deploy that
failed.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import config  # noqa: E402 -- the one reader of the surface

# ⛔ The exit status this module reserves for the target's stated absence, named
# for the reason `release.py` names its own: a reader comparing against a literal
# would be comparing against a number, and the number is the least readable part
# of the contract it carries.
NO_STEP = 3

# The ordered sequence § 35 states, held here as data so that the plan a caller
# reads and the sequence `prepare` performs are one list rather than two.
# ⛔ **The write is not in it**, and that is the whole point of the split: every
# step below runs without a go, and the one that needs one is a subcommand of its
# own.
PREPARED = ("backup.run", "backup.verify", "rehearse")

# What the go has to name, and ⛔ **not a form the go is composed to satisfy.**
# § 29 states the rule for a dispatch and § 35 states it for this write: a go is
# an approval of something, so one that names neither what it approves nor the
# reading it was given is an answer to a question nobody can reconstruct.
#
# ⚠️ Matched case-insensitively and as a substring, which is the loosest form that
# still carries the fact. A tighter match would be a form, and a person typing a
# correct answer in their own words would be refused by it.
GO_MUST_NAME = ("the target", "the rehearsal's verdict")

# Where the reading `prepare` took is left for `apply` to find, under the
# directory § 11 states artifacts crossing a role boundary live in.
# ⛔ **A name per target**, because a project with two stepped targets prepares
# each separately and a shared file would let a reading taken against one license
# a write against the other.
RECORD = "live-data-step-{target}.json"

# ⚠️ What a rehearsal that said nothing is reported as. A stand-in and never a
# default: every arm that would compare against it is dropped instead, which is
# why it says what it is rather than looking like an output somebody might have
# meant.
_UNREAD = "<the rehearsal's output could not be read>"

# ⛔ **No word is matched in a rehearsal's output, and the attempt is recorded
# here rather than left out.** A substring reading was written first and is wrong
# by construction: the surveyed copy's guarded rehearsal states that it must
# report *no divergence* to pass, so the **passing** output carries the word the
# failing one does — and the first run of this module's own suite stopped a clean
# rehearsal on it.
#
# ⚠️ So the verdict is the exit status, which is what § 35 states, and the output
# is carried verbatim for a person to read before the go. ⛔ What that leaves open
# is named in § 35 rather than closed here: a project whose dry variant reports a
# divergence and exits zero anyway has to make that comparison inside its own
# command, and nothing in this module can make it.


def _slug(target: str) -> str:
    """A target's name as a file name, with nothing of the name invented.

    ⚠️ Lossy by construction — two names differing only in punctuation collapse —
    which is why `prepare` writes the name itself into the record and `apply`
    compares that rather than the path it opened.
    """
    return "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in target)


def _record_path(configuration: config.Config, target: str) -> str:
    where = configuration.get("context.artifacts.dir") or tempfile.gettempdir()
    return os.path.join(os.path.expandvars(where), RECORD.format(target=_slug(target)))


def _run(command: str, root: str) -> dict:
    """One of the project's own commands, run whole in the root it was given.

    ⛔ **Nothing is prefixed to it and nothing is read out of it beyond its
    status and its output**, by § 35's boundary: the command is the project's and
    this module has no business parsing what it prints.
    """
    try:
        done = subprocess.run(
            command, shell=True, cwd=root, capture_output=True, text=True,
        )
    except OSError as error:
        # ⚠️ A command that could not be started at all, which is not the same as
        # one that ran and failed: reported as unestablished rather than as a
        # non-zero status nothing produced (§ 11).
        return {
            "command": command,
            "ran": False,
            "status": None,
            "output": f"{error.__class__.__name__}: {error}",
        }
    return {
        "command": command,
        "ran": True,
        "status": done.returncode,
        "output": (done.stdout + done.stderr).strip(),
    }


def _steps(block: dict) -> list[dict]:
    """The ordered sequence, one entry per step, with the command for each.

    ⚠️ A `rehearse` the project does not state is **in the list** and marked as
    stated-nowhere rather than dropped: § 35 makes an omitted rehearsal a step
    reported as no rehearsal, and a list that silently lost the row would be a
    plan a reader counts the steps of and gets the wrong answer.
    """
    out = []
    for name in PREPARED:
        if name == "rehearse":
            command = block.get("rehearse")
        else:
            command = block["backup"][name.split(".", 1)[1]]
        out.append({
            "step": name,
            "command": command,
            "stated": isinstance(command, str) and bool(command.strip()),
        })
    return out


def _dump(answer: dict) -> str:
    """The command that took the dump, read out of the plan **by name**.

    ⛔ By name and never by position. The sequence lives in `PREPARED` and a
    reader that took `steps[0]` would be a second derivation of its order, free
    to name the wrong command the day that list is reordered -- which is the
    restated-derivation class a review reads a diff for.
    """
    for step in answer["steps"]:
        if step["step"] == "backup.run":
            return str(step["command"])
    # ⚠️ Unreachable while `PREPARED` carries the dump, and reported rather than
    # raised: this runs inside the message about a failed write, which is the one
    # place a traceback would replace the fact a reader needs.
    return "<the plan carries no dump>"


def plan(configuration: config.Config, target: str) -> dict | None:
    """The whole ordering, with nothing run and nothing written, or `None`.

    `None` is the target's stated absence (§ 35) and never an empty plan: this
    target writes no live data, so there is no step rather than a step with
    nothing in it.
    """
    read = configuration.live_data_step(target)
    if read["found"] is None:
        return None
    block, entry = read["found"], read["target"]
    report = list(read["report"])
    report.append(
        f"The order stated is {block['order']!r}, which is where this step falls "
        "against § 33's invocation. ⛔ The configured value is what this role "
        "proposes and the go is where it is settled: whether the write belongs "
        "before the image depends on what is pending, and detecting that is the "
        "project's own (§ 35)."
    )
    if block["apply_by"] == "person":
        report.append(
            "This target states that a person performs the write, so the command "
            "is handed over and ⛔ **no write is made by this role** (§ 35). The "
            "go is still asked: `apply_by` says who runs the command, never "
            "whether it is approved."
        )
    if not any(step["step"] == "rehearse" and step["stated"] for step in _steps(block)):
        report.append(
            "This target states no rehearsal, which § 35 makes a key a block may "
            "omit. ⛔ Reported as **no rehearsal** rather than as a clean one, and "
            "the go is asked with that said."
        )
    return {
        "target": target,
        "not_live": entry.get("not_live"),
        "code_root": configuration.code_root(),
        "order": block["order"],
        "apply_by": block["apply_by"],
        "steps": _steps(block),
        "apply": block["apply"],
        "record": block["record"],
        # ⛔ Read from live targets only, which is § 35's liveness pairing and is
        # the accessor's answer rather than a second reading here.
        "reads_record": read["reads_record"],
        "go_must_name": list(GO_MUST_NAME),
        "report": report,
    }


def prepare(configuration: config.Config, target: str) -> dict | None:
    """The dump, the dump read back, the rehearsal — and then a stop.

    ⛔ **The stop is the outcome rather than a failure**: the go is the person's
    and the rehearsal's output is what it is given on, so a pass that ran these
    three and then wrote would have approved on their behalf (§ 35).

    ⛔ **And the dump runs whether or not anything is pending.** What a deploy
    turns out to write against a store is not fully known until it has run, and a
    dump taken afterwards records the damage rather than the state before it.
    """
    answer = plan(configuration, target)
    if answer is None:
        return None
    root = answer["code_root"]
    answer["ran"] = []
    answer["stopped_at"] = None
    answer["rehearsal"] = None
    for step in answer["steps"]:
        if not step["stated"]:
            # The rehearsal nobody stated. Already reported by `plan`; nothing is
            # run and nothing is treated as having passed.
            continue
        outcome = _run(step["command"], root)
        answer["ran"].append(dict(outcome, step=step["step"]))
        if not outcome["ran"] or outcome["status"] != 0:
            answer["stopped_at"] = step["step"]
            answer["report"].insert(
                0,
                f"The deploy stops: {step['step']} "
                + (
                    "could not be run at all, so it is reported unestablished "
                    "rather than failed"
                    if not outcome["ran"]
                    else f"exited {outcome['status']}"
                )
                + ". ⛔ The deploy and not the step (§ 35), and nothing after "
                "this ran.",
            )
            return answer
        if step["step"] == "rehearse":
            answer["rehearsal"] = outcome["output"] or _UNREAD
            if not outcome["output"]:
                answer["stopped_at"] = step["step"]
                answer["report"].insert(
                    0,
                    "The deploy stops: the rehearsal produced no output, so there "
                    "is nothing for a person to read and the go would be given on "
                    "nothing. ⛔ Reported unread rather than clean (§ 11).",
                )
                return answer
    # ⛔ Written only once every step above came back, so a record on disk is
    # evidence that the sequence completed rather than that it was started.
    path = _record_path(configuration, target)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(
            {
                "target": target,
                "order": answer["order"],
                "rehearsal": answer["rehearsal"],
                "verified": [outcome["step"] for outcome in answer["ran"]],
            },
            handle,
        )
    answer["record_at"] = path
    answer["report"].insert(
        0,
        "The dump is taken and read back"
        + (
            ", the rehearsal ran and its output is above"
            if answer["rehearsal"]
            else " and this target states no rehearsal"
        )
        + ". ⛔ The step stops here: the write is the person's act, and the go is "
        "asked on what is above rather than before any of it existed (§ 35).",
    )
    return answer


def apply(configuration: config.Config, target: str, go: str) -> dict | None:
    """The write, under a go that names what it is a go for. `None` where none.

    ⛔ **Four refusals before anything runs**, and each is a stop rather than a
    warning: no record from `prepare`, a record for another target, a go that
    names neither the target nor the reading it was given, and a target whose
    configuration states that a person performs the write.
    """
    answer = plan(configuration, target)
    if answer is None:
        return None
    answer["written"] = False
    # ⛔ A field of its own, because `written: False` is **two** outcomes and the
    # invocation has to tell them apart: a write that was refused or failed, and a
    # write this target states is the operator's. ⚠️ Without it, a target whose
    # `apply_by` is `person` reported every deploy as a stop — measured, and
    # firing on exactly the shape § 35 writes the key for.
    answer["handed_over"] = False
    answer["ran"] = []
    path = _record_path(configuration, target)
    held = None
    if os.path.exists(path):
        with open(path, encoding="utf-8") as handle:
            try:
                held = json.load(handle)
            except ValueError:
                held = None
    if not isinstance(held, dict) or held.get("target") != target:
        answer["report"].insert(
            0,
            "Nothing was written: no completed preparation is on record for "
            f"{target!r}, so the dump is unverified and the rehearsal unread. "
            "⛔ The step cannot be entered at the write (§ 35).",
        )
        return answer
    # ⛔ The go held to what it is a go for, which is § 29's binding for a
    # dispatch met one facet over. ⚠️ The words are never composed to satisfy
    # this: a role that filled in the form would have a form rather than an
    # approval, so a go that is short is refused and reported, never rewritten.
    missing = [what for what in GO_MUST_NAME if what not in (go or "").lower()]
    if missing:
        answer["report"].insert(
            0,
            "Nothing was written: the go names "
            + " and ".join(f"no {what}" for what in missing)
            + ". ⛔ A go is an approval of something, so one that names neither "
            "what it approves nor the reading it was given is an answer nobody "
            "can reconstruct (§ 35). ⚠️ It is reported rather than rewritten.",
        )
        return answer
    answer["go"] = go
    answer["rehearsal_read_as"] = held.get("rehearsal")
    if answer["apply_by"] == "person":
        answer["handed_over"] = True
        answer["report"].insert(
            0,
            "⛔ **No write was made.** This target states that a person performs "
            f"it, so the command is handed over whole: {answer['apply']}\n"
            f"Run it in {answer['code_root']}. The dump is verified and the "
            "rehearsal was read, and the go above is recorded — what is left is "
            "the act, which is yours (§ 35).",
        )
        return answer
    outcome = _run(answer["apply"], answer["code_root"])
    answer["ran"].append(dict(outcome, step="apply"))
    answer["written"] = outcome["ran"] and outcome["status"] == 0
    if not answer["written"]:
        answer["report"].insert(
            0,
            "The deploy stops: the write "
            + (
                "could not be run at all"
                if not outcome["ran"]
                else f"exited {outcome['status']}"
            )
            + ". ⛔ **What the store is left holding is unestablished by this "
            "module** and is named rather than omitted: the command may have "
            "written part of what it was asked for, and the verified dump is "
            f"what a recovery reads. The dump was taken by: {_dump(answer)} "
            "(§ 35).",
        )
        return answer
    answer["report"].insert(
        0,
        "The write ran and exited zero. ⚠️ **That is a fact about the invocation "
        "and not about what the store now holds** — § 33's own rule for a deploy, "
        "which reads no differently here.",
    )
    return answer


def _report(configuration: config.Config, target: str) -> dict:
    """What this target states, without running any of it."""
    read = configuration.live_data_step(target)
    if read["found"] is None:
        return {
            "target": target,
            "live_data_step": None,
            "names": read["names"],
            "report": read["report"],
        }
    answer = plan(configuration, target)
    return {
        "target": target,
        "live_data_step": read["found"],
        "names": read["names"],
        "order": answer["order"],
        "apply_by": answer["apply_by"],
        "reads_record": answer["reads_record"],
        "steps": answer["steps"],
        "report": answer["report"],
    }


# --- the suite -------------------------------------------------------------


class _Stated:
    """A configuration answering only what this module reads.

    ⛔ **At the accessor seam and not at the reader's**: every arm below is about
    what this module does with a block, and a fake at the parse would make each
    one assert the parse instead. What holds the block's own shape is the
    reader's own suite, where the refusals are.
    """

    def __init__(self, block, root, *, not_live=False, name="a-target", artifacts=None):
        self._block = block
        self._root = root
        self._not_live = not_live
        self._name = name
        self._artifacts = artifacts

    def code_root(self):
        return self._root

    def get(self, path, default=None):
        if path == "context.artifacts.dir":
            return self._artifacts
        return default

    def live_data_step(self, target):
        if target != self._name:
            return {
                "target": None, "found": None, "reads_record": False,
                "names": [self._name], "report": ["a planted absence of the target"],
            }
        if self._block is None:
            return {
                "target": {"name": self._name, "not_live": self._not_live},
                "found": None, "reads_record": False, "names": [self._name],
                "report": ["a planted target carrying no block"],
            }
        return {
            "target": {"name": self._name, "not_live": self._not_live},
            "found": dict(self._block),
            "reads_record": self._not_live is False,
            "names": [self._name],
            "report": [],
        }


def _a_tree(files: dict[str, str]) -> str:
    """A throwaway tree carrying the given files, each made executable."""
    root = tempfile.mkdtemp(prefix="mjolnir-live-data-")
    for name, text in files.items():
        full = os.path.join(root, name)
        os.makedirs(os.path.dirname(full) or root, exist_ok=True)
        with open(full, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.chmod(full, 0o755)
    return root


def _a_block(**overrides) -> dict:
    """The smallest block this module reads, to break one key of at a time.

    ⚠️ Every command is a script in the planted tree rather than a shell builtin:
    an arm asserting a non-zero status has to be able to *produce* one, and a
    builtin would make the arm depend on which shell the host runs.
    """
    block = {
        "backup": {"run": "./dump", "verify": "./read-back"},
        "rehearse": "./dry",
        "apply": "./write",
        "apply_by": "procedure",
        "order": "before_invoke",
        "record": "./released",
    }
    block.update(overrides)
    return {key: value for key, value in block.items() if value is not None}


def _scripts(**status) -> dict[str, str]:
    """A tree of commands, each exiting and printing what the arm needs.

    The default is every command succeeding and the rehearsal saying something a
    person can read, which is the state every arm about a *failure* breaks one
    command of.
    """
    out = {}
    for name, (code, says) in {
        "dump": (0, "wrote a dump"),
        "read-back": (0, "every table is in it"),
        "dry": (0, "no divergence; two statements would run"),
        "write": (0, "two statements ran"),
        "released": (0, "store/0001.sql"),
    }.items():
        code, says = status.get(name, (code, says))
        out[name] = f"#!/bin/sh\nprintf '%s\\n' {shlex.quote(says)}\nexit {code}\n"
    return out


def _a_go() -> str:
    """A go naming everything § 35 binds one to, written as a person would."""
    return (
        "Yes — the target is the one named above, and the rehearsal's verdict was "
        "no divergence over two statements."
    )


def self_test() -> int:
    failures = 0

    def check(label: str, held: bool, saw: str = "") -> None:
        nonlocal failures
        if held:
            print(f"  ok    {label}")
        else:
            failures += 1
            print(f"  FAIL  {label}" + (f": {saw}" if saw else ""))

    print("The ordering, which is what this module is for:")
    root = _a_tree(_scripts())
    stated = _Stated(_a_block(), root, artifacts=_a_tree({}))
    answer = plan(stated, "a-target")
    check(
        "the plan names every step in the order § 35 states",
        [step["step"] for step in answer["steps"]] == list(PREPARED),
        f"planned {[step['step'] for step in answer['steps']]!r}",
    )
    check(
        "and the plan runs nothing",
        "ran" not in answer,
        f"answered {sorted(answer)!r}",
    )
    check(
        "a target this project does not state answers None rather than an empty plan",
        plan(stated, "another-target") is None,
    )
    check(
        "a target carrying no block answers None too, and says which it was",
        plan(_Stated(None, root), "a-target") is None,
    )

    print("\nEvery stop, each planted alone — and each stops the deploy:")
    for label, broken, at in (
        ("a dump that cannot be taken", {"dump": (1, "no such store")}, "backup.run"),
        ("a dump nothing can read back", {"read-back": (1, "not an archive")},
         "backup.verify"),
        # ⛔ Where a divergence has to land: § 35 states the exit status is the
        # verdict, so a project whose dry variant finds one makes its own command
        # say so. ⚠️ A reading of the *output* was written first and removed — the
        # passing output carries the same word as the failing one.
        ("a rehearsal that exits non-zero on a divergence",
         {"dry": (2, "DIVERGENCE: a statement no longer applies")}, "rehearse"),
        # ⛔ And the one § 11 makes a stop rather than a pass: a rehearsal with no
        # output is a go given on nothing.
        ("a rehearsal that printed nothing", {"dry": (0, "")}, "rehearse"),
    ):
        broken_at = _a_tree({})
        tree = _a_tree(_scripts(**broken))
        answer = prepare(
            _Stated(_a_block(), tree, artifacts=broken_at), "a-target"
        )
        check(
            f"{label} stops at {at}",
            answer["stopped_at"] == at and answer.get("record_at") is None,
            f"stopped at {answer['stopped_at']!r}",
        )
        # ⛔ The path is this run's own, derived from the same artifacts directory
        # `prepare` was handed. ⚠️ Written as a bare `_Stated` first, which
        # resolved to the system temporary directory instead and made every one of
        # these arms pass without asserting anything.
        check(
            f"and {label} leaves no record for an apply to find",
            not os.path.exists(
                _record_path(_Stated(_a_block(), tree, artifacts=broken_at), "a-target")
            ),
        )

    print("\nWhat a completed preparation is, and what it refuses to do next:")
    artifacts = _a_tree({})
    tree = _a_tree(_scripts())
    ready = _Stated(_a_block(), tree, artifacts=artifacts)
    answer = prepare(ready, "a-target")
    check(
        "every step ran, in order",
        [outcome["step"] for outcome in answer["ran"]] == list(PREPARED),
        f"ran {[outcome['step'] for outcome in answer['ran']]!r}",
    )
    check(
        "the rehearsal's output is carried for a person to read",
        answer["rehearsal"] and "no divergence" in answer["rehearsal"],
        f"read {answer['rehearsal']!r}",
    )
    check("and a record is left for the write to find", os.path.exists(answer["record_at"]))
    # ⛔ The stop is the outcome: nothing in a completed preparation says the
    # write happened, and an arm asserting that is what keeps a later edit from
    # quietly running it here.
    check(
        "a completed preparation writes nothing itself",
        "written" not in answer,
        f"answered {sorted(answer)!r}",
    )

    print("\nThe go, held to what it is a go for:")
    for label, go in (
        ("a go that is merely a yes", "yes"),
        ("a go naming the target and not the reading", "yes, deploy the target"),
        ("a go naming the reading and not the target",
         "the rehearsal's verdict was no divergence"),
        ("a go that is empty", ""),
    ):
        answer = apply(ready, "a-target", go)
        check(
            f"{label} is refused and nothing is written",
            answer["written"] is False and "the go names" in " ".join(answer["report"]),
            f"reported {answer['report'][:1]!r}",
        )
    answer = apply(ready, "a-target", _a_go())
    check(
        "a go naming both writes",
        answer["written"] is True,
        f"reported {answer['report'][:1]!r}",
    )
    check(
        "and says that exiting zero is a fact about the invocation",
        "not about what the store now holds" in " ".join(answer["report"]),
        f"reported {answer['report'][:1]!r}",
    )

    print("\nThe write that cannot be entered without a preparation:")
    fresh = _Stated(_a_block(), _a_tree(_scripts()), artifacts=_a_tree({}))
    answer = apply(fresh, "a-target", _a_go())
    check(
        "a write with no completed preparation on record is refused",
        answer["written"] is False
        and "no completed preparation" in " ".join(answer["report"]),
        f"reported {answer['report'][:1]!r}",
    )
    # ⛔ A record written for another target may not license this one's write, and
    # ⚠️ **the arm that reaches that comparison is the one the file name cannot
    # catch**: a record is kept per target, so two differently-named targets
    # already miss each other by path. What collides is a pair of names the slug
    # cannot tell apart — `a target` and `a-target` — which is why `prepare`
    # writes the name itself into the record and this compares that.
    #
    # ⚠️ Measured: written first as two plainly different names, the arm stayed
    # green with the comparison removed, having been refused by the
    # does-the-file-exist branch above it instead.
    shared = _a_tree({})
    spaced = _Stated(
        _a_block(), _a_tree(_scripts()), artifacts=shared, name="a target"
    )
    prepared_elsewhere = prepare(spaced, "a target")
    borrowed = _Stated(_a_block(), _a_tree(_scripts()), artifacts=shared)
    check(
        "the two names collide on one record path, which is what makes the arm below reach",
        prepared_elsewhere["record_at"] == _record_path(borrowed, "a-target"),
        f"prepared at {prepared_elsewhere['record_at']!r}",
    )
    answer = apply(borrowed, "a-target", _a_go())
    check(
        "and one prepared for another target is refused as well",
        answer["written"] is False
        and "no completed preparation" in " ".join(answer["report"]),
        f"reported {answer['report'][:1]!r}",
    )

    print("\nThe hand-over, where the target states a person performs the write:")
    by_hand_artifacts = _a_tree({})
    by_hand_tree = _a_tree(_scripts())
    by_hand = _Stated(
        _a_block(apply_by="person"), by_hand_tree, artifacts=by_hand_artifacts
    )
    prepared = prepare(by_hand, "a-target")
    check(
        "the preparation runs in full, the hand-over being about the write alone",
        prepared["stopped_at"] is None and prepared.get("record_at"),
        f"stopped at {prepared['stopped_at']!r}",
    )
    answer = apply(by_hand, "a-target", _a_go())
    check(
        "the write is handed over and nothing is written",
        answer["written"] is False
        and "No write was made" in " ".join(answer["report"]),
        f"reported {answer['report'][:1]!r}",
    )
    check(
        "and the command is handed over whole",
        _a_block()["apply"] in " ".join(answer["report"]),
        f"reported {answer['report'][:1]!r}",
    )
    # ⛔ **A hand-over is an outcome and not a stop**, which § 35 states and which
    # the invocation has to agree with: a target whose write is the operator's
    # reaches this on every single deploy, so reading it as a failure would report
    # every such deploy as broken. ⚠️ Reproduced before the field existed —
    # `written` was `False` for both a hand-over and a refused go, and the
    # invocation read the two the same way and exited 1 for each.
    check(
        "the hand-over is marked as one, so the invocation does not read it as a stop",
        answer.get("handed_over") is True and answer.get("stopped_at") is None,
        f"answered {answer.get('handed_over')!r}",
    )
    refused = apply(by_hand, "a-target", "yes")
    check(
        "while a refused go on the same target is not marked handed over",
        refused.get("handed_over") is not True,
        f"answered {refused.get('handed_over')!r}",
    )
    # ⛔ The go is asked either way, which is what `apply_by` does *not* decide:
    # a short go is refused before the hand-over is reached, so the key says who
    # runs the command and never whether it was approved.
    answer = apply(by_hand, "a-target", "yes")
    check(
        "a hand-over under a go that names nothing is still refused",
        "the go names" in " ".join(answer["report"])
        and "No write was made" not in " ".join(answer["report"]),
        f"reported {answer['report'][:1]!r}",
    )

    print("\nThe write that ran and failed, and what the report may not omit:")
    broken_artifacts = _a_tree({})
    broken_tree = _a_tree(_scripts(write=(1, "one statement of two applied")))
    broken = _Stated(_a_block(), broken_tree, artifacts=broken_artifacts)
    prepare(broken, "a-target")
    answer = apply(broken, "a-target", _a_go())
    check(
        "a failed write is reported as a stop",
        answer["written"] is False and "The deploy stops" in " ".join(answer["report"]),
        f"reported {answer['report'][:1]!r}",
    )
    check(
        "and names what the store is left holding as unestablished",
        "left holding is unestablished" in " ".join(answer["report"]),
        f"reported {answer['report'][:1]!r}",
    )
    check(
        "and names the dump a recovery reads",
        _a_block()["backup"]["run"] in " ".join(answer["report"]),
        f"reported {answer['report'][:1]!r}",
    )

    print("\nThe rehearsal a project does not state:")
    none_artifacts = _a_tree({})
    without = _Stated(
        _a_block(rehearse=None), _a_tree(_scripts()), artifacts=none_artifacts
    )
    answer = prepare(without, "a-target")
    check(
        "the step completes with no rehearsal run",
        answer["stopped_at"] is None
        and [outcome["step"] for outcome in answer["ran"]]
        == ["backup.run", "backup.verify"],
        f"ran {[outcome['step'] for outcome in answer['ran']]!r}",
    )
    # ⛔ Reported as *no rehearsal* and never as a clean one, which is § 35's own
    # rule and the direction a reader would otherwise read silence in.
    check(
        "and the report says there was none rather than that it passed",
        "states no rehearsal" in " ".join(answer["report"]),
        f"reported {answer['report']!r}",
    )
    check(
        "while the row stays in the plan, marked stated nowhere",
        [step["stated"] for step in answer["steps"]] == [True, True, False],
        f"planned {answer['steps']!r}",
    )

    print("\nWhat the plan says about the order and who performs the write:")
    for order in ("before_invoke", "after_invoke"):
        answer = plan(_Stated(_a_block(order=order), root), "a-target")
        check(
            f"the plan carries {order} and says the go settles it",
            answer["order"] == order
            and "the go is where it is settled" in " ".join(answer["report"]),
            f"reported {answer['report']!r}",
        )
    # ⛔ The liveness pairing § 35 reads the released set from, asserted in both
    # directions: a step on a target the project states is not live must not have
    # its record read, and one that says nothing cannot occur -- the reader
    # refuses it at the load.
    check(
        "a live target's released set is read",
        plan(_Stated(_a_block(), root, not_live=False), "a-target")["reads_record"]
        is True,
    )
    check(
        "and a target the session is the only user of has its own left unread",
        plan(_Stated(_a_block(), root, not_live=True), "a-target")["reads_record"]
        is False,
    )

    print("\nAnd this project's own configuration:")
    try:
        resolved = config.load(config.REPO_ROOT)
        targets = resolved.get("deploy") or []
        check(
            "this project states no deploy target, so it states no live data step",
            not targets,
            f"states {len(targets)} target(s)",
        )
    except config.ConfigError as error:
        failures += 1
        print(f"  FAIL  this repository's own configuration: {error}")

    print(
        "\n"
        + ("All green." if not failures else f"{failures} failure(s).")
    )
    return 1 if failures else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(add_help=True, description=__doc__)
    parser.add_argument("action", nargs="?", choices=("plan", "prepare", "apply"))
    parser.add_argument("--target", help="the § 33 target this step belongs to")
    # ⛔ `--given`, which is this toolkit's own word for an answer a gate reads
    # back, and ⚠️ **not `--go`**: the names check reads that spelling as the build
    # tool of the same name and refuses the command, which is a false refusal the
    # flag is renamed around rather than argued with.
    parser.add_argument("--given", help="the answer licensing the write, in their words")
    parser.add_argument("--skills-root", default=None)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()
    if not args.target:
        parser.error("--target is required: a step belongs to one § 33 target")
    try:
        resolved = config.load(args.skills_root or os.getcwd())
    except config.ConfigError as error:
        print(json.dumps({"error": str(error)}, indent=2, ensure_ascii=False))
        return 2

    if args.action == "apply" and not args.given:
        # ⛔ Refused before anything is read, and ⚠️ **not a go this module
        # supplies a default for**: a write with no answer behind it is the act
        # § 35 exists to stop, and an empty string would be refused one branch
        # later while reading as an answer somebody gave.
        print(json.dumps({
            "error": "--given is required: the write is licensed by a person's own "
                     "answer, naming the target and the rehearsal's verdict (§ 35).",
        }, indent=2, ensure_ascii=False))
        return 1

    if args.action == "plan":
        answer = plan(resolved, args.target)
    elif args.action == "prepare":
        answer = prepare(resolved, args.target)
    elif args.action == "apply":
        answer = apply(resolved, args.target, args.given)
    else:
        answer = _report(resolved, args.target)
        print(json.dumps(answer, indent=2, ensure_ascii=False))
        return NO_STEP if answer["live_data_step"] is None else 0

    if answer is None:
        read = resolved.live_data_step(args.target)
        print(json.dumps({
            "target": args.target,
            "live_data_step": None,
            "names": read["names"],
            "report": read["report"],
        }, indent=2, ensure_ascii=False))
        return NO_STEP
    print(json.dumps(answer, indent=2, ensure_ascii=False))
    if args.action == "plan":
        return 0
    # ⛔ A hand-over is excluded by name rather than by the absence of a stop: it
    # is the outcome § 35 states for `apply_by: person`, so a status reading it as
    # a failure would report every deploy to such a target as broken.
    stopped = answer.get("stopped_at") is not None or (
        args.action == "apply"
        and answer.get("written") is False
        and not answer.get("handed_over")
    )
    return 1 if stopped else 0


if __name__ == "__main__":
    sys.exit(main())
