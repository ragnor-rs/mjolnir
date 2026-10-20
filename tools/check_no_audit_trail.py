#!/usr/bin/env python3
"""Hold the prose this change writes to the rule that an artifact states what is true now.

The rule is `plugins/mjolnir/config/schema.md § The loop -> An artifact states
what is true now`, which states it and carries the measurement behind it.
Neither is restated here.

⛔ **Only the lines this change adds are read**, which is the rule's own
carve-out rather than a convenience: existing artifacts stand as they are, and
rewrapping the past would repaint every document in the tree. The post-image
line numbers come from a diff against the merge base, so a refusal names the
file and the line a reader can open.

What is in scope: tracked markdown, including table rows -- a row's argument
column is exactly where the measured habit lived. What is out of scope, and why,
is stated once in
docs/single-source-of-truth.md#an-artifact-states-what-is-true-now-held-on-the-lines-a-change-adds.

⚠️ **The forbidden shapes are lexical, and this is a forbidding check rather
than a computed one.** A record phrased without any of the markers below passes.
The run says so in its own output rather than implying completeness, because a
green run on a document that narrates its own history would otherwise read as
coverage. Two words the shapes are commonly phrased with -- `was` and
`corrected` -- are held only in compound forms (`(was 7)`, `Was:`, `this pass
corrected`), because bare prose uses both constantly and a sweep for them hands
back a change over the honest form of a sentence.

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
#
# ⛔ `pass` itself is absent for the same reason, measured rather than reasoned:
# with it in, *the gate passes on every document in the tree as of 2026-10-20*
# reddens, and at a hundred columns a date is nearly always inside the window.
# The words left are ones a sentence reaches for only to narrate a pass.
# ⛔ `audit` is absent too, and that one is this rule's own name turning on it:
# with it in, `#100 landed 2026-10-20 as the audit-trail rule` reddens, so the
# landed-record carve-out stops holding for exactly the item that states it.
PASS_WORD = (
    r"(?:revalidat\w+|re-?read|re-?check\w*|re-?deriv\w+|re-?stamp\w*|"
    r"stamped|swept|sweep|corrected|re-?counted|recount\w*|refreshed)"
)

DATED_PASS = re.compile(DATE + r".{0,200}?\b" + PASS_WORD + r"\b|\b" + PASS_WORD
                        + r"\b.{0,200}?" + DATE, re.I)

# A heading that is **only** a date, which is a per-pass section whatever its
# verb -- the shape the measured 70 lines took. ⛔ A heading that carries a date
# among other words is held by the line arm above instead, and so needs a pass
# word: without that split, every release heading of every changelog reddens,
# which is a false red waiting in the first project that adopts this.
HEADING = re.compile(r"^\s{0,3}#{1,6}\s+(?P<text>.*)$")
DATED_HEADING = re.compile(r"^[\s*_`#—–-]*" + DATE + r"[\s*_`.:—–-]*$")

# A figure stated beside its former value. ⚠️ A closed list, and the weakness is
# in the safe direction: a reworded former value passes and leaves a finding
# missed, which the person reading the diff can still raise, where a broader
# grammar hands back a change over a sentence like `the divergence was 71 lines`
# -- a measurement, not an annotation. ⛔ That sentence is the measurement of
# this list's own boundary: a sixth alternative reading `was <n> lines` shipped
# in the first draft of this file, reddening the very sentence the comment calls
# honest, and a plant asserted the contradiction rather than catching it.
FORMER_VALUE = re.compile(
    r"\(\s*was\s+[^)]{1,60}\)"
    r"|^\s*(?:[-*+]\s+)?(?:\*\*)?was\s*:"
    r"|\b(?:down|up)\s+from\s+\d"
    r"|\bformerly\s+\d"
    r"|\bpreviously\s+\d",
    re.I,
)

# A clause whose subject is a pass that already happened. `previously` is here
# bare, as one of the four forms the rule names: a sentence reaching for it is
# narrating a former state, and rewriting it costs a clause.
#
# ⚠️ The **indefinite** forms only — *a previous pass*, *an earlier pass*. *The
# last pass* is how a role's own procedure refers to the run before it (*filed
# since the last pass*, which this repository's close-out skill states twice),
# and an instruction about passes is not a record of one.
PREVIOUS_PASS = re.compile(
    r"\bpreviously\b"
    r"|\bthis (?:pass|run) (?:corrected|found|re-?derived|rewrote|replaced|fixed|updated)\b"
    r"|\b(?:a|an) (?:previous|earlier|prior) pass\b"
    r"|\bre-?derived rather than recalled\b"
    r"|\bas of (?:this|the last) pass\b"
    r"|\bused to (?:say|state|read)\b"
    r"|\bhas since been (?:corrected|replaced|updated|rewritten)\b"
    r"|\bno longer (?:says|states|reads)\b"
    r"|\bcorrected (?:in|on|during) (?:this|the last|a previous)\b",
    re.I,
)

# What is set aside before a line is read. A marker *shown* is not a marker
# *used*: the section of the surface that states this rule has to spell out
# every form it forbids. An inline-code span and a quoted run are the two ways
# this repository shows one.
#
# ⚠️ Each pair closes with its own mark and never with its partner's, and the
# curly pair is here because which quotation mark an author reaches for would
# otherwise decide the verdict. ⛔ What stays true of this exclusion is that it
# is an off switch an author controls: anything inside quotation marks passes.
# The remedy is that a reader can see the quotes.
CODE_SPAN = re.compile(r"`[^`\n]+`")
QUOTED = re.compile(r"\"[^\"\n]{1,80}\"|«[^»\n]{1,80}»|“[^”\n]{1,80}”")

# A fence's own marker is remembered rather than toggled on, because a toggle
# makes one unpaired opener exempt every line after it -- and a line shown
# inside a quadruple fence closes a triple one. A fence closes on the same
# character, at least as long.
FENCE = re.compile(r"^\s*(?P<marker>`{3,}|~{3,})")
FRONTMATTER = "---"
FRONTMATTER_FIELD = re.compile(r"^[A-Za-z_][\w-]*\s*:")

# The diff this check reads: post-image line numbers, so a refusal names a line
# somebody can open.
HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(?P<start>\d+)(?:,(?P<count>\d+))? @@")
FILE_HEADER = re.compile(r"^\+\+\+ b/(?P<path>.*)$")

# ⛔ This file carries no self-exemption, unlike the sibling sweep whose markers
# it would otherwise trip over: the diff above is filtered to markdown, so a
# `.py` path cannot enter the set at all. A `path != SELF` guard beside that
# filter read as an exclusion the check has and was three lines that could never
# fire.


def shown_only(line: str) -> str:
    """The line with every shown marker set aside."""
    return QUOTED.sub("x", CODE_SPAN.sub("x", line))


def split_lines(text: str) -> list[str]:
    """The document's lines, numbered the way git numbers them.

    ⛔ `str.splitlines()` breaks on a form feed, a line separator and five more
    characters git counts as ordinary text, so one of them anywhere in a
    document puts every line number after it out of step with the diff's --
    which sends a refusal to the wrong line and lets the right one pass.
    """
    return text.split("\n")


def prose_lines(text: str) -> set[int]:
    """The 1-indexed lines of a document that are prose a reader reads.

    Fenced blocks and the document's own frontmatter are out: a fence shows
    what a rule forbids, and frontmatter is metadata. ⛔ Table rows are **in**,
    because a row's argument column is where the measured habit lived -- which
    is the one exclusion a sweep of this kind would reach for and must not take.

    ⚠️ Frontmatter is only frontmatter where the line after the opener is a
    field. A document opening on a thematic break -- three dashes, which is
    ordinary markdown -- would otherwise have everything down to the next break
    exempted, and that is a hole shaped exactly like a per-pass preamble.
    """
    lines = split_lines(text)
    in_frontmatter = (
        len(lines) > 1
        and lines[0].strip() == FRONTMATTER
        and bool(FRONTMATTER_FIELD.match(lines[1].strip()))
        and any(line.strip() == FRONTMATTER for line in lines[1:])
    )
    out: set[int] = set()
    fence: str | None = None
    for number, line in enumerate(lines, 1):
        if in_frontmatter:
            if number > 1 and line.strip() == FRONTMATTER:
                in_frontmatter = False
            continue
        opened = FENCE.match(line)
        if fence is None and opened:
            fence = opened.group("marker")
            continue
        if fence is not None:
            if opened and opened.group("marker")[0] == fence[0] and len(
                opened.group("marker")
            ) >= len(fence):
                fence = None
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
        """Whichever document is there, and one synthesised where none is.

        ⛔ A plant that hardcoded a path turned `--self-test` -- the command the
        workflow runs -- into a `KeyError` the first time a file moved, which is
        a sibling sweep's measured failure rather than a hypothesis.
        """
        for path in sorted(self.text):
            return path
        self.text["planted.md"] = "# Planted\n"
        return "planted.md"


# --- reading the change -----------------------------------------------------


def _git(root: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", root, *args], capture_output=True, text=True, check=False
    )


def _branch(root: str) -> str:
    """The branch this change is against.

    ⛔ **The change's own base first, where the run states it.** A host that
    sends a pull-request event names the base branch in the environment, free
    and with no credential, and a change stacked on a sibling branch is held to
    its own base and not to the default one -- which would otherwise count the
    sibling's lines as this change's and refuse on lines its author never wrote.
    ⚠️ The variable is the one fact about the host this file reads directly;
    everything else about the base is derived below.

    Where nothing states it, `claim.integration_branch` answers -- the one
    derivation this repository has for which branch that is, the surface
    carrying no key for it.
    """
    stated = os.environ.get("GITHUB_BASE_REF")
    if stated:
        return stated[len("refs/heads/"):] if stated.startswith("refs/heads/") else stated

    sys.path.insert(0, os.path.join(root, "plugins", "mjolnir", "scripts"))
    try:
        import claim as carrier  # noqa: PLC0415  -- the one derivation, not a second
    except ImportError as exc:
        raise Unreadable(f"the claim carrier could not be imported: {exc}") from exc
    try:
        return carrier.integration_branch(root, "origin")
    except Exception as exc:  # the carrier names what it could not derive
        raise Unreadable(f"the integration branch could not be derived: {exc}") from exc


def _base(root: str) -> str:
    """The merge base with that branch, or a refusal naming what it could not read."""
    branch = _branch(root)
    head = _git(root, "rev-parse", "HEAD").stdout.strip()
    for ref in (f"origin/{branch}", branch):
        resolved = _git(root, "rev-parse", "--verify", "--quiet", ref)
        if resolved.returncode != 0:
            continue
        found = _git(root, "merge-base", ref, "HEAD")
        base = found.stdout.strip()
        if found.returncode != 0 or not base:
            continue
        # ⛔ A base that **is** the head establishes no added lines, and the run
        # would then report green over a change it never read. The reachable way
        # in is a checkout with no remote, where the carrier's last fallback is
        # this branch's own name -- so the one state this check may not report
        # as green is refused here rather than printed as nothing to hold.
        if base == head:
            raise Unreadable(
                f"the merge base with `{branch}` is this change's own head, so no line "
                "reads as added and the rule would hold nothing. Name the base branch, or "
                "fetch one this branch actually diverges from."
            )
        return base
    raise Unreadable(
        f"no merge base against `{branch}` could be found, so which lines this change "
        "adds cannot be established. In a run, fetch the base branch with depth 0; by "
        "hand, fetch the remote."
    )


def read_change(root: str, patterns: tuple[str, ...] = ("*.md",)) -> Change:
    """The post-image text and added line numbers for every file this change touches.

    ⚠️ Which files is a **parameter**, and this check's own call passes markdown.
    A sibling holding another rule over the same lines reads them through this
    derivation rather than standing up a second one: the base, the hunk grammar
    and the two traps below are the part that is hard to get right, and two
    copies of them are free to disagree about which lines a change added.
    """
    base = _base(root)
    # ⛔ `core.quotePath=false`, because a path git decides to quote does not
    # match the header grammar below -- and a header the grammar misses leaves
    # the previous file's name standing, which records one file's added lines
    # against another: the offending document unread and an innocent one refused
    # on lines nobody wrote. The reset on `diff --git` below is the other half.
    diff = _git(root, "-c", "core.quotePath=false", "diff", "--unified=0", "--no-color",
                "--diff-filter=ACMR", base, "--", *patterns)
    if diff.returncode != 0:
        raise Unreadable(f"the diff against `{base[:12]}` could not be read: {diff.stderr.strip()}")

    added: dict[str, set[int]] = {}
    path = None
    for line in diff.stdout.splitlines():
        if line.startswith("diff --git "):
            path = None
            continue
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
        lines = split_lines(change.text[path])
        prose = prose_lines(change.text[path])
        for number in sorted(change.added.get(path, ())):
            if number not in prose or number > len(lines):
                continue
            yield path, number, lines[number - 1], shown_only(lines[number - 1])


def _held_paragraphs(change: Change):
    """(path, the run's first line number, the run joined, and it set aside).

    ⛔ A pass record wrapped across two lines is the measured habit's own shape
    at this project's width -- the date on one line and the verb on the next --
    and a per-line grammar reads neither half. A run is consecutive **added**
    held lines, so a paragraph half written by this change is read as far as
    this change wrote it and no further, which is the rule's carve-out one
    granularity up.
    """
    for path in sorted(change.text):
        lines = split_lines(change.text[path])
        prose = prose_lines(change.text[path])
        run: list[tuple[int, str]] = []

        def flush(run=run, path=path):
            if len(run) > 1:
                joined = " ".join(line.strip() for _, line in run)
                return path, run[0][0], joined, shown_only(joined)
            return None

        for number in sorted(change.added.get(path, ())):
            line = lines[number - 1] if number <= len(lines) else ""
            contiguous = bool(run) and number == run[-1][0] + 1
            if number not in prose or not line.strip() or not (contiguous or not run):
                found = flush()
                if found:
                    yield found
                run.clear()
                if number in prose and line.strip():
                    run.append((number, line))
                continue
            run.append((number, line))
        found = flush()
        if found:
            yield found


def check_the_change_was_read(change: Change) -> list[str]:
    return [
        f"{entry}: is markdown this change touches and could not be read, so nothing below "
        "held it. A document the sweep cannot open is unheld, which is the one state this "
        "check may not report as green."
        for entry in change.unread
    ]


def check_no_dated_pass_record(change: Change) -> list[str]:
    problems = []
    reported: set[tuple[str, int]] = set()
    for path, number, line, cleaned in _held(change):
        heading = HEADING.match(line)
        if heading and DATED_HEADING.search(shown_only(heading.group("text"))):
            problems.append(
                f"{path}:{number}: a heading that is only a date is a per-pass section — "
                f"{' '.join(line.split())[:90]}"
            )
            reported.add((path, number))
            continue
        if DATED_PASS.search(cleaned):
            problems.append(
                f"{path}:{number}: a dated record of a pass — "
                f"{' '.join(line.split())[:90]}"
            )
            reported.add((path, number))

    # ⛔ Then the same grammar over each run of added lines, because the shape
    # this arm exists for is wrapped at this project's width and a per-line read
    # sees the date on one line and the verb on the next -- neither half a
    # match. A run whose own lines already reported is not reported twice.
    for path, number, _joined, cleaned in _held_paragraphs(change):
        if (path, number) in reported:
            continue
        found = DATED_PASS.search(cleaned)
        if found:
            problems.append(
                f"{path}:{number}: a dated record of a pass, wrapped across the lines "
                f"from here — {' '.join(found.group(0).split())[:90]}"
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
    # ⚠️ The document's **content** lines, not every element the split yields: a
    # text ending in a newline splits to a trailing empty string, and counting
    # that one in hands the next appended line a number the fixture already
    # calls added — which is precisely the line the carve-out exemption needs
    # left unadded. Measured twice, once per line-splitting change.
    added={
        "docs/planted.md": set(
            range(1, len(split_lines(A_WHOLE_DOCUMENT.rstrip("\n"))) + 1)
        )
    },
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


def _plant_wrapped_pass_record(change: Change) -> Change:
    """The measured habit at this project's width: the date and the verb apart.

    ⛔ Two lines, each green on its own, and the record is in neither half. A
    per-line grammar reported this document clean, which is what the paragraph
    arm exists for.
    """
    change.plant("The seven paragraphs were swept out of the document and the counts in")
    return change.plant("the table were brought current, on 2026-10-19.")


def _plant_a_fence_inside_a_longer_fence(change: Change) -> Change:
    """A fence shown inside a longer fence, with a violation after the inner one.

    ⛔ The green side of the fence exclusion, and the arm the marker tracking
    bought: under a bare toggle the inner ``` closes the outer block, and every
    line after it — including the violation — is read as prose. A document
    showing somebody what a fenced violation looks like is this file's own
    shape, so the false red it would take is the likely case.
    """
    change.text["docs/planted-fence.md"] = (
        "# A planted document\n"
        "\n"
        "````markdown\n"
        "```\n"
        "### Revalidation 2026-10-19\n"
        "```\n"
        "Previously the row argued the opposite.\n"
        "````\n"
    )
    change.added["docs/planted-fence.md"] = set(range(1, 9))
    return change


def _plant_a_line_separator(change: Change) -> Change:
    """A violation after a character git does not count as a line break.

    ⛔ `str.splitlines()` breaks on U+2028 and six more characters git reads as
    ordinary text, so the diff's line 3 and the file's line 3 stop being the
    same line — the violation goes green and every refusal after it names the
    wrong line. The plant carries the separator *before* the violation, which
    is the only arrangement that tells the two splittings apart.
    """
    change.text["docs/planted-separator.md"] = (
        "# A planted document\n"
        "A paragraph with a\u2028separator inside it.\n"
        "### Revalidation 2026-10-19\n"
    )
    change.added["docs/planted-separator.md"] = {1, 2, 3}
    return change


def _plant_frontmatter(change: Change) -> Change:
    """A violation inside a document's own frontmatter, which is metadata.

    The green side of the frontmatter exclusion, which had no plant on either
    side: with the exclusion disabled this reddens, and with the opener's
    field test removed its sibling plant above stops reddening.
    """
    change.text["docs/planted-frontmatter.md"] = (
        "---\nname: planted\nnote: previously 26 rows (was 70)\n---\n\n# A planted document\n"
    )
    change.added["docs/planted-frontmatter.md"] = {1, 2, 3, 4, 5, 6}
    return change


def _plant_a_leading_thematic_break(change: Change) -> Change:
    """A document opening on three dashes, which is not frontmatter.

    ⛔ Read as frontmatter, everything down to the next break is exempt, and a
    per-pass preamble is exactly what sits there.
    """
    change.text["docs/planted-break.md"] = (
        "---\n\n## A planted section\n\nPreviously the row argued the opposite.\n\n---\n"
    )
    change.added["docs/planted-break.md"] = {1, 2, 3, 4, 5, 6, 7}
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
    ("no dated record of a pass", "a pass record wrapped across two lines",
     _plant_wrapped_pass_record),
    ("no dated record of a pass", "a violation after a character git does not break on",
     _plant_a_line_separator),
    ("no clause whose subject is a previous pass", "a document opening on a thematic break",
     _plant_a_leading_thematic_break),
    ("no former value", "a parenthetical former value", _plant("70 rows are placed (was 26).")),
    ("no former value", "a `Was:` label opening a line",
     _plant("Was: inferred from the working directory, which § 1 forbids.")),
    ("no former value", "a figure stated as a movement",
     _plant("The plan carries 26 rows, down from 70.")),
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
# The green side of the scope, in two kinds and labelled as such. ⛔ **An
# exclusion** is something the check sets aside, and each of those was verified
# by disabling that exclusion and watching its plant redden -- an exemption
# nothing can fail is an exemption nobody checked. ⛔ **An omission** is a shape
# the grammar simply does not carry: there is nothing to disable, and what the
# plant asserts is that the grammar stays narrow. Calling both "verified by
# disabling its own exclusion" overstated three of the six.

EXEMPTIONS = [
    # ⛔ The rule's own carve-out, and the one this check exists inside: an
    # artifact's existing history is not this change's business. An exclusion,
    # verified by marking the line added and watching the arms redden.
    ("an exclusion: a violation the change did not write",
     _carry("Previously the row argued the opposite, and the count was 26 of them.")),
    ("an exclusion: a forbidden word shown in a code span",
     _plant("The clause this forbids is `previously`, and `(was 7)` is the other.")),
    ("an exclusion: a forbidden clause shown in a straight quotation",
     _plant('A clause whose subject is a pass — "this pass corrected the figure" — is one.')),
    ("an exclusion: the same clause shown in a curly quotation",
     _plant("A clause whose subject is a pass — “this pass corrected the figure” — is one.")),
    ("an exclusion: a violation inside real frontmatter", _plant_frontmatter),
    ("an exclusion: a fence shown inside a longer fence",
     _plant_a_fence_inside_a_longer_fence),
    # ⛔ Omissions, not exclusions: `landed`, `measured` and a date beside
    # today's figures are shapes the grammar never carries. Each states
    # something still true, which is the rule's sixth point, and each would
    # redden the moment the vocabulary grew -- which is what these assert.
    ("an omission: a landed record carried as an entry's content",
     _plant("✅ **#100 landed `abc1234`, 2026-10-20**, and the row keeps its argument.")),
    ("an omission: a live-status line carrying the date it was taken",
     _plant("**Live as of 2026-10-20: 70 open, 87 relations, zero violations.**")),
    ("an omission: a dated measurement that states something still true",
     _plant("Measured on 2026-10-19: sixteen changes landed through the carriers.")),
    ("an omission: a release heading carrying a date among other words",
     _plant("## v1.2.0 — March 3, 2026")),
    ("an omission: a role's own instruction about the pass before it",
     _plant("For each issue the report lists as filed since the last pass, run the test.")),
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

    # ⛔ Each exemption is read against the fixture's **own** result, and only
    # problems the plant introduced count. Measured: with one exclusion
    # disabled, all six exemptions reported WENT RED — because `run()` collects
    # every line of the fixture and one of its lines carries code spans — so a
    # regression in one exclusion read as six broken carve-outs, and the first
    # problem printed was not the planted line's.
    baseline = {
        problem for arm in run(change).values() for problem in arm
    }
    for label, plant in EXEMPTIONS:
        planted = plant(change.copy())
        found = [
            problem
            for arm in run(planted).values()
            for problem in arm
            if problem not in baseline
        ]
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
    "the ordering document, which lives outside every tree — is stated in "
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

    # ⛔ Two figures and not one. The lines a change adds and the lines this
    # check holds are different numbers -- a fence, frontmatter and a line the
    # working tree no longer carries are all added and none is held -- and
    # printing the first alone reports a reach the run did not have.
    added = sum(len(numbers) for numbers in change.added.values())
    held = sum(1 for _ in _held(change))
    print(
        f"\n{held} of {added} added line(s) held, across {len(change.text)} document(s), "
        f"against the merge base `{change.base[:12]}`. The rest are fenced, frontmatter, or "
        f"lines the working tree no longer carries."
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
