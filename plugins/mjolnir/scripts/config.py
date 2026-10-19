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
    rule is written against: `local`, the check that carries a command, and
    `procedure`, the answerer a command is run by. Each is a member of a set the
    surface states, and which member a rule turns on is the part an alternation
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
`host.checks: []`, and a facet whose `carrier` is `none` with a stated
`absent_reason` all load silently and are not misconfigurations. An *unset* carrier is. `unavailable()` is how a role says what
it cannot do without any of those reading as a broken install.

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

# The markers that make the surface machine-readable, each read as one
# semicolon-separated clause of a key's trailing comment. Every clause of a
# comment is scanned, not just the last one, so a key that states prose and a
# marker together -- `# stated, never inherited; required` -- carries both.
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
# four `absent_reason` lines: `# required when carrier is none` is prose about a
# rule that another marker performs, and a grammar matching it would have turned
# every one of those into a condition on a sibling key no dotted path resolves.
# Measured -- it did, and every example stopped loading.
#
# ⛔ The condition is read, so it cannot be a condition nothing can meet: the
# referenced key must be one the surface declares, and the value one its
# alternation states where it states one. Both are refused below rather than
# skipped, because a marker whose condition never fires is a requirement nobody
# enforces that reads exactly like one somebody does.
REQUIRED_WHEN_CLAUSE = re.compile(
    r"^required_when\s*:\s*(?P<on>[A-Za-z_][\w.]*)\s*=\s*(?P<value>[\w-]+)$"
)

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
    declared: set[str] = set()

    for heading, block in _fences(surface_text):
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
    for (path, on, value), heading in sorted(required_when.items()):
        if on not in declared:
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
    }


def surface_keys(surface_text: str) -> set[str]:
    """Every dotted key path the surface's blocks declare.

    Used by the self-test to hold the retired keys to the surface: a key this
    reader refuses must not be one the surface still tells a project to write.
    """
    return {path for _, block in _fences(surface_text) for path, _ in _walk_keys(block)}


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
        if self.get("ordering.carrier") == "none":
            reason = self.get("ordering.absent_reason")
            out.append(
                "No ordering is carried (`ordering.carrier: none`), so a role "
                "invoked with no item asks for one by number rather than "
                f"choosing: {' '.join(str(reason).split())}"
            )
        if not self.get("host.checks"):
            out.append(
                "The host runs no checks, so every verdict is local. An empty "
                "check list reads as no answer, never as green."
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
RETIRED = [
    (
        "roots.skills",
        "the skills root is the directory the role was invoked in, which no "
        "configuration can state -- it is where this file is found. See § 1, "
        "`The skills root is where the role runs`. Delete the key",
    ),
]

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


def _mirrored_commands(data: dict) -> dict[str, str]:
    """Normalised command -> the workflow whose run mirrors it (§ 2).

    `mirrors` states one command per entry today, and a workflow that runs
    several has no form on the surface -- #58's gap. So § 13's refusal reads
    **whatever an entry mirrors** rather than comparing against a single string:
    a list is read as the commands it holds.

    ⚠️ That list is a *tolerance*, not a shape § 2 states, and it promises
    nothing about #58: that item's own acceptance names a per-command path
    filter, which is a list of mappings and is **refused** below rather than
    guessed at. Whoever lands #58 edits this function, and the refusal is what
    tells them so.

    ⚠️ A shape this cannot read is refused rather than skipped -- the list, an
    entry, and a `mirrors` alike. Skipping any of the three would empty this map
    in silence, and a collision check with nothing in its map is a check that
    reports green. Measured on this function's first form, which refused an
    unreadable `mirrors` and then tolerated the two shapes one key up: a
    `host.checks` written as a string or a mapping, or an entry written as a
    bare command, each let every colliding `run` load clean. `host.checks` is
    required and non-empty-checked and has never been type-checked, so the
    shapes were harmless until something read the entries.
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
        if entry.get("mirrors") is None:
            continue
        mirrors = entry["mirrors"]
        commands = mirrors if isinstance(mirrors, list) else [mirrors]
        for command in commands:
            if not isinstance(command, str):
                raise ConfigError(
                    f"host.checks[{index}].mirrors",
                    f"is {mirrors!r}, which is neither the local command § 2 "
                    "states nor a list of them. § 13's refusal reads this to "
                    "find a done check the host already runs, and would hold "
                    "nothing against a shape it cannot read.",
                )
            out.setdefault(_normalised_command(command), entry.get("workflow") or "unnamed")
    return out


def validate(data: dict, facts: dict) -> None:
    for path, where in RETIRED:
        if _has(data, path):
            raise ConfigError(path, f"is retired -- {where}.")

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

    # § 13. The same shape as `readiness` at the other end of the item, with two
    # things that gate has no need of: who answers each check, and a refusal for
    # a check whose command the host already runs.
    done = _get(data, "done")
    if not isinstance(done, list):
        raise ConfigError(
            "done", "must be a list; `[]` where the merge is the whole of it."
        )
    mirrored = _mirrored_commands(data)
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
        run = entry.get("run")
        # The other side of the collision comparison, and it has to be held to a
        # shape for the same reason `mirrors` is: `_normalised_command` stringifies
        # whatever it is given, so a `run` written as a list -- the natural way to
        # write a multi-word command -- becomes a key no mirrored command can ever
        # match, and the refusal below it holds nothing while looking like it holds.
        if run is not None and not isinstance(run, str):
            raise ConfigError(
                f"{where}.run",
                f"is {run!r}; § 13 states it as one command, written as a string. "
                "A value of another shape stringifies into something no "
                "`host.checks` entry can match, so the refusal of a check the host "
                "already runs would pass it in silence.",
            )
        if entry["check"] == "local":
            if not run:
                raise ConfigError(
                    f"{where}.run",
                    "required when the check is `local` (§ 13): there is nothing "
                    "to run, and the verdict would have to be reported from a "
                    "command that was never named.",
                )
            if entry["answered_by"] != "procedure":
                raise ConfigError(
                    f"{where}.answered_by",
                    f"is {entry['answered_by']!r} on a check carrying a command. "
                    "A command is the procedure's to run (§ 13), and a "
                    "machine-answerable check configured as a person's stops "
                    "every completion for a hand-over nobody needed. What a "
                    "command needs standing up before it can run at all is "
                    "#60's axis, not an answerer here.",
                )
        # Every check § 13 binds to an answerer, in both directions. The
        # `local` arm above is the same rule and stays where it is because it
        # needs the command in hand; these are the rest. ⛔ Both directions
        # matter and only one of them is obvious: a machine check handed to a
        # person is the check somebody turns off, and a person's check handed
        # to the procedure is answered by reasoning about it and reported
        # green, which is the failure § 13 exists for. `checklist_ticked` is
        # bound to neither, and § 13 says why.
        elif BOUND_ANSWERERS.get(entry["check"], entry["answered_by"]) != entry["answered_by"]:
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
        elif "run" in entry:
            # Presence rather than truthiness, which is the reader's own rule one
            # section up: a key written with nothing after it reads as absent and
            # is refused instead, so `run:` left dangling on a check that runs
            # none is as much a mistake as one carrying a command.
            raise ConfigError(
                f"{where}.run",
                f"is {run!r} on a `{entry['check']}` check, whose verdict comes "
                "from somewhere else (§ 13). A command nothing runs is a command "
                "that reads as covered.",
            )
        if run:
            collision = mirrored.get(_normalised_command(run))
            if collision:
                raise ConfigError(
                    f"{where}.run",
                    f"on the `{entry['check']}` check is {run!r}, which the "
                    f"`{collision}` workflow already mirrors (§ 2). A done check "
                    "colliding with a run the host owns asks a shared machine for "
                    "an answer it already has; a check no entry mirrors is the one "
                    "that must run locally.",
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
    "commit.staging",
    "commit.trailer",
    "context.artifacts.carrier",
    "done",
    "environment.inherits",
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
    "version",
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
MARKED_REQUIRED_WHEN = [
    ("tracker.board", "tracker.kind", "trello"),
    ("tracker.project.number", "tracker.kind", "github-projects"),
    ("tracker.project.owner", "tracker.kind", "github-projects"),
    ("tracker.project_key", "tracker.kind", "jira"),
]

MARKED_ABSENT_CAPABLE = [
    "context.artifacts",
    "ordering",
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

    # The surface's two marked sets, against the test's own statement of them.
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
        declared = surface_keys(handle.read())
    for path, _ in RETIRED:
        check(
            f"the surface declares no `{path}`",
            path not in declared,
            "the surface still states it, and this reader refuses it",
        )
        broken = _refused(_a_valid_example_with(path, "."))
        check(
            f"a configuration still declaring `{path}` is refused, with the key named",
            broken == path,
            f"reported {broken!r}",
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
        ("a local done check with no command", "done[0].run",
         at("done", [{"check": "local", "answered_by": "procedure", "stop": "…"}])),
        ("a machine-answerable check handed to a person", "done[0].answered_by",
         at("done", [{"check": "local", "run": "a-command", "answered_by": "human",
                      "stop": "…"}])),
        ("a person's check answered by the procedure", "done[0].answered_by",
         at("done", [{"check": "human_verification", "answered_by": "procedure",
                      "stop": "…"}])),
        ("a machine reading handed to a person", "done[0].answered_by",
         at("done", [{"check": "gate_green", "answered_by": "human", "stop": "…"}])),
        ("the merge itself handed to a person", "done[0].answered_by",
         at("done", [{"check": "merged", "answered_by": "human", "stop": "…"}])),
        ("a command on a check that runs none", "done[0].run",
         at("done", [{"check": "merged", "run": "a-command", "answered_by": "procedure",
                      "stop": "…"}])),
        ("a dangling command on a check that runs none", "done[0].run",
         at("done", [{"check": "merged", "run": None, "answered_by": "procedure",
                      "stop": "…"}])),
        ("a command that is not one command", "done[0].run",
         at("done", [{"check": "local", "run": ["a-command"], "answered_by": "procedure",
                      "stop": "…"}])),
        ("a done check the host already runs", "done[0].run",
         _collides_with_a_mirrored_command),
        ("a collision with the second command of a workflow that runs several", "done[0].run",
         _collides_with_a_workflows_second_command),
        ("a mirrored command this reader cannot read", "host.checks[0].mirrors",
         _unreadable_mirrors),
        ("a host check list that is not a list", "host.checks",
         at("host.checks", "a-mirrored-command")),
        ("a host check entry that is not a block", "host.checks[0]",
         at("host.checks", ["a-mirrored-command"])),
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
        ("a type the branch-prefix map does not cover",
         "work_item.type_branch_prefix.epic", _a_type_with_no_prefix),
        ("a template keyed to a type the project cannot assign",
         "work_item.template.by_type.epic",
         at("work_item.template.by_type.epic", "epic.md")),
    ]


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
    """§ 13's refusal, against whatever command the fixture's host already runs.

    The command is read out of the example rather than written here, for the
    reason the fixture itself is taken from the directory: a literal would be
    this reader's own code naming a project's command, and it would stop
    reaching this branch the moment the example was reworded.
    """
    checks = data.setdefault("host", {}).setdefault("checks", [])
    if not checks or not isinstance(checks[0], dict) or not checks[0].get("mirrors"):
        checks.insert(0, {"workflow": "Planted", "mirrors": "a-mirrored-command"})
    mirrors = checks[0]["mirrors"]
    command = mirrors[0] if isinstance(mirrors, list) else mirrors
    data["done"] = [
        {"check": "local", "run": command, "answered_by": "procedure", "stop": "…"}
    ]
    return data


def _collides_with_a_workflows_second_command(data: dict) -> dict:
    """The half of § 13's refusal that #58 is the open form of.

    A workflow running several commands has no form on the surface yet, so this
    plant writes the shape the refusal is read against rather than one an example
    carries: a check colliding with the **second** of them has to be refused the
    same way as one colliding with the first. Without this plant that clause is
    claimed by a comment and exercised by nothing.
    """
    data.setdefault("host", {})["checks"] = [
        {"workflow": "Planted", "mirrors": ["the-first-command", "the-second-command"]}
    ]
    data["done"] = [
        {
            "check": "local",
            "run": "the-second-command",
            "answered_by": "procedure",
            "stop": "…",
        }
    ]
    return data


def _unreadable_mirrors(data: dict) -> dict:
    """A `mirrors` that is neither a command nor a list of them."""
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


def _refused(data: dict, *, check_paths: bool = False) -> str | None:
    """The key a resolution refuses on, or None where it is accepted."""
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
