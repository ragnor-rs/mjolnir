#!/usr/bin/env python3
"""The configuration reader every role runs on.

A project states its facts once, in `.claude/mjolnir.yaml` relative to its
**skills root**, and the surface beside this script -- `../config/schema.md` --
is the single statement of what those facts are. This module is the one piece of
code that turns that file into values a role can act on: it resolves the path,
applies the surface's defaults, and refuses a configuration the surface does not
allow, naming the key so the person reading the failure knows what to write.

Three things it deliberately does not do:

  * **It carries no default and no vocabulary of its own.** Every default is read
    at run time from the `# default:` marker on a key's line in the surface's
    fenced blocks, and every closed set of values -- status roles, status
    writers, readiness checks, each `carrier` -- is read from the same blocks.
    A value restated here would be a second statement of one fact, which is the
    defect this toolkit exists to delete rather than a maintenance burden to
    absorb. Adding a status role to the surface therefore changes what this
    reader accepts without changing this reader.
  * **It infers no root.** `roots.code` is read, never derived from the working
    directory or from `git rev-parse` -- both would do something plausible first
    and be wrong wherever the two roots differ.
  * **It does not decide what a role then does.** It reports what a
    configuration cannot support; acting on that is the role's business.

**Absence is a configuration, not a gap.** `tracker.kind: none`, an empty
`statuses` list, an empty `readiness` list, `host.checks: []`, and a facet whose
`carrier` is `none` with a stated `absent_reason` all load silently and are not
misconfigurations. An *unset* carrier is. `unavailable()` is how a role says what
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

# Where a project's own configuration sits under its skills root. Stated once
# here because the surface states it in prose rather than as a key: a project
# does not get to move it, or a role would have to be told where to look.
CONFIG_PATH = os.path.join(".claude", "mjolnir.yaml")

# The marker that makes a default machine-readable, read as the last
# semicolon-separated clause of a key's trailing comment: `# default` means the
# value shown on the line is the default, and `# default: <value>` states one
# the line does not show -- which is how a key whose value is an alternation
# declares which arm of it applies. Matching the whole clause rather than the
# bare word keeps a comment that merely mentions a default from becoming one.
DEFAULT_CLAUSE = re.compile(r"^default(?:\s*:\s*(?P<literal>.+))?$")

# A fenced block of the surface, and a `key:` line inside one. List items are
# not matched on purpose -- a `- { ... }` line is an entry, not a key.
FENCE = re.compile(r"```yaml\n(.*?)```", re.S)
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
    return yaml.safe_load(text)


def _fences(surface_text: str) -> list[str]:
    return FENCE.findall(surface_text)


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

    for block in _fences(surface_text):
        for path, rest in _walk_keys(block):
            value, _, comment = rest.partition("#")

            clause = DEFAULT_CLAUSE.match(comment.strip().split(";")[-1].strip())
            if clause:
                shown = clause.group("literal")
                defaults[path] = _literal(shown if shown else value.strip())

            # A closed set, written either as the value or as a comment beside
            # it: `kind: github-projects | jira | trello | none` is the first
            # shape, `day_log: skill  # skill | command | hook` the second.
            for candidate in (value.strip(), comment.strip()):
                if ALTERNATION.match(candidate):
                    enums.setdefault(path, [v.strip() for v in candidate.split("|")])
                    break

    # A reader that derives nothing accepts anything, so an unreadable surface
    # is refused here rather than silently waved through.
    missing = [name for name, found in (("default", defaults), ("alternation", enums)) if not found]
    if missing:
        raise ConfigError(
            os.path.relpath(SURFACE, PLUGIN_ROOT),
            "states no " + " and no ".join(missing) + " this reader can read. "
            "Either the surface changed shape or its markers were dropped.",
        )

    return {"defaults": defaults, "enums": enums}


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


def _has(data, path: str) -> bool:
    sentinel = object()
    return _get(data, path, sentinel) is not sentinel


def _set_default(data: dict, path: str, value) -> None:
    parts = path.split(".")
    node = data
    for part in parts[:-1]:
        child = node.get(part)
        if not isinstance(child, dict):
            # A parent that is absent gets created so the default can land; a
            # parent that is present but not a mapping is the caller's error and
            # is reported by validation rather than silently overwritten here.
            if child is not None:
                return
            child = {}
            node[part] = child
        node = child
    node.setdefault(parts[-1], value)


class Config:
    """A project's facts, resolved. Read through the accessors, not the dict."""

    def __init__(self, data: dict, skills_root: str, facts: dict):
        self.data = data
        self.skills_root = skills_root
        self.facts = facts

    # -- the roots. Both are absolute, and neither is ever inferred.

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
                "No tracker is configured (`tracker.kind: none`), so every "
                "tracker operation is unavailable. Branching, the pull request, "
                "the review and the day log do not need one."
            )
        for facet in ("type", "estimate", "template"):
            if self.get(f"work_item.{facet}.carrier") == "none":
                reason = self.get(f"work_item.{facet}.absent_reason")
                out.append(f"No {facet} is carried: {' '.join(str(reason).split())}")
        if not self.get("statuses"):
            out.append(
                "No status is configured, so the procedure never asks the port "
                "to advance an item and reports no missing state as a fault."
            )
        if not self.get("readiness"):
            out.append("The readiness gate is empty, so there is nothing to gate.")
        if not self.get("host.checks"):
            out.append(
                "The host runs no checks, so every verdict is local. An empty "
                "check list reads as no answer, never as green."
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
            "code_root": os.path.abspath(self.code_root),
            "code_is_own_repo": self.code_is_own_repo,
            "config": self.data,
            "unavailable": self.unavailable(),
        }


# --- validation ------------------------------------------------------------
#
# Each rule names the section of the surface it enforces. The rules are
# procedure -- the surface's own boundary rule puts them in a skill rather than
# in the configuration -- but every *value* they test against is read from the
# surface above, so this table never has to be edited when a vocabulary grows.

REQUIRED = [
    ("version", "which revision of the surface this file was written against (§ The file itself)"),
    ("roots.code", "the path every git and gh call addresses, configured and never inferred (§ 1)"),
    ("host.kind", "the code host (§ 2)"),
    ("host.repo", "the repository, stated and never inherited from the working directory (§ 2)"),
    ("host.checks", "the host's runs; `[]` is the one legitimate absence and means every verdict is local (§ 2)"),
    ("tracker.kind", "the tracker port, or `none` (§ 3)"),
    ("work_item.type.carrier", "what carries the type, or `none` with an `absent_reason` (§ 4.1)"),
    ("work_item.estimate.carrier", "what carries the estimate, or `none` with an `absent_reason` (§ 4.3)"),
    ("work_item.template.carrier", "what carries the template, or `none` with an `absent_reason` (§ 4.4)"),
    ("statuses", "the status vocabulary; `[]` is legitimate (§ 4.2)"),
    ("readiness", "the readiness gate; `[]` is legitimate (§ 5)"),
    ("commit.staging", "how changes are staged (§ 6)"),
    ("commit.trailer", "the commit trailer, or `none` (§ 6)"),
    ("carriers", "each mapped role's carrier (§ 7)"),
    ("language.work_item", "the language work items are written in (§ 8)"),
    ("language.repo", "the language the repository is written in (§ 8)"),
]

# A facet whose carrier is `none` states why. This is the line between a
# deliberate absence and an unset value, and it is the whole reason the two can
# be told apart at all.
ABSENT_REASON_REQUIRED = [
    "work_item.type",
    "work_item.estimate",
    "work_item.template",
]

# Keys whose value must come from a set the surface states inline. The path is
# both where the value lives in a configuration and where the surface states the
# alternation, because the surface states each one on the key's own line.
#
# `commit.trailer` is deliberately absent: it admits a literal trailer line
# beside its alternation, so the set is open and there is nothing to enforce.
ENUM_KEYS = [
    "tracker.kind",
    "work_item.type.carrier",
    "work_item.estimate.carrier",
    "work_item.template.carrier",
    "commit.staging",
]


def validate(data: dict, facts: dict) -> None:
    for path, what in REQUIRED:
        if not _has(data, path):
            raise ConfigError(path, f"required -- {what}.")

    for path in ENUM_KEYS:
        allowed = vocabulary(facts, path, f"`{path}`")
        value = _get(data, path)
        if value not in allowed:
            raise ConfigError(
                path, f"is {value!r}; the surface allows {' | '.join(allowed)}."
            )

    for facet in ABSENT_REASON_REQUIRED:
        if _get(data, f"{facet}.carrier") == "none" and not _get(
            data, f"{facet}.absent_reason"
        ):
            raise ConfigError(
                f"{facet}.absent_reason",
                "required when the carrier is `none`. A deliberately absent "
                "facet states its reason; an unset one is a misconfiguration, "
                "and the two read identically without it.",
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
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ConfigError(CONFIG_PATH, "is empty or is not a mapping.")

    return _resolve(data, skills_root, facts, check_paths)


def load_text(text: str, skills_root: str, *, check_paths: bool = False) -> Config:
    """Resolve a configuration already in hand. Used to load the examples."""
    with open(SURFACE, encoding="utf-8") as handle:
        facts = surface_facts(handle.read())
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ConfigError(CONFIG_PATH, "is empty or is not a mapping.")
    return _resolve(data, skills_root, facts, check_paths)


def _resolve(data: dict, skills_root: str, facts: dict, check_paths: bool) -> Config:
    for path, value in facts["defaults"].items():
        _set_default(data, path, value)
    validate(data, facts)

    config = Config(data, skills_root, facts)
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

    for facet in ABSENT_REASON_REQUIRED:
        broken = _example_without(f"{facet}.absent_reason", loaded)
        check(
            f"an unset `{facet}` is refused, with the key named",
            broken == f"{facet}.absent_reason",
            f"reported {broken!r}",
        )

    for path, _ in REQUIRED:
        broken = _example_missing(path, loaded)
        check(f"a config missing `{path}` is refused, with the key named",
              broken == path, f"reported {broken!r}")

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

    if failures:
        print(f"\n{failures} assertion(s) did not hold.")
    return 1 if failures else 0


def _a_valid_example() -> dict:
    with open(os.path.join(EXAMPLES, "github-projects.yaml"), encoding="utf-8") as h:
        return yaml.safe_load(h.read())


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


# --- entry point -----------------------------------------------------------


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Read a project's configuration, once, for every role.",
    )
    parser.add_argument(
        "--skills-root",
        default=".",
        help="the root the configuration is resolved relative to; defaults to the "
        "working directory, and a role states it rather than relying on that",
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
