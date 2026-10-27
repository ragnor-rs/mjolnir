#!/usr/bin/env python3
"""The configuration reader every role runs on.

A project states its facts once, in `.claude/mjolnir.yaml` relative to its
**skills root**, and a copy of the surface -- `config/schema.md`, beside this
script or in the skills root that ships it, which `surface_for` decides -- is the
single statement of what those facts are. This module is the one piece of code
that turns that file into values a role can act on: it resolves the path, applies
the surface's defaults, and refuses a configuration the surface does not allow,
naming the key so the person reading the failure knows what to write.

Three things it deliberately does not do:

  * **It carries no default and no closed set of its own.** Every default is
    read at run time from the `# default` marker on a key's line in the
    surface's fenced blocks, and every closed set of values -- status roles,
    status writers, readiness checks, each `carrier`, and every other
    alternation the surface states -- is read from the same blocks and enforced
    at the key that states it. A value restated here would be a second
    statement of one fact, which is the defect this toolkit exists to delete
    rather than a maintenance burden to absorb. Adding a status role to the
    surface therefore changes what this reader accepts without changing this
    reader.

    ⚠️ It does carry *sentinels* -- `none` for an absent carrier or tracker,
    `never` for a writer the procedure may not use, and the two § 13 members a
    rule is written against: `local`, the check whose source is § 17's facet,
    and `procedure`, the answerer a command is run by. Each is a member of a set
    the surface states, and which member a rule turns on is the part an alternation
    cannot say. No count of them is given here -- the first form of this
    sentence said *four* and was stale the moment § 13 added two. Every one is
    held to the surface by the self-test rather than by inspection, so renaming
    one there reddens the build instead of silently turning off the rule that
    depends on it.
  * **It infers no root.** `roots.code` is read, never derived from the working
    directory or from `git rev-parse` -- both would do something plausible first
    and be wrong wherever the two roots differ.

    ⚠️ And **it picks no root** where § 1's collection states several. One view
    per root is resolved and validated as a configuration of one repository; a
    project-level read of a fact some root states for itself is refused with the
    roots named, rather than answered from the first of them. Which root a work
    item belongs to is stated nowhere on the surface yet, so the key reaching
    `root()` comes from a person or an invocation.

    ⚠️ The **skills root** is the one root no configuration can state, because it
    is where the configuration is found. The surface rules it the directory the
    role was invoked in, which is this reader's default, and `--skills-root` is
    how a role addresses a project it is not standing in. That is a definition
    rather than an inference -- the test the surface states is whether a project
    could have written the value down -- and because it cannot be checked, every
    resolution reports what § 1 requires a role to name before it acts. Which
    items those are is § 1's list, not a second one here.
  * **It does not decide what a role then does.** It reports what a
    configuration cannot support; acting on that is the role's business.

**Absence is a configuration, not a gap.** `tracker.kind: none`, an empty
`statuses` list, an empty `readiness` list, an empty `done` list,
`host.checks: []`, `checks_local: []`, and a facet whose `carrier` is `none`
with a stated `absent_reason` all load silently and are not misconfigurations.
An *unset* carrier is. `unavailable()` is how a role says what it cannot do
without any of those reading as a broken install.

Usage:
    config.py [--skills-root DIR]   print the resolved configuration as JSON
    config.py --self-test           hold this reader to the surface and the
                                    examples, then print what it found
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys


def _yaml():
    """PyYAML, or a stop naming the install that is missing.

    ⛔ Reached through here rather than imported at module load, because one
    question this module answers needs no parser at all: whether a project
    states a configuration is a path, and it is what every hook carrier asks
    before it does anything. A missing library stopping the interpreter as this
    module is imported would make a carrier fall silent in a project that *is*
    configured -- the one answer that rule may never produce -- so the stop
    happens where a parse is actually needed.
    """
    try:
        import yaml  # noqa: PLC0415 -- deliberately not at module load; see above
    except ModuleNotFoundError:  # pragma: no cover - environment, not logic
        sys.exit(
            "config.py needs PyYAML to read a project's configuration.\n"
            "Install it with: python3 -m pip install pyyaml"
        )
    return yaml


# --- where things are ------------------------------------------------------
#
# Paths relative to this file, never to the working directory. A role invokes
# this script by the absolute path the harness substitutes for
# ${CLAUDE_PLUGIN_ROOT}, and the shell it runs in may be anywhere.

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SURFACE = os.path.join(PLUGIN_ROOT, "config", "schema.md")
EXAMPLES = os.path.join(PLUGIN_ROOT, "config", "examples")

# The tree the plugin sits in. Where the plugin is installed into a project
# that is itself configured -- this toolkit building itself is the case that
# matters -- the self-test holds that configuration too. An adopter who
# installs the plugin from elsewhere simply has no file here, and the check is
# skipped rather than failed.
REPO_ROOT = os.path.dirname(os.path.dirname(PLUGIN_ROOT))

# Where the plugin sits inside the tree that carries it, derived from where this
# file actually is rather than stated. It is how `surface_for` below asks whether
# a skills root carries a surface of its own, and deriving it is what keeps the
# marketplace's own layout a single statement: the source path is declared once,
# in the marketplace manifest, and a copy of it here would be a second.
PLUGIN_IN_REPO = os.path.relpath(PLUGIN_ROOT, REPO_ROOT)

# Where a project's own configuration sits under its skills root. Stated once
# here because the surface states it in prose rather than as a key: a project
# does not get to move it, or a role would have to be told where to look.
CONFIG_PATH = os.path.join(".claude", "mjolnir.yaml")

# The markers that make the surface machine-readable. These are read as one
# semicolon-separated clause of a key's trailing comment; every clause of a
# comment is scanned, not just the last one, so a key that states prose and a
# marker together -- `# stated, never inherited; required` -- carries both.
#
# ⚠️ Two markers are not of that shape, being comment lines of their own for the
# same reason -- the key they name has no line left to hang a clause on, or never
# had one. `RETIRED_CLAUSE` is declared with the reader that uses it; the
# procedure-only pair is here, because `surface_facts` below is what reads it.
#
# `# procedure: <key>` is the clause the surface states under § The file itself,
# which says what it means and why it names a bare key; this reader performs it.
# ⛔ No list of those keys lives in this module: the clause is the statement, so
# a rule that becomes procedure is one marker on the surface and no edit here --
# the division every other marker has, and the one the retired `REQUIRED` table
# lost by keeping a copy.
PROCEDURE_CLAUSE = re.compile(r"^#\s*procedure\s*:\s*(?P<key>[A-Za-z_][\w-]*)$")

# ⛔ And a clause that means to be that marker and does not parse is refused
# rather than dropped: a mistyped clause leaves the surface reading as refusing
# a key and this reader refusing nothing, green. ⚠️ The retirement class is not
# that exposed -- a mistyped `# retired:` clause for a key already in `RETIRED`
# reddens the set arms below -- so the hole is specific to a *newly* marked key
# whose clause is mistyped, which is this class's whole state.
#
# ⛔ The guard is the **complement** of the clause and not a second grammar of
# near misses, because the two spellings that slipped between the first draft's
# pair were the obvious ones: a space before the colon, which the clause rejected
# and the guard exempted, and a capitalised keyword, which neither read. Any
# own-line comment inside a fence opening with the marker word and not parsing is
# refused, case included.
#
# ⚠️ **What that costs is stated rather than discovered**: a fence comment of its
# own whose first word is *procedure* is refused even where it meant to be
# English, and the remedy is to write that sentence in the prose beside the
# block, where every other sentence on this surface already lives. Measured
# before taking it: of the own-line comments inside this surface's fences, every
# one is a marker and none is prose.
PROCEDURE_NEAR_MISS = re.compile(r"^#\s*procedure\b", re.I)
#
# `# default` means the value shown on the line is the default, and
# `# default: <value>` states one the line does not show -- which is how a key
# whose value is an alternation declares which arm of it applies.
DEFAULT_CLAUSE = re.compile(r"^default(?:\s*:\s*(?P<literal>.+))?$")

# `# required` means every project writes the key, and its absence is refused.
# ⛔ Matched as the *bare* clause on purpose. A key whose requiredness depends on
# another key's value says so with the conditional marker below, or -- where the
# refusal carries an argument a marker's message cannot, as §§ 10, 11 and 12's
# each do -- in prose beside the key and in a rule of its own. Either way it is a
# different question from "must this key be written at all" and must not be
# answered by this marker. A key with neither marker is legitimately unset.
REQUIRED_CLAUSE = re.compile(r"^required$")

# `# required_when: <key> = <value>` means the key is required exactly where that
# other key holds that value, and refused as missing only then. It is what a flat
# list of required paths cannot express: § 3's per-kind tracker blocks are each
# required by one `tracker.kind` and meaningless under the others, so a bare
# `# required` would refuse every project on every other tracker, and nothing at
# all is what they did instead -- a block naming a kind and omitting the keys that
# address it loaded clean and failed at the first operation.
#
# ⚠️ Written as a token and not as the English the surface already uses beside
# every `absent_reason` line -- `# required when carrier is none`, prose about a
# rule another marker performs. ⛔ No count of those lines is carried here: the
# first form of this comment said *four*, there were five, and a facet landing
# while the change was open made it six. A grammar matching that English reads
# each of them as a condition on the bare sibling `carrier`, which no dotted path
# from the top of the file resolves. Measured: with the guard below in place every
# example then stops loading, and **with the guard removed the same conditions are
# silently inert** -- which is the worse half and the reason the marker is a token
# rather than the guard being the whole answer.
#
# ⛔ The condition is read, so it cannot be a condition nothing can meet: the
# referenced key must be one the surface declares, and the value one its
# alternation states where it states one. Both are refused below rather than
# skipped, because a marker whose condition never fires is a requirement nobody
# enforces that reads exactly like one somebody does.
#
# ⚠️ Neither guard is sufficient, and the limits are stated rather than implied.
# The value is compared as the **text** the surface states, so a condition on a
# number or a boolean cannot fire; and the surface declares some keys only inside
# a fence that opens at an indent or shows one entry of a list, where no absolute
# path reaches them at all. What catches both is the self-test asserting that each
# marked condition is met by some example -- a condition no example meets is the
# one thing a loader cannot tell from a condition no project happens to meet.
REQUIRED_WHEN_CLAUSE = re.compile(
    r"^required_when\s*:\s*(?P<on>[A-Za-z_][\w.]*)\s*=\s*(?P<value>[\w-]+)$"
)

# ⛔ And a clause that *means* to be the marker and does not parse is refused
# rather than dropped. Measured on this change: `= "trello"` (the value quoted,
# as every other value on this surface is), `== trello`, `= trello.com` and
# `required when: …` each left `re.match` empty, so the surface read as marking a
# key and the reader enforced nothing for it -- and for a key not yet in the
# inventory below, the whole suite stayed green. This is the same refusal
# `# absent_reason` gets when it sits where nothing reads it.
#
# ⚠️ It demands the colon, which is what separates a mistyped marker from the
# English prose above: `required when carrier is none` carries none and must stay
# prose, while `required_when` on its own is a marker whoever wrote it meant.
REQUIRED_WHEN_NEAR_MISS = re.compile(r"^(?:required[_ ]when\s*:|required_when\b)")

# `# absent_reason` beside a `carrier` marks the facet as having a real absent
# case: `carrier: none` is then accepted only with a stated reason, and the
# facet is reported in `unavailable()`. The alternative was a list of such
# facets in this module, which is what left the reader with a second statement
# of which absences are deliberate -- and a sixth facet invisible to both rules.
ABSENT_REASON_CLAUSE = re.compile(r"^absent_reason$")

# A fenced block of the surface, the heading it sits under, and a `key:` line
# inside one. List items are not matched on purpose -- a `- { ... }` line is an
# entry, not a key.
FENCE = re.compile(r"```yaml\n(.*?)```", re.S)
HEADING = re.compile(r"^#{2,}\s+(?P<title>.+?)\s*$")
KEY_LINE = re.compile(r"^(?P<indent>\s*)(?P<key>[A-Za-z_][\w-]*):(?P<rest>.*)$")

# An alternation written as a value or as a trailing comment: `a | b | c`. This
# is how the surface states a closed set of values inline.
ALTERNATION = re.compile(r"^[\w-]+(?:\s*\|\s*[\w-]+)+$")


class ConfigError(Exception):
    """A configuration this reader refuses, with the offending key named.

    `key` is the dotted path, so a caller can report the key without parsing
    the message back out of the string.
    """

    def __init__(self, key: str, message: str):
        self.key = key
        super().__init__(f"{key}: {message}")


# --- reading the surface ---------------------------------------------------


def _literal(text: str):
    """Read a marker's value the way the configuration itself would be read."""
    return _load_yaml(text, os.path.relpath(SURFACE, PLUGIN_ROOT))


def _fences(surface_text: str) -> list[tuple[str, str]]:
    """Each fenced block, paired with the heading it sits under.

    The heading travels with the block so a refusal can cite the section that
    states the rule -- ``host.checks: required -- marked `# required` under
    § 2. Code host`` -- instead of carrying a gloss of its own. A gloss in this
    module would be a paraphrase of the surface, which is the shape nothing can
    hold to it.
    """
    out: list[tuple[str, str]] = []
    heading, block, fence = "", [], None
    for line in surface_text.splitlines():
        if fence is not None:
            if line.startswith("```"):
                if fence == "yaml":
                    out.append((heading, "\n".join(block)))
                block, fence = [], None
            elif fence == "yaml":
                block.append(line)
            # A fence of any other language is skipped entirely rather than
            # merely not yielded: a `markdown` example containing a `##` line
            # would otherwise be read as a heading and mis-cite the section of
            # every refusal after it.
            continue
        if line.startswith("```"):
            fence = line[3:].strip() or "(bare)"
            continue
        titled = HEADING.match(line)
        if titled:
            heading = titled.group("title").strip()
    return out


def _walk_keys(block: str):
    """Yield (dotted path, text after the colon) for each key line in a block.

    Nesting comes from indentation, which is what the surface uses and what a
    reader of the surface sees. A fence that opens at an indent -- several do,
    because they show one facet of a larger key -- still yields the paths it
    states, relative to its own first key.
    """
    stack: list[tuple[int, str]] = []
    for line in block.splitlines():
        match = KEY_LINE.match(line)
        if not match:
            continue
        indent = len(match.group("indent"))
        while stack and stack[-1][0] >= indent:
            stack.pop()
        stack.append((indent, match.group("key")))
        yield ".".join(key for _, key in stack), match.group("rest")


def surface_facts(surface_text: str) -> dict:
    """Everything this reader needs that the surface already states.

    Returns the marked defaults and every alternation, keyed by the dotted path
    of the line that states it.
    """
    defaults: dict[str, object] = {}
    enums: dict[str, list[str]] = {}
    lists: dict[str, list[str]] = {}
    required: dict[str, str] = {}
    required_when: dict[tuple[str, str, str], str] = {}
    absent_reason: dict[str, str] = {}
    procedure: dict[str, str] = {}
    declared: set[str] = set()

    for heading, block in _fences(surface_text):
        # The clause-shaped marker, read before the key walk because it sits on
        # no key line. ⚠️ A surface stating none is not refused below, unlike
        # every marker that hangs on a key: zero is the ordinary state of a
        # surface that has made nothing procedure, and what holds *this* one to
        # the clause it states is the reader's own suite.
        for line in block.splitlines():
            stripped = line.strip()
            found = PROCEDURE_CLAUSE.match(stripped)
            if found:
                procedure.setdefault(found.group("key"), heading)
            elif PROCEDURE_NEAR_MISS.match(stripped):
                raise ConfigError(
                    os.path.relpath(SURFACE, PLUGIN_ROOT),
                    f"carries `{stripped}` under § {heading}, which means to be the "
                    "procedure marker and does not parse as one. The form is "
                    "`# procedure: <key>`, the key bare. Left unparsed, the surface "
                    "reads as refusing a key and this reader refuses nothing.",
                )

        for path, rest in _walk_keys(block):
            declared.add(path)
            value, _, comment = rest.partition("#")
            clauses = [c.strip() for c in comment.split(";")]

            for clause in clauses:
                found = DEFAULT_CLAUSE.match(clause)
                if found:
                    shown = found.group("literal")
                    defaults[path] = _literal(shown if shown else value.strip())
                if REQUIRED_CLAUSE.match(clause):
                    # First statement wins: a key shown in several fences is
                    # marked where it is declared, and a later fence showing one
                    # facet of it must not be able to unmark it.
                    required.setdefault(path, heading)
                found = REQUIRED_WHEN_CLAUSE.match(clause)
                if found:
                    # Keyed by the whole condition, so one key required under two
                    # values of another is two requirements rather than one that
                    # the second statement silently replaces.
                    required_when.setdefault(
                        (path, found.group("on"), found.group("value")), heading
                    )
                elif REQUIRED_WHEN_NEAR_MISS.match(clause):
                    raise ConfigError(
                        path,
                        f"carries `# {clause}`, which means to be the conditional "
                        "marker and does not parse as one. The form is "
                        "`# required_when: <key> = <value>`, the key written "
                        "absolutely and the value bare. Left unparsed this key "
                        "reads as marked and is enforced nowhere.",
                    )
                # ⛔ The procedure marker is a clause of its own and is read
                # nowhere else, so one written here -- hanging off a key line,
                # the way every marker that *does* hang off one is written -- is
                # refused rather than dropped. It is the likeliest place an
                # author habituated to this surface would put it, and the one
                # place the own-line scan above cannot see.
                if PROCEDURE_NEAR_MISS.match(f"# {clause}"):
                    raise ConfigError(
                        path,
                        f"carries `# {clause}` as a clause of this key's comment. The "
                        "procedure marker is a comment line of its own inside a block, "
                        "the key it names never having had a line; read as a clause here "
                        "it states a rule nothing performs.",
                    )
                if ABSENT_REASON_CLAUSE.match(clause):
                    # ⛔ Refused rather than ignored where it is not on a
                    # `carrier`: the rule it marks reads `carrier: none`, so a
                    # marker anywhere else states a rule nothing applies -- and
                    # a marker nobody reads is the exact defect this marker
                    # exists to remove, one level up.
                    if not path.endswith(".carrier"):
                        raise ConfigError(
                            path,
                            "carries `# absent_reason`, which marks a facet's "
                            "`carrier` and is read nowhere else. Move it to the "
                            "facet's `carrier` line or delete it.",
                        )
                    absent_reason.setdefault(path[: -len(".carrier")], heading)

            # A closed set, written either as the value or as a comment beside
            # it -- `key: a | b | c` is the first shape, and a line whose value
            # is one member with `# a | b | c` beside it is the second.
            for candidate in (value.strip(), comment.strip()):
                if ALTERNATION.match(candidate):
                    enums.setdefault(path, [v.strip() for v in candidate.split("|")])
                    break

            # ⛔ The third shape, and it is a *list's* vocabulary rather than a
            # value's: a key whose value is a list shows its members as the list
            # itself. An alternation beside such a key cannot be read by the
            # alternation rule above -- that rule holds the value, and the value
            # here is the whole list -- so the two are separate facts and a
            # reader asking the wrong one of them refuses every configuration
            # stating more than one member.
            #
            # ⚠️ Why that matters beyond tidiness: a reader older than the key
            # resolves the newer surface by § 1, so an alternation it reads with
            # the wrong rule refuses a configuration the branch adding the key
            # legitimately wrote -- measured on this repository, every guard in
            # a work tree going quiet at once. A list's vocabulary written this
            # way is simply unread by an older reader, which is the direction
            # that fails safe.
            shown = _literal(value.strip()) if value.strip().startswith("[") else None
            if isinstance(shown, list) and shown and all(
                isinstance(member, str) for member in shown
            ):
                lists.setdefault(path, [member.strip() for member in shown])

    # A reader that derives nothing accepts anything, so an unreadable surface
    # is refused here rather than silently waved through. ⛔ `required` is in
    # this list for a sharper reason than the other two: a surface whose
    # requiredness markers were dropped would leave this reader accepting a
    # configuration with no `host.repo` and no `roots.code` at all, and the
    # refusals that are the only evidence the markers were ever read would
    # simply stop happening -- silently, and green.
    missing = [
        name
        for name, found in (
            ("default", defaults),
            ("alternation", enums),
            ("required key", required),
            ("conditionally required key", required_when),
            ("absent-capable facet", absent_reason),
        )
        if not found
    ]
    if missing:
        raise ConfigError(
            os.path.relpath(SURFACE, PLUGIN_ROOT),
            "states no " + " and no ".join(missing) + " this reader can read. "
            "Either the surface changed shape or its markers were dropped.",
        )

    # Each condition held to the surface that states it, now that every block has
    # been walked. A condition on a key nobody declares, or on a value outside the
    # set that key states, is one no configuration can ever meet -- so the keys it
    # guards would be required nowhere while reading as required here.
    #
    # ⛔ The comparison is **suffix-tolerant in both directions**, and that is not
    # laxity: `_walk_keys` yields a path relative to its own fence's first key, so
    # a key shown in a fence that opens at an indent is declared here under a
    # shorter path than the absolute one § 1 tells a marker to write. Measured: the
    # absolute, surface-mandated spelling of such a key was refused as "declares
    # nowhere" -- a load-time refusal of a legitimate marker, which is the
    # direction this guard must never fail in. What it still catches is a key the
    # surface declares under no path at all, which is the typo it exists for.
    for (path, on, value), heading in sorted(required_when.items()):
        known = any(
            on == shown or on.endswith(f".{shown}") or shown.endswith(f".{on}")
            for shown in declared
        )
        if not known:
            raise ConfigError(
                path,
                f"carries `# required_when: {on} = {value}` under § {heading}, and "
                f"`{on}` is a key the surface declares nowhere. A condition "
                "nothing can meet is a requirement nothing enforces.",
            )
        allowed = enums.get(on)
        if allowed and value not in allowed:
            raise ConfigError(
                path,
                f"carries `# required_when: {on} = {value}` under § {heading}, and "
                f"`{on}` states {' | '.join(allowed)}. A condition outside that "
                "set never fires, so the key would be required nowhere.",
            )

    # § 1's collection: which blocks an entry of `roots.code` carries, read off
    # the entry the surface shows rather than listed here. A block added to that
    # fence is resolved per root without this module changing, which is the
    # division every marker above already has -- and `path` is dropped because it
    # is the entry's own key rather than one of the project's blocks it narrows.
    #
    # ⚠️ Deliberately **not** in the `missing` refusal above, unlike every marker
    # class there. A surface that showed no entry would make this empty, and the
    # failure that follows is closed rather than silent: `_code_roots` refuses an
    # entry carrying a block this set does not name, so a collection is rejected
    # with the key named instead of having its per-root facts quietly ignored. A
    # refusal on the whole surface would instead make a work tree whose branch
    # predates the fence unable to read its own configuration, which is the cost
    # § 1's `surface_for` rule exists to avoid.
    per_root = sorted(
        {
            parts[3]
            for path in declared
            if len(parts := path.split(".")) == 4 and parts[:2] == ["roots", "code"]
        }
        - {"path"}
    )

    return {
        "defaults": defaults,
        "enums": enums,
        # ⚠️ Deliberately **not** in the `missing` refusal above, for the reason
        # `per_root` is not: a surface showing no inline list would empty this,
        # and the failure that follows is closed rather than silent —
        # `vocabulary_list` refuses at the point of use, naming the path.
        "lists": lists,
        "required": required,
        "required_when": required_when,
        "absent_reason": absent_reason,
        "procedure": procedure,
        "per_root": per_root,
        # Every path the blocks declare, for the one rule that is about a key's
        # *children* rather than its value: § 6 states which roles commit by
        # showing one entry each, and a reader that listed them would be the
        # second statement every marker above exists to avoid.
        "declared": declared,
    }


def surface_keys(surface_text: str) -> set[str]:
    """Every dotted key path the surface's blocks declare.

    Used by the self-test to hold the retired keys to the surface: a key this
    reader refuses must not be one the surface still tells a project to write.
    """
    return {path for _, block in _fences(surface_text) for path, _ in _walk_keys(block)}


# A retirement has no key line to hang a marker on -- the key being gone from
# the surface's blocks is what retiring it means -- so it is stated as a clause
# of its own, inside the block the key was declared in.
#
# ⛔ A token, and never the English beside it: the prose says why a key is
# retired and this clause is what this reader performs, which is the division
# every other marker on the surface already has. The surface states the rule and
# `docs/configuration-surface.md` carries the measurement behind it; neither is
# restated here.
RETIRED_CLAUSE = re.compile(r"^#\s*retired:\s*(?P<key>[A-Za-z0-9_.]+)$")


def retired_keys(surface_text: str) -> set[str]:
    """Every key the surface states is retired.

    The surface states the retirement and this reader performs it, so the two
    are held to each other rather than maintained apart -- which is the arm that
    was missing while `RETIRED` was the only statement of its own contents.

    ⚠️ No arm refuses a surface that states none. Unlike the marker classes
    above, zero retirements is the ordinary state of a surface that has never
    retired anything, so emptiness here is read against `RETIRED` -- which must
    then be empty too -- rather than against the surface being unreadable.
    """
    return {
        found.group("key")
        for _, block in _fences(surface_text)
        for line in block.splitlines()
        if (found := RETIRED_CLAUSE.match(line.strip()))
    }


def vocabulary(facts: dict, path: str, what: str) -> list[str]:
    """An alternation the reader requires, or a refusal naming what is absent."""
    found = facts["enums"].get(path)
    if not found:
        raise ConfigError(
            os.path.relpath(SURFACE, PLUGIN_ROOT),
            f"states no `{path}` alternation, so {what} would be unchecked.",
        )
    return found


def vocabulary_list(facts: dict, path: str, what: str) -> list[str]:
    """The members a list key may carry, read off the list the surface shows.

    The counterpart of `vocabulary` for a key whose value is a list: what the
    surface states there is the membership rather than the value, so the two
    facts are read apart and a refusal names which one is missing.
    """
    found = facts["lists"].get(path)
    if not found:
        raise ConfigError(
            os.path.relpath(SURFACE, PLUGIN_ROOT),
            f"shows no `{path}` list, so {what} would be unchecked.",
        )
    return found


# --- reading a project's configuration -------------------------------------


def _get(data, path: str, default=None):
    node = data
    for part in path.split("."):
        if not isinstance(node, dict) or part not in node:
            return default
        node = node[part]
    return node


_ABSENT = object()


def _has(data, path: str) -> bool:
    return _get(data, path, _ABSENT) is not _ABSENT


def _absent_as(value, empty):
    """A value a key states, with the key's absence read as `empty`.

    ⛔ **Whether a key is written is the surface's `# required` marker**, answered
    in `validate` before any shape rule runs; what a stated value has to *be* is
    the rule's. A rule refusing absence as well states the marker's fact a second
    time -- and the second statement outlives the first wherever the resolved
    surface stops marking the key, which is a work tree whose branch predates the
    marker (§ 1, `surface_for`). Measured on ten of these rules: each refused a
    configuration the surface it was held to did not require, naming the key, so
    the project could not read its own facts in its own tree.

    ⚠️ It is the shape rule that is relaxed and never the requirement. Against a
    surface that does mark the key, `validate` refuses the absence before this is
    reached, with the same message as before and the key named.
    """
    return empty if value is None else value


def _load_yaml(text: str, where: str):
    """Parse YAML, turning a parser error into the refusal this module promises.

    A one-space indentation slip is the likeliest thing to go wrong in a
    hand-written configuration, and a traceback out of the parser names no key
    and tells the person reading it nothing they can act on.
    """
    yaml = _yaml()
    try:
        return yaml.safe_load(text)
    except yaml.YAMLError as error:
        detail = " ".join(str(error).split())
        raise ConfigError(where, f"is not valid YAML -- {detail}") from None


def _set_default(data: dict, path: str, value) -> None:
    """Apply one marked default, creating the blocks it needs on the way down.

    A parent that is absent -- or present and empty, which is how YAML reads a
    key with nothing under it -- gets created so the default can land. A parent
    that is present and is some *other* kind of value is refused here: it used
    to be skipped silently on the grounds that validation would catch it, which
    was untrue for every `day_log` key, so a block written as a string dropped
    five defaults and loaded clean.
    """
    parts = path.split(".")
    node = data
    for depth, part in enumerate(parts[:-1]):
        child = node.get(part)
        if child is None:
            child = {}
            node[part] = child
        elif not isinstance(child, dict):
            raise ConfigError(
                ".".join(parts[: depth + 1]),
                f"is {type(child).__name__}, and has to be a block of keys for "
                f"`{path}` to be read.",
            )
        node = child
    node.setdefault(parts[-1], value)


# The key § 1 gives the one root a project writing the single form has, and what
# a report names that root by. ⛔ Taken from the last segment of the key that
# states the path rather than written out again: the surface's prose names it,
# and a second spelling here is a copy of that one free to disagree with it. ⚠️
# Not derived from the repository slug either, which would be the inference § 1
# forbids one step over.
ONE_ROOT = "roots.code".rpartition(".")[2]


def _merged(project: dict | None, entry: dict | None) -> dict | None:
    """One of § 1's blocks for one root: the entry's keys over the project's.

    Key by key and one level deep, which is the grain § 1 states: what an entry
    says is that root's, what it does not say is the project's. ⛔ Not a deep
    merge -- `checks` is a list and a root's check set is disjoint from the
    other's, so merging *into* a list would produce a set neither repository
    runs.
    """
    if entry is None:
        return project
    if project is None:
        return entry
    return {**project, **entry}


def _code_roots(data: dict, facts: dict) -> tuple[dict[str, dict], bool]:
    """§ 1's roots: (key -> {path, <block>...} resolved, whether it is the collection).

    The single form resolves to one entry under `ONE_ROOT`, carrying the
    project's own blocks, so everything downstream reads one shape and the two
    forms differ in this function alone.
    """
    blocks = tuple(facts.get("per_root") or ())
    stated = _get(data, "roots.code")
    if not isinstance(stated, dict):
        # The single form, the absent key included: whether `roots.code` is
        # written at all is the surface's `# required` marker, answered in
        # `validate` against this view rather than second-guessed here.
        return {ONE_ROOT: {"path": stated, **{b: _get(data, b) for b in blocks}}}, False

    if not stated:
        raise ConfigError(
            "roots.code",
            "is an empty block of named roots. A project states the path, or one "
            "entry per repository; a block with nothing in it states neither, and "
            "every root a role would address is missing (§ 1).",
        )

    roots: dict[str, dict] = {}
    for key, entry in stated.items():
        at = f"roots.code.{key}"
        if not isinstance(entry, dict):
            raise ConfigError(
                at,
                f"is {type(entry).__name__}, and a named root is a block carrying "
                "`path` and the blocks that root narrows (§ 1).",
            )
        unknown = sorted(set(entry) - {"path", *blocks})
        if unknown:
            raise ConfigError(
                f"{at}.{unknown[0]}",
                "is not a key a named root carries. The surface shows an entry "
                f"with `path` and {' and '.join(f'`{b}`' for b in blocks) or 'nothing else'}"
                ", and a key beside those would be a per-root fact nothing reads (§ 1).",
            )
        if not entry.get("path"):
            raise ConfigError(
                f"{at}.path",
                "required: a named root states the path every git and gh call "
                "addresses for it, read relative to the skills root like the "
                "single form's own value (§ 1).",
            )
        roots[key] = {
            "path": entry["path"],
            **{b: _merged(_get(data, b), entry.get(b)) for b in blocks},
        }

    # ⛔ The two keys no two roots may share, refused here rather than left to
    # produce a plausible answer later. The slug is the sharper of the two: it is
    # reached either by writing one twice or by leaving it off an entry, so that
    # the project's own block answers for both roots -- which is a second root
    # addressed as the first, silently, by every call that follows.
    for field, where in (("path", "path"), ("repo", "host.repo")):
        seen: dict[object, str] = {}
        for key, root in roots.items():
            block = root if field == "path" else (root.get("host") or {})
            value = block.get(field) if isinstance(block, dict) else None
            if value is None:
                continue
            first = seen.setdefault(value, key)
            if first != key:
                raise ConfigError(
                    f"roots.code.{key}.{where}",
                    f"resolves to {value!r}, which `roots.code.{first}` resolves "
                    "to as well. Two names for one repository is what this facet "
                    "exists against: state it per root, or write one root (§ 1).",
                )
    return roots, True


# § 4.7's carriers that an item holds exactly one of: the named field's value, and
# the title. `label` is the other kind -- an item carries every label it has, and
# the axis's prefix is what picks this one out of them.
ONE_VALUE_CARRIERS = ("field", "title_prefix")

# A character that continues a word, for § 4.7's title carrier. ⛔ The match is
# anchored on a boundary rather than on `startswith` alone, and the finding that
# forced it is in the suite: with a bare `startswith`, a root mapped to `app` took
# every item whose title opened *appendix*, which is the silent wrong root this
# facet exists against. ⚠️ `-` and `_` continue a word here, so `app` and
# `app-site` are distinguishable values rather than one stranding the other.
WORD_CHARACTER = re.compile(r"[A-Za-z0-9_-]")


def _opens_with(text: str, value: str) -> bool:
    """Whether `text` opens with `value` as a whole word (§ 4.7, title carrier)."""
    if text == value:
        return True
    return text.startswith(value) and not WORD_CHARACTER.match(text[len(value):])


def _gates_on_code_root(data: dict) -> bool:
    """Whether `readiness` configures § 5's `code_root_stated`."""
    gate = _get(data, "readiness")
    return isinstance(gate, list) and any(
        isinstance(entry, dict) and entry.get("check") == "code_root_stated"
        for entry in gate
    )


def _code_root_facet(data: dict, roots: dict[str, dict]) -> None:
    """§ 4.7: which of § 1's roots a work item belongs to.

    ⛔ Project-level rather than one of `validate`'s, and that is not a placement
    preference: a view carries one root's path at `roots.code`, so every rule in
    `validate` is blind to how many roots there are -- which is the whole
    condition this facet turns on. ⚠️ It runs *after* those rules, so a facet
    that is both misplaced and missing its reason is refused on the reason
    first; the two refusals name different keys and neither hides the other.
    """
    named = ", ".join(repr(key) for key in roots)
    facet = _get(data, "work_item.code_root")

    # ⛔ The single form, refused with the facet stated. § 4.7's reason is § 1's
    # retirement argument taken before the key exists: with one repository there
    # is one answer, so the value is read by nothing and a project that wrote it
    # would be ignored in silence.
    if len(roots) < 2:
        if facet is not None:
            raise ConfigError(
                "work_item.code_root",
                f"is stated while `roots.code` carries one root ({named}). § 4.7 "
                "makes this facet the answer to which of several repositories an "
                "item belongs to, and a project with one is never asked for it -- "
                "so the value would be read by nothing. Delete the facet, or state "
                "the roots it is choosing between (§ 1).",
            )
        if _gates_on_code_root(data):
            raise ConfigError(
                "readiness",
                f"configures `code_root_stated` while `roots.code` carries one root "
                f"({named}). The check reads § 4.7 and there is one answer, so it "
                "would pass every item and read as coverage (§ 5).",
            )
        return

    carrier = _get(data, "work_item.code_root.carrier")
    if carrier is None:
        raise ConfigError(
            "work_item.code_root.carrier",
            f"required where `roots.code` carries several roots ({named}): every "
            "role past the gate resolves the repository from the item, and § 4.7 "
            "is where a project states what carries that fact. ⛔ A role with "
            "nothing to read stops rather than taking the first root, so the gap "
            "is a loop that cannot run on all but one of these repositories. "
            "State the carrier, or `none` with the reason the tracker cannot hold "
            "it.",
        )

    # ⛔ The stated absence, and the check that reads the facet refused with it --
    # § 4.6's shape for `queue_position`, with the project's own reason quoted
    # rather than a sentence of this reader's.
    if carrier == "none":
        if _gates_on_code_root(data):
            stated = " ".join(
                str(_get(data, "work_item.code_root.absent_reason")).split()
            )
            raise ConfigError(
                "work_item.code_root.carrier",
                "is `none` while `readiness` configures `code_root_stated`, which "
                "reads this facet and nothing else (§ 5). The check would be "
                "refusing every item for a fact the tracker cannot hold, and the "
                f"facet's own stated reason is: {stated!r}. Carry the facet, or "
                "drop the check -- the root then arrives on each role's invocation "
                "(§ 4.7).",
            )
        return

    if carrier == "label" and not _get(data, "work_item.code_root.label_prefix"):
        raise ConfigError(
            "work_item.code_root.label_prefix",
            "required when the carrier is `label`: the prefix is what keeps this "
            "axis apart from every other label on an item (§ 4.7), which is "
            "§ 4.6's rule for the same carrier one facet over.",
        )
    if carrier == "field" and not _get(data, "work_item.code_root.field"):
        raise ConfigError(
            "work_item.code_root.field",
            "required when the carrier is `field`: there is nowhere to read the "
            "root from (§ 4.7).",
        )

    mapping = _get(data, "work_item.code_root.roots")
    if not isinstance(mapping, dict) or not mapping:
        raise ConfigError(
            "work_item.code_root.roots",
            f"is {mapping!r}; § 4.7 states it as every named root of § 1 mapped to "
            "what the carrier holds for it. A carrier with no mapping is a value on "
            f"an item that names no repository, with {named} to choose between.",
        )
    # ⛔ Total over the collection, which is § 4.1's rule for the branch prefix and
    # fails in the same expensive place: the gap surfaces at a role that has
    # already admitted the item.
    for key in roots:
        if key not in mapping:
            raise ConfigError(
                f"work_item.code_root.roots.{key}",
                "is missing, and § 4.7's mapping is total over § 1's roots. A root "
                "with no value is a repository no item can name, and nothing refuses "
                "the item until a role needs the answer.",
            )
    seen: dict[str, str] = {}
    for key, value in mapping.items():
        at = f"work_item.code_root.roots.{key}"
        if key not in roots:
            raise ConfigError(
                at,
                f"names a root `roots.code` does not carry. It carries {named} "
                "(§ 4.7). A value mapped to nothing is an item resolving to a "
                "repository the project cannot address.",
            )
        if not isinstance(value, str) or not value.strip():
            raise ConfigError(
                at,
                f"is {value!r}; § 4.7 states what the carrier holds for this root, "
                "and an entry naming nothing matches no item while reading as a "
                "root that is carried.",
            )
        first = seen.setdefault(value, key)
        if first != key:
            raise ConfigError(
                at,
                f"is {value!r}, which `work_item.code_root.roots.{first}` holds as "
                "well. One value answering for two roots is an item that resolves "
                "to both, and choosing either would be this reader deciding what "
                "the configuration did not (§ 4.7).",
            )

    # ⛔ Under the title carrier, distinctness is not equality. A value that opens
    # another value as a whole word answers for both roots on every item of the
    # longer one, so the longer root is a repository no item can reach -- the
    # failure the totality rule above exists against, arrived at from the other
    # side. ⚠️ Refused here rather than at the match, because a project that
    # loaded and then stopped every item is the gap this surface settles where the
    # configuration is read.
    if carrier == "title_prefix":
        for key, value in mapping.items():
            for other, shorter in mapping.items():
                if other != key and _opens_with(value, shorter):
                    raise ConfigError(
                        f"work_item.code_root.roots.{key}",
                        f"is {value!r}, which opens with "
                        f"{shorter!r} — `work_item.code_root.roots.{other}`'s value — "
                        "as a whole word. Under the title carrier that makes every "
                        f"title of `{key}` answer for `{other}` as well, so one of the "
                        "two roots is a repository no item can reach (§ 4.7).",
                    )

    # ⛔ And the check, required rather than refused -- the inverse direction from
    # § 4.6's, for the reason § 5 states: this is the last point before a claim is
    # taken, and a role that stops instead has already read the item and reported
    # a gap the gate exists to catch.
    if not _gates_on_code_root(data):
        raise ConfigError(
            "readiness",
            "configures no `code_root_stated` while `work_item.code_root` carries "
            f"the roots {named} (§ 5). An item naming no repository would then be "
            "admitted by the gate and stop a role downstream, which is the one "
            "place § 4.7's answer is expensive to be missing.",
        )


class Config:
    """A project's facts, resolved. Read through the accessors, not the dict."""

    def __init__(self, data: dict, skills_root: str, facts: dict, source: str | None = None,
                 surface: str | None = None, *, root_key: str | None = None,
                 views: "dict[str, Config] | None" = None,
                 overridden: set[str] | None = None):
        self.data = data
        self.skills_root = skills_root
        self.facts = facts
        # Which of § 1's roots this object answers for, or None where it answers
        # for the project. A view's `data` carries that root's path and its
        # resolved blocks, so every accessor below reads one root's facts
        # without knowing it is doing so -- which is what keeps a consumer
        # written against one repository correct against a project with two.
        self.root_key = root_key
        self.views: dict[str, Config] = views if views is not None else {}
        # The paths some entry states for itself, so a project-level read of one
        # is refused rather than answered from the block it narrows (§ 1).
        self.overridden = overridden or set()
        # The file this came from, where it came from one. `None` for a
        # configuration handed over as text, which is the self-test loading the
        # examples -- reporting a path that was never opened would be the
        # plausible-looking wrong answer this whole section is about.
        self.source = source
        # The surface it was held to, which `surface_for` resolved and § 1 puts
        # in what a role names. Two copies can answer the question -- the
        # installed plugin's and a shipping project's own tree -- so which one
        # ruled is a fact about the resolution rather than a constant.
        self.surface = surface or SURFACE

    # -- the roots. The skills root is where the role ran (§ 1); the code root is
    # read from the file found there and is never inferred.

    @property
    def config_path(self) -> str | None:
        """The file this configuration was read from, absolute, or None.

        Reported so a role can say *which project* it resolved. Under § 1 the
        skills root is the directory the role ran in, and a role run from a
        sibling project that has a configuration of its own resolves that
        project and proceeds -- naming the file is the only thing that makes
        that visible at the moment it happens.
        """
        return self.source

    @property
    def surface_path(self) -> str:
        """The surface this configuration was held to, absolute.

        Reported for the reason `config_path` is: where a project ships this
        surface as well as consuming it, the copy that ruled is a fact a role
        states rather than one a reader of the output has to work out.
        """
        return os.path.abspath(self.surface)

    @property
    def code_root(self) -> str:
        return os.path.normpath(os.path.join(self.skills_root, self.get("roots.code")))

    @property
    def root_keys(self) -> list[str]:
        """The names § 1's roots are addressed by, in the order stated."""
        return list(self.views)

    def root(self, key: str) -> "Config":
        """One of § 1's roots by name, or a stop naming the ones there are.

        ⛔ The stop is § 1's: a role handed a root this project does not carry
        reports it rather than falling back to whichever root is first. The key
        reaching here is the name § 1's collection gives a root -- from a
        person, from an invocation, or from `root_for` below, which is where an
        item's own answer is turned into one.
        """
        if key in self.views:
            return self.views[key]
        raise ConfigError(
            "roots.code",
            f"carries no root named {key!r}. It carries "
            f"{', '.join(repr(k) for k in self.views) or 'none'} (§ 1).",
        )

    def root_for(self, values: list[str]) -> "Config":
        """§ 1's root the item itself names, by § 4.7's facet, or a stop.

        `values` is what the item carries on whichever carrier the facet names:
        every label on it, the named field's value, or its title. ⛔ **One
        implementation, so two roles cannot disagree** -- the alternative is
        each role matching a prefix for itself, which is the divergence § 4.7's
        mapping exists to close, one facet over from the branch name's.

        The refusals are § 4.7's, and both directions are stops: an item naming
        no root and an item naming two are each reported rather than resolved,
        because the permissive reading of either is this project's work landing
        in the wrong repository.
        """
        # ⛔ A view is refused rather than answered, and it is told apart from a
        # single-root project by its own key and not by the number of roots it
        # carries: `_resolve` narrows every view to itself, so both hold one.
        # Reviewed on this change: a view answered with *its* root whatever the
        # item said, which is the silent pick this method exists to refuse, one
        # caller further in than § 1's own refusal reaches.
        if self.root_key is not None:
            raise ConfigError(
                "work_item.code_root",
                f"cannot be resolved against the root `{self.root_key}` alone: this "
                "configuration has already been narrowed to one root, so the "
                "question *which root does this item name* has been answered by "
                "whoever narrowed it. Ask the project (§ 4.7).",
            )
        # One root is the case § 4.7 refuses the facet in, so there is nothing
        # on the item to read and nothing to disagree with. ⚠️ Reported as the
        # one root rather than refused: a role calling this on a single-root
        # project is correct, and what it needs back is the root.
        if len(self.views) < 2:
            return self.only_root
        carrier = self.get("work_item.code_root.carrier")
        if carrier == "none":
            stated = " ".join(str(self.get("work_item.code_root.absent_reason")).split())
            raise ConfigError(
                "work_item.code_root.carrier",
                "is `none`, so no item here states which repository it belongs to "
                f"and the project's stated reason is: {stated!r}. The root arrives "
                "on the invocation instead, and a role takes neither the first of "
                f"{', '.join(repr(k) for k in self.views)} nor a guess (§ 4.7).",
            )
        mapping = self.get("work_item.code_root.roots")
        held = [v for v in values if isinstance(v, str) and v.strip()]
        prefix = self.get("work_item.code_root.label_prefix") or ""
        # ⛔ A carrier an item holds one of is handed one value, and several is a
        # stop rather than a search through them. Reviewed on this change: a title
        # handed over unquoted arrives word-split, and one *word* of it opening
        # with a mapped value resolved the item -- so the permissive reading of a
        # longer list is the wrong root reached through a shell quirk.
        if carrier in ONE_VALUE_CARRIERS and len(held) > 1:
            raise ConfigError(
                "work_item.code_root",
                f"was handed {len(held)} values for the `{carrier}` carrier, which "
                f"an item holds one of: {', '.join(repr(v) for v in held)}. A title "
                "or a field value is one string, and a list of them is a value that "
                "was split on the way in (§ 4.7).",
            )
        matched = set()
        for key, value in mapping.items():
            for carried in held:
                # Each carrier matched the way § 4.7 states it is held: a label
                # is the mapped value behind the axis's prefix, a field is the
                # value itself, and a title prefix opens the title as a whole
                # word -- never as a bare `startswith`, which is the finding
                # `_opens_with` above carries.
                if carrier == "label":
                    found = carried.startswith(prefix) and carried[len(prefix):] == value
                elif carrier == "title_prefix":
                    found = _opens_with(carried, value)
                else:
                    found = carried == value
                if found:
                    matched.add(key)
        if len(matched) == 1:
            return self.views[next(iter(matched))]
        shown = ", ".join(repr(v) for v in held) or "nothing"
        if not matched:
            # ⚠️ The two cases are named apart, because their remedies are: an
            # item holding nothing needs the value added, and an item holding
            # something no root answers to needs that value corrected or the
            # mapping extended. Reviewed on this change, where one message said
            # *not stated on this item* about an item that stated something.
            raise ConfigError(
                "work_item.code_root",
                ("is not stated on this item at all" if not held else
                 f"names no root this project carries: the item holds {shown}")
                + f", and the facet's carrier `{carrier}` holds "
                f"{', '.join(f'{v!r} for {k}' for k, v in mapping.items())} (§ 4.7). "
                "⛔ The first root is not the answer -- a role stops here rather "
                "than landing the work in whichever repository is written first.",
            )
        # ⚠️ The roots are named and their number is not: the mapping may hold
        # more than two, and a message saying *two* would be wrong on a project
        # this reader accepts.
        raise ConfigError(
            "work_item.code_root",
            f"resolves to {', '.join(sorted(matched))} on this item, which carries "
            f"{shown}. An item belongs to one repository (§ 4.7), and which of the "
            "roots it names is meant is not this reader's to choose.",
        )

    @property
    def only_root(self) -> "Config":
        """This project's one root, or a stop naming the several it has."""
        if self.root_key is not None:
            return self
        if len(self.views) == 1:
            return next(iter(self.views.values()))
        raise ConfigError(
            "roots.code",
            f"carries {len(self.views)} named roots -- "
            f"{', '.join(repr(k) for k in self.views)} -- and this read wants one. "
            "Name the root (§ 1); a role with no key for it stops rather than "
            "taking the first.",
        )

    @property
    def tracker_kind(self) -> str:
        return self.get("tracker.kind")

    @property
    def has_tracker(self) -> bool:
        return self.tracker_kind != "none"

    def per_root(self, path: str) -> list[str]:
        """The per-root facts a project-level read of `path` would cross.

        Empty for a project whose code is one repository written as one path,
        which is why every consumer written against that shape reads on
        unchanged. Non-empty only where some entry of § 1's collection states
        the fact itself -- `host.kind` stated once above two roots is still one
        answer, and is not refused.
        """
        if self.root_key is not None:
            return []
        return sorted(
            crossed
            for crossed in self.overridden
            if path == crossed
            or path.startswith(f"{crossed}.")
            or crossed.startswith(f"{path}.")
        )

    def get(self, path: str, default=None):
        crossed = self.per_root(path)
        if crossed:
            raise ConfigError(
                path,
                f"is stated per code root here ({', '.join(crossed)}), and this "
                f"read is the project's. {len(self.views)} roots carry it -- "
                f"{', '.join(repr(k) for k in self.views)} -- so there is no one "
                "answer to give and the first of them is not it (§ 1).",
            )
        return _get(self.data, path, default)

    def mirrors(self) -> list[dict]:
        """§ 2's `host.checks` as a consumer reads it -- one record per command.

        An accessor rather than a read of `self.data`, for the reason the class
        opens with: every refusal the facet carries is in the walk, and a
        consumer reaching past this would be a second reading of the one
        statement § 2 exists to be. ⚠️ `[]` here is the project's stated
        absence and not an empty answer -- what that means is `unavailable()`'s
        to say, and `host_checks.py` answers *no answer* from it rather than
        *not covered*.

        ⚠️ Read per root where § 1's collection states the checks per root, by
        the refusal `get` carries: one flat list across two repositories would
        be a single answer made of two disjoint check sets, which is the shape
        that grain exists against.
        """
        self.get("host.checks")
        return mirrored_runs(self.data)

    def host_runs(self) -> list[dict]:
        """§ 2's `host.checks` as one record per entry, the run rather than the command.

        The accessor beside `mirrors()` and the same single walk behind both.
        ⚠️ **An entry mirroring nothing is here and not there**: § 2 makes the
        facet the single statement of which runs exist, so a run with no local
        counterpart is still a run -- which the check holding this facet to the
        host's own definitions has to see, and which a per-command view
        legitimately drops.
        """
        self.get("host.checks")
        return host_runs(self.data)

    def runner(self) -> dict | None:
        """§ 2's `host.runner`, or `None` where this project states none.

        The accessor beside the two above, and the facet's whole public face:
        an installer writing a workflow file reads the label, the budget and the
        supersession group from here and ⛔ **writes no literal of its own**, and
        the check holding the facet to the host's own definitions reads the same
        record. ⚠️ `None` is the project's stated absence -- the host kind's own
        default answers, and what that default is lives where the per-kind
        template does rather than on this surface.
        """
        self.get("host.runner")
        return host_runner(self.data)

    def pull_request_title(self) -> dict | None:
        """§ 2's `host.pull_request_title`, or `None` where this project states none.

        The facet's whole public face, and both of its readers come through
        here: the finishing role writing a title and the step installing the
        gate that refuses one. ⚠️ `None` is the project's stated absence —
        titles here open with no reference, so there is no rule for a gate to
        enforce and none for a role to render, which is a configuration rather
        than a gap.
        """
        self.get("host.pull_request_title")
        return host_pull_request_title(self.data)

    def _report_roots(self) -> "list[tuple[str, Config]]":
        """(what to prefix a line with, the root to read it from).

        ⛔ Every arm of the report below that reads a per-root fact reads it
        through this, because an absence is the root's rather than the
        project's: a project with two code repositories whose first runs
        workflows and whose second runs none has one of each answer, and a
        single line would state whichever came first. Where there is one root
        the prefix is empty and the line is exactly the line it was before § 1
        carried a collection at all.
        """
        if len(self.views) <= 1:
            return [("", self.only_root)]
        return [(f"`{key}`: ", view) for key, view in self.views.items()]

    def _memory_report(self) -> list[str]:
        """§ 25's own report, for a project that runs the memory third.

        ⛔ **What this names is what the store's carrier leaves open, never that
        the third is unavailable.** Before § 25 the third had no store at all and
        the whole of it was reported absent; what is reported now is narrower and
        has to stay narrower, because a third reported unavailable is a third the
        role is told to skip.

        ⚠️ **The `path` arm is not reported**, by the rule the rest of this
        method follows: a store the project pinned is a store the procedure
        writes, which is a behaviour rather than an absence.
        """
        out = []
        carrier = self.get(f"{MEMORY_KEY}.carrier")
        # ⛔ Reached only where the third runs, so this cannot be `none` without
        # the reader having refused the configuration first -- and the `none` case
        # is reported by the generic absent-carrier arm below, exactly like every
        # other facet's. A second line for it here would be the same absence
        # stated twice, free to drift from the one every other facet gets.
        if carrier == "none":
            return out
        # ⛔ Compared against the value rather than read as a boolean, and never
        # defaulted here: § 25 gives this key no default, so a configuration that
        # reaches this method has stated one of the two words.
        write_from = self.get(f"{MEMORY_KEY}.write_from")
        if carrier == "derived":
            out.append(
                "The memory store is the harness's own (`memory.carrier: "
                "derived`), so the procedure composes no path to it and resolves "
                "nothing inside it: the index two sessions contend on cannot be "
                "appended under a lock here, and a checkout that is moved or "
                "renamed derives a different store and orphans the old one "
                "silently. Both are reported rather than closed (§ 25)."
            )
        if write_from == "main_tree":
            out.append(
                "The memory third runs from the shared checkout alone "
                "(`memory.write_from: main_tree`), so a save standing in a tree "
                "**refuses** that third and names the refusal rather than writing "
                "the tree's own store (§ 25)."
            )
        # ⛔ Asked of every root rather than of one, `branch_model` being a block
        # § 1 lets a named root carry: a project whose first repository cuts trees
        # and whose second does not has a key that decides something, and a line
        # read off whichever root came first would state the opposite for half of
        # it.
        if not any(
            view.get("branch_model.kind") == "worktree" for view in self.views.values()
        ):
            out.append(
                "No code root here cuts a tree per item, so `memory.write_from` "
                "decides nothing: there is no second working directory for the "
                "memory third to run from. A stated key rather than an inert one "
                "-- the branch model is the project's and may change under a "
                "configuration that already carries this (§ 25)."
            )
        return out

    def unavailable(self) -> list[str]:
        """What this configuration cannot support, and why.

        A role prints this rather than failing: every entry is a stated
        decision or a legitimate absence, never a broken install.
        """
        out = []
        roots = self._report_roots()
        if not self.has_tracker:
            out.append(
                "No tracker is configured (`tracker.kind: none`). Branching, the "
                "pull request, the review and the day log do not need one. What "
                "that leaves each tracker operation doing is the port's to report, "
                "never this reader's: a capability is the adapter's fact."
            )
        # Which § 4 facets have a real absent case is the surface's
        # `# absent_reason` marker, not a triple written here: a fourth one is
        # reported the moment it is declared, and the old list would have left
        # it invisible to this report and to validation together.
        for path in sorted(self.facts.get("absent_reason", {})):
            facet = path.rpartition(".")[2]
            if path.startswith("work_item.") and self.get(f"{path}.carrier") == "none":
                reason = self.get(f"{path}.absent_reason")
                out.append(f"No {facet} is carried: {' '.join(str(reason).split())}")
        if self.get("context.artifacts.carrier") == "none":
            reason = self.get("context.artifacts.absent_reason")
            out.append(
                "No artifact store is carried (`context.artifacts.carrier: "
                "none`), so nothing crosses a role boundary in a file here: "
                f"{' '.join(str(reason).split())}"
            )
        if not self.get("statuses"):
            out.append(
                "No status is configured, so the procedure never asks the port "
                "to advance an item and reports no missing state as a fault."
            )
        if not self.get("readiness"):
            out.append("The readiness gate is empty, so there is nothing to gate.")
        if not self.get("done"):
            out.append(
                "The done list is empty, so what finished means here is the "
                "merge and whatever the host already runs, and no further check "
                "is asked for. That is a stated configuration (§ 13)."
            )
        # § 15. Reported for the reason the ordering below is: a role that would
        # have asked whether a change is covered end to end learns that the
        # project decided it runs nothing end to end, rather than meeting a key
        # that is not there. ⛔ And the complement is not reported: a project that
        # *does* carry the facet has a check to run, which is a verdict rather
        # than an absence.
        if self.get("e2e_register.carrier") == "none":
            reason = self.get("e2e_register.absent_reason")
            out.append(
                "No end-to-end register is carried (`e2e_register.carrier: "
                "none`), so no case list and no register are compared and a "
                "change is held to neither: "
                f"{' '.join(str(reason).split())}"
            )
        # § 16, and reported for the reason § 15's is: a role that would have
        # asked what a tier executed learns that this project has no tier whose
        # dependency a run stands up, rather than meeting a key that is not
        # there. ⛔ And the count is never reported as a zero — absence of signal
        # is not an answer, and zero executed is the failure this facet names, so
        # reporting it for a project that declared nothing would be the one wrong
        # answer available here.
        if self.get("executed.carrier") == "none":
            reason = self.get("executed.absent_reason")
            out.append(
                "No executed count is carried (`executed.carrier: none`), so "
                "what a run executed is **unavailable** here rather than zero, "
                "and no run is held to a floor: "
                f"{' '.join(str(reason).split())}"
            )
        # § 25, and reported for the reason § 15's is: a role that would have
        # refreshed memory, or read it, learns that the project keeps none --
        # rather than meeting a block that is not there. ⛔ And it is reported as
        # *no store* and never as a store that is empty: a reading nobody could
        # take and a store with nothing in it license different next steps, and
        # the second is the one a later pass acts on.
        if self.get(f"{MEMORY_KEY}.carrier") == "none":
            reason = self.get(f"{MEMORY_KEY}.absent_reason")
            out.append(
                "No memory store is carried (`memory.carrier: none`), so the "
                "bookkeeping role's memory third does not run and a restoring "
                "pass has no store to check a recalled fact against: "
                f"{' '.join(str(reason).split())}"
            )
        if self.get("ordering.carrier") == "none":
            reason = self.get("ordering.absent_reason")
            out.append(
                "No ordering is carried (`ordering.carrier: none`), so a role "
                "invoked with no item asks for one by number rather than "
                f"choosing: {' '.join(str(reason).split())}"
            )
        for where, root in roots:
            if not root.get("host.checks"):
                out.append(
                    f"{where}The host runs no checks, so every verdict is local and "
                    "`done`'s `gate_green` reads `checks_local` for its source "
                    "(§ 17). An empty check list reads as no answer, never as green."
                )
        # § 2. The runner statement's absence, reported for the reason § 15's is:
        # a role or an installer that would have asked where this project's jobs
        # run learns that the project declared the host kind's own default,
        # rather than meeting a key that is not there. ⛔ And it is reported as an
        # absence and never as a label -- the default is the host's, carried
        # nowhere on this surface, so naming one here would be this reader
        # inventing the fact the facet exists to have stated.
        for where, root in roots:
            if root.get("host.runner") is None:
                out.append(
                    f"{where}No runner is stated (`host.runner` is absent), so every "
                    "job of this project's workflows runs on the host kind's own "
                    "default, every job's budget is a run budget rather than a queue "
                    "budget, and nothing holds a workflow file to a label, a budget "
                    "or a supersession group (§ 2)."
                )
        # § 2. The title form's absence, reported for the same reason: the two
        # readers of that facet are a role that writes a title and a step that
        # installs the gate refusing one, and each of them would otherwise meet
        # a key that is not there. ⛔ Reported as the absence of a *rule* and
        # never as a permission -- a reader answering *any title is allowed*
        # would be stating a rule the project did not write.
        for where, root in roots:
            if root.get("host.pull_request_title") is None:
                out.append(
                    f"{where}No title form is stated (`host.pull_request_title` is "
                    "absent), so a pull request title here opens with no work-item "
                    "reference: the finishing role renders none, no title gate is "
                    "installed, and nothing holds a title to anything (§ 2)."
                )
        # § 23. Which thirds of the bookkeeping role this project does not run,
        # and the one third whose mechanism the surface does not carry yet. ⛔ The
        # memory arm is reported wherever the third is named, rather than the
        # third being dropped: a third that silently did not run reads exactly
        # like one that did, which is the failure direction § 11's
        # report-what-you-could-not-establish rule exists for.
        parts = _absent_as(self.get("session.parts"), [])
        if not parts:
            out.append(
                "No bookkeeping role runs here (`session.parts: []`), so nothing "
                "brings the tracker current, refreshes memory or commits on that "
                "role's account. A stated decision rather than a partial install "
                "(§ 23)."
            )
        else:
            if MEMORY_THIRD in parts:
                out += self._memory_report()
            # The vocabulary is the surface's, read rather than listed: a fourth
            # third would otherwise be absent from this report alone.
            every = self.facts.get("lists", {}).get("session.parts", [])
            missing = [t for t in every if t not in parts]
            if missing:
                out.append(
                    "The bookkeeping role runs " + ", ".join(parts) + " here and "
                    "not " + ", ".join(missing) + ", which is a configuration of "
                    "that role rather than a third of it going wrong (§ 23)."
                )
        # § 17, and the complement of the arm above: the two facets together are
        # every verdict there is, so an empty list here is reported for the
        # reason an empty `host.checks` is. ⛔ Where both are empty the project
        # has stated no verdict anywhere, which is reported as the two lines it
        # is rather than folded into one -- each is a separate decision, and a
        # project that acquires workflows tomorrow clears only one of them.
        if not self.get("checks_local"):
            out.append(
                "No local check is stated (`checks_local: []`), so no verdict is "
                "produced outside the host's own runs and a `local` done check "
                "has no source to read: a role reports it unanswered rather than "
                "inventing a command (§ 17)."
            )
        # § 18, and reported only where the facet above leaves it with nothing to
        # match. ⛔ The complement is not reported: a project whose host does run
        # checks has a guard that can refuse, which is a behaviour rather than an
        # absence -- and `never_guard: []` is not reported either, that being the
        # ordinary configuration rather than something a role cannot do.
        for where, root in roots:
            if not root.get("host.checks"):
                out.append(
                    f"{where}No command is guarded against a run the host has already "
                    "made (`host.checks: []`, § 18), so that guard matches nothing "
                    "here. A configuration rather than a partial install: there is no "
                    "mirrored command for a local run to duplicate."
                )
        # § 19, and the stated absence of a list rather than of a carrier: the
        # guard is installed in every project the install reaches, so what `[]`
        # buys is the difference between a project that decided no command of its
        # own spends and one that never asked. ⛔ The complement is not reported —
        # a project carrying entries has a guard that acts, which is behaviour
        # rather than an absence.
        if not self.get("spend_guard.deny"):
            out.append(
                "No command is denied as a spend (`spend_guard.deny: []`), so the "
                "spend guard is installed and refuses nothing here. ⛔ Not an "
                "absence of signal: the project states it (§ 19)."
            )
        # § 20, and the stated absence of a list rather than of a carrier: the
        # body is held to § 6 whatever this says, so what `[]` buys is the
        # difference between a project that decided no other role reads a
        # section of its bodies and one that never asked. ⛔ Reported as the
        # gate not being installed and never as a body that passed -- a run
        # asserting nothing is the shape the facet exists against.
        if not self.get("body_sections"):
            out.append(
                "No body section is required beyond § 6's (`body_sections: []`), "
                "so no body gate is installed and a body is held to the summary, "
                "the test plan and the closing reference alone (§ 20)."
            )
        # § 21, and the stated absence of a list rather than of a carrier, for the
        # reason § 19's is: the guard is installed in every project the install
        # reaches, so what `[]` buys is the difference between a project that
        # decided no command of its own leaves this machine and one that never
        # asked. ⛔ The complement is not reported -- a project carrying entries
        # has a guard that acts, which is behaviour rather than an absence.
        if not self.get("live_guard.session_tools"):
            out.append(
                "No command opens a session on another machine "
                "(`live_guard.session_tools: []`), so the live guard is installed "
                "and holds nothing here. ⛔ Not an absence of signal: the project "
                "states it (§ 21)."
            )
        # § 22, and two absences rather than one: the guard is installed in every
        # project the install reaches, so what each states is the difference
        # between a project that looked and one that never asked. ⛔ The
        # complement is not reported -- a project carrying entries or a limit has
        # a guard that acts, which is behaviour rather than an absence. ⛔ And
        # `never_bound: []` is not reported either, an exemption list with nothing
        # in it being the ordinary configuration rather than something a role
        # cannot do.
        if not self.get("context_guard.unbounded"):
            out.append(
                "No command produces output nothing bounds "
                "(`context_guard.unbounded: []`), so the context guard refuses and "
                "rewrites nothing here. ⛔ Not an absence of signal: the project "
                "states it (§ 22)."
            )
        if self.get("context_guard.result_limit_chars") is None:
            out.append(
                "No result is replaced by a path, a head and a tail "
                "(`context_guard.result_limit_chars` is absent), so every result "
                "reaches the window whole however long it is (§ 22)."
            )
        # A role's own unset key. `day_log.script` is the first absence in this
        # toolkit that is load-bearing rather than theoretical: the day-log role
        # cannot run without it, and reporting that -- naming the key -- is what
        # keeps an absence a configuration instead of a crash downstream.
        if self.get("day_log.script") is None:
            out.append(
                "`day_log.script` is not set, so the day-log role cannot run "
                "here. It names the project's evidence script, which is "
                "transitional until the script is extracted into the plugin."
            )

        for role, status in (
            (s.get("role"), s) for s in (self.get("statuses") or [])
        ):
            if status.get("writer") == "never":
                out.append(
                    f"The `{role}` status may not be written by the procedure "
                    "(`writer: never`): the credential acts as a person's own "
                    "account, so the move is reported instead of made."
                )
        return out

    def to_dict(self) -> dict:
        out = {
            "skills_root": os.path.abspath(self.skills_root),
            "config_path": self.config_path,
            "surface_path": self.surface_path,
        }
        # § 1 has a role name the repository its configuration addresses before
        # it acts, so where there are several the report names each of them with
        # the root it belongs to. ⛔ `code_root` is emitted only where there is
        # one, rather than emitted as the first of several: a reader of this
        # output has no way to tell a single root from a silent pick, and that
        # key is the one every role's own report is written from.
        if len(self.views) == 1:
            out["code_root"] = os.path.abspath(self.only_root.code_root)
        out["code_roots"] = {
            key: {
                "code_root": os.path.abspath(view.code_root),
                "repo": view.get("host.repo"),
            }
            for key, view in self.views.items()
        }
        out["config"] = self.data
        out["unavailable"] = self.unavailable()
        return out


# --- validation ------------------------------------------------------------
#
# Each rule names the section of the surface it enforces. The rules are
# procedure -- the surface's own boundary rule puts them in a skill rather than
# in the configuration -- but every *value* and every *key* they test against is
# read from the surface above, so nothing here has to be edited when a
# vocabulary grows or a facet gains a key.

# ⛔ There is no table of required keys here, and there must not be one again.
# Requiredness is read off the surface's `# required` marker, exactly as a
# default is read off `# default` -- see `surface_facts`. What the table cost
# while it existed: its entries paraphrased the sections they cited, nothing
# could hold the paraphrase to the original, the judgement calls it encoded
# (`carriers` required, `day_log.out_dir` not) were stated in no section, and
# the self-test generated its missing-key assertions from the table, so
# deleting an entry deleted the enforcement and its only assertion together --
# silently green. Adding a required key is now a marker on the surface and
# nothing here.

# Keys the surface used to declare and no longer does, each with where the fact
# lives now. A retired key is **refused**, not ignored: `roots.skills` was
# declared, written in every configuration and read by nothing, so a project
# that pointed it at a subdirectory was ignored in silence -- and a stale file
# that still carries it would be that same silence surviving the removal. The
# self-test holds each entry to the surface in both directions, so re-declaring
# one there reddens the build rather than making every configuration unreadable.
#
# ⛔ The **set** is held to the surface too, by `retired_keys` below, and that is
# a separate arm from holding each entry: without it, deleting an entry here
# deleted the refusal and its only assertion together and left the suite green --
# measured, with the reader accepting `version: 1` again. That is the defect the
# retired `REQUIRED` table demonstrated, in the one list still shaped like it.
RETIRED = [
    (
        "roots.skills",
        "the skills root is the directory the role was invoked in, which no "
        "configuration can state -- it is where this file is found. See § 1, "
        "`The skills root is where the role runs`. Delete the key",
    ),
    (
        "roots.code_is_own_repo",
        "whether a code root is a repository of its own is established at the "
        "root where a rule wants it -- `rev-parse --show-toplevel` there, with "
        "`.gitmodules` separating a submodule from an ignored nested repository "
        "-- and the two rules keyed to it are addressed to a person. No script "
        "and no role ever read the key. See § 1. Delete the key",
    ),
    (
        "version",
        "requiredness and the absent case are marked beside each key on the "
        "surface, so a configuration states its decision or is refused with the "
        "key named, and no revision is left to separate the two. See "
        "§ `The file itself`. Delete the key",
    ),
    (
        "done.run",
        "a done check carries no command. The command, what its pass proves, "
        "what defeats a cached pass, what it needs before it can run and when "
        "its verdict is the one to read are a `checks_local` entry's, and a "
        "`local` check reads that facet for its source. See § 17. Move the "
        "command to `checks_local` and delete the key",
    ),
]

# A retired key sits at a path, and a path may cross a list: § 13's entries are
# list members, so the surface declares `done.run` once and a configuration
# writes it on whichever entry carries it. The indices come out before the
# comparison, and the refusal names the path the configuration actually carries
# -- `done[0].run` -- because that is what the person editing the file sees.
INDEX = re.compile(r"\[\d+\]")

# A facet whose carrier is `none` states why. This is the line between a
# deliberate absence and an unset value, and it is the whole reason the two can
# be told apart at all. ⛔ Which facets those are is **not** listed here either:
# it is the `# absent_reason` marker beside each `carrier` line on the surface,
# so a facet that grows a real absent case declares it once, where it is
# declared, and both this rule and `unavailable()` pick it up.

# Alternations the surface states for a *context* rather than for a key of its
# own: a status's `role` and `writer`, a readiness entry's `check` and
# `on_fail`, and the carrier any role may take. Each is enforced where that
# context occurs, below, so these are the only alternation paths this module
# names. Everything else the surface states as an alternation is enforced at
# the key that states it, derived rather than listed -- otherwise the surface's
# "the reader accepts what the alternation states and nothing else" would hold
# only as far as whoever last remembered to extend a list here. It did not:
# `day_log.round_ties`, `day_log.sections` and `work_item.estimate.unit` were
# each stated as a closed set and accepted anything.
# § 6's one conditional committing role, and the third of it that decides the
# condition. ⛔ Two names rather than a rule written out: the surface states that
# the bookkeeping role's commit is a third of that role
# ([§ 6](#what-staging-is-per-and-the-two-rules-that-hold-regardless)), and these
# are the spellings it states the role and the third under. A reader working the
# condition out of `carriers` alone would require a staging mode of a project
# whose bookkeeping role never commits.
SESSION_ROLE = "session"
COMMIT_THIRD = "commit"
# § 25's two spellings, which are the same string and are not the same fact: the
# first is the third's name inside `session.parts` and the second is the block's
# own key. ⛔ Apart on purpose, for the reason the pair above it is: a rule reading
# one of them where it means the other is the defect these constants exist
# against, and the two could legitimately diverge.
MEMORY_THIRD = "memory"
MEMORY_KEY = "memory"

CONTEXTUAL = {
    "role",
    "writer",
    "check",
    "on_fail",
    "carriers.day_log",
    # § 13's two, written under the key they belong to rather than bare. That is
    # not decoration: a second `check` alternation would have been read as the
    # same context as § 5's and lost -- the first statement of a path wins -- so
    # the done library would have been enforced as the readiness one.
    "done.check",
    "done.answered_by",
}


# § 13 binds four of its five checks to an answerer and leaves `checklist_ticked`
# to the project. Spelled out here for the same reason the sentinels above are,
# and held to the surface by the same loop: which member of a set a rule turns on
# is the part an alternation cannot state. A check the surface adds without a
# binding simply does not appear here and is the project's to answer either way.
BOUND_ANSWERERS = {
    "gate_green": "procedure",
    "local": "procedure",
    "human_verification": "human",
    "merged": "procedure",
}


def _normalised_command(command: str) -> str:
    """A command as written, with its runs of whitespace normalised.

    The whole of the normalisation, deliberately: § 13 states that the
    comparison is otherwise the command as both sides wrote it, so a project
    writing one command two genuinely different ways has two commands here.
    That errs towards accepting a duplicate rather than towards refusing a
    legitimate check, which is the direction a refusal has to err in.

    ⚠️ Whitespace is the one thing collapsed rather than merely trimmed, and the
    first form of this said *surrounding* whitespace while doing more: a command
    spelled with two spaces between its words is the same command to any shell,
    so treating it as a second one would refuse a duplicate the rule means to
    catch. § 13 says the same, having been corrected with this.
    """
    return " ".join(command.split())


def _path_filter(node: dict, where: str) -> None:
    """§ 2's path filter, held to being a list of globs where it is stated.

    Read by `host_checks.py`, which answers whether a mirroring run reaches a
    change, and held to a shape for the reason § 13's `run` is: a single glob
    written as a string is the natural mistake, and it stringifies into
    something a comparison would walk character by character. ⚠️ Both levels go
    through here, so the entry's filter and a job's are held identically -- a
    shape rule that applied to one of them would be read as a statement about
    the other.

    ⛔ The **key's presence** is what is read, not its value, which is § 2's rule
    for every key here whose absence is itself an answer: a filter omitted means
    the level carries none, while one written with nothing after it is the same
    text as a filter somebody meant to write.
    """
    if "paths" not in node:
        return
    value = node["paths"]
    if not isinstance(value, list) or not value:
        raise ConfigError(
            where,
            f"is {value!r}; § 2 states a path filter as a list of globs, or "
            "omitted where that level carries none. A single glob written as a "
            "string is read as a list of its characters by anything that walks "
            "it, and an empty list is the key written blank -- which § 2 refuses "
            "rather than reading as the absence it looks like.",
        )
    for position, pattern in enumerate(value):
        if not isinstance(pattern, str) or not pattern.strip():
            raise ConfigError(
                f"{where}[{position}]",
                f"is {pattern!r}; each entry of a path filter is a glob (§ 2). A "
                "blank one matches nothing while reading as a filter somebody "
                "wrote.",
            )


# § 2's trigger grammar, in one place. The event, the types of it the workflow
# listens for, and the ref the run is against -- and ⛔ a second spelling of this
# anywhere is the defect the facet exists against, a key stated in two
# vocabularies being the thing § 17 refuses for the half of it that it owns.
#
# ⚠️ It is a parse and not a refusal: § 2 holds no pattern to this shape, a
# trigger a consumer cannot read being no answer about the run rather than a
# configuration to reject. What `_triggers` below refuses is the *clause* rules
# the surface does state, which are reachable only once a pattern has parsed.
TRIGGER = re.compile(
    r"^\s*(?P<event>[A-Za-z_][\w-]*)"
    r"(?:\s*\((?P<types>[^()]*)\))?"
    r"\s*->\s*(?P<ref>\S.*?)\s*$"
)

# What a trigger states as its ref where it filters on none (§ 2), and what
# `host.pull_request_title.into` states to be held on every pull request. ⛔ One
# spelling for one vocabulary: the title facet states its refs in a trigger's
# own, and a second literal would be a second vocabulary for the same fact.
ANY_REF = "*"

# Where a work item's identifier goes inside `host.pull_request_title.reference`
# (§ 2). ⛔ The reference is a form and not a pattern, because the one statement
# has two readers and only one of them is matching: a role *writes* a title, so
# what it reads has to say where the identifier it already holds belongs.
PLACEHOLDER = "<number>"


def parse_trigger(pattern: str):
    """(event, types, ref) for one § 2 trigger, or None where it does not parse.

    `types` is the list the clause states, or None where the pattern carries no
    clause at all -- which § 2 makes two different statements: no clause means
    the workflow's event block states no `types:` key, and is never read as the
    host's default set for that event.
    """
    match = TRIGGER.match(pattern)
    if not match:
        return None
    clause = match.group("types")
    types = None if clause is None else [t.strip() for t in clause.split(",")]
    return match.group("event"), types, match.group("ref")


def _type_clauses(value, where: str) -> None:
    """§ 2's two clause refusals, over patterns already held to their shape.

    ⛔ Reached from both ends of the one mapping -- `host.checks[].triggers` and
    § 17's `counts_when`, which is stated in the same form -- because a refusal
    one of them has and the other does not is the two vocabularies § 17 refuses,
    arriving as behaviour instead of as text.

    ⚠️ The pattern itself is not held: § 2 refuses none, a trigger a consumer
    cannot read being no answer about the run. What this rejects is a clause
    written empty and a type written blank inside one -- each the same text as
    something somebody meant to write, which is why neither is read as the
    absence it looks like.
    """
    patterns = value if isinstance(value, list) else [value]
    for position, pattern in enumerate(patterns):
        parsed = parse_trigger(pattern)
        if parsed is None:
            continue
        _event, types, _ref = parsed
        if types is None:
            continue
        at = f"{where}[{position}]" if isinstance(value, list) else where
        if types == [""]:
            raise ConfigError(
                at,
                f"is {pattern!r}, whose type clause is empty; § 2 refuses that "
                "rather than reading it as the absence it looks like. A trigger "
                "whose workflow filters on no type states no clause at all, and "
                "one that meant to state its types and stated none is the same "
                "text.",
            )
        if any(not t for t in types):
            raise ConfigError(
                at,
                f"is {pattern!r}, whose type clause states a blank type (§ 2). "
                "It matches no event the host sends while reading as a type "
                "somebody wrote.",
            )


def _triggers(entry: dict, where: str) -> None:
    """§ 2's `triggers`, held to its shape and then to its clause rules.

    Read by `host_checks.py`, which answers from the parse above whether a
    mirroring run reaches a change, and held anyway for the reason
    `_path_filter` is: the natural mistakes here are silent ones.
    """
    if "triggers" not in entry:
        return
    value = entry["triggers"]
    patterns = value if isinstance(value, list) else [value]
    if not patterns or any(
        not isinstance(p, str) or not p.strip() for p in patterns
    ):
        raise ConfigError(
            where,
            f"is {value!r}; § 2 states a trigger as `<event>(<types>) -> <ref>`, "
            "one pattern or a list of them where a workflow has more than one. "
            "Written blank it states what starts a run while naming no event, "
            "and a conjunction improvised inside one string is the shape the "
            "list exists instead of.",
        )
    _type_clauses(value, where)


def _mirrored_commands(data: dict) -> dict[str, str]:
    """Normalised command -> where the host's runs mirror it (§ 2).

    The value is the phrase § 13's refusal names, so a collision reports the
    **job** where a job is what mirrors the command and the workflow where the
    entry does. A map to the workflow alone would answer a question § 2 stopped
    asking: one entry can now carry four commands, and *the `Checks` workflow
    already mirrors it* is the per-workflow answer this form exists to replace.

    Both forms are walked, and ⛔ **an entry stating both is refused**: § 2 makes
    them exclusive, and a reader preferring one would decide a question the
    surface answers. An entry stating neither mirrors nothing, which is the
    shape a workflow with no local counterpart has always had.

    ⚠️ A shape the facet cannot be read in is refused rather than skipped, and
    the refusals are the walk's below rather than this function's -- skipping
    any of them would empty this map in silence, and a collision check with
    nothing in its map is a check that reports green. Measured on this
    function's first form, which refused an unreadable `mirrors` and then
    tolerated the two shapes one key up: a `host.checks` written as a string or
    a mapping, or an entry written as a bare command, each let every colliding
    `run` load clean. `host.checks` is required and non-empty-checked and had
    never been type-checked, so the shapes were harmless until something read
    the entries.
    """
    out: dict[str, str] = {}
    for record in mirrored_runs(data):
        out.setdefault(record["normalised"], record["mirrored_by"])
    return out


def mirrored_runs(data: dict) -> list[dict]:
    """Every mirrored command the facet states, with the run that answers it.

    § 2's facet as a consumer reads it, walked **once** here rather than once
    per consumer: the mapping, what starts the run, and the path filters at the
    two levels the surface states them at. The map above is this list keyed, and
    `host_checks.py` is the consumer that answers from the rest of it -- ⛔ two
    walks of one facet being two readings allowed to disagree about what the
    project wrote, which is the defect the facet exists to delete one level up.

    ⚠️ The entry's filter and the job's are carried **separately**, because § 2
    makes neither inherited and neither an override: a command's run covers a
    change within both, and a merged filter could not say which level excluded
    it. `triggers` stays the entry's for the same section's reason -- the event
    block is the workflow's and no job's -- and is carried on every record of
    that entry rather than resolved here, a consumer with no trigger to match
    having no answer rather than a default.

    ⚠️ A shape this cannot read is refused rather than skipped -- the list and
    an entry here, and a `mirrors`, a `jobs`, a member of one, a trigger and a
    path filter below. Skipping any of them empties this list in silence, and
    both consumers of it report an absence where the project stated a run.
    """
    out: list[dict] = []
    for run in host_runs(data):
        for mirrored in run["commands"]:
            out.append(
                {
                    "command": mirrored["command"],
                    "normalised": mirrored["normalised"],
                    "mirrored_by": mirrored["mirrored_by"],
                    "workflow": run["workflow"],
                    "job": mirrored["job"],
                    "triggers": run["triggers"],
                    "paths": {"workflow": run["paths"], "job": mirrored["paths"]},
                }
            )
    return out


def host_runs(data: dict) -> list[dict]:
    """§ 2's `host.checks` as one record per **entry**, walked once.

    The facet keyed by the one key it has, with every refusal the facet carries
    in this one walk. `mirrored_runs` above is this list exploded per mirrored
    command, and the drift check beside it reads it per entry -- ⛔ two walks of
    one facet being two readings allowed to disagree about what the project
    wrote, which is the defect the facet exists to delete one level up.

    ⚠️ **An entry mirroring nothing is a record here and no record there**, and
    that is the whole reason this accessor exists beside the other: § 2 makes the
    facet the single statement of which runs *exist*, so a run with no local
    counterpart is an entry stating neither `mirrors` nor `jobs` -- which a
    per-command view legitimately drops and a check holding the facet to the
    host's own definitions may not.
    """
    checks = _absent_as(_get(data, "host.checks"), [])
    if not isinstance(checks, list):
        raise ConfigError(
            "host.checks",
            f"is {type(checks).__name__}, and § 2 states it as the host's runs -- "
            "a list of entries, or `[]` where every verdict is local. § 13's "
            "refusal reads them to find a done check the host already runs, and "
            "would hold nothing against a shape it cannot walk.",
        )
    out: list[dict] = []
    for index, entry in enumerate(checks):
        if not isinstance(entry, dict):
            raise ConfigError(
                f"host.checks[{index}]",
                f"is {entry!r}, and has to be a mapping stating at least a "
                "`workflow` (§ 2). An entry this reader cannot walk takes "
                "whatever it mirrors out of § 13's refusal in silence.",
            )
        out.append(_entry_run(entry, index))
    return out


def _entry_run(entry: dict, index: int) -> dict:
    """One entry's record: every fact § 2 states about the run, held to its shape.

    `commands` is the per-command half, one member per command this entry
    mirrors and empty where it mirrors none.
    """
    where = f"host.checks[{index}]"
    workflow = _entry_workflow(entry, where)
    _path_filter(entry, f"{where}.paths")
    # ⛔ The entry's and never a job's: § 2 puts the event block on the workflow,
    # so a `triggers` inside a `jobs` member is a key nothing states and nothing
    # would read.
    _triggers(entry, f"{where}.triggers")
    return {
        "index": index,
        "where": where,
        "workflow": workflow,
        "triggers": entry.get("triggers"),
        "paths": entry.get("paths"),
        "jobs": entry.get("jobs") if "jobs" in entry else None,
        "commands": list(_entry_commands(entry, index)),
    }


def _entry_workflow(entry: dict, where: str) -> str:
    """The key the whole facet is keyed on, held because an entry without one has none.

    It read as `unnamed` before: every entry missing a workflow collapsed into
    one answer, and § 13's refusal then named a workflow no file contains.
    """
    workflow = entry.get("workflow")
    if not isinstance(workflow, str) or not workflow.strip():
        raise ConfigError(
            f"{where}.workflow",
            f"is {workflow!r}; § 2 keys an entry by its workflow's name, so an "
            "entry stating none has no key. Every consumer reads this facet by "
            "that name, and a refusal naming a workflow nothing is called sends "
            "a reader to a file their repository does not have.",
        )
    return workflow


def _entry_commands(entry: dict, index: int):
    """Yield one record per command this entry mirrors.

    The two forms § 2 states, read in one place so that neither can grow a
    refusal the other does not have. An entry stating neither yields nothing,
    which is a run the host makes with no local counterpart -- `host_runs`
    above is the walk that still carries it.

    Each record carries the command as written, its normalised form, the phrase
    naming where it is mirrored, the job's id where a job is what mirrors it,
    and that job's own path filter. ⚠️ The entry's own facts -- its workflow,
    its triggers and its filter -- sit on the entry's record rather than being
    copied onto each of these, `mirrored_runs` being what joins the two.
    """
    where = f"host.checks[{index}]"
    workflow = _entry_workflow(entry, where)

    def record(command: str, mirrored_by: str, job: str | None, filters) -> dict:
        return {
            "command": command,
            "normalised": _normalised_command(command),
            "mirrored_by": mirrored_by,
            "job": job,
            "paths": filters,
        }

    # Presence and never value, for both keys below: a `mirrors` written with
    # nothing after it would otherwise satisfy the exclusivity rule and the
    # absence rule at once, so an entry could state both forms and be read as
    # stating one.
    if "jobs" in entry and "mirrors" in entry:
        raise ConfigError(
            f"{where}.jobs",
            "is stated beside a `mirrors` on the same entry, and § 2 makes the "
            "two exclusive: whichever one an entry states is the whole of what "
            "it mirrors. Read together they leave a consumer choosing which of "
            "two statements of one fact to believe.",
        )
    if "mirrors" in entry:
        if entry["mirrors"] is None:
            raise ConfigError(
                f"{where}.mirrors",
                "is written with nothing after it, which § 2 refuses rather than "
                "reading as the absence it looks like: an entry mirroring no "
                "local command states neither this key nor `jobs`, and one that "
                "meant to state a command and stated none is the same text.",
            )
        yield record(
            _command(entry["mirrors"], f"{where}.mirrors"),
            f"the `{workflow}` workflow",
            None,
            None,
        )
        return
    if "jobs" not in entry:
        return
    jobs = entry["jobs"]
    if not isinstance(jobs, list) or not jobs:
        raise ConfigError(
            f"{where}.jobs",
            f"is {jobs!r}; § 2 states it as the jobs of one workflow that mirror "
            "a local command each, and an entry mirroring nothing states neither "
            "this key nor `mirrors`. Written blank it reads as that absence while "
            "looking like a list somebody filled in.",
        )
    for position, job in enumerate(jobs):
        at = f"{where}.jobs[{position}]"
        if not isinstance(job, dict):
            raise ConfigError(
                at,
                f"is {job!r}, and has to be a mapping stating the job's `job` name "
                "and the command it `mirrors` (§ 2).",
            )
        name = job.get("job")
        if not isinstance(name, str) or not name.strip():
            raise ConfigError(
                f"{at}.job",
                f"is {name!r}; § 2 states the job's id as the workflow file spells "
                "it. Without it nothing can ask the host about this command's own "
                "job, which is the whole of what this form adds.",
            )
        if job.get("mirrors") is None:
            raise ConfigError(
                f"{at}.mirrors",
                "is required (§ 2): a job mirroring no local command is left out "
                "of the list rather than written into it with nothing to mirror.",
            )
        _path_filter(job, f"{at}.paths")
        yield record(
            _command(job["mirrors"], f"{at}.mirrors"),
            f"the `{name}` job of the `{workflow}` workflow",
            name,
            job.get("paths"),
        )


def host_runner(data: dict) -> dict | None:
    """§ 2's `host.runner`, held to its shape, or `None` where none is stated.

    The one facet of § 2 that is the **project's** rather than an entry's: it
    states one answer for every job the host runs, which is why it is walked
    here beside the per-entry accessors rather than inside one.

    ⛔ `None` is the stated absence and not a gap -- § 2 makes the block omitted
    where the host kind's own default runner is the answer, and that default is
    the host's and is carried nowhere on this surface. A reader that invented
    one would hold every workflow file to a label the project never chose.

    ⛔ **Presence and never truthiness**, which is § 2's rule for every key here
    whose absence is itself an answer: `supersedes:` written with nothing after
    it is the same text as one somebody meant to fill in, and the omission that
    means *no run of this project's retires another* is the key not being there.
    """
    block = _get(data, "host.runner")
    if block is None:
        return None
    if not isinstance(block, dict):
        raise ConfigError(
            "host.runner",
            f"is {block!r}; § 2 states it as the block saying where this project's "
            "jobs run -- a label, the account's capacity and one job's budget. "
            "Omitted, it means the host kind's own default answers; written as "
            "anything else it reads as a statement and holds nothing.",
        )
    # ⛔ Stated, the block states all three. § 2 defaults none of them: each is a
    # measurement of an account rather than a preference about it, and the
    # permissive direction is what makes that matter -- a budget nobody wrote is
    # a generated job that can hold the only runner there is for as long as it
    # likes, while every reader reports the runner as configured.
    for key in ("label", "concurrent_jobs", "budget_minutes"):
        if block.get(key) in (None, ""):
            raise ConfigError(
                f"host.runner.{key}",
                "is missing. § 2 states all three of `label`, `concurrent_jobs` and "
                "`budget_minutes` wherever the block is stated at all, and defaults "
                "none of them.",
            )
    label = block["label"]
    if not isinstance(label, str) or not label.strip():
        raise ConfigError(
            "host.runner.label",
            f"is {label!r}; § 2 states it as the label every job of this project's "
            "workflows states. A job asking for a label the account has no runner "
            "for never starts at all, so a value nothing can match is a check that "
            "never reports rather than one that fails.",
        )
    for key in ("concurrent_jobs", "budget_minutes"):
        value = block[key]
        # ⛔ `bool` is excluded by name, as § 10's `cap` excludes it: it is an
        # `int` in this language, so `concurrent_jobs: true` would read as a
        # single-runner account and turn every budget into a queue budget on a
        # project that said no such thing.
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ConfigError(
                f"host.runner.{key}",
                f"is {value!r}; it is a whole number of at least one (§ 2). An "
                "account that takes no job at once runs nothing, and a budget below "
                "one minute is a job cancelled before it can start.",
            )
    supersedes = block.get("supersedes")
    if "supersedes" in block and (
        not isinstance(supersedes, str) or not supersedes.strip()
    ):
        raise ConfigError(
            "host.runner.supersedes",
            f"is {supersedes!r}; § 2 states it as the group a newer run retires an "
            "older one in, and omits the key where none does. Written blank it is "
            "the same text as a group somebody meant to name, and the two readings "
            "send a consumer meeting a cancelled run opposite ways.",
        )
    return {
        "label": label.strip(),
        "concurrent_jobs": block["concurrent_jobs"],
        "budget_minutes": block["budget_minutes"],
        "supersedes": supersedes.strip() if isinstance(supersedes, str) else None,
        # ⚠️ Derived and not a key: § 2 states that `concurrent_jobs` is what
        # gives the budget its meaning, so the one fact a consumer reads off the
        # pair is carried here rather than recomputed per reader.
        "budget_is_a_queue_budget": block["concurrent_jobs"] == 1,
    }


def host_pull_request_title(data: dict) -> dict | None:
    """§ 2's `host.pull_request_title`, held to its shape, or `None` where none is stated.

    The facet beside `host.runner` and the project's rather than an entry's for
    the same reason: it states one answer for every pull request this project
    opens. ⛔ `None` is the stated absence -- a project whose titles are prose
    has no rule for anything to hold them to, and a reader inventing one would
    refuse every title that project has ever written.

    ⛔ **Shape only, and no derivation.** What the form composes into -- the
    expression a gate enforces, the title a role writes -- is one derivation
    read through its own consumer, so a second one here would be free to
    disagree with the file that gets installed.
    """
    block = _get(data, "host.pull_request_title")
    if block is None:
        return None
    if not isinstance(block, dict):
        raise ConfigError(
            "host.pull_request_title",
            f"is {block!r}; § 2 states it as the block saying what a pull request "
            "title opens with -- one reference, whether more than one may appear, "
            "and the base refs a title is held on. Omitted, it means titles here "
            "carry no reference; written as anything else it reads as a statement "
            "and holds nothing.",
        )
    reference = block.get("reference")
    if not isinstance(reference, str) or not reference.strip():
        raise ConfigError(
            "host.pull_request_title.reference",
            f"is {reference!r}; § 2 states it as one work-item reference, with "
            f"`{PLACEHOLDER}` standing where the identifier goes.",
        )
    # ⛔ Exactly one placeholder, and both directions refused. ⚠️ Neither is a
    # shape a reader could repair: none leaves the finishing role with no place
    # to put the identifier it is writing the title for -- a value that reads as
    # a form and renders nothing -- and several leave it with no answer about
    # which identifier is which, on a facet whose whole point is that one
    # statement serves the role and the gate alike.
    occurrences = reference.count(PLACEHOLDER)
    if occurrences != 1:
        raise ConfigError(
            "host.pull_request_title.reference",
            f"is {reference!r}, which states `{PLACEHOLDER}` {occurrences} times; "
            "§ 2 states it exactly once. A reference with no place for the "
            "identifier is one no role can render a title from, and a reference "
            "with two says nothing about which identifier is which.",
        )
    # ⛔ A flag and never truthiness, which is this surface's rule for every key
    # whose two values send a consumer opposite ways: `repeated: "no"` is a
    # non-empty string, so a reader asking whether it is set would admit more
    # than one reference on a project that wrote the opposite word.
    repeated = block.get("repeated")
    if not isinstance(repeated, bool):
        raise ConfigError(
            "host.pull_request_title.repeated",
            f"is {repeated!r}; § 2 states it as a flag, written wherever the block "
            "is written and defaulted neither way. A form admitting one reference "
            "refuses what a role writes for a change closing two items, and a form "
            "admitting several admits what a project meant to refuse.",
        )
    into = block.get("into")
    if not isinstance(into, list) or not into:
        raise ConfigError(
            "host.pull_request_title.into",
            f"is {into!r}; § 2 states it as the base refs a title is held on, in a "
            f"trigger's own ref vocabulary, with {ANY_REF!r} for every pull "
            "request. An empty list is a gate that never fires while reading as "
            "one that does.",
        )
    for index, ref in enumerate(into):
        if not isinstance(ref, str) or not ref.strip():
            raise ConfigError(
                f"host.pull_request_title.into[{index}]",
                f"is {ref!r}; each member is one base ref pattern, and a blank one "
                "is the same text as a pattern somebody meant to write.",
            )
    return {
        "reference": reference,
        "repeated": repeated,
        "into": [ref.strip() for ref in into],
    }


def _command(mirrors, where: str) -> str:
    """The one command a `mirrors` states, wherever it sits.

    ⛔ A list is refused here and was tolerated before § 2 stated the second
    form: several commands behind one workflow name are the jobs that mirror
    them, each stating its own, so a list would be a second shape for a fact the
    surface now states once -- and the one that cannot say which command a
    filter or a job name belongs to. § 13's refusal reads this to find a done
    check the host already runs, and would hold nothing against a shape it
    cannot read.
    """
    if not isinstance(mirrors, str):
        raise ConfigError(
            where,
            f"is {mirrors!r}, and § 2 states one local command per `mirrors`. "
            "Several behind one workflow name are its `jobs`, each mirroring the "
            "command its own run answers about.",
        )
    return mirrors


def _every_key(data, prefix: str = ""):
    """Yield (bare key, the path it sits at) for every key in a configuration.

    At any depth and through lists, which is what the marker's own statement on
    the surface asks for.
    """
    if isinstance(data, dict):
        for key, value in data.items():
            # ⚠️ A non-string key is quoted in the path, because YAML admits one
            # and `on:` reads back as `True`: a refusal naming `True.audit_trail`
            # sends a reader to a key their file does not contain, out of the one
            # module whose whole promise is naming the key.
            path = f"{prefix}{key}" if isinstance(key, str) else f"{prefix}{key!r}"
            yield str(key), path
            yield from _every_key(value, f"{path}.")
    elif isinstance(data, list):
        for index, item in enumerate(data):
            yield from _every_key(item, f"{prefix[:-1]}[{index}].")


def _memory(data: dict, parts: list) -> None:
    """§ 25's block, against the third that writes it.

    ⛔ **Both directions, because the two misconfigurations fail opposite ways.**
    A store configured where the third does not run is a path nothing ever writes,
    which reads from the configuration exactly like a store that is kept current.
    A third that runs with `carrier: none` is the role choosing a path of its own,
    which is the one fact § 25 exists to have given it.

    ⚠️ The shape rules alone. Whether `carrier` is written at all is the surface's
    `# required` marker, which values it and `write_from` may take is its
    alternation, and whether `store`, `index` and `write_from` are written is its
    conditional marker -- each performed by the generic rules above. What is left
    here is the agreement with `session.parts`, the keys a carrier cannot read,
    and the one pairing of two stated values that is the hazard as a permission.
    """
    carrier = _get(data, f"{MEMORY_KEY}.carrier")
    # ⛔ A shape rule answers what a value has to be and never whether it is
    # written: requiredness is the `# required` marker, enforced above, and a
    # rule refusing absence here would state one fact twice -- outliving the
    # first the day a resolved surface stops marking the key (§ 1).
    if carrier is None:
        return

    runs = MEMORY_THIRD in parts
    if runs and carrier == "none":
        raise ConfigError(
            f"{MEMORY_KEY}.carrier",
            f"is `none` while `session.parts` names the `{MEMORY_THIRD}` third "
            "(§ 25), which is a third mapped to write a store the project says it "
            "keeps none of. A role meeting that writes to a path of its own "
            "choosing -- under a derived location, a different path in every tree, "
            "reported as a save that succeeded. State a carrier, or drop the third.",
        )
    if not runs and carrier != "none":
        raise ConfigError(
            f"{MEMORY_KEY}.carrier",
            f"states a memory store while `session.parts` does not run the "
            f"`{MEMORY_THIRD}` third, so nothing here ever writes it (§ 25). A "
            "store configured for a third nothing runs reads from the "
            "configuration exactly like one being kept current. Run the third, or "
            "state `carrier: none` with the reason.",
        )

    # ⛔ Refused rather than accepted and unread, carrier by carrier: a key naming
    # a location nothing opens is a project believing its store is pinned while
    # every tree still derives its own.
    unread = {
        "derived": (
            ("store", "index"),
            "Under that carrier the harness decides where the store is and the "
            "procedure resolves nothing inside it, so this key is read by nothing "
            "while reading as a store somebody pinned. State `carrier: path` with "
            "the store, or drop the key.",
        ),
        "none": (
            ("store", "index", "write_from"),
            "Under that carrier the memory third does not run, so there is nothing "
            "to write and nobody to read this. Run the third with a carrier, or "
            "drop the key.",
        ),
    }.get(carrier)
    if unread:
        keys, why = unread
        for key in keys:
            if _has(data, f"{MEMORY_KEY}.{key}"):
                raise ConfigError(
                    f"{MEMORY_KEY}.{key}",
                    f"is written beside `carrier: {carrier}` (§ 25). {why}",
                )
    index = _get(data, f"{MEMORY_KEY}.index")
    if isinstance(index, str) and (
        os.path.isabs(index) or ".." in index.replace("\\", "/").split("/")
    ):
        # ⛔ The store is the unit this facet addresses, so an index outside it is
        # a second store with one file in it, pointed at by the key that was
        # meant to name the first one's. ⚠️ Refused here rather than at the write,
        # where a role meeting it has already resolved a path it may not write.
        raise ConfigError(
            f"{MEMORY_KEY}.index",
            f"is {index!r}, which reaches outside the store (§ 25). It names the "
            "one file inside `store` that every session reads -- an absolute path "
            "or one climbing out with `..` makes it a second store with a single "
            "file in it, under the key that was supposed to name the first one's.",
        )
    if carrier == "derived" and _get(data, f"{MEMORY_KEY}.write_from") == "any_tree":
        # ⛔ The one pairing of two individually legal values that is the hazard
        # itself, and the one rule here no single-key marker reaches. Under a
        # derived store *wherever the session is standing* is a different store,
        # so this pair licenses exactly the write § 25 is written to stop -- and
        # licenses it in the shape that reports success.
        raise ConfigError(
            f"{MEMORY_KEY}.write_from",
            "is `any_tree` beside `carrier: derived` (§ 25), which is the hazard "
            "written as a permission: a derived store is derived from the working "
            "directory, so a save from a tree writes a store the checkout never "
            "reads and reports that it succeeded. Pin the store with "
            "`carrier: path`, or state `main_tree` and let the third refuse from "
            "a tree.",
        )


def validate(data: dict, facts: dict) -> None:
    # ⛔ Walked rather than looked up by path, because a retired key may sit
    # inside a list: `_get` descends a dict and returns the default the moment it
    # meets one, so `done.run` read that way is a refusal that never fires on the
    # only shape a project can write it in -- silently, and green.
    retired = {path for path, _ in RETIRED}
    for _key, at in _every_key(data):
        path = INDEX.sub("", at)
        if path in retired:
            where = next(reason for name, reason in RETIRED if name == path)
            raise ConfigError(at, f"is retired -- {where}.")

    # A key the surface marked procedure, wherever a configuration put it. The
    # section the clause sits under is what the refusal cites, so the rule's own
    # statement is what a reader is sent to rather than a gloss written here.
    marked = facts.get("procedure") or {}
    if marked:
        for key, path in _every_key(data):
            heading = marked.get(key)
            if heading:
                raise ConfigError(
                    path,
                    f"is procedure, not configuration -- the rule it would turn off is "
                    f"stated under § {heading}, and no key on the surface turns it off. "
                    "Delete the key.",
                )

    for path, section in sorted(facts["required"].items()):
        where = f"marked `# required` under § {section}"
        if not _has(data, path):
            raise ConfigError(path, f"required -- {where}.")
        # Present and empty is not present. YAML reads a key with nothing after
        # it as null, which satisfied a presence test and then arrived in a
        # path join as None -- a traceback naming no key, out of the one module
        # whose whole promise is naming the key.
        if _get(data, path) is None:
            raise ConfigError(path, f"is empty -- {where}.")

    # The same question asked where the surface states a condition for it. ⛔ A
    # configuration that does not meet the condition is not merely unchecked
    # here: the key is meaningless under any other value, so its absence is
    # correct and its presence is somebody else's business (§ 3's blocks are the
    # case this is for -- `board` addresses a Trello board and nothing else).
    for (path, on, value), section in sorted(facts["required_when"].items()):
        if _get(data, on) != value:
            continue
        where = f"marked `# required_when: {on} = {value}` under § {section}"
        if not _has(data, path):
            raise ConfigError(
                path, f"required where `{on}` is `{value}` -- {where}."
            )
        if _get(data, path) is None:
            raise ConfigError(path, f"is empty -- {where}.")

    for path, allowed in sorted(facts["enums"].items()):
        if path in CONTEXTUAL or not _has(data, path):
            continue
        value = _get(data, path)
        # An alternation constrains a value that is stated; it says nothing
        # about one that is absent. Several keys are null under a condition the
        # surface states beside them -- `work_in_shared_checkout` under
        # `in_place` is the case that found this -- and whether a key may be
        # absent at all is `REQUIRED`'s question, answered above.
        if value is None:
            continue
        if value not in allowed:
            raise ConfigError(
                path, f"is {value!r}; the surface allows {' | '.join(allowed)}."
            )

    for facet in sorted(facts["absent_reason"]):
        if _get(data, f"{facet}.carrier") == "none" and not _get(
            data, f"{facet}.absent_reason"
        ):
            raise ConfigError(
                f"{facet}.absent_reason",
                "required when the carrier is `none`. A deliberately absent "
                "facet states its reason; an unset one is a misconfiguration, "
                "and the two read identically without it.",
            )

    # § 11. Three facts are in hand by the time this runs -- the branch model,
    # the store's path and whether it is committed -- so the section's in-tree
    # rule is decidable rather than advisory, and refusing it here is the
    # standard that section sets for itself when it declines to state a
    # threshold nothing could enforce.
    if _get(data, "context.artifacts.carrier") == "file":
        directory = _get(data, "context.artifacts.dir")
        if not directory:
            raise ConfigError(
                "context.artifacts.dir",
                "required when the carrier is `file`: there is nowhere for an "
                "artifact to be written, and a role would discover that at the "
                "boundary it was meant to survive (§ 11).",
            )
        committed = _get(data, "context.artifacts.committed")
        if not isinstance(committed, bool):
            raise ConfigError(
                "context.artifacts.committed",
                f"is {committed!r}; it takes true or false (§ 11). It is the "
                "key the in-tree rule hinges on, so a value that merely reads "
                "as truthy would resolve to the permissive arm.",
            )
        # In-tree is a path read relative to the skills root, per § 11: one
        # that is absolute, or begins with a variable the shell expands, is
        # somewhere a tree's teardown cannot reach.
        in_tree = not str(directory).startswith(("/", "$", "~"))
        if in_tree and not committed and _get(data, "branch_model.kind") == "worktree":
            raise ConfigError(
                "context.artifacts.dir",
                f"is {directory!r}, inside the tree, while `committed` is false "
                "and `branch_model.kind` is `worktree`. The teardown takes "
                "everything git does not have, so the plan for the work would "
                "go with the tree it was planning: commit the store, or put it "
                "outside every tree (§ 11).",
            )

    # §§ 4.1 and 4.4. The two keys that are functions of the type, held to its
    # domain. Both are conditional on `type.values` being stated, which is why
    # neither is a `# required` marker: that marker answers "must this key be
    # written at all" and states it does not carry a condition.
    #
    # ⚠️ Only where the type is actually carried. A project whose `type.carrier`
    # is `none` has no domain for either map to be total over, and `values` is
    # then absent legitimately -- so a rule applied unconditionally here would
    # refuse every configuration that deliberately carries no type, which is this
    # repository's own.
    type_values = _get(data, "work_item.type.values")
    if _get(data, "work_item.type.carrier") not in (None, "none") and type_values:
        known = list(type_values)
        # ⛔ The map is read whole rather than through a dotted path per value: a
        # type whose name carries a dot would have the path descend into a
        # nesting that is not there and read as a prefix nobody wrote, which is a
        # refusal against a configuration that is correct.
        prefixes = _get(data, "work_item.type_branch_prefix") or {}
        for value in known:
            if not prefixes.get(value):
                raise ConfigError(
                    f"work_item.type_branch_prefix.{value}",
                    f"is missing, while `work_item.type.values` carries "
                    f"{value!r}. The prefix is a function of the type and a "
                    "function is total over its domain (§ 4.1): an item of this "
                    "type is one no role can cut a branch for, and the gap "
                    "surfaces once the branch is already named.",
                )
        by_type = _get(data, "work_item.template.by_type") or {}
        for keyed in by_type:
            if keyed not in known:
                raise ConfigError(
                    f"work_item.template.by_type.{keyed}",
                    f"keys a template to {keyed!r}, which is not one of "
                    f"`work_item.type.values` ({', '.join(map(str, known))}). "
                    "A template keyed to a type the project cannot assign is a "
                    "template nothing selects, and the filing role's "
                    "type-versus-template cross-check would hold a body against "
                    "a file no item can legitimately have used (§ 4.4).",
                )

    # § 4.6. The one facet another facet's check reads, so what a stated carrier
    # owes is what `queue_position` cannot run without. Whether the carrier is
    # written at all is the surface's `# required` marker; these are held here for
    # the reason § 4.5's `field` is -- the role that meets the gap is a gate
    # refusing an item, which is the one role that may not ask for anything.
    #
    # ⚠️ `None` is in the guard below and is not dead: the suite resolves a copy of
    # the surface with this carrier's `# required` marker stripped, to assert that
    # no rule here answers whether the key is written. Under that surface a
    # configuration carrying no carrier reaches this block, and every rule in it
    # has to stay silent for one.
    priority = _get(data, "work_item.priority.carrier")
    if priority not in (None, "none"):
        values = _get(data, "work_item.priority.values")
        # ⛔ Held to being a list, and the direction that matters is the shape
        # rather than the length: one value is a legitimate axis -- the measured
        # partial one labels its top tier alone -- while a single value written
        # bare reads as a sequence of characters, and the comparison § 5's check
        # performs would then rank two items letter by letter.
        if not isinstance(values, list) or not values:
            raise ConfigError(
                "work_item.priority.values",
                f"is {values!r}; § 4.6 states it as the values the axis holds, "
                "ordered most important first and written as a list even where "
                "there is one. It is the whole of what makes two items "
                "comparable, so a carrier stating none leaves `queue_position` "
                "(§ 5) with nothing to compare.",
            )
        for index, value in enumerate(values):
            if value is None or (isinstance(value, str) and not value.strip()):
                raise ConfigError(
                    f"work_item.priority.values[{index}]",
                    f"is {value!r}, which names no tier (§ 4.6). An entry naming "
                    "nothing still takes a rank in the order while matching no "
                    "item, so every tier below it is compared against one the "
                    "tracker cannot hold.",
                )
        if len(set(map(str, values))) != len(values):
            raise ConfigError(
                "work_item.priority.values",
                f"repeats a value in {values!r}, and § 4.6 reads the list itself "
                "as the order: a tier written twice holds two ranks at once, so "
                "the comparison between those two ranks has no answer.",
            )
        if priority == "label" and not _get(data, "work_item.priority.label_prefix"):
            raise ConfigError(
                "work_item.priority.label_prefix",
                "required when the carrier is `label`: the prefix is what keeps "
                "this axis apart from every other label on an item (§ 4.6), and "
                "without it a reader matching a bare value picks up whatever "
                "else the project happens to label with that word.",
            )
        if priority == "field" and not _get(data, "work_item.priority.field"):
            raise ConfigError(
                "work_item.priority.field",
                "required when the carrier is `field`: there is nowhere to read "
                "the tier from, which is § 4.5's rule for the same carrier on "
                "the date.",
            )
        # ⛔ Who writes it, out of § 4.2's vocabulary and never a second one: the
        # alternation is read from the surface at the path that states it, so a
        # value added there is accepted here with no edit, and a facet that
        # carried its own narrower copy would be free to disagree with it.
        writers = vocabulary(facts, "writer", "a priority writer")
        writer = _get(data, "work_item.priority.writer")
        if writer is None:
            raise ConfigError(
                "work_item.priority.writer",
                "required where a priority is carried: § 4.6 states who writes "
                f"it out of § 4.2's vocabulary ({' | '.join(writers)}). A tier "
                "with no stated writer reads as one any role may set, which is "
                "the derivation § 4.6 forbids.",
            )
        if writer not in writers:
            raise ConfigError(
                "work_item.priority.writer",
                f"is {writer!r}; § 4.6 takes § 4.2's writers "
                f"({' | '.join(writers)}).",
            )
    # ⛔ And the check that reads the facet, refused where the facet is absent
    # rather than left to report itself unanswered on every item forever. ⚠️ The
    # reason quoted is the **project's own**: `absent_reason` says why it carries
    # no tier, and that is the sentence whoever configured this gate has to read.
    # A message of this reader's own would be a second answer to a question the
    # configuration already answers, one facet over.
    #
    # ⚠️ `none` is the whole of the absent case reachable here, and that is the
    # surface's doing rather than an assumption: the `# required` marker above
    # refuses a missing or empty carrier, and the `# absent_reason` loop above
    # refuses `none` with no reason -- so a branch for either would be a branch
    # no configuration can reach and no plant could redden.
    gate = _get(data, "readiness")
    if priority == "none" and isinstance(gate, list) and any(
        isinstance(entry, dict) and entry.get("check") == "queue_position"
        for entry in gate
    ):
        stated = " ".join(str(_get(data, "work_item.priority.absent_reason")).split())
        raise ConfigError(
            "work_item.priority.carrier",
            "is `none` while `readiness` configures `queue_position`, which reads "
            "this facet and nothing else (§ 5). The check would be comparing this "
            "item against work it has no way to rank, and the facet's own stated "
            f"reason for carrying no tier is: {stated!r}. Carry the facet, or drop "
            "the check.",
        )

    # § 10. Where a tree is created is required under the mode that creates trees
    # and meaningless under the mode that does not, which is the shape
    # `work_in_shared_checkout` already has. It is required rather than defaulted
    # because the two measured placements -- beside the shared checkout and
    # nested under the skills root -- are a project's fact, and a default would
    # pick one of them for every project that did not notice the key.
    if _get(data, "branch_model.kind") == "worktree" and not _get(
        data, "branch_model.tree_dir"
    ):
        raise ConfigError(
            "branch_model.tree_dir",
            "required under `kind: worktree`: a role that cuts a tree has "
            "nowhere to cut it, and the standing convention that used to answer "
            "this is readable by a person and by nothing shipped (§ 10).",
        )

    # § 10. What a rebuild writes again, which is the only half of the pruning
    # oracle a project states. ⛔ Whether the key is *written* is the surface's
    # `# required_when` marker and not a rule here; what is held here is its
    # shape, and the direction that matters is the permissive one -- an entry
    # that is not a path reads as an exemption and licenses the removal of a
    # tree holding the file it failed to name.
    #
    # ⚠️ Each entry is held to being a non-empty string and to nothing further.
    # Whether a path exists is not a question about the configuration: the paths
    # are relative to a tree that does not exist yet, and most of them name
    # something no tree has until its build has run once.
    regenerable = _get(data, "branch_model.regenerable")
    if regenerable is not None:
        if not isinstance(regenerable, list):
            raise ConfigError(
                "branch_model.regenerable",
                f"is {regenerable!r}; § 10 states it as a list of ignored paths a rebuild "
                "writes again, and `[]` where a tree of this project holds none.",
            )
        for index, entry in enumerate(regenerable):
            if not isinstance(entry, str) or not entry.strip():
                raise ConfigError(
                    f"branch_model.regenerable[{index}]",
                    f"is {entry!r}; each entry is a path (§ 10). ⛔ Refused rather than "
                    "skipped: an entry that names nothing exempts nothing, and the tree it "
                    "was written to protect is removed with the file still in it.",
                )

    # § 10. Each exclusive resource, held key by key. ⛔ Every one of them is
    # stated on the surface with no default, so an entry missing one is refused
    # here rather than resolved to something the project never said -- and the
    # direction that matters is the permissive one: a `claimed_by` nobody wrote
    # is a resource no call ever claims, which is a guard installed and holding
    # nothing while every reader reports the resource as configured.
    resources = _get(data, "branch_model.exclusive_resources")
    if resources is not None:
        if not isinstance(resources, list):
            raise ConfigError(
                "branch_model.exclusive_resources",
                f"is {resources!r}; § 10 states it as a list of entries, and `[]` where "
                "nothing in this project is exclusive.",
            )
        subjects = vocabulary(
            facts, "branch_model.exclusive_resources.subject", "what holds a place"
        )
        for index, entry in enumerate(resources):
            at = f"branch_model.exclusive_resources[{index}]"
            if not isinstance(entry, dict):
                raise ConfigError(
                    at,
                    f"is {entry!r}; § 10 states each entry as a block of keys, every one of "
                    "them written.",
                )
            for key in ("name", "cap", "subject", "claimed_by", "ttl"):
                if entry.get(key) in (None, ""):
                    raise ConfigError(
                        f"{at}.{key}",
                        "is missing. § 10 states every key of an entry and defaults none of "
                        "them, each being a measurement of the resource rather than a "
                        "preference about it.",
                    )
            if entry["subject"] not in subjects:
                raise ConfigError(
                    f"{at}.subject",
                    f"is {entry['subject']!r}; § 10 states {' | '.join(subjects)}. A place is "
                    "held by a tree or by a call, and the two release differently.",
                )
            for key in ("cap", "ttl"):
                value = entry[key]
                # ⛔ `bool` is excluded by name: it is an `int` in this language,
                # so `cap: true` would read as a cap of one and install a guard
                # the project never described.
                if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                    raise ConfigError(
                        f"{at}.{key}",
                        f"is {value!r}; it is a whole number of at least one (§ 10). A cap "
                        "below one is a resource nothing may ever hold, and a lifetime below "
                        "one is a lease that has expired before the call it covers starts.",
                    )
            try:
                re.compile(str(entry["claimed_by"]))
            except re.error as error:
                raise ConfigError(
                    f"{at}.claimed_by",
                    f"does not compile as a pattern -- {error}. ⛔ Refused rather than left to "
                    "the guard: a pattern that cannot be compiled matches no call, so the "
                    "resource reads as guarded and nothing is ever held (§ 10).",
                ) from None
            probe = entry.get("probe")
            if probe is not None and (not isinstance(probe, str) or not probe.strip()):
                raise ConfigError(
                    f"{at}.probe",
                    f"is {probe!r}; it is a command, or `null` where the resource cannot be "
                    "asked how many are held (§ 10). An empty string is neither: it reads as "
                    "a command and prints no count.",
                )

    # § 14. The one key of the three halves of the boundary, and the one thing a
    # reader can hold about it: it is names. `[]` is a real statement and is
    # accepted -- a project whose roles need nothing beyond the shell's own
    # variables -- so what is refused here is a list carrying something that is
    # not a variable name.
    #
    # ⚠️ The limit, stated rather than discovered: a name-shaped entry that is
    # somehow a secret passes. Refusing that would need the credential grammar,
    # which lives in the boundary carrier, and a copy of it here would be a
    # second grammar allowed to disagree with the one that runs.
    inherited = _get(data, "environment.inherits")
    if inherited is not None:
        if not isinstance(inherited, list):
            raise ConfigError(
                "environment.inherits",
                f"is {inherited!r}; § 14 states it as a list of variable names, and `[]` "
                "where a role's commands need none.",
            )
        for index, name in enumerate(inherited):
            if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
                raise ConfigError(
                    f"environment.inherits[{index}]",
                    f"is {name!r}, which is not a variable name. § 14 states the list as "
                    "names and never values: a configuration carrying the value would be "
                    "the leak the section exists to prevent.",
                )

    # § 4.5. A `field` carrier owes the field's name, for the reason § 12's
    # `command` carrier owes a command: the one role that writes a date would
    # discover the gap holding a date it has nowhere to put, and the item is by
    # then the only thing left saying what was committed to.
    #
    # ⚠️ Only `field` is held. `native` names the tracker's own date and has no
    # name to state, and whether the tracker in fact has one is the adapter's
    # answer rather than this reader's (§ 3).
    if _get(data, "work_item.due_date.carrier") == "field" and not _get(
        data, "work_item.due_date.field"
    ):
        raise ConfigError(
            "work_item.due_date.field",
            "required when the carrier is `field`: there is nowhere to write the "
            "date, and the gating role is the only thing on this surface that "
            "writes one (§ 4.5).",
        )

    # § 12. A command carrier owes a command, for the reason § 11's `file`
    # carrier owes a directory: the absence surfaces at the moment a role needs
    # the answer, which is the one moment it cannot be asked for.
    if _get(data, "ordering.carrier") == "command" and not _get(
        data, "ordering.command"
    ):
        raise ConfigError(
            "ordering.command",
            "required when the carrier is `command`: there is nothing to run, "
            "and a role invoked with no item would have to invent an ordering "
            "rather than report one it could not read (§ 12).",
        )

    # § 15. The two keys of this facet whose *shape* the comparisons walk, held
    # here for the reason `environment.inherits` is: requiredness is marked on
    # the surface and answers whether the key is written, never what it is.
    #
    # ⛔ A shape the check cannot walk is refused rather than skipped, which is
    # the fail-closed direction and the only one that matters here. `judged`
    # written as a string is a plausible mistake — one tree is the common case —
    # and read as a sequence it would judge a change over each *character* of the
    # path, matching no file: the change arm would then find nothing in a judged
    # tree and report green over every change there is.
    if _get(data, "e2e_register.carrier") == "file":
        judged = _get(data, "e2e_register.judged")
        if not isinstance(judged, list):
            raise ConfigError(
                "e2e_register.judged",
                f"is {judged!r}; § 15 states it as the trees a change is judged "
                "over — a list, even where there is one. Read as a sequence of "
                "characters it matches no path, so every change would pass as "
                "touching nothing judged.",
            )
        for index, tree in enumerate(judged):
            if not isinstance(tree, str) or not tree.strip():
                raise ConfigError(
                    f"e2e_register.judged[{index}]",
                    f"is {tree!r}, which is not a tree a change can be judged "
                    "over (§ 15). An entry nothing can match narrows the "
                    "judgement in silence, and the run's own report of what it "
                    "left unjudged would still name every other tree.",
                )
        cases = _get(data, "e2e_register.cases")
        if cases is not None and (not isinstance(cases, str) or not cases.strip()):
            raise ConfigError(
                "e2e_register.cases",
                f"is {cases!r}; § 15 states it as the glob a case file matches, "
                "and the default where it is absent is every file under the "
                "suite. A value of another shape matches nothing, which reads as "
                "a suite with no cases in it.",
            )

    # § 16. Requiredness is marked on the surface and answers whether each
    # command is written; what each value has to *be* is here.
    if _get(data, "executed.carrier") == "command":
        for key in ("declares", "reports"):
            command = _get(data, f"executed.{key}")
            if not isinstance(command, str) or not command.strip():
                raise ConfigError(
                    f"executed.{key}",
                    f"is {command!r}; § 16 states it as a command whose output "
                    "the arithmetic is read from. A value of another shape runs "
                    "as no command, and a count that could not be read is "
                    "reported as unanswered — so a verdict would be withheld on "
                    "a configuration defect rather than on a tier that ran "
                    "nothing.",
                )
        # ⛔ The one floor § 16 judges, and the refusal is the section's
        # not-a-threshold rule rather than a type check. A project writing
        # `min: 40` has asked for coverage enforcement, which this facet does not
        # state — and accepting it would ship exactly the threshold the rule is
        # defined against, reddening on the count being wrong rather than on the
        # tier having executed nothing.
        floor = _get(data, "executed.min")
        # ⚠️ The boolean arm runs **first**, because `True == 1` in Python: the
        # value comparison below would accept `min: true` as the floor and
        # refuse `min: false` with a message about which numbers are allowed.
        # Both are the same mistake and are named as the one they are.
        if isinstance(floor, bool):
            raise ConfigError(
                "executed.min",
                "is a boolean; § 16 states it as the floor that must have "
                "executed, which is a count. A boolean compares equal to `1`, so "
                "`true` would otherwise be read as that floor.",
            )
        # ⚠️ And an integer, not merely something equal to one: `1.0` compares
        # equal and is not the count § 16 states. The same trap as the boolean
        # above, one line down, and missed there on the first pass — found by
        # review on this change.
        if floor is not None and (not isinstance(floor, int) or floor != 1):
            raise ConfigError(
                "executed.min",
                f"is {floor!r}; § 16 states `1` as the one floor this facet "
                "judges. Zero executed against a non-zero declaration is the "
                "failure, every other number is reported rather than judged, and "
                "a higher floor is the coverage threshold this rule is defined "
                "against. Leave it unset to have the counts reported and nothing "
                "judged.",
            )
        requires = _get(data, "executed.requires")
        if requires is not None:
            if not isinstance(requires, list):
                raise ConfigError(
                    "executed.requires",
                    f"is {requires!r}; § 16 states it as the preconditions the "
                    "cases need — a list, even where there is one. Read as a "
                    "sequence it names one precondition per character, and the "
                    "verdict that misses the floor would print the dependency a "
                    "character at a time.",
                )
            for index, precondition in enumerate(requires):
                if not isinstance(precondition, str) or not precondition.strip():
                    raise ConfigError(
                        f"executed.requires[{index}]",
                        f"is {precondition!r}, which names no precondition "
                        "(§ 16). An entry naming nothing is counted as a named "
                        "dependency and printed as a blank, so the verdict reads "
                        "as having said what the skipped cases wanted.",
                    )
    elif _get(data, "executed.carrier") == "none":
        # ⛔ A stated absence that also states a floor, a command or a
        # precondition is refused with the key named. The shape rules above are
        # gated on the carrier, so without this arm the one value § 16 says a
        # reader "refuses rather than silently accepts" — a coverage threshold —
        # loads clean on any project whose carrier is `none`, and reads to the
        # next person as a floor something judges. Found by review on this
        # change, where the sibling facet one section up has the same hole.
        for key in ("declares", "reports", "min", "requires"):
            if _has(data, f"executed.{key}"):
                raise ConfigError(
                    f"executed.{key}",
                    "is written beside `executed.carrier: none` (§ 16). The "
                    "absence is the statement, so a value here is a rule nothing "
                    "performs: delete the key, or state the carrier it belongs "
                    "to.",
                )

    statuses = _absent_as(_get(data, "statuses"), [])
    if not isinstance(statuses, list):
        raise ConfigError("statuses", "must be a list; `[]` where no status is mapped.")
    for index, status in enumerate(statuses):
        where = f"statuses[{index}]"
        if not isinstance(status, dict):
            raise ConfigError(where, "must be a mapping of name, role and writer.")
        for field in ("role", "writer"):
            allowed = vocabulary(facts, field, f"a status {field}")
            if field not in status:
                raise ConfigError(f"{where}.{field}", "required (§ 4.2).")
            if status[field] not in allowed:
                raise ConfigError(
                    f"{where}.{field}",
                    f"is {status[field]!r}; the surface states "
                    f"{' | '.join(allowed)}.",
                )
        if "name" not in status:
            raise ConfigError(f"{where}.name", "required (§ 4.2).")

    readiness = _absent_as(_get(data, "readiness"), [])
    if not isinstance(readiness, list):
        raise ConfigError("readiness", "must be a list; `[]` where there is no gate.")
    for index, entry in enumerate(readiness):
        where = f"readiness[{index}]"
        if not isinstance(entry, dict):
            raise ConfigError(where, "must be a mapping with a `check`.")
        library = vocabulary(facts, "check", "a readiness check")
        if "check" not in entry:
            raise ConfigError(f"{where}.check", "required (§ 5).")
        if entry["check"] not in library:
            raise ConfigError(
                f"{where}.check",
                f"is {entry['check']!r}; the surface's library is "
                f"{' | '.join(library)}.",
            )
        on_fail = vocabulary(facts, "on_fail", "a readiness failure mode")
        if "on_fail" in entry and entry["on_fail"] not in on_fail:
            raise ConfigError(
                f"{where}.on_fail",
                f"is {entry['on_fail']!r}; the surface allows {' | '.join(on_fail)}.",
            )

    # § 2. Where this project's jobs run, walked for its refusals alone -- the
    # value is read back through the accessor by whatever needs it. ⛔ Called
    # even though nothing here uses the result: the walk *is* the refusal, and a
    # facet validated only when a consumer happens to ask is a facet an adopter
    # writes wrong and learns about from a generated workflow that never starts.
    host_runner(data)

    # § 2. What a pull request title opens with, walked here for its refusals
    # alone and for the reason the walk above is: the facet has two readers and
    # neither of them is reached on the run that would have caught a bad value.
    # ⛔ An adopter writing it wrong otherwise learns about it from a generated
    # gate refusing every title the finishing role writes.
    host_pull_request_title(data)

    # § 17. The verdicts no host run produces, and the one facet on this surface
    # whose entries carry a command the procedure runs for a verdict. Requiredness
    # is marked on the surface and answers whether the key is written; what each
    # value has to *be* is here, as § 16's is.
    mirrored = _mirrored_commands(data)
    local_checks = _absent_as(_get(data, "checks_local"), [])
    if not isinstance(local_checks, list):
        raise ConfigError(
            "checks_local",
            f"is {type(local_checks).__name__}, and § 17 states it as the verdicts "
            "no host run produces -- a list of entries, or `[]` where every verdict "
            "is the host's. A shape this reader cannot walk takes every local "
            "command out of the collision refusal below in silence.",
        )
    for index, entry in enumerate(local_checks):
        where = f"checks_local[{index}]"
        if not isinstance(entry, dict):
            raise ConfigError(
                where,
                f"is {entry!r}, and has to be a mapping stating at least the "
                "`command` whose exit status is the verdict and what a pass "
                "`proves` (§ 17).",
            )
        command = entry.get("command")
        # ⛔ One command, and a list refused for the reason § 2 refuses one inside
        # a `mirrors`: a list cannot say which `proves`, which `invalidate` and
        # which precondition belong to which command, and several verdicts are
        # several entries. A list also stringifies into a key no mirrored command
        # can match, which would pass a duplicate of the host's own run.
        if not isinstance(command, str) or not command.strip():
            raise ConfigError(
                f"{where}.command",
                f"is {command!r}; § 17 states one command per entry, written as a "
                "string and stated whole. Several verdicts are several entries, "
                "and a value of another shape runs as no command while matching "
                "no `host.checks` entry either.",
            )
        proves = entry.get("proves")
        if not isinstance(proves, str) or not proves.strip():
            raise ConfigError(
                f"{where}.proves",
                f"is {proves!r}; § 17 states what a pass establishes beside the "
                "command that produces it. A verdict with no claim beside it is "
                "read as proving whatever the reader needed, which is the failure "
                "the facet exists for arriving one step earlier.",
            )
        if "invalidate" in entry:
            defeat = entry["invalidate"]
            if not isinstance(defeat, str) or not defeat.strip():
                raise ConfigError(
                    f"{where}.invalidate",
                    f"is {defeat!r}; § 17 states it as the command that defeats a "
                    "cached, incremental or stale pass, and absent where nothing "
                    "can go stale. Written blank it reads as that absence while "
                    "looking like a defeat somebody configured, and a pass "
                    "produced without it having run is not proof.",
                )
        requires = entry.get("requires")
        if requires is not None:
            # § 16's list, cited rather than given a second grammar -- so the
            # shape it is held to is the same one, for the same reason: read as a
            # sequence a string names one precondition per character, and the
            # report that blocks the verdict would print the dependency a
            # character at a time.
            if not isinstance(requires, list):
                raise ConfigError(
                    f"{where}.requires",
                    f"is {requires!r}; § 17 reads § 16's list -- the preconditions "
                    "the command does not check itself, written as a list even "
                    "where there is one.",
                )
            for position, precondition in enumerate(requires):
                if not isinstance(precondition, str) or not precondition.strip():
                    raise ConfigError(
                        f"{where}.requires[{position}]",
                        f"is {precondition!r}, which names no precondition (§ 17). "
                        "An entry naming nothing blocks the verdict and names a "
                        "blank, so the report reads as having said what was unmet.",
                    )
        if "counts_when" in entry:
            # The shape only: § 2 states the trigger grammar and deliberately
            # refuses no pattern, a trigger a consumer cannot parse being no
            # answer about the run. ⚠️ Which is safe here and nowhere else -- an
            # unestablished condition is *run it here* under § 17, so a pattern
            # this reader lets through costs a local run rather than a green.
            condition = entry["counts_when"]
            patterns = condition if isinstance(condition, list) else [condition]
            if not patterns or any(
                not isinstance(p, str) or not p.strip() for p in patterns
            ):
                raise ConfigError(
                    f"{where}.counts_when",
                    f"is {condition!r}; § 17 states it in § 2's `triggers` form -- "
                    "one pattern or a list of them, and omitted where the verdict "
                    "counts for every change. Written blank it states a condition "
                    "nothing can read while reading as a condition somebody set.",
                )
            # ⛔ And the same clause refusals the other end of this mapping
            # gets: § 17 states this key in § 2's form, so a shape refused
            # there and accepted here is the second vocabulary that section
            # refuses, arriving as behaviour rather than as text.
            _type_clauses(condition, f"{where}.counts_when")
        collision = mirrored.get(_normalised_command(command))
        if collision:
            raise ConfigError(
                f"{where}.command",
                f"is {command!r}, which {collision} already mirrors (§ 2). A local "
                "check colliding with a run the host owns asks a shared machine "
                "for an answer it already has; a command no entry mirrors is the "
                "one that must run locally, because nothing else will ever answer "
                "it.",
            )

    # § 20. The sections a body must carry beyond § 6's. Requiredness is the
    # surface's marker and answers whether the key is written; what each entry
    # has to *be* is here, as § 17's is -- and for the same stated reason: a
    # member of a list sits at no path a marker can reach, so all three of its
    # keys are held in prose there and in code here.
    body_sections = _absent_as(_get(data, "body_sections"), [])
    if not isinstance(body_sections, list):
        raise ConfigError(
            "body_sections",
            f"is {type(body_sections).__name__}, and § 20 states it as the sections a "
            "body carries beyond § 6's -- a list of entries, or `[]` where a project "
            "requires none. A shape this reader cannot walk is a gate installed over "
            "sections nobody can read.",
        )
    seen_headings: dict[str, int] = {}
    for index, entry in enumerate(body_sections):
        where = f"body_sections[{index}]"
        if not isinstance(entry, dict):
            raise ConfigError(
                where,
                f"is {entry!r}, and has to be a mapping stating the `heading` a body "
                "spells, what `read_by` collects it, and the `nothing_needed` answer "
                "that closes it (§ 20).",
            )
        for key, what in (
            ("heading", "the heading text a body spells, in the repository's language"),
            ("read_by", "what collects this section out of the change"),
            ("nothing_needed", "the answer the section carries where nothing is needed"),
        ):
            value = entry.get(key)
            if not isinstance(value, str) or not value.strip():
                raise ConfigError(
                    f"{where}.{key}",
                    f"is {value!r}; § 20 states it as {what}, written on every entry. "
                    "Written blank it reads as a key somebody set while stating "
                    "nothing, and the gate then holds a body to a heading that is "
                    "not there.",
                )
        # ⛔ The collision § 20 refuses, and it is keyed the way the gate reads a
        # heading: the text alone, cased however a body cases it. Two entries
        # under one heading leave every reader of the facet choosing between two
        # statements of what one section is for -- § 2's own argument for keying
        # `checks` on the workflow name, arriving at the other end of the body.
        folded = entry["heading"].strip().casefold()
        if folded in seen_headings:
            raise ConfigError(
                f"{where}.heading",
                f"is {entry['heading']!r}, which body_sections[{seen_headings[folded]}] "
                "already states (§ 20). The section is collected by that text, so a "
                "second entry under it is two statements of what one section is for, "
                "and a gate reading either would be right.",
            )
        seen_headings[folded] = index

    # § 18. The guard on a command the host has already run. Requiredness is the
    # surface's marker and answers whether `never_guard` is written; what these
    # three values have to *be* is here, as § 17's are.
    exempt = _absent_as(_get(data, "already_run.never_guard"), [])
    if not isinstance(exempt, list):
        raise ConfigError(
            "already_run.never_guard",
            f"is {type(exempt).__name__}, and § 18 states it as the commands this guard "
            "never refuses -- a list, or `[]` where none is exempt. A shape this reader "
            "cannot walk takes every exemption out of the guard in silence, and the guard "
            "then refuses a repair rather than a duplicated verdict.",
        )
    for index, entry in enumerate(exempt):
        if not isinstance(entry, str) or not entry.strip():
            raise ConfigError(
                f"already_run.never_guard[{index}]",
                f"is {entry!r}, which names no command (§ 18). An entry naming nothing is "
                "an exemption that matches nothing while reading as one somebody wrote.",
            )
    escape = _get(data, "already_run.escape")
    if escape is not None and (
        not isinstance(escape, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", escape)
    ):
        # ⛔ A name and never a value, which is § 14's rule at the one key on this
        # surface that names a variable outside that section: a configuration
        # carrying the value would be the leak that section exists to prevent,
        # and the value here is the person's own reason rather than a secret.
        raise ConfigError(
            "already_run.escape",
            f"is {escape!r}, which is not a variable name. § 18 states it as the name of "
            "the variable a person sets to why a refusal is stood down, and absent where "
            "there is none -- never the value, and never a phrase.",
        )
    probe = _get(data, "already_run.operational_when")
    if probe is not None and (not isinstance(probe, str) or not probe.strip()):
        raise ConfigError(
            "already_run.operational_when",
            f"is {probe!r}; § 18 states it as one command, stated whole, and absent where "
            "the host's own answer is the only one there is. Written blank it reads as that "
            "absence while looking like a probe somebody configured, and a probe that "
            "answers nothing stands every refusal down.",
        )

    # § 13. The same shape as `readiness` at the other end of the item, with one
    # thing that gate has no need of: who answers each check.
    done = _absent_as(_get(data, "done"), [])
    if not isinstance(done, list):
        raise ConfigError(
            "done", "must be a list; `[]` where the merge is the whole of it."
        )
    for index, entry in enumerate(done):
        where = f"done[{index}]"
        if not isinstance(entry, dict):
            raise ConfigError(where, "must be a mapping with a `check` and an `answered_by`.")
        library = vocabulary(facts, "done.check", "a done check")
        if "check" not in entry:
            raise ConfigError(f"{where}.check", "required (§ 13).")
        if entry["check"] not in library:
            raise ConfigError(
                f"{where}.check",
                f"is {entry['check']!r}; the surface's library is "
                f"{' | '.join(library)}.",
            )
        answerers = vocabulary(facts, "done.answered_by", "who answers a done check")
        # Stated on every check and never defaulted. A default could only be
        # `procedure`, and the configuration it would silently produce -- a check
        # only a person can answer, answered by reasoning about it -- is the one
        # failure here that reads exactly like success.
        if "answered_by" not in entry:
            raise ConfigError(
                f"{where}.answered_by",
                "required (§ 13): who answers a check is stated per check and "
                "never defaulted, because the default that reads as harmless is "
                "the one that lets a session answer a check it cannot.",
            )
        if entry["answered_by"] not in answerers:
            raise ConfigError(
                f"{where}.answered_by",
                f"is {entry['answered_by']!r}; the surface states "
                f"{' | '.join(answerers)}.",
            )
        if not entry.get("stop"):
            raise ConfigError(
                f"{where}.stop",
                "required (§ 13): a done check that fails is handed to a person "
                "in place of an answer, and one with no message hands over the "
                "failure without what it wants.",
            )
        # Every check § 13 binds to an answerer, in both directions. ⛔ Both
        # directions matter and only one of them is obvious: a machine check
        # handed to a person is the check somebody turns off, and a person's
        # check handed to the procedure is answered by reasoning about it and
        # reported green, which is the failure § 13 exists for.
        # `checklist_ticked` is bound to neither, and § 13 says why.
        #
        # ⚠️ `local` is in that map like any other check now that no entry
        # carries a command: it used to need an arm of its own because the
        # refusal read the `run` beside it, and the rule it states is the same
        # one -- a command is the procedure's to run (§ 17).
        if BOUND_ANSWERERS.get(entry["check"], entry["answered_by"]) != entry["answered_by"]:
            raise ConfigError(
                f"{where}.answered_by",
                f"is {entry['answered_by']!r} on a check § 13 binds to "
                f"`{BOUND_ANSWERERS[entry['check']]}`. A check that names its own "
                "answerer is not a project's to reassign: a machine reading "
                "handed to a person is a check that gets turned off, and a "
                "person's verification handed to the procedure is answered by "
                "reasoning about it. `checklist_ticked` is the one that may go "
                "either way, since reading whether a list is ticked can be a "
                "machine's work.",
            )

    carriers = _absent_as(_get(data, "carriers"), {})
    if not isinstance(carriers, dict):
        raise ConfigError("carriers", "must map each mapped role to its carrier.")
    # Every role's carrier comes from one set, which the surface states once, on
    # the one role its block happens to show.
    allowed = vocabulary(facts, "carriers.day_log", "a role's carrier")
    for role, carrier in carriers.items():
        if carrier not in allowed:
            raise ConfigError(
                f"carriers.{role}",
                f"is {carrier!r}; the surface allows {' | '.join(allowed)}.",
            )

    # § 6. Staging is per role, and which roles commit is read off the surface's
    # own block rather than listed here -- the derivation § 1's per-root blocks
    # already have, for the same reason: a fourth committing role is a fence edit
    # and not an edit to this module.
    committing = sorted({
        path.split(".")[2]
        for path in facts["declared"]
        if path.startswith("commit.staging.")
    })

    # § 23 first, because § 6's per-role requirement reads it: the bookkeeping
    # role's commit is a third of that role, so whether it commits at all is
    # `session.parts`'s answer and not `carriers`'s. ⛔ Read through `_absent_as`,
    # so this shape rule answers what a stated value has to be and never whether
    # the key is written -- requiredness is the surface's marker, and a work tree
    # whose surface predates the key marks nothing.
    parts = _absent_as(_get(data, "session.parts"), [])
    if not isinstance(parts, list):
        raise ConfigError(
            "session.parts",
            f"is {parts!r}; § 23 states the thirds of the bookkeeping role that "
            "run here as a list, or `[]` where the project maps no such role. A "
            "value that is not a list leaves the role running whichever thirds it "
            "reads out of it.",
        )
    if parts:
        thirds = vocabulary_list(
            facts, "session.parts", "a third of the bookkeeping role"
        )
        for part in parts:
            if part not in thirds:
                raise ConfigError(
                    "session.parts",
                    f"names {part!r}; the surface allows {' | '.join(thirds)} (§ 23).",
                )
        repeated = sorted({p for p in parts if parts.count(p) > 1})
        if repeated:
            raise ConfigError(
                "session.parts",
                f"names {', '.join(repeated)} more than once. It is a set: a third "
                "stated twice does not run twice (§ 23).",
            )
    if SESSION_ROLE in carriers and not parts:
        raise ConfigError(
            "session.parts",
            "is empty while `carriers` maps the role, which is a role mapped to "
            "do nothing. An empty list is how a project that maps no bookkeeping "
            "role states it, and the two read identically otherwise (§ 23).",
        )
    if parts and SESSION_ROLE not in carriers:
        raise ConfigError(
            "session.parts",
            f"states {', '.join(map(str, parts))} while `carriers` maps no "
            f"`{SESSION_ROLE}` role, so nothing runs them (§ 7). Map the role or "
            "state `[]`.",
        )

    # ⛔ Read through `_absent_as` for the reason § 23's block above is: an absent
    # block falls to the per-role requirement below, which names the role rather
    # than the block.
    staging = _absent_as(_get(data, "commit.staging"), {})
    if not isinstance(staging, dict):
        raise ConfigError(
            "commit.staging",
            f"is {staging!r}; § 6 states it per role -- one entry per role that "
            "commits, or `{}` where the project maps none of them. A single value "
            "for a project is the shape that made one of two roles wrong in the "
            "project this was measured in.",
        )
    # ⛔ A surface that declares the block with no role under it is refused at the
    # point of use and never on sight. `per_root` already declined the other
    # shape for this reason: a refusal on the whole surface would leave a work
    # tree whose branch predates the fence unable to read its own configuration
    # (§ 1), while a configuration that states no entry has nothing to hold.
    if staging and not committing:
        raise ConfigError(
            "commit.staging",
            f"states {', '.join(sorted(map(str, staging)))} while the surface this "
            "tree is held to declares no role under `commit.staging`, so this "
            "reader cannot tell which roles commit and would hold every entry to "
            "nothing (§ 6).",
        )
    for role in staging:
        # ⛔ Before the sort, which is where a key that is not a string arrives as
        # a traceback naming nothing -- out of the one module whose whole promise
        # is naming the key. An unquoted word that reads as a number or a boolean
        # is the shape it comes in.
        if not isinstance(role, str):
            raise ConfigError(
                "commit.staging",
                f"carries an entry keyed {role!r}, which is not a role's name. "
                f"§ 6 states the roles that commit: {' | '.join(committing)}.",
            )
    # Which roles commit *here*: mapped, and for the bookkeeping role only where
    # the commit third is one it runs. ⛔ The condition is § 6's own statement
    # about that role and is not derivable from `carriers`, which says a role is
    # mapped and nothing about which of its thirds run.
    commits_here = [
        role
        for role in committing
        if role in carriers
        and (role != SESSION_ROLE or COMMIT_THIRD in parts)
    ]
    for role in sorted(staging):
        if role not in committing:
            raise ConfigError(
                f"commit.staging.{role}",
                f"names a role that does not commit. § 6 states the roles that do: "
                f"{' | '.join(committing)}.",
            )
        if role not in carriers:
            raise ConfigError(
                f"commit.staging.{role}",
                "names a role `carriers` does not map, so nothing here ever reads "
                "it (§ 7). Map the role or drop the entry -- an unmapped role and a "
                "misspelled one read alike, and this is where they come apart.",
            )
        if role not in commits_here:
            raise ConfigError(
                f"commit.staging.{role}",
                f"states a staging mode for a commit this project never makes: "
                f"`session.parts` does not run the `{COMMIT_THIRD}` third, so that "
                "role reaches no commit here (§ 23). Drop the entry or run the "
                "third.",
            )
        # ⛔ Only the empty value, because the surface's own alternation on each
        # entry is what holds a *stated* one and the generic enum rule above
        # performs it. What that rule cannot answer is a key written with nothing
        # after it, which it reads as absent and skips -- leaving the one role
        # whose staging nobody chose looking configured.
        if staging[role] is None:
            raise ConfigError(
                f"commit.staging.{role}",
                "is written and empty, so that role's commit runs on the staging "
                "nobody chose. The surface allows "
                f"{' | '.join(vocabulary(facts, f'commit.staging.{role}', 'a staging mode'))} "
                "(§ 6).",
            )
    for role in commits_here:
        if role not in staging:
            raise ConfigError(
                f"commit.staging.{role}",
                "required: the project maps that role and it commits, so this is "
                "the staging nobody chose otherwise (§ 6).",
            )

    # § 25, whose condition is the `parts` list read above. ⛔ The requiredness is
    # a rule rather than a `# required_when` marker: that marker compares one
    # key's value against a literal, and what makes this block needed is a
    # *list's membership*, which no comparison of that shape reaches.
    #
    # ⚠️ **After § 6's block and not before it, which is ordering rather than
    # arrangement.** § 6 refuses a staging entry for a bookkeeping role whose
    # commit third does not run, and the configuration that trips it states a
    # `parts` list with neither the commit third nor the memory one -- so a § 25
    # refusal raised first would answer that configuration with the wrong key,
    # and the older rule would be left asserted by nothing.
    _memory(data, parts)

    # § 8. A width is a count of columns, and absence is the answer "this
    # project does not hard-wrap" rather than a missing setting -- so the key is
    # not required, and a value that is present is held to being a positive
    # whole number. `true` is an int in Python and would otherwise resolve to a
    # width of one column.
    width = _get(data, "language.prose_width")
    if width is not None and (
        isinstance(width, bool) or not isinstance(width, int) or width <= 0
    ):
        raise ConfigError(
            "language.prose_width",
            f"is {width!r}; it takes a positive number of columns, or is absent "
            "where the project does not hard-wrap its files (§ 8).",
        )

    # § 19. Each denied call, held key by key. ⛔ Every refusal here is in the
    # permissive direction, which is the one that matters for this facet: an entry
    # a guard cannot act on is a paid command nothing ever refuses, while every
    # reader goes on reporting the guard as configured. The shape rules are here
    # for the reason § 16's and § 17's are -- requiredness is marked on the
    # surface and answers whether a key is written, and a member of a list sits at
    # no path a marker can reach.
    denied = _absent_as(_get(data, "spend_guard.deny"), [])
    if not isinstance(denied, list):
        raise ConfigError(
            "spend_guard.deny",
            f"is {denied!r}; § 19 states it as the calls that spend -- a list of "
            "entries, or `[]` where no command here spends. A shape this reader "
            "cannot walk is a guard with nothing to match, installed and silent.",
        )
    for index, entry in enumerate(denied):
        where = f"spend_guard.deny[{index}]"
        if not isinstance(entry, dict):
            raise ConfigError(
                where,
                f"is {entry!r}, and has to be a mapping stating at least the "
                "`command` whose invocation spends and the `reason` naming what it "
                "costs (§ 19).",
            )
        command = entry.get("command")
        if not isinstance(command, str) or not command.strip():
            raise ConfigError(
                f"{where}.command",
                f"is {command!r}; § 19 states one command per entry, matched "
                "against the command position of each segment of a call. A value "
                "of another shape stands in no command position, so the entry "
                "refuses nothing while reading as a denial somebody configured.",
            )
        reason = entry.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            raise ConfigError(
                f"{where}.reason",
                f"is {reason!r}; § 18 states it as what the call costs, in the "
                "project's own terms, and it is what a refusal names.",
            )
        if "args_match" in entry:
            pattern = entry["args_match"]
            if not isinstance(pattern, str) or not pattern.strip():
                raise ConfigError(
                    f"{where}.args_match",
                    f"is {pattern!r}; § 18 states it as the pattern the arguments "
                    "carry, and absent where the command alone decides. Written "
                    "blank it matches every call of that command, which is the "
                    "opposite of the narrowing it was written for.",
                )
            try:
                re.compile(pattern)
            except re.error as error:
                raise ConfigError(
                    f"{where}.args_match",
                    f"does not compile as a pattern -- {error}. ⛔ Refused rather "
                    "than left to the guard: a pattern that cannot be compiled "
                    "matches no call, so the paid command reads as denied and is "
                    "never refused (§ 19).",
                ) from None

    # § 19's other key. The bar is compared against a figure the harness states in
    # its own units, so what is refused here is a value that cannot be compared to
    # one. ⚠️ The boolean arm runs first, for the reason § 16's floor states: a
    # boolean compares equal to `1` in this language, so `true` would otherwise be
    # read as a bar of one unit.
    bar = _get(data, "spend_guard.resume_bar_usd")
    if isinstance(bar, bool):
        raise ConfigError(
            "spend_guard.resume_bar_usd",
            "is a boolean; § 19 states it as the price a resume is reported above, "
            "which is a number. A boolean compares equal to `1`, so `true` would "
            "be read as that price.",
        )
    if bar is not None and (not isinstance(bar, (int, float)) or bar < 0):
        raise ConfigError(
            "spend_guard.resume_bar_usd",
            f"is {bar!r}; § 19 states it as the price a resume is reported above, "
            "in the figure's own units, and absent where no resume is priced. A "
            "value nothing can compare to a price prices no resume while reading "
            "as a bar somebody set.",
        )

    # § 21. The commands that open a session elsewhere, held key by key -- and
    # every refusal here is in the permissive direction, which is the one that
    # matters: an entry a guard cannot act on is a connection nothing ever puts
    # to anybody, while every reader goes on reporting the guard as configured.
    # The shape rules are here for the reason § 19's are: requiredness is marked
    # on the surface and answers whether a key is written, and a member of a list
    # sits at no path a marker can reach.
    tools = _absent_as(_get(data, "live_guard.session_tools"), [])
    if not isinstance(tools, list):
        raise ConfigError(
            "live_guard.session_tools",
            f"is {tools!r}; § 21 states it as the commands that open a session on "
            "another machine -- a list of entries, or `[]` where no command here "
            "does. A shape this reader cannot walk is a guard with nothing to "
            "match, installed and silent.",
        )
    for index, entry in enumerate(tools):
        where = f"live_guard.session_tools[{index}]"
        if not isinstance(entry, dict):
            raise ConfigError(
                where,
                f"is {entry!r}, and has to be a mapping stating at least the "
                "`command` that opens the session (§ 21).",
            )
        command = entry.get("command")
        if not isinstance(command, str) or not command.strip():
            raise ConfigError(
                f"{where}.command",
                f"is {command!r}; § 21 states one command per entry, matched "
                "against the command position of each segment of a call. A value "
                "of another shape stands in no command position, so the entry "
                "holds nothing while reading as a guard somebody configured.",
            )
        if "valued_flags" in entry:
            flags = entry["valued_flags"]
            if not isinstance(flags, list):
                raise ConfigError(
                    f"{where}.valued_flags",
                    f"is {flags!r}; § 21 states it as the flags of that command "
                    "whose value is a separate word, as a list, and absent where "
                    "it takes none.",
                )
            for at_flag, flag in enumerate(flags):
                # ⛔ Held to being one dashed word, which is what the reading of a
                # call can act on: a flag written without its dash matches no word
                # of any call, so its value stands where the machine should be and
                # the guard reads a port or a key file as the machine it is about
                # to reach -- the failure § 21 names this key for.
                if (
                    not isinstance(flag, str)
                    or not flag.strip().startswith("-")
                    or len(flag.split()) != 1
                ):
                    raise ConfigError(
                        f"{where}.valued_flags[{at_flag}]",
                        f"is {flag!r}; § 21 states each as a flag of that command, "
                        "which is one word written with its dashes. Anything else "
                        "matches no word of any call, and then the flag's own value "
                        "is read as the machine.",
                    )
    allowlist = _get(data, "live_guard.allowlist")
    if tools and (not isinstance(allowlist, str) or not allowlist.strip()):
        # ⛔ Required where an entry is, and in prose rather than by the
        # conditional marker: that marker compares a key against a stated value,
        # and what makes this key needed is a *list with something in it*. ⚠️ The
        # refusal is about the key and not the file: a path naming no file on the
        # machine in hand is § 21's stricter-rather-than-silent case and is the
        # guard's to answer, while a project with no key at all has nowhere for
        # the names to live and no way to stop being prompted.
        raise ConfigError(
            "live_guard.allowlist",
            f"is {allowlist!r}; § 21 states it wherever `session_tools` carries an "
            "entry -- the file the machines that are not live are named in, outside "
            "every working tree. With no file to read, every name reads as live and "
            "nothing a project does clears the guard.",
        )
    local = _get(data, "live_guard.local_names")
    if local is not None and (
        not isinstance(local, list)
        or any(not isinstance(name, str) or not name.strip() for name in local)
    ):
        raise ConfigError(
            "live_guard.local_names",
            f"is {local!r}; § 21 states it as the names reached without leaving "
            "this machine, each a name, and absent where no name is read as local. "
            "A blank member matches nothing and reads as a name somebody listed.",
        )

    # § 22. The calls whose output nothing bounds, held key by key -- and every
    # refusal here is in the permissive direction, which is the one that matters:
    # an entry a guard cannot act on is a window spent on a dump nothing bounded,
    # while every reader goes on reporting the guard as configured. The shape
    # rules are here for the reason §§ 19 and 21's are: requiredness is marked on
    # the surface and answers whether a key is written, and a member of a list
    # sits at no path a marker can reach.
    unbounded = _absent_as(_get(data, "context_guard.unbounded"), [])
    if not isinstance(unbounded, list):
        raise ConfigError(
            "context_guard.unbounded",
            f"is {unbounded!r}; § 22 states it as the commands whose output "
            "nothing bounds -- a list of entries, or `[]` where no command here "
            "produces one. A shape this reader cannot walk is a guard with "
            "nothing to match, installed and silent.",
        )
    for index, entry in enumerate(unbounded):
        where = f"context_guard.unbounded[{index}]"
        if not isinstance(entry, dict):
            raise ConfigError(
                where,
                f"is {entry!r}, and has to be a mapping stating at least the "
                "`command` whose output nothing bounds, the `reason` naming what "
                "it would put in the window, and one of `bound` or `instead` "
                "(§ 22).",
            )
        command = entry.get("command")
        if not isinstance(command, str) or not command.strip():
            raise ConfigError(
                f"{where}.command",
                f"is {command!r}; § 22 states one command per entry, matched "
                "against the command position of each segment of a call. A value "
                "of another shape stands in no command position, so the entry "
                "bounds nothing while reading as a guard somebody configured.",
            )
        reason = entry.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            raise ConfigError(
                f"{where}.reason",
                f"is {reason!r}; § 22 states it as what the unbounded call would "
                "put in the window, in the project's own terms, and it is what a "
                "refusal names.",
            )
        # ⛔ Exactly one, by § 22's own rule at those keys: with neither, the
        # entry names a call to hold and no route past it, and the refusal it
        # produces is the one § 7 says somebody edits the guard to get past;
        # with both, a rewrite and a replacement both apply and the guard would
        # have to choose which of the project's two statements to honour.
        # ⚠️ Written with a value, rather than merely present: a key written with
        # nothing after it is one a mapping carries as null, and counting it left
        # the refusal naming two keys at a project that wrote one. Found by
        # review on this change.
        stated = [key for key in ("bound", "instead") if entry.get(key) is not None]
        if len(stated) != 1:
            raise ConfigError(
                f"{where}.bound",
                "and `instead`: § 22 states exactly one of the two per entry, and "
                f"this one states {stated or 'neither'}. A `bound` is a flag added "
                "to the arguments and an `instead` is a form the refusal names, so "
                "an entry with neither refuses a call and offers no route past it, "
                "and an entry with both states two answers to one call.",
            )
        for key in stated:
            value = entry[key]
            if not isinstance(value, str) or not value.strip():
                raise ConfigError(
                    f"{where}.{key}",
                    f"is {value!r}; § 22 states `bound` as the flag and value that "
                    "bounds this command's output and `instead` as the bounded "
                    "form to run, each written out. A blank value is a rewrite "
                    "that adds nothing, or a refusal that names nothing to run.",
                )
        if "args_match" in entry:
            pattern = entry["args_match"]
            if not isinstance(pattern, str) or not pattern.strip():
                raise ConfigError(
                    f"{where}.args_match",
                    f"is {pattern!r}; § 22 states it as the pattern the arguments "
                    "carry, and absent where the command alone decides. Written "
                    "blank it matches every call of that command, which is the "
                    "opposite of the narrowing it was written for.",
                )
            try:
                re.compile(pattern)
            except re.error as error:
                raise ConfigError(
                    f"{where}.args_match",
                    f"does not compile as a pattern -- {error}. ⛔ Refused rather "
                    "than left to the guard: a pattern that cannot be compiled "
                    "matches no call, so the command reads as bounded and is "
                    "never held (§ 22).",
                ) from None
    exempt = _absent_as(_get(data, "context_guard.never_bound"), [])
    if not isinstance(exempt, list):
        raise ConfigError(
            "context_guard.never_bound",
            f"is {exempt!r}; § 22 states it as the commands this guard neither "
            "bounds nor replaces a result of -- a list of entries, or `[]` where "
            "none is exempt. A shape this reader cannot walk is an exemption "
            "nothing matches, which is the direction that costs a role the "
            "measurement it forbids truncating.",
        )
    for index, entry in enumerate(exempt):
        where = f"context_guard.never_bound[{index}]"
        if not isinstance(entry, dict):
            raise ConfigError(
                where,
                f"is {entry!r}; § 22 states each exemption as a mapping stating "
                "the `command` it exempts, with `args_match` where the command "
                "alone does not decide -- the same two keys an `unbounded` entry "
                "carries, matched the same way.",
            )
        command = entry.get("command")
        if not isinstance(command, str) or not command.strip():
            raise ConfigError(
                f"{where}.command",
                f"is {command!r}; § 22 states one command per exemption, matched "
                "against the command position of each segment of a call. A value "
                "of another shape stands in no command position, so the exemption "
                "matches nothing while reading as one somebody stated.",
            )
        if "args_match" in entry:
            pattern = entry["args_match"]
            if not isinstance(pattern, str) or not pattern.strip():
                raise ConfigError(
                    f"{where}.args_match",
                    f"is {pattern!r}; § 22 states it as the pattern the arguments "
                    "carry, and absent where the command alone decides. Written "
                    "blank it exempts every call of that command, which for an "
                    "interpreter is a project exempting a language.",
                )
            try:
                re.compile(pattern)
            except re.error as error:
                raise ConfigError(
                    f"{where}.args_match",
                    f"does not compile as a pattern -- {error}. ⛔ Refused rather "
                    "than left to the guard: a pattern that cannot be compiled "
                    "matches no call, so the exemption reads as stated and the "
                    "role it was written for meets the guard anyway (§ 22).",
                ) from None
    limit = _get(data, "context_guard.result_limit_chars")
    if isinstance(limit, bool) or (
        limit is not None and (not isinstance(limit, int) or limit <= 0)
    ):
        # ⛔ A boolean is refused by name for the reason § 19's price key refuses
        # one: `true` compares equal to `1`, so it would be read as a limit of one
        # character and every result replaced.
        raise ConfigError(
            "context_guard.result_limit_chars",
            f"is {limit!r}; § 22 states it as the size a result is replaced above, "
            "in characters, and absent where no result is replaced. A value nothing "
            "can compare to a length replaces nothing while reading as a limit "
            "somebody set.",
        )
    sidecar = _get(data, "context_guard.sidecar_dir")
    if limit is not None and (not isinstance(sidecar, str) or not sidecar.strip()):
        # ⛔ Required where the limit is, and in prose on the surface rather than by
        # the conditional marker: that marker compares a key against a stated
        # value, and what makes this key needed is *a number being stated at all*.
        # ⚠️ The refusal is about the key and not the directory: a path that cannot
        # be written is the guard's to answer, and § 22 has it leave the result
        # whole, while a project with no key at all has nowhere for the full text
        # to go and would lose every result the arm replaced.
        raise ConfigError(
            "context_guard.sidecar_dir",
            f"is {sidecar!r}; § 22 states it wherever `result_limit_chars` is -- "
            "the directory a replaced result's full text is written to, outside "
            "every working tree. With nowhere to write it, a replacement is a "
            "result the window has lost and nothing can recover.",
        )


def surface_for(skills_root: str = ".") -> str:
    """The surface a project's configuration is held to (§ 1).

    The installed plugin's copy, except where the skills root carries a copy of
    its own -- a project that *ships* this surface rather than only consuming it.
    Then that one is read, because the configuration and the surface are two
    halves of one statement and the half under work is the one in the tree.

    ⛔ The case this exists for is a work tree, and it is a correctness
    requirement rather than a convenience. A harness serves the plugin from one
    installed path, which is a checkout of the integration branch; a role runs in
    a tree whose branch is somewhere else. Holding that tree's configuration to
    the installed branch's surface refuses it for every key the branch has not
    caught up to yet -- measured, and what it costs is not a message: a key newly
    marked `# required` made the configuration unreadable in every tree cut
    before it, and the guards that read a configuration to decide what to hold
    held every command to nothing, in a project that had configured them.

    ⚠️ It is the *surface* that moves and never the configuration. A project's
    facts are read where `load` finds them and nowhere else: a tree carries the
    configuration under work, so reading some other tree's would discard the
    statement the branch is making -- the mirror of the failure above, and the
    reason the skills root is still the only place a configuration is looked for.

    ⚠️ An adopter is unaffected, and that is a property of the test rather than a
    case handled: a project that consumes the plugin carries no surface, so there
    is nothing for this to find and the installed copy is read. The two answers
    coincide for the shipping project's own primary checkout as well, that root
    and the installed path being the same directory.
    """
    own = os.path.join(skills_root or ".", PLUGIN_IN_REPO, "config", "schema.md")
    return own if os.path.isfile(own) else SURFACE


def configured(skills_root: str = ".") -> bool:
    """Whether this project states a configuration at all.

    The question a hook carrier asks before it acts: a hook is addressed by an
    event rather than by an invocation, so it fires in every project the install
    reaches, including the ones that have never adopted this toolkit.

    ⛔ **It answers nothing about whether that configuration loads.** A file that
    is there and does not resolve is the project's own statement, badly written,
    and a carrier reading values out of one reports that rather than going quiet
    -- which is why this is a question of its own and not `load`'s boolean form.

    ⛔ The same path `load` resolves, and no walk up the tree: where a project's
    configuration lives is one statement, and a carrier searching upwards would
    act on a parent project's facts in a directory that states none.
    """
    return os.path.isfile(os.path.join(skills_root or ".", CONFIG_PATH))


def load(skills_root: str = ".", *, check_paths: bool = True) -> Config:
    """Resolve a project's configuration relative to its skills root.

    `check_paths` tests that the configured `code` root exists. A role leaves it
    on: a fresh clone of an outer repository does not contain the inner one, and
    proceeding from there addresses the wrong repository having done something
    plausible first. The examples are shapes rather than projects, so the
    self-test below turns it off for them.
    """
    surface = surface_for(skills_root)
    with open(surface, encoding="utf-8") as handle:
        facts = surface_facts(handle.read())

    path = os.path.join(skills_root, CONFIG_PATH)
    if not os.path.exists(path):
        raise ConfigError(
            CONFIG_PATH,
            f"not found under the skills root {os.path.abspath(skills_root)!r}. "
            "A project states its facts there, relative to the skills root, and "
            "the path is not configurable.",
        )
    with open(path, encoding="utf-8") as handle:
        data = _load_yaml(handle.read(), CONFIG_PATH)
    if not isinstance(data, dict):
        raise ConfigError(CONFIG_PATH, "is empty or is not a block of keys.")

    return _resolve(
        data, skills_root, facts, check_paths, os.path.abspath(path), surface
    )


def load_text(text: str, skills_root: str, *, check_paths: bool = False) -> Config:
    """Resolve a configuration already in hand. Used to load the examples."""
    surface = surface_for(skills_root)
    with open(surface, encoding="utf-8") as handle:
        facts = surface_facts(handle.read())
    data = _load_yaml(text, CONFIG_PATH)
    if not isinstance(data, dict):
        raise ConfigError(CONFIG_PATH, "is empty or is not a block of keys.")
    return _resolve(data, skills_root, facts, check_paths, None, surface)


def _resolve(
    data: dict,
    skills_root: str,
    facts: dict,
    check_paths: bool,
    source: str | None = None,
    surface: str | None = None,
) -> Config:
    roots, collection = _code_roots(data, facts)

    # ⛔ One view per root, each resolved and validated as a configuration of one
    # repository -- so every rule below is enforced per root without being
    # written twice, and the two forms § 1 states differ in `_code_roots` alone.
    # ⚠️ The single form's view shares this dict rather than copying it: a
    # project with one code repository is then not merely validated the same way
    # but reading the same object, which is what makes *unchanged* a property
    # rather than a claim.
    views: dict[str, Config] = {}
    # ⛔ Complete before the first view is validated, rather than accumulated as
    # the loop runs. It is what decides whether a refusal names the entry a
    # person would write the key in, and a set still filling up would answer
    # that differently for the first root than for the last -- the first one's
    # missing slug reported at the project's path and the second one's at its
    # own, for one defect written twice.
    overridden: set[str] = {"roots.code"} if collection else set()
    if collection:
        for key in roots:
            for name in facts.get("per_root") or ():
                entry = _get(data, f"roots.code.{key}.{name}") or {}
                overridden.update(f"{name}.{stated}" for stated in entry)

    for key, root in roots.items():
        if collection:
            view = dict(data)
            view["roots"] = {**(data.get("roots") or {}), "code": root["path"]}
            for name, block in root.items():
                if name != "path":
                    view[name] = block
        else:
            view = data
        for path, value in facts["defaults"].items():
            _set_default(view, path, value)
        try:
            validate(view, facts)
        except ConfigError as error:
            if not collection:
                raise
            # The key a view refuses on is that root's, so the refusal names
            # where a person would write it rather than a path the file does not
            # carry. ⚠️ A key no root states for itself keeps its own path: the
            # project's own block is where it is written and where it is missing
            # from, so rewriting that one would send a reader to an entry that
            # was never its home.
            at = error.key
            if at == "roots.code":
                at = f"roots.code.{key}.path"
            elif any(
                at == stated or at.startswith(f"{stated}.") for stated in overridden
            ):
                at = f"roots.code.{key}.{at}"
            raise ConfigError(at, str(error).partition(": ")[2]) from None
        views[key] = Config(
            view, skills_root, facts, source, surface, root_key=key
        )
        # A view is the whole of its own answer, so it reports itself as the one
        # root there is. ⛔ Without this a root resolved by name reports no root
        # at all, which is the one output § 1 forbids: a role names the
        # repository its configuration addresses before it acts.
        views[key].views = {key: views[key]}

    # § 4.7, after every view and before the paths are tested: the rules turn on
    # how many roots there are, which no view can see.
    _code_root_facet(data, roots)

    config = Config(
        data, skills_root, facts, source, surface, views=views, overridden=overridden
    )
    for key, view in views.items():
        if check_paths and not os.path.isdir(view.code_root):
            raise ConfigError(
                "roots.code" if not collection else f"roots.code.{key}.path",
                f"names {view.code_root!r}, which does not exist. A skill stops "
                "here rather than proceeding -- a fresh clone of an outer "
                "repository does not contain the inner one.",
            )
    return config


# --- self-test -------------------------------------------------------------
#
# The acceptance check of the work item this reader was built for, run as code:
# every example loads, a missing required key fails with the key named, a
# deliberately absent facet loads silently, and the trackerless example reports
# what it cannot do rather than failing.


def _examples() -> list[str]:
    return sorted(
        os.path.join(EXAMPLES, name)
        for name in os.listdir(EXAMPLES)
        if name.endswith((".yaml", ".yml"))
    )


# ⛔ The keys the surface is expected to mark, and the facets it is expected to
# mark absent-capable -- written out here, in the test, on purpose. This is a
# second statement of the same fact, in the one place where a second statement
# is what makes the first one hold: the reader derives both sets from the
# surface, so a test that derived its assertions from the surface too would
# assert whatever the surface happened to say and pass. That is precisely how
# the retired `REQUIRED` table's assertions behaved -- generated from the table,
# so deleting an entry deleted the enforcement and its only assertion together,
# silently green. Here, a marker dropped from the surface fails the comparison
# below, and a marker added fails it until somebody writes the key down here.
MARKED_REQUIRED = [
    "already_run.never_guard",
    "body_sections",
    "branch_model.exclusive_resources",
    "branch_model.kind",
    "branch_model.parallel_trees",
    "carriers",
    "checks_local",
    "commit.staging",
    "commit.trailer",
    "context.artifacts.carrier",
    "context_guard.never_bound",
    "context_guard.unbounded",
    "done",
    "e2e_register.carrier",
    "environment.inherits",
    "executed.carrier",
    "host.checks",
    "host.kind",
    "host.landing.delete_branch",
    "host.landing.method",
    "host.repo",
    "language.repo",
    "language.work_item",
    "live_guard.session_tools",
    "memory.carrier",
    "ordering.carrier",
    "readiness",
    "roots.code",
    "session",
    "spend_guard.deny",
    "statuses",
    "tracker.kind",
    "work_item.due_date.carrier",
    "work_item.estimate.carrier",
    "work_item.priority.carrier",
    "work_item.template.carrier",
    "work_item.type.carrier",
]

# The blocks § 1 shows a named root carrying, stated here for the reason the list
# above is: the reader derives them from the entry the surface shows, so an
# assertion that derived them too would assert whatever the surface happened to
# say. ⛔ `path` is not among them -- it is the entry's own key rather than a
# block of the project's that the entry narrows. ⚠️ What this comparison catches
# is the surface's entry losing a block, which empties the derivation; what it
# cannot catch is the derivation replaced by a literal of these same contents,
# and what catches *that* is the arm asserting the shipped collection is refused
# once the derived set is emptied.
PER_ROOT_BLOCKS = ["branch_model", "host"]

# The conditional requirements, stated here for the reason the list above is:
# derived assertions would assert whatever the surface happened to say. Each entry
# is (the key, the key its requiredness turns on, the value that turns it on).
#
# ⚠️ These name tracker kinds, where the fixtures below deliberately do not. The
# two are different things: which example a plant is broken against must not
# depend on a kind this code picked, while *what the surface marks* cannot be
# stated without the values it marks it under -- the surface names every kind, and
# an inventory that would not would be an inventory of nothing.
# A key the surface declares **relatively**, with the value to condition on — the
# case the suffix-tolerant comparison in `surface_facts` exists for, stated here so
# the assertion does not derive its own fixture from the surface. The surface shows
# this key in a fence opening at `type_branch_prefix:`, so the walk yields two
# segments where § 1 tells a marker to write three.
RELATIVELY_DECLARED = ("work_item.type_branch_prefix.bug", "bugfix")

MARKED_REQUIRED_WHEN = [
    # § 10's one, meaningless under the mode that creates no tree: with nothing
    # ever pruned there is no removal for an ignored path to be lost to. ⚠️ Its
    # sibling `tree_dir` is **not** here, carrying the same condition in prose
    # and a rule of its own -- that refusal names what the role was left unable
    # to do, which a marker's message cannot say.
    ("branch_model.regenerable", "branch_model.kind", "worktree"),
    # § 15's five, each meaningless where the facet is absent and each needed by
    # one of the two comparisons: the first three by the register-against-suite
    # one, the last two by the change-against-both one.
    ("e2e_register.exemptions", "e2e_register.carrier", "file"),
    ("e2e_register.heading", "e2e_register.carrier", "file"),
    ("e2e_register.judged", "e2e_register.carrier", "file"),
    ("e2e_register.register", "e2e_register.carrier", "file"),
    ("e2e_register.suite", "e2e_register.carrier", "file"),
    # § 16's two, each the command one half of the arithmetic is read from and each
    # meaningless where the facet is absent. ⛔ `min` is **not** here: a floor left
    # unset is the weaker configuration the section states, where the counts are
    # reported and nothing is judged, so marking it required would refuse that.
    ("executed.declares", "executed.carrier", "command"),
    ("executed.reports", "executed.carrier", "command"),
    # § 25's four, each meaningless under a carrier that cannot read it -- and
    # each *refused* there rather than merely unmarked, which is a rule of the
    # reader beside the marker rather than a second spelling of it. ⚠️
    # `write_from` is two entries for one key, which is what the marker's own
    # keying is for: it is needed under either carrier that writes and read by
    # nothing under the one that does not.
    ("memory.index", "memory.carrier", "path"),
    ("memory.store", "memory.carrier", "path"),
    ("memory.write_from", "memory.carrier", "derived"),
    ("memory.write_from", "memory.carrier", "path"),
    ("tracker.board", "tracker.kind", "trello"),
    ("tracker.project.number", "tracker.kind", "github-projects"),
    ("tracker.project.owner", "tracker.kind", "github-projects"),
    ("tracker.project_key", "tracker.kind", "jira"),
    # ⚠️ Two entries for one kind, which is the first block where that happens:
    # § 3 states that an address and the project within it are different halves
    # and that neither is derivable from the other, so a configuration carrying
    # one of them is as unaddressable as one carrying neither.
    ("tracker.site", "tracker.kind", "jira"),
]

# The keys the surface marks procedure, stated here for the reason the lists
# above are: an assertion derived from the surface would assert whatever the
# surface happened to say. ⛔ This one carries the whole weight of the class,
# since the reader keeps no list of its own to compare against -- drop the clause
# from the surface and this is what reddens.
MARKED_PROCEDURE = ["audit_trail", "fail_open", "install", "readings", "waive_review"]

# The list keys whose membership a rule in this reader reads off the surface, and
# the members each shows. Stated here for the reason the sets above are, and
# ⛔ scoped to the paths a rule reads: the surface shows other lists to
# illustrate a project's own values, and holding those would be an inventory of
# the fence instead of one of what is enforced.
SHOWN_LISTS = {"session.parts": ["tracker", "memory", "commit"]}

MARKED_ABSENT_CAPABLE = [
    "context.artifacts",
    "e2e_register",
    "executed",
    "memory",
    "ordering",
    "work_item.code_root",
    "work_item.due_date",
    "work_item.estimate",
    "work_item.priority",
    "work_item.template",
    "work_item.type",
]


def _surface_without(marker: re.Pattern) -> str:
    """The surface with one marker stripped from every line that carries it.

    Used to plant the absence of a marker class. Stripping the clause rather
    than editing a copy by hand keeps the plant honest: what is removed is
    exactly what the reader looks for, so a reader that stopped looking would
    pass the plant.
    """
    with open(SURFACE, encoding="utf-8") as handle:
        out = []
        for line in handle.read().splitlines():
            body, hash_, comment = line.partition("#")
            if hash_:
                kept = [c.strip() for c in comment.split(";") if not marker.match(c.strip())]
                line = f"{body}# {'; '.join(kept)}" if kept else body.rstrip()
            out.append(line)
    return "\n".join(out)


def _surface_without_procedure() -> str:
    """The surface with every `# procedure:` clause removed.

    The plant that tells a reader of the surface from a reader of itself, for a
    class where that is the whole mechanism: nothing in this module lists the
    procedure-only keys, so stripping the clauses must make the refusal
    disappear. A reader that had quietly grown a list of its own would go on
    refusing with the surface silent.
    """
    with open(SURFACE, encoding="utf-8") as handle:
        return "\n".join(
            line
            for line in handle.read().splitlines()
            if not PROCEDURE_CLAUSE.match(line.strip())
        )


def _surface_without_retirements() -> str:
    """The surface with every `# retired:` clause removed.

    The counterpart of `_surface_without` for a marker written as a line of its
    own rather than as a clause of a key's trailing comment, and planted for the
    same reason: `retired_keys` replaced by a constant passes every assertion
    that only compares it against this reader's own list, which is the shape
    `MARKED_REQUIRED`'s comment names one marker class over.
    """
    with open(SURFACE, encoding="utf-8") as handle:
        return "\n".join(
            line
            for line in handle.read().splitlines()
            if not RETIRED_CLAUSE.match(line.strip())
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

    paths = _examples()
    check("the examples directory holds configurations", bool(paths))

    loaded: dict[str, Config] = {}
    for path in paths:
        name = os.path.basename(path)
        try:
            with open(path, encoding="utf-8") as handle:
                loaded[name] = load_text(handle.read(), EXAMPLES)
            print(f"  ok    {name} loads")
        except ConfigError as error:
            failures += 1
            print(f"  FAIL  {name} does not load: {error}")

    # A deliberately absent facet loads silently; an unset one does not.
    silent = [
        name
        for name, config in loaded.items()
        if config.get("work_item.estimate.carrier") == "none"
    ]
    check("a deliberately absent facet loads silently", bool(silent))

    # § 23's report arms, each held by the example that takes it: one example
    # runs the commit third alone and one maps no bookkeeping role at all. ⛔ The
    # last assertion is what keeps this honest -- an arm no example reaches is an
    # arm nothing asserts can speak, which is how the § 19 arm one facet over got
    # to be deletable with every assertion green.
    subset, unmapped = [], []
    for name, example in loaded.items():
        parts = _absent_as(example.get("session.parts"), [])
        lines = example.unavailable()
        every = example.facts.get("lists", {}).get("session.parts", [])
        if not parts:
            unmapped.append(name)
            check(
                f"{name} says no bookkeeping role runs there",
                any("session.parts: []" in line for line in lines),
                f"reported {lines!r}",
            )
        elif len(parts) < len(every):
            subset.append(name)
            check(
                f"{name} names the thirds of that role it does not run",
                all(
                    any(third in line for line in lines)
                    for third in every
                    if third not in parts
                ),
                f"reported {lines!r}",
            )
    check(
        "an example reaches each of those two arms",
        bool(subset) and bool(unmapped),
        f"a subset in {subset!r}, none mapped in {unmapped!r}",
    )

    # The surface's key-clause marked sets, against the test's own statement of
    # them. ⚠️ The retirement class is held separately, below: it is marked by a
    # line rather than by a key's clause, and its two statements are the reader's
    # `RETIRED` and the surface's clauses rather than a list written here.
    # Both directions, and the difference is named rather than reported as a
    # count: a marker added to the surface and a marker dropped from it are
    # different problems with different fixes.
    with open(SURFACE, encoding="utf-8") as handle:
        surface = surface_facts(handle.read())
    for label, derived, expected in (
        ("required", set(surface["required"]), set(MARKED_REQUIRED)),
        (
            "conditionally required",
            set(surface["required_when"]),
            set(MARKED_REQUIRED_WHEN),
        ),
        ("absent-capable", set(surface["absent_reason"]), set(MARKED_ABSENT_CAPABLE)),
        ("procedure-only", set(surface["procedure"]), set(MARKED_PROCEDURE)),
    ):
        check(
            f"the surface marks exactly the {label} keys this test states",
            derived == expected,
            f"the surface marks {sorted(derived - expected)} that this test does not, "
            f"and this test states {sorted(expected - derived)} that the surface does not",
        )

    # The list vocabularies a rule reads off the surface, held to a statement
    # written here for the reason the marked sets above are: the reader derives
    # them from the surface, so an assertion that derived them too would assert
    # whatever the surface happened to show and pass. ⛔ Only the paths a rule
    # actually reads — a list the surface shows to illustrate a project's own
    # values is not a vocabulary, and asserting those would be an inventory of
    # the fence rather than of what is enforced.
    for path, expected in sorted(SHOWN_LISTS.items()):
        check(
            f"the surface shows `{path}` as exactly the list this test states",
            surface["lists"].get(path) == expected,
            f"the surface shows {surface['lists'].get(path)!r}",
        )

    for facet in MARKED_ABSENT_CAPABLE:
        broken = _example_without(f"{facet}.absent_reason", loaded)
        check(
            f"an unset `{facet}` is refused, with the key named",
            broken == f"{facet}.absent_reason",
            f"reported {broken!r}",
        )

    for path in MARKED_REQUIRED:
        broken = _example_missing(path, loaded)
        check(f"a config missing `{path}` is refused, with the key named",
              broken == path, f"reported {broken!r}")

    # § 3's per-kind blocks, each broken against an example that meets its own
    # condition. ⛔ The example is found by the condition rather than named, so
    # a kind whose block nothing illustrates fails here instead of being tested
    # against whichever file this code happened to pick. That an example carries
    # every key its own kind requires is asserted by the loads above: a key
    # deleted from one leaves the reader refusing it, and the file stops loading.
    for path, on, value in MARKED_REQUIRED_WHEN:
        data = _example_meeting(on, value)
        check(
            f"an example states `{on}: {value}`, so its block is exercised",
            data is not None,
        )
        if data is None:
            continue
        broken = _refused(_without(data, path))
        check(
            f"a `{on}: {value}` config missing `{path}` is refused, with the key named",
            broken == path,
            f"reported {broken!r}",
        )
        empty = _refused(_with(_example_meeting(on, value), path, None))
        check(
            f"a `{on}: {value}` config whose `{path}` is empty is refused the same way",
            empty == path,
            f"reported {empty!r}",
        )

    # The two ways a condition can be written so that it never fires, each
    # planted on the surface itself. A requirement nobody can meet reads exactly
    # like one somebody does, and the keys it guards go unenforced in silence.
    for on, value in sorted({(o, v) for _, o, v in MARKED_REQUIRED_WHEN}):
        guarded = sorted(p for p, o, v in MARKED_REQUIRED_WHEN if (o, v) == (on, value))
        for label, planted in (
            ("a key the surface declares nowhere", f"required_when: {on}_no_such = {value}"),
            ("a value outside that key's own set", f"required_when: {on} = no-such-value"),
        ):
            with open(SURFACE, encoding="utf-8") as handle:
                text = handle.read().replace(f"required_when: {on} = {value}", planted)
            try:
                surface_facts(text)
                reported = None
            except ConfigError as error:
                reported = error.key
            check(
                f"a condition on {label} is refused, naming the key it guards",
                reported in guarded,
                f"reported {reported!r}",
            )

        # ⛔ And the direction that guard must never fail in. A mistyped clause is
        # a round trip; a legitimate marker refused at load time is every role in
        # the project stopping on a configuration that is correct. Both plants
        # below ride the same marker line, replaced rather than appended, so a
        # reworded surface takes the plant with it instead of leaving it green.
        for label, planted, expected in (
            (
                "a clause that means to be the marker and does not parse",
                f'required_when: {on} = "{value}"',
                "refused",
            ),
            (
                # Written out rather than derived: the surface declares this key
                # inside a fence that opens at an indent, so the absolute spelling
                # § 1 mandates is longer than the path the walk yields. If the
                # surface stops declaring it, this assertion fails and says so.
                "a condition naming a relatively-declared key the absolute way",
                f"required_when: {RELATIVELY_DECLARED[0]} = {RELATIVELY_DECLARED[1]}",
                "accepted",
            ),
        ):
            with open(SURFACE, encoding="utf-8") as handle:
                text = handle.read().replace(f"required_when: {on} = {value}", planted)
            try:
                surface_facts(text)
                got = "accepted"
            except ConfigError:
                got = "refused"
            check(f"{label} is {expected}", got == expected, f"was {got}")

    # The marker itself, planted away in each direction. ⛔ A surface that
    # states no requiredness must redden rather than accept anything: without
    # this, dropping every `# required` would leave the reader applying no
    # requiredness rule at all and every example still loading clean.
    for label, marker in (
        ("requiredness", REQUIRED_CLAUSE),
        ("conditional requiredness", REQUIRED_WHEN_CLAUSE),
        ("absent-capable facets", ABSENT_REASON_CLAUSE),
    ):
        try:
            surface_facts(_surface_without(marker))
            refused = None
        except ConfigError as error:
            refused = str(error)
        check(
            f"a surface stating no {label} is refused rather than read as none",
            refused is not None and "markers were dropped" in refused,
            f"reported {refused!r}",
        )

    # And the marker put somewhere it is read nowhere. A plant for this branch
    # because the branch exists to make a silently-ignored marker impossible,
    # which is only true while something asserts it is not ignored.
    with open(SURFACE, encoding="utf-8") as handle:
        misplaced = handle.read().replace(
            "  kind: github                               # required",
            "  kind: github                               # required; absent_reason",
            1,
        )
    try:
        surface_facts(misplaced)
        where = None
    except ConfigError as error:
        where = error.key
    check(
        "`# absent_reason` away from a `carrier` is refused, with the key named",
        where == "host.kind",
        f"reported {where!r}",
    )

    trackerless = [c for c in loaded.values() if not c.has_tracker]
    check("the trackerless example loads", bool(trackerless))
    if trackerless:
        reported = trackerless[0].unavailable()
        check(
            "the trackerless example reports what it could not do",
            any("tracker" in line for line in reported),
            f"reported {reported!r}",
        )

    # § 2's runner statement, both arms held against the examples rather than
    # against a fixture. ⛔ The green side of the walk, which the plants above
    # cannot show: every refusal in `host_runner` is asserted there, and an arm
    # widened until it rejected a legitimate block would pass all twelve of them
    # while making the facet unusable. ⚠️ Found by the condition and never
    # named, for the reason § 3's per-kind blocks are: a shape no example
    # carries has to fail here rather than be tested against whichever file this
    # code happened to pick.
    stating = [c for c in loaded.values() if c.runner() is not None]
    check(
        "an example states a `host.runner`, so the block is exercised",
        bool(stating),
        "no example states where its jobs run, so every refusal in the walk is "
        "asserted and nothing asserts the walk accepts a block somebody wrote",
    )
    if stating:
        read = stating[0].runner()
        check(
            "and it reads back the label, the capacity and the budget",
            read["label"] and read["concurrent_jobs"] >= 1 and read["budget_minutes"] >= 1,
            f"read {read!r}",
        )
        check(
            "and a single-runner account makes the budget a queue budget",
            read["budget_is_a_queue_budget"] == (read["concurrent_jobs"] == 1),
            "the pair § 2 says gives the budget its meaning was not derived from it",
        )
    silent = [c for c in loaded.values() if c.runner() is None]
    check(
        "an example states none, so the absent case is exercised too",
        bool(silent),
        "every example states where its jobs run, so the legitimate absence -- "
        "the host kind's own default answering -- is asserted nowhere",
    )
    if silent:
        reported = silent[0].unavailable()
        check(
            "and the absence is reported rather than passed over",
            any("`host.runner` is absent" in line for line in reported),
            f"reported {reported!r}",
        )
        # ⛔ The direction that matters: § 2 keeps the per-kind default off this
        # surface, so a report naming one would be the reader inventing the fact
        # the facet exists to have stated -- and every workflow file would then
        # be held to a label nobody chose.
        check(
            "and names no default label of its own",
            not any("ubuntu" in line.lower() for line in reported),
            f"reported {reported!r}",
        )

    # § 2's title form, both arms held against the examples for the reason the
    # runner's are: the plants above assert every refusal in the walk, and an arm
    # widened until it rejected a form somebody wrote would pass all twelve of
    # them while making the facet unusable.
    titled = [c for c in loaded.values() if c.pull_request_title() is not None]
    check(
        "an example states a `host.pull_request_title`, so the block is exercised",
        bool(titled),
        "no example states what a title opens with, so every refusal in the walk "
        "is asserted and nothing asserts the walk accepts a form somebody wrote",
    )
    if titled:
        read = titled[0].pull_request_title()
        check(
            "and it reads back the reference, the repetition and the base refs",
            PLACEHOLDER in read["reference"]
            and isinstance(read["repeated"], bool)
            and bool(read["into"]),
            f"read {read!r}",
        )
    untitled = [c for c in loaded.values() if c.pull_request_title() is None]
    check(
        "an example states none, so the absent case is exercised too",
        bool(untitled),
        "every example states a title form, so the legitimate absence -- a title "
        "that opens with no reference -- is asserted nowhere",
    )
    if untitled:
        reported = untitled[0].unavailable()
        check(
            "and the absence is reported rather than passed over",
            any("`host.pull_request_title` is absent" in line for line in reported),
            f"reported {reported!r}",
        )
        # ⛔ The direction that matters: the absence of a rule is not a rule
        # permitting anything, and a report saying otherwise would hand a role a
        # statement the project never wrote.
        check(
            "and the absence is not reported as a title rule of its own",
            not any("allowed" in line.lower() for line in reported),
            f"reported {reported!r}",
        )

    missing_root = _refuses_missing_code_root()
    check(
        "a `code` root that does not exist stops rather than proceeding",
        missing_root == "roots.code",
        f"reported {missing_root!r}",
    )

    # § 1's named roots, held against the collection this repository ships.
    print("\n§ 1's named roots, and the one answer a project-level read does not have:")
    check(
        "the surface shows exactly the blocks a named root carries that this test states",
        set(surface["per_root"]) == set(PER_ROOT_BLOCKS),
        f"the surface shows {sorted(set(surface['per_root']) - set(PER_ROOT_BLOCKS))} "
        f"that this test does not, and this test states "
        f"{sorted(set(PER_ROOT_BLOCKS) - set(surface['per_root']))} that the surface does not",
    )
    keys = _collection_keys()
    check(
        "an example carries named roots, so the shape an adopter copies is the one held",
        len(keys) > 1,
        f"the examples carry {keys!r}",
    )
    if len(keys) > 1:
        first, second = keys[0], keys[1]
        with open(_examples()[0], encoding="utf-8") as handle:
            single = load_text(handle.read(), EXAMPLES)
        several = _resolve(_a_collection_example(), EXAMPLES, surface, False)

        # ⛔ The direction that matters, and the reason this facet is not simply
        # a block a role loops over: a project-level read of a fact stated per
        # root has no answer, and the first root's answer is available and
        # wrong. A role is handed the stop instead.
        for path in ("roots.code", "host.repo", "host.checks"):
            refused = None
            try:
                several.get(path)
            except ConfigError as error:
                refused = error.key
            check(
                f"a project-level read of `{path}` is refused where a root states it",
                refused == path,
                f"reported {refused!r}",
            )
            check(
                "and the refusal names the roots that carry it, not a count alone",
                all(repr(k) in str(_project_read(several, path)) for k in keys),
                str(_project_read(several, path)),
            )
        # ⚠️ And the complement, which is what keeps the refusal from being a
        # project with two roots having no readable configuration at all: a fact
        # no root states for itself is one answer and is answered.
        shared = several.get("host.kind")
        check(
            "a fact no root states for itself is still answered at the project level",
            shared is not None,
            f"reported {shared!r}",
        )
        check(
            "the mirrored-command view is refused for the same reason the key is",
            _project_read(several, "mirrors") is not None,
            "mirrors() answered across two repositories' disjoint check sets",
        )
        # Each root's own answers, which is what the refusal sends a role to.
        per_root_repo = {k: several.root(k).get("host.repo") for k in keys}
        check(
            "each root answers with its own slug",
            len(set(per_root_repo.values())) == len(keys)
            and all(per_root_repo.values()),
            str(per_root_repo),
        )
        differ = {k: several.root(k).get("branch_model.kind") for k in keys}
        check(
            "and with its own branch model, which is the axis the measurement forced",
            len(set(differ.values())) > 1,
            str(differ),
        )
        inherited = {k: several.root(k).get("host.landing.method") for k in keys}
        check(
            "a key an entry does not state is read from the project's own block",
            len(set(inherited.values())) == 1 and all(inherited.values()),
            str(inherited),
        )
        reported = several.to_dict()
        check(
            "the resolution reports every root with the repository it addresses",
            set(reported["code_roots"]) == set(keys)
            and all(r["repo"] for r in reported["code_roots"].values()),
            str(reported["code_roots"]),
        )
        check(
            "and reports no single `code_root`, which would be a silent pick",
            "code_root" not in reported,
            str(sorted(reported)),
        )
        named = several.root(keys[0]).to_dict()
        check(
            "a root resolved by name reports itself as the one root there is",
            named.get("code_root") and set(named["code_roots"]) == {keys[0]},
            str(sorted(named)),
        )
        absent = None
        try:
            several.root("a-root-no-project-carries")
        except ConfigError as error:
            absent = str(error)
        check(
            "a root this project does not carry stops, naming the ones it does",
            absent is not None and all(repr(k) in absent for k in keys),
            str(absent),
        )

        # ⛔ The single form, asserted rather than assumed: it is not merely
        # validated the same way, it reads the same dict, which is what makes
        # *a project with one code repository is unchanged* a property.
        check(
            "the single form's one root reads the project's own dict",
            single.only_root.data is single.data and single.per_root("host.repo") == [],
            f"{single.root_keys!r}, crossing {single.per_root('host.repo')!r}",
        )
        check(
            "and is reported under the key § 1 gives it",
            single.root_keys == [ONE_ROOT],
            str(single.root_keys),
        )

        for label, mutate, expected in (
            ("a block of named roots with nothing in it",
             lambda roots: roots.clear(), "roots.code"),
            ("a named root that is not a block",
             lambda roots: roots.__setitem__(first, "a-path"), f"roots.code.{first}"),
            ("a named root stating no path",
             lambda roots: roots[first].pop("path"), f"roots.code.{first}.path"),
            ("a named root carrying a block the surface does not show",
             lambda roots: roots[first].__setitem__("deploy", {}),
             f"roots.code.{first}.deploy"),
            ("two roots resolving to one slug",
             lambda roots: roots[second]["host"].__setitem__(
                 "repo", roots[first]["host"]["repo"]),
             f"roots.code.{second}.host.repo"),
            ("two roots naming one path",
             lambda roots: roots[second].__setitem__("path", roots[first]["path"]),
             f"roots.code.{second}.path"),
            ("a root whose own block drops a required key",
             lambda roots: roots[first]["host"].pop("repo"),
             f"roots.code.{first}.host.repo"),
        ):
            broken = _collection_broken(mutate)
            check(
                f"{label} is refused, with the root's own key named",
                broken == expected,
                f"reported {broken!r}, expected {expected!r}",
            )
        # ⛔ And the per-root blocks are read off the surface rather than listed
        # in this module: with the derivation emptied, the shipped collection's
        # own `host` is refused as a block a named root does not carry. ⚠️ What
        # this arm does not catch is the derivation replaced by a literal of the
        # same contents -- the set comparison above is that direction, reddening
        # the moment the surface's entry stops showing a block.
        blind = dict(surface)
        blind["per_root"] = []
        unread = _refused(_a_collection_example(), facts=blind)
        check(
            "the blocks a named root carries are read from the surface, not from here",
            unread == f"roots.code.{first}.host",
            f"reported {unread!r}",
        )

        # § 4.7. ⛔ Against the **shipped** collection for the reason the arms
        # above are: what an adopter copies is what is held, and a hand-built
        # facet here would be a shape this repository ships nowhere. Its own
        # `roots.code` is the single form, so every arm below is reached through
        # the one example that carries two.
        print("\n§ 4.7, which of several code roots a work item belongs to:")
        facet = _get(_a_collection_example(), "work_item.code_root") or {}
        prefix = facet.get("label_prefix") or ""
        mapping = facet.get("roots") or {}
        check(
            "the collection example carries the facet, every root mapped",
            facet.get("carrier") and set(mapping) == set(keys),
            f"carrier {facet.get('carrier')!r} mapping {sorted(mapping)!r}",
        )
        # ⛔ The resolution itself, per root: the value the item carries resolves
        # to that root's own view and never to the first of them. ⚠️ Asserted on
        # the slug rather than on the object, because a view answering for the
        # wrong root would otherwise read as a pass.
        #
        # ⚠️ The refusal is caught rather than allowed to raise. Reviewed on this
        # change: a plant that turns the match into a *stop* -- deleting the
        # label arm is one -- raised through this arm and aborted the suite,
        # since `self_test` is called outside the caller's own handler. The
        # sibling arm below had the same hole as an unbound name.
        resolved = {}
        for key, value in mapping.items():
            try:
                resolved[key] = several.root_for([f"{prefix}{value}"]).get("host.repo")
            except ConfigError as error:
                resolved[key] = f"stopped: {error}"
        check(
            "an item's own value resolves to that root and no other",
            resolved == {k: several.root(k).get("host.repo") for k in mapping},
            str(resolved),
        )
        # ⚠️ The three readings are asserted on the lead clause each one carries,
        # because the remedies differ: a value to add, a value to correct, and a
        # value to remove. Reviewed on this change, where one message told the
        # second case to add what it already had.
        for label, values, wanted in (
            ("an item carrying nothing at all", [],
             "is not stated on this item at all"),
            ("an item carrying nothing the facet maps", ["a label no root answers to"],
             "names no root this project carries"),
            ("an item naming two roots", [f"{prefix}{mapping[k]}" for k in keys],
             "belongs to one repository"),
        ):
            stopped = None
            try:
                several.root_for(values)
            except ConfigError as error:
                stopped = str(error)
            check(
                f"{label} stops rather than resolving",
                stopped is not None and wanted in stopped,
                str(stopped),
            )
        # ⛔ And the stop names the roots or the values rather than a count: the
        # remedy is stating one of them on the item.
        #
        # ⚠️ Bound before the `try` and not only inside it. Reviewed on this
        # change: with the resolution planted away to one that *answers*, this
        # arm raised `NameError` instead of reporting -- aborting the suite over
        # every assertion after it, which is every § 4.7 plant below. A traceback
        # where a verdict belongs, in exactly the run the plants exist for. ⚠️ The
        # arm three above had the mirror of it for a plant that *stops*, and the
        # pair is the reason both now catch rather than one.
        named_in_stop = False
        try:
            several.root_for(["a label no root answers to"])
        except ConfigError as error:
            named_in_stop = all(repr(v) in str(error) for v in mapping.values())
        check(
            "the stop names what the carrier holds for each root",
            named_in_stop,
            "the refusal named no mapped value",
        )

        for label, mutate, expected in (
            ("several roots with the facet absent",
             lambda data: _get(data, "work_item").pop("code_root"),
             "work_item.code_root.carrier"),
            ("a label-carried root with no prefix to tell the axis by",
             lambda data: _get(data, "work_item.code_root").pop("label_prefix"),
             "work_item.code_root.label_prefix"),
            ("a field-carried root with no field named",
             lambda data: _get(data, "work_item.code_root").update(carrier="field"),
             "work_item.code_root.field"),
            ("a mapping that is not a block",
             lambda data: _get(data, "work_item.code_root").update(roots="app"),
             "work_item.code_root.roots"),
            ("a root the mapping leaves out",
             lambda data: _get(data, "work_item.code_root.roots").pop(second),
             f"work_item.code_root.roots.{second}"),
            ("a mapping entry naming a root the project does not carry",
             lambda data: _get(data, "work_item.code_root.roots").__setitem__(
                 "a-root-no-project-carries", "x"),
             "work_item.code_root.roots.a-root-no-project-carries"),
            ("a mapped value naming nothing",
             lambda data: _get(data, "work_item.code_root.roots").__setitem__(second, "  "),
             f"work_item.code_root.roots.{second}"),
            ("two roots answering to one value",
             lambda data: _get(data, "work_item.code_root.roots").__setitem__(
                 second, _get(data, "work_item.code_root.roots")[first]),
             f"work_item.code_root.roots.{second}"),
            ("a carried facet the gate does not check",
             lambda data: data.__setitem__("readiness", [
                 entry for entry in data["readiness"]
                 if entry.get("check") != "code_root_stated"
             ]),
             "readiness"),
            ("the facet absent and the check configured anyway",
             lambda data: _get(data, "work_item.code_root").update(
                 carrier="none", absent_reason="the tracker cannot hold it"),
             "work_item.code_root.carrier"),
        ):
            data = _a_collection_example()
            mutate(data)
            broken = _refused(data)
            check(
                f"{label} is refused, with the key named",
                broken == expected,
                f"reported {broken!r}, expected {expected!r}",
            )

        # ⛔ The two carriers the shipped collection cannot also carry, each
        # matched its own way and each with the finding that forced the rule.
        # ⚠️ Reviewed on this change: both of these branches had no arm at all,
        # and both carried a defect -- which is why the fixture is built here
        # rather than the coverage being left to whichever carrier an example
        # happens to ship.
        print("\n§ 4.7's other two carriers, and the matching each states:")
        for label, data, values, wanted in (
            ("a title opening with a mapped value as a whole word",
             _a_collection_carrying("title_prefix", {first: "app", second: "site"}),
             ["app: add a button"], f"root {first}"),
            ("a title merely *beginning* with one, which is not a match",
             _a_collection_carrying("title_prefix", {first: "app", second: "site"}),
             ["appendix: rework the appendix"], "stop work_item.code_root"),
            ("a title handed over word-split, which is one value split on the way in",
             _a_collection_carrying("title_prefix", {first: "app", second: "site"}),
             "Fix the app header".split(), "stop work_item.code_root"),
            ("a value that opens another as a whole word, refused at the configuration",
             _a_collection_carrying("title_prefix", {first: "app", second: "app site"}),
             ["app site: a page"], f"refused work_item.code_root.roots.{second}"),
            ("a value that opens another only mid-word, which stays two roots",
             _a_collection_carrying("title_prefix", {first: "app", second: "app-site"}),
             ["app-site: a page"], f"root {second}"),
            ("a field's value, matched whole",
             _a_collection_carrying("field", {first: "APP", second: "SITE"}, field="Repo"),
             ["SITE"], f"root {second}"),
            ("a field's value naming no root",
             _a_collection_carrying("field", {first: "APP", second: "SITE"}, field="Repo"),
             ["OTHER"], "stop work_item.code_root"),
        ):
            answered = _resolved_or_refused(data, values)
            check(
                f"{label} answers `{wanted}`",
                answered == wanted,
                f"answered {answered!r}",
            )
        # ⛔ And a root resolved by name may not answer for an item: it has been
        # narrowed already, so the question has been answered by whoever narrowed
        # it. ⚠️ Told apart from a single-root project by the view's own key, both
        # carrying one root -- which is the confusion the arm reproduced.
        narrowed = None
        try:
            several.root(first).root_for([f"{prefix}{mapping[second]}"])
        except ConfigError as error:
            narrowed = str(error)
        check(
            "a root resolved by name refuses to answer which root an item names",
            narrowed is not None and first in narrowed,
            str(narrowed),
        )
        # ⚠️ And the absent case's own `absent_reason` rule, on the configuration
        # where `carrier: none` is *legal*. The generic arm for every
        # absent-capable facet builds its fixture on a single-root example, which
        # § 4.7 refuses outright -- so without this one, nothing asserts the rule
        # on the shape that can actually carry it.
        several_none = _a_collection_example()
        _get(several_none, "work_item.code_root").clear()
        _get(several_none, "work_item.code_root")["carrier"] = "none"
        several_none["readiness"] = [
            entry for entry in several_none["readiness"]
            if entry.get("check") != "code_root_stated"
        ]
        reasonless = _refused(several_none)
        check(
            "several roots, `carrier: none` and no reason is refused, with the key named",
            reasonless == "work_item.code_root.absent_reason",
            f"reported {reasonless!r}",
        )

        # ⚠️ The green side of the absent case, verified by disabling the arm
        # above rather than asserted around it: a tracker that cannot hold the
        # fact is a configuration, so `carrier: none` **with** the check dropped
        # loads -- and then the resolution stops, quoting the project's own
        # reason, instead of answering with the first root.
        absent_facet = _a_collection_example()
        _get(absent_facet, "work_item.code_root").clear()
        _get(absent_facet, "work_item.code_root").update(
            carrier="none", absent_reason="the board has nowhere to put it"
        )
        absent_facet["readiness"] = [
            entry for entry in absent_facet["readiness"]
            if entry.get("check") != "code_root_stated"
        ]
        loaded_absent = _refused(absent_facet)
        check(
            "a tracker that cannot hold the fact is a configuration, not a refusal",
            loaded_absent is None,
            f"refused on {loaded_absent!r}",
        )
        if loaded_absent is None:
            stated = _resolve(absent_facet, EXAMPLES, surface, False)
            check(
                "and it is reported as an absence rather than left to be discovered",
                any("code_root" in line for line in stated.unavailable()),
                str(stated.unavailable()),
            )
            no_answer = None
            try:
                stated.root_for(["anything at all"])
            except ConfigError as error:
                no_answer = str(error)
            check(
                "and the resolution stops with the project's reason, not the first root",
                no_answer is not None and "nowhere to put it" in no_answer,
                str(no_answer),
            )

        # ⛔ The single form, which is the other half of § 4.7's condition: a
        # project with one repository is never asked for the fact, so stating it
        # is refused rather than read by nothing -- and so is the check.
        for label, mutate, expected in (
            ("the facet stated where there is one root",
             lambda data: _place(data, "work_item.code_root.carrier", "label"),
             "work_item.code_root"),
            ("the check configured where there is one root",
             lambda data: data["readiness"].append(
                 {"check": "code_root_stated", "stop": "No repository stated."}),
             "readiness"),
        ):
            data = _a_valid_example()
            mutate(data)
            broken = _refused(data)
            check(
                f"{label} is refused, with the key named",
                broken == expected,
                f"reported {broken!r}, expected {expected!r}",
            )
        check(
            "and a single-root project that states neither is unchanged",
            _refused(_a_valid_example()) is None,
            f"refused on {_refused(_a_valid_example())!r}",
        )

    # § 1's two halves, in both directions. A retired key must be refused where a
    # project still writes it, *and* must be gone from the surface -- a key this
    # reader refuses while the surface still asks for it would make every
    # configuration that follows the surface unreadable.
    with open(SURFACE, encoding="utf-8") as handle:
        surface_text = handle.read()
    declared = surface_keys(surface_text)

    # ⛔ The set, not only each entry. Deleting an entry from `RETIRED` used to
    # delete the refusal and the assertion that holds it in one edit, silently
    # green -- so the surface's own statements are what this reader is measured
    # against, in both directions.
    stated = retired_keys(surface_text)
    performed = {path for path, _ in RETIRED}
    check(
        "every retirement the surface states is one this reader refuses",
        stated <= performed,
        f"the surface retires {sorted(stated - performed)}, which this reader accepts",
    )
    check(
        "this reader refuses no key the surface does not state as retired",
        performed <= stated,
        f"it refuses {sorted(performed - stated)}, stated nowhere on the surface",
    )
    # ⛔ And the derivation itself is planted, because the two arms above compare
    # it only against this reader's own list: `retired_keys` replaced by the
    # constant `{"roots.skills", "version"}` left both of them green. Stripping
    # the clauses from the surface is what tells a reader of the surface from a
    # reader of itself.
    stripped = retired_keys(_surface_without_retirements())
    check(
        "those arms are reading the surface, not a copy of their own answer",
        not performed <= stripped,
        "every `# retired:` clause was stripped and the reader's list was still "
        f"satisfied by {sorted(stripped)}, so nothing there reads the surface",
    )

    for path, _ in RETIRED:
        check(
            f"the surface declares no `{path}`",
            path not in declared,
            "the surface still states it, and this reader refuses it",
        )
        # ⛔ Planted through `_place`, which descends into a list where the path
        # crosses one: `done.run` is a key of a list member and nothing can write
        # it at the dotted path itself. The expectation is the path the
        # configuration then carries -- `done[0].run` -- because a refusal that
        # named the surface's spelling would send a reader to a key their file
        # does not contain.
        data = _a_valid_example()
        at = _place(data, path, ".")
        broken = _refused(data)
        check(
            f"a configuration still declaring `{path}` is refused, with the key named",
            broken == at,
            f"reported {broken!r}, expected {at!r}",
        )

    # The procedure-only class, which has no path to be looked up at: what is
    # asserted is that the *name* is refused wherever a configuration puts it,
    # and that the name comes from the surface rather than from this module.
    for name in MARKED_PROCEDURE:
        check(
            f"the surface declares no key named `{name}`",
            all(part != name for path in declared for part in path.split(".")),
            "the surface declares it, and this reader refuses it",
        )
        top = _refused(_a_valid_example_with(name, "off"))
        check(
            f"a configuration declaring `{name}` is refused, with the key named",
            top == name,
            f"reported {top!r}",
        )
        # Nested under a facet, which is where a project reaching for a switch
        # would sooner put it than at the top of the file.
        nested = _refused(_a_valid_example_with(f"language.{name}", "off"))
        check(
            f"a `{name}` nested under a facet is refused, with its path named",
            nested == f"language.{name}",
            f"reported {nested!r}",
        )

    stripped = surface_facts(_surface_without_procedure())["procedure"]
    check(
        "the procedure arm reads the surface, not a list of this reader's own",
        not stripped,
        f"the clauses were stripped and the reader still derived {sorted(stripped)}",
    )
    # ⛔ And the mechanism broken from the other end: with the clause gone the
    # same configuration must **load**. An arm that only asserts the refusal
    # happens passes just as well for a reader that refuses the key on its own
    # authority, which is the shape this class exists not to have.
    if MARKED_PROCEDURE:
        released = _refused(
            _a_valid_example_with(MARKED_PROCEDURE[0], "off"),
            facts=surface_facts(_surface_without_procedure()),
        )
        check(
            "with the clause stripped that same configuration loads",
            released is None,
            f"it was still refused on {released!r}",
        )

        # ⛔ The guard planted in five spellings and not one. A single plant —
        # the colon dropped — left the whole first alternative of the first
        # draft's grammar asserted by nothing, and two spellings slipped
        # between the pair: a space before the colon, which the clause rejected
        # and the guard exempted, and a capitalised keyword, which neither read.
        # Both shipped a marker that states a rule nothing performs, green.
        # ⚠️ `marked` is the expectation and not a verdict shape: one of these
        # must **parse**, which is the direction a guard widened to everything
        # fails in.
        marker = f"# procedure: {MARKED_PROCEDURE[0]}"
        with open(SURFACE, encoding="utf-8") as handle:
            surface_text = handle.read()
        for label, planted, expected in (
            ("the colon dropped", f"# procedure {MARKED_PROCEDURE[0]}", "refused"),
            ("a capitalised keyword", f"# Procedure: {MARKED_PROCEDURE[0]}", "refused"),
            ("a dotted path where a bare key belongs",
             f"# procedure: tracker.{MARKED_PROCEDURE[0]}", "refused"),
            ("two keys in one clause",
             f"# procedure: {MARKED_PROCEDURE[0]} history", "refused"),
            ("a space before the colon", f"# procedure : {MARKED_PROCEDURE[0]}", "parsed"),
        ):
            try:
                derived = surface_facts(surface_text.replace(marker, planted, 1))
                got = "parsed" if MARKED_PROCEDURE[0] in derived["procedure"] else "dropped"
            except ConfigError as error:
                got = "refused" if "procedure marker" in str(error) else f"refused: {error}"
            check(f"{label} is {expected}", got == expected, f"was {got}")

        # The same marker written where every marker that hangs on a key is
        # written, which the own-line scan cannot see.
        hung = surface_text.replace(
            "  kind: github                               # required",
            "  kind: github                               # required; procedure: audit_trail",
            1,
        )
        try:
            surface_facts(hung)
            where = None
        except ConfigError as error:
            where = error.key
        check(
            "the procedure marker hung on a key line is refused, with the key named",
            where == "host.kind",
            f"reported {where!r}",
        )

        # ⛔ The green side of the guard, which a grammar reading every line
        # would fail: the clause is read inside a fence and nowhere else, so the
        # same text in the prose beside a block is prose. Without this arm, a
        # guard widened to the whole document reads every sentence of this
        # surface about procedure as a mistyped marker.
        outside = surface_text.replace(
            "## 1. Roots", f"# procedure: planted_outside_a_fence\n\n## 1. Roots", 1
        )
        try:
            loose = surface_facts(outside)["procedure"]
            reported = sorted(loose)
        except ConfigError as error:
            reported = f"refused: {error}"
        check(
            "the same clause in the prose beside a block is read by nothing",
            reported == sorted(MARKED_PROCEDURE),
            f"derived {reported!r}",
        )

    # A root with no configuration stops, and names the root it looked in --
    # which is the one case § 1 can make a stop rather than a statement.
    stopped, named = _refuses_a_root_with_no_config()
    check(
        "a root with no configuration stops, naming the file",
        stopped == CONFIG_PATH,
        f"reported {stopped!r}",
    )
    check(
        "that refusal names the absolute root it looked in",
        named,
        "the message did not carry the root",
    )

    # ⛔ And the question a hook carrier asks instead of taking that stop, which
    # every one of them reads from here: the same root, answered without a
    # parser and without raising. ⚠️ Asserted in both directions, because a
    # predicate stuck on one answer silences every carrier in every project or
    # in none of them, and neither failure is visible from one side alone. The
    # stated side is planted rather than read off this tree: the plugin may be
    # installed beside a project that configures nothing.
    check(
        "a root with no configuration states none",
        not configured(EXAMPLES),
        f"{EXAMPLES} was read as stating one",
    )
    import tempfile

    with tempfile.TemporaryDirectory() as planted:
        stated = os.path.join(planted, CONFIG_PATH)
        os.makedirs(os.path.dirname(stated), exist_ok=True)
        with open(stated, "w", encoding="utf-8") as handle:
            handle.write('roots:\n  code: "."\n')
        check(
            "and a root that carries that file states one",
            configured(planted),
            f"{planted} was read as stating none",
        )
        # ⛔ Found at the whole of the path this module resolves and not by the
        # file's name, which is what keeps the predicate and the load one
        # statement: a carrier answering yes to a path `load` does not open
        # would hold a project to a file nothing ever reads.
        stray = os.path.join(planted, "elsewhere")
        os.makedirs(stray, exist_ok=True)
        with open(os.path.join(stray, os.path.basename(CONFIG_PATH)), "w",
                  encoding="utf-8") as handle:
            handle.write('roots:\n  code: "."\n')
        check(
            "while a file of that name somewhere else is not a configuration",
            not configured(stray),
            f"{stray} was read as stating one",
        )

    # Every marked default is applied. Nothing used to assert this: emptying
    # `_set_default` left the whole suite green, because every example spells
    # its defaults out and so exercises the one path the defaults do not take.
    with open(SURFACE, encoding="utf-8") as handle:
        marked = surface_facts(handle.read())["defaults"]
    check("the surface marks defaults for this reader to apply", bool(marked))
    for path, value in sorted(marked.items()):
        got = _default_applied(path)
        check(
            f"the marked default for `{path}` is applied when the key is absent",
            got == value,
            f"got {got!r}, surface marks {value!r}",
        )

    # The sentinels this reader spells out, held to the surface so that renaming
    # one there reddens the build rather than silently disabling the report it
    # drives. `none` and `never` are members of sets the surface states; which
    # member means "absent" is the part an alternation cannot say.
    for member, path in (
        ("none", "tracker.kind"),
        ("never", "writer"),
        # § 13's two. `local` is the check a `run` hangs off and `procedure` is
        # the answerer it is bound to, so a rename in the surface would leave
        # both rules reading a member that no longer exists -- and the examples
        # alone would not say so, since a rule that matches nothing refuses
        # nothing.
        ("procedure", "done.answered_by"),
        ("human", "done.answered_by"),
    ) + tuple((check, "done.check") for check in sorted(BOUND_ANSWERERS)):
        states = facts_for(path)
        check(
            f"the surface still states `{member}` in its `{path}` set",
            member in states,
            f"states {states!r}",
        )

    # § 2's second form on the green side, which the plants below cannot assert:
    # every one of them reddens, and a form that only ever reddens is a form no
    # project can write. ⛔ The discrimination is the assertion and not the load:
    # four commands behind one workflow name resolving to one answer is exactly
    # what the one-command entry did, and it loaded clean the whole time.
    four = _a_valid_example()
    four["host"]["checks"] = [_four_jobs_behind_one_workflow()]
    broken = _refused(four)
    check(
        "a workflow whose four jobs mirror four commands loads",
        broken is None,
        f"refused {broken!r}",
    )
    mirrored = _mirrored_commands(four)
    answers = [
        mirrored.get(f"the-{ordinal}-command")
        for ordinal in ("first", "second", "third", "fourth")
    ]
    check(
        "and each of the four is answered about by its own job, not by the workflow "
        "they share",
        all(answers) and len(set(answers)) == 4,
        f"resolved {answers!r}",
    )

    # § 2's `triggers` on the green side, which the plants below cannot assert
    # either and which no configuration in this tree is in: every example states
    # a trigger, so the absence is a shape no load here would otherwise meet. ⛔
    # And it has to stay loadable, the key being marked neither required nor
    # defaulted -- a reader that refused it would refuse an adopter's first
    # entry, written before anybody told them the key exists. ⚠️ Verified by
    # making the key required and watching both of these redden.
    #
    # ⚠️ Placed ahead of the two raw walks below rather than beside the record
    # read it belongs with, because those call the walk outside `_refused`: a
    # key that became mandatory would stop the suite there with a traceback, and
    # an assertion that never runs is one nobody can read a verdict from.
    silent_trigger = _a_valid_example()
    silent_trigger["host"]["checks"] = [
        {"workflow": "A planted workflow", "mirrors": "a-mirrored-command"}
    ]
    broken = _refused(silent_trigger)
    check(
        "an entry stating no `triggers` loads",
        broken is None,
        f"refused {broken!r}",
    )
    carried = (
        mirrored_runs(silent_trigger)[0]["triggers"] if broken is None else broken
    )
    check(
        "and the record it yields carries the absence rather than a default",
        broken is None and carried is None,
        f"carried {carried!r}, so a consumer would match a change against a "
        "pattern no project wrote",
    )

    # The collision the key exists for, still impossible from inside an entry:
    # two workflows naming one job, each mirroring a different command. ⛔ A
    # reader that keyed anything on the job name would answer both with one
    # entry, which is the build refused on the strength of a title check.
    shared = _a_valid_example()
    shared["host"]["checks"] = [
        {"workflow": "A first planted workflow",
         "jobs": [{"job": "a-shared-name", "mirrors": "the-first-command"}]},
        {"workflow": "A second planted workflow",
         "jobs": [{"job": "a-shared-name", "mirrors": "the-second-command"}]},
    ]
    across = _mirrored_commands(shared)
    check(
        "two workflows naming one job keep their own answers",
        len(across) == 2
        and across.get("the-first-command") != across.get("the-second-command"),
        f"resolved {across!r}",
    )

    # And the form a project whose workflow runs exactly one check writes, which
    # is what it wrote before this form existed: answered about by the workflow.
    plain = _mirrored_commands(
        {"host": {"checks": [{"workflow": "Planted", "mirrors": "a-mirrored-command"}]}}
    )
    check(
        "a workflow running one check is still answered about by its own name",
        "Planted" in (plain.get("a-mirrored-command") or ""),
        f"resolved {plain!r}",
    )

    # One planted violation per refusal branch that does real work, which is the
    # standard tools/check_single_source.py sets and this suite did not meet: it
    # covered three of sixteen, so most of `validate` could not fail.
    for label, key, mutate in _planted_violations():
        broken = _refused(mutate(_a_valid_example()))
        check(f"{label} is refused, with the key named", broken == key,
              f"reported {broken!r}")

    # ⛔ A shape rule answers what a value has to *be* and never whether it is
    # written. Requiredness is the surface's marker, checked in `validate` above,
    # and a rule that refuses absence as well states one fact twice -- with the
    # second statement outliving the first the day the resolved surface stops
    # marking the key. ⚠️ Not a theoretical pairing: § 20's rule refused an absent
    # `body_sections` on the strength of its type, so a tree whose surface
    # predated the key could not read its own configuration even once
    # `surface_for` had handed it the right surface. Found by this arm.
    #
    # The assertion is over the marked set rather than a list written here, so a
    # key that grows a shape rule is covered the day the surface marks it. ⚠️ What
    # it holds is that the refusal does not name *that* key, and not that the
    # configuration loads: a rule reading two keys against each other may
    # legitimately refuse on the other one, which is a different statement.
    #
    # ⚠️ **And that is also the limit, stated rather than discovered.** A rule
    # refusing under a *child* of the marked key walks through this arm, the two
    # paths being different strings -- so `session` marked and `session.parts`
    # refused reads as compliant here. Both of this surface's block-valued
    # required keys are in that position, and what covers them is `_absent_as` at
    # each rule rather than this assertion. Measured by review on the change that
    # added the second of them; widening the arm to descendants is a change to
    # every key's assertion and is not this one's to make.
    with open(SURFACE, encoding="utf-8") as handle:
        marked = surface_facts(handle.read())
    for path in sorted(marked["required"]):
        unmarked = dict(
            marked,
            required={
                key: section
                for key, section in marked["required"].items()
                if key != path
            },
        )
        broken = _refused(_without(_a_valid_example(), path), facts=unmarked)
        check(
            f"no shape rule answers whether `{path}` is written",
            broken != path,
            f"refused on {broken!r} with the surface no longer marking it",
        )

    # § 1's surface resolution, both answers and then the one it exists for.
    import tempfile  # noqa: PLC0415 -- the only arm that needs a directory

    with tempfile.TemporaryDirectory() as root:
        consumer = os.path.join(root, "consumer")
        os.makedirs(os.path.join(consumer, ".claude"))
        check(
            "a skills root carrying no surface is held to the installed one",
            surface_for(consumer) == SURFACE,
            f"resolved {surface_for(consumer)!r}",
        )

        # A project that ships this surface rather than only consuming it. The
        # layout is `PLUGIN_IN_REPO`, derived from where this file sits, so the
        # fixture is built the way an adopter's tree would be rather than from a
        # path spelled here.
        shipper = os.path.join(root, "shipper")
        shipped = os.path.join(shipper, PLUGIN_IN_REPO, "config")
        os.makedirs(shipped)
        os.makedirs(os.path.join(shipper, ".claude"))
        own_surface = os.path.join(shipped, "schema.md")
        with open(SURFACE, encoding="utf-8") as handle:
            installed = handle.read()
        struck, landed = _surface_without_marker(installed, "host.kind")
        check(
            "the planted surface really drops the marker it names",
            landed and "host.kind" not in surface_facts(struck)["required"],
            "the strike was a no-op, so the arm below would pass on nothing",
        )
        with open(own_surface, "w", encoding="utf-8") as handle:
            handle.write(struck)
        check(
            "a skills root that ships a surface is held to its own copy",
            surface_for(shipper) == own_surface,
            f"resolved {surface_for(shipper)!r}",
        )

        # The measured failure, as an assertion: a configuration missing a key
        # the *installed* surface marks required, in a tree whose own surface
        # does not mark it. This is what every work tree cut before a newly
        # marked key looked like, and it held every guard that reads a
        # configuration to nothing in a project that had configured them.
        stated = os.path.join(shipper, CONFIG_PATH)
        with open(stated, "w", encoding="utf-8") as handle:
            handle.write(_yaml().safe_dump(_without(_a_valid_example(), "host.kind")))
        try:
            load(shipper, check_paths=False)
            reported = None
        except ConfigError as error:
            reported = error.key
        check(
            "a tree is held to the surface it ships, not the installed one",
            reported is None,
            f"refused on {reported!r}",
        )

        # And the must-stay-red side, which is what makes the arm above a
        # measurement rather than a configuration that happens to load: the same
        # file, with the shipped surface taken away, is refused naming the key.
        os.remove(own_surface)
        try:
            load(shipper, check_paths=False)
            reported = None
        except ConfigError as error:
            reported = error.key
        check(
            "and to the installed surface where it ships none",
            reported == "host.kind",
            f"refused on {reported!r}",
        )

    # The two refusals that happen before there is a configuration to validate.
    for label, text in (
        ("a configuration that is not valid YAML", "host:\n  kind: github\n   repo: x\n"),
        ("a configuration that is not a block of keys", "- just\n- a list\n"),
    ):
        try:
            load_text(text, EXAMPLES)
            reported = None
        except ConfigError as error:
            reported = error.key
        check(f"{label} is refused, naming the file", reported == CONFIG_PATH,
              f"reported {reported!r}")

    # The repository this plugin sits in, when it has a configuration of its
    # own. Without this the one config the project actually runs on is held by
    # nothing: corrupting it left both gates green while the reader refused it.
    own = os.path.join(REPO_ROOT, CONFIG_PATH)
    if os.path.exists(own):
        try:
            config = load(REPO_ROOT)
            print(f"  ok    this repository's own {CONFIG_PATH} loads")
            reported = config.unavailable()
            check(
                "it reports every absence that stops a role, naming the key",
                all(
                    any(key in line for line in reported)
                    for key in _load_bearing_absences(config)
                ),
                f"reported {reported!r}",
            )
            # ⛔ And every facet whose carrier this configuration states as
            # `none` is named in that report. Derived from the surface's own
            # `# absent_reason` marker rather than listed, so a facet that grows
            # an absent case is covered here the moment it is declared -- and
            # the arm that reports it is held by something. Found by review on
            # this change: the facet's own branch could be deleted whole and
            # every assertion in this file still passed, which is the shape the
            # retired required-key table is remembered for.
            for facet in sorted(config.facts.get("absent_reason", {})):
                if config.get(f"{facet}.carrier") != "none":
                    continue
                # ⚠️ The facet's own name rather than its dotted path, because
                # that is what the report names: `unavailable()` writes "No
                # due_date is carried" for a § 4 facet and the dotted key for
                # one that has a key of its own. Asserting the path would have
                # been an assertion about this test's spelling.
                named = facet.rpartition(".")[2]
                check(
                    f"and names `{named}` among them, its carrier being none",
                    any(named in line for line in reported),
                    f"reported {reported!r}",
                )
            # ⛔ The absences that are a stated *empty list* rather than a
            # carrier, each held the same way and for the same reason: this
            # repository writes every one of them, so each branch runs in this
            # suite and nothing read its output. Found by review on the § 19
            # change, where that facet's report line could be deleted whole with
            # every assertion here still green.
            for path, stated in (
                ("host.checks", "the host runs no checks"),
                ("checks_local", "no local check is stated"),
                ("spend_guard.deny", "no command is denied as a spend"),
                ("live_guard.session_tools", "no command opens a session elsewhere"),
                ("context_guard.unbounded", "no command's output is unbounded"),
                ("context_guard.result_limit_chars", "no result is replaced"),
            ):
                if config.get(path):
                    continue
                check(
                    f"and names `{path}` among them, the project stating it empty",
                    any(path in line for line in reported),
                    f"reported {reported!r}",
                )
            # § 25's arms, which only a project running the memory third reaches
            # -- this one does, so they are held here rather than over the
            # examples. ⛔ Asserted on what each arm names and not on a count:
            # this project takes the `derived` carrier, so both the unclosed
            # halves and the refusal from a tree have to be in the report, and a
            # suite counting lines would pass with either of them deleted.
            if MEMORY_THIRD in (config.get("session.parts") or []):
                for named, stated in (
                    ("memory.carrier", config.get("memory.carrier") == "derived"),
                    (
                        "memory.write_from",
                        config.get("memory.write_from") == "main_tree",
                    ),
                ):
                    if not stated:
                        continue
                    check(
                        f"and names `{named}` among them, this project stating it",
                        any(named in line for line in reported),
                        f"reported {reported!r}",
                    )
            # ⛔ The § 25 arm no shipped configuration reaches, asserted in both
            # directions over one key. Every example running the memory third
            # cuts a tree per item, so the line about `write_from` deciding
            # nothing would otherwise be a branch nothing can fail -- and the
            # negative is asserted with it, or the arm would pass by printing
            # that line always.
            inert = _refused_or_reported(_an_in_place_memory_project())
            check(
                "a project that cuts no tree is told `write_from` decides nothing",
                any("decides nothing" in line for line in inert),
                f"reported {inert!r}",
            )
            check(
                "and a project that cuts one is not told that",
                not any("decides nothing" in line for line in reported),
                f"reported {reported!r}",
            )
            # The resolved identity, which is the only guard § 1 has against a
            # role run from a sibling project: the reader says which root it
            # resolved and which file it read, both absolute, for the role to
            # name before it acts.
            resolved = config.to_dict()
            check(
                "a resolution reports the skills root it resolved, absolutely",
                resolved.get("skills_root") == os.path.abspath(REPO_ROOT),
                f"reported {resolved.get('skills_root')!r}",
            )
            check(
                "a resolution reports the configuration file it read, absolutely",
                resolved.get("config_path") == os.path.abspath(own),
                f"reported {resolved.get('config_path')!r}",
            )
            # And which surface ruled, now that two copies can answer. ⚠️ This
            # root is the primary checkout the plugin is installed from, so the
            # two answers coincide here -- what the assertion holds is that the
            # resolution states one at all, the arms above holding that it
            # resolves the right one where they differ.
            check(
                "a resolution reports the surface it was held to, absolutely",
                resolved.get("surface_path") == os.path.abspath(surface_for(REPO_ROOT)),
                f"reported {resolved.get('surface_path')!r}",
            )
        except ConfigError as error:
            failures += 1
            print(f"  FAIL  this repository's own {CONFIG_PATH}: {error}")

    if failures:
        print(f"\n{failures} assertion(s) did not hold.")
    return 1 if failures else 0


def facts_for(path: str) -> list[str]:
    with open(SURFACE, encoding="utf-8") as handle:
        return surface_facts(handle.read())["enums"].get(path, [])


def _load_bearing_absences(config: Config) -> list[str]:
    """Keys whose absence stops a role this project maps a carrier for."""
    carriers = config.get("carriers") or {}
    absent = []
    if carriers.get("day_log") and config.get("day_log.script") is None:
        absent.append("day_log.script")
    return absent


def _default_applied(path: str):
    """Resolve an example with `path` removed, and return what the reader gave."""
    data = _a_valid_example()
    node, parts = data, path.split(".")
    for part in parts[:-1]:
        node = node.get(part, {})
    node.pop(parts[-1], None)
    with open(SURFACE, encoding="utf-8") as handle:
        facts = surface_facts(handle.read())
    return _resolve(data, EXAMPLES, facts, False).get(path)


def _surface_without_marker(text: str, path: str) -> tuple[str, bool]:
    """The surface with one key's `# required` marker struck, and whether it was.

    ⛔ Both halves are returned because a plant that does not land reports green.
    The strike is matched on the key's own declaration line -- the leaf, at the
    head of a line, carrying the marker -- so a rename on the surface makes the
    arm that uses this fail rather than pass on an unmodified copy.
    """
    leaf = path.rpartition(".")[2]
    out, landed = [], False
    for line in text.splitlines(keepends=True):
        if not landed and re.match(rf"^\s*{re.escape(leaf)}:", line) and "required" in line:
            line = line.replace("required", "stated by the project", 1)
            landed = True
        out.append(line)
    return "".join(out), landed


def _planted_violations():
    """(label, the key the refusal must name, how to break a valid example).

    One per branch of `validate` that does real work. A branch with no plant is
    a branch nothing asserts can fail.
    """

    def at(path: str, value):
        def mutate(data: dict) -> dict:
            node, parts = data, path.split(".")
            for part in parts[:-1]:
                node = node.setdefault(part, {})
            node[parts[-1]] = value
            return data

        return mutate

    return [
        ("a value outside an alternation", "tracker.kind", at("tracker.kind", "gitlab")),
        ("a carrier outside its alternation", "work_item.type.carrier",
         at("work_item.type.carrier", "telepathy")),
        # § 6's per-role block, one plant per arm. ⛔ The scalar arm is the
        # withdrawn tolerance: a configuration written the way the first form of
        # that ruling told projects to write it has to stop loading, or the two
        # shapes coexist and one role goes on being wrong.
        ("a staging mode stated once for the whole project", "commit.staging",
         at("commit.staging", "sometimes")),
        # ⚠️ The out-of-alternation case is the generic enum rule's and is
        # planted there; what this arm answers is the *empty* value, which that
        # rule reads as absent and skips.
        ("a staging mode written empty", "commit.staging.finish",
         at("commit.staging.finish", None)),
        ("a staging entry for a role that does not commit", "commit.staging.day_log",
         at("commit.staging.day_log", "all")),
        # ⛔ Planted by unmapping a role the surface *does* state commits, not by
        # inventing one: a role outside that set is refused by the arm above, so
        # a plant written that way asserts the wrong arm and leaves this one
        # unasserted. Measured on this change, by review.
        ("a staging entry for a role `carriers` does not map", "commit.staging.review",
         lambda data: _without(data, "carriers.review")),
        ("a staging mode outside its alternation, held by the alternation rule",
         "commit.staging.finish", at("commit.staging.finish", "sometimes")),
        ("a staging entry keyed by something that is not a role", "commit.staging",
         _a_staging_entry_keyed_by_a_number),
        ("a staging entry for a commit the bookkeeping role never makes",
         "commit.staging.session",
         at("session.parts", ["tracker"])),
        ("a committing role mapped with no staging stated", "commit.staging.finish",
         lambda data: _without(data, "commit.staging.finish")),
        # § 23's thirds, one plant per arm.
        ("a parts list that is not a list", "session.parts",
         at("session.parts", "commit")),
        ("a third outside the vocabulary", "session.parts",
         at("session.parts", ["tracker", "telepathy"])),
        ("a third stated twice", "session.parts",
         at("session.parts", ["commit", "commit"])),
        ("a bookkeeping role mapped to run no third", "session.parts",
         at("session.parts", [])),
        # ⚠️ Its staging entry goes with the carrier, or § 6's unmapped-role arm
        # above refuses first and this arm is asserted by nothing.
        ("thirds stated while no bookkeeping role is mapped", "session.parts",
         lambda data: _without(
             _without(data, "carriers.session"), "commit.staging.session"
         )),
        # § 25's block, one plant per arm, and ⛔ both directions of the agreement
        # rather than one: a store configured for a third nothing runs and a third
        # running with `none` fail in opposite directions, and the first of them
        # reads from the configuration like a store being kept current.
        #
        # ⚠️ The commit third stays in this list, or § 6's own arm above refuses
        # first and this plant is asserted by nothing.
        ("a memory store stated for a third nothing runs", f"{MEMORY_KEY}.carrier",
         at("session.parts", ["tracker", "commit"])),
        ("the memory third running with no store carried", f"{MEMORY_KEY}.carrier",
         lambda data: at(f"{MEMORY_KEY}.absent_reason", "a planted reason")(
             at(f"{MEMORY_KEY}.carrier", "none")(
                 _without(_without(data, f"{MEMORY_KEY}.store"),
                          f"{MEMORY_KEY}.index")
             )
         )),
        # ⛔ The pinned keys under the carrier that resolves nothing inside the
        # store, one plant each: the second is reached only with the first key
        # gone, the loop refusing on whichever it meets first.
        ("a store pinned beside the carrier that composes no path",
         f"{MEMORY_KEY}.store", at(f"{MEMORY_KEY}.carrier", "derived")),
        ("an index named beside the carrier that composes no path",
         f"{MEMORY_KEY}.index",
         lambda data: at(f"{MEMORY_KEY}.carrier", "derived")(
             _without(data, f"{MEMORY_KEY}.store")
         )),
        # ⛔ The pairing of two individually legal values that is the hazard
        # written as a permission, which no single-key rule reaches.
        ("a derived store a save may write from any tree",
         f"{MEMORY_KEY}.write_from",
         lambda data: at(f"{MEMORY_KEY}.write_from", "any_tree")(
             at(f"{MEMORY_KEY}.carrier", "derived")(
                 _without(_without(data, f"{MEMORY_KEY}.store"),
                          f"{MEMORY_KEY}.index")
             )
         )),
        # ⛔ The other entry of the refused-keys table, and the key that is unique
        # to it: a project that keeps no memory stating which tree may write it
        # has written a policy for a third that does not run.
        ("a tree stated beside the carrier that writes nothing",
         f"{MEMORY_KEY}.write_from",
         lambda data: at(f"{MEMORY_KEY}.absent_reason", "a planted reason")(
             at(f"{MEMORY_KEY}.carrier", "none")(
                 at("session.parts", ["tracker", "commit"])(
                     _without(_without(data, f"{MEMORY_KEY}.store"),
                              f"{MEMORY_KEY}.index")
                 )
             )
         )),
        # ⛔ Both ways an index reaches outside the store it is supposed to sit in.
        ("an index climbing out of the store", f"{MEMORY_KEY}.index",
         at(f"{MEMORY_KEY}.index", "../elsewhere/index.md")),
        ("an index named absolutely", f"{MEMORY_KEY}.index",
         at(f"{MEMORY_KEY}.index", "/somewhere/else/index.md")),
        ("a memory carrier outside its alternation", f"{MEMORY_KEY}.carrier",
         at(f"{MEMORY_KEY}.carrier", "telepathy")),
        ("a write-from outside its alternation", f"{MEMORY_KEY}.write_from",
         at(f"{MEMORY_KEY}.write_from", "whichever_tree")),
        ("a unit outside its alternation", "work_item.estimate.unit",
         at("work_item.estimate.unit", "furlongs")),
        ("a rounding tie outside its alternation", "day_log.round_ties",
         at("day_log.round_ties", "sideways")),
        ("a sections mode outside its alternation", "day_log.sections",
         at("day_log.sections", "everything")),
        ("a required key present but empty", "host.repo", at("host.repo", None)),
        ("an inherited set that is not a list", "environment.inherits",
         at("environment.inherits", "GH_TOKEN")),
        # ⚠️ The stand-in is worded so the boundary carrier's own outward check
        # reads it as a placeholder rather than as a value: a plant that reddens
        # the scan § 6 runs over a diff is a plant somebody has to wave through
        # on every commit. What this asserts is the name *shape*, and any string
        # carrying an `=` fails that whatever follows it.
        ("an inherited entry that is not a variable name", "environment.inherits[0]",
         at("environment.inherits", ["GH_TOKEN=value-goes-here"])),
        ("an inherited entry that is not a string at all", "environment.inherits[0]",
         at("environment.inherits", [1])),
        ("a statuses list that is not a list", "statuses", at("statuses", "open")),
        ("a status entry that is not a block", "statuses[0]", at("statuses", ["open"])),
        ("a status with no name", "statuses[0].name",
         at("statuses", [{"role": "initial", "writer": "procedure"}])),
        ("a status role outside the vocabulary", "statuses[0].role",
         at("statuses", [{"name": "x", "role": "sideways", "writer": "procedure"}])),
        ("a status writer outside the vocabulary", "statuses[0].writer",
         at("statuses", [{"name": "x", "role": "initial", "writer": "the cat"}])),
        ("a readiness list that is not a list", "readiness", at("readiness", "all")),
        ("a readiness entry that is not a block", "readiness[0]", at("readiness", ["x"])),
        ("a readiness entry with no check", "readiness[0].check",
         at("readiness", [{"stop": "…"}])),
        ("a check outside the library", "readiness[0].check",
         at("readiness", [{"check": "vibes", "stop": "…"}])),
        ("an on_fail outside its alternation", "readiness[0].on_fail",
         at("readiness", [{"check": "state_is", "on_fail": "shout", "stop": "…"}])),
        ("a done list that is not a list", "done", at("done", "green")),
        ("a done entry that is not a block", "done[0]", at("done", ["merged"])),
        ("a done entry with no check", "done[0].check",
         at("done", [{"answered_by": "procedure", "stop": "…"}])),
        ("a done check outside the library", "done[0].check",
         at("done", [{"check": "vibes", "answered_by": "procedure", "stop": "…"}])),
        ("a done check with no answerer", "done[0].answered_by",
         at("done", [{"check": "merged", "stop": "…"}])),
        ("an answerer outside its alternation", "done[0].answered_by",
         at("done", [{"check": "merged", "answered_by": "the cat", "stop": "…"}])),
        ("a done check with no stop message", "done[0].stop",
         at("done", [{"check": "merged", "answered_by": "procedure"}])),
        ("a machine-answerable check handed to a person", "done[0].answered_by",
         at("done", [{"check": "local", "answered_by": "human", "stop": "…"}])),
        ("a person's check answered by the procedure", "done[0].answered_by",
         at("done", [{"check": "human_verification", "answered_by": "procedure",
                      "stop": "…"}])),
        ("a machine reading handed to a person", "done[0].answered_by",
         at("done", [{"check": "gate_green", "answered_by": "human", "stop": "…"}])),
        ("the merge itself handed to a person", "done[0].answered_by",
         at("done", [{"check": "merged", "answered_by": "human", "stop": "…"}])),
        # The retired key is planted by the arm that reads `RETIRED`, which places
        # it on the first entry; what is planted here is the shape that arm cannot
        # reach — the key written with nothing after it. ⛔ Presence and never
        # truthiness, which is the reader's rule for every key whose absence is
        # itself an answer: a blank `run:` is the same text as one somebody meant
        # to fill in, and a retirement read on the value would let it through.
        ("a retired command written with nothing after it", "done[0].run",
         at("done", [{"check": "merged", "run": None, "answered_by": "procedure",
                      "stop": "…"}])),
        # § 2's runner statement. ⚠️ Every one of these fails in the permissive
        # direction: each leaves a reader reporting a runner as configured while
        # the fact a generated job needs is one the project never stated.
        ("a runner block that is not a block", "host.runner",
         at("host.runner", "a-runner-label")),
        ("a runner stating no label", "host.runner.label", _a_runner_of(label=None)),
        ("a runner label that is not a label at all", "host.runner.label",
         _a_runner_of(label=["a-runner-label"])),
        ("a runner label written blank", "host.runner.label", _a_runner_of(label="   ")),
        ("a runner stating no capacity", "host.runner.concurrent_jobs",
         _a_runner_of(concurrent_jobs=None)),
        ("a capacity of zero, which runs nothing", "host.runner.concurrent_jobs",
         _a_runner_of(concurrent_jobs=0)),
        ("a capacity written as a flag, which reads as a single runner",
         "host.runner.concurrent_jobs", _a_runner_of(concurrent_jobs=True)),
        ("a runner stating no budget", "host.runner.budget_minutes",
         _a_runner_of(budget_minutes=None)),
        ("a budget of zero, which cancels before the job starts",
         "host.runner.budget_minutes", _a_runner_of(budget_minutes=0)),
        ("a budget that is not a whole number of minutes", "host.runner.budget_minutes",
         _a_runner_of(budget_minutes=1.5)),
        ("a supersession group written blank, which reads as the absence",
         "host.runner.supersedes", _a_runner_of(supersedes="   ")),
        ("a supersession group that is no group at all", "host.runner.supersedes",
         _a_runner_of(supersedes=7)),
        # § 2's title form. ⚠️ The first three fail in the direction that reads as
        # a stated form and renders or matches nothing; the `repeated` and `into`
        # plants are the permissive ones — each leaves a reader reporting a form
        # as configured while the gate written from it refuses titles the
        # finishing role legitimately writes, or fires on no pull request at all.
        ("a title form that is not a block", "host.pull_request_title",
         at("host.pull_request_title", "a-reference-form")),
        ("a title form stating no reference", "host.pull_request_title.reference",
         _a_title_form_of(reference=None)),
        ("a reference written blank", "host.pull_request_title.reference",
         _a_title_form_of(reference="   ")),
        ("a reference that is no reference at all", "host.pull_request_title.reference",
         _a_title_form_of(reference=["[A-KEY-<number>]"])),
        ("a reference with no place for the identifier",
         "host.pull_request_title.reference", _a_title_form_of(reference="[A-KEY]")),
        ("a reference with two places for one identifier",
         "host.pull_request_title.reference",
         _a_title_form_of(reference=f"[A-KEY-{PLACEHOLDER}/{PLACEHOLDER}]")),
        ("a title form stating nothing about repetition",
         "host.pull_request_title.repeated", _a_title_form_of(repeated=None)),
        ("repetition written as a word, which reads as true whatever it says",
         "host.pull_request_title.repeated", _a_title_form_of(repeated="no")),
        ("a title form stating no base refs", "host.pull_request_title.into",
         _a_title_form_of(into=None)),
        ("base refs written as one string rather than a list",
         "host.pull_request_title.into", _a_title_form_of(into=ANY_REF)),
        ("an empty base-ref list, which fires on no pull request",
         "host.pull_request_title.into", _a_title_form_of(into=[])),
        ("a base ref written blank, which matches nothing",
         "host.pull_request_title.into[0]", _a_title_form_of(into=["   "])),
        # § 10's entries. ⚠️ The `claimed_by` and `cap` plants are the two whose
        # refusal direction is the permissive one: each of them leaves a reader
        # reporting the resource as configured while no call ever claims it.
        ("an exclusive set that is not a list", "branch_model.exclusive_resources",
         at("branch_model.exclusive_resources", "the-local-stack")),
        ("an exclusive entry that is not a block", "branch_model.exclusive_resources[0]",
         at("branch_model.exclusive_resources", ["the-local-stack"])),
        ("an exclusive entry naming nothing", "branch_model.exclusive_resources[0].name",
         _a_resource_of(name=None)),
        ("an exclusive entry stating no cap", "branch_model.exclusive_resources[0].cap",
         _a_resource_of(cap=None)),
        ("a cap of zero, which nothing may ever hold",
         "branch_model.exclusive_resources[0].cap", _a_resource_of(cap=0)),
        ("a cap written as a flag, which reads as one",
         "branch_model.exclusive_resources[0].cap", _a_resource_of(cap=True)),
        ("a cap that is not a whole number", "branch_model.exclusive_resources[0].cap",
         _a_resource_of(cap=1.5)),
        ("an exclusive entry stating no subject",
         "branch_model.exclusive_resources[0].subject", _a_resource_of(subject=None)),
        ("a subject outside its alternation", "branch_model.exclusive_resources[0].subject",
         _a_resource_of(subject="session")),
        ("an exclusive entry stating what claims it nowhere",
         "branch_model.exclusive_resources[0].claimed_by", _a_resource_of(claimed_by=None)),
        ("a claim pattern that does not compile, so no call ever claims it",
         "branch_model.exclusive_resources[0].claimed_by",
         _a_resource_of(claimed_by="a-command-that-claims-it(")),
        ("an exclusive entry stating no lifetime", "branch_model.exclusive_resources[0].ttl",
         _a_resource_of(ttl=None)),
        ("a lifetime of zero, which expires before the call it covers starts",
         "branch_model.exclusive_resources[0].ttl", _a_resource_of(ttl=0)),
        ("a probe written blank, which reads as a command and prints no count",
         "branch_model.exclusive_resources[0].probe", _a_resource_of(probe="   ")),
        ("a probe that is no command at all", "branch_model.exclusive_resources[0].probe",
         _a_resource_of(probe=["a-command-that-counts-them"])),
        # ⚠️ Both of these refuse in the permissive direction, which is why each
        # has a plant of its own: a list written as one path exempts nothing and
        # an entry that names nothing exempts nothing, and in either case the
        # tree the key was written to protect is removed with the file in it.
        ("a regenerable set that is not a list", "branch_model.regenerable",
         at("branch_model.regenerable", "a-build-directory")),
        ("a regenerable entry that names no path", "branch_model.regenerable[0]",
         at("branch_model.regenerable", ["   "])),
        ("a regenerable entry that is not a path at all", "branch_model.regenerable[0]",
         at("branch_model.regenerable", [["a-build-directory"]])),
        ("a body-section list that is not a list", "body_sections",
         at("body_sections", "A section this project requires")),
        ("a body-section entry that is not a block", "body_sections[0]",
         at("body_sections", ["A section this project requires"])),
        ("a body section stating no heading", "body_sections[0].heading",
         _a_body_section_of(heading=None)),
        ("a body-section heading written blank", "body_sections[0].heading",
         _a_body_section_of(heading="   ")),
        ("a body-section heading that is no text at all", "body_sections[0].heading",
         _a_body_section_of(heading=["A section this project requires"])),
        ("a body section naming nothing that reads it", "body_sections[0].read_by",
         _a_body_section_of(read_by=None)),
        ("a body section whose reader is written blank", "body_sections[0].read_by",
         _a_body_section_of(read_by="  ")),
        ("a body section stating no answer for a change needing nothing",
         "body_sections[0].nothing_needed", _a_body_section_of(nothing_needed=None)),
        ("a nothing answer written blank, which no body can state",
         "body_sections[0].nothing_needed", _a_body_section_of(nothing_needed="  ")),
        ("two body-section entries under one heading", "body_sections[1].heading",
         _two_entries_under_one_heading),
        ("a local check list that is not a list", "checks_local",
         at("checks_local", "a-local-command")),
        ("a local check entry that is not a block", "checks_local[0]",
         at("checks_local", ["a-local-command"])),
        ("a local check stating no command", "checks_local[0].command",
         _a_local_check_of(command=None)),
        ("a local check whose command is blank", "checks_local[0].command",
         _a_local_check_of(command="   ")),
        ("several commands in one local check rather than several entries",
         "checks_local[0].command", _a_local_check_of(command=["a-command"])),
        ("a local check stating nothing about what a pass proves",
         "checks_local[0].proves", _a_local_check_of(proves=None)),
        ("an invalidation written with nothing after it",
         "checks_local[0].invalidate", _a_local_check_of(invalidate=None)),
        ("an invalidation that is no command at all",
         "checks_local[0].invalidate", _a_local_check_of(invalidate=["a-command"])),
        # ⚠️ Labelled apart from § 16's two plants of the same shape, which they
        # otherwise read as a repeat of: one list is declared there and cited
        # here, and a refusal that stopped happening on one of the two would be
        # invisible in a run whose lines are identical.
        ("a local check's preconditions written as one string rather than a list",
         "checks_local[0].requires",
         _a_local_check_of(requires="a-daemon-the-command-does-not-check")),
        ("a local check's precondition entry that names nothing",
         "checks_local[0].requires[1]",
         _a_local_check_of(requires=["a-daemon-the-command-does-not-check", "  "])),
        ("a counting condition written with nothing after it",
         "checks_local[0].counts_when", _a_local_check_of(counts_when=None)),
        ("a counting condition written as an empty list",
         "checks_local[0].counts_when", _a_local_check_of(counts_when=[])),
        ("a counting condition one of whose patterns is blank",
         "checks_local[0].counts_when",
         _a_local_check_of(counts_when=["pull_request -> *", "  "])),
        ("a condition whose type clause is empty",
         "checks_local[0].counts_when",
         _a_local_check_of(counts_when="pull_request() -> *")),
        ("a condition stating a blank type, at the other end of one form",
         "checks_local[0].counts_when[1]",
         _a_local_check_of(counts_when=["push -> main",
                                        "pull_request(edited, ) -> *"])),
        ("a local check the host already runs", "checks_local[0].command",
         _collides_with_a_mirrored_command),
        # § 18. ⚠️ The requiredness of the first is the surface's marker and is
        # asserted with every other marked key; what is planted here is the shape
        # each value has to have once it is written.
        ("an exemption list that is not a list", "already_run.never_guard",
         at("already_run.never_guard", "a-mirrored-command")),
        ("an exemption naming no command", "already_run.never_guard[0]",
         at("already_run.never_guard", ["  "])),
        ("an escape written as a value rather than a name", "already_run.escape",
         at("already_run.escape", "a reason somebody typed")),
        ("an escape written blank", "already_run.escape",
         at("already_run.escape", "")),
        ("an operational probe written blank", "already_run.operational_when",
         at("already_run.operational_when", "   ")),
        ("several commands in one `mirrors` rather than in its jobs",
         "host.checks[0].mirrors", _several_commands_in_one_mirrors),
        ("a mirrored command this reader cannot read", "host.checks[0].mirrors",
         _unreadable_mirrors),
        ("a host check list that is not a list", "host.checks",
         at("host.checks", "a-mirrored-command")),
        ("a host check entry that is not a block", "host.checks[0]",
         at("host.checks", ["a-mirrored-command"])),
        ("a collision with the command one job of a workflow mirrors",
         "checks_local[0].command", _collides_with_a_jobs_command),
        ("an entry mirroring both ways at once", "host.checks[0].jobs",
         _mirroring_both_ways),
        ("a job list that is not a list", "host.checks[0].jobs",
         _a_job_list_of("a-job")),
        ("a job list written blank", "host.checks[0].jobs", _a_job_list_of([])),
        ("a job entry that is not a block", "host.checks[0].jobs[0]",
         _a_job_list_of(["a-job"])),
        ("a job entry naming no job", "host.checks[0].jobs[0].job",
         _a_job_list_of([{"mirrors": "a-mirrored-command"}])),
        ("a job entry whose name is blank", "host.checks[0].jobs[0].job",
         _a_job_list_of([{"job": "  ", "mirrors": "a-mirrored-command"}])),
        ("a job entry mirroring nothing", "host.checks[0].jobs[0].mirrors",
         _a_job_list_of([{"job": "a-job"}])),
        ("a job's mirrored command this reader cannot read",
         "host.checks[0].jobs[0].mirrors",
         _a_job_list_of([{"job": "a-job", "mirrors": {"command": "a-command"}}])),
        ("a path filter written as one glob rather than a list",
         "host.checks[0].paths", _a_path_filter_of("a-tree/**")),
        ("a glob of a path filter written blank", "host.checks[0].paths[1]",
         _a_path_filter_of(["a-tree/**", "  "])),
        ("a path filter written as an empty list", "host.checks[0].paths",
         _a_path_filter_of([])),
        ("a path filter written with nothing after it", "host.checks[0].paths",
         _a_path_filter_of(None)),
        ("a job's path filter written as one glob", "host.checks[0].jobs[0].paths",
         _a_job_list_of([{"job": "a-job", "mirrors": "a-mirrored-command",
                          "paths": "a-tree/**"}])),
        ("a job's path filter written as an empty list",
         "host.checks[0].jobs[0].paths",
         _a_job_list_of([{"job": "a-job", "mirrors": "a-mirrored-command",
                          "paths": []}])),
        ("a trigger written with nothing after it", "host.checks[0].triggers",
         _a_trigger_of(None)),
        ("a trigger list written empty", "host.checks[0].triggers",
         _a_trigger_of([])),
        ("a trigger of a list written blank", "host.checks[0].triggers",
         _a_trigger_of(["pull_request -> main", "  "])),
        ("a type clause written empty", "host.checks[0].triggers",
         _a_trigger_of("pull_request() -> *")),
        ("a type clause written empty inside a list",
         "host.checks[0].triggers[1]",
         _a_trigger_of(["push -> main", "pull_request() -> *"])),
        ("a type written blank inside a clause", "host.checks[0].triggers",
         _a_trigger_of("pull_request(edited, ) -> *")),
        ("an entry naming no workflow", "host.checks[0].workflow",
         _an_entry_whose_workflow_is(None)),
        ("an entry whose workflow name is blank", "host.checks[0].workflow",
         _an_entry_whose_workflow_is("   ")),
        ("a mirrored command written with nothing after it",
         "host.checks[0].mirrors", _a_mirrors_of(None)),
        ("a `mirrors` written blank beside a job list", "host.checks[0].jobs",
         _mirroring_both_ways_one_blank),
        ("a carriers block that is not a block", "carriers", at("carriers", ["skill"])),
        ("a carrier outside the vocabulary", "carriers.day_log",
         at("carriers", {"day_log": "telepathy"})),
        ("a block written where keys belong", "day_log",
         at("day_log", "see tools/day_log.py")),
        ("a `file` carrier with no store", "context.artifacts.dir",
         at("context.artifacts.dir", None)),
        ("a `committed` flag that is not a boolean", "context.artifacts.committed",
         at("context.artifacts.committed", "definitely not")),
        ("an in-tree store a tree's teardown would take", "context.artifacts.dir",
         _in_tree_and_uncommitted),
        ("a prose width that is not a count of columns", "language.prose_width",
         at("language.prose_width", "wide")),
        ("a worktree model with nowhere to cut a tree", "branch_model.tree_dir",
         _cuts_trees_nowhere),
        ("a `command` ordering with no command", "ordering.command",
         at("ordering", {"carrier": "command"})),
        ("a field-carried date with no field named", "work_item.due_date.field",
         at("work_item.due_date", {"carrier": "field"})),
        # § 4.6's branches. ⚠️ Each writes the facet whole rather than editing one
        # key of the fixture's own, so what the plant states is what the refusal
        # has to be about: a carrier's keys differ per carrier, and a plant that
        # left another carrier's keys standing could pass on a rule it did not name.
        ("a priority axis whose values are not a list",
         "work_item.priority.values",
         _a_priority_carried_as("label", label_prefix="P: ", values="High",
                                writer="procedure")),
        ("a priority value that names no tier",
         "work_item.priority.values[1]",
         _a_priority_carried_as("label", label_prefix="P: ", values=["High", "  "],
                                writer="procedure")),
        ("a priority axis repeating a tier, so two ranks hold one value",
         "work_item.priority.values",
         _a_priority_carried_as("label", label_prefix="P: ", values=["High", "High"],
                                writer="procedure")),
        ("a label-carried priority with no prefix to tell the axis by",
         "work_item.priority.label_prefix",
         _a_priority_carried_as("label", values=["High"], writer="procedure")),
        ("a field-carried priority with no field named",
         "work_item.priority.field",
         _a_priority_carried_as("field", values=["High"], writer="procedure")),
        ("a carried priority with nobody stated to write it",
         "work_item.priority.writer",
         _a_priority_carried_as("label", label_prefix="P: ", values=["High"])),
        ("a priority writer outside § 4.2's vocabulary",
         "work_item.priority.writer",
         _a_priority_carried_as("label", label_prefix="P: ", values=["High"],
                                writer="whoever asks")),
        ("a gate reading a queue the facet does not carry",
         "work_item.priority.carrier", _gates_on_a_queue_with_no_priority),
        ("a judged set written as one tree rather than a list",
         "e2e_register.judged", _an_e2e_register_with(judged="a-judged-tree")),
        ("a judged entry that is not a tree at all",
         "e2e_register.judged[0]", _an_e2e_register_with(judged=[None])),
        ("a judged entry that is blank, and so matches every path",
         "e2e_register.judged[1]",
         _an_e2e_register_with(judged=["a-judged-tree", "   "])),
        ("a case glob of a shape that matches nothing",
         "e2e_register.cases", _an_e2e_register_with(cases=["*"])),
        ("a declaration that is no command at all",
         "executed.declares", _an_executed_with(declares=["a-command"])),
        ("a report command written blank",
         "executed.reports", _an_executed_with(reports="   ")),
        ("a floor above the one § 16 judges, which is a coverage threshold",
         "executed.min", _an_executed_with(min=40)),
        ("a floor written as a boolean, which compares equal to the floor",
         "executed.min", _an_executed_with(min=True)),
        ("preconditions written as one string rather than a list",
         "executed.requires",
         _an_executed_with(requires="a-store-the-run-creates")),
        ("a precondition entry that names nothing",
         "executed.requires[1]",
         _an_executed_with(requires=["a-store-the-run-creates", "  "])),
        ("a floor written as something merely equal to one",
         "executed.min", _an_executed_with(min=1.0)),
        ("a floor stated beside the carrier that judges nothing",
         "executed.min", _an_absent_executed_with(min=40)),
        ("a command stated beside the carrier that runs none",
         "executed.declares", _an_absent_executed_with(declares="a-command")),
        ("a precondition stated beside the carrier that names none",
         "executed.requires", _an_absent_executed_with(requires=["a-store"])),
        ("a type the branch-prefix map does not cover",
         "work_item.type_branch_prefix.epic", _a_type_with_no_prefix),
        ("a template keyed to a type the project cannot assign",
         "work_item.template.by_type.epic",
         at("work_item.template.by_type.epic", "epic.md")),
        # § 19's entries. ⚠️ Every one of these refusals is in the permissive
        # direction: each leaves a reader reporting the guard as configured while
        # the entry refuses no call at all.
        ("a deny list that is not a list", "spend_guard.deny",
         at("spend_guard.deny", "a-command-that-spends")),
        ("a deny entry that is not a block", "spend_guard.deny[0]",
         at("spend_guard.deny", ["a-command-that-spends"])),
        ("a deny entry naming no command", "spend_guard.deny[0].command",
         _a_denial_of(command=None)),
        ("a deny entry whose command is blank", "spend_guard.deny[0].command",
         _a_denial_of(command="   ")),
        ("several commands in one deny entry rather than several entries",
         "spend_guard.deny[0].command",
         _a_denial_of(command=["a-command-that-spends"])),
        ("a deny entry saying nothing about what the call costs",
         "spend_guard.deny[0].reason", _a_denial_of(reason=None)),
        ("a cost written blank, which a refusal would name as nothing",
         "spend_guard.deny[0].reason", _a_denial_of(reason="   ")),
        ("an argument pattern written blank, which matches every call of it",
         "spend_guard.deny[0].args_match", _a_denial_of(args_match="   ")),
        ("an argument pattern written with nothing after it",
         "spend_guard.deny[0].args_match", _a_denial_of(args_match=None)),
        ("an argument pattern that is no pattern at all",
         "spend_guard.deny[0].args_match",
         _a_denial_of(args_match=["--the-paid-tier"])),
        ("an argument pattern that does not compile, so no call ever matches it",
         "spend_guard.deny[0].args_match",
         _a_denial_of(args_match="--the-paid-tier(")),
        ("a resume bar written as a flag, which reads as a price",
         "spend_guard.resume_bar_usd", at("spend_guard.resume_bar_usd", True)),
        ("a resume bar that is no price at all", "spend_guard.resume_bar_usd",
         at("spend_guard.resume_bar_usd", "expensive")),
        ("a resume bar below nothing", "spend_guard.resume_bar_usd",
         at("spend_guard.resume_bar_usd", -1)),
        # § 21's entries, and every one of these refusals is permissive too: each
        # leaves a reader reporting the guard as configured while the entry holds
        # no call, or leaves the names it would clear with nowhere to live.
        ("a session-tool list that is not a list", "live_guard.session_tools",
         at("live_guard.session_tools", "a-command-that-opens-a-session")),
        ("a session-tool entry that is not a block", "live_guard.session_tools[0]",
         at("live_guard.session_tools", ["a-command-that-opens-a-session"])),
        ("a session-tool entry naming no command",
         "live_guard.session_tools[0].command", _a_session_tool_of(command=None)),
        ("a session-tool entry whose command is blank",
         "live_guard.session_tools[0].command", _a_session_tool_of(command="   ")),
        ("several commands in one session-tool entry rather than several entries",
         "live_guard.session_tools[0].command",
         _a_session_tool_of(command=["a-command-that-opens-a-session"])),
        ("a flag list that is not a list",
         "live_guard.session_tools[0].valued_flags",
         _a_session_tool_of(valued_flags="-a-flag")),
        ("a valued flag written without its dash, which matches no word of a call",
         "live_guard.session_tools[0].valued_flags[0]",
         _a_session_tool_of(valued_flags=["a-flag"])),
        ("a valued flag written as two words",
         "live_guard.session_tools[0].valued_flags[0]",
         _a_session_tool_of(valued_flags=["-a-flag a-value"])),
        ("a session command stated with no file for the names that clear it",
         "live_guard.allowlist", _a_session_tool_with_no_allowlist),
        ("a list of names that is not a list", "live_guard.local_names",
         at("live_guard.local_names", "a-local-name")),
        ("a local name written blank, which matches nothing",
         "live_guard.local_names", at("live_guard.local_names", ["   "])),
        # § 22's entries, permissive in the same direction: each leaves a reader
        # reporting the guard as configured while the entry bounds no call, or
        # leaves a replaced result with nowhere for its full text to go.
        ("an unbounded-call list that is not a list", "context_guard.unbounded",
         at("context_guard.unbounded", "a-command-whose-output-nothing-bounds")),
        ("an unbounded-call entry that is not a block", "context_guard.unbounded[0]",
         at("context_guard.unbounded", ["a-command-whose-output-nothing-bounds"])),
        ("an unbounded-call entry naming no command",
         "context_guard.unbounded[0].command", _an_unbounded_call_of(command=None)),
        ("an unbounded-call entry whose command is blank",
         "context_guard.unbounded[0].command", _an_unbounded_call_of(command="   ")),
        ("several commands in one unbounded-call entry rather than several entries",
         "context_guard.unbounded[0].command",
         _an_unbounded_call_of(command=["a-command-whose-output-nothing-bounds"])),
        ("an unbounded call stating no reason a refusal could name",
         "context_guard.unbounded[0].reason", _an_unbounded_call_of(reason=None)),
        ("an unbounded call whose reason is blank",
         "context_guard.unbounded[0].reason", _an_unbounded_call_of(reason="   ")),
        ("an unbounded call offering no route past the refusal",
         "context_guard.unbounded[0].bound", _an_unbounded_call_stating()),
        ("an unbounded call stating two answers to one call",
         "context_guard.unbounded[0].bound", _an_unbounded_call_stating("bound", "instead")),
        ("a bound that adds nothing to the arguments",
         "context_guard.unbounded[0].bound", _an_unbounded_call_of(bound="   ")),
        ("a bounded form that names nothing to run",
         "context_guard.unbounded[0].instead", _a_bounded_form_that_is_blank),
        ("an unbounded call whose narrowing pattern is blank",
         "context_guard.unbounded[0].args_match", _an_unbounded_call_of(args_match="   ")),
        ("an unbounded call whose narrowing pattern does not compile",
         "context_guard.unbounded[0].args_match",
         _an_unbounded_call_of(args_match="--a-whole-log(")),
        ("a never-bound list that is not a list", "context_guard.never_bound",
         at("context_guard.never_bound", "a-command-this-guard-never-bounds")),
        ("a never-bound entry that is not a block", "context_guard.never_bound[0]",
         at("context_guard.never_bound", ["a-command-this-guard-never-bounds"])),
        ("a never-bound entry naming no command", "context_guard.never_bound[0].command",
         at("context_guard.never_bound", [{"args_match": "a-pattern"}])),
        ("a never-bound command written blank, which matches no call",
         "context_guard.never_bound[0].command",
         at("context_guard.never_bound", [{"command": "   "}])),
        ("a never-bound entry whose narrowing pattern is blank, which exempts every call "
         "of that command", "context_guard.never_bound[0].args_match",
         at("context_guard.never_bound", [{"command": "an-interpreter", "args_match": "  "}])),
        ("a never-bound entry whose narrowing pattern does not compile",
         "context_guard.never_bound[0].args_match",
         at("context_guard.never_bound",
            [{"command": "an-interpreter", "args_match": "a-script("}])),
        ("a result limit written as a flag, which reads as one character",
         "context_guard.result_limit_chars", at("context_guard.result_limit_chars", True)),
        ("a result limit that is no length at all", "context_guard.result_limit_chars",
         at("context_guard.result_limit_chars", "long")),
        ("a result limit of nothing, which would replace every result",
         "context_guard.result_limit_chars", at("context_guard.result_limit_chars", 0)),
        ("a replaced result with nowhere for its full text to go",
         "context_guard.sidecar_dir", _a_replaced_result_with_no_sidecar),
    ]


def _an_e2e_register_with(**overrides):
    """§ 15's facet carried in full, with one key replaced.

    Written out rather than borrowed from whichever example states the facet,
    and that is not a literal this module could have read instead: the
    conditional markers refuse a *missing* sibling before any shape rule is
    reached, so a plant that broke one key of a borrowed block would redden on
    whatever else the borrowing left out and prove nothing about the branch it
    was written for. Each value here is a stand-in with no project in it.
    """

    def mutate(data: dict) -> dict:
        node = data.setdefault("e2e_register", {})
        node.clear()
        node.update(
            {
                "carrier": "file",
                "suite": "a-suite-root",
                "register": "a-suite-root/a-register.md",
                "heading": "A heading the table sits under",
                "exemptions": "A heading the written-down gaps sit under",
                "judged": ["a-judged-tree"],
            }
        )
        node.update(overrides)
        return data

    return mutate


def _an_executed_with(**overrides):
    """§ 16's facet carried, with one key replaced.

    Written out rather than borrowed from whichever example states the facet,
    for the reason stated one fixture up: the conditional markers refuse a
    *missing* `declares` or `reports` before any shape rule is reached, so a
    plant that broke one key of a borrowed block would redden on whatever the
    borrowing left out. ⚠️ `min` is deliberately absent from the base, since two
    of the plants above are about what a stated floor may be and a base carrying
    one would have each of them mutate a value rather than introduce it. ⛔ That
    leaves the **accepted** floor planted nowhere here, and what holds it is the
    arm that loads every example: the one carrying the facet in full states
    `min: 1`, so a refusal that caught the legitimate value would redden there.
    """

    def mutate(data: dict) -> dict:
        node = data.setdefault("executed", {})
        node.clear()
        node.update(
            {
                "carrier": "command",
                "declares": "a-command-printing-a-count",
                "reports": "a-command-printing-a-run",
            }
        )
        node.update(overrides)
        return data

    return mutate


def _an_absent_executed_with(**overrides):
    """§ 16's facet stated absent, with one key written beside the absence.

    The other half of the facet's shape rules: the block above is reached only
    under `carrier: command`, so these plants are what hold the arm that refuses
    a value beside a stated absence. ⛔ Without them the one value § 16 says a
    reader refuses rather than silently accepts loads clean on every project
    whose carrier is `none`.
    """

    def mutate(data: dict) -> dict:
        node = data.setdefault("executed", {})
        node.clear()
        node.update({"carrier": "none", "absent_reason": "a stated reason"})
        node.update(overrides)
        return data

    return mutate


def _a_staging_entry_keyed_by_a_number(data: dict) -> dict:
    """An entry whose key YAML reads as a number rather than a role's name.

    Written here rather than through the path helper, which writes every segment
    as a string: the defect is a key that is not a string, so a plant that wrote
    `"1"` would assert the wrong thing and stay green.
    """
    staging = data.setdefault("commit", {}).setdefault("staging", {})
    staging[1] = "all"
    return data


def _a_type_with_no_prefix(data: dict) -> dict:
    """A type added to `values` whose branch prefix nobody wrote.

    Added rather than subtracted on purpose: dropping an existing prefix would
    have the plant depend on which value the first example happens to carry,
    and this is the shape the rule is for -- a type gains a value and the map
    that is a function of it is not extended (§ 4.1).
    """
    node = data.setdefault("work_item", {}).setdefault("type", {})
    node["values"] = list(node.get("values") or []) + ["epic"]
    return data


def _a_priority_carried_as(carrier: str, **overrides) -> dict:
    """§ 4.6's facet rewritten whole, so a plant states every key it means to.

    Written as a replacement rather than as a key set on top of the example's
    own: the keys a carrier owes differ per carrier, so a plant that edited one
    key would leave the fixture carrying another carrier's keys and could pass
    for a reason this plant does not name.
    """

    def mutate(data: dict) -> dict:
        node = {"carrier": carrier}
        node.update(overrides)
        data.setdefault("work_item", {})["priority"] = node
        return data

    return mutate


def _gates_on_a_queue_with_no_priority(data: dict) -> dict:
    """§ 5's one check that reads another facet, configured where it is absent.

    The check is **added** to whatever gate the fixture carries rather than the
    gate being replaced, for the reason `_a_type_with_no_prefix` adds a value:
    the shape the rule is for is a project that configures the check and does
    not carry the facet, which is a gate growing an entry and not a gate
    rewritten.
    """
    data.setdefault("work_item", {})["priority"] = {
        "carrier": "none",
        "absent_reason": "nothing here ranks one item against another",
    }
    gate = data.get("readiness")
    data["readiness"] = (gate if isinstance(gate, list) else []) + [
        {"check": "queue_position", "ahead_allowed": 0, "stop": "Higher-ranked work is ahead."}
    ]
    return data


def _collides_with_a_mirrored_command(data: dict) -> dict:
    """§ 17's refusal, against whatever command the fixture's host already runs.

    The command is read out of the example rather than written here, for the
    reason the fixture itself is taken from the directory: a literal would be
    this reader's own code naming a project's command, and it would stop
    reaching this branch the moment the example was reworded.
    """
    checks = data.setdefault("host", {}).setdefault("checks", [])
    if not checks or not isinstance(checks[0], dict) or not checks[0].get("mirrors"):
        checks.insert(0, {"workflow": "Planted", "mirrors": "a-mirrored-command"})
    return _a_local_check_of(command=checks[0]["mirrors"])(data)


def _several_commands_in_one_mirrors(data: dict) -> dict:
    """The shape that was the tolerance before § 2 stated the second form.

    It read as a workflow mirroring two commands with neither a job nor a filter
    of its own, which is the second shape of the fact `jobs` now states once.
    Planted so the refusal is exercised: the configurations this tolerance
    accepted load against this reader and have to stop loading.
    """
    data.setdefault("host", {})["checks"] = [
        {"workflow": "Planted", "mirrors": ["the-first-command", "the-second-command"]}
    ]
    return data


def _four_jobs_behind_one_workflow() -> dict:
    """§ 2's second form written out: one workflow name, four mirrored commands.

    Written out rather than read from the example that illustrates the form, for
    the reason `_an_e2e_register_with` is: a plant that broke one key of a
    borrowed block would depend on how many jobs that example happens to carry,
    and the count is the whole of what this fixture asserts. ⚠️ The fourth job
    states no filter of its own, which is the arm an example with two jobs and
    two filters leaves asserted nowhere.
    """
    return {
        "workflow": "Planted",
        "triggers": ["pull_request -> *"],
        "jobs": [
            {"job": "a-first-job", "mirrors": "the-first-command",
             "paths": ["a-first-tree/**"]},
            {"job": "a-second-job", "mirrors": "the-second-command",
             "paths": ["a-second-tree/**"]},
            {"job": "a-third-job", "mirrors": "the-third-command",
             "paths": ["a-third-tree/**"]},
            {"job": "a-fourth-job", "mirrors": "the-fourth-command"},
        ],
    }


def _collides_with_a_jobs_command(data: dict) -> dict:
    """§ 17's refusal against a command one job of a workflow mirrors.

    The discrimination #33 and #39 could not make under the one-command entry,
    asserted where it is decidable: a local check colliding with the **third** of
    four commands behind one workflow name is refused exactly as one colliding
    with a workflow's only command is. ⚠️ What a hook does with that answer is
    its own item's; what is held here is that the answer is per command.
    """
    data.setdefault("host", {})["checks"] = [_four_jobs_behind_one_workflow()]
    return _a_local_check_of(command="the-third-command")(data)


def _a_body_section_of(**overrides):
    """§ 20's facet carried as one entry, with the stated keys replaced.

    Written out rather than borrowed from whichever example states the facet,
    for the reason `_a_local_check_of` below is. ⚠️ The base states all three
    keys, every one of them being required on every entry, so each plant here
    is about one key being absent, blank or of another shape.
    """

    def mutate(data: dict) -> dict:
        entry = {
            "heading": "A section this project requires",
            "read_by": "whatever collects it out of the change",
            "nothing_needed": "Nothing.",
        }
        entry.update(overrides)
        data["body_sections"] = [entry]
        return data

    return mutate


def _two_entries_under_one_heading(data: dict) -> dict:
    """§ 20's collision: one heading, two statements of what the section is for.

    ⛔ The two entries differ in `read_by`, so the refusal is about the heading
    rather than about a duplicated entry — a reader deduplicating whole entries
    would let this through, and the gate reading either one would be right.
    """
    data["body_sections"] = [
        {"heading": "A section this project requires",
         "read_by": "one reader", "nothing_needed": "Nothing."},
        {"heading": "a SECTION this project REQUIRES",
         "read_by": "another reader", "nothing_needed": "None."},
    ]
    return data


def _a_local_check_of(**overrides):
    """§ 17's facet carried as one entry, with the stated keys replaced.

    Written out rather than borrowed from whichever example states the facet, for
    the reason `_an_e2e_register_with` is: a plant that broke one key of a
    borrowed entry would redden on whatever else the borrowing left out and prove
    nothing about the branch it was written for. ⚠️ The base states `command` and
    `proves` and nothing else, since those two are the required pair and every
    other key's plants are about a value being written at all.

    ⛔ A key whose override is `None` is **written** with nothing after it rather
    than removed: the two are the same value once a mapping is parsed, and the
    blank form is the one a reader asking for truthiness lets through.
    """

    def mutate(data: dict) -> dict:
        entry = {
            "command": "a-local-command",
            "proves": "what a pass of it establishes",
        }
        entry.update(overrides)
        data["checks_local"] = [entry]
        return data

    return mutate


def _a_denial_of(**overrides):
    """§ 18's facet carried as one entry, with the stated keys replaced.

    Written out rather than borrowed from whichever example denies a command, for
    the reason `_a_resource_of` below is: an example states a project's own paid
    calls, and a plant that broke one key of a borrowed entry would redden on
    whichever other entry that project also wrote.

    ⛔ A key whose override is `None` is **written** with nothing after it rather
    than removed, the two being one value once a mapping is parsed -- and the
    blank form is the one a reader asking for truthiness lets through.
    """

    def mutate(data: dict) -> dict:
        entry = {
            "command": "a-command-that-spends",
            "reason": "what one call of it costs",
        }
        entry.update(overrides)
        data.setdefault("spend_guard", {})["deny"] = [entry]
        return data

    return mutate


def _a_session_tool_of(**overrides):
    """§ 21's facet carried as one entry, with the stated keys replaced.

    Written out rather than borrowed from whichever example names a session
    command, for the reason `_a_denial_of` above is: an example states a
    project's own commands, and a plant that broke one key of a borrowed entry
    would redden on whichever other entry that project also wrote.

    ⚠️ The `allowlist` beside it is written on every plant, because § 21 requires
    it wherever an entry exists: without it each of these would redden on the
    missing sibling instead of on the key it was written for -- the hazard the
    end-to-end fixture one facet over records.
    """

    def mutate(data: dict) -> dict:
        entry = {"command": "a-command-that-opens-a-session"}
        entry.update(overrides)
        node = data.setdefault("live_guard", {})
        node["session_tools"] = [entry]
        node.setdefault("allowlist", "/a-place-outside-every-tree/a-list-of-names")
        return data

    return mutate


def _a_session_tool_with_no_allowlist(data: dict) -> dict:
    """§ 21's facet carrying an entry and no file for the names that clear it.

    ⛔ The one plant of this facet the helper above cannot write, since that one
    supplies the sibling deliberately: what this breaks is the requirement
    itself, which has no key line of its own to mutate.
    """
    node = data.setdefault("live_guard", {})
    node["session_tools"] = [{"command": "a-command-that-opens-a-session"}]
    node.pop("allowlist", None)
    return data


def _an_unbounded_call_of(**overrides):
    """§ 22's facet carried as one entry, with the stated keys replaced.

    Written out rather than borrowed from whichever example names an unbounded
    command, for the reason `_a_session_tool_of` above is: an example states a
    project's own commands, and a plant that broke one key of a borrowed entry
    would redden on whichever other entry that project also wrote.

    ⚠️ The entry carries `bound` by default, so a plant that drops `command`,
    `reason` or `args_match` reddens on the key it was written for rather than on
    § 22's one-of-two rule -- and the plants for that rule state the pair
    themselves.
    """

    def mutate(data: dict) -> dict:
        entry = {
            "command": "a-command-whose-output-nothing-bounds",
            "bound": "--A-BOUNDING-FLAG 200",
            "reason": "what one call of it would put in the window",
        }
        entry.update(overrides)
        data.setdefault("context_guard", {})["unbounded"] = [entry]
        return data

    return mutate


def _an_unbounded_call_stating(*stated: str):
    """§ 22's facet carrying an entry that states neither route past it, or both.

    ⛔ The one rule the helper above cannot plant, since that one supplies
    `bound` deliberately: what this breaks is the exclusive pair, which has no
    single key line to mutate.
    """

    def mutate(data: dict) -> dict:
        entry = {
            "command": "a-command-whose-output-nothing-bounds",
            "reason": "what one call of it would put in the window",
        }
        for key in stated:
            entry[key] = (
                "--A-BOUNDING-FLAG 200" if key == "bound" else "a-bounded-form-to-run"
            )
        data.setdefault("context_guard", {})["unbounded"] = [entry]
        return data

    return mutate


def _a_bounded_form_that_is_blank(data: dict) -> dict:
    """§ 22's entry taking the `instead` route, with nothing written in it.

    ⛔ Written out rather than taken from `_an_unbounded_call_of`, which supplies
    `bound`: overriding that key to nothing leaves both stated, so the plant
    would redden on the exclusive pair and assert nothing about this key.
    """
    data.setdefault("context_guard", {})["unbounded"] = [{
        "command": "a-command-whose-output-nothing-bounds",
        "instead": "   ",
        "reason": "what one call of it would put in the window",
    }]
    return data


def _a_replaced_result_with_no_sidecar(data: dict) -> dict:
    """§ 22's limit stated with nowhere to write what a replacement replaces.

    ⛔ The requirement itself rather than a key's shape, which is why it is a
    mutation of its own: there is no `sidecar_dir` line to break where the whole
    defect is that none was written.
    """
    node = data.setdefault("context_guard", {})
    node["result_limit_chars"] = 20000
    node.pop("sidecar_dir", None)
    return data


def _a_resource_of(**overrides):
    """§ 10's facet carried as one entry, with the stated keys replaced.

    Written out rather than borrowed from whichever example carries a resource,
    for the reason `_a_local_check_of` is: an example states a project's two
    resources, and a plant that broke one key of a borrowed entry would redden on
    whichever other entry of that list the project also wrote.

    ⛔ A key whose override is `None` is **written** with nothing after it rather
    than removed, the two being one value once a mapping is parsed -- and the
    blank form is the one a reader asking for truthiness lets through.
    """

    def mutate(data: dict) -> dict:
        entry = {
            "name": "what is held",
            "cap": 1,
            "subject": "tree",
            "claimed_by": "a-command-that-claims-it",
            "probe": "a-command-that-counts-them",
            "ttl": 600,
        }
        entry.update(overrides)
        data.setdefault("branch_model", {})["exclusive_resources"] = [entry]
        return data

    return mutate


def _a_runner_of(**overrides):
    """§ 2's `host.runner` written whole, with the stated keys replaced.

    Written out rather than borrowed from whichever example states the block,
    for the reason `_a_resource_of` is: a plant that broke one key of a borrowed
    block would redden on whatever else that project's block left out and prove
    nothing about the branch it was written for.

    ⛔ A key whose override is `None` is **written** with nothing after it rather
    than removed, the two being one value once a mapping is parsed -- and the
    blank form is the one a reader asking for truthiness lets through.

    ⚠️ The green side of this block is asserted separately, by the examples and
    by the absent-case arm: a refusal widened until it rejected a legitimate
    runner statement would redden the load rather than passing quietly.
    """

    def mutate(data: dict) -> dict:
        block = {
            "label": "a-runner-label",
            "concurrent_jobs": 1,
            "budget_minutes": 30,
            "supersedes": "a-supersession-group",
        }
        block.update(overrides)
        data.setdefault("host", {})["runner"] = block
        return data

    return mutate


def _a_title_form_of(**overrides):
    """§ 2's `host.pull_request_title` written whole, with the stated keys replaced.

    Written out rather than borrowed from the example that states the block, for
    `_a_runner_of`'s reason: a plant breaking one key of a borrowed block reddens
    on whatever else that project left out and proves nothing about its branch.

    ⛔ A key whose override is `None` is **written** with nothing after it rather
    than removed, which is the form a reader asking for truthiness lets through.
    """

    def mutate(data: dict) -> dict:
        block = {
            "reference": f"[A-KEY-{PLACEHOLDER}]",
            "repeated": True,
            "into": [ANY_REF],
        }
        block.update(overrides)
        data.setdefault("host", {})["pull_request_title"] = block
        return data

    return mutate


def _mirroring_both_ways(data: dict) -> dict:
    """An entry stating a `mirrors` and a `jobs` list together."""
    checks = data.setdefault("host", {}).setdefault("checks", [])
    if not checks or not isinstance(checks[0], dict) or not checks[0].get("mirrors"):
        checks.insert(0, {"workflow": "Planted", "mirrors": "a-mirrored-command"})
    checks[0]["jobs"] = [{"job": "a-job", "mirrors": "a-second-command"}]
    return data


def _a_job_list_of(jobs):
    """An entry whose `jobs` is the stated value, and which mirrors nothing else.

    `mirrors` is cleared rather than left in place, so each of these reddens on
    the branch it was written for instead of on the exclusivity refusal above --
    which is the way a plant goes quietly wrong: it fails, the key it names is
    the one expected, and the branch it was meant to assert is never reached.
    """

    def mutate(data: dict) -> dict:
        checks = data.setdefault("host", {}).setdefault("checks", [])
        if not checks or not isinstance(checks[0], dict):
            checks.insert(0, {"workflow": "Planted"})
        checks[0].pop("mirrors", None)
        checks[0]["jobs"] = jobs
        return data

    return mutate


def _a_path_filter_of(paths):
    """An entry whose own `paths` is the stated value.

    ⚠️ `None` is a plant here and not a no-op: the key is written with nothing
    after it, which is a different shape from the key being absent, and the two
    are the same value once a mapping is parsed. A reader asking for the value
    rather than for the key reads the first as the second -- measured on this
    change, where the filter was held by its value and `paths:` passed blank.
    """

    def mutate(data: dict) -> dict:
        checks = data.setdefault("host", {}).setdefault("checks", [])
        if not checks or not isinstance(checks[0], dict):
            checks.insert(0, {"workflow": "Planted", "mirrors": "a-mirrored-command"})
        checks[0]["paths"] = paths
        return data

    return mutate


def _a_trigger_of(triggers):
    """An entry whose `triggers` is the stated value.

    ⚠️ The green side is asserted by every example and by this project's own
    configuration, which between them carry the single-string form, the list
    form and a pattern with a type clause -- so an arm widened until it refused
    a legitimate trigger reddens the load rather than passing quietly.

    ⛔ **One green shape none of them is in**, so it is asserted on its own: an
    entry stating no `triggers` at all. § 2 marks the key neither required nor
    defaulted, and a reader that refused the absence would refuse an adopter's
    first entry -- written before anybody tells them the key exists.
    """

    def mutate(data: dict) -> dict:
        checks = data.setdefault("host", {}).setdefault("checks", [])
        if not checks or not isinstance(checks[0], dict):
            checks.insert(0, {"workflow": "Planted", "mirrors": "a-mirrored-command"})
        checks[0]["triggers"] = triggers
        return data

    return mutate


def _an_entry_whose_workflow_is(name):
    """An entry whose `workflow` is the stated value, the key it is keyed on."""

    def mutate(data: dict) -> dict:
        checks = data.setdefault("host", {}).setdefault("checks", [])
        if not checks or not isinstance(checks[0], dict):
            checks.insert(0, {"mirrors": "a-mirrored-command"})
        checks[0]["workflow"] = name
        return data

    return mutate


def _a_mirrors_of(mirrors):
    """An entry whose `mirrors` is the stated value, its jobs left out."""

    def mutate(data: dict) -> dict:
        checks = data.setdefault("host", {}).setdefault("checks", [])
        if not checks or not isinstance(checks[0], dict):
            checks.insert(0, {"workflow": "Planted"})
        checks[0].pop("jobs", None)
        checks[0]["mirrors"] = mirrors
        return data

    return mutate


def _mirroring_both_ways_one_blank(data: dict) -> dict:
    """Both forms on one entry, with the `mirrors` written blank.

    The arm a value-read exclusivity rule lets through: blank, the key satisfies
    *states no command* and *states no jobs beside a command* at once, so the
    entry states both forms and is read as stating one.
    """
    checks = data.setdefault("host", {}).setdefault("checks", [])
    if not checks or not isinstance(checks[0], dict):
        checks.insert(0, {"workflow": "Planted"})
    checks[0]["mirrors"] = None
    checks[0]["jobs"] = [{"job": "a-job", "mirrors": "a-second-command"}]
    return data


def _unreadable_mirrors(data: dict) -> dict:
    """A `mirrors` that is no command at all, the list form having its own."""
    checks = data.setdefault("host", {}).setdefault("checks", [])
    if not checks or not isinstance(checks[0], dict):
        checks.insert(0, {"workflow": "Planted"})
    checks[0]["mirrors"] = {"command": "a-command"}
    return data


def _cuts_trees_nowhere(data: dict) -> dict:
    """§ 10's placement rule, which needs both keys to be wrong together.

    `kind` is set as well as `tree_dir` cleared, because the examples are not
    all `worktree` and a plant that only cleared the path would pass against
    whichever one the fixture happened to pick.
    """
    model = data.setdefault("branch_model", {})
    model["kind"] = "worktree"
    model["tree_dir"] = None
    return data


def _in_tree_and_uncommitted(data: dict) -> dict:
    """§ 11's in-tree rule, broken in the one way that needs three keys."""
    data.setdefault("context", {}).setdefault("artifacts", {}).update(
        {"carrier": "file", "dir": ".claude/artifacts", "committed": False}
    )
    data.setdefault("branch_model", {})["kind"] = "worktree"
    return data


def _an_in_place_memory_project() -> dict:
    """A project that runs the memory third and cuts no tree.

    ⛔ Built from two shipped examples rather than written here, and built at all
    because no single example is in this state: every one that runs the memory
    third cuts a tree per item, so § 25's *this key decides nothing* line would be
    a branch nothing could fail. ⚠️ Both halves are found by the value they carry
    rather than named, which is the rule `_a_valid_example` above follows.
    """
    pinned = _example_meeting(f"{MEMORY_KEY}.carrier", "path")
    in_place = _example_meeting("branch_model.kind", "in_place")
    if pinned is None or in_place is None:
        return {}
    return _with(dict(pinned), "branch_model", in_place["branch_model"])


def _refused_or_reported(data: dict) -> list[str]:
    """What `unavailable()` reports for `data`, or the one refusal it raised."""
    if not data:
        return ["no example carries the halves this fixture is built from"]
    with open(SURFACE, encoding="utf-8") as handle:
        facts = surface_facts(handle.read())
    try:
        return _resolve(data, EXAMPLES, facts, False).unavailable()
    except ConfigError as error:
        return [f"refused {error.key}"]


def _a_valid_example() -> dict:
    """Any complete example, to break in a stated way.

    Taken from the directory rather than named: a fixture that names one tracker
    is the toolkit's code naming a tracker, which is the thing the procedure
    does not do.
    """
    with open(_examples()[0], encoding="utf-8") as handle:
        return _load_yaml(handle.read(), CONFIG_PATH)


def _example_meeting(on: str, value) -> dict | None:
    """The first example whose `on` holds `value`, or None where none does.

    Found rather than named, for the reason `_a_valid_example` is: a fixture this
    code pointed at one tracker would be the toolkit naming a tracker, and a kind
    whose block no example illustrates has to fail rather than quietly borrow
    another kind's file.
    """
    for path in _examples():
        with open(path, encoding="utf-8") as handle:
            data = _load_yaml(handle.read(), CONFIG_PATH)
        if isinstance(data, dict) and _get(data, on) == value:
            return data
    return None


def _without(data: dict, path: str) -> dict:
    """The same configuration with one key removed, parents left as they are."""
    node, parts = data, path.split(".")
    for part in parts[:-1]:
        node = node.get(part)
        if not isinstance(node, dict):
            return data
    node.pop(parts[-1], None)
    return data


def _with(data: dict, path: str, value) -> dict:
    """The same configuration with one key written back into it."""
    node, parts = data, path.split(".")
    for part in parts[:-1]:
        node = node.setdefault(part, {})
    node[parts[-1]] = value
    return data


def _refused(data: dict, *, check_paths: bool = False, facts: dict | None = None) -> str | None:
    """The key a resolution refuses on, or None where it is accepted.

    `facts` is the surface to resolve against, for the one assertion that needs
    a surface other than this tree's: a refusal is the surface's only if it
    stops happening when the surface stops stating it.
    """
    if facts is None:
        with open(SURFACE, encoding="utf-8") as handle:
            facts = surface_facts(handle.read())
    try:
        _resolve(data, EXAMPLES, facts, check_paths)
    except ConfigError as error:
        return error.key
    return None


def _example_missing(path: str, _loaded) -> str | None:
    data = _a_valid_example()
    node, parts = data, path.split(".")
    for part in parts[:-1]:
        node = node.get(part, {})
    node.pop(parts[-1], None)
    return _refused(data)


def _example_without(path: str, _loaded) -> str | None:
    """Remove an `absent_reason` from a facet whose carrier is `none`."""
    facet = path.rsplit(".", 1)[0]
    data = _a_valid_example()
    node, parts = data, facet.split(".")
    for part in parts:
        node = node.setdefault(part, {})
    node["carrier"] = "none"
    node.pop("absent_reason", None)
    return _refused(data)


def _refuses_missing_code_root() -> str | None:
    data = _a_valid_example()
    data["roots"]["code"] = "a-directory-that-does-not-exist"
    return _refused(data, check_paths=True)


# § 1's named roots. ⛔ The fixtures below are the **shipped** collection rather
# than a shape written here: a hand-built one would be a form this repository
# ships nowhere, and what the arms are for is that the form an adopter copies is
# the form that is held. Found rather than named, for the reason
# `_a_valid_example` is -- a fixture this code pointed at one tracker would be
# the toolkit naming a tracker.
def _a_collection_example() -> dict | None:
    for path in _examples():
        with open(path, encoding="utf-8") as handle:
            data = _load_yaml(handle.read(), CONFIG_PATH)
        if isinstance(data, dict) and isinstance(_get(data, "roots.code"), dict):
            return data
    return None


def _collection_keys() -> list[str]:
    data = _a_collection_example()
    return list(_get(data, "roots.code") or {}) if data else []


def _collection_broken(mutate) -> str | None:
    """The key a collection with one plant in it refuses on."""
    data = _a_collection_example()
    mutate(_get(data, "roots.code"))
    return _refused(data)


def _a_collection_carrying(carrier: str, mapping: dict, **keys) -> dict:
    """The shipped collection with § 4.7's facet carried another way.

    ⛔ The one place a § 4.7 fixture is built rather than shipped, and the reason
    is the shipped collection can carry one carrier at a time: the two it does
    not carry are the two whose matching rules differ from it, so arms over the
    shipped file alone leave `_opens_with` and the one-value rule unexercised.
    ⚠️ The roots are the shipped collection's own, so the mapping is still held
    to the keys a project actually has.
    """
    data = _a_collection_example()
    facet = _get(data, "work_item.code_root")
    facet.clear()
    facet.update(carrier=carrier, roots=mapping, **keys)
    return data


def _resolved_or_refused(data: dict, values: list[str]) -> str:
    """`root <slug>` where § 4.7's resolution answers, `stop <key>` where it does not."""
    with open(SURFACE, encoding="utf-8") as handle:
        facts = surface_facts(handle.read())
    try:
        config = _resolve(data, EXAMPLES, facts, False)
    except ConfigError as error:
        return f"refused {error.key}"
    try:
        return f"root {config.root_for(values).root_key}"
    except ConfigError as error:
        return f"stop {error.key}"


def _project_read(configuration: Config, path: str) -> str | None:
    """The message a project-level read of a per-root fact is refused with.

    `None` where the read answered, which is what the complement arm asserts.
    `mirrors` names the accessor rather than a key: the two reach one refusal,
    the accessor asking for the key before it walks the facet.
    """
    try:
        if path == "mirrors":
            configuration.mirrors()
        else:
            configuration.get(path)
    except ConfigError as error:
        return str(error)
    return None


def _a_valid_example_with(path: str, value) -> dict:
    """A complete example with one key written back into it."""
    return _with(_a_valid_example(), path, value)


def _place(data: dict, path: str, value) -> str:
    """Write `value` at `path`, descending into the first entry of any list.

    Returns the path the configuration now carries it at, which is the dotted
    one with an index wherever a list was crossed. ⛔ The index is why this
    exists: a retired key declared inside a list member -- § 13's entries are
    list members -- cannot be written at the surface's own spelling of its path,
    and a plant that silently created a *dict* called `done` instead would
    redden on the shape rule rather than on the retirement it was written for.
    """
    node, parts, at = data, path.split("."), []
    for part in parts[:-1]:
        if isinstance(node, list):
            if not node:
                node.append({})
            at.append("[0]")
            node = node[0]
        node = node.setdefault(part, {})
        at.append(f".{part}" if at else part)
    if isinstance(node, list):
        if not node:
            node.append({})
        at.append("[0]")
        node = node[0]
    node[parts[-1]] = value
    at.append(f".{parts[-1]}" if at else parts[-1])
    return "".join(at)


def _refuses_a_root_with_no_config() -> tuple[str | None, bool]:
    """(the key the refusal names, whether it also names the root it looked in).

    The examples directory is a root with no configuration in it, so no
    temporary tree is needed to reach this branch.
    """
    root = EXAMPLES
    try:
        load(root)
    except ConfigError as error:
        return error.key, os.path.abspath(root) in str(error)
    return None, False


# --- entry point -----------------------------------------------------------


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Read a project's configuration, once, for every role.",
    )
    parser.add_argument(
        "--skills-root",
        default=".",
        help="the root the configuration is resolved relative to. Defaults to the "
        "working directory, which § 1 states is the skills root; pass it to "
        "address a project the role is not standing in",
    )
    parser.add_argument(
        "--no-check-paths",
        action="store_true",
        help="resolve without testing that the configured code root exists",
    )
    named = parser.add_mutually_exclusive_group()
    named.add_argument(
        "--root",
        help="the named code root to resolve, where § 1's collection carries "
        "several. Omitted, the whole configuration is reported and a fact "
        "stated per root is reported per root",
    )
    named.add_argument(
        "--root-for",
        nargs="+",
        metavar="VALUE",
        help="what the item carries on § 4.7's carrier -- every label on it, the "
        "named field's value, or its title -- resolved to the one root it "
        "names. A root named by none of them, or by two, is a stop",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="hold this reader to the surface and the examples",
    )
    args = parser.parse_args(argv)

    if args.self_test:
        print("Holding the reader to the surface and the examples:")
        return self_test()

    try:
        config = load(args.skills_root, check_paths=not args.no_check_paths)
        if args.root:
            config = config.root(args.root)
        elif args.root_for:
            config = config.root_for(args.root_for)
    except ConfigError as error:
        print(str(error), file=sys.stderr)
        return 1
    print(json.dumps(config.to_dict(), indent=2, ensure_ascii=False, sort_keys=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
