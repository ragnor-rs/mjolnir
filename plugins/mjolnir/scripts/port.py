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
    fallback taken. Two things do raise, each with the key named, the way
    `config.py` refuses a configuration the surface does not allow: the
    toolkit's own mistake -- an operation the surface does not state, asked for
    by name or implemented by an adapter -- and a configuration this contract
    cannot act on, which today is one status role mapped to two status words.
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

# The writer the procedure may act as (§ 4.2). A sentinel rather than a value:
# which member of the `writer` set means "the procedure itself" is not something
# the alternation says, so it is spelled here and held to the surface by the
# self-test -- the discipline `config.py` already applies to its own two.
PROCEDURE = "procedure"


def _tables(text: str) -> list[list[list[str]]]:
    """Every markdown table in document order, as rows of stripped cells."""
    tables: list[list[list[str]]] = []
    current: list[list[str]] = []
    fenced = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if not fenced and line.lstrip().startswith("|"):
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if not all(set(cell) <= set("-: ") for cell in cells):
                current.append(cells)
            continue
        if current:
            tables.append(current)
            current = []
    if current:
        tables.append(current)
    return tables


def operations(surface_text: str) -> dict[str, str]:
    """`operation -> what the procedure does when its capability is absent`.

    Read from § 3's table. An operation with an empty absent case is refused
    rather than defaulted: a fallback nobody wrote is the absence this contract
    exists to remove, and defaulting one here would put the text in this file.
    """
    found: dict[str, str] = {}
    for table in _tables(surface_text):
        header = table[0]
        if header[0] != OPERATION_COLUMN or header[-1] != ABSENT_COLUMN:
            continue
        for cells in table[1:]:
            match = OPERATION_NAME.match(cells[0])
            if not match:
                continue
            name = match.group("name")
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
            f"states no `{OPERATION_COLUMN}` / `{ABSENT_COLUMN}` table, so the "
            "port has no operation list to hold an adapter to. Either the "
            "surface changed shape or the table's headers were reworded.",
        )
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

        Three answers are reports rather than exceptions: no status here maps
        the role, which is a legitimate configuration (§ 4.2); the status exists
        and its configured writer is somebody else, which is a refusal naming
        that writer; or the move goes through `set_state` and its capability
        decides. The fourth is a configuration this contract cannot act on --
        one role mapped to two status words -- and that is refused with the key
        named, the way the reader refuses one the surface does not allow.
        """
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
            # answered by two status words has no answer. The reader does not
            # refuse this, so the port does.
            words = ", ".join(f"`{status.get('name')}`" for status in statuses)
            raise ConfigError(
                "statuses",
                f"maps the `{role}` role to more than one status ({words}). The "
                "procedure asks to advance to a role, so a role with two status "
                "words leaves the move undefined -- there is no first-match rule "
                "here to fall back on.",
            )

        status = statuses[0]
        writer = status.get("writer")
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
        if not self.config.has_tracker:
            out.append(
                "The configuration states no tracker, so the port implements "
                "nothing and every operation below takes its stated fallback. "
                "The reader reports that as a configuration; it is not a broken "
                "install."
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
        return {
            "kind": self.kind,
            "implementation_installed": self.adapter is not None,
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

    stated = surface_operations()
    check("the surface states the operation list this contract holds", bool(stated))
    check(
        "every stated operation carries an absent case",
        all(stated.values()),
        f"read {stated!r}",
    )

    # A surface with the table reworded away, and one with a fallback cell left
    # empty: the two ways the contract can stop being stated anywhere.
    with open(config.SURFACE, encoding="utf-8") as handle:
        surface_text = handle.read()
    without_table = surface_text.replace(f"| {OPERATION_COLUMN} |", "| Thing |", 1)
    check(
        "a surface stating no operation table is refused, naming the surface",
        _refused(lambda: operations(without_table))
        == os.path.relpath(config.SURFACE, config.PLUGIN_ROOT),
        f"reported {_refused(lambda: operations(without_table))!r}",
    )
    first = sorted(stated)[0]
    blanked = re.sub(
        r"^\| `" + first + r"` \|(?P<asks>[^|]*)\|[^|]*\|$",
        lambda m: f"| `{first}` |{m.group('asks')}|  |",
        surface_text,
        count=1,
        flags=re.M,
    )
    check(
        "an operation stated with no absent case is refused, naming it",
        _refused(lambda: operations(blanked)) == f"tracker.operations.{first}",
        f"reported {_refused(lambda: operations(blanked))!r}",
    )
    row = re.search(r"^\| `" + first + r"` \|.*\|$", surface_text, re.M).group(0)
    twice_stated = surface_text.replace(row, row + "\n" + row, 1)
    check(
        "an operation stated twice is refused, naming it",
        _refused(lambda: operations(twice_stated)) == f"tracker.operations.{first}",
        f"reported {_refused(lambda: operations(twice_stated))!r}",
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
    uninstalled = Port(
        [c for c in _loaded().values() if c.has_tracker][0], stated=stated
    )
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
    # asks for a role and is told whose state it is.
    for writer in [w for w in config.facts_for("writer") if w != PROCEDURE]:
        configuration = _with_statuses(
            [{"name": "a status", "role": "code_landed", "writer": writer}]
        )
        outcome = Port(configuration, adapter=Adapter(), stated=stated).advance_to("code_landed")
        check(
            f"an advance to a status written by `{writer}` is refused, naming the writer",
            outcome.refused and outcome.writer == writer and writer in outcome.detail,
            f"got {str(outcome)!r}",
        )

    through = Port(
        _with_statuses([{"name": "a status", "role": "in_flight", "writer": PROCEDURE}]),
        adapter=Adapter({"set_state": lambda *a, **k: "moved"}),
        stated=stated,
    )
    advanced = through.advance_to("in_flight")
    check(
        "an advance the procedure may write goes through the capability",
        advanced.performed and advanced.result == "moved" and not advanced.refused,
        f"got {str(advanced)!r}",
    )
    twice = _with_statuses(
        [
            {"name": "one word", "role": "in_flight", "writer": PROCEDURE},
            {"name": "another", "role": "in_flight", "writer": PROCEDURE},
        ]
    )
    ambiguous = _refused(
        lambda: Port(twice, adapter=Adapter(), stated=stated).advance_to("in_flight")
    )
    check(
        "a role mapped to two status words is refused, naming the key",
        ambiguous == "statuses",
        f"reported {ambiguous!r}",
    )
    unmapped = Port(_with_statuses([]), adapter=Adapter(), stated=stated).advance_to("deployed")
    check(
        "an advance to a role no status maps is reported, not refused and not raised",
        not unmapped.performed and not unmapped.refused and "deployed" in unmapped.detail,
        f"got {str(unmapped)!r}",
    )

    # The trackerless configuration, which is this contract's own acceptance
    # item: every operation unavailable, and nothing reading as a fault.
    trackerless = [c for c in _loaded().values() if not c.has_tracker]
    check("the trackerless example loads", bool(trackerless))
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
    with_tracker = [c for c in _loaded().values() if c.has_tracker]
    check("an example configures a tracker", bool(with_tracker))
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
    kind = _real_tracker_kinds()[0]
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

    # The sentinel this module spells out, held to the surface so that renaming
    # it there reddens the build instead of silently turning the refusal off.
    check(
        f"the surface still states `{PROCEDURE}` in its `writer` set",
        PROCEDURE in config.facts_for("writer"),
        f"states {config.facts_for('writer')!r}",
    )

    # ⛔ The contract names no tracker. This is the mechanical half of "no shared
    # procedure contains a tracker-specific branch": a carrier root is swept for
    # tracker names by the gate in `tools/`, and `scripts/` is deliberately
    # outside that sweep's strict set, so the contract holds itself here.
    with open(os.path.abspath(__file__), encoding="utf-8") as handle:
        source = handle.read()
    named = [kind for kind in _real_tracker_kinds() if kind in source]
    check(
        "the contract itself names no tracker the surface declares",
        not named,
        f"names {named!r}",
    )
    check(
        "the tracker names that check reads are derived from the surface",
        bool(_real_tracker_kinds()),
    )

    # This repository's own configuration, for the reason `config.py` holds it
    # too: the one configuration the project actually runs on is otherwise held
    # by nothing.
    own = os.path.join(config.REPO_ROOT, config.CONFIG_PATH)
    if os.path.exists(own):
        port = load(config.REPO_ROOT)
        print(f"  ok    this repository's own {config.CONFIG_PATH} loads")
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
