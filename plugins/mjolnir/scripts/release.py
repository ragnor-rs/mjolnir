#!/usr/bin/env python3
"""The files a version is written in, read and edited without knowing the stack.

`release` (§ 34) is one fact with one reader, and ⛔ **the reader is this module
rather than the role**: a role that knew a build file's syntax would be a role
per stack, which is the thing this toolkit is not. So the skill carries no
version pattern, no file path and no build-file syntax at all, and asks here
instead.

⛔ **It states no version scheme, no tag format, no registry and no publishing
command.** Each is `../config/schema.md § What the procedure models`'s middle
column read against this role; what this module owns is the part none of its
readers should perform twice:

  * **Reading** the version each file currently carries, out of the `version`
    capture of that file's own pattern -- which is the only thing either this
    module or the role ever learns about a project's scheme.
  * **The plan**: what every edit would do, with no file written. A file that is
    missing and marked optional, a file that is missing and is not, a pattern
    that matches nothing, a pattern that matches twice: each is answered here.
  * **Applying** the plan, ⛔ **all of it or none of it**. A release with half
    its files bumped is worse than a release not cut, because the half that
    moved is what every later reader believes -- so nothing is written until
    every edit the plan holds has been established against the file on disk.
  * **The changelog's refusal**, where the project states CI owns it: reported
    as a refusal naming the file, never as a file quietly skipped.

⚠️ **What it does not decide is the version.** There is no rule here for what the
next version of anything is: the increment depends on what landed, which is a
judgement this module has no input for. The version is handed in, and what this
module answers is what is written now -- so a caller can say which version it is
replacing rather than only which one it wrote.

⛔ **And it writes nothing outside the files the facet names.** No tag, no
commit, no push, no publish: each is an act somebody else performs, and two of
them are irreversible in a way this module has no standing to be.

Usage:
    release.py [--skills-root DIR]        what this project states, and the
                                          version each of its files carries now
    release.py plan --version X.Y.Z       every edit, with nothing written
    release.py apply --version X.Y.Z      the same edits, performed together
    release.py --self-test                assert every answer against planted
                                          trees, then report this project's own

Exit status, and ⛔ **four values rather than two**: 0 the answer was produced,
1 the plan cannot be carried out and names why, 2 the configuration could not be
read, 3 this project states that no file carries a version. ⚠️ The last is
§ 11's rule at a command line -- *no answer* collapsed into 0 reads as a release
that was cut, and into 1 as a project whose files are all wrong.

⚠️ **A project stating no configuration at all reaches 3 as well**, and that is a
deliberate collapse rather than an oversight: what a consumer asks is whether
there is a file to edit, and there is not either way. What separates them is the
report, which names which of the two it met -- and the unconfigured arm names the
file to write, by § 7's rule that whoever invokes a role by name is owed that
answer.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import config  # noqa: E402 -- the one reader of the surface

# ⛔ The exit status this module reserves for the project's stated absence, named
# for the reason `title_form.py` names its own: a reader that compared against a
# literal would be comparing against a number, and the number is the least
# readable part of the contract it carries.
NO_FILES = 3

# What a `replace` writes the version in as, and ⛔ **the only placeholder this
# module knows**. A project's replacement states it literally, which is what
# makes one form serve `version = "{version}"` and `Latest: **v{version}` alike.
#
# ⚠️ Substituted by a plain replacement rather than through a format call: the
# replacement is a project's own string and may legitimately carry a brace --
# every build file that declares a map does -- and a format call would read those
# as fields of its own and fail on a correct configuration.
PLACEHOLDER = "{version}"

# § 34's capture, read through the reader rather than spelled again here: the
# configuration is refused at the load for a pattern that carries no such
# capture, so what this module does with the name is read a match group by it.
VERSION_CAPTURE = config.VERSION_CAPTURE

# The heading level a changelog's own entries sit at, and ⛔ **the one shape this
# module imposes on a file rather than reading off the facet.** It is stated here
# because § 34 declares no key for it and the reason is measured: the copy this
# facet came from keeps its entries as `## <version>` sections in document order,
# newest first, and a facet key for the level would be a facet invented from one
# observation rather than found in several.
#
# ⚠️ So the insert is positional and not structural: the entry goes above the
# first line that looks like an entry of the same level, or at the head of the
# file where there is none. ⛔ What that cannot do is merge into an entry that is
# already there, which is reported rather than attempted -- a changelog already
# carrying the version being cut is a release somebody started and this module
# has no standing to finish.
ENTRY_LEVEL = "## "


def _entry_heading(version: str) -> str:
    return f"{ENTRY_LEVEL}{version}"


def _read(path: str) -> str | None:
    """A file's text, or `None` where it is not there.

    ⛔ `None` for absence alone. A file that is there and cannot be read is an
    error this module does not catch: a release that treated an unreadable file
    as a missing one would skip whichever file a permission happens to be wrong
    on, which is § 2's absence-of-signal rule arriving at a filesystem.
    """
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def _plan_entry(root: str, entry: dict, version: str) -> dict:
    """What one file's edit would do, with nothing written.

    ⛔ Every field of the answer is stated whether or not the edit can be made,
    which is § 11's rule inside one record: a caller reading `"holds": false`
    needs to know *which* file and *why* in the same breath, and a record that
    dropped its own path on the failing arm would name the problem and not the
    subject.
    """
    optional = bool(entry.get("optional", False))
    answer = {
        "path": entry["path"],
        "kind": entry["kind"],
        "optional": optional,
        "holds": False,
        "current": None,
        "because": None,
    }
    full = os.path.join(root, entry["path"])
    text = _read(full)
    if text is None:
        # ⛔ The flag's whole purpose, and the direction § 34 states: a file
        # marked optional and missing is **not** an error, and one that is not
        # marked stops the release with the file named.
        answer["holds"] = optional
        answer["because"] = (
            "not in this tree, and the entry marks it optional, so it is skipped"
            if optional
            else "not in this tree, and the entry does not mark it optional"
        )
        answer["skipped"] = optional
        return answer

    if entry["kind"] == "changelog":
        heading = _entry_heading(version)
        if heading in text:
            answer["because"] = (
                f"already carries an entry for {version}, which is a release "
                "somebody started; nothing here merges into it"
            )
            return answer
        answer["holds"] = True
        answer["because"] = f"a {heading!r} section is inserted at the head of the entries"
        answer["current"] = _newest_entry(text)
        return answer

    # ⚠️ Compiled here rather than carried from the load: the reader has already
    # refused a pattern that will not compile, so this is the same expression
    # read again rather than a second rule about it.
    pattern = re.compile(entry["pattern"])
    found = list(pattern.finditer(text))
    if not found:
        answer["because"] = (
            "the pattern this entry states matches nothing in it, so there is no "
            "span to replace"
        )
        return answer
    # ⛔ Every match, and a disagreement between them is a stop. Two spans
    # carrying two different versions is a file this module cannot say the
    # current version of, and picking the first would report a version the file
    # does not have.
    carried = sorted({match.group(VERSION_CAPTURE) for match in found})
    if len(carried) > 1:
        answer["because"] = (
            f"carries {', '.join(carried)} in {len(found)} places, so there is no "
            "one version this file is at"
        )
        return answer
    answer["holds"] = True
    answer["current"] = carried[0]
    answer["matches"] = len(found)
    answer["because"] = (
        f"{len(found)} span(s) carrying {carried[0]} become the stated replacement"
    )
    return answer


def _newest_entry(text: str) -> str | None:
    """The version of a changelog's first entry, or `None` where it has none."""
    for line in text.splitlines():
        if line.startswith(ENTRY_LEVEL):
            return line[len(ENTRY_LEVEL):].strip() or None
    return None


def _applied(entry: dict, text: str, version: str) -> str:
    """One file's new text. Only ever called for an entry whose plan holds."""
    if entry["kind"] == "changelog":
        heading = _entry_heading(version)
        lines = text.splitlines(keepends=True)
        at = next(
            (i for i, line in enumerate(lines) if line.startswith(ENTRY_LEVEL)),
            len(lines),
        )
        # ⚠️ A trailing newline on the inserted block in both positions, and the
        # blank line after it: inserted at the head of a file whose first line is
        # an entry, the heading would otherwise run into it.
        return "".join(lines[:at] + [f"{heading}\n\n"] + lines[at:])
    pattern = re.compile(entry["pattern"])
    replacement = entry["replace"].replace(PLACEHOLDER, version)
    # ⛔ A plain string and never a template: `re.sub` reads a backslash in its
    # replacement as a group reference, and a project's own replacement may
    # legitimately carry one. Measured on the surface's own example, whose
    # replacement is `version = "{version}"` and whose pattern carries two.
    return pattern.sub(lambda _match: replacement, text)


def plan(configuration: config.Config, version: str) -> dict | None:
    """Every edit this release would make, with nothing written, or `None`.

    `None` is the project's stated absence (§ 34) and never an empty plan: no
    file here carries a version, so there is nothing to edit rather than nothing
    to do.
    """
    stated = configuration.release()
    if stated is None:
        return None
    root = configuration.code_root()
    files = [_plan_entry(root, entry, version) for entry in stated["files"]]
    report = []
    # ⛔ Said rather than skipped, which § 34 makes the rule rather than a
    # courtesy: a release whose report does not mention the changelog reads as a
    # release that wrote one.
    if stated["changelog_ci_owned"]:
        report.append(
            "This project states that CI owns the changelog, so this role writes "
            "no changelog entry. ⛔ Not a file skipped: a role that wrote it "
            "anyway would produce a conflict on every release (§ 34)."
        )
    if stated["publishes_packages"]:
        report.append(
            "This project publishes packages, so the version is spent for ever "
            "once it is published and the go is the person's, asked for this "
            "release and no earlier one (§ 34)."
        )
    blocked = [entry for entry in files if not entry["holds"]]
    for entry in blocked:
        report.append(f"{entry['path']}: {entry['because']}")
    return {
        "version": version,
        "code_root": root,
        "publishes_packages": stated["publishes_packages"],
        "changelog_ci_owned": stated["changelog_ci_owned"],
        "files": files,
        # ⛔ The whole plan holds or it does not, and the field says which before
        # a caller reads a single entry: an apply that wrote the files it could
        # is the half-bumped tree this module exists against.
        "holds": not blocked,
        "report": report,
    }


def apply(configuration: config.Config, version: str) -> dict | None:
    """The plan, performed together. `None` where no file carries a version.

    ⛔ **Nothing is written unless every edit holds**, and the ordering is the
    rule rather than an implementation detail: the whole plan is established
    against the files on disk, each file's new text is composed in memory, and
    only then is anything written.

    ⚠️ **What this does not promise is atomicity against a crash.** The write
    loop can be interrupted between two files, and a report saying so is the
    honest answer rather than a claim a filesystem does not support: what is
    closed is the case this module can close -- a plan that was never going to
    work being carried out part of the way.
    """
    answer = plan(configuration, version)
    if answer is None:
        return None
    answer["written"] = []
    if not answer["holds"]:
        answer["report"].insert(
            0,
            "Nothing was written: the plan does not hold, and a release with half "
            "its files bumped is worse than one not cut (§ 34).",
        )
        return answer
    root = answer["code_root"]
    stated = {entry["path"]: entry for entry in configuration.release()["files"]}
    composed = []
    for entry in answer["files"]:
        if entry.get("skipped"):
            continue
        full = os.path.join(root, entry["path"])
        text = _read(full)
        if text is None:
            # ⚠️ Reachable only where the tree moved under this run, between the
            # plan and the write. Reported as that rather than silently skipped.
            answer["holds"] = False
            answer["report"].insert(
                0,
                f"{entry['path']} was there when the plan was taken and is not "
                "there now, so nothing was written.",
            )
            return answer
        composed.append((full, _applied(stated[entry["path"]], text, version)))
    for full, text in composed:
        with open(full, "w", encoding="utf-8") as handle:
            handle.write(text)
        answer["written"].append(os.path.relpath(full, root))
    return answer


def _report(configuration: config.Config) -> dict:
    """What this project states, and what each of its files carries now.

    ⚠️ The version read out is every file's own rather than the project's: a
    file that disagrees with its siblings is the fact a caller needs before it
    chooses a version, and a single answer here would hide it.
    """
    stated = configuration.release()
    if stated is None:
        return {
            "release": None,
            "report": [
                line
                for line in configuration.unavailable()
                if "release.carrier" in line
            ]
            or [
                "This project states that no file carries a version "
                "(`release.carrier: none`), so there is nothing to cut (§ 34)."
            ],
        }
    root = configuration.code_root()
    files = []
    for entry in stated["files"]:
        # ⚠️ The version is read through the plan with a placeholder that is
        # written nowhere: this arm reads and never writes, and a second reader
        # of the same patterns would be a second rule about them.
        reading = _plan_entry(root, entry, "0.0.0")
        files.append({
            "path": reading["path"],
            "kind": reading["kind"],
            "optional": reading["optional"],
            "current": reading["current"],
            "readable": reading["holds"],
            "because": reading["because"],
        })
    return {
        "release": {
            "publishes_packages": stated["publishes_packages"],
            "changelog_ci_owned": stated["changelog_ci_owned"],
            "files": files,
        },
        "report": [],
    }


# --- the suite -------------------------------------------------------------


def _a_tree(files: dict[str, str]) -> str:
    """A tree carrying the files named, for a plant to be taken against."""
    root = tempfile.mkdtemp(prefix="mjolnir-release-")
    for name, text in files.items():
        full = os.path.join(root, name)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as handle:
            handle.write(text)
    return root


class _Stated:
    """A project's stated facet and code root, with no configuration file.

    ⛔ A stand-in at the accessor seam rather than at the reader's: what this
    module reads is `release()` and `code_root()`, so a fake answering those two
    replaces exactly what it has to and leaves every rule the reader performs --
    the capture, the per-kind keys, the booleans -- where it is. ⚠️ Which is why
    the suite below also loads each planted facet **through the reader**, in the
    arm that asserts a configuration this module accepts is one the reader does.
    """

    def __init__(self, root: str, **facet):
        self._root = root
        self._facet = facet

    def release(self):
        return dict(self._facet) if self._facet else None

    def code_root(self):
        return self._root

    def unavailable(self):
        return []


def self_test() -> int:
    failures = []

    def check(label: str, held: bool, detail: str = "") -> None:
        print(f"  {'ok  ' if held else 'FAIL'}  {label}" + (
            "" if held else f": {detail}"))
        if not held:
            failures.append(label)

    def a_facet(**overrides):
        facet = {
            "files": [{
                "path": "build.txt",
                "kind": "regex",
                "pattern": f'version = "(?P<{VERSION_CAPTURE}>[0-9.]+)"',
                "replace": 'version = "{version}"',
            }],
            "publishes_packages": False,
            "changelog_ci_owned": False,
        }
        facet.update(overrides)
        return facet

    print("What a version is read out of, and the one thing this module learns:")
    root = _a_tree({"build.txt": 'name = "a"\nversion = "1.2.3"\n'})
    answer = plan(_Stated(root, **a_facet()), "1.3.0")
    check("the plan holds for a file the pattern matches", answer["holds"],
          f"reported {answer['report']!r}")
    check("and it reads the version the file carries now",
          answer["files"][0]["current"] == "1.2.3",
          f"read {answer['files'][0]['current']!r}")
    check("nothing is written by a plan",
          _read(os.path.join(root, "build.txt")) == 'name = "a"\nversion = "1.2.3"\n',
          "the plan wrote the file")

    applied = apply(_Stated(root, **a_facet()), "1.3.0")
    check("applying it writes the version handed in", applied["holds"]
          and _read(os.path.join(root, "build.txt")) == 'name = "a"\nversion = "1.3.0"\n',
          f"left {_read(os.path.join(root, 'build.txt'))!r}")
    check("and the report names every file it wrote",
          applied["written"] == ["build.txt"], f"named {applied['written']!r}")

    # ⛔ The replacement is a project's own string and may carry a brace or a
    # backslash. Both are planted, each having a mechanism that would eat it: a
    # format call reads the first as a field, and `re.sub` reads the second as a
    # group reference.
    root = _a_tree({"build.txt": 'v = "1.0.0"\n'})
    applied = apply(_Stated(root, **a_facet(files=[{
        "path": "build.txt",
        "kind": "regex",
        "pattern": f'v = "(?P<{VERSION_CAPTURE}>[0-9.]+)"',
        "replace": 'v = "{version}" # {"a": 1} \\1',
    }])), "2.0.0")
    check("a replacement carrying a brace and a backslash is written literally",
          _read(os.path.join(root, "build.txt")) == 'v = "2.0.0" # {"a": 1} \\1\n',
          f"left {_read(os.path.join(root, 'build.txt'))!r}")

    print("\nThe file marked optional, which is the arm the flag exists for:")
    root = _a_tree({"build.txt": 'version = "1.0.0"\n'})
    facet = a_facet(files=a_facet()["files"] + [
        {"path": "README.md", "kind": "regex",
         "pattern": f"v(?P<{VERSION_CAPTURE}>[0-9.]+)",
         "replace": "v{version}", "optional": True},
    ])
    answer = plan(_Stated(root, **facet), "1.1.0")
    check("a file marked optional and missing does not stop the plan",
          answer["holds"], f"reported {answer['report']!r}")
    check("and it is reported as skipped rather than as written",
          answer["files"][1].get("skipped") is True,
          f"reported {answer['files'][1]!r}")
    applied = apply(_Stated(root, **facet), "1.1.0")
    check("applying writes the files that are there and no others",
          applied["written"] == ["build.txt"], f"named {applied['written']!r}")

    # ⛔ The other direction, which is what makes the flag a decision rather than
    # a tolerance: a file that is not marked and is not there is a stop.
    root = _a_tree({"build.txt": 'version = "1.0.0"\n'})
    strict = a_facet(files=a_facet()["files"] + [
        {"path": "README.md", "kind": "regex",
         "pattern": f"v(?P<{VERSION_CAPTURE}>[0-9.]+)", "replace": "v{version}"},
    ])
    answer = plan(_Stated(root, **strict), "1.1.0")
    check("a file not marked optional and missing stops the plan",
          not answer["holds"], "the plan held")
    check("and the refusal names the file rather than the facet",
          any("README.md" in line for line in answer["report"]),
          f"said {answer['report']!r}")

    print("\nNothing is written unless every edit holds:")
    root = _a_tree({"build.txt": 'version = "1.0.0"\n'})
    before = _read(os.path.join(root, "build.txt"))
    applied = apply(_Stated(root, **strict), "1.1.0")
    check("a plan that does not hold writes no file at all",
          _read(os.path.join(root, "build.txt")) == before,
          f"left {_read(os.path.join(root, 'build.txt'))!r}")
    check("and the report says so first, before the file that blocked it",
          applied["written"] == [] and "Nothing was written" in applied["report"][0],
          f"said {applied['report']!r}")

    # ⛔ The same arm with the *first* file blocking and the second writable,
    # which is the ordering a loop that wrote as it went would get wrong in the
    # other direction.
    root = _a_tree({"second.txt": 'version = "1.0.0"\n'})
    answer = apply(_Stated(root, **a_facet(files=[
        {"path": "first.txt", "kind": "regex",
         "pattern": f"v(?P<{VERSION_CAPTURE}>[0-9.]+)", "replace": "v{version}"},
        {"path": "second.txt", "kind": "regex",
         "pattern": f'version = "(?P<{VERSION_CAPTURE}>[0-9.]+)"',
         "replace": 'version = "{version}"'},
    ])), "1.1.0")
    check("a writable file after a blocked one is still not written",
          _read(os.path.join(root, "second.txt")) == 'version = "1.0.0"\n',
          f"left {_read(os.path.join(root, 'second.txt'))!r}")

    print("\nA pattern that does not answer, in each of the two ways:")
    root = _a_tree({"build.txt": "nothing like a version here\n"})
    answer = plan(_Stated(root, **a_facet()), "1.1.0")
    check("a pattern matching nothing stops the plan", not answer["holds"],
          "the plan held")
    check("and says the pattern matched nothing rather than the file was missing",
          "matches nothing" in answer["files"][0]["because"],
          f"said {answer['files'][0]['because']!r}")

    root = _a_tree({"build.txt": 'version = "1.0.0"\nversion = "2.0.0"\n'})
    answer = plan(_Stated(root, **a_facet()), "3.0.0")
    check("one file carrying two different versions stops the plan",
          not answer["holds"], "the plan held")
    check("and the refusal names both, there being no one version to replace",
          "1.0.0" in answer["files"][0]["because"]
          and "2.0.0" in answer["files"][0]["because"],
          f"said {answer['files'][0]['because']!r}")

    # ⚠️ Two spans carrying the *same* version is the green side of that arm, and
    # it has to load: a build file naming its own version twice is ordinary.
    root = _a_tree({"build.txt": 'version = "1.0.0"\nversion = "1.0.0"\n'})
    applied = apply(_Stated(root, **a_facet()), "1.1.0")
    check("one version written twice is one version, and both spans move",
          _read(os.path.join(root, "build.txt"))
          == 'version = "1.1.0"\nversion = "1.1.0"\n',
          f"left {_read(os.path.join(root, 'build.txt'))!r}")

    print("\nThe changelog, and the project whose CI owns it:")
    root = _a_tree({"CHANGELOG.md": "# Changelog\n\n## 1.0.0\n\nthe first one\n"})
    log = a_facet(files=[{"path": "CHANGELOG.md", "kind": "changelog"}])
    answer = plan(_Stated(root, **log), "1.1.0")
    check("a changelog plan holds and reads the newest entry it carries",
          answer["holds"] and answer["files"][0]["current"] == "1.0.0",
          f"read {answer['files'][0]!r}")
    apply(_Stated(root, **log), "1.1.0")
    check("the entry is inserted above the entries and below what precedes them",
          _read(os.path.join(root, "CHANGELOG.md"))
          == "# Changelog\n\n## 1.1.0\n\n## 1.0.0\n\nthe first one\n",
          f"left {_read(os.path.join(root, 'CHANGELOG.md'))!r}")

    # ⛔ A changelog with no entry yet, which is where the positional insert has
    # no line to go above: the entry goes at the head of the file.
    root = _a_tree({"CHANGELOG.md": "# Changelog\n"})
    apply(_Stated(root, **log), "1.0.0")
    check("a changelog with no entries yet gets one at the end of its preamble",
          _read(os.path.join(root, "CHANGELOG.md")) == "# Changelog\n## 1.0.0\n\n",
          f"left {_read(os.path.join(root, 'CHANGELOG.md'))!r}")

    root = _a_tree({"CHANGELOG.md": "# Changelog\n\n## 1.1.0\n\nalready here\n"})
    answer = plan(_Stated(root, **log), "1.1.0")
    check("a changelog already carrying this version stops rather than merging",
          not answer["holds"], "the plan held")
    check("and says a release was started rather than that the file was wrong",
          "somebody started" in answer["files"][0]["because"],
          f"said {answer['files'][0]['because']!r}")

    # ⛔ The inversion: where CI owns the changelog the role writes none, and the
    # report **says so**. A run whose report did not mention it would read as a
    # run that wrote one.
    root = _a_tree({"build.txt": 'version = "1.0.0"\n'})
    answer = plan(_Stated(root, **a_facet(changelog_ci_owned=True)), "1.1.0")
    check("a project whose CI owns the changelog is told so in the report",
          any("CI owns the changelog" in line for line in answer["report"]),
          f"said {answer['report']!r}")
    check("and the plan still holds for the files that are not the changelog",
          answer["holds"], f"reported {answer['report']!r}")

    print("\nWhat a publishing project is told, and what the facet's absence is:")
    root = _a_tree({"build.txt": 'version = "1.0.0"\n'})
    answer = plan(_Stated(root, **a_facet(publishes_packages=True)), "1.1.0")
    check("a publishing project is told the go is the person's, for this release",
          any("spent for ever" in line for line in answer["report"]),
          f"said {answer['report']!r}")

    # ⛔ The stated absence, and it is `None` rather than an empty plan: a caller
    # reading an empty plan would see a release that had nothing to do, where
    # what the project said is that it is not versioned at all.
    check("a project stating no file reads back as no plan rather than an empty one",
          plan(_Stated(_a_tree({})), "1.0.0") is None, "an empty plan came back")
    check("and apply answers the same way rather than writing nothing quietly",
          apply(_Stated(_a_tree({})), "1.0.0") is None, "an empty answer came back")

    print("\nEvery planted facet, through the reader this module reads the surface with:")
    # ⛔ The arm that keeps the fake above honest: a facet this module accepts
    # must be one the reader accepts, or the suite is asserting against a shape
    # no configuration can have. ⚠️ Each is loaded whole rather than validated in
    # part, which is the only reading the reader offers.
    for label, facet in (
        ("the regex facet the arms above use", a_facet()),
        ("the changelog facet", log),
        ("a facet with an optional file", facet_with_optional := a_facet(files=[
            {"path": "README.md", "kind": "regex",
             "pattern": f"v(?P<{VERSION_CAPTURE}>[0-9.]+)",
             "replace": "v{version}", "optional": True},
        ])),
        ("a facet whose CI owns the changelog", a_facet(changelog_ci_owned=True)),
        ("a facet that publishes packages", a_facet(publishes_packages=True)),
    ):
        refusal = None
        try:
            config.load_text(
                _a_configuration_stating(facet), config.EXAMPLES, check_paths=False
            )
        except config.ConfigError as refused:
            refusal = str(refused)
        check(f"{label} loads through the reader", refusal is None,
              f"refused with {refusal!r}")
    del facet_with_optional

    print("\nThis project's own answer:")
    # ⚠️ This repository's own root rather than the directory this module sits
    # in, which is the reader's own constant: a skills root is where a project
    # states its facts, and `scripts/` is not one.
    try:
        configuration = config.load(config.REPO_ROOT)
    except (config.ConfigError, OSError) as exc:
        check("this project's configuration loads", False, str(exc))
    else:
        answer = _report(configuration)
        check("this project states whether any file carries a version",
              answer["release"] is not None or bool(answer["report"]),
              f"answered {answer!r}")
        for line in answer["report"]:
            print(f"        {line}")

    print()
    if failures:
        print(f"{len(failures)} failed: " + "; ".join(failures))
        return 1
    print("all held")
    return 0


def _a_configuration_stating(facet: dict) -> str:
    """An example's text with its `release` block replaced by this facet.

    ⛔ Composed off a shipped example rather than written here, for the reason
    every fixture in the reader beside this module is composed that way: a
    configuration written out in full would stop asserting the moment a key
    became required elsewhere, and the half of it that is a *fixture* would be
    invisible.
    """
    import yaml

    for name in sorted(os.listdir(config.EXAMPLES)):
        if not name.endswith((".yaml", ".yml")):
            continue
        with open(os.path.join(config.EXAMPLES, name), encoding="utf-8") as handle:
            data = yaml.safe_load(handle.read())
        if (data.get("release") or {}).get("carrier") == "list":
            data["release"] = {"carrier": "list", **facet}
            return yaml.safe_dump(data, allow_unicode=True)
    raise config.ConfigError(
        "release.carrier",
        "no example states a file that carries a version, so this suite has no "
        "configuration to place a planted facet into and would assert nothing.",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("what", nargs="?", choices=["plan", "apply"])
    parser.add_argument("--skills-root", default=None)
    parser.add_argument("--version", dest="version")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()

    root = args.skills_root or os.getcwd()
    if not config.configured(root):
        print(json.dumps({
            "release": None,
            "report": [
                "This project states no configuration, so nothing is known about "
                "whether any of its files carries a version. Write "
                "`.claude/mjolnir.yaml`; the keys are stated in the configuration "
                "surface shipped with the toolkit."
            ],
        }, indent=2, ensure_ascii=False))
        return NO_FILES

    try:
        configuration = config.load(root)
    except (config.ConfigError, OSError) as exc:
        print(exc, file=sys.stderr)
        return 2

    if args.what is None:
        answer = _report(configuration)
        print(json.dumps(answer, indent=2, ensure_ascii=False))
        return 0 if answer["release"] is not None else NO_FILES

    if not args.version:
        parser.error(f"`{args.what}` needs the version to cut: --version X.Y.Z")

    answer = (plan if args.what == "plan" else apply)(configuration, args.version)
    if answer is None:
        print(json.dumps(_report(configuration), indent=2, ensure_ascii=False))
        return NO_FILES
    print(json.dumps(answer, indent=2, ensure_ascii=False))
    return 0 if answer["holds"] else 1


if __name__ == "__main__":
    sys.exit(main())
