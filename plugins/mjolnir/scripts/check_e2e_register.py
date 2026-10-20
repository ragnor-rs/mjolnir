#!/usr/bin/env python3
"""Hold a project's end-to-end register to its suite, and its change to both.

The rule is `plugins/mjolnir/config/schema.md § 15`, which states it and carries
the measurement behind it. Neither is restated here. ⛔ The two comparisons are:

  the register against the suite -- a case with no row is coverage nobody
  recorded, and a row naming no case that is there is a record of coverage that
  is gone, both directions held because neither shows from the output of the
  other;

  the change against both -- a change touching a judged tree carries a new
  case, a new row, or a written exemption, and one carrying none of the three
  fails naming which is missing. ⛔ Its rule, which is the whole idea: an
  uncovered change is allowed; an uncovered change nobody wrote down is not.

⛔ Every value is **read from the configuration**: the suite root, the glob a
case matches, the register and the heading its table sits under, the heading the
written-down gaps sit under, and the trees a change is judged over. Nothing of
any project is written in this file, and a project that carries no
`e2e_register` has no subject here -- which is reported as *no subject* rather
than as a verdict, because a check that holds nothing reports green.

⚠️ It needs no stack, no credential, no indexed material and no spend. That is
why it can run as a host check where the suite it describes cannot, and it is
the whole of what this file claims: **it never runs a case and never asks
whether one passes.**

What is deliberately not held is stated once, with the rule, in
docs/single-source-of-truth.md#the-end-to-end-register-against-the-suite-and-the-change-against-both.

Usage:
    check_e2e_register.py                 hold the register and this change
    check_e2e_register.py --self-test     assert each check reddens on each
                                          planted violation and stays green on
                                          each planted exemption, then stop
"""

from __future__ import annotations

import argparse
import fnmatch
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import claim as carrier  # noqa: E402 -- the one derivation of the integration branch
import config as reader  # noqa: E402 -- the one reader of the surface

FACET = "e2e_register"

# A markdown heading, and a table row. ⚠️ A row whose cells are all dashes and
# colons is the separator the format requires rather than a record of anything.
HEADING = re.compile(r"^(?P<hashes>#{1,6})\s+(?P<title>.*?)\s*$")
SEPARATOR = re.compile(r"^\|[\s:|-]*\|?$")

# How a row names its case: a code span, or a link target. ⛔ Lexical, and the
# narrowness is the point -- a bare word read as a path turns every *Yes* in a
# cell into a file that is missing, so the contract § 15 states is that the row
# names its case the way a register already writes one. The run prints this
# limit in its own output rather than leaving a green to imply more.
CODE_SPAN = re.compile(r"`([^`\n]+)`")
LINK_TARGET = re.compile(r"\]\(([^)\s#]+)")


class Unreadable(RuntimeError):
    """Something this check needs could not be established.

    ⛔ Never a pass. A base it cannot find and a register it cannot open each
    leave both comparisons holding nothing, which is the one state a check may
    not report as green.
    """


# --- the subject -----------------------------------------------------------


def git(root: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", root, *args], capture_output=True, text=True, check=False
    )


def integration(root: str) -> str:
    """The branch this change is against.

    ⛔ The change's own base first, where the run states it: a host sending a
    pull-request event names the base branch in the environment, free and with
    no credential, so a change stacked on a sibling is held to its own base
    rather than to the default one. Where nothing states it, the claim carrier
    answers -- the one derivation of which branch that is, this surface carrying
    no key for it.
    """
    stated = os.environ.get("GITHUB_BASE_REF")
    if stated:
        return stated[len("refs/heads/"):] if stated.startswith("refs/heads/") else stated
    try:
        return carrier.integration_branch(root, "origin")
    except Exception as exc:  # the carrier names what it could not derive
        raise Unreadable(f"the integration branch could not be derived: {exc}") from exc


def merge_base(root: str, branch: str) -> str:
    """The merge base with that branch, or a refusal naming what it could not read."""
    head = git(root, "rev-parse", "HEAD").stdout.strip()
    for ref in (f"origin/{branch}", branch):
        if git(root, "rev-parse", "--verify", "--quiet", ref).returncode != 0:
            continue
        found = git(root, "merge-base", ref, "HEAD")
        base = found.stdout.strip()
        if found.returncode != 0 or not base:
            continue
        # ⛔ A base that **is** the head establishes no change at all, and the
        # change arm would then report green having read nothing. The reachable
        # way in is a checkout with no remote, where the carrier's last fallback
        # is this branch's own name.
        if base == head:
            raise Unreadable(
                f"the merge base with `{branch}` is this change's own head, so this change "
                "touches nothing and the rule would hold nothing. Name the base branch, or "
                "fetch one this branch actually diverges from."
            )
        return base
    raise Unreadable(
        f"no merge base against `{branch}` could be found, so what this change touches "
        "cannot be established. In a run, fetch the base branch with depth 0; by hand, "
        "fetch the remote."
    )


def under(path: str, root: str) -> bool:
    """Whether `path` is `root` itself or sits inside it."""
    root = root.strip().strip("/")
    return bool(root) and (path == root or path.startswith(f"{root}/"))


def matches(path: str, suite: str, glob: str) -> bool:
    """Whether a path is a case: inside the suite, and matching the glob under it.

    ⚠️ The glob is matched against the path **relative to the suite root**, with
    the shell's own wildcards -- where `*` crosses a directory separator, so
    `*.case` reaches a case in a subdirectory and the default `*` is every file
    the suite holds.
    """
    if not under(path, suite):
        return False
    relative = path[len(suite.strip().strip("/")) + 1:]
    return fnmatch.fnmatch(relative, glob)


class Subject:
    """The file lists, the register at both ends of the change, and what it touched.

    In memory, so the plants below mutate a copy rather than a checkout: a
    self-test that wrote into the tree it ran in would leave the break behind on
    the first failure.
    """

    def __init__(
        self,
        facet: dict,
        cases_before: set[str],
        cases_now: set[str],
        register_before: str | None,
        register_now: str | None,
        touched: set[str],
        suite_tracked: bool,
    ):
        self.facet = facet
        self.cases_before = cases_before
        self.cases_now = cases_now
        self.register_before = register_before
        self.register_now = register_now
        self.touched = touched
        self.suite_tracked = suite_tracked

    def copy(self) -> "Subject":
        return Subject(
            dict(self.facet),
            set(self.cases_before),
            set(self.cases_now),
            self.register_before,
            self.register_now,
            set(self.touched),
            self.suite_tracked,
        )

    # -- what the configuration named ------------------------------------

    @property
    def suite(self) -> str:
        return str(self.facet["suite"]).strip().strip("/")

    @property
    def glob(self) -> str:
        return str(self.facet.get("cases") or "*")

    @property
    def register(self) -> str:
        return str(self.facet["register"])

    @property
    def heading(self) -> str:
        return str(self.facet["heading"])

    @property
    def exemptions(self) -> str:
        return str(self.facet["exemptions"])

    @property
    def judged(self) -> list[str]:
        return [str(tree) for tree in self.facet["judged"]]

    # -- what the change touched -----------------------------------------

    def touched_judged(self) -> list[str]:
        return sorted(p for p in self.touched if any(under(p, t) for t in self.judged))

    def touched_unjudged(self) -> list[str]:
        return sorted(p for p in self.touched if not any(under(p, t) for t in self.judged))


def tracked_at(root: str, commit: str) -> set[str]:
    out = git(root, "ls-tree", "-r", "--name-only", commit)
    if out.returncode != 0:
        raise Unreadable(f"the file list at `{commit[:12]}` could not be read: {out.stderr.strip()}")
    return {line for line in out.stdout.splitlines() if line}


def tracked_now(root: str) -> set[str]:
    out = git(root, "ls-files")
    if out.returncode != 0:
        raise Unreadable(f"the tracked file list could not be read: {out.stderr.strip()}")
    return {line for line in out.stdout.splitlines() if line}


def text_at(root: str, commit: str, path: str) -> str | None:
    """The file's text at that commit, or None where it was not there."""
    out = git(root, "show", f"{commit}:{path}")
    return out.stdout if out.returncode == 0 else None


def read_subject(root: str, facet: dict, base: str | None = None) -> Subject:
    """Everything the two comparisons read, from git and the working tree.

    ⚠️ `base` is a parameter so the suite below can exercise this derivation
    against a repository it built itself: the plants are in memory and prove
    nothing about the plumbing, which is where a convincing false green lives.
    """
    base = base or merge_base(root, integration(root))
    suite = str(facet["suite"]).strip().strip("/")
    glob = str(facet.get("cases") or "*")

    at_base = tracked_at(root, base)
    now = tracked_now(root)

    diff = git(root, "-c", "core.quotePath=false", "diff", "--name-only",
               "--diff-filter=ACMRD", base)
    if diff.returncode != 0:
        raise Unreadable(f"the diff against `{base[:12]}` could not be read: {diff.stderr.strip()}")

    register = str(facet["register"])
    try:
        with open(os.path.join(root, register), encoding="utf-8") as handle:
            register_now = handle.read()
    except FileNotFoundError:
        register_now = None
    except (OSError, UnicodeDecodeError) as exc:
        raise Unreadable(f"the register `{register}` could not be read: {exc}") from exc

    return Subject(
        facet=facet,
        cases_before={p for p in at_base if matches(p, suite, glob)},
        cases_now={p for p in now if matches(p, suite, glob)},
        register_before=text_at(root, base, register),
        register_now=register_now,
        touched={line for line in diff.stdout.splitlines() if line},
        suite_tracked=any(under(p, suite) for p in now),
    )


# --- reading the register ---------------------------------------------------


def section(text: str, title: str) -> list[str] | None:
    """The lines under that heading, or None where the document carries no such heading.

    The extent runs to the next heading of the same level or higher, which is
    the document's own structure rather than a depth written down here.
    """
    wanted = " ".join(title.replace("`", "").split()).casefold()
    lines = text.splitlines()
    start, level = None, 0
    for index, line in enumerate(lines):
        found = HEADING.match(line)
        if not found:
            continue
        here = " ".join(found.group("title").replace("`", "").split()).casefold()
        if start is None:
            if here == wanted:
                start, level = index + 1, len(found.group("hashes"))
            continue
        if len(found.group("hashes")) <= level:
            return lines[start:index]
    return None if start is None else lines[start:]


def rows(lines: list[str]) -> list[str]:
    """The register's own rows: every table row under the heading, less the header.

    ⚠️ The first row is the table's header by the format's own rule, and a row
    of dashes is its separator. Everything else under that heading is a record
    of coverage, including the header of a second table written there -- which
    reddens as a row naming no case rather than being guessed at.
    """
    found = [l.strip() for l in lines if l.strip().startswith("|") and not SEPARATOR.match(l.strip())]
    return found[1:]


def named_in(row: str) -> list[str]:
    """Every path a row names, in the two forms a register writes one."""
    return [*(m.group(1).strip() for m in CODE_SPAN.finditer(row)),
            *(m.group(1).strip() for m in LINK_TARGET.finditer(row))]


def resolved(named: str, suite: str) -> list[str]:
    """The paths a named case could be: repository-relative, or under the suite."""
    cleaned = named.strip().lstrip("./")
    return [cleaned, f"{suite}/{cleaned}"]


def written_down(lines: list[str]) -> set[str]:
    """Each written exemption, as one normalised line.

    A heading inside the section is its own structure rather than an entry, and
    a blank line is nothing. What is left is what somebody wrote down.
    """
    return {
        " ".join(line.split())
        for line in lines
        if line.strip() and not HEADING.match(line)
    }


# --- the checks -------------------------------------------------------------


def check_the_register_and_the_suite_agree(subject: Subject) -> list[str]:
    """Both directions, and each half's absence reported as that half.

    ⛔ The cascade is what this must not do: an absent register makes every case
    rowless and an absent suite makes every row dangling, so a project carrying
    one half would have its whole content reported as broken with the one real
    fact buried in it (§ 15).
    """
    missing = []
    if subject.register_now is None:
        missing.append(
            f"the register `{subject.register}` is not in the tree, so what the suite "
            "covers is recorded nowhere. That half is missing — the cases are not held "
            "to anything until it exists."
        )
    if not subject.cases_now:
        where = "holds no tracked file" if not subject.suite_tracked else (
            f"holds no tracked file matching `{subject.glob}`"
        )
        missing.append(
            f"the suite root `{subject.suite}` {where}, so there is no case list to "
            "compare. That half is missing — a register with rows and no suite is held "
            "to nothing."
        )
    if missing:
        return missing

    lines = section(subject.register_now, subject.heading)
    if lines is None:
        return [
            f"`{subject.register}` carries no heading `{subject.heading}`, so the table "
            "this check reads is not there. The heading is configuration: either write "
            "it in the register, or state the one the register already uses."
        ]

    problems = []
    recorded: set[str] = set()
    for row in rows(lines):
        shown = " ".join(row.split())[:70]
        found = [
            case
            for named in named_in(row)
            for case in resolved(named, subject.suite)
            if case in subject.cases_now
        ]
        if found:
            recorded.update(found)
            continue
        candidates = named_in(row)
        if not candidates:
            problems.append(
                f"{subject.register}: a row names no case at all: {shown}. A row names "
                "its case in a code span or a link target (§ 15) — a path written bare is "
                "not read, and a row about nothing is a record nothing can be missing from."
            )
            continue
        problems.append(
            f"{subject.register}: a row names {', '.join(repr(c) for c in candidates)}, "
            f"which is no case under `{subject.suite}` matching `{subject.glob}`: {shown}. "
            "A row naming a file that is not there records coverage that is gone."
        )
    for case in sorted(subject.cases_now - recorded):
        problems.append(
            f"{case}: is a case and no row of `{subject.register}` under "
            f"`{subject.heading}` names it. Coverage nobody recorded reads as coverage "
            "nobody has."
        )
    return problems


def check_an_uncovered_change_is_written_down(subject: Subject) -> list[str]:
    """A change in a judged tree carries a case, a row, or a written exemption."""
    touched = subject.touched_judged()
    if not touched:
        return []

    new_cases = subject.cases_now - subject.cases_before
    rows_now = set(map(str.strip, rows(section(subject.register_now or "", subject.heading) or [])))
    rows_before = set(
        map(str.strip, rows(section(subject.register_before or "", subject.heading) or []))
    )
    new_rows = rows_now - rows_before
    exempt_now = written_down(section(subject.register_now or "", subject.exemptions) or [])
    exempt_before = written_down(
        section(subject.register_before or "", subject.exemptions) or []
    )
    new_exemptions = exempt_now - exempt_before

    if new_cases or new_rows or new_exemptions:
        return []
    return [
        f"this change touches {len(touched)} file(s) in a judged tree "
        f"({', '.join(touched[:5])}{', …' if len(touched) > 5 else ''}) and carries none "
        f"of the three: no new case under `{subject.suite}` matching `{subject.glob}`, no "
        f"new row under `{subject.heading}` of `{subject.register}`, and nothing new under "
        f"`{subject.exemptions}` there. An uncovered change is allowed; an uncovered change "
        "nobody wrote down is not (§ 15) — add the case, record the row, or write down what "
        "is not covered and why."
    ]


CHECKS = [
    ("the register and the suite agree", check_the_register_and_the_suite_agree),
    ("an uncovered change is written down", check_an_uncovered_change_is_written_down),
]


# --- what the run reports rather than holds ---------------------------------
#
# ⛔ Neither of these is a verdict, and both are § 15's: what is deliberately
# uncovered is readable in one place rather than inferred from an absence, and a
# tree the configuration does not judge is named rather than silently skipped.


def reported(subject: Subject) -> list[str]:
    out = []
    lines = section(subject.register_now or "", subject.exemptions)
    if lines is None:
        out.append(
            f"no `{subject.exemptions}` heading in `{subject.register}` yet, so a change "
            "that cannot be covered has nowhere compliant to say so."
        )
    else:
        written = sorted(written_down(lines))
        before = written_down(section(subject.register_before or "", subject.exemptions) or [])
        if not written:
            out.append(f"`{subject.exemptions}`: nothing is written down as uncovered.")
        for entry in written:
            mark = " (new in this change)" if entry not in before else ""
            out.append(f"deliberately not covered{mark}: {entry[:110]}")

    judged = ", ".join(f"`{t}`" for t in subject.judged)
    out.append(f"judged: {judged} — a change outside these passes unremarked (§ 15).")
    unjudged = subject.touched_unjudged()
    if unjudged:
        shown = ", ".join(unjudged[:8]) + (", …" if len(unjudged) > 8 else "")
        out.append(
            f"touched and not judged: {len(unjudged)} file(s) — {shown}. A reviewer "
            "stands in for the judgement here."
        )
    out.append(
        "a row is read from a code span or a link target, and a case is a **tracked** "
        "file: an untracked case file is not a case, and a path written bare in a row "
        "names nothing."
    )
    return out


# --- the planted violations -------------------------------------------------
#
# ⛔ One per branch that does real work, against a subject this file builds
# itself. No plant names a project, and no plant writes into the checkout it
# runs in.


def _a_subject() -> Subject:
    """A register and a suite that agree, and a change that is covered.

    The baseline every plant below is measured against. ⚠️ Its own premise is
    asserted before any plant runs: a fixture that was already failing would
    make every red below prove nothing.
    """
    facet = {
        "carrier": "file",
        "suite": "a-suite",
        "cases": "*.case",
        "register": "a-suite/a-register.md",
        "heading": "Coverage",
        "exemptions": "What is not covered, and why",
        "judged": ["a-judged-tree"],
    }
    register = (
        "# A register\n\n"
        "## Coverage\n\n"
        "| group | case |\n|---|---|\n"
        "| the first group | `a-suite/first.case` |\n"
        "| the second group | `second.case` |\n\n"
        "## What is not covered, and why\n\n"
        "- the third group: it needs a card reader nothing in the run has.\n"
    )
    return Subject(
        facet=facet,
        cases_before={"a-suite/first.case"},
        cases_now={"a-suite/first.case", "a-suite/second.case"},
        register_before=register.replace("| the second group | `second.case` |\n", ""),
        register_now=register,
        touched={"a-judged-tree/thing.src", "a-suite/second.case"},
        suite_tracked=True,
    )


def _without_the_new_case(subject: Subject) -> Subject:
    """A change in a judged tree that records nothing: the rule's own violation."""
    subject.cases_before = set(subject.cases_now)
    subject.register_before = subject.register_now
    subject.touched = {"a-judged-tree/thing.src"}
    return subject


def _a_case_with_no_row(subject: Subject) -> Subject:
    subject.cases_now = set(subject.cases_now) | {"a-suite/unlisted.case"}
    return subject


def _a_row_with_no_case(subject: Subject) -> Subject:
    subject.register_now = (subject.register_now or "").replace(
        "| the second group | `second.case` |",
        "| the second group | `second.case` |\n| a group whose file went | `gone.case` |",
    )
    return subject


def _a_row_naming_nothing(subject: Subject) -> Subject:
    """A row that writes its path bare, which this check does not read as a path."""
    subject.register_now = (subject.register_now or "").replace(
        "| the second group | `second.case` |",
        "| the second group | `second.case` |\n| a third group | second.case |",
    )
    return subject


def _no_register(subject: Subject) -> Subject:
    subject.register_now = None
    return subject


def _no_heading(subject: Subject) -> Subject:
    subject.register_now = (subject.register_now or "").replace("## Coverage", "## Scenarios")
    return subject


def _no_cases(subject: Subject) -> Subject:
    subject.cases_now = set()
    return subject


def _a_suite_holding_other_files(subject: Subject) -> Subject:
    """The other spelling of the missing half: files there, none of them a case."""
    subject.cases_now = set()
    subject.suite_tracked = True
    return subject


VIOLATIONS = [
    ("the register and the suite agree", "a case no row names", _a_case_with_no_row),
    ("the register and the suite agree", "a row naming a case that is gone", _a_row_with_no_case),
    ("the register and the suite agree", "a row naming no case at all", _a_row_naming_nothing),
    ("the register and the suite agree", "the register absent", _no_register),
    ("the register and the suite agree", "the register's heading absent", _no_heading),
    ("the register and the suite agree", "a suite with no case in it", _no_cases),
    ("the register and the suite agree", "a suite whose files are none of them cases",
     _a_suite_holding_other_files),
    ("an uncovered change is written down", "a judged change recording none of the three",
     _without_the_new_case),
]


# --- the planted exemptions -------------------------------------------------
#
# The green side of the scope. ⛔ Each of these is a hole somebody wrote on
# purpose, and each was verified by switching its own arm off and watching the
# plant redden -- an exemption nothing can fail is an exemption nobody checked.


def _a_written_exemption(subject: Subject) -> Subject:
    """The escape: a change that records nothing but writes down why."""
    subject = _without_the_new_case(subject)
    subject.register_now = (subject.register_now or "") + (
        "- the judged change in this plant: the behaviour it moves is not reachable "
        "through the interface.\n"
    )
    return subject


def _a_new_row_only(subject: Subject) -> Subject:
    """A change that adds no case and records one: the second of the three."""
    subject = _without_the_new_case(subject)
    subject.cases_now = set(subject.cases_now) | {"a-suite/third.case"}
    subject.cases_before = set(subject.cases_now)
    subject.register_now = (subject.register_now or "").replace(
        "| the second group | `second.case` |",
        "| the second group | `second.case` |\n| the third group | `third.case` |",
    )
    return subject


def _a_change_outside_every_judged_tree(subject: Subject) -> Subject:
    subject = _without_the_new_case(subject)
    subject.touched = {"a-container-tree/an-image-recipe", "a-document.md"}
    return subject


def _a_row_naming_its_case_under_the_suite(subject: Subject) -> Subject:
    """A row naming its case relative to the suite root, a directory down.

    ⚠️ What this exercises is the **resolution**, not the glob: the subject here
    is in memory, so no plant on it reaches the matching that decides what a
    case is. That arm is exercised against the repository the suite builds.
    """
    subject.cases_now = set(subject.cases_now) | {"a-suite/deeper/fourth.case"}
    subject.register_now = (subject.register_now or "").replace(
        "| the second group | `second.case` |",
        "| the second group | `second.case` |\n| the fourth group | `deeper/fourth.case` |",
    )
    return subject


def _a_row_naming_its_case_as_a_link(subject: Subject) -> Subject:
    subject.cases_now = set(subject.cases_now) | {"a-suite/fifth.case"}
    subject.register_now = (subject.register_now or "").replace(
        "| the second group | `second.case` |",
        "| the second group | `second.case` |\n| the fifth group | [the case](fifth.case) |",
    )
    return subject


def _a_second_heading_after_the_table(subject: Subject) -> Subject:
    """The section ends at the next heading, so a later table is not read as rows."""
    subject.register_now = (subject.register_now or "") + (
        "\n## Something else\n\n| a | b |\n|---|---|\n| not a row of the register | x |\n"
    )
    return subject


EXEMPTIONS = [
    ("a judged change that writes down why it is uncovered", _a_written_exemption),
    ("a judged change that records a row rather than adding a case", _a_new_row_only),
    ("a change outside every judged tree", _a_change_outside_every_judged_tree),
    ("a row naming its case relative to the suite root, a directory down",
     _a_row_naming_its_case_under_the_suite),
    ("a row naming its case as a link target", _a_row_naming_its_case_as_a_link),
    ("a table under a later heading of the same document", _a_second_heading_after_the_table),
]


def run(subject: Subject) -> dict[str, list[str]]:
    return {name: check(subject) for name, check in CHECKS}


# --- the suite --------------------------------------------------------------


def _a_repository(where: str) -> tuple[str, str]:
    """A repository with a base commit and a change on top. Returns (root, base).

    ⚠️ The plants above are in memory and prove nothing about the plumbing: the
    base, the two file lists and the diff are where a convincing false green
    lives, so one arm reads a repository this function builds.
    """
    root = os.path.join(where, "tree")
    os.makedirs(os.path.join(root, "a-suite"))
    os.makedirs(os.path.join(root, "a-judged-tree"))
    git(root, "init", "--quiet")
    # ⛔ An identity that is not address-shaped, which is this repository's own
    # gate rather than taste: the sweep forbidding a person or an account to be
    # named reads every tracked file and not only the carrier roots, so the
    # conventional placeholder address a fixture would use is a red here — and
    # so is writing one into the comment that explains why. Git commits under
    # any string.
    git(root, "config", "user.email", "the-suite")
    git(root, "config", "user.name", "the-suite")

    def write(relative: str, text: str) -> None:
        full = os.path.join(root, relative)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as handle:
            handle.write(text)

    write("a-suite/first.case", "the first case\n")
    # A case a directory down, and a file in the suite that is not a case: the
    # glob is what tells them apart, and it is reached only from here.
    write("a-suite/deeper/second.case", "the second case\n")
    write("a-suite/a-fixture.json", "{}\n")
    write(
        "a-suite/a-register.md",
        "# A register\n\n## Coverage\n\n| group | case |\n|---|---|\n"
        "| the first group | `a-suite/first.case` |\n"
        "| the second group | `deeper/second.case` |\n\n"
        "## What is not covered, and why\n\n- nothing yet.\n",
    )
    write("a-judged-tree/thing.src", "the behaviour\n")
    git(root, "add", "-A")
    git(root, "commit", "--quiet", "-m", "the base")
    base = git(root, "rev-parse", "HEAD").stdout.strip()
    git(root, "branch", "a-base-branch")

    write("a-judged-tree/thing.src", "the behaviour, moved\n")
    git(root, "add", "-A")
    git(root, "commit", "--quiet", "-m", "the change")
    return root, base


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

    # ⛔ The fixture's own premise first. A plant measured against a baseline
    # that is already red proves nothing, and a fixture whose change touches no
    # judged tree would make every exemption below pass vacuously.
    baseline = {name: set(found) for name, found in run(subject).items()}
    check("the fixture starts green", not any(baseline.values()), f"{baseline}")
    check("the fixture's change touches a judged tree", bool(subject.touched_judged()))
    check(
        "the fixture's register names every case it has",
        bool(subject.cases_now) and subject.register_now is not None,
    )

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

    # The plumbing, against a repository built for it: the base derivation, the
    # two file lists and the diff, each in both directions.
    with tempfile.TemporaryDirectory() as where:
        root, base = _a_repository(where)
        facet = dict(_a_subject().facet)
        live = read_subject(root, facet, base=base)
        check(
            "a real tree's change is read from the diff",
            live.touched == {"a-judged-tree/thing.src"},
            f"read {sorted(live.touched)}",
        )
        check(
            "a real tree's cases are read from the index, the glob crossing a separator "
            "and the fixture beside them left out",
            live.cases_now == {"a-suite/first.case", "a-suite/deeper/second.case"},
            f"read {sorted(live.cases_now)}",
        )
        # ⛔ And the glob held from the other end: with every file in the suite a
        # case, the fixture that is not one is in the list — so the arm above is
        # the glob doing work rather than the suite happening to hold cases only.
        every = read_subject(root, {**facet, "cases": "*"}, base=base)
        check(
            "with the glob widened, the file that is not a case is in the list",
            "a-suite/a-fixture.json" in every.cases_now,
            f"read {sorted(every.cases_now)}",
        )
        check(
            "a real tree's register is read at both ends",
            live.register_now is not None and live.register_before is not None,
        )
        found = run(live)
        check(
            "that change reddens the rule, the register being untouched",
            bool(found["an uncovered change is written down"]),
            f"{found}",
        )
        check(
            "and the register still agrees with the suite",
            not found["the register and the suite agree"],
            f"{found['the register and the suite agree']}",
        )

        # The base derived rather than handed over, which is what a run does.
        was = os.environ.get("GITHUB_BASE_REF")
        os.environ["GITHUB_BASE_REF"] = "a-base-branch"
        try:
            derived = read_subject(root, facet)
        finally:
            if was is None:
                os.environ.pop("GITHUB_BASE_REF", None)
            else:
                os.environ["GITHUB_BASE_REF"] = was
        check(
            "the base the host states is the base read",
            derived.touched == live.touched,
            f"read {sorted(derived.touched)}",
        )

        # And the one state this check may not report as green.
        os.environ["GITHUB_BASE_REF"] = git(root, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
        try:
            read_subject(root, facet)
            refused = None
        except Unreadable as exc:
            refused = str(exc)
        finally:
            if was is None:
                os.environ.pop("GITHUB_BASE_REF", None)
            else:
                os.environ["GITHUB_BASE_REF"] = was
        check(
            "a base that is this change's own head is refused, not read as nothing to hold",
            refused is not None and "hold nothing" in refused,
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
        description="Hold a project's end-to-end register to its suite, and its change to both.",
    )
    parser.add_argument(
        "--skills-root",
        default=".",
        help="the root the configuration is resolved relative to (§ 1)",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="assert each check reddens on its planted violations and stays green on each "
        "planted exemption, then stop",
    )
    args = parser.parse_args(argv)

    if args.self_test:
        print(
            "Asserting the checks redden on each planted violation "
            f"({len(VIOLATIONS)}), stay green on each planted exemption "
            f"({len(EXEMPTIONS)}), and read a repository built for it:"
        )
        return self_test()

    try:
        config = reader.load(args.skills_root)
    except reader.ConfigError as error:
        print(str(error), file=sys.stderr)
        return 1

    facet = config.get(FACET) or {}
    if facet.get("carrier") != "file":
        # ⛔ Not a verdict. A project that carries no register has no subject
        # here, and a run that printed green would be a check holding nothing
        # (§ 15) — so this says what is absent and exits neither green nor red.
        print(
            f"`{FACET}.carrier` is {facet.get('carrier')!r}, so this project states no "
            "end-to-end suite and no register, and this check has no subject. A project "
            "in that position runs no such check: delete the entry from `host.checks`, "
            f"or state the facet. What it decided instead: "
            f"{' '.join(str(facet.get('absent_reason')).split())}",
            file=sys.stderr,
        )
        return 2

    root = config.code_root
    try:
        subject = read_subject(root, facet)
    except Unreadable as exc:
        print(f"nothing could be held: {exc}", file=sys.stderr)
        return 1

    results = run(subject)
    for name, found in results.items():
        print(f"  {'FAIL' if found else 'ok  '}  {name}")
    print("\nWhat this run reports rather than refuses:")
    for line in reported(subject):
        print(f"  - {line}")

    problems = [problem for found in results.values() for problem in found]
    if problems:
        print(f"\n{len(problems)} problem(s):\n")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print(
        f"\nEvery case under `{subject.suite}` has a row, every row names a case, and this "
        "change carries a case, a row, or a written exemption."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
