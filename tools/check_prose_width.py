#!/usr/bin/env python3
"""Hold this repository's markdown prose to the width its configuration states.

Prose width was a habit before it was a rule: every document here wrapped at
roughly the same column and nothing anywhere said so, which is the shape this
toolkit deletes everywhere else -- a fact every writer must know, recorded in no
place a writer can read. The rule is now
`plugins/mjolnir/config/schema.md § 8 -> Prose line width`, and this script is
what makes it a property of the gate rather than of whoever typed last.

⛔ The width is **read from the configuration**, never carried here: a project
states `language.prose_width` or states nothing and does not wrap. A tree whose
configuration carries no width makes this check hold nothing, and it says so and
reddens rather than passing, because a check that holds nothing reports green.

What is held: every tracked `*.md` file, including the skills and the
examples. What is excluded is excluded **by the rule**, not by forbearance --
fenced and indented code, table rows, YAML frontmatter, and any line that fits
once the unbreakable runs in it are set aside (a link destination, an autolink,
a bare URL, an inline-code span). Each exclusion has a plant below asserting it stays green,
and each of those plants was verified by disabling its exclusion and watching
the plant redden; an exemption nothing can fail is an exemption nobody checked.

What it does not reach is stated with the rule, in
`docs/single-source-of-truth.md § Prose line width`.

Usage:
    check_prose_width.py              hold the tracked markdown to the width
    check_prose_width.py --self-test  assert the check reddens on each planted
                                      violation and stays green on each planted
                                      exemption, then hold the tree
"""

from __future__ import annotations

import os
import re
import subprocess
import sys

# --- the grammar of a line that cannot be broken ---------------------------
#
# Each of these is a run of characters with no legal line break inside it. A
# line is over the width only if it is still over it once they are out of the
# way, which is what makes the rule meetable: a table row has no break at all,
# and a citation's destination can be longer than the width on its own.

DESTINATION = re.compile(r"\]\([^)\s]*\)")       # an inline link or image target
AUTOLINK = re.compile(r"<https?://[^>\s]+>")
BARE_URL = re.compile(r"(?<![(<])\bhttps?://\S+")
CODE_SPAN = re.compile(r"`[^`\n]+`")
UNBREAKABLE = (DESTINATION, AUTOLINK, BARE_URL, CODE_SPAN)

FENCE = re.compile(r"^\s*(?:```|~~~)")
FRONTMATTER = "---"
WIDTH_KEY = "language.prose_width"


def collapse(line: str) -> str:
    """The line with every unbreakable run reduced to one character."""
    for pattern in UNBREAKABLE:
        line = pattern.sub("x", line)
    return line


def overruns(text: str, width: int) -> list[tuple[int, int, str]]:
    """(line number, length, line) for every line the rule holds and finds long."""
    found = []
    lines = text.splitlines()
    # Frontmatter is the file's own metadata and its fields are single-line by
    # the harness's grammar: a skill's `description` is one line however long.
    # ⛔ It counts as frontmatter only where it **closes**. An opening marker
    # with no closing one would otherwise exempt the whole file in silence,
    # which is the loudest way a sweep can stop holding something.
    in_frontmatter = (
        bool(lines)
        and lines[0].strip() == FRONTMATTER
        and any(line.strip() == FRONTMATTER for line in lines[1:])
    )
    fenced = False
    for number, line in enumerate(lines, 1):
        stripped = line.strip()
        if in_frontmatter:
            if number > 1 and stripped == FRONTMATTER:
                in_frontmatter = False
            continue
        if FENCE.match(line):
            fenced = not fenced
            continue
        if fenced:
            continue
        if stripped.startswith("|"):
            continue
        # An indented code block. A list's own continuation lines are indented
        # two or three spaces in this repository and are prose, so the test is
        # the four-space rule markdown itself uses, and only outside a list
        # item -- which a continuation line, having no marker, cannot be
        # distinguished from. Four spaces plus a marker is a nested item.
        if re.match(r"^(?: {4,}|\t)\S", line) and not re.match(r"^\s*(?:[-*+]|\d+\.)\s", line):
            continue
        if len(line) <= width:
            continue
        if len(collapse(line)) <= width:
            continue
        found.append((number, len(line), line))
    return found


# --- the tree ---------------------------------------------------------------


class Tree:
    """The tracked markdown and the configured width, in memory.

    A copy is a copy: the plants below mutate it rather than the working tree,
    so a self-test leaves no file behind in the checkout it ran in.
    """

    def __init__(self, root: str):
        self.root = root
        self.width = self._width()
        self.text = {path: self._read(path) for path in self._tracked()}

    def _tracked(self) -> list[str]:
        out = subprocess.run(
            ["git", "-C", self.root, "ls-files", "*.md"],
            capture_output=True, text=True,
        )
        return sorted(p for p in out.stdout.split("\n") if p)

    def _read(self, relative: str):
        """The file's text, or the reason it could not be read.

        ⛔ A tracked file missing from the working tree, or one that is not
        text, is a problem this check reports -- never a traceback out of the
        command a workflow runs. A file deleted without `git rm` is the common
        one, and it arrives mid-edit rather than in a broken tree.
        """
        try:
            with open(os.path.join(self.root, relative), encoding="utf-8") as handle:
                return handle.read()
        except (OSError, UnicodeDecodeError) as exc:
            return exc

    def _width(self):
        """The width this project states, through the one reader (§ 8)."""
        sys.path.insert(0, os.path.join(self.root, "plugins", "mjolnir", "scripts"))
        try:
            import config as reader  # noqa: PLC0415  -- the one reader, not a second parser
        except ImportError:
            return None
        try:
            return reader.load(self.root).get(WIDTH_KEY)
        except Exception:  # the reader names the key it refused; this check only needs the width
            return None

    def copy(self) -> "Tree":
        clone = Tree.__new__(Tree)
        clone.root, clone.width, clone.text = self.root, self.width, dict(self.text)
        return clone


# --- the check --------------------------------------------------------------


def check_prose_fits_the_configured_width(tree: Tree) -> list[str]:
    if not tree.width:
        return [
            f"the configuration states no `{WIDTH_KEY}`, so this check holds nothing. "
            "A project that does not hard-wrap its files states that by leaving the key "
            "out (§ 8) -- and then does not run this check either, rather than running "
            "one that passes on everything."
        ]
    if not tree.text:
        return [
            "no tracked markdown was found, so this check holds nothing. The file list "
            "comes from `git ls-files`, so a document is held only once it is indexed."
        ]
    problems = []
    for path in sorted(tree.text):
        text = tree.text[path]
        if isinstance(text, Exception):
            problems.append(
                f"{path}: is tracked and could not be read ({text}). A file the sweep "
                "cannot open is unheld, which is the one state this check may not report "
                "as green."
            )
            continue
        for number, length, line in overruns(text, tree.width):
            problems.append(
                f"{path}:{number}: {length} columns, over the configured {tree.width}. "
                f"Rewrap the paragraph: {' '.join(line.split())[:60]}…"
            )
    return problems


CHECKS = [("prose fits the configured width", check_prose_fits_the_configured_width)]


# --- the planted violations -------------------------------------------------
#
# ⛔ No plant names a file. The sweep's own first draft hardcoded one path and a
# rename turned `--self-test` -- the command the workflow runs -- into a
# `KeyError` instead of a verdict, so a plant takes whatever file is there and
# synthesises one where the set is empty.


def _a_document(tree: Tree) -> str:
    for path in sorted(tree.text):
        if not isinstance(tree.text[path], Exception):
            return path
    tree.text["planted.md"] = "# Planted\n"
    return "planted.md"


def _plant(line: str):
    def apply(tree: Tree) -> Tree:
        path = _a_document(tree)
        tree.text[path] = tree.text[path] + f"\n{line}\n"
        return tree

    return apply


def _long(filler: str, columns: int) -> str:
    return (filler * columns)[:columns]


def _plant_overlong_prose(tree: Tree) -> Tree:
    return _plant(_long("word ", (tree.width or 0) + 20))(tree)


def _plant_overlong_indented_prose(tree: Tree) -> Tree:
    """A list's continuation line is prose, and is held like any other."""
    return _plant("  " + _long("word ", (tree.width or 0) + 20))(tree)


def _plant_no_width_configured(tree: Tree) -> Tree:
    tree.width = None
    return tree


def _plant_nothing_tracked(tree: Tree) -> Tree:
    tree.text = {}
    return tree


def _plant_unreadable_file(tree: Tree) -> Tree:
    tree.text["docs/deleted-without-git-rm.md"] = FileNotFoundError("no such file")
    return tree


def _plant_unclosed_frontmatter(tree: Tree) -> Tree:
    """An opening marker with no closing one exempts nothing."""
    tree.text["docs/planted-frontmatter.md"] = (
        "---\nname: planted\n\n" + _long("word ", (tree.width or 0) + 20) + "\n"
    )
    return tree


VIOLATIONS = [
    ("prose fits the configured width", "an overlong paragraph", _plant_overlong_prose),
    ("prose fits the configured width", "an overlong continuation line",
     _plant_overlong_indented_prose),
    ("prose fits the configured width", "no width configured", _plant_no_width_configured),
    ("prose fits the configured width", "nothing tracked to hold", _plant_nothing_tracked),
    ("prose fits the configured width", "a tracked file that cannot be read",
     _plant_unreadable_file),
    ("prose fits the configured width", "a frontmatter marker that never closes",
     _plant_unclosed_frontmatter),
]


# --- the planted exemptions -------------------------------------------------
#
# The green side of the scope, which is the half an overrun count cannot show.
# Every plant here is longer than any width a project would state, and each was
# watched reddening with its own exclusion disabled.


def _plant_long_table_row(tree: Tree) -> Tree:
    return _plant("| " + _long("cell ", 400) + " |")(tree)


def _plant_long_fenced_line(tree: Tree) -> Tree:
    return _plant("```\n" + _long("code ", 400) + "\n```")(tree)


def _plant_long_indented_code(tree: Tree) -> Tree:
    return _plant("    " + _long("code ", 400))(tree)


def _plant_long_destination(tree: Tree) -> Tree:
    return _plant("A citation of [one section](" + _long("x", 400) + ").")(tree)


def _plant_long_autolink(tree: Tree) -> Tree:
    return _plant("Evidence at <https://example.invalid/" + _long("x", 400) + ">.")(tree)


def _plant_long_bare_url(tree: Tree) -> Tree:
    return _plant("Evidence at https://example.invalid/" + _long("x", 400))(tree)


def _plant_long_code_span(tree: Tree) -> Tree:
    return _plant("The command is `" + _long("x", 400) + "`.")(tree)


def _plant_long_frontmatter(tree: Tree) -> Tree:
    """A skill's own metadata: one line per field, however long the field is."""
    tree.text["planted/SKILL.md"] = (
        "---\nname: planted\ndescription: " + _long("word ", 400) + "\n---\n\n# Planted\n"
    )
    return tree


EXEMPTIONS = [
    ("a table row, which has no legal break", _plant_long_table_row),
    ("a fenced code line", _plant_long_fenced_line),
    ("an indented code line", _plant_long_indented_code),
    ("a link destination", _plant_long_destination),
    ("an autolink", _plant_long_autolink),
    ("a bare URL", _plant_long_bare_url),
    ("an inline-code span", _plant_long_code_span),
    ("a frontmatter field", _plant_long_frontmatter),
]


def run(tree: Tree) -> dict[str, list[str]]:
    return {name: check(tree) for name, check in CHECKS}


def self_test(tree: Tree) -> int:
    by_name = dict(CHECKS)
    # Against the tree's own result, not against zero: an assertion that reads
    # the whole problem list calls every plant red while one real overrun is
    # still in the tree, which would make the exemptions untestable exactly
    # when they matter -- in the change that is fixing the overruns.
    baseline = {name: set(check(tree)) for name, check in CHECKS}
    failures = 0
    for name, label, plant in VIOLATIONS:
        if set(by_name[name](plant(tree.copy()))) - baseline[name]:
            print(f"  red on                 {name}: {label}")
        else:
            print(f"  STAYED GREEN           {name}: {label}")
            failures += 1
    name = CHECKS[0][0]
    for label, plant in EXEMPTIONS:
        added = set(by_name[name](plant(tree.copy()))) - baseline[name]
        if added:
            print(f"  WENT RED               exempt: {label}")
            failures += 1
        else:
            print(f"  green on               exempt: {label}")
    if failures:
        print(
            f"\n{failures} assertion(s) did not hold. A check that cannot fail is not a "
            "check, and an exemption that cannot pass is not an exemption."
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
            "Asserting the check reddens on each planted violation "
            f"({len(VIOLATIONS)}) and stays green on each planted exemption "
            f"({len(EXEMPTIONS)}):"
        )
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
        f"\nEvery tracked markdown line fits the {tree.width} columns this project "
        "states, or is a line the format forbids breaking."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
