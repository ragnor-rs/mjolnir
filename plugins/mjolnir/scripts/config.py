#!/usr/bin/env python3
"""The configuration reader every role runs on.

A project states its facts once, in `.claude/mjolnir.yaml` relative to its
**skills root**, and the surface beside this script -- `../config/schema.md` --
is the single statement of what those facts are. This module is the one piece of
code that turns that file into values a role can act on: it resolves the path,
applies the surface's defaults, and refuses a configuration the surface does not
allow, naming the key so the person reading the failure knows what to write.

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

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - environment, not logic
    sys.exit(
        "config.py needs PyYAML to read a project's configuration.\n"
        "Install it with: python3 -m pip install pyyaml"
    )


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

    return {
        "defaults": defaults,
        "enums": enums,
        "required": required,
        "required_when": required_when,
        "absent_reason": absent_reason,
        "procedure": procedure,
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


def _load_yaml(text: str, where: str):
    """Parse YAML, turning a parser error into the refusal this module promises.

    A one-space indentation slip is the likeliest thing to go wrong in a
    hand-written configuration, and a traceback out of the parser names no key
    and tells the person reading it nothing they can act on.
    """
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


class Config:
    """A project's facts, resolved. Read through the accessors, not the dict."""

    def __init__(self, data: dict, skills_root: str, facts: dict, source: str | None = None):
        self.data = data
        self.skills_root = skills_root
        self.facts = facts
        # The file this came from, where it came from one. `None` for a
        # configuration handed over as text, which is the self-test loading the
        # examples -- reporting a path that was never opened would be the
        # plausible-looking wrong answer this whole section is about.
        self.source = source

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
    def code_root(self) -> str:
        return os.path.normpath(os.path.join(self.skills_root, self.get("roots.code")))

    @property
    def code_is_own_repo(self) -> bool:
        return bool(self.get("roots.code_is_own_repo"))

    @property
    def tracker_kind(self) -> str:
        return self.get("tracker.kind")

    @property
    def has_tracker(self) -> bool:
        return self.tracker_kind != "none"

    def get(self, path: str, default=None):
        return _get(self.data, path, default)

    def unavailable(self) -> list[str]:
        """What this configuration cannot support, and why.

        A role prints this rather than failing: every entry is a stated
        decision or a legitimate absence, never a broken install.
        """
        out = []
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
        if self.get("ordering.carrier") == "none":
            reason = self.get("ordering.absent_reason")
            out.append(
                "No ordering is carried (`ordering.carrier: none`), so a role "
                "invoked with no item asks for one by number rather than "
                f"choosing: {' '.join(str(reason).split())}"
            )
        if not self.get("host.checks"):
            out.append(
                "The host runs no checks, so every verdict is local and `done`'s "
                "`gate_green` reads `checks_local` for its source (§ 17). An "
                "empty check list reads as no answer, never as green."
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
        return {
            "skills_root": os.path.abspath(self.skills_root),
            "config_path": self.config_path,
            "code_root": os.path.abspath(self.code_root),
            "code_is_own_repo": self.code_is_own_repo,
            "config": self.data,
            "unavailable": self.unavailable(),
        }


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

    Read by no consumer in this tree and held to a shape anyway, for the reason
    § 13's `run` is: a single glob written as a string is the natural mistake,
    and it stringifies into something a comparison would walk character by
    character. ⚠️ Both levels go through here, so the entry's filter and a job's
    are held identically -- a shape rule that applied to one of them would be
    read as a statement about the other.

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


def _triggers(entry: dict, where: str) -> None:
    """§ 2's `triggers`, held to its shape and to its clause rules.

    Read by no consumer in this tree and held anyway, for the reason
    `_path_filter` is: the natural mistakes here are silent ones. ⚠️ The pattern
    itself is **not** held -- § 2 refuses no pattern on purpose -- so what this
    rejects is the key's shape and the two clause readings the surface does
    state: a clause written empty, and a type written blank inside one. Both are
    the same text as something somebody meant to write, which is why neither is
    read as the absence it looks like.
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
    for position, pattern in enumerate(patterns):
        parsed = parse_trigger(pattern)
        if parsed is None:
            continue
        _event, types, _ref = parsed
        if types is None:
            continue
        at = where if not isinstance(value, list) else f"{where}[{position}]"
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

    ⚠️ A shape this cannot read is refused rather than skipped -- the list, an
    entry, a `mirrors`, a `jobs` and a member of one alike. Skipping any of them
    would empty this map in silence, and a collision check with nothing in its
    map is a check that reports green. Measured on this function's first form,
    which refused an unreadable `mirrors` and then tolerated the two shapes one
    key up: a `host.checks` written as a string or a mapping, or an entry
    written as a bare command, each let every colliding `run` load clean.
    `host.checks` is required and non-empty-checked and has never been
    type-checked, so the shapes were harmless until something read the entries.
    """
    out: dict[str, str] = {}
    checks = _get(data, "host.checks")
    if not isinstance(checks, list):
        raise ConfigError(
            "host.checks",
            f"is {type(checks).__name__}, and § 2 states it as the host's runs -- "
            "a list of entries, or `[]` where every verdict is local. § 13's "
            "refusal reads them to find a done check the host already runs, and "
            "would hold nothing against a shape it cannot walk.",
        )
    for index, entry in enumerate(checks):
        if not isinstance(entry, dict):
            raise ConfigError(
                f"host.checks[{index}]",
                f"is {entry!r}, and has to be a mapping stating at least a "
                "`workflow` (§ 2). An entry this reader cannot walk takes "
                "whatever it mirrors out of § 13's refusal in silence.",
            )
        for command, mirrored_by in _entry_commands(entry, index):
            out.setdefault(_normalised_command(command), mirrored_by)
    return out


def _entry_commands(entry: dict, index: int):
    """Yield (command, the phrase naming where it is mirrored) for one entry.

    The two forms § 2 states, read in one place so that neither can grow a
    refusal the other does not have. An entry stating neither yields nothing.
    """
    where = f"host.checks[{index}]"
    workflow = entry.get("workflow")
    # The key the whole facet is keyed on, held here because an entry without
    # one has no key at all. It read as `unnamed` before: every entry missing a
    # workflow collapsed into one answer, and § 13's refusal then named a
    # workflow no file contains.
    if not isinstance(workflow, str) or not workflow.strip():
        raise ConfigError(
            f"{where}.workflow",
            f"is {workflow!r}; § 2 keys an entry by its workflow's name, so an "
            "entry stating none has no key. Every consumer reads this facet by "
            "that name, and a refusal naming a workflow nothing is called sends "
            "a reader to a file their repository does not have.",
        )
    _path_filter(entry, f"{where}.paths")
    # ⛔ The entry's and never a job's: § 2 puts the event block on the workflow,
    # so a `triggers` inside a `jobs` member is a key nothing states and nothing
    # would read.
    _triggers(entry, f"{where}.triggers")
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
        yield _command(entry["mirrors"], f"{where}.mirrors"), f"the `{workflow}` workflow"
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
        yield (
            _command(job["mirrors"], f"{at}.mirrors"),
            f"the `{name}` job of the `{workflow}` workflow",
        )


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

    statuses = _get(data, "statuses")
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

    readiness = _get(data, "readiness")
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

    # § 17. The verdicts no host run produces, and the one facet on this surface
    # whose entries carry a command the procedure runs for a verdict. Requiredness
    # is marked on the surface and answers whether the key is written; what each
    # value has to *be* is here, as § 16's is.
    mirrored = _mirrored_commands(data)
    local_checks = _get(data, "checks_local")
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

    # § 13. The same shape as `readiness` at the other end of the item, with one
    # thing that gate has no need of: who answers each check.
    done = _get(data, "done")
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

    carriers = _get(data, "carriers")
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


def load(skills_root: str = ".", *, check_paths: bool = True) -> Config:
    """Resolve a project's configuration relative to its skills root.

    `check_paths` tests that the configured `code` root exists. A role leaves it
    on: a fresh clone of an outer repository does not contain the inner one, and
    proceeding from there addresses the wrong repository having done something
    plausible first. The examples are shapes rather than projects, so the
    self-test below turns it off for them.
    """
    with open(SURFACE, encoding="utf-8") as handle:
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

    return _resolve(data, skills_root, facts, check_paths, os.path.abspath(path))


def load_text(text: str, skills_root: str, *, check_paths: bool = False) -> Config:
    """Resolve a configuration already in hand. Used to load the examples."""
    with open(SURFACE, encoding="utf-8") as handle:
        facts = surface_facts(handle.read())
    data = _load_yaml(text, CONFIG_PATH)
    if not isinstance(data, dict):
        raise ConfigError(CONFIG_PATH, "is empty or is not a block of keys.")
    return _resolve(data, skills_root, facts, check_paths)


def _resolve(
    data: dict,
    skills_root: str,
    facts: dict,
    check_paths: bool,
    source: str | None = None,
) -> Config:
    for path, value in facts["defaults"].items():
        _set_default(data, path, value)
    validate(data, facts)

    config = Config(data, skills_root, facts, source)
    if check_paths and not os.path.isdir(config.code_root):
        raise ConfigError(
            "roots.code",
            f"names {config.code_root!r}, which does not exist. A skill stops "
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
    "branch_model.exclusive_resources",
    "branch_model.kind",
    "branch_model.parallel_trees",
    "carriers",
    "checks_local",
    "commit.staging",
    "commit.trailer",
    "context.artifacts.carrier",
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
    "ordering.carrier",
    "readiness",
    "roots.code",
    "statuses",
    "tracker.kind",
    "work_item.due_date.carrier",
    "work_item.estimate.carrier",
    "work_item.template.carrier",
    "work_item.type.carrier",
]

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
    ("tracker.board", "tracker.kind", "trello"),
    ("tracker.project.number", "tracker.kind", "github-projects"),
    ("tracker.project.owner", "tracker.kind", "github-projects"),
    ("tracker.project_key", "tracker.kind", "jira"),
]

# The keys the surface marks procedure, stated here for the reason the lists
# above are: an assertion derived from the surface would assert whatever the
# surface happened to say. ⛔ This one carries the whole weight of the class,
# since the reader keeps no list of its own to compare against -- drop the clause
# from the surface and this is what reddens.
MARKED_PROCEDURE = ["audit_trail", "fail_open"]

MARKED_ABSENT_CAPABLE = [
    "context.artifacts",
    "e2e_register",
    "executed",
    "ordering",
    "work_item.due_date",
    "work_item.estimate",
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

    missing_root = _refuses_missing_code_root()
    check(
        "a `code` root that does not exist stops rather than proceeding",
        missing_root == "roots.code",
        f"reported {missing_root!r}",
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
        ("a staging mode outside its alternation", "commit.staging",
         at("commit.staging", "sometimes")),
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
        ("a local check the host already runs", "checks_local[0].command",
         _collides_with_a_mirrored_command),
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
    except ConfigError as error:
        print(str(error), file=sys.stderr)
        return 1
    print(json.dumps(config.to_dict(), indent=2, ensure_ascii=False, sort_keys=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
