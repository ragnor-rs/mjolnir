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
    RULINGS: RECORDS,
    "docs/building-itself.md": RECORDS,
    "plugins/mjolnir/skills/day-report/SKILL.md": PROCEDURE,
    "plugins/mjolnir/skills/file-work-item/SKILL.md": PROCEDURE,
    "plugins/mjolnir/skills/finish/SKILL.md": PROCEDURE,
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

# A citation of the surface: a link whose target is the surface and whose
# fragment names a section of it. The path is checked, not only the fragment --
# a fragment that resolves against a path that does not is a dead link with a
# green gate.
CITATION = re.compile(r"\]\((?P<path>[^)\s#]*" + re.escape(SURFACE_NAME) + r")#(?P<anchor>[^)\s]+)\)")

# The two homes a ruling's outcome may have. `the skill` is permitted only
# alongside one of them, for a role whose outcome is split between the surface
# and the skill that carries it.
OUTCOME_IN_SURFACE = re.compile(
    r"\[schema § (?P<number>\d+)\]\((?P<path>[^)#]*" + re.escape(SURFACE_NAME) + r")#(?P<anchor>[^)]+)\)"
)
OUTCOME_IN_WORK_ITEM = re.compile(r"#(?P<number>\d+), until extracted")
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


def headings(text: str) -> list[tuple[int, str, str]]:
    """(level, title, anchor) in document order, outside fenced blocks.

    Repeats carry the host's `-1`, `-2` suffixes, so a citation of the second
    section with a given title resolves and the first does not stand in for it.
    """
    out: list[tuple[int, str, str]] = []
    seen: dict[str, int] = {}
    fenced = False
    for line in text.splitlines():
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
        out.append((len(match.group(1)), title, base if nth == 0 else f"{base}-{nth}"))
    return out


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
    cited = {c for _, _, c in tree.citations()}
    problems = []
    for _, title, slug in tree.headings(2):
        if slug not in cited:
            problems.append(
                f"{SURFACE}: section \"{title}\" is cited by no document. A rule stated "
                "here with nothing recording why it has this shape is either unmotivated or "
                "the documents have gone stale."
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
            number, target, slug = match.group("number"), match.group("path"), match.group("anchor")
            resolved = os.path.normpath(
                os.path.join(os.path.dirname(RULINGS), target)
            ).replace(os.sep, "/")
            if number not in sections:
                problems.append(
                    f"{RULINGS}: ruling {ruling} names schema § {number}, "
                    "which is not a section of the surface."
                )
            elif resolved == SURFACE and section_of.get(slug) != number:
                problems.append(
                    f"{RULINGS}: ruling {ruling} names schema § {number} but links `{slug}`, "
                    f"which belongs to § {section_of.get(slug) or 'no numbered section'}. "
                    "The number and the link must name the same home."
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


CHECKS = [
    ("every document has a role", check_every_document_has_a_role),
    ("citations resolve", check_citations_resolve),
    ("no orphan section", check_no_orphan_section),
    ("outcomes live in the surface or a work item", check_outcomes_live_in_one_of_two_places),
    ("binding statements cite the surface", check_binding_statements_cite_the_surface),
    ("configurations match the surface", check_configurations_match_the_surface),
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
    tree.text[SURFACE] += "\n## 99. A planted section nothing motivates\n"
    return tree


def _outcome_table(tree: Tree) -> tuple[str, str]:
    """The rulings document split at its outcome table, so a plant breaks a cell.

    ⚠️ The three plants below substituted into the whole document, on the unstated
    assumption that the outcome form `[schema § N](…#a)` occurs nowhere but a cell.
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
    above, table = _outcome_table(tree)
    match = OUTCOME_IN_SURFACE.search(table)
    other = next(
        a for _, _, a in headings(tree.text[SURFACE]) if a != match.group("anchor")
    )
    tree.text[RULINGS] = above + table.replace(
        match.group(0),
        f"[schema § {match.group('number')}]({match.group('path')}#{other})",
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
    ("outcomes live in the surface or a work item", "a cell with no home", _plant_outcome_with_no_home),
    ("outcomes live in the surface or a work item", "a cell with a second home", _plant_outcome_with_a_second_home),
    ("outcomes live in the surface or a work item", "a number against the wrong anchor", _plant_outcome_number_against_wrong_anchor),
    ("binding statements cite the surface", "a statement citing nothing", _plant_uncited_binding_statement),
    ("binding statements cite the surface", "a statement citing no section", _plant_binding_statement_citing_no_section),
    ("configurations match the surface", "an undeclared key in this project's own config", _plant_undeclared_key),
    ("configurations match the surface", "an undeclared key in an example", _plant_undeclared_key_in_an_example),
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
    if failures:
        print(
            f"\n{failures} assertion(s) did not hold. A check that cannot fail is not a check."
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
        print(f"Asserting each check reddens on its planted violations ({len(VIOLATIONS)}):")
        if self_test(tree):
            return 1
        print()

    results = run(tree)
    problems = [p for found in results.values() for p in found]
    for name, found in results.items():
        print(f"  {'FAIL' if found else 'ok  '}  {name}")
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
