#!/usr/bin/env python3
"""Hold this repository's single-authority claim to its own statement.

The configuration surface declares itself the single statement of every rule and
flow of the shared procedure, and the documents beside it explain or record
without being a second authority. This script is what makes that claim a
property of the gate rather than of whoever happens to read the diff.

It derives every expectation from the surface at run time: the section list from
its headings, the key vocabulary from its fenced blocks, the citation targets
from its anchors. It hardcodes grammar only -- heading syntax, the anchor rule,
the binding marker, and which document plays which role. Adding a section to the
surface therefore changes what this script expects without changing this script,
which is the whole point: a check that restated the principles would be one more
copy of them, and a copy that has to be kept in sync is the defect rather than
the maintenance burden.

What it cannot check is fidelity -- whether a document's paraphrase still matches
the section it cites. That is the *quoting* kind of check, which goes red on an
innocent reword and green when a claim is reworded into its opposite. The checks
here are all of the *computed* and *forbidding* kinds.

Two things it reports rather than holds, for the same reason: resolving a
citation costs the whole document it points into, so the run prints what each
file costs a reader, and how many citations name a section where a subsection
may be the smaller home. Which subsection states a given fact is the *quoting*
kind again, so that half is a count and not a verdict.

Usage:
    check_single_source.py              hold the tree to the surface
    check_single_source.py --self-test  assert every check reddens on each of its
                                        planted violations, then hold the tree
"""

from __future__ import annotations

import glob
import os
import re
import sys
import textwrap

# --- what plays which role -------------------------------------------------
#
# Grammar, not content. A markdown document at the repository root or anywhere
# under docs/ that is absent from this map fails rather than being skipped: a new
# store of prose is exactly the thing that quietly becomes a second authority.

SURFACE = "plugins/mjolnir/config/schema.md"
SURFACE_NAME = os.path.basename(SURFACE)
READER = "README.md"
RULINGS = "docs/divergences-and-rulings.md"

# A document either explains the surface, records how a divergence was settled, or
# carries procedure for one role. The first two may not state a rule; procedure
# may, by the surface's own boundary rule, so check 4 leaves it alone -- but its
# citations are still held, because a dead citation in a skill is a dead citation.
EXPLAINS, RECORDS, PROCEDURE = "explains", "records", "procedure"

ROLES = {
    READER: EXPLAINS,
    "docs/configuration-surface.md": EXPLAINS,
    "docs/single-source-of-truth.md": EXPLAINS,
    "docs/working-on-the-toolkit.md": EXPLAINS,
    RULINGS: RECORDS,
    "docs/building-itself.md": RECORDS,
    "plugins/mjolnir/skills/day-report/SKILL.md": PROCEDURE,
    "plugins/mjolnir/skills/file-work-item/SKILL.md": PROCEDURE,
    "plugins/mjolnir/skills/finish/SKILL.md": PROCEDURE,
    "plugins/mjolnir/skills/gate-work-item/SKILL.md": PROCEDURE,
    "plugins/mjolnir/skills/review/SKILL.md": PROCEDURE,
    "plugins/mjolnir/skills/start/SKILL.md": PROCEDURE,
}

MAY_NOT_STATE_A_RULE = (EXPLAINS, RECORDS)

PROSE_GLOBS = ["*.md", "docs/**/*.md", "plugins/**/*.md"]
CONFIG_GLOBS = [".claude/mjolnir.yaml", "plugins/mjolnir/config/examples/*.y*ml"]

# The column through which the decision record names each ruling's home. The
# table is found by this header rather than by a section heading, so renumbering
# a section is not a change this script has to be edited for.
OUTCOME_COLUMN = "Outcome lives in"

# The marker a binding statement carries in this repository. A statement opens a
# line, optionally as a list item; the marker inside a table cell is prose about
# a rule rather than a statement of one.
BINDING = "⛔"
STATEMENT = re.compile(r"^\s*(?:[-*]\s+)?" + BINDING)

# The markers that direct a reader rather than inform one. The footprint counts
# both, because what a citation costs is not the file's length alone: a document
# of directives is read differently from a document of the same size that
# explains, and the count is the only part of that a machine can report.
#
# ⚠️ The advisory marker is its emoji form, variation selector included. The bare
# codepoint would also match it, and would then count the one bare instance in
# this tree -- a script's output quoted inside a code span, which is a marker
# being shown rather than a marker directing anybody.
DIRECTIVE = (BINDING, "⚠️")

# A citation of the surface: a link whose target is the surface and whose
# fragment names a section of it. The path is checked, not only the fragment --
# a fragment that resolves against a path that does not is a dead link with a
# green gate.
CITATION = re.compile(r"\]\((?P<path>[^)\s#]*" + re.escape(SURFACE_NAME) + r")#(?P<anchor>[^)\s]+)\)")

# The two homes a ruling's outcome may have. `the skill` is permitted only
# alongside one of them, for a role whose outcome is split between the surface
# and the skill that carries it.
OUTCOME_IN_SURFACE = re.compile(
    r"\[schema § (?P<section>[^\]]+)\]\((?P<path>[^)#]*"
    + re.escape(SURFACE_NAME)
    + r")#(?P<anchor>[^)]+)\)"
)
OUTCOME_IN_WORK_ITEM = re.compile(r"#(?P<number>\d+), until extracted")
# The ordinal a section label opens with, where it has one: `6`, `4.1`, and the
# `10 → Where a tree is created` form the documents already use in prose. What
# is cross-checked is the top-level number, which is what an anchor resolves to.
# ⛔ Without this, `4.1` and the arrow form fall into the branch for sections
# that carry no number at all and are refused as not existing, which is false of
# the surface and points a reader at renaming a correctly-named section.
LEADING_ORDINAL = re.compile(r"^(?P<number>\d+)(?:\.\d+)*(?:\s*(?:→|->)\s*.*)?$")
OUTCOME_ALSO_IN_SKILL = "the skill"


def anchor(heading: str) -> str:
    """Slug a heading the way the code host does.

    Note the per-space replacement: collapsing whitespace instead produces a
    single hyphen where the host produces two, which is a false red waiting to
    happen on any heading containing a dash surrounded by spaces.
    """
    text = heading.strip().lower().replace("`", "")
    text = re.sub(r"[^\w\s-]", "", text)
    return text.replace(" ", "-")


def outline(text: str) -> list[tuple[int, int, str, str]]:
    """(line index, level, title, anchor) in document order, outside fenced blocks.

    Repeats carry the host's `-1`, `-2` suffixes, so a citation of the second
    section with a given title resolves and the first does not stand in for it.

    The line index is here so that a section's own extent is read from the same
    scan its anchor is: a second walk looking the headings up again would be a
    second reading of the document, free to disagree with this one about which
    `## Title` inside a fenced block is a heading.
    """
    out: list[tuple[int, int, str, str]] = []
    seen: dict[str, int] = {}
    fenced = False
    for index, line in enumerate(text.splitlines()):
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if fenced:
            continue
        match = re.match(r"^(#{1,6})\s+(.*)", line)
        if not match:
            continue
        title = match.group(2).strip()
        base = anchor(title)
        nth = seen.get(base, 0)
        seen[base] = nth + 1
        out.append((index, len(match.group(1)), title, base if nth == 0 else f"{base}-{nth}"))
    return out


def headings(text: str) -> list[tuple[int, str, str]]:
    """(level, title, anchor) in document order, outside fenced blocks."""
    return [(level, title, slug) for _at, level, title, slug in outline(text)]


def split_row(line: str) -> list[str]:
    """Split a table row on its unescaped pipes."""
    return [cell.strip() for cell in re.split(r"(?<!\\)\|", line.strip().strip("|"))]


class Tree:
    """The files the claim spans, in memory, so a violation can be planted."""

    def __init__(self, root: str):
        self.root = root
        self.text: dict[str, str] = {}
        self.prose = self._glob(PROSE_GLOBS)
        self.configs = self._glob(CONFIG_GLOBS)
        self.empty_globs = [p for p in PROSE_GLOBS + CONFIG_GLOBS if not glob.glob(self._abs(p), recursive=True)]
        for path in [SURFACE] + self.prose + self.configs:
            self.text[path] = self._read(path)

    def _glob(self, patterns: list[str]) -> list[str]:
        found: set[str] = set()
        for pattern in patterns:
            for path in glob.glob(self._abs(pattern), recursive=True):
                rel = os.path.relpath(path, self.root).replace(os.sep, "/")
                if rel != SURFACE:
                    found.add(rel)
        return sorted(found)

    def _abs(self, rel: str) -> str:
        return os.path.join(self.root, rel)

    def _read(self, rel: str) -> str:
        with open(self._abs(rel), encoding="utf-8") as handle:
            return handle.read()

    def copy(self) -> "Tree":
        clone = Tree.__new__(Tree)
        clone.root = self.root
        clone.text = dict(self.text)
        clone.prose = list(self.prose)
        clone.configs = list(self.configs)
        clone.empty_globs = list(self.empty_globs)
        return clone

    # --- what the surface itself says ------------------------------------

    def headings(self, level: int | None = None) -> list[tuple[int, str, str]]:
        found = headings(self.text[SURFACE])
        return found if level is None else [h for h in found if h[0] == level]

    def anchors(self) -> set[str]:
        return {a for _, _, a in self.headings()}

    def sections(self) -> dict[str, str]:
        """Numbered `##` sections of the surface, by their number."""
        out = {}
        for _, title, _ in self.headings(2):
            match = re.match(r"(\d+)\.\s", title)
            if match:
                out[match.group(1)] = title
        return out

    def section_of(self) -> dict[str, str]:
        """Anchor -> the number of the `##` section it belongs to, if any."""
        out: dict[str, str] = {}
        current = None
        for level, title, slug in self.headings():
            if level <= 2:
                match = re.match(r"(\d+)\.\s", title)
                current = match.group(1) if match else None
            if current:
                out[slug] = current
        return out

    def unnumbered_of(self) -> dict[str, str]:
        """Anchor -> the title of the unnumbered `##` section it belongs to.

        The counterpart of `section_of` for the sections carrying no number, and
        ⛔ **deep anchors included for the same reason that one includes them**:
        an outcome may live in a `###` subsection, as ruling 11's does inside a
        numbered section. A map of each `##` heading's own anchor alone would be
        narrower than the branch it mirrors, and would refuse the one case the
        numbered-home limit was recorded against -- a procedure rule under the
        loop, which is a `###` beneath an unnumbered `##`.
        """
        out: dict[str, str] = {}
        current = None
        for level, title, slug in self.headings():
            if level <= 2:
                current = None if re.match(r"(\d+)\.\s", title) else title
            if current:
                out[slug] = current
        return out

    def outline(self) -> list[tuple[int, int, str, str]]:
        return outline(self.text[SURFACE])

    def section_shape(self) -> dict[str, tuple[str, list[str]]]:
        """`##` anchor -> (the section's own text, the titles of its subsections).

        The own text is what a citation of the section resolves to: everything
        between its heading and its first subsection. ⛔ Where that is empty the
        section is a *container* — it states nothing itself, so a citation of it
        names a heading and a list of subsections rather than a fact, and the
        motivation check reads it through its subsections rather than directly.
        """
        lines = self.text[SURFACE].splitlines()
        marks = self.outline()
        shape: dict[str, tuple[str, list[str]]] = {}
        for i, (at, level, _title, slug) in enumerate(marks):
            if level != 2:
                continue
            ends = next((m[0] for m in marks[i + 1:]), len(lines))
            subs = []
            for _at, deeper, title, _slug in marks[i + 1:]:
                if deeper <= 2:
                    break
                if deeper == 3:
                    subs.append(title)
            shape[slug] = ("\n".join(lines[at + 1:ends]).strip(), subs)
        return shape

    def declared_keys(self) -> set[str]:
        keys = set()
        for block in re.findall(r"```yaml\n(.*?)```", self.text[SURFACE], re.S):
            for line in block.splitlines():
                match = re.match(r"^([a-z_][a-z0-9_]*):", line)
                if match:
                    keys.add(match.group(1))
        return keys

    def citations(self) -> list[tuple[str, str, str]]:
        """(citing document, link target resolved from it, anchor)."""
        out = []
        for path in ROLES:
            for match in CITATION.finditer(self.text.get(path, "")):
                target = os.path.normpath(
                    os.path.join(os.path.dirname(path), match.group("path"))
                ).replace(os.sep, "/")
                out.append((path, target, match.group("anchor")))
        return out


# --- the checks ------------------------------------------------------------
#
# Each returns a list of problems, and each has at least one planted violation
# below that it is asserted to go red on -- including one per branch that does
# real work, because an assertion written before its break tends to match only
# the break its author imagined.


def check_every_document_has_a_role(tree: Tree) -> list[str]:
    problems = []
    for path in tree.prose:
        if path not in ROLES:
            problems.append(
                f"{path}: no declared role. A markdown document at the root or under docs/ "
                "must be given a role in this script, so that a new store of prose cannot "
                "become a second authority by being skipped."
            )
    for path in ROLES:
        if path not in tree.text:
            problems.append(f"{path}: has a declared role and does not exist.")
    for pattern in tree.empty_globs:
        problems.append(
            f"{pattern}: matched no file, so whatever it was meant to cover is unchecked. "
            "A check that holds nothing reports green."
        )
    return problems


def check_citations_resolve(tree: Tree) -> list[str]:
    known = tree.anchors()
    found = tree.citations()
    problems = []
    if not found:
        problems.append(
            "No document cites the surface at all, so this check holds nothing. Either the "
            "citation form changed or the documents stopped citing."
        )
    for path, target, cited in found:
        if target != SURFACE:
            problems.append(
                f"{path}: cites `{target}#{cited}`, which is not the surface ({SURFACE}). "
                "The fragment resolves but the path does not — a dead link."
            )
        if cited not in known:
            problems.append(
                f"{path}: cites `{cited}`, which is not a heading of the surface."
            )
    return problems


def check_no_orphan_section(tree: Tree) -> list[str]:
    """Every heading below the title is motivated by a document that cites it.

    The depth is the surface's own rather than a level written down here: a
    `####` added tomorrow is held the moment it exists. ⛔ The one exemption is
    a **container** — a `##` section whose whole content is in its subsections
    states nothing of its own, so what a document would be motivating is the
    subsections, and each of those is held here in its own right.
    """
    cited = {c for _, _, c in tree.citations()}
    shape = tree.section_shape()
    problems = []
    for level, title, slug in tree.headings():
        if level < 2 or slug in cited:
            continue
        own, subs = shape.get(slug, ("", []))
        if subs and not own:
            continue
        kind = "section" if level == 2 else "subsection"
        problems.append(
            f"{SURFACE}: {kind} \"{title}\" is cited by no document. A rule stated "
            "here with nothing recording why it has this shape is either unmotivated or "
            "the documents have gone stale."
        )
    return problems


def check_no_citation_names_a_container(tree: Tree) -> list[str]:
    """A citation of a container resolves to a heading and a list, never a fact.

    The rule behind it is that a citation names the section stating the fact
    rather than the one above it, and ⛔ **this check holds only the decidable
    end of that**: which subsection states a given fact is the *quoting* kind
    this gate rules out everywhere else. A `##` section whose own text is empty
    states nothing anywhere, so a citation of it is wrong without anything
    needing to be read. The refusal names its subsections, because the remedy
    is choosing one.

    Every other coarse citation — a section that has subsections *and* states
    something itself — is counted by `coarse_citations` and held by nobody. That
    limit is stated in `docs/single-source-of-truth.md` rather than left to be
    inferred from a green run.
    """
    shape = tree.section_shape()
    problems = []
    for path, _target, cited in tree.citations():
        own, subs = shape.get(cited, ("", []))
        if subs and not own:
            problems.append(
                f"{path}: cites `{cited}`, whose whole content is in its subsections, so the "
                "citation resolves to a heading and nothing else. One of these states the "
                f"fact: {' · '.join(subs)}."
            )
    return problems


def check_outcomes_live_in_one_of_two_places(tree: Tree) -> list[str]:
    lines = tree.text[RULINGS].splitlines()
    header = next(
        (i for i, l in enumerate(lines) if l.strip().startswith("|") and OUTCOME_COLUMN in l),
        None,
    )
    if header is None:
        return [
            f"{RULINGS}: no table has a `{OUTCOME_COLUMN}` column, so no ruling's outcome "
            "is held to anything."
        ]
    # Rows run to the first line that is not a table row, so a table added later
    # in the document is not parsed as a row of this one.
    rows = []
    for line in lines[header + 2:]:
        if not line.strip().startswith("|"):
            break
        rows.append(line)
    if not rows:
        return [f"{RULINGS}: the rulings table has no rows."]

    sections = tree.sections()
    section_of = tree.section_of()
    unnumbered_of = tree.unnumbered_of()
    unnumbered_titles = set(unnumbered_of.values())
    problems = []
    for row in rows:
        cells = split_row(row)
        if len(cells) < 2:
            problems.append(f"{RULINGS}: a ruling row has too few cells to read: {row.strip()!r}")
            continue
        ruling, cell = cells[0], cells[-1]
        found = False
        for match in OUTCOME_IN_SURFACE.finditer(cell):
            found = True
            section = match.group("section")
            target, slug = match.group("path"), match.group("anchor")
            resolved = os.path.normpath(
                os.path.join(os.path.dirname(RULINGS), target)
            ).replace(os.sep, "/")
            ordinal = LEADING_ORDINAL.match(section)
            if ordinal:
                number = ordinal.group("number")
                if number not in sections:
                    problems.append(
                        f"{RULINGS}: ruling {ruling} names schema § {section}, "
                        f"whose § {number} is not a section of the surface."
                    )
                elif resolved == SURFACE and section_of.get(slug) != number:
                    problems.append(
                        f"{RULINGS}: ruling {ruling} names schema § {section} but links "
                        f"`{slug}`, which belongs to "
                        f"§ {section_of.get(slug) or 'no numbered section'}. "
                        "The number and the link must name the same home."
                    )
            # ⛔ An unnumbered `##` section is a home as well. Every numbered
            # section is a configuration facet, so a ruling whose outcome is
            # procedure -- how the file itself is written, rather than a key in
            # it -- lands in a section with no number, and refusing that would
            # push the outcome into a document instead, which is the one thing
            # this check exists to stop. ⚠️ With no number to cross-check, the
            # heading's own title is what ties the cell to the section.
            elif section not in unnumbered_titles:
                problems.append(
                    f"{RULINGS}: ruling {ruling} names schema § {section}, which is "
                    "neither a numbered section of the surface nor one of its "
                    "unnumbered `##` headings."
                )
            elif resolved == SURFACE and unnumbered_of.get(slug) != section:
                here = unnumbered_of.get(slug)
                problems.append(
                    f"{RULINGS}: ruling {ruling} names schema § {section} but links "
                    f"`{slug}`, which belongs to "
                    f"§ {here or 'no unnumbered section'}. "
                    "The heading and the link must name the same home."
                )
        if OUTCOME_IN_WORK_ITEM.search(cell):
            found = True
        if not found:
            problems.append(
                f"{RULINGS}: ruling {ruling} names no home this check recognises: {cell!r}. "
                "An outcome lives in the surface, or in a numbered work item marked "
                "`until extracted`, and nowhere else."
            )
            continue
        residue = OUTCOME_IN_SURFACE.sub("", cell)
        residue = OUTCOME_IN_WORK_ITEM.sub("", residue)
        residue = residue.replace(OUTCOME_ALSO_IN_SKILL, "")
        residue = re.sub(r"[\s,.]", "", residue)
        if residue:
            problems.append(
                f"{RULINGS}: ruling {ruling} names a home outside the surface: {residue!r}. "
                "A document that states a ruling's outcome is a second authority for it."
            )
    return problems


def check_binding_statements_cite_the_surface(tree: Tree) -> list[str]:
    problems = []
    for path, kind in ROLES.items():
        if kind not in MAY_NOT_STATE_A_RULE:
            continue
        for block in re.split(r"\n\s*\n", tree.text.get(path, "")):
            statements = [
                line
                for line in block.splitlines()
                if STATEMENT.match(line) and not line.lstrip().startswith("|")
            ]
            if not statements:
                continue
            cited = [
                os.path.normpath(
                    os.path.join(os.path.dirname(path), m.group("path"))
                ).replace(os.sep, "/")
                for m in CITATION.finditer(block)
            ]
            if SURFACE not in cited:
                first = " ".join(statements[0].split())[:90]
                problems.append(
                    f"{path}: a binding statement cites no section of the surface: "
                    f"\"{first}…\". Where a document appears to state a rule, the binding "
                    "form is the section of the surface that it cites — a bare mention of "
                    "the file, or a link without a fragment, is not a citation."
                )
    return problems


def check_configurations_match_the_surface(tree: Tree) -> list[str]:
    declared = tree.declared_keys()
    problems = []
    if not declared:
        problems.append(f"{SURFACE}: declares no top-level key, so this check holds nothing.")
    for path in tree.configs:
        present = set(re.findall(r"^([a-z_][a-z0-9_]*):", tree.text[path], re.M))
        for key in sorted(present - declared):
            problems.append(
                f"{path}: carries top-level key `{key}`, which the surface does not declare."
            )
        for key in sorted(declared - present):
            problems.append(
                f"{path}: does not carry top-level key `{key}`, which the surface declares."
            )
    return problems


# --- what the run reports rather than holds --------------------------------
#
# Neither of these has a verdict. They exist because resolving a citation costs
# the whole document it points into, and a cost nothing prints is a cost nobody
# reads: a role that doubles in size, or a document that acquires ten more
# coarse citations, is then visible in the diff of a build log. ⛔ No threshold
# is applied to either — a budget is a judgement, and a judgement hardcoded here
# is the copy-that-must-be-kept-in-sync this script exists not to become.


def footprint(tree: Tree) -> list[tuple[str, int, int, int]]:
    """(path, lines, characters, directive markers) for every file the checks walk."""
    rows = []
    for path in [SURFACE] + tree.prose:
        text = tree.text.get(path)
        if text is None:
            continue
        rows.append(
            (path, len(text.splitlines()), len(text), sum(text.count(m) for m in DIRECTIVE))
        )
    return rows


def coarse_citations(tree: Tree) -> list[tuple[str, list[str], list[tuple[str, int]]]]:
    """(anchor, its subsections, the documents citing it and how often).

    The sections held by `check_no_citation_names_a_container` are absent:
    those are a verdict rather than a report. What is left is every citation of
    a section that states something itself *and* has subsections — where a
    subsection may be the smaller home and no machine here can tell.
    """
    shape = tree.section_shape()
    by_anchor: dict[str, dict[str, int]] = {}
    for path, _target, cited in tree.citations():
        own, subs = shape.get(cited, ("", []))
        if subs and own:
            by_anchor.setdefault(cited, {})
            by_anchor[cited][path] = by_anchor[cited].get(path, 0) + 1
    return [
        (cited, shape[cited][1], sorted(docs.items(), key=lambda d: (-d[1], d[0])))
        for cited, docs in sorted(by_anchor.items(), key=lambda a: (-sum(a[1].values()), a[0]))
    ]


def check_the_footprint_covers_what_is_walked(tree: Tree) -> list[str]:
    """The report shrinking in silence is the one way it can lie.

    A file the checks read and the footprint skips is a cost reported by
    nothing, which is check 0's argument one column over — and the same reason
    a glob matching no file is a problem here rather than a quiet pass.
    """
    measured = {path for path, *_ in footprint(tree)}
    problems = [
        f"{path}: is read by the checks and carries no footprint, so what it costs a reader "
        "is reported by nothing."
        for path in [SURFACE] + tree.prose
        if path not in measured
    ]
    if not measured:
        problems.append("the footprint measured no file at all, so the report holds nothing.")
    return problems


CHECKS = [
    ("every document has a role", check_every_document_has_a_role),
    ("citations resolve", check_citations_resolve),
    ("no orphan section", check_no_orphan_section),
    ("outcomes live in the surface or a work item", check_outcomes_live_in_one_of_two_places),
    ("binding statements cite the surface", check_binding_statements_cite_the_surface),
    ("configurations match the surface", check_configurations_match_the_surface),
    ("no citation names a container", check_no_citation_names_a_container),
    ("the footprint covers what is walked", check_the_footprint_covers_what_is_walked),
]


# --- the planted violations ------------------------------------------------
#
# One per branch that does real work, not one per check: a plant that reddens a
# check by the wrong route proves nothing about the branch it was written for.


def _plant(path: str, mutate):
    def apply(tree: Tree) -> Tree:
        tree.text[path] = mutate(tree.text[path])
        return tree

    return apply


def _plant_unroled_document(tree: Tree) -> Tree:
    tree.prose.append("docs/planted.md")
    tree.text["docs/planted.md"] = "# Planted\n"
    return tree


def _plant_unroled_nested_document(tree: Tree) -> Tree:
    tree.prose.append("docs/nested/planted.md")
    tree.text["docs/nested/planted.md"] = "# Planted\n"
    return tree


def _plant_glob_matching_nothing(tree: Tree) -> Tree:
    tree.empty_globs.append("docs/**/*.md")
    return tree


def _plant_broken_anchor(tree: Tree) -> Tree:
    tree.text[READER] = CITATION.sub(
        lambda m: f"]({m.group('path')}#planted-anchor-that-does-not-exist)",
        tree.text[READER],
        count=1,
    )
    return tree


def _plant_broken_path(tree: Tree) -> Tree:
    tree.text[READER] = CITATION.sub(
        lambda m: f"](planted/elsewhere/{SURFACE_NAME}#{m.group('anchor')})",
        tree.text[READER],
        count=1,
    )
    return tree


def _plant_orphan_section(tree: Tree) -> Tree:
    tree.text[SURFACE] += "\n## 99. A planted section nothing motivates\n\nIts own text.\n"
    return tree


def _plant_orphan_subsection(tree: Tree) -> Tree:
    """The level the check used to stop one short of.

    ⚠️ The section above it is given own text and a citation, so what reddens is
    the subsection being unmotivated rather than its parent being so. A plant
    that reddens the branch next door proves nothing about this one.
    """
    tree.text[SURFACE] += (
        "\n## 98. A planted section a document motivates\n\nIts own text.\n"
        "\n### A planted subsection nothing motivates\n\nIts own text.\n"
    )
    tree.text[READER] += (
        f"\n\n[the planted section](plugins/mjolnir/config/{SURFACE_NAME}"
        "#98-a-planted-section-a-document-motivates)\n"
    )
    return tree


def _plant_citation_of_a_container(tree: Tree) -> Tree:
    """A section with no text of its own, cited.

    ⚠️ Planted on the surface *and* in a document, because the check reads a
    citation against the section's shape and a plant touching either one alone
    exercises nothing: a container nobody cites is permitted, and a citation of
    a section that states something is permitted too.
    """
    tree.text[SURFACE] += (
        "\n## 97. A planted container\n\n### A planted subsection that states the fact\n"
        "\nIts own text.\n"
    )
    tree.text[READER] += (
        f"\n\n[the planted container](plugins/mjolnir/config/{SURFACE_NAME}"
        "#97-a-planted-container)\n"
    )
    return tree


def _plant_file_the_footprint_cannot_measure(tree: Tree) -> Tree:
    """A document the checks walk and the report skips."""
    tree.prose.append("docs/unmeasurable.md")
    return tree


def _plant_uncited_container(tree: Tree) -> Tree:
    """The exemption, on the green side: a container cited through its subsection.

    ⛔ An exemption nothing can fail is an exemption nobody checked, and the
    motivation check's is the only place it can quietly stop holding: read
    without the carve-out, every container is an orphan; read with the carve-out
    written one level too wide, so is nothing. This was verified by disabling
    the exemption and watching the plant redden.
    """
    tree.text[SURFACE] += (
        "\n## 96. A planted container\n\n### A planted subsection a document motivates\n"
        "\nIts own text.\n"
    )
    tree.text[READER] += (
        f"\n\n[the planted subsection](plugins/mjolnir/config/{SURFACE_NAME}"
        "#a-planted-subsection-a-document-motivates)\n"
    )
    return tree


def _outcome_table(tree: Tree) -> tuple[str, str]:
    """The rulings document split at its outcome table, so a plant breaks a cell.

    ⚠️ The plants below substituted into the whole document, on the unstated
    assumption that the outcome form `[schema § <N or heading>](…#a)` occurs
    nowhere but a cell. ⛔ No count of them is written here: one was added the
    moment the cell grammar admitted a section named by its heading, and a
    number in this sentence would have been wrong by that change, green.
    It is an ordinary citation shape, and the first one written in prose *above*
    § 4 took all three plants: each mutated a sentence, every cell stayed valid,
    and three checks reported STAYED GREEN. A plant that reddens nothing is the
    cheaper failure; a plant that silently stops reaching its branch is the one
    that leaves a check believed and unexercised.

    The split is derived the same way the check derives it -- the header carrying
    the outcome column -- so a renumbered or moved table needs no edit here.
    """
    lines = tree.text[RULINGS].splitlines(keepends=True)
    header = next(
        i for i, line in enumerate(lines)
        if line.strip().startswith("|") and OUTCOME_COLUMN in line
    )
    return "".join(lines[:header]), "".join(lines[header:])


def _plant_outcome_with_no_home(tree: Tree) -> Tree:
    above, table = _outcome_table(tree)
    tree.text[RULINGS] = above + OUTCOME_IN_SURFACE.sub(
        "A planted document § Somewhere", table, count=1
    )
    return tree


def _plant_outcome_with_a_second_home(tree: Tree) -> Tree:
    """Keep a valid home and add a document beside it -- the residue branch."""
    above, table = _outcome_table(tree)
    match = OUTCOME_IN_SURFACE.search(table)
    tree.text[RULINGS] = above + table.replace(
        match.group(0), match.group(0) + ", README § Somewhere", 1
    )
    return tree


def _plant_outcome_number_against_wrong_anchor(tree: Tree) -> Tree:
    """⛔ Filtered to a *numbered* cell, which the first match is not by rule.

    Once the cell grammar admitted a section named by its heading, a bare first
    match made this plant exercise whichever branch happened to come first in
    the table -- numeric today only because the one named cell sits eleven rows
    in. The plant names the numeric branch, so it selects for it.
    """
    above, table = _outcome_table(tree)
    match = next(m for m in OUTCOME_IN_SURFACE.finditer(table) if m.group("section").isdigit())
    other = next(
        a for _, _, a in headings(tree.text[SURFACE]) if a != match.group("anchor")
    )
    tree.text[RULINGS] = above + table.replace(
        match.group(0),
        f"[schema § {match.group('section')}]({match.group('path')}#{other})",
        1,
    )
    return tree


def _plant_outcome_named_section_against_wrong_anchor(tree: Tree) -> Tree:
    """The unnumbered branch: a named section whose link goes elsewhere.

    ⛔ Planted on a cell naming an unnumbered section, and **synthesised** where
    the table has none. A plant that stopped on a missing cell would exit the
    whole run on a traceback where a verdict belongs -- the failure this gate
    has already paid for three times -- and one that fell through to a numeric
    cell would assert about the branch beside the one it names.
    """
    above, table = _outcome_table(tree)
    match = next(
        (m for m in OUTCOME_IN_SURFACE.finditer(table) if not m.group("section").isdigit()),
        None,
    )
    named = next(
        (title for _, title, slug in tree.headings(2) if not re.match(r"\d+\.\s", title)),
        None,
    )
    if named is None:
        # The surface carries no unnumbered `##` section at all, so the branch
        # has nothing to be wrong about. Said, not skipped in silence.
        tree.text[RULINGS] = above + table + (
            "\n<!-- the surface has no unnumbered `##` section, so this plant "
            "synthesised nothing -->\n"
        )
        return tree
    # ⛔ An anchor belonging to a *different* unnumbered section, so the plant
    # lands on the title-agreement arm rather than on the one that reports an
    # anchor belonging to no unnumbered section at all. Those are different
    # failures and the realistic one is this.
    elsewhere = tree.unnumbered_of()
    other = next(
        (slug for slug, title in elsewhere.items() if title != named),
        next(a for _, _, a in headings(tree.text[SURFACE]) if a != anchor(named)),
    )
    if match is None:
        # No ruling names one today. Synthesise the row rather than stopping:
        # what is under test is the branch, not the table's present contents.
        row = (
            f"| planted | A synthesised divergence | Planted "
            f"| [schema § {named}]({SURFACE_NAME}#{other}) |\n"
        )
        tree.text[RULINGS] = above + table.rstrip("\n") + "\n" + row
        return tree
    tree.text[RULINGS] = above + table.replace(
        match.group(0),
        f"[schema § {match.group('section')}]({match.group('path')}#{other})",
        1,
    )
    return tree


def _plant_uncited_binding_statement(tree: Tree) -> Tree:
    path = "docs/configuration-surface.md"
    tree.text[path] += f"\n\n{BINDING} **A planted rule stated with no citation.**\n"
    return tree


def _plant_binding_statement_citing_no_section(tree: Tree) -> Tree:
    """The realistic break: the file is named, but no section is."""
    path = "docs/configuration-surface.md"
    tree.text[path] += (
        f"\n\n{BINDING} **A planted rule.** It merely mentions "
        f"[{SURFACE_NAME}](../{SURFACE}) with no fragment.\n"
    )
    return tree


def _plant_undeclared_key(tree: Tree) -> Tree:
    tree.text[tree.configs[0]] += "\nplanted_key: 1\n"
    return tree


def _plant_undeclared_key_in_an_example(tree: Tree) -> Tree:
    tree.text[tree.configs[-1]] += "\nplanted_key: 1\n"
    return tree


VIOLATIONS = [
    ("every document has a role", "a document with no role", _plant_unroled_document),
    ("every document has a role", "a nested document with no role", _plant_unroled_nested_document),
    ("every document has a role", "a glob that matches nothing", _plant_glob_matching_nothing),
    ("citations resolve", "an anchor that does not exist", _plant_broken_anchor),
    ("citations resolve", "a valid anchor on a wrong path", _plant_broken_path),
    ("no orphan section", "a section nothing motivates", _plant_orphan_section),
    ("no orphan section", "a subsection nothing motivates", _plant_orphan_subsection),
    ("no citation names a container", "a citation of a container section", _plant_citation_of_a_container),
    ("the footprint covers what is walked", "a file the report skips", _plant_file_the_footprint_cannot_measure),
    ("outcomes live in the surface or a work item", "a cell with no home", _plant_outcome_with_no_home),
    ("outcomes live in the surface or a work item", "a cell with a second home", _plant_outcome_with_a_second_home),
    ("outcomes live in the surface or a work item", "a number against the wrong anchor", _plant_outcome_number_against_wrong_anchor),
    ("outcomes live in the surface or a work item", "a named section against the wrong anchor", _plant_outcome_named_section_against_wrong_anchor),
    ("binding statements cite the surface", "a statement citing nothing", _plant_uncited_binding_statement),
    ("binding statements cite the surface", "a statement citing no section", _plant_binding_statement_citing_no_section),
    ("configurations match the surface", "an undeclared key in this project's own config", _plant_undeclared_key),
    ("configurations match the surface", "an undeclared key in an example", _plant_undeclared_key_in_an_example),
]


# The other side of the one check that carries an exemption. ⛔ A red-only suite
# says nothing about a carve-out: these must stay green, and each is compared
# against the tree's own result rather than against zero, so a real problem
# elsewhere in the tree does not read as the exemption failing.

EXEMPTIONS = [
    ("no orphan section", "a container cited through its subsection", _plant_uncited_container),
]


def run(tree: Tree) -> dict[str, list[str]]:
    return {name: check(tree) for name, check in CHECKS}


def self_test(tree: Tree) -> int:
    by_name = dict(CHECKS)
    uncovered = [name for name, _ in CHECKS if not any(n == name for n, _, _ in VIOLATIONS)]
    for name in uncovered:
        print(f"  NO PLANTED VIOLATION   {name}")
    failures = len(uncovered)
    for name, label, plant in VIOLATIONS:
        if by_name[name](plant(tree.copy())):
            print(f"  red on                 {name}: {label}")
        else:
            print(f"  STAYED GREEN           {name}: {label}")
            failures += 1
    for name, label, plant in EXEMPTIONS:
        before = by_name[name](tree)
        if by_name[name](plant(tree.copy())) == before:
            print(f"  green on               {name}: {label}")
        else:
            print(f"  WENT RED               {name}: {label}")
            failures += 1
    if failures:
        print(
            f"\n{failures} assertion(s) did not hold. A check that cannot fail is not a check, "
            "and an exemption that cannot pass is not an exemption."
        )
    return 1 if failures else 0


def main(argv: list[str]) -> int:
    unknown = [a for a in argv if a != "--self-test"]
    if unknown:
        print(f"unrecognised argument(s): {' '.join(unknown)}\n\n{__doc__}")
        return 2

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tree = Tree(root)

    if "--self-test" in argv:
        print(
            f"Asserting each check reddens on its planted violations ({len(VIOLATIONS)}) "
            f"and stays green on each exemption ({len(EXEMPTIONS)}):"
        )
        if self_test(tree):
            return 1
        print()

    results = run(tree)
    problems = [p for found in results.values() for p in found]
    for name, found in results.items():
        print(f"  {'FAIL' if found else 'ok  '}  {name}")

    print("\nWhat each file costs whoever opens it — lines, characters, ⛔/⚠️ markers:")
    for path, lines, chars, marks in sorted(footprint(tree), key=lambda row: -row[2]):
        print(f"  {lines:6}  {chars:7}  {marks:4}   {path}")

    coarse = coarse_citations(tree)
    print(
        f"\nCoarse citations — a section cited where a subsection may state the fact "
        f"({sum(n for _, _, docs in coarse for _, n in docs)} into {len(coarse)} sections).\n"
        "Reported and held by nobody: which subsection states it cannot be computed."
    )
    for cited, subs, docs in coarse:
        total = sum(n for _, n in docs)
        print(f"  {total:3}  #{cited} — {len(subs)} subsection{'s' if len(subs) > 1 else ''}")
        print(textwrap.fill(
            ", ".join(f"{path} ×{n}" for path, n in docs),
            width=98, initial_indent=" " * 8, subsequent_indent=" " * 8,
        ))

    if problems:
        print(f"\n{len(problems)} problem(s):\n")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print(
        "\nThe surface is the single statement of every rule and flow, and every document "
        "beside it cites rather than states."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
