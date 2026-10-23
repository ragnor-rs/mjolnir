#!/usr/bin/env python3
"""The artifacts the toolkit writes into a repository, and what takes them out.

What the toolkit generates has to be a **file in the adopting repository**
wherever nothing else can express it: a host gate is a workflow file or the host
never runs it, and a `commit-msg` rail is a hook file or git never calls it.
This module is the one step that writes them, and the surface
beside it -- `../config/schema.md`, the section on what the toolkit installs --
is the single statement of what that step may do. Neither is restated here.

⛔ **It asks nothing.** The interrogation that writes a project's configuration
is a different step, and this one waits on no answer from it: every artifact
below is wanted or not wanted by facts the project has **already** stated, and
an artifact whose content needs a value the configuration does not state is not
written and names the value. That split is the whole reason this module exists
separately from the step that asks.

⛔ **It carries no gate of its own.** `ARTIFACTS` is the registry, and each
member is a rule somebody else's work item states -- what the file says, which
configured value it reads, and which `host.checks` entry registers it. What this
module owns is the four properties none of those items should each solve again:

  * **Marked.** Every artifact carries a generated-by marker at its head, so a
    later run can tell its own output from the project's and so the marker can
    be taken out again when a plugin is retired.
  * **Removable.** An artifact the toolkit wrote is one the toolkit takes back
    out. A project that turns a gate off gets the file **removed** rather than
    orphaned, and ⛔ **a file carrying no marker is never removed and never
    written over** -- it is the project's, and meeting one is a stop.
  * **Idempotent.** A second run leaves the tree byte-identical. Which is
    asserted on the **bytes** and not on a verdict string, and is why no marker
    carries a date, a version or a commit: a head line that moved every run
    would make every run a change.
  * **Refusing rather than improvising.** A value absent, a path occupied, a
    `host.checks` entry the surface cannot state, a host whose definitions are
    not files this step can write -- each is an answer with the thing named, and
    none of them is a partial install left behind.

Two facts it deliberately does not carry:

  * **Where a generated gate goes, and whether it may join a file that exists.**
    That is § 2's ruling, and this module reads it rather than deciding again: a
    generated gate takes a workflow file of its own, a job is never appended to
    a workflow the toolkit did not write, and a file that already exists is a
    stop. ⛔ **Nor the directory**: which host kind keeps its workflow
    definitions where is `check_host_checks.DEFINITIONS`, the one statement of
    it in this toolkit, and a second spelling here would be free to disagree
    with the check that holds the facet to those same files.
  * **Which route a git hook is installed by.** A repository stating
    `core.hooksPath` has chosen one; a repository stating none is read through
    git's own answer for where its hooks live. ⚠️ **Choosing between a tracked
    hooks directory and this step is the hook's own work item**, so this module
    reads whichever route the repository already states and decides neither.

**A project that states no configuration gets nothing written and is told so.**
Not silence: this step is invoked by name, and § 7 makes the answer owed to
whoever invokes a role in a project that configures nothing. The silent arm
there is the one for a carrier addressed by an event, which this is not.

Usage:
    install.py [--skills-root DIR]        what each artifact's state is, writing
                                          nothing
    install.py install [--skills-root DIR] [--dry-run]
                                          write every artifact the configuration
                                          asks for, remove the ones it no longer
                                          asks for, and register what was written
    install.py remove [--skills-root DIR] [--dry-run]
                                          take out every artifact carrying the
                                          marker, and nothing else
    install.py --self-test                assert every answer against a planted
                                          tree, then report this project's own
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import config  # noqa: E402 -- the one reader of the surface
from config import ConfigError  # noqa: E402

# ⛔ Imported for one fact and not for its checks: where a host kind keeps its
# workflow definitions. That module declares it as the only host fact it
# carries, which makes it the single statement of it -- and this module writing
# a directory of its own would be free to write somewhere the check holding the
# facet to those files never looks.
import check_host_checks  # noqa: E402

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - environment, not logic
    sys.exit(
        "install.py needs PyYAML to render a `host.checks` entry.\n"
        "Install it with: python3 -m pip install pyyaml"
    )


# --- the marker ------------------------------------------------------------
#
# ⛔ Nothing in it moves between runs. A marker carrying the pass that wrote it
# would be the audit trail the surface forbids an artifact outright, and it
# would also defeat the byte-identical property above -- the same line failing
# two rules for one reason, which is why the form has no room for either.

MARKER = "mjolnir-generated"

# The second line is the removal instruction, because the first thing somebody
# meeting one of these files wants is to know it is not theirs to edit and what
# takes it out. ⚠️ It names this module rather than a role: the role that calls
# this step is a project's configured carrier and is not a fact this file holds.
REMOVAL = "edits here are overwritten; remove it with install.py remove"

# What opens a comment, per artifact rather than per toolkit. Both kinds this
# registry has today use `#`, and stating it on the artifact is what keeps a
# third kind from inheriting a syntax nobody checked for it.
HASH = "#"


def marker_lines(artifact: "Artifact") -> list[str]:
    """The two head lines an artifact carries, in order."""
    return [
        f"{artifact.comment} {MARKER}: {artifact.name}",
        f"{artifact.comment} {REMOVAL}",
    ]


def _marked(text: str) -> bool:
    """Whether this text is one the toolkit wrote.

    ⛔ The head only, and the head is the first two lines -- or the second and
    third where the first is a shebang, which is the one position a comment
    cannot take. Read anywhere in the file, a document that merely *quotes* the
    marker would read as generated, and this module's own source is the first
    such document.
    """
    lines = text.splitlines()
    head = lines[1:3] if lines and lines[0].startswith("#!") else lines[:2]
    return any(f"{MARKER}:" in line for line in head)


def rendered(artifact: "Artifact", body: str) -> str:
    """`body` with the marker at its head, and a trailing newline.

    ⚠️ **After a shebang and never before it.** A shebang is only a shebang on
    the first line, so a marker written above one turns an executable hook into
    a file the kernel will not run -- which git reports as a hook that failed
    rather than as a hook that was installed wrong.
    """
    lines = body.splitlines()
    shebang = lines[:1] if lines and lines[0].startswith("#!") else []
    rest = lines[len(shebang):]
    out = shebang + marker_lines(artifact) + rest
    return "\n".join(out) + "\n"


# --- what an artifact is ---------------------------------------------------

WORKFLOW, HOOK = "workflow", "hook"

# The answers this step gives per artifact. ⛔ Every one of them is an answer:
# none of them is a skip, and `waiting` in particular is not a pass -- an
# artifact whose value is absent is a gate the project does not have.
WRITTEN = "written"
UNCHANGED = "unchanged"
REMOVED = "removed"
NOT_WANTED = "not wanted"
WAITING = "waiting on a value"
OCCUPIED = "occupied"
UNSTATABLE = "unstatable entry"
NO_PLACE = "no place to write it"

# Which answers leave the install incomplete. ⛔ `waiting` is among them: the
# configuration asks for the artifact and the artifact cannot be rendered, so a
# run reporting zero is reporting a gate that is not there.
INCOMPLETE = (WAITING, OCCUPIED, UNSTATABLE, NO_PLACE)

_ABSENT = object()


class Artifact:
    """One file the toolkit writes, and the facts that decide whether it does.

    ⛔ Nothing here states a rule. `wanted`, `needs`, `body` and `entry` are
    each a work item's own statement handed over as data, so that this module
    can hold the four properties without reading any of them.
    """

    def __init__(
        self,
        name: str,
        kind: str,
        leaf: str,
        *,
        needs: tuple[str, ...] = (),
        wanted=None,
        body=None,
        entry=None,
        comment: str = HASH,
    ):
        self.name = name
        self.kind = kind
        self.leaf = leaf
        self.needs = needs
        # Absent, an artifact is wanted wherever its values are stated, which
        # `needs` already answers. A gate whose presence turns on a facet of
        # its own states that facet here.
        self._wanted = wanted
        self._body = body
        self._entry = entry
        self.comment = comment

    def wanted(self, configuration: config.Config) -> bool:
        return True if self._wanted is None else bool(self._wanted(configuration))

    def absent_values(self, configuration: config.Config) -> list[str]:
        """The `needs` paths this configuration does not state.

        ⚠️ Absent means *no value*, not an empty one. An empty list or an
        explicit `none` is a project's stated absence, which is a question for
        `wanted` above: read as a missing value it would turn every legitimate
        absence into an artifact waiting forever on a key nobody is going to
        write.
        """
        return [
            path for path in self.needs
            if configuration.get(path, _ABSENT) is _ABSENT
            or configuration.get(path) is None
        ]

    def body(self, configuration: config.Config) -> str:
        return "" if self._body is None else self._body(configuration)

    def entry(self, configuration: config.Config):
        return None if self._entry is None else self._entry(configuration)


# ⛔ The live registry, and it is **empty on purpose rather than unfinished**.
# The three artifacts this step was separated out for -- two host gates and a
# `commit-msg` rail -- are each their own work item, and each of those states
# what its file says and which value it reads. A placeholder here would be this
# module inventing a gate, which is the one thing the split exists to prevent.
#
# ⚠️ So a run against this repository reports an empty registry **as** an
# answer, named, rather than as a complete install: a step that holds nothing
# and prints success is the shape every check in this tree is written against.
ARTIFACTS: tuple[Artifact, ...] = ()


# --- where an artifact goes ------------------------------------------------


def workflow_directory(configuration: config.Config) -> str | None:
    """The directory this host kind keeps its workflow definitions in.

    ⛔ Read out of `check_host_checks.DEFINITIONS` and never written here. A
    kind absent from it keeps its definitions somewhere no reader can open,
    which § 2 makes an answer rather than a gap -- so there is nowhere to write
    and this step says so instead of guessing a path.
    """
    where = check_host_checks.DEFINITIONS.get(configuration.get("host.kind"))
    return None if where is None else where.directory


def hook_directory(code_root: str) -> str | None:
    """Where git calls this repository's hooks from, or None where it will not say.

    `core.hooksPath` where the repository states one -- a repository that has
    chosen the tracked-directory route has said so there -- and git's own answer
    otherwise, which is what makes this correct inside a worktree, where the
    git directory is not `.git` at all.

    ⛔ It decides nothing between those two routes. Which one a project ought to
    take is the hook's own work item, and a step that picked would be answering
    it in passing.
    """
    stated = _git(code_root, "config", "--get", "core.hooksPath")
    if stated:
        return os.path.join(code_root, stated) if not os.path.isabs(stated) else stated
    answered = _git(code_root, "rev-parse", "--git-path", "hooks")
    if not answered:
        return None
    return answered if os.path.isabs(answered) else os.path.join(code_root, answered)


def _git(root: str, *arguments: str) -> str | None:
    """One git question, or None where git did not answer it.

    ⚠️ A non-zero status is an answer of its own here -- `config --get` exits 1
    on a key the repository does not state -- so the two are collapsed into
    *nothing stated* deliberately, and a root that is not a repository at all
    reaches the same branch rather than raising.
    """
    try:
        done = subprocess.run(
            ["git", "-C", root, *arguments],
            capture_output=True, text=True, check=False,
        )
    except OSError:
        return None
    return done.stdout.strip() or None


def place(configuration: config.Config, artifact: Artifact) -> str | None:
    """The absolute path this artifact takes, or None where there is nowhere."""
    root = configuration.code_root
    if artifact.kind == WORKFLOW:
        directory = workflow_directory(configuration)
        return None if directory is None else os.path.join(root, directory, artifact.leaf)
    if artifact.kind == HOOK:
        directory = hook_directory(root)
        return None if directory is None else os.path.join(directory, artifact.leaf)
    return None


# --- the `host.checks` entry an artifact registers -------------------------


def refuses_entry(configuration: config.Config, entry: dict) -> str | None:
    """Why the surface cannot state this entry, or None where it can.

    ⛔ Asked of the **reader** rather than answered here. Every refusal § 2
    carries -- an entry with no workflow name, `mirrors` beside `jobs`, a list
    inside one `mirrors`, a trigger that does not parse, a path filter written
    blank -- is in that one walk, and a second judgement here would be free to
    admit a shape the project's own configuration then fails to load.
    """
    data = copy.deepcopy(configuration.data)
    data.setdefault("host", {})
    data["host"]["checks"] = list(data["host"].get("checks") or []) + [entry]
    try:
        config.load_text(yaml.safe_dump(data, allow_unicode=True), ".", check_paths=False)
    except ConfigError as exc:
        return str(exc)
    return None


def already_registered(configuration: config.Config, entry: dict) -> bool:
    return any(
        existing == entry for existing in (configuration.get("host.checks") or [])
    )


CHECKS = re.compile(r"^(?P<indent>\s+)checks:(?P<rest>.*)$")
MEMBER = re.compile(r"^(?P<indent>\s*)-\s")


def _depth(line: str) -> int:
    return len(line) - len(line.lstrip())


def _insertion(lines: list[str]) -> tuple[int, str, bool] | str:
    """(the line to insert after, the member indent, whether `[]` is to be replaced).

    Or a sentence naming why this file cannot be written into. ⛔ Textual and
    not a round trip: re-dumping the file would take out every comment a project
    wrote about its own facts, which is a loss no run reports and nobody asked
    for. So the two shapes that can be inserted into are the two that are read,
    and every other shape is refused by name rather than reformatted.

    ⚠️ **The member indent is read off the list and never derived from the
    key's.** A block sequence may sit at its key's own column or one in from
    it — both are the same document, and the two shapes occur in this tree —
    so an indent computed as *the key plus two* writes a member the file cannot
    parse against a list written the other way. Measured by inserting into a
    dumped configuration, where the members sit at the key's column.
    """
    host = next((i for i, line in enumerate(lines) if line.rstrip() == "host:"), None)
    if host is None:
        return "no `host:` block opens a line, so there is nowhere to register an entry."
    for index in range(host + 1, len(lines)):
        line = lines[index]
        if line.strip() and not line[:1].isspace():
            break
        found = CHECKS.match(line)
        if not found:
            continue
        indent, rest = found.group("indent"), found.group("rest").strip()
        if rest == "[]":
            return index, indent + "  ", True
        if rest != "":
            return (
                f"`host.checks` is written as {rest!r}, which this step cannot insert "
                "into. A block list, or an empty list written `[]`, are the two shapes "
                "it reads."
            )
        member, last = None, index
        for after in range(index + 1, len(lines)):
            following = lines[after]
            if not following.strip() or following.lstrip().startswith("#"):
                continue
            opens = MEMBER.match(following)
            depth = _depth(following)
            if member is None:
                if opens and depth >= len(indent):
                    member, last = opens.group("indent"), after
                    continue
                if depth > len(indent):
                    return (
                        "`host.checks` opens a block of keys rather than a list, which "
                        "this step cannot insert into. A block list, or an empty list "
                        "written `[]`, are the two shapes it reads."
                    )
                break
            # ⛔ A new member sits at the dash's own column; anything deeper
            # belongs to the member above it, **dash or not**. Both halves were
            # measured against a real file. A sibling key of `host:` sits at
            # the dash's column and opens no dash, which a looser test
            # swallows — the entry then lands below the list. And a member
            # whose own value is a block list carries dashes deeper than the
            # member indent, which a test keyed on *not a dash* breaks at — the
            # entry then lands between that key and its own members, and the
            # key reads as stating nothing.
            if opens and depth == len(member):
                last = after
                continue
            if depth > len(member):
                last = after
                continue
            break
        return last, member if member is not None else indent + "  ", False
    return "`host:` states no `checks` key, so there is nowhere to register an entry."


def rendered_entry(entry: dict, indent: str) -> list[str]:
    """One `host.checks` member as lines, at the stated indent."""
    dumped = yaml.safe_dump(
        [entry], default_flow_style=False, sort_keys=False, allow_unicode=True,
    )
    return [indent + line if line.strip() else line for line in dumped.splitlines()]


def register(configuration: config.Config, entry: dict) -> str | None:
    """Write one entry into this project's own configuration file.

    Returns None on success, or a sentence naming why not. ⛔ The write is
    verified by loading the file again, and a file that stops loading is
    **restored** -- a configuration half-edited by an installer is a project
    whose every role then refuses, for a reason none of them can name.
    """
    path = configuration.config_path
    if path is None:
        return "this configuration came from text rather than a file, so there is nothing to write."
    with open(path, encoding="utf-8") as handle:
        before = handle.read()
    lines = before.splitlines()
    found = _insertion(lines)
    if isinstance(found, str):
        return found
    after, indent, replace = found
    written = list(lines)
    if replace:
        written[after] = written[after].split("checks:")[0] + "checks:"
    written[after + 1:after + 1] = rendered_entry(entry, indent)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(written) + "\n")
    try:
        config.load(configuration.skills_root)
    except (ConfigError, OSError) as exc:
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(before)
        return f"the entry was written and the file then would not load, so it was put back: {exc}"
    return None


# --- the step --------------------------------------------------------------


def _state(artifact: Artifact, answer: str, path: str | None, **rest) -> dict:
    return {"artifact": artifact.name, "kind": artifact.kind,
            "path": path, "answer": answer, **rest}


def one(configuration: config.Config, artifact: Artifact, *, write: bool) -> dict:
    """Bring one artifact to the state this configuration asks for.

    ⛔ The order of the tests is the rule rather than a convenience. The entry
    is validated **before** the file is written, so a shape the surface cannot
    state leaves nothing behind; the file is written before the entry is
    inserted, and a failed insertion takes the file back out again. Reversed,
    either half can leave the other's output orphaned in a repository that did
    not ask for it.
    """
    path = place(configuration, artifact)
    if path is None:
        return _state(
            artifact, NO_PLACE, None,
            because="this host kind keeps its definitions somewhere this step cannot "
                    "write, which § 2 states as an answer rather than a gap"
            if artifact.kind == WORKFLOW else
            "git did not say where this repository's hooks are called from",
        )

    here = None
    if os.path.exists(path):
        with open(path, encoding="utf-8") as handle:
            here = handle.read()

    if not artifact.wanted(configuration):
        if here is None:
            return _state(artifact, NOT_WANTED, path)
        if not _marked(here):
            return _state(artifact, OCCUPIED, path,
                          because="a file is there carrying no marker, so it is the "
                                  "project's own and is neither removed nor written over")
        if write:
            os.remove(path)
        return _state(artifact, REMOVED, path)

    absent = artifact.absent_values(configuration)
    if absent:
        return _state(artifact, WAITING, path, values=absent,
                      standing=here is not None,
                      because="the configuration asks for this artifact and states no "
                              "value for what it would say, so it is not written")

    entry = artifact.entry(configuration)
    if entry is not None:
        refusal = refuses_entry(configuration, entry)
        if refusal is not None:
            return _state(artifact, UNSTATABLE, path, entry=entry, because=refusal)

    if here is not None and not _marked(here):
        return _state(artifact, OCCUPIED, path,
                      because="a file is already there carrying no marker. § 2 makes "
                              "that a stop: it is the project's own file, and a "
                              "generated artifact neither joins it nor replaces it")

    wanted_text = rendered(artifact, artifact.body(configuration))
    needs_entry = entry is not None and not already_registered(configuration, entry)
    if here == wanted_text and not needs_entry:
        return _state(artifact, UNCHANGED, path)

    if not write:
        return _state(artifact, WRITTEN, path, dry_run=True,
                      registers=entry if needs_entry else None)

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(wanted_text)

    if needs_entry:
        refusal = register(configuration, entry)
        if refusal is not None:
            if here is None:
                os.remove(path)
            else:
                with open(path, "w", encoding="utf-8") as handle:
                    handle.write(here)
            return _state(artifact, UNSTATABLE, path, entry=entry,
                          because=f"the artifact was taken back out because its entry "
                                  f"could not be registered: {refusal}")
        return _state(artifact, WRITTEN, path, registered=entry)

    return _state(artifact, WRITTEN, path)


def run(
    configuration: config.Config,
    artifacts: tuple[Artifact, ...] = None,
    *,
    write: bool,
) -> dict:
    """Every artifact brought to the state this configuration asks for."""
    members = ARTIFACTS if artifacts is None else artifacts
    states = [one(configuration, artifact, write=write) for artifact in members]
    report = []
    if not members:
        report.append(
            "No artifact is registered, so this step wrote nothing and holds nothing. "
            "That is the registry being empty rather than the install being complete."
        )
    for state in states:
        if state["answer"] in INCOMPLETE:
            report.append(
                f"{state['artifact']}: {state['answer']} — {state.get('because', '')}".strip()
            )
    return {"artifacts": states, "wrote": write, "report": report}


def removal(
    configuration: config.Config,
    artifacts: tuple[Artifact, ...] = None,
    *,
    write: bool,
) -> dict:
    """Take out every artifact carrying the marker, and nothing else."""
    members = ARTIFACTS if artifacts is None else artifacts
    states = []
    for artifact in members:
        path = place(configuration, artifact)
        if path is None or not os.path.exists(path):
            states.append(_state(artifact, NOT_WANTED, path))
            continue
        with open(path, encoding="utf-8") as handle:
            here = handle.read()
        if not _marked(here):
            states.append(_state(
                artifact, OCCUPIED, path,
                because="a file is there carrying no marker, so it is the project's own "
                        "and this step does not remove it",
            ))
            continue
        if write:
            os.remove(path)
        states.append(_state(artifact, REMOVED, path))
    report = [
        f"{state['artifact']}: {state['answer']} — {state.get('because', '')}".strip()
        for state in states if state["answer"] in INCOMPLETE
    ]
    if not members:
        report.append("No artifact is registered, so there was nothing to take out.")
    return {"artifacts": states, "wrote": write, "report": report}


def facet(configuration: config.Config,
          artifacts: tuple[Artifact, ...] = None) -> dict:
    """What each artifact's state is, writing nothing."""
    return run(configuration, artifacts, write=False)


# --- the self-test ---------------------------------------------------------


def _a_project(tmp: str, checks=None) -> config.Config:
    """A loadable configuration in a tree of its own.

    Built from an example rather than written here, for the reason the sibling
    consumer's fixtures are: a planted configuration the reader beside this
    module would refuse makes every answer below an answer about nothing.
    """
    with open(os.path.join(config.EXAMPLES, "github-issues.yaml"), encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    data["roots"] = {"code": ".", "code_is_own_repo": False}
    data.setdefault("host", {})["kind"] = "github"
    data["host"]["checks"] = [] if checks is None else checks
    # § 17 refuses a local check the host already runs, and a fixture colliding
    # with one would be refused by the reader rather than answered here.
    data["checks_local"] = []
    os.makedirs(os.path.join(tmp, ".claude"), exist_ok=True)
    with open(os.path.join(tmp, config.CONFIG_PATH), "w", encoding="utf-8") as handle:
        handle.write(yaml.safe_dump(data, allow_unicode=True))
    return config.load(tmp)


def _a_gate(**rest) -> Artifact:
    """A fixture artifact of the workflow kind.

    ⚠️ Fixture data and not a gate this module knows about: the gates are their
    own work items, and the registry above is empty for exactly that reason.
    """
    defaults = dict(
        name="a-fixture-gate",
        kind=WORKFLOW,
        leaf="a-fixture-gate.yml",
        body=lambda _c: "name: A fixture gate\non:\n  pull_request:\n",
    )
    defaults.update(rest)
    return Artifact(**defaults)


def _a_rail(**rest) -> Artifact:
    """A fixture artifact of the hook kind, with a shebang."""
    defaults = dict(
        name="a-fixture-rail",
        kind=HOOK,
        leaf="a-fixture-rail",
        body=lambda _c: "#!/bin/sh\nexit 0\n",
    )
    defaults.update(rest)
    return Artifact(**defaults)


def _a_repository(root: str) -> bool:
    """Make the fixture tree a git repository, since a hook needs one to live in.

    ⚠️ **git on `PATH` is a precondition this run does not check for itself**,
    which is why the arm that uses this asserts the directory was *established*
    before it asserts anything about a file in it: read as a skip, a missing git
    would turn the whole hook half of this suite green while holding nothing.
    """
    try:
        done = subprocess.run(
            ["git", "init", "--quiet", root],
            capture_output=True, text=True, check=False,
        )
    except OSError:
        return False
    return done.returncode == 0


AN_ENTRY = {
    "workflow": "A fixture gate",
    "mirrors": "a-fixture-command",
    "triggers": "pull_request -> *",
}

# A shape § 2 refuses: `mirrors` beside `jobs`. ⛔ Refused by the reader and not
# by anything here, which is what the plant using it asserts.
A_REFUSED_ENTRY = {
    "workflow": "A fixture gate",
    "mirrors": "a-fixture-command",
    "jobs": [{"job": "a-job", "mirrors": "another-fixture-command"}],
    "triggers": "pull_request -> *",
}


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as handle:
        return handle.read()


# What reading from whoever is running the step looks like, as names rather
# than as text. ⛔ Each is matched against a parsed call or attribute, so this
# tuple is data the parser never sees as either -- which is what keeps the arm
# below from finding its own list.
ASKING = ("input", "getpass", "raw_input")
A_STREAM = ("stdin",)


def _asks(source: str) -> list[str]:
    """Every place this source reads from whoever ran it, by name."""
    import ast

    found = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id in ASKING:
            found.append(node.func.id)
        if isinstance(node, ast.Attribute) and node.attr in A_STREAM + ASKING:
            found.append(node.attr)
    return sorted(set(found))


def self_test() -> int:  # noqa: C901 -- one assertion per property, read in order
    """Assert every answer against a planted tree, then report this project's own."""
    failures: list[str] = []
    ran = 0

    def check(label: str, condition: bool, detail: str = "") -> None:
        nonlocal ran
        ran += 1
        print(f"  {'ok  ' if condition else 'FAIL'}  {label}"
              + (f": {detail}" if detail and not condition else ""))
        if not condition:
            failures.append(label)

    print("the facts this module reads rather than carries")
    own = _read(os.path.abspath(__file__))
    check(
        "the reader this module loaded is the one beside it",
        os.path.dirname(os.path.abspath(config.__file__)) == HERE,
        f"imported {config.__file__}, which is not in this tree",
    )
    # ⛔ Computed from the fact rather than written as a pattern over it. The
    # first form of this arm spelled the directory inside its own regex, so the
    # assertion matched itself and reported the violation it exists to forbid —
    # the failure mode a forbidding check has whenever the thing forbidden has
    # to be named to forbid it. Read out of `DEFINITIONS`, this file names none
    # of them and the arm grows with the kinds that module reads.
    spelled = [
        where.directory
        for where in check_host_checks.DEFINITIONS.values()
        if re.search(r"""["'][^"'\n]*""" + re.escape(where.directory)
                     + r"""[^"'\n]*["']""", own)
    ]
    check(
        "where a host kind keeps its definitions is read, not written here",
        "check_host_checks.DEFINITIONS" in own and not spelled,
        f"this module spells {spelled} itself, which is free to disagree with "
        "the check that holds the facet to those files",
    )
    check(
        "the entry refusal is the reader's walk and not a judgement here",
        "config.load_text(" in own,
        "nothing calls the reader, so a shape it refuses could be admitted here",
    )
    # ⛔ The property the whole split rests on, asserted rather than stated. A
    # step that asked one question would be waiting on the interrogation it was
    # separated out from, and the three artifacts it writes would be gated on
    # it again by a route no reader of either item would look for.
    #
    # ⚠️ Read as a **tree** and not as text, for the reason the directory arm
    # above is computed rather than matched: a lexical form of this arm finds
    # the spellings it has to write down in order to forbid them, and reports
    # the violation it exists to catch. Measured — the first form of it failed
    # on its own list.
    check(
        "this step asks nothing, which is what makes it separable at all",
        not _asks(own),
        f"it reads {_asks(own)} from whoever runs it",
    )

    print()
    print("an artifact is written, marked, and byte-identical the second time")
    with tempfile.TemporaryDirectory() as tmp:
        project = _a_project(tmp)
        gate = _a_gate()
        first = one(project, gate, write=True)
        path = first["path"]
        check("a wanted artifact is written", first["answer"] == WRITTEN, str(first))
        check(
            "it lands where this host kind keeps its definitions",
            path == os.path.join(
                project.code_root, check_host_checks.DEFINITIONS["github"].directory,
                gate.leaf,
            ),
            str(path),
        )
        text = _read(path)
        check("its head carries the marker", _marked(text), repr(text[:120]))
        check(
            "the marker names the artifact and how it comes out",
            text.splitlines()[:2] == marker_lines(gate),
            repr(text.splitlines()[:2]),
        )
        check(
            "the body below the marker is exactly what the artifact stated",
            "\n".join(text.splitlines()[2:]) + "\n" == gate.body(project),
            repr("\n".join(text.splitlines()[2:])),
        )
        second = one(project, gate, write=True)
        check("a second run reports it unchanged", second["answer"] == UNCHANGED, str(second))
        check(
            "and the file is byte-identical, which is what that claim rests on",
            _read(path) == text,
        )
        check(
            "nothing in the marker moved between the two runs",
            MARKER in text and not re.search(r"\d{4}-\d{2}-\d{2}", text),
            "a date in the head line would make every run a change",
        )

    print()
    print("a shebang keeps the first line, and the marker takes the second")
    with tempfile.TemporaryDirectory() as tmp:
        project = _a_project(tmp)
        check("the fixture tree is a git repository, which a hook needs",
              _a_repository(project.code_root),
              "git did not initialise the fixture, so the arms below would hold "
              "nothing; git on PATH is this suite's one unchecked precondition")
        check("and git answered where its hooks are called from",
              hook_directory(project.code_root) is not None)
        rail = _a_rail()
        state = one(project, rail, write=True)
        check("a hook-kind artifact is written", state["answer"] == WRITTEN, str(state))
        text = _read(state["path"]) if state["path"] else ""
        check("the shebang is still the first line", text.startswith("#!/bin/sh\n"),
              repr(text[:40]))
        check("the marker is on the second", _marked(text), repr(text[:120]))
        check(
            "git's own answer is what placed it, so a worktree resolves too",
            os.path.dirname(state["path"] or "") == hook_directory(project.code_root),
            str(state["path"]),
        )
        check("a second run leaves it byte-identical",
              one(project, rail, write=True)["answer"] == UNCHANGED
              and _read(state["path"]) == text)
        stated = os.path.join(project.code_root, "a-tracked-hooks-directory")
        subprocess.run(
            ["git", "-C", project.code_root, "config", "core.hooksPath",
             "a-tracked-hooks-directory"],
            capture_output=True, check=False,
        )
        check(
            "a repository stating `core.hooksPath` is read there instead",
            hook_directory(project.code_root) == stated,
            str(hook_directory(project.code_root)),
        )

    print()
    print("an artifact the configuration no longer asks for is removed")
    with tempfile.TemporaryDirectory() as tmp:
        project = _a_project(tmp)
        one(project, _a_gate(), write=True)
        gone = one(project, _a_gate(wanted=lambda _c: False), write=True)
        check("it is removed rather than orphaned", gone["answer"] == REMOVED, str(gone))
        check("and the file is gone", not os.path.exists(gone["path"]))
        again = one(project, _a_gate(wanted=lambda _c: False), write=True)
        check("asking again is not wanted rather than removed again",
              again["answer"] == NOT_WANTED, str(again))

    print()
    print("a file the toolkit did not write is a stop, in both directions")
    with tempfile.TemporaryDirectory() as tmp:
        project = _a_project(tmp)
        gate = _a_gate()
        path = place(project, gate)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        theirs = "name: The project's own workflow\n"
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(theirs)
        state = one(project, gate, write=True)
        check("writing over it is refused", state["answer"] == OCCUPIED, str(state))
        check("and its bytes are untouched", _read(path) == theirs)
        taken = removal(project, (gate,), write=True)
        check("removing it is refused too",
              taken["artifacts"][0]["answer"] == OCCUPIED, str(taken))
        check("and its bytes are still untouched", _read(path) == theirs)
        unwanted = one(project, _a_gate(wanted=lambda _c: False), write=True)
        check("an unwanted artifact does not remove it either",
              unwanted["answer"] == OCCUPIED, str(unwanted))
        check("and its bytes survive that too", _read(path) == theirs)
        # ⛔ The arm that makes the marker's *position* load-bearing. Read
        # anywhere in the file, a project's own workflow that merely mentions
        # the marker — one grepping for generated files is the obvious case —
        # reads as the toolkit's own and is then written over. Measured: with
        # the head-only rule removed, every other arm here stayed green.
        quoting = theirs + f"\n# this project greps for {MARKER}: in its own tree\n"
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(quoting)
        mentions = one(project, gate, write=True)
        check("a file that merely mentions the marker below its head is still theirs",
              mentions["answer"] == OCCUPIED, str(mentions))
        check("and its bytes are untouched as well", _read(path) == quoting)

    print()
    print("an artifact needing an absent value is not written, and the value is named")
    with tempfile.TemporaryDirectory() as tmp:
        project = _a_project(tmp)
        gate = _a_gate(needs=("host.a_value_no_project_states",))
        state = one(project, gate, write=True)
        check("it is waiting rather than written", state["answer"] == WAITING, str(state))
        check("the absent value is named",
              state["values"] == ["host.a_value_no_project_states"], str(state))
        check("and nothing was written", not os.path.exists(state["path"]))
        check("waiting counts as an incomplete install", WAITING in INCOMPLETE)
        check("and the run says so rather than reporting nothing",
              bool(run(project, (gate,), write=False)["report"]))
        standing = _a_gate()
        one(project, standing, write=True)
        again = one(project, gate, write=True)
        check("an artifact already installed is left standing and reported",
              again["answer"] == WAITING and again["standing"] is True, str(again))
        check("its file is still there", os.path.exists(again["path"]))

    print()
    print("a stated absence is not a missing value")
    with tempfile.TemporaryDirectory() as tmp:
        project = _a_project(tmp)
        gate = _a_gate(needs=("host.checks",))
        state = one(project, gate, write=True)
        check(
            "an empty list satisfies `needs` and the artifact is written",
            state["answer"] == WRITTEN,
            "read as a missing value, every legitimate absence would wait forever",
        )

    print()
    print("an entry the surface cannot state is refused, and nothing is left behind")
    with tempfile.TemporaryDirectory() as tmp:
        project = _a_project(tmp)
        gate = _a_gate(entry=lambda _c: A_REFUSED_ENTRY)
        before = _read(project.config_path)
        state = one(project, gate, write=True)
        check("the install is refused", state["answer"] == UNSTATABLE, str(state))
        check("the entry it could not write is named", state["entry"] == A_REFUSED_ENTRY)
        check("no artifact was written", not os.path.exists(state["path"]))
        check("and the configuration is untouched", _read(project.config_path) == before)
        # ⛔ The arm that makes the refusal happen **before** the write rather
        # than being undone after it. Bypassing the check leaves the write and
        # the rollback reaching the same three answers above — measured, all
        # three stayed green — and a dry run is the one place the two differ:
        # it writes nothing, so there is nothing for a rollback to undo and the
        # only way to report the refusal is to have asked first.
        dry = one(project, gate, write=False)
        check("a dry run reports it refused rather than as something it would write",
              dry["answer"] == UNSTATABLE, str(dry))

    print()
    print("an entry the surface can state is registered, once")
    with tempfile.TemporaryDirectory() as tmp:
        project = _a_project(tmp)
        gate = _a_gate(entry=lambda _c: AN_ENTRY)
        state = one(project, gate, write=True)
        check("the artifact is written", state["answer"] == WRITTEN, str(state))
        check("and its entry is registered", state.get("registered") == AN_ENTRY, str(state))
        reloaded = config.load(tmp)
        check("the file still loads through the reader", AN_ENTRY in reloaded.get("host.checks"),
              str(reloaded.get("host.checks")))
        bytes_now = _read(project.config_path)
        again = one(reloaded, gate, write=True)
        check("a second run changes nothing", again["answer"] == UNCHANGED, str(again))
        check("and does not register it twice", _read(project.config_path) == bytes_now)

    print()
    print("an entry is inserted into a block list without reformatting the file")
    with tempfile.TemporaryDirectory() as tmp:
        project = _a_project(tmp, checks=[{
            "workflow": "The project's own run",
            "mirrors": "the-project-s-own-command",
            "triggers": "push -> main",
        }])
        path = project.config_path
        with open(path, encoding="utf-8") as handle:
            kept = handle.read()
        commented = kept.replace("host:\n", "host:\n  # a comment the project wrote\n")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(commented)
        project = config.load(tmp)
        refusal = register(project, AN_ENTRY)
        check("the insertion succeeds", refusal is None, str(refusal))
        after = _read(path)
        check("the project's own comment survives it",
              "# a comment the project wrote" in after)
        check("both entries are there",
              len(config.load(tmp).get("host.checks")) == 2,
              str(config.load(tmp).get("host.checks")))

    print()
    print("and into this repository's own file, which is the shape an adopter has")
    # ⛔ The arm no fixture reproduces. A dumped configuration has no comments,
    # its keys are sorted and its list sits at its key's column; a hand-written
    # one has the opposite of all three. This repository's own file is the only
    # instance of the second shape in reach, and the whole argument for a
    # textual insertion is that it keeps what a dump would take out.
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, ".claude"))
        theirs = _read(os.path.join(config.REPO_ROOT, config.CONFIG_PATH))
        with open(os.path.join(tmp, config.CONFIG_PATH), "w", encoding="utf-8") as handle:
            handle.write(theirs)
        project = config.load(tmp)
        was = len(project.get("host.checks"))
        refusal = register(project, AN_ENTRY)
        check("the insertion succeeds", refusal is None, str(refusal))
        after = _read(project.config_path)
        reloaded = config.load(tmp)
        check("the entry is the list's last member",
              reloaded.get("host.checks")[-1] == AN_ENTRY,
              str(reloaded.get("host.checks")[-1]))
        check("every entry that was there is still there",
              len(reloaded.get("host.checks")) == was + 1,
              f"{was} before, {len(reloaded.get('host.checks'))} after")
        check("every line the project wrote survives it",
              all(line in after.splitlines() for line in theirs.splitlines()),
              "a line the project wrote is gone, which is what a round trip costs")
        check("and nothing but the entry was added",
              len(after.splitlines()) - len(theirs.splitlines())
              == len(rendered_entry(AN_ENTRY, "    ")))

    print()
    print("a marked artifact is taken out by the removal step, and nothing else is")
    with tempfile.TemporaryDirectory() as tmp:
        project = _a_project(tmp)
        gate = _a_gate()
        written = one(project, gate, write=True)
        dry = removal(project, (gate,), write=False)
        check("a dry run reports the removal", dry["artifacts"][0]["answer"] == REMOVED,
              str(dry))
        check("and writes nothing", os.path.exists(written["path"]))
        taken = removal(project, (gate,), write=True)
        check("the removal takes it out", taken["artifacts"][0]["answer"] == REMOVED,
              str(taken))
        check("and the file is gone", not os.path.exists(written["path"]))

    print()
    print("a dry run of the install reports and writes nothing")
    with tempfile.TemporaryDirectory() as tmp:
        project = _a_project(tmp)
        gate = _a_gate(entry=lambda _c: AN_ENTRY)
        before = _read(project.config_path)
        dry = one(project, gate, write=False)
        check("it says what it would write", dry["answer"] == WRITTEN and dry["dry_run"],
              str(dry))
        check("the entry it would register is named", dry["registers"] == AN_ENTRY)
        check("no artifact exists", not os.path.exists(dry["path"]))
        check("and the configuration is untouched", _read(project.config_path) == before)

    print()
    print("a shape this step cannot insert into is refused by name")
    with tempfile.TemporaryDirectory() as tmp:
        project = _a_project(tmp)
        path = project.config_path
        flow = _read(path).replace("checks: []", "checks: [{workflow: A run}]")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(flow)
        refusal = _insertion(_read(path).splitlines())
        check("a flow sequence is named rather than rewritten",
              isinstance(refusal, str) and "cannot insert into" in refusal, str(refusal))
        without = _read(path).replace("checks: [{workflow: A run}]\n", "")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(without)
        refusal = _insertion(_read(path).splitlines())
        check("an absent `checks` key is named too",
              isinstance(refusal, str) and "no" in refusal.lower(), str(refusal))

    print()
    print("a host kind whose definitions are not files has nowhere to write")
    with tempfile.TemporaryDirectory() as tmp:
        project = _a_project(tmp)
        kinds = dict(check_host_checks.DEFINITIONS)
        try:
            check_host_checks.DEFINITIONS.clear()
            state = one(project, _a_gate(), write=True)
            check("it answers no place rather than guessing one",
                  state["answer"] == NO_PLACE, str(state))
            check("and nothing is written", state["path"] is None)
        finally:
            check_host_checks.DEFINITIONS.update(kinds)

    print()
    print("a project that states no configuration is told, not written into")
    with tempfile.TemporaryDirectory() as tmp:
        check("the reader says this project configures nothing",
              not config.configured(tmp))
        answered = main(["install", "--skills-root", tmp])
        check("the step exits zero rather than refusing", answered == 0, str(answered))
        check(
            "and wrote nowhere a workflow would go",
            not os.path.isdir(os.path.join(
                tmp, check_host_checks.DEFINITIONS["github"].directory,
            )),
        )

    print()
    print("the green side: a project asking for nothing is green and silent")
    with tempfile.TemporaryDirectory() as tmp:
        project = _a_project(tmp)
        quiet = run(project, (_a_gate(wanted=lambda _c: False),), write=True)
        check("nothing is reported", quiet["report"] == [], str(quiet["report"]))
        check("and the one answer is a stated absence",
              quiet["artifacts"][0]["answer"] == NOT_WANTED, str(quiet))

    print()
    print("this project's own registry, read rather than assumed")
    live = _live()
    # ⛔ Stated as an equivalence rather than as *the report is non-empty*, so
    # that the arm keeps holding when the registry grows: what it asserts is
    # that an empty registry is *named*, in whichever direction the registry is.
    said = any(
        "No artifact is registered" in line
        for line in run(live, write=False)["report"]
    )
    check(
        "an empty registry is named rather than read as a complete install",
        said == (not ARTIFACTS),
        "a step that holds nothing and prints success is the shape every check "
        "in this tree is written against",
    )
    check(
        "every registered artifact has somewhere to go in this repository",
        all(place(live, artifact) is not None for artifact in ARTIFACTS),
        "an artifact shipped with nowhere to write is one no adopter can install",
    )
    check(
        "every registered artifact's entry is one the surface can state",
        all(
            refuses_entry(live, artifact.entry(live)) is None
            for artifact in ARTIFACTS
            if artifact.entry(live) is not None
        ),
        "an artifact shipped with an unstatable entry refuses on every tree",
    )

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


def _live() -> config.Config:
    """This repository's own configuration, for the arms that read it."""
    return config.load(config.REPO_ROOT)


# --- the command line ------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="The artifacts the toolkit writes into a repository.",
    )
    parser.add_argument("--skills-root", default=".")
    parser.add_argument("--self-test", action="store_true")
    sub = parser.add_subparsers(dest="what")

    for name, help_text in (
        ("install", "write what the configuration asks for and register it"),
        ("remove", "take out every artifact carrying the marker"),
    ):
        step = sub.add_parser(name, help=help_text)
        step.add_argument("--skills-root", default=".")
        step.add_argument(
            "--dry-run", action="store_true",
            help="report what would happen and write nothing",
        )

    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()

    # ⛔ Asked before the configuration is loaded, and answered rather than
    # refused: § 7 makes an invitation the one thing an unconfigured project
    # gets, and this step is invoked by name, so whoever invoked it is owed the
    # answer that the project states nothing.
    if not config.configured(args.skills_root):
        print(json.dumps({
            "artifacts": [],
            "wrote": False,
            "report": [
                "This project states no configuration, so nothing was written. Write "
                "`.claude/mjolnir.yaml`; the keys are stated in the configuration "
                "surface shipped with the toolkit."
            ],
        }, indent=2, ensure_ascii=False))
        return 0

    try:
        configuration = config.load(args.skills_root)
    except (ConfigError, OSError) as exc:
        print(exc, file=sys.stderr)
        return 2

    write = not getattr(args, "dry_run", False)
    if args.what == "install":
        answer = run(configuration, write=write)
    elif args.what == "remove":
        answer = removal(configuration, write=write)
    else:
        answer = facet(configuration)
    print(json.dumps(answer, indent=2, ensure_ascii=False))
    return 1 if answer["report"] and args.what else 0


if __name__ == "__main__":
    sys.exit(main())
