#!/usr/bin/env python3
"""Refuse a command that spends where nobody is answering for it.

The surface states which calls a project has decided cost money, what a refusal
names, and the one price the harness states before a turn runs -- see
`schema.md § 19 -> A command that spends, and the supervision it is refused
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
(`schema.md § 19`); what this file carries is the command position, the match,
the decision and the report. ⛔ **No interpreter and no project's tooling is
named below**, by `schema.md § What the procedure models`: a list of runners or
stacks here would be the first project writing one in another language getting a
guard that holds nothing. ⚠️ **The wrappers that are named are POSIX's own** and
stand between any call and its command whatever the stack, which is the one
thing a parse has to know to find where a command is.

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
    "facet": "19-a-command-that-spends-and-the-supervision-it-is-refused-without",
    "position": "the-command-position-and-why-the-whole-call-is-not-one",
    "approval": "what-an-approval-is-per-and-the-one-price-stated-before-a-turn-runs",
    # The two § 7 rules this carrier obeys rather than states: an install is
    # silent in a project that configures nothing, and the direction a guard
    # fails in is procedure rather than a setting.
    "unconfigured": "a-hook-in-a-project-that-states-no-configuration",
    "direction": "which-direction-a-guard-fails-in",
}

FACET_CITATION = "schema § 19 → A command that spends, and the supervision it is refused without"
POSITION_CITATION = "schema § 19 → The command position, and why the whole call is not one"
PRICE_CITATION = (
    "schema § 19 → What an approval is per, and the one price stated before a turn runs"
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

# A token that ends one command and starts another.
SEPARATORS = set(";&|()\n")

# A brace that groups commands, matched as a **whole token** rather than by its
# characters. ⛔ A group runs its contents as commands, so a denied call inside
# one stands in a command position -- while the placeholder some utilities take
# is the same two characters and is an argument. Measured by review: the
# character test refused a copy whose destination was the denied path, which is
# the false-refusal direction this whole parse exists to stay out of.
GROUPING = {"{", "}"}

# A redirection, which is **not** a separator: `<command> > <path>` is one
# command, and splitting there would put the path in a command position. That is
# the false-refusal direction -- a write to a file whose name a project denies as
# a command is honest work.
REDIRECTIONS = set("<>&")

# A here-document, whose body is **text and not commands**. ⛔ Its lines are
# newline-separated like any other, so a parse that did not skip them refused a
# document that merely quoted the denied command -- the same defect as the one
# this guard was extracted carrying, one construct over, and measured by review.
# ⚠️ The delimiter of the dash form arrives with the dash attached, which is why
# the comparison strips it rather than the token.
HEREDOC = "<<"

# A line continuation, which is not a token at all. ⚠️ Left in place, the escaped
# newline became a separator of its own where the next line was indented, which
# cut one command in two -- taking its arguments out of reach of an `args_match`
# and reading the continuation's first word as a command.
CONTINUATION = re.compile(r"\\\r?\n")

# An environment assignment, which stands before a command rather than being
# one.
ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")

# A shell word that introduces a command rather than being one. ⛔ The body of a
# condition or a loop is where a paid command is most naturally run once per
# input, and the word in front of it stood in the command position: measured by
# review, the first command of every `if`/`for`/`while` body was invisible.
# ⚠️ `in` is deliberately absent -- the words after it are a list and not
# commands, so skipping it would read a denied path in that list as a call of it.
INTRODUCERS = {"then", "do", "else", "elif", "exec", "command", "coproc", "!"}

# A runner runs the command that follows it, so the command is one token further
# right -- and its own flags move it further right again. ⛔ The flags that take
# a **separate** value are named per runner, for the measurement
# `schema.md § 19 -> The command position` states: a flag's value must never be
# read as the command.
#
# ⚠️ These are the shell's own runners rather than any project's tooling, by the
# boundary rule this file's docstring cites. A project whose own paid command is
# spelled like one of them is still guarded, because every command position of a
# call is matched rather than the innermost one.
# ⚠️ **And a second number per runner, because some of them take an argument of
# their own before the command**: a duration, a lock file, a priority. Measured
# by review, each reproduced: the runner's own first argument stood where the
# command should be, and the command behind it was invisible. One record per
# runner — the flags whose value is a separate word, and how many plain words of
# its own stand before the command it runs.
WRAPPERS = {
    "sudo": ({"-u", "--user", "-g", "--group", "-p", "--prompt", "-h", "--host",
              "-U", "--other-user", "-r", "--role", "-t", "--type", "-C",
              "--close-from", "-D", "--chdir", "-R", "--chroot", "-T",
              "--command-timeout", "-a", "--auth-type", "-c", "--login-class"}, 0),
    "doas": ({"-u", "-C"}, 0),
    # ⚠️ Zero rather than one for the two that take a user: the user arrives as
    # the value of a flag in the form that then runs a command as its own words,
    # and the form that takes the user as a plain word runs its command as a
    # quoted string instead — which is the interpreter residue § 19 states.
    "runuser": ({"-u", "--user", "-g", "--group", "-G", "--supp-group", "-s",
                 "--shell", "-c", "--command"}, 0),
    "su": ({"-s", "--shell", "-g", "--group", "-G", "--supp-group", "-c", "--command"}, 0),
    "env": ({"-u", "--unset", "-C", "--chdir", "-S", "--split-string"}, 0),
    "time": ({"-f", "--format", "-o", "--output"}, 0),
    "timeout": ({"-k", "--kill-after", "-s", "--signal"}, 1),
    "nice": ({"-n", "--adjustment"}, 0),
    "ionice": ({"-c", "--class", "-n", "--classdata", "-p", "--pid"}, 0),
    "chrt": ({"-p", "--pid"}, 1),
    "stdbuf": ({"-i", "--input", "-o", "--output", "-e", "--error"}, 0),
    "flock": ({"-w", "--wait", "--timeout", "-E", "--conflict-exit-code",
               "-c", "--command"}, 1),
    "xargs": ({"-I", "-i", "--replace", "-L", "-l", "--max-lines", "-n", "--max-args",
               "-P", "--max-procs", "-s", "--max-chars", "-E", "-e", "--eof",
               "-d", "--delimiter", "-a", "--arg-file"}, 0),
    "setsid": (set(), 0),
    "nohup": (set(), 0),
}

# A flag whose **value** is a command, wherever it stands in a call. ⛔ The
# utilities that run a command once per input take it this way rather than as
# their own argument, so the command behind one is reached by reading the flag
# and not by reading the utility's name — which is also why no utility name is
# needed here. Measured by review: a search running the paid command per match
# was invisible.
COMMAND_FLAGS = {"-exec", "-execdir", "-ok", "-okdir", "-c", "--command"}

# How much of a segment a report quotes.
SHOWN = 160


def _lexer(command: str) -> shlex.shlex:
    """The lexer `words` reads a call with, built in one place.

    ⛔ One construction, because every setting on it is a measurement -- each is
    stated beside `words` below -- and a second copy of them would be a second
    reading of the shell, free to disagree with the first about where a command
    is. `readable` asks the same lexer whether it could read a call at all.
    """
    lexer = shlex.shlex(command, posix=True, punctuation_chars="();<>|&\n")
    lexer.whitespace_split = True
    lexer.whitespace = " \t\r"
    lexer.commenters = ""
    return lexer


def readable(command: str) -> bool:
    """Whether this call is one the lexer could read, rather than fall back on.

    ⛔ Answered here rather than inferred from `words`, whose fallback returns
    tokens either way: a caller comparing the two lists would be reimplementing
    this question, and the fallback is deliberately not distinguishable by its
    output. What reads it is the sibling guard whose verdict turns on it -- a call
    nothing can parse has no reliable command positions in it, which
    `schema.md § 20 -> The four ways it fails closed` makes one of the four.

    ⚠️ It says nothing about whether the *shell* would run the call. A quote
    nobody closed is unreadable to both; a construct this lexer reads and the
    shell rejects, or the reverse, is a difference neither this nor `words` can
    report, and the fallback is what keeps such a call guarded rather than
    waved through.
    """
    try:
        list(_lexer(command))
    except ValueError:
        return False
    return True


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
    try:
        return list(_lexer(command))
    except ValueError:
        # A call this lexer cannot read is a call the shell cannot read either,
        # and the fallback reads the words between the separators rather than
        # answering nothing at all: a quote nobody closed must not be the way
        # past a guard.
        return [w for w in re.split(r"([;&|()\n{}])", command) for w in w.split() if w]


def nested(command: str) -> tuple[str, list[str]]:
    """The call with every substitution taken out, and each one's own text.

    ⛔ A substitution runs a command, so its body is a command text of its own —
    and the lexer cannot see into one, because inside double quotes the whole
    substitution is a single token. Measured by review: `OUT="$(<the paid
    command>)"` reached the shell unasked, which is the ordinary way to capture
    output, and a backtick pair was invisible quoted or not.

    ⚠️ Single quotes are tracked and nothing inside them is a substitution, which
    is the shell's own rule: a path mentioned inside `'…'` is text.

    ⚠️ The body is **replaced by a space** in the text that comes back, so each
    command text is segmented exactly once and one spend is reported once.
    """
    out: list[str] = []
    bodies: list[str] = []
    index, end, quoted = 0, len(command), False
    while index < end:
        char = command[index]
        if char == "'":
            quoted = not quoted
            out.append(char)
            index += 1
            continue
        if quoted:
            out.append(char)
            index += 1
            continue
        if char == "\\" and index + 1 < end:
            out.append(command[index:index + 2])
            index += 2
            continue
        # `$(…)` and the process-substitution forms, which differ only in what
        # the shell does with the body's output.
        if char in "$<>" and command[index + 1:index + 2] == "(":
            depth, scan = 0, index + 1
            while scan < end:
                if command[scan] == "(":
                    depth += 1
                elif command[scan] == ")":
                    depth -= 1
                    if depth == 0:
                        break
                scan += 1
            bodies.append(command[index + 2:scan])
            out.append(" ")
            index = scan + 1
            continue
        if char == "`":
            scan = command.find("`", index + 1)
            if scan == -1:
                out.append(char)
                index += 1
                continue
            bodies.append(command[index + 1:scan])
            out.append(" ")
            index = scan + 1
            continue
        out.append(char)
        index += 1
    return "".join(out), bodies


def calls(command: str) -> list[str]:
    """Every command text this call runs: itself, and each one nested in it."""
    outer, bodies = nested(CONTINUATION.sub(" ", command))
    found = [outer]
    for body in bodies:
        found.extend(calls(body))
    return found


def _segments_of(call: str) -> list[list[str]]:
    """One command text's own commands, each as its own list of words.

    Separators end a segment; a redirection and its target are dropped, for the
    reason stated beside `REDIRECTIONS`; a here-document's whole body is dropped,
    for the reason stated beside `HEREDOC`.
    """
    out: list[list[str]] = [[]]
    tokens = words(call)
    index = 0
    while index < len(tokens):
        token = tokens[index]
        index += 1
        if token.startswith(HEREDOC) and set(token) <= set("<-"):
            # The delimiter, then everything up to the line that repeats it. ⚠️ A
            # body nothing terminates runs to the end of the call, which is what
            # the shell does with it too.
            delimiter = tokens[index].lstrip("-") if index < len(tokens) else None
            index += 1
            while index < len(tokens) and tokens[index] != delimiter:
                index += 1
            index += 1
            continue
        if token and set(token) <= REDIRECTIONS and (set(token) & set("<>")):
            index += 1
            continue
        if token in GROUPING or (token and set(token) <= SEPARATORS):
            out.append([])
            continue
        out[-1].append(token)
    return out


def segments(command: str) -> list[list[str]]:
    """Every command of the call and of everything nested in it.

    An empty segment is kept out, so a trailing separator is not a command that
    spends nothing.
    """
    out: list[list[str]] = []
    for call in calls(command):
        out.extend(_segments_of(call))
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
        if ASSIGNMENT.match(token) or token == "--":
            # An assignment stands before a command, and `--` is never one.
            index += 1
            continue
        # ⛔ The arguments are every word after the position, assignments
        # included: a leading `NAME=value` stands *before* a command and is
        # stripped by the branch above, while one standing after it is an
        # argument like any other. Filtering them here hid exactly the call a
        # project distinguishes by a `KEY=value` argument, which is an
        # `args_match` that silently matches nothing — the direction this facet
        # cannot fail in. Found by reading the diff.
        out.append((token, list(segment[index + 1:])))
        if token in INTRODUCERS:
            # It is a position, so a command spelled like one of these words is
            # still matched — and the scan continues, because what follows it is
            # a command rather than its arguments.
            index += 1
            continue
        runner = WRAPPERS.get(os.path.basename(token))
        if runner is None:
            # ⛔ Not a runner, so this is the command — and the scan stops here
            # rather than reading further words, which is the whole positional
            # rule. What is still read is a flag whose value is a command: the
            # one way a command stands behind something that is not a runner.
            for at in range(index + 1, len(segment) - 1):
                if segment[at] in COMMAND_FLAGS:
                    out.append((segment[at + 1], list(segment[at + 2:])))
            return out
        flags, positionals = runner
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
                flag, equals, value = word.partition("=")
                index += 1
                if flag in COMMAND_FLAGS:
                    # ⛔ Its value is a command rather than a setting, so it is a
                    # position: the runners that take one this way would
                    # otherwise have their command read as a flag's value and
                    # skipped. ⚠️ Where that value is a multi-word string the
                    # shell splits, only its first word stands here, which is the
                    # interpreter residue § 19 states.
                    if equals:
                        out.append((value, []))
                    elif index < len(segment):
                        out.append((segment[index], list(segment[index + 1:])))
                        index += 1
                    continue
                if not equals and flag in flags and index < len(segment):
                    index += 1
                continue
            break
        # The runner's own words, before the command it runs.
        index += min(positionals, max(0, len(segment) - index))
    return out


def names_the_command(called: str, configured: str) -> bool:
    """Whether a token in a command position is the command an entry names.

    The comparison is `schema.md § 19`'s `command` bullet and is not restated
    here. ⚠️ What is local to this function is the limit: the comparison is
    lexical, so a path reached through a symlink or spelled in another case is
    not this one -- stated in `docs/single-source-of-truth.md` § The spend half
    rather than resolved, a hook that stats the filesystem on every call of
    every session being the costlier of the two answers.
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
                        # Refused at load by the shared reader (§ 19), so this is
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
        # project — the edit that repairs the configuration included (§ 19).
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
        # An unset bar prices no resume, and then this arm says nothing (§ 19).
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
    # ⛔ The arm each event has to call, and not merely this file's name: the two
    # arms answer different events, so a carrier naming the script with the other
    # arm's argument — or with none, which prints usage and answers nothing —
    # leaves both events wired and both dead. Measured by review, where swapping
    # them left this check green.
    for event, arm in ((GUARD_EVENT, "guard"), (PRICE_EVENT, "price")):
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
        if arm not in named.split():
            problems.append(
                f"{CARRIER.name} calls {mine} on {event} without the `{arm}` arm, so that "
                f"event is wired to an answer it is not the event for."
            )
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


def _plant_in_alternation(text: str, added: str, drop: str | None = None) -> str:
    """The surface's own approval line, widened by a value or missing one.

    ⛔ Found by the key the reader walks rather than by the words beside it, so a
    reworded comment moves the plant instead of silencing it. Raises where the
    line is gone, which is the no-op this file's other plants are held to.
    """
    for line in text.splitlines():
        head, _, rest = line.partition(":")
        if head.strip() != APPROVAL.rpartition(".")[2] or "|" not in rest:
            continue
        value, _, comment = rest.partition("#")
        values = [v.strip() for v in value.split("|")]
        if drop is not None:
            values = [v for v in values if v != drop]
        replaced = f"{head}: {' | '.join(values)}{added}"
        if comment:
            replaced += f"   # {comment.strip()}"
        return text.replace(line, replaced, 1)
    raise AssertionError(f"no line of the surface declares `{APPROVAL}` as an alternation")


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
    # ⛔ The two arms swapped, and the arm dropped: a carrier in either state
    # names this script on both events and answers nothing on either.
    ("a carrier calling each arm on the other's event",
     lambda text: text.replace('"guard"', '"a-placeholder"').replace(
         '"price"', '"guard"').replace('"a-placeholder"', '"price"')),
    ("a carrier naming no arm at all",
     lambda text: text.replace(', "guard"', "").replace(', "price"', "")),
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
    ("inside a substitution the shell expands in quotes",
     'a-free-command "$(<deny> --the-paid-tier)"'),
    ("as the value of an assignment, substituted", 'AN_OUTPUT=$(<deny> --the-paid-tier)'),
    ("as the value of an assignment, substituted and quoted",
     'AN_OUTPUT="$(<deny> --the-paid-tier)"'),
    ("inside the older substitution spelling", "a-free-command `<deny> --the-paid-tier`"),
    ("inside a process substitution", "a-diffing-command <(<deny> --the-paid-tier) a-file"),
    ("inside a brace group", "{ <deny> --the-paid-tier; }"),
    ("as the body of a condition", "if a-free-command; then <deny> --the-paid-tier; fi"),
    ("as the body of a loop", "for i in a b; do <deny> --the-paid-tier; done"),
    ("as the alternative of a condition",
     "if a-free-command; then a-free-command; else <deny>; fi"),
    ("behind the word that replaces the shell", "exec <deny> --the-paid-tier"),
    ("behind a negation", "! <deny> --the-paid-tier"),
    ("as the command a search runs per match",
     "a-searching-command . -name a-file -exec <deny> --the-paid-tier {} ;"),
    ("across a line continuation, which is not a separator",
     "<deny> \\\n  --the-paid-tier"),
    ("after a word carrying a fragment, which is not a comment",
     "a-free-command --url=https://a-host/a-path#a-fragment ; <deny> --the-paid-tier"),
    ("with its output redirected", "<deny> --the-paid-tier > a-file"),
    ("with an argument quoted", "<deny> --the-paid-tier \"a value; with a separator\""),
]

# One real call shape per runner the table names, written out rather than
# generated from it — see the loop that reads this for why that is the point.
# Each shape is the way that runner is actually invoked, its own arguments
# included.
RUNNER_SHAPES = [
    ("sudo", "sudo -u a-user <deny> --the-paid-tier"),
    ("doas", "doas -u a-user <deny> --the-paid-tier"),
    ("runuser", "runuser -u a-user <deny> --the-paid-tier"),
    ("su", "su -s a-shell -c <deny>"),
    ("env", "env A_VARIABLE=a-value <deny> --the-paid-tier"),
    ("time", "time -p <deny> --the-paid-tier"),
    ("timeout", "timeout -k 5 30 <deny> --the-paid-tier"),
    ("nice", "nice -n 10 <deny> --the-paid-tier"),
    ("ionice", "ionice -c 3 <deny> --the-paid-tier"),
    ("chrt", "chrt -f 10 <deny> --the-paid-tier"),
    ("stdbuf", "stdbuf -o L <deny> --the-paid-tier"),
    ("flock", "flock -w 5 a-lock-file <deny> --the-paid-tier"),
    ("xargs", "xargs -I a-token <deny> --the-paid-tier"),
    ("setsid", "setsid <deny> --the-paid-tier"),
    ("nohup", "nohup <deny> --the-paid-tier"),
]

MUST_ALLOW = [
    ("the denied path inside the prose of another command",
     "a-text-editing-command 'the note mentions <deny> in passing'"),
    ("the denied path as the argument of a reading command", "a-reading-command <deny>"),
    ("the denied path as a redirection's target", "a-free-command > <deny>"),
    ("the denied path as the value of a flag", "a-free-command --input <deny>"),
    ("a command whose name merely ends in the denied one", "a-prefix-<deny> --the-paid-tier"),
    ("a command of the same base name in another place", "another-place/<base> --the-paid-tier"),
    # ⚠️ The denied path is in this one on purpose, in an argument position of
    # each segment: a chain of commands that merely *could* not match asserts
    # nothing about the position rule, which is what the chain is read for here.
    ("a chain of free commands reading the denied path",
     "a-free-command --input <deny> && another-free-command <deny>"),
    # ⛔ The false-refusal shapes found by review, each reproduced before it was
    # fixed: a document that quotes the command, a placeholder that is not a
    # group, a continuation that is not a separator, and a path inside single
    # quotes, where the shell itself expands nothing.
    ("a here-document whose body quotes the command",
     "a-writing-command <<'A_DELIMITER' > a-file\n<deny> --the-paid-tier is the paid step\n"
     "A_DELIMITER"),
    ("the same body under the dash form of the delimiter",
     "a-writing-command <<-A_DELIMITER\n<deny> --the-paid-tier\nA_DELIMITER"),
    ("a placeholder standing before the denied path",
     "a-searching-command . -name a-file -exec a-copying-command {} <deny> ;"),
    ("the denied path as an argument across a line continuation",
     "a-reading-command \\\n    <deny>"),
    ("the denied path inside single quotes", "a-printing-command '<deny> --the-paid-tier'"),
    ("the denied path as a word of a loop's own list", "for f in <deny>; do a-free-command; done"),
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

    # ⛔ The tables themselves, which are a surface nothing else holds: a
    # mistyped runner, a flag written without its dash or a shape whose first
    # word is not the runner it names matches nothing the parse ever produces,
    # and every assertion below it stays green — the other shapes do not contain
    # the broken entry. A plant on the mechanism says nothing about whether each
    # row of its data is live.
    out.append("The tables this parse reads are well-formed, row by row:")
    bad = [name for name in WRAPPERS
           if not name or name != os.path.basename(name) or not name.isalpha()
           or name != name.lower()]
    check("every runner is a bare lowercase name", not bad, f"{bad}")
    bad = [f"{name}:{flag}" for name, (flags, _n) in WRAPPERS.items() for flag in flags
           if not flag.startswith("-") or len(flag.split()) != 1]
    check("every valued flag is one dashed word", not bad, f"{bad}")
    bad = [name for name, (_f, count) in WRAPPERS.items()
           if isinstance(count, bool) or not isinstance(count, int) or count < 0]
    check("every runner states how many words of its own stand first", not bad, f"{bad}")
    bad = [word for word in INTRODUCERS if not word or len(word.split()) != 1]
    check("every introducing word is one word", not bad, f"{bad}")
    bad = [flag for flag in COMMAND_FLAGS
           if not flag.startswith("-") or len(flag.split()) != 1]
    check("every command-valued flag is one dashed word", not bad, f"{bad}")
    bad = [shape for runner, shape in RUNNER_SHAPES
           if shape.split()[0] != runner or shape.count("<deny>") != 1]
    check("every runner's shape opens with that runner and names the denied command once",
          not bad, f"{bad}")
    # ⛔ And carries no *other* runner's name, which is what catches the one
    # malformation the rules above let through: two entries written with the
    # comma between them missing are joined into one string by the language
    # itself, and the pair then asserts about one runner while the other's row
    # is gone. Measured on a sibling carrier's own word list.
    bad = [f"{runner}:{word}" for runner, shape in RUNNER_SHAPES for word in shape.split()
           if word in WRAPPERS and word != runner]
    check("and names no second runner, so no two rows were joined by a missing comma",
          not bad, f"{bad}")
    bad = [shape for _label, shape in MUST_REFUSE + MUST_ALLOW
           if "<deny>" not in shape and "<base>" not in shape]
    check("every planted shape carries the denied command", not bad, f"{bad}")

    out.append("")
    out.append("Every call shape a denied command arrives in is refused:")
    for label, shape in MUST_REFUSE:
        command = shape.replace("<deny>", paid)
        answered = guard_answer(_call(command), config=one)
        check(label, decision(answered) == "ask", f"{command[:60]!r} → {answered!r}"[:140])
    # ⛔ One plant per runner, written out rather than derived from the table.
    # ⚠️ This is a **deliberate** second statement of the table's own membership,
    # for the reason the reader's marker inventories are: a plant generated from
    # `WRAPPERS` asserts whatever `WRAPPERS` happens to say, so a runner missing
    # from the table is missing from its own plant too and the suite certifies
    # itself. Measured by review, which is how the runners below were found
    # absent. ⛔ And each shape carries the runner's own arguments, because a
    # runner that takes a duration or a lock file before its command is one a
    # bare `<runner> <command>` plant would pass without ever reaching it.
    for runner, shape in RUNNER_SHAPES:
        check(f"behind `{runner}`: {shape.replace('<deny>', '…')}",
              decision(guard_answer(_call(shape.replace("<deny>", paid)),
                                    config=one)) == "ask",
              repr(guard_answer(_call(shape.replace("<deny>", paid)), config=one))[:120])
    named = {runner for runner, _shape in RUNNER_SHAPES}
    check("every runner the table names has a shape of its own above",
          named >= set(WRAPPERS), f"missing: {sorted(set(WRAPPERS) - named)}")
    check("and every shape above names a runner the table carries",
          named <= set(WRAPPERS), f"unknown: {sorted(named - set(WRAPPERS))}")

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
    # ⚠️ Anchored at both ends on purpose: an unanchored pattern matches the
    # quoted token as a substring whether the quotes were removed or not, so the
    # assertion would pass against a lexer that kept them. Measured by review.
    check("and an argument's quotes are gone before the pattern reads it",
          decision(guard_answer(_call(f"{base} '--tier the-paid-one'"), config=_a_config(
              [_a_denial(base, args_match="^--tier the-paid-one$")]))) == "ask")
    # ⛔ The plant that reaches the redirection arm, and the only one that can:
    # a redirection is not a separator, so its target never stands in a command
    # position and the allow-direction shapes above pass with that arm dead. What
    # the arm decides is whether `> <path>` is read as an *argument* of the
    # command, and an anchored pattern is what tells the two apart.
    # ⛔ An argument that looks like an environment assignment is still an
    # argument. A leading `NAME=value` stands before a command and is stripped;
    # one standing after it is what some runners take their settings as, and
    # filtering it out of the arguments made an `args_match` naming one match
    # nothing at all — a denial that reads as configured and refuses no call.
    assigned = _a_config([_a_denial(base, args_match="A_SETTING=the-paid-one")])
    check("an argument spelled like an assignment is matched as an argument",
          decision(guard_answer(_call(f"{base} A_SETTING=the-paid-one"),
                                config=assigned)) == "ask",
          repr(guard_answer(_call(f"{base} A_SETTING=the-paid-one"), config=assigned))[:140])
    check("and the same spelling before the command is still stripped, not matched",
          guard_answer(_call(f"A_SETTING=the-paid-one {base}"), config=assigned) == {},
          repr(guard_answer(_call(f"A_SETTING=the-paid-one {base}"), config=assigned))[:140])

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
    # ⛔ A redirection's target stands in no command position at all, read off
    # the positions rather than off a verdict: every allow-side shape above
    # passes with the redirection arm dead, so the direct reading is the only
    # thing that holds it. Measured by review.
    check("a redirection's target is in no command position",
          [token for token, _args in command_chain(segments("a-free-command > a-file")[0])]
          == ["a-free-command"],
          repr(segments("a-free-command > a-file"))[:120])
    check("and a here-document's body is in no segment at all",
          segments("a-writing-command <<'A_DELIMITER'\na-command-in-the-body\nA_DELIMITER")
          == [["a-writing-command"]],
          repr(segments("a-writing-command <<'A_DELIMITER'\na-command-in-the-body\n"
                        "A_DELIMITER"))[:160])

    out.append("")
    out.append("What the refusal says, which no verdict asserts by itself:")
    costly = _a_config([_a_denial(base, args_match="--the-paid-tier",
                                  reason="a-stated-cost-per-run")])
    asked = guard_answer(_call(f"a-free-command && {base} --the-paid-tier"), config=costly)
    check("the project's own cost reaches the person", "a-stated-cost-per-run" in reason(asked),
          reason(asked)[:200])
    check("the rule it is refused under is cited", PRICE_CITATION in reason(asked),
          reason(asked)[:200])
    check("and the ask says what unblocks it", "unblocks" in reason(asked),
          reason(asked)[:200])
    # ⛔ Every other fact the refusal is supposed to carry, read out of the
    # message rather than out of the record behind it: a report branch produces
    # no verdict, so a red/green suite is blind to it unless a phrase is
    # asserted. § 19 states that the refusal names the segment that matched —
    # which, before this, was asserted only against the internal record.
    check("the segment that spends is named by number", "segment 2" in reason(asked),
          reason(asked)[:200])
    check("the entry's own command is named", base in reason(asked), reason(asked)[:200])
    check("and the argument pattern that narrowed it", "--the-paid-tier" in reason(asked),
          reason(asked)[:200])
    check("the answer is keyed to the event the harness asked on",
          asked.get("hookSpecificOutput", {}).get("hookEventName") == GUARD_EVENT,
          repr(asked)[:160])
    bare_entry = guard_answer(_call(base), config=_a_config([_a_denial(base)]))
    check("and an entry with no pattern says nothing about one",
          "whose arguments carry" not in reason(bare_entry), reason(bare_entry)[:200])
    refused = guard_answer(_call(base), config=_a_config(
        [_a_denial(base, reason="a-stated-cost-per-run")], approval="denied"))
    check("the stricter approval refuses rather than asks", decision(refused) == "deny",
          repr(refused)[:140])
    check("and its remedy is a person outside the loop, not an answer inside it",
          "themselves" in reason(refused), reason(refused)[:160])
    check("an approval this carrier cannot read refuses rather than asking",
          decision(guard_answer(_call(base), config=_a_config(
              [_a_denial(base)], approval="something-else"))) == "deny")
    # ⛔ A pattern that cannot be compiled matches no call, and this is the arm
    # that decides what it does instead. The shared reader refuses such an entry
    # at load, so nothing reaches this through a validated configuration — but a
    # guard that refused every call of the command would be refusing on a
    # configuration defect, which is the answer this asserts.
    check("a pattern that does not compile refuses nothing rather than everything",
          guard_answer(_call(f"{base} --the-paid-tier"), config=_a_config(
              [_a_denial(base, args_match="--the-paid-tier(")])) == {})

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
    check("a figure the harness states for a forked session is priced too",
          bool(price_answer(_resume(figure=2.5, source="fork"),
                            config=priced).get("systemMessage")))
    check("and a forked session it priced nowhere is reported as no figure",
          "no figure" in str(price_answer(_resume(figure=None, source="fork"),
                                          config=priced).get("systemMessage")).lower())
    # ⚠️ Both arms of the cache clause, because one phrase contains the other:
    # *not expired* carries *expired*, so an assertion reading the shorter word
    # cannot tell the two reports apart. Measured by review.
    expired = str(price_answer(_resume(figure=2.5, expired=True),
                               config=priced).get("systemMessage"))
    fresh = str(price_answer(_resume(figure=2.5, expired=False),
                             config=priced).get("systemMessage"))
    check("the cache's own state is reported where the harness states it",
          "likely expired" in expired and "likely not expired" not in expired,
          expired[:160])
    check("and the other way where it states the opposite",
          "likely not expired" in fresh, fresh[:160])
    check("a resume the harness said nothing about the cache for says nothing about it",
          "prompt cache had" not in str(price_answer(_resume(figure=2.5),
                                                     config=priced).get("systemMessage")))
    # ⛔ The payload that reaches the event gate: one the arm would otherwise
    # answer. A payload carrying no figure and no priced source exits at a later
    # gate, so it passes with this one dead. Measured by review.
    check("and the price arm answers nothing on another event",
          price_answer({"hook_event_name": "Stop", "cwd": ".", "source": "resume",
                        FIGURE: 99.0}, config=priced) == {})
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
        # ⛔ The predicate first, because both silences below are reachable by
        # another route: a project that states nothing also fails to *load*, so
        # an arm whose configuration gate was gone would still answer nothing.
        # What makes these two assertions about § 7's rule is that the question
        # was asked and answered no. Measured by review.
        check("the shared reader says this project states none",
              states_a_configuration(bare) is False)
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
        # ⛔ The decision this example's own `approval` resolves to, and not
        # merely *a* decision: an arm accepting either would pass a project that
        # wrote the stricter value and got the ask.
        wanted = DECISIONS.get(str(loaded.get(APPROVAL)))
        check(f"{name}: its own denied call is held, as `{loaded.get(APPROVAL)}` states",
              wanted is not None and decision(answered) == wanted,
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
    # ⛔ Each comparison arm separately, because the plant above reddens only the
    # unreadable-surface arm: a surface that grew a third value and a surface
    # that dropped one are the two drifts this check exists for, and neither was
    # asserted. Measured by review. ⚠️ The surface's own line is mutated rather
    # than a copy of it being written here, so a reworded line moves the plant.
    widened = _plant_in_alternation(text, " | a-third-value")
    check("and reddens on a value the surface states and this carrier decides nothing for",
          widened != text and bool(check_the_decisions_are_the_surfaces(widened)))
    narrowed = _plant_in_alternation(text, "", drop="denied")
    check("and reddens on a value this carrier decides for and the surface stopped stating",
          narrowed != text and bool(check_the_decisions_are_the_surfaces(narrowed)))

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
    # ⛔ And an answer it *can* read reaches the harness, which the two
    # assertions above cannot say: they assert silence, so both hooks could be
    # answering nothing at all with the suite green. Measured by review.
    printed = io.StringIO()
    hook(io.StringIO(json.dumps({**_call(f"{paid} --the-paid-tier"), "cwd": "."})),
         lambda payload: guard_answer(payload, config=one), printed)
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
