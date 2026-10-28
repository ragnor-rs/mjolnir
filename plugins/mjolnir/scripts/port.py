#!/usr/bin/env python3
"""The ports: one contract, and what happens where an operation is absent.

The shared procedure names **the port and never the thing behind it**. This
module is every port the surface declares: it reads the operation list and the
absent case out of the surface beside it -- `../config/schema.md`, each port
from the section its own marker sits in -- answers whether a given operation is
available here, and resolves the one that is not into the fallback the surface
states for it. ⛔ **Which sections those are is not written here.** Naming them
would be the list of ports the first bullet below says this module does not
carry, and the receipt is that it drifted: a sibling change renumbered a section
while this one was open, and every copy of the number had to be walked by hand. One implementation per kind is **discovered** -- a
module in that port's own package beside this one, naming the kind it answers
for -- so the contract itself knows none of them by name and nothing has to
remember an import.

⛔ **Which port is a parameter and never a branch.** § 26 states the marker that
declares one, and the three facts it carries: the key a project writes the kind
on, the section the operation list is read from, and the directory the
implementations live in. A second copy of this machine per port would be a second
place a fallback could be defaulted, which is exactly what the first bullet below
exists to prevent.

Three things it deliberately does not do:

  * **It carries no operation list and no fallback text of its own, and no list
    of ports.** All three are read at run time off the surface, so an operation
    added there is accepted here without this module changing, a fallback
    reworded there is reworded everywhere, and a port declared there is resolved
    here. The self-test holds this file to naming no tracker the surface
    declares, so a branch on one reddens the build rather than being noticed in
    review.
  * **It never raises on an absence, and never on the host being unreachable.**
    A capability that is missing, a role no status maps, a configuration with no
    tracker at all and a tracker whose adapter has not been built yet are four
    different outcomes and none of them is an error. Every one of them comes
    back as an `Outcome` naming the fallback taken. A **fifth** outcome is the
    host refusing to answer -- a timeout, a credential, a repository that is not
    there -- which is neither an absence nor the toolkit's mistake: it comes
    back as an `Outcome` too, with `failed` set so a role cannot read a broken
    call as a missing feature. An implementation reports it by raising
    `HostUnavailable`, which is declared here rather than per tracker.

    What raises -- always with the key named, the way `config.py` refuses a
    configuration the surface does not allow -- is a statement that is
    **missing or ambiguous rather than absent**: a port's section stating no
    operation table, two tables stating one under it, an operation table under a
    section no port declares, a port asked for that no marker declares, an
    operation stated twice or in a row with a cell missing, an operation whose
    absent case is blank, an operation asked for or implemented that the surface
    does not state for that port, two adapters for one kind, a module in a port's
    package naming no kind or failing to import, a status word the configuration
    maps that its tracker cannot hold, and a role mapped to two status words.
    None of those is a tracker or a store that cannot do something; each is a
    text that does not say what the procedure is supposed to do.
  * **It does not decide what a role then does.** The port reports which
    fallback was taken; whether that stops the role is the role's business, the
    way `config.py` reports what a configuration cannot support without acting
    on it.

**A capability is the adapter's fact, not the project's** (§ 3). Nothing on the
surface lets a project claim an operation its tracker cannot do, so nothing here
reads one: the query goes to the implementation, which declares an operation by
implementing it.

Usage:
    port.py [--skills-root DIR]   print the tracker port's state here as JSON
    port.py --port <kind key>     print that port's state instead -- the key the
                                  kind is written on, which is its name
    port.py --ports               print every port the surface declares
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
# Grammar only, per the rule above: a table is found by its column headers rather
# than by a section number, so renumbering a section changes nothing. The first
# and last headers are the two cells this module reads -- the operation and its
# absent case -- and the column between them is for the person reading the
# section.

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

# The kind that addresses nothing, shared by every port: § 3's trackerless
# configuration and § 26's project with no destination are the same statement one
# port apart, and both get the adapter that implements nothing. Spelled out for
# the reason the two writers above are, and held to **every** port's own kind set
# by the self-test -- a port whose alternation lost the word would otherwise have
# this module resolve `none` as a kind somebody forgot to build.
NONE = "none"

# The port `load()` answers for with no argument. ⛔ The default and not a second
# statement of what ports exist: the surface's markers are the statement, and the
# self-test holds this name to being one of them. Every role but § 9's asks for
# this one, which is the whole of why it is the default -- and § 26's is asked for
# by name, on the invocation, rather than by a second constant here.
TRACKER = "tracker.kind"

# What a port's name is the kind of. ⛔ Stripped from the name rather than stated
# per port: the refusals below are keyed on the configuration block a person would
# edit -- `tracker.operations.read_item` -- and a port whose prefix were written
# out separately would be a second spelling of the path its own marker sits on.
KIND_SUFFIX = ".kind"

# The three answers `to_dict` gives about an adapter, and the only three. ⛔ Named
# here rather than written at the one place they are produced, because they are a
# **wire format**: a consumer outside this file matches on the word, so renaming
# one is a change to somebody else's lookup table. ⚠️ Measured on this change --
# `trackerless` became `unconfigured` and the readiness script's own three-way
# lookup, eleven lines from an edit in the same commit, raised `KeyError` for
# every configuration with no tracker. The self-test below holds `to_dict` to
# producing each of these, which is the assertion whose absence let that land.
STATE_REGISTERED = "registered"
STATE_UNCONFIGURED = "unconfigured"
STATE_ABSENT = "absent"
ADAPTER_STATES = (STATE_REGISTERED, STATE_UNCONFIGURED, STATE_ABSENT)


class HostUnavailable(Exception):
    """The tracker did not answer.

    ⛔ **Declared by the contract, not by an implementation**, so a role can tell
    a broken call from a missing capability without knowing which tracker it is
    talking to. An implementation raises this and `Port.invoke` turns it into an
    `Outcome` with `failed` set; that is the one exception the port converts
    rather than letting through, because the alternative is the traceback this
    module exists to keep away from a role.

    ⚠️ It is **not** an absence. An absence is a stated decision with a stated
    fallback; this is the network, the credential or the repository being wrong,
    and a role that retried the fallback here would be answering a question
    nobody could ask. The message names the command, so the failure is
    reproducible by hand.
    """

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


# ⛔ Level two exactly, and not any heading from level two down. A port's `kind`
# fence sits in its section's own prose, above every subsection, so the reader
# beside this file reports the `##` title as that marker's section -- while the
# operation table sits under a `###` of its own. Tracking the nearest heading of
# any depth made those two different strings, and the contract then read the
# marker's section as one carrying no table at all. The section a port owns is the
# `##` one, and both halves resolve to it.
SECTION_HEADING = re.compile(r"^##\s+(?P<title>.+?)\s*$")


def _tables(text: str) -> list[tuple[str, list[list[str]]]]:
    """Every markdown table in document order, with the heading it sits under.

    Fenced blocks are skipped by a line toggle rather than a paired regex, for
    the reason the sweep in `tools/` records: one trailing space after a fence's
    language tag makes a paired regex pair the wrong fences. ⚠️ A fence also
    **ends** the table above it -- it used to merely be skipped, which glued an
    unrelated table's rows onto the one before it and read them as operations.

    ⛔ The heading travels with the table because § 26 makes the section a
    **parameter** of this contract rather than a fact baked into it: two ports
    state two tables with the same columns, and a lookup by columns alone has one
    answer for both. ⚠️ Headings inside a fence are not headings -- a `markdown`
    example carrying a `##` line would otherwise move every table after it into a
    section the document does not have, which is the mistake `config.py`'s own
    fence walk records paying for.
    """
    tables: list[tuple[str, list[list[str]]]] = []
    current: list[list[str]] = []
    heading = ""

    def flush() -> None:
        nonlocal current
        if current:
            tables.append((heading, current))
            current = []

    fenced = False
    for line in text.splitlines():
        if line.lstrip().startswith(("```", "~~~")):
            fenced = not fenced
            flush()
            continue
        if fenced:
            continue
        if line.lstrip().startswith("|"):
            cells = _row(line)
            if not all(set(cell) <= set("-: ") for cell in cells):
                current.append(cells)
            continue
        flush()
        titled = SECTION_HEADING.match(line)
        if titled:
            heading = titled.group("title").strip()
    flush()
    return tables


def section_body(surface_text: str, section: str) -> str:
    """The text of one `##` section, its heading line included.

    ⛔ Not part of reading the contract -- the suite below plants with it, and a
    plant that edited the whole document would hit whichever section stated the
    thing first. Measured: a plant on the operation column's name unmade the
    *other* port's table, asserted nothing about the port under test, and read
    green.
    """
    lines = surface_text.splitlines(keepends=True)
    start, fenced = None, False
    for index, line in enumerate(lines):
        if line.lstrip().startswith(("```", "~~~")):
            fenced = not fenced
            continue
        if fenced:
            continue
        titled = SECTION_HEADING.match(line.rstrip("\n"))
        if not titled:
            continue
        if start is None:
            if titled.group("title").strip() == section:
                start = index
            continue
        return "".join(lines[start:index])
    return "".join(lines[start:]) if start is not None else ""


def _is_operation_table(header: list[str]) -> bool:
    return header[0] == OPERATION_COLUMN and header[-1] == ABSENT_COLUMN


def operation_sections(surface_text: str) -> list[str]:
    """Every heading under which an operation table sits, in document order.

    What `surface_ports` holds the declared ports against: a table carrying these
    columns under a section no marker names is an operation list no port reads,
    which is the half of § 26's *one table per port, one port per table* that the
    per-port lookup below cannot see.
    """
    return [
        heading
        for heading, table in _tables(surface_text)
        if _is_operation_table(table[0])
    ]


def operations(surface_text: str, section: str, prefix: str) -> dict[str, str]:
    """`operation -> what the procedure does when its capability is absent`.

    Read from the operation table under `section`, which is where that port's
    marker puts it (§ 26). Four shapes are refused rather than read past, each
    naming what it refuses on, because every one of them silently changes the
    list or a fallback: a second table with these headers under the same section
    (the list is stated once per port), an operation stated twice, a row with a
    cell missing or added, and an operation whose absent case is blank. A
    fallback nobody wrote is the absence this contract exists to remove, and
    defaulting one here would move the text into this file.

    `prefix` is the configuration block the refusals are keyed on, so a person
    reading one is sent to the keys they would edit rather than to another port's.
    """
    found: dict[str, str] = {}
    matching = 0
    for heading, table in _tables(surface_text):
        if heading != section or not _is_operation_table(table[0]):
            continue
        header = table[0]
        matching += 1
        if matching > 1:
            raise ConfigError(
                os.path.relpath(config.SURFACE, config.PLUGIN_ROOT),
                f"states more than one `{OPERATION_COLUMN}` / `{ABSENT_COLUMN}` "
                f"table under § {section}, so the `{prefix}` port's operation list "
                "is stated more than once and the tables may disagree. One table "
                "per port.",
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
                    f"{prefix}.operations.{name}",
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
                    f"{prefix}.operations.{name}",
                    "is stated twice, so it has two absent cases and the second "
                    "would silently win. One row per operation.",
                )
            if not fallback:
                raise ConfigError(
                    f"{prefix}.operations.{name}",
                    "is stated with no absent case. Every operation states what "
                    "the procedure does when its capability is missing -- that "
                    "table column is the fallback, and nothing here supplies one.",
                )
            found[name] = fallback

    if not found:
        raise ConfigError(
            os.path.relpath(config.SURFACE, config.PLUGIN_ROOT),
            f"states no `{OPERATION_COLUMN}` / `{ABSENT_COLUMN}` table whose rows "
            f"name an operation under § {section}, so the `{prefix}` port has no "
            "operation list to hold an adapter to. Either the surface changed "
            "shape, the table's headers were reworded, or its `# port:` marker "
            "sits under a different section from its table.",
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


class PortSpec:
    """One port, as the surface declares it.

    Three facts and no fourth, every one of them off the `# port:` marker § 26
    states: the configuration key carrying the kind -- which **is** the port's
    name -- the section its operation list is read from, and the directory its
    implementations live in. ⛔ Nothing here is written in this module. A list of
    ports in the contract would be the shape § 3 already forbids for capabilities:
    a second statement allowed to disagree with the one that is read.
    """

    def __init__(self, name: str, section: str, package: str):
        self.name = name
        self.section = section
        self.package = package

    @property
    def prefix(self) -> str:
        """The configuration block this port's refusals are keyed on."""
        return self.name[: -len(KIND_SUFFIX)]

    @property
    def directory(self) -> str:
        """Where this port's implementations sit, beside this file."""
        return os.path.join(SCRIPTS_DIR, self.package)

    def operations(self) -> dict[str, str]:
        with open(config.SURFACE, encoding="utf-8") as handle:
            return operations(handle.read(), self.section, self.prefix)

    def __repr__(self) -> str:  # pragma: no cover -- a failure message's shape
        return f"PortSpec({self.name!r}, {self.section!r}, {self.package!r})"


def surface_ports(surface_text: str | None = None) -> dict[str, PortSpec]:
    """`the kind's path -> its PortSpec`, for every port the surface declares.

    ⛔ Held both ways, here rather than at the first query: a port whose kind is
    marked and whose section carries no operation table is refused when its list
    is asked for, and a table carrying the operation columns under a section no
    marker names is refused **here** -- the per-port lookup cannot see it, and an
    operation list no port reads is a list this contract would silently not hold
    an adapter to.
    """
    if surface_text is None:
        with open(config.SURFACE, encoding="utf-8") as handle:
            surface_text = handle.read()
    declared = config.surface_facts(surface_text)["ports"]
    specs = {
        name: PortSpec(name, section, package)
        for name, (section, package) in declared.items()
    }
    # ⛔ And the other direction of § 26's *one port per table*, which the orphan
    # check below cannot see: two markers naming one **section** are two ports
    # reading one operation list, and two naming one **package** are two ports
    # over one registry -- where the second port resolves an implementation
    # registered for the first and never held to its own closed list, so every
    # operation answers from an adapter built for somebody else. Both were
    # reachable by editing the surface and neither was refused, measured.
    for facet, taken in (("section", "section"), ("directory", "package")):
        seen: dict[str, str] = {}
        for name in sorted(specs):
            value = getattr(specs[name], taken)
            if value in seen:
                raise ConfigError(
                    os.path.relpath(config.SURFACE, config.PLUGIN_ROOT),
                    f"declares `{seen[value]}` and `{name}` with one {facet}, "
                    f"{value!r}. The surface states one table per port and one "
                    "port per table: two ports sharing a section read one list, "
                    "and two sharing a directory resolve one registry -- so an "
                    "implementation built for one answers for the other, held to "
                    "a list it was never checked against.",
                )
            seen[value] = name
    sections = {spec.section for spec in specs.values()}
    for heading in operation_sections(surface_text):
        if heading not in sections:
            raise ConfigError(
                os.path.relpath(config.SURFACE, config.PLUGIN_ROOT),
                f"states an `{OPERATION_COLUMN}` / `{ABSENT_COLUMN}` table under "
                f"§ {heading}, which no `# port:` marker names. That is an "
                "operation list no port reads and no adapter is held to -- the "
                "surface states one table per port and one port per table.",
            )
    return specs


def port_spec(name: str = TRACKER) -> PortSpec:
    """The one port named, refused where the surface declares no such port."""
    specs = surface_ports()
    try:
        return specs[name]
    except KeyError:
        raise ConfigError(
            name,
            "is not a port the surface declares. A port is declared by a "
            "`# port:` marker on its `kind` line, and the surface declares "
            f"{', '.join('`' + key + '`' for key in sorted(specs))}.",
        ) from None


def surface_operations(name: str = TRACKER) -> dict[str, str]:
    return port_spec(name).operations()


# --- the contract ----------------------------------------------------------


class Adapter:
    """One tracker behind the port.

    An adapter is a mapping from an operation's name to the callable that
    performs it, and that mapping **is** the capability declaration (§ 3): there
    is no second list to disagree with it. An operation the surface does not
    state is refused at registration, so an adapter cannot grow a private
    operation that no role could portably call.
    """

    def __init__(self, operations: dict[str, object] | None = None, *, binder=None):
        self.operations = dict(operations or {})
        self._binder = binder

    def implements(self, operation: str) -> bool:
        return operation in self.operations

    def bind(self, configuration) -> None:
        """Hand the implementation the configuration it is answering for.

        ⛔ Called by `Port.invoke` before every operation, so an implementation
        never resolves a project for itself. Which project a write lands on is
        the configuration's to say and the port's to pass; an implementation that
        read it from the working directory would address the wrong repository
        wherever a role is not standing in the project it is acting on -- and
        would have done something plausible first.

        An implementation with no `binder` needs nothing, which is every double
        in the suite and the trackerless adapter.
        """
        if self._binder is not None:
            self._binder(configuration)

    def hold_to(self, stated: dict[str, str], prefix: str) -> None:
        for name in sorted(self.operations):
            if name not in stated:
                raise ConfigError(
                    f"{prefix}.operations.{name}",
                    "is implemented by an adapter and is not an operation the "
                    "surface states. The operation list is closed: an "
                    "implementation's own extra is either one of the stated "
                    "operations or a shape the surface has to grow first.",
                )


# The adapter for the kind that addresses nothing (§ 3's trackerless
# configuration, § 26's project with no destination): it implements nothing, so
# every operation takes its stated fallback. It is an adapter rather than a branch
# in the procedure -- which is the whole of why a `kind` of `none` reports as a
# configuration and never as a broken install. ⛔ One object for every port, there
# being nothing per-port about implementing nothing.
UNCONFIGURED = Adapter()

# Where this module sits, and so where every port's package sits: a port's own
# directory is the `# port:` marker's value joined onto this. ⛔ No directory is
# named here. Naming one would be the second statement of a fact the surface
# already carries, and naming the modules inside it would name the trackers --
# which this file is held to not doing.
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))

# Installed implementations, by package and then by `kind`, populated by
# discovery -- § 3 states why there is no written list and this file does not
# restate it. ⛔ Not read directly: a role asks a `Port`, and anything needing the
# set itself calls `load_adapters()`, since reading this before a sweep has run
# reports every kind as unbuilt. One report did exactly that. ⚠️ Keyed by
# **package** and not by port name: the package is what a sweep reads, and two
# ports resolving one directory would be two registries over one set of modules.
ADAPTERS: dict[str, dict[str, Adapter]] = {}

# Discovery runs once per package, and a package is marked done **after** a sweep
# that finished. ⚠️ Setting it first was a measured defect: a module that raised
# left discovery marked done over a half-filled registry, so every later query
# returned early and a kind that *was* built reported as one that never was --
# the single distinction § 3 asks this module to keep. A failure is remembered
# instead and re-raised on every call, because a broken implementation does not
# become an absence by being asked twice.
#
# ⛔ Both are per package rather than per process. A broken module behind one port
# must not make the other port's implementations read as absent, which is what one
# shared flag would do -- the two ports are swept independently and a failure
# belongs to the one whose directory holds it.
_discovered: set[str] = set()
_discovery_failed: dict[str, ConfigError] = {}


def installed(spec: PortSpec) -> dict[str, Adapter]:
    """This port's registry, created empty on first touch."""
    return ADAPTERS.setdefault(spec.package, {})


def register(spec: PortSpec, kind: str, adapter: Adapter) -> None:
    """Install an implementation for one kind of one port."""
    registry = installed(spec)
    if kind in registry:
        raise ConfigError(
            f"{spec.prefix}.kind.{kind}",
            "already has an implementation registered. Two adapters for one "
            "kind means a role's capability query has two answers.",
        )
    adapter.hold_to(spec.operations(), spec.prefix)
    registry[kind] = adapter


def load_adapters(spec: PortSpec | None = None) -> dict[str, Adapter]:
    """Import every implementation in one port's package and install it.

    **The module's presence is the install**, per § 3 -- which also states why no
    list of them is written anywhere, so this does not restate it. Which directory
    is swept is the port's `# port:` marker (§ 26) and never an argument a caller
    composes.

    ⚠️ Imported here rather than at module scope: an adapter imports this module
    for `Adapter`, so an eager import would be a cycle. Deferring it to the first
    capability query is what breaks that, and is the whole reason this is a
    function rather than a constant.

    An adapter that fails to import is **not** silently skipped, and not on the
    second ask either. A module that is present and broken is the toolkit's own
    mistake -- the one thing § 3 holds apart from an absence -- and swallowing it
    would report a kind that was built as a kind that never was. The refusal is
    remembered and re-raised, with the module named in both cases: failing to
    import and naming no kind are the same class of mistake, and neither is an
    implementation that cannot do something.

    Re-entrant: a sweep that runs again installs the same module objects, which
    is not two adapters for one kind. A *different* adapter for a kind already
    installed is still refused by `register`.
    """
    if spec is None:
        spec = port_spec()
    failed = _discovery_failed.get(spec.package)
    if failed is not None:
        raise failed
    registry = installed(spec)
    if spec.package in _discovered:
        return dict(registry)
    directory = spec.directory
    if not os.path.isdir(directory):
        # ⚠️ Not a fault **of the contract**. A declared port whose directory is
        # not there yet has every kind unbuilt, which is the state § 3 already
        # holds apart from a project that configured none -- and the report below
        # says which. ⛔ That is a statement about this function and not about
        # whether the toolkit may ship such a port: the suite below and the
        # adapter-suite runner each hold every declared port to having an
        # implementation installed, because a port on this surface with nothing
        # behind it is a hole in the toolkit rather than a configuration. The two
        # readings are not in tension -- one is what a role is handed at run time,
        # the other is what a gate requires of this repository.
        _discovered.add(spec.package)
        return dict(registry)
    import importlib

    # ⛔ Appended, not prepended, and the package's parent rather than the
    # package: a sweep pointed at a temporary directory used to leave the shared
    # temp root ahead of the standard library for the rest of the process.
    parent = os.path.dirname(directory)
    if parent not in sys.path:
        sys.path.append(parent)
    for entry in sorted(os.listdir(directory)):
        if not entry.endswith(".py") or entry.startswith("_"):
            continue
        try:
            module = importlib.import_module(f"{spec.package}.{entry[:-3]}")
            kind, adapter = module.KIND, module.ADAPTER
        except ConfigError:
            raise
        except Exception as error:
            # The import itself, or a module that states neither name. Both come
            # back keyed on the module, because a raw traceback out of here is
            # the thing this file refuses to hand a role.
            refusal = ConfigError(
                f"{spec.prefix}.implementations.{entry}",
                f"is in the `{spec.package}` package and could not be installed "
                f"({type(error).__name__}: {error}). An implementation states a "
                "`KIND` and an `ADAPTER` and imports cleanly; a module that is "
                "present and broken is a built implementation nothing can "
                "address, which is this toolkit's own mistake and never an "
                "implementation that cannot do something.",
            )
            _discovery_failed[spec.package] = refusal
            raise refusal from None
        if registry.get(kind) is not adapter:
            register(spec, kind, adapter)
    _discovered.add(spec.package)
    return dict(registry)


class Outcome:
    """What the port did about one operation, or did not do and why.

    Returned for every outcome that is not the toolkit's own mistake: performed,
    fallen back, refused by a status's writer, or **failed at the host**. A role
    reads `performed` and, where that is false, says `detail` out loud -- which
    is how an absence reaches a person as a stated decision rather than as a
    traceback.

    ⛔ `failed` is read apart from the other three. A fallback says *this tracker
    cannot do that, here is what happens instead*; `failed` says *it can, and the
    call did not go through*. A role that retried the fallback on a failure would
    be acting on a decision nobody made, so the two never share a branch.
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
        failed: bool = False,
    ):
        self.operation = operation
        self.performed = performed
        self.detail = detail
        self.result = result
        self.refused = refused
        self.writer = writer
        self.failed = failed

    def __bool__(self) -> bool:
        return self.performed

    def __str__(self) -> str:
        return f"{self.operation}: {self.detail}"


class Port:
    """One of the surface's ports, over one project's configuration.

    ⛔ Which port is a `PortSpec` read off the surface and never a branch here:
    the contract is one machine, and § 26 makes the section, the kind's key and
    the implementation directory its parameters.
    """

    def __init__(
        self,
        configuration: config.Config,
        spec: PortSpec | None = None,
        *,
        adapter: Adapter | None = None,
        stated: dict[str, str] | None = None,
        installed: dict[str, Adapter] | None = None,
    ):
        self.config = configuration
        self.spec = spec if spec is not None else port_spec()
        self.stated = stated if stated is not None else self.spec.operations()
        # An adapter handed in directly -- by a role under test, or by a project
        # carrying its own -- is held to the surface exactly as a registered one
        # is. Skipping that here would leave `register` the only guarded route.
        if adapter is not None:
            adapter.hold_to(self.stated, self.spec.prefix)
        self._given = adapter
        # ⛔ The registry this port resolves against, defaulting to the installed
        # one. A seam rather than a convenience: § 3 requires *configured kind
        # with no implementation* to read apart from *no store configured*
        # permanently, and that property was only provable while some real kind
        # happened to be unbuilt -- so it would have stopped being testable
        # exactly when the toolkit was finished. `installed={}` states the
        # condition directly.
        self._installed = installed

    @property
    def name(self) -> str:
        """The configuration key carrying this port's kind, which is its name."""
        return self.spec.name

    @property
    def kind(self) -> str:
        return self.config.get(self.name)

    @property
    def configured(self) -> bool:
        """Whether this port addresses anything at all.

        ⛔ An unstated kind counts as unconfigured and never as a kind named
        `None`: § 26 defaults its own kind and § 3 marks its own required, so a
        port reaching here with neither is a surface this contract cannot resolve
        rather than a store to go looking for.
        """
        return self.kind not in (None, NONE)

    @property
    def adapter(self) -> Adapter | None:
        """The implementation answering here, or `None` where none is installed.

        A kind of `none` gets the adapter that implements nothing -- a stated
        decision. A configured kind with nothing registered gets `None`, which is
        an adapter that has not been built yet. Both leave every operation
        unavailable and they are **not** the same fact, so they are reported
        apart (§ 3).

        Discovery happens here, on the first ask, and only where a store is
        actually configured: a project that configured none has no reason to
        import an implementation, and an adapter handed in directly is the caller
        saying which one answers.
        """
        if self._given is not None:
            return self._given
        if not self.configured:
            return UNCONFIGURED
        if self._installed is not None:
            return self._installed.get(self.kind)
        return load_adapters(self.spec).get(self.kind)

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
                f"{self.spec.prefix}.operations.{operation}",
                "is not an operation the surface states for this port. The list "
                f"is closed and holds: {', '.join(sorted(self.stated))}.",
            ) from None

    def invoke(self, operation: str, *args, **kwargs) -> Outcome:
        """Perform an operation, or come back with the fallback stated for it.

        Three answers, never a traceback: the fallback where the capability is
        absent, the result where it is present, and a `failed` outcome naming the
        host's own words where the call did not go through.
        """
        fallback = self._stated(operation)
        adapter = self.adapter
        if adapter is None or not adapter.implements(operation):
            return Outcome(operation, performed=False, detail=fallback)
        # ⛔ The configuration goes to the implementation here, every time, and
        # the implementation keeps none of its own. An adapter that resolved the
        # project itself would read it from the working directory -- which § 2
        # forbids for exactly this reason -- and a `Port` built over one project
        # would then address whichever project the process happened to stand in.
        adapter.bind(self.config)
        try:
            result = adapter.operations[operation](*args, **kwargs)
        except HostUnavailable as error:
            return Outcome(
                operation,
                performed=False,
                failed=True,
                detail=f"The `{self.kind}` host did not answer, so `{operation}` "
                f"did not happen: {error}. This is the capability working and "
                "the call failing, which is not the absence below it -- the "
                "stated fallback answers a tracker that cannot, not one that "
                "did not.",
            )
        return Outcome(
            operation,
            performed=True,
            detail=f"performed by the `{self.kind}` implementation of the port.",
            result=result,
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
        # ⛔ The resolved status word is handed to the adapter, which is the
        # whole point of asking for a role: the caller names a **role**, this
        # layer turns it into the one status word the project mapped to it, and
        # the implementation writes that word.
        #
        # ⚠️ Measured by building the first adapter against this method: the
        # word used to be resolved here for the writer checks and then dropped,
        # so `set_state` reached the adapter with no target. The only ways out
        # were an adapter re-deriving the mapping the port had just read, or a
        # role passing the status word itself -- and that second one is exactly
        # what § 3 forbids. An absent capability stayed correct throughout,
        # which is why nothing before an implementation existed could catch it.
        return self.invoke("set_state", *args, status=status.get("name"), **kwargs)

    # -- what this configuration cannot do, as a report and never as a fault

    def report(self) -> list[str]:
        out = []
        if self.adapter is UNCONFIGURED:
            # What the absence *means* per operation, and not a second statement
            # that the absence exists: the reader already reports that, and two
            # hand-written sentences for one fact is the defect, not the report.
            # ⛔ What the configuration *says* and not what it resolved to. The
            # same adapter answers for a kind written `none` and for a kind the
            # configuration never states, and a report that said `none` either way
            # would be telling somebody their file carries a word it does not --
            # sending them to read a key that is not there.
            out.append(
                (
                    f"The configuration states `{self.name}: {NONE}`"
                    if self.kind == NONE
                    else f"The configuration states no `{self.name}`"
                )
                + ", so the port implements nothing and every operation below "
                "takes its stated fallback."
            )
        elif self.adapter is None:
            out.append(
                f"No implementation of the port is installed for "
                f"`{self.name}: {self.kind}`, so every operation below takes "
                "its stated fallback. That is an adapter not built yet rather "
                "than a project that configured none, and the two read apart "
                "here for exactly that reason."
            )
        for operation in sorted(self.stated):
            if not self.implements(operation):
                out.append(f"`{operation}` is unavailable: {self.fallback(operation)}")
        return out

    def to_dict(self) -> dict:
        # Three states, not a boolean: `installed: true` read as an adapter for
        # this kind where the answer was the one that implements nothing, which is
        # the distinction § 3 asks the port to keep.
        adapter = (
            STATE_UNCONFIGURED
            if self.adapter is UNCONFIGURED
            else STATE_ABSENT
            if self.adapter is None
            else STATE_REGISTERED
        )
        return {
            "port": self.name,
            "section": self.spec.section,
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


def invocation_report(name: str, operation: str, outcome: "Outcome") -> dict:
    """What performing one operation comes back as, for a role to read.

    ⛔ Every one of `Outcome`'s three answers is a field, and `performed` is not
    inferred from `result` being there: an operation that legitimately answers
    `None` -- a day with no entry -- would otherwise read as one that did not run.
    """
    return {
        "port": name,
        "operation": operation,
        "performed": outcome.performed,
        "failed": outcome.failed,
        "refused": outcome.refused,
        "detail": outcome.detail,
        "result": outcome.result,
    }


def refusal_report(name: str, operation: str, error: ConfigError) -> dict:
    """What a refusal comes back as, in the same shape an outcome does.

    ⛔ The same keys, so a role reads one thing. A refusal reported in a shape of
    its own is a role writing two readers, and the second one is the one nobody
    tests.
    """
    return {
        "port": name,
        "operation": operation,
        "performed": False,
        "failed": False,
        "refused": True,
        "detail": str(error),
        "result": None,
        "key": error.key,
    }


def load(skills_root: str = ".", name: str = TRACKER, **kwargs) -> Port:
    """One port over the configuration at `skills_root`, read through #1's reader.

    `name` is the key carrying the kind, which is the port's name (§ 26). It
    defaults to § 3's, that being the port every role but § 9's asks for.
    """
    return Port(config.load(skills_root, **kwargs), port_spec(name))


def load_every(skills_root: str = ".", **kwargs) -> dict[str, Port]:
    """Every port the surface declares, over one configuration.

    ⛔ One read of the configuration for all of them. A per-port load would
    resolve the project once per port, and § 1 has a role state the project it
    addresses -- which it cannot do about a resolution it made more than once.
    """
    configuration = config.load(skills_root, **kwargs)
    return {
        name: Port(configuration, spec) for name, spec in sorted(surface_ports().items())
    }


# --- self-test -------------------------------------------------------------
#
# The acceptance check of the work items this contract was built for, run as
# code: the contract is read from the surface, an absent capability produces the
# stated fallback and never an error, a state whose writer is not the procedure
# is refused with the writer named, and a kind of `none` has every operation
# unavailable while reporting no fault. One planted violation per branch that
# does real work, which is the standard the two gates in `tools/` set.
#
# ⛔ **Every assertion below runs once per port the surface declares**, over the
# ports the markers name rather than over a list here. A suite that held one port
# would be a suite that holds the contract for the port it was written against
# and claims the machine is general -- which is precisely the claim § 26 makes
# and the one this file has to pay for.


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
    kinds = facts["enums"].get(TRACKER, [])
    return [
        kind
        for kind in kinds
        if config.Config({"tracker": {"kind": kind}}, ".", facts).has_tracker
    ]


def _set(configuration: config.Config, path: str, value) -> config.Config:
    """One dotted key written into a fixture's own data.

    ⛔ Written rather than defaulted, and on a configuration loaded from the
    examples: the suite states the condition it is testing -- a kind that
    addresses nothing, a kind nothing is installed for -- instead of waiting for
    an example to happen to carry it, which is the discipline `installed={}`
    already has one assertion over.
    """
    node, parts = configuration.data, path.split(".")
    for part in parts[:-1]:
        node = node.setdefault(part, {})
    node[parts[-1]] = value
    return configuration


def _stated_kinds(spec: PortSpec) -> list[str]:
    """Every kind this port states that addresses something.

    Derived from the port's own alternation, and the member that addresses
    nothing is dropped by the shared sentinel rather than by spelling a tracker
    here -- which is the point of the sweep this feeds.
    """
    return [kind for kind in config.facts_for(spec.name) if kind != NONE]


def _hold_port(check, surface_text: str, spec: PortSpec) -> None:
    """Every assertion the contract makes, against one of the surface's ports.

    ⛔ Takes the port rather than finding one: `self_test` runs this over every
    port the markers declare, so an assertion written here is an assertion made
    about all of them. A port-specific one — § 4.2's writer refusal is the only
    case — is guarded by the operation it needs being in that port's own list,
    which is the port's fact and not a branch on its name.
    """
    # ⛔ Read the surface through `check` rather than beside it. The reader's
    # own suite learned this the hard way one file over: the command the
    # workflow runs must come back with a verdict, so a section this module
    # cannot parse is a red line and a non-zero exit, never a traceback where
    # the report should be.
    try:
        stated = operations(surface_text, spec.section, spec.prefix)
        broken = None
    except ConfigError as error:
        stated, broken = {}, str(error)
    check("the surface states the operation list this contract holds", bool(stated), broken or "")
    if not stated:
        return

    # Five plants against the port's table, each a shape that silently changes the
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
    check(
        f"§ {spec.section} states `{first}` in a row this suite can plant into",
        row is not None,
    )

    # ⛔ Every plant is spliced into **this port's own section** and never into the
    # document: a `replace(..., 1)` hits whichever section states the thing first,
    # so for the second port a plant on the operation column's name used to unmake
    # the other port's table, assert nothing about this one, and read green.
    body = section_body(surface_text, spec.section)
    check(
        f"this suite can find § {spec.section} to plant inside",
        bool(body) and (not row or row in body),
        "the section is empty, or states its operation table somewhere else",
    )
    surface_name = os.path.relpath(config.SURFACE, config.PLUGIN_ROOT)

    def with_body(changed: str) -> str:
        return surface_text.replace(body, changed, 1)

    plants = []
    if row and body:
        cells = _row(row)
        a_second_table = "\n".join(
            [
                "| " + " | ".join([OPERATION_COLUMN, "Asks", ABSENT_COLUMN]) + " |",
                "|---|---|---|",
                row,
            ]
        )
        plants += [
            (
                # The header unmade, so the section states rows and no operation
                # table. ⚠️ Unmaking a *row* would not do it: the other rows still
                # make an operation list, so the refusal would never fire.
                "a port's section stating no operation table",
                with_body(body.replace(f"| {OPERATION_COLUMN} |", "| Thing |", 1)),
                surface_name,
            ),
            (
                "an operation stated with no absent case",
                with_body(body.replace(row, "| " + " | ".join(cells[:-1]) + " |  |", 1)),
                f"{spec.prefix}.operations.{first}",
            ),
            (
                "an operation stated twice",
                with_body(body.replace(row, row + "\n" + row, 1)),
                f"{spec.prefix}.operations.{first}",
            ),
            (
                "an operation stated in a row with a cell missing",
                with_body(body.replace(row, "| " + " | ".join(cells[:-1]) + " |", 1)),
                f"{spec.prefix}.operations.{first}",
            ),
            (
                # ⛔ Appended **inside this port's section**. A second table at the
                # end of the document sits under whatever section is last and is
                # refused by `surface_ports` as a table no port names -- a
                # different refusal, which would leave the per-port one unasserted.
                "a second table stating the port's operation list",
                with_body(f"{body}\nand again:\n\n{a_second_table}\n"),
                surface_name,
            ),
        ]
    for label, planted, key in plants:
        reported = _refused(
            lambda text=planted: operations(text, spec.section, spec.prefix)
        )
        check(f"{label} is refused, naming {key}", reported == key, f"reported {reported!r}")

    # A pipe inside a cell is written `\|` and must stay inside it. Planted on
    # the fallback the module exists to carry, because getting this wrong hands
    # a role a truncated instruction that reads as a whole one.
    if row and body:
        cells = _row(row)
        escaped = "| " + " | ".join(cells[:-1] + [r"wait \| then report"]) + " |"
        planted = operations(
            with_body(body.replace(row, escaped, 1)), spec.section, spec.prefix
        )
        check(
            "a pipe escaped inside a fallback stays inside it",
            planted[first] == "wait | then report",
            f"read {planted[first]!r}",
        )

        # A fenced block ends the table above it, so an unrelated table below one
        # cannot contribute operations. ⛔ Planted inside this port's own section,
        # for the reason the plants above are: appended to the document it would
        # sit under the last section and assert nothing about this one.
        #
        # ⛔ And spliced **directly behind the table's last row**, with a row this
        # reader would otherwise accept. The earlier plant put a `Thing | Other`
        # table two blank lines down: those headers are discarded whatever the
        # fence does, and a blank line already ends a table, so the assertion
        # passed identically with the fence handling removed -- measured. What
        # discriminates is a row that *is* operation-shaped, immediately after the
        # fence, with nothing else to end the table.
        glued = with_body(
            body.replace(
                row, f"{row}\n```yaml\nkey: value\n```\n| `telepathy` | asks | x |", 1
            )
        )
        read_back = operations(glued, spec.section, spec.prefix)
        check(
            "a table after a fenced block is not read as part of the operation table",
            "telepathy" not in read_back,
            f"read {sorted(read_back)!r}",
        )

    # An absent capability resolves to the stated fallback, for every operation,
    # and nothing raises on the way. This is the acceptance item that would be
    # vacuous if it were only asserted of the adapter for a kind of `none`, so it
    # runs over a double that implements nothing and over one that implements
    # half.
    nothing = Port(_any_example(), spec, adapter=Adapter(), stated=stated)
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
    configured = [c for c in _loaded().values() if Port(c, spec, stated=stated).configured]
    # ⛔ Asserted here, before anything indexes the list. The guard used to sit a
    # hundred lines below the first `[0]`, so an examples directory with one kind
    # of configuration in it killed the run with an `IndexError` where the verdict
    # belongs -- dead exactly when it was needed.
    check(f"an example configures `{spec.name}`", bool(configured))
    if not configured:
        return
    # ⛔ The registry is **stated**, not taken from whatever happens to be built.
    # Two earlier shapes were both wrong: indexing the first configured example
    # turned this check -- which *invokes every operation* -- into real calls
    # against a live tracker the moment that example's kind had an adapter, and
    # filtering the examples by what is installed made the property untestable the
    # day the last adapter lands, which is a gate that reddens on the project
    # finishing. `installed={}` says *configured kind, nothing built* with no
    # dependence on either.
    uninstalled = Port(configured[0], spec, stated=stated, installed={})
    check(
        "a configured kind with no implementation resolves to no adapter",
        uninstalled.adapter is None,
    )
    check(
        "an operation with no implementation installed falls back too, and does not raise",
        all(
            not uninstalled.invoke(operation).performed
            and uninstalled.invoke(operation).detail == stated[operation]
            for operation in stated
        ),
    )
    # And the seam itself is held: a registry that *does* carry the kind answers
    # from it, so `installed={}` above is proving an absence rather than a
    # parameter nothing reads. ⛔ The operation is taken from this port's own list
    # rather than named, which is what makes this one assertion rather than one
    # per port.
    seam = Adapter({first: lambda *a, **k: "seam"})
    stocked = Port(
        configured[0],
        spec,
        stated=stated,
        installed={configured[0].get(spec.name): seam},
    )
    check(
        "a stated registry carrying the kind answers from it",
        stocked.adapter is seam and stocked.invoke(first).result == "seam",
    )

    half = sorted(stated)[: max(1, len(stated) // 2)]
    performed = Port(
        _any_example(),
        spec,
        adapter=Adapter({name: lambda *a, **k: "done" for name in half}),
        stated=stated,
    )
    check(
        "a declared capability is performed by the implementation",
        all(performed.invoke(name).performed for name in half),
    )

    # The host refusing to answer: a capability that exists and a call that did
    # not go through. ⛔ Held apart from an absence, because the two share
    # `performed: false` and a role that read a broken call as a missing feature
    # would take the fallback -- acting on a decision nobody made.
    def _unreachable(*_args, **_kwargs):
        raise HostUnavailable("`gh issue view 1` timed out after 30s")

    one = sorted(stated)[0]
    broke = Port(
        _any_example(), spec, adapter=Adapter({one: _unreachable}), stated=stated
    )
    failure = broke.invoke(one)
    check(
        "a host that does not answer comes back as an outcome, not a traceback",
        not failure.performed and failure.failed,
        f"got {str(failure)!r}",
    )
    check(
        "and names the host's own words rather than the stated fallback",
        "timed out" in failure.detail and failure.detail != stated[one],
        f"got {failure.detail!r}",
    )
    check(
        "while a genuine absence is not marked failed",
        not nothing.invoke(one).failed,
    )
    # The capability is still declared: a failure is not an absence, so the query
    # must keep answering yes. Reading it the other way would have a role give up
    # on an operation its tracker has because one call timed out.
    check(
        "and the capability still reads as present after a failure",
        broke.implements(one),
    )
    check(
        "the capability query answers from the implementation, not a configuration",
        all(performed.implements(name) for name in half)
        and not any(performed.implements(n) for n in stated if n not in half),
    )
    check(
        "an operation the surface does not state is refused, naming it",
        _refused(lambda: nothing.invoke("telepathy"))
        == f"{spec.prefix}.operations.telepathy",
        f"reported {_refused(lambda: nothing.invoke('telepathy'))!r}",
    )
    check(
        "an adapter implementing an unstated operation is refused, naming it",
        _refused(
            lambda: Port(
                _any_example(),
                spec,
                adapter=Adapter({"telepathy": lambda: None}),
                stated=stated,
            )
        )
        == f"{spec.prefix}.operations.telepathy",
    )

    # The adapter for a kind that addresses nothing: every operation unavailable,
    # and nothing reading as a fault. ⛔ The kind is **written into** a fixture
    # rather than looked for among the examples, for the reason `installed={}`
    # above is stated: a port whose `none` no example happens to carry would leave
    # this -- the contract's own acceptance item -- asserted by nothing.
    unconfigured = Port(_set(_any_example(), spec.name, NONE), spec, stated=stated)
    check(
        "a kind of `none` gets an adapter rather than nothing",
        unconfigured.adapter is UNCONFIGURED,
    )
    check(
        "against it every operation is unavailable",
        not any(unconfigured.implements(operation) for operation in stated),
    )
    reported = unconfigured.report()
    check(
        "and it reports a configuration rather than a broken install",
        len(reported) == len(stated) + 1 and f"{spec.name}: {NONE}" in reported[0],
        f"reported {reported!r}",
    )

    # A configured kind with no implementation installed: the same unavailability,
    # reported as the different fact it is.
    # ⛔ `installed={}` again, for the same reason as above: the two reports have
    # to read apart permanently, and that property must not stop being provable
    # the day every kind the surface states has an implementation.
    check(
        "a kind whose implementation is not installed reports that, not a configured none",
        uninstalled.adapter is None
        and uninstalled.kind in uninstalled.report()[0]
        and uninstalled.report()[0] != reported[0],
        f"reported {uninstalled.report()[:1]!r}",
    )

    # ⛔ And the **word** each of those three states comes back as, which is the
    # one thing in this contract a consumer outside this file matches on. ⚠️ Held
    # because its absence was paid for: renaming one of them in `to_dict` left the
    # readiness script's three-way lookup raising `KeyError` for every
    # configuration with no tracker, and no assertion anywhere called `to_dict` at
    # all. ⛔ The set is held closed as well as each member named -- a fourth state
    # added here is a consumer's lookup table silently missing a key.
    states = {
        STATE_UNCONFIGURED: unconfigured,
        STATE_ABSENT: uninstalled,
        STATE_REGISTERED: stocked,
    }
    for word, answering in states.items():
        described = answering.to_dict()
        check(
            f"`to_dict` reports the `{word}` state as exactly that word",
            described["adapter"] == word,
            f"reported {described['adapter']!r}",
        )
    check(
        "and those are the only states it has, so a consumer's lookup is complete",
        set(states) == set(ADAPTER_STATES),
        f"this module names {sorted(ADAPTER_STATES)!r}",
    )

    # What performing an operation comes back as. ⛔ Asserted over the report
    # builder rather than by running the command, because invoking an operation
    # for real is a write against whatever this project configures -- a tracker,
    # or somebody's timesheet. ⚠️ A port whose operations no role can reach is a
    # contract nobody can keep, which is why that path exists at all; it shipped
    # with nothing holding its shape, which is how the state words above shipped
    # wrong one field over.
    done = Port(
        _any_example(), spec, adapter=Adapter({first: lambda *a, **k: None}), stated=stated
    ).invoke(first)
    reported = invocation_report(spec.name, first, done)
    check(
        "an operation that answers `None` still reports as performed",
        reported["performed"] and reported["result"] is None,
        f"reported {reported!r}",
    )
    refusal = refusal_report(
        spec.name, "telepathy", ConfigError(f"{spec.prefix}.operations.telepathy", "x")
    )
    check(
        "a refusal reports in the same shape an outcome does, plus the key",
        set(refusal) == set(reported) | {"key"}
        and refusal["refused"]
        and not refusal["performed"],
        f"reported {sorted(refusal)!r} against {sorted(reported)!r}",
    )

    # § 4.2's refusal, which is the one guard above a capability: the procedure
    # asks for a role and is told whose state it is. ⚠️ The role words are taken
    # from the surface's own `role` set rather than written here -- the writers
    # were derived from the start and the roles were not, which left three
    # status words copied into this file with nothing holding them to § 4.2.
    #
    # ⛔ Guarded by the **operation** rather than by the port's name: the status
    # machinery hangs off `set_state`, so a port whose list does not carry it has
    # no advance to refuse. A branch on which port this is would be the thing § 26
    # says this contract must not grow.
    if "set_state" not in stated:
        return
    roles = config.facts_for("role")
    check("the surface states the `role` set this suite advances to", bool(roles))
    a_role, another_role = (roles + roles)[0], (roles + roles)[1]
    for writer in [w for w in config.facts_for("writer") if w != PROCEDURE]:
        configuration = _with_statuses(
            [{"name": "a status", "role": a_role, "writer": writer}]
        )
        outcome = Port(
            configuration, spec, adapter=Adapter(), stated=stated
        ).advance_to(a_role)
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

    # ⛔ The double **returns what it was handed**, rather than a constant. A
    # fixture of `lambda *a, **k: "moved"` swallowed the resolved status word, so
    # the hand-off below could be deleted and this suite stayed green -- the one
    # defect building the first adapter against this method found, held by
    # nothing. What is asserted is the word the configuration mapped, not that a
    # call happened.
    through = Port(
        _with_statuses([{"name": "a status", "role": a_role, "writer": PROCEDURE}]),
        spec,
        adapter=Adapter({"set_state": lambda *a, **k: k.get("status", "<no status>")}),
        stated=stated,
    )
    advanced = through.advance_to(a_role)
    check(
        "an advance the procedure may write goes through the capability",
        advanced.performed and not advanced.refused,
        f"got {str(advanced)!r}",
    )
    check(
        "and the implementation is handed the status word the role resolved to",
        advanced.result == "a status",
        f"the implementation received {advanced.result!r}, not the mapped word",
    )
    # The role name is never what arrives: a double that got `a_role` would pass
    # the check above if the two ever coincided, and they must not.
    check(
        "and never the role name in its place",
        advanced.result != a_role,
        f"received the role `{a_role}` where its status word belongs",
    )
    twice = _with_statuses(
        [
            {"name": "one word", "role": a_role, "writer": PROCEDURE},
            {"name": "another", "role": a_role, "writer": PROCEDURE},
        ]
    )
    ambiguous = _refused(
        lambda: Port(twice, spec, adapter=Adapter(), stated=stated).advance_to(a_role)
    )
    check(
        "a role mapped to two status words is refused, naming the key",
        ambiguous == "statuses",
        f"reported {ambiguous!r}",
    )
    unmapped = Port(
        _with_statuses([]), spec, adapter=Adapter(), stated=stated
    ).advance_to(another_role)
    check(
        "an advance to a role no status maps is reported, not refused and not raised",
        not unmapped.performed and not unmapped.refused and another_role in unmapped.detail,
        f"got {str(unmapped)!r}",
    )


def _hold_registration(check, spec: PortSpec) -> None:
    """Registration and discovery, against one port's own package.

    ⛔ Separate from `_hold_port` because these touch the live registry and the
    import system rather than a fixture, and a failure here is the toolkit's own
    mistake rather than a contract the surface states. ⚠️ Run per port for the
    same reason everything above is: the flags and the registry are keyed by
    package, so a port swept once proves nothing about the other.
    """
    stated = spec.operations()
    first = sorted(stated)[0]

    # The seam the installed adapters register against. The word is taken from
    # the surface rather than written here, for the same reason the fixtures are
    # taken from the examples directory: nothing in this file names a tracker.
    # ⛔ A kind **nothing is installed for**, and ⛔ one the surface does not
    # state either -- **derived** from a stated word rather than chosen out of
    # the stated set. Two earlier shapes were both wrong for the same reason, a
    # step apart: the first-listed kind collided with a real implementation the
    # day it had one, and picking the first stated kind nothing was installed for
    # made this block a gate that **reddens on the project finishing** --
    # measured, on the change that landed the last of them, where there was no
    # free kind left and the whole block went unasserted while the run reported a
    # failure nobody could fix. ⚠️ The `pop` below is the reason the kind must not
    # be a real one: it would uninstall a live implementation mid-run, leaving
    # every later check reading a registry this suite had corrupted.
    kinds = _stated_kinds(spec)
    registry = load_adapters(spec)
    check(f"`{spec.name}` states a kind to register against", bool(kinds))
    # The suffix is this suite's own and the word before it is the surface's, so
    # this names no tracker while being derived from one.
    derived = f"{kinds[0]}-nothing-answers-for" if kinds else None
    free = bool(derived) and derived not in kinds and derived not in registry
    check(
        "and a kind derived from it that nothing states and nothing installed",
        free,
        f"`{derived}` is either stated by the surface or already installed, so "
        "registering a double against it would evict or shadow a real one",
    )
    if free:
        kind = derived
        register(spec, kind, Adapter({first: lambda *a, **k: "read"}))
        registered = _set(_any_example(), spec.name, kind)
        port = Port(registered, spec, stated=stated)
        check(
            "a registered implementation answers the capability query for its kind",
            port.adapter is installed(spec)[kind]
            and port.invoke(first).result == "read",
        )
        refusal = _refused(lambda: register(spec, kind, Adapter()))
        check(
            "a second implementation for one kind is refused, naming the kind",
            refusal == f"{spec.prefix}.kind.{kind}",
            f"reported {refusal!r}",
        )
        check(
            "an implementation of an unstated operation is refused at registration",
            _refused(
                lambda: register(
                    spec, kind + "-x", Adapter({"telepathy": lambda: None})
                )
            )
            == f"{spec.prefix}.operations.telepathy",
        )
        installed(spec).pop(kind)

    # Discovery: the directory is the install list, so what is checked is that
    # a sweep installs what is there, that a sweep run again is not refused, and
    # that a module which cannot be installed is refused rather than skipped --
    # on the second ask as well as the first.
    #
    # ⛔ Through `check`, not beside it. A bare `load_adapters()` here was the one
    # place in this suite where a broken module made the gate exit on a traceback
    # with no verdict and no count, which is what the surface read twenty lines
    # into this function is wrapped to avoid.
    swept, sweep_refused = {}, None
    try:
        swept = load_adapters(spec)
    except ConfigError as error:
        sweep_refused = str(error)
    check(
        f"discovery installs at least one implementation from `{spec.package}/`",
        bool(swept),
        sweep_refused or f"{spec.directory} yielded nothing",
    )
    # ⛔ A **real** second sweep, with this package's flag cleared, rather than a
    # second read of the first one's result. Comparing the return against a copy
    # of the registry taken on the line before was the earlier shape and could not
    # fail. What this holds is that re-entry installs the same module objects
    # rather than handing `register` a kind it already has, which would be refused
    # and turn a later capability query into an error.
    was_done = spec.package in _discovered
    _discovered.discard(spec.package)
    try:
        again = load_adapters(spec)
        resweep_refused = None
    except ConfigError as error:
        again, resweep_refused = None, str(error)
    finally:
        if was_done:
            _discovered.add(spec.package)
    check(
        "a sweep run again installs the same implementations rather than being refused",
        again == swept,
        resweep_refused or f"the second sweep gave {again!r}, not {swept!r}",
    )
    # ⛔ Planted in a temporary directory, never in the live package. A probe
    # module written beside the real implementations would be imported by every
    # later run in this tree -- and by any other session sharing it.
    #
    # ⚠️ The plant is a `PortSpec` of its own over a package name no port uses,
    # which is what the per-package flags above buy: the live registry, the live
    # sweep state and the live package are all untouched, so nothing has to be
    # saved and put back. The earlier shape swapped a module global for the
    # directory and restored it in a `finally`, which was one exception away from
    # leaving the contract pointed at a deleted temporary directory.
    import tempfile
    import types

    with tempfile.TemporaryDirectory() as planted:
        package = f"{spec.package}_nothing_installs_from"
        directory = os.path.join(planted, package)
        os.makedirs(directory)
        open(os.path.join(directory, "probe.py"), "w").close()
        # Seeded into the module cache so the import resolves without the
        # temporary directory having to be an importable package.
        sys.modules[f"{package}.probe"] = types.ModuleType("probe")
        was_root = SCRIPTS_DIR
        try:
            globals()["SCRIPTS_DIR"] = planted
            broken_spec = PortSpec(spec.name, spec.section, package)
            check(
                "an implementation that cannot be installed is refused, naming the module",
                _refused(lambda: load_adapters(broken_spec))
                == f"{spec.prefix}.implementations.probe.py",
                f"reported {_refused(lambda: load_adapters(broken_spec))!r}",
            )
            # ⛔ And refused *again*. The flag used to be set before the sweep,
            # so a module that raised left discovery marked done over a half-full
            # registry and every later ask came back clean -- reporting a kind
            # that was built as a kind that never was, which is the single
            # distinction § 3 asks this module to keep.
            check(
                "and refused on the second ask, not quietly skipped",
                _refused(lambda: load_adapters(broken_spec))
                == f"{spec.prefix}.implementations.probe.py",
                "the second ask came back clean, so a broken implementation "
                "would read as an absence from then on",
            )
            # ⛔ And the other port is untouched by it. The flags are per package
            # for exactly this reason: one broken module must not make a sibling
            # port's built implementations read as absent, which is the one
            # distinction § 3 asks this module to keep, one port over.
            #
            # ⛔ Through a refusal that is caught, not a bare call. The regression
            # this assertion exists for -- a failure remembered for the process
            # rather than for the package -- makes the live sweep *raise*, and a
            # bare call would come back as a traceback out of the suite instead of
            # the red line and the count this file holds every other read to.
            # Measured: planted, the run died at this line having printed `ok` for
            # the two assertions above.
            #
            # ⛔ And it is a **real** sweep. With the package still marked swept
            # this returned the memo without looking at a directory -- and
            # `SCRIPTS_DIR` is pointed at the temporary root here, so the live
            # port's own directory does not even exist at this moment. Both are
            # put back for the duration, or the assertion holds the memo rather
            # than the sweep.
            globals()["SCRIPTS_DIR"] = was_root
            _discovered.discard(spec.package)
            try:
                live, live_refused = load_adapters(spec), None
            except ConfigError as error:
                live, live_refused = {}, str(error)
            finally:
                globals()["SCRIPTS_DIR"] = planted
            check(
                "a broken package leaves the live one's implementations installed",
                bool(live),
                live_refused
                or "the live sweep came back empty after a sibling package failed",
            )
        finally:
            globals()["SCRIPTS_DIR"] = was_root
            sys.modules.pop(f"{package}.probe", None)
            _discovery_failed.pop(package, None)
            _discovered.discard(package)
            ADAPTERS.pop(package, None)
            # ⛔ And the temporary root comes back off the path. Discovery appends
            # the package's parent, so leaving it adds one dead entry per port per
            # run -- under a comment claiming nothing has to be put back.
            if planted in sys.path:
                sys.path.remove(planted)


def _hold_own_configuration(check, spec: PortSpec) -> None:
    """This repository's own configuration, through one port.

    Held for the reason `config.py` holds the same file: the one configuration the
    project actually runs on is otherwise held by nothing. ⚠️ Per port, because
    what *this* project configures differs per port -- one kind has an
    implementation here and another may not yet -- and that is the fact the
    assertions below are about.
    """
    own = os.path.join(config.REPO_ROOT, config.CONFIG_PATH)
    if not os.path.exists(own):
        return
    stated = spec.operations()
    # Through `check`, not printed beside it: a configuration this repository
    # cannot load is a red line and a count, the way the reader reports the
    # same file, rather than a traceback where the verdict belongs.
    try:
        port, refused = load(config.REPO_ROOT, spec.name), None
    except ConfigError as error:
        port, refused = None, str(error)
    check(
        f"this repository's own {config.CONFIG_PATH} loads through `{spec.name}`",
        port is not None,
        refused or "",
    )
    if port is None:
        return
    # ⛔ Asserted as a **relation** and never as a list of names or a count: the
    # lines a report carries are exactly the operations the installed
    # implementation leaves alone. Spelling either side out would put an
    # implementation's capabilities in the contract -- which the sweep in
    # `self_test` forbids -- and would need editing every time an adapter grew an
    # operation.
    own_adapter = port.adapter
    check(
        "this repository's own configuration gets an installed implementation",
        own_adapter is not None and own_adapter is not UNCONFIGURED,
        f"resolved to the adapter for `{NONE}`"
        if own_adapter is UNCONFIGURED
        else "no implementation is installed for its kind",
    )
    if own_adapter is None or own_adapter is UNCONFIGURED:
        return
    absent = sorted(op for op in stated if not port.implements(op))
    check(
        "and performs at least one operation, so the install is load-bearing",
        len(absent) < len(stated),
    )
    check(
        "its report names the absent operations and nothing else -- no fault line",
        len(port.report()) == len(absent)
        and all(
            line.startswith(f"`{operation}` is unavailable: ")
            for operation, line in zip(absent, port.report())
        ),
        f"reported {port.report()!r}",
    )


def self_test() -> int:
    failures = 0

    def check(label: str, condition: bool, detail: str = "") -> None:
        nonlocal failures
        if condition:
            print(f"  ok    {label}")
        else:
            failures += 1
            print(f"  FAIL  {label}{': ' + detail if detail else ''}")

    with open(config.SURFACE, encoding="utf-8") as handle:
        surface_text = handle.read()

    # ⛔ The ports come off the surface, and that read is itself through `check`:
    # a surface this module cannot resolve ports from is a red line and a
    # non-zero exit, never a traceback where the verdict belongs.
    try:
        specs, unreadable = surface_ports(surface_text), None
    except ConfigError as error:
        specs, unreadable = {}, str(error)
    check("the surface declares the ports this contract holds", bool(specs), unreadable or "")
    if not specs:
        print(f"\n{failures} assertion(s) did not hold.")
        return 1

    # ⛔ More than one, asserted rather than assumed. Every assertion below runs
    # per port, so a surface that had lost a marker would run the whole suite
    # against one port and report green -- which is the generality § 26 claims
    # going unheld while reading as held.
    check(
        "it declares more than one, so the contract is held as the machine it is",
        len(specs) > 1,
        f"declares only {sorted(specs)!r}",
    )
    # ⛔ And the port `load()` answers for with no argument is one of them. The
    # one port name this module spells: held here so that renaming the key on the
    # surface reddens the build instead of leaving every role's default unresolvable.
    check(
        f"`{TRACKER}` is among them, which is what `load()` defaults to",
        TRACKER in specs,
        f"declares {sorted(specs)!r}",
    )
    # ⛔ A port no marker declares is refused by name rather than resolved to the
    # default, which is the plausible-thing-first failure the surface keeps naming.
    check(
        "a port the surface does not declare is refused, naming it",
        _refused(lambda: port_spec("telepathy.kind")) == "telepathy.kind",
        f"reported {_refused(lambda: port_spec('telepathy.kind'))!r}",
    )
    # ⛔ An operation table under a section no marker names is refused **here**,
    # the per-port lookup being unable to see it: § 26's *one port per table*, and
    # the half that would otherwise let a whole operation list sit on the surface
    # holding no adapter to anything.
    orphan = surface_text + "\n## A section no marker names\n\n" + "\n".join(
        [
            "| " + " | ".join([OPERATION_COLUMN, "Asks", ABSENT_COLUMN]) + " |",
            "|---|---|---|",
            "| `telepathy` | everything | nothing |",
        ]
    ) + "\n"
    check(
        "an operation table under no declared port is refused, naming the surface",
        _refused(lambda: surface_ports(orphan))
        == os.path.relpath(config.SURFACE, config.PLUGIN_ROOT),
        f"reported {_refused(lambda: surface_ports(orphan))!r}",
    )
    # ⛔ And the other direction of the same rule, which the orphan check cannot
    # see. Both plants copy a declared marker onto a second key: one leaves the
    # section it sits under alone, so two ports read one table; the other gives it
    # its own section and keeps the directory, so two ports resolve one registry
    # and the second answers from an implementation held to the first's list.
    # Neither was refused before this was written.
    # ⚠️ The plant declares a whole block of its own, because the marker is read
    # only on a `kind`: copying the clause onto a neighbouring key is refused by
    # that rule instead and never reaches this one. Measured while writing it.
    one = specs[sorted(specs)[0]]
    body = section_body(surface_text, one.section)
    heading = body.splitlines()[0]
    second = (
        f"{heading}\n\n```yaml\n"
        "a_port_this_suite_planted:\n"
        f"  kind: a | b          # port: {one.package}\n"
        "```\n"
    )
    twinned = surface_text.replace(body, body.replace(heading, second, 1), 1)
    check(
        "two ports declared under one section are refused, naming the surface",
        _refused(lambda: surface_ports(twinned))
        == os.path.relpath(config.SURFACE, config.PLUGIN_ROOT),
        f"reported {_refused(lambda: surface_ports(twinned))!r}",
    )

    # Each port's own kinds, needed below and asserted before anything indexes it.
    kinds = _real_tracker_kinds()
    check("the surface states a tracker kind to sweep for", bool(kinds))

    for name, spec in sorted(specs.items()):
        print(f"\n--- the `{name}` port, § {spec.section} " + "-" * max(0, 24 - len(name)))
        _hold_port(check, surface_text, spec)
        _hold_registration(check, spec)
        _hold_own_configuration(check, spec)

    print()
    # ⛔ One registry per port, and not one shared across them. Nothing on this
    # surface stops two ports stating the same kind word, and with the registries
    # merged the second port's implementation for that word is refused as a second
    # adapter for one kind -- or, where it is not, resolved for the wrong port with
    # the capability query answering yes. ⚠️ Asserted because the plant was
    # measured: merging the two registries left every assertion above green, the
    # kinds the two ports happen to state not colliding today.
    if len(specs) > 1:
        two = [specs[name] for name in sorted(specs)][:2]
        shared = "a-kind-more-than-one-port-states"
        answered, refused_at = {}, None
        try:
            for spec in two:
                own = sorted(spec.operations())[0]
                answered[spec.name] = own
                register(
                    spec, shared, Adapter({own: lambda *a, _own=own, **k: _own})
                )
            check(
                "two ports may state one kind word, each resolving its own adapter",
                all(
                    Port(_set(_any_example(), spec.name, shared), spec)
                    .invoke(answered[spec.name])
                    .result
                    == answered[spec.name]
                    for spec in two
                ),
                "a port resolved an implementation registered for the other one",
            )
        except ConfigError as error:
            refused_at = str(error)
        finally:
            for spec in two:
                installed(spec).pop(shared, None)
        if refused_at is not None:
            check(
                "two ports may state one kind word, each resolving its own adapter",
                False,
                f"registering it for the second port was refused: {refused_at}",
            )
    # The two sentinels this module spells out, held to the surface so that
    # renaming one there reddens the build instead of silently turning a refusal
    # into the wrong words.
    for sentinel in (PROCEDURE, NEVER):
        check(
            f"the surface still states `{sentinel}` in its `writer` set",
            sentinel in config.facts_for("writer"),
            f"states {config.facts_for('writer')!r}",
        )
    # ⛔ And the one every port shares, held to **every** port's own kind set
    # rather than to one: a port whose alternation lost the word would have this
    # module resolve `none` as a kind somebody forgot to build, which is the one
    # distinction § 3 asks it to keep.
    for name, spec in sorted(specs.items()):
        check(
            f"`{name}` still states `{NONE}` among its kinds",
            NONE in config.facts_for(name),
            f"states {config.facts_for(name)!r}",
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

    if failures:
        print(f"\n{failures} assertion(s) did not hold.")
    return 1 if failures else 0


# --- entry point -----------------------------------------------------------


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="A port: what is available here, and what each absence does.",
    )
    parser.add_argument(
        "--skills-root",
        default=".",
        help="the root the configuration is resolved relative to; defaults to the "
        "working directory, which is where a role invoked inside a project finds it",
    )
    parser.add_argument(
        "--port",
        default=TRACKER,
        help="which port to report: the configuration key its kind is written on, "
        f"which is the port's name. Defaults to `{TRACKER}`, the port every role "
        "but the day log's asks for",
    )
    parser.add_argument(
        "--ports",
        action="store_true",
        help="report every port the surface declares rather than one",
    )
    parser.add_argument(
        "--invoke",
        metavar="OPERATION",
        help="perform one of this port's operations rather than reporting it, and "
        "print the outcome. Every value is passed as written; an implementation "
        "holds what it will accept",
    )
    parser.add_argument(
        "--argument",
        action="append",
        default=[],
        metavar="VALUE",
        help="one argument for `--invoke`, repeated in the order the operation "
        "takes them. Always passed as text",
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

    # ⛔ Performing an operation is a separate request from reporting one, and the
    # two are not combined. ⚠️ This exists because a port whose operations no role
    # can reach is a contract nobody can keep: the tracker port's roles have a
    # host client of their own to perform with, and § 26's has none -- its adapter
    # *is* the only writer. Without this the day-log role was told to call five
    # operations and left to compose a path by hand, which is the one thing its
    # own text forbids.
    if args.invoke:
        if args.ports:
            print(
                "Refused: `--invoke` performs one port's operation, so it is not "
                "asked of every port at once.",
                file=sys.stderr,
            )
            return 2
        try:
            answering = load(
                args.skills_root, args.port, check_paths=not args.no_check_paths
            )
            outcome = answering.invoke(args.invoke, *args.argument)
        except ConfigError as error:
            # ⛔ Reported as a refusal and never as a traceback. A value the
            # configuration states badly, or an operation this port does not
            # state, is an answer a role can put in its report -- and the
            # alternative measured here was a raw exception reaching a role that
            # had been told the absence would be reported to it.
            print(
                json.dumps(
                    refusal_report(args.port, args.invoke, error),
                    indent=2,
                    ensure_ascii=False,
                )
            )
            return 1
        print(
            json.dumps(
                invocation_report(answering.name, args.invoke, outcome),
                indent=2,
                ensure_ascii=False,
                default=str,
            )
        )
        return 0 if outcome.performed else 1

    # ⛔ One port by default and never all of them. A role reads this output for
    # the fallbacks it must take, and a report carrying a second port's fallbacks
    # is a role being handed decisions about a store it is not writing to.
    try:
        if args.ports:
            every = load_every(args.skills_root, check_paths=not args.no_check_paths)
            out = {"ports": {name: port.to_dict() for name, port in every.items()}}
        else:
            out = load(
                args.skills_root, args.port, check_paths=not args.no_check_paths
            ).to_dict()
    except ConfigError as error:
        print(str(error), file=sys.stderr)
        return 1
    print(json.dumps(out, indent=2, ensure_ascii=False, sort_keys=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
