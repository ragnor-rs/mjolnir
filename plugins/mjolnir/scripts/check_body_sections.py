#!/usr/bin/env python3
"""Hold a pull request body to the sections this project's configuration states.

A body section is the procedure's own interface wherever **another role reads
it**: one role writes the section and a second collects it out of every change
a batch carries. A section like that is not a repository convention, and a
project that enforces it by hand enforces it unevenly -- so the sections are a
configured fact, stated once, and this is the one thing that holds a body to
them. The surface beside this file -- `../config/schema.md`, the section on the
sections a body must carry -- is the single statement of what a section is and
what each of its keys means, and none of it is restated here.

⛔ **The headings are not here.** `SECTIONS` below is empty in the copy that
ships with the toolkit, and the install step renders a project's own stated
sections into it. A heading written into this file would be one project's
vocabulary shipped to every project, and the surface already refuses that
twice over -- in the repository's own language (§ 8), and as a value a carrier
may not carry.

**Two callers, one implementation, and that is the whole point of the split
below.** Everything above the sentinel line is what the install step vendors
into an adopting repository, where the host's own run executes it; the source
you are reading is what a person runs from the toolkit. The halves cannot
disagree about a body, because the second half contains no rule -- it is the
renderer and the suite, and the suite's last arms execute the *rendered* copy
against the same bodies as the source and assert the same answers.

What it reads a body from, in order, and why there are three:

  * `--body-file PATH`, which is the explicit route and the one a suite uses;
  * `PR_BODY` in the environment, which is what the generated workflow sets off
    the event -- ⚠️ **the event and never a checkout**, so a body edited in
    place is re-read with no new commit, which is why the generated trigger
    carries the edit event;
  * the host's own CLI for the pull request on this branch, which is what the
    local run has and the generated one does not.

⛔ **A body that could not be read is not an empty body.** It exits on its own
status and names what it could not reach: § 11's rule that a report names what
it could not establish, arriving where the other answer -- every section
missing -- is a refusal naming work no author can do.

Usage:
    check_body_sections.py [--body-file PATH]  hold a body to the sections
                                               rendered into this copy
    check_body_sections.py --self-test         assert every answer against
                                               planted bodies, assert the
                                               rendered copy agrees, then report
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys

# The sections this copy holds a body to: the heading as the body spells it,
# the answer that closes the section with nothing in it, and what reads the
# section out of the body. ⛔ Empty in the toolkit's own copy and rendered by
# the install step, which is what keeps one project's vocabulary out of every
# other project's gate.
SECTIONS: tuple = ()

# --- the grammar of a section ----------------------------------------------
#
# Form, not content. An ATX heading at any level, matched on its text alone and
# without regard to case: which level a body puts a section at, and how it
# cases the words, are formatting rather than the fact the section carries.

HEADING = re.compile(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$")

# A line under a heading that carries no claim: blank, a horizontal rule, or a
# comment the host does not render. Stripping these is what lets a body close a
# section with a rule and still read as having answered it, rather than as
# having stated the rule as its content.
NOISE = re.compile(r"^\s*(?:-{3,}|\*{3,}|_{3,}|<!--.*-->)?\s*$")
LIST_MARKER = re.compile(r"^(?:[-*+]|\d+[.)])\s+")

# What a heading's text is once the emphasis a body wraps it in is off. The
# same strip both callers apply, so `**Deployment**` and `Deployment` are one
# heading rather than two.
DECORATION = "*_`:"


def sections(body: str, heading: str) -> list[list[str]]:
    """Every section under the heading named, in document order.

    ⚠️ Fenced blocks are skipped by a line toggle rather than matched by a
    paired expression. One trailing space after a fence's language tag makes a
    paired expression pair one block's closer with the next block's opener, and
    a body quoting the required shape in an example would then hijack the real
    section -- which is the likely case rather than the exotic one, a body
    being the place authors are told what the shape is.

    ⛔ Every match is returned and never the first. A second section under one
    heading is not a repeat of the first: a body answering the section and then
    stating something else under the same heading further down reads as
    answered under any rule that takes one, and a heading stated twice is a
    refusal of its own one level up.
    """
    wanted = heading.strip().strip(DECORATION).strip().lower()
    found: list[list[str]] = []
    current: list[str] | None = None
    fenced = False
    for line in body.splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
            if current is not None:
                current.append(line)
            continue
        if not fenced:
            match = HEADING.match(line)
            if match:
                title = match.group(2).strip().strip(DECORATION).strip().lower()
                if current is not None:
                    found.append(current)
                    current = None
                if title == wanted:
                    current = []
                continue
        if current is not None:
            current.append(line)
    if current is not None:
        found.append(current)
    return found


def claims(lines: list[str]) -> list[str]:
    """The lines of a section that state something, with the noise out."""
    return [line.strip() for line in lines if not NOISE.match(line)]


def answered_nothing(stated: list[str], answer: str) -> bool:
    """Whether this section's whole content is the configured *nothing* answer.

    ⛔ **The whole of it.** A section answering *nothing is needed* and then
    stating three more lines has not answered -- it has said both things, and
    taking the first would read the one a body can always add.

    ⚠️ The list marker and a trailing period are formatting: a body writing the
    answer as a bullet has written the answer. Nothing else is normalised, the
    answer being the project's own string and not a vocabulary this file holds.
    """
    if len(stated) != 1:
        return False
    written = LIST_MARKER.sub("", stated[0]).strip().strip(DECORATION).strip()
    return written.rstrip(".").casefold() == answer.strip().rstrip(".").casefold()


def verdict(body: str, stated_sections) -> list[str]:
    """Every refusal this body earns, or an empty list.

    ⛔ All of them, never the first. A body with three sections missing hears
    about three rather than being handed back once per round trip -- the
    readiness gate's rule one surface over, arriving at the artifact a role
    writes rather than at the item it reads.
    """
    refusals = []
    for heading, nothing_needed, read_by in stated_sections:
        found = sections(body, heading)
        if not found:
            refusals.append(
                f"the body states no `{heading}` section. {read_by} reads it out "
                f"of this change, and a body with nothing under that heading is a "
                f"change that reader has no answer from. Where there is nothing to "
                f"state, the section says so: `{nothing_needed}`."
            )
            continue
        if len(found) > 1:
            refusals.append(
                f"the body states `{heading}` {len(found)} times. {read_by} "
                f"collects the section by its heading, so a second one leaves it "
                f"choosing between them -- and a body answering under the first "
                f"and stating something else under the second reads as answered."
            )
            continue
        stated = claims(found[0])
        if not stated:
            refusals.append(
                f"the body states `{heading}` and puts nothing under it. An empty "
                f"section is not an answer: where the change needs nothing of what "
                f"{read_by} reads, the section says so in as many words — "
                f"`{nothing_needed}`."
            )
            continue
        # ⛔ The answer and something beside it is not an answer. ⚠️ Measured as
        # the shape a body arrives in after an edit: the `nothing` line written
        # first and the work added under it, which reads as answered to a rule
        # that takes the first claim and leaves the reader of the section
        # running nothing.
        if len(stated) > 1 and any(
            answered_nothing([line], nothing_needed) for line in stated
        ):
            refusals.append(
                f"the body's `{heading}` section states `{nothing_needed}` and "
                f"then states something else. {read_by} would have to choose "
                f"between them: either the change needs nothing there, or it "
                f"needs what the rest of the section says."
            )
    return refusals


# --- what a body is read from ----------------------------------------------


class Unreadable(Exception):
    """The body could not be read, which is not a verdict about it."""


def from_the_host() -> str:
    """The body of the pull request on this branch, through the host's own CLI.

    ⚠️ **The local caller's route and not the generated one.** A run on the
    host already has the body on the event it was started by, and asking the
    host for it again would be a credential a gate reading a body does not
    need -- so the generated workflow sets `PR_BODY` and never reaches here.
    """
    try:
        done = subprocess.run(
            ["gh", "pr", "view", "--json", "body", "--jq", ".body"],
            capture_output=True, text=True, check=False,
        )
    except OSError as exc:
        raise Unreadable(
            "the host's CLI is not on PATH, and no body was given. Pass "
            "`--body-file`, or set `PR_BODY`, or authenticate the host's CLI."
        ) from exc
    if done.returncode != 0:
        raise Unreadable(
            "the host's CLI could not read a pull request for this branch: "
            + (done.stderr.strip() or "no reason given").splitlines()[0]
        )
    return done.stdout


def read_body(body_file: str | None) -> str:
    """The body, from whichever of the three routes answers first."""
    if body_file is not None:
        try:
            with open(body_file, encoding="utf-8") as handle:
                return handle.read()
        except OSError as exc:
            raise Unreadable(f"{body_file} could not be read: {exc}") from exc
    if os.environ.get("PR_BODY") is not None:
        return os.environ["PR_BODY"]
    return from_the_host()


# --- the command line ------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Hold a pull request body to the sections this project states.",
    )
    parser.add_argument(
        "--body-file",
        help="the file the body is in; otherwise `PR_BODY`, otherwise the host",
    )
    # ⛔ Strict, and an unknown argument is refused rather than ignored. ⚠️ A
    # tolerant parse makes a mistyped `--body-file` into a silent fall-through
    # to the environment or to the host, so the run answers about a body
    # nobody asked it to read and reports a verdict either way.
    args = parser.parse_args(argv)

    # ⛔ Answered before a body is read, and answered as a configuration rather
    # than as a pass. A project stating no section has no gate, and a copy of
    # this file rendered for one would be a run asserting nothing -- which the
    # install step already refuses by not writing it.
    if not SECTIONS:
        print(
            "This copy holds no section, so there is nothing to hold a body to. "
            "The sections are the project's own and are rendered in by the "
            "install step; a project stating none gets no gate."
        )
        return 0

    try:
        body = read_body(args.body_file)
    except Unreadable as exc:
        print(f"the body could not be read, so this change was not held: {exc}",
              file=sys.stderr)
        return 2

    refusals = verdict(body, SECTIONS)
    for refusal in refusals:
        print(f"  - {refusal}")
    if refusals:
        print(f"\n{len(refusals)} section(s) this project requires are not answered.",
              file=sys.stderr)
        return 1
    print(f"every section this project requires is answered ({len(SECTIONS)} held).")
    return 0


# ---- the vendored half ends here ------------------------------------------
#
# ⛔ The line above is the sentinel `render` splits on, and everything below it
# is the renderer and the suite. Nothing below states a rule about a body: a
# rule down here would be one the host's own run never executes, since the
# copy it runs is the half above.


RENDER_SENTINEL = "# ---- the vendored half ends here "

# What the rendered copy ends with, in place of everything below the sentinel.
# ⛔ Nothing in it moves between runs, which is the install step's own
# byte-identical property reaching the one artifact whose body is generated
# rather than written.
RENDER_TAIL = 'if __name__ == "__main__":\n    sys.exit(main())\n'

# The line the sections are rendered over. ⛔ Matched whole and anchored, so a
# render is a substitution of one line and never a search through the source.
PLACEHOLDER = "SECTIONS: tuple = ()"


def _source() -> str:
    with open(os.path.abspath(__file__), encoding="utf-8") as handle:
        return handle.read()


def rendered_sections(stated_sections) -> str:
    """The `SECTIONS` line a project's own stated sections render to."""
    if not stated_sections:
        return PLACEHOLDER
    members = "".join(
        f"    ({heading!r}, {nothing!r}, {read_by!r}),\n"
        for heading, nothing, read_by in stated_sections
    )
    return "SECTIONS: tuple = (\n" + members + ")"


def render(stated_sections) -> str:
    """This file's vendored half, with a project's own sections rendered in.

    ⛔ The half above the sentinel and not the whole file. The suite below
    plants headings of its own, and a whole-file copy would carry every one of
    them into an adopting repository -- heading literals that project never
    stated, in the one artifact whose whole claim is that it carries none.
    """
    source = _source()
    if PLACEHOLDER not in source:
        raise ValueError(
            f"this file states no {PLACEHOLDER!r} line, so there is nowhere to "
            "render a project's sections. The placeholder is what a render "
            "substitutes, and a file without it would be vendored holding nothing."
        )
    head = source.split(RENDER_SENTINEL)[0]
    return head.replace(PLACEHOLDER, rendered_sections(stated_sections), 1) \
        + RENDER_TAIL


def from_config(configuration) -> tuple:
    """`body_sections` as this file's own triples, read through the reader.

    ⛔ Keyed off the surface's names and not re-spelled: the reader has already
    refused every shape the facet does not permit, so what reaches here is
    three strings per entry.
    """
    return tuple(
        (entry["heading"], entry["nothing_needed"], entry["read_by"])
        for entry in (configuration.get("body_sections") or [])
    )


# --- collecting a section out of one change --------------------------------
#
# ⛔ **The toolkit's own route, and deliberately not the vendored copy's.** The
# half above the sentinel holds a body to the sections rendered into it; what a
# collecting role needs is the opposite reading -- which of this project's
# sections this change owes work under, and which it closed with nothing. The
# reading lives below the sentinel because it reads the configuration, which the
# vendored half must not depend on, and because an adopting repository's gate has
# no use for it.


def collected(entries, body: str) -> list[dict]:
    """Each section this project states, read out of one change's body.

    ⛔ **Through the same grammar the gate applies, which is the whole reason
    this reading is here rather than in the role that collects.** Whether a
    section closed with *nothing* is `answered_nothing` above's question -- it
    normalises a list marker, a trailing period, the emphasis a body wraps a
    line in and its case -- so a role deciding it by eye would be a second
    grammar, free to disagree with the one the host's own run applied to the
    same body and in the direction that collects no step.

    ⛔ **Three readings and never two.** A body the gate would refuse is neither
    owed nor answered: reporting it as answered collects nothing out of a change
    that may state something, and reporting it as owed hands a role content it
    could not identify. ⚠️ `unheld` is the one reading that says *ask the gate*.

    ⛔ **And which bodies those are is asked of `verdict` above rather than
    worked out again here.** The conditions it refuses on are its own and are not
    listed again in this function: a second statement of them is a copy free to
    disagree with the run that holds the change. ⚠️ **Measured on this
    function's first version**, which restated them, left one out, and read a
    body the gate refuses as a step owed.

    Each entry comes back carrying the keys the configuration stated -- where
    the step falls and who answers it -- so the collecting role reads them here
    rather than going back to the configuration per section.
    """
    read: list[dict] = []
    for entry in entries or []:
        triple = (entry["heading"], entry["nothing_needed"], entry["read_by"])
        found = sections(body, entry["heading"])
        stated = claims(found[0]) if len(found) == 1 else []
        read.append({
            "heading": entry["heading"],
            "read_by": entry["read_by"],
            "when": entry.get("when"),
            "answered_by": entry.get("answered_by"),
            "reading": (
                "unheld" if verdict(body, (triple,))
                else "nothing" if answered_nothing(stated, entry["nothing_needed"])
                else "owed"
            ),
            "stated": stated,
        })
    return read


def _rendered_collection(read: list[dict]) -> str:
    """What a collecting role is handed, one section per block."""
    out = []
    for section in read:
        out.append(
            f"{section['reading']}: {section['heading']!r} "
            f"(when: {section['when']}, answered_by: {section['answered_by']}, "
            f"read_by: {section['read_by']!r})"
        )
        out.extend(f"    {line}" for line in section["stated"])
    return "\n".join(out)


def collect(argv: list[str] | None = None) -> int:
    """Print this project's sections as read out of one change's body.

    ⛔ **It is no gate and its status is not a verdict about the change.** What
    holds a body is `main` above, run by the host; this prints what one change
    owes so that a role can act on it, and a section it reports `unheld` is the
    gate's answer to give rather than this one's.
    """
    parser = argparse.ArgumentParser(
        description="Read this project's body sections out of one change's body.",
    )
    parser.add_argument("--collect", action="store_true", help="the mode flag")
    parser.add_argument(
        "--body-file", required=True, help="the file the change's body is in"
    )
    parser.add_argument(
        "--skills-root", default=".",
        help="the directory the project's configuration is resolved from (§ 1)",
    )
    args = parser.parse_args(argv)

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import config  # noqa: PLC0415 -- the one reader of the surface, imported here

    try:
        loaded = config.load(args.skills_root, check_paths=False)
    except Exception as error:  # noqa: BLE001 -- a stated configuration that did not resolve
        print(
            f"the configuration at {args.skills_root} did not resolve "
            f"({type(error).__name__}: {error}), so no section was collected.",
            file=sys.stderr,
        )
        return 2
    entries = loaded.get("body_sections") or []
    # ⛔ A stated absence and its own status, which is `title_form.py render`'s
    # answer for a project stating no form: a project requiring no section owes
    # no step, and that is not a run that found nothing.
    if not entries:
        print(
            "This project states no body section, so a change owes no step through "
            "this facet (§ 20's `[]`). Nothing was collected."
        )
        return 3
    try:
        body = read_body(args.body_file)
    except Unreadable as exc:
        print(f"no section was collected: {exc}", file=sys.stderr)
        return 2
    print(_rendered_collection(collected(entries, body)))
    return 0


# --- the self-test ---------------------------------------------------------

# Fixture sections, and ⛔ **they live below the sentinel on purpose**: every
# heading here is one no project stated, and the acceptance this file is
# written to says none of them may reach a generated file.
A_SECTION = ("Before it can be deployed", "Nothing is needed.",
             "the role that deploys a batch")
ANOTHER = ("Data to migrate", "None.", "the role that runs a migration")


def self_test() -> int:  # noqa: C901 -- one assertion per property, read in order
    """Assert every answer against planted bodies, then assert the copy agrees."""
    import tempfile

    failures: list[str] = []
    ran = 0

    def check(label: str, condition: bool, detail: str = "") -> None:
        nonlocal ran
        ran += 1
        print(f"  {'ok  ' if condition else 'FAIL'}  {label}"
              + (f": {detail}" if detail and not condition else ""))
        if not condition:
            failures.append(label)

    one = (A_SECTION,)
    two = (A_SECTION, ANOTHER)
    heading, nothing, _reader = A_SECTION

    print("a body that answers the section is green")
    for label, body in (
        ("stated and answered", f"A summary.\n\n## {heading}\n\nRun the backfill.\n"),
        ("the configured nothing answer", f"## {heading}\n\n{nothing}\n"),
        ("that answer as a bullet", f"## {heading}\n\n- {nothing}\n"),
        ("that answer without its period",
         f"## {heading}\n\n{nothing.rstrip('.')}\n"),
        ("a different heading level", f"#### {heading}\n\nRun the backfill.\n"),
        ("a cased heading", f"## {heading.upper()}\n\nRun the backfill.\n"),
        ("an emphasised heading", f"## **{heading}**\n\nRun the backfill.\n"),
        ("the section closed with a rule",
         f"## {heading}\n\nRun the backfill.\n\n---\n"),
    ):
        check(f"green: {label}", verdict(body, one) == [],
              str(verdict(body, one)))

    print()
    print("and every way of not answering it is refused, each named as itself")
    for label, body, wanted in (
        ("no such section", "A summary and a test plan.\n", "states no"),
        ("an empty body", "", "states no"),
        ("the heading inside a fence",
         f"## Notes\n\n```markdown\n## {heading}\n\n{nothing}\n```\n", "states no"),
        ("the heading twice",
         f"## {heading}\n\n{nothing}\n\n## Notes\n\nx\n\n## {heading}\n\nRun it.\n",
         "2 times"),
        ("the section left empty", f"## {heading}\n\n## Notes\n\nx\n", "puts nothing"),
        ("the section holding only a rule", f"## {heading}\n\n---\n", "puts nothing"),
        ("the section holding only a comment",
         f"## {heading}\n\n<!-- later -->\n", "puts nothing"),
        ("the nothing answer and then something else",
         f"## {heading}\n\n{nothing}\n\nAnd run the backfill.\n", None),
    ):
        answered = verdict(body, one)
        check(f"refused: {label}", len(answered) == 1, str(answered))
        if wanted is not None:
            check(f"  and named as itself: {label}",
                  bool(answered) and wanted in answered[0], str(answered))

    # ⛔ The arm that makes the *whole content* rule load-bearing rather than
    # incidental. ⚠️ Measured with the length test taken out: a body answering
    # `None.` and then listing the work it needs done passed, which is the
    # shape the section exists to catch.
    mixed = f"## {heading}\n\n{nothing}\n\nAnd run the backfill.\n"
    check("a nothing answer with anything beside it is not an answer",
          verdict(mixed, one) != [],
          "a section saying both things reads as answered under any rule that "
          "takes the first")

    print()
    print("every missing section is reported, not the first")
    both_missing = verdict("A summary.\n", two)
    check("two sections missing are two refusals", len(both_missing) == 2,
          str(both_missing))
    check("and each names its own heading",
          any(A_SECTION[0] in r for r in both_missing)
          and any(ANOTHER[0] in r for r in both_missing),
          str(both_missing))
    check("a refusal names what reads the section",
          any(A_SECTION[2] in r for r in both_missing), str(both_missing))
    check("and the answer that would close it",
          any(A_SECTION[1] in r for r in both_missing), str(both_missing))

    print()
    print("a project stating no section is held to nothing, and says so")
    check("no section is no refusal", verdict("", ()) == [])
    with tempfile.TemporaryDirectory() as tmp:
        empty = os.path.join(tmp, "a-body.md")
        with open(empty, "w", encoding="utf-8") as handle:
            handle.write("A summary.\n")
        check("and the shipped copy exits zero over any body",
              main(["--body-file", empty]) == 0,
              "the toolkit's own copy states no section, so it holds nothing")

    print()
    print("a body that could not be read is not an empty body")
    was = os.environ.pop("PR_BODY", None)
    try:
        # ⛔ Asserted on the function rather than through `main`, whose shipped
        # `SECTIONS` is empty and which therefore returns before reading a body
        # at all. ⚠️ Measured the other way: the arm passed on the early return
        # and held nothing about the read.
        try:
            read_body(os.path.join("a-directory-that-is-not-there", "a-body.md"))
            raised = False
        except Unreadable:
            raised = True
        check("an unreadable file is an exception rather than an empty string",
              raised,
              "read as empty, every section would be reported missing and the "
              "refusal would name work nobody can do")
    finally:
        if was is not None:
            os.environ["PR_BODY"] = was

    print()
    print("`PR_BODY` is read where no file is given, which is the generated route")
    was = os.environ.get("PR_BODY")
    try:
        os.environ["PR_BODY"] = f"## {heading}\n\n{nothing}\n"
        check("the environment answers", verdict(read_body(None), one) == [])
        os.environ["PR_BODY"] = ""
        check("and an empty one is a body rather than an absence",
              read_body(None) == "",
              "a body edited down to nothing is a refusal, not a read that failed")
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "a-body.md")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("from the file\n")
            os.environ["PR_BODY"] = "from the environment"
            check("an explicit file outranks the environment",
                  read_body(path) == "from the file\n")
    finally:
        if was is None:
            os.environ.pop("PR_BODY", None)
        else:
            os.environ["PR_BODY"] = was

    print()
    print("the rendered copy is the same implementation, and carries no heading")
    source = _source()
    check("the source states the placeholder the render substitutes",
          PLACEHOLDER in source, "a file without it would be vendored holding nothing")
    # ⛔ The split is held on what each half contains rather than on a count of
    # the sentinel: the constant stating it is itself below the line, so a
    # count is two and always was. What matters is that the head is the rule
    # and the tail is the renderer.
    head_only = source.split(RENDER_SENTINEL)[0]
    check("the sentinel splits the rule off from the renderer",
          RENDER_SENTINEL in source and "def verdict(" in head_only
          and "def render(" not in head_only and "def self_test(" not in head_only,
          "the half this vendors is the half above the sentinel, and it has to "
          "be all of the rule and none of the suite")
    shipped = render(())
    check("rendered for a project stating nothing, it still states the placeholder",
          PLACEHOLDER in shipped)
    copy = render(two)
    check("rendered for a project, it states that project's headings",
          all(h in copy for h, _n, _r in two))
    # ⛔ The acceptance bullet, held mechanically: every string literal in the
    # rendered file is either one the source's vendored half already carried or
    # one the configuration stated. ⚠️ Measured against a whole-file render,
    # which carried every fixture heading below the sentinel into the artifact.
    import ast
    vendored = {
        node.value for node in ast.walk(ast.parse(head_only))
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    } | {
        node.value for node in ast.walk(ast.parse(RENDER_TAIL))
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    stated = {value for member in two for value in member}
    strayed = sorted(
        node.value for node in ast.walk(ast.parse(copy))
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
        and node.value not in vendored and node.value not in stated
    )
    check("and no literal the configuration did not state", not strayed,
          f"the rendered file carries {strayed}, which this project never stated")
    check("the suite's own fixture headings are below the sentinel",
          all(h not in copy for h, _n, _r in (A_SECTION,) if (h, _n, _r) not in two),
          "a fixture heading in the vendored half is a heading every adopter gets")

    print()
    print("and the two callers reach the same verdict on the same body")
    with tempfile.TemporaryDirectory() as tmp:
        vendored_path = os.path.join(tmp, "check_body_sections.py")
        with open(vendored_path, "w", encoding="utf-8") as handle:
            handle.write(copy)
        check("the rendered copy parses", _parses(copy), "a render that does not "
              "parse is a gate that errors rather than one that answers")
        for label, body, status in (
            ("a body answering both", f"## {two[0][0]}\n\nx\n\n## {two[1][0]}\n\ny\n", 0),
            ("a body answering neither", "A summary.\n", 1),
            ("a body answering one", f"## {two[0][0]}\n\nx\n", 1),
        ):
            path = os.path.join(tmp, "a-body.md")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(body)
            done = subprocess.run(
                [sys.executable, vendored_path, "--body-file", path],
                capture_output=True, text=True, check=False,
                env={k: v for k, v in os.environ.items() if k != "PR_BODY"},
            )
            check(f"the rendered copy answers {label}", done.returncode == status,
                  f"exited {done.returncode}: {done.stdout.strip()[:200]}"
                  f"{done.stderr.strip()[:200]}")
            here = verdict(body, two)
            check(f"and the source agrees about {label}",
                  (1 if here else 0) == status, str(here))
        # ⛔ Byte-identical, which is what the install step's idempotence rests
        # on for this artifact: the body is generated, so a render that varied
        # would make every install a change.
        check("a second render is byte-identical", render(two) == copy)

    print()
    print("the collecting reading, which is the opposite question over the same grammar")
    # ⚠️ Entries as the reader hands them over -- every key the facet declares,
    # since what a collecting role reads off a section is `when` and
    # `answered_by` beside the heading.
    def _entry(triple, when, answered_by) -> dict:
        heading, nothing, reader = triple
        return {"heading": heading, "nothing_needed": nothing, "read_by": reader,
                "when": when, "answered_by": answered_by}

    owing = [_entry(A_SECTION, "before", "human"),
             _entry(ANOTHER, "after", "procedure")]
    first, second = A_SECTION[0], ANOTHER[0]
    for label, body, wanted in (
        ("work stated under the section is owed",
         f"A summary.\n\n## {first}\n\nApply the two schema changes.\n", "owed"),
        ("the nothing answer closes it",
         f"A summary.\n\n## {first}\n\n{A_SECTION[1]}\n", "nothing"),
        ("a section the body never states is unheld, never answered",
         "A summary.\n", "unheld"),
        ("a section stated with nothing under it is unheld",
         f"A summary.\n\n## {first}\n\n## Something else\n\nx\n", "unheld"),
        ("a section the body states twice is unheld, never read off the first",
         f"## {first}\n\n{A_SECTION[1]}\n\n## {first}\n\nApply it.\n", "unheld"),
        # ⛔ The arm this reading's first version got wrong: the gate refuses the
        # *nothing* answer with something beside it, and a reading that restated
        # the gate's conditions called it a step owed -- so a role would have run
        # work out of a body that never landed, on the strength of content the
        # gate says nobody may choose between.
        ("the nothing answer with something beside it is unheld, never owed",
         f"## {first}\n\n{A_SECTION[1]}\n\nApply it.\n", "unheld"),
    ):
        read = collected(owing, body)
        check(f"  {label}", read[0]["reading"] == wanted,
              f"read {read[0]['reading']!r} with {read[0]['stated']!r}")
    read = collected(owing, f"## {first}\n\nApply the two schema changes.\n")
    check("the lines the section states come back, for the role to name the step",
          read[0]["stated"] == ["Apply the two schema changes."],
          f"came back {read[0]['stated']!r}")
    # ⛔ The two keys the collecting role acts on, read back rather than assumed
    # present: a reading that dropped them would send every step down one arm.
    check("where each step falls and who answers it come back as stated",
          [(each["when"], each["answered_by"]) for each in read]
          == [("before", "human"), ("after", "procedure")],
          f"came back {[(e['when'], e['answered_by']) for e in read]}")
    # ⛔ The arm that is the whole argument for this reading living here: the
    # *nothing* answer written as an emphasised bullet with no period is the
    # answer, by `answered_nothing` above -- and a role reading the section by
    # eye is exactly what would call this one owed and run a step nobody owes.
    check("the gate's own normalisation decides it, not the literal",
          collected(owing, f"## {first}\n\n- **{A_SECTION[1].rstrip('.')}**\n")[0]
          ["reading"] == "nothing",
          "an emphasised bullet without its period did not read as the answer")
    check("a project stating no section collects nothing", collected([], "A summary.\n") == [])
    # ⚠️ Every section is read, never the first: the batch's own report names one
    # change's sections together, and a reading that stopped would hide the step
    # that falls on the other side of the deploy.
    check("every section stated is read, in the order the configuration states them",
          [each["heading"] for each in collected(owing, "A summary.\n")]
          == [first, second],
          "the reading did not cover every stated section")
    rendered = _rendered_collection(collected(owing, f"## {first}\n\nApply it.\n"))
    check("what a role is handed names the reading, the step's place and its answerer",
          all(word in rendered for word in ("owed", "before", "human", "unheld")),
          rendered)

    print()
    print("the rendered copy carries no import the toolkit's own tree supplies")
    # ⛔ The property the vendoring rests on: the artifact runs in a checkout of
    # the *adopting* repository, where nothing of this toolkit is present. An
    # import of the reader beside this file would be a gate that fails to start.
    imported = sorted(_imports(copy))
    check("every import it states is in the standard library",
          all(name in sys.stdlib_module_names for name in imported),
          f"it imports {[n for n in imported if n not in sys.stdlib_module_names]}, "
          "which an adopting repository's checkout does not carry")

    print()
    check("this run executed assertions rather than reporting a green nothing",
          ran > 1,
          "a suite that executes no case and exits zero is the degradation every "
          "check here is written against")
    print()
    if failures:
        print(f"{len(failures)} check(s) failed:")
        for label in failures:
            print(f"  - {label}")
        return 1
    print(f"every check passed ({ran} assertions).")
    return 0


def _parses(text: str) -> bool:
    import ast
    try:
        ast.parse(text)
    except SyntaxError:
        return False
    return True


def _imports(text: str) -> set[str]:
    """Every top-level module this source imports, by name."""
    import ast
    found = set()
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.Import):
            found.update(alias.name.split(".")[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            found.add(node.module.split(".")[0])
    return found


if __name__ == "__main__":
    if "--self-test" in sys.argv[1:]:
        sys.exit(self_test())
    # ⛔ Dispatched here and not inside `main`, which is the half the install step
    # vendors: the collecting reading needs the configuration, and a flag for it
    # above the sentinel would ship an adopting repository a gate that imports
    # this toolkit. Passed to the vendored copy the flag is refused by that
    # parser, which is the direction this split has to fail in.
    if "--collect" in sys.argv[1:]:
        sys.exit(collect())
    sys.exit(main())
