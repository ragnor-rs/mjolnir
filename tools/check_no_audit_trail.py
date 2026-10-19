#!/usr/bin/env python3
"""Hold the prose this change writes to the rule that an artifact states what is true now.

The rule is `plugins/mjolnir/config/schema.md § The loop -> An artifact states
what is true now`: no artifact a role writes carries a record of the pass that
wrote it unless the person running the role asks for one. A stale line is
replaced rather than annotated beside its replacement, and what a pass did goes
in the reply, which is read once and kept nowhere.

Measured on the one artifact that had the habit: the ordering document this
repository plans with had accumulated seven dated revalidation paragraphs, 70 of
its 469 lines, each stating one pass's figures and what it had corrected. Every
figure in them was stale and every standing fact in them was already argued in a
row. That is the cost shape -- a role that runs often writes a document that
grows monotonically and is read less the longer it gets.

⛔ **Only the lines this change adds are read**, which is the rule's own
carve-out rather than a convenience: existing artifacts stand as they are, and
rewrapping the past would repaint every document in the tree. The post-image
line numbers come from a diff against the merge base, so a refusal names the
file and the line a reader can open.

What is in scope: tracked markdown, including table rows -- a row's `why` column
is exactly where the measured habit lived. What is out of scope, and why, is
stated once in
docs/single-source-of-truth.md#an-artifact-states-what-is-true-now-held-on-the-lines-a-change-adds.

⚠️ **The forbidden shapes are lexical, and this is a forbidding check rather
than a computed one.** A record phrased without any of the markers below passes.
The run says so in its own output rather than implying completeness, because a
green run on a document that narrates its own history would otherwise read as
coverage. Two of the four words the rule names -- `was` and `corrected` -- are
held only in compound forms (`(was 7)`, `Was:`, `this pass corrected`), because
bare prose uses both constantly and a sweep for them hands back a change over
the honest form of a sentence.

Usage:
    check_no_audit_trail.py              hold the lines this change adds
    check_no_audit_trail.py --self-test  assert each check reddens on each of its
                                         planted violations and stays green on
                                         each planted exemption, then hold the
                                         change
"""

from __future__ import annotations

import os
import re
import subprocess
import sys

# --- the grammar -----------------------------------------------------------
#
# Form, not content. Each of these is a shape a line has, and none is a fact
# about this project.

# A date, in the two spellings this repository's documents use.
MONTHS = (
    "January|February|March|April|May|June|July|August|September|October|November|December"
)
DATE = r"(?:\d{4}-\d{2}-\d{2}|\b(?:" + MONTHS + r")\s+\d{1,2},?\s+\d{4}\b)"

# What makes a dated line a record of a *pass* rather than a dated fact. ⛔ The
# vocabulary is deliberately the document-pass one: `landed`, `measured`,
# `ruled` and `merged` are absent, because a line stating that an item landed on
# a date, or that something was measured on one, states something still true --
# which is the rule's sixth point and the distinction this whole check turns on.
PASS_WORD = (
    r"(?:pass|passes|revalidat\w+|re-?read|re-?check\w*|re-?deriv\w+|re-?stamp\w*|"
    r"stamped|swept|sweep|audit|audited|corrected|re-?counted|recount\w*|refreshed)"
)

DATED_PASS = re.compile(DATE + r".{0,120}?\b" + PASS_WORD + r"\b|\b" + PASS_WORD
                        + r"\b.{0,120}?" + DATE, re.I)

# A heading carrying a date. ⚠️ Held with no pass word required, unlike the line
# arm above: a section of a document headed by a date is a per-pass section
# whatever its verb, and that is the shape the measured 70 lines took.
HEADING = re.compile(r"^\s{0,3}#{1,6}\s+(?P<text>.*)$")
DATED_HEADING = re.compile(DATE)

# A figure stated beside its former value. ⚠️ A closed list, and the weakness is
# in the safe direction: a reworded former value passes and leaves a finding
# missed, which the person reading the diff can still raise, where a broader
# grammar hands back a change over a sentence like *the divergence was 71 lines*
# -- a measurement, not an annotation.
FORMER_VALUE = re.compile(
    r"\(\s*was\s+[^)]{1,60}\)"
    r"|^\s*(?:[-*+]\s+)?(?:\*\*)?was\s*:"
    r"|\b(?:down|up)\s+from\s+\d"
    r"|\bformerly\s+\d"
    r"|\bpreviously\s+\d"
    r"|\bwas\s+\d[\d,.]*\s+(?:lines?|items?|paragraphs?|columns?|rows?|of\s+them)\b",
    re.I,
)

# A clause whose subject is a previous pass. `previously` is here bare, as one
# of the four forms the rule names: a sentence reaching for it is narrating a
# former state, and rewriting it costs a clause.
PREVIOUS_PASS = re.compile(
    r"\bpreviously\b"
    r"|\bthis (?:pass|run) (?:corrected|found|re-?derived|rewrote|replaced|fixed|updated)\b"
    r"|\b(?:a|an|the) (?:previous|earlier|last|prior) pass\b"
    r"|\bre-?derived rather than recalled\b"
    r"|\bas of (?:this|the last) pass\b"
    r"|\bused to (?:say|state|read)\b"
    r"|\bhas since been (?:corrected|replaced|updated|rewritten)\b"
    r"|\bno longer (?:says|states|reads)\b"
    r"|\bcorrected (?:in|on|during) (?:this|the last|a previous)\b",
    re.I,
)

# What is set aside before a line is read. A marker *shown* is not a marker
# *used*: this file's own rule has to spell out every form it forbids, and so
# does the section of the surface that states it. An inline-code span and a
# double-quoted run are the two ways this repository shows one.
CODE_SPAN = re.compile(r"`[^`\n]+`")
QUOTED = re.compile(r"[\"«][^\"»\n]{1,80}[\"»]")

FENCE = re.compile(r"^\s*(?:```|~~~)")
FRONTMATTER = "---"

# The diff this check reads: post-image line numbers, so a refusal names a line
# somebody can open.
HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(?P<start>\d+)(?:,(?P<count>\d+))? @@")
FILE_HEADER = re.compile(r"^\+\+\+ b/(?P<path>.*)$")

SELF = "tools/" + os.path.basename(__file__)


def shown_only(line: str) -> str:
    """The line with every shown marker set aside."""
    return QUOTED.sub("x", CODE_SPAN.sub("x", line))


def prose_lines(text: str) -> set[int]:
    """The 1-indexed lines of a document that are prose a reader reads.

    Fenced blocks and the document's own frontmatter are out: a fence shows
    what a rule forbids, and frontmatter is metadata. ⛔ Table rows are **in**,
    because a row's argument column is where the measured habit lived -- which
    is the one exclusion a sweep of this kind would reach for and must not take.
    """
    lines = text.splitlines()
    in_frontmatter = (
        bool(lines)
        and lines[0].strip() == FRONTMATTER
        and any(line.strip() == FRONTMATTER for line in lines[1:])
    )
    out: set[int] = set()
    fenced = False
    for number, line in enumerate(lines, 1):
        if in_frontmatter:
            if number > 1 and line.strip() == FRONTMATTER:
                in_frontmatter = False
            continue
        if FENCE.match(line):
            fenced = not fenced
            continue
        if fenced:
            continue
        out.add(number)
    return out


class Unreadable(Exception):
    """The change could not be read at all, which is not a verdict about it."""


class Change:
    """The markdown this change adds, in memory, so a violation can be planted.

    `text` is each touched document's post-image, `added` the post-image line
    numbers the change writes. The two are kept apart on purpose: the rule holds
    the lines a change adds and the file supplies the context -- whether a line
    sits in a fence cannot be read off the diff.
    """

    def __init__(self, base: str, text: dict[str, str],
                 added: dict[str, set[int]], unread: list[str] | None = None):
        self.base = base
        self.text = text
        self.added = added
        self.unread = list(unread or [])

    def copy(self) -> "Change":
        return Change(
            self.base,
            dict(self.text),
            {path: set(numbers) for path, numbers in self.added.items()},
            list(self.unread),
        )

    def plant(self, line: str, path: str | None = None) -> "Change":
        """Append a line to a document and mark it as added by this change."""
        path = path or self._a_document()
        text = self.text.get(path, "# Planted\n")
        self.text[path] = text + line + "\n"
        self.added.setdefault(path, set()).add(len(self.text[path].splitlines()))
        return self

    def carry(self, line: str, path: str | None = None) -> "Change":
        """Append a line to a document and leave it **unadded**.

        The green side of the rule's own carve-out: a line the change did not
        write is somebody else's history and not this merge's business.
        """
        path = path or self._a_document()
        self.text[path] = self.text.get(path, "# Planted\n") + line + "\n"
        return self

    def _a_document(self) -> str:
        """Whichever document is there, never one this file names.

        ⛔ A plant that hardcoded a path turned `--self-test` -- the command the
        workflow runs -- into a `KeyError` the first time a file moved, which is
        a sibling sweep's measured failure rather than a hypothesis.
        """
        for path in sorted(self.text):
            if path != SELF:
                return path
        self.text["planted.md"] = "# Planted\n"
        return "planted.md"


# --- reading the change -----------------------------------------------------


def _git(root: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", root, *args], capture_output=True, text=True, check=False
    )


def _base(root: str) -> str:
    """The merge base against the integration branch, derived and never named.

    ⛔ Which branch that is comes from `claim.integration_branch`, the one
    derivation this repository already has for it -- the surface carries no key
    for the integration branch, and a second derivation here would be a second
    answer to a question § 10's carrier already answers.
    """
    sys.path.insert(0, os.path.join(root, "plugins", "mjolnir", "scripts"))
    try:
        import claim as carrier  # noqa: PLC0415  -- the one derivation, not a second
    except ImportError as exc:
        raise Unreadable(f"the claim carrier could not be imported: {exc}") from exc
    try:
        branch = carrier.integration_branch(root, "origin")
    except Exception as exc:  # the carrier names what it could not derive
        raise Unreadable(f"the integration branch could not be derived: {exc}") from exc

    for ref in (f"origin/{branch}", branch):
        resolved = _git(root, "rev-parse", "--verify", "--quiet", ref)
        if resolved.returncode == 0:
            found = _git(root, "merge-base", ref, "HEAD")
            if found.returncode == 0 and found.stdout.strip():
                return found.stdout.strip()
    raise Unreadable(
        f"no merge base against `{branch}` could be found, so which lines this change "
        "adds cannot be established. In a run, fetch the base branch with depth 0; by "
        "hand, fetch the remote."
    )


def read_change(root: str) -> Change:
    """The post-image text and added line numbers for every markdown this change touches."""
    base = _base(root)
    diff = _git(root, "diff", "--unified=0", "--no-color", "--diff-filter=ACMR",
                base, "--", "*.md")
    if diff.returncode != 0:
        raise Unreadable(f"the diff against `{base[:12]}` could not be read: {diff.stderr.strip()}")

    added: dict[str, set[int]] = {}
    path = None
    for line in diff.stdout.splitlines():
        header = FILE_HEADER.match(line)
        if header:
            path = header.group("path")
            added.setdefault(path, set())
            continue
        hunk = HUNK.match(line)
        if hunk and path:
            start = int(hunk.group("start"))
            count = 1 if hunk.group("count") is None else int(hunk.group("count"))
            added[path].update(range(start, start + count))

    text: dict[str, str] = {}
    unread: list[str] = []
    for touched in sorted(added):
        try:
            with open(os.path.join(root, touched), encoding="utf-8") as handle:
                text[touched] = handle.read()
        except (OSError, UnicodeDecodeError) as exc:
            unread.append(f"{touched} ({exc})")
    return Change(base, text, added, unread)


# --- the checks ------------------------------------------------------------
#
# Each returns a list of problems, and each has at least one planted violation
# below that it is asserted to go red on -- one per arm that does real work,
# because a plant that reddens a check by the wrong route proves nothing about
# the arm it was written for.


def _held(change: Change):
    """(path, line number, the line, the line with shown markers set aside)."""
    for path in sorted(change.text):
        if path == SELF:
            continue
        lines = change.text[path].splitlines()
        prose = prose_lines(change.text[path])
        for number in sorted(change.added.get(path, ())):
            if number not in prose or number > len(lines):
                continue
            yield path, number, lines[number - 1], shown_only(lines[number - 1])


def check_the_change_was_read(change: Change) -> list[str]:
    return [
        f"{entry}: is markdown this change touches and could not be read, so nothing below "
        "held it. A document the sweep cannot open is unheld, which is the one state this "
        "check may not report as green."
        for entry in change.unread
    ]


def check_no_dated_pass_record(change: Change) -> list[str]:
    problems = []
    for path, number, line, cleaned in _held(change):
        heading = HEADING.match(line)
        if heading and DATED_HEADING.search(shown_only(heading.group("text"))):
            problems.append(
                f"{path}:{number}: a heading carrying a date is a per-pass section — "
                f"{' '.join(line.split())[:90]}"
            )
            continue
        if DATED_PASS.search(cleaned):
            problems.append(
                f"{path}:{number}: a dated record of a pass — "
                f"{' '.join(line.split())[:90]}"
            )
    return problems


def check_no_former_value(change: Change) -> list[str]:
    problems = []
    for path, number, line, cleaned in _held(change):
        found = FORMER_VALUE.search(cleaned)
        if found:
            problems.append(
                f"{path}:{number}: a figure stated beside a former value "
                f"({found.group(0).strip()!r}) — state what is true now and replace the "
                f"line: {' '.join(line.split())[:90]}"
            )
    return problems


def check_no_previous_pass_clause(change: Change) -> list[str]:
    problems = []
    for path, number, line, cleaned in _held(change):
        found = PREVIOUS_PASS.search(cleaned)
        if found:
            problems.append(
                f"{path}:{number}: a clause whose subject is a previous pass "
                f"({found.group(0).strip()!r}) — {' '.join(line.split())[:90]}"
            )
    return problems


CHECKS = [
    ("the markdown this change touches was read", check_the_change_was_read),
    ("no dated record of a pass", check_no_dated_pass_record),
    ("no figure beside its former value", check_no_former_value),
    ("no clause whose subject is a previous pass", check_no_previous_pass_clause),
]


# --- the planted violations ------------------------------------------------
#
# A fixture rather than the live change, so the assertions hold with no network,
# on a clean branch, and say the same thing on every branch.

A_WHOLE_DOCUMENT = (
            "# A planted document\n"
            "\n"
            "**Live as of 2026-10-20: 70 open, 87 relations, 70/70 placed.**\n"
            "\n"
            "✅ **#94 landed `e888170`, 2026-10-19**, and the row's argument is kept as the "
            "record of what it cost.\n"
            "\n"
            "The forbidden clauses are `previously` and `(was 7)`, and \"this pass corrected\" "
            "is a third.\n"
            "\n"
            "```markdown\n"
            "### Revalidated 2026-10-19\n"
            "\n"
            "The figures were re-derived rather than recalled.\n"
            "```\n"
            "\n"
            "| row | why |\n"
            "|---|---|\n"
            "| 8 | Cheap, independent, and measured on 2026-10-19 at 16 changes. |\n"
)

# ⛔ Every line of the document above is marked added, so the green side is
# asserted rather than passing for being out of scope: the landed record, the
# live-status line carrying today's date, the shown markers, the fenced
# violation and the dated table row all have to stay green while held. ⚠️ The
# set is **derived** from the text rather than written as a range: a range
# longer than the document swallows the next line appended to it, which is
# exactly the line the carve-out exemption needs left unadded — measured, with
# that exemption reporting WENT RED for the fixture's shape rather than for the
# check's behaviour.
WHOLE = Change(
    base="0" * 40,
    text={"docs/planted.md": A_WHOLE_DOCUMENT},
    added={"docs/planted.md": set(range(1, len(A_WHOLE_DOCUMENT.splitlines()) + 1))},
    unread=[],
)


def _plant(line: str):
    def apply(change: Change) -> Change:
        return change.plant(line)

    return apply


def _carry(line: str):
    def apply(change: Change) -> Change:
        return change.carry(line)

    return apply


def _plant_unreadable(change: Change) -> Change:
    change.unread.append("docs/deleted-without-git-rm.md (no such file)")
    return change


# The measured shape, reproduced rather than described: one of the seven dated
# paragraphs the ordering document had accumulated, in the form it had.
THE_MEASURED_SHAPE = (
    "### Revalidation 2026-10-19 — the figures re-derived rather than recalled"
)

VIOLATIONS = [
    ("the markdown this change touches was read", "a document the sweep cannot open",
     _plant_unreadable),
    ("no dated record of a pass", "the measured shape: a dated revalidation heading",
     _plant(THE_MEASURED_SHAPE)),
    ("no dated record of a pass", "a dated heading with no pass word in it",
     _plant("## 2026-10-19")),
    ("no dated record of a pass", "a dated pass record in prose",
     _plant("On 2026-10-19 this document was swept and its counts corrected.")),
    ("no dated record of a pass", "a pass record with the date after the verb",
     _plant("The ordering was re-read against the live graph on 2026-10-20.")),
    ("no former value", "a parenthetical former value", _plant("70 rows are placed (was 26).")),
    ("no former value", "a `Was:` label opening a line",
     _plant("Was: inferred from the working directory, which § 1 forbids.")),
    ("no former value", "a figure stated as a movement",
     _plant("The plan carries 26 rows, down from 70.")),
    ("no former value", "a counted former value",
     _plant("The document was 469 lines of which 70 were dated paragraphs.")),
    ("no clause whose subject is a previous pass", "the word the rule names",
     _plant("The row previously argued the opposite.")),
    ("no clause whose subject is a previous pass", "a pass as the subject of a clause",
     _plant("This pass corrected the two figures above.")),
    ("no clause whose subject is a previous pass", "a reference to an earlier pass",
     _plant("An earlier pass left the live-status line stale.")),
    ("no clause whose subject is a previous pass", "the measured phrase",
     _plant("Every figure here was re-derived rather than recalled.")),
    ("no clause whose subject is a previous pass", "what the document used to say",
     _plant("The cell used to state that the edge was required.")),
]

# ⛔ The names above are the arms, and the names in CHECKS are what reports them.
# Keeping the two in step is what the self-test's coverage arm does, and the two
# former-value and previous-pass labels differ from their check names on purpose
# -- so the mapping below is explicit rather than a string match that would
# silently cover nothing.
ARM_OF = {
    "no former value": "no figure beside its former value",
    "no clause whose subject is a previous pass": "no clause whose subject is a previous pass",
}


# --- the planted exemptions -------------------------------------------------
#
# The green side of the scope. Each was verified by disabling its own exclusion
# and watching the plant redden: an exemption nothing can fail is an exemption
# nobody checked, and this check's whole shape is an exclusion -- the lines a
# change does not add.

EXEMPTIONS = [
    # ⛔ The rule's own carve-out, and the one this check exists inside: an
    # artifact's existing history is not this change's business. Verified by
    # marking the line added and watching every arm redden.
    ("a violation the change did not write",
     _carry("Previously the row argued the opposite, and the count was 26 of them.")),
    ("a forbidden word shown in a code span",
     _plant("The clause this forbids is `previously`, and `(was 7)` is the other.")),
    ("a forbidden clause shown in a quotation",
     _plant('A clause whose subject is a pass — "this pass corrected the figure" — is one.')),
    ("a landed record carried as an entry's content",
     _plant("✅ **#100 landed `abc1234`, 2026-10-20**, and the row keeps its argument.")),
    ("a live-status line carrying the date it was taken",
     _plant("**Live as of 2026-10-20: 70 open, 87 relations, zero violations.**")),
    ("a dated measurement that states something still true",
     _plant("Measured on 2026-10-19: sixteen changes landed through the carriers.")),
]


def run(change: Change) -> dict[str, list[str]]:
    return {name: check(change) for name, check in CHECKS}


def self_test(change: Change) -> int:
    by_name = dict(CHECKS)
    named = {ARM_OF.get(name, name) for name, _, _ in VIOLATIONS}
    uncovered = [name for name, _ in CHECKS if name not in named]
    for name in uncovered:
        print(f"  NO PLANTED VIOLATION   {name}")
    failures = len(uncovered)

    # A check that cannot pass is as useless as one that cannot fail, and this
    # grammar's whole risk is the honest line it would hand back.
    whole = [problem for found in run(change).values() for problem in found]
    if whole:
        print(f"  RED ON A WHOLE CHANGE  {len(whole)} problem(s): {whole[0]}")
        failures += 1
    else:
        print("  green on               a change whose prose states what is true now")

    for name, label, plant in VIOLATIONS:
        check = by_name[ARM_OF.get(name, name)]
        if check(plant(change.copy())):
            print(f"  red on                 {name}: {label}")
        else:
            print(f"  STAYED GREEN           {name}: {label}")
            failures += 1

    for label, plant in EXEMPTIONS:
        planted = plant(change.copy())
        found = [problem for arm in run(planted).values() for problem in arm]
        if found:
            print(f"  WENT RED               exempt: {label} — {found[0]}")
            failures += 1
        else:
            print(f"  green on               exempt: {label}")

    if failures:
        print(
            f"\n{failures} assertion(s) did not hold. A check that cannot fail is not a "
            "check, and an exemption that cannot pass is not an exemption."
        )
    return 1 if failures else 0


LIMIT = (
    "⚠️ The shapes above are lexical, so a record phrased without any of them passes: this "
    "is a forbidding check and not a computed one. `was` and `corrected` are held only in "
    "compound forms, because bare prose uses both constantly. What else it does not reach — "
    "the day log and the ordering document, which live outside every tree — is stated in "
    "docs/single-source-of-truth.md."
)


def main(argv: list[str]) -> int:
    unknown = [a for a in argv if a != "--self-test"]
    if unknown:
        print(f"unrecognised argument(s): {' '.join(unknown)}\n\n{__doc__}")
        return 2

    if "--self-test" in argv:
        print(
            f"Asserting each check reddens on its planted violations ({len(VIOLATIONS)}) "
            f"and stays green on each planted exemption ({len(EXEMPTIONS)}):"
        )
        if self_test(WHOLE):
            return 1
        print()

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    try:
        change = read_change(root)
    except Unreadable as exc:
        print(f"  FAIL  the markdown this change touches was read\n\n  - {exc}")
        return 1

    results = run(change)
    problems = [problem for found in results.values() for problem in found]
    for name, found in results.items():
        print(f"  {'FAIL' if found else 'ok  '}  {name}")

    held = sum(len(numbers) for path, numbers in change.added.items() if path != SELF)
    print(
        f"\n{held} added line(s) across {len([p for p in change.text if p != SELF])} "
        f"document(s), against the merge base `{change.base[:12]}`."
    )
    if problems:
        print(f"\n{len(problems)} problem(s):\n")
        for problem in problems:
            print(f"  - {problem}")
        print(
            "\nAn artifact states what is true now: replace the stale line rather than "
            "annotating it, and put what this pass did in the reply."
        )
        print(f"\n{LIMIT}")
        return 1
    if not held:
        print("This change adds no markdown prose, so the rule holds nothing here.")
    print(f"\n{LIMIT}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
