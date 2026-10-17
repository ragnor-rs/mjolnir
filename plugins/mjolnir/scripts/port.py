#!/usr/bin/env python3
"""The tracker port: one contract, and what happens where an operation is absent.

The shared procedure names **the port and never a tracker**. This module is that
port: it reads the operation list and the absent case out of the surface beside
it -- `../config/schema.md` § 3 -- answers whether a given operation is available
here, and resolves the one that is not into the fallback the surface states for
it. An implementation per tracker registers itself; the contract itself knows
none of them by name.

Three things it deliberately does not do:

  * **It carries no operation list and no fallback text of its own.** Both are
    read at run time from § 3's table, so an operation added to the surface is
    accepted here without this module changing, and a fallback reworded there is
    reworded everywhere. The self-test holds this file to naming no tracker the
    surface declares, so a branch on one reddens the build rather than being
    noticed in review.
  * **It never raises on an absence.** A capability that is missing, a role no
    status maps, a configuration with no tracker at all and a tracker whose
    adapter has not been built yet are four different outcomes and none of them
    is an error. Every one of them comes back as an `Outcome` naming the
    fallback taken. What raises -- always with the key named, the way
    `config.py` refuses a configuration the surface does not allow -- is a
    statement that is **missing or ambiguous rather than absent**: § 3's table
    stating no operation, two tables stating it, an operation stated twice or in
    a row with a cell missing, an operation whose absent case is blank, an
    operation asked for or implemented that the surface does not state, two
    adapters for one kind, and a role mapped to two status words. None of those
    is a tracker that cannot do something; each is a text that does not say what
    the procedure is supposed to do.
  * **It does not decide what a role then does.** The port reports which
    fallback was taken; whether that stops the role is the role's business, the
    way `config.py` reports what a configuration cannot support without acting
    on it.

**A capability is the adapter's fact, not the project's** (§ 3). Nothing on the
surface lets a project claim an operation its tracker cannot do, so nothing here
reads one: the query goes to the implementation, which declares an operation by
implementing it.

Usage:
    port.py [--skills-root DIR]   print the port's state here as JSON
    port.py --self-test           hold the contract to the surface and the
                                  examples, then print what it found
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

import config
from config import ConfigError

# --- what the surface states -----------------------------------------------
#
# Grammar only, per the rule above: the table is found by its column headers
# rather than by a section number, so renumbering § 3 changes nothing. The first
# and last headers are the two cells this module reads -- the operation and its
# absent case -- and the column between them is for the person reading § 3.

OPERATION_COLUMN = "Operation"
ABSENT_COLUMN = "When the capability is absent"

# An operation's name, written as a code span in the first cell. A row whose
# first cell is prose is not an operation, which is what keeps this from reading
# the three documents' tables if the headers ever collide.
OPERATION_NAME = re.compile(r"^`(?P<name>[a-z][a-z0-9_]*)`$")

# The two writers this module has to tell apart from the rest, spelled out
# because which member of the `writer` set means what is not something an
# alternation says. Both are held to the surface by the self-test -- the
# discipline `config.py` already applies to its own two -- so renaming one there
# reddens the build instead of silently turning a refusal into the wrong words.
# `never` needs its own: § 4.2 states it as the case where the procedure writes
# nothing *and reports*, so a refusal handing the move to "that writer" would
# name a writer that does not exist.
PROCEDURE = "procedure"
NEVER = "never"

# A table row's cells, split on its **unescaped** pipes -- the grammar
# `tools/check_single_source.py` already reads markdown tables with. A pipe
# inside a cell is written `\|`, and splitting on every pipe would silently shift
# every cell after it: measured on a fallback containing an alternation, which is
# this surface's own idiom, the operation took the wrong column's text.
CELL_SPLIT = re.compile(r"(?<!\\)\|")


def _row(line: str) -> list[str]:
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|") and not stripped.endswith(r"\|"):
        stripped = stripped[:-1]
    return [cell.strip().replace(r"\|", "|") for cell in CELL_SPLIT.split(stripped)]


def _tables(text: str) -> list[list[list[str]]]:
    """Every markdown table in document order, as rows of stripped cells.

    Fenced blocks are skipped by a line toggle rather than a paired regex, for
    the reason the sweep in `tools/` records: one trailing space after a fence's
    language tag makes a paired regex pair the wrong fences. ⚠️ A fence also
    **ends** the table above it -- it used to merely be skipped, which glued an
    unrelated table's rows onto the one before it and read them as operations.
    """
    tables: list[list[list[str]]] = []
    current: list[list[str]] = []

    def flush() -> None:
        nonlocal current
        if current:
            tables.append(current)
            current = []

    fenced = False
    for line in text.splitlines():
        if line.lstrip().startswith(("```", "~~~")):
            fenced = not fenced
            flush()
            continue
        if not fenced and line.lstrip().startswith("|"):
            cells = _row(line)
            if not all(set(cell) <= set("-: ") for cell in cells):
                current.append(cells)
            continue
        flush()
    flush()
    return tables


def operations(surface_text: str) -> dict[str, str]:
    """`operation -> what the procedure does when its capability is absent`.

    Read from § 3's table. Four shapes are refused rather than read past, each
    naming what it refuses on, because every one of them silently changes the
    list or a fallback: a second table with these headers (the list is stated
    once), an operation stated twice, a row with a cell missing or added, and an
    operation whose absent case is blank. A fallback nobody wrote is the absence
    this contract exists to remove, and defaulting one here would move the text
    into this file.
    """
    found: dict[str, str] = {}
    matching = 0
    for table in _tables(surface_text):
        header = table[0]
        if header[0] != OPERATION_COLUMN or header[-1] != ABSENT_COLUMN:
            continue
        matching += 1
        if matching > 1:
            raise ConfigError(
                os.path.relpath(config.SURFACE, config.PLUGIN_ROOT),
                f"states more than one `{OPERATION_COLUMN}` / `{ABSENT_COLUMN}` "
                "table, so the operation list is stated more than once and the "
                "tables may disagree. § 3 states it once.",
            )
        for cells in table[1:]:
            match = OPERATION_NAME.match(cells[0])
            if not match:
                continue
            name = match.group("name")
            if len(cells) != len(header):
                # A row one cell short takes the *middle* column as its absent
                # case and reads as a perfectly good fallback. Measured on a row
                # whose last two pipes had nothing between them.
                raise ConfigError(
                    f"tracker.operations.{name}",
                    f"is stated in a row of {len(cells)} cells where the table's "
                    f"header has {len(header)}. A row with a cell missing takes "
                    "another column's text as its absent case and reads as sound.",
                )
            fallback = " ".join(cells[-1].split())
            if name in found:
                # Two rows for one operation are two fallbacks that may
                # disagree, which is the defect this contract is here to stop
                # rather than something to resolve by row order.
                raise ConfigError(
                    f"tracker.operations.{name}",
                    "is stated twice, so it has two absent cases and the second "
                    "would silently win. One row per operation.",
                )
            if not fallback:
                raise ConfigError(
                    f"tracker.operations.{name}",
                    "is stated with no absent case. Every operation states what "
                    "the procedure does when its capability is missing -- that "
                    "table column is the fallback, and nothing here supplies one.",
                )
            found[name] = fallback

    if not found:
        raise ConfigError(
            os.path.relpath(config.SURFACE, config.PLUGIN_ROOT),
            f"states no `{OPERATION_COLUMN}` / `{ABSENT_COLUMN}` table whose rows "
            "name an operation, so the port has no operation list to hold an "
            "adapter to. Either the surface changed shape or the table's headers "
            "were reworded.",
        )
    return found


# A tracker's name reaches the surface as a `kind:` slug and prose as words, so
# the slug alone is the one spelling nobody writes. The de-slugged form is the
# grammar the sweep in `tools/` reads tracker names with, and this module holds
# itself to the same one rather than to a weaker substring test.
def names_a_tracker(text: str, kinds: list[str]) -> list[str]:
    """Which of `kinds` the text names, in either spelling, ignoring case."""
    found = []
    for kind in kinds:
        words = r"[\s_-]*".join(re.escape(part) for part in kind.split("-"))
        if re.search(words, text, re.I):
            found.append(kind)
    return found


def surface_operations() -> dict[str, str]:
    with open(config.SURFACE, encoding="utf-8") as handle:
        return operations(handle.read())


# --- the contract ----------------------------------------------------------


class Adapter:
    """One tracker behind the port.

    An adapter is a mapping from an operation's name to the callable that
    performs it, and that mapping **is** the capability declaration (§ 3): there
    is no second list to disagree with it. An operation the surface does not
    state is refused at registration, so an adapter cannot grow a private
    operation that no role could portably call.
    """

    def __init__(self, operations: dict[str, object] | None = None):
        self.operations = dict(operations or {})

    def implements(self, operation: str) -> bool:
        return operation in self.operations

    def hold_to(self, stated: dict[str, str]) -> None:
        for name in sorted(self.operations):
            if name not in stated:
                raise ConfigError(
                    f"tracker.operations.{name}",
                    "is implemented by an adapter and is not an operation the "
                    "surface states. The operation list is closed: a tracker's "
                    "own extra is either one of the stated operations or a shape "
                    "the surface has to grow first.",
                )


# The trackerless adapter (§ 3): it implements nothing, so every operation takes
# its stated fallback. It is an adapter rather than a branch in the procedure --
# which is the whole of why `tracker.kind: none` reports as a configuration and
# never as a broken install.
TRACKERLESS = Adapter()

# Installed implementations, by `tracker.kind`. Empty today: the three adapters
# and this repository's own are separate work items, and the contract is what
# they register against. A role never reads this -- it asks a `Port`.
ADAPTERS: dict[str, Adapter] = {}


def register(kind: str, adapter: Adapter) -> None:
    """Install an implementation for one `tracker.kind`."""
    if kind in ADAPTERS:
        raise ConfigError(
            f"tracker.kind.{kind}",
            "already has an implementation registered. Two adapters for one "
            "kind means a role's capability query has two answers.",
        )
    adapter.hold_to(surface_operations())
    ADAPTERS[kind] = adapter


class Outcome:
    """What the port did about one operation, or did not do and why.

    Returned for every outcome that is not the toolkit's own mistake: performed,
    fallen back, or refused by a status's writer. A role reads `performed` and,
    where that is false, says `detail` out loud -- which is how an absence
    reaches a person as a stated decision rather than as a traceback.
    """

    def __init__(
        self,
        operation: str,
        *,
        performed: bool,
        detail: str,
        result: object = None,
        refused: bool = False,
        writer: str | None = None,
    ):
        self.operation = operation
        self.performed = performed
        self.detail = detail
        self.result = result
        self.refused = refused
        self.writer = writer

    def __bool__(self) -> bool:
        return self.performed

    def __str__(self) -> str:
        return f"{self.operation}: {self.detail}"


class Port:
    """The tracker port over one project's configuration."""

    def __init__(
        self,
        configuration: config.Config,
        *,
        adapter: Adapter | None = None,
        stated: dict[str, str] | None = None,
    ):
        self.config = configuration
        self.stated = stated if stated is not None else surface_operations()
        # An adapter handed in directly -- by a role under test, or by a project
        # carrying its own -- is held to the surface exactly as a registered one
        # is. Skipping that here would leave `register` the only guarded route.
        if adapter is not None:
            adapter.hold_to(self.stated)
        self._given = adapter

    @property
    def kind(self) -> str:
        return self.config.tracker_kind

    @property
    def adapter(self) -> Adapter | None:
        """The implementation answering here, or `None` where none is installed.

        The trackerless configuration gets the trackerless adapter -- a stated
        decision. A configured kind with nothing registered gets `None`, which is
        an adapter that has not been built yet. Both leave every operation
        unavailable and they are **not** the same fact, so they are reported
        apart (§ 3).
        """
        if self._given is not None:
            return self._given
        if not self.config.has_tracker:
            return TRACKERLESS
        return ADAPTERS.get(self.kind)

    # -- the capability query. Never assumed, never read from a configuration.

    def implements(self, operation: str) -> bool:
        self._stated(operation)
        adapter = self.adapter
        return adapter is not None and adapter.implements(operation)

    def fallback(self, operation: str) -> str:
        return self._stated(operation)

    def _stated(self, operation: str) -> str:
        try:
            return self.stated[operation]
        except KeyError:
            raise ConfigError(
                f"tracker.operations.{operation}",
                "is not an operation the surface states. The list is closed and "
                f"holds: {', '.join(sorted(self.stated))}.",
            ) from None

    def invoke(self, operation: str, *args, **kwargs) -> Outcome:
        """Perform an operation, or come back with the fallback stated for it."""
        fallback = self._stated(operation)
        adapter = self.adapter
        if adapter is None or not adapter.implements(operation):
            return Outcome(operation, performed=False, detail=fallback)
        return Outcome(
            operation,
            performed=True,
            detail=f"performed by the `{self.kind}` implementation of the port.",
            result=adapter.operations[operation](*args, **kwargs),
        )

    # -- the one operation the surface guards with more than a capability

    def advance_to(self, role: str, *args, **kwargs) -> Outcome:
        """Ask for an advance to a status **role**, never to a status word.

        Four answers are reports rather than exceptions: no status here maps the
        role, which is a legitimate configuration (§ 4.2); the configured writer
        is somebody else, which is a refusal naming that writer; the writer is
        `never`, which § 4.2 states as the case where the procedure writes
        nothing at all and reports -- so the refusal hands the move to nobody,
        there being no writer to hand it to; or the move goes through `set_state`
        and its capability decides. What is refused with the key named, the way
        the reader refuses a configuration the surface does not allow, is a role
        mapped to two status words (§ 4.2 states the mapping is at most one).
        """
        # Named rather than written into the two Outcomes below: an operation the
        # surface has renamed must stop this role rather than have it report a
        # move against an operation that no longer exists.
        self._stated("set_state")
        statuses = [
            status
            for status in (self.config.get("statuses") or [])
            if status.get("role") == role
        ]
        if not statuses:
            return Outcome(
                "set_state",
                performed=False,
                detail=f"No status here maps the `{role}` role, so there is "
                "nothing to advance to. A project maps a subset and an absent "
                "role is a legitimate configuration.",
            )
        if len(statuses) > 1:
            # Taking the first would be the plausible-thing-first failure the
            # surface keeps naming: the procedure asks for a role, and a role
            # answered by two status words has no answer. § 4.2 states the
            # mapping is at most one, and this is where that is read.
            words = ", ".join(f"`{status.get('name')}`" for status in statuses)
            raise ConfigError(
                "statuses",
                f"maps the `{role}` role to more than one status ({words}). § 4.2 "
                "maps a role to at most one status, because the procedure asks to "
                "advance to a role and two status words leave the move undefined.",
            )

        status = statuses[0]
        writer = status.get("writer")
        if writer == NEVER:
            return Outcome(
                "set_state",
                performed=False,
                refused=True,
                writer=writer,
                detail=f"Refused: the `{role}` status (`{status.get('name')}`) is "
                f"`writer: {NEVER}` here, so the procedure writes nothing at all "
                "and reports instead. There is no other writer to hand the move "
                "to -- the credential acts as a person's own account, and every "
                "write would read as that person speaking.",
            )
        if writer != PROCEDURE:
            return Outcome(
                "set_state",
                performed=False,
                refused=True,
                writer=writer,
                detail=f"Refused: the `{role}` status (`{status.get('name')}`) is "
                f"written by `{writer}` here, not by the procedure. The move is "
                "reported for that writer to make rather than made.",
            )
        return self.invoke("set_state", *args, **kwargs)

    # -- what this configuration cannot do, as a report and never as a fault

    def report(self) -> list[str]:
        out = []
        if self.adapter is TRACKERLESS:
            # What the absence *means* per operation, and not a second statement
            # that the absence exists: the reader already reports that, and two
            # hand-written sentences for one fact is the defect, not the report.
            out.append(
                "The configuration states no tracker, so the port implements "
                "nothing and every operation below takes its stated fallback."
            )
        elif self.adapter is None:
            out.append(
                f"No implementation of the port is installed for "
                f"`tracker.kind: {self.kind}`, so every operation below takes "
                "its stated fallback. That is an adapter not built yet rather "
                "than a project that needs no tracker, and the two read apart "
                "here for exactly that reason."
            )
        for operation in sorted(self.stated):
            if not self.implements(operation):
                out.append(f"`{operation}` is unavailable: {self.fallback(operation)}")
        return out

    def to_dict(self) -> dict:
        # Three states, not a boolean: `installed: true` read as an adapter for
        # this tracker where the answer was the trackerless one, which is the
        # distinction § 3 asks the port to keep.
        adapter = (
            "trackerless"
            if self.adapter is TRACKERLESS
            else "absent"
            if self.adapter is None
            else "registered"
        )
        return {
            "kind": self.kind,
            "adapter": adapter,
            "operations": {
                operation: {
                    "available": self.implements(operation),
                    "absent": fallback,
                }
                for operation, fallback in sorted(self.stated.items())
            },
            "report": self.report(),
        }


def load(skills_root: str = ".", **kwargs) -> Port:
    """The port over the configuration at `skills_root`, read through #1's reader."""
    return Port(config.load(skills_root, **kwargs))


# --- self-test -------------------------------------------------------------
#
# The acceptance check of the work item this contract was built for, run as
# code: the contract is read from the surface, an absent capability produces the
# stated fallback and never an error, a state whose writer is not the procedure
# is refused with the writer named, and the trackerless configuration has every
# operation unavailable while reporting no fault. One planted violation per
# branch that does real work, which is the standard the two gates in `tools/`
# set.


def _examples() -> list[str]:
    return sorted(
        os.path.join(config.EXAMPLES, name)
        for name in os.listdir(config.EXAMPLES)
        if name.endswith((".yaml", ".yml"))
    )


def _loaded() -> dict[str, config.Config]:
    out = {}
    for path in _examples():
        with open(path, encoding="utf-8") as handle:
            out[os.path.basename(path)] = config.load_text(handle.read(), config.EXAMPLES)
    return out


def _any_example() -> config.Config:
    """Any whole example, to put a contract question to.

    Taken from the directory rather than named, for the reason `config.py` gives
    for the same choice: a fixture that names one tracker is this toolkit's code
    naming a tracker.
    """
    return _loaded()[os.path.basename(_examples()[0])]


def _with_statuses(statuses: list[dict]) -> config.Config:
    configuration = _any_example()
    configuration.data["statuses"] = statuses
    return configuration


def _refused(call) -> str | None:
    """The key a call refuses on, or None where it returns instead."""
    try:
        call()
    except ConfigError as error:
        return error.key
    return None


def _real_tracker_kinds() -> list[str]:
    """Every `tracker.kind` the surface states that is a tracker.

    Derived rather than listed, and the trackerless member is found by asking
    the reader rather than by spelling its name here -- which is the whole point
    of the check this feeds: nothing in this file may name a tracker.
    """
    with open(config.SURFACE, encoding="utf-8") as handle:
        facts = config.surface_facts(handle.read())
    kinds = facts["enums"].get("tracker.kind", [])
    return [
        kind
        for kind in kinds
        if config.Config({"tracker": {"kind": kind}}, ".", facts).has_tracker
    ]


def self_test() -> int:
    failures = 0

    def check(label: str, condition: bool, detail: str = "") -> None:
        nonlocal failures
        if condition:
            print(f"  ok    {label}")
        else:
            failures += 1
            print(f"  FAIL  {label}{': ' + detail if detail else ''}")

    # ⛔ Read the surface through `check` rather than beside it. The reader's
    # own suite learned this the hard way one file over: the command the
    # workflow runs must come back with a verdict, so a § 3 this module cannot
    # parse is a red line and a non-zero exit, never a traceback where the
    # report should be.
    with open(config.SURFACE, encoding="utf-8") as handle:
        surface_text = handle.read()
    try:
        stated = operations(surface_text)
        broken = None
    except ConfigError as error:
        stated, broken = {}, str(error)
    check("the surface states the operation list this contract holds", bool(stated), broken or "")
    if not stated:
        print(f"\n{failures} assertion(s) did not hold.")
        return 1

    # Five plants against § 3's table, each a shape that silently changes the
    # list or a fallback rather than announcing itself. ⚠️ None of them names a
    # line number or assumes a cell's spacing: a plant that hardcodes the text
    # it plants into turns a reformatted table into a dead self-test, which is
    # the failure the sweep in `tools/` records having paid for.
    first = sorted(stated)[0]
    # Matched on the row's **first cell**, not on the operation appearing
    # anywhere in the line: one fallback names another operation, so a
    # substring match planted into the wrong row and the plants reported a
    # refusal about a different operation while reading green.
    row = next(
        (
            line
            for line in surface_text.splitlines()
            if line.lstrip().startswith("|") and _row(line)[0] == f"`{first}`"
        ),
        None,
    )
    check(f"§ 3 states `{first}` in a row this suite can plant into", row is not None)

    without_table = surface_text.replace(f"| {OPERATION_COLUMN} |", "| Thing |", 1)
    surface_name = os.path.relpath(config.SURFACE, config.PLUGIN_ROOT)
    plants = [
        ("a surface stating no operation table", without_table, surface_name),
    ]
    if row:
        cells = _row(row)
        plants += [
            (
                "an operation stated with no absent case",
                surface_text.replace(row, "| " + " | ".join(cells[:-1]) + " |  |", 1),
                f"tracker.operations.{first}",
            ),
            (
                "an operation stated twice",
                surface_text.replace(row, row + "\n" + row, 1),
                f"tracker.operations.{first}",
            ),
            (
                "an operation stated in a row with a cell missing",
                surface_text.replace(row, "| " + " | ".join(cells[:-1]) + " |", 1),
                f"tracker.operations.{first}",
            ),
            (
                "a second table stating the operation list",
                surface_text + "\n" + "\n".join(
                    ["| " + " | ".join([OPERATION_COLUMN, "Asks", ABSENT_COLUMN]) + " |",
                     "|---|---|---|",
                     row]
                ) + "\n",
                surface_name,
            ),
        ]
    for label, planted, key in plants:
        reported = _refused(lambda text=planted: operations(text))
        check(f"{label} is refused, naming {key}", reported == key, f"reported {reported!r}")

    # A pipe inside a cell is written `\|` and must stay inside it. Planted on
    # the fallback the module exists to carry, because getting this wrong hands
    # a role a truncated instruction that reads as a whole one.
    if row:
        cells = _row(row)
        escaped = "| " + " | ".join(cells[:-1] + [r"wait \| then report"]) + " |"
        planted = operations(surface_text.replace(row, escaped, 1))
        check(
            "a pipe escaped inside a fallback stays inside it",
            planted[first] == "wait | then report",
            f"read {planted[first]!r}",
        )

    # A fenced block ends the table above it, so an unrelated table below one
    # cannot contribute operations.
    glued = (
        surface_text
        + "\n```yaml\nkey: value\n```\n| Thing | Other |\n|---|---|\n| `telepathy` | x |\n"
    )
    check(
        "a table after a fenced block is not read as part of the operation table",
        "telepathy" not in operations(glued),
        f"read {sorted(operations(glued))!r}",
    )

    # An absent capability resolves to the stated fallback, for every operation,
    # and nothing raises on the way. This is the acceptance item that would be
    # vacuous if it were only asserted of the trackerless adapter, so it runs
    # over a double that implements nothing and over one that implements half.
    nothing = Port(_any_example(), adapter=Adapter(), stated=stated)
    fallbacks = {
        operation: nothing.invoke(operation) for operation in sorted(stated)
    }
    check(
        "an absent capability comes back as the surface's stated fallback",
        all(
            not outcome.performed and outcome.detail == stated[operation]
            for operation, outcome in fallbacks.items()
        ),
        f"got {[str(o) for o in fallbacks.values()]!r}",
    )
    # The other way an operation can be unavailable: no implementation at all,
    # rather than one that implements nothing. Both have to come back as the
    # fallback, and the first draft tested only the second.
    with_tracker = [c for c in _loaded().values() if c.has_tracker]
    trackerless = [c for c in _loaded().values() if not c.has_tracker]
    # ⛔ Asserted here, before anything indexes either list. The guard used to
    # sit a hundred lines below the first `[0]`, so an examples directory with
    # one kind of configuration in it killed the run with an `IndexError` where
    # the verdict belongs -- dead exactly when it was needed.
    check("an example configures a tracker", bool(with_tracker))
    check("an example configures no tracker", bool(trackerless))
    if with_tracker:
        uninstalled = Port(with_tracker[0], stated=stated)
        check(
            "an operation with no implementation installed falls back too, and does not raise",
            all(
                not uninstalled.invoke(operation).performed
                and uninstalled.invoke(operation).detail == stated[operation]
                for operation in stated
            ),
        )

    half = sorted(stated)[: max(1, len(stated) // 2)]
    performed = Port(
        _any_example(),
        adapter=Adapter({name: lambda *a, **k: "done" for name in half}),
        stated=stated,
    )
    check(
        "a declared capability is performed by the implementation",
        all(performed.invoke(name).performed for name in half),
    )
    check(
        "the capability query answers from the implementation, not a configuration",
        all(performed.implements(name) for name in half)
        and not any(performed.implements(n) for n in stated if n not in half),
    )
    check(
        "an operation the surface does not state is refused, naming it",
        _refused(lambda: nothing.invoke("telepathy")) == "tracker.operations.telepathy",
        f"reported {_refused(lambda: nothing.invoke('telepathy'))!r}",
    )
    check(
        "an adapter implementing an unstated operation is refused, naming it",
        _refused(
            lambda: Port(
                _any_example(), adapter=Adapter({"telepathy": lambda: None}), stated=stated
            )
        )
        == "tracker.operations.telepathy",
    )

    # § 4.2's refusal, which is the one guard above a capability: the procedure
    # asks for a role and is told whose state it is. ⚠️ The role words are taken
    # from the surface's own `role` set rather than written here -- the writers
    # were derived from the start and the roles were not, which left three
    # status words copied into this file with nothing holding them to § 4.2.
    roles = config.facts_for("role")
    check("the surface states the `role` set this suite advances to", bool(roles))
    a_role, another_role = (roles + roles)[0], (roles + roles)[1]
    for writer in [w for w in config.facts_for("writer") if w != PROCEDURE]:
        configuration = _with_statuses(
            [{"name": "a status", "role": a_role, "writer": writer}]
        )
        outcome = Port(configuration, adapter=Adapter(), stated=stated).advance_to(a_role)
        check(
            f"an advance to a status written by `{writer}` is refused, naming the writer",
            outcome.refused and outcome.writer == writer and writer in outcome.detail,
            f"got {str(outcome)!r}",
        )
        if writer == NEVER:
            # § 4.2's strictest case: the procedure writes nothing *and
            # reports*. The generic refusal hands the move to "that writer to
            # make", which for `never` names a writer that does not exist --
            # measured on a shipped example, where three of four statuses carry
            # it.
            check(
                f"the `{NEVER}` refusal hands the move to nobody",
                "writer to make" not in outcome.detail
                and "no other writer" in outcome.detail,
                f"got {str(outcome)!r}",
            )

    through = Port(
        _with_statuses([{"name": "a status", "role": a_role, "writer": PROCEDURE}]),
        adapter=Adapter({"set_state": lambda *a, **k: "moved"}),
        stated=stated,
    )
    advanced = through.advance_to(a_role)
    check(
        "an advance the procedure may write goes through the capability",
        advanced.performed and advanced.result == "moved" and not advanced.refused,
        f"got {str(advanced)!r}",
    )
    twice = _with_statuses(
        [
            {"name": "one word", "role": a_role, "writer": PROCEDURE},
            {"name": "another", "role": a_role, "writer": PROCEDURE},
        ]
    )
    ambiguous = _refused(
        lambda: Port(twice, adapter=Adapter(), stated=stated).advance_to(a_role)
    )
    check(
        "a role mapped to two status words is refused, naming the key",
        ambiguous == "statuses",
        f"reported {ambiguous!r}",
    )
    unmapped = Port(_with_statuses([]), adapter=Adapter(), stated=stated).advance_to(another_role)
    check(
        "an advance to a role no status maps is reported, not refused and not raised",
        not unmapped.performed and not unmapped.refused and another_role in unmapped.detail,
        f"got {str(unmapped)!r}",
    )

    # The trackerless configuration, which is this contract's own acceptance
    # item: every operation unavailable, and nothing reading as a fault.
    for configuration in trackerless:
        port = Port(configuration, stated=stated)
        check(
            "the trackerless configuration gets an adapter rather than nothing",
            port.adapter is TRACKERLESS,
        )
        check(
            "against the trackerless configuration every operation is unavailable",
            not any(port.implements(operation) for operation in stated),
        )
        reported = port.report()
        check(
            "and it reports a configuration rather than a broken install",
            len(reported) == len(stated) + 1 and "no tracker" in reported[0],
            f"reported {reported!r}",
        )

    # A configured kind with no implementation installed: the same unavailability,
    # reported as the different fact it is.
    trackerless_line = Port(trackerless[0], stated=stated).report()[0] if trackerless else ""
    for configuration in with_tracker[:1]:
        port = Port(configuration, stated=stated)
        reported = port.report()
        check(
            "a kind whose implementation is not installed reports that, not an absent tracker",
            port.adapter is None
            and port.kind in reported[0]
            and reported[0] != trackerless_line,
            f"reported {reported[:1]!r}",
        )

    # The seam the three adapters register against. The kind is taken from the
    # surface rather than written here, for the same reason the fixtures are
    # taken from the examples directory: nothing in this file names a tracker.
    kinds = _real_tracker_kinds()
    check("the surface states a tracker kind to register against", bool(kinds))
    if kinds:
        kind = kinds[0]
        register(kind, Adapter({"read_item": lambda *a, **k: "read"}))
        registered = _any_example()
        registered.data["tracker"]["kind"] = kind
        port = Port(registered, stated=stated)
        check(
            "a registered implementation answers the capability query for its kind",
            port.adapter is ADAPTERS[kind] and port.invoke("read_item").result == "read",
        )
        check(
            "a second implementation for one kind is refused, naming the kind",
            _refused(lambda: register(kind, Adapter())) == f"tracker.kind.{kind}",
            f"reported {_refused(lambda: register(kind, Adapter()))!r}",
        )
        check(
            "an implementation of an unstated operation is refused at registration",
            _refused(lambda: register(kind + "-x", Adapter({"telepathy": lambda: None})))
            == "tracker.operations.telepathy",
        )
        ADAPTERS.pop(kind)

    # The two sentinels this module spells out, held to the surface so that
    # renaming one there reddens the build instead of silently turning a refusal
    # into the wrong words.
    for sentinel in (PROCEDURE, NEVER):
        check(
            f"the surface still states `{sentinel}` in its `writer` set",
            sentinel in config.facts_for("writer"),
            f"states {config.facts_for('writer')!r}",
        )

    # ⛔ The contract names no tracker, **in either spelling**. This is the
    # mechanical half of "no shared procedure contains a tracker-specific
    # branch": a carrier root is swept for tracker names by the gate in
    # `tools/`, and `scripts/` sits outside that sweep's strict set, so the
    # contract holds itself here -- and to the same grammar, because a slug is
    # the one spelling nobody writes in prose. The planted violation below is
    # what shows it can fail at all.
    with open(os.path.abspath(__file__), encoding="utf-8") as handle:
        source = handle.read()
    check(
        "the contract itself names no tracker the surface declares",
        not names_a_tracker(source, kinds),
        f"names {names_a_tracker(source, kinds)!r}",
    )
    if kinds:
        for spelling in (kinds[0], kinds[0].replace("-", " ").title(), kinds[0].upper()):
            planted = source + f"\n# a branch on {spelling} would go here\n"
            check(
                f"a tracker named as `{spelling}` reddens that check",
                names_a_tracker(planted, kinds) == [kinds[0]],
                f"reported {names_a_tracker(planted, kinds)!r}",
            )

    # This repository's own configuration, for the reason `config.py` holds it
    # too: the one configuration the project actually runs on is otherwise held
    # by nothing.
    own = os.path.join(config.REPO_ROOT, config.CONFIG_PATH)
    if os.path.exists(own):
        # Through `check`, not printed beside it: a configuration this repository
        # cannot load is a red line and a count, the way the reader reports the
        # same file, rather than a traceback where the verdict belongs.
        try:
            port, refused = load(config.REPO_ROOT), None
        except ConfigError as error:
            port, refused = None, str(error)
        check(f"this repository's own {config.CONFIG_PATH} loads", port is not None, refused or "")
        if port is not None:
            check(
                "its port reports every operation unavailable and no fault",
                not any(port.implements(operation) for operation in stated)
                and len(port.report()) == len(stated) + 1,
                f"reported {port.report()!r}",
            )

    if failures:
        print(f"\n{failures} assertion(s) did not hold.")
    return 1 if failures else 0


# --- entry point -----------------------------------------------------------


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="The tracker port: what is available here, and what each absence does.",
    )
    parser.add_argument(
        "--skills-root",
        default=".",
        help="the root the configuration is resolved relative to; defaults to the "
        "working directory, which is where a role invoked inside a project finds it",
    )
    parser.add_argument(
        "--no-check-paths",
        action="store_true",
        help="resolve without testing that the configured code root exists",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="hold the contract to the surface and the examples",
    )
    args = parser.parse_args(argv)

    if args.self_test:
        print("Holding the port contract to the surface and the examples:")
        return self_test()

    try:
        port = load(args.skills_root, check_paths=not args.no_check_paths)
    except ConfigError as error:
        print(str(error), file=sys.stderr)
        return 1
    print(json.dumps(port.to_dict(), indent=2, ensure_ascii=False, sort_keys=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
