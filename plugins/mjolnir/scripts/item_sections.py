#!/usr/bin/env python3
"""Hold a work item's body to the sections this project declares beyond the procedure's.

`work_item.template.declared` (§ 4.4) is where a project requires sections of
its own -- an implementation plan written from a scan of the code is the
measured case. ⛔ **This module states no rule of its own.** The keys an entry
carries, what each means, and what a body owes a section are
`../config/schema.md` § 4.4's, read through the shared reader; what this
module owns is reading a body against them, once, for the filing role that
writes a body and for anyone reading one back.

What it refuses, per declared section:

  * a **required** section the body does not carry;
  * a section the body carries with **nothing under it** -- required or not,
    since a heading with nothing under it reads as answered;
  * a section whose `source` is `code` that **names no file**, a file being a
    repository-relative path in backticks;
  * given `--code-root`, a named file that **is not there**, or a path that is
    not repository-relative at all.

⚠️ **What it cannot see is whether the files named are the files read.** A
reference to a real file passes whether or not anybody opened it; § 4.4 states
that limit and this module does not narrow it.

It also composes and holds the dated section that § 3's `tracker.duplicate:
append` adds to a confirmed duplicate, under § 4.4's `sections.addendum`. What
it refuses there:

  * a body whose text before the section is **not the existing body exactly**;
  * **no dated section, or more than one**, after the existing body;
  * a heading that is **not the project's wording with a date in it**;
  * a section with **nothing under it**.

Usage:
    item_sections.py [--skills-root DIR]   the sections this project declares
    item_sections.py check --body-file PATH [--code-root DIR]
                                           hold a body to them
    item_sections.py addendum --before PATH --material PATH [--date YYYY-MM-DD]
                                           a confirmed duplicate's body with its
                                           dated section added
    item_sections.py appended --before PATH --after PATH
                                           hold that body to the existing one
    item_sections.py --self-test           assert every answer against planted
                                           bodies, then report this project's own

Exit status: 0 the body holds, 1 it does not, 2 the configuration or the body
could not be read, 3 this project declares no section -- or, for `addendum` and
`appended`, states `rewrite`, so there is no dated section to compose or hold. ⚠️ The last is § 11's
rule at a command line: *nothing to hold a body to* collapsed into 0 reads as a
body checked and passed, and a filing role reading 3 files as it did before the
key existed.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import config  # noqa: E402 -- the one reader of the surface

NOTHING_DECLARED = 3

# An ATX heading at any level, matched on its text: § 4.4 reads a heading as
# § 20 does, the level and the casing being formatting rather than the fact.
HEADING = re.compile(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$")
FENCE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")
# A line that carries no claim: blank, a rule, or a comment the host hides.
NOISE = re.compile(r"^\s*(?:-{3,}|\*{3,}|_{3,}|<!--.*-->)?\s*$")
# A file named in backticks. ⚠️ A trailing line reference (`a/b.py:12`, `:3-9`)
# is part of how a file is cited and not part of its path.
CITED = re.compile(r"`([^`\s]+)`")
LINE_REFERENCE = re.compile(r":\d+(?:-\d+)?$")


def declared(configuration: config.Config) -> list[dict]:
    """The sections this project declares, `[]` being its stated absence."""
    return list(configuration.get(config.DECLARED) or [])


def sections_of(body: str) -> dict[str, list[str]]:
    """Each heading's text, folded, mapped to the lines under it.

    A section runs to the next heading at its own level or above. ⛔ Lines inside
    a fenced block are content and never headings: a quoted shell comment opens
    with the same character an ATX heading does.
    """
    found: dict[str, list[str]] = {}
    open_sections: list[tuple[int, str]] = []
    fenced = None
    for line in body.splitlines():
        fence = FENCE.match(line)
        if fence:
            marker = fence.group(1)[0]
            fenced = None if fenced == marker else (fenced or marker)
        heading = None if fenced or fence else HEADING.match(line)
        if heading:
            level = len(heading.group(1))
            open_sections = [(lvl, key) for lvl, key in open_sections if lvl < level]
            key = heading.group(2).strip().casefold()
            found.setdefault(key, [])
            open_sections.append((level, key))
            continue
        for _level, key in open_sections:
            found[key].append(line)
    return found


def _content(lines: list[str]) -> list[str]:
    return [line for line in lines if not NOISE.match(line)]


def cited_files(lines: list[str]) -> list[str]:
    """Every path a section names in backticks, in the order it names them.

    A path is a token with a separator or an extension; a backticked word with
    neither is code or a key and not a file.
    """
    files: list[str] = []
    for line in lines:
        for token in CITED.findall(line):
            path = LINE_REFERENCE.sub("", token)
            if ("/" in path or re.search(r"\.\w+$", path)) and path not in files:
                files.append(path)
    return files


def _outside(path: str) -> bool:
    return os.path.isabs(path) or ".." in path.replace("\\", "/").split("/")


def hold(configuration: config.Config, body: str, code_root: str | None = None) -> list[dict]:
    """Every problem a body has against the declared sections; `[]` where it holds."""
    found = sections_of(body)
    problems: list[dict] = []

    def problem(entry: dict, what: str) -> None:
        problems.append({"section": entry["name"], "heading": entry["heading"],
                         "problem": what})

    for entry in declared(configuration):
        key = entry["heading"].strip().casefold()
        if key not in found:
            if entry["required"]:
                problem(entry, "required, and the body does not carry it")
            continue
        content = _content(found[key])
        if not content:
            problem(entry, "carried with nothing under it, which reads as answered")
            continue
        if entry["source"] != "code":
            continue
        files = cited_files(content)
        if not files:
            problem(entry, "sourced from the code and names no file it read, as a "
                           "repository-relative path in backticks")
            continue
        if code_root is None:
            continue
        for path in files:
            if _outside(path):
                problem(entry, f"names {path!r}, which is not a repository-relative path")
            elif not os.path.exists(os.path.join(code_root, path)):
                problem(entry, f"names {path!r}, which is not in {code_root}")
    return problems


# --- § 3's append mode -----------------------------------------------------

APPEND = "append"


def duplicate_mode(configuration: config.Config) -> str:
    """§ 3's `tracker.duplicate`, with the default the reader applies."""
    return str(configuration.get("tracker.duplicate"))


def addendum_heading(configuration: config.Config) -> str:
    """§ 4.4's `sections.addendum`, carrying `{date}` once by the reader's rule."""
    return str(configuration.get(config.ADDENDUM))


def _level(body: str) -> int:
    """The level of the body's first heading outside a fence, `##` where it has none."""
    fenced = None
    for line in body.splitlines():
        fence = FENCE.match(line)
        if fence:
            marker = fence.group(1)[0]
            fenced = None if fenced == marker else (fenced or marker)
            continue
        heading = None if fenced else HEADING.match(line)
        if heading:
            return len(heading.group(1))
    return 2


def _spaced(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def _dated(configuration: config.Config, line: str) -> str | None:
    """The date a line carries where it is the project's dated heading, else None.

    Matched as § 4.4 matches a heading: the text alone, at any level and in any
    case, a run of spaces being formatting rather than wording.
    """
    heading = HEADING.match(line)
    if not heading:
        return None
    before, after = addendum_heading(configuration).split(config.DATE_SLOT)
    pattern = (re.escape(_spaced(before).lstrip()) + r"(\d{4}-\d{2}-\d{2})"
               + re.escape(_spaced(after).rstrip()))
    found = re.fullmatch(pattern, _spaced(heading.group(2).strip()), re.IGNORECASE)
    return found.group(1) if found else None


def compose(configuration: config.Config, before: str, material: str, date: str) -> str:
    """The existing body byte for byte, then one dated section carrying `material`."""
    heading = addendum_heading(configuration).replace(config.DATE_SLOT, date)
    if not before or before.endswith("\n\n"):
        gap = ""
    elif before.endswith("\n"):
        gap = "\n"
    else:
        gap = "\n\n"
    return f"{before}{gap}{'#' * _level(before)} {heading}\n\n{material.strip()}\n"


def hold_appended(configuration: config.Config, before: str, after: str) -> list[str]:
    """Every problem `after` has as `before` with one dated section added; `[]` holds."""
    if not after.startswith(before):
        return ["the text before the dated section is not the existing body exactly, "
                "so what was accepted has changed"]
    lines = after[len(before):].splitlines()
    content = [line for line in lines if not NOISE.match(line)]
    if not content:
        return ["nothing follows the existing body, so no dated section was added"]
    problems: list[str] = []
    if _dated(configuration, content[0]) is None:
        problems.append(f"what follows the existing body opens with {content[0].strip()!r}, "
                        "which is not the project's dated heading")
    dated = [i for i, line in enumerate(lines) if _dated(configuration, line) is not None]
    if len(dated) > 1:
        problems.append(f"{len(dated)} dated sections follow the existing body, and one "
                        "filing adds one")
    for index in dated[:1]:
        stamp = _dated(configuration, lines[index])
        try:
            datetime.date.fromisoformat(stamp)
        except ValueError:
            problems.append(f"the heading's date {stamp!r} is not a calendar date")
        if not [line for line in lines[index + 1:] if not NOISE.match(line)]:
            problems.append("the dated section has nothing under it, which reads as "
                            "material added")
    return problems


# --- the suite -------------------------------------------------------------


def _a_project(tmp: str, entries=None, addendum=None) -> config.Config:
    """A loadable configuration in a tree of its own, declaring `entries` or nothing.

    Built from an example rather than written here, for the reason the sibling
    consumers' fixtures are: a configuration the shared reader would refuse makes
    every answer below an answer about nothing.
    """
    import yaml

    with open(os.path.join(config.EXAMPLES, "github-issues.yaml"), encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    data["roots"] = {"code": "."}
    template = data.setdefault("work_item", {}).setdefault("template", {})
    if entries is None:
        template.pop("declared", None)
    else:
        template["declared"] = entries
    if addendum is not None:
        data.setdefault("tracker", {})["duplicate"] = "append"
        template.setdefault("sections", {})["addendum"] = addendum
    os.makedirs(os.path.join(tmp, ".claude"), exist_ok=True)
    with open(os.path.join(tmp, config.CONFIG_PATH), "w", encoding="utf-8") as handle:
        handle.write(yaml.safe_dump(data, allow_unicode=True))
    return config.load(tmp)


A_PLAN = {
    "name": "plan",
    "heading": "Implementation plan",
    "fills": "the steps the work takes, read off a scan of the code",
    "source": "code",
    "required": True,
}
A_NOTE = {
    "name": "notes",
    "heading": "Notes from the requester",
    "fills": "anything the person added that is not the outcome",
    "source": "request",
    "required": False,
}

A_BODY = """### Outcome

Something is possible.

### Implementation plan

1. Change the reader, read from `lib/reader.py:40-60`.
2. Then the consumer in `lib/consumer.py`.

### Acceptance check

- It holds.
"""


def self_test() -> int:  # noqa: C901 -- one assertion per property, read in order
    """Assert every answer against planted bodies, then report this project's own."""
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

    def problems_of(project, body, root=None) -> list[str]:
        return [each["problem"] for each in hold(project, body, root)]

    print("the facts this module reads rather than carries")
    check(
        "the reader this module loaded is the one beside it",
        os.path.dirname(os.path.abspath(config.__file__)) == HERE,
        f"imported {config.__file__}, which is not in this tree",
    )

    with tempfile.TemporaryDirectory() as tmp:
        project = _a_project(tmp, [A_PLAN, A_NOTE])
        check("a project's declared sections are read through the shared reader",
              [each["name"] for each in declared(project)] == ["plan", "notes"],
              str(declared(project)))

        print()
        print("a body holding every declared section")
        check("a body carrying the required section, filled and citing files, holds",
              problems_of(project, A_BODY) == [], str(hold(project, A_BODY)))
        check("an optional section the body leaves out is not a problem",
              problems_of(project, A_BODY) == [])
        check("the heading is matched at another level and in another case",
              problems_of(project, A_BODY.replace("### Implementation plan",
                                                  "## IMPLEMENTATION Plan")) == [])

        print()
        print("planted violations, each refused")
        missing = A_BODY.replace("### Implementation plan", "### Something else")
        check("a required section the body does not carry is refused",
              problems_of(project, missing) == ["required, and the body does not carry it"],
              str(hold(project, missing)))
        empty = "### Implementation plan\n\n---\n\n### Acceptance check\n\n- It holds.\n"
        check("a required section with nothing but a rule under it is refused",
              any("nothing under it" in p for p in problems_of(project, empty)),
              str(hold(project, empty)))
        empty_note = A_BODY + "\n### Notes from the requester\n\n<!-- none -->\n"
        check("an optional section carried empty is refused too",
              problems_of(project, empty_note)
              == ["carried with nothing under it, which reads as answered"],
              str(hold(project, empty_note)))
        uncited = A_BODY.replace("`lib/reader.py:40-60`", "the reader").replace(
            "`lib/consumer.py`", "the consumer")
        check("a code-sourced section naming no file is refused",
              any("names no file" in p for p in problems_of(project, uncited)),
              str(hold(project, uncited)))
        keyword = A_BODY.replace("`lib/reader.py:40-60`", "`declared`").replace(
            "`lib/consumer.py`", "`hold`")
        check("a backticked word with no separator or extension is not a file",
              any("names no file" in p for p in problems_of(project, keyword)),
              str(hold(project, keyword)))
        request_sourced = _a_project(os.path.join(tmp, "r"),
                                     [{**A_PLAN, "source": "request"}])
        check("a request-sourced section owes no file",
              problems_of(request_sourced, uncited) == [], str(hold(request_sourced, uncited)))
        nested = A_BODY.replace("2. Then", "#### Detail\n\n2. Then")
        check("a deeper heading inside a section stays part of it",
              problems_of(project, nested) == [], str(hold(project, nested)))
        fenced = ("### Implementation plan\n\n```sh\n# a comment, not a heading\n```\n"
                  "Read `lib/reader.py`.\n")
        check("a line inside a fenced block is not read as a heading",
              problems_of(project, fenced) == [], str(hold(project, fenced)))
        sibling = A_BODY.replace("1. Change", "### Acceptance check\n\n1. Change")
        check("a sibling heading closes the section, so content after it is not the section's",
              problems_of(project, sibling)
              == ["carried with nothing under it, which reads as answered"],
              str(hold(project, sibling)))

        print()
        print("files named, checked against a code root where one is given")
        root = os.path.join(tmp, "code")
        os.makedirs(os.path.join(root, "lib"))
        for name in ("reader.py", "consumer.py"):
            with open(os.path.join(root, "lib", name), "w", encoding="utf-8") as handle:
                handle.write("")
        check("files present in the code root hold",
              problems_of(project, A_BODY, root) == [], str(hold(project, A_BODY, root)))
        os.remove(os.path.join(root, "lib", "consumer.py"))
        check("a named file absent from the code root is refused",
              problems_of(project, A_BODY, root)
              == [f"names 'lib/consumer.py', which is not in {root}"],
              str(hold(project, A_BODY, root)))
        escaping = A_BODY.replace("`lib/consumer.py`", "`../elsewhere/secret.py`")
        check("a path climbing out of the code root is refused",
              any("not a repository-relative path" in p
                  for p in problems_of(project, escaping, root)),
              str(hold(project, escaping, root)))
        check("without a code root, presence is not asked",
              problems_of(project, A_BODY) == [])

        print()
        print("the command line")
        body_file = os.path.join(tmp, "body.md")
        with open(body_file, "w", encoding="utf-8") as handle:
            handle.write(A_BODY)
        check("a holding body exits 0",
              main(["check", "--skills-root", tmp, "--body-file", body_file]) == 0)
        with open(body_file, "w", encoding="utf-8") as handle:
            handle.write(missing)
        check("a body that does not hold exits 1",
              main(["check", "--skills-root", tmp, "--body-file", body_file]) == 1)
        check("a body that cannot be read exits 2 rather than reading as empty",
              main(["check", "--skills-root", tmp, "--body-file",
                    os.path.join(tmp, "absent.md")]) == 2)
        bare = os.path.join(tmp, "bare")
        _a_project(bare)
        check("a project declaring none exits 3 and files as before",
              main(["check", "--skills-root", bare, "--body-file", body_file])
              == NOTHING_DECLARED)
        check("and its declared list reads as empty rather than absent",
              declared(config.load(bare)) == [])

        print()
        print("§ 3's append mode, composed and held")
        appending = _a_project(os.path.join(tmp, "a"), addendum="Addendum of {date}")
        check("a project stating nothing rewrites, the reader's default",
              duplicate_mode(config.load(bare)) == "rewrite",
              duplicate_mode(config.load(bare)))
        check("a project stating append reads as append", duplicate_mode(appending) == APPEND)
        material = "#### User story\n\nAs a requester I see the new case.\n"
        composed = compose(appending, A_BODY, material, "2026-11-27")
        check("the composed body opens with the existing body byte for byte",
              composed.startswith(A_BODY), composed)
        check("the dated section sits at the level of the body's first heading",
              "\n### Addendum of 2026-11-27\n" in composed, composed)
        check("the composed body holds", hold_appended(appending, A_BODY, composed) == [],
              str(hold_appended(appending, A_BODY, composed)))
        unterminated = "Accepted text with no heading and no newline"
        joined = compose(appending, unterminated, material, "2026-11-27")
        check("a body with no heading and no final newline gains a `##` section after a gap",
              joined == unterminated + "\n\n## Addendum of 2026-11-27\n\n" + material.strip()
              + "\n" and hold_appended(appending, unterminated, joined) == [], repr(joined))
        check("the heading is matched in another case and at another level",
              hold_appended(appending, A_BODY, A_BODY + "\n# ADDENDUM  of 2026-11-27\n\nNew.\n")
              == [])

        print()
        print("planted violations of the append mode, each refused")
        edited = composed.replace("Something is possible.", "Something else is possible.")
        check("an existing body changed by one word is refused",
              any("not the existing body exactly" in p
                  for p in hold_appended(appending, A_BODY, edited)),
              str(hold_appended(appending, A_BODY, edited)))
        trimmed = A_BODY + "  \n" + composed[len(A_BODY):]
        check("whitespace added to the end of the existing body is refused too",
              any("not the existing body exactly" in p
                  for p in hold_appended(appending, A_BODY + "\n", trimmed)),
              str(hold_appended(appending, A_BODY + "\n", trimmed)))
        check("an existing body with nothing added is refused",
              hold_appended(appending, A_BODY, A_BODY + "\n\n")
              == ["nothing follows the existing body, so no dated section was added"])
        undated = A_BODY + "\n### Addendum\n\nNew.\n"
        check("a section under the wording with no date is refused",
              any("not the project's dated heading" in p
                  for p in hold_appended(appending, A_BODY, undated)),
              str(hold_appended(appending, A_BODY, undated)))
        reworded = A_BODY + "\n### Update 2026-11-27\n\nNew.\n"
        check("a dated section under another wording is refused",
              any("not the project's dated heading" in p
                  for p in hold_appended(appending, A_BODY, reworded)),
              str(hold_appended(appending, A_BODY, reworded)))
        twice = composed + "\n### Addendum of 2026-11-28\n\nMore.\n"
        check("two dated sections from one filing are refused",
              any("2 dated sections" in p for p in hold_appended(appending, A_BODY, twice)),
              str(hold_appended(appending, A_BODY, twice)))
        hollow = A_BODY + "\n### Addendum of 2026-11-27\n\n---\n"
        check("a dated section with nothing under it is refused",
              any("nothing under it" in p for p in hold_appended(appending, A_BODY, hollow)),
              str(hold_appended(appending, A_BODY, hollow)))
        impossible = A_BODY + "\n### Addendum of 2026-13-45\n\nNew.\n"
        check("a heading whose date is no calendar date is refused",
              any("not a calendar date" in p
                  for p in hold_appended(appending, A_BODY, impossible)),
              str(hold_appended(appending, A_BODY, impossible)))
        loose = A_BODY + "\nA paragraph first.\n\n### Addendum of 2026-11-27\n\nNew.\n"
        check("material written before the dated heading is refused",
              any("opens with 'A paragraph first.'" in p
                  for p in hold_appended(appending, A_BODY, loose)),
              str(hold_appended(appending, A_BODY, loose)))

        print()
        print("the append mode at the command line")
        before_file = os.path.join(tmp, "before.md")
        material_file = os.path.join(tmp, "material.md")
        after_file = os.path.join(tmp, "after.md")
        for path, text in ((before_file, A_BODY), (material_file, material),
                           (after_file, composed)):
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(text)
        root_a = os.path.join(tmp, "a")
        check("a composed body that holds exits 0",
              main(["appended", "--skills-root", root_a, "--before", before_file,
                    "--after", after_file]) == 0)
        with open(after_file, "w", encoding="utf-8") as handle:
            handle.write(edited)
        check("an edited existing body exits 1",
              main(["appended", "--skills-root", root_a, "--before", before_file,
                    "--after", after_file]) == 1)
        check("a date that is no calendar date exits 2 and composes nothing",
              main(["addendum", "--skills-root", root_a, "--before", before_file,
                    "--material", material_file, "--date", "2026-02-30"]) == 2)
        check("a compact date some interpreters read as ISO exits 2 too",
              main(["addendum", "--skills-root", root_a, "--before", before_file,
                    "--material", material_file, "--date", "20261127"]) == 2)
        check("a rewriting project exits 3 for either command",
              main(["addendum", "--skills-root", bare, "--before", before_file,
                    "--material", material_file]) == NOTHING_DECLARED
              and main(["appended", "--skills-root", bare, "--before", before_file,
                        "--after", after_file]) == NOTHING_DECLARED)

    print()
    print("this project's own declaration, read rather than assumed")
    live = config.load(config.REPO_ROOT)
    check("the live configuration loads and its declared list is a list",
          isinstance(declared(live), list))

    print()
    check(
        "this run executed assertions rather than reporting a green nothing",
        ran > 1,
        "a suite that executes no case and exits zero is the degradation every "
        "check here is written against",
    )
    print()
    if failures:
        print(f"{len(failures)} check(s) failed:")
        for label in failures:
            print(f"  - {label}")
        return 1
    print(f"every check passed ({ran} assertions).")
    return 0


# --- the command line ------------------------------------------------------


def _read(path: str) -> str | None:
    try:
        with open(path, encoding="utf-8", newline="") as handle:
            return handle.read()
    except OSError as exc:
        print(f"{path} could not be read: {exc}", file=sys.stderr)
        return None


def _append_command(configuration: config.Config, args) -> int:
    """`addendum` and `appended`: § 3's append mode at a command line."""
    mode = duplicate_mode(configuration)
    if mode != APPEND:
        print(json.dumps({
            "mode": mode, "holds": None, "problems": [],
            "report": [f"This project states `tracker.duplicate: {mode}`, so a confirmed "
                       "duplicate is rewritten and gains no dated section to compose or "
                       "hold (§ 3)."],
        }, indent=2, ensure_ascii=False))
        return NOTHING_DECLARED
    before = _read(args.before)
    if before is None:
        return 2
    if args.what == "addendum":
        material = _read(args.material)
        if material is None:
            return 2
        date = args.date or datetime.date.today().isoformat()
        # ⛔ The shape first: from 3.11 `fromisoformat` also takes `20261127`,
        # which would write a heading `appended` refuses.
        try:
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
                raise ValueError(date)
            datetime.date.fromisoformat(date)
        except ValueError:
            print(f"--date {date!r} is not a YYYY-MM-DD calendar date", file=sys.stderr)
            return 2
        if not material.strip():
            print("the material is empty, and a dated section with nothing under it reads "
                  "as material added (§ 3)", file=sys.stderr)
            return 1
        sys.stdout.write(compose(configuration, before, material, date))
        return 0
    after = _read(args.after)
    if after is None:
        return 2
    problems = hold_appended(configuration, before, after)
    print(json.dumps({"mode": mode, "holds": not problems, "problems": problems},
                     indent=2, ensure_ascii=False))
    return 1 if problems else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Hold a work item's body to the sections this project declares.",
    )
    parser.add_argument("--skills-root", default=".")
    parser.add_argument("--self-test", action="store_true")
    sub = parser.add_subparsers(dest="what")
    reading = sub.add_parser("check", help="hold a body to the declared sections")
    reading.add_argument("--skills-root", default=".")
    reading.add_argument("--body-file", required=True)
    reading.add_argument("--code-root", default=None,
                         help="where a code-sourced section's files must exist")
    composing = sub.add_parser("addendum", help="a duplicate's body with its dated section")
    composing.add_argument("--skills-root", default=".")
    composing.add_argument("--before", required=True, help="the existing body, as read")
    composing.add_argument("--material", required=True, help="the new material")
    composing.add_argument("--date", default=None, help="YYYY-MM-DD; today where omitted")
    holding = sub.add_parser("appended", help="hold a duplicate's body to the existing one")
    holding.add_argument("--skills-root", default=".")
    holding.add_argument("--before", required=True, help="the existing body, as read")
    holding.add_argument("--after", required=True, help="the body about to be written")

    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()

    try:
        configuration = config.load(args.skills_root)
    except (config.ConfigError, OSError) as exc:
        print(exc, file=sys.stderr)
        return 2

    if args.what in ("addendum", "appended"):
        return _append_command(configuration, args)

    entries = declared(configuration)
    if args.what != "check":
        print(json.dumps({"declared": entries}, indent=2, ensure_ascii=False))
        return 0 if entries else NOTHING_DECLARED

    if not entries:
        print(json.dumps({
            "holds": None, "problems": [],
            "report": ["This project declares no section beyond the procedure's "
                       "(`work_item.template.declared: []`), so a body is held to "
                       "nothing here and files as it did before the key existed (§ 4.4)."],
        }, indent=2, ensure_ascii=False))
        return NOTHING_DECLARED
    try:
        with open(args.body_file, encoding="utf-8") as handle:
            body = handle.read()
    except OSError as exc:
        print(f"the body could not be read: {exc}", file=sys.stderr)
        return 2
    problems = hold(configuration, body, args.code_root)
    print(json.dumps({"holds": not problems, "problems": problems},
                     indent=2, ensure_ascii=False))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
