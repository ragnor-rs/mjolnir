#!/usr/bin/env python3
"""Hold the prose a change writes into a file to the floor the surface fixes for it.

The rule is `plugins/mjolnir/config/schema.md § 8 -> The floor under prose a
role writes into a file`, which states the three properties, the unit each is
read over, and which comments count as prose at all. ⛔ No line here restates
any of that, and nothing here decides it: a project's register and audience are
its own, and this check reaches only what the surface calls a floor.

⛔ **Only the lines this change adds are read.** That is the rule's own
carve-out, and it is the reason this check can exist at all without a sweep that
repaints the tree: the habits below are measurable in prose that predates them
and were measured there.

⛔ **Nothing is re-implemented that a sibling already carries.** The word list
and the emphasis grammar come from the reply's own check, and the diff, the
merge base and the markdown prose grammar come from the one that holds the lines
a change adds -- both imported, so a list reworded there is reworded here. What
is written here is grammar neither one has: which lines of a script are prose,
how a run of added lines is grouped, and how one file's words are read against a
document it cites.

⚠️ **Three arms, each holding one corner of its property.** The corners, the
measurements behind the three numbers in this file, and what is left to a reader
are recorded once, in `docs/single-source-of-truth.md` § The floor under file
prose. This docstring carries no copy of them.

Usage:
    check_prose_register.py              hold the prose this change writes
    check_prose_register.py --self-test  assert each arm reddens on each of its
                                         planted violations and stays green on
                                         each planted exemption, then hold the
                                         change
"""

from __future__ import annotations

import ast
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "plugins", "mjolnir", "scripts"))

import check_no_audit_trail as lines_a_change_adds  # noqa: E402 -- the one diff derivation
import check_reply_register as reply  # noqa: E402 -- the one word list and emphasis grammar

SURFACE = os.path.join("plugins", "mjolnir", "config", "schema.md")

# The subsection whose table this script reads, by the anchor the host would give
# its heading -- the bargain every citation of the surface already makes, and the
# one the reply's check struck for the table one subsection over.
PROPERTY_TABLE_ANCHOR = "the-floor-under-prose-a-role-writes-into-a-file"
CITATION = "schema § 8 → The floor under prose a role writes into a file"

# --- the three numbers, and what each was measured on ----------------------
#
# ⛔ No document carries any of them, and a run prints its own. Each was picked
# by reading this tree rather than by argument, and each errs toward the finding
# it misses -- the direction an arm that reddens a build has to err in. Why each
# number is where it is, the counts beside it, and what each one is a proxy for
# are the document's: `docs/single-source-of-truth.md` § The floor under file
# prose.

# A run of words repeated verbatim off a cited document. Twelve, which is past
# the length two writers reach separately.
RESTATEMENT_WORDS = 12

# Emphasis as a texture rather than as a mark: the length at which a marked line
# is no longer one of a few. Four, and the measurement is the document's.
EMPHASIS_LINES = 4

# Hedging, counted inside one paragraph. One, which this tree exceeds twice.
HEDGES_ALLOWED = 1

# --- grammar this file carries, because no sibling's fits the unit ---------

# A quotation, bounded for a **run of words** rather than for a clause, and
# **read across the wrap**. ⛔ Two departures from the sibling grammar, and both
# were measured on this file's own fixture. The sibling bounds a quotation at a
# clause's length, which is shorter than the shortest run this arm can match --
# a dozen quoted words run past it. And a quotation of that length does not fit
# on one line of a wrapped document, so a per-line pattern never closes it: the
# fixture's own quoted citation reddened, which is the exact shape every long
# quotation in this tree has. Quoting a cited document is how a document cites
# it; repeating it unquoted is the finding.
QUOTED = re.compile(r"\"[^\"]{0,400}\"|“[^”]{0,400}”|«[^»]{0,400}»", re.S)

# A docstring's opening and closing delimiter, which is syntax rather than a
# quotation. Blanked to its own width so no line number moves.
DOCSTRING_DELIMITER = re.compile(r"\"{3}|'{3}")

# An inline link, reduced to the text a reader reads: a destination is not prose,
# and a path repeated in two documents is a citation rather than a restatement.
LINK = re.compile(r"\[([^\]\n]*)\]\([^)\s]*\)")

# What a line may open with before its first word: a list marker, and the
# directive markers this repository writes. ⛔ A span marked at the start of a
# line is a term being defined, so the arm reads only what sits past the
# opening -- four defined terms are four marked lines and are no texture. Which
# of the two readings this tree bears out is the document's.
OPENER = re.compile(r"^[\s>]*(?:[-*+]\s+|\d+\.\s+)?(?:[⛔⚠️✅❌]️?\s*)*")

WORD = re.compile(r"[a-z0-9_]+")

# A whole-line comment, and a comment block is more than one of them in a row.
WHOLE_LINE_COMMENT = re.compile(r"^\s*#")

# A heading of a cited document, for the carve-out a citation needs: naming a
# section by its title repeats that title by rule.
MD_HEADING = re.compile(r"^\s{0,3}#{1,6}\s+(?P<text>.*)$")

# ⛔ Which files carry prose at all, by the rule's test rather than by what is
# convenient to parse: markdown, and every tracked file whose comment is a line
# beginning `#`. A workflow and a configuration are in that set and their
# comment blocks are read straight through exactly as a script's are -- this
# change's own first draft read scripts alone and left its own workflow
# unheld. A format with no comment at all, which here is JSON, is reached by
# nothing and is named in the document.
MARKDOWN, PYTHON = ".md", ".py"
HASH_COMMENT = (PYTHON, ".yaml", ".yml", ".toml", ".sh", ".cfg")
TRACKED = (f"*{MARKDOWN}",) + tuple(f"*{suffix}" for suffix in HASH_COMMENT)


def shown_only(text: str) -> str:
    """The text with code, quotations and link destinations set aside.

    ⛔ Every line break survives, because the callers below map words back to the
    line they were written on: a quotation replaced by one space would pull the
    rest of a document onto the line its quotation opened on, and every finding
    after it would name a line nobody can open.

    ⛔ **A docstring's own delimiter is syntax and is dropped first.** Three
    quote characters read as one empty pair and then an opener, so without this
    the grammar below runs to the end of the docstring and takes the text with
    it. What that cost, and the plant that found it, are in the document.
    """
    text = DOCSTRING_DELIMITER.sub("   ", text)
    text = LINK.sub(r"\1", lines_a_change_adds.CODE_SPAN.sub(" ", text))
    return QUOTED.sub(lambda found: re.sub(r"[^\n]", " ", found.group(0)), text)


def words(text: str) -> list[str]:
    """The word sequence of a line or a document, read the way both sides are."""
    return WORD.findall(shown_only(text).lower())


def numbered_words(numbered: list[tuple[int, str]]) -> list[tuple[str, int]]:
    """(word, the line it was written on) over a run of lines, cleaned as one text.

    ⛔ As one text and not line by line, which is what reads a quotation across
    the wrap. The lines are joined on the newline they were split at, so the
    blanking above keeps each word on its own line.
    """
    joined = shown_only("\n".join(line for _, line in numbered))
    out: list[tuple[str, int]] = []
    for offset, line in enumerate(joined.split("\n")):
        for word in WORD.findall(line.lower()):
            out.append((word, numbered[offset][0]))
    return out


# --- which lines of a file are prose ---------------------------------------


def comment_prose(text: str) -> tuple[set[int], str | None]:
    """(the prose line numbers of a commented file, and nothing it could not read).

    ⛔ Which lines those are is the rule's test rather than this file's choice,
    and what is written here is how one of its shapes is recognised: a run of
    whole-line comments longer than one. Everything the test calls annotation is
    what is left over.
    """
    lines = lines_a_change_adds.split_lines(text)
    held: set[int] = set()
    run: list[int] = []
    for number, line in enumerate(lines, 1):
        if WHOLE_LINE_COMMENT.match(line):
            run.append(number)
            continue
        if len(run) > 1:
            held.update(run)
        run = []
    if len(run) > 1:
        held.update(run)
    return held, None


def python_prose(text: str) -> tuple[set[int], str | None]:
    """A script's prose: its comment blocks, and whatever `ast` calls a docstring.

    ⚠️ A file that does not parse yields **no** prose and a reason, never an
    empty set on its own: a script the sweep cannot read is unheld, and that is
    the one state a check may not report as green.
    """
    lines = lines_a_change_adds.split_lines(text)
    held = comment_prose(text)[0]
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError) as exc:
        return set(), f"{type(exc).__name__}: {exc}"
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        body = node.body
        if not (body and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)):
            continue
        at = body[0]
        for number in range(at.lineno, (at.end_lineno or at.lineno) + 1):
            if number <= len(lines) and lines[number - 1].strip():
                held.add(number)
    return held, None


def prose_of(path: str, text: str) -> tuple[set[int], str | None]:
    if path.endswith(PYTHON):
        return python_prose(text)
    if path.endswith(HASH_COMMENT):
        return comment_prose(text)
    return lines_a_change_adds.prose_lines(text), None


def read_straight_through(path: str, line: str) -> bool:
    """Is this prose line one a density is read over?

    A table row and a heading sit outside the **paragraph** arms and inside the
    rest, which is the division the reply's own check already draws and for the
    reason it draws it: marking up a cell is what the rule one row over asks
    for, so an arm reading rows for a texture reddens on a sibling rule.
    """
    if not path.endswith(MARKDOWN):
        return True
    return not (reply.TABLE_ROW.match(line) or reply.HEADING.match(line))


# --- the change, and the documents it cites --------------------------------


class Prose:
    """What this change wrote, and the documents its files cite.

    `change` carries the post-image text and the added line numbers; `documents`
    is every tracked document's text, which the restatement arm needs whole --
    a file restating one this change did not touch is the common case, and a
    haystack limited to the touched set would miss every one of them.
    """

    def __init__(self, change, documents: dict[str, str]):
        self.change = change
        self.documents = documents
        self.unparsed: dict[str, str] = {}
        self.prose: dict[str, set[int]] = {}
        self._read: dict[str, tuple[list[str], list[tuple[str, ...]]]] = {}
        for path, text in change.text.items():
            held, why = prose_of(path, text)
            self.prose[path] = held
            if why:
                self.unparsed[path] = why

    def haystack(self, document: str) -> tuple[list[str], list[tuple[str, ...]]]:
        """(the cited document's own word sequence, its headings), read once."""
        if document not in self._read:
            text = self.documents[document]
            self._read[document] = (
                [word for word, _ in numbered_words(
                    _prose_lines(document, text, prose_of(document, text)[0])
                )],
                headings_of(text),
            )
        return self._read[document]

    def held(self):
        """(path, line number, the line) for every added prose line, in order."""
        for path in sorted(self.change.text):
            lines = lines_a_change_adds.split_lines(self.change.text[path])
            for number in sorted(self.change.added.get(path, ())):
                if number > len(lines) or number not in self.prose.get(path, ()):
                    continue
                yield path, number, lines[number - 1]

    def paragraphs(self):
        """(path, first line number, the lines) for each run of added prose lines.

        A run is consecutive **added** prose, so a paragraph half written by this
        change is read as far as this change wrote it. ⛔ Grouped here rather
        than taken from the sibling that also groups added lines: that one joins
        its run into one string, because its grammar reads across a wrap, where
        every arm here counts per line and needs the lines kept apart.
        """
        for path in sorted(self.change.text):
            lines = lines_a_change_adds.split_lines(self.change.text[path])
            run: list[tuple[int, str]] = []
            for number in sorted(self.change.added.get(path, ())):
                line = lines[number - 1] if number <= len(lines) else ""
                held = (number in self.prose.get(path, ()) and line.strip()
                        and read_straight_through(path, line))
                if not held or (run and number != run[-1][0] + 1):
                    if run:
                        yield path, run[0][0], [text for _, text in run]
                    run = []
                if held:
                    run.append((number, line))
            if run:
                yield path, run[0][0], [text for _, text in run]

    def cites(self, path: str) -> list[str]:
        """The tracked documents this file names, by either of the two path forms.

        ⚠️ A path and nothing else resolves here, because one file name can
        belong to several tracked files and guessing which would be worse than
        the gap. The gap is recorded where the gaps are.
        """
        text = self.change.text.get(path, "")
        here = os.path.dirname(path)
        found = []
        for document in sorted(self.documents):
            if document == path:
                continue
            relative = os.path.relpath(document, here) if here else document
            if document in text or relative.replace(os.sep, "/") in text:
                found.append(document)
        return found


def headings_of(text: str) -> list[tuple[str, ...]]:
    """Each heading of a document as a word tuple, for the citation carve-out."""
    found = []
    for line in text.splitlines():
        match = MD_HEADING.match(line)
        if match:
            found.append(tuple(words(match.group("text"))))
    return found


def _inside(run: tuple[str, ...], heading: tuple[str, ...]) -> bool:
    size = len(run)
    return size <= len(heading) and any(
        heading[at:at + size] == run for at in range(len(heading) - size + 1)
    )


def repeated_runs(needle: list[tuple[str, int]], haystack: list[str], floor: int,
                  headings: list[tuple[str, ...]]) -> list[tuple[int, int, str]]:
    """(length, the line it starts on, the run) for each maximal repeat of `floor`+ words.

    Maximal rather than every window, so one restated sentence is one finding
    carrying its own length rather than a window count nobody can act on. A run
    that sits inside a heading of the cited document is a citation and is
    dropped: naming a section repeats its title by rule.
    """
    where: dict[str, list[int]] = {}
    for at, word in enumerate(haystack):
        where.setdefault(word, []).append(at)
    sequence = [word for word, _ in needle]
    found: list[tuple[int, int, str]] = []
    at = 0
    while at < len(sequence):
        longest = 0
        for start in where.get(sequence[at], ()):
            size = 0
            while (at + size < len(sequence) and start + size < len(haystack)
                   and sequence[at + size] == haystack[start + size]):
                size += 1
            longest = max(longest, size)
        if longest < floor:
            at += 1
            continue
        run = tuple(sequence[at:at + longest])
        line = needle[at][1]
        at += longest
        if any(_inside(run, heading) for heading in headings):
            continue
        found.append((len(run), line, " ".join(run)))
    return found


# --- the arms ---------------------------------------------------------------


def check_the_change_was_read(prose: Prose) -> list[str]:
    problems = [
        f"{entry}: is a file this change touches and could not be read, so nothing below held "
        "it. A file the sweep cannot open is unheld, which is the one state this check may not "
        "report as green."
        for entry in prose.change.unread
    ]
    problems += [
        f"{path}: this change touches it and it does not parse ({why}), so its comments and "
        "docstrings were held by nothing."
        for path, why in sorted(prose.unparsed.items())
    ]
    return problems


def check_no_restatement(prose: Prose) -> list[str]:
    """Words this change repeats off a document the file it wrote them in cites.

    ⛔ The needle is the file's **whole** prose and the finding is filtered to
    runs starting on a line this change added, rather than the needle being the
    added lines alone. A quotation is read across the wrap, so the text it is
    read in has to be the one the writer wrote: cut to the added lines, a
    citation quoted from the line above reopens as an unclosed quotation and the
    carve-out stops holding on exactly the edit that adds to a quoting paragraph.
    """
    problems = []
    for path in sorted(prose.change.text):
        cited = prose.cites(path)
        added = prose.change.added.get(path, set())
        if not cited or not added:
            continue
        needle = numbered_words(_prose_lines(path, prose.change.text[path], prose.prose[path]))
        for document in cited:
            # ⚠️ Read once per document and not once per citing file. Every file
            # here cites the same two or three documents, so the uncached shape
            # re-read each of them for each of them.
            haystack, headings = prose.haystack(document)
            for size, number, run in repeated_runs(needle, haystack, RESTATEMENT_WORDS, headings):
                if number not in added:
                    continue
                problems.append(
                    f"{path}:{number}: {size} words repeated off {document}, which this file "
                    f"cites — \"{run[:90]}\". Cite the section, or quote it where the words "
                    "themselves are the point."
                )
    return problems


def _prose_lines(path: str, text: str, held: set[int]) -> list[tuple[int, str]]:
    """(line number, line) for a file's own prose, so a fenced example is no haystack."""
    lines = lines_a_change_adds.split_lines(text)
    return [(number, lines[number - 1]) for number in sorted(held) if number <= len(lines)]


def check_emphasis_is_not_the_texture(prose: Prose) -> list[str]:
    problems = []
    for path, number, run in prose.paragraphs():
        if len(run) < EMPHASIS_LINES:
            continue
        if all(_emphasis_past_the_opening(line) for line in run):
            spans = sum(len(reply.EMPHASIS.findall(line)) for line in run)
            problems.append(
                f"{path}:{number}: {spans} emphasised spans, one past the opening of every one of "
                f"{len(run)} prose lines, reads as the paragraph's texture rather than as a mark "
                f"on a load-bearing fact — {' '.join(run[0].split())[:70]}"
            )
    return problems


def _emphasis_past_the_opening(line: str) -> bool:
    cleaned = lines_a_change_adds.CODE_SPAN.sub(" ", line)
    opens = len(OPENER.match(cleaned).group(0))
    return any(span.start() > opens for span in reply.EMPHASIS.finditer(cleaned))


def check_uncertainty_is_stated_once(prose: Prose) -> list[str]:
    problems = []
    for path, number, run in prose.paragraphs():
        hits = reply.HEDGE.findall(shown_only("\n".join(run)))
        if len(hits) > HEDGES_ALLOWED:
            problems.append(
                f"{path}:{number}: {len(hits)} hedges in one paragraph "
                f"({', '.join(repr(h) for h in hits[:4])}) reads as hedging throughout rather "
                f"than as uncertainty stated plainly, once (over {HEDGES_ALLOWED})."
            )
    return problems


# Which property of the surface's table each arm holds, and the corner of it the
# arm reaches. ⛔ Every property the table carries is here or in RESIDUE, and the
# accounting arm below holds both directions: a row added to the surface with no
# arm and no stated reason reddens at the moment it is added, which is the
# direction the reply's own check runs in one subsection over.
HELD = {
    "Restatement": [("no restatement of a cited document", check_no_restatement)],
    "Emphasis": [("emphasis is not the paragraph's texture", check_emphasis_is_not_the_texture)],
    "Uncertainty": [("uncertainty is stated once", check_uncertainty_is_stated_once)],
}

# ⚠️ Load-bearing rather than descriptive, as the reply's own residue is: a
# property held in part must also appear above, and one held by nothing must
# not. The reasons live in the document and are not copied here.
WHOLE, PARTIAL = "whole", "partial"
RESIDUE = {
    "Restatement": PARTIAL,
    "Emphasis": PARTIAL,
    "Uncertainty": PARTIAL,
}


def read_properties(text: str) -> list[str]:
    """The first column of the floor's table, read out of the surface.

    Found by the anchor its subsection slugs to, so a reworded heading is a
    change this file does not have to be edited for as long as the anchor
    survives. Reading stops at the next heading of any level.
    """
    found, fenced, properties = False, False, []
    for line in text.splitlines():
        if reply.FENCE.match(line):
            fenced = not fenced
            continue
        if fenced:
            continue
        if reply.HEADING.match(line):
            if found:
                break
            title = re.sub(r"^\s*#{1,6}\s+", "", line).strip().lower().replace("`", "")
            found = re.sub(r"[^\w\s-]", "", title).replace(" ", "-") == PROPERTY_TABLE_ANCHOR
            continue
        if not found or not reply.TABLE_ROW.match(line):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        head = re.sub(r"[*`]", "", cells[0]) if cells else ""
        if not head or set(head) <= set("-: ") or head == "Property":
            continue
        if head not in properties:
            properties.append(head)
    return properties


def check_every_property_is_accounted_for(text: str) -> list[str]:
    declared = read_properties(text)
    if not declared:
        return [
            f"{os.path.basename(SURFACE)}: no table was found under `{PROPERTY_TABLE_ANCHOR}`, so "
            "this script holds nothing. Either the subsection moved or its heading no longer slugs "
            "to that anchor."
        ]
    problems = []
    accounted = set(HELD) | set(RESIDUE)
    for name in declared:
        if name not in accounted:
            problems.append(
                f"{os.path.basename(SURFACE)}: the floor's `{name}` property is held by no arm and "
                "no reason is stated for leaving it unheld."
            )
    for name in sorted(accounted - set(declared)):
        problems.append(
            f"{name}: this script holds or excuses a property the floor's table does not carry. "
            "An arm with nothing behind it is a copy of a rule that has moved."
        )
    for name, extent in RESIDUE.items():
        if extent == PARTIAL and name not in HELD:
            problems.append(
                f"{name}: excused in part, which says the rest of it is held — and no arm holds "
                "it. A half-excused property with no arm is a limit stated over nothing."
            )
        if extent == WHOLE and name in HELD:
            problems.append(
                f"{name}: excused whole and also held by an arm. One of the two is wrong, and the "
                "document states whichever this file does not."
            )
    return problems


CHECKS = [("the files this change touches were read", check_the_change_was_read)] + [
    (name, arm) for tests in HELD.values() for name, arm in tests
]


# --- what the run reports rather than holds --------------------------------
#
# ⛔ No threshold is applied to either figure. What a change writes and how
# densely it writes it is a measurement, and a budget hardcoded here would be
# the judgement-kept-in-sync this repository refuses everywhere else.


def measured(prose: Prose) -> list[tuple[str, int, int, int, int]]:
    """(path, added, prose lines, emphasised spans, hedges) per file this change touches."""
    rows = []
    for path in sorted(prose.change.text):
        held = [(number, line) for p, number, line in prose.held() if p == path]
        body = shown_only("\n".join(line for _, line in held))
        rows.append((
            path,
            len(prose.change.added.get(path, ())),
            len(held),
            sum(len(reply.EMPHASIS.findall(line)) for _, line in held),
            len(reply.HEDGE.findall(body)),
        ))
    return rows


# --- the fixture, and the plants against it --------------------------------
#
# A fixture rather than the live change, so every assertion holds on a clean
# branch, with no network, and says the same thing on every branch.

A_CITED_DOCUMENT = (
    "# A planted document that others cite\n"
    "\n"
    "## A planted section whose title is long enough to be repeated by anyone citing it\n"
    "\n"
    "The planted authority states this sentence once, and it is long enough that a dozen of its\n"
    "words in a row could not be two writers arriving at the same clause by accident.\n"
    "\n"
    "A second planted sentence, carrying nothing a citing file has any reason to repeat at all.\n"
)

A_DOCUMENT = (
    "# A planted citing document\n"
    "\n"
    "The rule is [one planted section](planted-cited.md#a-planted-section-whose-title-is-long-"
    "enough-to-be-repeated-by-anyone-citing-it), and the floor it carries is cited rather than\n"
    "stated twice.\n"
    "\n"
    "⛔ **A paragraph may mark one fact** and then say the rest of what it has to say in plain\n"
    "sentences, which is this document's own shape.\n"
    "\n"
    "The authority is quoted where its words are the point: \"The planted authority states this\n"
    "sentence once, and it is long enough that a dozen of its words in a row could not be two\n"
    "writers arriving at the same clause by accident.\"\n"
    "\n"
    "| Property | A planted cell |\n"
    "|---|---|\n"
    "| **A term** | **A second term**, bolded as a cell's content is |\n"
    "\n"
    "One hedge is stated plainly: the planted count may be wrong on a longer document.\n"
    "\n"
    "```\n"
    "Previously the planted figure was 26, and perhaps possibly arguably it might be 70.\n"
    "```\n"
)

A_SCRIPT = (
    '#!/usr/bin/env python3\n'
    '"""A planted script whose own prose is held.\n'
    '\n'
    'The rule it implements lives in docs/planted-cited.md, which it cites rather\n'
    'than restating.\n'
    '"""\n'
    '\n'
    '# A planted comment block of more than one whole line, which is prose a\n'
    '# reader reads straight through, and which says what the code below is for.\n'
    'PLANTED = 1  # a trailing comment, annotation on this line of data\n'
    '\n'
    '# a lone whole-line comment, read with the statement it sits against\n'
    'ALSO_PLANTED = "perhaps possibly arguably it might be somewhat wrong"\n'
)

A_WORKFLOW = (
    "# A planted workflow, whose comment block is prose a reader reads straight through.\n"
    "#\n"
    "# The rule it runs is in docs/planted-cited.md, cited here and stated there.\n"
    "\n"
    "on:\n"
    "  pull_request:   # annotation on this line of data\n"
)

TRACKED_DOCUMENTS = {"docs/planted-cited.md": A_CITED_DOCUMENT}
FIXTURE_FILES = {
    "docs/planted.md": A_DOCUMENT,
    "tools/planted.py": A_SCRIPT,
    # ⛔ The third reader gets a planted file of its own, because a kind with no
    # plant is a kind nothing asserts -- and this one shipped unasserted once,
    # which the document records.
    ".github/workflows/planted.yml": A_WORKFLOW,
}


def fixture() -> Prose:
    """The whole fixture, every line of it marked added.

    ⛔ Every line, so the green side is asserted rather than passing for being
    out of scope: the quotation, the cell of bolded terms, the one hedge, the
    fenced violation, the trailing comment and the lone comment line all have to
    stay green while held. ⚠️ The added set is **derived** from each text rather
    than written as a range, because a range longer than the file swallows the
    next line a plant appends -- which is the line an exemption needs left
    unadded.
    """
    change = lines_a_change_adds.Change(
        base="0" * 40,
        text=dict(FIXTURE_FILES),
        added={
            path: set(range(1, len(lines_a_change_adds.split_lines(text.rstrip("\n"))) + 1))
            for path, text in FIXTURE_FILES.items()
        },
        unread=[],
    )
    return Prose(change, dict(TRACKED_DOCUMENTS))


THE_RESTATED_SENTENCE = (
    "The planted authority states this sentence once, and it is long enough that a dozen of its "
    "words in a row could not be two writers arriving at the same clause by accident."
)

# A sentence of comparable length sharing no run with the authority above, for
# the plant that asserts an uncited document is no haystack.
THE_UNCITED_SENTENCE = (
    "Nobody points anywhere near this paragraph, whose wording overlaps nothing an adopting "
    "project would ever go looking for under some other heading entirely."
)


def _plant(line: str, path: str = "docs/planted.md"):
    def apply(prose: Prose) -> Prose:
        prose.change.plant(line, path)
        return refreshed(prose)

    return apply


def _carry(line: str, path: str = "docs/planted.md"):
    def apply(prose: Prose) -> Prose:
        prose.change.carry(line, path)
        return refreshed(prose)

    return apply


def refreshed(prose: Prose) -> Prose:
    """The same change, with each file's prose lines read again.

    ⛔ Needed because a plant appends to the text after the prose map was built,
    and a map built once would leave every planted line outside the set the arms
    walk -- which is a plant that reddens nothing while reporting that it did.
    """
    return Prose(prose.change, prose.documents)


def _plant_unreadable(prose: Prose) -> Prose:
    prose.change.unread.append("docs/deleted-without-git-rm.md (no such file)")
    return prose


def _plant_a_script_that_does_not_parse(prose: Prose) -> Prose:
    prose.change.text["tools/planted-broken.py"] = '"""A planted docstring."""\ndef (\n'
    prose.change.added["tools/planted-broken.py"] = {1, 2}
    return refreshed(prose)


def _plant_a_restated_docstring(prose: Prose) -> Prose:
    """The measured habit, in the place it was measured: a script's own prose."""
    prose.change.text["tools/planted.py"] = (
        A_SCRIPT + f'\n\ndef planted():\n    """{THE_RESTATED_SENTENCE}"""\n    return 1\n'
    )
    prose.change.added["tools/planted.py"] = set(
        range(1, len(lines_a_change_adds.split_lines(prose.change.text["tools/planted.py"])) + 1)
    )
    return refreshed(prose)


def _plant_a_restated_comment_block(prose: Prose) -> Prose:
    """Two whole comment lines, which is the comment test's red side."""
    prose.change.text["tools/planted.py"] = (
        A_SCRIPT + "\n# " + THE_RESTATED_SENTENCE[:90] + "\n# " + THE_RESTATED_SENTENCE[90:] + "\n"
    )
    prose.change.added["tools/planted.py"] = set(
        range(1, len(lines_a_change_adds.split_lines(prose.change.text["tools/planted.py"])) + 1)
    )
    return refreshed(prose)


def _plant_a_restated_workflow_comment(prose: Prose) -> Prose:
    """The same two-line comment rule, in a file that carries no code at all."""
    path = ".github/workflows/planted.yml"
    prose.change.text[path] = (
        A_WORKFLOW + "\n# " + THE_RESTATED_SENTENCE[:90] + "\n# " + THE_RESTATED_SENTENCE[90:]
        + "\n"
    )
    prose.change.added[path] = set(
        range(1, len(lines_a_change_adds.split_lines(prose.change.text[path])) + 1)
    )
    return refreshed(prose)


def _plant_a_restated_table_cell(prose: Prose) -> Prose:
    """A row restates as readily as a sentence, and a row is in this arm's scope."""
    return _plant(f"| a planted row | {THE_RESTATED_SENTENCE} |")(prose)


def _plant_emphasis_as_the_texture(prose: Prose) -> Prose:
    run = "".join(
        f"A planted line {number} whose **own emphasis** sits past its opening.\n"
        for number in range(EMPHASIS_LINES)
    )
    prose.change.text["docs/planted.md"] += "\n" + run
    first = len(lines_a_change_adds.split_lines(prose.change.text["docs/planted.md"])) - \
        EMPHASIS_LINES
    prose.change.added["docs/planted.md"].update(range(first, first + EMPHASIS_LINES + 1))
    return refreshed(prose)


def _plant_emphasis_in_a_comment_block(prose: Prose) -> Prose:
    """The same arm over a script's prose, which is the other surface it reaches."""
    block = "".join(
        f"# A planted line {number} whose **own emphasis** sits past its opening.\n"
        for number in range(EMPHASIS_LINES)
    )
    prose.change.text["tools/planted.py"] = A_SCRIPT + "\n" + block
    prose.change.added["tools/planted.py"] = set(
        range(1, len(lines_a_change_adds.split_lines(prose.change.text["tools/planted.py"])) + 1)
    )
    return refreshed(prose)


def _plant_hedging(prose: Prose) -> Prose:
    return _plant(
        "The planted figure is perhaps wrong, and it may be somewhat narrow as well."
    )(prose)


VIOLATIONS = [
    ("the files this change touches were read", "a file the sweep cannot open", _plant_unreadable),
    ("the files this change touches were read", "a script that does not parse",
     _plant_a_script_that_does_not_parse),
    ("no restatement of a cited document", "a sentence repeated in a document's prose",
     _plant(THE_RESTATED_SENTENCE)),
    ("no restatement of a cited document", "the measured habit: a restating docstring",
     _plant_a_restated_docstring),
    ("no restatement of a cited document", "a restating comment block",
     _plant_a_restated_comment_block),
    ("no restatement of a cited document", "a restating comment block in a workflow",
     _plant_a_restated_workflow_comment),
    ("no restatement of a cited document", "a restating table cell", _plant_a_restated_table_cell),
    ("emphasis is not the paragraph's texture", "every line of a paragraph marked",
     _plant_emphasis_as_the_texture),
    ("emphasis is not the paragraph's texture", "the same, inside a script's comment block",
     _plant_emphasis_in_a_comment_block),
    ("uncertainty is stated once", "two hedges in one paragraph", _plant_hedging),
]


# --- the planted exemptions -------------------------------------------------
#
# ⛔ Two kinds, labelled apart. **An exclusion** is something an arm sets aside,
# and each was verified by disabling that exclusion and watching its plant
# redden. **An omission** is a shape no grammar here carries: there is nothing to
# disable, and the plant asserts the grammar stays narrow.

def _plant_a_quoted_restatement(prose: Prose) -> Prose:
    return _plant(f"The authority states it: \"{THE_RESTATED_SENTENCE}\"")(prose)


def _plant_a_restatement_in_a_code_span(prose: Prose) -> Prose:
    return _plant(f"The forbidden span is `{THE_RESTATED_SENTENCE}`.")(prose)


def _plant_a_cited_heading(prose: Prose) -> Prose:
    """A section named by its title, which repeats that title by rule."""
    return _plant(
        "The rule is § A planted section whose title is long enough to be repeated by anyone "
        "citing it, and nothing here states it twice."
    )(prose)


def _plant_a_restatement_of_an_uncited_document(prose: Prose) -> Prose:
    """An omission: the arm reads a file against what that file cites, and no more.

    ⚠️ The sentence is one the **authority does not carry**, measured rather than
    assumed: planted as a reworded copy of the authority's own, it matched the
    authority on the dozen words the rewording left alone, and this exemption
    reported WENT RED for the plant's shape rather than for the arm's behaviour.
    """
    prose.documents["docs/planted-uncited.md"] = (
        "# A planted document nobody cites\n\n" + THE_UNCITED_SENTENCE + "\n"
    )
    return _plant(THE_UNCITED_SENTENCE)(prose)


def _plant_a_fenced_restatement(prose: Prose) -> Prose:
    prose.change.text["docs/planted.md"] += f"\n```\n{THE_RESTATED_SENTENCE}\n```\n"
    first = len(lines_a_change_adds.split_lines(prose.change.text["docs/planted.md"])) - 4
    prose.change.added["docs/planted.md"].update(range(first, first + 5))
    return refreshed(prose)


def _plant_a_term_list(prose: Prose) -> Prose:
    """The measured shape: defined terms opening their own lines, three of them."""
    run = "".join(
        f"- **A planted term {number}** is what the line goes on to define in plain words.\n"
        for number in range(EMPHASIS_LINES + 1)
    )
    prose.change.text["docs/planted.md"] += "\n" + run
    first = len(lines_a_change_adds.split_lines(prose.change.text["docs/planted.md"])) - \
        EMPHASIS_LINES - 1
    prose.change.added["docs/planted.md"].update(range(first, first + EMPHASIS_LINES + 2))
    return refreshed(prose)


def _plant_a_paragraph_with_one_plain_line(prose: Prose) -> Prose:
    run = "".join(
        f"A planted line {number} whose **own emphasis** sits past its opening.\n"
        for number in range(EMPHASIS_LINES)
    ) + "A planted line carrying no emphasis at all, which is what the arm asks of one line.\n"
    prose.change.text["docs/planted.md"] += "\n" + run
    first = len(lines_a_change_adds.split_lines(prose.change.text["docs/planted.md"])) - \
        EMPHASIS_LINES - 1
    prose.change.added["docs/planted.md"].update(range(first, first + EMPHASIS_LINES + 2))
    return refreshed(prose)


def _plant_a_trailing_comment(prose: Prose) -> Prose:
    """Annotation on a line of data, by the surface's own test."""
    return _plant(
        f'PLANTED_AGAIN = 2  # {THE_RESTATED_SENTENCE}', "tools/planted.py"
    )(prose)


def _plant_a_lone_comment(prose: Prose) -> Prose:
    prose.change.text["tools/planted.py"] += f"\nALSO = 3\n# {THE_RESTATED_SENTENCE}\nAND = 4\n"
    first = len(lines_a_change_adds.split_lines(prose.change.text["tools/planted.py"])) - 4
    prose.change.added["tools/planted.py"].update(range(first, first + 5))
    return refreshed(prose)


def _plant_code_carrying_a_violation(prose: Prose) -> Prose:
    """A string literal is not prose: the arms read comments and docstrings."""
    return _plant(f'PLANTED_STRING = "{THE_RESTATED_SENTENCE}"', "tools/planted.py")(prose)


EXEMPTIONS = [
    ("an exclusion: a violation the change did not write", _carry(THE_RESTATED_SENTENCE)),
    ("an exclusion: a restatement inside a quotation, which is how a document cites one",
     _plant_a_quoted_restatement),
    ("an exclusion: a restatement inside a code span", _plant_a_restatement_in_a_code_span),
    ("an exclusion: a restatement inside a fenced block", _plant_a_fenced_restatement),
    ("an exclusion: a section named by its own long title", _plant_a_cited_heading),
    ("an omission: words shared with a document this file does not cite",
     _plant_a_restatement_of_an_uncited_document),
    ("an omission: defined terms opening their lines, which is the Structure shape",
     _plant_a_term_list),
    ("an omission: a paragraph with one unmarked line", _plant_a_paragraph_with_one_plain_line),
    ("an exclusion: a trailing comment, which annotates its line of data",
     _plant_a_trailing_comment),
    ("an exclusion: a lone whole-line comment", _plant_a_lone_comment),
    ("an omission: a violation in code rather than in prose", _plant_code_carrying_a_violation),
]


# --- the plants against the surface ----------------------------------------
#
# ⛔ No plant names the content it plants into. A plant written against a spelled
# -out row or heading plants nothing the moment either is reworded, and then the
# self-test prints STAYED GREEN for an edit that was not a defect.


def _row_of(text: str, name: str) -> str:
    for line in text.splitlines():
        if reply.TABLE_ROW.match(line):
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if cells and re.sub(r"[*`]", "", cells[0]) == name:
                return line
    raise AssertionError(f"no row for {name!r} to plant against")


def _heading_of(text: str) -> str:
    for line in text.splitlines():
        if reply.HEADING.match(line):
            title = re.sub(r"^\s*#{1,6}\s+", "", line).strip().lower().replace("`", "")
            if re.sub(r"[^\w\s-]", "", title).replace(" ", "-") == PROPERTY_TABLE_ANCHOR:
                return line
    raise AssertionError("no heading carrying the floor table's anchor")


def _plant_unaccounted_property(text: str) -> str:
    row = _row_of(text, read_properties(text)[0])
    return text.replace(row, row + "\n| Cadence | A rhythm | one sentence |")


def _plant_renamed_property(text: str) -> str:
    held = next(name for name in read_properties(text) if name in HELD)
    row = _row_of(text, held)
    return text.replace(row, row.replace(held, f"{held}Renamed", 1))


def _plant_removed_property(text: str) -> str:
    """The other direction alone: an arm whose property the table stopped carrying."""
    held = next(name for name in read_properties(text) if name in HELD)
    return text.replace(_row_of(text, held) + "\n", "")


def _plant_renamed_heading(text: str) -> str:
    heading = _heading_of(text)
    return text.replace(heading, re.sub(r"\bfloor\b", "floors", heading))


SURFACE_PLANTS = [
    ("a property with no arm and no stated reason", _plant_unaccounted_property),
    ("a renamed property, leaving an arm with nothing behind it", _plant_renamed_property),
    ("a held property the table stopped carrying", _plant_removed_property),
    ("a subsection whose heading no longer slugs to the anchor", _plant_renamed_heading),
]


def run(prose: Prose) -> dict[str, list[str]]:
    return {name: arm(prose) for name, arm in CHECKS}


def self_test(surface: str) -> int:
    by_name = dict(CHECKS)
    failures = 0

    print("Asserting the fixture's own premises, so no plant can pass vacuously:")
    base = fixture()
    for path in sorted(FIXTURE_FILES):
        cited = base.cites(path)
        held = [number for p, number, _ in base.held() if p == path]
        if cited == sorted(TRACKED_DOCUMENTS) and held:
            print(f"  ok                     {path}: cites the planted authority, "
                  f"{len(held)} prose line(s) held")
        else:
            print(f"  FAIL                   {path}: cites {cited}, holds {len(held)} line(s)")
            failures += 1
    held = prose_of("docs/planted-cited.md", A_CITED_DOCUMENT)[0]
    haystack = [word for word, _ in numbered_words(
        _prose_lines("docs/planted-cited.md", A_CITED_DOCUMENT, held)
    )]
    sentence = [(word, 1) for word in words(THE_RESTATED_SENTENCE)]
    if len(sentence) > RESTATEMENT_WORDS and repeated_runs(
        sentence, haystack, RESTATEMENT_WORDS, []
    ):
        print("  ok                     the restated sentence is in the authority, and long enough")
    else:
        print("  FAIL                   the restated sentence is not a run the arm could find")
        failures += 1

    named = {name for name, _, _ in VIOLATIONS}
    for name, _ in CHECKS:
        if name not in named:
            print(f"  NO PLANTED VIOLATION   {name}")
            failures += 1
    for name, label, _ in VIOLATIONS:
        if name not in by_name:
            print(f"  PLANT WITHOUT AN ARM   {name}: {label}")
            failures += 1

    whole = [problem for found in run(fixture()).values() for problem in found]
    if whole:
        print(f"  RED ON THE FIXTURE     {len(whole)} problem(s): {whole[0]}")
        failures += 1
    else:
        print("  green on               a change whose prose cites rather than restating")

    print(f"\nAsserting each arm reddens on its planted violations ({len(VIOLATIONS)}):")
    for name, label, plant in VIOLATIONS:
        if name not in by_name:
            continue
        if by_name[name](plant(fixture())):
            print(f"  red on                 {name}: {label}")
        else:
            print(f"  STAYED GREEN           {name}: {label}")
            failures += 1

    # ⛔ Each exemption is read against the fixture's own result, and only what
    # the plant introduced counts: a whole-change assertion reads every plant as
    # red while one real finding stands elsewhere in the fixture.
    baseline = {problem for found in run(fixture()).values() for problem in found}
    print(f"\nAsserting each stays green where it must ({len(EXEMPTIONS)}):")
    for label, plant in EXEMPTIONS:
        found = [
            problem for arm in run(plant(fixture())).values()
            for problem in arm if problem not in baseline
        ]
        if found:
            print(f"  WENT RED               exempt: {label} — {found[0][:80]}")
            failures += 1
        else:
            print(f"  green on               exempt: {label}")

    print(f"\nAsserting the property list is held to the surface ({len(SURFACE_PLANTS)}):")
    for label, plant in SURFACE_PLANTS:
        if check_every_property_is_accounted_for(plant(surface)):
            print(f"  red on                 {label}")
        else:
            print(f"  STAYED GREEN           {label}")
            failures += 1

    if failures:
        print(
            f"\n{failures} assertion(s) did not hold. A check that cannot fail is not a check, "
            "and an exemption that cannot pass is not an exemption."
        )
    return 1 if failures else 0


LIMIT = (
    "⚠️ Each arm holds one corner of its property: a reworded restatement passes, a paragraph "
    "with one unmarked line passes, and a hedge off the list passes. The padding judgement is a "
    "reader's by rule. What is held, what is not, and the measurements behind the three numbers "
    "here are stated in docs/single-source-of-truth.md."
)


def tracked(root: str) -> dict[str, str]:
    """Every tracked document's text: the haystack a restatement is read against."""
    found = subprocess.run(
        ["git", "-C", root, "ls-files", f"*{MARKDOWN}"], capture_output=True, text=True, check=False
    )
    documents = {}
    for path in sorted(p for p in found.stdout.split("\n") if p):
        try:
            with open(os.path.join(root, path), encoding="utf-8") as handle:
                documents[path] = handle.read()
        except (OSError, UnicodeDecodeError):
            continue
    return documents


def main(argv: list[str]) -> int:
    unknown = [a for a in argv if a != "--self-test"]
    if unknown:
        print(f"unrecognised argument(s): {' '.join(unknown)}\n\n{__doc__}")
        return 2

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    surface = os.path.join(root, SURFACE)
    try:
        with open(surface, encoding="utf-8") as handle:
            text = handle.read()
    except OSError as exc:
        print(f"  FAIL  the floor's own table was read\n\n  - {SURFACE}: {exc}")
        return 1

    if "--self-test" in argv:
        if self_test(text):
            return 1
        print()

    # ⛔ The accounting arm reads the surface alone, so it is answered before the
    # diff and reported even where the diff refuses: a run that printed only the
    # refusal would leave a property with no arm unreported on every branch a
    # merge base could not be found for.
    accounting = check_every_property_is_accounted_for(text)
    try:
        change = lines_a_change_adds.read_change(root, TRACKED)
    except lines_a_change_adds.Unreadable as exc:
        print(f"  {'FAIL' if accounting else 'ok  '}  every property of the floor is accounted for")
        print(f"  FAIL  the files this change touches were read\n")
        for problem in accounting + [str(exc)]:
            print(f"  - {problem}")
        return 1

    prose = Prose(change, tracked(root))
    results = run(prose)
    results["every property of the floor is accounted for"] = accounting
    problems = [problem for found in results.values() for problem in found]
    for name, found in results.items():
        print(f"  {'FAIL' if found else 'ok  '}  {name}")

    rows = measured(prose)
    if rows:
        print("\nWhat this change writes — added lines, of them prose, emphasised spans, hedges:")
        for path, added, held, spans, hedges in rows:
            print(f"  {added:5}  {held:5}  {spans:5}  {hedges:5}   {path}")
    print(
        f"\n{sum(held for _, _, held, _, _ in rows)} of "
        f"{sum(added for _, added, _, _, _ in rows)} added line(s) are prose this floor reaches, "
        f"across {len(rows)} file(s), against the merge base `{change.base[:12]}`. The rest are "
        "code, fences, frontmatter, annotation, or lines the working tree no longer carries."
    )
    if problems:
        print(f"\n{len(problems)} problem(s):\n")
        for problem in problems:
            print(f"  - {problem}")
        print(f"\nThe floor is {CITATION}.\n\n{LIMIT}")
        return 1
    print(f"\n{LIMIT}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
