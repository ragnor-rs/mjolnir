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
    maps that its tracker cannot hold, a role mapped to two status words, and a
    reverse-edge trigger ruled twice. None of those is a tracker or a store that
    cannot do something; each is a text that does not say what the procedure is
    supposed to do. ⚠️ **The last two are one shape and are listed apart on
    purpose**: both are a configuration answering once-asked questions twice,
    and each names its own key, so a reader meeting either is sent to the key
    they would edit rather than to the shape they share.
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
import inspect
import json
import os
import re
import subprocess
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

# The writer the deploying role asks as (§ 4.2, § 33). ⛔ A third constant rather
# than a widening of `PROCEDURE`: the two are different answers to *who may write
# this status*, and a guard that treated them as one would let any role write a
# status the project reserved for the deploy. ⚠️ Held to the surface by the
# self-test exactly as the two above are.
DEPLOY = "deploy"

# What a role is taken to be asking as where it says nothing. ⛔ `procedure`, so
# that every caller written before a deploying role existed is held exactly as it
# was -- which is what makes the parameter an addition rather than a change to
# what any existing ask means.
ASKED_AS = PROCEDURE

# ⛔ The writers a role in this procedure may ask as, and the whole of them. § 4.2
# states it in as many words: `procedure` is what every role but one asks as and
# `deploy` is the only other. The rest of that set names parties this procedure
# is not -- a merge's automation, the person who ordered the work, a mechanical
# path test -- so a caller naming one would be claiming to be somebody, which is
# the fabricated attestation the record rules out one section over.
#
# ⚠️ Without this the parameter inverts the guard it was added to: any caller
# could write any status by naming that status's own writer, and the one writer
# the guard refuses outright would be the only one left refusing.
ASKABLE_AS = (PROCEDURE, DEPLOY)

# § 32's key, spelled out for the reason the two writers above are and held to
# the surface by the self-test the same way: a refusal naming a key the surface
# has renamed sends somebody to edit a key that is not there.
REVERSALS = "reversals"

# § 4.8's writer key and § 33's two publishing operations, spelled out for the
# same reason and held to the surface the same way. ⛔ The **operation** names are
# held to § 3's own table rather than carried as literals a renamed row could
# leave matching nothing: `_stated` refuses a name the table has lost, so each of
# these is named once and the refusal arrives under the key somebody would edit.
CLOSED_BY = "closed_by"

# § 4.8's key saying how the current grouping is identified, named here because
# the refusal below is keyed on it. ⛔ **Nothing in this module reads the
# tracker's own mark**, so the grouping's value arrives on the invocation under
# either of that key's values -- and a caller handing none over is refused
# against *this* key rather than against the operation's argument list, which is
# where an unkeyed refusal would have sent somebody.
CURRENT = "current"
GROUPING_ITEMS = "grouping_items"
MARK_RELEASED = "mark_grouping_released"

# The operation a writer refusal is reported against where the caller named none.
# ⛔ § 4.2's guard is shared by three directions now -- the advance, § 32's step
# backwards and § 33's grouping close -- and the two status directions report
# against the operation that would have written the status, so that stays the
# default and the third names its own.
WROTE_A_STATUS = "set_state"

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


def _set_from(outcome: "Outcome") -> list:
    """The items an answered `grouping_items` carried, or an empty set.

    ⛔ **Empty where the operation did not perform, and the caller is told
    separately.** An unread grouping and a grouping holding nothing are the same
    list, so nothing here folds them together: the outcome itself carries which
    it was, and the exit status is taken off that rather than off the length.

    ⚠️ Both shapes an implementation may answer with: the list itself, or a
    mapping carrying it under `items` beside the grouping's own value. The second
    is what every implementation here returns, the value being a fact the role
    reports; a bare list is accepted so that an implementation answering the
    narrower thing is not refused for it.
    """
    if not outcome.performed:
        return []
    result = outcome.result
    if isinstance(result, dict):
        items = result.get("items")
        return list(items) if isinstance(items, list) else []
    return list(result) if isinstance(result, list) else []


def _item_name(item: object) -> dict:
    """What identifies one item in a report, and nothing else about it.

    ⛔ **Compact by rule and not for tidiness.** § 33's precondition has to name
    **every** item holding a release, and a report that carried each item whole
    would put a backlog's worth of bodies into the window the deploy's reply is
    written in -- which is § 22's hazard arriving through a report rather than
    through a command. What a person acts on is the identifier, the title and
    where the item stands.

    ⚠️ **Every identifier shape the implementations answer with**, because the
    operation returns the host's own field names (§ 3): a short number, a key, or
    an opaque id. A reader that took one of them would name no item on two of
    the trackers, and an unnamed item in a refusal is the first one somebody
    cannot go and look at.
    """
    if not isinstance(item, dict):
        return {"item": item}
    named = {}
    for key in ("number", "key", "id", "unread"):
        if item.get(key) not in (None, ""):
            named["item"] = item[key]
            break
    else:
        named["item"] = None
    for key in ("title", "name", "url"):
        if isinstance(item.get(key), str) and item[key].strip():
            named[key] = item[key]
    return named


def _item_word(item: object) -> str | None:
    """The status word an item carries, or `None` where it carries none readable.

    ⛔ **`status` before `state`, and both, because an implementation answers
    with the host's own field names** (§ 3): where a tracker has a status field
    of its own that is the word `statuses` maps, and where it has none the coarse
    state *is* that word. A reader that took one of them would place every item
    on one tracker and none on the other.

    ⛔ **`None` rather than a guess**, which is what makes § 33's precondition
    able to report an item it could not place: an item answering no readable word
    is unanswered, and a release held by one of those reads exactly like a
    release held by nothing unless the two are kept apart.
    """
    if not isinstance(item, dict):
        return item if isinstance(item, str) and item.strip() else None
    for key in ("status", "state"):
        word = item.get(key)
        if isinstance(word, str) and word.strip():
            return word
    return None


# --- what a vocabulary read answers with -----------------------------------
#
# ⛔ **Three answers and never two.** `read_vocabulary` (§ 3) is asked once per
# project, before a configuration exists, and what it answers about is a set a
# tracker may genuinely not have: a vocabulary read, one the tracker states none
# of, and one this toolkit could not establish are three different facts. A shape
# able to say only *these are the words* and *there are none* would collapse the
# last two, which is § 2's absence-of-signal rule arriving exactly where a step
# would otherwise write a guess into a project's own file.
#
# ⛔ **Stated here rather than in each implementation**, because every adapter
# answers in one shape and a consumer reads one set of words -- four spellings of
# *unestablished* would leave a reader taking three of them as a vocabulary that
# was read.
VOCABULARY_READ = "read"
VOCABULARY_NONE = "none"
VOCABULARY_UNESTABLISHED = "unestablished"


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

    ⚠️ **`refused` carries one more case than a writer's.** § 32 refuses a step
    backwards the project rules no reverse edge for, and that refusal has no
    writer to name -- so `refused` with `writer` unset is a real state rather
    than a half-filled one.

    ⛔ **`to_role` and `trigger` are data and not prose.** A batch report naming
    the items that stepped back has to read them off the outcome; parsing them
    out of `detail` would make a sentence somebody may reword into an interface.
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
        to_role: str | None = None,
        trigger: str | None = None,
        grouping: str | None = None,
    ):
        self.operation = operation
        self.performed = performed
        self.detail = detail
        self.result = result
        self.refused = refused
        self.writer = writer
        self.failed = failed
        self.to_role = to_role
        self.trigger = trigger
        # ⛔ § 33's third fact of the same kind: which grouping a close or its
        # refusal was about. A field for `to_role`'s reason -- a deploy's report
        # names the grouping it left open beside the items it did not move, and
        # reading it out of `detail` would make a sentence into an interface.
        self.grouping = grouping

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

        ⛔ **A fourth is the arguments not fitting the operation**, which was a
        traceback until a § 33 plant surfaced it: the invocation passes whatever
        it was handed, so an operation asked for with too few of them reached the
        implementation and raised out of here — past the contract this docstring
        states. ⚠️ **Raised as a `ConfigError` and not answered as an outcome**:
        it is the *caller* that is wrong rather than the tracker, so there is no
        fallback to give and nothing about the item to report.
        """
        fallback = self._stated(operation)
        adapter = self.adapter
        if adapter is None or not adapter.implements(operation):
            return Outcome(operation, performed=False, detail=fallback)
        try:
            inspect.signature(adapter.operations[operation]).bind(*args, **kwargs)
        except TypeError as error:
            raise ConfigError(
                f"{self.spec.prefix}.operations.{operation}",
                f"was asked for with arguments it does not take: {error}. The "
                "invocation passes every value as written, so what each operation "
                "takes and in what order is the contract's -- read the port's own "
                "report rather than guessing at the list.",
            ) from None
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

    def _mapped_status(self, role: str) -> dict | None:
        """The one status this project maps to a role, or `None` where it maps none.

        ⛔ **One reader of `statuses`, shared by both directions.** § 4.2 puts the
        role-to-word mapping in the port and nowhere else, and a reverse move
        resolving it a second time would be exactly the second reader that
        section forbids -- allowed to disagree with this one about which word a
        role answers to.

        What is refused with the key named, the way the reader refuses a
        configuration the surface does not allow, is a role mapped to two status
        words (§ 4.2 states the mapping is at most one).
        """
        statuses = [
            status
            for status in (self.config.get("statuses") or [])
            if status.get("role") == role
        ]
        if not statuses:
            return None
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
        return statuses[0]

    def _refused_by_writer(
        self,
        writer: str | None,
        move: str,
        asked_as: str = ASKED_AS,
        operation: str = WROTE_A_STATUS,
        **about,
    ) -> Outcome | None:
        """§ 4.2's writer guard, in one statement for both directions.

        ⛔ **Shared rather than written once per direction**, because § 32 states
        a reverse edge's writer is checked *exactly* as the forward one is: two
        copies of this refusal are two copies allowed to drift, and the `never`
        arm is the one that must not -- it is the only writer with nobody to hand
        the move to, so a refusal that handed it to somebody would name a writer
        that does not exist.

        ⛔ **`asked_as` is the writer the caller is asking as, and it is carried
        rather than worked out here.** § 4.2 states the ask carries it: a port
        that derived who was asking would be answering a question about the
        session rather than about the procedure. ⚠️ **`never` stays refused
        whatever a caller asks as** -- it is the one writer that is not a party
        the move may be handed to, so a role claiming it would be claiming to be
        the absence of a writer.

        ⛔ **`operation` is which operation the refusal is reported against, and
        the third direction is why it is a parameter.** § 33's grouping close is
        a write to the grouping rather than to a status, so a refusal of it
        reported against the status operation would send a reader to the wrong
        half of the port -- and § 4.8 states that writer independently of the
        one § 4.2 states for the items, so the two refusals have to be
        distinguishable in a report that carries both.

        `None` where the caller may write; the refusal otherwise.
        """
        # ⛔ First, and before the configured writer is read at all: a caller
        # asking as a party this procedure is not has made a claim rather than a
        # request, and reading the configuration next would answer it.
        if asked_as not in ASKABLE_AS:
            return Outcome(
                operation,
                performed=False,
                refused=True,
                writer=writer,
                # ⚠️ No count of the askable set is written into this message,
                # which is the defect the review of this very commit found six of
                # elsewhere: the join below *is* the list, and a figure beside it
                # is a second statement free to disagree.
                detail=f"Refused: this ask is made as `{asked_as}`, which is not a "
                "writer a role in this procedure may ask as (§ 4.2). What it may "
                f"be made as is {' and '.join(f'`{word}`' for word in ASKABLE_AS)}"
                "; the rest of that set names parties this procedure is not, so "
                "naming one would be claiming to be somebody rather than asking.",
                **about,
            )
        if writer == NEVER:
            return Outcome(
                operation,
                performed=False,
                refused=True,
                writer=writer,
                detail=f"Refused: {move} is "
                f"`writer: {NEVER}` here, so the procedure writes nothing at all "
                "and reports instead. There is no other writer to hand the move "
                "to -- the credential acts as a person's own account, and every "
                "write would read as that person speaking.",
                **about,
            )
        if writer != asked_as:
            asker = (
                "the procedure" if asked_as == PROCEDURE else f"the `{asked_as}` role"
            )
            return Outcome(
                operation,
                performed=False,
                refused=True,
                writer=writer,
                detail=f"Refused: {move} is "
                f"written by `{writer}` here, not by {asker}. The move is "
                "reported for that writer to make rather than made.",
                **about,
            )
        return None

    def advance_to(self, role: str, *args, as_writer: str = ASKED_AS, **kwargs) -> Outcome:
        """Ask for an advance to a status **role**, never to a status word.

        `as_writer` is the writer the caller is asking as (§ 4.2), defaulting to
        the procedure — so every role but the deploying one asks exactly as it
        did before that role existed, and a project reserving a status for the
        deploy is still refused every other asker.

        What comes back is a report rather than an exception wherever the
        configuration is a legitimate one: no status here maps the role, which is
        exactly that (§ 4.2); the configured writer is somebody else, which is a
        refusal naming that writer; the writer is `never`, which § 4.2 states as
        the case where the procedure writes nothing at all and reports -- so the
        refusal hands the move to nobody, there being no writer to hand it to; or
        the move goes through `set_state` and its capability decides. ⛔ **The
        raise is one layer down**, in `_mapped_status`, for a role two status
        words answer. ⚠️ **No count of either list is written here**, a figure
        over them being a copy of what the code does.

        ⛔ **It asks for an advance and never discovers a reversal.** A step
        backwards is `revert_to` below, asked for as one, by § 32 -- so what this
        method does on a project that rules no reverse edge is what it did before
        that facet existed.
        """
        # Named rather than written into the two Outcomes below: an operation the
        # surface has renamed must stop this role rather than have it report a
        # move against an operation that no longer exists.
        self._stated("set_state")
        status = self._mapped_status(role)
        # ⛔ `to_role` is carried on every answer this method gives, including the
        # ones whose `detail` already names the role. The report's own rule is
        # that a fact a move or a refusal *names* is a field, and a direction
        # that spelled the role into prose and left the field null would oblige
        # the parse that rule exists to delete -- measured as exactly that, the
        # reverse direction having been given the fields while this one kept the
        # prose.
        if status is None:
            return Outcome(
                "set_state",
                performed=False,
                to_role=role,
                detail=f"No status here maps the `{role}` role, so there is "
                "nothing to advance to. A project maps a subset and an absent "
                "role is a legitimate configuration.",
            )
        refusal = self._refused_by_writer(
            status.get("writer"),
            f"the `{role}` status (`{status.get('name')}`)",
            asked_as=as_writer,
            to_role=role,
        )
        if refusal is not None:
            return refusal
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
        outcome = self.invoke("set_state", *args, status=status.get("name"), **kwargs)
        outcome.to_role = role
        return outcome

    def revert_to(self, trigger: str, *args, as_writer: str = ASKED_AS, **kwargs) -> Outcome:
        """Step an item **back**, on a trigger this project rules (§ 32).

        ⛔ **The target role is the configuration's and never the caller's.** A
        role naming where to step back to would be deriving the edge § 32 says
        is configured; what a role states here is what it observed.

        `as_writer` is `advance_to`'s, carried here for the reason § 32 gives for
        every other half of this guard: the reverse is checked **exactly** as the
        forward one is, so a parameter one direction grew and the other did not
        is the drift one shared guard exists to prevent.

        What comes back is a report rather than an exception wherever the
        configuration is a legitimate one: this project rules no reverse edge for
        the trigger, which is the refusal that keeps a role from inventing a step
        backwards and is the behaviour of every project that writes `[]`; no
        status maps the entry's role; either writer refusal, by the shared guard
        above, so the reverse is checked exactly as the forward one is; or the
        move goes through `set_state` and its capability decides. ⛔ **One case
        raises instead** — a trigger ruled twice, which the module docstring
        lists with the other ambiguous statements. ⚠️ **No count of them is
        written here**: the list above is answers and the one below is a raise,
        and a figure over either is a copy of what the code does.

        ⚠️ **The writer read is the entry's and not the target status's.** § 4.2's
        writer answers who advances *into* a status, which is a different act --
        and the two legitimately differ, a status a deploy writes being sent back
        by the person who ordered the work.
        """
        # Named first, for the reason `advance_to` names it: an operation the
        # surface has renamed must stop the role rather than have it report a
        # move against an operation that no longer exists.
        self._stated("set_state")
        entries = [
            entry
            for entry in (self.config.get(REVERSALS) or [])
            if isinstance(entry, dict) and entry.get("trigger") == trigger
        ]
        if not entries:
            return Outcome(
                "set_state",
                performed=False,
                refused=True,
                trigger=trigger,
                detail=f"Refused: this project rules no reverse edge for "
                f"`{trigger}` (`{REVERSALS}`), so there is no step backwards to "
                "make. § 32 configures a reverse edge and derives none, which is "
                "what keeps a role from stepping an item back on its own "
                "judgement -- and where the move happened outside the procedure "
                "anyway, what the report names is that, never the item's role "
                "being written to match.",
            )
        if len(entries) > 1:
            # ⛔ The reader is where this rule is **stated**, and this is not a
            # second statement of it: the reader refuses a duplicate trigger at
            # load with the entry named, so what reaches here is a `Port` built
            # over a configuration the reader never validated -- the suite below,
            # and a role that composed its own dict. ⚠️ Refused rather than taking
            # the first, which is § 4.2's reason one role answered by two status
            # words has no answer, and the message points at the reader rather
            # than repeating why.
            raise ConfigError(
                REVERSALS,
                f"rules the `{trigger}` trigger {len(entries)} times here, which "
                "the configuration reader refuses at load with the entry named "
                "(§ 32). A configuration that did not go through it has no answer "
                "for this ask, and the first entry is not one.",
            )
        entry = entries[0]
        role = entry.get("to_role")
        status = self._mapped_status(role)
        if status is None:
            # ⚠️ The reader refuses this at load too, and this report does not
            # restate its reason either: a `to_role` no status maps is written in
            # the file, where § 4.2's absent role is met against an item. What is
            # left for this branch is the same unvalidated configuration as above.
            return Outcome(
                "set_state",
                performed=False,
                trigger=trigger,
                to_role=role,
                detail=f"No status here maps the `{role}` role, so the reverse "
                f"edge ruled for `{trigger}` has nowhere to step back to -- which "
                "the configuration reader refuses at load.",
            )
        refusal = self._refused_by_writer(
            entry.get("writer"),
            f"the step back to the `{role}` status (`{status.get('name')}`) on "
            f"`{trigger}`",
            asked_as=as_writer,
            trigger=trigger,
            to_role=role,
        )
        if refusal is not None:
            return refusal
        outcome = self.invoke("set_state", *args, status=status.get("name"), **kwargs)
        # ⛔ Written onto the shared outcome rather than threaded through
        # `invoke`: these two are this method's facts and no other operation has
        # them, and they are **fields** because a batch report naming what
        # stepped back reads them rather than parsing the sentence above.
        outcome.trigger = trigger
        outcome.to_role = role
        return outcome

    # -- § 33's publishing half: the grouping, and the bar its items are held to

    def _valued(self, block: dict, given: tuple, operation: str) -> None:
        """Refuse a publishing ask that handed over no value for the grouping.

        ⛔ **Keyed on § 4.8's `current`, which is the key that is actually
        unanswered.** Without this the ask falls through to `invoke`'s
        argument-count refusal, which names the *operation* and sends a reader to
        the port's contract to find out what a release is missing -- measured on
        a `discoverable` grouping, where both this surface and the deploying role
        say the value is read and nothing reads it.

        ⛔ **And the refusal is the same under either value of that key**, which
        is the honest statement rather than the convenient one: `stated` means
        the value arrives on the invocation, and `discoverable` means a procedure
        reads the tracker's own mark -- which **nothing here does**. So the
        second arm is a stated limit and not a behaviour, and a caller under it
        is told to supply the value rather than left to read an argument list.
        """
        if given:
            return
        # ⛔ Read straight off the block: `Config.grouping` answers with a mapping
        # carrying the name it resolved under, or raises -- so a guard on one of
        # these two reads and not the other would claim a state neither has.
        raise ConfigError(
            f"{config.GROUPING_KEY}.{CURRENT}",
            f"is {block.get(CURRENT)!r} for the `{block.get('name')}` grouping, and "
            f"`{operation}` "
            "was asked for with no value for it. The grouping's own value -- which "
            "release, which time box -- arrives on the invocation of the role that "
            "needs it, and ⛔ nothing here reads the tracker's own mark, so that "
            "holds under either value of this key. Hand the value over.",
        )

    def mark_released(
        self, grouping: str | None = None, *args, as_writer: str = ASKED_AS, **kwargs
    ) -> Outcome:
        """Mark one of § 4.8's groupings released, as a writer (§ 33).

        ⛔ **The writer read is § 4.8's `closed_by` and never § 4.2's.** They are
        two writers on two objects, and a project states them apart: one measured
        release is marked by hand while its items advance programmatically in the
        same pass. A close that read the items' writer would be answering about
        the wrong half, and the independence is the whole reason this is an
        operation of its own rather than part of the advance.

        What comes back is a report rather than an exception wherever the
        configuration is a legitimate one: the configured writer is somebody
        else, which is a refusal naming that writer; the writer is `never`, which
        hands the close to nobody, there being no writer to hand it to; or the
        mark goes through `mark_grouping_released` and its capability decides --
        and ⛔ **the absence there is the measured one**, a tracker with no tool
        for this at all, so § 3's fallback has the run name the step and carry on.

        ⛔ **A project planning in no grouping raises rather than answering**, and
        that is the reader's own refusal passed through: there is no grouping for
        the ask to be about, which is a caller asking the wrong question rather
        than a tracker that cannot answer it. ⚠️ The same is true of a name this
        project does not carry, and of an ask naming none where it carries
        several -- § 4.8 refuses all three where `grouping` is read.
        """
        # Named first, for the reason the two status directions name theirs: an
        # operation the surface has renamed must stop the role rather than have
        # it report a close against an operation that no longer exists.
        self._stated(MARK_RELEASED)
        block = self.config.grouping(grouping)
        name = block.get("name")
        refusal = self._refused_by_writer(
            block.get(CLOSED_BY),
            f"the `{name}` grouping (`{CLOSED_BY}`)",
            asked_as=as_writer,
            operation=MARK_RELEASED,
            grouping=name,
        )
        if refusal is not None:
            return refusal
        # ⛔ After the writer guard and not before it, which is where `invoke`'s
        # own argument refusal already landed: the guard answers about the
        # configuration and comes back as an outcome, while this says the caller
        # is wrong and raises. Ordering it first would turn a project whose
        # grouping nobody may close into a caller error.
        self._valued(block, args, MARK_RELEASED)
        outcome = self.invoke(MARK_RELEASED, *args, grouping=block, **kwargs)
        outcome.grouping = name
        return outcome

    def items_in(self, grouping: str | None = None, *args, **kwargs) -> Outcome:
        """The items the tracker holds in one of § 4.8's groupings (§ 33).

        ⛔ **A read, so no writer is consulted** -- which is why this is a method
        at all rather than a bare `invoke`: what it resolves is the *block*, so
        that an implementation is handed where the grouping is held rather than
        re-reading § 4.8 for itself. ⚠️ The value of the grouping is the
        caller's, by that facet's `current`: discoverable where the tracker marks
        one, and arriving on the role's invocation where a project holds several
        open at once.

        ⛔ **A project planning in no grouping raises**, exactly as the close
        above does and for the same reason: there is no grouping for the ask to
        be about.
        """
        self._stated(GROUPING_ITEMS)
        block = self.config.grouping(grouping)
        self._valued(block, args, GROUPING_ITEMS)
        outcome = self.invoke(GROUPING_ITEMS, *args, grouping=block, **kwargs)
        outcome.grouping = block.get("name")
        return outcome

    def short_of(self, role: str, items: list) -> dict:
        """Which of `items` have not reached a role, in § 4.2's own order (§ 33).

        ⛔ **Here because the mapping is here.** § 4.2 puts role-to-word in the
        port and nowhere else, and this answer needs it in both directions: the
        role the target requires resolved to a word, and each item's own word
        resolved back to a position. A role that compared words for itself would
        be the second reader of `statuses` that section forbids.

        ⛔ **The order is the project's own list order and nothing here reorders
        it.** § 4.2 states the set is ordered for exactly this, so *short of* is
        a position comparison against the configuration as written -- which also
        means a project whose ladder puts a non-advancing role late has answered
        that question for itself.

        ⛔ **Three answers per item and never two.** An item whose word this
        project maps is placed; an item carrying no readable word, or one whose
        word no status maps, is **unanswered** -- never *short* and never
        *satisfied*, by § 2's rule that absence of signal is not an answer. ⚠️ So
        a caller reads `unanswered` as well as `short` before it concludes the
        set is clear: a release held by an item nobody could place reads exactly
        like one held by nothing.

        ⚠️ **No verdict about the target.** What may be invoked is § 33's and the
        role's; what this answers is which items are where.
        """
        self._stated(WROTE_A_STATUS)
        ladder = [
            status
            for status in (self.config.get("statuses") or [])
            if isinstance(status, dict) and status.get("role")
        ]
        status = self._mapped_status(role)
        if status is None:
            # ⛔ The reader refuses a `requires_role` no status maps at load with
            # the key named, so this is the same unvalidated configuration the
            # two status directions report on: a bar no item can ever clear.
            return {
                "role": role,
                "status": None,
                "placed": [],
                "short": [],
                "unanswered": [
                    {**_item_name(item), "word": _item_word(item)} for item in items
                ],
                "detail": f"No status here maps the `{role}` role, so no item can "
                "be placed against it and none is reported as having reached it. "
                "The configuration reader refuses that bar where it is written.",
            }
        order = {entry["name"]: index for index, entry in enumerate(ladder)}
        folded: dict[str, list[str]] = {}
        for word in order:
            folded.setdefault(str(word).casefold(), []).append(word)
        bar = order[status["name"]]
        placed, short, unanswered = [], [], []
        for item in items:
            word = _item_word(item)
            # ⛔ Exact first, then case-insensitively, which is what every
            # implementation's own `set_state` already does with the word this
            # layer hands it -- and a fold matching two of this project's status
            # words is **unanswered** rather than either of them.
            matched = word if word in order else None
            if matched is None and word is not None:
                candidates = folded.get(str(word).casefold(), [])
                matched = candidates[0] if len(candidates) == 1 else None
            named = _item_name(item)
            if matched is None:
                unanswered.append({**named, "word": word})
                continue
            placed.append(
                {**named, "status": matched, "role": ladder[order[matched]]["role"]}
            )
            if order[matched] < bar:
                short.append(placed[-1])
        return {
            "role": role,
            "status": status.get("name"),
            "placed": placed,
            "short": short,
            "unanswered": unanswered,
            "detail": f"{len(short)} of {len(items)} in the set are short of the "
            f"`{role}` role (`{status.get('name')}`), and {len(unanswered)} could "
            "not be placed at all.",
        }

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

    ⛔ **And every fact a refusal or a move *names* is a field too.** § 4.2's
    writer, § 32's trigger and target role and § 33's grouping are what a role
    acts on -- the writer a refusal hands the move to, the items a batch report
    says stepped back, the grouping a release left open -- and a shape that
    carried them only inside `detail` would oblige every reader to parse a
    sentence somebody may reword. ⚠️ **Both directions, which
    is the half that goes missing**: a role named in an advance's prose and left
    null in its field is the same parse one direction over.
    """
    return {
        "port": name,
        "operation": operation,
        "performed": outcome.performed,
        "failed": outcome.failed,
        "refused": outcome.refused,
        "detail": outcome.detail,
        "result": outcome.result,
        "writer": outcome.writer,
        "to_role": outcome.to_role,
        "trigger": outcome.trigger,
        "grouping": outcome.grouping,
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
        # ⛔ Present and null rather than absent: the shape is the same shape, and
        # a refusal that dropped three keys would be the second reader the
        # docstring above forbids. A `ConfigError` names a key and never a writer,
        # a trigger, a role or a grouping, so null is the honest value for each.
        "writer": None,
        "to_role": None,
        "trigger": None,
        "grouping": None,
        "key": error.key,
    }


def load(
    skills_root: str = ".", name: str = TRACKER, *, root: str | None = None, **kwargs
) -> Port:
    """One port over the configuration at `skills_root`, read through #1's reader.

    `name` is the key carrying the kind, which is the port's name (§ 26). It
    defaults to § 3's, that being the port every role but § 9's asks for.

    ⛔ `root` is one of § 1's named code roots, and it exists because a port's
    kind may sit inside a **per-root** block: § 29's does, `host` being one of
    the two blocks § 1 lets a root narrow. A project that states such a kind per
    root has no project-level answer at all -- the reader refuses one, naming the
    roots -- so without this the port was unreachable for exactly the project the
    surface invites to state it that way. ⚠️ A tracker is one per project and its
    port takes no root, which is why this is a parameter rather than a rule.
    """
    configuration = config.load(skills_root, **kwargs)
    return Port(
        configuration if root is None else configuration.root(root), port_spec(name)
    )


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


def _needing_two_arguments() -> str:
    """An available operation of this project's tracker that takes two arguments.

    ⛔ Found rather than named, which is every fixture here's rule: an operation
    spelled out would be this suite naming a capability, and a rename would leave
    the arm asserting about an operation the port no longer states. ⚠️ Raises
    where every available operation takes one argument or none -- there is then
    nothing to ask for short, and an arm built on a fallback would assert
    whatever the fallback happened to be.
    """
    answering = load(config.REPO_ROOT, TRACKER, check_paths=False)
    adapter = answering.adapter
    for name in sorted(answering.stated):
        if adapter is None or not adapter.implements(name):
            continue
        # ⚠️ **Required** and not merely declared: an operation whose second
        # parameter carries a default binds with one argument and goes out to the
        # host, so an arm built on *declared* count asserted a failed call
        # instead of a refusal -- measured, on the first spelling of this helper.
        required = [
            parameter
            for parameter in inspect.signature(adapter.operations[name]).parameters.values()
            if parameter.default is inspect.Parameter.empty
            and parameter.kind
            in (parameter.POSITIONAL_ONLY, parameter.POSITIONAL_OR_KEYWORD)
        ]
        if len(required) > 1:
            return name
    raise ConfigError(
        f"{TRACKER}.operations",
        "no available operation of this project's tracker requires more than one "
        "argument, so the too-few-arguments arm has nothing to ask for and would "
        "assert nothing.",
    )


def _with_statuses(statuses: list[dict]) -> config.Config:
    configuration = _any_example()
    configuration.data["statuses"] = statuses
    return configuration


def _with_reversals(statuses: list[dict], reversals: list[dict]) -> config.Config:
    """A configuration carrying both halves § 32 is read across.

    Both at once because neither half answers alone: a reverse edge names a role
    and the role names a status word, so a fixture setting one of them is a
    fixture whose reversal has nowhere to land.
    """
    configuration = _with_statuses(statuses)
    configuration.data[REVERSALS] = reversals
    return configuration


def _with_grouping(statuses: list[dict], groupings: dict[str, dict]) -> config.Config:
    """A configuration carrying both halves § 33's publishing act is read across.

    Both at once because neither answers alone: the grouping carries the writer
    the close is held to and `statuses` carries the writer its items are held
    to, and the point of the act is that those are two.

    ⛔ **`groupings` is written onto the resolved attribute rather than into the
    raw block.** § 4.8's two forms are resolved at load, so a fixture editing the
    block would be a second resolver of that facet -- which is the drift the
    reader's own resolution exists to prevent, arriving through a test.
    """
    configuration = _with_statuses(statuses)
    configuration.groupings = dict(groupings)
    return configuration


def _refused(call) -> str | None:
    """The key a call refuses on, or None where it returns instead."""
    try:
        call()
    except ConfigError as error:
        return error.key
    return None


def _slug_kinds() -> list[str]:
    """Every kind, of every port, whose spelling is a slug rather than a word.

    ⛔ **The subject of the forbidding sweep below is wider than one port, and the
    test is the spelling.** A kind compounded out of two words is a *name* and is
    the one spelling nobody writes in prose, which is the whole reason
    `names_a_tracker` joins the parts with a separator class. A single-word kind
    is not reachable this way and is deliberately not swept: `file` is in
    `__file__`, in *a file name*, and in half the prose beside this.

    ⚠️ **So this is not the sweep the tracker port gets** — that one is every kind
    that port states, word-shaped ones included, because each of them is a service
    and this file may name none. The two are unioned at the point of use, and
    what each one reaches is stated rather than left to be read off a run.
    """
    with open(config.SURFACE, encoding="utf-8") as handle:
        facts = config.surface_facts(handle.read())
    return sorted(
        kind
        for name in surface_ports(None)
        for kind in facts["enums"].get(name, [])
        if kind != NONE and re.search(r"[-_]", kind)
    )


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
    about all of them. A port-specific one — § 4.2's writer refusal and § 32's
    reverse edge, both of which hang off `set_state` — is guarded by the
    operation it needs being in that port's own list, which is the port's fact
    and not a branch on its name. ⚠️ **No count of those is written here**: the
    guard is what makes one safe, so a figure over them would be a copy that
    goes stale the next time one is added, green.
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

    # § 4.2's writer carried on the ask, in both directions and on both sides.
    # ⛔ The green arm is the one no refusal above reaches: a status a project
    # reserves for the deploy is **writable** by the role that asks as the
    # deploy, and without this arm the whole parameter could be deleted with the
    # refusals still red and this suite still green.
    def _asking(writer: str, as_writer: str) -> Outcome:
        return Port(
            _with_statuses([{"name": "a status", "role": a_role, "writer": writer}]),
            spec,
            adapter=Adapter(
                {"set_state": lambda *a, **k: k.get("status", "<no status>")}
            ),
            stated=stated,
        ).advance_to(a_role, as_writer=as_writer)

    # ⛔ Every member of the askable set, derived from the set rather than
    # written out: a word added to it would otherwise be refused by nothing in
    # the refusing loop below — which is derived as the complement — and asserted
    # by nothing here, so it would be askable with no arm on either side.
    for askable in ASKABLE_AS:
        allowed = _asking(askable, askable)
        check(
            f"an ask made as `{askable}` reaches the status that writer writes",
            allowed.performed and not allowed.refused,
            f"got {str(allowed)!r}",
        )
    as_the_deploy = _asking(DEPLOY, DEPLOY)
    check(
        f"a status written by `{DEPLOY}` is advanced by the role asking as it",
        as_the_deploy.performed and not as_the_deploy.refused,
        f"got {str(as_the_deploy)!r}",
    )
    check(
        "and the implementation is handed the mapped word on that route too",
        as_the_deploy.result == "a status",
        f"the implementation received {as_the_deploy.result!r}",
    )
    # ⛔ Both wrong pairings, because one of them alone would pass a guard that
    # simply stopped reading the writer: the procedure asking for the deploy's
    # status, and the deploy asking for the procedure's.
    for writer, asker in ((DEPLOY, PROCEDURE), (PROCEDURE, DEPLOY)):
        wrong = _asking(writer, asker)
        check(
            f"a status written by `{writer}` is refused an ask made as `{asker}`",
            wrong.refused and wrong.writer == writer and writer in wrong.detail,
            f"got {str(wrong)!r}",
        )
    # ⛔ And `never` is refused whatever a caller claims to be, which is the arm
    # a parameter like this invites getting wrong: it is the writer that is not a
    # party, so there is nobody for a caller to claim to be.
    for asker in ASKABLE_AS:
        claimed = _asking(NEVER, asker)
        check(
            f"a `{NEVER}` status stays refused an ask made as `{asker}`",
            claimed.refused and "no other writer" in claimed.detail,
            f"got {str(claimed)!r}",
        )
    # ⛔ The askable set itself, in both directions — and the refusing direction
    # is what keeps the parameter from inverting the guard: a caller naming a
    # status's own writer would otherwise write that party's status, which is the
    # one thing § 4.2's writer exists to stop. ⚠️ Planted on the status whose
    # writer **matches** what the caller claims, because that is the pairing a
    # guard reading the configuration first would let through.
    for asker in [w for w in config.facts_for("writer") if w not in ASKABLE_AS]:
        claiming = _asking(asker, asker)
        check(
            f"an ask made as `{asker}` is refused whatever the status says",
            claiming.refused
            and not claiming.performed
            and asker in claiming.detail
            and "may ask as" in claiming.detail,
            f"got {str(claiming)!r}",
        )
    # ⛔ The forward direction carries the role as a field too, on every answer it
    # gives. ⚠️ Asserted on the **report** and over all three answers, because the
    # way this fails is one direction being given the fields while the other keeps
    # the role in its prose -- measured exactly that way on § 32's own change.
    for label, outcome in (
        ("a performed advance", advanced),
        (
            "an advance refused by its writer",
            Port(
                _with_statuses([{"name": "a status", "role": a_role, "writer": NEVER}]),
                spec,
                adapter=Adapter(),
                stated=stated,
            ).advance_to(a_role),
        ),
        (
            "an advance to a role no status maps",
            Port(_with_statuses([]), spec, adapter=Adapter(), stated=stated).advance_to(
                another_role
            ),
        ),
    ):
        asked = another_role if "no status maps" in label else a_role
        reported = invocation_report(spec.name, "set_state", outcome)
        check(
            f"{label} reports the role it was about as a field",
            reported["to_role"] == asked,
            f"reported to_role={reported['to_role']!r}, wanted {asked!r}",
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

    # § 32's step backwards, asked for as one. ⚠️ The trigger words are the
    # surface's own, for the reason the role words above are: a literal here is a
    # vocabulary this file would be allowed to disagree with.
    triggers = config.facts_for(f"{REVERSALS}.trigger")
    check(
        f"the surface states the `{REVERSALS}.trigger` set this suite reverts on",
        bool(triggers),
        f"states {triggers!r}",
    )
    a_trigger, another_trigger = (triggers + triggers)[0], (triggers + triggers)[1]
    a_status = {"name": "a status", "role": a_role, "writer": PROCEDURE}
    # ⛔ The first arm, and the one the facet exists for: a project that rules no
    # reverse edge refuses the ask rather than performing it. A `set_state` double
    # that answers is what makes this falsifiable -- if the refusal were dropped,
    # the move would go through and the result would be the status word.
    answering = Adapter({"set_state": lambda *a, **k: k.get("status", "<no status>")})
    unruled = Port(
        _with_reversals([a_status], []), spec, adapter=answering, stated=stated
    ).revert_to(a_trigger)
    check(
        "a step backwards no reverse edge rules is refused, naming the key",
        unruled.refused
        and not unruled.performed
        and REVERSALS in unruled.detail
        and unruled.trigger == a_trigger,
        f"got {str(unruled)!r}",
    )
    check(
        "and the refusal names no writer, there being no edge to have one",
        unruled.writer is None,
        f"named `{unruled.writer}`",
    )
    # ⛔ The entry's writer and not the target status's, which is the one place
    # the two directions differ: the status below is one the procedure may write,
    # so a reverse move reading *its* writer would go through.
    for writer in [w for w in config.facts_for("writer") if w != PROCEDURE]:
        outcome = Port(
            _with_reversals(
                [a_status],
                [{"trigger": a_trigger, "to_role": a_role, "writer": writer}],
            ),
            spec,
            adapter=answering,
            stated=stated,
        ).revert_to(a_trigger)
        check(
            f"a step backwards written by `{writer}` is refused, naming the writer",
            outcome.refused
            and not outcome.performed
            and outcome.writer == writer
            and writer in outcome.detail
            and outcome.to_role == a_role,
            f"got {str(outcome)!r}",
        )
        if writer == NEVER:
            check(
                f"and the `{NEVER}` arm hands the step back to nobody here too",
                "writer to make" not in outcome.detail
                and "no other writer" in outcome.detail,
                f"got {str(outcome)!r}",
            )
    # ⛔ The ask's own writer reaches this direction too, which is § 32's rule
    # that the reverse is checked **exactly** as the forward one is — and without
    # this arm the parameter could be deleted from `revert_to` alone with every
    # refusal above still red.
    reversed_by_the_deploy = Port(
        _with_reversals(
            [a_status],
            [{"trigger": a_trigger, "to_role": a_role, "writer": DEPLOY}],
        ),
        spec,
        adapter=answering,
        stated=stated,
    ).revert_to(a_trigger, as_writer=DEPLOY)
    check(
        f"a step backwards written by `{DEPLOY}` goes through for that asker",
        reversed_by_the_deploy.performed and not reversed_by_the_deploy.refused,
        f"got {str(reversed_by_the_deploy)!r}",
    )
    reverting = Port(
        _with_reversals(
            [a_status],
            [{"trigger": a_trigger, "to_role": a_role, "writer": PROCEDURE}],
        ),
        spec,
        adapter=answering,
        stated=stated,
    )
    stepped = reverting.revert_to(a_trigger)
    check(
        "a step backwards the procedure may write goes through the capability",
        stepped.performed and not stepped.refused,
        f"got {str(stepped)!r}",
    )
    check(
        "and the implementation is handed the status word, through one resolver",
        stepped.result == "a status" and stepped.result != a_role,
        f"the implementation received {stepped.result!r}",
    )
    check(
        "and the outcome carries the trigger and the role as fields, not as prose",
        stepped.trigger == a_trigger and stepped.to_role == a_role,
        f"carries trigger={stepped.trigger!r} to_role={stepped.to_role!r}",
    )
    # ⛔ The configuration is read on every call and never resolved once -- which
    # is § 1's rule that the reader is the one answer and not § 32's about an
    # item's role, a distinction worth keeping because the two are easy to
    # conflate here. A port that cached the edge would answer the second ask from
    # the first ask's configuration, so the fixture is **edited between two calls
    # on one port** and the second answer has to follow the edit. ⚠️ A suite that
    # built a second `Port` would pass with the cache in place, which is why this
    # reuses the instance above.
    reverting.config.data[REVERSALS] = [
        {"trigger": a_trigger, "to_role": a_role, "writer": NEVER}
    ]
    again = reverting.revert_to(a_trigger)
    check(
        "the same port asked twice reads the configuration again, not a cached edge",
        again.refused and again.writer == NEVER,
        f"answered {str(again)!r} after the edge was rewritten under it",
    )
    twice_ruled = _refused(
        lambda: Port(
            _with_reversals(
                [a_status],
                [
                    {"trigger": a_trigger, "to_role": a_role, "writer": PROCEDURE},
                    {"trigger": a_trigger, "to_role": a_role, "writer": NEVER},
                ],
            ),
            spec,
            adapter=Adapter(),
            stated=stated,
        ).revert_to(a_trigger)
    )
    check(
        "one trigger ruled twice is refused, naming the key",
        twice_ruled == REVERSALS,
        f"reported {twice_ruled!r}",
    )
    nowhere = Port(
        _with_reversals(
            [],
            [{"trigger": another_trigger, "to_role": another_role, "writer": PROCEDURE}],
        ),
        spec,
        adapter=answering,
        stated=stated,
    ).revert_to(another_trigger)
    check(
        "a reverse edge to a role no status maps is reported, not performed",
        not nowhere.performed
        and not nowhere.refused
        and another_role in nowhere.detail,
        f"got {str(nowhere)!r}",
    )
    # ⛔ Only the role moves. § 32 states a reverse move does not rewrite the
    # item's own text, and the way that fails is a convenience: a reversal that
    # left a note saying why would make itself a second author of the item. The
    # double below implements the operations that would do it, so the assertion
    # is that they were never reached rather than that they were absent.
    touched: list[str] = []

    def _noting(name):
        def operation(*args, **kwargs):
            touched.append(name)
            return kwargs.get("status", name)

        return operation

    writes = {
        operation: _noting(operation)
        for operation in ("set_state", "comment", "set_labels")
        if operation in stated
    }
    writing = Adapter(writes)
    # ⛔ The double has to implement something besides the move, or the assertion
    # below degrades from *they were never reached* to *they were absent* -- the
    # `if operation in stated` filter is required, `Adapter` refusing an
    # operation the surface does not state, and it is also what would quietly
    # empty this fixture if either of the other two left § 3's table.
    check(
        "the double implements an item-writing operation besides the move itself",
        len(writes) > 1,
        f"implements only {sorted(writes)!r}, so nothing could have been reached",
    )
    only_the_role = Port(
        _with_reversals(
            [a_status],
            [{"trigger": a_trigger, "to_role": a_role, "writer": PROCEDURE}],
        ),
        spec,
        adapter=writing,
        stated=stated,
    ).revert_to(a_trigger)
    check(
        "a step backwards writes the state and nothing else on the item",
        only_the_role.performed and touched == ["set_state"],
        f"the implementation was asked for {touched!r}",
    )
    # ⛔ The fields reach the shape a role actually reads, which is the half the
    # `Outcome` docstring promises and the half that went missing: a role handed
    # only `detail` has to parse the sentence that docstring forbids parsing.
    # ⚠️ Asserted on the report rather than on the outcome, the outcome's own
    # fields being asserted three arms up.
    stepped_report = invocation_report(spec.name, "set_state", stepped)
    check(
        "and a role reads the trigger and the role off the report, not out of the prose",
        stepped_report["trigger"] == a_trigger and stepped_report["to_role"] == a_role,
        f"reported {stepped_report!r}",
    )
    refused_report = invocation_report(
        spec.name,
        "set_state",
        Port(
            _with_reversals(
                [a_status],
                [{"trigger": a_trigger, "to_role": a_role, "writer": NEVER}],
            ),
            spec,
            adapter=answering,
            stated=stated,
        ).revert_to(a_trigger),
    )
    check(
        "and reads the refusing writer off it too, which § 4.2 says the refusal names",
        refused_report["writer"] == NEVER and refused_report["trigger"] == a_trigger,
        f"reported {refused_report!r}",
    )
    # ⛔ The operation is named before anything is resolved, in both directions,
    # and ⚠️ **the fixture has to take a path that never reaches `invoke`** --
    # which is the whole subtlety and cost one no-op plant to find. `invoke`
    # names the operation itself, so a configuration the procedure may write
    # raises from there whether or not these methods name it first, and an arm built
    # on one passes with the early call deleted. What the early call actually
    # buys is the **returning** paths: a refusal or a report is an `Outcome`
    # naming `set_state`, and without the call a role is handed one about an
    # operation the surface has renamed away.
    without = {
        operation: fallback
        for operation, fallback in stated.items()
        if operation != "set_state"
    }
    # ⚠️ The adapter implements nothing, and it has to: `Port` holds an adapter to
    # the stated list as it is built, so one implementing an operation this
    # fixture has removed is refused before either method is reached.
    # ⛔ Both lists empty, so **every** ask takes a returning path whatever the
    # surface's vocabularies hold: no entry rules any trigger and no status maps
    # any role. ⚠️ Written this way rather than with a second trigger and a
    # second role, which is the shape it had first: those come off the surface's
    # own sets by index, so a surface that ever stated one trigger or one role
    # would hand this fixture the same word twice, the ask would reach `invoke`
    # after all, and the arm would go quietly back to asserting nothing.
    renamed = Port(
        _with_reversals([], []),
        spec,
        adapter=Adapter(),
        stated=without,
    )
    for direction, argument in (("revert_to", a_trigger), ("advance_to", a_role)):
        gone = _refused(lambda: getattr(renamed, direction)(argument))
        check(
            f"`{direction}` names the operation before it reports anything, and stops without it",
            gone == f"{spec.prefix}.operations.set_state",
            f"reported {gone!r}",
        )
    # ⚠️ The two directions over one configuration, which is what *behaves
    # exactly as it did* has to mean: the reverse edge above is ruled, and the
    # advance is unchanged by its being there.
    both = Port(
        _with_reversals(
            [a_status],
            [{"trigger": a_trigger, "to_role": a_role, "writer": NEVER}],
        ),
        spec,
        adapter=answering,
        stated=stated,
    )
    check(
        "an advance is unaffected by a reverse edge being ruled beside it",
        both.advance_to(a_role).performed,
        f"got {str(both.advance_to(a_role))!r}",
    )

    # § 33's publishing half: the grouping marked, and the bar its items are held
    # to. ⚠️ Every word here comes off the surface's own sets for the reason the
    # two blocks above take theirs there.
    a_grouping = "a-grouping"
    marking = Adapter(
        {MARK_RELEASED: lambda *a, **k: (k.get("grouping") or {}).get("name")}
    )
    # ⛔ The writer read is § 4.8's `closed_by` and never the status's, and this is
    # the arm that proves it: the status below is one the deploy may write, so a
    # close reading *its* writer would go through every refusal in this loop.
    for writer in [w for w in config.facts_for("writer") if w != DEPLOY]:
        outcome = Port(
            _with_grouping(
                [{"name": "a status", "role": a_role, "writer": DEPLOY}],
                {a_grouping: {CLOSED_BY: writer}},
            ),
            spec,
            adapter=marking,
            stated=stated,
        ).mark_released(a_grouping, as_writer=DEPLOY)
        check(
            f"a grouping closed by `{writer}` is refused, naming the writer",
            outcome.refused
            and not outcome.performed
            and outcome.writer == writer
            and writer in outcome.detail
            and outcome.grouping == a_grouping,
            f"got {str(outcome)!r}",
        )
        check(
            f"and the refusal is reported against `{MARK_RELEASED}`, not the status write",
            outcome.operation == MARK_RELEASED,
            f"reported against {outcome.operation!r}",
        )
        if writer == NEVER:
            check(
                f"and the `{NEVER}` arm hands the close to nobody",
                "writer to make" not in outcome.detail
                and "no other writer" in outcome.detail,
                f"got {str(outcome)!r}",
            )
    # ⛔ The two writers honoured **independently**, which is the whole reason this
    # is an operation of its own: one measured release is marked by hand while its
    # items advance programmatically, in the same pass. ⚠️ A single arm asserting
    # both halves, because the failure is them sharing an answer -- a port reading
    # one writer for both would be green on either half alone.
    split = Port(
        _with_grouping(
            [{"name": "a status", "role": a_role, "writer": DEPLOY}],
            {a_grouping: {CLOSED_BY: NEVER}},
        ),
        spec,
        adapter=Adapter(
            {
                MARK_RELEASED: lambda *a, **k: "marked",
                "set_state": lambda *a, **k: k.get("status", "<no status>"),
            }
        ),
        stated=stated,
    )
    closed = split.mark_released(a_grouping, as_writer=DEPLOY)
    advanced = split.advance_to(a_role, as_writer=DEPLOY)
    check(
        "a grouping nobody may close beside items the deploy may advance: the close "
        "refuses and the advance goes through",
        closed.refused
        and not closed.performed
        and advanced.performed
        and not advanced.refused,
        f"close {str(closed)!r}, advance {str(advanced)!r}",
    )
    # ⛔ And the close that is allowed is handed the resolved block, which is what
    # keeps an implementation from re-reading § 4.8 for itself.
    allowed = Port(
        _with_grouping(
            [{"name": "a status", "role": a_role, "writer": DEPLOY}],
            {a_grouping: {CLOSED_BY: DEPLOY, "carrier": "label"}},
        ),
        spec,
        adapter=marking,
        stated=stated,
    ).mark_released(a_grouping, "a value", as_writer=DEPLOY)
    check(
        f"a grouping closed by `{DEPLOY}` goes through, and the block reaches the "
        "implementation",
        allowed.performed and allowed.result == a_grouping,
        f"got {str(allowed)!r}, the implementation received {allowed.result!r}",
    )
    # ⛔ The shared guard reaches this direction too: a caller asking as a party
    # this procedure is not is refused before the configured writer is read, so the
    # close cannot be had by naming its own writer.
    claimed = Port(
        _with_grouping(
            [{"name": "a status", "role": a_role, "writer": DEPLOY}],
            {a_grouping: {CLOSED_BY: "orderer"}},
        ),
        spec,
        adapter=marking,
        stated=stated,
    ).mark_released(a_grouping, as_writer="orderer")
    check(
        "a close asked for as a writer this procedure is not is refused for the ask",
        claimed.refused and "may ask as" in claimed.detail,
        f"got {str(claimed)!r}",
    )
    # ⛔ The capability absence, which is the measured one for this operation: a
    # tracker with no tool for it at all. ⚠️ Not refused and not failed -- the
    # stated fallback is what comes back, and § 33 has the run carry on.
    unmarkable = Port(
        _with_grouping(
            [{"name": "a status", "role": a_role, "writer": DEPLOY}],
            {a_grouping: {CLOSED_BY: DEPLOY}},
        ),
        spec,
        adapter=Adapter(),
        stated=stated,
    ).mark_released(a_grouping, "a value", as_writer=DEPLOY)
    check(
        "a tracker with no tool for marking a release comes back with the fallback",
        not unmarkable.performed
        and not unmarkable.refused
        and not unmarkable.failed
        and unmarkable.detail == stated[MARK_RELEASED],
        f"got {str(unmarkable)!r}",
    )
    # ⛔ A publishing ask handed no value for the grouping is refused against
    # § 4.8's `current`, which is the key that is actually unanswered. ⚠️ The arm
    # that matters is `discoverable`: both this surface and the deploying role
    # describe that value as read, nothing reads it, and without this refusal the
    # ask fell through to the argument-count one -- which names the operation and
    # sends a reader to the port's contract to find out what a release is missing.
    currents = config.facts_for(f"{config.GROUPING_KEY}.{CURRENT}")
    check(
        f"the surface states the `{config.GROUPING_KEY}.{CURRENT}` set these arms read",
        bool(currents),
        f"states {currents!r}",
    )
    a_current = currents[0] if currents else None
    for current in currents:
        valueless = _refused(
            lambda current=current: Port(
                _with_grouping(
                    [{"name": "a status", "role": a_role, "writer": DEPLOY}],
                    {a_grouping: {CLOSED_BY: DEPLOY, CURRENT: current}},
                ),
                spec,
                adapter=marking,
                stated=stated,
            ).mark_released(a_grouping, as_writer=DEPLOY)
        )
        check(
            f"a close on a `{current}` grouping with no value is refused, naming that key",
            valueless == f"{config.GROUPING_KEY}.{CURRENT}",
            f"reported {valueless!r}",
        )
    # ⛔ And the green side, which the refusal above cannot assert: a value handed
    # over reaches the implementation. Without it the refusal could be refusing
    # every ask and read as correct.
    valued = Port(
        _with_grouping(
            [{"name": "a status", "role": a_role, "writer": DEPLOY}],
            # ⚠️ The word is the surface's own, as the loop above takes its own:
            # a literal here would go on passing after a rename, the fixture's
            # value being validated by nothing.
            {a_grouping: {CLOSED_BY: DEPLOY, CURRENT: a_current}},
        ),
        spec,
        adapter=marking,
        stated=stated,
    ).mark_released(a_grouping, "a value", as_writer=DEPLOY)
    check(
        "and a close carrying the grouping's own value goes through",
        valued.performed and valued.result == a_grouping,
        f"got {str(valued)!r}",
    )
    # ⛔ A project planning in no grouping raises rather than answering, in both
    # publishing directions: there is no grouping for either ask to be about, and
    # an answer would be this layer choosing one.
    none_planned = _with_grouping(
        [{"name": "a status", "role": a_role, "writer": DEPLOY}], {}
    )
    for direction in ("mark_released", "items_in"):
        nothing = _refused(
            lambda: getattr(
                Port(none_planned, spec, adapter=marking, stated=stated), direction
            )(a_grouping)
        )
        check(
            f"`{direction}` on a project planning in no grouping is refused, naming the key",
            nothing == f"{config.GROUPING_KEY}.carrier",
            f"reported {nothing!r}",
        )
    # ⛔ An unread grouping is not an empty one, which is the distinction the
    # precondition rests on: the set comes back empty either way and the outcome
    # is what says which, so a caller reading the length alone would publish a
    # release it never checked.
    unreadable = Port(
        _with_grouping(
            [{"name": "a status", "role": a_role, "writer": DEPLOY}],
            {a_grouping: {CLOSED_BY: DEPLOY}},
        ),
        spec,
        adapter=Adapter(),
        stated=stated,
    ).items_in(a_grouping, "a value")
    readable = Port(
        _with_grouping(
            [{"name": "a status", "role": a_role, "writer": DEPLOY}],
            {a_grouping: {CLOSED_BY: DEPLOY}},
        ),
        spec,
        adapter=Adapter({GROUPING_ITEMS: lambda *a, **k: {"items": []}}),
        stated=stated,
    ).items_in(a_grouping, "a value")
    check(
        "a grouping nothing could read and a grouping holding nothing give the same "
        "set and different outcomes",
        _set_from(unreadable) == _set_from(readable) == []
        and not unreadable.performed
        and readable.performed,
        f"unread {str(unreadable)!r}, empty {str(readable)!r}",
    )

    # ⛔ The reported set is identities and never whole items, which is what keeps
    # a release's own batch out of the window the reply is written in.
    check(
        "an item reaches a report by identity rather than whole",
        _item_name({"number": 7, "title": "a title", "body": "a body"})
        == {"item": 7, "title": "a title"},
        f"named {_item_name({'number': 7, 'title': 'a title', 'body': 'a body'})!r}",
    )

    # § 33's precondition, which is the one answer here that is not an `Outcome`.
    ladder = [
        {"name": "first", "role": a_role, "writer": PROCEDURE},
        {"name": "second", "role": another_role, "writer": DEPLOY},
    ]
    placing = Port(_with_statuses(ladder), spec, adapter=Adapter(), stated=stated)
    verdict = placing.short_of(
        another_role,
        [
            {"number": 1, "status": "first"},
            {"number": 2, "status": "second"},
            {"number": 3, "status": "FIRST"},
            {"number": 4, "status": "a word nothing maps"},
            {"number": 5},
        ],
    )
    # ⛔ **Every** item short, and not the first: § 33 states the refusal names
    # them all, the answer a person needs being what the release waits on.
    check(
        "the precondition names every item short of the role, not the first",
        [entry.get("item") for entry in verdict["short"]] == [1, 3],
        f"named {verdict['short']!r}",
    )
    check(
        "an item already at or past the role is not short of it",
        all(entry.get("item") != 2 for entry in verdict["short"]),
        f"named {verdict['short']!r}",
    )
    # ⛔ Three answers and never two: a word no status maps, and an item carrying
    # no readable word at all, are **unanswered** rather than either of the other
    # two -- a release held by an item nobody could place reads exactly like one
    # held by nothing.
    check(
        "an item whose word no status maps is unanswered, never short and never clear",
        sorted(str(entry.get("item")) for entry in verdict["unanswered"]) == ["4", "5"],
        f"named {verdict['unanswered']!r}",
    )
    check(
        "and the placement is case-insensitive, as every implementation's own write is",
        any(
            entry.get("item") == 3 and entry.get("status") == "first"
            for entry in verdict["placed"]
        ),
        f"placed {verdict['placed']!r}",
    )
    # ⛔ A bar no status maps places nothing and reports nothing as having cleared
    # it, which is the configuration the reader refuses at load.
    barless = Port(
        _with_statuses([ladder[0]]), spec, adapter=Adapter(), stated=stated
    ).short_of(another_role, [{"number": 1, "status": "first"}])
    check(
        "a precondition naming a role no status maps clears nothing and places nothing",
        barless["status"] is None
        and not barless["short"]
        and not barless["placed"]
        and len(barless["unanswered"]) == 1,
        f"answered {barless!r}",
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
    # ⛔ And the slug-shaped kinds of **every** port, which is the other half of
    # the subject the sweep below has. Asserted non-empty for the same reason:
    # with nothing in it the sweep holds nothing while reporting green.
    slugs = _slug_kinds()
    check("the surface states a slug-shaped kind to sweep for", bool(slugs))
    swept = sorted(set(kinds) | set(slugs))
    # ⛔ And the plants for the new half come off a kind the old half does **not**
    # already reach. Measured: `slugs` is sorted and its first member is a
    # *tracker* kind, so the second half's evidence was taken off a subject the
    # first half had covered since before this port existed -- which is the
    # failure the comment beside the plants names, produced by the plants
    # themselves.
    others = [kind for kind in slugs if kind not in set(kinds)]
    check(
        "a slug-shaped kind of some port other than the tracker is stated",
        bool(others),
        f"slug-shaped {slugs!r} against tracker {kinds!r}",
    )

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
    # The sentinels this module spells out, held to the surface so that renaming
    # one there reddens the build instead of silently turning a refusal into the
    # wrong words. ⛔ `deploy` is here for the same reason and not because it is
    # a third of the same kind: it is the one writer **besides** the procedure
    # that a role in this procedure asks as, so a rename on the surface would
    # leave the deploying role asking as a writer no project can configure and
    # being refused on every item.
    for sentinel in (PROCEDURE, NEVER, DEPLOY):
        check(
            f"the surface still states `{sentinel}` in its `writer` set",
            sentinel in config.facts_for("writer"),
            f"states {config.facts_for('writer')!r}",
        )
    # § 32's key, held the same way and for the same reason: a refusal above
    # tells somebody which key to edit, and a key the surface has renamed sends
    # them to one that is not there. ⚠️ **Through `surface_facts` and not
    # `facts_for`**, which is the sibling above's idiom and reaches `enums`
    # alone -- a `# required` marker is not an alternation, so there is nothing
    # to read it through. ⛔ And over the text this function already holds rather
    # than opening the surface a third time.
    declared = config.surface_facts(surface_text)["required"]
    check(
        f"the surface still declares `{REVERSALS}` as a required key",
        REVERSALS in declared,
        f"declares {sorted(declared)!r}",
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

    # ⛔ The contract names **nothing behind any port**, in either spelling. This
    # is the mechanical half of "no shared procedure contains a kind-specific
    # branch": a carrier root is swept by the gate in `tools/`, and `scripts/`
    # sits outside that sweep's strict set, so the contract holds itself here --
    # and to the same grammar, because a slug is the one spelling nobody writes
    # in prose. The planted violations below are what show it can fail at all.
    #
    # ⚠️ **The subject is the union above and not the tracker's kinds alone**, and
    # which half reaches which kind is `_slug_kinds`'s docstring: every tracker
    # kind, plus every slug-shaped kind of every other port. ⛔ A word-shaped kind
    # of another port is **not** held here, which is stated rather than left to be
    # discovered -- `file` cannot be forbidden in a file about files.
    with open(os.path.abspath(__file__), encoding="utf-8") as handle:
        source = handle.read()
    check(
        "the contract itself names nothing behind a port the surface declares",
        not names_a_tracker(source, swept),
        f"names {names_a_tracker(source, swept)!r}",
    )
    # ⛔ One planted spelling set per half, so neither half can be the only one
    # the evidence covers: a sweep extended to a second port with its plant taken
    # off the first port's kind would report green over a subject it never read.
    for label, pool in (("tracker", kinds), ("non-tracker slug-shaped", others)):
        if not pool:
            continue
        for spelling in (pool[0], pool[0].replace("-", " ").title(), pool[0].upper()):
            planted = source + f"\n# a branch on {spelling} would go here\n"
            check(
                f"a {label} kind named as `{spelling}` reddens that check",
                names_a_tracker(planted, swept) == [pool[0]],
                f"reported {names_a_tracker(planted, swept)!r}",
            )

    # ⛔ *Three answers, never a traceback* held on the path a role actually
    # uses, which is this file run as a **script**. Every assertion above runs
    # in-process, where `HostUnavailable` is one class -- and that is exactly why
    # none of them could see the defect this case exists for: run as a script
    # this file is loaded twice, once as `__main__` and once as `port` under the
    # implementations' own import, so the two classes were unrelated and
    # `invoke`'s `except` caught nothing.
    #
    # ⛔ **Two arms, because the end-to-end one cannot be the only one.** What it
    # provokes is a *failed* call, and only an implementation that reaches its
    # host through a client on the path can be made to fail with no host — so on
    # a project whose kind speaks its own transport the provocation lands on a
    # different arm, and a case that insisted would redden in an adopter's tree
    # for a reason that is not the defect. The first arm below holds the dispatch
    # whatever the kind; the second is the evidence where it can be had, and says
    # so when it cannot.
    #
    # ⚠️ **The first is a forbidding check on this file's own entry point**, which
    # is the shape the tracker-name check above already takes against this same
    # source. It is weaker than running the thing, and it is the arm that cannot
    # be absent.
    entry = source.rsplit('if __name__ == "__main__":', 1)
    check(
        "this file's entry point dispatches through its own module name",
        len(entry) == 2 and re.search(r"import\s+port\s+as\s+\w+", entry[1])
        and not re.search(r"(?<![\w.])main\(sys\.argv", entry[1]),
        f"the entry point reads {entry[-1].strip()[:120]!r}",
    )

    # ⚠️ **A subprocess, because the fault only exists in one**, which is the
    # shape `docs/single-source-of-truth.md` records as the plant that cannot be
    # in-suite.
    #
    # ⛔ **The child is handed a minimal environment rather than this one with the
    # path emptied**, and that is not tidiness: an implementation speaking its own
    # transport does not need a client at all, so a child inheriting this shell
    # could carry a credential and make a **live call out of a self-test** the
    # host runs with no credential precisely to prevent it. What is passed is what
    # the configuration reader needs to resolve a project and nothing else, so
    # *no host and no credential* is a property of the call rather than a claim in
    # a comment.
    own = os.path.join(config.REPO_ROOT, config.CONFIG_PATH)
    if os.path.exists(own) and TRACKER in specs:
        bare = {
            name: os.environ[name]
            for name in ("HOME", "TMPDIR", "LANG", "LC_ALL")
            if name in os.environ
        }
        try:
            run = subprocess.run(
                [
                    sys.executable, os.path.abspath(__file__),
                    "--skills-root", config.REPO_ROOT,
                    "--invoke", "read_item", "--argument", "1",
                ],
                capture_output=True, text=True, env=dict(bare, PATH=""), timeout=60,
            )
        except subprocess.TimeoutExpired:
            # ⛔ Reported rather than raised. A transport that hangs would
            # otherwise kill the run with a traceback where a verdict belongs,
            # which is the defect one layer up from the one this case is about.
            run = None
            check(
                "the script answered at all, rather than hanging",
                False,
                "the child did not return within its bound, so the end-to-end arm "
                "could not be read",
            )
        if run is not None:
            # ⚠️ Read off stdout rather than off the exit status: a failed outcome
            # and a traceback both exit non-zero, so the status cannot tell them
            # apart and asserting on it would have passed before the fix.
            try:
                reported = json.loads(run.stdout)
            except ValueError:
                reported = None
            # ⛔ The traceback arm holds whatever the child answered, because it
            # is the one that is kind-independent: a refusal, a fallback and a
            # failure are all outcomes, and none of them is a traceback.
            check(
                "run as a script, no traceback reaches the person running it",
                "Traceback (most recent call last)" not in run.stderr,
                f"stderr carried {run.stderr.strip()[:200]!r}",
            )
            if isinstance(reported, dict) and reported.get("failed") is True:
                check(
                    "and a call that could not go out came back as a failed outcome",
                    True,
                )
            else:
                # ⛔ Named as unprovoked rather than passed or failed, which is
                # § 11's rule about what a report could not establish: this
                # project's configured kind could not be made to fail without a
                # host, so the end-to-end half of the dispatch is unheld here and
                # the arm above is what holds it.
                print(
                    "  --    the failed-call arm is UNPROVOKED under this project's "
                    f"kind: the child answered {str(reported)[:90]!r}, which is an "
                    "outcome and not a failure"
                )

        # ⛔ The two halves of the status-move route, asserted through the script
        # rather than through the methods above: the guard § 4.2 states lives
        # inside `advance_to`, so what has to be held is that **no invocation
        # reaches the implementation around it**. ⚠️ The refusal is the arm that
        # matters -- without it the flag beside it is a second route rather than
        # the only one, and both would read green.
        def _ran(*flags: str) -> subprocess.CompletedProcess:
            return subprocess.run(
                [
                    sys.executable, os.path.abspath(__file__),
                    "--skills-root", config.REPO_ROOT, *flags,
                ],
                capture_output=True, text=True, env=dict(bare, PATH=""), timeout=60,
            )

        try:
            named = _ran("--invoke", "set_state", "--argument", "1")
            by_role = _ran("--advance-to", "initial", "--argument", "1")
            # ⛔ The reverse direction's own route, which had no invocation at
            # all until § 39's role came to ask for one. ⚠️ This project rules
            # `reversals: []`, so what is asserted is that the ask **reaches the
            # facet and is refused by it** -- never that a move was made, which
            # would be an assertion about a configuration this arm must not
            # depend on.
            by_trigger = _ran(
                "--revert-on", "acceptance_rejected", "--argument", "1"
            )
            both_ways = _ran(
                "--advance-to", "initial",
                "--revert-on", "acceptance_rejected",
                "--argument", "1",
            )
            # ⛔ An operation asked for with arguments it does not take, which
            # was a traceback out of `invoke` until the arm below was written.
            # ⚠️ The operation is read off this port's own report rather than
            # named, so the arm survives a renamed capability: what is wanted is
            # any available operation taking more than one argument.
            short = _ran("--invoke", _needing_two_arguments(), "--argument", "1")
        except subprocess.TimeoutExpired:
            check(
                "the status-move route answered at all, rather than hanging",
                False,
                "a child did not return within its bound",
            )
        else:
            check(
                "naming `set_state` on the invocation is refused, pointing at the role",
                named.returncode == 2 and "--advance-to" in named.stderr,
                f"exited {named.returncode} saying {named.stderr.strip()[:160]!r}",
            )
            check(
                "and the refusal says why rather than only that it refused",
                "writer guard" in named.stderr,
                f"said {named.stderr.strip()[:160]!r}",
            )
            # ⚠️ Asserted on the answer's shape and not on the move going
            # through: whether this project maps the role, and whether its host
            # is reachable, are facts about the configuration this arm must not
            # depend on. What is held is that the flag reaches the guarded route
            # and comes back as an outcome.
            try:
                moved = json.loads(by_role.stdout)
            except ValueError:
                moved = None
            check(
                "asking by role reaches the guarded route and answers as an outcome",
                isinstance(moved, dict) and moved.get("operation") == "set_state",
                f"answered {by_role.stdout.strip()[:160]!r}",
            )
            check(
                "and no traceback reaches the person running it either",
                "Traceback (most recent call last)" not in by_role.stderr,
                f"stderr carried {by_role.stderr.strip()[:160]!r}",
            )
            try:
                reverted = json.loads(by_trigger.stdout)
            except ValueError:
                reverted = None
            check(
                "asking by trigger reaches the reverse route and answers as an outcome",
                isinstance(reverted, dict)
                and reverted.get("operation") == "set_state",
                f"answered {by_trigger.stdout.strip()[:160]!r}",
            )
            check(
                "and a project ruling no edge for it is refused with `reversals` named",
                isinstance(reverted, dict)
                and REVERSALS in json.dumps(reverted),
                f"answered {by_trigger.stdout.strip()[:220]!r}",
            )
            check(
                "naming both directions at once is refused rather than ordered",
                both_ways.returncode == 2
                and "--revert-on" in both_ways.stderr,
                f"exited {both_ways.returncode} saying "
                f"{both_ways.stderr.strip()[:160]!r}",
            )
            check(
                "an operation asked for with too few arguments is a refusal, not a "
                "traceback",
                "Traceback (most recent call last)" not in short.stderr
                and "arguments it does not take" in short.stdout,
                f"stderr carried {short.stderr.strip()[:120]!r}, "
                f"stdout {short.stdout.strip()[:160]!r}",
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
        "--root",
        help="which of § 1's named code roots to resolve the kind under, where "
        "this port's kind sits in a block a root may narrow and the project "
        "states it per root. Omitted, the project's own statement answers",
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
        "--advance-to",
        metavar="ROLE",
        help="ask for an advance to one of § 4.2's status **roles**, never to a "
        "status word: the port resolves the role to the word this project mapped "
        "and § 4.2's writer guard decides. ⛔ This is the only route that reaches "
        "that guard -- `--invoke set_state` names the operation underneath it and "
        "is refused for exactly that reason",
    )
    parser.add_argument(
        "--revert-on",
        metavar="TRIGGER",
        help="ask for a step **back**, on one of § 32's triggers. The role it "
        "steps to is the project's own entry and never the caller's, and that "
        "entry's writer guard decides -- checked exactly as the forward one is. "
        "⛔ This is the only route that reaches the reverse edge: `--invoke "
        "set_state` is refused for the same reason it is refused for an advance, "
        "and ⚠️ a project ruling no edge for the trigger refuses the ask with "
        "`reversals` named, which is that facet working rather than an obstacle",
    )
    parser.add_argument(
        "--mark-released",
        metavar="GROUPING",
        nargs="?",
        const="",
        help="ask for one of § 4.8's groupings to be marked released, by the name "
        "that facet keys it on -- omitted where the project carries one. The "
        "writer read is § 4.8's `closed_by` and never a status's, and ⛔ this is "
        "the only route that reaches that guard: `--invoke mark_grouping_released` "
        "names the operation underneath it and is refused for the same reason the "
        "status move's is",
    )
    parser.add_argument(
        "--in-grouping",
        metavar="GROUPING",
        nargs="?",
        const="",
        help="the items the tracker holds in one of § 4.8's groupings, by the name "
        "that facet keys it on -- omitted where the project carries one. The "
        "grouping's own value goes in `--argument` where that facet says `stated`",
    )
    parser.add_argument(
        "--short-of",
        metavar="ROLE",
        help="which items in a set have not reached one of § 4.2's **roles**, "
        "which is § 33's precondition on a publishing target. The set is the one "
        "`--in-grouping` names, or the identifiers given with `--argument` read "
        "through `read_item` where no grouping is named -- § 33's two arms. The "
        "answer places every item and names the ones it could not, and it ⛔ "
        "carries no verdict about whether the target may be invoked",
    )
    parser.add_argument(
        "--as-writer",
        metavar="WRITER",
        default=ASKED_AS,
        help="which of § 4.2's writers the ask is made as. Defaults to the "
        "procedure, which is what every role but § 33's deploying one asks as",
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
    # ⛔ The status move is asked for by **role**, through its own flag, and the
    # operation underneath it is refused by name. Without this refusal § 4.2's
    # writer guard is reachable from no invocation and avoidable from every one:
    # `--invoke set_state` goes straight to the implementation with a status word
    # the caller chose, which is the indirection § 3 forbids a role and the guard
    # § 33's advance rests on. ⚠️ It refuses rather than silently rerouting --
    # the two take different arguments, and a reroute would guess which.
    # ⛔ **Both directions, which is why the condition names both flags.** § 32
    # states that the reverse edge is checked exactly as the forward one is, so a
    # refusal that cleared only on `--advance-to` would leave the step back
    # reachable through the operation alone -- the guard avoidable in the one
    # direction whose writer is most often a person.
    if args.invoke == "set_state" and not (args.advance_to or args.revert_on):
        print(
            "Refused: `set_state` is reached through `--advance-to <role>` or "
            "`--revert-on <trigger>`, which resolve § 4.2's role and § 32's edge "
            "to the status word this project mapped and are where the writer "
            "guard sits. Naming the operation instead would write a status word "
            "the caller chose, past the guard.",
            file=sys.stderr,
        )
        return 2
    # ⛔ Neither direction at once. The two name different things -- a role to
    # advance into and a trigger to step back on -- and a call stating both has
    # asked for two moves on one item with nothing saying which happens first.
    if args.advance_to and args.revert_on:
        print(
            "Refused: `--advance-to` and `--revert-on` are two moves on one item "
            "and the order between them is stated nowhere. Ask for one.",
            file=sys.stderr,
        )
        return 2
    # ⛔ The same refusal for the grouping close, and for the same reason one
    # direction over: § 4.8's `closed_by` guard sits inside `--mark-released`, so
    # naming the operation would close a grouping past the one writer check the
    # surface states for it. ⚠️ Independent of the status guard above rather than
    # folded into it -- the two read different keys about different objects, and a
    # single refusal would have had to pick one of them to name.
    if args.invoke == MARK_RELEASED and args.mark_released is None:
        print(
            f"Refused: `{MARK_RELEASED}` is reached through `--mark-released "
            "[<grouping>]`, which reads § 4.8's `closed_by` for that grouping and "
            "is where its writer guard sits. Naming the operation instead would "
            "mark a release past the guard -- and on the one project measured, "
            "past a writer that is a person.",
            file=sys.stderr,
        )
        return 2
    if args.mark_released is not None:
        if args.ports:
            print(
                "Refused: `--mark-released` marks one grouping on one port, so it "
                "is not asked of every port at once.",
                file=sys.stderr,
            )
            return 2
        try:
            answering = load(
                args.skills_root,
                args.port,
                root=args.root,
                check_paths=not args.no_check_paths,
            )
            outcome = answering.mark_released(
                args.mark_released or None,
                *args.argument,
                as_writer=args.as_writer,
            )
        except ConfigError as error:
            print(
                json.dumps(
                    refusal_report(args.port, MARK_RELEASED, error),
                    indent=2,
                    ensure_ascii=False,
                )
            )
            return 1
        print(
            json.dumps(
                invocation_report(answering.name, MARK_RELEASED, outcome),
                indent=2,
                ensure_ascii=False,
                default=str,
            )
        )
        return 0 if outcome.performed else 1

    if args.in_grouping is not None or args.short_of:
        if args.ports:
            print(
                "Refused: the publishing set and the bar it is held to are one "
                "project's on one port, so neither is asked of every port at once.",
                file=sys.stderr,
            )
            return 2
        try:
            answering = load(
                args.skills_root,
                args.port,
                root=args.root,
                check_paths=not args.no_check_paths,
            )
            read_grouping = None
            if args.in_grouping is not None:
                read_grouping = answering.items_in(
                    args.in_grouping or None, *args.argument
                )
                # ⛔ An unread grouping is not an empty one. The capability's own
                # fallback says what happens instead, and the exit status below
                # carries it: a set nobody could read is never a set that cleared
                # a bar (§ 2's absence-of-signal rule, § 3's stated fallback).
                held = _set_from(read_grouping)
            else:
                # ⛔ Each identifier is read through the port's own `read_item`,
                # and an item it could not answer about goes into the set
                # **unread** rather than being dropped: § 33's precondition
                # reports what it could not place, and an item quietly left out
                # would make a held release read as a clear one.
                held = []
                for given in args.argument:
                    read = answering.invoke("read_item", given)
                    held.append(read.result if read.performed else {"unread": given})
            answer = (
                answering.short_of(args.short_of, held) if args.short_of else None
            )
        except ConfigError as error:
            print(
                json.dumps(
                    refusal_report(
                        args.port,
                        WROTE_A_STATUS if args.short_of else GROUPING_ITEMS,
                        error,
                    ),
                    indent=2,
                    ensure_ascii=False,
                )
            )
            return 1
        # ⛔ The set is reported by **identity** and never whole, for `_item_name`'s
        # reason: a release's own batch read through here would otherwise put every
        # item's body into the window the reply is written in. ⚠️ What a role needs
        # off this is which items the grouping holds and where each one stands,
        # both of which the compact form carries.
        reported = {
            "port": answering.name,
            "grouping": (
                {
                    key: value
                    for key, value in invocation_report(
                        answering.name, GROUPING_ITEMS, read_grouping
                    ).items()
                    if key != "result"
                }
                if read_grouping is not None
                else None
            ),
            "set": [_item_name(item) for item in held],
            "short_of": answer,
        }
        print(json.dumps(reported, indent=2, ensure_ascii=False, default=str))
        # ⛔ Nonzero where the grouping could not be read, or where anything is
        # short **or unanswered**: each of the three is a precondition a target
        # has not cleared, and a set nobody could place is not a clear one.
        if read_grouping is not None and not read_grouping.performed:
            return 1
        if answer is None:
            return 0
        return 0 if not (answer["short"] or answer["unanswered"]) else 1
    if args.advance_to or args.revert_on:
        if args.ports:
            print(
                "Refused: a status move touches one item on one port, so it is "
                "not asked of every port at once.",
                file=sys.stderr,
            )
            return 2
        try:
            answering = load(
                args.skills_root,
                args.port,
                root=args.root,
                check_paths=not args.no_check_paths,
            )
            # ⛔ One shared branch for the two directions, which is § 32's rule
            # read as code: the reports, the exit status and the refusal handling
            # are the same because a reverse move reported differently from a
            # forward one is a move a reader weighs differently.
            outcome = (
                answering.revert_to(
                    args.revert_on, *args.argument, as_writer=args.as_writer
                )
                if args.revert_on
                else answering.advance_to(
                    args.advance_to, *args.argument, as_writer=args.as_writer
                )
            )
        except ConfigError as error:
            print(
                json.dumps(
                    refusal_report(args.port, "set_state", error),
                    indent=2,
                    ensure_ascii=False,
                )
            )
            return 1
        print(
            json.dumps(
                invocation_report(answering.name, "set_state", outcome),
                indent=2,
                ensure_ascii=False,
                default=str,
            )
        )
        return 0 if outcome.performed else 1

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
                args.skills_root,
                args.port,
                root=args.root,
                check_paths=not args.no_check_paths,
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
                args.skills_root,
                args.port,
                root=args.root,
                check_paths=not args.no_check_paths,
            ).to_dict()
    except ConfigError as error:
        print(str(error), file=sys.stderr)
        return 1
    print(json.dumps(out, indent=2, ensure_ascii=False, sort_keys=False))
    return 0


if __name__ == "__main__":
    # ⛔ Dispatched through this file **under its own module name**, never through
    # `__main__`. Every implementation beside it does `import port`, so a run as a
    # script loads this file twice -- once as `__main__` and once as `port` -- and
    # `HostUnavailable` becomes two unrelated classes. `invoke`'s `except` then
    # cannot catch what an adapter raised, and the contract's stated *three
    # answers, never a traceback* stops holding on the one path a role actually
    # uses.
    #
    # ⚠️ Measured rather than reasoned about: `--invoke read_item` against a pull
    # request number came back as a traceback from the pull-request guard, where
    # the guard's own message belongs in a `failed` outcome. ⛔ And the suite
    # could not see it, because a suite imports this file as a module and the two
    # classes are one there -- which is why the dispatch is the fix rather than a
    # wider `except`.
    import port as _itself

    sys.exit(_itself.main(sys.argv[1:]))
