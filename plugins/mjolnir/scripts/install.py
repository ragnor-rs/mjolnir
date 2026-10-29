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
from typing import NamedTuple

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

# ⛔ Imported for one derivation and not for a rule: what a pull request title
# opens with is stated once (§ 2) and composed once, and this step is the second
# reader of it. A pattern composed here would be free to refuse what the
# finishing role writes, which is the drift that facet exists to close.
import title_form  # noqa: E402

# ⛔ Imported for its rendering and not for its rule. The body gate's two
# artifacts are registered at the foot of this file, and what the vendored
# checker says is that module's -- this one holds the four properties above and
# reads `body_sections` through the reader like any other configured fact.
import check_body_sections  # noqa: E402

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

WORKFLOW, HOOK, SCRIPT = "workflow", "hook", "script"

# Where a generated script goes in an adopting repository, stated here once and
# nowhere else. ⛔ Unlike a workflow's directory this is **not** a host fact: no
# host and no git reads it, so there is nothing to hold it to and nothing to
# read it from. What makes it safe to state here is the pair of properties
# above it -- every file under it carries the marker, and the removal takes
# them back out, so the directory is the toolkit's for as long as a project
# asks for one artifact and gone from the tree when it stops.
TOOLKIT_DIRECTORY = ".mjolnir"

# The mode each kind's file has to carry. ⛔ A hook is **executable or git does
# not call it at all** -- newer git says so in as many words and treats the file
# as absent, so a rail installed 0644 is a rail that is not installed while the
# step reports it written. ⚠️ Measured on this module's own hook fixture: 0644,
# `os.access(..., X_OK)` false, answer `written`. A workflow file is data the
# host reads and carries no mode of its own, which is `None` here rather than a
# number nobody needs. ⚠️ **And so is a generated script**, which is run as an
# argument to an interpreter by the workflow that calls it and by the command
# `host.checks` names: nothing execs it, so a bit it does not need would be a
# mode this step then has to keep.
MODES = {HOOK: 0o755, WORKFLOW: None, SCRIPT: None}

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
# ⛔ Distinct from both of the two it used to be collapsed into. Where the place
# cannot be resolved and the project does not want the artifact, this step can
# say neither *nothing is there* nor *it was removed*: it cannot look. ⚠️
# Measured as `not wanted`, which is not in `INCOMPLETE`, so `remove` exited
# green with a marked artifact still installed — § 11's rule that a report names
# what it could not establish, arriving at the one answer that had no form.
UNDETERMINED = "could not establish whether one is installed"

# Which answers leave the install incomplete. ⛔ `waiting` is among them: the
# configuration asks for the artifact and the artifact cannot be rendered, so a
# run reporting zero is reporting a gate that is not there.
INCOMPLETE = (WAITING, OCCUPIED, UNSTATABLE, NO_PLACE, UNDETERMINED)

_ABSENT = object()

# What an artifact's `mode` says when it states none: take the kind's. ⛔ A
# sentinel rather than `None`, because `None` is itself a mode answer -- *leave
# whatever the file system gave it* -- and collapsing the two would make a
# workflow's deliberate absence of a mode indistinguishable from an artifact
# that never said.
_BY_KIND = object()


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
        registers_as: str | None = None,
        comment: str = HASH,
        mode: int | None = _BY_KIND,
    ):
        # ⛔ Refused at construction and not reported per run. `leaf` is the one
        # field that decides *where* a file lands, the registry is code in this
        # repository, and `place()` joins it onto a directory it read from the
        # host's own fact — so a leaf carrying a separator or a parent reference
        # writes outside that directory entirely. Raised here because an invalid
        # registry is a defect in this toolkit rather than a state an adopting
        # project can be in, and raising reddens every run including the gate.
        # ⚠️ Both separators, not the platform's: a registry authored on one
        # platform is installed on the other.
        if (not leaf or leaf in (os.curdir, os.pardir)
                or leaf != os.path.basename(leaf) or "/" in leaf or "\\" in leaf):
            raise ValueError(
                f"an artifact's leaf must be a bare file name; {leaf!r} is not one, "
                "and joining it would write outside the directory this step resolved."
            )
        self.name = name
        self.kind = kind
        self.leaf = leaf
        self.mode = MODES.get(kind) if mode is _BY_KIND else mode
        self.needs = needs
        # Absent, an artifact is wanted wherever its values are stated, which
        # `needs` already answers. A gate whose presence turns on a facet of
        # its own states that facet here.
        self._wanted = wanted
        self._body = body
        self._entry = entry
        # The workflow name this artifact's entry is keyed on, where that name is
        # a fact about the artifact rather than about the project. ⛔ It exists
        # because an entry cannot always be *reconstructed*: an artifact whose
        # entry is composed from the same facet that decides whether it is wanted
        # has none to compose once the project stops stating that facet, and the
        # removal path then takes out the file and leaves the entry.
        self.registers_as = registers_as
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

    def standing_entry(self, configuration: config.Config):
        """The entry this configuration already states for this artifact, or None.

        ⛔ Found by the workflow name § 2 keys the facet on, and never
        reconstructed. ⚠️ Measured as a reconstruction, on the first artifact
        whose entry is composed from the facet deciding whether it is wanted: a
        project that stopped stating the facet had its gate removed as a file and
        left as an entry — which reddens the drift check and leaves every
        consumer of the facet waiting on a run the host will never make.
        """
        if self.registers_as is not None:
            return registered_as(configuration, self.registers_as)
        # ⛔ An artifact that does not declare the name it registers under makes
        # no claim on one, so nothing here is read as its own: the workflow name
        # alone cannot tell two artifacts apart, and reading one's entry as the
        # other's to replace turns a genuine collision into a silent overwrite.
        # ⚠️ Measured on two fixture artifacts composing one workflow name — the
        # second replaced the first's entry instead of being refused.
        composed = self.entry(configuration)
        if composed is None or not already_registered(configuration, composed):
            return None
        return composed


# --- what a generated workflow says about where it runs --------------------
#
# ⛔ Read from § 2's `host.runner` and chosen nowhere here, which is that
# subsection's own rule for this step: the label, the budget and the
# supersession group come from the project, and a literal of this module's own
# beside a statement that disagrees with it is the drift the facet exists
# against.

class Template(NamedTuple):
    """What a host kind's own workflow files look like, for every generator here.

    ⛔ **Not on the surface, and deliberately.** § 2 keeps the per-kind default
    off it, a table of labels there being a second statement of the host's own
    naming -- wrong the next time the host renames one, and wrong silently.
    ⚠️ **This is the "own template" § 2 names** as where the fact does live, and
    the label is read only for a project that states no `host.runner` at all.

    ⛔ **And it is here rather than in `check_host_checks`.** That module's host
    facts are what a *reader* needs to open a definition, and § 2 states in as
    many words that a kind is added there by adding a reader and never a
    default. A label is the opposite fact: it is what a generator writes for a
    project that stated none, so it lives with the template it is written into.

    ⚠️ **One table, read by every gate this module writes.** Two of them want
    the label, so a second map of it beside this one would be the restated fact
    § 2's own drift argument is about -- stated twice here rather than once here
    and once on the surface, which is the same defect one level down.
    """

    default_label: str
    checkout: str


TEMPLATES = {"github": Template("ubuntu-latest", "actions/checkout@v4")}


def runner_of(configuration: config.Config) -> dict:
    """The label, the budget and the supersession group a generated job carries.

    ⛔ **Nothing is chosen here.** Where the project states a runner, all three
    come from it; where it states none, the label is the host kind's own default
    above and the other two are `None` -- which is § 2's statement that the facet
    bounds and retires nothing on such a project, rather than a value to invent.

    ⚠️ **A kind with no template raises rather than returning a guess**, and what
    keeps that unreachable is the suite's assertion that every kind whose
    definitions this step can write also has a label here -- not a branch, since
    a generated workflow with no `runs-on` is a file the host refuses to load.
    """
    stated = configuration.runner()
    if stated is not None:
        return {"label": stated["label"], "budget": stated["budget_minutes"],
                "group": stated["supersedes"]}
    kind = configuration.get("host.kind")
    if kind not in TEMPLATES:
        raise ValueError(
            f"no default runner label is known for the `{kind}` host kind, and § 2 "
            "keeps that default off the configuration surface -- so there is "
            "nothing to write a generated job's `runs-on` from."
        )
    return {"label": TEMPLATES[kind].default_label, "budget": None, "group": None}


def _scalar(value) -> str:
    """One YAML scalar, quoted by the emitter rather than by hand.

    ⛔ Every value a generated workflow carries goes through this. ⚠️ The one
    that makes it load-bearing is the expression a title gate enforces: it is
    composed from a project's own reference, so it carries whatever that
    reference carries -- a bracket, a brace, an apostrophe -- and a quoting rule
    written by hand here would be a second YAML emitter in a step whose output
    the host has to parse.
    """
    # ⛔ Folding off, which `width` is the only way to say. ⚠️ Measured at the
    # emitter's default: a sentence past the eightieth column came back as two
    # lines, and the second one landed at the emitter's own indent rather than
    # inside the block this scalar is written into — valid to one parser, and a
    # workflow the host may refuse to load, for a value nobody can see is long.
    dumped = yaml.safe_dump(
        [value], default_flow_style=True, allow_unicode=True, width=10 ** 6,
    ).strip()
    one_line = dumped[1:-1].strip()
    if "\n" in one_line:
        raise ValueError(
            f"a generated file's scalar came back on more than one line: {one_line!r}"
        )
    return one_line


# --- the title gate (#48) --------------------------------------------------
#
# ⛔ What the gate enforces is `title_form`'s derivation and not a pattern
# composed here: § 2 states the form once for both of its readers, and this step
# is the second reader. A pattern of this module's own would be the drift the
# facet was written to close -- a gate refusing what the finishing role writes.

TITLE_GATE_WORKFLOW = "Pull request title"
TITLE_GATE_JOB = "pull-request-title"

# The event types the gate listens for. ⛔ Procedure and not a project's list,
# per § 2: a title changes under `edited`, the commit a run answers about changes
# under `synchronize`, and the other three are the ways a pull request becomes
# one the host has no run for.
TITLE_GATE_TYPES = ("opened", "edited", "synchronize", "reopened", "ready_for_review")


def _title_gate(configuration: config.Config) -> str:
    """The workflow file that refuses a title not opening with this project's form."""
    form = title_form.form(configuration)
    where = runner_of(configuration)
    lines = [
        f"name: {_scalar(TITLE_GATE_WORKFLOW)}",
        "",
        "# Refuses a pull request whose title does not open with the work-item reference this",
        "# project states. The form is read from `host.pull_request_title`, so changing that key",
        "# changes what this file enforces and nothing here is edited by hand.",
        "",
        "on:",
        "  pull_request:",
        "    types: [" + ", ".join(TITLE_GATE_TYPES) + "]",
    ]
    # ⛔ Omitted whole where the project states every pull request, rather than
    # written as a filter matching everything: § 2 reads an omitted filter as
    # *the run covers every change*, and a `branches:` list spelling that out
    # would be a filter the facet then has to describe.
    if list(form["into"]) != [config.ANY_REF]:
        lines.append("    branches:")
        lines += [f"      - {_scalar(ref)}" for ref in form["into"]]
    lines += [
        "",
        "# Nothing is read from the repository and no credential is held: the title arrives in the",
        "# event payload, so the job needs neither a checkout nor a token.",
        "permissions: {}",
    ]
    if where["group"] is not None:
        lines += [
            "",
            "concurrency:",
            f"  group: {_scalar(where['group'])}",
            "  cancel-in-progress: true",
        ]
    lines += [
        "",
        "jobs:",
        f"  {TITLE_GATE_JOB}:",
        f"    name: {_scalar(TITLE_GATE_WORKFLOW)}",
        f"    runs-on: {_scalar(where['label'])}",
    ]
    if where["budget"] is not None:
        lines.append(f"    timeout-minutes: {where['budget']}")
    lines += [
        "    steps:",
        "      - name: Hold the title to the form this project states",
        # ⛔ The title reaches the shell as a variable and never as text
        # substituted into the script. A host expression written inside `run:` is
        # the title's own characters becoming shell, so a title carrying a
        # substitution would run it -- on a gate whose whole job is to read that
        # title.
        "        env:",
        "          TITLE: ${{ github.event.pull_request.title }}",
        f"          FORM: {_scalar(form['expression'])}",
        f"          SAYS: {_scalar(form['says'])}",
        # ⛔ Named rather than left to the runner's own default, and it is not a
        # project fact: the script below is a POSIX shell script, so which shell
        # runs it is a property of the script. ⚠️ The default differs per runner
        # platform, so a project whose stated label is a Windows one would
        # otherwise have this handed to another language entirely — a gate that
        # fails on every pull request rather than one that enforces the form.
        "        shell: bash",
        "        run: |",
        '          if printf \'%s\\n\' "$TITLE" | grep -Eq -e "$FORM"; then exit 0; fi',
        "          printf 'this title does not open with %s\\n' \"$SAYS\" >&2",
        "          printf 'it states: %s\\n' \"$TITLE\" >&2",
        "          exit 1",
    ]
    return "\n".join(lines) + "\n"


# --- the body gate's two artifacts -----------------------------------------
#
# ⛔ Everything in this block is § 20's and not this module's. What a required
# section is, which keys an entry states and what a body has to do to answer
# one are the surface's; what the vendored checker says about a body is
# `check_body_sections`'s. What is here is the pair of files that gate needs in
# a repository -- because the host runs files and nothing else -- and the
# `host.checks` entry that registers the run.

BODY_GATE_SCRIPT_LEAF = "check_body_sections.py"

# ⛔ Written with a forward slash and never joined by the platform's separator.
# It is a path **the host reads**, in a workflow file and in a `host.checks`
# entry, so a backslash from a run on the other platform would be a command no
# runner can execute and an entry naming a file nothing can find.
BODY_GATE_COMMAND = f"python3 {TOOLKIT_DIRECTORY}/{BODY_GATE_SCRIPT_LEAF}"

BODY_GATE_WORKFLOW = "Pull request body sections"
BODY_GATE_LEAF = "mjolnir-body-sections.yml"
BODY_GATE_JOB = "pull-request-body-sections"

# ⛔ The edit event is in here rather than left to the kind's defaults, and it
# is the reason this gate is a run of its own. § 20 states why: a body
# corrected in place produces no push, so without it a refusal stands on a body
# that no longer exists until something unrelated is committed.
BODY_GATE_TYPES = ("opened", "edited", "synchronize", "reopened", "ready_for_review")
BODY_GATE_TRIGGER = f"pull_request({', '.join(BODY_GATE_TYPES)}) -> *"

# The two artifacts this gate installs, named once. ⛔ Named rather than reached
# by position in the registry: every arm below asks about this pair and not about
# whatever else a later item registers beside it, and an arm indexing into the
# registry reads the wrong artifact silently the first time one is appended.
BODY_GATE_ARTIFACTS = ("body-sections-checker", "body-sections-gate")


def body_gate_wanted(configuration: config.Config) -> bool:
    """Whether this project asks for the body gate at all.

    ⛔ Read off `body_sections` and nothing else. § 20 makes `[]` a stated
    absence, so a project requiring no section is not waiting on a value -- it
    gets no gate, and that is a configuration rather than an install left half
    done.
    """
    return bool(configuration.get("body_sections"))


def body_gate_script(configuration: config.Config) -> str:
    """The vendored checker, with this project's own sections rendered in."""
    return check_body_sections.render(check_body_sections.from_config(configuration))


def body_gate_workflow(configuration: config.Config) -> str:
    """The workflow that runs the vendored checker on this host kind.

    ⛔ **No literal of this module's where the configuration states one.** The
    runner label, the budget and the supersession group come from § 2's
    `host.runner` through the reader's own accessor; a project stating no block
    gets the kind's template label and this step waits for nothing, which is §
    2's ordinary case rather than an absent value.

    ⚠️ **The body comes off the event and never out of the checkout.** A body
    edited in place fires the event again with the new text, while the checkout
    is the same commit it always was -- so reading the body from the event is
    what makes `edited` worth triggering on at all.
    """
    template = TEMPLATES[configuration.get("host.kind")]
    runner = configuration.runner()
    label = template.default_label if runner is None else runner["label"]
    lines = [
        f"name: {BODY_GATE_WORKFLOW}",
        "",
        "# This gate refuses a pull request whose body omits a section this project's",
        "# configuration requires. The sections are in the checker this runs, rendered",
        "# there from `body_sections`; nothing about them is written in this file.",
        "",
        "on:",
        "  pull_request:",
        f"    types: [{', '.join(BODY_GATE_TYPES)}]",
        "",
        "# No credential: the body arrives on the event and the checker asks the host",
        "# for nothing.",
        "permissions: {}",
        "",
    ]
    if runner is not None and runner.get("supersedes"):
        lines += [
            "concurrency:",
            f"  group: {runner['supersedes']}-${{{{ github.ref }}}}",
            "  cancel-in-progress: true",
            "",
        ]
    lines += [
        "jobs:",
        f"  {BODY_GATE_JOB}:",
        f"    name: {BODY_GATE_WORKFLOW}",
        f"    runs-on: {label}",
    ]
    if runner is not None:
        lines.append(f"    timeout-minutes: {runner['budget_minutes']}")
    lines += [
        "    steps:",
        f"      - uses: {template.checkout}",
        "        with:",
        "          persist-credentials: false",
        "",
        "      - name: Hold the body to the sections this project requires",
        "        env:",
        "          PR_BODY: ${{ github.event.pull_request.body }}",
        f"        run: {BODY_GATE_COMMAND}",
    ]
    return "\n".join(lines) + "\n"


def _title_gate_entry(configuration: config.Config) -> dict | None:
    """The `host.checks` entry the title gate registers, or None where there is none.

    ⛔ **No `mirrors`, and that is the entry's whole shape rather than a key left
    out.** There is no local command to duplicate -- the title is the host's own
    field and a tree does not carry one -- so § 2 reads this as a run with no
    local counterpart, and § 18's guard refuses no local run on its account.

    ⚠️ **`None` where the project states no form**, this entry's triggers being
    composed from the same facet that decides whether the gate is wanted. What
    finds an entry already written in that state is `registers_as` above and not
    this function, which has nothing left to compose from.
    """
    form = title_form.form(configuration)
    if form is None:
        return None
    types = ", ".join(TITLE_GATE_TYPES)
    return {
        "workflow": TITLE_GATE_WORKFLOW,
        "triggers": [f"pull_request({types}) -> {ref}" for ref in form["into"]],
    }


def body_gate_entry(configuration: config.Config) -> dict:
    """§ 2's entry for the run this gate makes.

    ⛔ It states a `mirrors`, and that is § 20's own distinction from a gate
    whose rule is a pattern over the event payload: the command named here is
    the same file the workflow runs, so a local run of it duplicates the
    host's verdict and the guard on a duplicated verdict is right to say so.
    """
    return {
        "workflow": BODY_GATE_WORKFLOW,
        "mirrors": BODY_GATE_COMMAND,
        "triggers": BODY_GATE_TRIGGER,
    }


# ⛔ The live registry. Each member is a rule somebody else's work item states,
# handed over as data: what the file says, which configured value decides whether
# it is wanted, and which `host.checks` entry registers it. This module holds the
# four properties above and reads none of them.
#
# ⚠️ **The order is load-bearing inside the body pair.** The checker is written
# before the workflow that runs it, so a run interrupted between the two leaves a
# file nothing calls rather than a workflow calling a file that is not there --
# the first is inert and the second is a red check on every change.
#
# ⚠️ **The title gate states no `needs`, and that is #68's ruling rather than an
# omission.** The two absences are told apart there: a project stating no
# `host.pull_request_title` does not want this artifact at all, and a project
# stating the block incompletely is refused by the shared reader before this step
# is reached. So there is no value that artifact could be *waiting* on -- which
# is what separates it from the body pair, whose `needs` names the one key a
# project may legitimately not have written yet.
ARTIFACTS: tuple[Artifact, ...] = (
    Artifact(
        "body-sections-checker", SCRIPT, BODY_GATE_SCRIPT_LEAF,
        needs=("body_sections",), wanted=body_gate_wanted, body=body_gate_script,
    ),
    Artifact(
        "body-sections-gate", WORKFLOW, BODY_GATE_LEAF,
        needs=("body_sections",), wanted=body_gate_wanted,
        body=body_gate_workflow, entry=body_gate_entry,
        registers_as=BODY_GATE_WORKFLOW,
    ),
    Artifact(
        name="pull-request-title",
        kind=WORKFLOW,
        leaf="mjolnir-pull-request-title.yml",
        wanted=lambda c: c.pull_request_title() is not None,
        body=_title_gate,
        entry=_title_gate_entry,
        registers_as=TITLE_GATE_WORKFLOW,
    ),
)


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
    """Where git calls *this repository's* hooks from, or None where it will not say.

    `core.hooksPath` where the **repository** states one -- a repository that has
    chosen the tracked-directory route has said so there -- and git's own answer
    otherwise, which is what makes this correct inside a worktree, where the git
    directory is not `.git` at all.

    ⛔ It decides nothing between those two routes. Which one a project ought to
    take is the hook's own work item, and a step that picked would be answering
    it in passing.

    ⛔ **`--local`, and never `--get` alone.** ⚠️ Measured: `git config --get`
    answers from the repository, the per-user scope **and** the system scope
    alike, so a developer with a machine-wide `core.hooksPath` -- an ordinary
    setup -- had this step resolve a directory shared by every repository on the
    machine, write a marked artifact into it, and later delete a file there.
    Reading the repository's own scope is the question the docstring above
    always claimed to be asking.

    ⛔ **`--type=path`, so git expands what git wrote.** ⚠️ Measured:
    `core.hooksPath` is a path-typed variable that git tilde-expands itself
    while the untyped read hands back the raw string, so a tilde-prefixed value
    was joined under the code root -- a directory named for the tilde itself
    created inside the project, and the rail written where git will never look.

    ⚠️ **A machine-wide path with no repository one is a stop and not a
    fallback.** git calls hooks from that directory, so a hook written into this
    repository's own would never run; and the directory is outside the project,
    which is not somewhere this step may write. `None` here is `place()`'s
    *nowhere*, and the answer names it.
    """
    stated = _git(code_root, "config", "--local", "--get", "--type=path",
                  "core.hooksPath")
    if stated:
        return stated if os.path.isabs(stated) else os.path.join(code_root, stated)
    elsewhere = _git(code_root, "config", "--get", "--type=path", "core.hooksPath")
    if elsewhere:
        return None
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
    if artifact.kind == SCRIPT:
        # ⛔ Always resolvable, which is the one way this kind differs from the
        # two above: nothing outside the repository decides where it goes, so
        # there is no answer here that is *nowhere*. The refusals it can still
        # meet are the shared ones -- a file there carrying no marker, a value
        # the configuration does not state.
        return os.path.join(root, TOOLKIT_DIRECTORY, artifact.leaf)
    return None


# --- the `host.checks` entry an artifact registers -------------------------


def refuses_entry(configuration: config.Config, entry: dict, replacing=None) -> str | None:
    """Why the surface cannot state this entry, or None where it can.

    ⛔ Asked of the **reader** rather than answered here. Every refusal § 2
    carries is in that one walk, and a second judgement here would be free to
    admit a shape the project's own configuration then fails to load.

    ⛔ **Which refusals those are is not listed here, and the list that was here
    is deleted rather than extended.** It named six, where the facet's own
    refusals counted off `config._planted_violations` at the moment it was
    deleted were thirty -- a lossy copy of a set living one module over, with
    nothing comparing the two. ⚠️ **The wrong remedy is the tempting one**: a
    rule added to the reader reads as something to *synchronise* into this
    docstring, which is how six of thirty came to look complete.

    ⛔ **`replacing` is this artifact's own standing entry, and it comes out
    before the new one goes in** -- which is the order the write itself runs in,
    `unregister` then `register`. Asked without it, the reader is shown the two
    entries side by side and refuses the one shape § 2 keys the facet against,
    so the step refuses for ever over its own output while naming a remedy --
    choose between the two -- that nobody can perform.

    ⚠️ **And it is the *idempotent* property that goes first, not the rewritten
    entry.** Measured by dropping the argument at the one call site: six arms
    reddened, and the ones that named it were `a second run changes nothing` and
    `a second run reports it unchanged` -- an artifact whose entry is already
    registered, byte-identical, re-read as a duplicate of itself. The pre-check
    runs on every pass, before anything asks whether the entry needs writing at
    all, so *unchanged* is the first answer a reader-side uniqueness rule takes
    away.
    """
    data = copy.deepcopy(configuration.data)
    data.setdefault("host", {})
    # ⚠️ `stated` and not `standing`: one entry is what `one()` calls the
    # standing entry, and the same word for the whole list beside it is the
    # reading this module is written against.
    stated = list(data["host"].get("checks") or [])
    if replacing is not None:
        # ⛔ The first copy and not every equal one: a facet legitimately states
        # one entry, so dropping all matches would be this step deciding what a
        # project wrote. There can be no second copy anyway, the reader now
        # refusing the shape -- but a pre-check that relies on that is a second
        # statement of it.
        for index, existing in enumerate(stated):
            if existing == replacing:
                del stated[index]
                break
    data["host"]["checks"] = stated + [entry]
    # ⛔ Every failure is an answer with the entry named, which is what this step
    # promises. ⚠️ Caught as `ConfigError` alone, an entry the reader cannot even
    # be *shown* — one carrying a value no safe dump represents — left this
    # function raising, so the module delivered a stack trace where it had
    # stated a refusal. Nothing is left behind either way, the pre-check running
    # before any write, but a traceback is not the named answer.
    try:
        config.load_text(yaml.safe_dump(data, allow_unicode=True), ".", check_paths=False)
    except ConfigError as exc:
        return str(exc)
    except Exception as exc:                     # noqa: BLE001 - naming it is the point
        return (
            f"this entry cannot be put to the reader at all: {type(exc).__name__}: {exc}"
        )
    return None


def already_registered(configuration: config.Config, entry: dict) -> bool:
    """Whether this exact entry is already stated, content and all.

    ⛔ Full equality and not the workflow name, which is the stricter of the two
    on purpose: an entry whose content a project's own edit has changed is one
    this step has to rewrite, and matching on the key alone would report it
    registered while the facet described a run the file no longer makes.
    """
    return any(
        existing == entry for existing in (configuration.get("host.checks") or [])
    )


def registered_as(configuration: config.Config, workflow: str) -> dict | None:
    """The entry this configuration states under `workflow`, or None.

    ⛔ The complement of the test above, and keyed on the one name § 2 keys the
    facet on. It answers the question a *removal* has — which entry did this
    artifact write — where full equality cannot, the content being gone with the
    facet that composed it.
    """
    for existing in (configuration.get("host.checks") or []):
        if isinstance(existing, dict) and existing.get("workflow") == workflow:
            return existing
    return None


CHECKS = re.compile(r"^(?P<indent>\s+)checks:(?P<rest>.*)$")
HOST = re.compile(r"^host:(?P<rest>.*)$")
MEMBER = re.compile(r"^(?P<indent>\s*)-\s")

# A comment opening at the end of a line's value. ⛔ Space-hash and not a bare
# hash, which is YAML's own rule and the reason a `#` inside a value is not a
# comment. ⚠️ Measured against the surface's own § 2 example block, which writes
# `checks:` with a trailing comment on it: read as part of the value, that line
# is refused as a shape this step cannot insert into — a refusal naming a
# comment as the facet's value, on the shape an adopter copies.
TRAILING = re.compile(r"(?:^|\s)#.*$")


def _value(rest: str) -> str:
    """What a key's line states, with any trailing comment taken off."""
    return TRAILING.sub("", rest).strip()


def _depth(line: str) -> int:
    return len(line) - len(line.lstrip())


def _blank(line: str) -> bool:
    """Whether this line carries nothing the walk below should read.

    ⛔ A comment counts, **at any indentation**. YAML puts no indentation rule
    on one, so a comment flush with the left margin sits legally inside an
    indented block — and a walk that stopped at the first unindented line
    answered *`host:` states no `checks` key* about a file that states one.
    """
    return not line.strip() or line.lstrip().startswith("#")


def _members(lines: list[str]) -> tuple[int, str, list[tuple[int, int]]] | str:
    """(the `checks:` line, the member indent, one span per member) or a refusal.

    One walk behind both the insertion and the removal, so the two cannot
    disagree about where a member begins and ends. ⛔ Textual and not a round
    trip: re-dumping the file would take out every comment a project wrote about
    its own facts, and the terminator its lines are written with, which is a loss
    no run reports and nobody asked for.

    ⚠️ **The member indent is read off the list and never derived from the
    key's.** A block sequence may sit at its key's own column or one in from
    it — both are the same document, and the two shapes occur in this tree — so
    an indent computed as *the key plus two* writes a member the file cannot
    parse against a list written the other way.
    """
    host = next(
        (i for i, line in enumerate(lines) if HOST.match(line)
         and _value(HOST.match(line).group("rest")) == ""),
        None,
    )
    if host is None:
        return "no `host:` block opens a line, so there is nowhere to register an entry."
    for index in range(host + 1, len(lines)):
        line = lines[index]
        if _blank(line):
            continue
        if not line[:1].isspace():
            break
        found = CHECKS.match(line)
        if not found:
            continue
        indent, rest = found.group("indent"), _value(found.group("rest"))
        if rest == "[]":
            return index, indent + "  ", []
        if rest != "":
            return (
                f"`host.checks` is written as {rest!r}, which this step cannot insert "
                "into. A block list, or an empty list written `[]`, are the two shapes "
                "it reads."
            )
        member, spans = None, []
        for after in range(index + 1, len(lines)):
            following = lines[after]
            if _blank(following):
                continue
            opens = MEMBER.match(following)
            depth = _depth(following)
            if member is None:
                if opens and depth >= len(indent):
                    member = opens.group("indent")
                    spans.append((after, after))
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
                spans.append((after, after))
                continue
            if depth > len(member):
                spans[-1] = (spans[-1][0], after)
                continue
            break
        return index, member if member is not None else indent + "  ", spans
    return "`host:` states no `checks` key, so there is nowhere to register an entry."


def _insertion(lines: list[str]) -> tuple[int, str, bool] | str:
    """(the line to insert after, the member indent, whether `[]` is to be replaced)."""
    found = _members(lines)
    if isinstance(found, str):
        return found
    index, member, spans = found
    if not spans:
        # ⚠️ Either `checks: []`, which is replaced, or a key with nothing under
        # it — which the reader refuses as a facet, so the only file in that
        # shape is one this step is about to make loadable.
        return index, member, _value(CHECKS.match(lines[index]).group("rest")) == "[]"
    return spans[-1][1], member, False


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
    # ⛔ Read and written with newline translation off, and rejoined with the
    # terminator the file already used. ⚠️ Measured: translation on,
    # `splitlines()` drops every `\r` and the rejoin writes `\n`, so a project
    # whose file is written with the other terminator has **every line** of it
    # changed by a step whose stated property is that it edits rather than
    # re-renders. The trailing newline is preserved for the same reason: a file
    # that ended without one is a byte different for a reason nothing asked for.
    with open(path, encoding="utf-8", newline="") as handle:
        before = handle.read()
    terminator = "\r\n" if "\r\n" in before else "\n"
    lines = before.splitlines()
    found = _insertion(lines)
    if isinstance(found, str):
        return found
    after, indent, replace = found
    written = list(lines)
    if replace:
        written[after] = written[after].split("checks:")[0] + "checks:"
    written[after + 1:after + 1] = rendered_entry(entry, indent)
    text = terminator.join(written)
    if before.endswith(("\n", "\r")):
        text += terminator
    return _written_back(configuration, path, before, text, entry, present=True)


def unregister(configuration: config.Config, entry: dict) -> str | None:
    """Take one entry back out of this project's own configuration file.

    ⛔ The inverse half of `register`, and it exists because without it removal
    took out one of the two things installing wrote. ⚠️ Measured: a gate turned
    off, or the plugin retired, left a `host.checks` entry naming a workflow the
    repository no longer contains — which reddens the drift gate and leaves
    every consumer of the facet waiting on a run the host will never make.

    ⚠️ **An emptied list is written `[]` and never left bare.** A key with
    nothing under it reads as `null`, which the reader refuses, so taking out
    the last member without that would hand the project a file none of its roles
    can load.
    """
    path = configuration.config_path
    if path is None:
        return "this configuration came from text rather than a file, so there is nothing to write."
    with open(path, encoding="utf-8", newline="") as handle:
        before = handle.read()
    terminator = "\r\n" if "\r\n" in before else "\n"
    lines = before.splitlines()
    found = _members(lines)
    if isinstance(found, str):
        return found
    index, _member, spans = found
    for start, end in spans:
        block = "\n".join(line[len(_member):] for line in lines[start:end + 1])
        try:
            read = yaml.safe_load("- " + block.lstrip("- ").lstrip())
        except yaml.YAMLError:
            continue
        if not (isinstance(read, list) and read and read[0] == entry):
            continue
        written = lines[:start] + lines[end + 1:]
        if len(spans) == 1:
            written[index] = written[index].split("checks:")[0] + "checks: []"
        text = terminator.join(written)
        if before.endswith(("\n", "\r")):
            text += terminator
        return _written_back(configuration, path, before, text, entry, present=False)
    return (
        f"`host.checks` states no entry matching the one this artifact registered, so "
        f"there is nothing to take out: {entry}"
    )


def _written_back(
    configuration: config.Config,
    path: str,
    before: str,
    text: str,
    entry: dict,
    *,
    present: bool,
) -> str | None:
    """Write the file, read it back, and restore it where the read disagrees.

    ⛔ Restored on two conditions and not one. A file that stops loading is the
    obvious half; the other is a file that loads and **does not carry the
    change** — ⚠️ measured on a configuration stating `host:` twice, where the
    textual walk takes the first block and the parser keeps the last, so the
    entry was inserted into a block the reader discards. `register` then
    reported success, `already_registered` stayed false for ever, and every
    later run appended another copy of the entry to a project's own file while
    reporting a clean install.
    """
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    try:
        reloaded = config.load(configuration.skills_root)
    except (ConfigError, OSError) as exc:
        with open(path, "w", encoding="utf-8", newline="") as handle:
            handle.write(before)
        return f"the entry was written and the file then would not load, so it was put back: {exc}"
    if already_registered(reloaded, entry) is not present:
        with open(path, "w", encoding="utf-8", newline="") as handle:
            handle.write(before)
        return (
            "the file was edited, still loads, and does not carry the change — the "
            "block this step wrote into is not the one the parser reads, so it was "
            "put back. A configuration stating `host:` or `checks:` twice is the "
            "measured shape."
        )
    return None


# ⛔ No guard of this step's own on a workflow name the facet already states. It
# had one, and it was written because the shared reader loaded that shape; the
# reader now refuses it, so a second test here would be a second statement of one
# rule -- free to drift from it, and the drift would show up as an install the
# project's own file then refuses to load. What is left of it is `replacing`
# above, which is this step's fact rather than § 2's: that an artifact's own
# standing entry is what the write replaces.


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

    ⛔ **And `wanted` is asked before the place is resolved.** ⚠️ Measured the
    other way round: an artifact a project explicitly does **not** want, on a
    host kind whose definitions are not files, reported *no place to write it* —
    an incompleteness, and a non-zero exit — about a gate nobody asked for.
    """
    asked = artifact.wanted(configuration)
    path = place(configuration, artifact)
    if path is None:
        if not asked:
            return _state(
                artifact, UNDETERMINED, None,
                because="the project does not ask for this artifact and this step "
                        "cannot resolve where one would be, so it can say neither "
                        "that none is installed nor that one was taken out",
            )
        return _state(
            artifact, NO_PLACE, None,
            because="this host kind keeps its definitions somewhere this step cannot "
                    "write, which § 2 states as an answer rather than a gap"
            if artifact.kind == WORKFLOW else
            "git did not say where this repository's own hooks are called from, or "
            "says they are called from outside this repository",
        )

    here = None
    if os.path.exists(path):
        with open(path, encoding="utf-8") as handle:
            here = handle.read()

    if not asked:
        if here is None:
            return _state(artifact, NOT_WANTED, path)
        if not _marked(here):
            return _state(artifact, OCCUPIED, path,
                          because="a file is there carrying no marker, so it is the "
                                  "project's own and is neither removed nor written over")
        if write:
            os.remove(path)
            _swept(path, artifact)
            # ⛔ The entry is found the way `standing_entry` finds one and never
            # by composing it and testing equality: that test is still in there
            # for an artifact declaring no `registers_as`, so this site loses
            # none of it while gaining the by-name lookup a withdrawn facet
            # needs.
            standing = artifact.standing_entry(configuration)
            if standing is not None:
                refusal = unregister(configuration, standing)
                if refusal is not None:
                    return _state(artifact, REMOVED, path, entry=standing,
                                  because=f"the artifact was removed and its entry was "
                                          f"not: {refusal}")
                return _state(artifact, REMOVED, path, unregistered=standing)
        return _state(artifact, REMOVED, path)

    absent = artifact.absent_values(configuration)
    if absent:
        return _state(artifact, WAITING, path, values=absent,
                      standing=here is not None,
                      because="the configuration asks for this artifact and states no "
                              "value for what it would say, so it is not written")

    entry = artifact.entry(configuration)
    # This artifact's own earlier entry, where it wrote one. ⛔ Read before the
    # pre-check and passed to it: the step's own output under its own key is what
    # it replaces, not something the reader should be shown beside the new entry.
    standing = artifact.standing_entry(configuration) if entry is not None else None
    if entry is not None:
        refusal = refuses_entry(configuration, entry, replacing=standing)
        if refusal is not None:
            return _state(artifact, UNSTATABLE, path, entry=entry, because=refusal)

    if here is not None and not _marked(here):
        return _state(artifact, OCCUPIED, path,
                      because="a file is already there carrying no marker. § 2 makes "
                              "that a stop: it is the project's own file, and a "
                              "generated artifact neither joins it nor replaces it")

    wanted_text = rendered(artifact, artifact.body(configuration))
    needs_entry = entry is not None and not already_registered(configuration, entry)
    if here == wanted_text and not needs_entry and _mode_holds(path, artifact):
        return _state(artifact, UNCHANGED, path)

    if not write:
        return _state(artifact, WRITTEN, path, dry_run=True,
                      registers=entry if needs_entry else None)

    made = _place_it(path, wanted_text, artifact)

    if needs_entry:
        # ⛔ An earlier entry of this artifact's comes out before the new one goes
        # in, and in that order: two entries under one workflow name are the one
        # shape § 2's key cannot be read through, so a run that appended first
        # would leave the project's own file carrying it between two writes.
        if standing is not None and standing != entry:
            refusal = unregister(configuration, standing)
            if refusal is not None:
                _put_back(path, here, made)
                return _state(artifact, UNSTATABLE, path, entry=entry,
                              because=f"the artifact was taken back out because the entry "
                                      f"it had already registered could not be replaced: "
                                      f"{refusal}")
            configuration = config.load(configuration.skills_root)
        refusal = register(configuration, entry)
        if refusal is not None:
            _put_back(path, here, made)
            return _state(artifact, UNSTATABLE, path, entry=entry,
                          because=f"the artifact was taken back out because its entry "
                                  f"could not be registered: {refusal}")
        return _state(artifact, WRITTEN, path, registered=entry, mode=artifact.mode,
                      replaced=standing if standing != entry else None)

    return _state(artifact, WRITTEN, path, mode=artifact.mode)


def _mode_holds(path: str, artifact: Artifact) -> bool:
    """Whether the file already carries the mode this artifact states.

    ⛔ Part of what *unchanged* means, not a step after it. A file whose bytes
    match and whose mode does not is a hook git will not call, and reporting it
    unchanged would leave it that way for ever.
    """
    if artifact.mode is None:
        return True
    try:
        import stat
        return stat.S_IMODE(os.stat(path).st_mode) == artifact.mode
    except OSError:
        return False


def _place_it(path: str, text: str, artifact: Artifact) -> str | None:
    """Write the artifact where it goes, atomically. Returns any directory made.

    ⛔ Through a temporary sibling and `os.replace`, which is atomic on one file
    system. ⚠️ Measured as a truncating open: an interruption between the
    truncate and the write leaves an **unmarked** file — `_marked("")` is false
    — so from then on every run answers *a file is already there carrying no
    marker, it is the project's own* about this step's own debris, and no run
    will ever write or remove it.
    """
    directory = os.path.dirname(path)
    made = None if os.path.isdir(directory) else directory
    os.makedirs(directory, exist_ok=True)
    handle, temporary = tempfile.mkstemp(dir=directory, prefix=".mjolnir-", suffix=".tmp")
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="") as opened:
            opened.write(text)
        if artifact.mode is not None:
            os.chmod(temporary, artifact.mode)
        os.replace(temporary, path)
    except BaseException:
        if os.path.exists(temporary):
            os.remove(temporary)
        raise
    return made


def _swept(path: str, artifact: Artifact) -> None:
    """Take the toolkit's own directory out once its last artifact has gone.

    ⛔ **Only the toolkit's own, and only when it is empty.** A workflow
    directory and a hooks directory are the *project's* -- the toolkit writes
    into them and does not own them -- so an empty one there is the project's
    to keep. The directory this kind writes into exists because the toolkit
    asked for it, and a project that stops asking for every artifact in it is
    owed the directory back: an empty directory left standing is the orphan the
    removable property is about, one level up from the file.
    """
    if artifact.kind != SCRIPT:
        return
    directory = os.path.dirname(path)
    if os.path.basename(directory) != TOOLKIT_DIRECTORY:
        return
    try:
        if not os.listdir(directory):
            os.rmdir(directory)
    except OSError:
        # Something else is in it, or it is gone already. Neither is this
        # step's to report: what it promised was the file, and the directory
        # is a courtesy it takes only where it is unambiguous.
        pass


def _put_back(path: str, here: str | None, made: str | None) -> None:
    """Undo `_place_it`, including the directory it created where it created one.

    ⚠️ The directory half is small and is the difference between *nothing left
    behind* being true and being nearly true: an install refused after creating
    the host's own directory leaves an empty one in a project that said no.
    """
    if here is None:
        os.remove(path)
    else:
        with open(path, "w", encoding="utf-8", newline="") as handle:
            handle.write(here)
    if made and os.path.isdir(made) and not os.listdir(made):
        os.rmdir(made)


def run(
    configuration: config.Config,
    artifacts: tuple[Artifact, ...] = None,
    *,
    write: bool,
) -> dict:
    """Every artifact brought to the state this configuration asks for.

    ⛔ The configuration is **re-read after any artifact that registered**, and
    not carried forward. ⚠️ Measured: carried forward, the second artifact of a
    run validates against a configuration missing the first's entry, so two
    artifacts registering one workflow name were both written and the file then
    carried the collision § 2 keys the facet to prevent.

    ⛔ **What the registry's order means is *install* order, so the artifacts a
    configuration no longer asks for come out in the reverse of it and before
    anything is written.** ⚠️ A registry may hold an artifact that only works
    while a sibling is there -- a workflow calling a checker is the shipped
    case -- and walking one order for both directions produces exactly the
    intermediate state the order exists to avoid: the called file gone and the
    caller still installed, which is a red check on every change rather than
    something inert. ⚠️ **The report stays in registry order** whichever order
    the acts were taken in, a reader of it reading a registry rather than a
    schedule.
    """
    members = ARTIFACTS if artifacts is None else artifacts
    wanted, unwanted = [], []
    for index, artifact in enumerate(members):
        (wanted if artifact.wanted(configuration) else unwanted).append((index, artifact))
    # ⛔ Keyed by position and never by name: two members may legitimately carry
    # one name -- a fixture list does -- and a name-keyed answer would report
    # one artifact's state twice while losing the other's.
    by_position = {}
    for index, artifact in list(reversed(unwanted)) + wanted:
        state = one(configuration, artifact, write=write)
        by_position[index] = state
        if write and state.get("registered") is not None:
            try:
                configuration = config.load(configuration.skills_root)
            except (ConfigError, OSError):
                # The write was already verified by a load inside `register`, so
                # a failure here is the file having moved under the run. Leave
                # the configuration as it stands rather than guessing.
                pass
    states = [by_position[index] for index in range(len(members))]
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
    """Take out every artifact carrying the marker, and its entry, and nothing else.

    ⛔ **Two things installing wrote, so two things removal takes out.** ⚠️
    Measured with only the file: a retired plugin left a `host.checks` entry
    naming a workflow the repository no longer contains, which reddens the drift
    gate and leaves every consumer of the facet waiting on a run the host will
    never make.

    ⛔ **And a place that cannot be resolved is not *nothing is there*.** ⚠️
    Measured as `not wanted`, which is no incompleteness, so this step exited
    green with a marked artifact still installed in a tree it could not look at.

    ⛔ **The registry is walked in the reverse of its install order**, for the
    reason `run` above states: an artifact that only works while a sibling is
    there comes out before that sibling, never after it. ⚠️ The report is still
    in registry order, as it is there.
    """
    members = ARTIFACTS if artifacts is None else artifacts
    by_position: dict[int, dict] = {}

    def answered(index: int, state: dict) -> None:
        by_position[index] = state

    for index, artifact in reversed(list(enumerate(members))):
        path = place(configuration, artifact)
        if path is None:
            answered(index, _state(
                artifact, UNDETERMINED, None,
                because="this step cannot resolve where this artifact would be, so it "
                        "can say neither that none is installed nor that one was taken "
                        "out",
            ))
            continue
        if not os.path.exists(path):
            answered(index, _state(artifact, NOT_WANTED, path))
            continue
        with open(path, encoding="utf-8") as handle:
            here = handle.read()
        if not _marked(here):
            answered(index, _state(
                artifact, OCCUPIED, path,
                because="a file is there carrying no marker, so it is the project's own "
                        "and this step does not remove it",
            ))
            continue
        standing = artifact.standing_entry(configuration)
        if not write:
            answered(index, _state(artifact, REMOVED, path, dry_run=True,
                                   unregisters=standing))
            continue
        os.remove(path)
        _swept(path, artifact)
        if standing is not None:
            refusal = unregister(configuration, standing)
            if refusal is not None:
                answered(index, _state(
                    artifact, REMOVED, path, entry=standing,
                    because=f"the artifact was removed and its entry was not: {refusal}",
                ))
                continue
            configuration = config.load(configuration.skills_root)
            answered(index, _state(artifact, REMOVED, path, unregistered=standing))
            continue
        answered(index, _state(artifact, REMOVED, path))
    states = [by_position[index] for index in range(len(members))]
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


A_TITLE_FORM = {
    "reference": f"[A-KEY-{config.PLACEHOLDER}]",
    "repeated": True,
    "into": ["release/*"],
}

# The same facet with `into` stating every pull request, which is the arm where a
# generated gate carries no `branches:` filter at all.
EVERY_PULL_REQUEST = {**A_TITLE_FORM, "into": [config.ANY_REF]}

A_RUNNER = {
    "label": "a-runner-label",
    "concurrent_jobs": 1,
    "budget_minutes": 45,
    "supersedes": "a-supersession-group",
}


def _a_project(tmp: str, checks=None, title=None, runner=None) -> config.Config:
    """A loadable configuration in a tree of its own.

    Built from an example rather than written here, for the reason the sibling
    consumer's fixtures are: a planted configuration the reader beside this
    module would refuse makes every answer below an answer about nothing.
    """
    with open(os.path.join(config.EXAMPLES, "github-issues.yaml"), encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    data["roots"] = {"code": "."}
    data.setdefault("host", {})["kind"] = "github"
    data["host"]["checks"] = [] if checks is None else checks
    # ⚠️ Each is popped rather than left as the example wrote it, so an arm asking
    # for the absent case gets one whichever example this fixture is built from.
    data["host"].pop("pull_request_title", None)
    data["host"].pop("runner", None)
    if title is not None:
        data["host"]["pull_request_title"] = title
    if runner is not None:
        data["host"]["runner"] = runner
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


def _registered(name: str) -> Artifact:
    """The live registry's member under this name.

    ⛔ By name and never by position. The registry is the one place a new
    artifact lands, so an arm indexing into it reads whichever artifact the
    next item happens to append before it -- and the failure is silent, the
    suite asserting a workflow's properties against a script.
    """
    for artifact in ARTIFACTS:
        if artifact.name == name:
            return artifact
    raise AssertionError(
        f"no artifact named {name!r} is registered; the registry states "
        f"{[artifact.name for artifact in ARTIFACTS]}"
    )


def _answers_of(report: dict) -> dict:
    """A report's artifact states, keyed by the name each was registered under."""
    return {state["artifact"]: state for state in report["artifacts"]}


def _answer_of(answers: dict, name: str):
    """One artifact's answer out of those, by name and tolerantly.

    ⛔ Tolerant because an arm reading a name nothing registered has to
    **report** rather than raise. ⚠️ Measured: a mistyped member of the carrier
    list below came back as a `KeyError` out of the first arm that indexed it —
    a traceback, which is the one answer a check may not give, and which leaves
    every arm after it unrun. What names the mistake is the precondition beside
    the arms; what keeps it a verdict is this.
    """
    return answers.get(name, {}).get("answer")


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


# The surface, read by one arm below for the shape its own § 2 example block is
# written in. ⛔ Read from the reader's constant rather than joined here, so a
# move of the file is one statement and not two.
SURFACE_BLOCK = config.SURFACE


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
    """Every place this source reads from whoever ran it, by name.

    ⚠️ **What it does not reach, stated rather than left to read as covered**: a
    question *delegated* to another module. It reads this module's own source and
    matches a bare call or an attribute by name, so `somewhere.ask(...)` or a
    read of file descriptor zero through `os.read` is invisible to it. The
    direct forms are held; the indirect ones are a reader's.
    """
    import ast

    found = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id in ASKING:
            found.append(node.func.id)
        if isinstance(node, ast.Attribute) and node.attr in A_STREAM + ASKING:
            found.append(node.attr)
    return sorted(set(found))


def _reads_definitions(source: str) -> bool:
    """Whether this source actually reads the sibling module's host fact.

    ⛔ Read as a tree. ⚠️ Measured as `"check_host_checks.DEFINITIONS" in own`:
    the assertion has to write the name down in order to look for it, so the
    conjunct was true however the module behaved — the same self-match the
    directory half of the arm had already been corrected for, left standing in
    the clause beside it.
    """
    import ast

    for node in ast.walk(ast.parse(source)):
        if (isinstance(node, ast.Attribute) and node.attr == "DEFINITIONS"
                and isinstance(node.value, ast.Name)
                and node.value.id == check_host_checks.__name__.rsplit(".", 1)[-1]):
            return True
    return False


def _spells_in_source(source: str, values) -> list[str]:
    """Any of `values` this source writes into a string literal of its own.

    ⛔ Read as a tree rather than matched in the text, for the reason `_spells`
    below is: an arm that has to write down what it forbids finds its own list.
    What it is for is the acceptance this module's one registered gate carries —
    a generated file holding no literal the configuration does not state.
    """
    import ast

    literals = {
        node.value for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    return sorted({
        value for value in values
        if any(value in literal for literal in literals)
    })


def _as_the_host_would(document: dict, job: str, title: str):
    """Run a generated job's one step as a shell, with the title in the environment.

    ⛔ The step's own script and its own `env`, read out of the file rather than
    retyped: what this asserts is the **gate**, and a reimplementation of its
    logic here would be a second gate passing while the generated one refused.
    ⚠️ The host's own expression is substituted the way the host substitutes it —
    into the environment and never into the script — which is also the property
    the arm beside this one holds.

    Returns the exit status, or None where the shell did not answer, which is
    this suite's second unchecked precondition after git.
    """
    step = document["jobs"][job]["steps"][0]
    environment = {
        key: title if "${{" in str(value) else str(value)
        for key, value in step["env"].items()
    }
    try:
        done = subprocess.run(
            ["sh", "-c", step["run"]],
            env={**os.environ, **environment},
            capture_output=True, text=True, check=False,
        )
    except OSError:
        return None
    return done.returncode


def _restate(configuration: config.Config, title) -> config.Config:
    """This fixture's own file with its title facet changed, the rest left alone.

    ⚠️ Not `_a_project` again: that writes the file from an example, which would
    take out the entry the install just registered — and the arms below are about
    what happens to that entry when the facet it was composed from moves.
    """
    with open(configuration.config_path, encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if title is None:
        data["host"].pop("pull_request_title", None)
    else:
        data["host"]["pull_request_title"] = title
    with open(configuration.config_path, "w", encoding="utf-8") as handle:
        handle.write(yaml.safe_dump(data, allow_unicode=True))
    return config.load(configuration.skills_root)


def _spells(source: str, directories) -> list[str]:
    """Any host directory this source writes down itself, whole or in parts.

    ⛔ By **component** and not by the whole path. ⚠️ Measured: an arm matching
    the joined spelling inside a quoted literal was defeated by the idiom this
    codebase actually uses — `os.path.join(".github", "workflows")`, which is
    how the sibling module itself writes it — so the literal never appears and
    the arm reported nothing while the module carried the fact.
    """
    import ast

    literals = {
        node.value for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    found = []
    for directory in directories:
        parts = [part for part in directory.replace("\\", "/").split("/") if part]
        if directory in literals or any(part in literals for part in parts):
            found.append(directory)
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
    # ⛔ Both halves computed from the fact rather than matched as text, and
    # both for the same reason: a forbidding arm has to write down what it
    # forbids and then finds its own list. ⚠️ Each was measured defeated. The
    # read half was `"check_host_checks.DEFINITIONS" in own`, true however the
    # module behaved. The spelling half matched the joined literal only, and the
    # idiom this codebase uses is `os.path.join(".github", "workflows")` — the
    # sibling module's own spelling — so nothing was ever found.
    spelled = _spells(own, [w.directory for w in check_host_checks.DEFINITIONS.values()])
    check(
        "the sibling module's host fact is what this module reads",
        _reads_definitions(own),
        "nothing here reads that fact, so the directory below is this module's own",
    )
    check(
        "where a host kind keeps its definitions is not written here",
        not spelled,
        f"this module spells {spelled} itself, whole or in parts, which is free "
        "to disagree with the check that holds the facet to those files",
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
        # ⛔ Against the two things the marker has to say, not against the
        # function that produced it. ⚠️ Measured as `== marker_lines(gate)`:
        # both sides move together, so the arm held the head's position and
        # line count and nothing about its content — a build identifier added to
        # the head line, and `REMOVAL` emptied to one character, each left the
        # suite green.
        head = text.splitlines()[:2]
        check("the marker names the artifact", any(gate.name in line for line in head),
              repr(head))
        check("and says what takes it out",
              any("install.py" in line and "remove" in line for line in head),
              repr(head))
        check(
            "and carries nothing that moves between runs",
            not re.search(r"\d{4}-\d{2}-\d{2}|\b[0-9a-f]{7,40}\b|\bv?\d+\.\d+", text),
            "a date, a commit or a version in the head line is the record of a "
            "pass an artifact may not carry, and would make every run a change",
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
    print("a hook is executable, or git does not call it at all")
    with tempfile.TemporaryDirectory() as tmp:
        import stat
        project = _a_project(tmp)
        _a_repository(project.code_root)
        rail = _a_rail()
        state = one(project, rail, write=True)
        mode = stat.S_IMODE(os.stat(state["path"]).st_mode)
        check("the file carries the mode its kind states", mode == MODES[HOOK], oct(mode))
        check("and is executable, which is what git tests",
              os.access(state["path"], os.X_OK),
              "git treats a non-executable hook as absent, so a rail installed "
              "without the bit is a rail that is not installed")
        os.chmod(state["path"], 0o644)
        again = one(project, rail, write=True)
        check("a file whose bytes match and whose mode does not is not unchanged",
              again["answer"] == WRITTEN, str(again))
        check("and the mode is put back",
              os.access(state["path"], os.X_OK))
        gate = one(project, _a_gate(), write=True)
        check("a workflow file is left whatever mode the file system gave it",
              _a_gate().mode is None and gate["answer"] == WRITTEN)

    print()
    print("the artifact is placed atomically, so a half-written file is never its own")
    with tempfile.TemporaryDirectory() as tmp:
        project = _a_project(tmp)
        gate = _a_gate()
        state = one(project, gate, write=True)
        directory = os.path.dirname(state["path"])
        check("no temporary sibling is left behind",
              [n for n in os.listdir(directory)] == [gate.leaf],
              str(os.listdir(directory)))
        check("an empty file would not read as this step's own, which is why it is atomic",
              not _marked("") and not _marked("\n"))
        # ⛔ The directory half of *nothing left behind*, and it has to be
        # asserted on the route that **writes**. ⚠️ Measured against a pre-check
        # refusal: nothing is written, so no directory is ever created and the
        # arm passed with the clean-up switched off. The route that creates one
        # is the post-write rollback — a `host.checks` the reader accepts and
        # the textual walk refuses.
        with tempfile.TemporaryDirectory() as second:
            other = _a_project(second)
            path = other.config_path
            with open(path, encoding="utf-8") as handle:
                flow = handle.read().replace(
                    "checks: []",
                    "checks: [{workflow: A run, mirrors: one, "
                    "triggers: 'pull_request -> *'}]",
                )
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(flow)
            other = config.load(second)
            refused = one(other, _a_gate(entry=lambda _c: AN_ENTRY), write=True)
            check("the post-write route is the one taken", refused["answer"] == UNSTATABLE,
                  str(refused))
            check("a refused install leaves no artifact", not os.path.exists(refused["path"]))
            check("and no directory it created",
                  not os.path.isdir(os.path.dirname(refused["path"])),
                  str(os.path.dirname(refused["path"])))

    print()
    print("git's own answer, and the two ways of reading it wrongly")
    with tempfile.TemporaryDirectory() as tmp:
        project = _a_project(tmp)
        _a_repository(project.code_root)
        # ⚠️ A worktree, which is the shape the arm beside this one used to
        # claim and never exercised: its git directory is not `.git`, so a
        # module that spelled that path answered about the wrong place.
        subprocess.run(["git", "-C", project.code_root, "commit", "--allow-empty",
                        "-m", "a fixture commit", "--no-gpg-sign"],
                       capture_output=True, check=False,
                       env=dict(os.environ, GIT_AUTHOR_NAME="a", GIT_AUTHOR_EMAIL="a@a",
                                GIT_COMMITTER_NAME="a", GIT_COMMITTER_EMAIL="a@a"))
        tree = os.path.join(tmp, "a-worktree")
        made = subprocess.run(
            ["git", "-C", project.code_root, "worktree", "add", "--detach", tree],
            capture_output=True, text=True, check=False)
        check("the fixture worktree was created", made.returncode == 0,
              made.stderr.strip()[:200])
        answered = hook_directory(tree)
        check("a worktree resolves to the repository's own hooks directory, not its own",
              answered is not None and os.path.isdir(answered)
              and not answered.startswith(os.path.join(tree, ".git")),
              str(answered))
        check("and it is not a path this module spelled",
              answered == _git(tree, "rev-parse", "--git-path", "hooks"),
              str(answered))
        # ⚠️ Assembled rather than written as a literal: a tilde-prefixed path
        # spelled out here is a path under somebody's home directory to the
        # sweep that forbids one, which has no absent case and no exception for
        # a fixture.
        tilde = "~" + os.sep + "a-fixture-hooks-dir"
        subprocess.run(["git", "-C", project.code_root, "config",
                        "core.hooksPath", tilde], capture_output=True)
        check(
            "a tilde is expanded by git rather than joined under the project",
            hook_directory(project.code_root) == os.path.expanduser(tilde),
            f"{hook_directory(project.code_root)} — read untyped, git hands back the "
            "raw string and the join makes a directory named for the tilde itself",
        )
        subprocess.run(["git", "-C", project.code_root, "config", "--unset",
                        "core.hooksPath"], capture_output=True)
        # ⛔ A scope outside the repository is **planted** rather than looked
        # for. ⚠️ Measured as *either nothing states one or this answers None*,
        # which passes vacuously on a machine where nothing does — so the arm
        # held nothing, and reading every scope again left it green.
        machine_wide = os.path.join(tmp, "a-machine-wide-gitconfig")
        with open(machine_wide, "w", encoding="utf-8") as handle:
            handle.write("[core]\n\thooksPath = " + os.path.join(tmp, "elsewhere") + "\n")
        was = os.environ.get("GIT_CONFIG_GLOBAL")
        try:
            os.environ["GIT_CONFIG_GLOBAL"] = machine_wide
            elsewhere = _git(project.code_root, "config", "--get", "core.hooksPath")
            check("the fixture's machine-wide scope is visible to git",
                  elsewhere is not None, "the plant did not take, so the arm below "
                                         "would hold nothing")
            check(
                "a machine-wide hooks path is a stop rather than a place to write",
                hook_directory(project.code_root) is None,
                f"a scope outside the repository states {elsewhere!r} and this step "
                f"resolved {hook_directory(project.code_root)!r} — git calls hooks from "
                "there, so a hook written into this repository would never run, and "
                "that directory is outside the project",
            )
            subprocess.run(["git", "-C", project.code_root, "config",
                            "core.hooksPath", "a-repository-hooks-dir"],
                           capture_output=True)
            check(
                "and the repository's own scope still wins over it",
                hook_directory(project.code_root)
                == os.path.join(project.code_root, "a-repository-hooks-dir"),
                str(hook_directory(project.code_root)),
            )
        finally:
            if was is None:
                os.environ.pop("GIT_CONFIG_GLOBAL", None)
            else:
                os.environ["GIT_CONFIG_GLOBAL"] = was

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
    print("a stated absence is not a missing value, and both shapes of one are held")
    with tempfile.TemporaryDirectory() as tmp:
        project = _a_project(tmp)
        gate = _a_gate(needs=("host.checks",))
        state = one(project, gate, write=True)
        check(
            "an empty list satisfies `needs` and the artifact is written",
            state["answer"] == WRITTEN,
            "read as a missing value, every legitimate absence would wait forever",
        )
        # ⛔ The other half of the rule's own sentence — «an empty list **and an
        # explicit absence**» — asserted at the function rather than through a
        # fixture, because the reader refuses a bare `null` at every key that
        # has an absent case, so no loadable configuration reaches this clause.
        # ⚠️ Stated rather than left to read as covered: the clause is a guard
        # against a shape the reader does not currently permit.
        absent = Artifact("a-fixture", WORKFLOW, "a-fixture.yml",
                          needs=("host.a_value_stated_null",))
        stated = _a_project(tmp)
        stated.data.setdefault("host", {})["a_value_stated_null"] = None
        check(
            "a value stated as an explicit absence is a missing one to `needs`",
            absent.absent_values(stated) == ["host.a_value_stated_null"],
            str(absent.absent_values(stated)),
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
    print("the terminator and the trailing newline a project's file already used")
    with tempfile.TemporaryDirectory() as tmp:
        project = _a_project(tmp)
        path = project.config_path
        body = _read(path)
        with open(path, "w", encoding="utf-8", newline="") as handle:
            handle.write(body.replace("\n", "\r\n"))
        was = open(path, "rb").read().count(b"\r")
        project = config.load(tmp)
        check("the insertion succeeds on the other terminator",
              register(project, AN_ENTRY) is None)
        now = open(path, "rb").read().count(b"\r")
        check(
            "and every line still carries it",
            now >= was,
            f"{was} carriage returns before, {now} after — a step whose stated "
            "property is that it edits rather than re-renders changed every line",
        )
    with tempfile.TemporaryDirectory() as tmp:
        project = _a_project(tmp)
        path = project.config_path
        # ⛔ Read before the open that truncates. The first form of this read
        # the file inside the write call's own argument list, so it read the
        # file the `w` mode had already emptied and planted nothing at all.
        unterminated = _read(path).rstrip("\n")
        with open(path, "w", encoding="utf-8", newline="") as handle:
            handle.write(unterminated)
        project = config.load(tmp)
        register(project, AN_ENTRY)
        check("a file that ended without a newline still does",
              not _read(path).endswith("\n"))

    print()
    print("a leaf that is not a bare file name is refused at construction")
    for planted in ("../escaped.yml", "a/escaped.yml", "a\\escaped.yml", "", ".", ".."):
        try:
            _a_gate(leaf=planted)
            refused = False
        except ValueError:
            refused = True
        check(f"a leaf of {planted!r} is refused", refused,
              "place() would join it onto the directory the host's fact stated "
              "and write outside it")
    check(
        "and every registered artifact's leaf is a bare file name",
        all(artifact.leaf == os.path.basename(artifact.leaf) for artifact in ARTIFACTS),
    )

    print()
    print("two artifacts cannot register one workflow name between them")
    with tempfile.TemporaryDirectory() as tmp:
        project = _a_project(tmp)
        second = dict(AN_ENTRY, mirrors="a-second-fixture-command")
        states = run(project, (
            _a_gate(entry=lambda _c: AN_ENTRY),
            _a_gate(name="a-second-gate", leaf="a-second-gate.yml",
                    entry=lambda _c: second),
        ), write=True)["artifacts"]
        check("the first is written", states[0]["answer"] == WRITTEN, str(states[0]))
        check("the second is refused", states[1]["answer"] == UNSTATABLE, str(states[1]))
        check("the collision is named, with the workflow name in it",
              repr(AN_ENTRY["workflow"]) in states[1].get("because", ""),
              states[1].get("because", ""))
        names = [e["workflow"] for e in config.load(tmp).get("host.checks")]
        check("and the file carries the name once", len(names) == len(set(names)), str(names))
        check("the second artifact was not written", not os.path.exists(states[1]["path"]))
    # ⛔ Where that refusal comes from, asserted rather than assumed: it is the
    # shared reader's, which is why this module carries no guard of its own on a
    # repeated workflow name. ⚠️ The fixture builder *loads* what it writes, so
    # the refusal arrives as the exception it raises -- which is the assertion.
    with tempfile.TemporaryDirectory() as tmp:
        try:
            _a_project(tmp, checks=[
                {"workflow": "A run", "mirrors": "one", "triggers": "pull_request -> *"},
                {"workflow": "A run", "mirrors": "two", "triggers": "pull_request -> *"},
            ])
            reader_refusal = None
        except ConfigError as exc:
            reader_refusal = str(exc)
        check("the shared reader refuses two entries keyed on one name",
              reader_refusal is not None
              and "host.checks[1].workflow" in reader_refusal,
              str(reader_refusal))
    # ⛔ The green side of that refusal, and the reason the pre-check is asked
    # `replacing`: an artifact rewriting its own entry under its own name is not
    # a collision with itself. ⚠️ Measured by changing what the entry says
    # between two runs, which is what a project editing the facet the entry is
    # composed from does to it. ⛔ The fixture declares `registers_as`, as every
    # shipped artifact that registers one does -- asserted of the registry by an
    # arm below, and the reason that assertion is load-bearing: an artifact
    # without it cannot find its own standing entry once the content has changed,
    # so this is the by-name lookup's own green side.
    with tempfile.TemporaryDirectory() as tmp:
        project = _a_project(tmp)
        first = dict(AN_ENTRY)
        second = dict(AN_ENTRY, mirrors="a-rewritten-fixture-command")
        gate = _a_gate(entry=lambda _c: first, registers_as=AN_ENTRY["workflow"])
        one(project, gate, write=True)
        project = config.load(tmp)
        check("the first run registered the entry",
              first in project.get("host.checks"), str(project.get("host.checks")))
        again = one(project, _a_gate(entry=lambda _c: second,
                                     registers_as=AN_ENTRY["workflow"]), write=True)
        check("the second run is not refused over its own standing entry",
              again["answer"] == WRITTEN, str(again))
        left = config.load(tmp).get("host.checks")
        check("the rewritten entry replaced it rather than joining it",
              left == [second], str(left))

    print()
    print("removal takes out both things installing wrote")
    with tempfile.TemporaryDirectory() as tmp:
        project = _a_project(tmp)
        gate = _a_gate(entry=lambda _c: AN_ENTRY)
        one(project, gate, write=True)
        check("the entry is there after the install",
              AN_ENTRY in config.load(tmp).get("host.checks"))
        taken = removal(config.load(tmp), (gate,), write=True)
        check("the removal reports the entry it took out",
              taken["artifacts"][0].get("unregistered") == AN_ENTRY,
              str(taken["artifacts"][0]))
        left = config.load(tmp).get("host.checks")
        check("and the entry is gone", AN_ENTRY not in left, str(left))
        check("the emptied list is written `[]` rather than left bare",
              left == [] and "checks: []" in _read(project.config_path),
              repr(left))
    with tempfile.TemporaryDirectory() as tmp:
        project = _a_project(tmp)
        unwanted_entry = _a_gate(entry=lambda _c: AN_ENTRY)
        one(project, unwanted_entry, write=True)
        off = one(config.load(tmp), _a_gate(wanted=lambda _c: False,
                                            entry=lambda _c: AN_ENTRY), write=True)
        check("turning a gate off takes its entry out too",
              off.get("unregistered") == AN_ENTRY, str(off))
        check("and the facet no longer states it",
              AN_ENTRY not in config.load(tmp).get("host.checks"))
    with tempfile.TemporaryDirectory() as tmp:
        project = _a_project(tmp, checks=[{
            "workflow": "The project's own run",
            "mirrors": "the-project-s-own-command",
            "triggers": "push -> main",
        }])
        gate = _a_gate(entry=lambda _c: AN_ENTRY)
        one(project, gate, write=True)
        removal(config.load(tmp), (gate,), write=True)
        kept = config.load(tmp).get("host.checks")
        check("a project's own entry beside it is untouched",
              [e["workflow"] for e in kept] == ["The project's own run"], str(kept))

    print()
    print("a place that cannot be resolved is not nothing being there")
    with tempfile.TemporaryDirectory() as tmp:
        project = _a_project(tmp)
        kinds = dict(check_host_checks.DEFINITIONS)
        try:
            check_host_checks.DEFINITIONS.clear()
            taken = removal(project, (_a_gate(),), write=True)
            check("the removal says it could not establish it",
                  taken["artifacts"][0]["answer"] == UNDETERMINED,
                  str(taken["artifacts"][0]))
            check("and that is an incompleteness rather than a clean run",
                  UNDETERMINED in INCOMPLETE and bool(taken["report"]))
            # ⛔ The other side of the same ordering: an artifact the project
            # does not want must not be an incompleteness merely because this
            # step cannot locate it — it reports what it could not establish,
            # and `wanted` is asked before the place is resolved.
            unwanted = run(project, (_a_gate(wanted=lambda _c: False),), write=True)
            check("an unwanted artifact is not reported as having nowhere to go",
                  unwanted["artifacts"][0]["answer"] != NO_PLACE,
                  str(unwanted["artifacts"][0]))
        finally:
            check_host_checks.DEFINITIONS.update(kinds)

    print()
    print("the two routes that put the artifact and the file back")
    with tempfile.TemporaryDirectory() as tmp:
        # ⛔ The **post-write** rollback, which no arm reached: the three
        # unstatable arms above all use an entry the reader refuses before any
        # write, so they pass because nothing was written rather than because
        # anything was taken back out. This route is a `host.checks` the reader
        # accepts and the textual walk refuses — a non-empty flow sequence.
        project = _a_project(tmp)
        path = project.config_path
        flow = _read(path).replace(
            "checks: []",
            "checks: [{workflow: A run, mirrors: one, triggers: 'pull_request -> *'}]",
        )
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(flow)
        project = config.load(tmp)
        check("the configuration loads in that shape",
              len(project.get("host.checks")) == 1)
        gate = _a_gate(entry=lambda _c: AN_ENTRY)
        check("the reader does not refuse the entry, so the pre-check passes it",
              refuses_entry(project, AN_ENTRY) is None)
        state = one(project, gate, write=True)
        check("the install is refused after the write", state["answer"] == UNSTATABLE,
              str(state))
        check("and the artifact was taken back out",
              not os.path.exists(state["path"]),
              "every artifact whose entry cannot be inserted would otherwise be "
              "orphaned in the adopter's tree")
        check("and the configuration is untouched", _read(path) == flow)

    print()
    print("a file that loads and does not carry the change is put back")
    with tempfile.TemporaryDirectory() as tmp:
        # ⚠️ `host:` twice: the textual walk takes the first block and the
        # parser keeps the last, so the entry lands in a block the reader
        # discards. Measured without the read-back: `register` reported success,
        # `already_registered` stayed false for ever, and every later run
        # appended another copy to the project's own file.
        project = _a_project(tmp)
        path = project.config_path
        doubled = _read(path).replace(
            "host:", "host:\n  checks: []\nhost:", 1)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(doubled)
        try:
            project = config.load(tmp)
            loads = True
        except ConfigError:
            loads = False
        check("the doubled-key fixture loads", loads)
        if loads:
            refusal = register(project, AN_ENTRY)
            check("the insertion is refused rather than reported as a success",
                  refusal is not None, str(refusal))
            check("and the file is byte-identical", _read(path) == doubled)

    print()
    print("an entry the reader cannot be shown is named, not raised")
    with tempfile.TemporaryDirectory() as tmp:
        project = _a_project(tmp)

        class Unrepresentable:
            pass

        try:
            answered = refuses_entry(
                project, {"workflow": "A run", "mirrors": Unrepresentable()})
            raised = None
        except Exception as error:               # noqa: BLE001 - that is the finding
            answered, raised = None, error
        check("a refusal comes back rather than an exception", raised is None,
              f"{type(raised).__name__}: {raised}" if raised else "")
        check("and it names what could not be put to the reader",
              isinstance(answered, str) and "cannot be put to the reader" in answered,
              str(answered))

    print()
    print("register's own read-back puts a file that stops loading back")
    with tempfile.TemporaryDirectory() as tmp:
        # ⛔ The route reaches the read-back and not the pre-check, and the
        # difference is which copy each one reads. The pre-check validates a
        # dump of the configuration **in hand**; the read-back loads the **file**.
        # So the branch is reached wherever the file has moved under the step —
        # here a `checks_local` entry added to the file after it was loaded,
        # which § 17 refuses beside a `host.checks` entry mirroring the same
        # command. ⚠️ The first form of this arm assumed § 2 refuses two entries
        # mirroring one command; measured, it does not, so that route passed the
        # pre-check *and* the read-back and reached neither.
        project = _a_project(tmp)
        path = project.config_path
        colliding = "a-colliding-command"
        with open(path, encoding="utf-8") as handle:
            on_disk = handle.read()
        moved = on_disk.replace(
            "checks_local: []",
            "checks_local:\n- command: " + colliding
            + "\n  proves: a fixture verdict\n",
        )
        check("the fixture's own file states a local check", moved != on_disk)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(moved)
        entry = {"workflow": "A run", "mirrors": colliding,
                 "triggers": "pull_request -> *"}
        check("the pre-check passes it, the configuration in hand stating no local check",
              refuses_entry(project, entry) is None,
              str(refuses_entry(project, entry)))
        refusal = register(project, entry)
        check("the read-back refuses it", refusal is not None, str(refusal))
        check("and names that the file was put back",
              isinstance(refusal, str) and "put back" in refusal, str(refusal))
        check("and the file is byte-identical", _read(path) == moved,
              "a configuration half-edited by an installer is a project whose "
              "every role then refuses, for a reason none of them can name")

    print()
    print("a comment on the key's own line is a comment, not the facet's value")
    # ⛔ The shape the surface's own § 2 example block is written in. ⚠️
    # Measured reading the whole of the line after the key: the step answered
    # «`host.checks` is written as '# the host's own runs…', which this step
    # cannot insert into» — a refusal naming a comment as the facet's value, on
    # the shape an adopter copies out of the schema.
    with open(SURFACE_BLOCK, encoding="utf-8") as handle:
        example = next(
            (line for line in handle
             if line.lstrip().startswith("checks:") and "#" in line),
            None,
        )
    check("the surface's own example block writes `checks:` with a trailing comment",
          example is not None, "the shape this arm is written for is not there any more")
    lines = [
        "host:  # the code host",
        "  kind: github",
        example.rstrip("\n") if example else "  checks:  # a trailing comment",
        "    - workflow: \"CI\"",
        "      mirrors: \"a-command\"",
    ]
    found = _insertion(lines)
    check("a trailing comment on both keys still finds the list",
          not isinstance(found, str), str(found))
    check("and the member indent is the list's own",
          not isinstance(found, str) and found[1] == "    ", str(found))
    # ⚠️ And a comment flush with the left margin inside the block, which YAML
    # permits and the walk used to stop at.
    flush = ["host:", "  kind: github", "# a comment the project wrote",
             "  checks:", "    - workflow: \"CI\"", "      mirrors: \"a-command\""]
    check("a comment at column zero inside the block does not end it",
          not isinstance(_insertion(flush), str), str(_insertion(flush)))

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
              isinstance(refusal, str) and "which this step cannot insert into" in refusal,
              str(refusal))
        without = _read(path).replace("checks: [{workflow: A run}]\n", "")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(without)
        # ⛔ Against the sentence and not against a word every sentence shares.
        # ⚠️ Measured as `"no" in refusal.lower()`, which all four of this
        # walk's refusals satisfy — two of them through *cannot* — so the arm
        # asserted only that some string came back, and returning the wrong
        # reason left it green.
        refusal = _insertion(_read(path).splitlines())
        check("an absent `checks` key is named as that and not as something else",
              isinstance(refusal, str) and "states no `checks` key" in refusal,
              str(refusal))
        refusal = _insertion(["kind: github"])
        check("an absent `host:` block is named as that",
              isinstance(refusal, str) and "no `host:` block" in refusal, str(refusal))
        refusal = _insertion(["host:", "  checks:", "    workflow: A run"])
        check("a block of keys under `checks:` is named as that",
              isinstance(refusal, str) and "opens a block of keys" in refusal,
              str(refusal))

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
            # ⛔ Read off the file system and not off the answer. ⚠️ Measured as
            # `state["path"] is None`, which restates the literal the `NO_PLACE`
            # branch passes to its own constructor — a statement about the
            # answer wearing the label of a statement about the tree.
            check(
                "and nothing was written anywhere under the project",
                not any(
                    name for root, _dirs, files in os.walk(project.code_root)
                    for name in files if name.endswith((".yml", ".yaml"))
                    and os.path.join(root, name) != project.config_path
                ),
                "a file was written despite there being nowhere stated to write it",
            )
        finally:
            check_host_checks.DEFINITIONS.update(kinds)

    print()
    print("a project that states no configuration is told, not written into")
    with tempfile.TemporaryDirectory() as tmp:
        check("the reader says this project configures nothing",
              not config.configured(tmp))
        answered = main(["install", "--skills-root", tmp])
        check("the step exits zero rather than refusing", answered == 0, str(answered))
        # ⛔ Asked with a registry that would otherwise write, so the arm turns
        # on the invitation and not on the registry being empty. ⚠️ Measured
        # with the live registry: switching the unconfigured branch off left
        # this arm green, because there was nothing to write either way.
        check(
            "and nothing was written where a workflow would go",
            not os.path.isdir(os.path.join(
                tmp, check_host_checks.DEFINITIONS["github"].directory,
            )),
        )
        try:
            config.load(tmp)
            resolved = True
        except (ConfigError, OSError):
            resolved = False
        check("because the step never reached a configuration to read", not resolved)

    print()
    print("the title gate: written from the facet, and from no literal here")
    # ⛔ That every writable kind has a template is asserted once, further down
    # with the rest of the registry's own preconditions -- the claim this gate
    # needs and the claim the body gate needs being the same claim, and a second
    # copy of it here the restated fact the single-source check is about.
    check(
        "every registered artifact declares the name it registers under",
        all(
            artifact.registers_as is not None or artifact._entry is None
            for artifact in ARTIFACTS
        ),
        "an artifact composing an entry and declaring no key cannot have that "
        "entry found again once the facet composing it is gone",
    )
    with tempfile.TemporaryDirectory() as tmp:
        project = _a_project(tmp, title=A_TITLE_FORM)
        gate = _registered("pull-request-title")
        written = one(project, gate, write=True)
        check("a project stating a title form gets the gate",
              written["answer"] == WRITTEN, str(written))
        text = _read(written["path"])
        document = yaml.safe_load(text)
        check("and the file the host has to parse parses", isinstance(document, dict),
              repr(text[:200]))
        block = document.get(True, document.get("on"))
        check("its event block is a pull request, with the types procedure states",
              set(block["pull_request"]["types"]) == set(TITLE_GATE_TYPES),
              repr(block))
        check("and `edited` is among them, or a title fixed in place never re-runs",
              "edited" in block["pull_request"]["types"], repr(block))
        check("its branch filter is what the project stated",
              block["pull_request"]["branches"] == A_TITLE_FORM["into"], repr(block))
        check("it holds no credential at all", document["permissions"] == {},
              repr(document.get("permissions")))
        job = document["jobs"][TITLE_GATE_JOB]
        check("and the job runs on this host kind's own default",
              job["runs-on"] == TEMPLATES["github"].default_label, repr(job))
        check("with no budget and no supersession group, the project stating none",
              "timeout-minutes" not in job and "concurrency" not in document,
              repr(document))
        # ⛔ The acceptance this item was filed on, asserted on the file's own
        # bytes: what the gate enforces is the derivation beside this module, and
        # the expression appears in no literal here. ⚠️ Read as a string constant
        # of this module's source rather than matched in it — an arm that writes
        # down the expression it forbids finds its own list.
        environment = job["steps"][0]["env"]
        check(
            "what it enforces is the one derivation and not a pattern composed here",
            environment["FORM"] == title_form.form(project)["expression"],
            repr(environment),
        )
        # ⛔ Round-tripped rather than eyeballed, and on every value: the emitter
        # folds a long scalar by default, and a folded one comes back out of the
        # host's parser as whatever that parser made of the continuation line.
        check(
            "and every value reads back out of the file as it went in",
            environment["SAYS"] == title_form.form(project)["says"],
            repr(environment),
        )
        # ⛔ Each on one line of the file, which is the half a round trip through
        # this tree's own parser cannot show. ⚠️ Measured at the emitter's default
        # width: a sentence past the eightieth column was folded, and the
        # continuation landed at an indent one parser accepted and the host's own
        # may not — so the arm is on the line and not on the value.
        check(
            "and sits whole on one line, the emitter folding nothing",
            all(
                any(f"{key}: {_scalar(environment[key])}" == line.strip()
                    for line in text.splitlines())
                for key in ("FORM", "SAYS")
            ),
            repr([line for line in text.splitlines() if "SAYS" in line]),
        )
        check(
            "and that expression is in no literal of this module's",
            not _spells_in_source(own, [environment["FORM"],
                                        A_TITLE_FORM["reference"]]),
            "a literal here is free to disagree with the form the finishing role "
            "renders a title from",
        )
        check(
            "the title reaches the shell as a variable, never as text in the script",
            "${{" in environment["TITLE"]
            and "${{" not in job["steps"][0]["run"],
            repr(job["steps"][0]),
        )
        entry = config.load(tmp).get("host.checks")
        check("the entry is registered", entry == [gate.entry(project)], repr(entry))
        check(
            "and it mirrors no local command, which is the entry's whole shape",
            "mirrors" not in entry[0] and "jobs" not in entry[0],
            repr(entry[0]),
        )
        # ⛔ The other half of that, read through the shared reader rather than by
        # eye: § 18's guard matches a *command*, so an entry mirroring none is one
        # it can never refuse a local run on.
        standing = config.load(tmp)
        check(
            "so no mirrored command names it, and that guard matches nothing of it",
            all(record["command"] for record in standing.mirrors())
            and TITLE_GATE_WORKFLOW not in [r["workflow"] for r in standing.mirrors()],
            repr(standing.mirrors()),
        )
        check(
            "while the facet still states the run, which the drift check reads",
            TITLE_GATE_WORKFLOW in [r["workflow"] for r in standing.host_runs()],
            repr(standing.host_runs()),
        )
        again = one(standing, gate, write=True)
        check("a second run reports it unchanged", again["answer"] == UNCHANGED, str(again))
        check("and the file is byte-identical", _read(written["path"]) == text)

        # ⛔ The gate itself run, rather than its text read. ⚠️ Every arm above
        # holds the *file*, and a file whose expression is right and whose script
        # inverts the test is a gate that refuses every correct title while every
        # one of those arms stays green. The shell on PATH is this suite's second
        # unchecked precondition, so what it answered is asserted first.
        passing = _as_the_host_would(document, TITLE_GATE_JOB, "[A-KEY-48] A title")
        check(
            "the shell answered, which this arm's assertions rest on",
            passing is not None,
            "`sh` did not run the generated step, so the two arms below would "
            "hold nothing",
        )
        if passing is not None:
            check("a title opening with the form passes the generated gate",
                  passing == 0, f"the step exited {passing}")
            for refused in ("A title with no reference", "[A-KEY-x] A title",
                            "[A-KEY-48]", " [A-KEY-48] A title"):
                status = _as_the_host_would(document, TITLE_GATE_JOB, refused)
                check(f"and {refused!r} is refused by it", status == 1,
                      f"the step exited {status}")
            # ⛔ The title's own characters are data to that script and never
            # shell, and the arm is on a title the form *refuses*: one it accepts
            # would exit zero either way, which is a green that says nothing.
            # ⚠️ The title is the one field this gate exists to read, so a title
            # that could end the command and start another would run on every
            # pull request of a project that installed the gate.
            for dangerous in ('A title"; exit 0 #', "A title $(exit 0)",
                              "A title `exit 0`", "-v A title"):
                status = _as_the_host_would(document, TITLE_GATE_JOB, dangerous)
                check(f"a refused title spelled {dangerous!r} is read, not run",
                      status == 1, f"the step exited {status}")

    print()
    print("the gate's own facts come from the project, and are chosen nowhere here")
    with tempfile.TemporaryDirectory() as tmp:
        project = _a_project(tmp, title=EVERY_PULL_REQUEST, runner=A_RUNNER)
        state = one(project, _registered("pull-request-title"), write=True)
        document = yaml.safe_load(_read(state["path"]))
        block = document.get(True, document.get("on"))
        check(
            "a project holding every pull request gets no branch filter at all",
            "branches" not in block["pull_request"],
            repr(block),
        )
        job = document["jobs"][TITLE_GATE_JOB]
        check("a stated runner's label is what the job asks for",
              job["runs-on"] == A_RUNNER["label"], repr(job))
        check("its budget is what the job is given",
              job["timeout-minutes"] == A_RUNNER["budget_minutes"], repr(job))
        check(
            "and its supersession group is the workflow's, cancelling what is running",
            document["concurrency"] == {"group": A_RUNNER["supersedes"],
                                        "cancel-in-progress": True},
            repr(document.get("concurrency")),
        )
        check(
            "the trigger registered states every pull request in the ref vocabulary",
            config.load(tmp).get("host.checks")[0]["triggers"]
            == [f"pull_request({', '.join(TITLE_GATE_TYPES)}) -> {config.ANY_REF}"],
            repr(config.load(tmp).get("host.checks")),
        )

    print()
    print("the facet edited, and the facet withdrawn")
    with tempfile.TemporaryDirectory() as tmp:
        project = _a_project(tmp, title=A_TITLE_FORM)
        one(project, _registered("pull-request-title"), write=True)
        # ⛔ A project editing the half of the facet the entry carries gets the
        # entry replaced. ⚠️ Measured as a collision: the step's own output under
        # its own key read as a second entry, so the install refused for ever and
        # named a remedy — choose between the two — nobody could perform.
        edited = dict(A_TITLE_FORM, into=["release/*", "main"])
        state = one(_restate(project, edited), _registered("pull-request-title"), write=True)
        check("an edited facet is written rather than refused",
              state["answer"] == WRITTEN, str(state))
        entries = config.load(tmp).get("host.checks")
        check("and exactly one entry stands under the workflow name",
              [e["workflow"] for e in entries].count(TITLE_GATE_WORKFLOW) == 1,
              repr(entries))
        check("which is the edited one",
              entries[0]["triggers"][-1].endswith("main"), repr(entries))
        # ⛔ The facet withdrawn: both things installing wrote come back out.
        # ⚠️ This is the arm the first registered artifact was needed for — an
        # entry composed from the facet deciding wantedness cannot be
        # reconstructed once that facet is gone, so a reconstruction took out the
        # file and left the entry.
        gone = one(_restate(project, None), _registered("pull-request-title"), write=True)
        check("withdrawing the facet removes the gate", gone["answer"] == REMOVED, str(gone))
        check("and the file is gone", not os.path.exists(gone["path"]))
        left = config.load(tmp).get("host.checks")
        check("and its entry with it", left == [], repr(left))

    print()
    print("the green side: a project stating no title form gets no gate")
    with tempfile.TemporaryDirectory() as tmp:
        silent = _a_project(tmp, title=None)
        answered = run(silent, write=True)
        check("nothing is reported", answered["report"] == [], str(answered["report"]))
        # ⛔ This gate's own answer, found by name. The fixture's example states
        # sections as well as a title form, so the report carries the body pair
        # beside this one -- and an arm reading the first member would be
        # answering about whichever artifact the registry happens to list first.
        silent_answers = _answers_of(answered)
        check("and the gate's answer is a stated absence",
              _answer_of(silent_answers, "pull-request-title") == NOT_WANTED,
              str(answered))
        check("nothing was written where it would have gone",
              not os.path.exists(place(silent, _registered("pull-request-title"))))
        # ⛔ No entry **under this gate's name**, rather than an empty facet: the
        # body pair legitimately registers one in the same fixture, and asserting
        # the facet empty would make this arm red for somebody else's artifact.
        check("and the facet states no entry for it",
              registered_as(config.load(tmp), TITLE_GATE_WORKFLOW) is None,
              str(config.load(tmp).get("host.checks")))
        # ⛔ The plant verified rather than asserted: the same fixture with the
        # facet stated has to answer the other way, or this green side is green
        # about a step that writes nothing for anybody.
        with tempfile.TemporaryDirectory() as other:
            stated = _a_project(other, title=A_TITLE_FORM)
            check(
                "while the same fixture stating one does get it, so the green side holds",
                one(stated, _registered("pull-request-title"), write=True)["answer"] == WRITTEN,
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
    print("the body gate: two artifacts, and neither written where none is wanted")
    with tempfile.TemporaryDirectory() as tmp:
        # ⛔ The fixture states a section, which is what makes the arms below
        # about a gate rather than about an absence. ⚠️ Asserted first: read
        # from an example that stopped stating one, every arm here would pass
        # on nothing being wanted.
        asking = _a_project(tmp)
        check("the fixture project states a section to require",
              bool(asking.get("body_sections")),
              "the example this fixture is built from states none, so the arms "
              "below would hold nothing")
        # ⛔ The pair held to the registry before anything reads it. ⚠️ Asserted
        # here and not with the registry's other preconditions, which run after
        # these arms: a mistyped member would be named only once every arm
        # reading it had already reported about an artifact that is not there.
        registered = {artifact.name for artifact in ARTIFACTS}
        check(
            "and both members of the pair name artifacts the registry holds",
            set(BODY_GATE_ARTIFACTS) <= registered,
            f"{sorted(set(BODY_GATE_ARTIFACTS) - registered)} is named by the pair "
            f"and registered by nothing; the registry states {sorted(registered)}",
        )
        done = run(asking, write=True)
        answers = _answers_of(done)
        check("both artifacts are written",
              all(_answer_of(answers, name) == WRITTEN
                  for name in BODY_GATE_ARTIFACTS),
              str(done["artifacts"]))
        check("and the install reports nothing incomplete", done["report"] == [],
              str(done["report"]))
        script = answers["body-sections-checker"]["path"]
        flow = answers["body-sections-gate"]["path"]
        check("the checker lands under the toolkit's own directory",
              script == os.path.join(asking.code_root, TOOLKIT_DIRECTORY,
                                     BODY_GATE_SCRIPT_LEAF), script)
        check("the workflow lands where this host kind keeps its definitions",
              flow == os.path.join(
                  asking.code_root,
                  check_host_checks.DEFINITIONS["github"].directory, BODY_GATE_LEAF),
              flow)
        stated = asking.get("body_sections")
        check("the checker carries the headings this project stated",
              all(entry["heading"] in _read(script) for entry in stated))
        # ⛔ The acceptance bullet, held on the artifact rather than on the
        # renderer: the workflow is the file a reader meets first, and a
        # heading in it would be a project's vocabulary in a file this step
        # regenerates from a different source.
        check(
            "and the workflow carries none of them",
            not any(entry["heading"] in _read(flow) for entry in stated),
            "a heading literal in the generated workflow is one the gate would "
            "then enforce from two places",
        )
        check("the entry registered mirrors the command the workflow runs",
              answers["body-sections-gate"].get("registered", {}).get("mirrors")
              == BODY_GATE_COMMAND and BODY_GATE_COMMAND in _read(flow),
              str(answers["body-sections-gate"].get("registered")))
        again = _answers_of(run(config.load(tmp), write=True))
        check("a second run changes nothing",
              all(_answer_of(again, name) == UNCHANGED
                  for name in BODY_GATE_ARTIFACTS),
              str([again.get(name) for name in BODY_GATE_ARTIFACTS]))
        # ⛔ The facet held to the file it describes, by the check that holds
        # it everywhere else. ⚠️ This is the arm that would have caught a
        # trigger written one way in the entry and another in the template --
        # two statements of one fact, which is the drift that check exists for.
        drift = check_host_checks.run(check_host_checks.read_subject(tmp))
        check("the generated workflow and its entry do not drift",
              not any(drift.values()),
              str({k: v for k, v in drift.items() if v}))

    print()
    print("what a sibling depends on comes out first, and the directory with it")
    with tempfile.TemporaryDirectory() as tmp:
        # ⛔ The order is read off the acts rather than off the report, which is
        # in registry order by design. ⚠️ Measured with one order for both
        # directions: the checker went first, so an interruption between the
        # two left a workflow calling a file that was not there — a red check
        # on every change, which is the state the install order exists to
        # avoid and which walking it forwards reproduced exactly.
        project = _a_project(tmp)
        run(project, write=True)
        taken: list[str] = []
        real = os.remove

        def watched(path, _real=real):
            taken.append(os.path.basename(path))
            _real(path)

        os.remove = watched
        try:
            removal(config.load(tmp), write=True)
        finally:
            os.remove = real
        check(
            "the workflow is taken out before the checker it calls",
            taken.index(BODY_GATE_LEAF) < taken.index(BODY_GATE_SCRIPT_LEAF),
            str(taken),
        )
        check(
            "and the toolkit's own directory does not outlive its last artifact",
            not os.path.isdir(os.path.join(project.code_root, TOOLKIT_DIRECTORY)),
            "an empty directory left standing is the orphan the removable "
            "property is about, one level up from the file",
        )
        check(
            "while the project's own workflow directory is left alone",
            os.path.isdir(os.path.join(
                project.code_root, check_host_checks.DEFINITIONS["github"].directory)),
            "that directory is the project's, and an empty one there is theirs to keep",
        )
    with tempfile.TemporaryDirectory() as tmp:
        # ⛔ The same order on the other route: a configuration that stops
        # asking removes through `run`, not through `removal`, and the two were
        # measured walking opposite orders with only one of them corrected.
        project = _a_project(tmp)
        run(project, write=True)
        turned_off = config.load(tmp)
        turned_off.data["body_sections"] = []
        order: list[str] = []
        real = os.remove

        def noted(path, _real=real):
            order.append(os.path.basename(path))
            _real(path)

        os.remove = noted
        try:
            answered_off = run(turned_off, write=True)
        finally:
            os.remove = real
        off = _answers_of(answered_off)
        check("turning the gate off takes both artifacts out",
              [_answer_of(off, name) for name in BODY_GATE_ARTIFACTS]
              == [REMOVED, REMOVED],
              str([off.get(name) for name in BODY_GATE_ARTIFACTS]))
        check("in the same reverse order",
              order.index(BODY_GATE_LEAF) < order.index(BODY_GATE_SCRIPT_LEAF),
              str(order))
        check("and the report is still in registry order",
              [s["artifact"] for s in answered_off["artifacts"]]
              == [a.name for a in ARTIFACTS],
              str([s["artifact"] for s in answered_off["artifacts"]]))
        check("the entry the workflow registered is gone too",
              not config.load(tmp).get("host.checks"),
              str(config.load(tmp).get("host.checks")))

    print()
    print("a project requiring no section gets no gate, and that is not an absence")
    with tempfile.TemporaryDirectory() as tmp:
        quiet = _a_project(tmp)
        quiet.data["body_sections"] = []
        answered = run(quiet, write=True)
        none_wanted = _answers_of(answered)
        check("both artifacts are reported as not wanted",
              [_answer_of(none_wanted, name) for name in BODY_GATE_ARTIFACTS]
              == [NOT_WANTED, NOT_WANTED],
              str([none_wanted.get(name) for name in BODY_GATE_ARTIFACTS]))
        check("nothing is reported incomplete", answered["report"] == [],
              str(answered["report"]))
        check("and no toolkit directory was created",
              not os.path.isdir(os.path.join(quiet.code_root, TOOLKIT_DIRECTORY)))

    print()
    print("where the project states a runner, the generated file states that one")
    with tempfile.TemporaryDirectory() as tmp:
        stated = _a_project(tmp)
        stated.data.setdefault("host", {})["runner"] = {
            "label": "a-label-this-account-states",
            "concurrent_jobs": 1,
            "budget_minutes": 7,
            "supersedes": "a-group-this-project-states",
        }
        text = body_gate_workflow(stated)
        for label, wanted in (
            ("the label", "runs-on: a-label-this-account-states"),
            ("the budget", "timeout-minutes: 7"),
            ("the supersession group", "group: a-group-this-project-states"),
        ):
            check(f"{label} comes from the configuration", wanted in text, text)
        check(
            "and the kind's own default is not in the file beside it",
            TEMPLATES["github"].default_label not in text,
            "a literal beside a statement that disagrees with it is the drift "
            "the runner facet exists against",
        )
        without = _a_project(tmp)
        plain = body_gate_workflow(without)
        check("a project stating none gets the kind's template label",
              f"runs-on: {TEMPLATES['github'].default_label}" in plain, plain)
        check("and no budget it never stated",
              "timeout-minutes" not in plain, plain)
        check("and no supersession group either",
              "concurrency" not in plain, plain)

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
    # ⛔ And the status is the complement of that sentence rather than its
    # restatement. ⚠️ Measured: read off the report's length, the step exited
    # non-zero on this repository — the report saying the registry is merely
    # empty while the status said the run had failed.
    with tempfile.TemporaryDirectory() as tmp:
        _a_project(tmp)
        check(
            "a registry with nothing incomplete in it exits zero",
            main(["install", "--skills-root", tmp, "--dry-run"]) == 0,
            "a statement in the report is not an incompleteness, and the status "
            "may not read one as the other",
        )
    # ⛔ The two per-kind tables have to agree, and the direction that bites is
    # this one: a kind whose definitions this toolkit can read resolves a place
    # to write, so the generator is then reached and would fail on a template
    # it does not hold. ⚠️ A `KeyError` there is the improvising failure wearing
    # a stack trace — the step promises an answer with the thing named, and a
    # crash is neither.
    check(
        "every host kind with readable definitions has a workflow template",
        set(check_host_checks.DEFINITIONS) <= set(TEMPLATES),
        f"{sorted(set(check_host_checks.DEFINITIONS) - set(TEMPLATES))} can be "
        "written to and has no template, so a generated workflow for it raises "
        "rather than refusing",
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
    # ⛔ The status reads the artifacts' own answers and never the report's
    # length. ⚠️ Measured on this repository: the empty-registry line is a
    # statement rather than an incompleteness, and read as one the step exited
    # non-zero on a project where nothing was wrong — the report saying the
    # registry is merely empty while the status said the run had failed.
    incomplete = [
        state for state in answer["artifacts"] if state["answer"] in INCOMPLETE
    ]
    return 1 if incomplete and args.what else 0


if __name__ == "__main__":
    sys.exit(main())
