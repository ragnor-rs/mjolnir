#!/usr/bin/env python3
"""Hold a command that could open a session on a machine outside this one.

The surface states which commands a project has decided open such a session,
where the machines that are *not* live are named, which verdict each permission
mode gets and the four facts whose absence puts the call to a person -- see
`schema.md § 20 -> A command that could open a session on a live machine` and
the three subsections beside it. This script is the carrier for each:

    guard   a `PreToolUse` answer: put the call to the person, or refuse it --
            and nothing at all where the project names no session command, or
            states no configuration

⛔ **Nothing here knows which machine is live, and no host, alias, user, jump
path or fingerprint is written below.** The commands are the project's, the
names that clear a call live in a file outside every working tree, and what this
file carries is the command position, the machine a call names, the decision and
the report (`schema.md § 20`).

⛔ **The command position is not resolved here either.** It is `spend.py`'s, one
facet over, and it is imported rather than copied: the parse carries a hundred
lines of measurement about where a command *is* in a call, and two copies of it
would be two readings of the shell allowed to disagree about which token is the
command (`schema.md § 19 -> The command position`).

⚠️ **What this cannot hold is stated rather than discovered**, in
`docs/single-source-of-truth.md` § The live half rather than restated here: the
machine read out of a call is its first plain word, so a command whose target
sits elsewhere is put to a person rather than passed, and a name spelled another
way is another name.

Usage:
    live.py guard              a hook payload on stdin
    live.py --self-test
"""

from __future__ import annotations

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
    "facet": "20-a-command-that-could-open-a-session-on-a-live-machine",
    "verdict": "which-verdict-and-who-would-answer-the-prompt",
    "allowlist": "the-machines-named-are-the-ones-that-are-not-live",
    "closed": "the-four-ways-it-fails-closed",
    # The parse this carrier reads rather than states, and the two § 7 rules it
    # obeys rather than states: an install is silent in a project that
    # configures nothing, and the direction a guard fails in is procedure.
    "position": "the-command-position-and-why-the-whole-call-is-not-one",
    "unconfigured": "a-hook-in-a-project-that-states-no-configuration",
    "direction": "which-direction-a-guard-fails-in",
}

FACET_CITATION = "schema § 20 → A command that could open a session on a live machine"
VERDICT_CITATION = "schema § 20 → Which verdict, and who would answer the prompt"
ALLOWLIST_CITATION = "schema § 20 → The machines named are the ones that are not live"
CLOSED_CITATION = "schema § 20 → The four ways it fails closed"

# The carrier, and the event the one arm answers. ⛔ Held rather than assumed: an
# arm whose event stopped being registered is dead in every session, and a dead
# guard holds nothing while every reader goes on reporting it installed.
CARRIER = Path(__file__).resolve().parent.parent / "hooks" / "hooks.json"
GUARD_EVENT = "PreToolUse"

# The one tool a command arrives through. A session is opened by running
# something, and that is this tool's calls and no other's.
GUARDED_TOOL = "Bash"

# --- what the configuration states ------------------------------------------

TOOLS = "live_guard.session_tools"
ALLOWLIST = "live_guard.allowlist"
LOCAL = "live_guard.local_names"

# --- who would answer the prompt --------------------------------------------
#
# ⛔ The harness's own vocabulary and not this surface's, by `schema.md § 20 ->
# Which verdict`: which mode a session is in is not a project's fact, so no key
# states it and no project may call an unattended mode answered. What is read
# here is the mode the event arrived with, and the two groups are the whole of
# the decision.
#
# ⚠️ Each group is what was **measured** of the harness's documented behaviour
# rather than inferred from the mode's name, and the one thing the names would
# have got wrong is in the second group: a mode that auto-*denies* the prompt is
# in it, because a component of the session can still approve on its own behalf,
# which is the test the subsection states rather than whether a call runs.

# A mode whose prompt reaches the person running the session.
ANSWERED_BY_A_PERSON = {
    # The ordinary mode, and the one a mode the harness calls manual arrives as.
    "default",
    # A shell command outside the read-only set still prompts here.
    "plan",
    # Edits are accepted for the person; a command of this kind still prompts.
    "acceptEdits",
}

# A mode that answers its own prompts, by whatever route.
ANSWERED_BY_THE_SESSION = {
    # A classifier reviews the action instead of a person.
    "auto",
    # Every call that would prompt is auto-answered; an installed component can
    # still approve one, which is the arm that makes this a session answering on
    # its own behalf rather than a refusal.
    "dontAsk",
    # Prompts are disabled outright and the call runs.
    "bypassPermissions",
}

# The field the mode arrives in, and the decision an unlisted one gets. ⛔ The
# stricter of the two, which is the direction a reader of a state it cannot
# understand has to err in (§ 20 → Which verdict) -- and it covers a payload
# carrying no mode at all for the same reason.
PERMISSION_MODE = "permission_mode"
UNRECOGNISED = "deny"

# --- what could not be established ------------------------------------------
#
# The four of `§ 20 -> The four ways it fails closed`, each as the phrase the
# report names it by. ⛔ Read by the suite, so a reword travels rather than
# breaking it.

NO_LIST = "the allowlist names no file on this machine"
UNPARSEABLE = "this call could not be parsed"
UNREADABLE_TARGET = "the machine this call names could not be read"
NO_MACHINE = "this call names no machine"

# A word carrying any of these is a word the shell would resolve and this guard
# would not: an expansion of a variable, and whatever a substitution left behind.
# ⚠️ The substitution case arrives as a *missing* word rather than as this one --
# the parse replaces a substitution's body with a space -- so what this catches
# is the expansion written plainly.
UNRESOLVED = re.compile(r"[$`]")

# How much of a segment a report quotes.
SHOWN = 160

# A line of the allowlist that names nothing: blank, or a comment.
A_COMMENT = re.compile(r"\s*#")


def verdict_for(mode: str) -> str:
    """`ask` where a person would answer the prompt, `deny` where the session would."""
    if mode in ANSWERED_BY_A_PERSON:
        return "ask"
    if mode in ANSWERED_BY_THE_SESSION:
        return "deny"
    return UNRECOGNISED


def entries(config) -> list[dict]:
    """The commands this project says open a session. `[]` is its stated absence."""
    stated = config.get(TOOLS)
    if not isinstance(stated, list):
        return []
    return [entry for entry in stated if isinstance(entry, dict)]


def named_in(path, config) -> set[str] | None:
    """The machines named as not live, or None where no file could be read.

    ⛔ None and an empty set are different answers, and the difference is the
    first of § 20's four: a file nobody has written on this machine is a machine
    where every name is live, while a file that exists and names nothing is a
    project's own statement that nothing is allowlisted yet. Both put a call to a
    person; only the first says *there is no list* when it does.

    ⚠️ The names a project states as this machine's are read in beside them, from
    the configuration rather than from the file: `local_names` is the one list
    § 20 keeps on the surface, and a loopback name is not another machine's
    identity.
    """
    local = config.get(LOCAL)
    here = {
        str(name).strip()
        for name in (local if isinstance(local, list) else [])
        if str(name).strip()
    }
    if not isinstance(path, str) or not path.strip():
        return None
    try:
        with open(os.path.expanduser(path.strip()), encoding="utf-8") as handle:
            lines = handle.read().splitlines()
    except OSError:
        # ⛔ Every failure to read is the same answer, deliberately: a file that
        # is not there, a directory where a file was named and a file this user
        # may not open are one state to a guard -- there is no list here -- and
        # telling them apart would be a report about somebody's filesystem
        # rather than about the call in hand.
        return None
    return here | {
        line.split("#")[0].strip()
        for line in lines
        if line.strip() and not A_COMMENT.match(line)
    }


def machine_of(arguments: list[str], valued_flags) -> tuple[str | None, str | None]:
    """The machine a call names, or None with the reason it could not be read.

    ⛔ The first plain word, after the flags: `§ 20` states that reading and the
    direction it is wrong in, and this function performs it rather than deciding
    it. A flag written with its value attached is one word and carries both; a
    flag the entry names as taking a separate word consumes the word after it;
    a flag this entry does not name consumes nothing, so **its** value stands
    where the machine would -- which is a name in no allowlist and therefore a
    call put to a person.

    ⚠️ `--` ends the flags, and what follows it is read as plainly as a word that
    never looked like a flag.
    """
    takes_a_value = {
        str(flag).strip()
        for flag in (valued_flags if isinstance(valued_flags, list) else [])
        if isinstance(flag, str) and flag.strip()
    }
    index, ended = 0, False
    while index < len(arguments):
        word = arguments[index]
        index += 1
        if not ended and word == "--":
            ended = True
            continue
        if not ended and word.startswith("-") and len(word) > 1:
            flag, equals, _value = word.partition("=")
            if not equals and flag in takes_a_value:
                index += 1
            continue
        if UNRESOLVED.search(word):
            return None, UNREADABLE_TARGET
        # A leading user and a trailing path are the two things a session
        # command's own syntax wraps a machine in. ⚠️ The user is dropped rather
        # than read: § 20 keeps every user out of this toolkit, and what the
        # guard decides on is the machine.
        name = word.rpartition("@")[2]
        name = name.partition(":")[0]
        if not name.strip():
            return None, UNREADABLE_TARGET
        return name.strip(), None
    return None, NO_MACHINE


def _names_a_tool(called: str, entry: dict) -> bool:
    configured = entry.get("command")
    if not isinstance(configured, str):
        return False
    return position.names_the_command(called, configured)


def holds(config, command: str) -> list[dict]:
    """Every (entry, segment) this call opens a session in, in the call's own order.

    ⛔ One record per *segment*, for the reason the sibling guard keeps one: a
    person reading *this call reaches a machine* against four semicolons has no
    way to tell which of them was meant.

    ⛔ **An unparseable call is held on its tokens rather than on its
    positions.** A call the lexer could not read has no reliable command
    position in it, so *no session command here* would be a reading of a parse
    that did not happen -- the second of § 20's four. ⚠️ Which is the one place
    this guard looks at a token outside a command position, and it is the
    direction the position rule exists to protect: it holds a call rather than
    letting one through.
    """
    stated = entries(config)
    if not stated:
        return []
    if not position.readable(command):
        found = []
        for token in position.words(command):
            for entry in stated:
                if _names_a_tool(token, entry):
                    found.append({
                        "entry": entry,
                        "segment": 1,
                        "called": token,
                        "shown": command[:SHOWN],
                        "machine": None,
                        "why": UNPARSEABLE,
                    })
        return found
    found = []
    for at, segment in enumerate(position.segments(command), start=1):
        for called, arguments in position.command_chain(segment):
            for entry in stated:
                if not _names_a_tool(called, entry):
                    continue
                machine, why = machine_of(arguments, entry.get("valued_flags"))
                found.append({
                    "entry": entry,
                    "segment": at,
                    "called": called,
                    "shown": " ".join(segment)[:SHOWN],
                    "machine": machine,
                    "why": why,
                })
    return found


# --- the decision -----------------------------------------------------------


def _decision(kind: str, reason: str) -> dict:
    return {
        "hookSpecificOutput": {
            "hookEventName": GUARD_EVENT,
            "permissionDecision": kind,
            "permissionDecisionReason": reason,
        }
    }


def live_guard(config, command: str, mode: str) -> dict:
    """Hold a call that could open a session elsewhere, or answer nothing at all."""
    found = holds(config, command)
    if not found:
        return {}
    stated = config.get(ALLOWLIST)
    cleared = named_in(stated, config)
    lines, held = [], False
    for match in found:
        machine, why = match["machine"], match["why"]
        if why is None and cleared is None:
            why = NO_LIST
        if why is None and machine in cleared:
            # ⛔ The one silent answer this guard has, and it is silence rather
            # than an `allow`: § 20 states the verdict is never that, so a
            # machine the project named as not live is left to the permission
            # flow the session already has.
            continue
        held = True
        reaching = (
            f"reaching `{machine}`"
            if why is None or (machine and why == NO_LIST)
            else f"and {why}"
        )
        lines.append(
            f"segment {match['segment']} — `{match['shown']}` — runs "
            f"{match['entry'].get('command')!r}, which this project states opens a session on "
            f"another machine, {reaching}"
        )
    if not held:
        return {}
    where = (
        f"The machines that are not live are named in `{stated}`"
        if isinstance(stated, str) and stated.strip()
        else "This project names no file for the machines that are not live"
    )
    if cleared is None:
        where += f" — and {NO_LIST}, so every name here reads as live"
    kind = verdict_for(mode)
    body = (
        "This command could open a session on a live machine:\n  "
        + "\n  ".join(lines)
        + f"\n{where} ({ALLOWLIST_CITATION})."
    )
    if kind == "ask":
        return _decision("ask", (
            f"{body}\n⛔ Neither verdict here is the approval: what this catches is a connection "
            f"nobody asked for ({VERDICT_CITATION}). What unblocks it is an answer here, now — or, "
            "where this machine is not live, its name in the file above, which clears every later "
            "call of it."
        ))
    return _decision("deny", (
        f"{body}\n⛔ This session is in a mode that answers its own prompts, so no answer inside it "
        f"releases the call ({VERDICT_CITATION}): a prompt the session can clear on its own behalf "
        "is not approval. What unblocks it is the approval being asked for in the conversation, or "
        "a person opening the session themselves — or, where this machine is not live, its name in "
        "the file above."
    ))


def guard_answer(payload: dict, *, config=None) -> dict:
    """The `PreToolUse` answer for one call."""
    if payload.get("tool_name") != GUARDED_TOOL:
        return {}
    command = str((payload.get("tool_input") or {}).get("command") or "")
    if not command.strip():
        return {}
    if config is None and not states_a_configuration(payload.get("cwd")):
        # ⛔ Silence, and not a report: this arm fires on every command in every
        # project the install reaches, and a project that states no
        # configuration has agreed to no rule this guard could hold (§ 7).
        return {}
    loaded = config if config is not None else _config(payload.get("cwd"))
    if loaded is None:
        # ⛔ Reported, and the call proceeds. § 20 settles this one case by
        # pointing at § 19's: what a broken configuration cannot say is whether
        # this call reaches anything at all, so the refusing arm would refuse
        # every call in the project -- the edit that repairs the configuration
        # included.
        return {"systemMessage": (
            "Live guard: the project's configuration could not be read, so this command was held "
            f"to nothing. ({FACET_CITATION})"
        )}
    return live_guard(loaded, command, str(payload.get(PERMISSION_MODE) or ""))


# --- the shared reader ------------------------------------------------------


def states_a_configuration(cwd: str | None) -> bool:
    """Whether the project this event names states a configuration at all.

    ⛔ Asked through the shared reader rather than by testing a path here: where
    a project's configuration lives is one statement, and a second copy of that
    path drifts the first time either moves.

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
    """`hooks.json` still registers this file on the event its arm answers."""
    try:
        carrier = json.loads(text)
    except json.JSONDecodeError as error:
        return [f"{CARRIER.name} is not readable as JSON ({error}), so nothing calls this."]
    hooks = carrier.get("hooks") or {}
    mine = Path(__file__).name
    problems = []
    called = None
    for group in hooks.get(GUARD_EVENT) or []:
        for item in group.get("hooks") or []:
            named = " ".join([str(item.get("command") or "")]
                             + [str(a) for a in (item.get("args") or [])])
            if mine in named:
                called = (group, named)
    if called is None:
        return [
            f"{CARRIER.name} registers no {GUARD_EVENT} hook calling {mine}, so whatever that "
            "event covers is covered by nothing."
        ]
    group, named = called
    # ⛔ The arm and not merely this file's name: a carrier naming the script with
    # no argument prints usage and answers nothing, while the event stays wired
    # and reads as installed.
    if "guard" not in named.split():
        problems.append(
            f"{CARRIER.name} calls {mine} on {GUARD_EVENT} without the `guard` arm, so that "
            "event is wired to an answer it is not the event for."
        )
    if "${CLAUDE_PLUGIN_ROOT}" not in named:
        problems.append(
            f"{CARRIER.name} names {mine} on {GUARD_EVENT} by a path the plugin root does not "
            "expand — the handler must address it through `${CLAUDE_PLUGIN_ROOT}`."
        )
    if GUARDED_TOOL not in (group.get("matcher") or ""):
        problems.append(
            f"{CARRIER.name} calls {mine} on {GUARD_EVENT} with matcher "
            f"{group.get('matcher')!r}, which does not select the one tool a command "
            "arrives through."
        )
    return problems


# --- the plants ------------------------------------------------------------
#
# ⛔ Both directions, per rule. A call that must be held and a call that must not
# are one pair, and a lone green proves nothing: a dead matcher holds nothing and
# is silent on every call there is.


def _a_config(tools: list[dict], allowlist=None, local=None):
    """A stand-in for the shared reader's answer, carrying what the arm reads.

    ⛔ A fake and not a mock: it answers as the reader does for the three keys
    this arm asks it, so a rename of any of them reddens here rather than
    passing. ⚠️ Its shape is the production one -- the dotted-path accessor --
    because a fixture thinner than that tests the fixture.
    """

    class _Loaded:
        def __init__(self):
            self.data = {"live_guard": {"session_tools": tools}}
            if allowlist is not None:
                self.data["live_guard"]["allowlist"] = allowlist
            if local is not None:
                self.data["live_guard"]["local_names"] = local

        def get(self, path, default=None):
            node = self.data
            for part in path.split("."):
                if not isinstance(node, dict) or part not in node:
                    return default
                node = node[part]
            return node

    return _Loaded()


def _a_tool(command: str, valued_flags: list[str] | None = None) -> dict:
    entry: dict = {"command": command}
    if valued_flags is not None:
        entry["valued_flags"] = valued_flags
    return entry


def _call(command: str, mode: str = "default") -> dict:
    return {
        "tool_name": GUARDED_TOOL,
        "cwd": ".",
        PERMISSION_MODE: mode,
        "tool_input": {"command": command},
    }


def _a_root(where: Path, states: str | None) -> str:
    """A project root stating this configuration, or stating none at all.

    ⛔ Written at the reader's own `CONFIG_PATH` rather than at a path spelled
    out here: a fixture built against a literal would stay green after that path
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
    ("a carrier calling a script that is not this one",
     lambda text: text.replace("live.py", "live_something_else.py")),
    ("a carrier whose expansion of the plugin root is mistyped",
     lambda text: text.replace("CLAUDE_PLUGIN_ROOT", "CLAUDE_PLUGIN_ROOTS")),
    # ⚠️ Anchored on this script's own name, so the plant takes the arm off
    # *this* entry rather than off whichever sibling also names `guard`.
    ("a carrier naming no arm at all",
     lambda text: text.replace('live.py", "guard"', 'live.py"')),
]

# The call shapes a session command actually arrives in, enumerated by hand: a
# guard asserted only against the shape its author imagined is a guard that
# holds that shape. ⛔ `<tool>` is substituted with the entry's own command and
# `<live>` with a machine no list names, so no literal here is under test.
MUST_HOLD = [
    ("the command itself", "<tool> <live>"),
    ("the same command spelled relatively", "./<tool> <live>"),
    ("with a user in front of the machine", "<tool> a-user@<live>"),
    ("with a path after the machine", "<tool> <live>:a-path a-file"),
    ("with both", "<tool> a-user@<live>:a-path a-file"),
    ("behind an environment assignment", "A_VARIABLE=a-value <tool> <live>"),
    ("behind an elevation wrapper", "sudo <tool> <live>"),
    ("behind a wrapper's own valued flag", "sudo -u a-user <tool> <live>"),
    ("after the command's end-of-flags marker", "<tool> -- <live>"),
    ("after a flag written with its value attached", "<tool> --a-flag=a-value <live>"),
    ("after a flag this entry states takes a separate word", "<tool> --a-valued-flag v <live>"),
    ("as the second command of a chain", "a-free-command && <tool> <live>"),
    ("after a semicolon", "a-free-command; <tool> <live>"),
    ("at the end of a pipe", "a-free-command | <tool> <live>"),
    ("on the second line of one call", "a-free-command\n<tool> <live>"),
    ("inside a substitution", "a-free-command $(<tool> <live>)"),
    ("inside a substitution the shell expands in quotes", 'a-free-command "$(<tool> <live>)"'),
    ("inside the older substitution spelling", "a-free-command `<tool> <live>`"),
    ("inside a brace group", "{ <tool> <live>; }"),
    ("as the body of a condition", "if a-free-command; then <tool> <live>; fi"),
    ("as the body of a loop", "for i in a b; do <tool> <live>; done"),
    ("behind the word that replaces the shell", "exec <tool> <live>"),
    ("as the command a search runs per match",
     "a-searching-command . -name a-file -exec <tool> <live> {} ;"),
    ("across a line continuation, which is not a separator", "<tool> \\\n  <live>"),
    ("with its output redirected", "<tool> <live> > a-file"),
]

# ⛔ The shapes a flag the entry does *not* name leaves behind: the flag's own
# value stands where the machine would, which is a name in no list and therefore
# a call that is held. ⚠️ Held *on that word* rather than on the machine behind
# it, which the suite asserts directly -- a verdict alone would pass if the guard
# had read the real machine and found it live.
MUST_HOLD_ON_THE_FLAGS_VALUE = [
    ("an unnamed flag's value standing first", "<tool> --an-unnamed-flag a-value <live>"),
]

MUST_PASS = [
    ("the command named inside another command's prose",
     "a-text-editing-command 'the note mentions <tool> in passing'"),
    ("the command's path as the argument of a reading command", "a-reading-command <tool>"),
    ("the command's path as a redirection's target", "a-free-command > <tool>"),
    ("a command whose name merely ends in the configured one", "a-prefix-<tool> <live>"),
    ("the command inside single quotes", "a-printing-command '<tool> <live>'"),
    ("a here-document whose body names the command",
     "a-writing-command <<'A_DELIMITER' > a-file\n<tool> <live> is the step\nA_DELIMITER"),
    ("the command's path as a word of a loop's own list",
     "for f in <tool>; do a-free-command; done"),
]

# The machines a project named as not live, and the one it did not. ⛔ Placeholder
# names with no project in them, by § 20's rule that no machine's identity enters
# this toolkit.
LIVE = "a-machine-no-list-names"
ALLOWED = "a-borrowed-egress-box"
LOCAL_NAME = "a-name-that-leaves-nothing"


def self_test() -> int:  # noqa: PLR0915 -- one assertion per rule, read top to bottom
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

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        listed = root / "outside-every-tree" / "the-names-that-are-not-live"
        listed.parent.mkdir(parents=True, exist_ok=True)
        listed.write_text(
            f"# a comment, which names nothing\n\n{ALLOWED}\n", encoding="utf-8"
        )
        missing = str(root / "outside-every-tree" / "a-file-nobody-wrote")

        tool = "a-directory/a-command-that-opens-a-session"
        base = os.path.basename(tool)
        one = _a_config(
            [_a_tool(tool, ["--a-valued-flag"])],
            allowlist=str(listed),
            local=[LOCAL_NAME],
        )

        out.append("A project that names no session command gets no live hook:")
        nothing = _a_config([], allowlist=str(listed))
        for command in (f"{tool} {LIVE}", f"sudo {tool} {LIVE}", "any-command-at-all"):
            answered = guard_answer(_call(command), config=nothing)
            check(f"no answer for: {command[:56]}", answered == {}, repr(answered)[:120])

        # ⛔ The tables themselves, which are a surface nothing else holds: a mode
        # mistyped, a group that overlaps the other, or two shapes joined by a
        # missing comma matches nothing the decision ever reads, and every
        # assertion below stays green because the other rows are intact.
        out.append("")
        out.append("The tables this decision reads are well-formed, row by row:")
        bad = sorted(ANSWERED_BY_A_PERSON & ANSWERED_BY_THE_SESSION)
        check("no mode is in both groups", not bad, f"{bad}")
        bad = [m for m in ANSWERED_BY_A_PERSON | ANSWERED_BY_THE_SESSION
               if not m or len(m.split()) != 1]
        check("every mode is one word, so no two rows were joined by a missing comma",
              not bad, f"{bad}")
        check("the person-answered group is not empty", bool(ANSWERED_BY_A_PERSON))
        check("and neither is the session-answered one", bool(ANSWERED_BY_THE_SESSION))
        bad = [label for label, shape in MUST_HOLD + MUST_PASS + MUST_HOLD_ON_THE_FLAGS_VALUE
               if "<tool>" not in shape]
        check("every planted shape carries the session command", not bad, f"{bad}")
        bad = [phrase for phrase in (NO_LIST, UNPARSEABLE, UNREADABLE_TARGET, NO_MACHINE)
               if not phrase.strip()]
        check("each of the four unestablished facts has a phrase to report", not bad, f"{bad}")

        out.append("")
        out.append("Every call shape a session command arrives in is held:")
        for label, shape in MUST_HOLD:
            command = shape.replace("<tool>", tool).replace("<live>", LIVE)
            answered = guard_answer(_call(command), config=one)
            check(label, decision(answered) == "ask", f"{command[:60]!r} → {answered!r}"[:140])
        for label, shape in MUST_HOLD_ON_THE_FLAGS_VALUE:
            command = shape.replace("<tool>", tool).replace("<live>", ALLOWED)
            answered = guard_answer(_call(command), config=one)
            # ⛔ The machine the guard read, and not merely that it held: the
            # real machine in this shape is one the list clears, so a guard that
            # skipped the flag's value would pass -- which is the arm this plant
            # exists for and the reason the word is named in the assertion.
            check(f"{label}, and on that value", decision(answered) == "ask"
                  and "a-value" in reason(answered),
                  f"{command[:60]!r} → {answered!r}"[:160])

        out.append("")
        out.append("And a call that is not one of it is not held — the defect paid for once:")
        for label, shape in MUST_PASS:
            command = shape.replace("<tool>", tool).replace("<live>", LIVE)
            answered = guard_answer(_call(command), config=one)
            check(label, answered == {}, f"{command[:60]!r} → {answered!r}"[:140])
        check("a command of the same base name in another place is another command",
              guard_answer(_call(f"another-place/{base} {LIVE}"), config=one) == {},
              repr(guard_answer(_call(f"another-place/{base} {LIVE}"), config=one))[:140])

        out.append("")
        out.append("A machine the project named as not live passes, and says nothing:")
        for label, command in (
            ("a name in the file outside every tree", f"{tool} {ALLOWED}"),
            ("the same name with a user in front of it", f"{tool} a-user@{ALLOWED}"),
            ("the same name with a path after it", f"{tool} {ALLOWED}:a-path a-file"),
            ("a name the configuration states is this machine", f"{tool} {LOCAL_NAME}"),
            # ⛔ The plant that reaches the flag rule, and the only one that can:
            # a flag the entry names takes the word after it, so the machine is
            # the word behind *that*. ⚠️ Where the flag's value were read as the
            # machine instead, this call would be held — the verdict shapes above
            # all pass with the rule dead, because a value in no list is held
            # exactly as a live machine is.
            ("the machine behind a flag the entry says takes a separate word",
             f"{tool} --a-valued-flag a-value {ALLOWED}"),
        ):
            answered = guard_answer(_call(command), config=one)
            check(label, answered == {}, f"{command[:60]!r} → {answered!r}"[:140])
        # ⛔ The green side, verified by taking the exemption away rather than
        # argued: the same call against a configuration whose file names nothing
        # has to be held, or the four assertions above would pass with the
        # allowlist never read at all.
        empty = root / "outside-every-tree" / "a-file-naming-nothing"
        empty.write_text("# nothing is cleared yet\n", encoding="utf-8")
        check("and the same call is held where that file names nothing",
              decision(guard_answer(_call(f"{tool} {ALLOWED}"), config=_a_config(
                  [_a_tool(tool)], allowlist=str(empty)))) == "ask")
        check("and where the project states no local name either",
              decision(guard_answer(_call(f"{tool} {LOCAL_NAME}"), config=_a_config(
                  [_a_tool(tool)], allowlist=str(empty)))) == "ask")

        out.append("")
        out.append("Each of the four facts that cannot be established holds the call:")
        for label, config, command, phrase in (
            ("the allowlist names no file on this machine",
             _a_config([_a_tool(tool)], allowlist=missing), f"{tool} {ALLOWED}", NO_LIST),
            ("the call cannot be parsed",
             one, f"a-free-command 'an unclosed quote; {tool} {ALLOWED}", UNPARSEABLE),
            ("the machine is named by an expansion",
             one, f"{tool} $A_VARIABLE", UNREADABLE_TARGET),
            ("the call names no machine at all", one, f"{tool} --a-valued-flag v", NO_MACHINE),
        ):
            answered = guard_answer(_call(command), config=config)
            check(f"{label} — the call is held", decision(answered) == "ask",
                  f"{command[:60]!r} → {answered!r}"[:140])
            check(f"{label} — and the report says which fact", phrase in reason(answered),
                  reason(answered)[:200])

        out.append("")
        out.append("Which verdict it is depends on who would answer the prompt:")
        for mode in sorted(ANSWERED_BY_A_PERSON):
            check(f"`{mode}` puts the call to the person",
                  decision(guard_answer(_call(f"{tool} {LIVE}", mode=mode),
                                        config=one)) == "ask")
        for mode in sorted(ANSWERED_BY_THE_SESSION):
            check(f"`{mode}` answers its own prompts, so the call is refused",
                  decision(guard_answer(_call(f"{tool} {LIVE}", mode=mode),
                                        config=one)) == "deny")
        check("a mode this carrier does not recognise is refused",
              decision(guard_answer(_call(f"{tool} {LIVE}", mode="a-mode-nobody-states"),
                                    config=one)) == "deny")
        check("and a payload carrying no mode at all is refused too",
              decision(guard_answer({"tool_name": GUARDED_TOOL, "cwd": ".",
                                     "tool_input": {"command": f"{tool} {LIVE}"}},
                                    config=one)) == "deny")
        check("the verdict is never `allow`, whatever the mode",
              all(decision(guard_answer(_call(f"{tool} {LIVE}", mode=mode), config=one))
                  != "allow"
                  for mode in sorted(ANSWERED_BY_A_PERSON | ANSWERED_BY_THE_SESSION)
                  + ["a-mode-nobody-states"]))

        out.append("")
        out.append("What the report says, which no verdict asserts by itself:")
        asked = guard_answer(_call(f"a-free-command && {tool} {LIVE}"), config=one)
        check("the segment that reaches a machine is named by number",
              "segment 2" in reason(asked), reason(asked)[:200])
        check("the entry's own command is named", tool in reason(asked), reason(asked)[:200])
        check("the machine the call reaches is named", LIVE in reason(asked),
              reason(asked)[:200])
        check("the file the names would be cleared in is named",
              str(listed) in reason(asked), reason(asked)[:200])
        check("the rule it is held under is cited", VERDICT_CITATION in reason(asked),
              reason(asked)[:200])
        check("and the report says what unblocks it", "unblocks" in reason(asked),
              reason(asked)[:200])
        check("neither free command is named", "a-free-command" not in reason(asked).split("`")[2]
              if reason(asked).count("`") > 2 else True, reason(asked)[:200])
        check("the answer is keyed to the event the harness asked on",
              asked.get("hookSpecificOutput", {}).get("hookEventName") == GUARD_EVENT,
              repr(asked)[:160])
        refused = guard_answer(_call(f"{tool} {LIVE}", mode="bypassPermissions"), config=one)
        check("a refusal says the approval has to be asked for in the conversation",
              "conversation" in reason(refused), reason(refused)[:200])
        check("and that clearing a prompt on the session's own behalf is not approval",
              "not approval" in reason(refused), reason(refused)[:200])
        check("two segments that each reach a machine are both named",
              len(holds(one, f"{tool} {LIVE}; {tool} {LIVE}")) == 2)
        check("a compound of free commands is answered with nothing",
              guard_answer(_call("a-free-command && another-free-command"), config=one) == {})
        check("the guard answers nothing on another tool",
              guard_answer({"tool_name": "Edit", "cwd": ".", PERMISSION_MODE: "default",
                            "tool_input": {"command": f"{tool} {LIVE}"}}, config=one) == {})
        check("and nothing on an empty command", guard_answer(_call("   "), config=one) == {})

        out.append("")
        out.append("A project that states no configuration gets nothing at all:")
        bare = _a_root(root / "states-nothing", None)
        # ⛔ The predicate first, because the silence below is reachable by
        # another route: a project that states nothing also fails to load, so an
        # arm whose configuration gate was gone would still answer nothing.
        check("the shared reader says this project states none",
              states_a_configuration(bare) is False)
        check("no answer on a command",
              guard_answer({**_call(f"{tool} {LIVE}"), "cwd": bare}) == {})

        out.append("")
        out.append("A configuration that is there and does not resolve is reported, not refused:")
        broken = _a_root(root / "states-nonsense", "roots: [this is not a mapping]\n")
        answered = guard_answer({**_call(f"{tool} {LIVE}"), "cwd": broken})
        check("the call is held to nothing rather than denied",
              "hookSpecificOutput" not in answered and bool(answered.get("systemMessage")),
              repr(answered)[:160])
        check("and the person is told which guard held nothing",
              "held to nothing" in str(answered.get("systemMessage")),
              str(answered.get("systemMessage"))[:160])

        out.append("")
        out.append("The allowlist is read as a file of names, and nothing else:")
        check("a comment in it names no machine",
              "# a comment, which names nothing" not in (named_in(str(listed), one) or set()))
        check("a blank line names nothing either",
              "" not in (named_in(str(listed), one) or set()))
        check("the names it does carry are read",
              ALLOWED in (named_in(str(listed), one) or set()))
        check("a file nobody wrote is no list rather than an empty one",
              named_in(missing, one) is None)
        check("and a key stating no path is no list either", named_in(None, one) is None)
        check("the names the configuration states as local are read beside it",
              LOCAL_NAME in (named_in(str(listed), one) or set()))

    # ⛔ The one thing the fake above cannot assert: that the keys this carrier
    # reads are the keys a shipped configuration actually resolves to. The fake
    # answers as the reader does by construction, so a rename of
    # `session_tools`, `allowlist` or the facet itself would leave every
    # assertion above green -- and the project would get a guard that reads
    # nothing.
    out.append("")
    out.append("A configuration the shared reader resolved is read through the same keys:")
    import config as shipped  # noqa: PLC0415 -- the path is set at import time

    carried = []
    for name in sorted(os.listdir(shipped.EXAMPLES)):
        if not name.endswith((".yaml", ".yml")):
            continue
        path = os.path.join(shipped.EXAMPLES, name)
        with open(path, encoding="utf-8") as handle:
            loaded = shipped.load_text(handle.read(), ".")
        if entries(loaded):
            carried.append((name, loaded))
    if not carried:
        check("an example configuration names a session command", False,
              "no shipped example carries an entry, so this arm reads nothing")
    for name, loaded in carried:
        first = entries(loaded)[0]
        # ⚠️ Quoted, because a command position is **one token**: an example's
        # command is a placeholder in prose, and a call that spelled it bare
        # would put its first word in the position and match nothing.
        called = shlex.quote(str(first.get("command")))
        answered = guard_answer(_call(f"{called} {LIVE}"), config=loaded)
        check(f"{name}: its own session command is held", decision(answered) == "ask",
              f"{called!r} → {answered!r}"[:140])
        # ⛔ And the allowlist it states is named in the report rather than
        # merely configured: the file a project would clear a name in is the one
        # thing the person meeting this refusal has to be told.
        check(f"{name}: and the file it names is in the report",
              str(loaded.get(ALLOWLIST)) in reason(answered), reason(answered)[:160])
        check(f"{name}: a command it says nothing about is not held",
              guard_answer(_call(f"a-command-no-example-names {LIVE}"), config=loaded) == {})

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
    out.append("The carrier still calls this script on the event its arm answers:")
    carrier = CARRIER.read_text(encoding="utf-8")
    problems = check_the_carrier_still_calls_this(carrier)
    check("the carrier as it stands registers this arm", not problems,
          "; ".join(problems)[:200])
    for label, plant in CARRIER_PLANTS:
        planted = plant(carrier)
        if planted == carrier:
            check(label, False, "the plant was a no-op")
            continue
        check(label, bool(check_the_carrier_still_calls_this(planted)))
    without_bash = carrier.replace(f'"matcher": "{GUARDED_TOOL}"', '"matcher": "Edit"')
    check("a matcher that selects another tool",
          without_bash != carrier and bool(check_the_carrier_still_calls_this(without_bash)))

    out.append("")
    out.append("The arm fails open and interrupts nothing:")
    stream, printed = io.StringIO("not json at all"), io.StringIO()
    check("a payload it cannot read is answered with silence",
          hook(stream, guard_answer, printed) == 0 and not printed.getvalue(),
          printed.getvalue()[:120])
    # ⛔ And an answer it *can* read reaches the harness, which the assertion
    # above cannot say: it asserts silence, so the hook could be answering
    # nothing at all with the suite green.
    printed = io.StringIO()
    with tempfile.TemporaryDirectory() as directory:
        listed = Path(directory) / "the-names-that-are-not-live"
        listed.write_text(f"{ALLOWED}\n", encoding="utf-8")
        reading = _a_config(
            [_a_tool("a-directory/a-command-that-opens-a-session")], allowlist=str(listed)
        )
        hook(io.StringIO(json.dumps(
            _call(f"a-directory/a-command-that-opens-a-session {LIVE}")
        )), lambda payload: guard_answer(payload, config=reading), printed)
    written = printed.getvalue()
    check("and an answer it can read is written to the harness as one line of JSON",
          written.count("\n") == 1
          and json.loads(written)["hookSpecificOutput"]["permissionDecision"] == "ask",
          written[:160])

    print("\n".join(out))
    print()
    if failures:
        print(f"{len(failures)} assertion(s) failed:")
        for name in failures:
            print(f"  - {name}")
        return 1
    print(
        "Every shape a session command arrives in is held and every shape that merely names one is "
        "not; a machine the project named as not live passes silently, and each of the four facts "
        "that cannot be established holds the call instead. Which verdict it is turns on who would "
        "answer the prompt. Nothing here knows which machine is live: the commands are the "
        "project's and the names are the machine's."
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
    print(f"unrecognised argument(s): {' '.join(argv)}\n\n{__doc__}")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
