#!/usr/bin/env python3
"""Refuse an act on the strength of a record, and hold a place on what contends.

The surface states what a hook may refuse and what it reads to refuse it -- see
`schema.md § 7 -> What a hook refuses, and the record it reads`, the subsection
beside it that fixes which direction a guard fails in, the one after that which
states the lease, and the one above them all which says what a hook does in a
project that states no configuration. This script is the carrier for each:

    guard     a `PreToolUse` answer: refuse a merge with no recorded answer,
              refuse a local run the host's own runs have already made, then
              hold a place on whatever the call puts at stake -- and nothing at
              all where the project states no configuration
    release   a `PostToolUse`, `Stop`, `SessionEnd` or `SubagentStop` answer:
              give back the places this session is holding -- and, at two of
              those four, report whether this tree's branch has fallen behind
              its base
    record    write the recorded answer a guard reads onto a change
    held      report what is held right now, and by what

⛔ **Nothing here judges the work.** A guard reads a record somebody else wrote,
a count somebody else's command printed and runs somebody else's host made;
where any of them is missing it says so in those words. The two directions it
may fail in are the surface's and not this file's choice, and both are exercised
below -- the merge refusing on what it could not establish and the local run
proceeding on it.

⚠️ **One arm here refuses nothing at all**, and that is the surface's statement
rather than this file's restraint: a branch behind its base is a state somebody
else's merge produced, answered at two exit events where no call is in hand to
hold. `schema.md § 7 -> A branch that has fallen behind its base` is its rule.

⚠️ **The third refusal is an arm here rather than a carrier of its own**, which
is what keeps the ordering in one place: a sibling script denying a call after
this one has taken a place leaves that place behind, a denied call reaching no
exit event at all. `schema.md § 18` is its rule, and the facet it reads is § 2's.

⚠️ **What this cannot hold is the live half**: whether the place a guard took was
actually given back, on a machine nobody is watching. The `ttl` is what bounds
that, and the residue is stated in `docs/single-source-of-truth.md` § The
enforcement half rather than restated here.

Usage:
    enforce.py guard                        a hook payload on stdin
    enforce.py release                      a hook payload on stdin
    enforce.py record --change O/R#N --question Q --given TEXT --by WHO
    enforce.py held   [--skills-root R]
    enforce.py --self-test
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# --- where the rules live --------------------------------------------------

SURFACE = Path(__file__).resolve().parent.parent / "config" / "schema.md"

# The subsections this script is the carrier for, by the anchors the code host
# would give their headings. Grammar: a heading may be reworded without touching
# this file only if its anchor survives, which is the bargain every citation of
# the surface already makes.
ARM_ANCHORS = {
    "unconfigured": "a-hook-in-a-project-that-states-no-configuration",
    "record": "what-a-hook-refuses-and-the-record-it-reads",
    "direction": "which-direction-a-guard-fails-in",
    "lease": "a-lease-on-an-exclusive-resource-and-the-exit-paths-that-release-it",
    "already_run": "18-the-guard-on-a-command-the-host-has-already-run",
    "guardable": "what-may-be-guarded-and-the-two-ways-a-refusal-stands-down",
    "behind": ("a-branch-that-has-fallen-behind-its-base-and-the-two-points-it-is-"
               "reported-at"),
}

RECORD_CITATION = "schema § 7 → What a hook refuses, and the record it reads"
LEASE_CITATION = ("schema § 7 → A lease on an exclusive resource, and the exit paths that "
                  "release it")
ALREADY_RUN_CITATION = "schema § 18 → The guard on a command the host has already run"
GUARDED_CITATION = ("schema § 18 → What may be guarded, and the two ways a refusal stands "
                    "down")
BEHIND_CITATION = ("schema § 7 → A branch that has fallen behind its base, and the two points "
                   "it is reported at")

# § 18's four answers. ⛔ The last three all proceed and are still reported apart:
# their remedies differ, which is the whole reason the third exists -- a reader
# told *nothing has run* on a conflicted change is sent to run a suite whose
# result cannot land.
# What every answer of this arm is headed by. ⚠️ The guard's subject rather than
# its answer: one of the four answers below is spelled *already run* too, and a
# report headed by the same words twice reads as a stutter rather than as a
# verdict -- measured on this repository's own first live refusal.
REPORT_PREFIX = "The host's own runs"

ALREADY_RUN = "already run"
NOTHING_HAS_RUN = "nothing has run"
NOTHING_CAN_RUN = "nothing can run"
UNESTABLISHED = "unestablished"

# What a project's own probe prints where the host can run these jobs, and ⛔ the
# only string that satisfies the operational condition through that key: anything
# else proceeds, which is the fail-open direction arriving at somebody else's
# command.
OPERATIONAL = "operational"

# What the host reports for a run that never became one. ⚠️ A conclusion and not
# a status: the two cases § 2 names -- a suspended billing account and a run
# awaiting an action -- surface here rather than as an absent run, which is why
# condition 3 stands apart from the conclusion at all.
NOT_OPERATIONAL = {"startup_failure", "action_required", "stale"}

# A run or a job the host has not finished with. ⛔ Read as *the time is being
# spent now*, which is the duplicate this guard exists for -- and it is the one
# state where no step having executed is not an answer about the run: § 2's third
# precondition is a test for a run that is *over*, and applying it to one still
# going would wave through exactly the call that duplicates live work.
#
# ⚠️ Open rather than closed, deliberately: a status this set does not name is
# read as finished, and a finished run is then held to its steps. The vocabulary
# is the host's (§ 2), so a status nobody here has seen errs towards the check
# rather than past it.
IN_FLIGHT = {"queued", "in_progress", "requested", "waiting", "pending"}

# The words that end one command inside a call, so what follows begins another in
# command position. ⛔ Read as tokens rather than searched for as text: a quoted
# argument carrying one of them is an argument.
SEPARATORS = {"&&", "||", "|", ";", "&", "(", ")", "{", "}", "!", "\n"}

# The carrier, and every event an arm here answers. ⛔ Held rather than assumed:
# an event that stopped being registered leaves the arm dead in every session,
# and a dead guard reports green on every act it was supposed to refuse.
CARRIER = Path(__file__).resolve().parent.parent / "hooks" / "hooks.json"
GUARD_EVENT = "PreToolUse"

# The events that give a place back, and what each of them covers. ⚠️ The keys
# are the harness's event names and the values are what the sweep is scoped to --
# the one call that just ended, or every place the session is holding.
RELEASE_EVENTS = {
    "PostToolUse": "call",
    "Stop": "session",
    "SessionEnd": "session",
    "SubagentStop": "session",
}

# The one tool whose calls reach anything a project would guard. A place is held
# by a command, and a command arrives through this tool.
GUARDED_TOOL = "Bash"

# § 7's two points a branch is measured against its base at, and ⛔ **two of the
# four events above rather than all of them**: a session ending is a report
# nobody is left to act on, and a subagent stopping is not this tree's turn
# ending. The second entry is further narrowed to a call that merged, which is
# read with the merge guard's own grammar rather than a second one.
TURN_ENDED = "Stop"
CALL_FINISHED = "PostToolUse"
BEHIND_EVENTS = (TURN_ENDED, CALL_FINISHED)

# § 7's three answers for that reading. ⛔ Only the middle one carries a figure,
# and the figure may be absent on it: a base this tree does not hold yet is
# behind by an amount no local read can establish, which is still not level.
# ⚠️ `UNESTABLISHED` is § 18's own name reused rather than a second spelling of
# it, both subsections meaning the same thing by it.
LEVEL = "level"
BEHIND = "behind"

# What every answer of this arm is headed by, the way `REPORT_PREFIX` heads the
# already-run arm's: a report that opens with its subject is one a reader can
# tell from the lease sweep's in the same message.
BEHIND_PREFIX = "This branch against its base"

# ⛔ **Bounded against the carrier's own registered budget rather than picked**,
# and the arithmetic is the whole of the reason: this arm reaches the network
# twice at worst -- once to derive the base where the clone has no record of the
# remote's default, once for that base's head -- so two of these have to fit
# inside the budget the release hook is registered with, with the three local
# reads and the interpreter's own start inside what is left over. A read that
# hangs then costs itself rather than the hook, which is what the bound is for.
BEHIND_TIMEOUT = 3

# --- the record a guard reads ----------------------------------------------
#
# The form is the surface's: one comment on the change, keyed by the repository
# and the change's own number, stating the question, the answer as it came back,
# who answered and when. It is a visible table rather than a hidden marker, for
# two reasons: the boundary carrier reports an HTML comment as a span that
# renders as nothing, so a record written as one would be surfaced as a finding
# every time a role ingested the change; and a record a person cannot read on the
# change is a record only a machine can audit.

RECORD_MARKER = "**mjolnir · recorded answer**"
RECORD_COLUMNS = ["question", "answer", "answered by", "answered at"]

# The question a merge is held on, and where the whole vocabulary comes from.
# ⛔ The name is read out of the surface's own alternation rather than carried
# here: a role recording `read-by-a-person` would satisfy nothing, and a guard
# matching a spelling this file invented would be the second statement of a
# vocabulary the surface already publishes.
#
# ⚠️ The spelling below is the one the guard matches, and `--self-test` asserts
# the surface still states it. That is the bargain every citation of the surface
# makes: one name, held by a run rather than by whoever edits either file.
MERGE_QUESTION = "read_by_a_person"
QUESTION_VOCABULARY = "recorded_answer.question"

# A change named the way the record is keyed. ⛔ The repository is part of the
# address and not context: a bare number names a different change in every
# repository the route carries.
CHANGE_ADDRESS = re.compile(r"^(?P<slug>[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)#(?P<number>\d+)$")

# A cell's own pipe, escaped on the way in so an answer carrying one does not
# become two columns. Read back by the inverse, so the answer a guard reports is
# the answer somebody gave.
PIPE = "|"
PIPE_ESCAPED = "\\|"

# --- what a merge call looks like ------------------------------------------
#
# ⛔ Two spellings, because both are in use: the host client's own subcommand and
# the same act through its raw API arm. A grammar that knew only the first would
# leave the second unguarded, which is a guard that reads as installed.
#
# ⚠️ Matched on the parsed words rather than on the text, for the reason the
# boundary carrier's outward arm is: a flag that takes a value has to be skipped
# with its value, and a path that happens to contain the word `merge` is not a
# merge.
MERGE_API = re.compile(r"^/?repos/(?P<slug>[^/]+/[^/]+)/pulls/(?P<number>\d+)/merge$")
WRITE_METHODS = {"PUT", "POST", "PATCH"}

# A change named as a web address, which is the other form the client accepts.
PULL_URL = re.compile(r"/pull/(?P<number>\d+)")

# ⛔ The flags of each subcommand that take a **separate** value, which have to
# be skipped with their value before anything else is read as the change. The
# same measurement the boundary carrier records for `git -C`: dropping every word
# that starts with a dash and reading the next one makes a flag's value look like
# a positional, and here that value is `--repo`'s — so a merge naming no change
# would have been checked against the repository slug read as a change.
MERGE_VALUE_FLAGS = {"--repo", "-R", "--body", "-b", "--body-file", "-F", "--subject", "-t",
                     "--match-head-commit", "--author-email", "-A"}
API_VALUE_FLAGS = {"--method", "-X", "--field", "-F", "--raw-field", "-f", "--input",
                   "--header", "-H", "--jq", "-q", "--template", "--hostname", "--cache"}

# ⛔ The raw arm needs the method read, because the same path is a read and a
# write. With no method stated the client sends a read unless a field is passed,
# in which case it sends a write -- so a grammar that fired on the path alone
# would refuse the call that *asks* whether a change is merged, which is one of
# the reads the finishing role makes before merging anything.
METHOD_FLAGS = ("--method", "-X")
FIELD_FLAGS = ("-f", "--raw-field", "-F", "--field", "--input")

# How long a command of somebody else's may run before its answer is no longer
# worth waiting for. ⚠️ Bounded well inside the carrier's own timeout: a probe
# that hangs must cost the call a known delay rather than the whole hook.
PROBE_TIMEOUT = 5
HOST_TIMEOUT = 8

# ⚠️ Tighter than the merge guard's, because this arm may make three reads where
# that one makes two and runs on every call rather than on a merge: the whole of
# what it may cost has to stay inside the carrier's own timeout, and a guard that
# makes a session slow is a guard somebody removes.
ALREADY_RUN_TIMEOUT = 5

# How much of a command a report quotes.
SHOWN = 160


# --- the store --------------------------------------------------------------
#
# ⛔ Derived, never configured. A lease is not an artifact a role hands the next
# one (§ 11's store), and nothing reads it to decide what to do next: it is this
# guard's own scratch, and a key for it would be one more thing an adopting
# project has to get right before anything is held.
#
# ⚠️ Under the system temp directory **on purpose**, which is the one place § 11
# warns a store does not survive a reboot. For a lease that is the wanted
# behaviour and not a cost: a reboot releases the resource too, so a lease that
# outlived one would hold a place on something that is no longer running.


def store_for(skills_root: str | Path) -> Path:
    """Where this project's leases live.

    Keyed by a digest of the skills root rather than by its path, so two projects
    on one machine never share a place and nothing about either of them is
    written into a directory name.
    """
    root = str(Path(skills_root).resolve())
    digest = hashlib.sha256(root.encode("utf-8")).hexdigest()[:16]
    return Path(tempfile.gettempdir()) / "mjolnir-leases" / digest


def _lease_files(store: Path) -> list[Path]:
    try:
        return sorted(p for p in store.iterdir() if p.suffix == ".json")
    except OSError:
        return []


def _read_lease(path: Path) -> dict | None:
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return loaded if isinstance(loaded, dict) else None


def live_leases(store: Path, now: float) -> list[tuple[Path, dict]]:
    """Every lease still counting, with the expired ones removed on the way past.

    ⛔ Expiry is applied on every read rather than by anything sweeping on a
    schedule. There is no process here that runs when no session is running, so a
    lease that only a sweep could remove would be a place held until somebody
    happened to take the next one.
    """
    found = []
    for path in _lease_files(store):
        lease = _read_lease(path)
        if lease is None:
            # ⚠️ A file this cannot parse is removed rather than counted: it was
            # written by this arm or by nothing, and counting it would hold a
            # place against a record no release could ever match.
            path.unlink(missing_ok=True)
            continue
        if now - float(lease.get("taken") or 0) >= float(lease.get("ttl") or 0):
            path.unlink(missing_ok=True)
            continue
        found.append((path, lease))
    return found


# --- the resources a project states ----------------------------------------


def resources(config) -> list[dict]:
    """`branch_model.exclusive_resources`, as the configuration states it.

    ⛔ Read through the shared reader and never parsed here, which is also what
    makes the empty case free: a project that states `[]` reaches this with an
    empty list and every arm below answers nothing.
    """
    stated = config.get("branch_model.exclusive_resources") or []
    return [entry for entry in stated if isinstance(entry, dict)]


def claims(entry: dict, command: str) -> bool:
    """Does this call put that resource at stake?

    ⚠️ The pattern is searched rather than matched whole: a project states what a
    claiming command looks like, and a command is a line with flags and paths
    around whatever the project named.
    """
    pattern = str(entry.get("claimed_by") or "")
    if not pattern:
        return False
    try:
        return bool(re.search(pattern, command))
    except re.error:
        # ⛔ The reader refuses a pattern that does not compile, so reaching this
        # means the guard is running against a configuration nothing validated.
        # Not claiming is the open direction, which is the one the surface states
        # for a call.
        return False


def probe_count(entry: dict, root: str | Path, run=None) -> tuple[int, str | None]:
    """How many of this resource are held right now, or why that is unestablished.

    `probe: null` is a stated absence and not a count of zero: it returns `0`
    with no complaint, because the leases are then the whole of the count.
    """
    command = entry.get("probe")
    if command is None:
        return 0, None
    runner = run if run is not None else _run_in_shell
    try:
        code, out = runner(str(command), root, PROBE_TIMEOUT)
    except Exception as error:  # noqa: BLE001 -- any failure is a named absence
        return 0, f"{type(error).__name__} while asking how many are held"
    if code != 0:
        return 0, "the probe exited non-zero, so how many are held is unestablished"
    first = out.strip().splitlines()[0].strip() if out.strip() else ""
    if not re.fullmatch(r"\d+", first):
        return 0, (f"the probe printed {first[:40]!r} rather than a count, so how many are "
                   "held is unestablished")
    return int(first), None


def _run_in_shell(command: str, root: str | Path, timeout: int) -> tuple[int, str]:
    """Run a command the project stated, whole, from the skills root.

    ⚠️ Through a shell because the command is stated whole and the procedure
    supplies no part of it: a project's probe may be a pipeline, and splitting it
    here would be this file deciding what shape somebody else's command has.
    """
    proc = subprocess.run(
        command, shell=True, cwd=str(root), capture_output=True, text=True, timeout=timeout,
    )
    return proc.returncode, proc.stdout


# --- holding a place -------------------------------------------------------


def _call_key(session: str, command: str) -> str:
    """What holds a place under `subject: call`.

    Derived from the session and the command rather than from a call id, because
    the event that releases a place carries the command and no id. ⚠️ Two
    identical commands in flight in one session therefore share one key, which is
    stated rather than discovered: the second takes no second place, and the
    first release gives the place back.
    """
    return hashlib.sha256(f"{session}\0{command}".encode("utf-8")).hexdigest()[:16]


def _tree_key(cwd: str) -> str:
    """What holds a place under `subject: tree`.

    The working directory the call was made from, resolved. ⚠️ Not the git
    worktree root, which would cost a subprocess on a path this arm reaches for
    every claiming call -- and two sessions in one tree share a directory as
    surely as they share a tree.
    """
    try:
        return str(Path(cwd or ".").resolve())
    except OSError:
        return str(cwd or ".")


def occupancy(entry: dict, leases: list[tuple[Path, dict]], counted: int) -> tuple[int, set[str]]:
    """What is compared against `cap`: the resource's own count plus the young leases.

    ⛔ A sum and never a maximum of the two. Measured on one project: a build
    started outside the loop holds the resource with no lease, while one just
    launched holds a lease the resource does not report yet, and reading the two
    as a maximum let a third through a cap of two.

    ⛔ Distinct keys rather than lease files, which is what `subject` decides: two
    sessions in one tree share one place, and two calls each hold their own.
    """
    keys = {
        str(lease.get("key"))
        for _path, lease in leases
        if lease.get("resource") == entry.get("name")
    }
    return counted + len(keys), keys


def take(entry: dict, store: Path, key: str, session: str, command: str,
         background: bool, counted: int, now: float) -> tuple[Path | None, bool, int, int]:
    """Take a place, or report that there is none.

    Returns (the lease this call wrote or None, taken, occupancy as it stood, cap)
    — the path because a caller taking places on several resources has to be able
    to give back the ones it took when a later one refuses.

    ⛔ The place is written **before** the count is read back, which is the same
    test-and-set the claim on a work item takes and for the same reason: counting
    and then writing lets two sessions each read the last place as free. A lease
    that puts the resource over its cap is removed again, so the bias is towards
    refusing rather than towards two holders.
    """
    cap = int(entry.get("cap") or 1)
    held = live_leases(store, now)
    standing, keys = occupancy(entry, held, counted)
    if key in keys:
        # The place is already this key's -- the `tree` case, where a second call
        # from the same tree takes no second place. ⛔ No path comes back, because
        # this call did not write the lease and must not give back a place a
        # sibling session is holding.
        return None, True, standing, cap

    store.mkdir(parents=True, exist_ok=True)
    lease = {
        "resource": entry.get("name"),
        "subject": entry.get("subject"),
        "key": key,
        "session": session,
        "command": command[:SHOWN],
        "background": bool(background),
        "taken": now,
        "ttl": int(entry.get("ttl") or 1),
    }
    path = store / f"{hashlib.sha256(json.dumps(lease, sort_keys=True).encode()).hexdigest()[:24]}.json"
    try:
        with open(path, "x", encoding="utf-8") as handle:
            json.dump(lease, handle)
    except FileExistsError:
        return None, True, standing, cap
    except OSError:
        # ⛔ A store that cannot be written is a guard holding nothing, which is
        # the open direction for a call: the answer says so rather than refusing.
        return None, True, standing, cap

    standing, _keys = occupancy(entry, live_leases(store, now), counted)
    if standing > cap:
        path.unlink(missing_ok=True)
        return None, False, standing, cap
    return path, True, standing, cap


def release(store: Path, session: str, scope: str, command: str, now: float) -> list[dict]:
    """Give back what this session holds, and report what was given back.

    ⛔ A backgrounded call's place is skipped deliberately, by the surface's own
    table: the call itself finishes at launch, so a sweep that released it would
    hand the place back while the work ran. Expiry is the only release for one.
    """
    given = []
    for path, lease in live_leases(store, now):
        if lease.get("session") != session:
            continue
        if lease.get("background"):
            continue
        if scope == "call" and lease.get("command") != command[:SHOWN]:
            continue
        path.unlink(missing_ok=True)
        given.append(lease)
    return given


# --- reading the record ----------------------------------------------------


def record_body(question: str, given: str, by: str, at: str) -> str:
    """The comment a recorded answer is, in the form the surface states."""
    cells = [
        question,
        given.replace(PIPE, PIPE_ESCAPED),
        by.replace(PIPE, PIPE_ESCAPED),
        at,
    ]
    return "\n".join([
        RECORD_MARKER,
        "",
        "| " + " | ".join(RECORD_COLUMNS) + " |",
        "|" + "---|" * len(RECORD_COLUMNS),
        "| " + " | ".join(cells) + " |",
        "",
        f"Read by a guard rather than by a reader ({RECORD_CITATION}).",
    ])


def answers_in(text: str) -> list[dict]:
    """Every recorded answer in one comment body.

    ⛔ The marker is required. A table of four columns is an ordinary shape in a
    change's conversation, and reading one as a record would let a guard be
    satisfied by somebody's notes.
    """
    if RECORD_MARKER not in text:
        return []
    found = []
    for line in text.splitlines():
        if not line.strip().startswith(PIPE):
            continue
        cells = [
            cell.strip().replace(PIPE_ESCAPED, PIPE)
            for cell in re.split(r"(?<!\\)\|", line.strip().strip(PIPE))
        ]
        if len(cells) != len(RECORD_COLUMNS):
            continue
        if cells == RECORD_COLUMNS or set("".join(cells)) <= set("-: "):
            continue
        found.append(dict(zip(RECORD_COLUMNS, cells)))
    return found


def recorded_answer(comments: list[str], question: str) -> dict | None:
    """The last answer recorded for this question, or None.

    ⛔ The last and not the first: an answer recorded twice is a question asked
    again, and the standing answer is the one given most recently -- the same
    reading `§ An artifact states what is true now` gives every artifact.
    """
    answered = [
        answer
        for text in comments
        for answer in answers_in(text)
        if answer["question"] == question and answer["answer"] and answer["answered by"]
    ]
    return answered[-1] if answered else None


def host_comments(slug: str, number: str, run=None) -> tuple[list[str], str | None]:
    """Every comment on a change, or why they could not be read."""
    runner = run if run is not None else _run_host
    try:
        code, out = runner(
            ["api", "--paginate", f"repos/{slug}/issues/{number}/comments"], HOST_TIMEOUT
        )
    except Exception as error:  # noqa: BLE001 -- any failure is a named absence
        return [], f"{type(error).__name__} while reading the change's own comments"
    if code != 0:
        return [], "the host did not answer for this change's comments"
    bodies = []
    # ⚠️ A paginated read prints one array per page, so the text is read as a
    # stream of values rather than as one document.
    decoder = json.JSONDecoder()
    index, text = 0, out.strip()
    while index < len(text):
        try:
            value, index = decoder.raw_decode(text, index)
        except json.JSONDecodeError:
            return [], "the host's answer about this change's comments did not parse"
        while index < len(text) and text[index] in " \t\r\n":
            index += 1
        for item in value if isinstance(value, list) else []:
            if isinstance(item, dict) and isinstance(item.get("body"), str):
                bodies.append(item["body"])
    return bodies, None


def _run_host(args: list[str], timeout: int) -> tuple[int, str]:
    proc = subprocess.run(
        ["gh", *args], capture_output=True, text=True, timeout=timeout,
    )
    return proc.returncode, proc.stdout


# --- which call is a merge -------------------------------------------------


def _words(command: str) -> list[str]:
    try:
        return shlex.split(command, comments=True)
    except ValueError:
        return re.findall(r"[^\s;&|()]+", command)


def _flag_value(words: list[str], *names: str) -> str | None:
    for index, word in enumerate(words):
        flag, _, inline = word.partition("=")
        if flag not in names:
            continue
        value = inline or (words[index + 1] if index + 1 < len(words) else "")
        if value and not value.startswith("-"):
            return value
    return None


def _positionals(words: list[str], value_flags: set[str]) -> list[str]:
    """The words that are arguments rather than flags or the values of flags."""
    out, expecting = [], False
    for word in words:
        if expecting:
            expecting = False
            continue
        if word.startswith("-"):
            flag, sign, _value = word.partition("=")
            if not sign and flag in value_flags:
                expecting = True
            continue
        out.append(word)
    return out


def merge_target(
    command: str, fallback_slug: str | None
) -> tuple[str | None, str | None, str | None] | None:
    """(repository, number, the change as the command named it), else None.

    The number is `None` where the command names no change -- the client's own
    form for *the change on this branch* -- and then the third member is `None`
    too, which is what tells the caller it may resolve one.

    ⛔ **A change named in a form this cannot read comes back with the number
    `None` and the name as written**, and the caller refuses it rather than
    resolving the branch's. A command merging one change, checked against another
    change's record, is the one way this guard could pass an act nobody answered
    for.
    """
    words = _words(command)
    if not words:
        return None
    for index, word in enumerate(words):
        if os.path.basename(word) != "gh":
            continue
        after = words[index + 1:]
        slug = _flag_value(after, "--repo", "-R") or fallback_slug
        merging = _positionals(after, MERGE_VALUE_FLAGS)
        if len(merging) >= 2 and merging[0] == "pr" and merging[1] == "merge":
            named = merging[2] if len(merging) > 2 else None
            if named is None:
                return slug, None, None
            if named.isdigit():
                return slug, named, named
            found = PULL_URL.search(named)
            return slug, (found.group("number") if found else None), named
        raw = _positionals(after, API_VALUE_FLAGS)
        if raw and raw[0] == "api":
            method = _flag_value(after, *METHOD_FLAGS)
            writes = (
                method.upper() in WRITE_METHODS if method
                else any(w.partition("=")[0] in FIELD_FLAGS for w in after)
            )
            for candidate in raw[1:]:
                found = MERGE_API.match(candidate)
                if found and writes:
                    return found.group("slug"), found.group("number"), candidate
    return None


def change_on_this_branch(slug: str, run=None) -> tuple[str | None, str | None]:
    """The number of the change the current branch has open, or why it is unknown."""
    runner = run if run is not None else _run_host
    try:
        code, out = runner(["pr", "view", "--repo", slug, "--json", "number"], HOST_TIMEOUT)
    except Exception as error:  # noqa: BLE001 -- any failure is a named absence
        return None, f"{type(error).__name__} while resolving which change this branch has open"
    if code != 0:
        return None, "the host did not say which change this branch has open"
    try:
        loaded = json.loads(out or "{}")
    except json.JSONDecodeError:
        return None, "the host's answer about this branch's change did not parse"
    number = (loaded or {}).get("number")
    if not isinstance(number, int):
        return None, "the host's answer named no change number"
    return str(number), None


# --- the guard -------------------------------------------------------------


def _deny(reason: str) -> dict:
    return {
        "hookSpecificOutput": {
            "hookEventName": GUARD_EVENT,
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def merge_guard(config, command: str, *, host=None) -> dict:
    """Refuse a merge where the review question has no recorded answer.

    ⛔ Refused rather than waved through where the record could not be read at
    all, which is the surface's fail direction for an act that cannot be undone.
    """
    target = merge_target(command, config.get("host.repo"))
    if target is None:
        return {}
    slug, number, named = target
    if number is None and named is not None:
        return _deny(
            f"This command merges a change named {named!r}, which is not a form this guard can "
            f"resolve to a number. ⛔ The branch's own change is not read instead: a merge "
            f"checked against another change's record is an act nobody answered for "
            f"({RECORD_CITATION}). Name the change by its number."
        )
    if not slug:
        return _deny(
            "This command merges a change and names no repository, and the configuration "
            f"states none either. A recorded answer is keyed by the repository and the "
            f"change's number ({RECORD_CITATION}), so there is nothing to resolve it against: "
            "name the repository on the command."
        )
    unread = None
    if number is None:
        number, unread = change_on_this_branch(slug, run=host)
    if number is None:
        return _deny(
            f"This command merges a change in {slug} and the change itself could not be "
            f"established: {unread}. ⛔ A merge is not undone, so an unestablished record is "
            f"refused rather than read as a pass ({RECORD_CITATION}). Name the change's own "
            "number on the command, or re-run once the host answers."
        )
    comments, unread = host_comments(slug, number, run=host)
    if unread:
        return _deny(
            f"This command merges {slug}#{number} and whether the review question has an "
            f"answer could not be established: {unread}. ⛔ Refused rather than allowed: a "
            f"merge is not undone, and an unread record is not an empty one "
            f"({RECORD_CITATION})."
        )
    answer = recorded_answer(comments, MERGE_QUESTION)
    if answer:
        return {}
    # ⛔ The remedy is named as a command somebody can run, not as a description of
    # one: a refusal whose remedy has to be worked out is a refusal somebody gets
    # past by editing the guard. The path is this file's own, so it names whichever
    # copy of the plugin the session actually loaded.
    return _deny(
        f"This command merges {slug}#{number}, and no answer to `{MERGE_QUESTION}` is "
        f"recorded on it ({RECORD_CITATION}). ⛔ The question is whether a person is going to "
        "read this diff, and it is procedure rather than a setting — nobody is going to look "
        "is an answer, and so is unanswered. What unblocks this is the answer written onto "
        f"the change:\n  python3 {Path(__file__).resolve()} record \\\n"
        f"    --change {slug}#{number} --question {MERGE_QUESTION} \\\n"
        "    --given '<the answer as it came back>' --by '<who answered>'"
    )


# --- the run the host has already made -------------------------------------
#
# ⛔ The facet is not read here and no part of it is carried: which run mirrors a
# command, what triggers it and which paths it watches are `host.checks`, reached
# through the reader's own accessor. What this half adds is the three facts a
# facet cannot hold, each of them about one commit.


def in_command_position(call: str, wanted: str) -> bool:
    """Does this call run `wanted`, as a command rather than as text?

    ⛔ **The measured defect this exists for**: a predicate matching the raw
    string took a build slot for a text search whose prose merely contained the
    build command. So the call is parsed into words, cut at the operators that
    end one command, and each piece is compared from its first word -- which a
    quoted argument carrying the same text can never reach.

    ⚠️ **A prefix and not an equality.** A flagged form of a command is that
    command, and a project that wants one of those left alone names it in
    `never_guard` -- which is read through this same function, so the longer form
    is matched there before the shorter one is matched here.

    ⛔ **§ 17's whitespace rule is not spelled again here**: both sides are cut
    into words, and runs of whitespace are gone by the time anything is compared.
    A third statement of that comparison is what this file would otherwise carry.
    """
    wanted_words = _words(wanted)
    if not wanted_words:
        return False
    segment: list[str] = []
    for word in [*_words(call), ";"]:
        if word in SEPARATORS:
            # ⛔ A leading assignment is not the command: `FOO=bar a-command` runs
            # the command, and a segment read from its first word would miss it.
            while segment and "=" in segment[0] and not segment[0].startswith("="):
                segment = segment[1:]
            if segment[:len(wanted_words)] == wanted_words:
                return True
            segment = []
            continue
        segment.append(word)
    return False


def _held_nothing(why: str, answer: str = UNESTABLISHED) -> dict:
    """The proceeding answer, naming which of § 18's values it is.

    ⛔ Never silent. A guard that proceeds without saying so is a guard nobody
    can tell from one that is not installed, and the three proceeding answers
    have three different remedies.
    """
    return {"systemMessage": f"{REPORT_PREFIX} — {answer}: {why} ({ALREADY_RUN_CITATION})."}


def _this_code(root: str) -> tuple[str, bool, str | None]:
    """(the commit in the tree, whether it carries anything uncommitted, or why not).

    ⚠️ Both halves of § 2's first precondition are asked of the tree rather than
    of the host: what is unpushed is what the next read answers, a run existing
    for this commit at all.
    """
    try:
        head = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=PROBE_TIMEOUT,
        )
        status = subprocess.run(
            ["git", "-C", str(root), "status", "--porcelain"],
            capture_output=True, text=True, timeout=PROBE_TIMEOUT,
        )
    except Exception as error:  # noqa: BLE001 -- any failure is a named absence
        return "", False, f"{type(error).__name__} while reading the commit in this tree"
    if head.returncode != 0 or not head.stdout.strip():
        return "", False, ("the commit in this tree could not be read, so no run can be "
                           "matched to it")
    return head.stdout.strip(), bool(status.stdout.strip()), None


def runs_for_commit(slug: str, head: str, root: str, run=None) -> tuple[list[dict], str | None]:
    """Every run the host made for this commit, or why they could not be read.

    ⛔ **The client's exit status is not read as the answer anywhere here.** The
    measured client exits non-zero while runs are pending and also when one has
    failed, so a guard reading it is a no-op while the host runs and a blocker
    once it has finished. What is read is the runs themselves; a non-zero exit is
    the host not answering, which proceeds.

    ⚠️ **The page is bounded and the bound errs towards proceeding**: a commit
    with more runs than this asks for may come back without the mirroring one,
    and the answer is then *nothing has run* rather than a refusal.
    """
    runner = run if run is not None else _run_host_in
    try:
        code, out = runner(
            ["run", "list", "--repo", slug, "--commit", head, "--limit", "50",
             "--json", "databaseId,workflowName,status,conclusion"],
            root, ALREADY_RUN_TIMEOUT,
        )
    except Exception as error:  # noqa: BLE001 -- any failure is a named absence
        return [], f"{type(error).__name__} while asking the host which runs exist for this commit"
    if code != 0:
        return [], "the host did not say which runs exist for this commit"
    try:
        loaded = json.loads(out or "[]")
    except json.JSONDecodeError:
        return [], "the host's answer about this commit's runs did not parse"
    return [r for r in loaded if isinstance(r, dict)], None


def change_is_conflicted(slug: str, root: str, run=None) -> tuple[bool, str | None]:
    """Whether this change is one the host can run nothing for.

    ⚠️ Asked only where no run was found, which is the one state the two answers
    share a shape in: § 2 records that *no checks reported* is almost always the
    conflicted case and reads as *nothing to wait for* to anyone not told.
    """
    runner = run if run is not None else _run_host_in
    try:
        code, out = runner(
            ["pr", "view", "--repo", slug, "--json", "mergeable"], root, ALREADY_RUN_TIMEOUT,
        )
    except Exception as error:  # noqa: BLE001 -- any failure is a named absence
        return False, f"{type(error).__name__} while asking whether this change is conflicted"
    if code != 0:
        # ⛔ Not an error to report: a branch with no change open on it is the
        # ordinary state this guard proceeds in, and it is the first of § 18's
        # conditions rather than a failure to establish one.
        return False, None
    try:
        loaded = json.loads(out or "{}")
    except json.JSONDecodeError:
        return False, "the host's answer about this change did not parse"
    return str((loaded or {}).get("mergeable") or "").upper() == "CONFLICTING", None


def _in_flight(entity: dict) -> bool:
    """Is the host still working on this run or job?"""
    return str(entity.get("status") or "") in IN_FLIGHT


def _how_the_run_stands(found: dict, record: dict, slug: str, root: str,
                        run=None) -> tuple[str | None, str | None]:
    """(why this run is not one to be refused on, or None — then why that is unknown).

    ⛔ **Where the facet names a job, the job is what this is read on**, by § 2: a
    workflow concluding anything says nothing about a command whose job was
    skipped, filtered out of the run or never started, and a per-workflow reading
    reports a run on a job that never ran.

    ⛔ **§ 2's third precondition is read on a workflow-level entry too**, which is
    the defect this review reproduced: with the jobs read only where the facet
    names one, a run cancelled in the queue, skipped, or concluding neutral
    refused the local check on the strength of a run that executed nothing —
    ⚠️ **and a run cancelled in the queue is routine rather than exotic** on an
    account whose runners take one job at a time.
    """
    if str(found.get("conclusion") or "") in NOT_OPERATIONAL:
        return (
            f"the host reports {record['mirrored_by']} as {found['conclusion']} for this "
            "commit, which is a fact about where the run was made rather than about this code",
            None,
        )
    # ⛔ A run the host is still working on answers for the command without any
    # step having executed yet, and the jobs are not read for it: the time is
    # being spent now, which is the duplicate. ⚠️ Only where the entry names no
    # job — a workflow still going says nothing about whether *this command's*
    # job has started, which is the same absence rule one level down.
    if _in_flight(found) and not record.get("job"):
        return None, None
    runner = run if run is not None else _run_host_in
    try:
        code, out = runner(
            ["run", "view", str(found.get("databaseId")), "--repo", slug, "--json", "jobs"],
            root, ALREADY_RUN_TIMEOUT,
        )
    except Exception as error:  # noqa: BLE001 -- any failure is a named absence
        return None, f"{type(error).__name__} while reading the jobs of the run for this commit"
    if code != 0:
        return None, "the host did not say which jobs this commit's run executed"
    try:
        loaded = json.loads(out or "{}")
    except json.JSONDecodeError:
        return None, "the host's answer about this run's jobs did not parse"
    jobs = [j for j in (loaded or {}).get("jobs") or [] if isinstance(j, dict)]
    if record.get("job"):
        mine = [j for j in jobs if j.get("name") == record["job"]]
        if not mine:
            return (
                f"the run for this commit executed no job named `{record['job']}`, so nothing "
                "in it answers about this command",
                None,
            )
        if not _answering(mine[0]):
            return (
                f"the job `{record['job']}` executed no step for this commit, which is no "
                "answer about this command rather than an answer of any kind",
                None,
            )
        return None, None
    if not any(_answering(job) for job in jobs):
        return (
            f"the run of {record['mirrored_by']} for this commit executed no step — it was "
            "cancelled, skipped or never started — so it is no answer about this command "
            "rather than an answer of any kind",
            None,
        )
    return None, None


def _answering(entity: dict) -> bool:
    """Is this run or job something to refuse a local run on?

    ⛔ **In flight, or it executed a step.** § 2's third precondition stands apart
    from the conclusion precisely because a run can conclude having started
    nothing, and the two states it separates are the two this answers: work being
    done now, and work that was done.
    """
    return _in_flight(entity) or bool(entity.get("steps"))


def _operational(config, found: dict, root: str, run=None) -> tuple[bool, str]:
    """§ 18's one condition a project may answer in place of the host.

    ⛔ Anything but the stated word proceeds, the probe's own failure included: a
    probe that cannot answer is not a host that can.
    """
    stated = config.get("already_run.operational_when")
    if not stated:
        # The host's own answer, already read beside the run's standing. Reaching
        # here means nothing it reported was a startup failure or an awaited
        # action, which is the whole of what this condition asks.
        return True, ""
    runner = run if run is not None else _run_in_shell
    try:
        code, out = runner(str(stated), root, PROBE_TIMEOUT)
    except Exception as error:  # noqa: BLE001 -- any failure is a named absence
        return False, (f"{type(error).__name__} while asking this project's own probe whether "
                       "the host can run these jobs")
    if code != 0:
        return False, ("this project's `operational_when` probe exited non-zero, so whether the "
                       "host can run these jobs is unestablished")
    printed = out.strip().splitlines()[0].strip() if out.strip() else ""
    if printed != OPERATIONAL:
        return False, (f"this project's `operational_when` probe printed {printed[:40]!r} rather "
                       f"than `{OPERATIONAL}`, so the host is not reported able to run these jobs")
    return True, ""


def _run_host_in(args: list[str], root: str, timeout: int) -> tuple[int, str]:
    """The host client, run from the tree whose change is being asked about.

    ⚠️ Rooted deliberately: the client resolves which change is open from the
    branch it is standing on, and a call made wherever the hook happened to start
    would answer about another tree or about none.
    """
    proc = subprocess.run(
        ["gh", *args], cwd=str(root), capture_output=True, text=True, timeout=timeout,
    )
    return proc.returncode, proc.stdout


def already_run_guard(config, command: str, *, host=None, probe=None,
                      environment=None, code=None) -> dict:
    """Refuse a local run of a command the host's own runs have already made.

    ⛔ **Nothing is read here that the facet already states.** Which run mirrors
    the command is `host.checks`, read through the shared reader's accessor, and
    the keying is the workflow's name — never a job's, which is the measured
    defect § 2 records. What this arm adds is the three per-commit facts no facet
    can carry: a run exists for this commit, it executed steps, and it is
    operational.

    ⚠️ **How that run concluded is deliberately not read**, by § 18: a red run has
    spent the time and answered, and what releases the call afterwards is the work
    itself — an edit leaves the tree carrying something the host has not seen.
    """
    stated = config.get("already_run.never_guard")
    if stated is None:
        # The reader refuses a configuration that states no list, so reaching this
        # means the guard is running against one nothing validated. Holding
        # nothing is the open direction, which is this guard's throughout.
        return {}
    records = [
        record for record in config.mirrors()
        if record.get("normalised") and in_command_position(command, record["normalised"])
    ]
    if not records:
        # ⛔ The silent arm, and the one every call in every project takes: a
        # command no entry mirrors is § 17's complement, and `checks: []` reaches
        # here with nothing to match at all.
        return {}
    # ⛔ **Every record mirroring this command, never the first or the longest.**
    # § 2 ranks across a command two entries mirror and makes `reached` outrank
    # the rest, for the stated reason that a run reaching this change exists —
    # and the reproduction here was the mirror image: with one record read, a
    # command mirrored twice reported *nothing has run* and named a workflow that
    # was not the one the host had run.
    records.sort(key=lambda r: -len(r["normalised"]))
    exempt = next(
        (entry for entry in stated
         if isinstance(entry, str) and in_command_position(command, entry)),
        None,
    )
    if exempt is not None:
        return {"systemMessage": (
            f"{REPORT_PREFIX}: `{exempt}` is one of this project's `never_guard` commands, so "
            f"this call was not held to them ({GUARDED_CITATION})."
        )}
    held = environment if environment is not None else os.environ
    escape = config.get("already_run.escape")
    if escape:
        # ⛔ The value is the reason, so a variable set to nothing is not an
        # escape: a blank why would stand every refusal down for whoever exported
        # it once and forgot.
        why = str(held.get(str(escape)) or "").strip()
        if why:
            return {"systemMessage": (
                f"{REPORT_PREFIX}: stood down by `{escape}` — {why} ({GUARDED_CITATION})."
            )}
    slug = config.get("host.repo")
    if not slug:
        return _held_nothing(
            "this project's configuration names no repository, so the host cannot be asked "
            "which runs exist for this commit"
        )
    root = config.code_root
    head, dirty, unread = (code if code is not None else _this_code)(root)
    if unread:
        return _held_nothing(unread)
    if dirty:
        # § 2's first precondition, read for the opposite act: an edit the host
        # never received is an edit no run answered about, so the local run is
        # the only verdict there is.
        return _held_nothing(
            "this tree carries changes the host has not seen, so no run of its own answers "
            "about the code in hand",
            answer=NOTHING_HAS_RUN,
        )
    runs, unread = runs_for_commit(slug, head, root, run=host)
    if unread:
        return _held_nothing(unread)
    answered = [
        (record, *_record_answer(record, runs, slug, root, config, host=host, probe=probe))
        for record in records
    ]
    # ⛔ § 2's ranking, applied here rather than re-derived: a run that reaches
    # this change exists, so what a sibling entry could not say does not unmake
    # it. The first record answering `already run` is the one refused on.
    refusing = next((a for a in answered if a[1] == ALREADY_RUN), None)
    if refusing is not None:
        record, _answer, why = refusing
        # ⛔ The remedy is named as something somebody can do rather than as a
        # description of the refusal, by § 7: a guard whose refusal states only
        # that it refused leaves one route past it, which is editing the guard.
        unblocks = (
            f"Set `{config.get('already_run.escape')}` to why this run is wanted anyway"
            if config.get("already_run.escape")
            else "Edit the tree, so the host's run stops answering about the code in hand"
        )
        return _deny(
            f"{REPORT_PREFIX} — {ALREADY_RUN}: {why}, {head[:12]} ({ALREADY_RUN_CITATION}). "
            f"⛔ Its conclusion is not what is read here — the run exists for this code and "
            f"did not conclude without executing one, so running `{record['normalised']}` "
            f"locally spends the time a second time and holds whatever place the call puts at "
            f"stake. {unblocks}."
        )
    # ⛔ The conflict is asked about only once nothing has a run, which is the one
    # state the two answers share a shape in — and asked once for the call rather
    # than once per record.
    if all(a[1] == NOTHING_HAS_RUN for a in answered):
        conflicted, unread = change_is_conflicted(slug, root, run=host)
        if conflicted:
            return _held_nothing(
                "this change is conflicted, so the host produces no run for it at all — "
                f"{answered[0][0]['mirrored_by']} has nothing to report until that is "
                "resolved, and a local run answers nothing that can land",
                answer=NOTHING_CAN_RUN,
            )
        if unread:
            return _held_nothing(
                f"no run answering for this command exists for this commit, and whether that "
                f"is because the change is conflicted could not be established: {unread}",
            )
    # ⚠️ Every record is reported and not only the one that decided it, the way
    # the facet's own consumer reports each run it read.
    worst = next(a for a in answered if a[1] == UNESTABLISHED) if any(
        a[1] == UNESTABLISHED for a in answered
    ) else answered[0]
    return _held_nothing(
        "; ".join(why for _record, _answer, why in answered), answer=worst[1],
    )


def _record_answer(record: dict, runs: list[dict], slug: str, root: str, config,
                   host=None, probe=None) -> tuple[str, str]:
    """§ 18's answer for one record of the facet, and what decided it.

    ⚠️ **The workflow's name and never a job's**, which is § 2's keying rule: two
    unrelated workflows named their job identically, and a job-keyed reading
    refused a build on a check that only validated a title. ⚠️ **The first of
    several runs is the newest**, the host listing them that way, and a re-run is
    the answer that stands — the same reading § 11 gives every artifact.
    """
    mine = [r for r in runs if r.get("workflowName") == record["workflow"]]
    if not mine:
        return NOTHING_HAS_RUN, (
            f"the host has made no run of {record['mirrored_by']} for this commit"
        )
    standing, unread = _how_the_run_stands(mine[0], record, slug, root, run=host)
    if unread:
        return UNESTABLISHED, unread
    if standing:
        return NOTHING_HAS_RUN, standing
    operational, why = _operational(config, mine[0], root, run=probe)
    if not operational:
        return UNESTABLISHED, why
    state = mine[0].get("conclusion") or mine[0].get("status") or "unreported"
    return ALREADY_RUN, f"{record['mirrored_by']} reports {state} for this commit"


def capacity_guard(config, command: str, session: str, cwd: str, background: bool,
                   *, now: float, store: Path | None = None, probe=None) -> dict:
    """Hold a place on whatever this call puts at stake, or refuse the call.

    ⛔ Every refusal the arm above can make has already been made, which is the
    ordering the surface's own table implies and the measured leak it closes: a
    place taken by a call that is then denied is a place nothing releases, because
    a call refused before it runs reaches no event at all.
    """
    stated = resources(config)
    if not stated:
        return {}
    where = store if store is not None else store_for(config.skills_root)
    refusals, notes, written = [], [], []
    for entry in stated:
        if not claims(entry, command):
            continue
        counted, unestablished = probe_count(entry, config.skills_root, run=probe)
        if unestablished:
            # ⛔ The open direction, per the surface: a call can be run again, so
            # the answer says the place was not held rather than refusing.
            notes.append(f"{entry.get('name')}: {unestablished}, so no place was held")
            continue
        key = _tree_key(cwd) if entry.get("subject") == "tree" else _call_key(session, command)
        path, taken, standing, cap = take(
            entry, where, key, session, command, background, counted, now
        )
        if path is not None:
            written.append(path)
        if not taken:
            refusals.append(
                f"{entry.get('name')} is at its cap of {cap}, with {standing} held"
            )
    if refusals:
        # ⛔ Every place this call took on its way to being refused is given back
        # here. One call may claim several resources, and a place taken for a call
        # that is then denied is a place nothing releases — a denied call reaching
        # no exit event at all, which is the measured leak this whole arm is
        # ordered around.
        for path in written:
            path.unlink(missing_ok=True)
        return _deny(
            "This command puts a resource at stake that is fully held: "
            + "; ".join(refusals)
            + f". ⛔ The call is refused rather than queued ({LEASE_CITATION}). What unblocks "
            "it is a place coming back — a holder finishing, or its lease expiring."
        )
    if notes:
        return {"systemMessage": "Capacity: " + "; ".join(notes) + f". ({LEASE_CITATION})"}
    return {}


def guard_answer(payload: dict, *, config=None, now: float | None = None,
                 store: Path | None = None, probe=None, host=None, runs=None,
                 code=None) -> dict:
    """The `PreToolUse` answer for one call."""
    if payload.get("tool_name") != GUARDED_TOOL:
        return {}
    tool_input = payload.get("tool_input") or {}
    command = str(tool_input.get("command") or "")
    if not command.strip():
        return {}
    if config is None and not _states_a_configuration(payload.get("cwd")):
        # ⛔ Silence, and not a report: this arm fires on every command in every
        # project the install reaches, and a project that states no configuration
        # has agreed to no rule this guard could hold. Separate from the branch
        # below, which is a configuration that *is* stated and does not resolve.
        return {}
    loaded = config if config is not None else _config(payload.get("cwd"))
    if loaded is None:
        said = (
            "Enforcement: the project's configuration could not be read, so this command was "
            "held to nothing."
        )
        stop = _stop(payload.get("cwd"))
        if stop:
            said += f" What the reader refused it for, which is the repair: {stop}"
        return {"systemMessage": said}
    refused = merge_guard(loaded, command, host=host)
    if refused:
        return refused
    # ⛔ Before any place is taken, for the reason the arm below is ordered after
    # the merge guard: a place taken by a call that is then denied is a place
    # nothing releases. ⚠️ And this arm proceeds far more often than it refuses,
    # so its `systemMessage` is returned only where it had something to say.
    # ⚠️ Its host reader is its own and not the merge guard's: the two arms ask
    # different questions of the client and one of them is rooted in the tree,
    # so one stand-in for both would answer with the wrong shape.
    answered = already_run_guard(loaded, command, host=runs, probe=probe, code=code)
    if answered.get("hookSpecificOutput"):
        return answered
    held = capacity_guard(
        loaded,
        command,
        str(payload.get("session_id") or ""),
        str(payload.get("cwd") or "."),
        bool(tool_input.get("run_in_background")),
        now=time.time() if now is None else now,
        store=store,
        probe=probe,
    )
    # ⛔ A refusal below wins, and the arm above still gets to say what it found:
    # two arms answering one call must not silence each other, and only one of
    # the two can refuse at a time.
    if held.get("hookSpecificOutput") or not answered.get("systemMessage"):
        return held
    if not held.get("systemMessage"):
        return answered
    return {"systemMessage": answered["systemMessage"] + " " + held["systemMessage"]}


# --- the branch against its base -------------------------------------------
#
# ⛔ **Nothing in this arm refuses, and that is the surface's statement rather
# than a preference.** Both points it answers at are exit events, so there is no
# call in hand to hold: `§ 7 -> A branch that has fallen behind its base` states
# it, and what this produces is a report. ⚠️ Which also means the fail-direction
# rule does not reach it -- an unestablished reading here costs a report naming
# what it could not read, there being no act to let through or refuse.


def _claim():
    """The claim carrier, or None where it could not be loaded.

    ⛔ Imported rather than re-implemented, for the same reason the configuration
    is read through its own reader: which branch a project integrates into, and
    what the remote says that branch's head is, are one derivation -- and a
    second one here would be free to disagree with the one every start and every
    landing already takes.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        import claim as carrier  # noqa: PLC0415 -- the path is set one line up
        return carrier
    except Exception:  # noqa: BLE001 -- any failure is reported by the caller
        return None


def commits_behind(printed: str) -> int:
    """How many commits of the base carry a patch this branch does not.

    ⛔ **The marked lines and never the line count.** The carrier prints one line
    per commit of the base this branch lacks *by ancestry*, marking it `-` where
    an equivalent patch is in the branch anyway -- and `-` lines are exactly what
    a rewritten base produces, so a count of lines is the plain count § 7
    forbids, reached one character later.
    """
    return sum(1 for line in printed.splitlines() if line.startswith("+"))


def _commits(figure: int) -> str:
    return f"{figure} commit" if figure == 1 else f"{figure} commits"


def behind_of(where: str, *, remote: str = "origin",
              load=None) -> tuple[str | None, int | None, str]:
    """(§ 7's answer, the figure where there is one, the answer in words).

    ⛔ **`(None, None, "")` is the silent case and not an answer**: a directory
    that is no work tree, and a code root that publishes no base at all. § 7
    splits those from a base that could not be *reached*, which is the section's
    own absent-against-unreadable rule and is the direction a report every turn
    would otherwise get this arm switched off in.

    ⛔ **The words name the tree the answer was taken in.** A session stands in
    one tree per item, so an answer with no tree named is an answer whose subject
    a reader has to guess.
    """
    carrier = (load if load is not None else _claim)()
    if carrier is None:
        return UNESTABLISHED, None, (
            f"the claim carrier could not be loaded from {Path(__file__).resolve().parent}, so "
            "which branch this project integrates into could not be derived"
        )

    # ⛔ **Every read this arm makes goes through one bound and one failure path.**
    # The review of this change reproduced the alternative: with three of the
    # reads unwrapped, a timeout on any of them escaped this function altogether,
    # so the arm produced no answer at all rather than an unestablished one -- and
    # took the lease sweep's own message out with it on the way, two arms of one
    # event lost to one read.
    #
    # ⚠️ **A non-zero exit is not a failed read and stays each caller's to
    # interpret.** `cat-file` exiting non-zero is the object being absent, which
    # is this arm's *behind* answer; conflating the two would report a timeout as
    # a branch behind its base.
    unread: list[str] = []

    def run(root, *args):
        try:
            return carrier.git(root, *args, check=False, timeout=BEHIND_TIMEOUT)
        except Exception as error:  # noqa: BLE001 -- any failure is a named absence
            unread.append(f"{type(error).__name__} while running `{args[0]}` in {root}")
            return None

    top = run(where, "rev-parse", "--show-toplevel")
    if top is None:
        return UNESTABLISHED, None, (
            f"{unread[-1]}, so which tree {where} is in could not be established"
        )
    if top.returncode != 0 or not top.stdout.strip():
        # ⛔ Silent: no work tree means no branch and no base, which is nothing to
        # have fallen behind rather than something unread.
        return None, None, ""
    tree = top.stdout.strip()
    try:
        publishes = bool(carrier.remote_url(tree, remote))
    except Exception as error:  # noqa: BLE001 -- any failure is a named absence
        return UNESTABLISHED, None, (
            f"in {tree}, {type(error).__name__} while asking whether this code root publishes a "
            "base at all"
        )
    if not publishes:
        # ⛔ Silent for the same reason, by § 10's derived local-only claim: a
        # code root with no remote publishes no base.
        return None, None, ""
    # ⚠️ The branch names the answer's subject and does not decide it, so a read
    # that could not answer here leaves the tree alone as the subject rather than
    # making the whole answer unestablished.
    named = run(tree, "rev-parse", "--abbrev-ref", "HEAD")
    branch = named.stdout.strip() if named is not None and named.returncode == 0 else ""
    here = f"{tree} on `{branch}`" if branch else tree
    try:
        base = carrier.integration_branch(tree, remote, timeout=BEHIND_TIMEOUT)
    except Exception as error:  # noqa: BLE001 -- any failure is a named absence
        return UNESTABLISHED, None, f"in {here}, the base could not be named: {error}"
    try:
        head = carrier.remote_ref_sha(tree, remote, base, timeout=BEHIND_TIMEOUT)
    except Exception as error:  # noqa: BLE001 -- any failure is a named absence
        return UNESTABLISHED, None, (
            f"in {here}, the head of `{base}` could not be read from `{remote}`: {error}"
        )
    if head is None:
        return UNESTABLISHED, None, (
            f"in {here}, `{remote}` carries no branch named `{base}`, so there is no base to "
            "read this branch against"
        )
    held_here = run(tree, "cat-file", "-e", f"{head}^{{commit}}")
    if held_here is None:
        return UNESTABLISHED, None, (
            f"in {here}, {unread[-1]}, so whether this tree holds `{base}` at {head[:12]} is "
            "unknown"
        )
    if held_here.returncode != 0:
        # ⛔ Behind with no figure, never level: the remote reports a head this
        # tree does not hold, which is § 2's absence of signal one ref over.
        return BEHIND, None, (
            f"in {here}, `{remote}/{base}` is at {head[:12]} and this tree does not hold that "
            f"commit, so how far behind it this branch is cannot be read here — fetch "
            f"`{remote}` and the figure follows"
        )
    compared = run(tree, "cherry", "HEAD", head)
    if compared is None or compared.returncode != 0:
        return UNESTABLISHED, None, (
            f"in {here}, the commits of `{base}` could not be compared against this branch by "
            "patch" + (f": {unread[-1]}" if compared is None else "")
        )
    figure = commits_behind(compared.stdout)
    if figure == 0:
        return LEVEL, 0, (
            f"in {here}, `{remote}/{base}` at {head[:12]} carries no commit whose patch this "
            "branch does not"
        )
    return BEHIND, figure, (
        f"in {here}, `{remote}/{base}` at {head[:12]} carries {_commits(figure)} whose patch "
        "this branch does not — what clears it is the base brought into this branch"
    )


def behind_answer(payload: dict, *, event: str | None = None, load=None, read=None) -> str:
    """§ 7's report for one exit event, or `""` where this is not one of its points.

    ⛔ **Two of the four release events, and the second one narrowed further.**
    A session ending is a report nobody is left to act on and a subagent stopping
    is not this tree's turn ending; a finished call is one of the two points only
    where the call *merged*, which is read with the merge guard's own grammar
    rather than a second one written here.
    """
    fired = event if event is not None else str(payload.get("hook_event_name") or "")
    # ⛔ The two points are read out of the one place that states them, never
    # matched again here: the first form of this arm compared the event against
    # each name inline and left the list beside it decorative — measured by
    # widening the list to all four events and watching only the list's own
    # assertion redden while the arm went on answering at two.
    if fired not in BEHIND_EVENTS:
        return ""
    if fired == CALL_FINISHED:
        if payload.get("tool_name") != GUARDED_TOOL:
            return ""
        command = str((payload.get("tool_input") or {}).get("command") or "")
        # ⚠️ The repository is not supplied, and nothing here needs it: what is
        # asked is whether the call was a merge, which the grammar answers off
        # the parsed words alone. ⚠️ Nor is the call's own result read -- a merge
        # that failed moved no base, and `level` is the true answer for it.
        if not command.strip() or merge_target(command, None) is None:
            return ""
    answer, _figure, said = (read if read is not None else behind_of)(
        str(payload.get("cwd") or "."), load=load
    )
    if answer is None:
        return ""
    return f"{BEHIND_PREFIX} — {answer}: {said} ({BEHIND_CITATION})."


def release_answer(payload: dict, *, config=None, now: float | None = None,
                   store: Path | None = None, load=None, read=None) -> dict:
    """The answer for whichever event gives a place back, and reports the base.

    ⛔ This arm was already silent in a project that states no configuration,
    the reader refusing and the answer being empty either way. It asks the
    question anyway, so that both arms of this carrier ask it before anything
    else: reaching the same silence through a refusal costs the surface's own
    parse on every call in a project that holds nothing.

    ⛔ **A configuration that is there and does not resolve still gets the base
    reported**, which is § 7's absent-against-unreadable split applied to this
    arm rather than inherited: the sweep below reads `exclusive_resources` and
    can do nothing without it, while the arm beside it reads no key at all.
    """
    event = str(payload.get("hook_event_name") or "")
    scope = RELEASE_EVENTS.get(event)
    if scope is None:
        return {}
    if config is None and not _states_a_configuration(payload.get("cwd")):
        return {}
    loaded = config if config is not None else _config(payload.get("cwd"))
    said = [
        _places_given_back(loaded, payload, scope, now=now, store=store),
        behind_answer(payload, event=event, load=load, read=read),
    ]
    spoken = [line for line in said if line]
    return {"systemMessage": " ".join(spoken)} if spoken else {}


def _places_given_back(loaded, payload: dict, scope: str, *, now: float | None,
                       store: Path | None) -> str:
    """What the sweep released, in words, or `""` where it released nothing."""
    if loaded is None or not resources(loaded):
        return ""
    where = store if store is not None else store_for(loaded.skills_root)
    command = str((payload.get("tool_input") or {}).get("command") or "")
    given = release(
        where,
        str(payload.get("session_id") or ""),
        scope,
        command,
        time.time() if now is None else now,
    )
    if not given:
        return ""
    return (
        "Capacity: gave back " + ", ".join(sorted({str(g.get("resource")) for g in given}))
        + f". ({LEASE_CITATION})"
    )


def _states_a_configuration(cwd: str | None) -> bool:
    """Whether the project this event names states a configuration at all.

    ⛔ Asked through the shared reader rather than by testing a path here: where
    a project's configuration lives is one statement, and a second copy of that
    path drifts the first time either moves.

    ⛔ False where the reader cannot be reached at all, which is the silent
    direction deliberately: an install whose own reader is missing cannot hold a
    project to a file it has no way to find.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        import config as reader  # noqa: PLC0415 -- the path is set one line up
        return bool(reader.configured(cwd or "."))
    except Exception:  # noqa: BLE001 -- an unreachable reader answers no, per above
        return False


def _config(cwd: str | None):
    """The project's configuration, or None where it could not be read.

    ⛔ Read through the shared reader, never parsed here: a second reader is a
    second set of defaults, and two sets drift apart with nothing noticing.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        import config as reader  # noqa: PLC0415 -- the path is set one line up
        return reader.load(cwd or ".", check_paths=False)
    except Exception:  # noqa: BLE001 -- any failure is reported by the caller
        return None


def _stop(cwd: str | None) -> str:
    """Why the reader refused it, for the message — empty where it resolves.

    ⛔ Asked through the shared reader, for `_config`'s own reason, and because
    the stop names the missing key: a message that reports *could not be read*
    without it is noise once per call, where the same message carrying it is the
    repair.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        import config as reader  # noqa: PLC0415 -- the path is set one line up
        return reader.why_refused(cwd or ".")
    except Exception:  # noqa: BLE001 -- an unreachable reader explains nothing
        return ""


# --- the arms a role invokes ------------------------------------------------


def questions(surface_text: str | None = None) -> list[str]:
    """The questions an answer may be recorded for, read out of the surface.

    ⛔ Through the surface's own reader and never parsed here, which is what makes
    the alternation one statement rather than two. An empty list where the
    alternation cannot be read at all, which the caller reports rather than
    treating as *every question is fine*.

    ⚠️ **Which copy of the surface** is § 1's question and not this arm's, so it
    is asked through the reader rather than answered here: the working directory
    is the skills root this arm is invoked from, and a tree that ships the surface
    is read against its own copy. Without that, a question a branch adds to the
    vocabulary is refused by the installed branch's list while the configuration
    beside it loads -- the same skew one facet over.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        import config as reader  # noqa: PLC0415 -- the path is set one line up
        text = (
            surface_text
            if surface_text is not None
            else Path(reader.surface_for()).read_text(encoding="utf-8")
        )
        return list(reader.surface_facts(text)["enums"].get(QUESTION_VOCABULARY) or [])
    except Exception:  # noqa: BLE001 -- any failure is a named absence to the caller
        return []


def write_record(address: str, question: str, given: str, by: str, at: str,
                 run=None) -> tuple[str, int]:
    """Write a recorded answer onto a change, and say where it went.

    ⛔ A question outside the surface's own vocabulary is refused rather than
    written. A record under a name nothing reads is a record a guard sees as
    absent, so writing one would report an answer recorded and leave the act
    refused — which is the failure the keying rule above is about, one field over.
    """
    known = questions()
    if not known:
        return (
            "⛔ Not established: the surface's own list of questions could not be read, so "
            f"whether `{question}` is one of them is unknown. Nothing was recorded — a record "
            "under a name nothing reads is a record a guard sees as absent.",
            1,
        )
    if question not in known:
        return (
            f"Refused: `{question}` is not one of the questions an answer is recorded for "
            f"({' | '.join(known)}). ⛔ Nothing was written: a record under a name nothing "
            f"reads leaves the act refused however it was answered ({RECORD_CITATION}).",
            2,
        )
    found = CHANGE_ADDRESS.match(address.strip())
    if not found:
        return (
            f"Refused: {address!r} is not a change the way a record is keyed. The form is "
            f"`<owner>/<repository>#<number>` ({RECORD_CITATION}): a bare number names a "
            "different change in every repository the route carries.",
            2,
        )
    slug, number = found.group("slug"), found.group("number")
    body = record_body(question, given, by, at)
    runner = run if run is not None else _run_host
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as out:
        out.write(body + "\n")
        path = out.name
    try:
        code, printed = runner(
            ["pr", "comment", number, "--repo", slug, "--body-file", path], HOST_TIMEOUT
        )
    finally:
        os.unlink(path)
    if code != 0:
        return (
            f"Refused: the host did not accept the record for {slug}#{number}. ⛔ Nothing was "
            "recorded, so a guard reading this change still has no answer to read.",
            1,
        )
    return (
        f"Recorded on {slug}#{number}: `{question}` answered {given!r} by {by} at {at}.\n"
        f"{printed.strip()}",
        0,
    )


def held_report(config, *, now: float | None = None, store: Path | None = None,
                probe=None) -> tuple[str, int]:
    """What is held right now, and by what."""
    stated = resources(config)
    lines = [f"What is held on this project's exclusive resources ({LEASE_CITATION})."]
    if not stated:
        lines.append("")
        lines.append(
            "Nothing is exclusive here (`branch_model.exclusive_resources: []`), so no place "
            "is held and no guard is installed. ⛔ Not an absence of signal: the project "
            "states it."
        )
        return "\n".join(lines), 0
    where = store if store is not None else store_for(config.skills_root)
    moment = time.time() if now is None else now
    leases = live_leases(where, moment)
    for entry in stated:
        counted, unestablished = probe_count(entry, config.skills_root, run=probe)
        standing, keys = occupancy(entry, leases, counted)
        lines.append("")
        lines.append(f"{entry.get('name')} — cap {entry.get('cap')}, held by {entry.get('subject')}")
        if unestablished:
            lines.append(f"  ⛔ {unestablished}")
        else:
            lines.append(f"  the resource itself reports {counted} held")
        lines.append(f"  {len(keys)} lease(s) still counting, so {standing} against the cap")
        for _path, lease in leases:
            if lease.get("resource") != entry.get("name"):
                continue
            age = int(moment - float(lease.get("taken") or 0))
            lines.append(
                f"    - {lease.get('key')} — {age}s old of {lease.get('ttl')}s"
                + (", backgrounded" if lease.get("background") else "")
            )
    return "\n".join(lines), 0


# --- holding this file to the surface and to its carrier --------------------


def _anchor(heading: str) -> str:
    text = heading.strip().lower().replace("`", "")
    text = re.sub(r"[^\w\s-]", "", text)
    return text.replace(" ", "-")


def check_the_surface_still_states_this(text: str) -> list[str]:
    """Every subsection this script is the carrier for is still there, by anchor."""
    anchors = {
        _anchor(line.lstrip("#").strip())
        for line in text.splitlines()
        if line.startswith("#")
    }
    problems = []
    for arm, slug in sorted(ARM_ANCHORS.items()):
        if slug not in anchors:
            problems.append(
                f"the `{arm}` rule cites `{slug}`, which is not a heading of the surface. "
                "Either the subsection was reworded or the rule it holds is gone."
            )
    return problems


def check_the_carrier_still_calls_this(text: str) -> list[str]:
    """`hooks.json` still registers this file on the guard event and on every release event.

    ⛔ Every event rather than one: a release event that stopped being registered
    leaks a place on exactly the exit path it covered, and the leak is invisible
    until a cap is pinned with nothing running.
    """
    try:
        carrier = json.loads(text)
    except json.JSONDecodeError as error:
        return [f"{CARRIER.name} is not readable as JSON ({error}), so nothing calls this."]
    hooks = carrier.get("hooks") or {}
    mine = Path(__file__).name
    problems = []
    for event in [GUARD_EVENT, *sorted(RELEASE_EVENTS)]:
        called = None
        for group in hooks.get(event) or []:
            for item in group.get("hooks") or []:
                named = " ".join([str(item.get("command") or "")]
                                 + [str(a) for a in (item.get("args") or [])])
                if mine in named:
                    called = group
        if called is None:
            problems.append(
                f"{CARRIER.name} registers no {event} hook calling {mine}, so whatever that "
                "event covers is covered by nothing."
            )
            continue
        if event in (GUARD_EVENT, "PostToolUse"):
            matcher = called.get("matcher") or ""
            if GUARDED_TOOL not in matcher:
                problems.append(
                    f"{CARRIER.name} calls {mine} on {event} with matcher {matcher!r}, which "
                    f"does not select the one tool a place is held by a call of."
                )
    return problems


# --- the plants ------------------------------------------------------------


def _a_config(resources_stated: list[dict], repo: str = "an-owner/a-repository",
              root: str = "."):
    """A stand-in for the shared reader's answer, carrying only what an arm reads.

    ⛔ A fake and not a mock: it answers as the reader does for the two things an
    arm asks it, so a rename of either key reddens here rather than passing.
    ⚠️ Its shape is the production one -- the dotted-path accessor and the skills
    root -- because a fixture thinner than that tests the fixture.
    """

    class _Loaded:
        def __init__(self):
            self.skills_root = root
            self.data = {
                "host": {"repo": repo},
                "branch_model": {"exclusive_resources": resources_stated},
            }

        def get(self, path, default=None):
            node = self.data
            for part in path.split("."):
                if not isinstance(node, dict) or part not in node:
                    return default
                node = node[part]
            return node

    return _Loaded()


def _a_resource(**overrides) -> dict:
    entry = {
        "name": "a-held-thing",
        "cap": 2,
        "subject": "call",
        "claimed_by": "a-claiming-command",
        "probe": None,
        "ttl": 600,
    }
    entry.update(overrides)
    return entry


def _a_host(comments: list[str] | None = None, number: int | None = 7, code: int = 0):
    """A stand-in for the host, answering the two reads the merge guard makes."""

    def run(args, _timeout):
        if code:
            return code, ""
        if args[:2] == ["api", "--paginate"]:
            return 0, json.dumps([{"body": body} for body in (comments or [])])
        if args[:2] == ["pr", "view"]:
            return 0, json.dumps({"number": number} if number is not None else {})
        return 1, ""

    return run


# ⛔ Placeholder names throughout, as `host_checks.py`'s fixtures are: a workflow
# name, a command or a path belonging to a project is a fact this toolkit must not
# carry, and a fixture is where one would arrive unnoticed.
A_MIRRORED_RUN = [{
    "workflow": "A workflow",
    "mirrors": "a-mirrored-command",
    "triggers": "pull_request -> *",
}]

A_MIRRORED_JOB = [{
    "workflow": "A workflow",
    "triggers": "pull_request -> *",
    "jobs": [{"job": "a-job", "mirrors": "a-mirrored-command"}],
}]


def _a_project(checks, never_guard=None, escape=None, operational_when=None,
               repo: str = "an-owner/a-repository"):
    """A loadable configuration carrying this facet and this guard's own keys.

    ⛔ Built from an example and loaded through the shared reader rather than
    hand-written here, for the reason `host_checks.py` builds its fixtures that
    way: the records this arm reads are the reader's own walk of § 2, so a plant
    assembling them by hand would assert the plant.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import yaml  # noqa: PLC0415 -- a fixture's dependency, not the arm's
    import config as reader  # noqa: PLC0415 -- the path is set two lines up

    with open(SURFACE.parent / "examples" / "github-issues.yaml", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    data["host"]["repo"] = repo
    data["host"]["checks"] = checks
    # § 17's collision refusal reads `host.checks`, so the example's own local
    # list is cleared rather than left to collide with a planted entry.
    data["checks_local"] = []
    stated = {"never_guard": list(never_guard or [])}
    if escape is not None:
        stated["escape"] = escape
    if operational_when is not None:
        stated["operational_when"] = operational_when
    data["already_run"] = stated
    return reader.load_text(yaml.safe_dump(data), ".", check_paths=False)


def _a_run(workflow: str = "A workflow", status: str = "completed",
           conclusion: str | None = "success") -> dict:
    return {
        "databaseId": 1,
        "workflowName": workflow,
        "status": status,
        "conclusion": conclusion,
    }


# A run that genuinely ran: one job, finished, with a step behind it. ⛔ The
# default rather than an empty job list, and the review that reproduced the
# defect is why: with no jobs the fixtures asserted a refusal on a run that had
# executed nothing, which is the state § 2's third precondition exists to catch.
A_JOB_THAT_RAN = [{"name": "a-job", "status": "completed", "steps": [{"name": "a-step"}]}]


def _a_host_making(runs=None, jobs=None, mergeable=None, code: int = 0):
    """A stand-in for the host, answering the three reads this guard makes."""

    def run(args, _root, _timeout):
        if code:
            return code, ""
        if args[:2] == ["run", "list"]:
            return 0, json.dumps(runs if runs is not None else [])
        if args[:2] == ["run", "view"]:
            return 0, json.dumps({"jobs": jobs if jobs is not None else A_JOB_THAT_RAN})
        if args[:2] == ["pr", "view"]:
            # ⚠️ Non-zero is a branch with no change open on it, which is the
            # ordinary state and not a failure to establish anything.
            if mergeable is None:
                return 1, ""
            return 0, json.dumps({"mergeable": mergeable})
        return 1, ""

    return run


def _a_tree(head: str = "a-commit-in-the-tree", dirty: bool = False,
            unread: str | None = None):
    def read(_root):
        return head, dirty, unread

    return read


def _a_probe(count: int | None = 0, code: int = 0, prints: str | None = None):
    def run(_command, _root, _timeout):
        if prints is not None:
            return code, prints
        return code, "" if count is None else f"{count}\n"

    return run


def _a_root(where: Path, states: str | None) -> str:
    """A project root stating this configuration, or stating none at all.

    ⛔ Written at the reader's own `CONFIG_PATH` rather than at a path spelled
    out here: a fixture built against a literal would stay green after that path
    moved, while every live hook went silent in every project.
    """
    where.mkdir(parents=True, exist_ok=True)
    if states is not None:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import config as reader  # noqa: PLC0415 -- the path is set one line up

        stated = where / reader.CONFIG_PATH
        stated.parent.mkdir(parents=True, exist_ok=True)
        stated.write_text(states, encoding="utf-8")
    return str(where)


def _in(root, *args: str) -> str:
    """A fixture's own git, which raises rather than returning a bad fixture quietly."""
    proc = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    if proc.returncode != 0:
        raise AssertionError(
            f"the fixture's `git {' '.join(args)}` failed in {root}: "
            f"{proc.stderr.strip() or proc.stdout.strip()}"
        )
    return proc.stdout.strip()


def _a_commit(root, name: str, text: str = "a line\n") -> None:
    (Path(root) / name).write_text(text, encoding="utf-8")
    _in(root, "add", name)
    _in(root, "commit", "--quiet", "-m", f"add {name}")


def _a_published_base(where: Path, branch: str = "a-branch") -> tuple[str, str, str]:
    """(a bare repository standing in for the host, a clone that moves the base, a tree).

    ⛔ **Real repositories and no stand-in anywhere in this arm**, which is the
    one thing the rewritten-base plant below cannot be asserted without: what is
    in question is what git itself says about a base whose hashes changed, and a
    fake would assert the fake's own idea of a patch.

    ⚠️ The integration branch is named explicitly, for the reason the claim
    carrier's own fixture names it: a bare repository's `HEAD` follows this
    machine's default branch name, and a clone of one whose `HEAD` points at a
    ref nothing created has no local integration branch at all.
    """
    # ⚠️ Resolved, and the suite's assertions compare against these: the answer
    # names the tree as git reports it, and the temporary directory this is built
    # under is reached through a symlink on one of the two platforms measured --
    # so a path taken straight from the fixture matches nothing in the report.
    where = where.resolve()
    origin = where / "origin.git"
    subprocess.run(
        ["git", "init", "--quiet", "--bare", "--initial-branch=main", str(origin)], check=True
    )
    seed = where / "a-clone-that-moves-the-base"
    # ⚠️ Captured rather than discarded: a clone of a repository with no commits
    # warns on stderr, which `--quiet` does not cover, and a clone that genuinely
    # fails must still be able to say why.
    subprocess.run(["git", "clone", "--quiet", str(origin), str(seed)],
                   capture_output=True, text=True, check=True)
    for key, value in (("user.email", "a@seed"), ("user.name", "A Seed")):
        _in(seed, "config", key, value)
    _a_commit(seed, "base.txt")
    _in(seed, "branch", "-M", "main")
    _in(seed, "push", "--quiet", "origin", "main")

    tree = where / "a-tree"
    subprocess.run(["git", "clone", "--quiet", str(origin), str(tree)],
                   capture_output=True, text=True, check=True)
    for key, value in (("user.email", "a@tree"), ("user.name", "A Tree")):
        _in(tree, "config", key, value)
    _in(tree, "checkout", "--quiet", "-b", branch)
    return str(origin), str(seed), str(tree)


def _rewrite_the_base(seed: str) -> None:
    """Rewrite every commit the base has, leaving its content identical.

    ⛔ **The plant the whole reading exists for**, and it has to rewrite a commit
    the branch *already carries* to be one: rewriting a commit the branch never
    had is a base that genuinely advanced, which is a different answer and was
    the first form of this plant.
    """
    _in(seed, "commit", "--quiet", "--amend", "--no-edit",
        "--author", "Another Name <another@seed>")
    _in(seed, "push", "--quiet", "--force", "origin", "main")


def _a_carrier_that_will_not_load():
    return None


class _OneReadMissing:
    """The claim carrier with one of this arm's reads unable to run at all.

    ⛔ **The real carrier with one call replaced, never a stand-in for the whole
    of it**: what is in question is this arm's own failure path, so every other
    read has to answer exactly as it really does — a fake carrier would assert
    the fake.
    """

    def __init__(self, real, which: str):
        self._real, self._which = real, which
        self.remote_url = real.remote_url
        self.integration_branch = real.integration_branch
        self.remote_ref_sha = real.remote_ref_sha

    def git(self, root, *args, check: bool = True, timeout=None):
        if args and args[0] == self._which:
            raise subprocess.TimeoutExpired(cmd=["git", self._which], timeout=timeout or 0)
        return self._real.git(root, *args, check=check, timeout=timeout)


def _a_carrier_that_cannot_run(which: str):
    def load():
        real = _claim()
        if real is None:
            raise AssertionError("the fixture could not load the claim carrier to break")
        return _OneReadMissing(real, which)

    return load


def _call(command: str, session: str = "a-session", cwd: str = ".",
          background: bool = False) -> dict:
    return {
        "tool_name": GUARDED_TOOL,
        "session_id": session,
        "cwd": cwd,
        "tool_input": {"command": command, "run_in_background": background},
    }


def _exit(event: str, cwd: str, session: str = "a-session", command: str = "") -> dict:
    """An exit payload. ⛔ **The directory is stated and has no default.**

    One arm of the release answer measures the tree the event names against its
    base, so a payload defaulting to `.` would point every lease assertion in
    this suite at **this** repository and reach the network from a suite that
    must not. The directory passed below is one that is no work tree at all.
    """
    return {
        "hook_event_name": event,
        "session_id": session,
        "cwd": cwd,
        "tool_input": {"command": command},
    }


def _plant_in(text: str, what: str, replacement: str) -> str:
    if what not in text:
        raise AssertionError(f"the plant's target {what!r} is not in the text")
    return text.replace(what, replacement, 1)


def _reword_heading(text: str, slug: str) -> str:
    out, planted = [], False
    for line in text.splitlines():
        if line.startswith("#") and _anchor(line.lstrip("#").strip()) == slug:
            out.append("#" * (len(line) - len(line.lstrip("#"))) + " Reworded")
            planted = True
            continue
        out.append(line)
    if not planted:
        raise AssertionError(f"no heading of the surface is anchored {slug!r} to reword")
    return "\n".join(out)


def self_test() -> int:  # noqa: PLR0915 -- one assertion per rule, read top to bottom
    out: list[str] = []
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        out.append(f"  {'ok  ' if ok else 'FAIL'}  {name}"
                   + (f" — {detail}" if detail and not ok else ""))
        if not ok:
            failures.append(name)

    def denied(answer: dict) -> bool:
        return answer.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"

    def reason(answer: dict) -> str:
        return str(answer.get("hookSpecificOutput", {}).get("permissionDecisionReason", ""))

    with tempfile.TemporaryDirectory() as directory:
        def fresh(name: str) -> Path:
            where = Path(directory) / name
            where.mkdir(parents=True, exist_ok=True)
            return where

        # ⛔ What every exit payload below names as its directory, and the reason
        # is the base-reading arm rather than the leases: that arm answers about
        # the tree the event names, so a payload naming `.` would point it at
        # this repository and reach the network from a suite that must not.
        outside = str(fresh("no-work-tree-at-all"))

        # --- a project with nothing exclusive -----------------------------
        out.append("A project with no capacity concept gets no capacity guard:")
        nothing = _a_config([])
        for command in (
            "a-claiming-command --with a-flag",
            "a-command-that-boots-something",
            "a-command naming a host, a port and a container",
        ):
            answered = guard_answer(
                _call(command), config=nothing, now=1000.0, store=fresh("none"),
                host=_a_host(comments=[]),
            )
            check(f"no answer for: {command[:48]}", answered == {}, repr(answered)[:120])
        check(
            "and no event gives anything back, there being nothing to give",
            release_answer(_exit("Stop", outside), config=nothing, now=1000.0,
                           store=fresh("none")) == {},
        )

        # --- the guard branches on the configuration and on nothing else ---
        out.append("")
        out.append("Every resource the guard names is one the configuration stated:")
        one = _a_config([_a_resource(name="the-first-thing", cap=1, claimed_by="claims-the-first")])
        two = _a_config([_a_resource(name="the-second-thing", cap=1, claimed_by="claims-the-second")])
        where = fresh("differential")
        first = guard_answer(_call("claims-the-first"), config=one, now=1000.0, store=where)
        check("a claiming call under one configuration takes a place", first == {})
        again = guard_answer(_call("claims-the-first", session="another"), config=one,
                             now=1000.0, store=where)
        check("and the next one is refused, the cap being one", denied(again))
        check("and the refusal names the resource the configuration named",
              "the-first-thing" in reason(again), reason(again)[:120])
        check("and names nothing the other configuration states",
              "the-second-thing" not in reason(again))
        check("the same call under the other configuration claims nothing",
              guard_answer(_call("claims-the-first"), config=two, now=1000.0,
                           store=fresh("differential-2")) == {})

        # --- the six exit paths -------------------------------------------
        out.append("")
        out.append("Every exit path either gives the place back or is covered by the sweep:")
        paths = [
            ("the call finished", "PostToolUse", False),
            ("the turn ended", "Stop", False),
            ("the session ended", "SessionEnd", False),
            ("a subagent stopped", "SubagentStop", False),
        ]
        for label, event, background in paths:
            where = fresh(f"exit-{event}")
            config = _a_config([_a_resource(cap=1)])
            check(f"{label}: the place is taken",
                  guard_answer(_call("a-claiming-command", background=background),
                               config=config, now=1000.0, store=where) == {})
            check(f"{label}: and the cap is then full",
                  denied(guard_answer(_call("a-claiming-command", session="another"),
                                      config=config, now=1000.0, store=where)))
            release_answer(_exit(event, outside, command="a-claiming-command"), config=config,
                           now=1000.0, store=where)
            check(f"{label}: and the place comes back on `{event}`",
                  guard_answer(_call("a-claiming-command", session="another"),
                               config=config, now=1001.0, store=where) == {})

        # ⛔ The path the harness publishes no event for. What is asserted is
        # not that an event fires: it is that the sweep at the end of the turn
        # releases a place whose call never reached a completion at all, which
        # is the only thing that can cover it.
        where = fresh("exit-denied")
        config = _a_config([_a_resource(cap=1)])
        guard_answer(_call("a-claiming-command"), config=config, now=1000.0, store=where)
        check("a call refused before it ran reaches no completion, and nothing registers one",
              "PermissionDecision" not in RELEASE_EVENTS
              and not any("denial" in event.lower() for event in RELEASE_EVENTS))
        check("so the end-of-turn sweep is what gives that place back",
              bool(release(where, "a-session", "session", "", 1000.0)))
        check("and the cap is free again",
              guard_answer(_call("a-claiming-command", session="another"), config=config,
                           now=1000.0, store=where) == {})

        # --- the backgrounded path ----------------------------------------
        out.append("")
        out.append("A backgrounded call's place is skipped by every sweep and expires instead:")
        where = fresh("background")
        config = _a_config([_a_resource(cap=1, ttl=120)])
        check("it is taken",
              guard_answer(_call("a-claiming-command", background=True), config=config,
                           now=1000.0, store=where) == {})
        for event in sorted(RELEASE_EVENTS):
            release_answer(_exit(event, outside, command="a-claiming-command"), config=config,
                           now=1000.0, store=where)
        check("and no event released it, the work still running",
              denied(guard_answer(_call("a-claiming-command", session="another"),
                                  config=config, now=1010.0, store=where)))
        check("and it is gone once its lifetime is up",
              guard_answer(_call("a-claiming-command", session="another"), config=config,
                           now=1121.0, store=where) == {})

        # --- the sum, and the maximum that let a third through -------------
        out.append("")
        out.append("What is compared against the cap is the sum, never the maximum:")
        where = fresh("sum")
        config = _a_config([_a_resource(cap=2, probe="a-command-that-counts-them")])
        taken = guard_answer(_call("a-claiming-command"), config=config, now=1000.0,
                             store=where, probe=_a_probe(count=1))
        check("a call joins a resource the probe already reports one of", taken == {})
        third = guard_answer(_call("a-claiming-command", session="another"), config=config,
                             now=1000.0, store=where, probe=_a_probe(count=1))
        check("and the next is refused: one reported plus one young lease is the cap",
              denied(third), repr(third)[:140])
        leases = live_leases(where, 1000.0)
        standing, keys = occupancy(config.get("branch_model.exclusive_resources")[0], leases, 1)
        check("the sum is what reached the cap", standing == 2, f"was {standing}")
        check("and a maximum would have left a place free, which is the measured defect",
              max(1, len(keys)) < 2, f"maximum was {max(1, len(keys))}")

        out.append("")
        out.append("A count that could not be established holds nothing, and says so:")
        where = fresh("unestablished")
        config = _a_config([_a_resource(cap=1, probe="a-command-that-counts-them")])
        for label, probe in (
            ("a probe that exits non-zero", _a_probe(code=1)),
            ("a probe that prints something that is not a count", _a_probe(prints="lots\n")),
            ("a probe that prints nothing at all", _a_probe(prints="")),
        ):
            answered = guard_answer(_call("a-claiming-command"), config=config, now=1000.0,
                                    store=where, probe=probe)
            check(f"{label}: the call proceeds", not denied(answered))
            check(f"{label}: and the answer says no place was held",
                  "no place was held" in str(answered.get("systemMessage", "")),
                  repr(answered)[:140])
        check("and nothing was written, so no place is held by a count nobody read",
              not live_leases(where, 1000.0))

        out.append("")
        out.append("`probe: null` is a stated absence and not a count of zero:")
        where = fresh("null-probe")
        config = _a_config([_a_resource(cap=1, probe=None)])
        check("the first call takes the only place",
              guard_answer(_call("a-claiming-command"), config=config, now=1000.0,
                           store=where) == {})
        check("and the second is refused on the leases alone",
              denied(guard_answer(_call("a-claiming-command", session="another"),
                                  config=config, now=1000.0, store=where)))

        # --- what holds a place -------------------------------------------
        out.append("")
        out.append("What holds a place is the subject, and the two release differently:")
        where = fresh("subject-tree")
        config = _a_config([_a_resource(cap=1, subject="tree")])
        check("one tree's first call takes the place",
              guard_answer(_call("a-claiming-command", cwd=directory), config=config,
                           now=1000.0, store=where) == {})
        check("a second session in the same tree shares it rather than queueing",
              guard_answer(_call("a-claiming-command", session="another", cwd=directory),
                           config=config, now=1000.0, store=where) == {})
        check("and another tree queues against it",
              denied(guard_answer(_call("a-claiming-command", session="third",
                                        cwd=str(Path(directory) / "subject-tree")),
                                  config=config, now=1000.0, store=where)))
        where = fresh("subject-call")
        config = _a_config([_a_resource(cap=2, subject="call")])
        guard_answer(_call("a-claiming-command --one"), config=config, now=1000.0, store=where)
        guard_answer(_call("a-claiming-command --two"), config=config, now=1000.0, store=where)
        check("two calls in one session each hold their own",
              denied(guard_answer(_call("a-claiming-command --three"), config=config,
                                  now=1000.0, store=where)))
        release_answer(_exit("PostToolUse", outside, command="a-claiming-command --one"),
                       config=config, now=1000.0, store=where)
        check("and releasing one does not release its sibling",
              len(live_leases(where, 1000.0)) == 1,
              f"{len(live_leases(where, 1000.0))} left")

        # --- the record ---------------------------------------------------
        out.append("")
        out.append("A recorded answer round-trips through the form the surface states:")
        body = record_body(MERGE_QUESTION, "nobody is going to look | by their decision",
                           "a-person", "2026-01-01T00:00:00Z")
        read = answers_in(body)
        check("exactly one answer is read back", len(read) == 1, repr(read)[:140])
        check("and the answer carrying a pipe survives it",
              read and read[0]["answer"] == "nobody is going to look | by their decision",
              repr(read)[:140])
        check("and the question and the answerer come back as written",
              read and read[0]["question"] == MERGE_QUESTION
              and read[0]["answered by"] == "a-person")
        check("a table with no marker above it is nobody's record",
              not answers_in(body.replace(RECORD_MARKER, "Some notes")))
        check("a record with no answer in it is not an answer",
              recorded_answer([record_body(MERGE_QUESTION, "", "a-person", "x")],
                              MERGE_QUESTION) is None)
        check("a record with no answerer in it is not an answer either",
              recorded_answer([record_body(MERGE_QUESTION, "yes", "", "x")],
                              MERGE_QUESTION) is None)
        later = recorded_answer(
            [record_body(MERGE_QUESTION, "first", "a-person", "x"),
             record_body(MERGE_QUESTION, "second", "a-person", "y")],
            MERGE_QUESTION,
        )
        check("and the standing answer is the last one recorded",
              later and later["answer"] == "second", repr(later))
        check("an address with no repository in it is refused",
              write_record("7", MERGE_QUESTION, "yes", "a-person", "x")[1] == 2)
        # ⛔ The vocabulary is the surface's, so a near-miss spelling is refused
        # rather than written under a name no guard reads.
        refused, status = write_record("an-owner/a-repository#7", "read-by-a-person", "yes",
                                       "a-person", "x")
        check("a question outside the surface's own list is refused", status == 2)
        check("and the refusal names the list it is not in",
              MERGE_QUESTION in refused, refused[:140])

        # ⛔ The write arm reaches the host only through the runner handed to it,
        # and this is the one assertion that exercises the whole of it. ⚠️ Every
        # refusal above returns before any host call, which is what keeps this
        # suite off the network — asserted here by taking the arm all the way
        # through a stand-in that records what it was handed.
        sent: list[str] = []

        def _records(args, _timeout):
            sent.append(Path(args[args.index("--body-file") + 1]).read_text(encoding="utf-8"))
            return 0, "an-address-the-host-printed"

        printed, status = write_record("an-owner/a-repository#7", MERGE_QUESTION,
                                       "nobody is going to look", "a-person",
                                       "2026-01-01T00:00:00Z", run=_records)
        check("a well-formed record is written, and the arm says where", status == 0
              and "an-owner/a-repository#7" in printed, printed[:140])
        check("and what reached the host parses back as the answer that was given",
              len(sent) == 1
              and recorded_answer(sent, MERGE_QUESTION) is not None
              and recorded_answer(sent, MERGE_QUESTION)["answer"] == "nobody is going to look",
              repr(sent)[:160])
        check("and the guard allows a merge on exactly that comment",
              guard_answer(_call("gh pr merge 7"), config=_a_config([]), now=1000.0,
                           store=fresh("written"), host=_a_host(comments=sent)) == {})

        # --- the merge guard ----------------------------------------------
        out.append("")
        out.append("The guard on a merge reads that record and nothing else:")
        config = _a_config([])
        for label, command in (
            ("the client's own subcommand", "gh pr merge 7 --squash"),
            ("the same with the repository named", "gh pr merge 7 --repo an-owner/a-repository"),
            ("the same act through the raw arm",
             "gh api --method PUT repos/an-owner/a-repository/pulls/7/merge"),
            ("and through the raw arm with a field, which the client sends as a write",
             "gh api repos/an-owner/a-repository/pulls/7/merge -f merge_method=squash"),
            ("and with no number, resolved from the branch", "gh pr merge --squash"),
        ):
            answered = guard_answer(_call(command), config=config, now=1000.0,
                                    store=fresh("merge"), host=_a_host(comments=[]))
            check(f"{label}: refused with no record", denied(answered), repr(answered)[:140])
            check(f"{label}: and the refusal names what would unblock it",
                  "--question" in reason(answered) and MERGE_QUESTION in reason(answered),
                  reason(answered)[:160])
        recorded = [record_body(MERGE_QUESTION, "a person is reading it", "a-person",
                                "2026-01-01T00:00:00Z")]
        check("allowed once the answer is on the change",
              guard_answer(_call("gh pr merge 7"), config=config, now=1000.0,
                           store=fresh("merge"), host=_a_host(comments=recorded)) == {})
        other = [record_body("merge_now", "yes", "a-person", "2026-01-01T00:00:00Z")]
        check("and still refused where only the merge ask was recorded, which this act writes",
              denied(guard_answer(_call("gh pr merge 7"), config=config, now=1000.0,
                                  store=fresh("merge"), host=_a_host(comments=other))))
        check("a record that could not be read is refused, not read as absent",
              denied(guard_answer(_call("gh pr merge 7"), config=config, now=1000.0,
                                  store=fresh("merge"), host=_a_host(code=1))))
        check("and that refusal says what it could not establish",
              "could not be established" in reason(
                  guard_answer(_call("gh pr merge 7"), config=config, now=1000.0,
                               store=fresh("merge"), host=_a_host(code=1))))
        check("a change nothing could resolve is refused too",
              denied(guard_answer(_call("gh pr merge"), config=config, now=1000.0,
                                  store=fresh("merge"), host=_a_host(number=None))))
        # ⛔ The change named in a form this cannot read is refused rather than
        # resolved to the branch's, which would check one change's merge against
        # another change's record.
        answered = guard_answer(_call("gh pr merge a-branch-name --squash"), config=config,
                                now=1000.0, store=fresh("merge"),
                                host=_a_host(comments=recorded))
        check("a change named by its branch is refused rather than resolved to the branch's",
              denied(answered), repr(answered)[:140])
        check("and the refusal quotes the name it could not resolve",
              "a-branch-name" in reason(answered), reason(answered)[:140])
        check("the same change named as an address is read",
              guard_answer(
                  _call("gh pr merge https://a-host.invalid/an-owner/a-repository/pull/7"),
                  config=config, now=1000.0, store=fresh("merge"),
                  host=_a_host(comments=recorded)) == {})
        # ⚠️ The flag-value measurement: with `--repo`'s value read as a
        # positional, a merge naming no change was checked against the slug.
        check("a merge naming no change reads past the repository flag's value",
              guard_answer(_call("gh pr merge --repo an-owner/a-repository --squash"),
                           config=config, now=1000.0, store=fresh("merge"),
                           host=_a_host(comments=recorded, number=7)) == {})
        check("and a merge naming no repository, with none configured, is refused",
              denied(guard_answer(_call("gh pr merge 7"), config=_a_config([], repo=None),
                                  now=1000.0, store=fresh("merge"),
                                  host=_a_host(comments=recorded))))

        # ⛔ The measured leak, asserted directly rather than implied by the
        # ordering of the code: a place taken by a call that is then refused is a
        # place nothing releases, a call refused before it runs reaching no event
        # at all.
        out.append("")
        out.append("A call this guard refuses leaves no place behind:")
        where = fresh("ordering")
        both = _a_config([_a_resource(cap=1, claimed_by="pr merge")])
        answered = guard_answer(_call("gh pr merge 7"), config=both, now=1000.0,
                                store=where, host=_a_host(comments=[]))
        check("the merge is refused", denied(answered))
        check("and nothing was held on its way to being refused",
              not live_leases(where, 1000.0),
              f"{len(live_leases(where, 1000.0))} lease(s) left behind")

        # ⛔ The same rule across resources rather than across arms: one call may
        # claim several, and a place taken for a call a later resource refuses is
        # a place nothing releases.
        out.append("")
        out.append("A call refused on one resource gives back the place it took on another:")
        where = fresh("several")
        several = _a_config([
            _a_resource(name="the-free-one", cap=2, claimed_by="a-claiming-command"),
            _a_resource(name="the-full-one", cap=1, claimed_by="a-claiming-command"),
        ])
        guard_answer(_call("a-claiming-command", session="the-holder"), config=several,
                     now=1000.0, store=where)
        before = len(live_leases(where, 1000.0))
        answered = guard_answer(_call("a-claiming-command", session="another"), config=several,
                                now=1000.0, store=where)
        check("the call is refused on the resource that is full", denied(answered))
        check("and names only that one", "the-full-one" in reason(answered)
              and "the-free-one" not in reason(answered), reason(answered)[:140])
        check("and left no place behind on the one that had room",
              len(live_leases(where, 1000.0)) == before,
              f"{len(live_leases(where, 1000.0))} lease(s), was {before}")

        out.append("")
        out.append("And it answers for a merge and for nothing else:")
        for label, command in (
            ("a read of the same change", "gh pr view 7 --json state"),
            ("a path that merely contains the word", "gh api repos/an-owner/a-repository/merges"),
            ("a local merge of branches", "git -C . merge --no-ff a-branch"),
            ("a tool that is not the guarded one", ""),
            # ⚠️ The same path, read rather than written — which is one of the
            # reads the finishing role makes *before* it merges anything, so a
            # grammar firing on the path alone would refuse it.
            ("the raw arm read rather than written",
             "gh api repos/an-owner/a-repository/pulls/7/merge"),
            ("and the same read with its method stated",
             "gh api --method GET repos/an-owner/a-repository/pulls/7/merge"),
        ):
            payload = _call(command) if command else {"tool_name": "Write", "tool_input": {}}
            answered = guard_answer(payload, config=config, now=1000.0, store=fresh("merge"),
                                    host=_a_host(comments=[]))
            check(f"{label}: no answer", answered == {}, repr(answered)[:140])

        # --- the run the host has already made ------------------------------
        out.append("")
        out.append("A command the host has already run for this commit is refused:")

        def already(command: str, project=None, runs=None, jobs=None, mergeable=None,
                    host_code: int = 0, tree=None, environment=None, probe=None) -> dict:
            return already_run_guard(
                project if project is not None else _a_project(A_MIRRORED_RUN),
                command,
                host=_a_host_making(runs=runs if runs is not None else [_a_run()],
                                    jobs=jobs, mergeable=mergeable, code=host_code),
                code=tree if tree is not None else _a_tree(),
                environment=environment if environment is not None else {},
                probe=probe,
            )

        def said(answer: dict) -> str:
            return str(answer.get("systemMessage", ""))

        answered = already("a-mirrored-command")
        check("the mirrored command in command position is refused", denied(answered),
              repr(answered)[:160])
        check("and the refusal names the run it was refused on",
              "A workflow" in reason(answered), reason(answered)[:160])
        check("and names what would unblock it",
              "Edit the tree" in reason(answered), reason(answered)[:200])

        # ⛔ The measured defect this arm exists against: a predicate matching the
        # raw string took a build slot for a text search whose prose merely
        # carried the command.
        out.append("")
        out.append("A call whose prose merely carries that command is not that command:")
        for label, command in (
            ("a search for it", "a-searching-command 'a-mirrored-command' a-file"),
            ("a message naming it", "a-printing-command a-mirrored-command"),
            ("it as a flag's value", "a-command --with-argument a-mirrored-command"),
            ("a longer word beginning with it", "a-mirrored-command-that-is-another"),
        ):
            answered = already(command)
            check(f"{label}: no answer", answered == {}, repr(answered)[:160])
        for label, command in (
            ("after a separator", "a-command && a-mirrored-command"),
            ("after a leading assignment", "A_VARIABLE=a-value a-mirrored-command"),
            ("with flags of its own", "a-mirrored-command --with-a-flag"),
        ):
            check(f"{label}: still the command, and refused", denied(already(command)),
                  repr(already(command))[:160])

        # ⛔ The exit-status measurement. The client exits non-zero while runs are
        # pending *and* when one has failed, so both readings are planted: a
        # pending run is not green, and a failed one is not absent.
        out.append("")
        out.append("A pending run does not read as green, and a failed one does not read as absent:")
        for label, run_state in (
            ("a run still in progress", _a_run(status="in_progress", conclusion=None)),
            ("a run that concluded red", _a_run(conclusion="failure")),
            ("a run still queued", _a_run(status="queued", conclusion=None)),
        ):
            answered = already("a-mirrored-command", runs=[run_state])
            check(f"{label}: refused, the run existing for this commit", denied(answered),
                  repr(answered)[:160])
        check("and the host answering nothing at all proceeds rather than refusing",
              not denied(already("a-mirrored-command", host_code=1)))
        check("naming it as unestablished rather than as no run",
              UNESTABLISHED in said(already("a-mirrored-command", host_code=1)),
              said(already("a-mirrored-command", host_code=1))[:160])

        out.append("")
        out.append("Each state where the host's run does not answer about this code proceeds:")
        for label, kwargs, answer in (
            ("the tree carries uncommitted work",
             {"tree": _a_tree(dirty=True)}, NOTHING_HAS_RUN),
            # ⚠️ The head having moved is this same answer and reaches it by the
            # same route: the runs are asked for by commit, so a commit the host
            # has no run of comes back empty however many runs the branch has.
            ("the commit in the tree is one the host has no run of",
             {"tree": _a_tree(head="a-commit-the-host-has-not-seen"), "runs": []},
             NOTHING_HAS_RUN),
            # ⛔ The path-filtered case, which is why *some live check* says
            # nothing about the command in hand: the host ran something for this
            # commit, and it was not the run that mirrors this command.
            ("a run exists for this commit and the mirroring workflow is not it",
             {"runs": [_a_run(workflow="Another workflow")]}, NOTHING_HAS_RUN),
            # ⛔ § 2's environment failure, which is a fact about where the run
            # was made rather than about the change — and therefore a run that
            # answered nothing, not a fact this arm could not establish.
            ("the host never started the run",
             {"runs": [_a_run(conclusion="startup_failure")]}, NOTHING_HAS_RUN),
            ("the run is awaiting an action",
             {"runs": [_a_run(conclusion="action_required")]}, NOTHING_HAS_RUN),
            ("the commit in the tree could not be read",
             {"tree": _a_tree(unread="a reason")}, UNESTABLISHED),
        ):
            answered = already("a-mirrored-command", **kwargs)
            check(f"{label}: the call proceeds", not denied(answered), repr(answered)[:160])
            check(f"{label}: and the answer is `{answer}`", answer in said(answered),
                  said(answered)[:200])

        # ⛔ § 2's third precondition, reproduced in review as a defect: with the
        # jobs read only where the facet names one, every one of these refused
        # the local check on the strength of a run that had executed nothing —
        # and a run cancelled in the queue is routine on an account whose runners
        # take one job at a time, so this was firing rather than theoretical.
        out.append("")
        out.append("A run that concluded without executing a step is no answer about the command:")
        no_step = [{"name": "a-job", "status": "completed", "steps": []}]
        for label, conclusion, status, jobs in (
            ("cancelled in the queue", "cancelled", "completed", no_step),
            ("skipped entirely", "skipped", "completed", no_step),
            ("concluded neutral having run nothing", "neutral", "completed", no_step),
            ("with no job listed at all", "cancelled", "completed", []),
        ):
            answered = already("a-mirrored-command",
                               runs=[_a_run(status=status, conclusion=conclusion)], jobs=jobs)
            check(f"a run {label}: the call proceeds", not denied(answered),
                  repr(answered)[:160])
            check(f"a run {label}: and the answer is `{NOTHING_HAS_RUN}`",
                  NOTHING_HAS_RUN in said(answered), said(answered)[:200])
        # ⛔ And the other side of the same condition, which is what keeps the
        # check from being met by standing every refusal down: a run the host is
        # still working on has executed no step either, and is the duplicate this
        # guard exists for rather than an absence.
        for label, status in (("queued", "queued"), ("in progress", "in_progress")):
            check(f"a run still {label} is refused, the time being spent now",
                  denied(already("a-mirrored-command",
                                 runs=[_a_run(status=status, conclusion=None)], jobs=no_step)))
        check("and a run that executed steps and was then cancelled is refused",
              denied(already("a-mirrored-command",
                             runs=[_a_run(conclusion="cancelled")], jobs=A_JOB_THAT_RAN)))

        # ⛔ § 2's ranking across a command two entries mirror, reproduced in
        # review as the mirror image of what the facet states: with one record
        # read, a command mirrored twice reported *nothing has run* and named a
        # workflow that was not the one the host had run.
        out.append("")
        out.append("A command two entries mirror is answered on whichever of them the host ran:")
        twice = _a_project([
            {"workflow": "A workflow", "mirrors": "a-mirrored-command",
             "triggers": "pull_request -> *"},
            {"workflow": "Another workflow", "mirrors": "a-mirrored-command",
             "triggers": "pull_request -> *"},
        ])
        check("the facet states two records for the one command",
              len(twice.mirrors()) == 2, f"{len(twice.mirrors())} record(s)")
        for label, workflow in (
            ("the entry written first", "A workflow"),
            ("the entry written second", "Another workflow"),
        ):
            answered = already("a-mirrored-command", project=twice,
                               runs=[_a_run(workflow=workflow)])
            check(f"a run of {label} refuses the call", denied(answered),
                  repr(answered)[:160])
            check(f"and the refusal names {label} rather than a sibling",
                  workflow in reason(answered), reason(answered)[:160])
        check("and neither having run leaves the call proceeding",
              not denied(already("a-mirrored-command", project=twice,
                                 runs=[_a_run(workflow="A third workflow")])))

        # ⛔ The fourth value, and the reason it is not folded into the first: an
        # empty run list on a conflicted change has the opposite remedy, and a
        # reader told *nothing has run* is sent to run a suite that cannot land.
        out.append("")
        out.append("A conflicted change is told apart from one nothing has run for:")
        conflicted = already("a-mirrored-command", runs=[], mergeable="CONFLICTING")
        check("the call proceeds", not denied(conflicted))
        check("and the answer is the conflict rather than the absence",
              NOTHING_CAN_RUN in said(conflicted) and NOTHING_HAS_RUN not in said(conflicted),
              said(conflicted)[:200])
        check("and it names the remedy as resolving it rather than running anything",
              "conflicted" in said(conflicted), said(conflicted)[:200])
        check("while the same empty list with no conflict is the other answer",
              NOTHING_HAS_RUN in said(already("a-mirrored-command", runs=[], mergeable="MERGEABLE")))

        # ⛔ The keying rule, held on the one shape that can disagree with it: a
        # workflow whose job mirrors the command, where a job-keyed reading
        # refused a build on the strength of a check that validated a title.
        out.append("")
        out.append("Where the facet names a job, the job is what the run is read on:")
        jobbed = _a_project(A_MIRRORED_JOB)
        check("a run whose job executed steps is refused",
              denied(already("a-mirrored-command", project=jobbed,
                             jobs=[{"name": "a-job", "steps": [{"name": "a-step"}]}])))
        check("a run that executed no job of that name proceeds",
              not denied(already("a-mirrored-command", project=jobbed,
                                 jobs=[{"name": "another-job", "steps": [{"name": "a-step"}]}])))
        check("and a job that executed no step proceeds, which is not its conclusion",
              not denied(already("a-mirrored-command", project=jobbed,
                                 jobs=[{"name": "a-job", "steps": []}])))
        # ⛔ The in-flight arm read one level down, and the only plant that
        # reaches it: a workflow still going is answered for at the workflow
        # level before any job is read, so without a job of its own in flight
        # that arm could be deleted with the suite staying green — measured by
        # deleting it and watching nothing redden.
        check("a job the host is still running is refused, no step having executed yet",
              denied(already("a-mirrored-command", project=jobbed,
                             runs=[_a_run(status="in_progress", conclusion=None)],
                             jobs=[{"name": "a-job", "status": "in_progress",
                                    "steps": []}])))

        # --- the two ways a refusal stands down -----------------------------
        out.append("")
        out.append("The two ways a refusal stands down, and the way that is not one:")
        exempted = _a_project(A_MIRRORED_RUN, never_guard=["a-mirrored-command --with-a-flag"])
        check("a `never_guard` command is not refused",
              not denied(already("a-mirrored-command --with-a-flag", project=exempted)))
        check("and the answer names the list it was exempted by",
              "never_guard" in said(already("a-mirrored-command --with-a-flag",
                                            project=exempted)))
        check("while the shorter form it is a variant of is still refused",
              denied(already("a-mirrored-command", project=exempted)))
        escaped = _a_project(A_MIRRORED_RUN, escape="A_VARIABLE")
        check("the escape set to a reason stands the refusal down",
              not denied(already("a-mirrored-command", project=escaped,
                                 environment={"A_VARIABLE": "because the evidence is wrong"})))
        check("and the answer carries the reason the person gave",
              "the evidence is wrong" in said(
                  already("a-mirrored-command", project=escaped,
                          environment={"A_VARIABLE": "because the evidence is wrong"})))
        check("the escape set to nothing is not an escape",
              denied(already("a-mirrored-command", project=escaped,
                             environment={"A_VARIABLE": "   "})))
        check("and the refusal then names the variable as what would unblock it",
              "A_VARIABLE" in reason(already("a-mirrored-command", project=escaped,
                                             environment={"A_VARIABLE": ""})))

        out.append("")
        out.append("A project's own probe answers the operational condition, and only that one:")
        probed = _a_project(A_MIRRORED_RUN, operational_when="a-command-that-probes")
        check("a probe printing the stated word leaves the refusal standing",
              denied(already("a-mirrored-command", project=probed,
                             probe=_a_probe(prints=f"{OPERATIONAL}\n"))))
        for label, probe in (
            ("a probe printing anything else", _a_probe(prints="a-state-of-some-kind\n")),
            ("a probe that exits non-zero", _a_probe(code=1)),
            ("a probe that prints nothing", _a_probe(prints="")),
        ):
            answered = already("a-mirrored-command", project=probed, probe=probe)
            check(f"{label}: the call proceeds", not denied(answered), repr(answered)[:160])
            check(f"{label}: and the answer names the probe rather than the host",
                  "operational_when" in said(answered), said(answered)[:200])

        # ⛔ The project with nothing mirrored, which is a configuration rather
        # than a misconfiguration: there is no command to match, so no call here
        # is ever answered.
        out.append("")
        out.append("A project whose host runs no check is guarded by nothing:")
        empty = _a_project([])
        for command in ("a-mirrored-command", "a-command-of-any-kind --with-a-flag"):
            check(f"no answer for: {command}", already(command, project=empty) == {},
                  repr(already(command, project=empty))[:140])

        # ⛔ The ordering, asserted on this arm as it is on the merge guard: a
        # place taken by a call this arm then refuses is a place nothing releases.
        out.append("")
        out.append("A call this arm refuses leaves no place behind either:")
        where = fresh("already-run-ordering")
        claiming = _a_project(A_MIRRORED_RUN)
        claiming.data["branch_model"]["exclusive_resources"] = [
            _a_resource(cap=1, claimed_by="a-mirrored-command")
        ]
        answered = guard_answer(
            _call("a-mirrored-command"), config=claiming, now=1000.0, store=where,
            host=_a_host(comments=[]), runs=_a_host_making(runs=[_a_run()]),
            code=_a_tree(),
        )
        check("the call is refused", denied(answered), repr(answered)[:160])
        check("and nothing was held on its way to being refused",
              not live_leases(where, 1000.0),
              f"{len(live_leases(where, 1000.0))} lease(s) left behind")

        # --- what a project that states no configuration gets ---------------
        #
        # ⛔ Every answer the arm has, in a project that has adopted nothing:
        # none of them. ⚠️ Reached through the reader rather than by handing the
        # arm a `None`, here and in the pair below: the arm resolves its own
        # configuration where none is passed, so a plant that passed one would be
        # asserting about a branch no session takes.
        out.append("")
        out.append("A project that states no configuration is answered with nothing at all:")
        for label, root in (
            ("a root that is not there", "/nonexistent-root-for-the-self-test"),
            ("a root with no configuration in it", _a_root(Path(directory) / "adopted-nothing",
                                                           None)),
        ):
            where = fresh("unconfigured")
            answered = guard_answer(_call("a-claiming-command", cwd=root), now=1000.0,
                                    store=where)
            check(f"{label}: a claiming call is answered with nothing", answered == {},
                  repr(answered)[:140])
            # ⛔ The irreversible act too, which is the one this arm exists to
            # refuse: a host answering no record would deny if it were reached.
            merging = guard_answer(_call("gh pr merge 7", cwd=root), now=1000.0, store=where,
                                   host=_a_host(comments=[]))
            check(f"{label}: and a merge is not refused either", merging == {},
                  repr(merging)[:140])
            check(f"{label}: and no place was held", not live_leases(where, 1000.0))
            check(f"{label}: and no exit event gives anything back",
                  release_answer(_exit("Stop", outside, command="a-claiming-command"), now=1000.0,
                                 store=where) == {})

        # --- the two directions a guard fails in ---------------------------
        out.append("")
        out.append("The two directions a guard fails in are the two the surface states:")
        # ⛔ A configuration that is *there* and does not resolve, which is the
        # other half of the pair above: the file is the project's own facts badly
        # written, so it is reported rather than read as a project that adopted
        # nothing. A plant pointed at an absent file would take the silent branch
        # and assert this message on a route no session reaches.
        unreadable = _a_root(Path(directory) / "states-something-unreadable",
                             "- not a block of keys\n")
        answered = guard_answer(
            _call("a-claiming-command", cwd=unreadable),
            now=1000.0, store=fresh("unreadable"),
        )
        check("a configuration that could not be read holds the call to nothing, and says so",
              "held to nothing" in str(answered.get("systemMessage", "")), repr(answered)[:140])
        # ⛔ The message is the repair or it is noise once per call: measured, a
        # required key added to the surface held every command in five live
        # projects to nothing for a day, under a message naming no key.
        check("and it carries the reader's own stop rather than only that there was one",
              "the repair:" in str(answered.get("systemMessage", ""))
              and "not a block of keys" in str(answered.get("systemMessage", "")),
              str(answered.get("systemMessage", ""))[:220])
        check("and gives nothing back on an exit either, there being nothing read to release",
              release_answer(_exit("Stop", outside), now=1000.0,
                             store=fresh("unreadable")) == {})
        check("while a merge whose record could not be read is refused",
              denied(guard_answer(_call("gh pr merge 7"), config=_a_config([]), now=1000.0,
                                  store=fresh("merge"), host=_a_host(code=1))))

        out.append("")
        out.append("A payload neither arm can read interrupts nothing:")
        answered = io.StringIO()
        check("a broken payload exits 0", hook(io.StringIO("not json"), guard_answer,
                                               answered) == 0)
        check("and reports that nothing held the command",
              "held to nothing" in answered.getvalue(), answered.getvalue()[:140])
        released = io.StringIO()
        check("and the release arm says nothing at all",
              hook(io.StringIO("not json"), release_answer, released) == 0
              and not released.getvalue())

        # --- the report ---------------------------------------------------
        out.append("")
        out.append("The report says what is held, and what it could not establish:")
        where = fresh("report")
        config = _a_config([_a_resource(cap=2, probe="a-command-that-counts-them")])
        guard_answer(_call("a-claiming-command"), config=config, now=1000.0, store=where,
                     probe=_a_probe(count=1))
        printed, status = held_report(config, now=1000.0, store=where,
                                      probe=_a_probe(count=1))
        check("it exits 0", status == 0)
        check("and names the resource and the sum against its cap",
              "a-held-thing" in printed and "2 against the cap" in printed,
              " ".join(printed.split())[:160])
        printed, _ = held_report(config, now=1000.0, store=where, probe=_a_probe(code=1))
        check("and an unestablished count is named rather than shown as zero",
              "unestablished" in printed, " ".join(printed.split())[:160])
        printed, _ = held_report(_a_config([]), now=1000.0, store=where)
        check("a project with nothing exclusive is reported as stating so",
              "states it" in printed, " ".join(printed.split())[:160])

        # --- the branch against its base ----------------------------------
        #
        # ⛔ Real repositories and a real remote on disk, with no stand-in
        # anywhere: what is in question is what git itself says about a base
        # whose hashes changed, and a fake would assert the fake's own idea of a
        # patch. ⚠️ The remote is a bare repository beside the tree, so the suite
        # reaches no network.
        out.append("")
        out.append("A branch level with its base is reported as level, naming the tree:")
        _origin, _seed, tree = _a_published_base(fresh("level"))
        _a_commit(tree, "mine.txt")
        answer, figure, said = behind_of(tree)
        check(f"the answer is `{LEVEL}`", answer == LEVEL, f"was {answer!r}: {said}")
        check("and the figure is nought rather than absent", figure == 0, f"was {figure!r}")
        check("and it names the tree the answer was taken in", tree in said, said[:200])
        check("and the branch in it", "a-branch" in said, said[:200])

        out.append("")
        out.append("A base that has genuinely advanced is reported behind, with its figure:")
        _origin, seed, tree = _a_published_base(fresh("behind"))
        _a_commit(tree, "mine.txt")
        _a_commit(seed, "theirs.txt")
        _a_commit(seed, "theirs-again.txt")
        _in(seed, "push", "--quiet", "origin", "main")
        answer, figure, said = behind_of(tree)
        check("a head the remote reports and this tree does not hold is behind with no figure",
              answer == BEHIND and figure is None, f"{answer!r}, {figure!r}: {said}")
        check("and never level", answer != LEVEL, f"was {answer!r}")
        check("and it names the fetch that would establish the figure",
              "fetch" in said, said[:240])
        _in(tree, "fetch", "--quiet", "origin")
        answer, figure, said = behind_of(tree)
        check("once the tree holds the base the figure is the commits it gained",
              answer == BEHIND and figure == 2, f"{answer!r}, {figure!r}: {said}")
        check("and what clears it is named rather than described",
              "brought into this branch" in said, said[:240])

        # ⛔ The plant the whole reading exists for, and the two readings § 7
        # forbids are computed beside it rather than argued about: both of them
        # call this branch behind, and the base carries every patch it has.
        out.append("")
        out.append("A base whose history was rewritten is level, where ancestry and a count are not:")
        _origin, seed, tree = _a_published_base(fresh("rewritten"))
        _a_commit(tree, "mine.txt")
        _rewrite_the_base(seed)
        _in(tree, "fetch", "--quiet", "origin")
        head = _in(tree, "rev-parse", "origin/main")
        answer, figure, said = behind_of(tree)
        check(f"the answer is `{LEVEL}`", answer == LEVEL and figure == 0,
              f"{answer!r}, {figure!r}: {said}")
        counted = _in(tree, "rev-list", "--count", "--right-only", f"HEAD...{head}")
        check("a plain count of the base's commits would have said behind",
              int(counted) > 0, f"the count was {counted}, so the plant is a no-op")
        ancestry = subprocess.run(
            ["git", "-C", tree, "merge-base", "--is-ancestor", head, "HEAD"],
            capture_output=True, text=True,
        )
        check("and ancestry would have said behind too",
              ancestry.returncode != 0,
              f"ancestry exited {ancestry.returncode}, so the plant is a no-op")
        _a_commit(seed, "theirs.txt")
        _in(seed, "push", "--quiet", "origin", "main")
        _in(tree, "fetch", "--quiet", "origin")
        answer, figure, said = behind_of(tree)
        check("while a rewritten base that also advanced is behind by what it gained",
              answer == BEHIND and figure == 1, f"{answer!r}, {figure!r}: {said}")

        # ⚠️ The surface says the figure is a floor and not a total, because a
        # merge commit carries no patch of its own. Held by a run rather than
        # left as a sentence: the base here gains two commits and one of them is
        # the merge, and the figure is one.
        out.append("")
        out.append("A merge commit on the base carries no patch, so the figure is a floor:")
        _origin, seed, tree = _a_published_base(fresh("a-merge-on-the-base"))
        _a_commit(tree, "mine.txt")
        _in(seed, "checkout", "--quiet", "-b", "a-sibling")
        _a_commit(seed, "theirs.txt")
        _in(seed, "checkout", "--quiet", "main")
        _in(seed, "merge", "--quiet", "--no-ff", "-m", "merge the sibling", "a-sibling")
        _in(seed, "push", "--quiet", "origin", "main")
        _in(tree, "fetch", "--quiet", "origin")
        answer, figure, said = behind_of(tree)
        check("the base gained two commits, one of them the merge",
              int(_in(tree, "rev-list", "--count", "--right-only",
                      f"HEAD...{_in(tree, 'rev-parse', 'origin/main')}")) == 2,
              "the plant put no merge commit on the base")
        check("and the figure is the one commit that carries a patch",
              answer == BEHIND and figure == 1, f"{answer!r}, {figure!r}: {said}")

        # ⚠️ The one limit the surface states, held by a run rather than left as
        # a sentence: a squash is a patch no commit of the branch matches.
        out.append("")
        out.append("A branch whose own work landed as a squash reads as behind by that one commit:")
        _origin, seed, tree = _a_published_base(fresh("squashed"))
        _a_commit(tree, "mine-one.txt")
        _a_commit(tree, "mine-two.txt")
        _in(tree, "push", "--quiet", "origin", "a-branch")
        _in(seed, "fetch", "--quiet", "origin", "a-branch")
        _in(seed, "merge", "--quiet", "--squash", "FETCH_HEAD")
        _in(seed, "commit", "--quiet", "-m", "the squash of the branch")
        _in(seed, "push", "--quiet", "origin", "main")
        _in(tree, "fetch", "--quiet", "origin")
        answer, figure, said = behind_of(tree)
        check("it is behind by one, the squash matching neither of its commits",
              answer == BEHIND and figure == 1, f"{answer!r}, {figure!r}: {said}")

        out.append("")
        out.append("A base that could not be reached or named is unestablished, never level:")
        _origin, _seed, tree = _a_published_base(fresh("unreachable"))
        _a_commit(tree, "mine.txt")
        _in(tree, "remote", "set-url", "origin",
            str(Path(directory) / "a-remote-that-is-not-there.git"))
        answer, _figure, said = behind_of(tree)
        check(f"a remote that does not answer is `{UNESTABLISHED}`", answer == UNESTABLISHED,
              f"was {answer!r}: {said}")
        check("and never level", answer != LEVEL, f"was {answer!r}")
        check("and it names the tree and which half it could not read",
              tree in said and "could not be read" in said, said[:240])
        origin, _seed, tree = _a_published_base(fresh("no-such-base"))
        _a_commit(tree, "mine.txt")
        _in(origin, "update-ref", "-d", "refs/heads/main")
        answer, _figure, said = behind_of(tree)
        check("a remote carrying no such branch is unestablished too",
              answer == UNESTABLISHED, f"was {answer!r}: {said}")
        check("and says the base is what it could not find",
              "no branch named" in said, said[:240])
        answer, _figure, said = behind_of(outside, load=_a_carrier_that_will_not_load)
        check("and a claim carrier that could not be loaded is unestablished, not silence",
              answer == UNESTABLISHED and "claim carrier" in said, f"{answer!r}: {said}")

        # ⛔ The defect the review of this change reproduced: three of this arm's
        # reads were unwrapped, so a read that could not run escaped the arm
        # rather than being answered — and took the sweep's own message with it,
        # two arms of one event lost to one read.
        out.append("")
        out.append("A read this arm cannot make at all is unestablished, and takes nothing with it:")
        _origin, _seed, tree = _a_published_base(fresh("unrunnable"))
        _a_commit(tree, "mine.txt")
        # ⚠️ Each call is caught here, and that is the plant rather than caution:
        # the defect's own shape is an escape, so a plant that let one propagate
        # would kill this suite instead of reddening the assertion written for
        # it — measured by restoring the defect and watching the run die with no
        # failure named at all.
        def answered_for(which: str) -> tuple:
            try:
                return behind_of(tree, load=_a_carrier_that_cannot_run(which))
            except Exception as error:  # noqa: BLE001 -- the defect is the escape
                return None, None, f"escaped the arm as {type(error).__name__}"

        for which in ("rev-parse", "cat-file", "cherry"):
            answer, figure, said = answered_for(which)
            check(f"a `{which}` that cannot run is `{UNESTABLISHED}` rather than an escape",
                  answer == UNESTABLISHED and figure is None, f"{answer!r}, {figure!r}: {said}")
            check(f"and the answer names `{which}` as what could not be run",
                  which in said, said[:240])
        check("while a `cat-file` that runs and finds nothing is behind, not unestablished",
              behind_of(tree)[0] == LEVEL, repr(behind_of(tree))[:200])
        where = fresh("unrunnable-store")
        config = _a_config([_a_resource(cap=1)])
        guard_answer(_call("a-claiming-command", cwd=tree), config=config, now=1000.0,
                     store=where)
        try:
            answered = release_answer(
                _exit(TURN_ENDED, tree, command="a-claiming-command"), config=config,
                now=1000.0, store=where, load=_a_carrier_that_cannot_run("cherry"),
            )
        except Exception as error:  # noqa: BLE001 -- the defect is the escape
            answered = {"systemMessage": f"the whole answer escaped as {type(error).__name__}"}
        said = str(answered.get("systemMessage", ""))
        check("the sweep's message survives a read this arm could not make",
              "gave back" in said, said[:240])
        check("and this arm's own answer is beside it, as unestablished",
              UNESTABLISHED in said, said[:240])

        # ⛔ The other direction of § 7's absent-against-unreadable split, and the
        # one that keeps this arm from being switched off: a project with no base
        # answers nothing at all rather than unestablished on every turn.
        out.append("")
        out.append("While a project with no base to fall behind answers nothing at all:")
        alone = fresh("no-remote")
        subprocess.run(
            ["git", "init", "--quiet", "--initial-branch=main", str(alone)], check=True
        )
        for key, value in (("user.email", "a@alone"), ("user.name", "A Name")):
            _in(alone, "config", key, value)
        _a_commit(alone, "base.txt")
        check("a code root with no remote is silent",
              behind_of(str(alone)) == (None, None, ""), repr(behind_of(str(alone)))[:200])
        check("and a directory that is no work tree is silent too",
              behind_of(outside) == (None, None, ""), repr(behind_of(outside))[:200])

        out.append("")
        out.append("It answers at the turn's end and after a merge, and at no other exit:")

        def _a_reading(_where, load=None):
            return BEHIND, 3, "in a-tree on `a-branch`, three commits"

        for label, payload in (
            ("the turn ended", _exit(TURN_ENDED, outside)),
            ("a merge finished",
             {**_call("gh pr merge 7"), "hook_event_name": CALL_FINISHED}),
            ("a merge through the raw arm finished",
             {**_call("gh api --method PUT repos/an-owner/a-repository/pulls/7/merge"),
              "hook_event_name": CALL_FINISHED}),
        ):
            answered = behind_answer(payload, read=_a_reading)
            check(f"{label}: the answer is made", BEHIND_PREFIX in answered,
                  repr(answered)[:160])
            check(f"{label}: and it cites the rule it holds", BEHIND_CITATION in answered,
                  repr(answered)[:200])
        for label, payload in (
            ("the session ended", _exit("SessionEnd", outside)),
            ("a subagent stopped", _exit("SubagentStop", outside)),
            ("a call that merged nothing finished",
             {**_call("a-command-of-some-kind"), "hook_event_name": CALL_FINISHED}),
            ("a read of the same change finished",
             {**_call("gh pr view 7 --json state"), "hook_event_name": CALL_FINISHED}),
            ("a call of a tool that is not the guarded one finished",
             {"hook_event_name": CALL_FINISHED, "tool_name": "Write", "tool_input": {}}),
            ("an event no arm here answers at all", _exit("Notification", outside)),
        ):
            check(f"{label}: no answer at all", behind_answer(payload, read=_a_reading) == "",
                  repr(behind_answer(payload, read=_a_reading))[:160])

        # ⛔ Two arms answering one event must not silence each other, which is
        # the same rule the guard's two arms are held to one event over.
        out.append("")
        out.append("The sweep's answer and this one share one message rather than replacing it:")
        where = fresh("two-arms")
        config = _a_config([_a_resource(cap=1)])
        guard_answer(_call("a-claiming-command"), config=config, now=1000.0, store=where)
        answered = release_answer(
            _exit(TURN_ENDED, outside, command="a-claiming-command"), config=config,
            now=1000.0, store=where, read=_a_reading,
        )
        said = str(answered.get("systemMessage", ""))
        check("the places given back are in it", "gave back" in said, said[:200])
        check("and so is the branch against its base", BEHIND_PREFIX in said, said[:200])

    # --- the surface and the carrier ---------------------------------------
    out.append("")
    out.append("This file is still the carrier the surface and the hooks name:")
    surface = SURFACE.read_text(encoding="utf-8")
    problems = check_the_surface_still_states_this(surface)
    check("the surface still states every rule this file holds", not problems,
          "; ".join(problems))
    for arm, slug in sorted(ARM_ANCHORS.items()):
        check(f"and reddens when the `{arm}` subsection is reworded",
              bool(check_the_surface_still_states_this(_reword_heading(surface, slug))))

    # ⛔ The question the guard matches is the surface's own word, held by this
    # run rather than by whoever edits either file. A rename there with no rename
    # here leaves every merge refused and every record ignored, green.
    stated = questions(surface)
    check("the question the guard holds a merge on is one the surface states",
          MERGE_QUESTION in stated, f"the surface states {stated}")
    check("and reddens when the surface stops stating it",
          MERGE_QUESTION not in questions(
              surface.replace(MERGE_QUESTION, "something_else", 1)))

    # ⛔ The four answer names and the word a probe is compared against are a
    # vocabulary § 18 publishes, carried here as strings because the code needs
    # them. What keeps that from being a second statement of the table is this
    # loop — the discipline `host_checks.py` applies to § 2's own four, and the
    # one this arm was missing until the review went looking for it.
    for answer in (ALREADY_RUN, NOTHING_HAS_RUN, NOTHING_CAN_RUN, UNESTABLISHED):
        check(
            f"§ 18 names the `{answer}` answer",
            f"**{answer}**" in surface,
            "this arm reports under a name the surface does not state, so its "
            "vocabulary is held to nothing",
        )
    check(
        "and reddens when the surface stops naming one",
        f"**{NOTHING_CAN_RUN}**" not in surface.replace(
            f"**{NOTHING_CAN_RUN}**", "**reworded**", 1),
    )
    check(
        f"§ 18 states `{OPERATIONAL}` as what a project's own probe prints",
        f"`{OPERATIONAL}`" in surface,
        "the one word a probe's output is compared against is not on the surface, "
        "so the comparison is held to nothing",
    )

    # ⛔ The base-reading arm's own three answers, held the same way, and
    # `UNESTABLISHED` is deliberately not re-asserted here: § 18's loop above
    # already holds that spelling, and a second assertion of one name would be
    # the duplication this discipline exists to catch.
    for answer in (LEVEL, BEHIND):
        check(
            f"§ 7 names the `{answer}` answer",
            f"**{answer}**" in surface,
            "this arm reports under a name the surface does not state, so its "
            "vocabulary is held to nothing",
        )
    check(
        "and reddens when the surface stops naming one",
        f"**{LEVEL}**" not in surface.replace(f"**{LEVEL}**", "**reworded**", 1),
    )

    carrier = CARRIER.read_text(encoding="utf-8")
    problems = check_the_carrier_still_calls_this(carrier)
    check("the carrier still calls this file on every event an arm answers", not problems,
          "; ".join(problems))
    check("and reddens when it stops calling it at all",
          bool(check_the_carrier_still_calls_this(
              _plant_in(carrier, Path(__file__).name, "something_else.py"))))
    for event in [GUARD_EVENT, *sorted(RELEASE_EVENTS)]:
        planted = carrier.replace(f'"{event}"', '"Notification"')
        check(f"and reddens when `{event}` stops being registered",
              planted != carrier and bool(check_the_carrier_still_calls_this(planted)),
              "the plant was a no-op" if planted == carrier else "stayed green")
    check("and reddens when the guard's matcher stops selecting the guarded tool",
          bool(check_the_carrier_still_calls_this(
              carrier.replace(f'"matcher": "{GUARDED_TOOL}"', '"matcher": "Read"'))))

    # ⛔ The base-reading arm rides the release registration and registers
    # nothing of its own, so each point it answers at has to be one of those
    # events — a point added here with no event behind it would be an arm that
    # never fires, which reads from a green run exactly like one that does.
    check("every point the base-reading arm answers at is a registered release event",
          all(event in RELEASE_EVENTS for event in BEHIND_EVENTS),
          f"{[e for e in BEHIND_EVENTS if e not in RELEASE_EVENTS]} is registered by nothing")
    check("and it answers at fewer of them than the sweep does",
          set(BEHIND_EVENTS) < set(RELEASE_EVENTS),
          "it answers at every release event, so the two points are not two")

    print("\n".join(out))
    print()
    if failures:
        print(f"FAILED: {len(failures)} — " + "; ".join(failures))
        return 1
    print("Every exit path is covered or proved not to fire, both fail directions hold, and the "
          "carrier still calls this file on each event.")
    return 0


# --- entry point -----------------------------------------------------------


def hook(stream, answer, out=None) -> int:
    """Answer one payload. ⛔ Interrupts nothing, whatever happens here.

    ⚠️ **It can only say so once it is running.** A failure before that -- the
    harness's timeout, no interpreter on the path, a syntax error here -- produces
    no output, and nothing in the session says the act was held to nothing. That
    residue is irreducible from inside a guard; what covers it is the gate, where
    this file's own run asserts the arms still fire and the carrier still calls
    them.
    """
    out = out if out is not None else sys.stdout
    try:
        payload = json.load(stream)
        answered = answer(payload if isinstance(payload, dict) else {})
    except Exception as error:  # noqa: BLE001 -- any failure here must stay non-fatal
        if answer is guard_answer:
            print(json.dumps({"systemMessage": (
                f"Enforcement: the guard did not run ({type(error).__name__}), so this command "
                "was held to nothing."
            )}), file=out)
        return 0
    if answered:
        print(json.dumps(answered), file=out)
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Refuse an act on the strength of a record, and hold a place on what "
                    "contends.",
    )
    parser.add_argument("--self-test", action="store_true",
                        help="assert every rule reddens on its plants and stays green off them")
    sub = parser.add_subparsers(dest="arm")

    sub.add_parser("guard", help=f"answer a {GUARD_EVENT} payload on stdin")
    sub.add_parser("release", help="answer an exit payload on stdin: the places this session "
                                   "holds, and the branch against its base")

    writing = sub.add_parser("record", help="write a recorded answer onto a change")
    writing.add_argument("--change", required=True,
                         help="the change, keyed the way a record is: <owner>/<repo>#<number>")
    writing.add_argument("--question", required=True, help="which question was answered")
    writing.add_argument("--given", required=True, help="the answer, as it came back")
    writing.add_argument("--by", required=True, help="who answered it")
    writing.add_argument("--at", default=None, help="when; now where omitted")

    reporting = sub.add_parser("held", help="report what is held right now, and by what")
    reporting.add_argument("--skills-root", default=".",
                           help="the root the configuration is resolved relative to")

    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    if args.arm == "guard":
        return hook(sys.stdin, guard_answer)
    if args.arm == "release":
        return hook(sys.stdin, release_answer)
    if args.arm == "record":
        stamp = args.at or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        report, status = write_record(args.change, args.question, args.given, args.by, stamp)
        print(report)
        return status
    if args.arm == "held":
        loaded = _config(args.skills_root)
        if loaded is None:
            print("⛔ Not established: the project's configuration could not be read, so what "
                  "is held is unknown rather than nothing.")
            return 1
        report, status = held_report(loaded)
        print(report)
        return status
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
