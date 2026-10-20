#!/usr/bin/env python3
"""Hold a tier's run to the count the tree declares.

The rule is `plugins/mjolnir/config/schema.md § 16`, which states it and carries
the measurement behind it. Neither is restated here. ⛔ What this file performs:

  a run reporting **zero executed cases against a non-zero declaration is not a
  pass**, and the report names the dependency the skipped cases wanted -- from
  the configured preconditions and from the run's own skip reasons, or says the
  dependency is **unnamed** where neither states one;

  a **skip count carries what those cases wanted**, and one stating a count and
  nothing else is refused -- a skip nothing says anything about is a skip folded
  into a pass.

⛔ Every value is **read from the configuration**: the command that declares how
many cases the tree holds, the command that reports what a run executed and
skipped, the floor, and the preconditions. Nothing of any project is written in
this file, and no runner, task name or report format of any stack appears --
which is why the two commands are the project's own and this file only reads
their output.

⚠️ **It reads output and not exit status.** Whether the cases that executed
*passed* is the runner's verdict and not this one's, so a report naming failures
is read for its counts like any other. A command whose output this file cannot
read is a count it could not establish, which is reported as **unanswered** and
never as a pass or as a zero.

⚠️ **The commands run through a shell**, because § 16's contract is a command
ending in whatever turns a runner's output into the stated form, and that is a
pipeline. They are the project's own configuration read from the project's own
tree -- the same trust as the commands `host.checks` already states -- and not
text from outside the procedure.

What is deliberately not held is stated once, with the rule, in
docs/single-source-of-truth.md#a-tier-held-to-the-count-the-tree-declares.

Usage:
    executed.py                 hold this project's tier to its declaration
    executed.py --self-test     assert each check reddens on each planted
                                violation, stays green on each planted
                                exemption, and reads real commands, then stop
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import config as reader  # noqa: E402 -- the one reader of the surface

FACET = "executed"

# The two lines § 16 states, and the whole grammar. ⛔ Case-sensitive and
# anchored on purpose: a looser reading is a second grammar, and the surface
# states one. A skip's reason is optional *here* so that a line stating a count
# and nothing else is read and then refused by the check below -- dropping it at
# the parse would report the run unreadable, which names the wrong defect.
EXECUTED_LINE = re.compile(r"^executed\s+(?P<count>\d+)\s*$")
SKIPPED_LINE = re.compile(r"^skipped\s+(?P<count>\d+)(?:\s+(?P<wanted>.*))?$")


class Unreadable(RuntimeError):
    """A count this check needs could not be established.

    ⛔ Never a pass, and never a zero. Zero executed is the failure this facet
    names, so reading an unreadable count as zero would produce the right
    verdict by accident and the wrong one the moment the tier was healthy.
    """


# --- reading what the two commands print ------------------------------------


def declaration(text: str) -> int:
    """How many cases the tree holds, from the whole of a command's output.

    ⛔ The whole of it, stripped, and nothing looser. A reading that hunted for
    a number inside arbitrary output would judge against whichever one it found
    first, and the number a runner prints first is rarely the count.
    """
    stated = text.strip()
    if not re.fullmatch(r"\d+", stated):
        raise Unreadable(
            f"the declaration printed {stated[:80]!r}, which is not the one "
            "non-negative integer § 16 states. Nothing was judged: a count that "
            "could not be read is not a count of zero."
        )
    return _count(stated, "the declaration")


def _count(digits: str, what: str) -> int:
    """A matched run of digits as an integer, or a count nobody established.

    ⛔ The conversion is guarded rather than assumed: the interpreter refuses a
    digit string past a length limit of its own, so a grammar that matched and a
    conversion that raised would leave this file's one stated rule --
    unestablished counts are reported as unanswered -- answered by a traceback.
    Found by review on this change.
    """
    try:
        return int(digits)
    except ValueError as exc:
        raise Unreadable(
            f"{what} printed {len(digits)} digits, which is a count this "
            f"interpreter will not convert: {exc}. Nothing was judged."
        ) from exc


def report(text: str) -> tuple[int, list[tuple[int, str]]]:
    """What a run executed, and what it skipped, in the form § 16 states.

    Returns the executed count and one `(count, wanted)` pair per skip, the
    reason exactly as the run stated it -- blank where it stated none, which the
    check below is what refuses.

    ⛔ A non-blank line this grammar cannot read is refused rather than skipped.
    That is the only available direction: a line nobody can parse may be the
    count itself, and a run that ignored it would judge against a number it
    never read.
    """
    executed: int | None = None
    skips: list[tuple[int, str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        found = EXECUTED_LINE.match(stripped)
        if found:
            if executed is not None:
                raise Unreadable(
                    "the report states `executed` more than once, so which "
                    "count the run means is undecided. § 16 states the line "
                    "exactly once."
                )
            executed = _count(found.group("count"), "the report's executed line")
            continue
        found = SKIPPED_LINE.match(stripped)
        if found:
            skips.append(
                (
                    _count(found.group("count"), "a skip line of the report"),
                    (found.group("wanted") or "").strip(),
                )
            )
            continue
        raise Unreadable(
            f"the report states {stripped[:80]!r}, which § 16's grammar cannot "
            "read. A line nothing can parse may be the count, so nothing was "
            "judged."
        )
    if executed is None:
        raise Unreadable(
            "the report states no `executed` line, so what the run executed was "
            "never stated. ⛔ Not read as zero: zero executed is the failure this "
            "facet names, and an absent count is not a signal."
        )
    return executed, skips


# --- the subject ------------------------------------------------------------


class Subject:
    """One tier's declaration and one run's report, with the facet's own keys.

    Held as data so the plants below are a subject each rather than a project
    each. ⚠️ The in-memory half reaches every branch of the rule and **none** of
    the command-running, which is why the suite also runs real commands.
    """

    def __init__(
        self,
        facet: dict,
        declared: int,
        executed: int,
        skips: list[tuple[int, str]] | None = None,
        where: str | None = None,
    ):
        self.facet = facet
        self.declared = declared
        self.executed = executed
        self.skips = list(skips or [])
        # The tree the two commands ran in, where they ran at all. `None` for a
        # subject built in memory, which is a subject no tree produced -- and a
        # report naming a tree it never ran in would be the wrong-tree claim one
        # level down from the rule it exists to keep.
        self.where = where

    def copy(self) -> "Subject":
        return Subject(
            dict(self.facet), self.declared, self.executed, list(self.skips), self.where
        )

    @property
    def floor(self):
        return self.facet.get("min")

    @property
    def requires(self) -> list[str]:
        return list(self.facet.get("requires") or [])

    @property
    def skipped(self) -> int:
        return sum(count for count, _ in self.skips)

    def wanted(self) -> list[str]:
        """What the skipped cases wanted, from the configuration and the run.

        Both sources, in that order, because they answer differently: the
        configuration states what the cases need at all, and the run states what
        this run found missing. ⛔ Neither is read as the other's absence.
        """
        out = list(self.requires)
        for _, reason in self.skips:
            # ⚠️ Appended one at a time on purpose. A comprehension tests `not in`
            # against the list as it stood before the whole of it was added, so it
            # de-duplicates against `requires` and never among the skips -- and a
            # verdict then names one dependency once per line that wanted it.
            # Found by review on this change.
            if reason and reason not in out:
                out.append(reason)
        return out


def read_command(command: str, root: str, what: str) -> str:
    """Run one of the project's configured commands and return its output.

    ⛔ A command that could not be run at all is `Unreadable` rather than a
    verdict, by the rule in this file's docstring: the exit status is the
    runner's business, but a command that never produced output is a count
    nobody established.

    ⚠️ **Decoding replaces rather than raises.** A runner emitting one byte that
    is not text would otherwise answer this file's own rule with a traceback,
    and the mangled text is then refused by the grammar -- which is the right
    answer and the stated one. Found by review on this change.

    ⚠️ **No time bound is set here, and that is stated rather than discovered.**
    `reports` is frequently the tier's own run, which legitimately takes as long
    as the tier takes, so any number this toolkit picked would be wrong for some
    project and would redden a healthy tier. ⛔ What is bounded is the *handling*:
    a bound imposed from outside -- the runner's own job limit, or a caller
    passing one -- is reported as a count nobody established rather than as a
    zero. A configured bound would be a key on the surface, which § 16 does not
    state.
    """
    try:
        done = subprocess.run(
            command,
            shell=True,
            cwd=root,
            capture_output=True,
            text=True,
            errors="replace",
            check=False,
        )
    except OSError as exc:  # the shell itself was unavailable, or the root is gone
        raise Unreadable(f"the {what} command could not be run: {exc}") from exc
    except subprocess.TimeoutExpired as exc:
        raise Unreadable(
            f"the {what} command did not finish within the bound it was given "
            f"({exc.timeout}s). Nothing was judged: a count that could not be "
            "read is not a count of zero."
        ) from exc
    if not done.stdout.strip():
        raise Unreadable(
            f"the {what} command printed nothing"
            + (f", and said: {done.stderr.strip()[:120]}" if done.stderr.strip() else "")
            + ". Nothing was judged."
        )
    return done.stdout


def read_subject(root: str, facet: dict) -> Subject:
    declared = declaration(read_command(facet["declares"], root, "declaration"))
    executed, skips = report(read_command(facet["reports"], root, "report"))
    return Subject(
        facet=facet, declared=declared, executed=executed, skips=skips, where=root
    )


# --- the checks -------------------------------------------------------------


def check_the_run_executed_what_the_tree_declares(subject: Subject) -> list[str]:
    """§ 16's rule: zero executed against a non-zero declaration is not a pass.

    ⛔ Three conditions, and each one of them is the configuration's rather than
    this check's: a floor is stated, the tree declares cases, and fewer than the
    floor executed. A facet with no floor is the weaker configuration § 16
    states -- the counts reported and nothing judged -- and is not a failure.
    """
    floor = subject.floor
    if floor is None or subject.declared == 0 or subject.executed >= floor:
        return []
    wanted = subject.wanted()
    named = "; ".join(wanted) if wanted else (
        "**unnamed** — the facet states no `requires:` and the run's report "
        "named no skip, so what the cases wanted is not written anywhere"
    )
    return [
        f"{subject.executed} of {subject.declared} declared case(s) executed, which is "
        f"below the floor of {floor}: this run proved nothing about the tier and is not a "
        f"pass (§ 16). What the cases wanted: {named}."
    ]


def check_every_skip_says_what_it_wanted(subject: Subject) -> list[str]:
    """A skip count carries what those cases wanted, or it is refused.

    ⚠️ Per skip rather than once, so a report with two reasonless lines says so
    twice: each is a separate count nothing accounts for.

    ⛔ **A count of zero is not a skip**, and a line stating one is not refused
    for saying nothing about it. § 16's reason for the refusal is that a skip
    count with nothing saying what it was is a skip folded into a pass, and at
    zero there is nothing folded into anything -- so refusing it would redden a
    tier in which every declared case executed, on a report generator that emits
    the line unconditionally, with a message that is false as written. Found by
    review on this change; the plant for it is below.
    """
    return [
        f"a skip of {count} case(s) states no reason, so that count is a skip folded into "
        "a pass (§ 16). The line states a count and what those cases wanted."
        for count, reason in subject.skips
        if count and not reason
    ]


CHECKS = [
    ("the run executed what the tree declares", check_the_run_executed_what_the_tree_declares),
    ("every skip says what it wanted", check_every_skip_says_what_it_wanted),
]


# --- what the run reports rather than judges --------------------------------
#
# ⛔ None of this is a verdict. § 16 judges one thing and reports every other
# number, which is the line #91 draws for a measurement that reddens on nothing
# it cannot derive -- so each figure below is printed and held to nothing.


def reported(subject: Subject) -> list[str]:
    out = []
    # ⛔ Which tree answered, and with which commands, first.
    # [§ 10](../config/schema.md#which-tree-a-verdict-belongs-to) requires a run
    # to state the tree its verdict belongs to, and this is the first carrier
    # here to run a *project's* command rather than a git call -- so a command
    # talking to a service bound to another tree's stack would otherwise answer
    # about code this branch does not contain, in the direction that passes, with
    # nothing in the output to tell a reader which tree it was. Found by review
    # on this change.
    if subject.where:
        out.append(f"the tree this verdict belongs to: `{subject.where}`")
    out.append(
        f"declared by `{subject.facet.get('declares')}`; "
        f"reported by `{subject.facet.get('reports')}`"
    )
    out.append(
        f"declared: {subject.declared} case(s); executed: {subject.executed}; "
        f"skipped: {subject.skipped}."
    )
    for count, reason in subject.skips:
        out.append(f"skipped {count}: {reason[:110] if reason else '(no reason stated)'}")
    if subject.floor is None:
        out.append(
            "no `min` is stated, so these counts are reported and nothing is judged from "
            "them — the weaker configuration § 16 states, and a real one."
        )
    if subject.declared == 0:
        out.append(
            "the tree declares no case, so there is nothing for this rule to judge: the "
            "failure it names is zero executed against a **non-zero** declaration."
        )
        if subject.executed == 0:
            # ⛔ The hole in the rule's own premise, named in the output rather
            # than left for an adopter to discover: the two commands are equally
            # fragile over the same tree, so a shared degradation that makes the
            # declaration print zero disarms the rule and this run reports green.
            # Found by review on this change, and named rather than closed —
            # closing it would redden every project that genuinely has no case.
            out.append(
                "⛔ and nothing executed either, which reads identically to a declaration "
                "command that itself degraded: this rule is disarmed by a zero declaration, "
                "so a reader checks that the declaration is the tree's and not the failure's."
            )
    if subject.executed > subject.declared:
        out.append(
            f"more executed ({subject.executed}) than declared ({subject.declared}), so the "
            "two commands disagree about what the tree holds. Reported rather than judged."
        )
    if subject.declared and subject.executed + subject.skipped != subject.declared:
        # The one identity the two commands can be cross-checked on, computed
        # because nothing else here computes it. ⛔ Reported and not judged: a
        # tier whose cases are counted differently by its two commands is a
        # configuration this facet has no verdict about.
        out.append(
            f"executed ({subject.executed}) plus skipped ({subject.skipped}) is not the "
            f"declaration ({subject.declared}), so some declared case is accounted for by "
            "neither. Reported rather than judged."
        )
    for precondition in subject.requires:
        out.append(f"the cases need: {precondition[:110]}")
    out.append(
        "whether the cases that executed *passed* is the runner's verdict and not this "
        "one's: this run reads counts and never an exit status."
    )
    return out


def run(subject: Subject) -> dict[str, list[str]]:
    return {name: check(subject) for name, check in CHECKS}


# --- the planted violations -------------------------------------------------
#
# ⛔ One per branch that does real work, against a subject this file builds
# itself. No plant names a project, and no plant writes into the checkout it
# runs in.


def _a_subject() -> Subject:
    """A tier that executed every case it declared, with a reasoned skip.

    The baseline every plant below is measured against. ⚠️ Its own premises are
    asserted before any plant runs: a fixture already failing would make every
    red below prove nothing, and one carrying no floor would make the rule's own
    plant pass for the wrong reason.
    """
    facet = {
        "carrier": "command",
        "declares": "a-command-printing-a-count",
        "reports": "a-command-printing-a-run",
        "min": 1,
        "requires": ["a store the run creates for itself"],
    }
    return Subject(facet=facet, declared=4, executed=3, skips=[(1, "a reader nothing has")])


def _executed_nothing(subject: Subject) -> Subject:
    """The rule's own violation: the tier degraded to nothing and exited zero."""
    subject.executed = 0
    subject.skips = [(4, "a store the run never created")]
    return subject


def _executed_nothing_with_nothing_named(subject: Subject) -> Subject:
    """The same failure with no dependency written anywhere.

    ⛔ A separate plant rather than a variant of the one above, because the
    branch it reaches is the one that has to say **unnamed**: a verdict reporting
    only *zero* leaves whoever reads it to guess what the tier wanted, and a
    fixture that always carries `requires:` would never exercise it.
    """
    subject.facet.pop("requires", None)
    subject.executed = 0
    subject.skips = []
    return subject


def _a_skip_with_no_reason(subject: Subject) -> Subject:
    subject.skips = [(1, "a reader nothing has"), (2, "")]
    return subject


VIOLATIONS = [
    ("the run executed what the tree declares",
     "a tier that executed nothing against a non-zero declaration", _executed_nothing),
    ("the run executed what the tree declares",
     "the same, with no precondition and no skip reason to name",
     _executed_nothing_with_nothing_named),
    ("every skip says what it wanted",
     "a skip stating a count and nothing else", _a_skip_with_no_reason),
]


# --- the planted exemptions -------------------------------------------------
#
# ⛔ One per hole in the scope, each of which is a decision § 16 states rather
# than a gap. A red-only suite says nothing about any of them.
#
# ⚠️ **Two kinds, kept apart in the labels.** An *exclusion* is a guard in the
# rule above that carves the case out, and it is verified by switching that guard
# off and watching the plant redden -- performed, and recorded with the check.
# A *narrowness* plant has no guard to switch off: nothing was written to let the
# case through, and what the plant asserts is that the rule never grew an arm
# that would catch it. ⛔ Calling the second kind a verified exclusion would
# claim a step nobody performed.


def _no_floor_stated(subject: Subject) -> Subject:
    """The weaker configuration: zero executed, and nothing judged from it."""
    subject.facet.pop("min", None)
    subject.executed = 0
    subject.skips = [(4, "a store the run never created")]
    return subject


def _a_tree_declaring_nothing(subject: Subject) -> Subject:
    """A declaration of zero, which the rule is defined against."""
    subject.declared = 0
    subject.executed = 0
    subject.skips = []
    return subject


def _more_executed_than_declared(subject: Subject) -> Subject:
    """Two commands disagreeing, which is reported and not judged."""
    subject.executed = subject.declared + 2
    return subject


def _every_case_executed(subject: Subject) -> Subject:
    subject.executed = subject.declared
    subject.skips = []
    return subject


def _a_reasonless_skip_of_nothing(subject: Subject) -> Subject:
    """A healthy tier whose report emits `skipped 0` with nothing after it.

    ⛔ An exclusion, with a guard of its own in the skip check. The shape is what
    a generated report does unconditionally, and refusing it reddened a tier in
    which every declared case executed -- which is what this plant exists to
    keep from coming back.
    """
    subject.executed = subject.declared
    subject.skips = [(0, "")]
    return subject


EXEMPTIONS = [
    ("exclusion: no floor stated, so zero executed is reported and not judged",
     _no_floor_stated),
    ("exclusion: a tree declaring no case at all", _a_tree_declaring_nothing),
    ("exclusion: a reasonless skip of zero cases, which folds nothing into anything",
     _a_reasonless_skip_of_nothing),
    ("narrowness: more executed than declared, which the two commands disagree about",
     _more_executed_than_declared),
    ("narrowness: every declared case executed, and nothing skipped", _every_case_executed),
]


# --- what the report has to say, per state ----------------------------------
#
# ⛔ The reporting half is asserted here because nothing else asserted it: with
# `reported()` replaced by a function returning nothing, every plant above still
# passed and the suite was green -- measured by review on this change. Two of the
# green plants above are *labelled* for report branches, and a plant that asserts
# only that nothing reddened says nothing about what the run then said.
#
# Each entry is (the state, the plant, a phrase the report must carry).
REPORTED = [
    ("an unset floor says the counts are judged by nothing",
     _no_floor_stated, "nothing is judged from"),
    ("a zero declaration says the rule has nothing to judge",
     _a_tree_declaring_nothing, "nothing for this rule to judge"),
    ("and names that a degraded declaration reads the same way",
     _a_tree_declaring_nothing, "reads identically to a declaration"),
    ("more executed than declared says the two commands disagree",
     _more_executed_than_declared, "disagree about what the tree holds"),
    ("counts that do not add up to the declaration are reported",
     _a_skip_with_no_reason, "accounted for by neither"),
    ("a reasoned skip is reported with its reason",
     _every_case_executed, "declared: 4 case(s)"),
    ("a configured precondition is reported whether or not the floor was missed",
     _every_case_executed, "the cases need:"),
    ("and every run says the exit status is not what it read",
     _every_case_executed, "never an exit status"),
]


# --- what the grammar refuses rather than judges ----------------------------
#
# ⛔ Each of these is a count that could not be established, which is reported as
# unanswered. They are asserted as refusals rather than as planted violations
# because none of them reaches a check at all: the subject is never built.

UNREADABLE_DECLARATIONS = [
    ("output that is not a number", "a few"),
    ("a number with a runner's own output around it", "ran 3 files\n4\n"),
    ("nothing at all", "   "),
    ("a signed count, which the grammar does not state", "-1"),
    # ⛔ The grammar matches and the conversion refuses. Planted because the
    # interpreter's own digit limit is a route from *matched* to *traceback*,
    # which would answer this file's rule about unestablished counts with a
    # stack trace. Found by review on this change.
    ("more digits than the interpreter converts", "9" * 5000),
]

UNREADABLE_REPORTS = [
    ("no executed line", "skipped 2 a store nothing created"),
    ("two executed lines", "executed 3\nexecuted 4"),
    ("a line the grammar cannot read", "executed 3\nall good"),
    ("a skip count that is not a number", "executed 3\nskipped some a store"),
    ("a count stated in another case", "EXECUTED 3"),
]


# --- the suite --------------------------------------------------------------


def _two_commands(where: str) -> tuple[str, dict]:
    """A directory holding a declaration and a report, as real commands.

    ⚠️ The half the in-memory plants cannot reach: a configured command is a
    string run through a shell in a working directory, and every assertion above
    is about a subject that was already built. ⛔ Written as files in a temporary
    directory rather than as literals, because the branch under test is the
    running and the reading, not the strings.

    ⚠️ **The seam these stand at, named rather than assumed**
    ([§ The loop](../config/schema.md#what-earns-a-test-and-what-makes-its-red-believable)):
    a command string, a working directory, and the bytes it printed on standard
    output. ⛔ They are a **fake and not a mock** -- real commands answering as
    the thing they replace, which is a project's own command, so a change to how
    the carrier runs or reads one fails here rather than passing on an
    expectation nobody re-examined. ⚠️ And the facet is the **whole** facet,
    `requires:` included: a fixture carrying only the keys this arm's assertions
    read would leave the verdict's naming of the dependency exercised nowhere
    but in memory, which is a fixture testing itself.
    """
    root = os.path.join(where, "a-tree")
    os.makedirs(root)
    with open(os.path.join(root, "declare"), "w", encoding="utf-8") as handle:
        handle.write("#!/bin/sh\necho 4\n")
    with open(os.path.join(root, "report"), "w", encoding="utf-8") as handle:
        # A trailing pipeline, which is the shape § 16's contract asks a project
        # for and the reason these run through a shell at all.
        handle.write("#!/bin/sh\necho 'executed 3'\necho 'skipped 1 a reader nothing has'\n")
    for name in ("declare", "report"):
        os.chmod(os.path.join(root, name), 0o755)
    facet = {
        "carrier": "command",
        "declares": "./declare",
        "reports": "./report | cat",
        "min": 1,
        "requires": ["a store the run creates for itself"],
    }
    return root, facet


def self_test() -> int:
    subject = _a_subject()
    by_name = dict(CHECKS)
    failures = 0

    def check(label: str, condition: bool, detail: str = "") -> None:
        nonlocal failures
        if condition:
            print(f"  ok                     {label}")
        else:
            failures += 1
            print(f"  FAIL                   {label}{': ' + detail if detail else ''}")

    # ⛔ The fixture's own premises first. A plant measured against a baseline
    # that is already red proves nothing; a fixture with no floor would make the
    # rule's plant pass because nothing is judged rather than because it
    # reddened; and a fixture declaring no case would make it pass vacuously for
    # the same kind of reason.
    baseline = {name: set(found) for name, found in run(subject).items()}
    check("the fixture starts green", not any(baseline.values()), f"{baseline}")
    check("the fixture states a floor, so the rule has something to judge",
          subject.floor is not None)
    check("the fixture's tree declares cases", subject.declared > 0)
    check("the fixture's run skipped something, with a reason", bool(subject.skips))

    for name, label, plant in VIOLATIONS:
        if set(by_name[name](plant(subject.copy()))) - baseline[name]:
            print(f"  red on                 {name}: {label}")
        else:
            print(f"  STAYED GREEN           {name}: {label}")
            failures += 1

    for label, plant in EXEMPTIONS:
        planted = plant(subject.copy())
        added = {
            problem
            for name, found in run(planted).items()
            for problem in set(found) - baseline[name]
        }
        if added:
            print(f"  WENT RED               exempt: {label} — {sorted(added)[0][:90]}")
            failures += 1
        else:
            print(f"  green on               exempt: {label}")

    # ⛔ The reporting half, which no plant above reaches: each state against a
    # phrase the report has to carry. Without these, `reported()` could return
    # nothing at all and every assertion in this file would still hold.
    for label, plant, phrase in REPORTED:
        lines = reported(plant(subject.copy()))
        check(
            f"report: {label}",
            any(phrase in line for line in lines),
            f"no line carried {phrase!r}; said {lines}",
        )
    # And the other direction for the one branch whose absence is the finding:
    # a run with a floor stated must **not** say the counts are judged by nothing.
    check(
        "report: a stated floor does not say the counts are judged by nothing",
        not any("nothing is judged from" in line for line in reported(subject.copy())),
    )

    # The verdict that misses the floor names what the cases wanted, in both
    # directions: from the configuration and the run, and **unnamed** where
    # neither says. ⚠️ And one dependency is named once however many skip lines
    # wanted it. ⛔ Asserted on the message rather than on the red, because the
    # red is the same either way and the naming is half of what § 16 asks for.
    stated = check_the_run_executed_what_the_tree_declares(_executed_nothing(subject.copy()))
    check(
        "the verdict names the dependency from the configuration and the run",
        bool(stated)
        and "a store the run creates for itself" in stated[0]
        and "a store the run never created" in stated[0],
        f"said {stated}",
    )
    unnamed = check_the_run_executed_what_the_tree_declares(
        _executed_nothing_with_nothing_named(subject.copy())
    )
    check(
        "and says the dependency is unnamed where nothing states one",
        bool(unnamed) and "unnamed" in unnamed[0],
        f"said {unnamed}",
    )

    # The grammar, from the side that is never a verdict.
    for label, text in UNREADABLE_DECLARATIONS:
        try:
            got = declaration(text)
            check(f"a declaration of {label} is refused", False, f"read {got!r}")
        except Unreadable:
            print(f"  refused                a declaration of {label}")
    for label, text in UNREADABLE_REPORTS:
        try:
            got = report(text)
            check(f"a report with {label} is refused", False, f"read {got!r}")
        except Unreadable:
            print(f"  refused                a report with {label}")

    # And the green side of the grammar, so the refusals above are a grammar
    # doing work rather than one that rejects everything.
    check("a declaration of a bare count is read", declaration("  12\n") == 12)
    check(
        "a report of an executed line and two reasoned skips is read",
        report("executed 7\nskipped 1 a store\n\nskipped 2 a reader") == (
            7, [(1, "a store"), (2, "a reader")]
        ),
    )
    check(
        "a skip stating a count and nothing else is read, and refused by the check",
        report("executed 7\nskipped 2") == (7, [(2, "")]),
    )

    # The commands, run for real. ⛔ Everything above is a subject that was
    # already built; this is the only arm that reaches the running of a
    # configured command, the working directory it runs in, and the reading of
    # what it printed.
    with tempfile.TemporaryDirectory() as where:
        root, facet = _two_commands(where)
        live = read_subject(root, facet)
        check(
            "two real commands are run and read, the pipeline included",
            (live.declared, live.executed, live.skips) == (4, 3, [(1, "a reader nothing has")]),
            f"read {live.declared}, {live.executed}, {live.skips}",
        )
        check("and that run is green", not any(run(live).values()), f"{run(live)}")
        # The same two commands with the report replaced by one that executes
        # nothing, which is the incident this facet exists for -- reaching it
        # through the commands rather than through a subject.
        with open(os.path.join(root, "report"), "w", encoding="utf-8") as handle:
            handle.write("#!/bin/sh\necho 'executed 0'\necho 'skipped 4 a store nothing created'\n")
        degraded = read_subject(root, facet)
        found = run(degraded)
        check(
            "a real run that executed nothing reddens the rule",
            bool(found["the run executed what the tree declares"]),
            f"{found}",
        )
        # ⛔ And the verdict names the dependency **through the commands**, from
        # the configured precondition and from the reason the command printed.
        # Asserted here as well as in memory because it is half of what § 16 asks
        # of a missed floor, and an arm that only reddened would pass with the
        # naming gone.
        said = found["the run executed what the tree declares"][0]
        check(
            "and that verdict names the dependency, from the facet and from the command",
            "a store the run creates for itself" in said
            and "a store nothing created" in said,
            f"said {said!r}",
        )
        # ⛔ And a command that prints nothing is the state no fixture above
        # reproduces: the tier was never asked, and that is not a zero.
        with open(os.path.join(root, "report"), "w", encoding="utf-8") as handle:
            handle.write("#!/bin/sh\nexit 1\n")
        try:
            read_subject(root, facet)
            refused = None
        except Unreadable as exc:
            refused = str(exc)
        check(
            "a command that printed nothing is refused, not read as zero executed",
            refused is not None and "Nothing was judged" in refused,
            f"reported {refused!r}",
        )

    if failures:
        print(
            f"\n{failures} assertion(s) did not hold. A check that cannot fail is not a "
            "check, and an exemption that cannot pass is not an exemption."
        )
    return 1 if failures else 0


# --- entry point ------------------------------------------------------------


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Hold a tier's run to the count the tree declares.",
    )
    parser.add_argument(
        "--skills-root",
        default=".",
        help="the root the configuration is resolved relative to (§ 1)",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="assert each check reddens on its planted violations, stays green on each "
        "planted exemption, and reads real commands, then stop",
    )
    args = parser.parse_args(argv)

    if args.self_test:
        print(
            "Asserting the checks redden on each planted violation "
            f"({len(VIOLATIONS)}), stay green on each planted exemption "
            f"({len(EXEMPTIONS)}), and run two real commands:"
        )
        return self_test()

    try:
        config = reader.load(args.skills_root)
    except reader.ConfigError as error:
        print(str(error), file=sys.stderr)
        return 1

    facet = config.get(FACET) or {}
    if facet.get("carrier") != "command":
        # ⛔ Not a verdict, and ⛔ not a count of zero. A project with no tier
        # whose dependency a run stands up has no subject here, and § 16 states
        # that the count is **unavailable** rather than nothing-was-skipped.
        print(
            f"`{FACET}.carrier` is {facet.get('carrier')!r}, so what a run here executed is "
            "**unavailable** rather than zero, and this check has no subject. A project in "
            "that position runs no such check: delete the entry from `host.checks`, or state "
            f"the facet. What it decided instead: "
            f"{' '.join(str(facet.get('absent_reason')).split())}",
            file=sys.stderr,
        )
        return 2

    root = config.code_root
    try:
        subject = read_subject(root, facet)
    except Unreadable as exc:
        print(f"nothing could be judged: {exc}", file=sys.stderr)
        return 1

    results = run(subject)
    for name, found in results.items():
        print(f"  {'FAIL' if found else 'ok  '}  {name}")
    print("\nWhat this run reports rather than judges:")
    for line in reported(subject):
        print(f"  - {line}")

    problems = [problem for found in results.values() for problem in found]
    if problems:
        print(f"\n{len(problems)} problem(s):\n")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    # ⛔ A run that judged nothing does not print a pass. With no floor stated
    # there is no verdict about what executed, so the sentence a reader takes
    # away says what was read and what was *not* judged — and says it loudest in
    # the state the facet exists for, a tier that executed nothing. Found by
    # review on this change: the pass sentence read
    # "0 of 120 declared case(s) executed, and every skip states what those
    # cases wanted", which is the incident reported as success in prose.
    if subject.floor is None:
        print(
            f"\n{subject.executed} of {subject.declared} declared case(s) executed. ⛔ Nothing "
            "was judged: this facet states no `min`, so no floor was asked of this run. "
            + (
                "⚠️ And nothing executed, which is the failure § 16 names — unjudged here only "
                "because no floor is stated."
                if subject.declared and not subject.executed
                else "Every skip states what those cases wanted."
            )
        )
        return 0
    print(
        f"\n{subject.executed} of {subject.declared} declared case(s) executed, which met the "
        f"floor of {subject.floor}, and every skip states what those cases wanted."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
