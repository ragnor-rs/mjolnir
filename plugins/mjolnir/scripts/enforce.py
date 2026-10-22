#!/usr/bin/env python3
"""Refuse an act on the strength of a record, and hold a place on what contends.

The surface states what a hook may refuse and what it reads to refuse it -- see
`schema.md § 7 -> What a hook refuses, and the record it reads`, the subsection
beside it that fixes which direction a guard fails in, the one after that which
states the lease, and the one above them all which says what a hook does in a
project that states no configuration. This script is the carrier for each:

    guard     a `PreToolUse` answer: refuse a merge with no recorded answer,
              then hold a place on whatever the call puts at stake -- and
              nothing at all where the project states no configuration
    release   a `PostToolUse`, `Stop`, `SessionEnd` or `SubagentStop` answer:
              give back the places this session is holding
    record    write the recorded answer a guard reads onto a change
    held      report what is held right now, and by what

⛔ **Nothing here judges the work.** A guard reads a record somebody else wrote
and a count somebody else's command printed; where either is missing it says so
in those words. The two directions it may fail in are the surface's and not this
file's choice, and both are exercised below.

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
}

RECORD_CITATION = "schema § 7 → What a hook refuses, and the record it reads"
LEASE_CITATION = ("schema § 7 → A lease on an exclusive resource, and the exit paths that "
                  "release it")

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
                 store: Path | None = None, probe=None, host=None) -> dict:
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
        return {"systemMessage": (
            "Enforcement: the project's configuration could not be read, so this command was "
            "held to nothing."
        )}
    refused = merge_guard(loaded, command, host=host)
    if refused:
        return refused
    return capacity_guard(
        loaded,
        command,
        str(payload.get("session_id") or ""),
        str(payload.get("cwd") or "."),
        bool(tool_input.get("run_in_background")),
        now=time.time() if now is None else now,
        store=store,
        probe=probe,
    )


def release_answer(payload: dict, *, config=None, now: float | None = None,
                   store: Path | None = None) -> dict:
    """The answer for whichever event gives a place back.

    ⛔ This arm was already silent in a project that states no configuration,
    the reader refusing and the answer being empty either way. It asks the
    question anyway, so that both arms of this carrier ask it before anything
    else: reaching the same silence through a refusal costs the surface's own
    parse on every call in a project that holds nothing.
    """
    event = str(payload.get("hook_event_name") or "")
    scope = RELEASE_EVENTS.get(event)
    if scope is None:
        return {}
    if config is None and not _states_a_configuration(payload.get("cwd")):
        return {}
    loaded = config if config is not None else _config(payload.get("cwd"))
    if loaded is None or not resources(loaded):
        return {}
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
        return {}
    return {"systemMessage": (
        "Capacity: gave back " + ", ".join(sorted({str(g.get("resource")) for g in given}))
        + f". ({LEASE_CITATION})"
    )}


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


# --- the arms a role invokes ------------------------------------------------


def questions(surface_text: str | None = None) -> list[str]:
    """The questions an answer may be recorded for, read out of the surface.

    ⛔ Through the surface's own reader and never parsed here, which is what makes
    the alternation one statement rather than two. An empty list where the
    alternation cannot be read at all, which the caller reports rather than
    treating as *every question is fine*.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        import config as reader  # noqa: PLC0415 -- the path is set one line up
        text = surface_text if surface_text is not None else SURFACE.read_text(encoding="utf-8")
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


def _call(command: str, session: str = "a-session", cwd: str = ".",
          background: bool = False) -> dict:
    return {
        "tool_name": GUARDED_TOOL,
        "session_id": session,
        "cwd": cwd,
        "tool_input": {"command": command, "run_in_background": background},
    }


def _exit(event: str, session: str = "a-session", command: str = "") -> dict:
    return {
        "hook_event_name": event,
        "session_id": session,
        "cwd": ".",
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
            release_answer(_exit("Stop"), config=nothing, now=1000.0,
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
            release_answer(_exit(event, command="a-claiming-command"), config=config,
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
            release_answer(_exit(event, command="a-claiming-command"), config=config,
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
        release_answer(_exit("PostToolUse", command="a-claiming-command --one"),
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
                  release_answer(_exit("Stop", command="a-claiming-command"), now=1000.0,
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
        check("and gives nothing back on an exit either, there being nothing read to release",
              release_answer(_exit("Stop"), now=1000.0, store=fresh("unreadable")) == {})
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
    sub.add_parser("release", help="answer an exit payload on stdin")

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
