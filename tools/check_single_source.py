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
    check_single_source.py --self-test  assert each check reddens on a planted
                                        violation, then hold the tree
"""

from __future__ import annotations

import glob
import os
import re
import sys

# --- what plays which role -------------------------------------------------
#
# Grammar, not content. A markdown document under docs/ that is absent from
# this map fails rather than being skipped: a new store of prose is exactly the
# thing that quietly becomes a second authority.

SURFACE = "plugins/mjolnir/config/schema.md"
READER = "README.md"
RULINGS = "docs/divergences-and-rulings.md"

ROLES = {
    READER: "explains",
    "docs/configuration-surface.md": "explains",
    "docs/single-source-of-truth.md": "explains",
    RULINGS: "records",
}

CONFIG_GLOBS = [".claude/mjolnir.yaml", "plugins/mjolnir/config/examples/*.yaml"]

# The marker a binding statement carries in this repository.
BINDING = "⛔"

# A citation of the surface, with its anchor.
CITATION = re.compile(r"\]\(([^)\s#]*" + re.escape(os.path.basename(SURFACE)) + r")#([^)\s]+)\)")

# The two homes a ruling's outcome may have, and nothing else.
OUTCOME_IN_SURFACE = re.compile(r"\[schema § (\d+)\]\(([^)#]*schema\.md)#([^)]+)\)")
OUTCOME_IN_WORK_ITEM = re.compile(r"#(\d+), until extracted")
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


def split_row(line: str) -> list[str]:
    """Split a table row on its unescaped pipes."""
    return [cell.strip() for cell in re.split(r"(?<!\\)\|", line.strip().strip("|"))]


class Tree:
    """The files the claim spans, in memory, so a violation can be planted."""

    def __init__(self, root: str):
        self.root = root
        self.text: dict[str, str] = {}
        self.prose = [READER] + sorted(self._rel(p) for p in glob.glob(self._abs("docs/*.md")))
        self.configs: list[str] = []
        for pattern in CONFIG_GLOBS:
            self.configs += sorted(self._rel(p) for p in glob.glob(self._abs(pattern)))
        for path in [SURFACE] + self.prose + self.configs:
            self.text[path] = self._read(path)

    def _abs(self, rel: str) -> str:
        return os.path.join(self.root, rel)

    def _rel(self, path: str) -> str:
        return os.path.relpath(path, self.root).replace(os.sep, "/")

    def _read(self, rel: str) -> str:
        with open(self._abs(rel), encoding="utf-8") as handle:
            return handle.read()

    def copy(self) -> "Tree":
        clone = Tree.__new__(Tree)
        clone.root = self.root
        clone.text = dict(self.text)
        clone.prose = list(self.prose)
        clone.configs = list(self.configs)
        return clone

    # --- what the surface itself says ------------------------------------

    def headings(self, level: int) -> list[str]:
        marker = "#" * level + " "
        return [
            line[len(marker):].strip()
            for line in self.text[SURFACE].splitlines()
            if line.startswith(marker)
        ]

    def anchors(self) -> set[str]:
        out = set()
        for level in range(1, 7):
            out |= {anchor(h) for h in self.headings(level)}
        return out

    def sections(self) -> dict[str, str]:
        """Numbered sections of the surface, by their number."""
        out = {}
        for heading in self.headings(2):
            match = re.match(r"(\d+)\.\s", heading)
            if match:
                out[match.group(1)] = heading
        return out

    def declared_keys(self) -> set[str]:
        keys = set()
        for block in re.findall(r"```yaml\n(.*?)```", self.text[SURFACE], re.S):
            for line in block.splitlines():
                match = re.match(r"^([a-z_][a-z0-9_]*):", line)
                if match:
                    keys.add(match.group(1))
        return keys

    def citations(self) -> list[tuple[str, str]]:
        out = []
        for path in ROLES:
            for match in CITATION.finditer(self.text.get(path, "")):
                out.append((path, match.group(2)))
        return out


# --- the checks ------------------------------------------------------------
#
# Each returns a list of problems. Each has a planted violation below that it is
# asserted to go red on: an assertion written before its break tends to match
# only the break its author imagined.


def check_every_document_has_a_role(tree: Tree) -> list[str]:
    problems = []
    for path in tree.prose:
        if path not in ROLES:
            problems.append(
                f"{path}: no declared role. A document that may cite the surface must be "
                "given a role in this script, so that a new store of prose cannot become a "
                "second authority by being skipped."
            )
    for path in ROLES:
        if path not in tree.text:
            problems.append(f"{path}: has a declared role and does not exist.")
    return problems


def check_citations_resolve(tree: Tree) -> list[str]:
    known = tree.anchors()
    problems = []
    for path, cited in tree.citations():
        if cited not in known:
            problems.append(
                f"{path}: cites `{cited}`, which is not a heading of the surface."
            )
    return problems


def check_no_orphan_section(tree: Tree) -> list[str]:
    cited = {c for _, c in tree.citations()}
    problems = []
    for heading in tree.headings(2):
        if anchor(heading) not in cited:
            problems.append(
                f"{SURFACE}: section \"{heading}\" is cited by no document. A rule stated "
                "here with nothing recording why it has this shape is either unmotivated or "
                "the documents have gone stale."
            )
    return problems


def check_outcomes_live_in_one_of_two_places(tree: Tree) -> list[str]:
    text = tree.text[RULINGS]
    marker = "## 4. The rulings"
    if marker not in text:
        return [f"{RULINGS}: the rulings table is not where this check looks for it ({marker})."]
    table = text.split(marker, 1)[1].split("\n## ", 1)[0]
    rows = [line for line in table.splitlines() if line.strip().startswith("|")]
    if len(rows) < 3:
        return [f"{RULINGS}: the rulings table has no rows."]

    sections = tree.sections()
    problems = []
    for row in rows[2:]:
        cells = split_row(row)
        if len(cells) < 2:
            continue
        ruling, cell = cells[0], cells[-1]
        found = False
        for match in OUTCOME_IN_SURFACE.finditer(cell):
            found = True
            if match.group(1) not in sections:
                problems.append(
                    f"{RULINGS}: ruling {ruling} names surface § {match.group(1)}, "
                    "which is not a section of the surface."
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
    needle = os.path.basename(SURFACE)
    problems = []
    for path in ROLES:
        for block in re.split(r"\n\s*\n", tree.text.get(path, "")):
            if BINDING in block and needle not in block:
                first = " ".join(block.split())[:90]
                problems.append(
                    f"{path}: a binding statement cites nothing: \"{first}…\". Where a "
                    "document appears to state a rule, the binding form is the section of "
                    "the surface that it cites."
                )
    return problems


def check_configurations_match_the_surface(tree: Tree) -> list[str]:
    declared = tree.declared_keys()
    problems = []
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
# One per check, each asserted to redden the check it targets. #28's discipline:
# write the violation first, and confirm the check goes red on it.


def _plant_unroled_document(tree: Tree) -> Tree:
    tree.prose.append("docs/planted.md")
    tree.text["docs/planted.md"] = "# Planted\n"
    return tree


def _plant_broken_citation(tree: Tree) -> Tree:
    tree.text[READER] = CITATION.sub(
        lambda m: f"]({m.group(1)}#planted-anchor-that-does-not-exist)",
        tree.text[READER],
        count=1,
    )
    return tree


def _plant_orphan_section(tree: Tree) -> Tree:
    tree.text[SURFACE] += "\n## 99. A planted section nothing motivates\n"
    return tree


def _plant_outcome_outside_the_surface(tree: Tree) -> Tree:
    tree.text[RULINGS] = OUTCOME_IN_SURFACE.sub(
        "A planted document § Somewhere", tree.text[RULINGS], count=1
    )
    return tree


def _plant_uncited_binding_statement(tree: Tree) -> Tree:
    path = "docs/configuration-surface.md"
    tree.text[path] += f"\n\n{BINDING} **A planted rule stated with no citation.**\n"
    return tree


def _plant_undeclared_key(tree: Tree) -> Tree:
    tree.text[tree.configs[0]] += "\nplanted_key: 1\n"
    return tree


VIOLATIONS = [
    ("every document has a role", _plant_unroled_document),
    ("citations resolve", _plant_broken_citation),
    ("no orphan section", _plant_orphan_section),
    ("outcomes live in the surface or a work item", _plant_outcome_outside_the_surface),
    ("binding statements cite the surface", _plant_uncited_binding_statement),
    ("configurations match the surface", _plant_undeclared_key),
]


def run(tree: Tree) -> dict[str, list[str]]:
    return {name: check(tree) for name, check in CHECKS}


def self_test(tree: Tree) -> int:
    by_name = dict(CHECKS)
    missing = [name for name, _ in CHECKS if name not in dict(VIOLATIONS)]
    if missing:
        print("no planted violation for: " + ", ".join(missing))
        return 1
    failures = 0
    for name, plant in VIOLATIONS:
        problems = by_name[name](plant(tree.copy()))
        if problems:
            print(f"  red on its violation   {name}")
        else:
            print(f"  STAYED GREEN           {name}")
            failures += 1
    if failures:
        print(
            f"\n{failures} check(s) did not redden on their own planted violation. "
            "A check that cannot fail is not a check."
        )
    return 1 if failures else 0


def main(argv: list[str]) -> int:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tree = Tree(root)

    if "--self-test" in argv:
        print("Asserting each check reddens on a planted violation:")
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
