#!/usr/bin/env python3
"""The day log's evidence, measured once for every project.

Unions every trace of one working day into active-time blocks and prints the raw
evidence the day-log role describes the work from. ⛔ **It produces evidence and
never an entry**: what the two values are is § 9's, where they land is § 26's
port, and the role in `skills/day-report` is what reads one and asks the other.

This is the one copy. Five lived in five projects before it, 447 to 580 lines,
and what they agreed on is what is written here as procedure -- the day
boundary, the neutral-record pattern, the fifteen-minute bookkeeping cap -- while
every value they differed on is read from configuration and named below. ⛔ **No
project's name, path, chat, calendar or repository appears anywhere in this
file**, which is the property that makes it one copy rather than a sixth.

What comes from configuration, and the key each value is read from:

  day_log.day_start                  the hour a working day begins
  day_log.round_to                   the grid a reported figure sits on
  day_log.round_ties                 which way an exact tie goes
  day_log.enforce_grid               whether an off-grid entry fails the check
  day_log.streams                    which streams are read at all
  day_log.attribute_to               whose commits are the log owner's
  day_log.ritual_retired             this project's own retired command names
  day_log.evidence.chat.kind         what reads the chat stream, or `none`
  day_log.evidence.chat.path         the archive that kind reads
  day_log.evidence.chat.patterns     the chats that are this project's
  day_log.evidence.chat.exclude      the chats left out of those
  day_log.evidence.chat.mixed        the chats carrying something else as well
  day_log.evidence.calendars         the calendars a meeting may come from
  roots                              every repository this project is
  host.repo                          what the host-activity stream asks about
  day_log.destination.*              the store, reached through § 26's port

⛔ **The configuration is read through the shared reader and never parsed here.**
A script that read the file itself would be a second set of defaults, and two
sets drift apart with nothing noticing.

⛔ **The input is this project and nothing else.** Every stream is narrowed where
it is read and the bound is *derived*: the repositories are § 1's roots, the
session stores are the ones each root's own worktree list vouches for, the chats
are the configured patterns. An input that cannot be shown to belong here is
refused BY NAME under `SOURCES` -- never read, and never dropped in silence,
because an input that vanishes quietly is a low total nobody can see.

A working day is NOT a calendar day. It runs `day_start` → the same time next
morning, so a session carrying past midnight stays with the day it belongs to
instead of splitting across two entries. `--check` fails loudly if a block ever
straddles that boundary, which is the one way two entries can claim one minute.

  python3 day_log.py                            # today, this project
  python3 day_log.py --date 2026-10-28
  python3 day_log.py --meeting 14:00-14:30 --meeting 16:00-17:00
  python3 day_log.py --idle 20 --skip-session 0a1b68bf --skip-chat "A Name"
  python3 day_log.py --keep-ritual              # the total before the upkeep deduction
  python3 day_log.py --check                    # audit every recorded entry
  python3 day_log.py --month 2026-10            # sum a month's stated hours
  python3 day_log.py --self-test
"""

from __future__ import annotations

import argparse
import bisect
import datetime as dt
import functools
import glob
import json
import math
import os
import re
import shutil
import sqlite3
import subprocess
import sys

_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import config  # noqa: E402
import load  # noqa: E402
import port  # noqa: E402

# The port § 26 declares, named by the key carrying its kind. ⛔ Read from the
# surface through `port` rather than written as a string here: the name is the
# marker's and a second spelling would be free to disagree with it.
DESTINATION = "day_log.destination.kind"

# --------------------------------------------------------------------------------------------
# What is procedure, and is therefore here rather than in a project's configuration
# --------------------------------------------------------------------------------------------

# Minutes of silence that end an active block. Identical in all five surveyed
# copies, which is what makes it procedure: it is a property of how a person
# works at a keyboard, not of which project they are working on. ⚠️ `--idle`
# moves it for one run, for a day whose rhythm was plainly different.
IDLE = 15

# How long a bookkeeping turn is allowed to be. Past it the turn stops counting
# as ritual and its minutes count again. ⚠️ **This is the guard that keeps the
# deduction honest:** saving and reloading take minutes, so a turn that runs an
# hour is either real autonomous work or an empty room -- the first must be
# counted, and the second the idle cutoff already removes. Identical in all five.
RITUAL_CAP = dt.timedelta(minutes=15)

# The harness's own commands, plus the loop's two bookkeeping roles and this
# role itself. A turn opened by one of these is bookkeeping until the next thing
# is typed, and its minutes stop anchoring time.
#
# ⛔ **The loop's own roles are absent and must stay absent.** Filing, starting,
# gating, finishing and reviewing a work item are the work, not the upkeep
# around it (§ 9). The two bookkeeping roles -- keeping the session's books and
# restoring its context -- are the stated exception, and `day-report` is here
# because writing an entry is `log_upkeep` by name.
#
# ⛔ **Never widen this list to make a day smaller.** It is a closed list of
# commands that drive the tooling plus a closed list of farewells. A pattern
# catching one real instruction removes a working hour and nothing reports it.
BOOKKEEPING = [
    # The loop's two bookkeeping roles, and this one.
    "save", "load", "day-report",
    # The harness's own. ⚠️ `compact` and `usage-credits` were on no surveyed
    # copy's list and are in this project's own transcripts: a harness command
    # that drives the window or asks about spend produces nothing the log counts.
    "clear", "exit", "quit", "mcp", "model", "compact", "usage-credits",
]

# ⚠️ **A carrier's injected text is what the pattern matches, and it differs by
# carrier.** A command expands into a record carrying its own name in a
# `<command-name>` tag; a skill injects a `Base directory for this skill:`
# preamble instead. **Rename either and the deduction stops working silently** --
# the suite beside this file is what catches that.
#
# ⚠️ **Namespacing changes the string**, measured rather than anticipated: this
# project's own transcripts carry `/mjolnir:save` beside a bare `/start`, so the
# optional `<plugin>:` is not a precaution. A retired name stays matched for as
# long as it is still in history, which is what `day_log.ritual_retired` is for.
_NAMESPACE = r"(?:[A-Za-z0-9_.-]+:)?"

# ⛔ The tag has to **close** right after the name. `<command-message>commit the
# smtp fix</command-message>` is an instruction that happens to begin with a
# bookkeeping word, and a pattern ending at the word instead of at the tag
# unbills it -- measured on two of the five surveyed copies, which end at
# `[<\s]` and catch it.
_COMMAND = r"<command-(?:name|message)>\s*/?" + _NAMESPACE + r"(?:{names})\s*</command-"

# ⛔ Anchored at `/skills/<name>` and **not** at `/.claude/skills/<name>`. A
# plugin's skills sit at `<root>/plugins/<plugin>/skills/<name>`, so the stricter
# anchor -- which one surveyed copy carries -- silently stops matching the moment
# the role is installed as a plugin rather than copied into a project. Measured
# against this project's own transcripts, where every preamble is the plugin path.
_SKILL = r"^base directory for this skill: \S+/skills/(?:{names})(?![\w-])"

# A retired command's own injected body, which arrives as a user record opening
# with the command file's title.
_TITLE = r"^#\s*{title}(?![\w-])"

# The typed forms, which are nobody's command and nobody's skill: a bare
# instruction to save or reload, the question that follows one, and the sign-off
# a session actually ends on.
#
# ⛔ Each is anchored at the start and closed at the end. `save to txt` and
# `commit the fix` are work; `save` and `commit` alone are not.
TYPED = [
    # A bare reload, with only an orientation question allowed after it --
    # «load progress. do step 2» carries an instruction and is work.
    r"^load\s+prog\S*[\s.,!?]*(((let'?s\s+)?(resume|continue)|(what'?s|what\s+are\s+the)"
    r"\s+next(\s+(step|task)s?)?|next\s+(step|task)s?)[\s.,!?]*)?$",
    r"^(save|commit)(\s+(the\s+)?(all|only|progress|everything|it|git\s+only))?\s*[.!]?$",
    # The sign-off form. ⛔ The tail is a closed list: «save progress and fix the
    # failing test» has to stay work, so anything that is not a farewell or a
    # plain «we will …» about later ends the match and the turn is counted.
    r"^(save|commit)(\s+(the\s+)?(all|only|progress|everything|it|git\s+only))*"
    r"[\s.,!]*((bye|goodbye|good\s*night|see\s+you|until\s+next\s+time|thanks?|"
    r"thank\s+you|that'?s\s+(it|all)|(we|i)\s*(will|'ll)\s[^.!?]*)[\s.,!]*)+$",
    r"^(all\s+)?(saved|committed|pushed|progress\s+saved)\s*\??$",
    r"^(exit|quit|bye|buy|eit|xit|leave|pwd)\s*$",
    r"^did\s+you\s+(commit|save|push)\b",
    r"^did\s+you\s+(save|commit)\s+progress\?*\s*(bye|buy|thanks?)\s*[.!]?$",
]

# Records the harness injects on its own -- a background agent reporting back, a
# command's own output, a reminder. They are not typed, so they neither open a
# ritual turn nor close one; whatever turn is running keeps running.
NEUTRAL = re.compile(r"^<(local-command-|task-notification|system-reminder|bash-std)", re.I)

# A session's own transcripts, under the harness's store. ⛔ Derived and never
# configured: which directory the harness writes a session to is the harness's
# own fact, exactly as § 25 has the memory store derived -- a project that stated
# it would be stating something it does not decide.
#
# ⛔ **And derived by the sibling that already derives it**, rather than by a
# second reading here. `load.harness_dir` honours the harness's own relocation of
# that directory before falling back to the home directory § 14 states a role is
# handed; a copy spelled out here would be free to disagree with it, and the way
# it would disagree is by reading the real store while a session under a
# relocated one measured nothing and said the day was empty.
def store_root() -> str | None:
    """Where the harness keeps every project's transcripts, or `None`."""
    found = load.harness_dir()
    return str(found / load.SESSIONS_UNDER) if found is not None else None

# The sidecar a delegated sub-window writes, and the offloaded tool output beside
# it. ⚠️ **The sidecars are read**, and that is a decision rather than a detail:
# delegating exploration to a sub-window is the practice that keeps a session's
# context clean, so a run that read only the top-level transcripts would
# **under-measure the best-run sessions** -- the parent emits a tool call and then
# waits, and with nothing in the gap the idle cutoff splits a block that was
# never idle. Measured in this project's own store: 146 top-level transcripts
# against 159 sidecars.
SIDECARS = os.path.join("subagents", "agent-*.jsonl")

# ⛔ **And the offloaded tool results are deliberately excluded**, named here
# rather than left unmentioned. A `tool-results/<id>.txt` holds one tool's output
# as plain text with **no timestamp in it at all**, so it can anchor nothing; the
# call that produced it is already a record in the parent transcript, stamped at
# the moment it ran. Nothing is lost by not reading them, and `SOURCES` says so.
TOOL_RESULTS = "tool-results"

# The epsilon a tie is decided with. Float division puts an exact half-step at
# 7.5 reliably and a tenth-step nowhere near as reliably, so the comparison is
# given slack rather than trusted.
EPS = 1e-9


# --------------------------------------------------------------------------------------------
# The configuration, read once
# --------------------------------------------------------------------------------------------


class Unavailable(Exception):
    """Something configuration states this run cannot do, with the key named.

    ⛔ Raised rather than worked around, and never defaulted past. A stream with
    no source, a store with no address and a kind nothing implements are each a
    stated configuration, and a run that quietly measured without one would
    report a low total with nothing saying why.
    """


class Settings:
    """One project's day-log configuration, and the readings derived from it.

    ⛔ Every value here comes from the shared reader. The derivations -- the
    rounding function, the check's slack, the ritual patterns, the session stores
    -- are this script's, and each is derived from a configured value rather than
    carrying a constant of its own.
    """

    def __init__(self, configuration: config.Config) -> None:
        self.config = configuration
        self.skills_root = configuration.skills_root

        start = str(configuration.get("day_log.day_start"))
        self.day_start = dt.time.fromisoformat(start)
        self.round_to = float(configuration.get("day_log.round_to"))
        self.round_ties = configuration.get("day_log.round_ties")
        self.enforce_grid = bool(configuration.get("day_log.enforce_grid"))
        self.streams = list(configuration.get("day_log.streams") or [])
        self.attribute_to = configuration.get("day_log.attribute_to")

        self.chat_kind = configuration.get("day_log.evidence.chat.kind")
        self.chat_path = configuration.get("day_log.evidence.chat.path")
        self.chat_patterns = list(configuration.get("day_log.evidence.chat.patterns") or [])
        self.chat_exclude = list(configuration.get("day_log.evidence.chat.exclude") or [])
        self.chat_mixed = list(configuration.get("day_log.evidence.chat.mixed") or [])
        self.calendars = list(configuration.get("day_log.evidence.calendars") or [])

        # Every repository this project is, with the host repository each one
        # answers to. ⛔ All of § 1's roots and never `code_root` alone: one
        # surveyed project is two repositories, and a run reading the first would
        # drop the second's commits with nothing saying so.
        views = configuration.views or {}
        self.roots = [
            (name, view.code_root, view.get("host.repo"))
            for name, view in (views.items() or [("code", configuration)])
        ]

        # ⛔ The grid and the check's slack, derived from one configured figure.
        # The surveyed copies carried four mutually incompatible forms of this --
        # a step with a tolerance derived from it, a bare slack constant, a step
        # with its own tolerance, and no constant at all -- which is four answers
        # to one question. Half a step is the most the rounding itself can move a
        # faithful entry, either way, so that is exactly what the check allows.
        self.slack = self.round_to / 2 + EPS

        self.ritual = _patterns(configuration.get("day_log.ritual_retired") or [])
        # The chat reader, built once. See `chat_reader` for why it is held.
        self._chat = None

    # --- what each stream is, and whether it is read at all -------------------

    def reads(self, stream: str) -> bool:
        return stream in self.streams

    @property
    def chat_available(self) -> bool:
        """Whether the chat stream has a source to read.

        ⛔ The two halves have to agree and the reader already refuses a
        disagreement, so this is one question rather than two: `chat` in
        `streams` under `kind: none` is refused at the configuration, never met
        here as a stream with nothing behind it.
        """
        return self.reads("chat") and self.chat_kind not in (None, "none")

    def chat_reader(self):
        """The implementation that reads this project's chat archive.

        ⛔ A kind the surface allows and this script has not built is a refusal
        naming the kind, not an empty stream -- § 3's rule for a configured kind
        with no implementation, read one axis over. An empty stream would report
        a low total with nothing saying why.

        ⛔ **One instance per configuration, held here.** The reader memoises what
        its patterns resolve to, and a fresh instance per day defeats that -- so
        `--check`, which asks about a day at a time, would resolve the chat list
        once per day in the range.
        """
        if self._chat is not None:
            return self._chat
        self._chat = self._chat_class()(self)
        return self._chat

    def _chat_class(self):
        reader = CHAT_KINDS.get(self.chat_kind)
        if reader is None:
            raise Unavailable(
                f"`day_log.evidence.chat.kind` is {self.chat_kind!r}, which this "
                "script has no reader for, so the `chat` stream cannot be read. "
                "That is an implementation this toolkit has not built, never a "
                "project with no chat evidence -- which is `none` (§ 9)."
            )
        if not self.chat_path:
            raise Unavailable(
                "`day_log.evidence.chat.path` is not set, so the `chat` stream "
                f"has no archive to read under `kind: {self.chat_kind}` (§ 9)."
            )
        return reader

    # --- the day, and the grid -----------------------------------------------

    def window(self, day: dt.date) -> tuple[dt.datetime, dt.datetime]:
        """The half-open [start, end) span of the working day named by `day`."""
        start = dt.datetime.combine(day, self.day_start).replace(tzinfo=LOCAL)
        return start, start + dt.timedelta(days=1)

    def current_day(self) -> dt.date:
        """The working day in progress, which before `day_start` is yesterday.

        ⛔ The default `--date` and never `date.today()`. Three of the five
        surveyed copies defaulted to the calendar date, so a report written at
        01:00 -- which is when a day whose work ran late is written -- opened on
        a day with four minutes in it and the evening's hours read as
        unreported.
        """
        now = dt.datetime.now(LOCAL)
        return now.date() - dt.timedelta(days=1) if now.time() < self.day_start else now.date()

    def on_grid(self, stated: float) -> bool:
        """Whether a stated figure sits on the configured grid."""
        return abs(stated / self.round_to - round(stated / self.round_to)) <= EPS * 10

    def report_hours(self, total: dt.timedelta) -> float:
        """The figure the entry states: measured hours at `round_to` resolution.

        ⚠️ Rounding happens **once**, on what is left after the role's own
        exclusions -- never on the measured total on its way there, and never a
        second time after a drop. ⚠️ A day with any counted activity never states
        zero: the smallest entry a log holds is one grid step, because a blank
        means a day off.
        """
        hours = total.total_seconds() / 3600
        if hours <= 0:
            return 0.0
        steps = hours / self.round_to
        # Down is the default and the direction every other rule here cuts: an
        # exact tie is no reason to state more than was measured.
        if self.round_ties == "up":
            landed = math.floor(steps + 0.5 + EPS)
        else:
            landed = math.ceil(steps - 0.5 - EPS)
        return max(landed, 1) * self.round_to


def _patterns(retired: list) -> list[re.Pattern]:
    """Every ritual pattern, with this project's retired names folded in.

    ⛔ The configuration supplies **names**, never expressions. A key taking a
    regular expression would let a project widen the list into real work, which
    is the one direction § 9 forbids outright -- so the anchoring is this
    script's and only the name is the project's.
    """
    names = list(BOOKKEEPING)
    titles = []
    for entry in retired:
        if isinstance(entry, dict):
            command, title = entry.get("command"), entry.get("title")
        else:
            command, title = entry, None
        if command:
            names.append(str(command))
        if title:
            titles.append(str(title))
    alternation = "|".join(re.escape(name) for name in names)
    out = [
        re.compile(_COMMAND.format(names=alternation), re.I),
        re.compile(_SKILL.format(names=alternation), re.I),
    ]
    out += [re.compile(_TITLE.format(title=re.escape(title)), re.I) for title in titles]
    out += [re.compile(expression, re.I) for expression in TYPED]
    return out


LOCAL = dt.datetime.now().astimezone().tzinfo


def is_ritual(text: str, patterns: list[re.Pattern]) -> bool:
    return any(pattern.search(text.strip()) for pattern in patterns)


# --------------------------------------------------------------------------------------------
# The sessions stream
# --------------------------------------------------------------------------------------------


def dirkey(path: str) -> str:
    """The comparable shape of a working copy and of its session store.

    The harness names a store after the working directory with every
    non-alphanumeric run replaced by a dash, so compare on that shape rather
    than trying to reproduce its exact escaping rules.
    """
    return re.sub(r"[^A-Za-z0-9]+", "-", path).strip("-").lower()


def store_of(workdir: str) -> str:
    """Where the harness keeps the transcripts of sessions run in `workdir`.

    ⛔ A stop where the store cannot be located at all, never a path joined onto
    nothing: a run that measured no sessions because it looked in a directory
    named after a missing variable reports a low total and no reason.
    """
    root = store_root()
    if root is None:
        raise Unavailable(
            "neither the harness's own configuration directory nor the home "
            "directory this role is handed resolves, so where the session "
            "transcripts are kept cannot be established and the `sessions` "
            "stream could not be read at all (§ 14)."
        )
    return os.path.join(root, re.sub(r"[^A-Za-z0-9]", "-", workdir))


def git(root: str, *arguments: str) -> str:
    out = subprocess.run(["git", "-C", root, *arguments], capture_output=True, text=True)
    return out.stdout


def _unresolving(root: str) -> list[tuple[str, str]]:
    """The `(real, as given)` pairs this project's own root reveals.

    Every ancestor of the configured root that is reached through a link, most
    specific first. ⚠️ Derived from the root rather than guessed at: the one
    substitution that matters is whichever link the project's own path crosses,
    and nothing else here has to know that such a link exists.
    """
    pairs, here = [], os.path.abspath(root)
    while True:
        real = os.path.realpath(here)
        if real != here:
            pairs.append((real, here))
        parent = os.path.dirname(here)
        if parent == here:
            break
        here = parent
    return pairs


@functools.lru_cache(maxsize=None)
def working_copies(root: str) -> frozenset:
    """Every live checkout of one repository -- the main one and its worktrees.

    ⛔ **Each one in every spelling the project's own root reveals**, because git
    reports a worktree by its **resolved** path while the harness names a store
    after the working directory **as the session saw it**. On any machine whose
    checkouts sit under a symlinked ancestor the two never meet, and then a
    worktree's whole store is refused as another project's -- which is the
    failure direction that loses real minutes, and whose only tell is the
    refusal line nobody reads.

    ⚠️ Measured: a checkout under `/var`, which resolves to `/private/var`, has
    its worktree's transcripts dropped while the main checkout's are kept.
    `realpath` alone does not close it -- it resolves the one direction git has
    already resolved -- so what closes it is the substitution read back off the
    root.
    """
    listed = git(root, "worktree", "list", "--porcelain")
    paths = {root} | {
        line[9:] for line in listed.splitlines() if line.startswith("worktree ")
    }
    out = set(paths) | {os.path.realpath(path) for path in paths}
    for real, given in _unresolving(root):
        for path in list(out):
            if path == real or path.startswith(real + os.sep):
                out.add(given + path[len(real):])
    return frozenset(out)


def sift(candidates: list[str], working: frozenset) -> tuple[list[str], list[str]]:
    """`(kept, refused)` stores, judged against the repository's own checkouts.

    ⛔ **A store whose name merely starts with this project's is not evidence of
    this project's work.** A sibling checkout one directory over globs straight
    in and its hours are counted here, with nothing in the output to show they
    were never this project's. Git's worktree list is the only thing that knows
    which checkouts of a repository exist, so a candidate is kept only when it
    is one of them.

    ⚠️ **A refusal pulls the total the other way too**, and the two are not told
    apart here: a worktree removed since its work leaves a store nothing vouches
    for, and those minutes are real and go missing. Both are named under
    `SOURCES` for exactly that reason.
    """
    allowed = {dirkey(path) for path in working}
    kept = [c for c in candidates if dirkey(os.path.basename(c)) in allowed]
    refused = [c for c in candidates if c not in kept]
    return kept, refused


@functools.lru_cache(maxsize=None)
def session_stores(roots: tuple) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Every session store this project may read, and the ones it refused.

    ⛔ **The candidates are globbed from every working copy and not from the
    configured root alone.** A worktree is not always *under* the root it belongs
    to -- `tree_dir` routinely puts trees beside it, or somewhere else entirely --
    so a glob anchored on the root sees a sibling tree's store only when the
    naming happens to make it a prefix, and never sees one cut elsewhere. Those
    minutes then go missing with nothing in the report to show it, which is the
    failure direction `sift`'s own refusal line exists to make visible and this
    one slips past. ⚠️ Measured: run with the root pointed at a worktree, the
    main checkout's whole store was outside the glob and the day read as empty.

    ⚠️ **The prefix glob is still what finds a tree the list no longer carries** --
    a worktree removed since its work -- which is why it is a glob per working
    copy rather than an exact path per working copy. That is the arm that reports
    missing minutes rather than hiding them.

    Cached: `--check` walks every recorded day and the answer cannot change
    within one run.
    """
    kept: list[str] = []
    refused: list[str] = []
    for root in roots:
        working = working_copies(root)
        candidates = sorted({
            path
            for place in working
            for path in glob.glob(store_of(place) + "*")
            if os.path.isdir(path)
        })
        mine, theirs = sift(candidates, working)
        kept += mine
        refused += theirs
    # A store one root refuses may be another root's own -- the two-repository
    # case, where the second repository sits inside the first. Refusals are
    # therefore resolved against everything kept, and never per root.
    kept = list(dict.fromkeys(kept))
    refused = [path for path in dict.fromkeys(refused) if path not in kept]
    return tuple(kept), tuple(refused)


def transcripts(stores: tuple) -> tuple[list[str], list[str]]:
    """`(top-level transcripts, subagent sidecars)` across every store."""
    top, side = [], []
    for store in stores:
        top += sorted(glob.glob(os.path.join(store, "*.jsonl")))
        side += sorted(glob.glob(os.path.join(store, "*", SIDECARS)))
    return top, side


def _text_of(record: dict) -> str | None:
    """The typed text of a user record, or `None` where there is none."""
    content = record.get("message", {}).get("content")
    if isinstance(content, list):
        content = " ".join(
            part.get("text", "") for part in content if isinstance(part, dict)
        )
    if not isinstance(content, str) or not content.strip():
        return None
    return content


def _records(path: str):
    """Every record in a transcript that carries a timestamp, parsed."""
    try:
        handle = open(path, encoding="utf-8", errors="replace")
    except OSError:
        return
    with handle:
        for line in handle:
            try:
                record = json.loads(line)
            except ValueError:
                continue
            stamp = record.get("timestamp")
            if not stamp:
                continue
            when = dt.datetime.fromisoformat(stamp.replace("Z", "+00:00")).astimezone(LOCAL)
            yield when, record


@functools.lru_cache(maxsize=None)
def _parsed(stores: tuple, ritual: tuple):
    """Every session event, parsed once. `(events, prompts)`.

    An event is `(when, session, ritual)`; a prompt is `(when, text, ritual)`
    under its session. ⚠️ Parsed over the whole of every transcript rather than
    per day: the stores run to hundreds of megabytes, `--check` and `--month`
    ask about a day at a time, and the ritual state has to be carried across a
    day boundary anyway -- a turn opened before `day_start` is still the turn
    running at 05:01.
    """
    patterns = list(ritual)
    top, side = transcripts(stores)
    events: list[tuple] = []
    prompts: dict[str, list] = {}
    # The ritual flag of the turn running at each moment, per session, so a
    # sidecar's minutes inherit the mark of the turn that spawned it.
    timeline: dict[str, list[tuple[dt.datetime, bool]]] = {}

    for path in top:
        opened = None
        for when, record in _records(path):
            # ⛔ The session is read off the **record** and not off the file
            # name. A resumed session is documented to write a new file whose
            # records carry the original identifier, which would otherwise show
            # as two sessions and make `--skip-session` drop half of one. ⚠️ Not
            # reproduced in this project's store -- 158 files, 158 distinct
            # identifiers, none shared -- so this is the shape that holds if it
            # arises rather than a fix for something measured here.
            session = (record.get("sessionId") or os.path.basename(path)[:-6])[:8]
            text = None
            if record.get("type") == "user":
                text = _text_of(record)
                if text is not None and not NEUTRAL.match(text.strip()):
                    opened = when if is_ritual(text, patterns) else None
            ritual_now = opened is not None and when - opened <= RITUAL_CAP
            events.append((when, session, ritual_now))
            timeline.setdefault(session, []).append((when, ritual_now))
            if text and "local-command-caveat" not in text:
                prompts.setdefault(session, []).append(
                    (when, " ".join(text.split())[:200], ritual_now)
                )

    for session in timeline:
        timeline[session].sort(key=lambda row: row[0])

    for path in side:
        for when, record in _records(path):
            session = (record.get("sessionId") or "")[:8]
            # ⛔ **A sidecar's `user` record is not a typed prompt.** It is the
            # instruction the parent session sent the sub-window, so a delegated
            # task whose prompt opens with a bookkeeping word would open a ritual
            # turn and write off the whole sub-window's minutes. Nothing here
            # reads one as typed, and `isSidechain` is what says so on the record
            # itself. The mark is inherited from the parent turn instead.
            events.append((when, session or "agent", _at(timeline.get(session, []), when)))

    events.sort(key=lambda row: row[0])
    # ⛔ The timestamps are returned **beside** the events and never derived by a
    # second cached function. A cache whose key does not determine its value is
    # free to disagree with the thing it indexes: measured, a timestamp list held
    # over from a run that read no sidecars was bisected against a run that did,
    # and the slice came back short -- a day of 4.10 h read as 0.97 h, silently
    # and in the direction nothing reports.
    return events, prompts, [row[0] for row in events]


def _at(line: list, when: dt.datetime) -> bool:
    """Whether the parent turn running at `when` was bookkeeping.

    The latest record at or before the moment asked about. An event before a
    session's first record -- which a sidecar's first line can be, by
    milliseconds -- is not bookkeeping, since no bookkeeping turn had opened.
    """
    flag = False
    for stamp, ritual in line:
        if stamp > when:
            break
        flag = ritual
    return flag


def session_events(settings: Settings, span: tuple, skip: set) -> tuple[list, dict]:
    """`(events, prompts)` inside the window, with skipped sessions dropped."""
    if not settings.reads("sessions"):
        return [], {}
    stores, _refused = session_stores(tuple(root for _n, root, _r in settings.roots))
    events, prompts, stamps = _parsed(stores, tuple(settings.ritual))
    start, end = span
    # ⛔ The window is found by bisection and never by filtering the whole list.
    # `events` is sorted, and the days-with-activity walk asks about one day at a
    # time across this project's entire history -- so a scan per day costs the
    # event count times the day count. ⚠️ Measured at 74 s for a 915-day range on
    # one project, which is the `--check` that runs by default after every report.
    inside = [
        row for row in events[
            bisect.bisect_left(stamps, start):bisect.bisect_left(stamps, end)
        ]
        if row[1] not in skip
    ]
    shown = {
        session: [row for row in rows if start <= row[0] < end]
        for session, rows in prompts.items()
        if session not in skip
    }
    return inside, {session: rows for session, rows in shown.items() if rows}


# --------------------------------------------------------------------------------------------
# The chat stream
# --------------------------------------------------------------------------------------------


def _like(pattern: str, value: str) -> bool:
    """SQL `LIKE` over one value, case-insensitively.

    The patterns are written for the archive's own query, so a mark applied in
    Python has to agree with the rows the query returned -- and a second
    matching rule here would mark a different set of chats than the one read.
    """
    expression = "^" + re.escape(pattern).replace("%", ".*").replace("_", ".") + "$"
    return re.match(expression, value, re.I) is not None


class TelegramExport:
    """A chat archive exported to SQLite, which is one `kind` of chat source.

    ⛔ The archive's address is `day_log.evidence.chat.path` and appears nowhere
    in this file: it is a path on whoever's machine keeps the log.
    """

    KIND = "telegram_export"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.path = os.path.expanduser(os.path.expandvars(str(settings.chat_path)))
        # `(start, end, rows, newest)` for the widest range asked for so far.
        self._cache = None

    def available(self) -> bool:
        return os.path.exists(self.path)

    def _connect(self):
        return sqlite3.connect(f"file:{self.path}?mode=ro", uri=True)

    @functools.lru_cache(maxsize=None)  # noqa: B019 -- one archive per process
    def chats(self) -> tuple:
        """The chats the configured patterns actually resolve to.

        ⚠️ Resolved and printed rather than inferred, so a pattern that quietly
        widened onto somebody else's chat is visible. A bare surname pattern
        pulls in every personal chat that shares it.
        """
        if not self.available() or not self.settings.chat_patterns:
            return ()
        where = " OR ".join("name LIKE ?" for _ in self.settings.chat_patterns)
        with self._connect() as db:
            found = {row[0] for row in db.execute(
                f"SELECT name FROM chats WHERE {where}", self.settings.chat_patterns)}
        return tuple(sorted(
            name for name in found
            if not any(_like(bad, name) for bad in self.settings.chat_exclude)
        ))

    def mixed(self, chat: str) -> bool:
        """Whether a chat carries something other than this project as well."""
        return any(_like(pattern, chat) for pattern in self.settings.chat_mixed)

    def read(self, span: tuple, skip: tuple = ()) -> tuple[list, list, dt.datetime | None]:
        """`(events, rows, horizon)` for the window.

        An event from a mixed chat is tagged `chat~` rather than `chat`, which is
        what lets a block resting on nothing else be flagged.
        """
        patterns = self.settings.chat_patterns
        if not self.available() or not patterns:
            return [], [], None
        start, end = span
        rows, newest = self._rows(start, end)
        rows = [row for row in rows if not any(_like(f"%{s}%", row[1]) for s in skip)]
        events = [
            (dt.datetime.fromisoformat(row[0]).replace(tzinfo=LOCAL),
             "chat~" if self.mixed(row[1]) else "chat")
            for row in rows
        ]
        horizon = (
            dt.datetime.fromisoformat(newest).replace(tzinfo=LOCAL) if newest else None
        )
        return events, rows, horizon

    def warm(self, start: dt.datetime, end: dt.datetime) -> None:
        """Query the whole range before anything asks about one day of it.

        ⛔ **Not an optimisation to the side of the measurement.** The date
        comparison this archive is queried by cannot use an index, so every query
        is a full scan; `--check` and `--month` ask about a day at a time, and a
        range this project's own history is long enough to make that hundreds of
        scans. ⚠️ **Measured before this existed**: 0.28 s per day against a
        915-day range -- over four minutes for one `--check`, which runs by
        default after every day report. One wide query serves all of them.
        """
        if self.available() and self.settings.chat_patterns:
            self._rows(start, end)

    def _rows(self, start: dt.datetime, end: dt.datetime) -> tuple[list, str | None]:
        """The rows in `[start, end)`, from a cache that only ever widens."""
        held = self._cache
        if held is not None and held[0] <= start and end <= held[1]:
            rows, newest = held[2], held[3]
        else:
            rows, newest = self._query(start, end)
            self._cache = (start, end, rows, newest)
        return [
            row for row in rows
            if start <= dt.datetime.fromisoformat(row[0]).replace(tzinfo=LOCAL) < end
        ], newest

    def _query(self, start: dt.datetime, end: dt.datetime) -> tuple[list, str | None]:
        patterns = self.settings.chat_patterns
        where = " OR ".join("c.name LIKE ?" for _ in patterns)
        blocked = " ".join("AND c.name NOT LIKE ?" for _ in self.settings.chat_exclude)
        with self._connect() as db:
            rows = db.execute(
                "SELECT m.date, c.name, COALESCE(m.from_name,'?'), "
                "COALESCE(m.text,'['||COALESCE(m.media_type,m.type)||']') "
                "FROM messages m JOIN chats c ON c.id = m.chat_id "
                f"WHERE datetime(m.date) >= ? AND datetime(m.date) < ? AND ({where}) {blocked} "
                "ORDER BY m.date",
                [f"{start:%Y-%m-%d %H:%M:%S}", f"{end:%Y-%m-%d %H:%M:%S}",
                 *patterns, *self.settings.chat_exclude],
            ).fetchall()
            # ⛔ The newest message the archive actually **holds**, and not the
            # file's modification time. A live-synced archive in WAL mode leaves
            # the main file's time untouched until a checkpoint, so the mtime
            # reports a full day as truncated and the entry carries a "messages
            # are missing" caveat that is not true. Past this horizon messages
            # really are missing and the day really is under-measured.
            newest = db.execute("SELECT max(date) FROM messages").fetchone()[0]
        return rows, newest


CHAT_KINDS = {TelegramExport.KIND: TelegramExport}


# --------------------------------------------------------------------------------------------
# The commits stream
# --------------------------------------------------------------------------------------------


def commits(settings: Settings, span: tuple) -> list[tuple]:
    """Commits in the window, each flagged with whether it is the log owner's.

    ⛔ `%cd` and not `%ad`, because `--since`/`--until` filter on the committer
    date: a squash-merged or rebased commit carries an author date days earlier,
    and printing that one shows commits that look like they fell outside the
    window the filter just applied.

    ⚠️ Scoped to the repository and **not** to one person. A fetched commit
    arrives stamped inside the window and anchors a block exactly like the log
    owner's own; `day_log.attribute_to` is what marks it, and it is marked rather
    than dropped -- it proves the project moved, which is worth seeing.
    """
    if not settings.reads("commits"):
        return []
    start, end = span
    mine = {settings.attribute_to} if settings.attribute_to else set()
    out = []
    for name, root, _repo in settings.roots:
        if not os.path.exists(os.path.join(root, ".git")):
            continue
        for when, sha, author, email, subject in _commits_in(root, start, end):
            # ⚠️ Where no author is configured every commit is the owner's, which
            # is the right reading for a repository with one committer: a mark on
            # every line is a mark that says nothing.
            owned = not mine or email in mine
            out.append((name, when, sha, author, owned, subject))
    return sorted(out, key=lambda row: row[1])


# One listing per root over the widest range asked for, filtered per day. ⛔ Not a
# convenience: `--check` walks every day between this project's first commit and
# today, and a listing per day per root is that many `git log` invocations -- 915
# of them measured on one project, which is the same range the chat archive's
# widening cache exists for.
_COMMITS: dict = {}


def _commits_in(root: str, start: dt.datetime, end: dt.datetime) -> list[tuple]:
    """`(when, sha, author, email, subject)` in `[start, end)`, from a wide read."""
    held = _COMMITS.get(root)
    if held is None or not (held[0] <= start and end <= held[1]):
        listed = git(
            root, "log", "--all",
            f"--since={start:%Y-%m-%d %H:%M}", f"--until={end:%Y-%m-%d %H:%M}",
            "--date=format-local:%Y-%m-%d %H:%M:%S",
            "--pretty=format:%cd|%h|%an|%ae|%s", "--reverse",
        )
        rows = []
        for line in listed.splitlines():
            if line:
                rows.append(tuple(line.split("|", 4)))
        _COMMITS[root] = (start, end, rows)
        held = _COMMITS[root]
    return [
        row for row in held[2]
        if start <= dt.datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S").replace(
            tzinfo=LOCAL) < end
    ]


def warm(settings: Settings, start: dt.datetime, end: dt.datetime) -> None:
    """Read every stream over the whole range before any per-day loop runs.

    ⛔ **Without it the caches still work and serve nobody**: the first day asked
    about sets a narrow range that every later day misses, which is exactly the
    per-day rescan they exist to avoid. ⚠️ Measured on one project before any of
    this existed -- 0.28 s per day against a 915-day range, which is over four
    minutes for a `--check` that runs by default after every report.
    """
    if settings.reads("sessions"):
        session_events(settings, (start, end), set())
    if settings.reads("commits"):
        for _name, root, _repo in settings.roots:
            if os.path.exists(os.path.join(root, ".git")):
                _commits_in(root, start, end)
    if settings.chat_available:
        settings.chat_reader().warm(start, end)
    host_activity(settings, (start, end))


def commit_events(settings: Settings, span: tuple) -> list[tuple]:
    """Commits as block anchors.

    A commit is instantaneous, so on its own it only ever produces a 0m block --
    but that is the point: work done outside a session, a hand-written fix or a
    rebase, leaves no other trace in these streams.
    """
    start, end = span
    out = []
    for _name, when, *_rest in commits(settings, span):
        stamped = dt.datetime.strptime(when, "%Y-%m-%d %H:%M:%S").replace(tzinfo=LOCAL)
        # Clipped again rather than trusting git's own filter: `--since` and
        # `--until` are inclusive at minute resolution, so a commit exactly on
        # the boundary would otherwise anchor a block in both days at once.
        if start <= stamped < end:
            out.append((stamped, "git"))
    return out


# --------------------------------------------------------------------------------------------
# The host-activity stream
# --------------------------------------------------------------------------------------------


# Fetched once per process and filtered locally: `--check` walks a day at a time
# and a call per day would be both slow and rate-limited.
_HOST: dict = {"since": None, "rows": [], "error": None}


def _fetch_host(repos: list[str], since: dt.datetime) -> tuple[list, str | None]:
    """`(timestamp, what, text)` for items and pull requests, and every comment.

    Read through the host's own CLI, so it inherits that CLI's authentication.
    Returns a **reason** where that is not possible: a silently empty stream
    under-reports a project whose review work happens on the host and leaves no
    other trace, and the symptom is a low total with nothing else to see.
    """
    if not shutil.which("gh"):
        return [], "gh CLI not installed"
    stamp = f"{since.astimezone(dt.timezone.utc):%Y-%m-%dT%H:%M:%SZ}"
    rows = []
    for repo in repos:
        if not repo:
            continue
        endpoints = [
            (f"repos/{repo}/issues?state=all&since={stamp}&per_page=100", "item"),
            (f"repos/{repo}/issues/comments?since={stamp}&per_page=100", "comment"),
            (f"repos/{repo}/pulls/comments?since={stamp}&per_page=100", "comment"),
        ]
        for path, shape in endpoints:
            run = subprocess.run(
                ["gh", "api", "--paginate", path], capture_output=True, text=True
            )
            if run.returncode != 0:
                reason = (run.stderr.strip().splitlines() or ["gh api failed"])[-1][:120]
                return [], reason
            rows += _host_rows(run.stdout, shape)
    out = []
    for stamped, what, text in rows:
        if not stamped:
            continue
        when = dt.datetime.fromisoformat(stamped.replace("Z", "+00:00")).astimezone(LOCAL)
        out.append((when, what, text))
    return sorted(out), None


def _host_rows(text: str, shape: str) -> list[tuple]:
    """One endpoint's payload, which `--paginate` hands over as arrays in a row."""
    decoder, position, rows = json.JSONDecoder(), 0, []
    while position < len(text):
        while position < len(text) and text[position].isspace():
            position += 1
        if position >= len(text):
            break
        batch, position = decoder.raw_decode(text, position)
        for item in batch:
            kind = (
                "PR" if item.get("pull_request") or "pull" in item.get("html_url", "")
                else "issue"
            )
            if shape == "item":
                number = item.get("number")
                title = " ".join((item.get("title") or "").split())
                rows.append((item.get("created_at"), f"{kind} #{number} opened", title))
                if item.get("closed_at"):
                    merged = (item.get("pull_request") or {}).get("merged_at")
                    rows.append((
                        item.get("closed_at"),
                        f"{kind} #{number} {'merged' if merged else 'closed'}",
                        title,
                    ))
            else:
                found = re.search(r"/(?:issues|pull)/(\d+)", item.get("html_url", ""))
                body = " ".join((item.get("body") or "").split())
                rows.append((
                    item.get("created_at"),
                    f"{kind} #{found.group(1) if found else '?'} comment",
                    body,
                ))
    return rows


def host_activity(settings: Settings, span: tuple) -> tuple[list, list, str | None]:
    if not settings.reads("host_activity"):
        return [], [], None
    start, end = span
    if _HOST["since"] is None or start < _HOST["since"]:
        _HOST["since"] = start
        repos = [repo for _n, _r, repo in settings.roots]
        _HOST["rows"], _HOST["error"] = _fetch_host(repos, start)
    rows = [row for row in _HOST["rows"] if start <= row[0] < end]
    return [(row[0], "host") for row in rows], rows, _HOST["error"]


# --------------------------------------------------------------------------------------------
# Meetings, and the blocks every stream is unioned into
# --------------------------------------------------------------------------------------------


def meeting_events(settings: Settings, day: dt.date, spans: list) -> list[tuple]:
    """A meeting given as `HH:MM-HH:MM`, counted as solid.

    It lands on `day`, or on the morning after where it starts before
    `day_start` -- the same boundary the rest of the day uses.
    """
    if spans and not settings.reads("meetings"):
        raise Unavailable(
            "a meeting was passed and `day_log.streams` does not carry "
            "`meetings`, so it would be measured by a stream this project "
            "states it does not read (§ 9)."
        )
    events = []
    for span in spans:
        first, last = (dt.time.fromisoformat(part) for part in span.split("-"))
        base = day + dt.timedelta(days=1) if first < settings.day_start else day
        start = dt.datetime.combine(base, first).replace(tzinfo=LOCAL)
        end = dt.datetime.combine(base, last).replace(tzinfo=LOCAL)
        while start <= end:
            events.append((start, "meeting"))
            start += dt.timedelta(minutes=1)
    return events


def blocks(events: list, idle: int) -> list[list]:
    """Active blocks as `[start, end, sources, edges]`.

    `edges` names the ends whose clock is set by a **mixed** chat message alone
    -- `head`, `tail`, or both. A chat carrying this project's work alongside
    something else is the one stream that inflates a total two ways: a run of
    small talk becomes a block of its own, and one unrelated message on the edge
    of a real block stretches that block's clock. Flagged, never dropped -- the
    message may well be work, and only reading it can tell.
    """
    if not events:
        return []
    events = sorted({(when.replace(second=0, microsecond=0), src) for when, src in events})
    at: dict = {}
    for when, src in events:
        at.setdefault(when, set()).add(src)
    out, current = [], [events[0][0], events[0][0], {events[0][1]}]
    for when, src in events[1:]:
        if when - current[1] <= dt.timedelta(minutes=idle):
            current[1] = when
            current[2].add(src)
        else:
            out.append(current)
            current = [when, when, {src}]
    out.append(current)
    for block in out:
        edges = [
            name for name, when in (("head", block[0]), ("tail", block[1]))
            if at[when] == {"chat~"}
        ]
        block.append("+".join(edges))
    return out


def span_of(found: list) -> dt.timedelta:
    return sum((block[1] - block[0] for block in found), dt.timedelta())


class Day:
    """One working day's measured evidence."""

    def __init__(self, **fields) -> None:
        self.__dict__.update(fields)


def measure(
    settings: Settings,
    day: dt.date,
    idle: int = IDLE,
    meetings: tuple = (),
    skip: tuple = (),
    skip_chats: tuple = (),
    keep_ritual: bool = False,
) -> Day:
    """Active blocks for one working day.

    Meetings are optional -- omit them and the total is evidence-only, which is
    what `--check` compares against.

    ⚠️ **Ritual minutes do not anchor time.** Events belonging to a bookkeeping
    turn are dropped before the blocks are cut, so a save inside real work costs
    nothing and a save that was the only thing keeping an evening open stops
    holding it. The difference between the two totals is reported, because a
    deduction nobody can see is a deduction nobody can check.
    """
    span = settings.window(day)
    tagged, prompts = session_events(settings, span, set(skip))
    chat_events, chat_rows, horizon = [], [], None
    if settings.chat_available:
        chat_events, chat_rows, horizon = settings.chat_reader().read(
            span, tuple(skip_chats))
    host_events, host_rows, host_error = host_activity(settings, span)
    outside = (
        chat_events + host_events + commit_events(settings, span)
        + meeting_events(settings, day, list(meetings))
    )
    whole = blocks([(when, src) for when, src, _r in tagged] + outside, idle)
    if keep_ritual:
        found, dropped = whole, dt.timedelta()
    else:
        found = blocks(
            [(when, src) for when, src, ritual in tagged if not ritual] + outside, idle
        )
        dropped = span_of(whole) - span_of(found)
    return Day(
        day=day, span=span, blocks=found, total=span_of(found), prompts=prompts,
        chat_rows=chat_rows, horizon=horizon, host_rows=host_rows,
        host_error=host_error, dropped=dropped,
    )


def stamp(when: dt.datetime, day: dt.date) -> str:
    """`HH:MM`, or `+HH:MM` once the clock has rolled into the next morning."""
    return f"{'+' if when.date() != day else ' '}{when:%H:%M}"


def straddling(settings: Settings, first: dt.date, last: dt.date, idle: int) -> list[tuple]:
    """Active blocks that cross a day boundary, with no window clipping them.

    ⛔ **This is the one way the fold rule can still double-count.** Every block
    is assigned to a working day by where it starts, so two entries can only
    claim the same minutes if a block runs through a boundary -- then the earlier
    day measures it up to `day_start` and the later day measures it from
    `day_start`, and the same work is counted twice. An empty result is the proof
    that no entry overlaps another; it is not an assumption.
    """
    span = (
        dt.datetime.combine(first, settings.day_start).replace(tzinfo=LOCAL),
        dt.datetime.combine(
            last + dt.timedelta(days=2), settings.day_start
        ).replace(tzinfo=LOCAL),
    )
    tagged, _prompts = session_events(settings, span, set())
    events = [(when, src) for when, src, ritual in tagged if not ritual]
    if settings.chat_available:
        events += settings.chat_reader().read(span)[0]
    events += host_activity(settings, span)[0] + commit_events(settings, span)
    out = []
    for start, end, *_rest in blocks(events, idle):
        edge = dt.datetime.combine(start.date(), settings.day_start).replace(tzinfo=LOCAL)
        if edge <= start:
            edge += dt.timedelta(days=1)
        if start < edge <= end:
            out.append((start, end, edge))
    return out


# --------------------------------------------------------------------------------------------
# The store, reached through § 26's port
# --------------------------------------------------------------------------------------------


def recorded(settings: Settings, first: dt.date, last: dt.date) -> dict:
    """Every entry's stated hours across a range, read through the port.

    ⛔ **Through the port and never off a path composed here.** § 9's own
    cross-day validation read the store directly while the evidence script was
    each project's own; `read_hours` is the operation § 26 states for exactly
    this, and reading the directory here would be this script knowing what kind
    of store a project configured.

    ⚠️ **An answer carries two lists that are not one.** `unreadable` names days
    **inside** the range the store holds and could not read; `unplaced` names
    what it holds and cannot place in a day at all. Only the first says anything
    about the period asked for, and neither is an empty period.
    """
    opened = port.load(settings.skills_root, name=DESTINATION)
    if not opened.configured:
        raise Unavailable(
            f"`{DESTINATION}` addresses no store, so no entry can be read back "
            "and the cross-day validation cannot run (§ 26)."
        )
    if not opened.implements("read_hours"):
        raise Unavailable(
            f"`read_hours` is unavailable on this store, so this project has "
            f"**no answer** about the period: {opened.fallback('read_hours')} (§ 26)."
        )
    outcome = opened.invoke("read_hours", first.isoformat(), last.isoformat())
    if not outcome.performed:
        raise Unavailable(f"`read_hours` {outcome.detail} (§ 26).")
    return outcome.result


def located(settings: Settings, day: dt.date) -> str:
    """How the store is named out loud -- its own answer, or its configuration.

    ⛔ For the day being reported and never for today. The two differ on every
    backfill, and a header naming the entry's path for a different day is a path
    somebody would go and read.
    """
    try:
        opened = port.load(settings.skills_root, name=DESTINATION)
    except Exception as error:  # noqa: BLE001 -- reported, never raised past here
        return f"(could not be read: {error})"
    if not opened.configured:
        return f"(none — `{DESTINATION}` addresses nothing)"
    if not opened.implements("locate"):
        return f"({opened.kind}, addressed by its configuration)"
    outcome = opened.invoke("locate", day.isoformat())
    return str(outcome.result) if outcome.performed else f"({outcome.detail})"


def history(settings: Settings) -> dt.date:
    """The earliest day this project could have an entry for.

    The first commit in any of its repositories, which bounds the range handed to
    `read_hours`. ⚠️ Derived rather than configured and rather than unbounded: a
    period asked for from the epoch is a sweep of a store for no reason, and a
    period asked for from this month would report every earlier entry as absent.
    """
    earliest = None
    for _name, root, _repo in settings.roots:
        if not os.path.exists(os.path.join(root, ".git")):
            continue
        listed = git(
            root, "log", "--reverse", "--date=format-local:%Y-%m-%d",
            "--pretty=format:%cd", "--all",
        ).splitlines()
        if listed:
            found = dt.date.fromisoformat(listed[0])
            earliest = min(earliest, found) if earliest else found
    return earliest or settings.current_day()


# --------------------------------------------------------------------------------------------
# What the run prints
# --------------------------------------------------------------------------------------------


def sources(settings: Settings) -> list[str]:
    """Every input this run read, and every one it refused, by name.

    ⚠️ **Read this before the blocks.** It is the answer to *what did this total
    measure*, and a refusal that should have been kept shows up as a low total
    with no other symptom.
    """
    out = []
    for name, root, repo in settings.roots:
        out.append(f"    repo      [{name}] {root}" + (f"  → {repo}" if repo else ""))
    if settings.reads("sessions"):
        kept, refused = session_stores(tuple(root for _n, root, _r in settings.roots))
        top, side = transcripts(kept)
        for path in kept:
            out.append(f"    sessions  {path}")
        for path in refused:
            out.append(
                f" ⛔ sessions  {path} — no checkout of this project answers to it: "
                "another project whose path starts with this one's, or a worktree "
                "removed since its work, whose minutes are missing. Say which."
            )
        out.append(
            f"    sessions  {len(top)} transcripts and {len(side)} subagent sidecars read; "
            f"`{TOOL_RESULTS}/` deliberately excluded — offloaded tool output carries no "
            "timestamp, and the call that produced it is already a record in its parent"
        )
    else:
        out.append("    sessions  (not a configured stream)")
    if settings.chat_available:
        reader = settings.chat_reader()
        resolved = reader.chats()
        marked = ", ".join(
            f"{name}{'~' if reader.mixed(name) else ''}" for name in resolved
        )
        out.append(
            f"    chat      [{settings.chat_kind}] {marked or '(archive holds no matching chat)'}"
            + ("" if reader.available() else "  ⚠ archive not found")
        )
    else:
        out.append(f"    chat      (not read: `kind: {settings.chat_kind}`)")
    out.append(
        "    calendar  " + (", ".join(settings.calendars) or "(none configured)")
        + " — never another engagement's calendar, and a meeting arrives by --meeting"
    )
    if settings.attribute_to:
        out.append(f"    author    {settings.attribute_to} — another's commit is marked ~, never dropped")
    return out


def show(settings: Settings, found: Day, idle: int) -> None:
    """One day's evidence, as the role reads it."""
    day = found.day
    start, end = found.span
    aside = (
        f"   ritual {found.dropped.total_seconds() / 3600:.2f} h excluded"
        if found.dropped else ""
    )
    print(
        f"DAY {day}   {start:%m-%d %H:%M} → {end:%m-%d %H:%M}   "
        f"ACTIVE {found.total.total_seconds() / 3600:.2f} h   idle-cutoff {idle}m{aside}"
    )
    print(
        f"REPORT {settings.report_hours(found.total):.1f} h   ← the figure the entry states "
        f"(nearest {settings.round_to} h, ties {settings.round_ties}), "
        "once every drop above has been re-run"
    )

    print("\nSOURCES   (⛔ marks input refused as another project's, never counted)")
    for line in sources(settings):
        print(line)

    print("\nBLOCKS   (+ marks the small hours of the next morning, same working day)")
    suspect = dt.timedelta()
    for bstart, bend, src, edges in found.blocks:
        minutes = (bend - bstart).total_seconds() / 60
        mark = ""
        if src == {"chat~"}:
            mark = "   ⚠ a mixed chat alone — read it, then keep or --skip-chat"
            suspect += bend - bstart
        elif edges:
            mark = f"   ⚠ {edges} set by a mixed-chat message alone — read it"
        print(
            f" {stamp(bstart, day)}-{stamp(bend, day).strip()}  {minutes:4.0f}m  "
            f"{','.join(sorted(src))}{mark}"
        )
    if suspect:
        print(
            f"\n ⚠ {suspect.total_seconds() / 3600:.2f} h of the "
            f"{found.total.total_seconds() / 3600:.2f} h above rests on a mixed chat "
            "alone. Verify before reporting it."
        )

    print("\nSESSIONS   (· marks a bookkeeping turn — its minutes are not in the total)")
    for session, rows in sorted(found.prompts.items(), key=lambda kv: kv[1][0][0]):
        print(f" {session} {stamp(rows[0][0], day)}-{stamp(rows[-1][0], day).strip()}")
        for when, text, ritual in rows:
            print(f"    {'·' if ritual else ' '}{stamp(when, day)} {text}")

    print("\nCOMMITS   (~ marks someone else's commit — not your work to describe)")
    for name, when, sha, author, owned, subject in commits(settings, found.span):
        print(f"  {' ' if owned else '~'} {when[5:16]} [{name}] {sha} {author}: {subject}")

    if settings.reads("host_activity"):
        print("\nHOST")
        if found.host_error:
            print(
                f"  ⚠ unavailable ({found.host_error}) — review and merge work is NOT counted, "
                "so the total is low by however long it took"
            )
        for when, what, text in found.host_rows:
            print(f"  {stamp(when, day)} {what}: {text[:160]}")

    if settings.chat_available:
        print("\nCHAT   (~ marks a chat carrying something other than this project as well)")
        if found.horizon and found.horizon < end:
            print(
                f"  ⚠ archive ends {found.horizon:%Y-%m-%d %H:%M}, before this day does — "
                "later messages are missing and the total is low"
            )
        elif found.horizon:
            print(f"  (archive runs to {found.horizon:%Y-%m-%d %H:%M} — this day is covered)")
        reader = settings.chat_reader()
        for when, chat, who, text in found.chat_rows:
            mark = "~" if reader.mixed(chat) else " "
            print(f"  {mark}{when[5:16]} [{chat}] {who}: {' '.join(text.split())[:180]}")


# --------------------------------------------------------------------------------------------
# --check and --month
# --------------------------------------------------------------------------------------------


def check(settings: Settings, idle: int) -> int:
    """Every recorded entry, recomputed against the evidence.

    Fails on the ways an entry can be wrong against its neighbours, plus the one
    way its hours line can be wrong on its own:

      OVERLAP     a block runs through a day boundary, so two entries each
                  measure part of it and the same minutes are counted twice
      UNREPORTED  a day has measured activity and no entry at all
      GRID        the hours line is off the configured grid, where
                  `enforce_grid` is true

    ⚠️ `UNDER` is a **warning**. The role's own exclusions and `--skip-session`/
    `--skip-chat` legitimately remove measured time and this cannot know what
    left; the reply's cut list is what it is read against.
    """
    first, last = history(settings), settings.current_day()
    try:
        answer = recorded(settings, first, last)
    except Unavailable as absent:
        print(f"CHECK  could not run: {absent}")
        return 1

    # Every stream read once over the whole range, before the per-day loops. The
    # range is two days wider at the end, which is what `straddling` asks for.
    warm(settings, settings.window(first)[0],
         settings.window(last + dt.timedelta(days=2))[0])

    stated = answer["hours"]
    problems, notes = [], []
    days = sorted(stated)

    print(
        f"CHECK  {len(days)} entries   day boundary {settings.day_start:%H:%M}   "
        f"idle-cutoff {idle}m   stated to the nearest {settings.round_to} h "
        f"(±{settings.slack:.3f}), grid "
        f"{'asserted' if settings.enforce_grid else 'not asserted'}\n"
    )

    for name, reason in sorted(answer["unreadable"].items()):
        # ⛔ Never read as zero hours. The store holds the day and could not read
        # it, which is neither an absence nor a day nobody worked.
        problems.append(f"UNREADABLE  {name} — {reason}")
    for name, reason in sorted(answer["unplaced"].items()):
        problems.append(f"UNPLACED    {name} — {reason}, so it belongs to no period")

    # ⛔ **Over the range measured, never over the range recorded.** A boundary
    # crossing is computed from the blocks themselves and holds whether or not an
    # entry exists, so anchoring it on the recorded days means a store with no
    # entries yet has this check run over nothing at all -- and it is the one
    # failure recording an entry cannot clear, since it says the hours belong to
    # two days. ⚠️ Measured: a project with 0 entries reported no overlap line,
    # which read as *no working day is claimed twice*.
    for start, end, edge in straddling(settings, first, last, idle):
        problems.append(
            f"OVERLAP  {start:%m-%d %H:%M}-{end:%m-%d %H:%M} runs through the "
            f"{edge:%m-%d %H:%M} boundary — {edge.date() - dt.timedelta(days=1)} and "
            f"{edge.date()} both measure part of it"
        )

    for name in days:
        day = dt.date.fromisoformat(name)
        said = stated[name]
        found = measure(settings, day, idle)
        measured = found.total.total_seconds() / 3600
        note = ""
        if settings.enforce_grid and not settings.on_grid(said):
            # ⛔ A figure off the grid needs no judgement to spot and none to fix,
            # unlike UNDER below, so it fails rather than warns: that figure was
            # written by hand rather than read off REPORT, and every comparison
            # beside it is against a number this script never produced.
            note = f"  ✗ off the {settings.round_to} h grid"
            problems.append(
                f"GRID     {name} states {said} h, which is not a multiple of "
                f"{settings.round_to} h — the entry states the REPORT figure, "
                f"not the raw total, so this is "
                f"{settings.report_hours(dt.timedelta(hours=said))}"
            )
        elif said + settings.slack < measured:
            note = f"  ⚠ under-reported by {measured - said:.2f} h"
            notes.append(
                f"UNDER    {name} states {said:.1f} h, evidence shows {measured:.2f} h "
                "— a dropped session or chat, or time missing from the entry"
            )
        elif said > measured + settings.slack:
            floored = (
                abs(said - settings.round_to) <= EPS * 10 and measured < settings.round_to
            )
            note = (
                f"  (floored to {settings.round_to} h — a day with work never states 0.0)"
                if floored
                else f"  (+{said - measured:.2f} h — meetings must account for this)"
            )
        spans = " ".join(
            f"{stamp(s, day)}-{stamp(e, day).strip()}" for s, e, *_r in found.blocks
        )
        print(f"  {name}  stated {said:5.1f}  measured {measured:5.2f}{note}")
        print(f"              {spans.strip() or '(no activity)'}")

    # Work that exists and no entry covers -- the other way a log goes wrong, and
    # the one that matters most where a period is summed: it leaves the day out
    # of the total without saying so.
    covered = {dt.date.fromisoformat(name) for name in days}
    for day in sorted(_active(settings, first, last, idle) - covered):
        found = measure(settings, day, idle)
        problems.append(
            f"UNREPORTED  {day} has {found.total.total_seconds() / 3600:.2f} h and no entry"
        )

    print()
    if settings.reads("host_activity") and _HOST.get("error"):
        print(
            f"  ⚠ host stream unavailable ({_HOST['error']}) — review work is missing "
            "from every line above"
        )
    for note in notes:
        print(f"  ⚠ {note}")
    for problem in problems:
        print(f"  ✗ {problem}")
    if not problems:
        print(
            "  ✓ no working day is claimed twice, no measured time is unreported, "
            "and every entry read back"
        )
    return 1 if problems else 0


def _active(settings: Settings, first: dt.date, last: dt.date, idle: int) -> set:
    """Working days with any measured activity, across a range."""
    out, day = set(), first
    while day <= last:
        if measure(settings, day, idle).total:
            out.add(day)
        day += dt.timedelta(days=1)
    return out


def month(settings: Settings, tag: str, idle: int) -> int:
    """One month's stated hours, summed, with every hole in it named.

    **Why the dailies exist:** hours are only knowable on the day. A month later
    the evidence is still on disk, but the memory needed to read it is gone. A
    month with holes is wrong in one direction only -- too small -- which is why
    this fails loudly rather than shrugging: a missing day does not make the
    month look wrong, it makes it look smaller.
    """
    try:
        first = dt.date.fromisoformat(f"{tag}-01")
    except ValueError:
        print(f"MONTH  {tag!r} is not written `YYYY-MM`")
        return 1
    last = (first.replace(day=28) + dt.timedelta(days=4)).replace(day=1) - dt.timedelta(days=1)
    try:
        answer = recorded(settings, first, last)
    except Unavailable as absent:
        print(f"MONTH  could not run: {absent}")
        return 1

    # The whole month read once, for the reason `check` warms its own range.
    warm(settings, settings.window(first)[0],
         settings.window(last + dt.timedelta(days=1))[0])

    stated, gaps = answer["hours"], []
    print(f"MONTH {tag}   {len(stated)} entries\n")
    total = 0.0
    for name in sorted(stated):
        total += stated[name]
        print(f"  {name}  {stated[name]:5.1f}")
    for name, reason in sorted(answer["unreadable"].items()):
        gaps.append(f"UNREADABLE  {name} — {reason}, so it is not in this total")
    for name, reason in sorted(answer["unplaced"].items()):
        gaps.append(f"UNPLACED    {name} — {reason}")

    recorded_days = {dt.date.fromisoformat(name) for name in stated}
    for day in sorted(_active(settings, first, last, idle) - recorded_days):
        found = measure(settings, day, idle)
        gaps.append(
            f"UNREPORTED  {day} has {found.total.total_seconds() / 3600:.2f} h and no "
            "entry — missing from this total"
        )

    print(f"\n  TOTAL {total:.1f} h")
    for gap in gaps:
        print(f"  ✗ {gap}")
    return 1 if gaps else 0


# --------------------------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------------------------


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__.splitlines()[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--skills-root", default=".",
        help="the root this project's configuration is resolved against (§ 1). "
             "Defaults to the working directory",
    )
    parser.add_argument("--date", help="YYYY-MM-DD — the day the work started")
    parser.add_argument(
        "--idle", type=int, default=IDLE,
        help="minutes of silence that end a block",
    )
    parser.add_argument(
        "--meeting", action="append", default=[],
        help="HH:MM-HH:MM, counted as solid",
    )
    parser.add_argument(
        "--skip-session", action="append", default=[],
        help="8-character session identifier to drop for this day",
    )
    parser.add_argument(
        "--skip-chat", action="append", default=[],
        help="substring of a chat name to drop for this day",
    )
    parser.add_argument(
        "--keep-ritual", action="store_true",
        help="count blocks that hold nothing but tooling upkeep",
    )
    parser.add_argument(
        "--check", action="store_true",
        help="recompute every recorded entry; fail on overlap, an unreported day, "
             "an unreadable entry or an off-grid figure",
    )
    parser.add_argument("--month", help="YYYY-MM — sum that month's stated hours")
    parser.add_argument(
        "--self-test", action="store_true",
        help="hold this script to the surface and to its own corpus",
    )
    args = parser.parse_args(argv)

    if args.self_test:
        from _day_log_suite import self_test

        return self_test()

    try:
        settings = Settings(config.load(args.skills_root))
    except config.ConfigError as error:
        print(f"⛔ {error}")
        return 2

    day = dt.date.fromisoformat(args.date) if args.date else settings.current_day()
    print(
        f"PROJECT {settings.skills_root}   "
        f"configuration {settings.config.config_path}   "
        f"store {located(settings, day)}"
    )

    try:
        if args.check:
            return check(settings, args.idle)
        if args.month:
            return month(settings, args.month, args.idle)
        found = measure(
            settings, day, args.idle, tuple(args.meeting), tuple(args.skip_session),
            tuple(args.skip_chat), args.keep_ritual,
        )
        show(settings, found, args.idle)
        # One invocation per report: the cross-day validation runs here rather
        # than from a second call, so the day's evidence and every neighbour's
        # state arrive together and nothing has to be recomputed to write the
        # entry.
        print()
        check(settings, args.idle)
    except Unavailable as absent:
        print(f"⛔ {absent}")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
