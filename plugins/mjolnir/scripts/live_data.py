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
    live_data.py plan --target NAME [--step S]       the ordering, nothing run
    live_data.py prepare --target NAME [--step S] [--side SIDE]
                                                     the dump, its reading, the
                                                     rehearsal — and then a stop
    live_data.py apply --target NAME [--step S] --given TEXT
                                                     the write, under that go
    live_data.py --self-test                         assert every answer against
                                                     planted trees and commands

⚠️ `--step` names one step of a target that lists several, and is refused on a
target with one; `--side` prepares only the phases `sides` and `order` place on
that side of the invocation (§ 35).

Exit status, and ⛔ **four values rather than two**: 0 the answer was produced,
1 the step stopped and names where, 2 the configuration could not be read or does
not answer to the step named, 3 this target states no live data step. ⚠️ The last
is § 11's rule at a command line — *no step* collapsed into 0 reads as a step that
ran, and into 1 as a deploy that failed.
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
PREPARED = ("backup.run", "backup.verify", "preview", "rehearse")

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
# a write against the other -- ⛔ **and per step where the target lists several**,
# for the same reason one level down: each write has its own go after its own
# evidence (§ 35), so one step's reading may never license another's write.
RECORD = "live-data-step-{target}.json"
RECORD_OF_STEP = "live-data-step-{target}--{step}.json"


def _phase(step: str) -> str:
    """Which phase of § 35's sequence a prepared command belongs to.

    ⛔ Read off the command's own key rather than listed beside `PREPARED`, which
    would be a second statement of that list: `backup.run` and `backup.verify`
    are the backup's, and the dump's reading-back falls where the dump does — a
    verification on the other side of the deploy from its dump would be reading
    a store the new code may already have written.
    """
    return step.split(".", 1)[0]

def _preview_at(block: dict, root: str) -> str | None:
    """The file a step's preview writes to, resolved against the code root, or `None`.

    ⛔ `None` is the preview printing its listing, which the go then carries whole;
    a path is where the listing is read from instead (§ 35).
    """
    preview = block.get("preview")
    at = preview.get("at") if isinstance(preview, dict) else None
    if not isinstance(at, str) or not at.strip():
        return None
    return at if os.path.isabs(at) else os.path.join(root, at)


def _read_preview(outcome: dict, at: str | None) -> tuple[str | None, str]:
    """What a preview that ran showed, and why it is empty where it is.

    ⛔ Empty is a failure and never a clean answer (§ 35): a preview with nothing
    pending says so, and a go given on nothing is given on nothing.
    """
    if at is None:
        return (outcome["output"] or None), "printed nothing"
    if not os.path.isfile(at):
        return None, f"wrote no file at {at}"
    with open(at, encoding="utf-8", errors="replace") as handle:
        text = handle.read().strip()
    return (text or None), f"left {at} empty"


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


class _Unaddressed(Exception):
    """A step asked for that the target does not answer to, said out loud.

    ⛔ Never resolved to the first step: a target listing several is addressed by
    name or not at all, and one with a single step is addressed without one.
    """


def _slug(target: str) -> str:
    """A target's name as a file name, with nothing of the name invented.

    ⚠️ Lossy by construction — two names differing only in punctuation collapse —
    which is why `prepare` writes the name itself into the record and `apply`
    compares that rather than the path it opened.
    """
    return "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in target)


def _record_path(configuration: config.Config, target: str, step: str | None = None) -> str:
    where = configuration.get("context.artifacts.dir") or tempfile.gettempdir()
    name = (
        RECORD.format(target=_slug(target))
        if step is None
        else RECORD_OF_STEP.format(target=_slug(target), step=_slug(step))
    )
    return os.path.join(os.path.expandvars(where), name)


def _held(path: str) -> dict | None:
    """A record on disk, or `None` where there is none or it does not parse."""
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as handle:
        try:
            held = json.load(handle)
        except ValueError:
            return None
    return held if isinstance(held, dict) else None


def _keep(path: str, record: dict) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(record, handle)


def _the_sides() -> list[str]:
    """§ 35's sides, earlier first -- the order its alternation is written in."""
    return config.facts_for("deploy.live_data_step.order")


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

    ⚠️ A `preview` or `rehearse` the project does not state is **in the list** and
    marked as stated-nowhere rather than dropped: § 35 makes an omitted one a step
    reported as absent, and a list that silently lost the row would be a plan a
    reader counts the steps of and gets the wrong answer.
    """
    out = []
    for name in PREPARED:
        if name in config.LIVE_DATA_OPTIONAL:
            command = config.live_data_command(block, name)
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


def _which(read: dict, step: str | None) -> dict:
    """The one step of a target an invocation addresses, or `_Unaddressed`."""
    names = [block.get("name") for block in read["steps"]]
    if not read.get("listed"):
        if step is not None:
            raise _Unaddressed(
                f"The target states one live data step and no names, so --step "
                f"{step!r} addresses nothing; a single step is addressed without "
                "one (§ 35)."
            )
        return read["steps"][0]
    if step is None:
        raise _Unaddressed(
            "The target lists several live data steps, so the one meant is named "
            f"with --step: {', '.join(names)}. ⛔ Never the first by default — each "
            "write has its own go after its own evidence (§ 35)."
        )
    for block in read["steps"]:
        if block.get("name") == step:
            return block
    raise _Unaddressed(
        f"The target lists no live data step named {step!r}; it lists "
        f"{', '.join(names)} (§ 35)."
    )


def _sides_of(block: dict) -> dict:
    """The side every phase of one step falls on: the accessor's, or derived."""
    sides = block.get("sides")
    if isinstance(sides, dict) and set(sides) >= {"backup", "rehearse", "apply"}:
        return dict(sides)
    return config.live_data_sides(block)


def _plan_of(configuration: config.Config, target: str, read: dict, block: dict) -> dict:
    """The whole ordering of one step, with nothing run and nothing written."""
    entry = read["target"]
    sides = _sides_of(block)
    report = list(read["report"])
    split = len({side for side in sides.values() if side is not None}) > 1
    report.append(
        f"The order stated is {block['order']!r}, which is where this step falls "
        "against § 33's invocation"
        + (
            "; `sides` places its phases apart — "
            + ", ".join(f"{phase} {side}" for phase, side in sides.items() if side)
            if split
            else ""
        )
        + ". ⛔ The configured value is what this role proposes and the go is "
        "where it is settled: whether the write belongs before the image depends "
        "on what is pending, and detecting that is the project's own (§ 35). ⚠️ "
        "What the go may not settle is a write ahead of its own dump or "
        "rehearsal, which the write refuses whatever was asked."
    )
    if block["apply_by"] == "person":
        report.append(
            "This target states that a person performs the write, so the command "
            "is handed over and ⛔ **no write is made by this role** (§ 35). The "
            "go is still asked: `apply_by` says who runs the command, never "
            "whether it is approved."
        )
    if config.live_data_command(block, "preview") is None:
        report.append(
            "This target states no preview, so the go shows nothing of the writes "
            "this deploy would make and ⛔ says no preview is stated rather than "
            "that nothing is pending (§ 35)."
        )
    if not any(step["step"] == "rehearse" and step["stated"] for step in _steps(block)):
        report.append(
            "This target states no rehearsal, which § 35 makes a key a block may "
            "omit. ⛔ Reported as **no rehearsal** rather than as a clean one, and "
            "the go is asked with that said."
        )
    go_must_name = list(GO_MUST_NAME)
    if block.get("name") is not None:
        go_must_name.append(f"the step's name ({block['name']})")
    return {
        "target": target,
        "step": block.get("name"),
        "not_live": entry.get("not_live"),
        "code_root": configuration.code_root,
        "order": block["order"],
        "sides": sides,
        "apply_by": block["apply_by"],
        "steps": _steps(block),
        "preview_at": _preview_at(block, configuration.code_root),
        "apply": block["apply"],
        "record": block["record"],
        # ⛔ Read from live targets only, which is § 35's liveness pairing and is
        # the accessor's answer rather than a second reading here.
        "reads_record": read["reads_record"],
        "go_must_name": go_must_name,
        "report": report,
    }


def plan(configuration: config.Config, target: str, step: str | None = None) -> dict | None:
    """The whole ordering, with nothing run and nothing written, or `None`.

    `None` is the target's stated absence (§ 35) and never an empty plan: this
    target writes no live data, so there is no step rather than a step with
    nothing in it.

    ⚠️ **A target listing several steps, asked about without one, answers every
    step's plan in the order listed** — the preflight's reading, taken before the
    deploy is confirmed — while the commands that run something are addressed to
    one step by name (§ 35).
    """
    read = configuration.live_data_step(target)
    if read["found"] is None:
        return None
    if read.get("listed") and step is None:
        plans = [_plan_of(configuration, target, read, block) for block in read["steps"]]
        return {
            "target": target,
            "listed": True,
            "plans": plans,
            "report": [
                "This target lists "
                f"{len(plans)} live data steps — "
                + ", ".join(str(each["step"]) for each in plans)
                + " — performed in that order on each side of the invocation, "
                "each with its own dump, its own reading and its own go (§ 35)."
            ],
        }
    return _plan_of(configuration, target, read, _which(read, step))


def _position(block: dict, index: int, sides: list[str]) -> tuple[int, int]:
    """Where a step's own sequence starts in a deploy: its backup's side, then its place.

    ⛔ The derivation the reset below rests on. A deploy performs, on each side of
    the invocation in turn, the steps of the list in the order stated, and a
    step's sequence starts at its dump -- so a step whose start falls later than
    this one's has not started in this deploy, and a reading on disk for it is an
    earlier deploy's.
    """
    return sides.index(_sides_of(block)["backup"]), index


def _clear_later(configuration: config.Config, target: str, read: dict, block: dict) -> None:
    """Drop the readings of every step whose sequence starts after this one's.

    ⛔ **So a report of the writes made reads this deploy rather than the last
    one** (§ 35): a record left by an earlier deploy for a step that has not yet
    started here would otherwise read as a write already made.
    """
    if not read.get("listed"):
        return
    sides = _the_sides()
    blocks = read["steps"]
    here = _position(block, blocks.index(block), sides)
    for index, other in enumerate(blocks):
        if _position(other, index, sides) > here:
            path = _record_path(configuration, target, other.get("name"))
            if os.path.exists(path):
                os.remove(path)


def _writes(configuration: config.Config, target: str, read: dict) -> list[dict]:
    """Every step of the target by name, as written, handed over or not made.

    ⛔ Read from what this deploy performed, which the reset in `prepare` keeps
    the records to (§ 35).
    """
    out = []
    for block in read["steps"]:
        name = block.get("name")
        held = _held(_record_path(configuration, target, name))
        if held is None or held.get("target") != target or held.get("step") != name:
            held = {}
        state = (
            "written" if held.get("written")
            else "handed over" if held.get("handed_over")
            else "not made"
        )
        out.append({
            "step": name,
            "state": state,
            "prepared": list(held.get("verified") or []),
        })
    return out


def _writes_line(writes: list[dict]) -> str:
    """The writes made and not made, in one sentence a report can carry."""
    parts = []
    for state in ("written", "handed over", "not made"):
        named = [str(each["step"]) for each in writes if each["state"] == state]
        parts.append(f"{state}: {', '.join(named) if named else 'none'}")
    return "Of this target's live data steps — " + "; ".join(parts) + " (§ 35)."


def _on_this_side(phases: list[dict], sides: dict, side: str | None) -> list[dict]:
    """The prepared commands that fall on the side asked for, or all of them."""
    if side is None:
        return phases
    return [each for each in phases if sides[_phase(each["step"])] == side]


def prepare(
    configuration: config.Config,
    target: str,
    step: str | None = None,
    side: str | None = None,
) -> dict | None:
    """The dump, the dump read back, the rehearsal — and then a stop.

    ⛔ **The stop is the outcome rather than a failure**: the go is the person's
    and the rehearsal's output is what it is given on, so a pass that ran these
    three and then wrote would have approved on their behalf (§ 35).

    ⛔ **And the dump runs whether or not anything is pending.** What a deploy
    turns out to write against a store is not fully known until it has run, and a
    dump taken afterwards records the damage rather than the state before it.

    ⚠️ **`side` runs only the phases placed on that side of the invocation**,
    which is how a step whose dump falls before the deploy and whose rehearsal
    falls after it is prepared in two calls. Omitted, every phase runs — which is
    the single block exactly as it always was, and is refused for a step whose
    phases fall on both sides.
    """
    read = configuration.live_data_step(target)
    if read["found"] is None:
        return None
    block = _which(read, step)
    answer = _plan_of(configuration, target, read, block)
    root = answer["code_root"]
    sides = answer["sides"]
    name = block.get("name")
    path = _record_path(configuration, target, name)
    answer["ran"] = []
    answer["stopped_at"] = None
    answer["preview"] = None
    answer["rehearsal"] = None
    answer["side"] = side
    stated = [each for each in answer["steps"] if each["stated"]]
    if side is None and len({sides[_phase(each["step"])] for each in stated}) > 1:
        answer["stopped_at"] = stated[0]["step"]
        answer["report"].insert(
            0,
            "Nothing ran: this step's phases fall on both sides of the invocation, "
            "so it is prepared one side at a time with --side, never all at once — "
            "running them together would take the later phases on the wrong side "
            "of the deploy (§ 35).",
        )
        return answer
    here = _on_this_side(stated, sides, side)
    if not here:
        answer["nothing_on_side"] = True
        answer["report"].insert(
            0,
            f"No prepared phase of this step falls {side}, so nothing ran and the "
            "reading on record is untouched (§ 35).",
        )
        return answer
    starts_here = any(_phase(each["step"]) == "backup" for each in here)
    if starts_here:
        # ⛔ A fresh reading: whatever an earlier deploy left for this step, or for
        # a step that starts after it, is not this deploy's evidence.
        if os.path.exists(path):
            os.remove(path)
        _clear_later(configuration, target, read, block)
        record = {"target": target, "step": name, "order": answer["order"],
                  "sides": sides, "preview": None, "rehearsal": None, "verified": []}
    else:
        # ⛔ A later side of a sequence that began earlier: what it follows has to
        # be on record, or this side would be a rehearsal with no dump behind it.
        record = _held(path)
        if (
            record is None
            or record.get("target") != target
            or record.get("step") != name
            or not {"backup.run", "backup.verify"} <= set(record.get("verified") or [])
        ):
            answer["stopped_at"] = here[0]["step"]
            answer["writes"] = _writes(configuration, target, read)
            answer["report"].insert(
                0,
                f"The deploy stops: {here[0]['step']} falls {side}, after a dump that "
                "is not on record for this step, so it would follow nothing. ⛔ The "
                "dump is taken and read back first, on its own side (§ 35). "
                + _writes_line(answer["writes"]),
            )
            return answer
    for each in here:
        if each["step"] == "preview" and answer["preview_at"] and os.path.isfile(
            answer["preview_at"]
        ):
            # ⛔ An earlier run's listing is not this one's: cleared before the
            # command runs, so a preview that wrote nothing reads as empty rather
            # than as the last deploy's pending writes (§ 35).
            os.remove(answer["preview_at"])
        outcome = _run(each["command"], root)
        answer["ran"].append(dict(outcome, step=each["step"]))
        if not outcome["ran"] or outcome["status"] != 0:
            answer["stopped_at"] = each["step"]
            answer["writes"] = _writes(configuration, target, read)
            answer["report"].insert(
                0,
                f"The deploy stops: {each['step']} "
                + (
                    "could not be run at all, so it is reported unestablished "
                    "rather than failed"
                    if not outcome["ran"]
                    else f"exited {outcome['status']}"
                )
                + ". ⛔ The deploy and not the step (§ 35), and nothing after "
                "this ran."
                + (" " + _writes_line(answer["writes"]) if read.get("listed") else ""),
            )
            return answer
        if each["step"] == "preview":
            shown, why = _read_preview(outcome, answer["preview_at"])
            answer["preview"] = shown
            if shown is None:
                answer["stopped_at"] = each["step"]
                answer["writes"] = _writes(configuration, target, read)
                answer["report"].insert(
                    0,
                    f"The deploy stops: the preview {why}, so the go would show "
                    "nothing of the writes it approves. ⛔ Empty is a failed preview "
                    "and not a clean one (§ 35), and nothing after this ran."
                    + (" " + _writes_line(answer["writes"]) if read.get("listed") else ""),
                )
                return answer
        if each["step"] == "rehearse":
            answer["rehearsal"] = outcome["output"] or _UNREAD
            if not outcome["output"]:
                answer["stopped_at"] = each["step"]
                answer["writes"] = _writes(configuration, target, read)
                answer["report"].insert(
                    0,
                    "The deploy stops: the rehearsal produced no output, so there "
                    "is nothing for a person to read and the go would be given on "
                    "nothing. ⛔ Reported unread rather than clean (§ 11)."
                    + (" " + _writes_line(answer["writes"]) if read.get("listed") else ""),
                )
                return answer
    # ⛔ Written only once every command on this side came back, so a record on
    # disk is evidence that what it lists completed rather than that it started.
    record["verified"] = list(record.get("verified") or []) + [
        outcome["step"] for outcome in answer["ran"]
    ]
    for kept in ("preview", "rehearsal"):
        if answer[kept] is not None:
            record[kept] = answer[kept]
        else:
            answer[kept] = record.get(kept)
    _keep(path, record)
    answer["record_at"] = path
    owed = [each["step"] for each in stated if each["step"] not in record["verified"]]
    answer["report"].insert(
        0,
        (
            "The dump is taken and read back"
            + (
                (
                    f", the preview of the pending writes is at {answer['preview_at']}"
                    if answer["preview_at"]
                    else ", the preview of the pending writes is above, whole"
                )
                + " -- ⛔ a preview and not a rehearsal"
                if answer["preview"]
                else ", this target states no preview"
            )
            + (
                ", the rehearsal ran and its output is above"
                if answer["rehearsal"]
                else " and this target states no rehearsal"
            )
            + ". ⛔ The step stops here: the write is the person's act, and the go is "
            "asked on what is above rather than before any of it existed (§ 35)."
        )
        if not owed
        else (
            # ⛔ Whatever is owed is named, the preview as much as the rehearsal: a
            # report saying only that the dump was taken reads as a step ready
            # for its go.
            "The dump is taken and read back; "
            + ", ".join(owed)
            + " falls on the other side of the invocation and is still owed, so no go "
            "is asked yet — a write is never reached before its own preview or "
            "rehearsal (§ 35)."
        ),
    )
    return answer


def apply(
    configuration: config.Config,
    target: str,
    go: str,
    step: str | None = None,
) -> dict | None:
    """The write, under a go that names what it is a go for. `None` where none.

    ⛔ **Four refusals before anything runs**, and each is a stop rather than a
    warning: no record from `prepare`, a record for another target or step or
    one missing a phase this write follows, a go that names neither the target
    nor the reading it was given (nor the step, on a listed one), and a target
    whose configuration states that a person performs the write.
    """
    read = configuration.live_data_step(target)
    if read["found"] is None:
        return None
    block = _which(read, step)
    answer = _plan_of(configuration, target, read, block)
    name = block.get("name")
    answer["written"] = False
    # ⛔ A field of its own, because `written: False` is **two** outcomes and the
    # invocation has to tell them apart: a write that was refused or failed, and a
    # write this target states is the operator's. ⚠️ Without it, a target whose
    # `apply_by` is `person` reported every deploy as a stop — measured, and
    # firing on exactly the shape § 35 writes the key for.
    answer["handed_over"] = False
    answer["ran"] = []
    path = _record_path(configuration, target, name)
    held = _held(path)
    # ⛔ **What this write follows has to be on record, whatever the placement**:
    # the dump taken and read back, and the rehearsal where one is stated. A
    # deploy that took the phases out of order, or a go that overruled `order`
    # into a placement that would, reaches no write (§ 35).
    owed = [
        each["step"] for each in answer["steps"]
        if each["stated"]
        and each["step"] not in set((held or {}).get("verified") or [])
    ]
    if (
        held is None
        or held.get("target") != target
        or held.get("step") != name
        or owed
    ):
        answer["writes"] = _writes(configuration, target, read)
        answer["report"].insert(
            0,
            "Nothing was written: no completed preparation is on record for "
            f"{target!r}"
            + (f", step {name!r}" if name is not None else "")
            + (
                f" — {', '.join(owed)} is not on record"
                if held is not None and held.get("target") == target
                and held.get("step") == name
                else ""
            )
            + ", so the dump is unverified or the rehearsal unread. "
            "⛔ The step cannot be entered at the write (§ 35)."
            + (" " + _writes_line(answer["writes"]) if read.get("listed") else ""),
        )
        return answer
    # ⛔ The go held to what it is a go for, which is § 29's binding for a
    # dispatch met one facet over. ⚠️ The words are never composed to satisfy
    # this: a role that filled in the form would have a form rather than an
    # approval, so a go that is short is refused and reported, never rewritten.
    said = (go or "").lower()
    missing = [what for what in GO_MUST_NAME if what not in said]
    # ⛔ On a listed step the go names that step too: each write has its own go,
    # and one naming another step, or none, licenses nothing (§ 35).
    if name is not None and name.lower() not in said:
        missing.append(f"step {name!r}")
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
    answer["preview_shown"] = held.get("preview")
    answer["rehearsal_read_as"] = held.get("rehearsal")
    if answer["apply_by"] == "person":
        answer["handed_over"] = True
        _keep(path, dict(held, handed_over=True))
        answer["writes"] = _writes(configuration, target, read)
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
    if answer["written"]:
        _keep(path, dict(held, written=True))
    answer["writes"] = _writes(configuration, target, read)
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
            "(§ 35)."
            + (" " + _writes_line(answer["writes"]) if read.get("listed") else ""),
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
    if answer.get("listed"):
        return {
            "target": target,
            "live_data_step": read["found"],
            "names": read["names"],
            "plans": answer["plans"],
            "report": answer["report"],
        }
    return {
        "target": target,
        "live_data_step": read["found"],
        "names": read["names"],
        "order": answer["order"],
        "sides": answer["sides"],
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

    # ⛔ A property, because the reader's is one: a fake answering a call where
    # the reader answers an attribute let every arm here pass while the
    # invocation raised on the first real configuration it was given.
    @property
    def code_root(self):
        return self._root

    def get(self, path, default=None):
        if path == "context.artifacts.dir":
            return self._artifacts
        return default

    def live_data_step(self, target):
        if target != self._name:
            return {
                "target": None, "found": None, "steps": [], "reads_record": False,
                "names": [self._name], "report": ["a planted absence of the target"],
            }
        if self._block is None:
            return {
                "target": {"name": self._name, "not_live": self._not_live},
                "found": None, "steps": [], "reads_record": False,
                "names": [self._name],
                "report": ["a planted target carrying no block"],
            }
        # ⛔ The steps are the accessor's own derivation, called rather than
        # restated: a fake that placed the phases itself would let the arms below
        # assert its placement instead of the one the loader holds.
        listed = isinstance(self._block, list)
        blocks = self._block if listed else [self._block]
        return {
            "target": {"name": self._name, "not_live": self._not_live},
            "found": self._block,
            "steps": [
                dict(block, name=block.get("name"), sides=config.live_data_sides(block))
                for block in blocks
            ],
            "listed": listed,
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
        "preview": (0, "pending: store/0002.sql, store/0003.sql"),
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
        "every step the block states ran, in order",
        [outcome["step"] for outcome in answer["ran"]]
        == ["backup.run", "backup.verify", "rehearse"],
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
        [step["stated"] for step in answer["steps"]] == [True, True, False, False],
        f"planned {answer['steps']!r}",
    )

    print("\nThe preview of the pending writes, which is never a rehearsal:")
    with_preview = _Stated(
        _a_block(preview={"run": "./preview"}), _a_tree(_scripts()), artifacts=_a_tree({})
    )
    answer = prepare(with_preview, "a-target")
    check(
        "the preview runs after the verified dump and before the rehearsal",
        [outcome["step"] for outcome in answer["ran"]]
        == ["backup.run", "backup.verify", "preview", "rehearse"],
        f"ran {[outcome['step'] for outcome in answer['ran']]!r}",
    )
    check(
        "its output is carried whole for the go, beside the rehearsal's and apart from it",
        answer["preview"] == "pending: store/0002.sql, store/0003.sql"
        and "no divergence" in (answer["rehearsal"] or "")
        and "pending" not in (answer["rehearsal"] or ""),
        f"preview {answer['preview']!r}, rehearsal {answer['rehearsal']!r}",
    )
    answer = apply(with_preview, "a-target", _a_go())
    check(
        "and the write made under the go carries the preview it was shown",
        answer["written"] is True
        and answer.get("preview_shown") == "pending: store/0002.sql, store/0003.sql",
        f"reported {answer['report'][:1]!r}",
    )
    # ⛔ The target the key was written for: a preview and no rehearsal. The
    # listing is shown and the step is still reported as having no rehearsal.
    alone = _Stated(
        _a_block(preview={"run": "./preview"}, rehearse=None),
        _a_tree(_scripts()), artifacts=_a_tree({}),
    )
    answer = prepare(alone, "a-target")
    check(
        "a preview with no rehearsal is reported as no rehearsal, the preview beside it",
        answer["stopped_at"] is None
        and answer["rehearsal"] is None
        and answer["preview"]
        and "states no rehearsal" in answer["report"][0]
        and "a preview and not a rehearsal" in answer["report"][0],
        f"reported {answer['report'][:1]!r}",
    )
    at_path = _a_tree(dict(_scripts(), **{
        "preview-to-file": "#!/bin/sh\necho 'pending: store/0002.sql' > pending.txt\n",
    }))
    answer = prepare(
        _Stated(_a_block(preview={"run": "./preview-to-file", "at": "pending.txt"}),
                at_path, artifacts=_a_tree({})),
        "a-target",
    )
    check(
        "a preview written to a stated path is read back there, and the go names the path",
        answer["stopped_at"] is None
        and answer["preview_at"] == os.path.join(at_path, "pending.txt")
        and answer["preview"] == "pending: store/0002.sql"
        and os.path.join(at_path, "pending.txt") in answer["report"][0],
        f"reported {answer['report'][:1]!r}",
    )
    stale = _a_tree(dict(_scripts(), **{"pending.txt": "an earlier deploy's listing"}))
    answer = prepare(
        _Stated(_a_block(preview={"run": "./preview", "at": "pending.txt"}),
                stale, artifacts=_a_tree({})),
        "a-target",
    )
    check(
        "a file an earlier run left at the stated path is not read as this run's preview",
        answer["stopped_at"] == "preview" and answer["preview"] is None,
        f"read {answer['preview']!r}",
    )
    for label, broken, overrides in (
        ("a preview that exits non-zero", {"preview": (1, "no such store")},
         {"preview": {"run": "./preview"}}),
        ("a preview that printed nothing", {"preview": (0, "")},
         {"preview": {"run": "./preview"}}),
        ("a preview that wrote no file at its stated path", {},
         {"preview": {"run": "./preview", "at": "never-written.txt"}}),
        ("a preview that left its stated path empty", {},
         {"preview": {"run": "./preview", "at": "empty.txt"}}),
    ):
        tree = _a_tree(dict(_scripts(**broken), **{"empty.txt": ""}))
        stated_here = _Stated(_a_block(**overrides), tree, artifacts=_a_tree({}))
        answer = prepare(stated_here, "a-target")
        check(
            f"{label} stops the deploy at the preview, with no rehearsal run",
            answer["stopped_at"] == "preview"
            and "rehearse" not in [outcome["step"] for outcome in answer["ran"]]
            and answer.get("record_at") is None,
            f"stopped at {answer['stopped_at']!r}",
        )
        check(
            f"and after {label} the write is refused",
            apply(stated_here, "a-target", _a_go())["written"] is False,
        )
    # ⛔ The placement rule for the new phase: a preview owed on the later side
    # holds the write however good the go.
    before, after = _the_sides()
    owed = _Stated(
        _a_block(preview={"run": "./preview"}, rehearse=None, order=before,
                 sides={"preview": after, "apply": after}),
        _a_tree(_scripts()), artifacts=_a_tree({}),
    )
    answer = prepare(owed, "a-target", side=before)
    check(
        "the earlier side names the preview still owed and asks no go, with no rehearsal stated",
        "preview falls on the other side" in answer["report"][0]
        and "no go is asked yet" in answer["report"][0],
        f"reported {answer['report'][:1]!r}",
    )
    answer = apply(owed, "a-target", _a_go())
    check(
        "the write is refused while its preview is still owed",
        answer["written"] is False and "preview is not on record" in answer["report"][0],
        f"reported {answer['report'][:1]!r}",
    )
    prepare(owed, "a-target", side=after)
    check(
        "and made once the later side has shown it",
        apply(owed, "a-target", _a_go())["written"] is True,
    )
    check(
        "a step stating no preview says so in its plan rather than that nothing is pending",
        "states no preview" in " ".join(plan(ready, "a-target")["report"]),
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

    print("\nA step whose phases fall on both sides of the invocation:")
    before, after = _the_sides()
    split_block = _a_block(order=before, sides={"rehearse": after, "apply": after})
    split = _Stated(split_block, _a_tree(_scripts()), artifacts=_a_tree({}))
    answer = prepare(split, "a-target")
    check(
        "prepared with no side named, nothing runs — the later phases would land on "
        "the wrong side of the deploy",
        answer["ran"] == [] and answer["stopped_at"] is not None
        and answer.get("record_at") is None,
        f"ran {[outcome['step'] for outcome in answer['ran']]!r}",
    )
    answer = prepare(split, "a-target", side=before)
    check(
        "the earlier side takes the dump and reads it back, and runs no rehearsal",
        [outcome["step"] for outcome in answer["ran"]] == ["backup.run", "backup.verify"],
        f"ran {[outcome['step'] for outcome in answer['ran']]!r}",
    )
    # ⛔ The rule § 35 states for every placement: the write follows its own
    # rehearsal, so with the rehearsal still owed on the later side the write is
    # refused however good the go.
    answer = apply(split, "a-target", _a_go())
    check(
        "the write is refused while its rehearsal is still owed",
        answer["written"] is False and answer["ran"] == []
        and "rehearse is not on record" in " ".join(answer["report"]),
        f"reported {answer['report'][:1]!r}",
    )
    answer = prepare(split, "a-target", side=after)
    check(
        "the later side runs the rehearsal alone, after the dump on record",
        [outcome["step"] for outcome in answer["ran"]] == ["rehearse"]
        and "no divergence" in (answer["rehearsal"] or ""),
        f"ran {[outcome['step'] for outcome in answer['ran']]!r}",
    )
    answer = apply(split, "a-target", _a_go())
    check(
        "and then the write is made, under its go",
        answer["written"] is True,
        f"reported {answer['report'][:1]!r}",
    )
    # ⚠️ The later side reached with no dump on record — a deploy that skipped
    # the earlier side, or an earlier deploy's reading for another target.
    orphan = _Stated(split_block, _a_tree(_scripts()), artifacts=_a_tree({}))
    answer = prepare(orphan, "a-target", side=after)
    check(
        "a later side with no dump on record stops before running anything",
        answer["ran"] == [] and answer["stopped_at"] == "rehearse"
        and "not on record" in " ".join(answer["report"]),
        f"reported {answer['report'][:1]!r}",
    )
    # ⚠️ And a record that is this step's but carries no dump on it — what a
    # hand-edited or truncated file reads as. Planted directly, there being no
    # sequence of this module's own calls that writes one.
    _keep(_record_path(orphan, "a-target"),
          {"target": "a-target", "step": None, "verified": [], "rehearsal": None})
    answer = prepare(orphan, "a-target", side=after)
    check(
        "a record of this step with no dump on it stops the later side as well",
        answer["ran"] == [] and answer["stopped_at"] == "rehearse",
        f"ran {[outcome['step'] for outcome in answer['ran']]!r}",
    )
    answer = prepare(_Stated(_a_block(order=before), _a_tree(_scripts()),
                             artifacts=_a_tree({})), "a-target", side=after)
    check(
        "a side no phase of the step falls on runs nothing and is no stop",
        answer.get("nothing_on_side") is True and answer["stopped_at"] is None,
        f"answered {answer.get('nothing_on_side')!r}",
    )

    print("\nSeveral steps on one target, each addressed by name:")
    listed_tree = _a_tree(dict(
        _scripts(), **{"write-fails": "#!/bin/sh\necho 'half of it ran'\nexit 1\n"}
    ))
    listed_artifacts = _a_tree({})
    listed = _Stated(
        [
            dict(_a_block(order=before), name="first"),
            dict(_a_block(order=after), name="second"),
            dict(_a_block(order=after, apply="./write-fails"), name="third"),
        ],
        listed_tree, artifacts=listed_artifacts,
    )
    answer = plan(listed, "a-target")
    check(
        "the preflight's plan names every step in the order listed",
        [each["step"] for each in answer["plans"]] == ["first", "second", "third"],
        f"planned {answer.get('plans')!r}",
    )
    for label, call in (
        ("a step asked for by no name on a listed target is refused",
         lambda: prepare(listed, "a-target")),
        ("a step the target does not list is refused",
         lambda: prepare(listed, "a-target", step="fourth")),
        ("a name on a target with one step is refused",
         lambda: prepare(ready, "a-target", step="first")),
    ):
        try:
            call()
            refused = False
        except _Unaddressed:
            refused = True
        check(label, refused)

    def a_go_for(step: str) -> str:
        return _a_go() + f" This is the go for {step}."

    prepare(listed, "a-target", step="first", side=before)
    # ⛔ One step's reading may never license another's write: each write has its
    # own go after its own evidence (§ 35).
    answer = apply(listed, "a-target", a_go_for("second"), step="second")
    check(
        "one step's preparation does not license another step's write",
        answer["written"] is False and answer["ran"] == []
        and "no completed preparation" in " ".join(answer["report"]),
        f"reported {answer['report'][:1]!r}",
    )
    # ⚠️ The arm above is refused by the record's path alone, the two names
    # slugging apart. What reaches the comparison of the step written *inside*
    # the record is a pair the slug cannot tell apart, which is the per-target
    # arm's own lesson one level down.
    twins = _Stated(
        [dict(_a_block(), name="a step"), dict(_a_block(), name="a-step")],
        _a_tree(_scripts()), artifacts=_a_tree({}),
    )
    prepared_twin = prepare(twins, "a-target", step="a step")
    check(
        "two step names collide on one record path, which is what makes the arm below reach",
        prepared_twin["record_at"] == _record_path(twins, "a-target", "a-step"),
        f"prepared at {prepared_twin['record_at']!r}",
    )
    answer = apply(twins, "a-target", a_go_for("a-step"), step="a-step")
    check(
        "and the reading taken for one is refused for the other",
        answer["written"] is False and answer["ran"] == [],
        f"reported {answer['report'][:1]!r}",
    )
    answer = apply(listed, "a-target", _a_go(), step="first")
    check(
        "a go that does not name its step is refused, on a listed target",
        answer["written"] is False and "step 'first'" in " ".join(answer["report"]),
        f"reported {answer['report'][:1]!r}",
    )
    answer = apply(listed, "a-target", a_go_for("second"), step="first")
    check(
        "and so is a go naming another step",
        answer["written"] is False and "step 'first'" in " ".join(answer["report"]),
        f"reported {answer['report'][:1]!r}",
    )
    answer = apply(listed, "a-target", a_go_for("first"), step="first")
    check("a go naming its own step writes", answer["written"] is True,
          f"reported {answer['report'][:1]!r}")
    # The invocation, then the later side.
    prepare(listed, "a-target", step="second", side=after)
    apply(listed, "a-target", a_go_for("second"), step="second")
    prepare(listed, "a-target", step="third", side=after)
    answer = apply(listed, "a-target", a_go_for("third"), step="third")
    states = {each["step"]: each["state"] for each in answer.get("writes") or []}
    check(
        "a write failing after the invocation names the writes made and not made",
        answer["written"] is False
        and states == {"first": "written", "second": "written", "third": "not made"}
        and "written: first, second" in " ".join(answer["report"])
        and "not made: third" in " ".join(answer["report"]),
        f"reported {states!r} / {answer['report'][:1]!r}",
    )
    # ⛔ And what the next deploy reads is its own: the first step's fresh dump
    # drops the readings every later-starting step left, so they read not made
    # rather than as the last deploy's writes.
    prepare(listed, "a-target", step="first", side=before)
    states = {each["step"]: each["state"] for each in _writes(
        listed, "a-target", listed.live_data_step("a-target"))}
    check(
        "a new deploy's first dump drops the readings an earlier deploy left",
        states == {"first": "not made", "second": "not made", "third": "not made"},
        f"read {states!r}",
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
    parser.add_argument(
        "--step", default=None,
        help="the step's name, where the target lists several (§ 35)",
    )
    parser.add_argument(
        "--side", default=None,
        help="prepare only the phases placed on this side of the invocation (§ 35)",
    )
    parser.add_argument("--skills-root", default=None)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()
    if not args.target:
        parser.error("--target is required: a step belongs to one § 33 target")
    if args.side is not None and args.side not in _the_sides():
        parser.error(f"--side is one of {' | '.join(_the_sides())} (§ 35)")
    if args.side is not None and args.action != "prepare":
        parser.error("--side is read by prepare alone: the write's side is the go's (§ 35)")
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

    try:
        if args.action == "plan":
            answer = plan(resolved, args.target, args.step)
        elif args.action == "prepare":
            answer = prepare(resolved, args.target, args.step, args.side)
        elif args.action == "apply":
            answer = apply(resolved, args.target, args.given, args.step)
        else:
            answer = None
    except _Unaddressed as error:
        # ⛔ The configuration does not answer to the step named, which is a
        # reading that could not be taken rather than a step that stopped.
        print(json.dumps({"error": str(error)}, indent=2, ensure_ascii=False))
        return 2
    if args.action is None:
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
