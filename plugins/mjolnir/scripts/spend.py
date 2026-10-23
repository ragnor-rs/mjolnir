#!/usr/bin/env python3
"""Refuse a command that spends where nobody is answering for it.

The surface states which calls a project has decided cost money, what a refusal
names, and the one price the harness states before a turn runs -- see
`schema.md § 18 -> A command that spends, and the supervision it is refused
without`, the subsection beside it that resolves the command position, and the
one after that which states what an approval is per. This script is the carrier
for each:

    guard   a `PreToolUse` answer: put a call that spends to the person on every
            invocation, or refuse it outright -- and nothing at all where the
            project denies no command, or states no configuration
    price   a `SessionStart` answer: the price a resume states, before the first
            turn runs, and *no figure* where the harness gave none

⛔ **Nothing here judges the work, and nothing here knows what spends.** The
denied commands, their costs and every budget are the project's
(`schema.md § 18`); what this file carries is the command position, the match,
the decision and the report. ⛔ **And no interpreter, no runner and no tool is
named below**, by `schema.md § What the procedure models`: the wrappers that
stand between a call and its command are POSIX's, and a list of stacks here
would be the first project in another language getting a guard that holds
nothing.

⚠️ **What this cannot hold is the spend it never sees.** A paid command reached
through an interpreter stands in no command position of its own, and a project
that invokes one that way states that spelling itself -- the residue is stated
in `docs/single-source-of-truth.md` § The spend half rather than restated here.

Usage:
    spend.py guard             a hook payload on stdin
    spend.py price             a hook payload on stdin
    spend.py --self-test
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

# --- where the rules live --------------------------------------------------

SURFACE = Path(__file__).resolve().parent.parent / "config" / "schema.md"

# The subsections this script is the carrier for, by the anchors the code host
# would give their headings. Grammar: a heading may be reworded without touching
# this file only if its anchor survives, which is the bargain every citation of
# the surface already makes.
ARM_ANCHORS = {
    "facet": "18-a-command-that-spends-and-the-supervision-it-is-refused-without",
    "position": "the-command-position-and-why-the-whole-call-is-not-one",
    "approval": "what-an-approval-is-per-and-the-one-price-stated-before-a-turn-runs",
    # The two § 7 rules this carrier obeys rather than states: an install is
    # silent in a project that configures nothing, and the direction a guard
    # fails in is procedure rather than a setting.
    "unconfigured": "a-hook-in-a-project-that-states-no-configuration",
    "direction": "which-direction-a-guard-fails-in",
}

FACET_CITATION = "schema § 18 → A command that spends, and the supervision it is refused without"
POSITION_CITATION = "schema § 18 → The command position, and why the whole call is not one"
PRICE_CITATION = (
    "schema § 18 → What an approval is per, and the one price stated before a turn runs"
)

# The carrier, and the events the two arms answer. ⛔ Held rather than assumed:
# an arm whose event stopped being registered is dead in every session, and a
# dead guard reports green on every call it was supposed to hold.
CARRIER = Path(__file__).resolve().parent.parent / "hooks" / "hooks.json"
GUARD_EVENT = "PreToolUse"
PRICE_EVENT = "SessionStart"

# The one tool a command arrives through. A spend is reached by running
# something, and that is this tool's calls and no other's.
GUARDED_TOOL = "Bash"

# --- what the configuration states ------------------------------------------

DENY = "spend_guard.deny"
APPROVAL = "spend_guard.approval"
RESUME_BAR = "spend_guard.resume_bar_usd"

# The two decisions an approval resolves to, and the harness's own word for
# each. ⛔ The keys are the surface's alternation and `--self-test` asserts the
# surface still states both: a value this file invented would be a vocabulary
# beside the one the surface publishes, and a project writing the surface's
# spelling would get no decision at all.
DECISIONS = {"per_invocation": "ask", "denied": "deny"}

# --- what the harness states about a resume ---------------------------------
#
# The field names are the harness's own, and the figure is in the harness's own
# units -- which is why the key naming the bar names them too
# (`docs/configuration-surface.md § Why there is no threshold on the surface`).

FIGURE = "estimated_cache_write_usd"
EXPIRED = "prompt_cache_likely_expired"

# The sources the harness states a price for. ⚠️ Read in one direction only: a
# payload carrying a figure is priced whatever its source says, and this set
# decides nothing but whether a *missing* figure is reported as missing. So a
# source the harness starts pricing tomorrow is handled by the arm above rather
# than by an edit here, and the direction this set can be wrong in costs a
# report rather than a price.
PRICED_SOURCES = {"resume", "fork"}

# --- the shape of a call ----------------------------------------------------
#
# ⛔ Positions, never the text. The defect this closes was paid for once: an
# earlier version searched the raw command and refused a text edit whose prose
# happened to contain a denied script's path, and a guard that blocks honest
# work is a guard somebody turns off.

# A token that ends one command and starts another. ⚠️ A brace is in here with
# the pipes and the semicolons: a group runs its contents as commands, so a
# denied call inside one stands in a command position and a reader that kept the
# brace would have resolved the group's own `{` as the command.
SEPARATORS = set(";&|()\n{}")

# A redirection, which is **not** a separator: `<command> > <path>` is one
# command, and splitting there would put the path in a command position. That is
# the false-refusal direction -- a write to a file whose name a project denies as
# a command is honest work.
REDIRECTIONS = set("<>&")

# An environment assignment, which stands before a command rather than being
# one.
ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")

# A wrapper runs the command that follows it, so the command is one token
# further right -- and its own flags move the command further right again. ⛔ The
# flags that take a **separate** value are named per wrapper, for the measurement
# this toolkit's other guards already carry: dropping every word that opens with
# a dash and reading the next one puts a flag's value where the command stands,
# and the guard is then installed and holding nothing.
#
# ⚠️ These are the POSIX wrappers rather than any project's tooling, by the
# boundary rule this file's docstring cites. A project whose own paid command is
# spelled like one of them is still guarded, because every command position of a
# call is matched rather than the innermost one.
WRAPPERS = {
    "sudo": {"-u", "--user", "-g", "--group", "-p", "--prompt", "-h", "--host",
             "-U", "--other-user", "-r", "--role", "-t", "--type", "-C",
             "--close-from", "-D", "--chdir", "-R", "--chroot"},
    "env": {"-u", "--unset", "-C", "--chdir", "-S", "--split-string"},
    "time": {"-f", "--format", "-o", "--output"},
    "nohup": set(),
}

# How much of a segment a report quotes.
SHOWN = 160


def words(command: str) -> list[str]:
    """Every token of a call, with the separators kept as tokens of their own.

    ⛔ The shell's own quoting, so a separator inside a quoted argument is part
    of that argument and not a separator: `<command> "a; b"` is one command, and
    a reader splitting on the text would have found two.

    ⚠️ A newline is a separator here and whitespace to this lexer by default, so
    it is moved into the punctuation set -- two commands on two lines read as one
    command with an argument otherwise, which hides the second one's position.

    ⚠️ And `#` is not a comment marker: the shell starts a comment at the start
    of a word, while this lexer would truncate a word at one -- so an address
    carrying a fragment would take the rest of the call with it. Left as an
    ordinary character, a real comment's `#` stands in the command position and
    matches nothing, which is the same answer by a cheaper route.
    """
    lexer = shlex.shlex(command, posix=True, punctuation_chars="();<>|&\n")
    lexer.whitespace_split = True
    lexer.whitespace = " \t\r"
    lexer.commenters = ""
    try:
        return list(lexer)
    except ValueError:
        # A call this lexer cannot read is a call the shell cannot read either,
        # and the fallback reads the words between the separators rather than
        # answering nothing at all: a quote nobody closed must not be the way
        # past a guard.
        return [w for w in re.split(r"([;&|()\n{}])", command) for w in w.split() if w]


def segments(command: str) -> list[list[str]]:
    """The call's commands, each as its own list of words.

    Separators end a segment; a redirection and its target are dropped, for the
    reason stated beside `REDIRECTIONS`. An empty segment is kept out, so a
    trailing separator is not a command that spends nothing.
    """
    out: list[list[str]] = [[]]
    skip = False
    for token in words(command):
        if skip:
            skip = False
            continue
        if token and set(token) <= REDIRECTIONS and (set(token) & set("<>")):
            skip = True
            continue
        if token and set(token) <= SEPARATORS:
            out.append([])
            continue
        out[-1].append(token)
    return [segment for segment in out if segment]


def command_chain(segment: list[str]) -> list[tuple[str, list[str]]]:
    """Every command position in one segment, as (the token, its arguments).

    A segment with no wrapper has one position. A wrapper contributes its own,
    and the command it runs contributes the next -- so a call behind a stack of
    them is matched at each level, which is what makes a project's paid command
    guarded even where it is spelled like a wrapper.
    """
    out: list[tuple[str, list[str]]] = []
    index = 0
    while index < len(segment):
        token = segment[index]
        if ASSIGNMENT.match(token):
            index += 1
            continue
        out.append((token, [w for w in segment[index + 1:] if not ASSIGNMENT.match(w)]))
        flags = WRAPPERS.get(os.path.basename(token))
        if flags is None:
            return out
        index += 1
        while index < len(segment):
            word = segment[index]
            if word == "--":
                index += 1
                break
            if ASSIGNMENT.match(word):
                index += 1
                continue
            if word.startswith("-"):
                flag, equals, _value = word.partition("=")
                index += 1
                if not equals and flag in flags and index < len(segment):
                    index += 1
                continue
            break
    return out


def names_the_command(called: str, configured: str) -> bool:
    """Whether a token in a command position is the command an entry names.

    ⛔ Compared as a path rather than as a word: one command is spelled
    absolutely, relatively and bare for the shell to resolve, so what matches is
    equality or a suffix at a path separator in either direction. A name that
    merely ends in the configured one is a different command, and the separator
    is what tells those two apart.
    """
    if not called.strip() or not configured.strip():
        return False
    here, there = os.path.normpath(called.strip()), os.path.normpath(configured.strip())
    return here == there or here.endswith(f"/{there}") or there.endswith(f"/{here}")


def entries(config) -> list[dict]:
    """The calls this project has decided spend. `[]` is its stated absence."""
    stated = config.get(DENY)
    return [entry for entry in stated if isinstance(entry, dict)] if isinstance(stated, list) else []


def matches(command: str, stated: list[dict]) -> list[dict]:
    """Every (entry, segment) pair this call matches, in the call's own order.

    ⛔ One record per *segment* rather than one per call, because a refusal has
    to name which segment spends: a person reading *this call spends* against
    four semicolons has no way to tell which of them was meant.
    """
    found: list[dict] = []
    for position, segment in enumerate(segments(command), start=1):
        for called, arguments in command_chain(segment):
            for entry in stated:
                configured = entry.get("command")
                if not isinstance(configured, str) or not names_the_command(called, configured):
                    continue
                pattern = entry.get("args_match")
                if isinstance(pattern, str) and pattern.strip():
                    try:
                        if not re.search(pattern, " ".join(arguments)):
                            continue
                    except re.error:
                        # Refused at load by the shared reader (§ 18), so this is
                        # the arm nothing reaches through a validated
                        # configuration. It does not match on a pattern it cannot
                        # compile: a guard that refused every call of the command
                        # instead would be refusing on a configuration defect.
                        continue
                found.append({
                    "entry": entry,
                    "segment": position,
                    "called": called,
                    "shown": " ".join(segment)[:SHOWN],
                })
    return found


# --- the decision -----------------------------------------------------------


def approval_of(config) -> str:
    """The decision this project's approval resolves to, as the harness spells it.

    ⚠️ The default is the surface's own marker and is applied by the shared
    reader, so an unset key arrives here already resolved. A value outside the
    alternation is refused at load; what this falls back to is the stricter of
    the two, which is the direction a reader of a configuration it cannot
    understand has to err in.
    """
    return DECISIONS.get(str(config.get(APPROVAL) or ""), "deny")


def _decision(kind: str, reason: str) -> dict:
    return {
        "hookSpecificOutput": {
            "hookEventName": GUARD_EVENT,
            "permissionDecision": kind,
            "permissionDecisionReason": reason,
        }
    }


def spend_guard(config, command: str) -> dict:
    """Hold a call that this project says spends, or answer nothing at all."""
    stated = entries(config)
    if not stated:
        return {}
    found = matches(command, stated)
    if not found:
        return {}
    kind = approval_of(config)
    lines = []
    for match in found:
        entry = match["entry"]
        pattern = entry.get("args_match")
        narrowed = (
            f", whose arguments carry {pattern!r}"
            if isinstance(pattern, str) and pattern.strip()
            else ""
        )
        lines.append(
            f"segment {match['segment']} — `{match['shown']}` — runs "
            f"{entry.get('command')!r}{narrowed}, and this project states what that costs: "
            f"{entry.get('reason')}"
        )
    held = "This command spends:\n  " + "\n  ".join(lines)
    if kind == "ask":
        return _decision("ask", (
            f"{held}\n⛔ The go is per invocation and nothing is remembered between calls "
            f"({PRICE_CITATION}). What unblocks it is an answer here, now: a session nobody is "
            "watching gets none, and then the call does not run."
        ))
    return _decision("deny", (
        f"{held}\n⛔ This project states `approval: denied`, so no answer inside a session "
        f"releases it ({PRICE_CITATION}). What unblocks it is a person running the command "
        "themselves, outside every loop — or the project's own configuration saying otherwise."
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
        # project the install reaches, and a project that states no configuration
        # has agreed to no rule this guard could hold (§ 7). Separate from the
        # branch below, which is a configuration that *is* stated and does not
        # resolve.
        return {}
    loaded = config if config is not None else _config(payload.get("cwd"))
    if loaded is None:
        # ⛔ Reported, and the call proceeds. § 7's table settles this by whether
        # the act can be undone, and the act here is not known to be a spend at
        # all: what a broken configuration cannot say is whether this call is one
        # of the denied ones, so the refusing arm would refuse every call in the
        # project — the edit that repairs the configuration included (§ 18).
        return {"systemMessage": (
            "Spend guard: the project's configuration could not be read, so this command was "
            f"held to nothing. ({FACET_CITATION})"
        )}
    return spend_guard(loaded, command)


# --- the price a resume states ----------------------------------------------


def price_answer(payload: dict, *, config=None) -> dict:
    """The `SessionStart` answer: what this resume states it costs.

    ⚠️ It goes to the person and never into the session's context. The channel
    that reaches a person is `systemMessage`; spending is their call, and a
    figure handed to the session would be carried into every reply it writes.
    """
    if str(payload.get("hook_event_name") or PRICE_EVENT) != PRICE_EVENT:
        return {}
    if config is None and not states_a_configuration(payload.get("cwd")):
        return {}
    loaded = config if config is not None else _config(payload.get("cwd"))
    if loaded is None:
        return {}
    bar = loaded.get(RESUME_BAR)
    if not isinstance(bar, (int, float)) or isinstance(bar, bool):
        # An unset bar prices no resume, and then this arm says nothing (§ 18).
        return {}
    stated = payload.get(FIGURE)
    source = str(payload.get("source") or "")
    if isinstance(stated, bool) or not isinstance(stated, (int, float)):
        if source not in PRICED_SOURCES:
            return {}
        return {"systemMessage": (
            f"Spend guard: this session ({source}) carries **no figure** for what rewriting its "
            f"prompt cache costs. ⛔ Not free: an unstated cost and a cost of zero read "
            f"identically, and the bar of {bar} could not be applied to either. "
            f"({PRICE_CITATION})"
        )}
    if stated <= bar:
        return {}
    cache = ""
    if isinstance(payload.get(EXPIRED), bool):
        cache = (
            " The prompt cache had likely expired."
            if payload[EXPIRED]
            else " The prompt cache had likely not expired."
        )
    return {"systemMessage": (
        f"Spend guard: this session ({source or 'opened'}) states a cache-write price of "
        f"{stated}, above the bar of {bar} this project set.{cache} ⚠️ It prices this one event "
        f"and says nothing about what any command here costs. ({PRICE_CITATION})"
    )}


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


def check_the_decisions_are_the_surfaces(text: str) -> list[str]:
    """Each approval this file decides for is one the surface states.

    ⛔ The vocabulary is read out of the surface's own alternation rather than
    carried here: a project writing the surface's spelling and getting no
    decision is a guard that reports installed and holds nothing, and a value
    this file invented would be a second vocabulary beside a published one.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        import config as reader  # noqa: PLC0415 -- the path is set one line up
        stated = list(reader.surface_facts(text)["enums"].get(APPROVAL) or [])
    except Exception as error:  # noqa: BLE001 -- any failure is a named absence
        return [f"the surface's own alternation for `{APPROVAL}` could not be read ({error})."]
    if not stated:
        return [
            f"the surface states no alternation at `{APPROVAL}`, so which approvals exist is "
            "this file's claim rather than the surface's."
        ]
    problems = [
        f"the surface states `{value}` at `{APPROVAL}` and this carrier decides nothing for it, "
        "so a project writing it gets no decision at all."
        for value in stated if value not in DECISIONS
    ]
    problems += [
        f"this carrier decides for `{value}`, which the surface does not state at `{APPROVAL}`."
        for value in DECISIONS if value not in stated
    ]
    return problems


def check_the_carrier_still_calls_this(text: str) -> list[str]:
    """`hooks.json` still registers this file on both events an arm answers.

    ⛔ Both rather than one: the guard and the price are independent arms, and an
    event that stopped being registered leaves its arm dead in every session
    while the other goes on answering — which reads as an install that works.
    """
    try:
        carrier = json.loads(text)
    except json.JSONDecodeError as error:
        return [f"{CARRIER.name} is not readable as JSON ({error}), so nothing calls this."]
    hooks = carrier.get("hooks") or {}
    mine = Path(__file__).name
    problems = []
    for event in (GUARD_EVENT, PRICE_EVENT):
        called = None
        for group in hooks.get(event) or []:
            for item in group.get("hooks") or []:
                named = " ".join([str(item.get("command") or "")]
                                 + [str(a) for a in (item.get("args") or [])])
                if mine in named:
                    called = (group, named)
        if called is None:
            problems.append(
                f"{CARRIER.name} registers no {event} hook calling {mine}, so whatever that "
                "event covers is covered by nothing."
            )
            continue
        group, named = called
        if "${CLAUDE_PLUGIN_ROOT}" not in named:
            problems.append(
                f"{CARRIER.name} names {mine} on {event} by a path the plugin root does not "
                "expand — the handler must address it through `${CLAUDE_PLUGIN_ROOT}`."
            )
        if event == GUARD_EVENT and GUARDED_TOOL not in (group.get("matcher") or ""):
            problems.append(
                f"{CARRIER.name} calls {mine} on {event} with matcher "
                f"{group.get('matcher')!r}, which does not select the one tool a command "
                "arrives through."
            )
    return problems


# --- the plants ------------------------------------------------------------
#
# ⛔ Both directions, per rule. A denial that must be refused and a call that
# must not be is one pair, and a lone green proves nothing: a dead matcher
# refuses nothing and is green on every call there is.


def _a_config(denied: list[dict], approval: str = "per_invocation", bar=None):
    """A stand-in for the shared reader's answer, carrying what an arm reads.

    ⛔ A fake and not a mock: it answers as the reader does for the three keys an
    arm asks it, so a rename of any of them reddens here rather than passing.
    ⚠️ Its shape is the production one -- the dotted-path accessor -- because a
    fixture thinner than that tests the fixture.
    """

    class _Loaded:
        def __init__(self):
            self.data = {"spend_guard": {"deny": denied, "approval": approval}}
            if bar is not None:
                self.data["spend_guard"]["resume_bar_usd"] = bar

        def get(self, path, default=None):
            node = self.data
            for part in path.split("."):
                if not isinstance(node, dict) or part not in node:
                    return default
                node = node[part]
            return node

    return _Loaded()


def _a_denial(command: str, args_match: str | None = None,
              reason: str = "what one call of it costs") -> dict:
    entry = {"command": command, "reason": reason}
    if args_match is not None:
        entry["args_match"] = args_match
    return entry


def _call(command: str) -> dict:
    return {
        "tool_name": GUARDED_TOOL,
        "cwd": ".",
        "tool_input": {"command": command},
    }


def _resume(figure=None, source: str = "resume", expired=None) -> dict:
    payload: dict = {"hook_event_name": PRICE_EVENT, "cwd": ".", "source": source}
    if figure is not None:
        payload[FIGURE] = figure
    if expired is not None:
        payload[EXPIRED] = expired
    return payload


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
    ("a carrier registering nothing for the price's event",
     lambda text: text.replace(f'"{PRICE_EVENT}"', '"Notification"')),
    ("a carrier calling a script that is not this one",
     lambda text: text.replace("spend.py", "spend_something_else.py")),
    ("a carrier whose expansion of the plugin root is mistyped",
     lambda text: text.replace("CLAUDE_PLUGIN_ROOT", "CLAUDE_PLUGIN_ROOTS")),
]

# The call shapes a denied command actually arrives in, enumerated by hand: a
# guard asserted only against the shape its author imagined is a guard that
# holds that shape. ⛔ `<deny>` is substituted with the entry's own command, so
# no literal here is the thing under test.
MUST_REFUSE = [
    ("the command itself", "<deny> --the-paid-tier"),
    ("the same command spelled relatively", "./<deny> --the-paid-tier"),
    ("behind an environment assignment", "A_VARIABLE=a-value <deny> --the-paid-tier"),
    ("behind an elevation wrapper's own valued flag", "sudo -u a-user <deny> --the-paid-tier"),
    ("behind an inline-valued flag", "sudo --user=a-user <deny> --the-paid-tier"),
    ("after a wrapper's end-of-flags marker", "sudo -- <deny> --the-paid-tier"),
    ("behind a wrapper that sets a variable for it", "env A_VARIABLE=a-value <deny> --the-paid"),
    ("behind a stack of every wrapper at once",
     " ".join(sorted(WRAPPERS)) + " <deny> --the-paid-tier"),
    ("as the second command of a chain", "a-free-command && <deny> --the-paid-tier"),
    ("after a semicolon", "a-free-command; <deny> --the-paid-tier"),
    ("at the end of a pipe", "a-free-command | <deny> --the-paid-tier"),
    ("on the second line of one call", "a-free-command\n<deny> --the-paid-tier"),
    ("inside a substitution", "a-free-command $(<deny> --the-paid-tier)"),
    ("inside a brace group", "{ <deny> --the-paid-tier; }"),
    ("with its output redirected", "<deny> --the-paid-tier > a-file"),
    ("with an argument quoted", "<deny> --the-paid-tier \"a value; with a separator\""),
]

MUST_ALLOW = [
    ("the denied path inside the prose of another command",
     "a-text-editing-command 'the note mentions <deny> in passing'"),
    ("the denied path as the argument of a reading command", "a-reading-command <deny>"),
    ("the denied path as a redirection's target", "a-free-command > <deny>"),
    ("the denied path as the value of a flag", "a-free-command --input <deny>"),
    ("a command whose name merely ends in the denied one", "a-prefix-<deny> --the-paid-tier"),
    ("a command of the same base name in another place", "another-place/<base> --the-paid-tier"),
    ("a chain of free commands", "a-free-command && another-free-command"),
]


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

    # The command a project denies, and the one it does not. Written here as the
    # fixture's own values rather than read from a configuration: what is under
    # test is the matcher, and a plant whose selection is only *where the value
    # came from* is one configuration edit away from vacuous.
    paid = "a-directory/a-command-that-spends"
    base = os.path.basename(paid)
    one = _a_config([_a_denial(paid)])

    out.append("A project that denies no command gets no spend hook:")
    nothing = _a_config([])
    for command in (paid, f"sudo {paid} --the-paid-tier", "any-command-at-all"):
        answered = guard_answer(_call(command), config=nothing)
        check(f"no answer for: {command[:56]}", answered == {}, repr(answered)[:120])
    check("and no resume is priced either",
          price_answer(_resume(figure=99.0), config=nothing) == {})

    out.append("")
    out.append("Every call shape a denied command arrives in is refused:")
    for label, shape in MUST_REFUSE:
        command = shape.replace("<deny>", paid)
        answered = guard_answer(_call(command), config=one)
        check(label, decision(answered) == "ask", f"{command[:60]!r} → {answered!r}"[:140])
    # ⛔ One plant per wrapper, derived from the table rather than written out: a
    # wrapper added there with no assertion of its own would be covered only by
    # the stack above, where a single working wrapper is enough to reach the
    # command and the rest are asserted by nothing.
    for wrapper in sorted(WRAPPERS):
        command = f"{wrapper} {paid} --the-paid-tier"
        check(f"behind `{wrapper}`, which the table names",
              decision(guard_answer(_call(command), config=one)) == "ask")

    out.append("")
    out.append("And the shapes that are not a call of it are allowed — the defect paid for once:")
    for label, shape in MUST_ALLOW:
        command = shape.replace("<deny>", paid).replace("<base>", base)
        answered = guard_answer(_call(command), config=one)
        check(label, answered == {}, f"{command[:60]!r} → {answered!r}"[:140])

    out.append("")
    out.append("The command is matched as a path and not as a word:")
    absolute = _a_config([_a_denial(f"/a-root/{paid}")])
    check("a configured absolute path matches the call that spells it relatively",
          decision(guard_answer(_call(f"./{paid}"), config=absolute)) == "ask")
    check("a configured bare name matches the call that spells it absolutely",
          decision(guard_answer(_call(f"/a-root/{paid}"), config=_a_config(
              [_a_denial(base)]))) == "ask")
    check("and a longer name ending in it is a different command",
          guard_answer(_call(f"/a-root/a-prefix-{base}"), config=_a_config(
              [_a_denial(base)])) == {})

    out.append("")
    out.append("Where the command alone does not decide, the arguments do:")
    narrowed = _a_config([_a_denial(base, args_match=r"--the-paid-tier\b")])
    check("the paid invocation of a shared runner is refused",
          decision(guard_answer(_call(f"{base} --the-paid-tier"), config=narrowed)) == "ask")
    check("and the cheap one beside it is not",
          guard_answer(_call(f"{base} --the-free-tier"), config=narrowed) == {})
    check("a pattern that would match the command itself is not matched against it",
          guard_answer(_call(f"a-directory/--the-paid-tier-runner"), config=_a_config(
              [_a_denial("--the-paid-tier-runner", args_match="the-paid-tier")])) == {})
    check("a flag and its value together are one string to the pattern",
          decision(guard_answer(_call(f"{base} --tier the-paid-one"), config=_a_config(
              [_a_denial(base, args_match="--tier the-paid-one")]))) == "ask")
    check("and an argument's quotes are gone before the pattern reads it",
          decision(guard_answer(_call(f"{base} '--tier the-paid-one'"), config=_a_config(
              [_a_denial(base, args_match="--tier the-paid-one")]))) == "ask")
    # ⛔ The plant that reaches the redirection arm, and the only one that can:
    # a redirection is not a separator, so its target never stands in a command
    # position and the allow-direction shapes above pass with that arm dead. What
    # the arm decides is whether `> <path>` is read as an *argument* of the
    # command, and an anchored pattern is what tells the two apart.
    anchored = _a_config([_a_denial(base, args_match="--the-paid-tier$")])
    check("a redirection is not an argument of the command it redirects",
          decision(guard_answer(_call(f"{base} --the-paid-tier > a-file"),
                                config=anchored)) == "ask",
          repr(guard_answer(_call(f"{base} --the-paid-tier > a-file"), config=anchored))[:140])

    out.append("")
    out.append("The two refusals the guard this was extracted from paid for, reproduced:")
    # ⛔ The first incident: the original matched its interpreter arm by glob, so
    # a *longer* name beginning with the one it denied was refused too — the
    # repository's own linter, whenever the file it was linting carried the
    # denied script's name. A rail that blocks a lint it cannot possibly spend
    # money on is a rail somebody turns off.
    interpreted = _a_config([_a_denial("a-shell", args_match="a-paid-script")])
    check("an interpreter asked to run the paid script is refused",
          decision(guard_answer(_call("a-shell a-paid-script"), config=interpreted)) == "ask")
    check("and a longer name beginning with the interpreter's is not",
          guard_answer(_call("a-shell-linter a-paid-script"), config=interpreted) == {},
          repr(guard_answer(_call("a-shell-linter a-paid-script"), config=interpreted))[:140])
    # ⚠️ The second: the original denied one subcommand of a command whose other
    # subcommands are free reads, which is the shape the arguments have to carry
    # because the command is the same either way.
    subcommanded = _a_config(
        [_a_denial("a-stack-command", args_match=r"^a-subcommand (up|start)\b")])
    check("the subcommand that spends is refused",
          decision(guard_answer(_call("a-stack-command a-subcommand up"),
                                config=subcommanded)) == "ask")
    check("and the free reads of the same command are not",
          all(guard_answer(_call(f"a-stack-command a-subcommand {verb}"),
                           config=subcommanded) == {}
              for verb in ("logs", "status", "stop")))

    out.append("")
    out.append("A compound call is refused on the segment that spends, and on no other:")
    compound = f"a-free-command && {paid} --the-paid-tier && another-free-command"
    found = matches(compound, entries(one))
    check("one segment matched, not the call", len(found) == 1, repr(found)[:140])
    check("and it is the segment the denied command stands in",
          found and found[0]["segment"] == 2 and paid in found[0]["shown"],
          repr(found)[:140])
    answered = guard_answer(_call(compound), config=one)
    check("the refusal quotes that segment", found and found[0]["shown"] in reason(answered),
          reason(answered)[:160])
    check("and names neither of the free commands",
          "another-free-command" not in reason(answered),
          reason(answered)[:160])
    check("a compound of free commands is answered with nothing",
          guard_answer(_call("a-free-command && another-free-command"), config=one) == {})
    check("and two denied segments are both named",
          len(matches(f"{paid} --one; {paid} --two", entries(one))) == 2)

    out.append("")
    out.append("What the refusal says, which no verdict asserts by itself:")
    costly = _a_config([_a_denial(base, reason="a-stated-cost-per-run")])
    asked = guard_answer(_call(base), config=costly)
    check("the project's own cost reaches the person", "a-stated-cost-per-run" in reason(asked),
          reason(asked)[:160])
    check("the rule it is refused under is cited", PRICE_CITATION in reason(asked),
          reason(asked)[:160])
    check("and the ask says what unblocks it", "unblocks" in reason(asked),
          reason(asked)[:160])
    refused = guard_answer(_call(base), config=_a_config(
        [_a_denial(base, reason="a-stated-cost-per-run")], approval="denied"))
    check("the stricter approval refuses rather than asks", decision(refused) == "deny",
          repr(refused)[:140])
    check("and its remedy is a person outside the loop, not an answer inside it",
          "themselves" in reason(refused), reason(refused)[:160])
    check("an approval this carrier cannot read refuses rather than asking",
          decision(guard_answer(_call(base), config=_a_config(
              [_a_denial(base)], approval="something-else"))) == "deny")

    out.append("")
    out.append("The price a resume states, read before the first turn runs:")
    priced = _a_config([], bar=1.0)
    above = price_answer(_resume(figure=2.5), config=priced)
    check("a figure above the bar is reported", bool(above.get("systemMessage")))
    check("and the figure itself is in it", "2.5" in str(above.get("systemMessage")),
          str(above.get("systemMessage"))[:160])
    check("and the bar it was compared against", "1.0" in str(above.get("systemMessage")),
          str(above.get("systemMessage"))[:160])
    check("and the rule is cited", PRICE_CITATION in str(above.get("systemMessage")))
    check("a figure at the bar is not reported",
          price_answer(_resume(figure=1.0), config=priced) == {})
    check("a figure below it is not reported either",
          price_answer(_resume(figure=0.1), config=priced) == {})
    missing = price_answer(_resume(figure=None), config=priced)
    check("a resume the harness priced nowhere is reported", bool(missing.get("systemMessage")))
    check("as no figure, and never as free",
          "no figure" in str(missing.get("systemMessage")).lower()
          and "not free" in str(missing.get("systemMessage")).lower(),
          str(missing.get("systemMessage"))[:160])
    check("a session the harness states no price for says nothing",
          price_answer(_resume(figure=None, source="startup"), config=priced) == {})
    check("but a figure is read whatever the source says, so a new one needs no edit here",
          bool(price_answer(_resume(figure=2.5, source="compact"),
                            config=priced).get("systemMessage")))
    check("an unset bar prices no resume",
          price_answer(_resume(figure=99.0), config=_a_config([])) == {})
    check("a bar written as a flag prices none either, `true` comparing equal to one",
          price_answer(_resume(figure=99.0), config=_a_config([], bar=True)) == {})
    expired = price_answer(_resume(figure=2.5, expired=True), config=priced)
    check("the cache's own state is reported where the harness states it",
          "expired" in str(expired.get("systemMessage")),
          str(expired.get("systemMessage"))[:160])
    check("and the price arm answers nothing on another event",
          price_answer({"hook_event_name": "Stop", "cwd": "."}, config=priced) == {})
    check("the guard arm answers nothing on another tool",
          guard_answer({"tool_name": "Edit", "cwd": ".",
                        "tool_input": {"command": paid}}, config=one) == {})
    check("and nothing on an empty command",
          guard_answer(_call("   "), config=one) == {})

    out.append("")
    out.append("An unparseable call is still read for its positions:")
    unbalanced = f"a-free-command 'an unclosed quote; {paid} --the-paid-tier"
    check("a quote nobody closed is not the way past this guard",
          decision(guard_answer(_call(unbalanced), config=one)) == "ask",
          repr(guard_answer(_call(unbalanced), config=one))[:140])

    with tempfile.TemporaryDirectory() as directory:
        out.append("")
        out.append("A project that states no configuration gets nothing at all:")
        bare = _a_root(Path(directory) / "states-nothing", None)
        check("no answer on a command",
              guard_answer({**_call(paid), "cwd": bare}) == {})
        check("and none on a resume",
              price_answer(_resume(figure=99.0) | {"cwd": bare}) == {})

        out.append("")
        out.append("A configuration that is there and does not resolve is reported, not refused:")
        broken = _a_root(Path(directory) / "states-nonsense", "roots: [this is not a mapping]\n")
        answered = guard_answer({**_call(paid), "cwd": broken})
        check("the call is held to nothing rather than denied",
              "hookSpecificOutput" not in answered and bool(answered.get("systemMessage")),
              repr(answered)[:160])
        check("and the person is told which guard held nothing",
              "held to nothing" in str(answered.get("systemMessage")),
              str(answered.get("systemMessage"))[:160])
        check("the price arm stays silent there, having no bar it could read",
              price_answer(_resume(figure=99.0) | {"cwd": broken}) == {})

    # ⛔ The one thing the fake above cannot assert: that the keys this carrier
    # reads are the keys a shipped configuration actually resolves to. The fake
    # answers as the reader does by construction, so a rename of `deny`,
    # `approval` or the facet itself would leave every assertion above green —
    # and the project would get a guard that reads nothing.
    #
    # ⚠️ The denied command comes out of the configuration rather than being
    # written here, and the assertion is that the guard *acts* on it: a fixture
    # whose only property is where its value came from asserts nothing.
    out.append("")
    out.append("A configuration the shared reader resolved is read through the same keys:")
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import config as shipped  # noqa: PLC0415 -- the path is set one line up

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
        check("an example configuration denies a command", False,
              "no shipped example carries an entry, so this arm reads nothing")
    for name, loaded in carried:
        first = entries(loaded)[0]
        # ⚠️ Quoted, because a command position is **one token**: an example's
        # command is a placeholder in prose, and a call that spelled it bare
        # would put its first word in the position and match nothing. A real
        # command carrying a space has the same shape and the same answer.
        called = shlex.quote(str(first.get("command")))
        pattern = first.get("args_match")
        arguments = "" if not isinstance(pattern, str) else f" {shlex.quote(pattern)}"
        answered = guard_answer(_call(f"{called}{arguments}"), config=loaded)
        check(f"{name}: its own denied call is held",
              decision(answered) in DECISIONS.values(),
              f"{called!r} → {answered!r}"[:140])
        check(f"{name}: and the cost it states reaches the person",
              str(first.get("reason")) in reason(answered), reason(answered)[:160])
        check(f"{name}: a command it says nothing about is not held",
              guard_answer(_call("a-command-no-example-denies"), config=loaded) == {})

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
    problems = check_the_decisions_are_the_surfaces(text)
    check("every approval the surface states has a decision here", not problems,
          "; ".join(problems)[:200])
    stripped = "\n".join(
        line for line in text.splitlines()
        if not line.strip().startswith("approval:")
    )
    check("and reddens when the surface states no approval at all",
          bool(check_the_decisions_are_the_surfaces(stripped)))

    out.append("")
    out.append("The carrier still calls this script on both events:")
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
    without_bash = carrier.replace(f'"matcher": "{GUARDED_TOOL}"', '"matcher": "Edit"')
    check("a guard matcher that selects another tool",
          without_bash != carrier and bool(check_the_carrier_still_calls_this(without_bash)))

    out.append("")
    out.append("Both arms fail open and interrupt nothing:")
    for arm, answer in (("guard", guard_answer), ("price", price_answer)):
        stream, printed = io.StringIO("not json at all"), io.StringIO()
        check(f"the {arm} arm answers a payload it cannot read with silence",
              hook(stream, answer, printed) == 0 and not printed.getvalue(),
              printed.getvalue()[:120])

    print("\n".join(out))
    print()
    if failures:
        print(f"{len(failures)} assertion(s) failed:")
        for name in failures:
            print(f"  - {name}")
        return 1
    print(
        "Every call shape a denied command arrives in is refused, every shape that merely names "
        "one is allowed, a compound call is held on the segment that spends, and a resume states "
        "its price or states none. Nothing here knows what spends: the commands, their costs and "
        "the bar are the project's."
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
    arms = {"guard": guard_answer, "price": price_answer}
    if len(argv) == 1 and argv[0] in arms:
        return hook(sys.stdin, arms[argv[0]])
    print(f"unrecognised argument(s): {' '.join(argv)}\n\n{__doc__}")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
