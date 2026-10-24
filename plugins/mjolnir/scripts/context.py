#!/usr/bin/env python3
"""Bound what enters the window where the call is made.

The surface states which commands a project has decided produce output nothing
bounds, what bounds each of them, which commands are never bounded, the size a
result is replaced above and where its full text goes -- see
`schema.md § 22 -> What enters the window, bounded where the call is made` and
the four subsections beside it. This script is the carrier for each:

    guard   a `PreToolUse` answer: refuse the unbounded call naming the bounded
            form, rewrite the arguments where a flag bounds the command, refuse
            a read this session has already made -- and nothing at all where the
            project names no such command, or states no configuration

    result  a `PostToolUse` answer: replace a result longer than the stated
            limit with the path its full text was written to, a head and a tail;
            and record each read, which is what the arm above compares against

⛔ **Nothing here knows which of a project's commands are unbounded, and no
command's flags are written below.** The commands are the project's, what bounds
each one is the project's, and what this file carries is the command position,
the size of a result, the replacement, the ledger of what this session has read,
the decision and the report (`schema.md § 22`).

⛔ **The command position is not resolved here either.** It is `spend.py`'s, two
facets over, and it is imported rather than copied: the parse carries a hundred
lines of measurement about where a command *is* in a call, and two copies of it
would be two readings of the shell allowed to disagree about which token is the
command (`schema.md § 19 -> The command position`).

⛔ **Every fact this guard cannot establish leaves the call alone**, which is the
inversion of the sibling guard one facet over and is
`schema.md § 22 -> Why every unestablished fact here proceeds` rather than a
choice made here.

⚠️ **What this cannot hold is stated rather than discovered**, in
`docs/single-source-of-truth.md` § The context half rather than restated here:
the bound a project states is added to the arguments and nothing reads whether
the command accepted it, and what the harness does with a replaced result for a
tool whose response is not text is unstated in its own reference.

Usage:
    context.py guard           a hook payload on stdin
    context.py result          a hook payload on stdin
    context.py --self-test
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import re
import shlex
import sys
import tempfile
from pathlib import Path

# ⛔ The parse, imported from the carrier that owns it. The path is derived from
# this file's own location, so a run from a worktree reads that tree's parse
# rather than the primary checkout's.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import spend as position  # noqa: E402 -- the one reading of where a command is

# --- where the rules live --------------------------------------------------

SURFACE = Path(__file__).resolve().parent.parent / "config" / "schema.md"

# The subsections this script is the carrier for, by the anchors the code host
# would give their headings. Grammar: a heading may be reworded without touching
# this file only if its anchor survives, which is the bargain every citation of
# the surface already makes.
ARM_ANCHORS = {
    "facet": "22-what-enters-the-window-bounded-where-the-call-is-made",
    "arms": "the-three-arms-and-the-one-that-rewrites-rather-than-refuses",
    "read": "a-read-this-session-has-already-made",
    "exempt": "the-commands-a-project-names-as-never-bounded",
    "proceeds": "why-every-unestablished-fact-here-proceeds",
    # The parse this carrier reads rather than states, and the three § 7 rules it
    # obeys rather than states: an install is silent in a project that configures
    # nothing, the direction a guard fails in is procedure, and a hook holds its
    # rule on every call its matcher fires on.
    "position": "the-command-position-and-why-the-whole-call-is-not-one",
    "unconfigured": "a-hook-in-a-project-that-states-no-configuration",
    "direction": "which-direction-a-guard-fails-in",
    "reach": "what-a-hook-can-establish-about-the-role-it-is-running-under",
}

FACET_CITATION = "schema § 22 → What enters the window, bounded where the call is made"
ARMS_CITATION = "schema § 22 → The three arms, and the one that rewrites rather than refuses"
READ_CITATION = "schema § 22 → A read this session has already made"
EXEMPT_CITATION = "schema § 22 → The commands a project names as never bounded"
PROCEEDS_CITATION = "schema § 22 → Why every unestablished fact here proceeds"

# The carrier, and the events the arms answer. ⛔ Held rather than assumed: an arm
# whose event stopped being registered is dead in every session, and a dead guard
# holds nothing while every reader goes on reporting it installed.
CARRIER = Path(__file__).resolve().parent.parent / "hooks" / "hooks.json"
GUARD_EVENT = "PreToolUse"
RESULT_EVENT = "PostToolUse"

# The two tools a result enters the window through, and what each arm reads of
# them. ⛔ The harness's own vocabulary and not this surface's: which tool runs a
# command and which reads a file is the harness's fact, and a key stating it would
# be a project naming tools nothing hands it.
COMMAND_TOOL = "Bash"
READ_TOOL = "Read"
GUARDED_TOOLS = (COMMAND_TOOL, READ_TOOL)

# The fields a read arrives in, the harness's own spelling. ⚠️ A range absent is
# the whole file as that tool reads it, which is a different read from any range
# of it -- so the absence is part of the key rather than normalised away.
PATH_FIELD = "file_path"
RANGE_FIELDS = ("offset", "limit")

# --- what the configuration states ------------------------------------------

UNBOUNDED = "context_guard.unbounded"
NEVER_BOUND = "context_guard.never_bound"
LIMIT = "context_guard.result_limit_chars"
SIDECAR = "context_guard.sidecar_dir"
REREAD = "context_guard.reread"

# The value of `reread` that makes that arm hold anything. ⛔ Spelled out here
# rather than derived: the surface states the alternation and the reader holds a
# configuration to it, and what a *member* means is this carrier's, which is the
# treatment every other sentinel member gets.
REFUSE = "refuse"

# How much of a segment a report quotes.
SHOWN = 160

# How many reads one session's ledger keeps. ⛔ Derived and configured by nothing,
# like the ledger's own place: what it bounds is what a long session's ledger
# costs on disk, and a read pushed out of it is one this arm then lets through --
# the proceeding direction, which is this facet's everywhere else.
LEDGER_ENTRIES = 2000

# --- what could not be established ------------------------------------------
#
# Each of `§ 22 -> Why every unestablished fact here proceeds`, as the phrase the
# report names it by. ⛔ Read by the suite, so a reword travels rather than
# breaking it.

UNPARSEABLE = "this call could not be parsed, so it has no command position to read"
NO_SIDECAR = "the full text could not be written, so nothing was replaced"
UNREADABLE_RESULT = "this result's own text could not be read"


def entries(config) -> list[dict]:
    """The commands this project says produce unbounded output. `[]` is absence."""
    stated = config.get(UNBOUNDED)
    if not isinstance(stated, list):
        return []
    return [entry for entry in stated if isinstance(entry, dict)]


def never_bound(config) -> list[str]:
    """The commands this project exempts from both of the command arms."""
    stated = config.get(NEVER_BOUND)
    return [
        str(name).strip()
        for name in (stated if isinstance(stated, list) else [])
        if str(name).strip()
    ]


def limit_of(config):
    """The size a result is replaced above, or None where none is stated."""
    stated = config.get(LIMIT)
    if isinstance(stated, bool) or not isinstance(stated, int) or stated <= 0:
        # ⛔ Refused at load by the shared reader (§ 22), so this is the arm
        # nothing reaches through a validated configuration. It replaces nothing
        # rather than picking a limit of its own.
        return None
    return stated


def _names(called: str, configured: str) -> bool:
    return position.names_the_command(called, configured)


def exempt(config, command: str) -> str | None:
    """The exemption this call matches, or None.

    ⛔ Matched at a command position like every entry (§ 22 → The commands a
    project names as never bounded), so a call that merely *names* an exempt
    command is not exempt -- which is the direction that matters here, an
    exemption being the one thing in this facet that lets a call through.
    """
    stated = never_bound(config)
    if not stated or not position.readable(command):
        return None
    for segment in position.segments(command):
        for called, _arguments in position.command_chain(segment):
            for name in stated:
                if _names(called, name):
                    return name
    return None


def bounded_already(arguments: list[str], bound: str) -> bool:
    """Whether the call already carries the flag the entry's bound opens with.

    ⛔ Whatever value it carries: § 22 states that how large a bound a session
    chose for its own call is a judgement, and a guard that second-guessed it
    would be refusing a call that had already met the rule. ⚠️ Both spellings of
    a flag, since one word carrying flag and value is the same statement as two.
    """
    flag = bound.split()[0] if bound.split() else ""
    if not flag:
        return False
    return any(
        word == flag or word.startswith(f"{flag}=")
        for word in arguments
    )


def one_command(command: str) -> bool:
    """Whether this call is one command, which is the only call a rewrite is made on.

    ⛔ The rule is § 22's and the test is conservative on purpose: a call whose
    arguments cannot be appended to as text is one whose rewrite would mean
    re-rendering a parse, and a re-rendered call is not the call the person
    wrote. So what passes here is a call the parse reads as a single command
    position with **every token accounted for** -- a redirection, a here-document,
    a separator or a substitution each drop or add tokens, and the comparison
    catches all four without naming any of them.
    """
    if not position.readable(command):
        return False
    if len(position.calls(command)) != 1:
        return False
    found = position.segments(command)
    if len(found) != 1:
        return False
    if len(position.command_chain(found[0])) != 1:
        return False
    return position.words(command) == found[0]


def holds(config, command: str) -> list[dict]:
    """Every (entry, segment) this call is unbounded in, in the call's own order.

    ⛔ One record per *segment*, for the reason the sibling guards keep one: a
    person reading *this call is unbounded* against four semicolons has no way to
    tell which of them was meant.

    ⛔ **An unparseable call matches nothing**, and that is § 22's proceeding
    direction rather than an omission: a call the lexer could not read has no
    reliable command position in it, and reading one out of a parse that did not
    happen is how a text search gets refused for naming a command. The caller
    reports it instead.
    """
    stated = entries(config)
    if not stated or not position.readable(command):
        return []
    found = []
    for at, segment in enumerate(position.segments(command), start=1):
        for called, arguments in position.command_chain(segment):
            for entry in stated:
                configured = entry.get("command")
                if not isinstance(configured, str) or not _names(called, configured):
                    continue
                pattern = entry.get("args_match")
                if isinstance(pattern, str) and pattern.strip():
                    try:
                        if not re.search(pattern, " ".join(arguments)):
                            continue
                    except re.error:
                        # Refused at load by the shared reader (§ 22), so nothing
                        # reaches this through a validated configuration. It does
                        # not match on a pattern it cannot compile.
                        continue
                bound = entry.get("bound")
                if isinstance(bound, str) and bounded_already(arguments, bound):
                    continue
                found.append({
                    "entry": entry,
                    "segment": at,
                    "called": called,
                    "arguments": arguments,
                    "shown": " ".join(segment)[:SHOWN],
                })
    return found


# --- the decision -----------------------------------------------------------


def _refusal(reason: str) -> dict:
    return {
        "hookSpecificOutput": {
            "hookEventName": GUARD_EVENT,
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def _rewrite(command: str, told: str) -> dict:
    """The arguments replaced, and the session told they were.

    ⛔ Both in one answer, and the second half is not decoration: a bound the
    session is not told about is a bounded result read as complete, which is the
    one way this facet could leave a window worse than it found it (§ 22 → The
    three arms). ⚠️ The channel is the one that reaches the session's own next
    request rather than the one that reaches a person.
    """
    return {
        "hookSpecificOutput": {
            "hookEventName": GUARD_EVENT,
            "updatedInput": {"command": command},
            "additionalContext": told,
        }
    }


def _held_to_nothing(what: str) -> dict:
    return {"systemMessage": f"Context guard: {what} ({PROCEEDS_CITATION})."}


def bound_guard(config, command: str) -> dict:
    """Refuse an unbounded call, rewrite one a flag bounds, or answer nothing."""
    if not entries(config):
        return {}
    spared = exempt(config, command)
    if spared is not None:
        return {}
    if not position.readable(command):
        return _held_to_nothing(UNPARSEABLE)
    found = holds(config, command)
    if not found:
        return {}
    # ⛔ The rewrite is the one arm that acts on the call rather than refusing it,
    # and it is reached only where the whole call is one command and one entry
    # states a bound for it. Every other shape is refused, which is § 7's safe
    # direction for the one judgement this facet makes two ways.
    if len(found) == 1 and one_command(command):
        bound = found[0]["entry"].get("bound")
        if isinstance(bound, str) and bound.strip():
            rewritten = f"{command.rstrip()} {bound.strip()}"
            return _rewrite(rewritten, (
                f"This project states that `{found[0]['entry'].get('command')}` produces output "
                f"nothing bounds — {found[0]['entry'].get('reason')} — so `{bound.strip()}` was "
                f"added to this call before it ran ({ARMS_CITATION}). ⛔ What came back is "
                "therefore bounded rather than complete: read it as the first part of that output "
                "and not as all of it."
            ))
    lines = []
    for match in found:
        entry = match["entry"]
        instead = entry.get("instead")
        bound = entry.get("bound")
        if isinstance(instead, str) and instead.strip():
            route = f"run `{instead.strip()}` instead"
        else:
            route = f"add `{str(bound).strip()}` to it"
        lines.append(
            f"segment {match['segment']} — `{match['shown']}` — runs "
            f"{entry.get('command')!r}, whose output this project states nothing bounds: "
            f"{entry.get('reason')}. To get the same answer bounded, {route}"
        )
    return _refusal(
        "This command would put output nothing bounds into the window:\n  "
        + "\n  ".join(lines)
        + f"\n⛔ Refused where the call is made rather than summarised afterwards, because what a "
        f"summary dropped is gone ({FACET_CITATION}). What unblocks it is the bounded form above — "
        f"or, where this command is one a role is forbidden to truncate, its name in this "
        f"project's `{NEVER_BOUND}` ({EXEMPT_CITATION})."
    )


def read_key(tool_input: dict) -> str | None:
    """How a read is keyed in the ledger, or None where it names no path."""
    path = tool_input.get(PATH_FIELD)
    if not isinstance(path, str) or not path.strip():
        return None
    where = os.path.abspath(os.path.expanduser(path.strip()))
    stated = ":".join(str(tool_input.get(field, "")) for field in RANGE_FIELDS)
    return f"{where}@{stated}"


def signature(tool_input: dict) -> str | None:
    """The file's own size and modification time, or None where neither could be read.

    ⛔ Read from the file and never from the window (§ 22 → A read this session
    has already made): a path whose size or modification time differs from the
    recorded read is new content, whoever changed it, which is what keeps an
    edited file readable.
    """
    path = tool_input.get(PATH_FIELD)
    if not isinstance(path, str) or not path.strip():
        return None
    try:
        stated = os.stat(os.path.expanduser(path.strip()))
    except OSError:
        # ⛔ One answer for every failure to read, deliberately: a file that is
        # not there, a directory where a file was named and a file this user may
        # not open are one state to a guard -- there is nothing to compare -- and
        # the read itself is about to answer better than this guard could.
        return None
    return f"{stated.st_size}:{stated.st_mtime_ns}"


def ledger_root() -> Path:
    """Where this machine keeps what each session has read.

    ⛔ Derived, never configured. § 22 makes the ledger per session and nobody's
    artifact: a project stating where it lives would be stating a path for a
    record only one session ever reads. ⚠️ Under the harness's own store for this
    plugin where it hands one over, and a temp directory otherwise -- which does
    not survive a reboot, and for a ledger that is the wanted behaviour rather
    than a cost, a session not surviving one either.
    """
    stated = os.environ.get("CLAUDE_PLUGIN_DATA")
    if isinstance(stated, str) and stated.strip():
        return Path(stated.strip()) / "reads"
    return Path(tempfile.gettempdir()) / f"mjolnir-reads-{os.getuid()}"


def ledger_file(session: str) -> Path | None:
    """One session's ledger, or None where the event named no session."""
    if not session.strip():
        return None
    digest = hashlib.sha256(session.strip().encode("utf-8")).hexdigest()[:24]
    return ledger_root() / f"{digest}.json"


def ledger(session: str) -> dict:
    path = ledger_file(session)
    if path is None:
        return {}
    try:
        with open(path, encoding="utf-8") as handle:
            loaded = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return {}
    return loaded if isinstance(loaded, dict) else {}


def remember(session: str, key: str, sign: str) -> None:
    """Write one read into this session's ledger, oldest first out."""
    path = ledger_file(session)
    if path is None:
        return
    held = ledger(session)
    held.pop(key, None)
    held[key] = sign
    while len(held) > LEDGER_ENTRIES:
        held.pop(next(iter(held)))
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(held, handle)
    except OSError:
        # Nothing is recorded, so the next read of the same file proceeds. The
        # proceeding direction again, and the one a ledger can fail in.
        return


def reread_guard(config, tool_input: dict, session: str) -> dict:
    """Refuse a read this session has already made, or answer nothing."""
    if str(config.get(REREAD) or "") != REFUSE:
        return {}
    key, sign = read_key(tool_input), signature(tool_input)
    if key is None or sign is None or not session.strip():
        return {}
    if ledger(session).get(key) != sign:
        return {}
    where = tool_input.get(PATH_FIELD)
    ranged = any(tool_input.get(field) is not None for field in RANGE_FIELDS)
    return _refusal(
        f"This session has already read `{where}`"
        + (" over that range" if ranged else " in full")
        + ", and it has not changed since: same size, same modification time "
        f"({READ_CITATION}). ⛔ What is already in the window is not read into it twice — the "
        "day-log role counts that as overhead and cuts the hours for it after the fact, and this "
        "is the same judgement before the tokens are spent. What unblocks it: read a different "
        "part of the file, which is a different read and passes — the case being a window "
        "summarised since, which no longer holds what was read."
    )


def guard_answer(payload: dict, *, config=None) -> dict:
    """The `PreToolUse` answer for one call, whichever tool it arrived on."""
    tool = payload.get("tool_name")
    if tool not in GUARDED_TOOLS:
        return {}
    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        return {}
    command = str(tool_input.get("command") or "")
    if tool == COMMAND_TOOL and not command.strip():
        return {}
    if tool == READ_TOOL and read_key(tool_input) is None:
        return {}
    loaded, answered = _loaded(payload, config)
    if loaded is None:
        return answered
    if tool == COMMAND_TOOL:
        return bound_guard(loaded, command)
    return reread_guard(loaded, tool_input, str(payload.get("session_id") or ""))


# --- what comes back --------------------------------------------------------


def text_of(response) -> str | None:
    """A result's own text, or None where this arm could not read it.

    ⛔ Every string the response carries, joined, and **no field named here**: a
    tool's response shape is the harness's and a list of its keys in this file
    would be a vocabulary going stale in silence, while what a window pays for is
    the text whatever key it arrived under. ⚠️ What the harness does with a
    replacement for a response that was not text is unstated in its own
    reference, which is recorded in `docs/single-source-of-truth.md` rather than
    assumed away here: this arm reads the text and answers with text.
    """
    if isinstance(response, str):
        return response
    if isinstance(response, dict):
        carried = [value for value in response.values() if isinstance(value, str)]
        if carried:
            return "\n".join(carried)
    return None


def sidecar_of(config, text: str) -> str | None:
    """The path this result's full text was written to and read back from.

    ⛔ Read back, rather than reported written: § 22 replaces a result only once
    its full text is on disk, a replacement whose sidecar was not written being a
    result the window has lost and nothing can recover.

    ⛔ **The one path on this surface a guard expands itself**, by § 22: no
    command stands between this event and this write, and a path left unexpanded
    is a directory named for a variable created inside whatever tree the session
    is standing in.
    """
    stated = config.get(SIDECAR)
    if not isinstance(stated, str) or not stated.strip():
        return None
    root = os.path.expanduser(os.path.expandvars(stated.strip()))
    # Named by what it holds, so one result written twice is one file: a name
    # carrying a counter or a time would leave a directory nobody can read.
    name = f"{hashlib.sha256(text.encode('utf-8')).hexdigest()[:24]}.txt"
    where = os.path.join(root, name)
    try:
        os.makedirs(root, exist_ok=True)
        with open(where, "w", encoding="utf-8") as handle:
            handle.write(text)
        with open(where, encoding="utf-8") as handle:
            back = handle.read()
    except OSError:
        return None
    return where if back == text else None


def replacement(path: str, text: str, limit: int) -> str:
    """What reaches the window in place of an oversized result."""
    share = max(1, limit // 4)
    return (
        f"⛔ This result was {len(text)} characters, over the {limit} this project states as "
        f"`{LIMIT}`, so what reached the window is the two ends of it ({FACET_CITATION}).\n"
        # ⚠️ The path ends the line it is on, so whoever reads this back gets the
        # whole of it: a configured directory may carry a space, and a reader
        # taking the next run of non-blank characters would stop inside it.
        f"The whole of it is on disk at {path}\n"
        "Read the part you need from there rather than running the call again.\n"
        f"--- the first {share} characters ---\n{text[:share]}\n"
        f"--- the last {share} characters ---\n{text[-share:]}\n"
    )


def result_curb(config, command: str, response) -> dict:
    """Replace a result nothing bounded, or answer nothing."""
    limit = limit_of(config)
    if limit is None:
        return {}
    if command.strip() and exempt(config, command) is not None:
        return {}
    text = text_of(response)
    if text is None:
        return _held_to_nothing(UNREADABLE_RESULT) if response else {}
    if len(text) <= limit:
        return {}
    where = sidecar_of(config, text)
    if where is None:
        return _held_to_nothing(NO_SIDECAR)
    rendered = replacement(where, text, limit)
    if len(rendered) >= len(text):
        # ⛔ The arm's own promise is that less enters the window, and a limit set
        # low enough for the path and the two ends to outweigh the result is the
        # one case where rendering it would break that promise (§ 22).
        return {}
    return {
        "hookSpecificOutput": {
            "hookEventName": RESULT_EVENT,
            "updatedToolOutput": rendered,
        }
    }


def result_answer(payload: dict, *, config=None) -> dict:
    """The `PostToolUse` answer: a result replaced, or a read recorded."""
    tool = payload.get("tool_name")
    if tool not in GUARDED_TOOLS:
        return {}
    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        return {}
    loaded, answered = _loaded(payload, config)
    if loaded is None:
        return answered
    if tool == READ_TOOL:
        # ⛔ Recorded only where the arm that compares it holds anything: a
        # project stating `allow` gets no ledger written at all, rather than a
        # store kept on disk for nothing to read.
        if str(loaded.get(REREAD) or "") == REFUSE:
            key, sign = read_key(tool_input), signature(tool_input)
            if key is not None and sign is not None:
                remember(str(payload.get("session_id") or ""), key, sign)
        return {}
    return result_curb(loaded, str(tool_input.get("command") or ""), payload.get("tool_response"))


# --- the shared reader ------------------------------------------------------


def _loaded(payload: dict, config):
    """(the configuration, the answer to give where there is none).

    The two § 7 readings both arms need, in one place: a project that states no
    configuration gets silence, and one whose configuration does not resolve gets
    a report and an untouched call.
    """
    if config is not None:
        return config, {}
    if not states_a_configuration(payload.get("cwd")):
        # ⛔ Silence, and not a report: these arms fire on every command and every
        # read in every project the install reaches, and a project that states no
        # configuration has agreed to no rule this guard could hold (§ 7).
        return None, {}
    loaded = _config(payload.get("cwd"))
    if loaded is None:
        # ⛔ Reported, and the call proceeds. § 22 settles this one case by
        # pointing at § 19's: what a broken configuration cannot say is whether
        # this call is bounded at all, so the refusing arm would refuse every call
        # in the project -- the edit that repairs the configuration included.
        return None, {"systemMessage": (
            "Context guard: the project's configuration could not be read, so this call was held "
            f"to nothing. ({FACET_CITATION})"
        )}
    return loaded, {}


def states_a_configuration(cwd: str | None) -> bool:
    """Whether the project this event names states a configuration at all.

    ⛔ Asked through the shared reader rather than by testing a path here: where a
    project's configuration lives is one statement, and a second copy of that path
    drifts the first time either moves.

    ⛔ False where the reader cannot be reached at all, which is the silent
    direction deliberately: an install whose own reader is missing cannot hold a
    project to a file it has no way to find.
    """
    try:
        import config as reader  # noqa: PLC0415 -- the path is set at import time
        return bool(reader.configured(cwd or "."))
    except Exception:  # noqa: BLE001 -- an unreachable reader answers no, per above
        return False


def _config(cwd: str | None):
    """The project's configuration, or None where it could not be read.

    ⛔ Read through the shared reader, never parsed here: a second reader is a
    second set of defaults, and two sets drift apart with nothing noticing.
    """
    try:
        import config as reader  # noqa: PLC0415 -- the path is set at import time
        return reader.load(cwd or ".", check_paths=False)
    except Exception:  # noqa: BLE001 -- any failure is reported by the caller
        return None


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
    """`hooks.json` still registers both arms, on their events and both tools."""
    try:
        carrier = json.loads(text)
    except json.JSONDecodeError as error:
        return [f"{CARRIER.name} is not readable as JSON ({error}), so nothing calls this."]
    hooks = carrier.get("hooks") or {}
    mine = Path(__file__).name
    problems = []
    for event, arm in ((GUARD_EVENT, "guard"), (RESULT_EVENT, "result")):
        called = None
        for group in hooks.get(event) or []:
            for item in group.get("hooks") or []:
                named = " ".join([str(item.get("command") or "")]
                                 + [str(a) for a in (item.get("args") or [])])
                if mine in named and arm in named.split():
                    called = (group, named)
        if called is None:
            # ⛔ The arm and not merely this file's name: a carrier naming the
            # script with no argument prints usage and answers nothing, while the
            # event stays wired and reads as installed. ⚠️ And one arm registered
            # does not cover the other: the ledger the read arm compares against
            # is written by the result arm, so either one alone holds nothing.
            problems.append(
                f"{CARRIER.name} registers no {event} hook calling {mine} with the `{arm}` arm, "
                "so whatever that event covers is covered by nothing."
            )
            continue
        group, named = called
        if "${CLAUDE_PLUGIN_ROOT}" not in named:
            problems.append(
                f"{CARRIER.name} names {mine} on {event} by a path the plugin root does not "
                "expand — the handler must address it through `${CLAUDE_PLUGIN_ROOT}`."
            )
        matcher = group.get("matcher") or ""
        for tool in GUARDED_TOOLS:
            if tool not in matcher:
                problems.append(
                    f"{CARRIER.name} calls {mine} on {event} with matcher {matcher!r}, which "
                    f"does not select {tool} — one of the two tools a result enters the window "
                    "through."
                )
    return problems


# --- the plants ------------------------------------------------------------
#
# ⛔ Both directions, per rule. A call that must be held and a call that must not
# are one pair, and a lone green proves nothing: a dead matcher holds nothing and
# is silent on every call there is.


def _a_config(unbounded: list[dict], spared=None, limit=None, sidecar=None, reread=REFUSE):
    """A stand-in for the shared reader's answer, carrying what the arms read.

    ⛔ A fake and not a mock: it answers as the reader does for the five keys
    these arms ask it, so a rename of any of them reddens here rather than
    passing. ⚠️ Its shape is the production one -- the dotted-path accessor --
    because a fixture thinner than that tests the fixture.
    """

    class _Loaded:
        def __init__(self):
            node = {"unbounded": unbounded, "never_bound": spared or [], "reread": reread}
            if limit is not None:
                node["result_limit_chars"] = limit
            if sidecar is not None:
                node["sidecar_dir"] = sidecar
            self.data = {"context_guard": node}

        def get(self, path, default=None):
            node = self.data
            for part in path.split("."):
                if not isinstance(node, dict) or part not in node:
                    return default
                node = node[part]
            return node

    return _Loaded()


def _an_entry(command: str, **rest) -> dict:
    entry: dict = {"command": command, "reason": "what one call of it would put in the window"}
    entry.update(rest)
    return entry


def _call(command: str) -> dict:
    return {
        "tool_name": COMMAND_TOOL,
        "cwd": ".",
        "session_id": "a-session",
        "tool_input": {"command": command},
    }


def _came_back(command: str, response) -> dict:
    return {
        "tool_name": COMMAND_TOOL,
        "cwd": ".",
        "session_id": "a-session",
        "tool_input": {"command": command},
        "tool_response": response,
    }


def _a_read(path: str, session: str = "a-session", **rest) -> dict:
    return {
        "tool_name": READ_TOOL,
        "cwd": ".",
        "session_id": session,
        "tool_input": {PATH_FIELD: path, **rest},
    }


def _a_root(where: Path, states: str | None) -> str:
    """A project root stating this configuration, or stating none at all.

    ⛔ Written at the reader's own `CONFIG_PATH` rather than at a path spelled out
    here: a fixture built against a literal would stay green after that path
    moved, while every live hook went silent in every project.
    """
    where.mkdir(parents=True, exist_ok=True)
    if states is not None:
        import config as reader  # noqa: PLC0415 -- the path is set at import time

        stated = where / reader.CONFIG_PATH
        stated.parent.mkdir(parents=True, exist_ok=True)
        stated.write_text(states, encoding="utf-8")
    return str(where)


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


CARRIER_PLANTS = [
    ("a carrier that is not valid JSON", lambda text: text.rstrip()[:-1]),
    ("a carrier registering nothing for the guard's event",
     lambda text: text.replace(f'"{GUARD_EVENT}"', '"Notification"')),
    ("a carrier registering nothing for the result event",
     lambda text: text.replace(f'"{RESULT_EVENT}"', '"Notification"')),
    ("a carrier calling a script that is not this one",
     lambda text: text.replace("context.py", "context_something_else.py")),
    ("a carrier whose expansion of the plugin root is mistyped",
     lambda text: text.replace("CLAUDE_PLUGIN_ROOT", "CLAUDE_PLUGIN_ROOTS")),
    # ⚠️ Anchored on this script's own name, so each plant takes the arm off
    # *this* entry rather than off whichever sibling also names `guard`.
    ("a carrier naming no arm at all for the guard",
     lambda text: text.replace('context.py", "guard"', 'context.py"')),
    ("a carrier naming no arm at all for the result",
     lambda text: text.replace('context.py", "result"', 'context.py"')),
    ("a carrier whose matcher does not select the tool a command arrives on",
     lambda text: text.replace(f'"{COMMAND_TOOL}|{READ_TOOL}"', f'"{READ_TOOL}"')),
    ("a carrier whose matcher does not select the tool a read arrives on",
     lambda text: text.replace(f'"{COMMAND_TOOL}|{READ_TOOL}"', f'"{COMMAND_TOOL}"')),
]

# The call shapes an unbounded command actually arrives in, enumerated by hand: a
# guard asserted only against the shape its author imagined is a guard that holds
# that shape. ⛔ `<tool>` is substituted with the entry's own command, so no
# literal here is under test.
MUST_HOLD = [
    ("the command itself", "<tool>"),
    ("the same command spelled relatively", "./<tool>"),
    ("with an argument of its own", "<tool> an-argument"),
    ("behind an environment assignment", "A_VARIABLE=a-value <tool>"),
    ("behind an elevation wrapper", "sudo <tool>"),
    ("behind a wrapper's own valued flag", "sudo -u a-user <tool>"),
    ("after the command's end-of-flags marker", "<tool> -- an-argument"),
    ("as the second command of a chain", "a-free-command && <tool>"),
    ("after a semicolon", "a-free-command; <tool>"),
    ("at the head of a pipe", "<tool> | a-free-command"),
    ("on the second line of one call", "a-free-command\n<tool>"),
    ("inside a substitution", "a-free-command $(<tool>)"),
    ("inside a substitution the shell expands in quotes", 'a-free-command "$(<tool>)"'),
    ("inside the older substitution spelling", "a-free-command `<tool>`"),
    ("inside a brace group", "{ <tool>; }"),
    ("as the body of a condition", "if a-free-command; then <tool>; fi"),
    ("as the body of a loop", "for i in a b; do <tool>; done"),
    ("behind the word that replaces the shell", "exec <tool>"),
    ("as the command a search runs per match",
     "a-searching-command . -name a-file -exec <tool> {} ;"),
    ("across a line continuation, which is not a separator", "<tool> \\\n  an-argument"),
    ("with its output redirected", "<tool> > a-file"),
]

MUST_PASS = [
    ("the command named inside another command's prose",
     "a-text-editing-command 'the note mentions <tool> in passing'"),
    ("the command's path as the argument of a reading command", "a-reading-command <tool>"),
    ("the command's path as a redirection's target", "a-free-command > <tool>"),
    ("a command whose name merely ends in the configured one", "a-prefix-<tool> an-argument"),
    ("the command inside single quotes", "a-printing-command '<tool> an-argument'"),
    ("a here-document whose body names the command",
     "a-writing-command <<'A_DELIMITER' > a-file\n<tool> is the step\nA_DELIMITER"),
    ("the command's path as a word of a loop's own list",
     "for f in <tool>; do a-free-command; done"),
]

# ⛔ The shapes a rewrite is made on, and the shapes that must be refused instead
# although the same entry states a bound. The second list is the whole of what
# `one_command` decides, so every construct it refuses is named in it.
MUST_REWRITE = [
    ("the command itself", "<tool>"),
    ("the same command spelled relatively", "./<tool>"),
    ("with arguments of its own", "<tool> an-argument another-argument"),
    ("with a quoted argument", "<tool> 'an argument with a space'"),
    ("behind an environment assignment", "A_VARIABLE=a-value <tool>"),
]

MUST_REFUSE_RATHER_THAN_REWRITE = [
    ("a second command after it", "<tool> && a-free-command"),
    ("a semicolon after it", "<tool>;"),
    ("a pipe", "<tool> | a-free-command"),
    ("a redirection", "<tool> > a-file"),
    ("a wrapper in front of it", "sudo <tool>"),
    ("a substitution around it", "a-free-command $(<tool>)"),
    ("a brace group around it", "{ <tool>; }"),
    ("a second line", "<tool>\na-free-command"),
]

# The commands a project would name, with no project in any of them.
UNBOUNDED_COMMAND = "a-directory/a-command-whose-output-nothing-bounds"
A_BOUND = "--A-BOUNDING-FLAG 200"
A_FORM = "a-bounded-form-to-run"
EXEMPT_COMMAND = "a-directory/a-command-a-role-is-forbidden-to-truncate"


def self_test() -> int:  # noqa: PLR0912, PLR0915 -- one assertion per rule, read top to bottom
    out: list[str] = []
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        out.append(f"  {'ok  ' if ok else 'FAIL'}  {name}"
                   + (f" — {detail}" if detail and not ok else ""))
        if not ok:
            failures.append(name)

    def decision(answer: dict) -> str:
        return str(answer.get("hookSpecificOutput", {}).get("permissionDecision", ""))

    def reason(answer: dict) -> str:
        return str(answer.get("hookSpecificOutput", {}).get("permissionDecisionReason", ""))

    def rewritten(answer: dict) -> str:
        return str(answer.get("hookSpecificOutput", {}).get("updatedInput", {}).get("command", ""))

    def told(answer: dict) -> str:
        return str(answer.get("hookSpecificOutput", {}).get("additionalContext", ""))

    def replaced(answer: dict) -> str:
        return str(answer.get("hookSpecificOutput", {}).get("updatedToolOutput", ""))

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        os.environ["CLAUDE_PLUGIN_DATA"] = str(root / "a-plugin-store")
        sidecar = str(root / "outside-every-tree" / "the-results-that-were-replaced")
        # The two entry shapes, each in a configuration of its own: one the
        # refusal names a form for, one the rewrite adds a flag to.
        forms = _a_config([_an_entry(UNBOUNDED_COMMAND, instead=A_FORM)])
        bounds = _a_config([_an_entry(UNBOUNDED_COMMAND, bound=A_BOUND)])

        out.append("A project naming no unbounded command gets no answer at all:")
        nothing = _a_config([], limit=20000, sidecar=sidecar)
        for command in (UNBOUNDED_COMMAND, f"sudo {UNBOUNDED_COMMAND}", "any-command-at-all"):
            answered = guard_answer(_call(command), config=nothing)
            check(f"no answer for: {command[:56]}", answered == {}, repr(answered)[:120])

        # ⛔ The lists themselves, which are a surface nothing else holds: a shape
        # that lost its placeholder, a rewrite shape that is not one command, or
        # two rows joined by a missing comma assert nothing while reading as a
        # row somebody wrote.
        out.append("")
        out.append("The lists these assertions are driven by are well-formed, row by row:")
        bad = [label for label, shape in
               MUST_HOLD + MUST_PASS + MUST_REWRITE + MUST_REFUSE_RATHER_THAN_REWRITE
               if "<tool>" not in shape]
        check("every planted shape carries the unbounded command", not bad, f"{bad}")
        bad = [label for label, shape in MUST_REWRITE
               if not one_command(shape.replace("<tool>", UNBOUNDED_COMMAND))]
        check("every shape a rewrite is asserted on is one command", not bad, f"{bad}")
        bad = [label for label, shape in MUST_REFUSE_RATHER_THAN_REWRITE
               if one_command(shape.replace("<tool>", UNBOUNDED_COMMAND))]
        check("and every shape a refusal is asserted on is not", not bad, f"{bad}")
        bad = [phrase for phrase in (UNPARSEABLE, NO_SIDECAR, UNREADABLE_RESULT)
               if not phrase.strip()]
        check("each unestablished fact has a phrase to report", not bad, f"{bad}")
        check("the bound a plant adds is a flag and a value", len(A_BOUND.split()) == 2, A_BOUND)

        out.append("")
        out.append("Every call shape an unbounded command arrives in is refused:")
        for label, shape in MUST_HOLD:
            command = shape.replace("<tool>", UNBOUNDED_COMMAND)
            answered = guard_answer(_call(command), config=forms)
            check(label, decision(answered) == "deny", f"{command[:60]!r} → {answered!r}"[:140])

        out.append("")
        out.append("And a call that merely names one is not — the defect paid for once:")
        for label, shape in MUST_PASS:
            command = shape.replace("<tool>", UNBOUNDED_COMMAND)
            answered = guard_answer(_call(command), config=forms)
            check(label, answered == {}, f"{command[:60]!r} → {answered!r}"[:140])
        base = os.path.basename(UNBOUNDED_COMMAND)
        check("a command of the same base name in another place is another command",
              guard_answer(_call(f"another-place/{base}"), config=forms) == {},
              repr(guard_answer(_call(f"another-place/{base}"), config=forms))[:140])

        out.append("")
        out.append("Where a flag bounds the command the call is rewritten and runs:")
        for label, shape in MUST_REWRITE:
            command = shape.replace("<tool>", UNBOUNDED_COMMAND)
            answered = guard_answer(_call(command), config=bounds)
            check(label, rewritten(answered) == f"{command} {A_BOUND}",
                  f"{command[:60]!r} → {answered!r}"[:160])
            check(f"{label}, and nothing is refused",
                  "permissionDecision" not in answered.get("hookSpecificOutput", {}),
                  repr(answered)[:140])
        answered = guard_answer(_call(UNBOUNDED_COMMAND), config=bounds)
        check("the session is told the bound was added, rather than only the person",
              A_BOUND in told(answered) and "bounded rather than complete" in told(answered),
              told(answered)[:200])
        check("and the report says what it was added for",
              "nothing bounds" in told(answered), told(answered)[:200])

        out.append("")
        out.append("A call a rewrite cannot be made on is refused instead, naming the bound:")
        for label, shape in MUST_REFUSE_RATHER_THAN_REWRITE:
            command = shape.replace("<tool>", UNBOUNDED_COMMAND)
            answered = guard_answer(_call(command), config=bounds)
            check(label, decision(answered) == "deny" and A_BOUND in reason(answered),
                  f"{command[:60]!r} → {answered!r}"[:160])

        out.append("")
        out.append("A call that is already bounded passes, and says nothing:")
        for label, command in (
            ("the flag and its value as two words", f"{UNBOUNDED_COMMAND} --A-BOUNDING-FLAG 10"),
            ("the flag with its value attached", f"{UNBOUNDED_COMMAND} --A-BOUNDING-FLAG=10"),
            ("a bound smaller than the project's own", f"{UNBOUNDED_COMMAND} --A-BOUNDING-FLAG 1"),
            ("a bound larger than it", f"{UNBOUNDED_COMMAND} --A-BOUNDING-FLAG 100000"),
            ("the flag among other arguments",
             f"{UNBOUNDED_COMMAND} an-argument --A-BOUNDING-FLAG 10 another"),
        ):
            answered = guard_answer(_call(command), config=bounds)
            check(label, answered == {}, f"{command[:60]!r} → {answered!r}"[:140])
        # ⛔ A flag that merely starts with the bound's own is not that flag, so
        # the call is still unbounded and the bound is still added. ⚠️ Asserted on
        # the rewrite rather than on a verdict: this call is one command, so a
        # guard that read the longer flag as the bound would answer nothing at
        # all, and *nothing* is what every passing shape above also answers.
        longer = guard_answer(_call(f"{UNBOUNDED_COMMAND} --A-BOUNDING-FLAGGED 10"), config=bounds)
        check("a flag that merely starts with the bound's own is not that flag",
              rewritten(longer).endswith(A_BOUND), repr(longer)[:160])

        out.append("")
        out.append("A narrowing pattern decides which spelling of one command is held:")
        narrowed = _a_config([
            _an_entry(UNBOUNDED_COMMAND, instead=A_FORM, args_match="(^| )--WHOLE-TREE-FLAG( |$)")
        ])
        check("the spelling the pattern names is refused",
              decision(guard_answer(
                  _call(f"{UNBOUNDED_COMMAND} --WHOLE-TREE-FLAG"), config=narrowed)) == "deny")
        check("and the spelling it does not name passes",
              guard_answer(_call(f"{UNBOUNDED_COMMAND} a-path"), config=narrowed) == {})

        out.append("")
        out.append("A command the project names as never bounded is neither held nor replaced:")
        both = _a_config(
            [_an_entry(EXEMPT_COMMAND, instead=A_FORM), _an_entry(UNBOUNDED_COMMAND, bound=A_BOUND)],
            spared=[EXEMPT_COMMAND], limit=2000, sidecar=sidecar,
        )
        long_result = "a-line-of-the-measurement\n" * 2000
        check("the call itself runs untouched",
              guard_answer(_call(f"{EXEMPT_COMMAND} --every-transcript"), config=both) == {},
              repr(guard_answer(_call(EXEMPT_COMMAND), config=both))[:140])
        check("behind a wrapper too",
              guard_answer(_call(f"sudo {EXEMPT_COMMAND}"), config=both) == {})
        check("and its result comes back whole, however long it is",
              result_answer(_came_back(EXEMPT_COMMAND, long_result), config=both) == {},
              repr(result_answer(_came_back(EXEMPT_COMMAND, long_result), config=both))[:140])
        # ⛔ The green side verified by taking the exemption away rather than
        # argued: with the same command no longer named, both arms have to act, or
        # the three assertions above would pass with the exemption never read.
        without = _a_config(
            [_an_entry(EXEMPT_COMMAND, instead=A_FORM)], limit=2000, sidecar=sidecar,
        )
        check("and with the exemption removed the same call is refused",
              decision(guard_answer(_call(f"{EXEMPT_COMMAND} --every-transcript"),
                                    config=without)) == "deny")
        check("and the same result is replaced",
              bool(replaced(result_answer(_came_back(EXEMPT_COMMAND, long_result),
                                          config=without))))
        # ⛔ An exemption is matched at a command position like every entry, so a
        # call that merely *names* an exempt command is not exempt — asserted on
        # the rewrite the other entry of this configuration earns, since an
        # exemption read off the text would answer nothing here.
        naming = guard_answer(_call(f"{UNBOUNDED_COMMAND} {EXEMPT_COMMAND}"), config=both)
        check("a call that merely names the exempt command is not exempt",
              rewritten(naming).endswith(A_BOUND), repr(naming)[:160])

        out.append("")
        out.append("A result nothing bounded reaches the window as a path, a head and a tail:")
        curbed = _a_config([], limit=2000, sidecar=sidecar)
        answered = result_answer(_came_back("a-free-command", long_result), config=curbed)
        shown = replaced(answered)
        check("the result is replaced", bool(shown), repr(answered)[:140])
        check("the replacement is shorter than what it replaced", 0 < len(shown) < len(long_result),
              f"{len(shown)} against {len(long_result)}")
        check("it carries the head of the result", long_result[:200] in shown, shown[:120])
        check("and the tail of it", long_result[-200:] in shown, shown[-120:])
        check("it names the limit the project stated", "2000" in shown, shown[:200])
        check("and the rule it was replaced under", FACET_CITATION in shown, shown[:200])
        check("the answer is keyed to the event the harness asked on",
              answered.get("hookSpecificOutput", {}).get("hookEventName") == RESULT_EVENT,
              repr(answered)[:160])
        where = re.search(r"on disk at (.+)", shown)
        check("the replacement names a path", where is not None, shown[:200])
        # ⛔ Read defensively, so a path naming no file is **reported** rather than
        # raised: found by breaking this arm on purpose, where the suite died with
        # a traceback instead of naming the assertion that had stopped holding.
        on_disk = None
        if where is not None:
            try:
                on_disk = Path(where.group(1)).read_text(encoding="utf-8")
            except OSError as error:
                on_disk = f"could not be read: {error}"
        check("and the whole of the result is on disk at it", on_disk == long_result,
              str(on_disk)[:120])
        check("a result inside the limit is not replaced",
              result_answer(_came_back("a-free-command", "a-short-result"), config=curbed) == {})
        check("a project stating no limit replaces nothing",
              result_answer(_came_back("a-free-command", long_result),
                            config=_a_config([], sidecar=sidecar)) == {})
        # ⛔ The one case where rendering the replacement would break the arm's own
        # promise, asserted at a limit nothing else here uses.
        tiny = _a_config([], limit=1, sidecar=sidecar)
        check("a replacement that would not be shorter is not made",
              result_answer(_came_back("a-free-command", "a-result-of-forty-two-characters-or-so"),
                            config=tiny) == {},
              repr(result_answer(_came_back("a-free-command", "x" * 50), config=tiny))[:140])
        # A structured response, which is the shape a command's result arrives in.
        structured = result_answer(
            _came_back("a-free-command", {"stdout": long_result, "stderr": "", "interrupted": False}),
            config=curbed,
        )
        check("a response carrying its text under a key is measured and replaced too",
              bool(replaced(structured)), repr(structured)[:140])
        check("a response whose text could not be read is reported, not replaced",
              "hookSpecificOutput" not in result_answer(
                  _came_back("a-free-command", 12345), config=curbed),
              repr(result_answer(_came_back("a-free-command", 12345), config=curbed))[:140])
        # ⛔ The plant has to reach the write itself: a directory nobody has
        # created yet is one this arm creates, so what makes the write fail is a
        # **file** standing where the directory would be.
        in_the_way = root / "a-file-in-the-way"
        in_the_way.write_text("a file, where a directory was named\n", encoding="utf-8")
        unwritable = _a_config([], limit=2000, sidecar=str(in_the_way / "under-it"))
        answered = result_answer(_came_back("a-free-command", long_result), config=unwritable)
        check("and a result that could not be written is reported, not replaced",
              NO_SIDECAR in str(answered.get("systemMessage", ""))
              and "hookSpecificOutput" not in answered, repr(answered)[:200])

        out.append("")
        out.append("A read this session has already made is refused, and a new one is not:")
        read_me = root / "a-file-this-session-reads"
        read_me.write_text("a line\n" * 50, encoding="utf-8")
        reading = _a_config([])
        first = _a_read(str(read_me))
        check("the first read of a file passes", guard_answer(first, config=reading) == {})
        check("and nothing is recorded until the read happened",
              guard_answer(first, config=reading) == {})
        result_answer(first, config=reading)
        check("the same read again is refused",
              decision(guard_answer(first, config=reading)) == "deny",
              repr(guard_answer(first, config=reading))[:140])
        held = reason(guard_answer(first, config=reading))
        check("the refusal names the file", str(read_me) in held, held[:200])
        check("it cites the rule it is held under", READ_CITATION in held, held[:200])
        check("and it names what unblocks it", "different part" in held, held[:200])
        check("a read of another part of the same file is a different read",
              guard_answer(_a_read(str(read_me), offset=10, limit=5), config=reading) == {})
        result_answer(_a_read(str(read_me), offset=10, limit=5), config=reading)
        check("and that range is then refused on its own",
              decision(guard_answer(_a_read(str(read_me), offset=10, limit=5),
                                    config=reading)) == "deny")
        check("while the whole-file read stays refused beside it",
              decision(guard_answer(first, config=reading)) == "deny")
        read_me.write_text("a line\n" * 51, encoding="utf-8")
        check("a re-read after the file changed is not refused",
              guard_answer(first, config=reading) == {},
              repr(guard_answer(first, config=reading))[:140])
        result_answer(first, config=reading)
        check("and the changed file is recorded as it now stands",
              decision(guard_answer(first, config=reading)) == "deny")
        # ⛔ A read's own result is never replaced, whatever its length: the
        # replacement arm is the command tool's, and a role told to redirect a
        # measurement to a file and read the file would otherwise meet a head and
        # a tail in place of the thing it was told not to truncate (§ 22).
        curbing = _a_config([], limit=2000, sidecar=sidecar)
        big = root / "a-file-longer-than-the-limit"
        big.write_text("a line of the measurement\n" * 2000, encoding="utf-8")
        came_back = {**_a_read(str(big)), "tool_response": big.read_text(encoding="utf-8")}
        check("a read's own result is not replaced, however long it is",
              result_answer(came_back, config=curbing) == {},
              repr(result_answer(came_back, config=curbing))[:140])
        check("and the same text coming back from a command is replaced",
              bool(replaced(result_answer(
                  _came_back("a-free-command", big.read_text(encoding="utf-8")),
                  config=curbing))))
        check("another session's reads are not this session's",
              guard_answer(_a_read(str(read_me), session="another-session"),
                           config=reading) == {})
        check("an event naming no session holds nothing",
              guard_answer({**first, "session_id": ""}, config=reading) == {})
        check("a read of a path that could not be read holds nothing",
              guard_answer(_a_read(str(root / "a-file-nobody-wrote")), config=reading) == {})
        check("a read naming no path at all holds nothing",
              guard_answer({"tool_name": READ_TOOL, "cwd": ".", "session_id": "a-session",
                            "tool_input": {}}, config=reading) == {})
        # ⛔ The green side of the arm's own key, verified by stating the other
        # value rather than argued: with `allow`, the same read that was refused
        # above has to pass, and nothing may be written for it either.
        allowed = _a_config([], reread="allow")
        permitted = _a_read(str(root / "a-file-read-under-allow"))
        (root / "a-file-read-under-allow").write_text("a line\n", encoding="utf-8")
        result_answer(permitted, config=allowed)
        check("a project stating `allow` refuses no read",
              guard_answer(permitted, config=allowed) == {})
        check("and records none either, which is what `allow` has to mean",
              read_key(permitted["tool_input"]) not in ledger("a-session"))

        out.append("")
        out.append("Every fact that could not be established leaves the call alone:")
        unparsed = f"a-free-command 'an unclosed quote; {UNBOUNDED_COMMAND}"
        answered = guard_answer(_call(unparsed), config=forms)
        check("an unparseable call proceeds rather than being refused",
              "hookSpecificOutput" not in answered, repr(answered)[:140])
        check("and the report says which fact was not established",
              UNPARSEABLE in str(answered.get("systemMessage", "")),
              str(answered.get("systemMessage"))[:200])
        check("while a project naming no unbounded command says nothing about it either",
              guard_answer(_call(unparsed), config=nothing) == {})
        check("a result of an unparseable call is still measured",
              bool(replaced(result_answer(_came_back(unparsed, long_result), config=curbed))))

        out.append("")
        out.append("What each arm answers nothing on:")
        check("another tool's call", guard_answer(
            {"tool_name": "Edit", "cwd": ".", "session_id": "a-session",
             "tool_input": {"command": UNBOUNDED_COMMAND}}, config=forms) == {})
        check("another tool's result", result_answer(
            {"tool_name": "Edit", "cwd": ".", "tool_input": {},
             "tool_response": long_result}, config=curbed) == {})
        check("an empty command", guard_answer(_call("   "), config=forms) == {})
        check("a tool input of another shape", guard_answer(
            {"tool_name": COMMAND_TOOL, "cwd": ".", "tool_input": "a string"},
            config=forms) == {})

        out.append("")
        out.append("A project that states no configuration gets nothing at all:")
        bare = _a_root(root / "states-nothing", None)
        # ⛔ The predicate first, because the silence below is reachable by another
        # route: a project that states nothing also fails to load, so an arm whose
        # configuration gate was gone would still answer nothing.
        check("the shared reader says this project states none",
              states_a_configuration(bare) is False)
        check("no answer on a command",
              guard_answer({**_call(UNBOUNDED_COMMAND), "cwd": bare}) == {})
        check("no answer on a read", guard_answer({**_a_read(str(read_me)), "cwd": bare}) == {})
        check("and none on a result",
              result_answer({**_came_back("a-free-command", long_result), "cwd": bare}) == {})

        out.append("")
        out.append("A configuration that is there and does not resolve is reported, not refused:")
        broken = _a_root(root / "states-nonsense", "roots: [this is not a mapping]\n")
        answered = guard_answer({**_call(UNBOUNDED_COMMAND), "cwd": broken})
        check("the call is held to nothing rather than refused",
              "hookSpecificOutput" not in answered and bool(answered.get("systemMessage")),
              repr(answered)[:160])
        check("and the person is told which guard held nothing",
              "held to nothing" in str(answered.get("systemMessage")),
              str(answered.get("systemMessage"))[:160])
        check("the result arm says the same thing",
              "held to nothing" in str(result_answer(
                  {**_came_back("a-free-command", long_result), "cwd": broken}
              ).get("systemMessage", "")))

    # ⛔ The one thing the fake above cannot assert: that the keys these arms read
    # are the keys a shipped configuration actually resolves to. The fake answers
    # as the reader does by construction, so a rename of `unbounded`,
    # `never_bound`, the limit, the sidecar or the facet itself would leave every
    # assertion above green -- and the project would get a guard that reads
    # nothing.
    out.append("")
    out.append("A configuration the shared reader resolved is read through the same keys:")
    import config as shipped  # noqa: PLC0415 -- the path is set at import time

    carried, limited, spared_by = [], [], []
    for name in sorted(os.listdir(shipped.EXAMPLES)):
        if not name.endswith((".yaml", ".yml")):
            continue
        with open(os.path.join(shipped.EXAMPLES, name), encoding="utf-8") as handle:
            loaded = shipped.load_text(handle.read(), ".")
        if entries(loaded):
            carried.append((name, loaded))
        if limit_of(loaded) is not None:
            limited.append((name, loaded))
        if never_bound(loaded):
            spared_by.append((name, loaded))
    if not carried:
        check("an example configuration names an unbounded command", False,
              "no shipped example carries an entry, so this arm reads nothing")
    if not limited:
        check("an example configuration states a result limit", False,
              "no shipped example states one, so that arm reads nothing")
    if not spared_by:
        check("an example configuration exempts a command", False,
              "no shipped example does, so the exemption reads nothing")
    for name, loaded in carried:
        for entry in entries(loaded):
            # ⚠️ Quoted, because a command position is **one token**: an example's
            # command is a placeholder in prose, and a call that spelled it bare
            # would put its first word in the position and match nothing.
            called = shlex.quote(str(entry.get("command")))
            # ⛔ An entry narrowed by a pattern needs a call that pattern matches,
            # or this arm would assert that a *correctly* narrowed entry holds
            # nothing. The arguments are the pattern's own literal words, and
            # ⚠️ an entry whose pattern they do not satisfy reddens rather than
            # being skipped: a check that holds nothing reports green.
            pattern = entry.get("args_match")
            if isinstance(pattern, str) and pattern.strip():
                derived = " ".join(re.findall(r"[\w./=-]{3,}", pattern))
                check(f"{name}: its narrowing pattern can be exercised from its own words",
                      bool(derived) and bool(re.search(pattern, derived)),
                      f"{pattern!r} against {derived!r}")
                called = f"{called} {derived}"
            answered = guard_answer(_call(called), config=loaded)
            acted = bool(decision(answered) or rewritten(answered))
            check(f"{name}: `{entry.get('command')}` is held or rewritten", acted,
                  f"{called!r} → {answered!r}"[:140])
            if decision(answered) == "deny":
                check(f"{name}: and the refusal names what the call would cost",
                      str(entry.get("reason")) in reason(answered), reason(answered)[:200])
            # ⛔ The entry's own route past the refusal, run back through the same
            # guard: a `instead` that is itself held is an entry refusing every
            # route it offers, which no shape rule in the reader can catch.
            instead = entry.get("instead")
            if isinstance(instead, str) and instead.strip():
                check(f"{name}: and the form it names instead is not itself held",
                      guard_answer(_call(instead), config=loaded) == {},
                      repr(guard_answer(_call(instead), config=loaded))[:140])
        check(f"{name}: a command it says nothing about is not held",
              guard_answer(_call("a-command-no-example-names"), config=loaded) == {})
    # ⛔ Run with the working directory moved out of this tree, because an
    # example's `sidecar_dir` is a **placeholder** rather than a path: it is
    # relative, so the write it earns lands under whatever directory this suite
    # is standing in. Found by reading `git status` after a green run, which
    # carried two directories named after the placeholders, inside the repository
    # the examples are shipped from.
    here = os.getcwd()
    with tempfile.TemporaryDirectory() as elsewhere:
        try:
            os.chdir(elsewhere)
            for name, loaded in limited:
                stated = limit_of(loaded)
                over = "a-line-of-a-result\n" * (stated // 4)
                answered = result_answer(
                    _came_back("a-command-no-example-names", over), config=loaded)
                check(f"{name}: a result over its own limit is replaced",
                      bool(replaced(answered)), repr(answered)[:160])
                named = os.path.expandvars(str(loaded.get(SIDECAR)))
                check(f"{name}: and the path it names is under the directory it states",
                      named in replaced(answered), replaced(answered)[:200])
                written = re.search(r"on disk at (.+)", replaced(answered))
                check(f"{name}: and the full text is on disk at that path",
                      written is not None and os.path.isfile(written.group(1)),
                      replaced(answered)[:200])
        finally:
            os.chdir(here)
    for name, loaded in spared_by:
        for spared in never_bound(loaded):
            check(f"{name}: its exempt command `{spared}` is not held",
                  guard_answer(_call(shlex.quote(spared)), config=loaded) == {},
                  repr(guard_answer(_call(shlex.quote(spared)), config=loaded))[:140])
            check(f"{name}: and its result is not replaced",
                  result_answer(_came_back(shlex.quote(spared), "a-line\n" * 20000),
                                config=loaded) == {})

    out.append("")
    out.append("The surface still states every rule this carrier performs:")
    text = SURFACE.read_text(encoding="utf-8")
    problems = check_the_surface_still_states_this(text)
    check("every subsection cited is a heading of the surface", not problems,
          "; ".join(problems)[:200])
    for arm, slug in sorted(ARM_ANCHORS.items()):
        planted = _reword_heading(text, slug)
        check(f"and reddens when the `{arm}` subsection is reanchored",
              bool(check_the_surface_still_states_this(planted)))

    out.append("")
    out.append("The carrier still calls both arms, on their events and on both tools:")
    carrier = CARRIER.read_text(encoding="utf-8")
    problems = check_the_carrier_still_calls_this(carrier)
    check("the carrier as it stands registers both arms", not problems,
          "; ".join(problems)[:200])
    for label, plant in CARRIER_PLANTS:
        planted = plant(carrier)
        if planted == carrier:
            check(label, False, "the plant was a no-op")
            continue
        check(label, bool(check_the_carrier_still_calls_this(planted)))

    out.append("")
    out.append("Both arms fail open and interrupt nothing:")
    for arm, answer in (("guard", guard_answer), ("result", result_answer)):
        printed = io.StringIO()
        check(f"the `{arm}` arm answers a payload it cannot read with silence",
              hook(io.StringIO("not json at all"), answer, printed) == 0
              and not printed.getvalue(), printed.getvalue()[:120])
    # ⛔ And an answer each arm *can* read reaches the harness, which the
    # assertions above cannot say: they assert silence, so a hook answering
    # nothing at all would leave them green.
    printed = io.StringIO()
    reading = _a_config([_an_entry(UNBOUNDED_COMMAND, instead=A_FORM)])
    hook(io.StringIO(json.dumps(_call(UNBOUNDED_COMMAND))),
         lambda payload: guard_answer(payload, config=reading), printed)
    written = printed.getvalue()
    check("and the guard's answer is written as one line of JSON",
          written.count("\n") == 1
          and json.loads(written)["hookSpecificOutput"]["permissionDecision"] == "deny",
          written[:160])
    with tempfile.TemporaryDirectory() as directory:
        printed = io.StringIO()
        curbed = _a_config([], limit=2000, sidecar=str(Path(directory) / "the-replaced-results"))
        hook(io.StringIO(json.dumps(_came_back("a-free-command", "a-line\n" * 2000))),
             lambda payload: result_answer(payload, config=curbed), printed)
        written = printed.getvalue()
        check("and the result arm's answer is written the same way",
              written.count("\n") == 1
              and bool(json.loads(written)["hookSpecificOutput"]["updatedToolOutput"]),
              written[:160])

    print("\n".join(out))
    print()
    if failures:
        print(f"{len(failures)} assertion(s) failed:")
        for name in failures:
            print(f"  - {name}")
        return 1
    print(
        "Every call shape an unbounded command arrives in is refused and every shape that merely "
        "names one is not; a call a flag bounds is rewritten and the session is told so; a result "
        "nothing bounded reaches the window as a path, a head and a tail with the whole of it on "
        "disk; a read this session already made is refused and a read of something changed is not; "
        "and a command the project named as never bounded meets none of it. Nothing here knows "
        "which of a project's commands are unbounded: the commands are the project's and the "
        "bounds are its own."
    )
    return 0


# --- entry point -----------------------------------------------------------


def hook(stream, answer, out=None) -> int:
    """Answer one payload. ⛔ Fails open and says nothing, per the module docstring."""
    out = out if out is not None else sys.stdout
    try:
        payload = json.load(stream)
        answered = answer(payload if isinstance(payload, dict) else {})
    except Exception:  # noqa: BLE001 — a session must not be interrupted by this
        return 0
    if answered:
        print(json.dumps(answered), file=out)
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    if len(argv) == 1 and argv[0] == "guard":
        return hook(sys.stdin, guard_answer)
    if len(argv) == 1 and argv[0] == "result":
        return hook(sys.stdin, result_answer)
    print(f"unrecognised argument(s): {' '.join(argv)}\n\n{__doc__}")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
