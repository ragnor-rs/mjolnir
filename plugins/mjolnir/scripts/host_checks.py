#!/usr/bin/env python3
"""What the host's own runs answer about a command and a change.

A project states the host's workflows once, in `host.checks`, and the surface
beside this script -- `../config/schema.md` § 2 -- is the single statement of
what that facet holds: which local command each run mirrors, what starts it, and
which paths it watches. This module is the one piece of code that turns those
facts into an answer a role can act on, so that **no consumer carries a workflow
name, a trigger pattern or a path filter of its own**. The reviewing role driving
runs green, the finishing role refusing to merge without them and a guard
refusing a local run the host has already made all ask the same question here,
and a refusal they report names the workflow this module read.

Three things it deliberately does not do:

  * **It carries no workflow name, no trigger pattern and no path filter, and
    no trigger grammar either.** Every one of those is a project's fact, read
    through `config.py` at run time -- including the parse of § 2's
    `<event>(<types>) -> <ref>` form, which is `config.parse_trigger` and ⛔
    **never a second spelling here**. What this module carries is the one ref
    pattern a *rule* turns on, `*`, which the self-test holds to the surface so
    that renaming it there reddens the build rather than silently turning off
    the match that depends on it — and the glob characters a path filter is
    written with, which ⚠️ **the surface does not state and the self-test
    therefore cannot hold**: § 2 says only that a filter is a list of globs, so
    which of them this module can answer about is its own judgement, erring
    towards refusing a pattern. ⛔ **It enumerates no events**: § 2 states that vocabulary is
    the host's and that the facet holds no name against it, so an event this
    module has never seen is not this change's event rather than a trigger it
    may refuse.
  * **It never reads the host.** Which runs exist for a commit, whether one
    executed steps and how it concluded are § 2's four preconditions, answered
    from live state by the role that asks. This module answers the half the
    *facet* holds -- is there a run that answers for this command, and does it
    reach this change -- and ⛔ `reached` is therefore never *green*: it names
    the run whose conclusion is worth reading, and reading it is the caller's.
  * **It does not decide what a role then does.** It reports one of § 2's four
    answers and exits zero on every one of them, the way `config.py` reports
    what a configuration cannot support without acting on it. ⛔ A verdict in an
    exit status would make this module the guard rather than the guard's source,
    and a guard's own decision -- fail open, a never-guard list, an escape -- is
    its configuration and not this facet's.

**`checks: []` is an answer and not an empty one.** § 2 makes it the one
legitimate absence, meaning every verdict is local, so every question here comes
back *no answer* on it -- ⛔ never *not covered* and never green, which is the
absence rule the facet opens with.

Usage:
    host_checks.py [--skills-root DIR]
                                   print the facet as a consumer reads it
    host_checks.py mirrors --command CMD [--skills-root DIR]
                                   name where the host's runs mirror this
                                   command, or that nothing does
    host_checks.py covers --command CMD --event EVENT --ref REF
                          [--type TYPE] [--path PATH ...] [--skills-root DIR]
                                   which of § 2's four answers this change gets
    host_checks.py --self-test     hold the grammar to the surface and every
                                   answer to a planted configuration
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

import config
from config import ConfigError

# --- what the surface states -----------------------------------------------
#
# Grammar only, per the rule above, and ⛔ **the trigger grammar is not here at
# all**: `config.parse_trigger` is the one parser of § 2's `<event>(<types>) ->
# <ref>` form, and a second spelling of it in this module would be the defect
# the facet exists against. What is carried is the vocabulary a *rule* turns on,
# which a grammar cannot say -- the discipline `config.py` applies to its own
# sentinels -- and each constant is held to the surface by the self-test.

SURFACE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "schema.md"
)

# `*`, which § 2 states as the ref a trigger filters on none by. ⛔ Special-cased
# rather than run through the glob translation below, because the two disagree:
# read as an ordinary glob `*` stops at a path separator, so every project whose
# branches are named with one would read as out of scope for every run it makes.
ANY = "*"

# The four answers § 2 names, and the order a disjunction of them is resolved
# in -- `reached` first, then the three that read as *run it here*.
#
# ⚠️ This tuple **is** a second statement of the ranking, the first being § 2's
# prose, and the self-test holds it to that prose rather than claiming
# otherwise: the set is asserted member by member, and the one ordering fact the
# surface states -- that `reached` outranks the other three -- is asserted as a
# phrase. ⛔ The relative order of the remaining three is this module's and
# nothing holds it, which costs nothing a caller can see: all three read as
# *run it here*, so only the reported reason differs between them.
#
# ⛔ What it is stated for is `_ranked` below, so that the three places a
# precedence is needed read one tuple. Before it did, they disagreed.
REACHED, OUT_OF_SCOPE, NO_ANSWER, UNREADABLE = (
    "reached", "out of scope", "no answer", "unreadable",
)
ANSWERS = (REACHED, UNREADABLE, NO_ANSWER, OUT_OF_SCOPE)

# What a glob may be written with, and what makes one unreadable. § 2 states a
# path filter as a list of globs and nothing further, so the characters this
# module can answer about are stated here and everything else is refused as a
# pattern rather than guessed at.
#
# ⛔ The refused set is not decoration. `!` negates a filter on the host, `[` and
# `{` open a class and an alternation, and `+` opens an extended group: each one
# changes which paths a filter admits, and a translator that dropped it would
# answer *out of scope* for a change the run really covers -- a green reported
# for a run nobody read. Refusing the pattern errs the other way, which is § 17's
# direction.
UNPARSEABLE_IN_A_GLOB = "![]{}+()"

# --- the facet, as a consumer reads it -------------------------------------


def _glob(pattern: str) -> re.Pattern[str] | None:
    """§ 2's glob as an expression over a path, or None where it cannot be read.

    `**` spans separators, `*` and `?` stop at one. ⚠️ `**` is translated before
    `*` and in one pass, because a two-pass translation turns the first star of a
    `**` into *anything but a separator* and the pattern then matches nothing a
    directory deep -- a filter that admits no path reads exactly like a filter
    that excludes this change.
    """
    if any(character in pattern for character in UNPARSEABLE_IN_A_GLOB):
        return None
    out = []
    index = 0
    while index < len(pattern):
        character = pattern[index]
        if character == "*":
            if pattern.startswith("**", index):
                out.append(".*")
                index += 2
                continue
            out.append("[^/]*")
        elif character == "?":
            out.append("[^/]")
        else:
            out.append(re.escape(character))
        index += 1
    return re.compile("^" + "".join(out) + "$")


# How one trigger, or one level of a path filter, stands to a change. ⚠️
# `UNESTABLISHED` is deliberately not named for either of the two facts that
# reach it -- an event type the caller did not state, and a change whose paths
# it did not state -- because both do, and a name belonging to one of them reads
# as a defect to whoever meets it under the other.
ADMITS, EXCLUDES, UNREADABLE_GLOB, UNESTABLISHED = (
    "admits", "excludes", "unreadable glob", "unestablished",
)

# Which of § 2's answers each standing is. ⛔ A map rather than a branch per
# standing, so that the ranking below is applied to standings and answers
# alike and there is one ordering in this module rather than two.
AS_AN_ANSWER = {
    ADMITS: REACHED,
    UNREADABLE_GLOB: UNREADABLE,
    UNESTABLISHED: NO_ANSWER,
    EXCLUDES: OUT_OF_SCOPE,
}


def _within(filters, paths: list[str]) -> str:
    """How this filter stands to the paths a change touches.

    Four outcomes rather than a boolean with a `None`, because two of them are
    unanswerable for opposite reasons and § 2 gives them different answers: a
    glob the surface's form does not cover is the configuration's to fix, and a
    change whose paths the caller did not state is the caller's.

    ⛔ A level stating no filter bounds nothing and admits, which is § 2's rule
    that neither level is inherited and neither overrides the other: a filter
    that is not there is not a filter that excludes everything.
    """
    if not filters:
        return ADMITS
    expressions = [_glob(pattern) for pattern in filters]
    if any(expression is None for expression in expressions):
        return UNREADABLE_GLOB
    if not paths:
        return UNESTABLISHED
    return ADMITS if any(
        expression.match(path) for expression in expressions for path in paths
    ) else EXCLUDES


def _fires(parsed, event: str, ref: str, kind: str | None) -> str:
    """How one parsed trigger stands to this change: the three parts in order.

    ⛔ An event this module does not recognise is **not** a non-match and not
    unreadable either -- § 2 states that the event vocabulary is the host's and
    that the facet neither enumerates it nor holds a name against it, so the
    only question here is whether it is *this change's* event. A trigger on
    some other event does not fire for this change, which is an answer rather
    than an absence.
    """
    trigger_event, types, trigger_ref = parsed
    if trigger_event != event:
        return EXCLUDES
    # ⛔ No clause means the workflow's event block states no `types:` key, which
    # § 2 says is never read as the host's default set for that event -- so it
    # filters on nothing and this change's type cannot exclude it.
    if types is not None:
        if kind is None:
            return UNESTABLISHED
        # A set, their order carrying nothing, which is § 2's own rule.
        if kind not in set(types):
            return EXCLUDES
    if trigger_ref == ANY:
        return ADMITS
    expression = _glob(trigger_ref)
    if expression is None:
        return UNREADABLE_GLOB
    return ADMITS if expression.match(ref) else EXCLUDES


def _answer_for(
    record: dict, event: str, ref: str, kind: str | None, paths: list[str]
) -> dict:
    """§ 2's answer for one record of the facet, with what decided it."""
    triggers = record["triggers"]
    if triggers is None:
        return {
            "answer": NO_ANSWER,
            "because": "the entry states no `triggers`, so there is nothing to "
                       "match this change against (§ 2)",
        }
    patterns = triggers if isinstance(triggers, list) else [triggers]
    parsed = [config.parse_trigger(pattern) for pattern in patterns]
    unreadable = [
        pattern for pattern, found in zip(patterns, parsed) if found is None
    ]
    if unreadable:
        return {
            "answer": UNREADABLE,
            "because": "the entry states a trigger § 2's form does not cover: "
                       + ", ".join(f"`{pattern}`" for pattern in unreadable),
        }
    # ⛔ **A trigger list is a disjunction and the two filter levels are a
    # conjunction, so one ranking cannot be applied the same way to both.** A
    # workflow with two triggers runs when *either* fires, which is why `ADMITS`
    # wins here — the ranking § 2 states for a command mirrored twice, and for
    # the same reason: a trigger that fires on this change means the run exists,
    # so a sibling pattern nobody can parse does not unmake it. ⚠️ Measured as a
    # contradiction before it was a rule: the same two triggers answered
    # `reached` across two entries and `unreadable` inside one.
    fired = _ranked([_fires(found, event, ref, kind) for found in parsed])
    if fired == UNREADABLE:
        return {
            "answer": UNREADABLE,
            "because": "no trigger of this entry fires on this change and one "
                       "states a ref pattern that is no glob this module can "
                       "read, so the entry cannot be answered about (§ 2)",
        }
    if fired == NO_ANSWER:
        return {
            "answer": NO_ANSWER,
            "because": "a trigger of this entry filters on event types and "
                       "the change's own type was not stated, so whether "
                       "the run fires for it is unestablished (§ 2)",
        }
    if fired == OUT_OF_SCOPE:
        return {
            "answer": OUT_OF_SCOPE,
            "because": f"no trigger of this entry fires on `{event} -> {ref}`, "
                       "so the host runs nothing for this change and the local "
                       "verdict is the only one there is (§ 17)",
        }
    # ⛔ And here `ADMITS` does **not** win: § 2 makes a command's run cover a
    # change that is within the workflow's filter *and* the job's, neither
    # inherited and neither an override — so one level admitting says nothing
    # while the other excludes. What is ranked is only which of the three
    # non-admitting standings to report.
    levels = {
        level: _within(filters, paths)
        for level, filters in record["paths"].items()
    }
    blocked = {
        level: standing for level, standing in levels.items()
        if standing != ADMITS
    }
    if blocked:
        worst = _ranked(list(blocked.values()))
        level = next(
            name for name, standing in blocked.items()
            if AS_AN_ANSWER[standing] == worst
        )
        return {
            "answer": worst,
            "because": {
                UNREADABLE: f"the {level}'s path filter states a glob § 2's form "
                            "does not cover, so what the run watches cannot be "
                            "read off the configuration",
                NO_ANSWER: f"the {level} filters by path and the change's own "
                           "paths were not stated, so whether the run watches "
                           "this change is unestablished (§ 2)",
                OUT_OF_SCOPE: f"the {level}'s path filter admits no path this "
                              "change touches, so the host runs nothing for it "
                              "(§ 17)",
            }[worst],
        }
    return {
        "answer": REACHED,
        "because": f"{record['mirrored_by']} fires on `{event} -> {ref}` and its "
                   "filters admit this change -- so this is the run to read, and "
                   "how it concluded is § 2's four preconditions'",
    }


def _ranked(standings: list[str]) -> str:
    """The highest-ranked answer among these standings, by § 2's own order.

    ⛔ One ordering in this module and not one per caller: `ANSWERS` is applied
    to a trigger list, to a command two entries mirror, and to the filter
    levels, so a precedence written out at any of those three would be a second
    statement of the ranking — which is how the three came to disagree.
    """
    answers = {AS_AN_ANSWER[standing] for standing in standings}
    return next(answer for answer in ANSWERS if answer in answers)


def mirrors(configuration: config.Config, command: str) -> dict:
    """Where the host's runs mirror this command, read from the facet alone.

    The answer a guard's refusal names, so it carries the phrase § 2 keys the
    facet by -- the workflow, or the job of a workflow where a job is what
    mirrors the command.

    ⛔ `mirrored` is three-valued and the third value is not a `false`.
    Nothing mirroring the command is § 17's complement and a definite answer:
    that command is the one that must run locally, because nothing else will
    ever answer it. An **empty** facet is not that answer -- § 2 states it as
    every verdict being local, which is *no answer* about a host run, and
    collapsing the two would report a command as one the host does not run on
    the strength of a project having said nothing about its host at all.

    ⚠️ This answer is deliberately **not** one of § 2's four. Those are the
    answers about a run and a *change*, and this question has no change in it;
    borrowing `reached` here would name the same word for two findings.
    """
    wanted = " ".join(command.split())
    if not configuration.get("host.checks"):
        return {
            "command": command,
            "mirrored": None,
            "answer": NO_ANSWER,
            "mirrored_by": [],
            "because": "`host.checks` is empty, which § 2 states as every verdict "
                       "being local. That is no answer about a host run, never a "
                       "command the host runs and never one it does not.",
        }
    records = [r for r in configuration.mirrors() if r["normalised"] == wanted]
    if not records:
        return {
            "command": command,
            "mirrored": False,
            "answer": NO_ANSWER,
            "mirrored_by": [],
            "because": "no `host.checks` entry mirrors this command, so no host "
                       "run answers for it -- § 17's complement: it is the one "
                       "that must run locally.",
        }
    return {
        "command": command,
        "mirrored": True,
        "answer": None,
        "mirrored_by": [r["mirrored_by"] for r in records],
        "workflows": sorted({r["workflow"] for r in records}),
        "jobs": sorted({r["job"] for r in records if r["job"]}),
        "because": "the facet states a run that answers for this command; "
                   "whether it reaches a given change is `covers`.",
    }


def covers(
    configuration: config.Config,
    command: str,
    event: str,
    ref: str,
    kind: str | None = None,
    paths: list[str] | None = None,
) -> dict:
    """Which of § 2's four answers this change gets about this command.

    The change is its three facts, which are the three a trigger states: the
    event that produced it, the ref it is against, and the type of that event
    where the host sends one. ⚠️ `kind` is the **event's** type and not a
    change's kind in any other sense -- § 2's type clause, read from the other
    side.

    ⚠️ Every record mirroring the command is read and the answers ranked, never
    the first one found: a command mirrored by two entries is covered where
    either reaches the change, and stopping at the first would report *out of
    scope* on the strength of the entry that happens to be written above.
    """
    paths = paths or []
    change = {"event": event, "ref": ref, "type": kind, "paths": paths}
    found = mirrors(configuration, command)
    # Both of that answer's negative values land here, and § 2's table is why
    # they land on the same verdict: an empty facet and a command nothing
    # mirrors are each *nothing to read*, however differently they got there.
    if not found["mirrored"]:
        return {
            "command": command,
            "change": change,
            "verdict": NO_ANSWER,
            "because": found["because"],
            "per_run": [],
        }
    wanted = " ".join(command.split())
    per_run = []
    for record in configuration.mirrors():
        if record["normalised"] != wanted:
            continue
        answer = _answer_for(record, event, ref, kind, paths)
        per_run.append({
            "mirrored_by": record["mirrored_by"],
            "workflow": record["workflow"],
            "job": record["job"],
            **answer,
        })
    # The same ranking `_answer_for` applies inside one entry, for § 2's stated
    # reason: a run that reaches this change exists, so there is something to
    # read, whatever a sibling entry could not say.
    answered = {r["answer"] for r in per_run}
    verdict = next(
        (answer for answer in ANSWERS if answer in answered), NO_ANSWER
    )
    return {
        "command": command,
        "change": change,
        "verdict": verdict,
        "because": next(r["because"] for r in per_run if r["answer"] == verdict),
        "per_run": per_run,
    }


def facet(configuration: config.Config) -> dict:
    """The facet as a consumer reads it, with what an empty one means."""
    records = configuration.mirrors()
    return {
        "checks": records,
        "empty": not configuration.get("host.checks"),
        "report": (
            ["`host.checks` is empty: § 2 states that as every verdict being "
             "local, so every question about a host run here comes back no "
             "answer rather than not covered."]
            if not configuration.get("host.checks")
            else []
        ),
    }


# --- the self-test ---------------------------------------------------------


def _surface_text() -> str:
    with open(SURFACE, encoding="utf-8") as handle:
        return handle.read()


def _a_configuration(checks) -> config.Config:
    """A loadable configuration whose `host.checks` is the stated list.

    Built from an example rather than written here, so a facet this module reads
    is one the reader beside it accepts -- a planted configuration that does not
    load would make every answer below an answer about nothing.
    """
    import yaml

    path = os.path.join(
        os.path.dirname(SURFACE), "examples", "github-issues.yaml"
    )
    with open(path, encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    data.setdefault("host", {})["checks"] = checks
    # § 17's refusal reads `host.checks` to find a local check the host already
    # runs, so a plant that happens to collide with one would be refused by the
    # reader rather than answered here.
    data["checks_local"] = []
    return config.load_text(yaml.safe_dump(data), ".", check_paths=False)


# The events the fixtures below describe a change as having. ⚠️ Fixture data and
# **not** a vocabulary this module holds -- § 2 states the event set is the
# host's, so these are two events a change can have and not two this module
# knows about. `an-event-this-module-has-never-heard-of` is the plant that keeps
# the distinction honest.
A_PULL_REQUEST, A_PUSH = "pull_request", "push"

ONE_ENTRY = [{
    "workflow": "A workflow",
    "mirrors": "a-mirrored-command",
    "triggers": ["pull_request -> *", "push -> main"],
}]

TYPED = [{
    "workflow": "A workflow",
    "mirrors": "a-mirrored-command",
    "triggers": "pull_request(opened, ready_for_review) -> *",
}]

FILTERED = [{
    "workflow": "A workflow",
    "mirrors": "a-mirrored-command",
    "triggers": "pull_request -> *",
    "paths": ["a-tree/**"],
}]

FOUR_JOBS = [{
    "workflow": "A workflow",
    "triggers": "pull_request -> *",
    "paths": ["a-tree/**"],
    "jobs": [
        {"job": "a-job", "mirrors": "a-mirrored-command", "paths": ["a-tree/one/**"]},
        {"job": "another-job", "mirrors": "another-mirrored-command"},
    ],
}]


def self_test() -> int:
    """Hold the grammar to the surface, then every answer to a planted facet."""
    failures: list[str] = []

    def check(label: str, condition: bool, detail: str = "") -> None:
        print(f"  {'ok  ' if condition else 'FAIL'}  {label}"
              + (f": {detail}" if detail and not condition else ""))
        if not condition:
            failures.append(label)

    surface = _surface_text()

    print("the grammar this module carries is the surface's")
    # ⛔ The first of these is the one that matters most: it asserts that this
    # module has no trigger parser of its own. § 2's form is one grammar, and a
    # second reading of it here would be free to disagree with the reader every
    # consumer loads the facet through.
    # ⛔ Read off this module's own source, and ⛔ **not off a name and not off
    # what a compiled pattern contains.** Two forms of this assertion were
    # written and both held nothing: the first matched the literal name
    # `TRIGGER` and would have passed a `_TRIGGER_RE`, and the second searched
    # compiled patterns for § 2's arrow — which a parenthesis inside the
    # pattern truncates away, measured by planting a parser whose first group
    # closed before the arrow and watching the check stay green.
    #
    # ⚠️ What is asserted instead is positive and countable: the reader's parser
    # is called, and the one expression this module compiles is the path glob.
    # ⛔ **It does not reach a parser written with `str.split`** — nothing here
    # does, the arrow being a return annotation on half the functions in this
    # file — and that residue is stated with the check rather than left to
    # read as covered.
    with open(os.path.abspath(__file__), encoding="utf-8") as handle:
        own_source = handle.read()
    compiled = re.findall(r"re\.compile\(", own_source)
    check(
        "the reader's trigger parser is what this module calls",
        hasattr(config, "parse_trigger") and "config.parse_trigger(" in own_source,
        "this module does not call `config.parse_trigger`, so whatever reads a "
        "trigger here is a second spelling of one grammar",
    )
    check(
        "and the one expression it compiles is the path glob",
        len(compiled) == 1,
        f"{len(compiled)} compiled expression(s) in this module, where § 2's "
        "grammar is the reader's and a path glob is the only pattern left",
    )
    check(
        "§ 2 states `*` as the ref a trigger filters on none by",
        f"`{ANY}` for any" in surface,
        "the any-ref spelling is not stated with the trigger's three parts",
    )
    check(
        "§ 2 states that `reached` outranks the other three",
        f"`{REACHED}` outranks the other three" in surface,
        "the one ordering fact `ANSWERS` copies is not on the surface, so the "
        "ranking this module applies is held to nothing",
    )
    check(
        "§ 2 states that the event vocabulary is the host's and not this facet's",
        "event vocabulary is the host's" in surface,
        "the rule this module declines to enumerate events under is not stated, "
        "so an unrecognised event may have become refusable again",
    )
    for answer in ANSWERS:
        check(
            f"§ 2 names the `{answer}` answer",
            f"**{answer}**" in surface,
            "this module's answer is not one the surface names",
        )

    print("\nthe facet's own absence")
    empty = _a_configuration([])
    for label, got in (
        ("mirrors", mirrors(empty, "a-mirrored-command")["answer"]),
        ("covers",
         covers(empty, "a-mirrored-command", A_PULL_REQUEST, "main")["verdict"]),
    ):
        check(
            f"`checks: []` answers no answer to `{label}`",
            got == NO_ANSWER,
            f"answered {got!r}, and § 2 makes an empty list no answer rather "
            "than a command the host does not run",
        )
    check(
        "`checks: []` is reported as a stated absence rather than an empty read",
        facet(empty)["empty"] and facet(empty)["report"],
        "an empty facet came back with nothing said about it",
    )

    print("\na command no entry mirrors")
    one = _a_configuration(ONE_ENTRY)
    unmirrored = mirrors(one, "an-unmirrored-command")
    check(
        "is a definite not-mirrored, naming § 17's complement",
        unmirrored["mirrored"] is False,
        f"answered {unmirrored['mirrored']!r}",
    )
    check(
        "and is told apart from a facet that states nothing at all",
        mirrors(empty, "a-mirrored-command")["mirrored"] is None,
        "an empty facet answered the same value as a command nothing mirrors, "
        "so a project that said nothing about its host reads as one that "
        "decided this command is not run there",
    )

    print("\nan entry stating no triggers")
    # ⛔ The arm no configuration in this tree is in -- every example states a
    # trigger -- which is exactly why it is planted here: an adopter's first
    # entry is written before anybody tells them the key exists, and § 2 permits
    # the absence, so this is the shape a consumer meets first on their tree.
    silent = _a_configuration(
        [{"workflow": "A workflow", "mirrors": "a-mirrored-command"}]
    )
    check(
        "is mirrored, the facet having stated the run",
        mirrors(silent, "a-mirrored-command")["mirrored"] is True,
        "an entry with no trigger stopped mirroring the command it mirrors",
    )
    silent_answer = covers(silent, "a-mirrored-command", A_PULL_REQUEST, "main")
    check(
        f"and is {NO_ANSWER} about a change, never coverage",
        silent_answer["verdict"] == NO_ANSWER,
        f"answered {silent_answer['verdict']!r} -- {silent_answer['because']}",
    )

    print("\nwhat a trigger's event and ref reach")
    for label, event, ref, expected in (
        ("a pull request against any ref", A_PULL_REQUEST, "main", REACHED),
        # ⛔ `*` is any ref and not *any ref without a separator in it*. Read as
        # an ordinary glob it stops at the separator, so every project whose
        # branches are named with one would read as out of scope — and `*` is
        # the pattern every entry in this repository is written with.
        ("a pull request whose ref carries a separator", A_PULL_REQUEST,
         "release/1.0", REACHED),
        ("a push to the branch the entry names", A_PUSH, "main", REACHED),
        ("a push to a branch it does not name", A_PUSH, "a-topic", OUT_OF_SCOPE),
        # ⛔ Out of scope and never unreadable: § 2 states the event vocabulary
        # is the host's, so an event this module has never seen is simply not a
        # trigger of this entry's — the facet holds no name against it.
        ("an event no trigger of the entry names",
         "an-event-this-module-has-never-heard-of", "main", OUT_OF_SCOPE),
    ):
        got = covers(one, "a-mirrored-command", event, ref)["verdict"]
        check(f"{label} is {expected}", got == expected, f"answered {got!r}")

    print("\nwhat a type clause reaches")
    typed = _a_configuration(TYPED)
    for label, kind, expected in (
        ("a type the clause states", "opened", REACHED),
        ("a type stated second, the clause being a set", "ready_for_review",
         REACHED),
        ("a type the clause does not state", "closed", OUT_OF_SCOPE),
        # ⛔ Fail-closed, as § 17's arm requires: a clause the change cannot be
        # matched against is unestablished, which reads as *run it here*.
        ("a change whose event type was not stated", None, NO_ANSWER),
    ):
        got = covers(typed, "a-mirrored-command", A_PULL_REQUEST, "main", kind)
        check(f"{label} is {expected}", got["verdict"] == expected,
              f"answered {got['verdict']!r} -- {got['because']}")
    check(
        "a trigger stating no clause is not filtered by the change's type",
        covers(one, "a-mirrored-command", A_PULL_REQUEST, "main",
               "a-type-nothing-names")["verdict"] == REACHED,
        "an omitted clause was read as a filter, which § 2 forbids: it means "
        "the workflow's event block states no `types:` key",
    )

    print("\nwhat a path filter reaches")
    filtered = _a_configuration(FILTERED)
    for label, paths, expected in (
        ("a path the filter admits", ["a-tree/a-file"], REACHED),
        ("a path a directory deeper", ["a-tree/below/a-file"], REACHED),
        ("a path outside it", ["another-tree/a-file"], OUT_OF_SCOPE),
        ("a change whose paths were not stated", [], NO_ANSWER),
    ):
        got = covers(filtered, "a-mirrored-command", A_PULL_REQUEST, "main",
                     None, paths)
        check(f"{label} is {expected}", got["verdict"] == expected,
              f"answered {got['verdict']!r} -- {got['because']}")

    print("\nthe two levels a filter sits at, neither inherited")
    jobs = _a_configuration(FOUR_JOBS)
    for label, command, paths, expected in (
        ("a path within both levels", "a-mirrored-command",
         ["a-tree/one/a-file"], REACHED),
        ("a path within the workflow's filter and outside the job's",
         "a-mirrored-command", ["a-tree/two/a-file"], OUT_OF_SCOPE),
        ("a job stating no filter is bounded by the workflow's alone",
         "another-mirrored-command", ["a-tree/two/a-file"], REACHED),
    ):
        got = covers(jobs, command, A_PULL_REQUEST, "main", None, paths)
        check(f"{label} is {expected}", got["verdict"] == expected,
              f"answered {got['verdict']!r} -- {got['because']}")
    check(
        "a job's own id is what the answer names",
        covers(jobs, "a-mirrored-command", A_PULL_REQUEST, "main", None,
               ["a-tree/one/a-file"])["per_run"][0]["job"] == "a-job",
        "the answer did not name the job that mirrors the command",
    )

    print("\na pattern no consumer can parse")
    for label, entry in (
        ("a trigger written with no arrow",
         [{"workflow": "A workflow", "mirrors": "a-mirrored-command",
           "triggers": "pull_request"}]),
        ("a filter negating a glob",
         [{"workflow": "A workflow", "mirrors": "a-mirrored-command",
           "triggers": "pull_request -> *", "paths": ["!a-tree/**"]}]),
        # The same refusal one key over, which the filter plant above does not
        # reach: a trigger whose event parses and whose ref pattern does not.
        ("a trigger whose ref pattern is no glob this module reads",
         [{"workflow": "A workflow", "mirrors": "a-mirrored-command",
           "triggers": "pull_request -> release/[0-9]*"}]),
    ):
        got = covers(_a_configuration(entry), "a-mirrored-command",
                     A_PULL_REQUEST, "main", None, ["a-tree/a-file"])
        check(f"{label} is {UNREADABLE}", got["verdict"] == UNREADABLE,
              f"answered {got['verdict']!r} -- {got['because']}")

    print("\none entry whose own trigger list has more than one member")
    # ⛔ The finding this review reproduced: the same two triggers answered
    # `reached` across two entries and `unreadable` written as one entry's list,
    # so the module answered two ways about one configuration. Both shapes are
    # planted here, and the pair is the assertion rather than either alone.
    inside = _a_configuration([{
        "workflow": "A workflow",
        "mirrors": "a-mirrored-command",
        "triggers": ["pull_request -> *", "pull_request -> release/[0-9]*"],
    }])
    across = _a_configuration([
        {"workflow": "A workflow", "mirrors": "a-mirrored-command",
         "triggers": "pull_request -> *"},
        {"workflow": "Another workflow", "mirrors": "a-mirrored-command",
         "triggers": "pull_request -> release/[0-9]*"},
    ])
    answers = [
        covers(where, "a-mirrored-command", A_PULL_REQUEST, "main")["verdict"]
        for where in (inside, across)
    ]
    check(
        f"a trigger that fires beside one that cannot be read is {REACHED}",
        answers[0] == REACHED,
        f"answered {answers[0]!r}, so a sibling pattern nobody can parse unmade "
        "a run that fires",
    )
    check(
        "and the list and the two entries answer the same way",
        answers[0] == answers[1],
        f"answered {answers[0]!r} as one entry's list and {answers[1]!r} across "
        "two entries, which is two answers about one configuration",
    )
    typed_beside = _a_configuration([{
        "workflow": "A workflow",
        "mirrors": "a-mirrored-command",
        "triggers": ["pull_request -> *", "pull_request(edited) -> *"],
    }])
    got = covers(typed_beside, "a-mirrored-command", A_PULL_REQUEST, "main")
    check(
        f"a trigger with no clause beside a typed one is {REACHED}",
        got["verdict"] == REACHED,
        f"answered {got['verdict']!r} -- {got['because']}",
    )

    print("\na command two entries mirror")
    both = _a_configuration([
        {"workflow": "A workflow", "mirrors": "a-mirrored-command",
         "triggers": "pull_request -> a-release-branch"},
        {"workflow": "Another workflow", "mirrors": "a-mirrored-command",
         "triggers": "pull_request -> *"},
    ])
    got = covers(both, "a-mirrored-command", A_PULL_REQUEST, "main")
    check(
        f"is {REACHED} where either entry reaches the change",
        got["verdict"] == REACHED,
        f"answered {got['verdict']!r} on the strength of the entry written first",
    )
    check(
        "and both entries are reported, not only the one that decided it",
        len(got["per_run"]) == 2,
        "the answer named fewer runs than the facet states for this command",
    )

    print("\nthis project's own facet loads and answers")
    # ⚠️ The reader beside this file and never whichever one is first on the
    # path: a run from a worktree that imported the primary checkout's reader
    # would answer about a tree nobody is editing, and print a convincing
    # verdict doing it.
    check(
        "the reader this module read the facet through is the one beside it",
        os.path.dirname(os.path.abspath(config.__file__))
        == os.path.dirname(os.path.abspath(__file__)),
        f"imported {config.__file__}, which is not in this tree",
    )
    try:
        here = config.load(config.REPO_ROOT)
    except (ConfigError, OSError) as exc:
        here = None
        check("this repository's configuration loads", False, str(exc))
    if here is not None:
        check(
            "every entry of it states a command and a trigger this module reads",
            all(
                r["triggers"] is not None
                and all(config.parse_trigger(p) for p in (
                    r["triggers"] if isinstance(r["triggers"], list) else [r["triggers"]]
                ))
                for r in here.mirrors()
            ),
            "an entry of this repository's own facet is one this module cannot "
            "answer about, which is the state every consumer would report no "
            "answer from",
        )

    print()
    if failures:
        print(f"{len(failures)} check(s) failed:")
        for label in failures:
            print(f"  - {label}")
        return 1
    print("every check passed.")
    return 0


# --- the command line ------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="What the host's own runs answer about a command and a change.",
    )
    parser.add_argument("--skills-root", default=".")
    parser.add_argument("--self-test", action="store_true")
    sub = parser.add_subparsers(dest="what")

    named = sub.add_parser("mirrors", help="where the host's runs mirror a command")
    named.add_argument("--command", required=True)
    named.add_argument("--skills-root", default=".")

    reach = sub.add_parser("covers", help="which answer a change gets about a command")
    reach.add_argument("--command", required=True)
    # ⛔ No `choices` here: § 2 states the event vocabulary is the host's, so a
    # closed set in this parser would refuse a change whose event the host
    # really sends and the facet really names.
    reach.add_argument("--event", required=True,
                       help="the event that produced this change, as the host "
                            "and the facet both name it")
    reach.add_argument(
        "--ref", required=True,
        help="the ref this change is against -- its base branch under a pull "
             "request, and the branch pushed to under a push",
    )
    reach.add_argument(
        "--type", dest="kind",
        help="the type of that event, where the host sends one. Omitted, an "
             "entry that filters on types answers no answer rather than covered",
    )
    reach.add_argument("--path", action="append", default=[],
                       help="a path this change touches; repeatable")
    reach.add_argument("--skills-root", default=".")

    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    try:
        configuration = config.load(args.skills_root)
    except (ConfigError, OSError) as exc:
        print(exc, file=sys.stderr)
        return 2
    if args.what == "mirrors":
        answer = mirrors(configuration, args.command)
    elif args.what == "covers":
        answer = covers(
            configuration, args.command, args.event, args.ref, args.kind,
            args.path,
        )
    else:
        answer = facet(configuration)
    # ⚠️ Not escaped: every `because` cites a section by its sign, and a report
    # that printed the escape would send a reader looking for a section number
    # the surface does not have.
    print(json.dumps(answer, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
