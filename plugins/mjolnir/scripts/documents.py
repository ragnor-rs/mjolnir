#!/usr/bin/env python3
"""Hold a project's prose documents to the properties its configuration states.

The rule is `plugins/mjolnir/config/schema.md § 38`, which states it and carries
the measurement behind it. Neither is restated here.

⛔ Every value is **read from the configuration**: the governed set, the entry
points, the reference graph, the forbidden names, anything quoted and the link
targets exempted. Nothing of
any project is written in this file, and a project whose `documents.carrier` is
`none` has no subject here -- which is reported as *no subject* rather than as a
verdict, because a check that holds nothing reports green.

⛔ **The three kinds are the whole of what a check's green is worth**, and each
check below declares which it is:

  COMPUTED   the property is derived -- a cell counted, a link resolved, a
             document walked to -- so no reword reaches it;
  FORBIDDING a name must not appear, which is sound exactly where the forbidden
             thing is stable, and the entry states what makes it so;
  QUOTING    a sentence quoted back at the file it came from. ⛔ It is performed
             as the project configured it **and warned about on every run**: it
             goes red on an innocent reword and green when the claim is reworded
             into its opposite, so neither of its verdicts says what a reader
             takes it to say.

⚠️ It needs no stack, no credential and no network: it reads the index and the
files in it. ⛔ And it runs no project's own domain checks -- whether a project's
request shapes each have a home in its layout is a property of that project's
subject matter, which § 38 leaves in that project's own script.

What is deliberately not held is stated once, with the rule, in
docs/single-source-of-truth.md#the-documents-against-the-graph-the-forbidden-list-and-their-own-blocks.

Usage:
    documents.py                  hold this project's documents
    documents.py --self-test      assert each check reddens on each planted
                                  violation and stays green on each planted
                                  exemption, then stop
"""

from __future__ import annotations

import argparse
import functools
import os
import re
import subprocess
import sys
import unicodedata
from urllib.parse import unquote

# The facet this copy holds a tree to, and where that tree's documents are read
# from relative to the repository this copy sits in. ⛔ `None` in the toolkit's
# own copy and rendered by the install step, which is what lets a host run this
# file in a checkout holding neither the toolkit nor the configuration -- and
# what keeps one project's graph out of every other project's gate.
STATED = None

FACET = "documents"
LIST = "list"

COMPUTED, FORBIDDING, QUOTING = "computed", "forbidding", "quoting"

# A markdown inline link or image destination. The fragment is dropped: an
# anchor is a position inside the target and the edge is to the file.
LINK = re.compile(r"\]\(([^)\s]+)\)")
ABSOLUTE = re.compile(r"^[a-z][a-z0-9+.-]*:", re.I)
FENCE = re.compile(r"^[ \t]*(?P<delim>`{3,}|~{3,})(?P<info>[^\n]*)$")
# A delimiter row: pipes, dashes, colons and space, with at least one dash. The
# dash is required, so `|   |   |` is a row with nothing in it rather than the
# shape that makes the rows above it a table.
DELIMITER = re.compile(r"^[ \t]*\|[-|: \t]*$")

# --- what the link check reads ---------------------------------------------
#
# A link's destination, in each of the forms a renderer follows: inline, with or
# without angle brackets and a title, and a reference definition on a line of
# its own. ⛔ A footnote definition (`[^1]: …`) is prose and not a destination.
# ⚠️ A bare destination may carry balanced parentheses, which the host follows:
# `a_(b).png` cut at its first `)` is a working link reported missing.
INLINE_LINK = re.compile(
    r"\]\(\s*(?:<(?P<angled>[^>\n]*)>|(?P<bare>(?:[^()\s]|\([^()\s]*\))+))"
    r"(?:\s+[^)\n]*)?\)"
)
DEFINITION = re.compile(
    r"^ {0,3}\[(?!\^)[^\]\n]+\]:[ \t]*(?:<(?P<angled>[^>\n]*)>|(?P<bare>\S+))"
)
# What a renderer shows rather than follows: an HTML comment, and a code span
# held to one line -- an odd backtick otherwise pairs with one a paragraph away
# and hides every link between them.
SHOWN = re.compile(
    r"<!--.*?(?:-->|\Z)|(?P<ticks>`+)(?:(?!(?P=ticks))[^\n])*(?P=ticks)", re.S
)
# A fragment the host answers that names no heading: a line range.
A_LINE_RANGE = re.compile(r"^L\d+(?:C\d+)?(?:-L?\d+(?:C\d+)?)?$")
HEADING = re.compile(r"^ {0,3}(#{1,6})[ \t]+(.*?)(?:[ \t]+#+)?[ \t]*$")
# The underline of a setext heading, which makes the line above it a heading.
UNDERLINE = re.compile(r"^ {0,3}(?:=+|-+)[ \t]*$")
EXPLICIT_ANCHOR = re.compile(r"""<a\s[^>]*?\b(?:id|name)\s*=\s*["']([^"']+)["']""", re.I)
MARKDOWN = (".md", ".markdown")


def flat(text: str) -> str:
    """The text with every run of whitespace collapsed to one space.

    ⛔ Here because a document is **wrapped**: a sentence quoted against one
    spans a line break, and a comparison that did not flatten both sides would
    report a sentence that is there as gone.
    """
    return " ".join(text.split())


def glob_regex(glob: str) -> re.Pattern:
    """A governed-set glob, where `*` stops at a separator and `**` crosses one.

    ⛔ **Deliberately not the end-to-end register's semantics** -- § 15's
    consumer matches a case glob with the shell's own wildcards, where `*`
    crosses a separator -- and the difference is stated rather than left to be
    discovered: a
    governed set is a statement about *where* a project's documents live, so a
    wildcard that crossed a separator could not say *the root's own markdown and
    not a nested directory's* at all -- and a project writing `*.md` would
    silently govern every markdown file in its tree, the skills and the vendored
    ones among them.
    """
    out, index = [], 0
    while index < len(glob):
        char = glob[index]
        if glob.startswith("**/", index):
            out.append(r"(?:[^/]+/)*")
            index += 3
        elif glob.startswith("**", index):
            out.append(r".*")
            index += 2
        elif char == "*":
            out.append(r"[^/]*")
            index += 1
        elif char == "?":
            out.append(r"[^/]")
            index += 1
        else:
            out.append(re.escape(char))
            index += 1
    return re.compile("^" + "".join(out) + "$")


def governed(path: str, globs) -> bool:
    return any(glob_regex(glob).match(path) for glob in globs)


def fences(text: str) -> tuple:
    """The line numbers inside a fenced block, and whether one was left open.

    Returned as the pair, because an unclosed fence is one of the checks and the
    scan that finds it is the scan every other check needs anyway.
    """
    inside, open_at, lines = set(), None, text.splitlines()
    for number, line in enumerate(lines, 1):
        found = FENCE.match(line)
        if found and open_at is None:
            open_at = (number, found.group("delim"))
            continue
        if found and open_at is not None:
            # ⛔ A closing delimiter is at least as long as the opening one and
            # of the same character, which is the format's own rule: a ``` line
            # inside a ~~~ block is content, and treating it as a close would
            # make every nested example read as prose.
            delim = found.group("delim")
            if delim[0] == open_at[1][0] and len(delim) >= len(open_at[1]):
                open_at = None
                continue
        if open_at is not None:
            inside.add(number)
    return frozenset(inside), open_at


def mentioned(text: str, path: str, named_as: str | None = None) -> bool:
    """Whether the text names this document, by its own spelling or by its path.

    ⛔ **`named_as` is the project's own spelling and the path is only the
    default.** ⚠️ **Measured on one of the two implementations this facet was
    read out of**: it refers to each of its eight role carriers by that
    carrier's **slug** and never by its filename, so matching on the path alone
    reported thirty of its declared edges as edges the text had dropped.

    The rest of this docstring is about the default form.

    ⛔ **The boundary is the whole of what makes a bare path usable as an edge**,
    and a plain substring test is wrong in exactly the case it is needed for. ⚠️
    **Measured against the implementation this property was read out of**: that
    project carries a root `CLAUDE.md`, a `tech/CLAUDE.md` and a
    `main_website-CLAUDE.md`, and it recognises the first with three lookbehinds
    of its own -- `(?<!tech/)`, `(?<!main_website/)`, `(?<!main_website-)`. A
    substring test reports an edge to the root file from every document that
    names either of the others.

    ⛔ **So the boundary reproduces those patterns and the facet declares no key
    for them**, which is what makes that project's rules expressible here
    without a special case: every one of its per-node lookbehinds is a leading
    path character.

    ⚠️ **A trailing `.` is admitted on purpose**: a mention at the end of a
    sentence is the commonest form of all, and refusing it would cost far more
    than the longer-path-with-the-same-prefix case it would catch.
    """
    if named_as:
        return re.search(named_as, text) is not None
    return re.search(
        r"(?<![\w/.\-])" + re.escape(path) + r"(?![\w/\-])", text
    ) is not None


def names(text: str, here: str, documents) -> set:
    """Every governed document this text names, by link target or by its spelling.

    ⛔ Both forms, because either alone is half the edge: a project writes most
    of its references as links and some as a bare name in prose or in a listing,
    and a reader of one form reports the other as an edge the row invented.

    ⚠️ `documents` maps each document to its `named_as`, or to `None` where the
    row states none and the path is the spelling.
    """
    found = set()
    for target in LINK.findall(text):
        path = target.split("#", 1)[0]
        if not path or ABSOLUTE.match(path):
            continue
        resolved = os.path.normpath(os.path.join(os.path.dirname(here), path))
        if resolved in documents:
            found.add(resolved)
    for other, named_as in documents.items():
        if mentioned(text, other, named_as):
            found.add(other)
    found.discard(here)
    return found


def links(text: str) -> list:
    """Every link destination a renderer would follow, as (line number, destination).

    ⛔ **What a document shows is not what it links**: a destination inside a
    fence, a code span or an HTML comment is an example, and reading it as live
    refuses the prose that documents a link's own syntax. The shown spans are
    blanked character for character, so every line keeps its number.
    """
    inside, _open = fences(text)
    blanked = SHOWN.sub(lambda found: re.sub(r"[^\n]", " ", found.group(0)), text)
    out = []
    for number, line in enumerate(blanked.splitlines(), 1):
        if number in inside:
            continue
        for found in INLINE_LINK.finditer(line):
            out.append((number, found.group("angled") or found.group("bare") or ""))
        definition = DEFINITION.match(line)
        if definition:
            out.append(
                (number, definition.group("angled") or definition.group("bare") or "")
            )
    return out


def slug(heading: str) -> str:
    """A heading's anchor, the way the code host derives it.

    ⛔ **One hyphen per space and no collapsing**: a heading carrying a dash
    between two spaces is answered with two hyphens, so a collapsing slug
    refuses a working link. A link inside a heading contributes its text, which
    is what the host renders.
    """
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", heading)
    text = re.sub(r"<[^>]+>", "", text).strip().lower().replace("`", "")
    text = re.sub(r"[^\w\s-]", "", text)
    return text.replace(" ", "-")


@functools.lru_cache(maxsize=None)
def anchors(text: str) -> frozenset:
    """Every fragment a document answers: its headings, and the anchors it writes.

    ⚠️ A repeated heading carries the host's `-1`, `-2` suffix, so a link to the
    second section of a title resolves and the first does not stand in for it.
    ⚠️ Both heading forms are read -- a `#` line, and a line underlined with `=`
    or `-` -- since a link into either is a link the host follows. A line inside
    the opening frontmatter is no heading, whatever follows it.

    ⛔ Cached, because one target is asked about once per link into it: uncached,
    this repository's own run spent 24 seconds slugging one surface again for
    each of its two thousand fragments.
    """
    inside, _open = fences(text)
    lines = text.splitlines()
    front = set()
    if lines and lines[0].strip() == "---":
        for number, line in enumerate(lines[1:], 2):
            if line.strip() == "---":
                front.update(range(1, number + 1))
                break
    found, seen = set(), {}

    def add(title: str) -> None:
        base = slug(title)
        nth = seen.get(base, 0)
        seen[base] = nth + 1
        found.add(base if nth == 0 else f"{base}-{nth}")

    for number, line in enumerate(lines, 1):
        if number in inside or number in front:
            continue
        heading = HEADING.match(line)
        if heading:
            add(heading.group(2))
            continue
        above = lines[number - 2] if number > 1 else ""
        if UNDERLINE.match(line) and above.strip() and number - 1 not in inside \
                and number - 1 not in front and not HEADING.match(above) \
                and not UNDERLINE.match(above) \
                and not above.lstrip().startswith(("|", ">", "- ", "* ", "+ ")):
            add(above)
    blanked = SHOWN.sub(lambda shown: re.sub(r"[^\n]", " ", shown.group(0)), text)
    found.update(anchor.lower() for anchor in EXPLICIT_ANCHOR.findall(blanked))
    return frozenset(found)


class Subject:
    """The governed documents, the graph and the lists, in memory.

    A copy is a copy: the plants below mutate it rather than the working tree, so
    a self-test leaves no file behind in the checkout it ran in.
    """

    def __init__(self, root, facet, tracked, text):
        self.root = root
        self.files = list(facet.get("files") or ())
        self.entry_points = list(facet.get("entry_points") or ())
        self.rows = {
            row["document"]: {
                # ⛔ `None` is kept as `None`: it is a third state, the edge
                # this project does not enforce for that document, and a reader
                # that coerced it to `[]` would turn the strictest rule in the
                # facet on for a project that declared no graph at all.
                "may_name": (
                    None if row.get("may_name") is None
                    else list(row.get("may_name") or ())
                ),
                "derived_from": list(row.get("derived_from") or ()),
                "named_as": row.get("named_as"),
            }
            for row in facet.get("graph") or ()
        }
        self.forbidden = [dict(entry) for entry in facet.get("forbidden") or ()]
        self.quoted = [dict(entry) for entry in facet.get("quoted") or ()]
        # ⛔ Absent is `[]`: omitting the key exempts nothing, which is the
        # strict direction and the only one a default may take here (§ 38).
        self.exempt = list(facet.get("exempt_targets") or ())
        # ⛔ `None` where the project states no block, kept apart from a block
        # reading `held: false` only so a run can say which; both hold nothing.
        self.box_diagrams = (
            None if facet.get("box_diagrams") is None
            else {
                "held": bool(facet["box_diagrams"].get("held")),
                "exempt": [dict(e) for e in facet["box_diagrams"].get("exempt") or ()],
            }
        )
        self.tracked = sorted(tracked)
        self.text = dict(text)

    @property
    def diagrams_held(self) -> bool:
        return bool(self.box_diagrams and self.box_diagrams["held"])

    @property
    def set_now(self) -> list:
        """The tracked files the globs govern, which is the set every check is over."""
        return [path for path in self.tracked if governed(path, self.files)]

    def is_entry(self, path: str) -> bool:
        return any(glob_regex(glob).match(path) for glob in self.entry_points)

    @property
    def spellings(self) -> dict:
        """Each document in the graph or the governed set, to how prose names it."""
        found = {path: None for path in self.set_now}
        for path, row in self.rows.items():
            found[path] = row.get("named_as")
        return found

    @property
    def enforced(self) -> list:
        """The governed documents whose row states an enforced edge.

        ⛔ The three graph checks are over these and no others. Where there are
        none they return nothing and `warnings` is what says the graph half holds
        nothing -- a project that enforces no edge is a legitimate configuration,
        so what it is owed is the disclosure rather than a permanent red.
        """
        return [
            path for path in self.set_now
            if path in self.rows and self.rows[path]["may_name"] is not None
        ]

    @property
    def unenforced(self) -> list:
        """The governed documents whose row states `may_name: null`.

        ⛔ **A document with no row at all is not one of these**, and the two were
        measured collapsed: keyed on a missing row reading as `null`, a document
        the graph had never declared was reported as one this project *decided*
        not to enforce -- and a tree where no document had a row at all was
        reported as one where every row states `null`. Both are a different
        fault, and check 1 is what reports it.
        """
        return [
            path for path in self.set_now
            if path in self.rows and self.rows[path]["may_name"] is None
        ]

    @property
    def indexed(self) -> set:
        """Every path a link may resolve to: each tracked file and each directory above one.

        ⛔ **The index and not the disk**, for the reason the governed set is read
        from it: a file nobody added is a link target the host does not serve.
        """
        found = set(self.tracked)
        for path in self.tracked:
            parts = path.split("/")[:-1]
            for depth in range(1, len(parts) + 1):
                found.add("/".join(parts[:depth]))
        return found

    def read(self, path: str):
        return self.text.get(path, FileNotFoundError("not in the index"))

    def read_target(self, path: str):
        """A link target's text: the governed set's copy, or the file itself.

        A markdown target the globs do not govern is still a target whose
        headings a fragment names, so it is read from the tree rather than held
        to nothing.
        """
        if path in self.text:
            return self.text[path]
        try:
            with open(os.path.join(self.root, path), encoding="utf-8") as handle:
                return handle.read()
        except (OSError, UnicodeDecodeError) as exc:
            return exc

    def copy(self) -> "Subject":
        clone = Subject.__new__(Subject)
        clone.root, clone.files = self.root, list(self.files)
        clone.entry_points = list(self.entry_points)
        clone.rows = {doc: dict(row) for doc, row in self.rows.items()}
        clone.forbidden = [dict(entry) for entry in self.forbidden]
        clone.quoted = [dict(entry) for entry in self.quoted]
        clone.exempt = list(self.exempt)
        clone.box_diagrams = (
            None if self.box_diagrams is None
            else {
                "held": self.box_diagrams["held"],
                "exempt": [dict(e) for e in self.box_diagrams["exempt"]],
            }
        )
        clone.tracked, clone.text = list(self.tracked), dict(self.text)
        return clone


def read_subject(root: str, facet: dict) -> Subject:
    """The subject read off one tree: the index, and each governed file's text."""
    out = subprocess.run(
        ["git", "-C", root, "ls-files"], capture_output=True, text=True,
    )
    tracked = sorted(path for path in out.stdout.split("\n") if path)
    files = list(facet.get("files") or ())
    text = {}
    for path in tracked:
        if not governed(path, files):
            continue
        try:
            with open(os.path.join(root, path), encoding="utf-8") as handle:
                text[path] = handle.read()
        except (OSError, UnicodeDecodeError) as exc:
            # ⛔ A tracked file missing from the tree, or one that is not text, is
            # a problem this check reports -- never a traceback out of the command
            # a workflow runs. A file deleted without `git rm` is the common one.
            text[path] = exc
    return Subject(root, facet, tracked, text)


# --- the checks -------------------------------------------------------------


def check_every_governed_document_has_a_row(subject: Subject) -> list:
    """The governed set against the graph, both ways, and the files behind it.

    ⛔ A tracked document the globs govern and no row declares is the one that
    matters: a new store of prose is exactly the thing that quietly becomes a
    second authority, and a graph that does not know about it never checks it at
    all. ⚠️ **Not a skip** -- the permissive reading is what leaves it unheld.
    """
    if not subject.set_now:
        return [
            "the globs this project states govern no tracked file, so every check "
            "here passes for a reason that has nothing to do with the documents. "
            f"The globs are {subject.files}; the index was read with `git ls-files`, "
            "so a document is governed only once it is indexed."
        ]
    problems = []
    for path in subject.set_now:
        if path not in subject.rows:
            problems.append(
                f"{path}: is governed by {subject.files} and no row of `documents.graph` "
                "declares it, so it sits outside the graph and nothing holds it. Give it "
                "a row, which is a decision about where it sits, or narrow the globs."
            )
        text = subject.read(path)
        if isinstance(text, Exception):
            problems.append(
                f"{path}: is governed and could not be read ({text}). A document the "
                "sweep cannot open is unheld, which is the one state this check may not "
                "report as green."
            )
    for document in sorted(subject.rows):
        if document not in subject.set_now:
            problems.append(
                f"{document}: has a row of `documents.graph` and is not a governed "
                "tracked file. Every assertion over a document that moved otherwise "
                "reports green, which is the same failure from the other side."
            )
    return problems


def check_a_document_names_only_what_its_row_allows(subject: Subject) -> list:
    """The enforced edge, in the direction a filename appearing is the defect.

    ⛔ An empty row may name nothing at all, and that is where the teeth are: a
    filename in such a document is an edge running the wrong way.
    """
    # ⛔ Where nothing is enforced this check holds nothing, and what it owes is
    # the **disclosure** rather than a red: a project that declares no reference
    # graph is a legitimate configuration -- one of the two this facet was read
    # out of is exactly that -- and a permanent red is not a check. `warnings`
    # below says so on every run.
    problems = []
    documents = subject.spellings
    for path in subject.enforced:
        text = subject.read(path)
        if isinstance(text, Exception):
            continue
        allowed = set(subject.rows[path]["may_name"])
        for named in sorted(names(text, path, documents) - allowed):
            problems.append(
                f"{path}: names {named!r}, which its `may_name` row does not allow"
                + (
                    " -- and that row is empty, so this document may name no other "
                    "document at all."
                    if not allowed
                    else f". It may name: {sorted(allowed)}."
                )
            )
    return problems


def check_a_row_names_only_edges_the_text_carries(subject: Subject) -> list:
    """The enforced edge, in the direction nothing else reports.

    ⛔ Held because one direction is half a check: without this, a row stating an
    edge the text has dropped stays green for ever, and the graph goes on being
    read as the document's own contents.
    """
    problems = []
    documents = subject.spellings
    for path in subject.enforced:
        text = subject.read(path)
        if isinstance(text, Exception):
            continue
        carried = names(text, path, documents)
        for named in subject.rows[path]["may_name"]:
            if named not in carried:
                problems.append(
                    f"{path}: its `may_name` row states {named!r} and the text does not "
                    "name it. A row's edge the document dropped is a graph that no longer "
                    "describes the documents -- delete the edge, or restore the reference."
                )
    return problems


def check_every_document_is_reachable(subject: Subject) -> list:
    """Reachability from an entry point, which no per-file check can see.

    ⛔ Entry points are a **list** rather than one root, because a document
    addressed by name from outside the prose is arrived at without any document
    naming it -- a role carrier loaded by a harness being the measured case.
    """
    if subject.set_now and not subject.enforced:
        # ⛔ With no edge enforced anywhere there is no graph to walk at all, so
        # every governed document would be reported unreachable -- one state
        # reported as many findings. The disclosure is `warnings`'s.
        return []
    reached, frontier = set(), []
    for path in subject.set_now:
        if subject.is_entry(path):
            reached.add(path)
            frontier.append(path)
    while frontier:
        path = frontier.pop()
        for named in subject.rows.get(path, {}).get("may_name") or ():
            if named not in reached:
                reached.add(named)
                frontier.append(named)
    problems = []
    if not reached and subject.set_now:
        problems.append(
            f"no governed document matches an entry point. The entry points are "
            f"{subject.entry_points}, so nothing is a starting place and every document "
            "below is unreachable for that one reason."
        )
    for path in subject.set_now:
        if path not in reached:
            problems.append(
                f"{path}: is governed and no entry point reaches it by a `may_name` edge. "
                "A document nothing names and nothing addresses is a document no reader "
                "arrives at -- have something name it, or state it as an entry point and "
                "say why it is one."
            )
    return problems


def check_every_link_resolves(subject: Subject) -> list:
    """Every relative link in a governed document reaching something the index holds.

    ⛔ Computed: the target is resolved against the index and the fragment
    against the target's own headings, so no reword of the link text reaches it.
    ⛔ **An address outside the repository is not fetched** -- it names a host
    this check has no business asking, and a network read would make the verdict
    a fact about the day it ran. ⚠️ Two fragments are accepted unresolved: a line
    range, which the host answers and no heading carries, and one on a file that
    is not markdown, which has no headings to hold it to.
    """
    problems = []
    present = subject.indexed
    for path in subject.set_now:
        text = subject.read(path)
        if isinstance(text, Exception):
            continue
        for number, destination in links(text):
            if not destination or ABSOLUTE.match(destination) \
                    or destination.startswith("//"):
                continue
            target, _hash, fragment = destination.partition("#")
            target, fragment = unquote(target), unquote(fragment)
            if not target:
                resolved = path
            elif target.startswith("/"):
                resolved = os.path.normpath(target.lstrip("/") or ".")
            else:
                resolved = os.path.normpath(os.path.join(os.path.dirname(path), target))
            where = f"{path}:{number}: links to {destination!r}"
            # ⚠️ A link climbing out of the repository needs no arm of its own:
            # it resolves to a `../` path no index holds, and is reported below.
            # ⚠️ A link to an exempt directory itself is exempt: `site/**`
            # covers `site/`, which is the directory a generated index sits in.
            if resolved == "." or governed(resolved, subject.exempt) \
                    or governed(resolved + "/", subject.exempt):
                continue
            if resolved not in present:
                problems.append(
                    f"{where}, which resolves to {resolved!r}, and the index holds no file "
                    "or directory there. Restore the target, correct the link, or -- for a "
                    "file the build generates -- exempt it in `documents.exempt_targets`."
                )
                continue
            if not fragment or A_LINE_RANGE.match(fragment) \
                    or not resolved.lower().endswith(MARKDOWN):
                continue
            body = subject.read_target(resolved)
            if isinstance(body, Exception):
                problems.append(
                    f"{where}, and {resolved!r} could not be read ({body}), so whether it "
                    f"carries {fragment!r} is unanswered rather than passed."
                )
                continue
            if fragment.lower() not in anchors(body):
                problems.append(
                    f"{where}, and {resolved!r} carries no heading or anchor whose slug is "
                    f"{fragment!r}. A heading renamed or removed leaves every link into it "
                    "landing at the top of the document."
                )
    return problems


def check_no_forbidden_name_appears(subject: Subject) -> list:
    """The forbidding kind, over the governed set, each entry as the project wrote it."""
    problems = []
    for index, entry in enumerate(subject.forbidden):
        pattern = entry.get("pattern") or ""
        try:
            compiled = re.compile(pattern)
        except re.error as exc:
            # ⛔ A pattern that cannot be evaluated is reported rather than
            # treated as matching nothing: that is how a typo becomes an
            # assertion that can never fail again.
            problems.append(
                f"documents.forbidden[{index}]: {pattern!r} is not a usable expression "
                f"({exc}), so this check could not be evaluated at all. A pattern that "
                "does not compile is never *no match*."
            )
            continue
        for path in subject.set_now:
            text = subject.read(path)
            if isinstance(text, Exception):
                continue
            for number, line in enumerate(text.splitlines(), 1):
                if compiled.search(line):
                    problems.append(
                        f"{path}:{number}: carries {pattern!r}, which this project "
                        f"forbids: {' '.join(str(entry.get('reason')).split())}"
                    )
    return problems


def delimiters(line: str) -> int:
    """The cell delimiters in a row, which is every `|` the table's own grammar reads.

    ⛔ **An escaped `\\|` is one character of a cell and not a delimiter**, and
    this is the arm the obvious count gets wrong. ⚠️ **Measured on this
    repository's own decision record, on this check's first real run**: a ruling
    whose cell carries `` `high \\| medium \\| low` `` was reported as a row with
    two cells too many, while the document renders exactly as its author wrote
    it. The implementation this property was read out of counts the raw
    character and has the same defect.

    ⚠️ A doubled backslash is a literal backslash, so the pipe after it *is* a
    delimiter -- counted by consuming the escape rather than by looking back one
    character, which is what makes that case come out right.
    """
    found, index = 0, 0
    while index < len(line):
        char = line[index]
        if char == "\\":
            index += 2
            continue
        if char == "|":
            found += 1
        index += 1
    return found


def cells(line: str) -> int:
    """The cells a row carries, with the optional closing delimiter discounted.

    ⛔ **The closing `|` is optional in the format and a raw delimiter count
    treats it as a cell.** ⚠️ Measured: a table whose last row is written
    `| one | two` -- two cells, no closing delimiter -- was reported ragged
    against the rows above it, while a renderer reads the two forms
    identically. ⚠️ Whether the last character *is* a delimiter is asked by
    counting rather than by looking at it, so a row ending in an escaped `\\|`
    is not discounted.
    """
    found = delimiters(line)
    if line.endswith("|") and found > delimiters(line[:-1]):
        return found - 1
    return found


def _tables(text: str, inside) -> list:
    """Every run of consecutive pipe lines outside a fence, each as [(number, line)]."""
    runs, current = [], []
    for number, line in enumerate(text.splitlines(), 1):
        if number in inside:
            continue
        if line.lstrip().startswith("|"):
            current.append((number, line.rstrip()))
            continue
        if current:
            runs.append(current)
            current = []
    if current:
        runs.append(current)
    return runs


def check_a_table_keeps_its_shape(subject: Subject) -> list:
    """Every row of a table carrying the same number of cells.

    ⛔ Computed, and the kind is the point: a row short of a cell renders with
    every value after the gap under the wrong column, which no forbidding check
    could express -- there is nothing to ban.
    """
    problems = []
    for path in subject.set_now:
        text = subject.read(path)
        if isinstance(text, Exception):
            continue
        inside, _open = fences(text)
        for run in _tables(text, inside):
            # ⛔ A run of one line has nothing to compare, so the shape check is
            # silent about it and the **block** check is what reports it: a lone
            # line of pipes carries no delimiter row. ⚠️ Its plant is therefore
            # in that check and not here, which is where the first form of this
            # file put a green-side plant that no mutation of this guard decided.
            if len(run) < 2:
                continue
            widths = {cells(line) for _n, line in run}
            if len(widths) != 1:
                problems.append(
                    f"{path}:{run[0][0]}-{run[-1][0]}: the rows of this table carry "
                    f"{sorted(widths)} cell delimiters. A row short of a cell takes the "
                    "next column's value, and the table reads as consistent."
                )
    return problems


def check_a_table_row_keeps_its_table(subject: Subject) -> list:
    """A line of pipes that is a paragraph, which is the measured hole.

    ⚠️ Measured on this repository: a ruling appended after the blank line that
    ends a table was answered `<p>| 32 | … |</p>` by the host's own renderer
    while every check over that document was green -- each of them holding a
    line, or holding the document against the surface, and none its blocks.

    ⛔ The defect is the **absence** of a delimiter row under a line that begins
    a table, so there is no name and no pattern to forbid: this is the kind a
    forbidding check cannot express.
    """
    problems = []
    for path in subject.set_now:
        text = subject.read(path)
        if isinstance(text, Exception):
            continue
        inside, _open = fences(text)
        for run in _tables(text, inside):
            if any(DELIMITER.match(line) for _n, line in run):
                continue
            problems.append(
                f"{path}:{run[0][0]}" + (f"-{run[-1][0]}" if len(run) > 1 else "")
                + ": this run of pipe lines carries no delimiter row, so a renderer "
                "reads it as a paragraph with its pipes showing rather than as a table. "
                "A row separated from its own table by a blank line is the measured case."
            )
    return problems


def check_no_document_leaves_a_fence_open(subject: Subject) -> list:
    """An unclosed fence, which stops every check after it seeing prose at all."""
    problems = []
    for path in subject.set_now:
        text = subject.read(path)
        if isinstance(text, Exception):
            continue
        _inside, open_at = fences(text)
        if open_at:
            number, delim = open_at
            problems.append(
                f"{path}:{number}: opens a {delim!r} fence that never closes, so every "
                "line after it is read as code -- by a renderer, and by every check over "
                "this document that skips fenced lines."
            )
    return problems


def check_a_quoted_sentence_is_still_in_its_document(subject: Subject) -> list:
    """The kind that does not work, performed as the project configured it.

    ⛔ Its warning is emitted on every run whatever this returns, by
    `warnings` below: what a project is owed here is the disclosure, not a
    refusal to run the check it asked for.
    """
    problems = []
    for index, entry in enumerate(subject.quoted):
        document, sentence = entry.get("document"), entry.get("sentence") or ""
        text = subject.read(document)
        if isinstance(text, Exception):
            problems.append(
                f"documents.quoted[{index}]: {document!r} could not be read ({text}), so "
                "the sentence quoted against it was compared with nothing."
            )
            continue
        # ⛔ **Both sides flattened, because a document is hard-wrapped.** ⚠️
        # Measured on this very facet: a sentence present in a document that
        # wraps at a stated column spans a line break, so a raw substring test
        # reports it missing -- which this kind then reads as the claim having
        # been reworded away. A quoting check that cannot find a sentence that
        # is there is worse than the kind's own failure modes.
        if flat(sentence) not in flat(text):
            problems.append(
                f"{document}: no longer carries the quoted sentence "
                f"{sentence[:60]!r}. ⚠️ Read this as the kind says: the document may have "
                "been reworded without the claim changing, in which case the entry is "
                "what is wrong."
            )
    return problems


# --- box diagrams ------------------------------------------------------------
#
# ⛔ The arms of a box-drawing character are read off its **Unicode name** and
# never tabulated: the block names every character by the directions it reaches
# -- `BOX DRAWINGS LIGHT DOWN AND RIGHT`, `... VERTICAL AND HORIZONTAL`,
# `... DOWN SINGLE AND RIGHT DOUBLE` -- so the light, heavy, double, arc and
# mixed forms are one rule, and a table here would be a second statement of the
# block free to disagree with it.

ARM_WORDS = {
    "UP": {"up"}, "DOWN": {"down"}, "LEFT": {"left"}, "RIGHT": {"right"},
    "VERTICAL": {"up", "down"}, "HORIZONTAL": {"left", "right"},
}
OPPOSITE = {"up": "down", "down": "up", "left": "right", "right": "left"}
STEP = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}


def arms(char: str) -> frozenset:
    """The directions a character reaches, empty for anything that is not a line.

    ⚠️ An arrowhead is outside the block and carries no arm, so it reads as text:
    a tip touching a junction and a tail leaving one are each drawn correctly,
    and no direction an arrowhead could be given would tell them apart.
    """
    if not "\u2500" <= char <= "\u257f":
        return frozenset()
    found = set()
    for word in unicodedata.name(char, "").split():
        found |= ARM_WORDS.get(word, set())
    return frozenset(found)


def is_junction(char: str) -> bool:
    """A corner, a tee or a cross: a box character reaching both ways at once.

    ⛔ **Only these are held.** A straight run and a half line may end where the
    drawing does -- a tree listing's `├── name` ends every horizontal run in a
    space -- while a corner's arm meeting nothing is the misalignment itself.
    """
    found = arms(char)
    return bool(found & {"up", "down"}) and bool(found & {"left", "right"})


def width(char: str) -> int:
    """A character's display width: two where East Asian wide, none where it marks.

    ⛔ **Display width and not code points**, which is the whole of why a box
    that looks aligned in its author's editor is not: a wide character takes two
    columns, so a row carrying one is one column longer on screen per character
    than its code point count says.

    ⚠️ An ambiguous-width character -- `→`, `▶`, the box characters themselves --
    counts one, as a terminal outside an East Asian locale draws it.
    """
    if unicodedata.combining(char) or unicodedata.category(char) in ("Mn", "Me", "Cf"):
        return 0
    if unicodedata.east_asian_width(char) in ("W", "F"):
        return 2
    return 1


def grid(line: str) -> dict:
    """Each display column of a line, to the character drawn there.

    The second column of a wide character maps to `""`, which carries no arm: a
    junction whose arm lands on half of a wide character meets nothing.
    """
    cells, column = {}, 0
    for char in line:
        if char == "\t":
            column += 8 - column % 8
            continue
        size = width(char)
        if size == 0:
            continue
        cells[column] = char
        for extra in range(1, size):
            cells[column + extra] = ""
        column += size
    return cells


def diagram_blocks(text: str) -> list:
    """Every fenced block carrying a box-drawing character, as [(number, line)].

    ⛔ **Fenced, and carrying one at all**: a block drawn in ASCII is not read,
    and neither is a box character in running prose -- each is outside what the
    rule is about rather than a diagram that passed.

    ⛔ **The blocks are the runs of `fences`'s own lines**, never a second scan:
    which delimiter closes which is that function's rule, and a copy of it here
    would be free to disagree about a nested example. Two blocks are told apart
    by the delimiter lines between them, which `fences` leaves out.
    """
    inside, _open = fences(text)
    lines = text.splitlines()
    blocks, current = [], []
    for number in sorted(inside):
        if current and number != current[-1][0] + 1:
            blocks.append(current)
            current = []
        current.append((number, lines[number - 1]))
    if current:
        blocks.append(current)
    return [
        block for block in blocks
        if any(arms(char) for _n, line in block for char in line)
    ]


def misalignments(block: list) -> list:
    """Each junction arm in one block that meets no opposite arm, as (line, column, arm, met)."""
    rows = [grid(line) for _n, line in block]
    found = []
    for index, cells in enumerate(rows):
        for column, char in sorted(cells.items()):
            if not char or not is_junction(char):
                continue
            for arm in sorted(arms(char)):
                d_row, d_col = STEP[arm]
                at = index + d_row
                met = rows[at].get(column + d_col, " ") if 0 <= at < len(rows) else None
                if not meets_nothing(met, arm):
                    continue
                found.append((block[index][0], column + 1, char, arm, met))
    return found


def meets_nothing(met, arm: str) -> bool:
    """Whether what a junction's arm lands on leaves that arm drawn to nothing.

    ⛔ **Text is a label and not a defect.** ⚠️ The measured case is `tree`'s own
    output, which puts each nested `└` under the first letter of its parent's
    name and the first `├` under the root's: read strictly, every listing it
    prints is red. What is a misalignment is the arm landing on a space, past
    the block's edge, on either column of a wide character -- where a box drawn
    by code point count puts its corner -- or on a line that does not reach back.
    """
    if met is None or met == "" or met == " ":
        return True
    # ⛔ **Either column of a wide character, and not only its second.** ⚠️
    # Measured on this check's own plant: a box drawn by code point count around
    # two wide characters puts its corner over the *first* column of the second
    # one, which the text arm below then read as a label -- so the one defect
    # display width exists to find went green. A listing that names a file in
    # wide characters and draws a line to it is the cost, and `exempt` is where
    # such a block is named.
    if width(met) == 2:
        return True
    reached = arms(met)
    if reached:
        return OPPOSITE[arm] not in reached
    return False


def check_a_box_diagram_keeps_its_edges(subject: Subject) -> list:
    """Every junction of a box diagram meeting what it was drawn to, where held.

    ⛔ Computed: the defect is an arm meeting nothing, which has no name to
    forbid. Columns are display columns, and a red names the junction's line.
    """
    if not subject.diagrams_held:
        return []
    problems = []
    exemptions = []
    for index, entry in enumerate(subject.box_diagrams["exempt"]):
        try:
            exemptions.append((index, entry, re.compile(entry.get("block") or "")))
        except re.error as exc:
            problems.append(
                f"documents.box_diagrams.exempt[{index}]: {entry.get('block')!r} is not "
                f"a usable expression ({exc}), so this exemption could not be evaluated. "
                "An exemption that does not compile is never *matches nothing*."
            )
    used = set()
    for path in subject.set_now:
        text = subject.read(path)
        if isinstance(text, Exception):
            continue
        for block in diagram_blocks(text):
            body = "\n".join(line for _n, line in block)
            exempted = [
                index for index, entry, compiled in exemptions
                if entry.get("document") == path and compiled.search(body)
            ]
            if exempted:
                used.update(exempted)
                continue
            for number, column, char, arm, met in misalignments(block):
                what = (
                    "the edge of the block" if met is None
                    else "half of a wide character" if met == ""
                    else f"{met!r}"
                )
                problems.append(
                    f"{path}:{number}: the {char!r} at display column {column} reaches "
                    f"{arm} and meets {what}, which carries no arm back -- an edge or "
                    "corner of this diagram does not line up."
                )
    for index, entry, _compiled in exemptions:
        if index not in used:
            problems.append(
                f"documents.box_diagrams.exempt[{index}]: matches no diagram in "
                f"{entry.get('document')!r}. An exemption that outlived its diagram "
                "silently covers whatever is drawn there next -- remove it, or correct "
                "the expression."
            )
    return problems


CHECKS = [
    ("every governed document has a row", COMPUTED,
     check_every_governed_document_has_a_row),
    ("a document names only what its row allows", COMPUTED,
     check_a_document_names_only_what_its_row_allows),
    ("a row names only edges the text carries", COMPUTED,
     check_a_row_names_only_edges_the_text_carries),
    ("every document is reachable from an entry point", COMPUTED,
     check_every_document_is_reachable),
    ("every link resolves", COMPUTED, check_every_link_resolves),
    ("no forbidden name appears", FORBIDDING, check_no_forbidden_name_appears),
    ("a table keeps its shape", COMPUTED, check_a_table_keeps_its_shape),
    ("a table row keeps its table", COMPUTED, check_a_table_row_keeps_its_table),
    ("no document leaves a fence open", COMPUTED, check_no_document_leaves_a_fence_open),
    ("a box diagram keeps its edges", COMPUTED, check_a_box_diagram_keeps_its_edges),
    ("a quoted sentence is still in its document", QUOTING,
     check_a_quoted_sentence_is_still_in_its_document),
]


def run(subject: Subject) -> dict:
    return {name: check(subject) for name, _kind, check in CHECKS}


def warnings(subject: Subject) -> list:
    """What the quoting kind obliges, said on every run rather than at the load.

    ⛔ **Both failure modes, in both directions**, because the one that matters is
    invisible: a project told only that quoting is fragile hears *this may go red
    on a reword* and not *this stays green when the claim is reversed*.
    """
    said = []
    # ⛔ The rows this project declines to enforce, counted on every run. Where
    # that is all of them, the three graph checks hold nothing and this is the
    # only place that says so -- a project reading their green as its documents
    # agreeing is the one misread the third state invites.
    unenforced = subject.unenforced
    if unenforced and not subject.enforced:
        said.append(
            f"every one of the {len(unenforced)} governed document(s) states "
            "`may_name: null`, so no edge is enforced: the two edge checks and the "
            "reachability check HOLD NOTHING and their green says nothing about whether "
            "these documents agree. ⛔ What is still held is the governed set, every "
            "link's target, the forbidden names and each document's own blocks."
        )
    elif unenforced:
        said.append(
            f"{len(unenforced)} of {len(subject.set_now)} governed document(s) state "
            "`may_name: null`, so the enforced edge is not held for them: "
            + ", ".join(sorted(unenforced)[:6])
            + (f" and {len(unenforced) - 6} more" if len(unenforced) > 6 else "")
            + ". ⚠️ `null` is not `[]` -- these documents may name anything."
        )
    if not subject.quoted:
        return said
    return said + [
        f"documents.quoted[{index}] quotes {str(entry.get('sentence'))[:50]!r} at "
        f"{entry.get('document')!r}. ⛔ This is the kind that does not work (§ 38): it "
        "goes RED on an innocent reword of a claim that is still true, and it stays "
        "GREEN when the sentence is reworded into its opposite. Its green says nothing "
        "about the claim. Derive the property instead, or forbid a stable name."
        for index, entry in enumerate(subject.quoted)
    ]


def hold(subject: Subject) -> int:
    """Run every check over one subject, print the verdict, and return the status.

    ⛔ One function for both callers -- the toolkit's own `main` below the
    sentinel and the vendored copy's `vendored_main` above it -- so the two
    cannot print different verdicts over the same tree.
    """
    results = run(subject)
    for name, kind, _check in CHECKS:
        found = results[name]
        print(f"  {'FAIL' if found else 'ok  '}  [{kind:<10}] {name}")
    said = warnings(subject)
    if said:
        print()
        for warning in said:
            print(f"  warn  {warning}")
    problems = [problem for found in results.values() for problem in found]
    if problems:
        print(f"\n{len(problems)} problem(s):\n")
        for problem in problems:
            print(f"  - {problem}")
        print(
            "\n⚠️ When one of these goes red, the assertion is as likely to be wrong as "
            "the document (§ 38). Read the row and the text against each other before "
            "editing either."
        )
        return 1
    # ⛔ The summary names what was **held** and nothing more. ⚠️ Measured on
    # this file's own first form: it said every document names what its row
    # allows and is reached from an entry point, which is false of a project
    # whose rows state `may_name: null` -- the three graph checks held nothing
    # there, and the sentence asserted they had passed.
    held = [
        f"all {len(subject.set_now)} governed document(s) have a row",
        "every relative link reaches a file and a heading the index holds"
        + (f" or {len(subject.exempt)} exempt glob(s) cover" if subject.exempt else ""),
        "no forbidden name appears",
        "and every one keeps its own blocks"
        + (
            ", its box diagrams' edges included" if subject.diagrams_held
            else " -- no box diagram is held, `documents.box_diagrams` "
            + ("stating `held: false`" if subject.box_diagrams else "being unstated")
        ),
    ]
    if subject.enforced:
        held.insert(1, (
            f"{len(subject.enforced)} of them name only what their row allows and all "
            "of it, and are reached from an entry point"
        ))
    print("\n" + "; ".join(held) + ".")
    return 0


def vendored_main(argv: list) -> int:
    """The rendered copy's entry point: the facet rendered in, the checkout read.

    ⛔ **It reads no configuration and imports nothing of the toolkit's**, which
    is the whole of what makes it runnable on a host: the checkout holds this
    file and the documents, and nothing else is assumed to be there.
    """
    parser = argparse.ArgumentParser(
        description="Hold this repository's documents to the facet rendered into this copy.",
    )
    # ⛔ Strict: an argument this copy does not take is refused rather than
    # ignored, so a flag meant for the toolkit's copy is never read as a run.
    parser.parse_args(argv)
    if not STATED:
        # ⛔ Not a verdict, and not green: a copy holding no facet holds nothing,
        # which the install step never writes -- so meeting one is a copy taken
        # by hand, and saying so is the answer.
        print(
            "This copy holds no facet, so there is nothing to hold a document to. The "
            "facet is the project's own and is rendered in by the install step.",
            file=sys.stderr,
        )
        return 2
    repository = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    root = os.path.normpath(os.path.join(repository, STATED["root"]))
    return hold(read_subject(root, STATED["facet"]))


# ---- the vendored half ends here ------------------------------------------
#
# ⛔ The line above is the sentinel `render` splits on, and everything below it
# is the toolkit's own entry point, the renderer and the suite. Nothing below
# states a rule about a document: a rule down here would be one the host's own
# run of the rendered copy never executes.

import tempfile  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as reader  # noqa: E402  -- the one reader, never a second parser

RENDER_SENTINEL = "# ---- the vendored half ends here "

# What the rendered copy ends with, in place of everything below the sentinel.
# ⛔ Nothing in it moves between runs, which is the install step's own
# byte-identical property reaching an artifact whose body is generated.
RENDER_TAIL = 'if __name__ == "__main__":\n    sys.exit(vendored_main(sys.argv[1:]))\n'

# The line the facet is rendered over. ⛔ Matched whole, so a render is a
# substitution of one line and never a search through the source.
PLACEHOLDER = "STATED = None"


def render(stated) -> str:
    """This file's vendored half, with one project's facet rendered in.

    ⛔ The half above the sentinel and not the whole file: the suite below plants
    documents and names of its own, and a whole-file copy would carry every one
    of them into an adopting repository.
    """
    with open(os.path.abspath(__file__), encoding="utf-8") as handle:
        source = handle.read()
    head = source.split(RENDER_SENTINEL)[0]
    if head.count(PLACEHOLDER) != 1:
        raise ValueError(
            f"the vendored half states {head.count(PLACEHOLDER)} {PLACEHOLDER!r} lines "
            "where a render needs exactly one to substitute"
        )
    return head.replace(PLACEHOLDER, rendered_stated(stated), 1) + RENDER_TAIL


def rendered_stated(stated) -> str:
    """The `STATED` line one project's facet renders to, as a Python literal.

    ⛔ Read back before it is returned: a value the literal does not reproduce
    exactly would be a gate holding a different facet from the one the project
    states, with nothing reporting the difference.
    """
    import ast
    import pprint
    text = "STATED = " + pprint.pformat(stated, width=88, sort_dicts=False)
    if ast.literal_eval(text[len("STATED = "):]) != stated:
        raise ValueError("the facet does not survive as a Python literal")
    return text


def from_config(configuration) -> dict | None:
    """What a rendered copy holds for this project, or None where it cannot be held.

    ⛔ `None` where the documents are read from outside the repository the copy
    sits in: a checkout holds that repository and nothing above it, so a gate
    rendered for such a root would read a tree the host never has.
    """
    facet = configuration.get(FACET)
    relative = os.path.relpath(
        os.path.abspath(configuration.skills_root), os.path.abspath(configuration.code_root)
    )
    if relative == os.pardir or relative.startswith(os.pardir + os.sep):
        return None
    return {"root": relative.replace(os.sep, "/"), "facet": _plain(facet)}


def _plain(value):
    """The facet as the plain types a Python literal carries."""
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    return value


# --- the planted violations -------------------------------------------------
#
# ⛔ One per branch that does real work. A branch with no plant is a branch
# nothing asserts can fail. ⚠️ No plant names a file of any project: each takes
# whatever the fixture holds, so a rename cannot turn `--self-test` -- the
# command a workflow runs -- into a traceback instead of a verdict.


def _a_subject() -> Subject:
    """A project whose documents are governed, held and green.

    Two documents and one carrier: the carrier is the entry point nothing names,
    which is the arm a single-root reading of reachability gets wrong.
    """
    facet = {
        "carrier": LIST,
        "files": ["*.md", "docs/**/*.md", "carriers/*/CARRIER.md"],
        "entry_points": ["README.md", "carriers/*/CARRIER.md"],
        "graph": [
            {"document": "README.md", "may_name": ["docs/a-document.md"],
             "derived_from": []},
            {"document": "docs/a-document.md", "may_name": [], "derived_from": []},
            {"document": "carriers/a-role/CARRIER.md", "may_name": [],
             "derived_from": ["docs/a-document.md"]},
        ],
        "forbidden": [
            {"pattern": "ARetiredName", "reason": "the component was deleted",
             "stable_because": "the name was removed rather than renamed"},
        ],
        "quoted": [],
    }
    text = {
        "README.md": (
            "# A project\n\nThe shape of it is in [the document](docs/a-document.md).\n\n"
            "| what | where |\n|---|---|\n| the shape | the document |\n"
        ),
        "docs/a-document.md": "# The document\n\nIt names nothing.\n",
        "carriers/a-role/CARRIER.md": (
            "---\nname: a-role\n---\n\n# A role\n\nAddressed by name, named by nobody.\n"
        ),
    }
    tracked = sorted(list(text) + ["src/a-module.src", "notes.txt"])
    return Subject("/a-project", facet, tracked, text)


def _plant_a_governed_document_with_no_row(subject: Subject) -> Subject:
    subject.tracked.append("docs/undeclared.md")
    subject.text["docs/undeclared.md"] = "# Undeclared\n\nA second authority.\n"
    return subject


def _plant_a_row_whose_document_is_gone(subject: Subject) -> Subject:
    subject.rows["docs/moved-away.md"] = {"may_name": [], "derived_from": []}
    return subject


def _plant_a_governed_document_that_cannot_be_read(subject: Subject) -> Subject:
    subject.tracked.append("docs/deleted-without-git-rm.md")
    subject.rows["docs/deleted-without-git-rm.md"] = {"may_name": [], "derived_from": []}
    subject.text["docs/deleted-without-git-rm.md"] = FileNotFoundError("no such file")
    return subject


def _plant_nothing_governed(subject: Subject) -> Subject:
    subject.files = ["*.absent"]
    return subject


def _plant_an_edge_the_row_does_not_allow(subject: Subject) -> Subject:
    """A filename in a document whose row is empty, which is the check with teeth."""
    subject.text["docs/a-document.md"] += "\nSee README.md for the rest.\n"
    return subject


def _plant_an_edge_the_text_dropped(subject: Subject) -> Subject:
    subject.rows["README.md"]["may_name"] = [
        "docs/a-document.md", "carriers/a-role/CARRIER.md",
    ]
    return subject


def _plant_a_graph_that_enforces_nothing(subject: Subject) -> Subject:
    """Every row's enforced edge left unstated, which is a check holding nothing.

    ⛔ Red rather than green, and that is the arm the two-state reading could
    not have: one of the two surveyed projects governs a document set and
    declares no reference graph, so this is a configuration it reaches rather
    than a mistake.
    """
    for row in subject.rows.values():
        row["may_name"] = None
    return subject


def _plant_a_document_nothing_reaches(subject: Subject) -> Subject:
    subject.tracked.append("docs/orphan.md")
    subject.rows["docs/orphan.md"] = {"may_name": [], "derived_from": []}
    subject.text["docs/orphan.md"] = "# Orphan\n\nNothing names this.\n"
    return subject


def _plant_no_entry_point_matching_anything(subject: Subject) -> Subject:
    subject.entry_points = ["START-HERE.md"]
    return subject


def _plant_a_link_to_a_missing_file(subject: Subject) -> Subject:
    subject.text["README.md"] += "\nThe plan is in [the plan](docs/gone.md).\n"
    return subject


def _plant_a_root_relative_link_to_a_missing_file(subject: Subject) -> Subject:
    """A leading `/` is the repository's root, not the document's directory."""
    subject.text["docs/a-document.md"] += "\nSee [the plan](/docs/gone.md).\n"
    return subject


def _plant_a_titled_link_to_a_missing_file(subject: Subject) -> Subject:
    subject.text["README.md"] += '\nSee [the plan](docs/gone.md "the plan").\n'
    return subject


def _plant_a_definition_of_a_missing_file(subject: Subject) -> Subject:
    subject.text["README.md"] += "\nSee [the plan][plan].\n\n[plan]: docs/gone.md\n"
    return subject


def _plant_a_link_out_of_the_repository(subject: Subject) -> Subject:
    subject.text["README.md"] += "\nSee [a sibling](../a-sibling/README.md).\n"
    return subject


def _plant_a_missing_fragment(subject: Subject) -> Subject:
    subject.text["README.md"] += (
        "\nSee [a section](docs/a-document.md#a-section-that-was-renamed).\n"
    )
    return subject


def _plant_a_missing_fragment_within_the_document(subject: Subject) -> Subject:
    subject.text["README.md"] += "\nSee [below](#a-section-nowhere).\n"
    return subject


def _plant_a_second_heading_nobody_wrote(subject: Subject) -> Subject:
    """A repeat's suffix where there is no repeat: one `The document`, so no `-1`."""
    subject.text["README.md"] += "\nSee [it](docs/a-document.md#the-document-1).\n"
    return subject


def _plant_a_fragment_on_a_target_that_cannot_be_read(subject: Subject) -> Subject:
    """A markdown target outside the globs, indexed and unreadable here."""
    subject.tracked.append("vendor/notes.md")
    subject.text["README.md"] += "\nSee [the notes](vendor/notes.md#a-heading).\n"
    return subject


def _plant_a_fragment_naming_frontmatter(subject: Subject) -> Subject:
    """A frontmatter field above its closing `---` is no setext heading."""
    subject.text["README.md"] += (
        "\nThe [role](carriers/a-role/CARRIER.md#name-a-role).\n"
    )
    return subject


def _plant_a_forbidden_name(subject: Subject) -> Subject:
    subject.text["docs/a-document.md"] += "\nThe ARetiredName module does this.\n"
    return subject


def _plant_a_forbidden_pattern_that_cannot_compile(subject: Subject) -> Subject:
    subject.forbidden = [
        {"pattern": "A(Retired", "reason": "a typo in the pattern",
         "stable_because": "nothing, which is the point"},
    ]
    return subject


def _plant_a_ragged_table(subject: Subject) -> Subject:
    subject.text["README.md"] += "\n| a | b |\n|---|---|\n| one |\n"
    return subject


def _plant_a_row_cut_off_from_its_table(subject: Subject) -> Subject:
    """The measured case: a row appended after the blank line that ends a table."""
    subject.text["README.md"] += "\n| a late row | with no table above it |\n"
    return subject


def _plant_an_unclosed_fence(subject: Subject) -> Subject:
    subject.text["docs/a-document.md"] += "\n```yaml\nkey: value\n"
    return subject


def _plant_a_quoted_sentence_that_is_gone(subject: Subject) -> Subject:
    subject.quoted = [
        {"sentence": "a claim this document no longer makes",
         "document": "docs/a-document.md"},
    ]
    return subject


def _plant_a_quoted_sentence_reworded_away(subject: Subject) -> Subject:
    """The kind's own red: the document says something else now.

    ⚠️ Apart from the plant above, which deletes the sentence outright: this one
    leaves a sentence in place and changes what it claims, which is the shape a
    project writing a quoted check is actually afraid of.
    """
    subject.quoted = [
        {"sentence": "It names nothing", "document": "docs/a-document.md"},
    ]
    subject.text["docs/a-document.md"] = subject.text["docs/a-document.md"].replace(
        "It names nothing.", "It names everything."
    )
    return subject


def _drop_a_row(subject: Subject) -> Subject:
    """One document's row removed while the rest keep theirs.

    ⛔ The arm that tells *no row* apart from `may_name: null`: with the two
    collapsed, this planted state was reported as a document the project had
    decided not to enforce, and a tree where **no** document had a row was
    reported as one where every row states `null`.
    """
    del subject.rows["docs/a-document.md"]
    return subject


def _plant_a_quoted_document_that_cannot_be_read(subject: Subject) -> Subject:
    subject.quoted = [
        {"sentence": "a claim", "document": "docs/deleted-without-git-rm.md"},
    ]
    return subject


def _diagram(subject: Subject, body: str, held=True, exempt=None) -> Subject:
    """The fixture with one fenced diagram appended and the check stated as asked.

    ⛔ `held=None` leaves the block unstated, which is the configuration every
    project written before this key is in.
    """
    subject.box_diagrams = (
        None if held is None else {"held": held, "exempt": list(exempt or ())}
    )
    subject.text["docs/a-document.md"] += "\n```text\n" + body + "\n```\n"
    return subject


A_BOX_ONE_COLUMN_OFF = "┌────┐\n│ ab  │\n└────┘"


def _plant_a_box_edge_one_column_off(subject: Subject) -> Subject:
    """The defect itself: a right edge one column past the corners above and below."""
    return _diagram(subject, A_BOX_ONE_COLUMN_OFF)


def _plant_a_run_that_stops_short_of_its_corner(subject: Subject) -> Subject:
    """The horizontal arm: a run ending a column before the corner it was drawn to."""
    return _diagram(subject, "┌─── ┐\n│    │\n└────┘")


def _plant_a_box_drawn_by_code_point_count(subject: Subject) -> Subject:
    """A box whose rows agree by code points and not on screen.

    ⛔ **Reddens only by display width**: every row is six code points, so a
    count by code point puts the right edge under the corner and reports green.
    On screen the two wide characters push it two columns out.
    """
    return _diagram(subject, "┌────┐\n│漢字  │\n└────┘")


def _plant_a_corner_on_half_a_wide_character(subject: Subject) -> Subject:
    """A corner's arm landing on the second column of a wide character.

    ⛔ Apart from the space case: the narrower box drawn by code points puts its
    corner over half of `字`, which is not text a line was drawn to.
    """
    return _diagram(subject, "┌──┐\n│漢字│\n└──┘")


def _plant_a_double_box_one_column_short(subject: Subject) -> Subject:
    """A double-line box, read by the same name rule as a light one."""
    return _diagram(subject, "╔═══╗\n║   ║\n╚══╝")


def _plant_a_tee_whose_arm_runs_off_the_block(subject: Subject) -> Subject:
    """A tee on a block's last line, its arm reaching past the fence."""
    return _diagram(subject, "──┬──")


def _plant_a_junction_meeting_a_line_that_does_not_reach_back(subject: Subject) -> Subject:
    """A corner over a horizontal run, which carries no arm up to it."""
    return _diagram(subject, "┌──\n───")


def _plant_an_exemption_matching_no_block(subject: Subject) -> Subject:
    return _diagram(subject, "┌──┐\n│  │\n└──┘", exempt=[
        {"document": "docs/a-document.md", "block": "a block nobody drew",
         "reason": "it was drawn once"},
    ])


def _plant_an_exemption_that_cannot_compile(subject: Subject) -> Subject:
    return _diagram(subject, "┌──┐\n│  │\n└──┘", exempt=[
        {"document": "docs/a-document.md", "block": "(ab", "reason": "a typo"},
    ])


def _plant_an_exemption_naming_another_document(subject: Subject) -> Subject:
    """An exemption whose expression matches, written against the wrong document."""
    return _diagram(subject, A_BOX_ONE_COLUMN_OFF, exempt=[
        {"document": "README.md", "block": "ab", "reason": "drawn this way on purpose"},
    ])


VIOLATIONS = [
    ("every governed document has a row", "a governed document no row declares",
     _plant_a_governed_document_with_no_row),
    ("every governed document has a row", "a row whose document is not there",
     _plant_a_row_whose_document_is_gone),
    ("every governed document has a row", "a governed document that cannot be read",
     _plant_a_governed_document_that_cannot_be_read),
    ("every governed document has a row", "globs that govern no tracked file",
     _plant_nothing_governed),
    ("a document names only what its row allows", "a filename in a document that may name none",
     _plant_an_edge_the_row_does_not_allow),
    ("a row names only edges the text carries", "a row stating an edge the text dropped",
     _plant_an_edge_the_text_dropped),
    ("every document is reachable from an entry point", "a document nothing names",
     _plant_a_document_nothing_reaches),
    ("every document is reachable from an entry point", "entry points matching no document",
     _plant_no_entry_point_matching_anything),
    ("every link resolves", "a relative link to a file the index does not hold",
     _plant_a_link_to_a_missing_file),
    ("every link resolves", "a root-relative link to a file the index does not hold",
     _plant_a_root_relative_link_to_a_missing_file),
    ("every link resolves", "a titled link to a missing file",
     _plant_a_titled_link_to_a_missing_file),
    ("every link resolves", "a reference definition of a missing file",
     _plant_a_definition_of_a_missing_file),
    ("every link resolves", "a relative link climbing out of the repository",
     _plant_a_link_out_of_the_repository),
    ("every link resolves", "a fragment no heading of the target carries",
     _plant_a_missing_fragment),
    ("every link resolves", "a fragment within the document that nothing carries",
     _plant_a_missing_fragment_within_the_document),
    ("every link resolves", "a repeat's suffix on a heading that is not repeated",
     _plant_a_second_heading_nobody_wrote),
    ("every link resolves", "a fragment on a markdown target that cannot be read",
     _plant_a_fragment_on_a_target_that_cannot_be_read),
    ("every link resolves", "a fragment naming a frontmatter field",
     _plant_a_fragment_naming_frontmatter),
    ("no forbidden name appears", "a forbidden name in a governed document",
     _plant_a_forbidden_name),
    ("no forbidden name appears", "a forbidden pattern that cannot be evaluated",
     _plant_a_forbidden_pattern_that_cannot_compile),
    ("a table keeps its shape", "a table row short of a cell", _plant_a_ragged_table),
    ("a table row keeps its table", "a row separated from its table by a blank line",
     _plant_a_row_cut_off_from_its_table),
    ("no document leaves a fence open", "a fence that never closes",
     _plant_an_unclosed_fence),
    ("a quoted sentence is still in its document", "a sentence the document no longer carries",
     _plant_a_quoted_sentence_that_is_gone),
    ("a quoted sentence is still in its document", "a quoted document that cannot be read",
     _plant_a_quoted_document_that_cannot_be_read),
    ("a quoted sentence is still in its document", "a sentence reworded into something else",
     _plant_a_quoted_sentence_reworded_away),
    ("every governed document has a row",
     "one document's row gone while its siblings keep theirs", _drop_a_row),
    ("a box diagram keeps its edges", "a box edge one column off its corners",
     _plant_a_box_edge_one_column_off),
    ("a box diagram keeps its edges", "a run stopping short of its corner",
     _plant_a_run_that_stops_short_of_its_corner),
    ("a box diagram keeps its edges", "a box aligned by code points and not on screen",
     _plant_a_box_drawn_by_code_point_count),
    ("a box diagram keeps its edges", "a corner over half of a wide character",
     _plant_a_corner_on_half_a_wide_character),
    ("a box diagram keeps its edges", "a double-line box one column short",
     _plant_a_double_box_one_column_short),
    ("a box diagram keeps its edges", "a tee whose arm runs off the block",
     _plant_a_tee_whose_arm_runs_off_the_block),
    ("a box diagram keeps its edges", "a corner over a line that does not reach back",
     _plant_a_junction_meeting_a_line_that_does_not_reach_back),
    ("a box diagram keeps its edges", "an exemption matching no block",
     _plant_an_exemption_matching_no_block),
    ("a box diagram keeps its edges", "an exemption that cannot be evaluated",
     _plant_an_exemption_that_cannot_compile),
    ("a box diagram keeps its edges", "an exemption written against another document",
     _plant_an_exemption_naming_another_document),
]


# --- the planted exemptions -------------------------------------------------
#
# The green side of the scope, which is the half a problem count cannot show.
# ⛔ Each was verified by disabling the clause that admits it and watching the
# plant redden: an exemption nothing can fail is an exemption nobody checked.


def _plant_an_ungoverned_path_named(subject: Subject) -> Subject:
    """A link to a file the globs do not govern is not an edge.

    ⛔ **A link and not a bare path in backticks**, which is what the first form
    of this plant used: the bare form is reached only by the loop over known
    documents, so no mutation of the edge reader could have reddened it and the
    exemption asserted nothing. A link target is resolved first and then tested
    against the governed set, so this plant is decided by that test.
    """
    subject.text["docs/a-document.md"] += (
        "\nThe code is in [a module](../src/a-module.src).\n"
    )
    return subject


def _plant_a_carrier_nothing_names(subject: Subject) -> Subject:
    """An entry point needs no document to name it -- the single-root arm."""
    subject.text["carriers/a-role/CARRIER.md"] += "\nStill named by nobody.\n"
    return subject


def _plant_a_fenced_table_of_pipes(subject: Subject) -> Subject:
    """A table shown inside a fence is an example, not this document's own block."""
    subject.text["docs/a-document.md"] += "\n```\n| a | b |\n| one |\n```\n"
    return subject


def _plant_a_tilde_fence_that_closes(subject: Subject) -> Subject:
    """The other fence character, which is its own branch of the delimiter.

    ⛔ **The block carries a ragged table**, for the nested plant's measured
    reason: a tilde block with inert prose in it stays green whether the
    delimiter is recognised or not.
    """
    subject.text["docs/a-document.md"] += "\n~~~\n| a | b |\n| one |\n~~~\n"
    return subject


def _plant_a_nested_fence_delimiter(subject: Subject) -> Subject:
    """A delimiter of the other character inside a fence is content, not a close.

    ⛔ **The nested block carries a ragged table, and that is what makes this a
    plant at all.** ⚠️ Measured: the first form of it held only the two
    delimiters, so with the matching rule disabled the outer fence closed early,
    the inner one opened and closed, nothing was left unclosed and no line was
    read as prose -- the plant stayed green under both implementations and
    certified nothing.
    """
    subject.text["docs/a-document.md"] += (
        "\n~~~\n```\n| a | b |\n| one |\n```\n~~~\n"
    )
    return subject


def _plant_a_forbidden_name_outside_the_governed_set(subject: Subject) -> Subject:
    """The forbidding kind is over the governed set and not over the tree."""
    subject.tracked.append("src/legacy.src")
    subject.text["src/legacy.src"] = "ARetiredName\n"
    return subject


def _plant_a_row_that_does_not_enforce_its_edge(subject: Subject) -> Subject:
    """A document this project declines to enforce the edge of, naming another.

    ⛔ The green side of the third state: `null` is not `[]`, so the strictest
    rule in the facet must stay off for this row while the rows beside it keep
    it on.
    """
    subject.rows["docs/a-document.md"]["may_name"] = None
    subject.text["docs/a-document.md"] += "\nSee README.md for the rest.\n"
    return subject


def _plant_a_document_named_by_a_spelling_of_its_own(subject: Subject) -> Subject:
    """A row whose `named_as` is what the text uses, and whose path it never writes."""
    subject.rows["README.md"]["may_name"] = ["docs/a-document.md"]
    subject.rows["docs/a-document.md"]["named_as"] = r"the shape document"
    subject.text["README.md"] = (
        "# A project\n\nThe shape of it is in the shape document.\n\n"
        "| what | where |\n|---|---|\n| the shape | the document |\n"
    )
    return subject


def _plant_a_table_of_one_row(subject: Subject) -> Subject:
    """The smallest legitimate table: one row and its delimiter, both intact.

    ⚠️ **What decides this plant is the delimiter count agreeing**, not the
    run-length guard in the shape check -- measured by widening that guard and
    watching this stay green. The guard's own subject is a *lone* line of pipes,
    whose red belongs to the block check and is planted there.
    """
    subject.text["docs/a-document.md"] += "\n| only |\n|---|\n"
    return subject


def _plant_a_cell_carrying_an_escaped_pipe(subject: Subject) -> Subject:
    """An escaped pipe is one character of a cell, not a delimiter.

    ⚠️ The arm this project's own decision record is in: with the raw character
    counted, that row was reported as ragged and renders correctly.
    """
    subject.text["docs/a-document.md"] += (
        "\n| what | which |\n|---|---|\n| a value | `high \\| medium \\| low` |\n"
    )
    return subject


def _plant_a_row_with_no_closing_delimiter(subject: Subject) -> Subject:
    """The closing pipe is optional, and two rows written each way are one shape.

    ⚠️ Measured: with the raw delimiter count compared, a table whose last row
    omits the closing pipe was reported ragged against the rows above it, and a
    renderer reads the two forms identically.
    """
    subject.text["docs/a-document.md"] += "\n| a | b |\n|---|---|\n| one | two\n"
    return subject


def _plant_a_quoted_sentence_the_document_wraps(subject: Subject) -> Subject:
    """A sentence that is in the document and spans a line break.

    ⛔ The arm this kind would otherwise fail on every wrapped project: a raw
    substring test reports a sentence that is there as gone, which reads as the
    claim having been reworded away.
    """
    subject.text["docs/a-document.md"] += (
        "\nIt states that the claim this document\nstill makes, and nothing else.\n"
    )
    subject.quoted = [
        {"sentence": "the claim this document still makes",
         "document": "docs/a-document.md"},
    ]
    return subject


def _plant_a_cell_after_a_literal_backslash(subject: Subject) -> Subject:
    """A doubled backslash is a literal, so the pipe straight after it is a delimiter.

    ⚠️ The delimiter has to follow the escape **immediately** for this to assert
    anything: with a character between them, a look-back implementation and a
    consuming one agree, and the plant was measured passing under both.
    """
    subject.text["docs/a-document.md"] += (
        "\n| what | which |\n|---|---|\n| a path C:\\\\| a second cell |\n"
    )
    return subject


def _plant_a_fragment_the_target_carries(subject: Subject) -> Subject:
    subject.text["README.md"] += (
        "\nSee [the document](docs/a-document.md#the-document) and [this](#a-project).\n"
    )
    return subject


def _plant_a_heading_slugged_the_hosts_way(subject: Subject) -> Subject:
    """A code span, a dash between spaces and a link, each of which the slug changes.

    ⚠️ The dash is the arm a collapsing slug gets wrong -- two hyphens, not one.
    """
    subject.text["docs/a-document.md"] += (
        "\n## `key` — a rule\n\n## See [a module](../src/a-module.src)\n"
    )
    subject.text["README.md"] += (
        "\n[one](docs/a-document.md#key--a-rule) and "
        "[two](docs/a-document.md#see-a-module).\n"
    )
    return subject


def _plant_a_repeated_heading_named_by_its_suffix(subject: Subject) -> Subject:
    subject.text["docs/a-document.md"] += "\n## Twice\n\nOnce.\n\n## Twice\n\nAgain.\n"
    subject.text["README.md"] += "\nThe [second](docs/a-document.md#twice-1).\n"
    return subject


def _plant_an_anchor_written_by_hand(subject: Subject) -> Subject:
    subject.text["docs/a-document.md"] += '\n<a id="a-place"></a>\n\nA place.\n'
    subject.text["README.md"] += "\nThe [place](docs/a-document.md#a-place).\n"
    return subject


def _plant_a_link_to_a_directory(subject: Subject) -> Subject:
    """A directory above a tracked file, and the repository's own root."""
    subject.text["README.md"] += (
        "\nThe [role](carriers/a-role/) is loaded by name, from [the root](./).\n"
    )
    return subject


def _plant_a_root_relative_link_that_resolves(subject: Subject) -> Subject:
    """From a nested document, `/` is the root and not the document's directory."""
    subject.text["docs/a-document.md"] += "\nThe code is in [it](/src/a-module.src).\n"
    return subject


def _plant_links_outside_the_repository(subject: Subject) -> Subject:
    """Two schemes and a scheme-relative address: none is fetched."""
    subject.text["README.md"] += (
        "\n[a](https://example.invalid/gone.md), [b](ftp://example.invalid/gone.md) "
        "and [c](//example.invalid/gone.md).\n"
    )
    return subject


def _plant_fragments_no_heading_answers(subject: Subject) -> Subject:
    """A line range, and a fragment on a file that is not markdown."""
    subject.text["README.md"] += (
        "\n[a](README.md#L3-L5) and [b](src/a-module.src#a-symbol).\n"
    )
    return subject


def _plant_an_exempt_target(subject: Subject) -> Subject:
    subject.exempt = ["build/**"]
    subject.text["README.md"] += "\nThe [report](build/report/index.md) is generated.\n"
    return subject


def _plant_an_angled_destination_with_a_space(subject: Subject) -> Subject:
    """Angle brackets are what let a destination carry a space.

    ⚠️ A plant pointing angle brackets at a missing file certifies nothing: the
    bare form reads `<docs/the` off it and reports that missing instead.
    """
    subject.tracked.append("assets/a picture.png")
    subject.text["README.md"] += "\n![a picture](<assets/a picture.png>)\n"
    return subject


def _plant_a_destination_with_parentheses(subject: Subject) -> Subject:
    subject.tracked.append("assets/a_(b).png")
    subject.text["README.md"] += "\n![a picture](assets/a_(b).png)\n"
    return subject


def _plant_a_setext_heading(subject: Subject) -> Subject:
    """The underlined form of a heading, which the host anchors like a `#` one."""
    subject.text["docs/a-document.md"] += "\nAn underlined heading\n---------------------\n"
    subject.text["README.md"] += (
        "\nThe [heading](docs/a-document.md#an-underlined-heading).\n"
    )
    return subject


def _plant_a_link_to_an_exempt_directory(subject: Subject) -> Subject:
    subject.exempt = ["site/**"]
    subject.text["README.md"] += "\nThe [site](site/) is generated.\n"
    return subject


def _plant_an_encoded_path(subject: Subject) -> Subject:
    subject.tracked.append("assets/a picture.png")
    subject.text["README.md"] += "\n![a picture](assets/a%20picture.png)\n"
    return subject


def _plant_links_that_are_shown_rather_than_followed(subject: Subject) -> Subject:
    """A fence, a code span, a comment and a footnote: none is a destination."""
    subject.text["README.md"] += (
        "\n```\n[x](docs/gone.md)\n```\n\nWrite `[x](docs/gone.md)` for a link.\n\n"
        "<!-- [x](docs/gone.md) -->\n\nA claim.[^1]\n\n[^1]: docs/gone.md was retired.\n"
    )
    return subject


def _plant_a_box_aligned_by_display_width(subject: Subject) -> Subject:
    """Two wide characters in a box four columns wide, which is aligned on screen."""
    return _diagram(subject, "┌────┐\n│漢字│\n└────┘")


def _plant_a_box_carrying_a_combining_mark(subject: Subject) -> Subject:
    """A combining mark takes no column, so the edge after it is where it looks."""
    return _diagram(subject, "┌──┐\n│e\u0301 │\n└──┘")


def _plant_a_box_carrying_a_tab(subject: Subject) -> Subject:
    """A tab advances to the next multiple of eight, as a terminal draws it."""
    return _diagram(subject, "┌───────┐\n│\t│\n└───────┘")


def _plant_a_tree_listing(subject: Subject) -> Subject:
    """`tree`'s own shape: a nested `└` under its parent's first letter, runs ending in space."""
    return _diagram(subject, ".\n├── a\n│   └── b\n└── c")


def _plant_a_box_character_in_running_prose(subject: Subject) -> Subject:
    """A corner written in a sentence is not a diagram."""
    subject.box_diagrams = {"held": True, "exempt": []}
    subject.text["docs/a-document.md"] += "\nA corner ┌ written in a sentence.\n"
    return subject


def _plant_an_exempted_misaligned_block(subject: Subject) -> Subject:
    return _diagram(subject, A_BOX_ONE_COLUMN_OFF, exempt=[
        {"document": "docs/a-document.md", "block": "│ ab",
         "reason": "drawn this way on purpose"},
    ])


def _plant_a_misaligned_box_where_the_check_is_off(subject: Subject) -> Subject:
    return _diagram(subject, A_BOX_ONE_COLUMN_OFF, held=False)


def _plant_a_misaligned_box_where_nothing_is_stated(subject: Subject) -> Subject:
    """A project written before this key, which behaves as it did."""
    return _diagram(subject, A_BOX_ONE_COLUMN_OFF, held=None)


EXEMPTIONS = [
    ("a path that is not a governed document", _plant_an_ungoverned_path_named),
    ("a fragment the target carries, in another document and in this one",
     _plant_a_fragment_the_target_carries),
    ("a heading slugged the host's way", _plant_a_heading_slugged_the_hosts_way),
    ("a repeated heading named by its suffix",
     _plant_a_repeated_heading_named_by_its_suffix),
    ("an anchor written by hand", _plant_an_anchor_written_by_hand),
    ("a link to a directory the index holds, and to the root",
     _plant_a_link_to_a_directory),
    ("a root-relative link from a nested document",
     _plant_a_root_relative_link_that_resolves),
    ("links outside the repository, which are not fetched",
     _plant_links_outside_the_repository),
    ("a line range, and a fragment on a file that is not markdown",
     _plant_fragments_no_heading_answers),
    ("a target the project exempts", _plant_an_exempt_target),
    ("a percent-encoded path", _plant_an_encoded_path),
    ("an angle-bracketed destination carrying a space",
     _plant_an_angled_destination_with_a_space),
    ("a destination carrying balanced parentheses",
     _plant_a_destination_with_parentheses),
    ("a setext heading", _plant_a_setext_heading),
    ("a link to an exempt directory itself", _plant_a_link_to_an_exempt_directory),
    ("links shown rather than followed",
     _plant_links_that_are_shown_rather_than_followed),
    ("a carrier that no document names", _plant_a_carrier_nothing_names),
    ("a table shown inside a fence", _plant_a_fenced_table_of_pipes),
    ("a tilde fence that closes", _plant_a_tilde_fence_that_closes),
    ("a fence delimiter shown inside another fence", _plant_a_nested_fence_delimiter),
    ("a forbidden name in a file the globs do not govern",
     _plant_a_forbidden_name_outside_the_governed_set),
    ("a table carrying one row and its delimiter", _plant_a_table_of_one_row),
    ("a row whose enforced edge this project does not state",
     _plant_a_row_that_does_not_enforce_its_edge),
    ("a graph that enforces no edge at all, which is warned about and not refused",
     _plant_a_graph_that_enforces_nothing),
    ("a document named by a spelling of its own rather than by its path",
     _plant_a_document_named_by_a_spelling_of_its_own),
    ("a row that omits the optional closing delimiter",
     _plant_a_row_with_no_closing_delimiter),
    ("a quoted sentence the document wraps across a line break",
     _plant_a_quoted_sentence_the_document_wraps),
    ("a cell carrying an escaped pipe", _plant_a_cell_carrying_an_escaped_pipe),
    ("a cell whose delimiter follows a literal backslash",
     _plant_a_cell_after_a_literal_backslash),
    ("a box aligned by display width around wide characters",
     _plant_a_box_aligned_by_display_width),
    ("a box carrying a combining mark", _plant_a_box_carrying_a_combining_mark),
    ("a box carrying a tab", _plant_a_box_carrying_a_tab),
    ("a tree listing, its arms meeting labels and its runs ending in space",
     _plant_a_tree_listing),
    ("a box character in running prose", _plant_a_box_character_in_running_prose),
    ("a misaligned block a row of `exempt` names", _plant_an_exempted_misaligned_block),
    ("a misaligned box where `held` is false",
     _plant_a_misaligned_box_where_the_check_is_off),
    ("a misaligned box where no `box_diagrams` block is stated",
     _plant_a_misaligned_box_where_nothing_is_stated),
]


def _a_repository(where: str) -> str:
    """A real git repository with a governed document in its index.

    ⛔ Here because every plant above is in memory, and the one thing memory
    cannot assert is that the index is read at all: the first form of a sibling
    sweep read the working tree and reported a file nobody had added.
    """
    root = os.path.join(where, "a-project")
    os.makedirs(os.path.join(root, "docs"))
    subprocess.run(["git", "init", "-q", root], check=True, capture_output=True)
    with open(os.path.join(root, "README.md"), "w", encoding="utf-8") as handle:
        handle.write("# A project\n\nIn [the document](docs/a-document.md).\n")
    with open(os.path.join(root, "docs", "a-document.md"), "w", encoding="utf-8") as handle:
        handle.write("# The document\n")
    with open(os.path.join(root, "docs", "unindexed.md"), "w", encoding="utf-8") as handle:
        handle.write("# Not added\n")
    subprocess.run(
        ["git", "-C", root, "add", "README.md", "docs/a-document.md"],
        check=True, capture_output=True,
    )
    return root


def self_test() -> int:
    subject = _a_subject()
    by_name = {name: check for name, _kind, check in CHECKS}
    failures = 0

    def check(label: str, condition: bool, detail: str = "") -> None:
        nonlocal failures
        if condition:
            print(f"  ok                     {label}")
        else:
            failures += 1
            print(f"  FAIL                   {label}{': ' + detail if detail else ''}")

    # ⛔ The fixture's own premise first. A plant measured against a baseline that
    # is already red proves nothing, and an exemption measured against one would
    # pass vacuously.
    baseline = {name: set(found) for name, found in run(subject).items()}
    check("the fixture starts green", not any(baseline.values()), f"{baseline}")
    check("the fixture governs more than one document", len(subject.set_now) == 3,
          f"{subject.set_now}")
    check("the fixture tracks files the globs do not govern",
          len(subject.tracked) > len(subject.set_now), f"{subject.tracked}")
    check("every check declares one of the three kinds",
          {kind for _n, kind, _c in CHECKS} <= {COMPUTED, FORBIDDING, QUOTING},
          f"{sorted({kind for _n, kind, _c in CHECKS})}")
    check("the fixture quotes nothing, so it warns about nothing",
          warnings(subject) == [], f"{warnings(subject)}")

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

    # ⛔ The quoting kind's own obligation, which is not a problem count: a
    # project that configured one is warned on every run, and the warning names
    # both directions of the failure.
    quoting = _plant_a_quoted_sentence_that_is_gone(subject.copy())
    said = " ".join(warnings(quoting))
    check("a quoted entry is warned about at all", bool(said))
    check("the warning names the red direction", "RED" in said, said[:120])
    check("the warning names the green direction", "GREEN" in said, said[:120])
    check(
        "and the quoted check is still performed rather than stood down",
        bool(by_name["a quoted sentence is still in its document"](quoting)),
    )

    # ⛔ The third state's own obligation, which is the same shape: the rows a
    # project declines to enforce are counted on every run, and where that is
    # all of them the run says which three checks hold nothing.
    none_enforced = _plant_a_graph_that_enforces_nothing(subject.copy())
    said = " ".join(warnings(none_enforced))
    check("a graph that enforces nothing is warned about", bool(said))
    check("and the warning names the checks it empties", "HOLD NOTHING" in said,
          said[:140])
    check(
        "and the three graph checks come back with nothing rather than a red",
        not any(
            by_name[name](none_enforced)
            for name in ("a document names only what its row allows",
                         "a row names only edges the text carries",
                         "every document is reachable from an entry point")
        ),
    )
    check(
        "while the governed set, the forbidden names and the blocks are still held",
        bool(by_name["no forbidden name appears"](
            _plant_a_forbidden_name(_plant_a_graph_that_enforces_nothing(subject.copy()))
        )),
    )
    some_enforced = _plant_a_row_that_does_not_enforce_its_edge(subject.copy())
    partly = " ".join(warnings(some_enforced))
    check("a partly enforced graph names the rows it does not enforce",
          "docs/a-document.md" in partly, partly[:140])
    check("and does not claim the checks hold nothing", "HOLD NOTHING" not in partly)

    # ⛔ *No row* against `may_name: null`, which were one answer and are two.
    no_row = _drop_a_row(subject.copy())
    check("a document with no row is not reported as one the project left unenforced",
          no_row.unenforced == [], f"{no_row.unenforced}")
    check("and nothing warns about it, check 1 being what reports it",
          warnings(no_row) == [], f"{warnings(no_row)}")
    check("while a row stating null is reported as unenforced",
          _plant_a_row_that_does_not_enforce_its_edge(subject.copy()).unenforced
          == ["docs/a-document.md"])

    # ⛔ The two forms of a row, and the sentence a wrapped document carries --
    # each a false refusal this file's own first form produced.
    check("the optional closing delimiter is discounted",
          cells("| a | b |") == cells("| a | b") == 2,
          f"{cells('| a | b |')} vs {cells('| a | b')}")
    escaped_at_the_end = cells(r"| a | b \|")
    check("and an escaped pipe at the end of a row is not discounted",
          escaped_at_the_end == 2, f"{escaped_at_the_end}")
    check("a ragged row is still ragged once both are discounted",
          cells("| one |") != cells("| a | b |"))
    check("a wrapped sentence is found",
          flat("a claim\nacross a break") == "a claim across a break")

    # The glob semantics, which is where this file deliberately differs from
    # § 15's and the difference is asserted rather than described.
    check("a root glob does not cross a separator", not governed("docs/a.md", ["*.md"]))
    check("and matches the root's own file", governed("a.md", ["*.md"]))
    check("a doubled glob crosses one", governed("docs/deep/a.md", ["docs/**/*.md"]))
    check("and matches with nothing between", governed("docs/a.md", ["docs/**/*.md"]))
    check("a named directory glob matches one level",
          governed("carriers/a/CARRIER.md", ["carriers/*/CARRIER.md"]))
    check("and not two", not governed("carriers/a/b/CARRIER.md", ["carriers/*/CARRIER.md"]))

    # Both forms of naming, each asserted alone: a reader of one reports the
    # other as an edge the row invented.
    documents = {"README.md": None, "docs/a-document.md": None}
    check("a link target is an edge",
          names("[x](docs/a-document.md)", "README.md", documents) == {"docs/a-document.md"})
    check("a relative link is resolved against the naming document",
          names("[x](../README.md)", "docs/a-document.md", documents) == {"README.md"})
    check("a bare path in prose is an edge",
          names("see docs/a-document.md", "README.md", documents) == {"docs/a-document.md"})
    check("an absolute link is not an edge",
          names("[x](https://example.invalid/README.md)", "docs/a-document.md", {}) == set())
    check("a document does not name itself",
          names("README.md names README.md", "README.md", documents) == set())

    # ⛔ A project's own spelling, which is the key the surveyed implementation's
    # eight role carriers need: it names each of them by its slug, so the path
    # form reports every one of its declared edges as dropped.
    slugged = {"carriers/a-role/CARRIER.md": r"(?<![\w-])a-role(?![\w-])"}
    check("a document is named by the spelling its row states",
          names("hand it to a-role next", "README.md", slugged)
          == {"carriers/a-role/CARRIER.md"})
    check("and the spelling is held to its own boundary",
          names("hand it to a-role-two next", "README.md", slugged) == set())
    # ⚠️ The first form of this assertion used the slug's own pattern and was
    # wrong rather than failing: `a-role` occurs inside `carriers/a-role/…`, and
    # the slug's leading boundary admits a `/` on purpose -- which is the form
    # the surveyed project's own ambiguous-slug rule relies on. The spelling
    # here therefore shares nothing with the path.
    titled = {"carriers/a-role/CARRIER.md": r"the role's own file"}
    check("a path is not a mention where the row states another spelling",
          names("see carriers/a-role/CARRIER.md", "README.md", titled) == set())
    check("and that spelling is",
          names("stated in the role's own file", "README.md", titled)
          == {"carriers/a-role/CARRIER.md"})
    check("but a link to it resolves whatever the spelling is",
          names("[x](carriers/a-role/CARRIER.md)", "README.md", titled)
          == {"carriers/a-role/CARRIER.md"})

    # ⛔ The boundary, with the three cases the surveyed implementation carries a
    # lookbehind each for. Without it a substring test reports an edge to the
    # root file from every document naming either of the others.
    rooted = {"CLAUDE.md": None, "tech/CLAUDE.md": None, "main_website-CLAUDE.md": None}
    check("a bare path at a boundary is a mention",
          names("see CLAUDE.md for the route", "README.md", rooted) == {"CLAUDE.md"})
    check("a path under a directory is not a mention of the root's own file",
          names("see tech/CLAUDE.md", "README.md", rooted) == {"tech/CLAUDE.md"})
    check("and a path prefixed with a hyphenated name is not either",
          names("see main_website-CLAUDE.md", "README.md", rooted)
          == {"main_website-CLAUDE.md"})
    check("a mention ending a sentence is still a mention",
          names("the rest is in CLAUDE.md.", "README.md", rooted) == {"CLAUDE.md"})
    check("a longer name sharing the leading path is not a mention",
          names("see CLAUDE.md-draft", "README.md", rooted) == set())

    # The index, against a repository built for it: the one thing memory cannot
    # assert is that `git ls-files` is what the set comes from.
    with tempfile.TemporaryDirectory() as where:
        root = _a_repository(where)
        facet = {
            "carrier": LIST,
            "files": ["*.md", "docs/**/*.md"],
            "entry_points": ["README.md"],
            "graph": [
                {"document": "README.md", "may_name": ["docs/a-document.md"],
                 "derived_from": []},
                {"document": "docs/a-document.md", "may_name": [], "derived_from": []},
            ],
            "forbidden": [],
            "quoted": [],
        }
        live = read_subject(root, facet)
        check(
            "a real tree's governed set is read from the index, the unindexed file left out",
            live.set_now == ["README.md", "docs/a-document.md"],
            f"read {live.set_now}",
        )
        check("and that tree is green", not any(run(live).values()), f"{run(live)}")

        # ⛔ A link resolves against the index, and a markdown target the globs
        # do not govern is read off the tree for its headings: the two halves
        # memory cannot assert, each measured on a real repository.
        os.makedirs(os.path.join(root, "vendor"))
        with open(os.path.join(root, "vendor", "notes.md"), "w", encoding="utf-8") as handle:
            handle.write("# Notes\n\n## A heading\n")
        subprocess.run(
            ["git", "-C", root, "add", "vendor/notes.md"], check=True, capture_output=True,
        )
        with open(os.path.join(root, "README.md"), "a", encoding="utf-8") as handle:
            handle.write("\nThe [notes](vendor/notes.md#a-heading) are vendored.\n")
        linked = run(read_subject(root, facet))["every link resolves"]
        check("an ungoverned markdown target is read off the tree for its headings",
              linked == [], f"{linked}")
        with open(os.path.join(root, "README.md"), "a", encoding="utf-8") as handle:
            handle.write("\nA [draft](docs/unindexed.md) nobody added.\n")
        linked = run(read_subject(root, facet))["every link resolves"]
        check("a link to a file on disk that the index does not hold is reported",
              len(linked) == 1 and "docs/unindexed.md" in linked[0], f"{linked}")

    if failures:
        print(
            f"\n{failures} assertion(s) did not hold. A check that cannot fail is not a "
            "check, and an exemption that cannot pass is not an exemption."
        )
    return 1 if failures else 0


def main(argv: list) -> int:
    parser = argparse.ArgumentParser(
        description="Hold a project's prose documents to what its configuration states.",
    )
    parser.add_argument(
        "--skills-root",
        default=".",
        help="the root the configuration is resolved relative to (§ 1)",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="assert each check reddens on its planted violations and stays green on "
        "each planted exemption, then stop",
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
    if facet.get("carrier") != LIST:
        # ⛔ Not a verdict. A project that governs no document has no subject
        # here, and a run that printed green would be a check holding nothing
        # (§ 38) -- so this says what is absent and exits neither green nor red.
        print(
            f"`{FACET}.carrier` is {facet.get('carrier')!r}, so this project governs no "
            "document and this check has no subject. ⛔ That is not a statement that the "
            "documents agree: there is no graph to stand down from. A project in that "
            "position runs no such check -- while an entry mirroring `--self-test` "
            "answers about this carrier rather than about this tree and is permitted "
            "beside the absence. What it decided instead: "
            f"{' '.join(str(facet.get('absent_reason')).split())}",
            file=sys.stderr,
        )
        return 2

    return hold(read_subject(os.path.abspath(args.skills_root), facet))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
