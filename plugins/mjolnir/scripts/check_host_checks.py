#!/usr/bin/env python3
"""Hold `host.checks` to the host's own workflow definitions.

The rule is
`plugins/mjolnir/config/schema.md § 2 -> The facet against the host's own definitions`,
which states it and carries the argument behind it. Neither is restated here.

⛔ Five dimensions are compared, the first three in both directions, because
neither direction shows from the other's output: the **name** an entry is keyed
on, the **triggers** that start the run, the **paths** it watches, the **jobs**
an entry names where it states them, and the **runner** the project states its
jobs run on. A renamed workflow leaves an entry naming a run the host does not
make *and* a run no entry names, and a check reading one side only reports half
of it.

⚠️ **The runner dimension is the project's rather than an entry's**, and is the
one dimension a project may legitimately have nothing on either side of: § 2
keeps the host kind's default label off the surface, so a project stating no
`host.runner` has nothing for a file to be held to, and this check stands silent
on it rather than guessing a label and reporting drift on a correct project.

⛔ Nothing here is a verdict about the code. A drifted facet misdirects every
consumer that reads it -- the guards that refuse a local run on the strength of a
host run, the reviewing role driving those runs green, the finishing role
refusing to merge without them -- so what this holds is the statement, not the
change.

⛔ **It states facts and never edits.** Neither the facet nor a workflow file is
written, moved or reformatted: which of the two sides is wrong is a person's
call, and a check that picked one would have to be believed about a repository's
continuous integration.

⚠️ **Three answers, and only one of them is green.** The facet and the
definitions agree; they disagree, which is drift; or a dimension could not be
established, which is reported as itself and is never read as agreement -- § 2's
rule that absence of signal is not an answer, arriving at the facet instead of at
a run. `checks: []` is the fourth reading and the one with nothing to compare:
the project has stated that every verdict is local, so this check has no subject
rather than a green one.

⚠️ **Port-shaped.** A host kind whose workflow definitions are not files a reader
can open has no subject here either, and the dimension is undeterminable rather
than absent. What each kind keeps where is `DEFINITIONS` below and is the only
host fact in this file.

⚠️ **What the configuration reader has already refused is not re-refused.**
`config.py` holds every entry to being a mapping with a non-blank `workflow`, to
stating `mirrors` or `jobs` and never both, to one command per `mirrors`, and to
a trigger list and a path filter of the right shape (§ 2). This file reads those
values and compares them; an entry it would have to defend against never
reaches it.

Usage:
    check_host_checks.py              hold the facet to the host's own definitions
    check_host_checks.py --self-test  assert each check reddens on each planted
                                      violation, that each planted absence is
                                      reported rather than passed, that each
                                      planted exemption stays green and that the
                                      reader is linear, then hold the facet
"""

from __future__ import annotations

import argparse
import copy
import os
import sys
import time
from typing import NamedTuple

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import config as reader  # noqa: E402 -- the one reader of the surface, and the one trigger grammar

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - environment, not logic
    sys.exit(
        "check_host_checks.py needs PyYAML to read a workflow definition.\n"
        "Install it with: python3 -m pip install pyyaml"
    )


class Where(NamedTuple):
    """Where a host kind keeps its workflow definitions, and what a job of one carries."""

    directory: str
    extensions: tuple[str, ...]
    # Whether a job of a workflow carries a path filter of its own. ⛔ § 2 lets a
    # `jobs` member state `paths`, for a host whose jobs are filtered one by one;
    # a kind whose jobs carry none cannot be asked, so a member stating one is
    # reported undeterminable rather than compared against nothing.
    job_paths: bool


# ⛔ The only host facts in this file, and a kind absent from it keeps its
# definitions somewhere this reader cannot open -- which is an answer (§ 2) and
# not a gap. Adding a kind here is adding a reader for its files, never a default.
DEFINITIONS = {
    "github": Where(os.path.join(".github", "workflows"), (".yml", ".yaml"), job_paths=False),
}

# A dimension this reader could not establish. ⛔ Distinct from `None`, which is
# a dimension read and found empty: a workflow stating no path filter and a
# workflow whose filter could not be read are the two readings § 2 refuses to
# collapse, and one object for both is how they collapse.
UNKNOWN = object()

# The keys a host event block may carry that no trigger pattern and no path
# filter can state, each against the dimension it leaves undeterminable. ⛔ The
# dimension is *killed* and not merely annotated: a workflow excluding a set of
# refs fires on refs the facet cannot enumerate, so comparing the triggers it
# **can** state reports drift on an entry that is as right as the facet lets it
# be -- the one outcome ruling 15 of `docs/divergences-and-rulings.md` rules out.
UNSTATABLE = {
    "branches-ignore": "triggers",
    "tags": "triggers",
    "tags-ignore": "triggers",
    "paths-ignore": "paths",
}

# What opens a host expression, evaluated when the run starts rather than when
# the file is read. ⛔ A runner label, a budget or a supersession group written
# with one in it is a fact about the run and not about the file, so the
# dimension is reported undeterminable rather than compared as text: a project
# whose jobs do land where it says would otherwise read as drifted, which is the
# one outcome ruling 15 of `docs/divergences-and-rulings.md` rules out.
AN_EXPRESSION = "${{"

# What a trigger states as its ref where the event block filters on none (§ 2).
ANY_REF = "*"


class Unstatable(RuntimeError):
    """A dimension this reader could not establish, with the reason named.

    ⛔ Never a pass and never drift. An entry whose trigger does not parse and a
    workflow whose event block cannot be walked each leave a comparison holding
    nothing, which § 2 makes *no answer* rather than agreement.
    """


# --- reading one workflow definition ---------------------------------------


class Definition:
    """One workflow file, read for the four things an entry states about it.

    Every field is either the value the file states, `None` where it states
    none, or `UNKNOWN` where this reader could not establish it. ⚠️ `unstatable`
    carries the reasons, one per fact, so a report names the key rather than the
    file alone.
    """

    def __init__(self, path: str):
        self.path = path
        self.name = UNKNOWN
        self.triggers = UNKNOWN
        self.paths = UNKNOWN
        self.jobs = UNKNOWN
        # § 2's runner dimension, read per job rather than per file: a label is
        # a job's key and a workflow may spread its jobs across runners, so a
        # single value here would answer about whichever job came first.
        # `UNKNOWN` against a job is that job's own undeterminable reading, and
        # `None` is the job stating nothing -- the two § 2 refuses to collapse.
        self.runners: dict = {}
        self.budgets: dict = {}
        # The supersession group is the workflow's, the host putting it on the
        # document. ⚠️ Two facts rather than one: a group that does not cancel
        # what is in progress supersedes nothing, so the pair is what the facet's
        # `supersedes` is compared against.
        self.group = UNKNOWN
        self.cancels_in_progress = UNKNOWN
        self.unstatable: list[str] = []
        # ⛔ The runner dimension's reasons are kept apart from the four above,
        # and that is not tidiness: a project stating no `host.runner` has
        # nothing for a file to be held to, so a job whose label is an
        # expression leaves *nothing* undeterminable there. Folded into
        # `unstatable` these would deny such a project its green forever, over a
        # comparison it never asked for. Each is tagged with the key it kills,
        # and `undeterminable` emits only the ones the facet states.
        self.runner_unstatable: list[tuple[str, str]] = []

    def __repr__(self) -> str:  # pragma: no cover - diagnostics
        return f"<Definition {self.path} name={self.name!r}>"


def _sequence(value) -> list[str]:
    """A host key's value as the list of strings it states, in either shape.

    A host writes `branches: [main]` and `branches:` with a block sequence under
    it to mean one thing, and a single pattern as a bare scalar. ⛔ A shape that
    is neither is raised rather than coerced: a mapping read as a one-element
    list is the plausible-looking wrong answer this whole file is against.
    """
    if value is None:
        return []
    if isinstance(value, (str, int, float, bool)):
        return [str(value)]
    if isinstance(value, list) and all(
        isinstance(member, (str, int, float, bool)) for member in value
    ):
        return [str(member) for member in value]
    raise Unstatable(f"states {value!r}, which is neither a pattern nor a list of them")


def read_definition(text: str | Exception, path: str) -> Definition:
    """One workflow file's four facts, read from its text -- or from why it has none.

    ⛔ A file this cannot read yields a `Definition` whose fields are `UNKNOWN`
    and whose reasons are named -- never an empty one. An unreadable definition
    takes every entry keyed on it out of the comparison, and a comparison with
    nothing in it reports green.

    ⚠️ The event block arrives under `True` rather than under `"on"`: `on` is a
    boolean in the YAML version the parser implements, so the host's own key
    spelling resolves to one. Both are looked up, because a file that quotes the
    key states the string.
    """
    found = Definition(path)

    if isinstance(text, Exception):
        # ⛔ A definition the sweep could not open, kept as the reason rather
        # than dropped from the set: a file left out reads as a file that is not
        # there, which is the one reading that turns an unheld entry into a
        # green one.
        found.unstatable.append(f"is there and could not be read ({text})")
        return found

    try:
        document = yaml.safe_load(text)
    except yaml.YAMLError as error:
        found.unstatable.append(f"is not valid YAML -- {' '.join(str(error).split())}")
        return found
    if not isinstance(document, dict):
        found.unstatable.append("is empty, or is not a block of keys")
        return found

    name = document.get("name")
    if isinstance(name, str) and name.strip():
        found.name = name.strip()
    else:
        # ⛔ Reported rather than derived from the path. The host names such a
        # workflow by its file path, and writing that derivation here would put a
        # second statement of the host's own naming rule in this file -- wrong the
        # next time the host changes it, and wrong silently.
        found.unstatable.append(
            "states no `name:`, so the name every entry is keyed on cannot be read from it"
        )

    _supersession(document, found)

    jobs = document.get("jobs")
    if isinstance(jobs, dict):
        # ⛔ The keys of the `jobs` block and never of the document: a top-level
        # key read as a job id makes `concurrency` a job, and an entry naming one
        # then passes a check that was supposed to catch it.
        found.jobs = {str(job) for job in jobs}
        for job, body in jobs.items():
            _runner_of(str(job), body, found)
    else:
        found.unstatable.append("states no `jobs:` block this reader can walk")

    if True in document:
        block = document[True]
    elif "on" in document:
        block = document["on"]
    else:
        found.unstatable.append(
            "states no event block, so nothing in it says what starts the run"
        )
        return found

    try:
        found.triggers, found.paths = _derive(block, found)
    except Unstatable as reason:
        found.unstatable.append(str(reason))
    return found


def _runner_of(job: str, body, found: Definition) -> None:
    """One job's runner label and budget, or why neither could be established.

    ⛔ Three readings per key and not two, which is § 2's rule arriving at a
    job: the value the file states, `None` where the job states none -- which is
    drift against a facet that states one, the host's own fallback being
    whatever it is -- and `UNKNOWN` where the file says something this reader
    may not compare as text.

    ⚠️ A list of labels is `UNKNOWN` rather than drift. The host admits one, and
    § 2's `label` is singular, so a job written that way states something the
    facet has no form for -- and reporting drift against it is red forever with
    no edit that clears it.
    """
    if not isinstance(body, dict):
        found.runners[job] = UNKNOWN
        found.budgets[job] = UNKNOWN
        for key in ("label", "budget"):
            found.runner_unstatable.append((
                key,
                f"states the `{job}` job as {body!r}, which this reader cannot walk for "
                f"the runner it asks for",
            ))
        return

    label = body.get("runs-on")
    if label is None:
        found.runners[job] = None
    elif isinstance(label, str) and AN_EXPRESSION not in label:
        found.runners[job] = label.strip()
    else:
        found.runners[job] = UNKNOWN
        found.runner_unstatable.append((
            "label",
            f"states the `{job}` job's `runs-on:` as {label!r}, which is a fact about the "
            f"run rather than about the file -- an expression the host evaluates, or a set "
            f"of labels where § 2 states one",
        ))

    budget = body.get("timeout-minutes")
    if budget is None:
        found.budgets[job] = None
    elif isinstance(budget, bool) or not isinstance(budget, int):
        found.budgets[job] = UNKNOWN
        found.runner_unstatable.append((
            "budget",
            f"states the `{job}` job's `timeout-minutes:` as {budget!r}, which is not a "
            f"whole number of minutes this reader can compare against a stated budget",
        ))
    else:
        found.budgets[job] = budget


def _supersession(document: dict, found: Definition) -> None:
    """The workflow's concurrency group, and whether it retires what is running.

    ⛔ Two facts and not one. A group with nothing cancelling in progress
    supersedes nothing, so a file that states the stated group and lets both
    runs finish is drift against a facet saying a newer run retires an older --
    and a comparison on the group alone would call that agreement.
    """
    block = document.get("concurrency")
    if block is None:
        found.group, found.cancels_in_progress = None, False
        return
    if isinstance(block, str):
        block = {"group": block}
    if not isinstance(block, dict):
        found.runner_unstatable.append((
            "supersedes",
            f"states `concurrency:` as {block!r}, which this reader cannot walk for the "
            f"group a newer run would retire an older one in",
        ))
        return
    group = block.get("group")
    if not isinstance(group, str) or AN_EXPRESSION in group:
        found.runner_unstatable.append((
            "supersedes",
            f"states its concurrency group as {group!r}, which is a fact about the run "
            f"rather than about the file -- an expression the host evaluates when it starts",
        ))
        return
    found.group = group.strip()
    found.cancels_in_progress = bool(block.get("cancel-in-progress"))


def _derive(block, found: Definition):
    """(triggers, the event block's path filter) from a host's own `on:` block.

    The trigger set is § 2's: one member per (event, types, ref), with `*` for an
    event the block filters on no ref. ⚠️ A `branches:` list of several patterns
    is several triggers of one event sharing its types, which is the list the
    facet already exists for rather than a shape it cannot state.
    """
    if isinstance(block, str):
        events = {block: None}
    elif isinstance(block, list) and all(isinstance(event, str) for event in block):
        events = {event: None for event in block}
    elif isinstance(block, dict):
        events = {str(event): value for event, value in block.items()}
    else:
        raise Unstatable(f"states an event block this reader cannot walk ({block!r})")

    triggers: set[tuple[str, frozenset[str] | None, str]] = set()
    filters: list[tuple[str, ...] | None] = []
    killed: set[str] = set()
    for event, value in events.items():
        types, refs, filtered = None, [ANY_REF], None
        if isinstance(value, dict):
            for key, dimension in UNSTATABLE.items():
                if key in value:
                    killed.add(dimension)
                    found.unstatable.append(
                        f"filters `{event}` on `{key}:`, which no entry has a form for, so its "
                        f"{dimension} cannot be compared against what the facet states"
                    )
            if "types" in value:
                types = frozenset(_sequence(value["types"]))
            if "branches" in value:
                refs = _sequence(value["branches"]) or [ANY_REF]
            if "paths" in value:
                filtered = tuple(_sequence(value["paths"]))
        elif value is not None:
            raise Unstatable(f"states `{event}` as {value!r}, which this reader cannot walk")
        for ref in refs:
            triggers.add((event, types, ref))
        filters.append(filtered)

    # ⛔ One filter for the whole event block, because an entry carries one
    # `paths` for the whole entry (§ 2). A workflow filtering its events
    # differently states something the facet has no form for, so the dimension is
    # undeterminable rather than compared against whichever event came first.
    distinct = set(filters)
    if len(distinct) > 1:
        killed.add("paths")
        found.unstatable.append(
            "filters its events differently from one another, and an entry states one "
            "`paths` for the whole event block"
        )
    only = distinct.pop() if len(distinct) == 1 else None
    return (
        UNKNOWN if "triggers" in killed else triggers,
        UNKNOWN if "paths" in killed else (None if only is None else list(only)),
    )


# --- reading the facet's own side ------------------------------------------


def stated_triggers(run: dict):
    """The (event, types, ref) set one entry states, or `UNKNOWN` where it states none.

    ⛔ Through the one grammar (§ 2), imported rather than spelled again: a
    second parse of this pattern is the two vocabularies § 17 refuses for the
    half of the mapping it owns, arriving as behaviour instead of as text.

    ⚠️ An entry with no `triggers` key leaves the dimension **unstated**, which is
    reported and never read as agreement -- unlike `paths`, whose omission § 2
    gives a meaning to. ⛔ `None` on the record is that absence and nothing else:
    the reader refuses a `triggers` written blank, so the key being there and
    holding nothing never reaches this. A pattern the grammar does not parse is
    no answer about the run by § 2's own rule, and is raised naming the pattern.
    """
    stated = run["triggers"]
    if stated is None:
        return UNKNOWN
    patterns = stated if isinstance(stated, list) else [stated]
    out = set()
    for pattern in patterns:
        parsed = reader.parse_trigger(pattern)
        if parsed is None:
            raise Unstatable(f"states the trigger {pattern!r}, which § 2's grammar does not parse")
        event, types, ref = parsed
        out.add((event, None if types is None else frozenset(types), ref))
    return out


def shown(trigger) -> str:
    """One trigger back in the form § 2 states it in, for a report a reader can act on."""
    event, types, ref = trigger
    clause = "" if types is None else "(" + ", ".join(sorted(types)) + ")"
    return f"{event}{clause} -> {ref}"


# --- the subject ------------------------------------------------------------


class Subject:
    """The facet, the host's own definitions, and where each came from.

    ⛔ Both sides are held as what was **written** and read on first use: the
    facet as the entries a project stated, the definitions as their text. A
    plant below therefore goes through the real readers rather than through a
    hand-built result, which is what keeps the two parts of this file that have
    ever been got wrong -- the facet's walk and the definition's parse -- under
    the assertions.
    """

    def __init__(self, kind, entries: list, texts, where: Where | None, runner=None):
        self.kind = kind
        self.entries = entries
        self.texts = texts
        self.where = where
        # § 2's `host.runner` as the reader walked it, or `None` where the
        # project states none. ⛔ Held as the walked record rather than as the
        # raw block, so this file compares what every other consumer reads --
        # and so a block the reader would refuse never reaches a comparison.
        self.runner = runner
        self._checks = None
        self._definitions = None

    @property
    def directory(self) -> str:
        return self.where.directory if self.where else "the host's own definitions"

    @property
    def checks(self) -> list[dict]:
        """One record per entry, through the reader's own walk of the facet.

        ⛔ `config.host_runs` and never a walk of the entries here: § 2 makes
        this facet one statement, and a second reading of it in this file would
        be allowed to disagree with the one every other consumer reads. ⚠️ It is
        the per-**entry** accessor rather than the per-command one, because an
        entry mirroring nothing is a run the host makes and this check's whole
        second direction is about runs no entry names.
        """
        if self._checks is None:
            self._checks = reader.host_runs({"host": {"checks": self.entries}})
        return self._checks

    @property
    def definitions(self):
        """The definitions, read once, or `UNKNOWN` where the kind keeps none in files."""
        if self.texts is UNKNOWN:
            return UNKNOWN
        if self._definitions is None:
            self._definitions = [
                read_definition(self.texts[path], path) for path in sorted(self.texts)
            ]
        return self._definitions

    def copy(self) -> "Subject":
        # ⛔ Deep, so a plant that reaches into an entry's `jobs` list or its
        # trigger list cannot reach the next plant's baseline through it. A
        # shallow copy makes the assertions below order-dependent, which is the
        # shape that passes while asserting the wrong thing.
        texts = UNKNOWN if self.texts is UNKNOWN else dict(self.texts)
        return Subject(
            self.kind, copy.deepcopy(self.entries), texts, self.where,
            copy.deepcopy(self.runner),
        )


def read_subject(skills_root: str) -> Subject:
    """A project's facet and its host's own definitions, resolved through the reader (§ 1).

    ⚠️ A `github` project with no workflow directory has **zero** definitions
    rather than undeterminable ones: no directory is the host's own answer that
    it runs nothing, which is readable and definite. What is undeterminable is a
    host kind whose definitions are not files at all.
    """
    config = reader.load(skills_root)
    kind = config.get("host.kind")
    entries = config.get("host.checks")
    # ⛔ Through the reader's own accessor and never off the dict: § 2 makes
    # this one statement, and a second walk of it here would be allowed to
    # disagree with what the installer writing a workflow file reads.
    runner = config.runner()
    where = DEFINITIONS.get(kind)
    if where is None:
        return Subject(kind, entries, UNKNOWN, None, runner)
    root = os.path.join(config.code_root, where.directory)
    texts: dict[str, str] = {}
    for name in sorted(os.listdir(root)) if os.path.isdir(root) else []:
        if not name.endswith(where.extensions):
            continue
        path = os.path.join(where.directory, name)
        try:
            with open(os.path.join(root, name), encoding="utf-8") as handle:
                texts[path] = handle.read()
        except (OSError, UnicodeDecodeError) as error:
            texts[path] = error
    return Subject(kind, entries, texts, where, runner)


def _named(subject: Subject) -> dict[str, Definition]:
    """The definitions whose name could be read, keyed by it (§ 2's only key)."""
    return {
        found.name: found
        for found in subject.definitions
        if found.name is not UNKNOWN
    }


def _unnamed(subject: Subject) -> list[Definition]:
    """The definitions whose own name could not be read.

    ⛔ One of these suspends the name comparison rather than failing it. An entry
    matching no name this reader could read is drift only where every definition
    *was* read: while one file's name is unestablished, that file could be the
    one the entry names, and reporting drift would be this check calling the
    facet wrong on the strength of what it could not establish. The absence is
    reported instead, naming the file, and is fixed by the file stating a name.
    """
    return [found for found in subject.definitions if found.name is UNKNOWN]


# --- the checks -------------------------------------------------------------


def check_every_entry_names_a_workflow_the_host_defines(subject: Subject) -> list[str]:
    """An entry whose key names no definition answers about a run the host does not make."""
    if subject.definitions is UNKNOWN or _unnamed(subject):
        return []
    named = _named(subject)
    problems = []
    for run in subject.checks:
        workflow = run["workflow"]
        if workflow in named:
            continue
        problems.append(
            f"{run['where']} names the `{workflow}` workflow and no definition under "
            f"{subject.directory} states that name. Every consumer reads this facet by that "
            f"name (§ 2), so the entry answers about a run the host does not make. The names "
            f"that are there: {', '.join(repr(name) for name in sorted(named)) or 'none'}."
        )
    return problems


def check_every_workflow_the_host_defines_has_an_entry(subject: Subject) -> list[str]:
    """A definition no entry names is a run the facet does not state (§ 2)."""
    if subject.definitions is UNKNOWN:
        return []
    stated = {run["workflow"] for run in subject.checks}
    problems = []
    for found in subject.definitions:
        if found.name is UNKNOWN or found.name in stated:
            continue
        problems.append(
            f"{found.path} defines the `{found.name}` workflow and no entry of `host.checks` "
            f"names it. The facet is the single statement of which runs exist (§ 2), so a run "
            f"missing from it is a run no consumer knows about -- including a workflow that "
            f"mirrors no local command, which is an entry stating neither `mirrors` nor `jobs`."
        )
    return problems


def check_every_entrys_triggers_are_its_workflows_own(subject: Subject) -> list[str]:
    """The events, their types and their refs, compared as sets in both directions."""
    if subject.definitions is UNKNOWN:
        return []
    named = _named(subject)
    problems = []
    for run in subject.checks:
        found = named.get(run["workflow"])
        if found is None or found.triggers is UNKNOWN:
            continue
        try:
            stated = stated_triggers(run)
        except Unstatable:
            continue
        if stated is UNKNOWN:
            continue
        for trigger in sorted(stated - found.triggers, key=shown):
            problems.append(
                f"{run['where']} states the trigger `{shown(trigger)}` for the "
                f"`{found.name}` workflow and {found.path} does not fire on it. A consumer "
                f"waiting for that run waits for one the host will never make (§ 2)."
            )
        for trigger in sorted(found.triggers - stated, key=shown):
            problems.append(
                f"{found.path} fires the `{found.name}` workflow on `{shown(trigger)}` and "
                f"{run['where']} states no such trigger. A second event kind is a second "
                f"member of the list (§ 2), never a trigger left out of it."
            )
    return problems


def check_every_entrys_paths_are_its_workflows_own(subject: Subject) -> list[str]:
    """The path filter, compared in both directions -- its absence being a statement (§ 2)."""
    if subject.definitions is UNKNOWN:
        return []
    named = _named(subject)
    problems = []
    for run in subject.checks:
        found = named.get(run["workflow"])
        if found is None or found.paths is UNKNOWN:
            continue
        stated = run["paths"]
        if stated is None and found.paths is None:
            continue
        if stated is None:
            problems.append(
                f"{run['where']} states no `paths` for the `{found.name}` workflow and "
                f"{found.path} filters on {found.paths!r}. An omitted filter means the workflow "
                f"runs on every change (§ 2), so the entry reads as covering changes its run is "
                f"filtered out of -- which is the direction that ships unchecked code."
            )
        elif found.paths is None:
            problems.append(
                f"{run['where']} states the filter {stated!r} for the `{found.name}` "
                f"workflow and {found.path} filters on nothing. The entry reads as covering "
                f"less than the run does (§ 2)."
            )
        elif sorted(stated) != sorted(found.paths):
            problems.append(
                f"{run['where']} states the filter {sorted(stated)!r} for the "
                f"`{found.name}` workflow and {found.path} filters on "
                f"{sorted(found.paths)!r} (§ 2)."
            )
    return problems


def check_every_job_an_entry_names_is_its_workflows_own(subject: Subject) -> list[str]:
    """A job id an entry names, held against the `jobs:` block of its own file (§ 2)."""
    if subject.definitions is UNKNOWN:
        return []
    named = _named(subject)
    problems = []
    for run in subject.checks:
        found = named.get(run["workflow"])
        if found is None or found.jobs is UNKNOWN or run["jobs"] is None:
            continue
        for position, job in enumerate(run["jobs"]):
            name = job.get("job")
            if name in found.jobs:
                continue
            problems.append(
                f"{run['where']}.jobs[{position}] names the `{name}` job of the "
                f"`{found.name}` workflow and {found.path} defines no such job. A job's id is "
                f"scoped by the entry naming its workflow (§ 2), and the four preconditions are "
                f"read on the job where one mirrors the command in hand -- so a name no file "
                f"carries is a run nothing can ever be asked about. The jobs that are there: "
                f"{', '.join(repr(job) for job in sorted(found.jobs)) or 'none'}."
            )
    return problems


def check_every_jobs_runner_is_the_stated_label(subject: Subject) -> list[str]:
    """Every job's `runs-on`, held to `host.runner.label` where one is stated (§ 2)."""
    if subject.definitions is UNKNOWN or subject.runner is None:
        return []
    wanted = subject.runner["label"]
    problems = []
    for found in subject.definitions:
        for job, label in sorted(found.runners.items()):
            if label is UNKNOWN or label == wanted:
                continue
            problems.append(
                f"{found.path} runs the `{job}` job on "
                + (f"`{label}`" if label is not None else "no stated runner")
                + f" and `host.runner.label` is `{wanted}` (§ 2). A job asking for a label "
                f"the account has no runner behind never starts at all, which is a check "
                f"that never reports rather than one that fails."
            )
    return problems


def check_every_jobs_budget_is_the_stated_one(subject: Subject) -> list[str]:
    """Every job's `timeout-minutes`, held to `host.runner.budget_minutes` (§ 2)."""
    if subject.definitions is UNKNOWN or subject.runner is None:
        return []
    wanted = subject.runner["budget_minutes"]
    queued = subject.runner["budget_is_a_queue_budget"]
    problems = []
    for found in subject.definitions:
        for job, budget in sorted(found.budgets.items()):
            if budget is UNKNOWN or budget == wanted:
                continue
            problems.append(
                f"{found.path} gives the `{job}` job "
                + (f"a budget of {budget} minute(s)" if budget is not None
                   else "no `timeout-minutes:` at all, so the host's own fallback bounds it")
                + f" and `host.runner.budget_minutes` is {wanted} (§ 2)."
                + (" On an account whose runners take one job at a time that budget is what "
                   "the queue is bounded by, so the gap is measured in jobs behind this one."
                   if queued else "")
            )
    return problems


def check_the_supersession_group_is_the_stated_one(subject: Subject) -> list[str]:
    """Each workflow's concurrency group, held to `host.runner.supersedes` (§ 2).

    ⛔ Compared in one direction and only where the facet states the key: a
    project whose runs supersede nothing omits `supersedes`, and holding every
    file to *carrying no group* would refuse a workflow that serialises itself
    for a reason this facet knows nothing about.
    """
    if subject.definitions is UNKNOWN or subject.runner is None:
        return []
    wanted = subject.runner["supersedes"]
    if wanted is None:
        return []
    problems = []
    for found in subject.definitions:
        if found.group is UNKNOWN:
            continue
        if found.group != wanted:
            problems.append(
                f"{found.path} states the concurrency group "
                + (f"`{found.group}`" if found.group is not None else "no concurrency group")
                + f" and `host.runner.supersedes` is `{wanted}` (§ 2). A consumer told a "
                f"cancelled run was superseded is sent to a successor that was never "
                f"arranged."
            )
        elif not found.cancels_in_progress:
            problems.append(
                f"{found.path} states the `{wanted}` concurrency group and does not cancel "
                f"what is in progress, so a newer run retires nothing (§ 2). The facet says "
                f"a run of this project's supersedes an older one, and this file lets both "
                f"finish."
            )
    return problems


CHECKS = [
    ("every entry names a workflow the host defines",
     check_every_entry_names_a_workflow_the_host_defines),
    ("every workflow the host defines has an entry",
     check_every_workflow_the_host_defines_has_an_entry),
    ("every entry's triggers are its workflow's own",
     check_every_entrys_triggers_are_its_workflows_own),
    ("every entry's paths are its workflow's own",
     check_every_entrys_paths_are_its_workflows_own),
    ("every job an entry names is its workflow's own",
     check_every_job_an_entry_names_is_its_workflows_own),
    ("every job runs where the project says its jobs run",
     check_every_jobs_runner_is_the_stated_label),
    ("every job carries the stated budget",
     check_every_jobs_budget_is_the_stated_one),
    ("the supersession group is the stated one",
     check_the_supersession_group_is_the_stated_one),
]


def undeterminable(subject: Subject) -> list[str]:
    """Every dimension this run could not establish, each naming what it was.

    ⛔ Not a problem list and not a pass. § 2 makes absence of signal *no
    answer*, so each line here denies the run its green without claiming the
    facet is wrong -- the two readings a single list would collapse.
    """
    if subject.definitions is UNKNOWN:
        return [
            f"`host.kind` is {subject.kind!r}, whose workflow definitions are not files this "
            f"reader can open, so no dimension of the facet can be compared at all. The kinds "
            f"whose definitions are readable: {', '.join(sorted(DEFINITIONS))}. Every consumer "
            f"proceeds on the facet as stated (§ 2)."
        ]
    notes = []
    # Which of the runner dimension's three keys this project states, and so
    # which of a definition's runner reasons deny this run its green. ⛔ A key
    # the facet does not state is not an unestablished comparison -- it is no
    # comparison, which § 2 makes the ordinary case rather than an absence.
    runner_keys = set()
    if subject.runner is not None:
        runner_keys = {"label", "budget"}
        if subject.runner["supersedes"] is not None:
            runner_keys.add("supersedes")
    for found in subject.definitions:
        for reason in found.unstatable:
            notes.append(f"{found.path} {reason}")
        for key, reason in found.runner_unstatable:
            if key in runner_keys:
                notes.append(f"{found.path} {reason}")
    named = _named(subject)
    unnamed = _unnamed(subject)
    for run in subject.checks:
        workflow = run["workflow"]
        # The other end of the suspended name comparison. ⛔ Stated per entry and
        # not only per file, because the file's own note says a name is missing
        # while this one says which entry went unheld because of it.
        if unnamed and workflow not in named:
            notes.append(
                f"{run['where']} names the `{workflow}` workflow and no definition this "
                f"run could name states it, while "
                f"{', '.join(found.path for found in unnamed)} states no name of its own -- so "
                f"whether the entry names a run the host makes is unestablished rather than "
                f"wrong."
            )
        try:
            stated = stated_triggers(run)
        except Unstatable as reason:
            notes.append(f"{run['where']} {reason}")
            stated = None
        if stated is UNKNOWN:
            notes.append(
                f"{run['where']} states no `triggers` for the `{workflow}` workflow, so "
                f"what starts that run is stated nowhere and nothing holds the file to it. § 2 "
                f"gives an omitted `paths` a meaning and gives an omitted `triggers` none."
            )
        if (
            subject.where is not None
            and not subject.where.job_paths
            and run["jobs"] is not None
        ):
            for position, job in enumerate(run["jobs"]):
                if "paths" in job:
                    notes.append(
                        f"{run['where']}.jobs[{position}] states a `paths` filter, and a "
                        f"job of a {subject.kind!r} workflow carries none for this reader to "
                        f"compare it against. § 2 states the key at the level the file states it "
                        f"at, and this kind states it only on the event block."
                    )
    return notes


def no_subject(subject: Subject) -> str | None:
    """Why this project has nothing for this check to hold, where it has nothing.

    ⛔ Both sides empty, and not the facet alone. `checks: []` means every
    verdict is local (§ 2), which is a legitimate configuration only where the
    host in fact runs nothing: an empty facet beside a directory full of
    definitions is the facet at its most drifted, and reporting *no subject*
    there would be this check standing down exactly when it has most to say.

    ⚠️ A host kind whose definitions are not files is not this -- that is a
    dimension unestablished rather than a subject absent, and
    `undeterminable` carries it.
    """
    if subject.definitions is UNKNOWN or subject.checks or subject.definitions:
        return None
    return (
        f"`host.checks` is empty and {subject.directory} defines no workflow, so this project "
        f"states that every verdict is local (§ 2) and there is nothing on either side to "
        f"compare. A project in that position runs no such check; what its local verdicts are "
        f"is `checks_local` (§ 17)."
    )


def run(subject: Subject) -> dict[str, list[str]]:
    return {name: check(subject) for name, check in CHECKS}


# --- the planted subject ----------------------------------------------------
#
# ⛔ Synthetic rather than whatever workflows happen to be in the tree. The
# command a host run executes is `--self-test`, and a plant built on the tree's
# own files makes every assertion below a property of the tree instead of of the
# check -- which is how a rename turns the gate into a `KeyError` rather than a
# verdict. The tree is held straight afterwards, by the run itself.

FIRST = """\
name: First
on:
  pull_request:
  push:
    branches: [main]
permissions: {}
concurrency:
  group: first
jobs:
  first:
    runs-on: ubuntu-latest
    steps:
      - run: the-first-command
"""

SECOND = """\
name: Second

on:
  # A comment between the key and its events, which every definition in this
  # repository carries and which no reading of the block may be confused by.
  pull_request:
    types: [opened, edited]

  pull_request_review:
    types: [submitted]

jobs:
  second:
    runs-on: ubuntu-latest
    steps:
      - run: the-second-command
  a-job-mirroring-nothing:
    runs-on: ubuntu-latest
    steps:
      - run: the-third-command
"""

PLANTED = {
    os.path.join(".github", "workflows", "first.yml"): FIRST,
    os.path.join(".github", "workflows", "second.yml"): SECOND,
}

STATED = [
    {"workflow": "First", "mirrors": "the-first-command",
     "triggers": ["pull_request -> *", "push -> main"]},
    {"workflow": "Second",
     "triggers": ["pull_request_review(submitted) -> *",
                  "pull_request(edited, opened) -> *"],
     "jobs": [{"job": "second", "mirrors": "the-second-command"}]},
]


def _a_subject() -> Subject:
    """Two definitions and two entries, stated and defined in agreement.

    ⚠️ Deliberately not uniform: one entry states a `mirrors` and the other the
    `jobs` form, one definition filters on types and the other does not, one
    carries a job no member names, and the second entry's trigger list and type
    clause are in an order neither file is in. Each of those is a shape the
    exemptions below assert stays green.
    """
    return Subject("github", copy.deepcopy(STATED), dict(PLANTED), DEFINITIONS["github"])


# --- the planted violations -------------------------------------------------


def _edit(path_suffix: str, old: str, new: str):
    """A plant that rewrites one definition's text, so the reader reads the result."""

    def apply(subject: Subject) -> Subject:
        for path in subject.texts:
            if path.endswith(path_suffix):
                assert old in subject.texts[path], (path, old)
                subject.texts[path] = subject.texts[path].replace(old, new, 1)
        return subject

    return apply


def _entry(index: int, **values):
    """A plant that rewrites one entry, so the reader's own walk reads the result.

    ⛔ The entry and not its record: a plant that edited the walked record would
    assert the comparison and leave the walk -- including every refusal § 2
    carries -- out of the assertion. A value of `None` deletes the key, which is
    how a plant states an entry that does not carry it at all.
    """

    def apply(subject: Subject) -> Subject:
        for key, value in values.items():
            if value is None:
                subject.entries[index].pop(key, None)
            else:
                subject.entries[index][key] = value
        return subject

    return apply


def _plant_a_renamed_workflow(subject: Subject) -> Subject:
    """The acceptance case: a `name:` edited and the facet left alone."""
    return _edit("first.yml", "name: First", "name: First, renamed")(subject)


def _plant_an_entry_naming_no_workflow(subject: Subject) -> Subject:
    subject.entries.append({"workflow": "A workflow nothing defines", "mirrors": "a-command"})
    return subject


def _plant_a_workflow_no_entry_names(subject: Subject) -> Subject:
    subject.texts[os.path.join(".github", "workflows", "third.yml")] = (
        "name: Third\non:\n  pull_request:\njobs:\n  third:\n    runs-on: ubuntu-latest\n"
    )
    return subject


def _plant_a_trigger_the_file_does_not_state(subject: Subject) -> Subject:
    return _entry(0, triggers=["pull_request -> *", "push -> main", "schedule -> *"])(subject)


def _plant_a_trigger_the_entry_does_not_state(subject: Subject) -> Subject:
    return _entry(0, triggers=["pull_request -> *"])(subject)


def _plant_a_type_clause_the_file_does_not_state(subject: Subject) -> Subject:
    return _entry(0, triggers=["pull_request(opened) -> *", "push -> main"])(subject)


def _plant_a_ref_the_file_does_not_state(subject: Subject) -> Subject:
    return _entry(0, triggers=["pull_request -> *", "push -> release"])(subject)


def _plant_a_filter_the_file_does_not_carry(subject: Subject) -> Subject:
    return _entry(0, paths=["plugins/**"])(subject)


def _plant_a_filter_the_entry_does_not_carry(subject: Subject) -> Subject:
    return _edit("first.yml", "  pull_request:\n", "  pull_request:\n    paths: [plugins/**]\n")(
        _edit("first.yml", "    branches: [main]\n", "    branches: [main]\n    paths: [plugins/**]\n")(
            subject
        )
    )


def _plant_a_filter_neither_side_spells_the_same(subject: Subject) -> Subject:
    return _entry(0, paths=["tools/**"])(
        _plant_a_filter_the_entry_does_not_carry(subject)
    )


def _plant_a_job_the_file_does_not_define(subject: Subject) -> Subject:
    return _entry(1, jobs=[{"job": "a-job-nothing-defines", "mirrors": "a-command"}])(subject)


def _plant_a_top_level_key_named_as_a_job(subject: Subject) -> Subject:
    """`concurrency` is a key of the document and not a job of it."""
    return _entry(0, mirrors=None, jobs=[{"job": "concurrency", "mirrors": "a-command"}])(subject)


# § 2's runner dimension. ⚠️ The baseline states no `host.runner` -- which is
# the legitimate absence and is asserted as an exemption of its own below -- so
# every plant here has to put **both** sides in play: a statement, and files
# that agree with it. `_states_a_runner` is that agreeing pair, and each
# violation below is it with one agreement withdrawn.

A_RUNNER = {
    "label": "a-runner-label",
    "concurrent_jobs": 1,
    "budget_minutes": 30,
    "supersedes": "a-supersession-group",
    "budget_is_a_queue_budget": True,
}

A_DEFAULT_LABEL = "    runs-on: ubuntu-latest\n"


def _states_a_runner(subject: Subject) -> Subject:
    """Both sides stating where the jobs run, in agreement.

    ⛔ Every job of every definition, not the first one found: a label is a
    job's key, so a plant that rewrote one job would leave the other disagreeing
    and every violation below would redden on the wrong half.
    """
    subject.runner = dict(A_RUNNER)
    group = (
        f"concurrency:\n  group: {A_RUNNER['supersedes']}\n"
        "  cancel-in-progress: true\n"
    )
    for path, text in list(subject.texts.items()):
        if isinstance(text, Exception):
            continue
        text = text.replace(
            A_DEFAULT_LABEL,
            f"    runs-on: {A_RUNNER['label']}\n"
            f"    timeout-minutes: {A_RUNNER['budget_minutes']}\n",
        )
        text = text.replace("concurrency:\n  group: first\n", "")
        subject.texts[path] = group + text
    return subject


def _plant_a_job_on_another_runner(subject: Subject) -> Subject:
    return _edit("second.yml", f"    runs-on: {A_RUNNER['label']}\n",
                 "    runs-on: another-runner-label\n")(_states_a_runner(subject))


def _plant_a_job_with_no_runner_at_all(subject: Subject) -> Subject:
    return _edit("first.yml", f"    runs-on: {A_RUNNER['label']}\n", "")(
        _states_a_runner(subject)
    )


def _plant_a_job_on_another_budget(subject: Subject) -> Subject:
    return _edit("second.yml", "    timeout-minutes: 30\n", "    timeout-minutes: 5\n")(
        _states_a_runner(subject)
    )


def _plant_a_job_with_no_budget(subject: Subject) -> Subject:
    """The measured hazard: a job on a single-runner account with nothing bounding it."""
    return _edit("first.yml", "    timeout-minutes: 30\n", "")(_states_a_runner(subject))


def _plant_another_supersession_group(subject: Subject) -> Subject:
    return _edit("second.yml", f"  group: {A_RUNNER['supersedes']}\n",
                 "  group: another-group\n")(_states_a_runner(subject))


def _plant_a_group_that_retires_nothing(subject: Subject) -> Subject:
    """The group stated and nothing cancelled: both runs finish and neither supersedes."""
    return _edit("first.yml", "  cancel-in-progress: true\n", "")(_states_a_runner(subject))


def _plant_a_workflow_with_no_group(subject: Subject) -> Subject:
    return _edit(
        "second.yml",
        f"concurrency:\n  group: {A_RUNNER['supersedes']}\n  cancel-in-progress: true\n",
        "",
    )(_states_a_runner(subject))


VIOLATIONS = [
    ("every entry names a workflow the host defines", "a workflow renamed with the facet left alone",
     _plant_a_renamed_workflow),
    ("every entry names a workflow the host defines", "an entry naming no definition",
     _plant_an_entry_naming_no_workflow),
    ("every workflow the host defines has an entry", "a definition no entry names",
     _plant_a_workflow_no_entry_names),
    ("every workflow the host defines has an entry", "the other half of a rename",
     _plant_a_renamed_workflow),
    ("every entry's triggers are its workflow's own", "a trigger the file does not fire on",
     _plant_a_trigger_the_file_does_not_state),
    ("every entry's triggers are its workflow's own", "a trigger the entry leaves out",
     _plant_a_trigger_the_entry_does_not_state),
    ("every entry's triggers are its workflow's own", "a type clause the file does not state",
     _plant_a_type_clause_the_file_does_not_state),
    ("every entry's triggers are its workflow's own", "a ref the file does not filter on",
     _plant_a_ref_the_file_does_not_state),
    ("every entry's paths are its workflow's own", "a filter the file does not carry",
     _plant_a_filter_the_file_does_not_carry),
    ("every entry's paths are its workflow's own", "a filter the entry does not carry",
     _plant_a_filter_the_entry_does_not_carry),
    ("every entry's paths are its workflow's own", "two spellings of one filter",
     _plant_a_filter_neither_side_spells_the_same),
    ("every job an entry names is its workflow's own", "a job the file does not define",
     _plant_a_job_the_file_does_not_define),
    ("every job an entry names is its workflow's own", "a top-level key named as a job",
     _plant_a_top_level_key_named_as_a_job),
    ("every job runs where the project says its jobs run", "a job on another runner",
     _plant_a_job_on_another_runner),
    ("every job runs where the project says its jobs run", "a job naming no runner",
     _plant_a_job_with_no_runner_at_all),
    ("every job carries the stated budget", "a job on another budget",
     _plant_a_job_on_another_budget),
    ("every job carries the stated budget", "a job with nothing bounding it",
     _plant_a_job_with_no_budget),
    ("the supersession group is the stated one", "a workflow in another group",
     _plant_another_supersession_group),
    ("the supersession group is the stated one", "a group that retires nothing",
     _plant_a_group_that_retires_nothing),
    ("the supersession group is the stated one", "a workflow with no group at all",
     _plant_a_workflow_with_no_group),
]


# --- the planted absences ---------------------------------------------------
#
# ⛔ The third answer, asserted on its own terms: each of these has to be
# **reported** and must not arrive as drift. A dimension that could not be read
# showing up in the problem list would be this check reporting the facet wrong on
# the strength of what it could not establish, and showing up nowhere would be
# the green § 2 forbids.


def _plant_a_kind_with_no_readable_definitions(subject: Subject) -> Subject:
    subject.kind = "a-host-whose-definitions-are-not-files"
    subject.texts = UNKNOWN
    subject.where = None
    return subject


def _plant_a_definition_with_no_name(subject: Subject) -> Subject:
    return _edit("first.yml", "name: First\n", "")(subject)


def _plant_a_definition_that_is_not_yaml(subject: Subject) -> Subject:
    return _edit("first.yml", "on:\n", "on:\n  - [unclosed\n")(subject)


def _plant_a_definition_that_cannot_be_opened(subject: Subject) -> Subject:
    """A file in the directory listing that the sweep could not then read."""
    for path in subject.texts:
        if path.endswith("first.yml"):
            subject.texts[path] = PermissionError("permission denied")
    return subject


def _plant_an_ignore_filter(subject: Subject) -> Subject:
    return _edit("first.yml", "    branches: [main]\n", "    branches-ignore: [docs/**]\n")(subject)


def _plant_events_filtered_differently(subject: Subject) -> Subject:
    return _edit("second.yml", "    types: [submitted]\n",
                 "    types: [submitted]\n    paths: [plugins/**]\n")(subject)


def _plant_an_entry_stating_no_triggers(subject: Subject) -> Subject:
    del subject.entries[0]["triggers"]
    return subject


def _plant_a_trigger_the_grammar_does_not_parse(subject: Subject) -> Subject:
    return _entry(0, triggers=["a pattern with no arrow in it"])(subject)


def _plant_a_job_filter_the_kind_cannot_carry(subject: Subject) -> Subject:
    return _entry(1, jobs=[{"job": "second", "mirrors": "the-second-command",
                            "paths": ["plugins/**"]}])(subject)


def _plant_a_runner_chosen_at_run_time(subject: Subject) -> Subject:
    return _edit("second.yml", f"    runs-on: {A_RUNNER['label']}\n",
                 "    runs-on: ${{ matrix.os }}\n")(_states_a_runner(subject))


def _plant_a_set_of_labels_where_one_is_stated(subject: Subject) -> Subject:
    return _edit("first.yml", f"    runs-on: {A_RUNNER['label']}\n",
                 "    runs-on: [self-hosted, linux]\n")(_states_a_runner(subject))


def _plant_a_budget_the_host_evaluates(subject: Subject) -> Subject:
    return _edit("second.yml", "    timeout-minutes: 30\n",
                 "    timeout-minutes: ${{ fromJSON(vars.BUDGET) }}\n")(
        _states_a_runner(subject)
    )


def _plant_a_group_the_host_evaluates(subject: Subject) -> Subject:
    return _edit("first.yml", f"  group: {A_RUNNER['supersedes']}\n",
                 "  group: ${{ github.workflow }}-${{ github.ref }}\n")(
        _states_a_runner(subject)
    )


ABSENCES = [
    ("a host kind whose definitions are not files", _plant_a_kind_with_no_readable_definitions),
    ("a definition stating no `name:`", _plant_a_definition_with_no_name),
    ("a definition that is not valid YAML", _plant_a_definition_that_is_not_yaml),
    ("a definition that could not be opened", _plant_a_definition_that_cannot_be_opened),
    ("an event block filtered on `branches-ignore`", _plant_an_ignore_filter),
    ("one workflow filtering its events differently", _plant_events_filtered_differently),
    ("an entry stating no `triggers`", _plant_an_entry_stating_no_triggers),
    ("a trigger § 2's grammar does not parse", _plant_a_trigger_the_grammar_does_not_parse),
    ("a job filter the host kind carries nowhere", _plant_a_job_filter_the_kind_cannot_carry),
    ("a runner chosen when the run starts", _plant_a_runner_chosen_at_run_time),
    ("a set of labels where § 2 states one", _plant_a_set_of_labels_where_one_is_stated),
    ("a budget the host evaluates", _plant_a_budget_the_host_evaluates),
    ("a supersession group the host evaluates", _plant_a_group_the_host_evaluates),
]


# --- the planted exemptions -------------------------------------------------
#
# The green side of the scope, which a count of drift cannot show. Each of these
# is a shape the facet and the files are *allowed* to differ in, and each was
# watched reddening with its own rule disabled.


def _plant_reordered_triggers(subject: Subject) -> Subject:
    """A trigger list in an order no file is in: the facet states a set (§ 2)."""
    return _entry(0, triggers=["push -> main", "pull_request -> *"])(subject)


def _plant_reordered_types(subject: Subject) -> Subject:
    """The types are a set and their order carries nothing (§ 2)."""
    return _entry(1, triggers=["pull_request(opened, edited) -> *",
                               "pull_request_review(submitted) -> *"])(subject)


def _plant_an_entry_mirroring_nothing(subject: Subject) -> Subject:
    """A run that duplicates no local command is still a run the facet states (§ 2)."""
    subject.entries[0].pop("mirrors")
    return subject


def _plant_a_quoted_name(subject: Subject) -> Subject:
    return _edit("first.yml", "name: First", 'name: "First"')(subject)


def _plant_an_inline_event_list(subject: Subject) -> Subject:
    """`on: [pull_request]` is the block form's own shorthand, filtering on nothing."""
    return _entry(0, triggers=["pull_request -> *"])(
        _edit("first.yml", "on:\n  pull_request:\n  push:\n    branches: [main]\n",
              "on: [pull_request]\n")(subject)
    )


def _plant_an_inline_event(subject: Subject) -> Subject:
    return _entry(0, triggers=["pull_request -> *"])(
        _edit("first.yml", "on:\n  pull_request:\n  push:\n    branches: [main]\n",
              "on: pull_request\n")(subject)
    )


def _plant_a_branch_list_of_several(subject: Subject) -> Subject:
    """Several refs of one event are several triggers, which the list already states."""
    return _entry(0, triggers=["pull_request -> *", "push -> main", "push -> release/*"])(
        _edit("first.yml", "    branches: [main]\n", "    branches: [main, release/*]\n")(subject)
    )


def _plant_a_block_sequence_filter(subject: Subject) -> Subject:
    """A filter written as a block sequence states what the flow sequence states."""
    return _entry(0, paths=["plugins/**"])(
        _edit("first.yml", "on:\n  pull_request:\n  push:\n    branches: [main]\n",
              "on:\n  pull_request:\n    paths:\n      - plugins/**\n  push:\n"
              "    branches: [main]\n    paths:\n      - plugins/**\n")(subject)
    )


def _plant_a_job_no_member_names(subject: Subject) -> Subject:
    """A job mirroring no local command is left out of the list rather than written in (§ 2)."""
    return _entry(1, jobs=[{"job": "second", "mirrors": "the-second-command"}])(subject)


def _plant_two_members_naming_one_job(subject: Subject) -> Subject:
    """The mapping is many-to-one towards the job, which § 2 declines to refuse."""
    return _entry(1, jobs=[{"job": "second", "mirrors": "the-second-command"},
                           {"job": "second", "mirrors": "a-second-command-of-that-job"}])(subject)


def _plant_a_runner_stated_and_met(subject: Subject) -> Subject:
    """Both sides stating one runner, one budget and one group: the green side."""
    return _states_a_runner(subject)


def _plant_no_runner_stated_and_the_files_disagreeing(subject: Subject) -> Subject:
    """§ 2's legitimate absence, asserted on the shape that would tempt a guess.

    ⛔ The files are deliberately left saying **different** things -- one job on
    a label the others are not, one with a budget and the rest without, one
    workflow in a group -- while the project states no `host.runner`. A check
    that had guessed the host kind's default, or taken the majority label as the
    answer, would report drift here. The project has stated that the kind's own
    default is the answer, and this check has no subject in that dimension.

    ⚠️ **Verified by disabling the exemption, twice.** With the label check's
    `runner is None` arm replaced by a guessed `ubuntu-latest`, this plant goes
    red; with the budget check's arm replaced by a guessed thirty minutes, it
    goes red again -- and that second run reddens the **baseline** too, which is
    the shape a guessed default has on every project in this repository. The
    group arm is the same `runner is None` guard and the same three lines; what
    is not asserted by disabling is the group arm alone, because a plant stating
    no `supersedes` cannot carry a group divergence to be found.
    """
    subject.runner = None
    return _edit("second.yml", A_DEFAULT_LABEL, "    runs-on: a-label-nobody-stated\n")(
        _edit("first.yml", A_DEFAULT_LABEL,
              A_DEFAULT_LABEL + "    timeout-minutes: 7\n")(subject)
    )


EXEMPTIONS = [
    ("a trigger list in another order", _plant_reordered_triggers),
    ("a type clause in another order", _plant_reordered_types),
    ("an entry mirroring nothing", _plant_an_entry_mirroring_nothing),
    ("a quoted `name:`", _plant_a_quoted_name),
    ("an inline event list", _plant_an_inline_event_list),
    ("a single event written as a scalar", _plant_an_inline_event),
    ("a `branches:` list of several patterns", _plant_a_branch_list_of_several),
    ("a filter written as a block sequence", _plant_a_block_sequence_filter),
    ("a job of the file no member names", _plant_a_job_no_member_names),
    ("two members naming one job", _plant_two_members_naming_one_job),
    ("a runner stated and every job meeting it", _plant_a_runner_stated_and_met),
    ("no runner stated, the files saying what they like",
     _plant_no_runner_stated_and_the_files_disagreeing),
]


# --- the planted subjects ---------------------------------------------------
#
# ⛔ The fourth reading, and the one neither a problem list nor an absence list
# can show: a project with nothing on either side. The first has to be reported
# as *no subject*; the second -- an empty facet with definitions behind it -- has
# to be drift instead, which is where this reading is most tempting and most
# wrong. The flag is which of the two a plant expects.


def _plant_both_sides_empty(subject: Subject) -> Subject:
    subject.entries = []
    subject.texts = {}
    return subject


def _plant_an_empty_facet_with_definitions(subject: Subject) -> Subject:
    subject.entries = []
    return subject


SUBJECTLESS = [
    ("nothing stated and nothing defined", _plant_both_sides_empty, True),
    ("an empty facet with definitions behind it", _plant_an_empty_facet_with_definitions, False),
]


# --- the reader's own cost --------------------------------------------------

# How many refs the adversarial definition states. ⚠️ Far past the point where a
# reader that proves failure by enumerating partitions of the rest of the file
# can finish: the shape this guards against took seconds at two dozen lines, and
# each line doubled it.
ADVERSARIAL_REFS = 1000

# The wall clock the read has to come in under. ⛔ Enforced rather than noted: a
# pattern that can backtrack exponentially is a gate that hangs the session it
# runs in rather than reddening, which is the one failure no problem list can
# report. Generous by three orders of magnitude against what a linear read costs,
# so a loaded runner does not redden this and nothing super-linear passes it.
ADVERSARIAL_BUDGET = 2.0


def _adversarial() -> tuple[str, set]:
    """A definition carrying the two shapes that wedge a line-unanchored pattern.

    Blank lines **inside** the event block and left-margin keys after it: a
    lookahead that cannot stop at a left-margin line following a blank one has no
    reachable stopping point, and proves its failure by partitioning the rest of
    the file. ⚠️ The answer is asserted beside the clock, because a reader can be
    fast and wrong -- swallowing `concurrency:` into the block is the measured
    form of that.
    """
    refs = [f"release/{number}" for number in range(ADVERSARIAL_REFS)]
    body = "".join(
        f"      - {ref}\n" + ("\n" if number % 8 == 7 else "")
        for number, ref in enumerate(refs)
    )
    text = (
        "name: Adversarial\n"
        "on:\n"
        "  push:\n"
        "    branches:\n"
        f"{body}"
        "\n"
        "permissions: {}\n"
        "\n"
        "concurrency:\n"
        "  group: adversarial\n"
        "\n"
        "jobs:\n"
        "  adversarial:\n"
        "    runs-on: ubuntu-latest\n"
    )
    return text, {("push", None, ref) for ref in refs}


def assert_the_reader_is_linear() -> list[str]:
    """The read of an adversarial definition, held to the clock and to its answer."""
    text, expected = _adversarial()
    started = time.perf_counter()
    found = read_definition(text, "planted/adversarial.yml")
    elapsed = time.perf_counter() - started
    failures = []
    if elapsed > ADVERSARIAL_BUDGET:
        failures.append(
            f"reading {ADVERSARIAL_REFS} refs took {elapsed:.3f}s, over the {ADVERSARIAL_BUDGET}s "
            f"budget. A reader that is super-linear in the block's length hangs the session "
            f"rather than reddening."
        )
    if found.triggers != expected:
        failures.append(
            f"read {len(found.triggers) if found.triggers is not UNKNOWN else 'nothing'} of "
            f"{len(expected)} refs, and a reader that is fast and wrong swallows the "
            f"left-margin keys after the block into it."
        )
    if found.name != "Adversarial" or found.jobs != {"adversarial"}:
        failures.append(
            f"read the name {found.name!r} and the jobs {found.jobs!r}, so the block did not "
            f"stop where the file ends it."
        )
    return failures


# --- the self-test ----------------------------------------------------------


def self_test() -> int:
    """Every plant, against a baseline whose own premises are asserted first.

    ⛔ The planted subject has to start in **agreement and fully established**,
    and both halves are checked before a plant runs. A plant measured against a
    baseline that already drifts proves nothing, and one measured against a
    baseline that already reports an absence makes the absence assertions pass
    for the wrong reason -- which is the shape that holds while asserting
    nothing.
    """
    by_name = dict(CHECKS)
    subject = _a_subject()
    baseline = {name: set(check(subject)) for name, check in CHECKS}
    absent = set(undeterminable(subject))
    failures = 0

    if absent:
        print(f"  UNDETERMINED BASELINE  the planted subject reports {len(absent)} absence(s)")
        for line in sorted(absent):
            print(f"                         - {line}")
        failures += 1
    if any(baseline.values()):
        print("  DRIFTED BASELINE       the planted subject does not agree with itself")
        for name, found in baseline.items():
            for line in sorted(found):
                print(f"                         - {name}: {line}")
        failures += 1

    for name, label, plant in VIOLATIONS:
        if set(by_name[name](plant(subject.copy()))) - baseline[name]:
            print(f"  red on                 {name}: {label}")
        else:
            print(f"  STAYED GREEN           {name}: {label}")
            failures += 1

    for label, plant in ABSENCES:
        planted = plant(subject.copy())
        reported = set(undeterminable(planted)) - absent
        drifted = {
            line for _name, check in CHECKS for line in check(planted)
        } - {line for found in baseline.values() for line in found}
        if not reported:
            print(f"  WENT UNREPORTED        absent: {label}")
            failures += 1
        elif drifted:
            print(f"  REPORTED AS DRIFT      absent: {label}")
            failures += 1
        else:
            print(f"  reported               absent: {label}")

    for label, plant, subjectless in SUBJECTLESS:
        planted = plant(subject.copy())
        said = no_subject(planted) is not None
        drifted = bool([line for _name, check in CHECKS for line in check(planted)])
        if said is not subjectless:
            print(
                f"  {'CLAIMED A SUBJECT' if subjectless else 'STOOD DOWN':<22} "
                f"subject: {label}"
            )
            failures += 1
        elif not subjectless and not drifted:
            print(f"  REPORTED NO DRIFT      subject: {label}")
            failures += 1
        else:
            print(f"  {'no subject' if subjectless else 'red on':<22} subject: {label}")

    for label, plant in EXEMPTIONS:
        planted = plant(subject.copy())
        added = {line for _name, check in CHECKS for line in check(planted)} - {
            line for found in baseline.values() for line in found
        }
        reported = set(undeterminable(planted)) - absent
        if added:
            print(f"  WENT RED               exempt: {label}")
            failures += 1
        elif reported:
            print(f"  WENT UNDETERMINED      exempt: {label}")
            failures += 1
        else:
            print(f"  green on               exempt: {label}")

    over = assert_the_reader_is_linear()
    for line in over:
        print(f"  OVER BUDGET            linear: {line}")
        failures += 1
    if not over:
        print(f"  linear on              {ADVERSARIAL_REFS} refs, under {ADVERSARIAL_BUDGET}s")

    if failures:
        print(
            f"\n{failures} assertion(s) did not hold. A check that cannot fail is not a check, "
            "an absence that is not reported is a green nobody earned, and an exemption that "
            "cannot pass is not an exemption."
        )
    return 1 if failures else 0


# --- the command ------------------------------------------------------------


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Hold `host.checks` to the host's own workflow definitions (§ 2).",
    )
    parser.add_argument(
        "--skills-root",
        default=".",
        help="the root the configuration is resolved relative to (§ 1)",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="assert each check reddens on each planted violation, each planted absence is "
        "reported, each planted exemption stays green and the reader is linear, then hold "
        "the facet",
    )
    args = parser.parse_args(argv)

    if args.self_test:
        print(
            "Asserting the checks redden on each planted violation "
            f"({len(VIOLATIONS)}), report each planted absence ({len(ABSENCES)}), read each "
            f"planted subject ({len(SUBJECTLESS)}), stay green on each planted exemption "
            f"({len(EXEMPTIONS)}), and read an adversarial definition in linear time:"
        )
        if self_test():
            return 1
        print()

    try:
        subject = read_subject(args.skills_root)
    except reader.ConfigError as error:
        print(str(error), file=sys.stderr)
        return 1

    absent = no_subject(subject)
    if absent is not None:
        # ⛔ Not a verdict. A run printing green with nothing on either side to
        # compare would be a check holding nothing, which reports green forever.
        print(absent, file=sys.stderr)
        return 2

    results = run(subject)
    for name, found in results.items():
        print(f"  {'FAIL' if found else 'ok  '}  {name}")

    problems = [problem for found in results.values() for problem in found]
    notes = undeterminable(subject)
    if problems:
        print(f"\n{len(problems)} drift(s) between `host.checks` and {subject.directory}:\n")
        for problem in problems:
            print(f"  - {problem}")
    if notes:
        print(f"\n{len(notes)} dimension(s) this run could not establish:\n")
        for note in notes:
            print(f"  - {note}")

    if problems:
        print(
            "\n⛔ Which side is wrong is not this check's to say, and nothing here was edited: "
            "a statement the host's own definitions contradict is repaired by whoever knows "
            "which of the two was meant."
        )
        return 1
    if notes:
        print(
            "\nNo drift was found and the run is not green: a dimension that could not be "
            "established is no answer about the facet (§ 2), never agreement with it."
        )
        return 2
    print(
        f"\n`host.checks` states {len(subject.checks)} run(s) and "
        f"{len(subject.definitions)} definition(s) under {subject.directory} state the same "
        "names, triggers, paths and jobs."
    )
    # ⛔ Said rather than left to be inferred from the green above: a dimension
    # this run did not compare is not a dimension it agreed on, and the absent
    # runner statement is the one place that distinction is invisible otherwise.
    print(
        "`host.runner` states where the jobs run, and every job meets it."
        if subject.runner is not None else
        "`host.runner` is absent, so where the jobs run was not compared at all: § 2 "
        "makes that the host kind's own default answering, and this check holds no "
        "label, budget or supersession group against a file."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
