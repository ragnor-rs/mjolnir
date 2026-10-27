#!/usr/bin/env python3
"""Can mjolnir replace a target project's loop today, and what is missing where it cannot.

Readiness is not one fact, so this prints four per project and never averages them:

  **Resolution** -- does the plugin resolve in that project at all. The registration is
  machine-wide at user scope, so this is one global fact plus a check for a local override that
  turns it off again.

  **Configuration** -- is there a `.claude/mjolnir.yaml` the shared reader accepts. A project
  with none is not configured; a candidate file named on the invocation is validated against the
  project's own skills root without writing anything into that project.

  **The tracker** -- asked through a `Port` rather than read off the registry, so the three
  states § 3 keeps apart stay apart: an adapter registered for this kind, the trackerless
  adapter, and an adapter nobody has built yet.

  **The roles** -- what the project carries today against what the plugin ships. Both sides are
  enumerated from the trees rather than declared, because a count that is maintained by hand is
  the thing that goes stale first. Carriers are skills, commands *and* hooks (§ 7): a sweep of
  skill directories alone undercounts one target by six roles.

⛔ Which projects to check is an **argument, never a value in this tree**. Each is a path, with
that project's tracker kind after a colon where it has no configuration of its own to read one
from; the adapter work item per kind and the migration's roots are arguments too. So this file
names no project, no directory and no tracker, and a list nobody passed is reported as exactly
that rather than resolving to nothing and reading as ready.

  readiness.py <path>[:<kind>] ... [--adapter-item <kind>=<n>] [--migration-items 1,2]
               [--candidate <name>=<file>] [--no-host]

⛔ Nothing here writes to a target project, and nothing writes to this repository.

Exit status: 0 every target ready -- 1 at least one is not -- 2 something could not be
established, which is a different answer from "not ready" and is never folded into it.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(SKILL_DIR)))
PLUGIN_ROOT = os.path.join(REPO_ROOT, "plugins", "mjolnir")
PLUGIN_SCRIPTS = os.path.join(PLUGIN_ROOT, "scripts")
VOCABULARY = os.path.join(SKILL_DIR, "vocabulary.yaml")

# The reader and the port are imported rather than reimplemented: this check must report what a
# role would actually get, and a second implementation of either would report what it believes.
sys.path.insert(0, PLUGIN_SCRIPTS)
try:
    import config  # noqa: E402
    import port  # noqa: E402
    import yaml  # noqa: E402
except ModuleNotFoundError as error:  # pragma: no cover - environment, not logic
    sys.exit(f"readiness.py cannot import what it measures with: {error}")

# Where a project's own configuration sits, and where the loop's carriers sit under it. Both are
# the harness's layout rather than this check's choice.
CONFIG_PATH = os.path.join(".claude", "mjolnir.yaml")
SETTINGS = ["settings.json", "settings.local.json"]
PLUGIN_ID = "mjolnir@mjolnir"

# A carrier root, and how a carrier is named inside it. A skill is a directory holding SKILL.md;
# a command is a markdown file; a hook is an executable file -- and a hook is also registered in
# settings, which is the only place a hook with no file of its own is visible.
SKILLS_DIR = "skills"
COMMANDS_DIR = "commands"
HOOKS_DIR = "hooks"

NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
}

LOOP_HEADING = re.compile(r"^##\s+The loop\s+—\s+(\w+)\s+roles\s*$", re.MULTILINE)


class CannotEstablish(Exception):
    """Something this check reads did not have the shape it reads for."""


# --- the invocation, which is where every project value comes from ----------


def parse_project(argument: str) -> dict:
    """One target from one argument: `<path>` or `<path>:<kind>`.

    The name is the directory's own basename rather than a label somebody chose, so nothing has
    to be declared twice. ⚠️ The kind is optional and the colon form is only read as one when
    the tail carries no separator -- a path with a colon in it is a path, and a project that has
    written its own configuration needs no kind here at all, since the reader supplies it.
    """
    path, kind = argument, None
    if ":" in argument:
        head, tail = argument.rsplit(":", 1)
        if head and os.sep not in tail:
            path, kind = head, tail or None
    path = os.path.abspath(os.path.expanduser(path))
    return {"name": os.path.basename(path.rstrip(os.sep)), "dir": path, "kind": kind}


def parse_pair(argument: str, what: str) -> tuple[str, str]:
    """A `key=value` argument, refused rather than half-read when it carries no `=`."""
    if "=" not in argument:
        raise SystemExit(f"{what} wants `<key>=<value>`, and `{argument}` carries no `=`")
    key, value = argument.split("=", 1)
    return key.strip(), value.strip()


# --- the surface, held against the declaration ------------------------------


def loop_role_count(surface_text: str) -> tuple[int, int]:
    """The two statements of the loop's size the surface carries, read apart.

    The heading counts the roles in a word; the paragraph under it lists them separated by `·`.
    Returning both lets the caller refuse a disagreement instead of picking one.
    """
    match = LOOP_HEADING.search(surface_text)
    if not match:
        raise CannotEstablish(
            "schema.md no longer carries a `## The loop — <count> roles` heading, so the role "
            "vocabulary in vocabulary.yaml is held to nothing."
        )
    word = match.group(1).lower()
    if word not in NUMBER_WORDS:
        raise CannotEstablish(f"schema.md's loop heading counts the roles as `{word}`.")

    rest = surface_text[match.end():].lstrip("\n")
    paragraph = []
    for line in rest.split("\n"):
        if not line.strip():
            break
        paragraph.append(line.strip())
    phrases = " ".join(paragraph).split("·")
    return NUMBER_WORDS[word], len(phrases)


# --- what the plugin ships --------------------------------------------------


def shipped_carriers() -> list[tuple[str, str]]:
    """Every carrier the plugin ships, as `(kind, name)`.

    Enumerated from the plugin tree. A role is shipped when something here carries it, which is
    not the same question as whether its work item is closed.
    """
    found = []
    skills = os.path.join(PLUGIN_ROOT, SKILLS_DIR)
    if os.path.isdir(skills):
        for name in sorted(os.listdir(skills)):
            if os.path.isfile(os.path.join(skills, name, "SKILL.md")):
                found.append(("skill", name))

    commands = os.path.join(PLUGIN_ROOT, COMMANDS_DIR)
    if os.path.isdir(commands):
        for name in sorted(os.listdir(commands)):
            if name.endswith(".md"):
                found.append(("command", name[:-3]))

    hooks = os.path.join(PLUGIN_ROOT, HOOKS_DIR, "hooks.json")
    if os.path.isfile(hooks):
        with open(hooks, encoding="utf-8") as handle:
            declared = json.load(handle)
        for event, matchers in (declared.get("hooks") or {}).items():
            for matcher in matchers:
                for entry in matcher.get("hooks") or []:
                    found.append(("hook", hook_stem(entry, event)))
    return found


def hook_stem(entry: dict, event: str) -> str:
    """What a hook entry is named by, which is the script it runs and not the interpreter.

    ⚠️ The carrier is the script, and the script can sit in `args` rather than in `command` --
    reading `command` alone names every hook after whatever runs it.
    """
    tokens = [entry.get("command", "")] + list(entry.get("args") or [])
    for token in reversed([t for t in tokens if t]):
        base = os.path.basename(token)
        if "/" in token and "." in base:
            return os.path.splitext(base)[0]
    return os.path.splitext(os.path.basename(tokens[0]))[0] if tokens[0] else event


# --- what a project carries -------------------------------------------------


def project_carriers(claude_dir: str) -> list[tuple[str, str]]:
    """Every carrier a project carries today, across all three carrier kinds."""
    found = []
    skills = os.path.join(claude_dir, SKILLS_DIR)
    if os.path.isdir(skills):
        for name in sorted(os.listdir(skills)):
            path = os.path.join(skills, name)
            if os.path.isfile(os.path.join(path, "SKILL.md")):
                found.append(("skill", name))
            elif os.path.isfile(path) and name.endswith(".md"):
                # A loose document in a carrier root is not a carrier. It is still reported,
                # because something in a carrier root that nothing classifies is a finding.
                found.append(("loose", name[:-3]))

    commands = os.path.join(claude_dir, COMMANDS_DIR)
    if os.path.isdir(commands):
        for name in sorted(os.listdir(commands)):
            if name.endswith(".md"):
                found.append(("command", name[:-3]))

    hooks = os.path.join(claude_dir, HOOKS_DIR)
    if os.path.isdir(hooks):
        for name in sorted(os.listdir(hooks)):
            if os.path.isfile(os.path.join(hooks, name)):
                found.append(("hook", os.path.splitext(name)[0]))
    return found


def registered_hook_matchers(claude_dir: str) -> int:
    """How many hooks the harness is actually running for this project.

    Counted from settings rather than from the hooks directory, because one of these projects
    registers hooks it keeps no file for -- so the directory listing is not the population.
    """
    total = 0
    for name in SETTINGS:
        path = os.path.join(claude_dir, name)
        if not os.path.isfile(path):
            continue
        try:
            with open(path, encoding="utf-8") as handle:
                data = json.load(handle) or {}
        except (json.JSONDecodeError, OSError):
            continue
        hooks = data.get("hooks")
        if isinstance(hooks, dict):
            total += sum(len(v) for v in hooks.values() if isinstance(v, list))
    return total


def classify(carriers: list[tuple[str, str]], vocabulary: dict) -> dict:
    """Split a carrier list into roles, non-role classes, and what nothing classifies."""
    roles: dict[str, list[str]] = {}
    classes: dict[str, list[str]] = {}
    unclassified: list[str] = []
    partial: dict[str, str] = {}
    for kind, name in carriers:
        entry = vocabulary.get(name)
        label = f"{name} ({kind})"
        if entry is None:
            unclassified.append(label)
        elif "role" in entry:
            roles.setdefault(entry["role"], []).append(label)
            if entry.get("partial"):
                partial[entry["role"]] = entry["partial"]
        else:
            classes.setdefault(entry["class"], []).append(label)
    return {
        "roles": roles,
        "classes": classes,
        "unclassified": unclassified,
        "partial": partial,
    }


# --- the plugin's reach into a project --------------------------------------


def resolution(claude_dir: str) -> tuple[bool, str]:
    """Whether the plugin resolves in this project, and what says so.

    The registration this repository documents is a **directory source at user scope**, whose
    registry entry is machine-wide -- so the per-project question is only whether something
    local turns it off again.
    """
    cfg = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(
        os.path.expanduser("~"), ".claude")
    marketplaces = os.path.join(cfg, "plugins", "known_marketplaces.json")
    served = None
    if os.path.isfile(marketplaces):
        with open(marketplaces, encoding="utf-8") as handle:
            entry = (json.load(handle) or {}).get("mjolnir") or {}
        served = entry.get("installLocation")
    if not served:
        return False, "no `mjolnir` marketplace is registered on this machine"

    enabled = None
    user_settings = os.path.join(cfg, "settings.json")
    if os.path.isfile(user_settings):
        with open(user_settings, encoding="utf-8") as handle:
            enabled = ((json.load(handle) or {}).get("enabledPlugins") or {}).get(PLUGIN_ID)
    if enabled is not True:
        return False, f"`{PLUGIN_ID}` is not enabled at user scope"

    for name in SETTINGS:
        path = os.path.join(claude_dir, name)
        if not os.path.isfile(path):
            continue
        try:
            with open(path, encoding="utf-8") as handle:
                local = ((json.load(handle) or {}).get("enabledPlugins") or {}).get(PLUGIN_ID)
        except (json.JSONDecodeError, OSError):
            continue
        if local is False:
            return False, f"disabled for this project in .claude/{name}"

    tree = "the working tree" if served == REPO_ROOT else served
    return True, f"user scope, directory source → {tree}"


def tracker_evidence(claude_dir: str) -> str:
    """What the project's own carriers name, so a declared tracker kind is falsifiable.

    ⚠️ A declaration nobody tests is a declaration nobody can be wrong about. This counts the
    tracker names appearing in the carriers themselves and prints them beside the declaration.
    """
    names = {
        "trello": "trello",
        "jira": "jira",
        "gh project": "github-projects",
        "gh issue": "github-issues",
    }
    counts: dict[str, int] = {}
    for root in (SKILLS_DIR, COMMANDS_DIR, HOOKS_DIR):
        base = os.path.join(claude_dir, root)
        for directory, _, files in os.walk(base):
            for name in files:
                path = os.path.join(directory, name)
                try:
                    with open(path, encoding="utf-8", errors="ignore") as handle:
                        text = handle.read().lower()
                except OSError:
                    continue
                for needle, kind in names.items():
                    hits = text.count(needle)
                    if hits:
                        counts[kind] = counts.get(kind, 0) + hits
    if not counts:
        return "no tracker named in any carrier"
    return ", ".join(
        f"{kind} ×{n}" for kind, n in sorted(counts.items(), key=lambda kv: -kv[1])
    )


# --- the configuration, and the port over it --------------------------------


def configuration(target: dict, project_dir: str,
                  candidate: str | None) -> tuple[object, bool, str, str | None]:
    """Resolve the configuration this project's roles would read, and say where it came from.

    Four sources, in the order that answers the readiness question most truthfully first:
    the project's own file; a candidate named on the invocation for it; the shipped example for
    the kind the invocation gave; this repository's own configuration where the kind matches.

    ⛔ Only the first two are **this project's facts**, which the returned flag says, because
    the other two are a probe of the port for a `kind` and carry nobody's values. Reading a
    project fact off an example or off this repository's own file is the mistake the flag
    exists to make impossible -- it would report one project's absence as another's.
    """
    own = os.path.join(project_dir, CONFIG_PATH)
    if os.path.isfile(own):
        try:
            loaded = config.load(project_dir, check_paths=True)
            return loaded, True, "the project's own file", None
        except config.ConfigError as error:
            return None, True, "the project's own file", str(error)

    if candidate:
        if not os.path.isfile(candidate):
            return None, True, f"candidate: {candidate}", "the candidate file named on the " \
                                                          "invocation does not exist"
        with open(candidate, encoding="utf-8") as handle:
            text = handle.read()
        where = f"candidate: {candidate}"
        try:
            return config.load_text(text, project_dir, check_paths=True), True, where, None
        except config.ConfigError as error:
            return None, True, where, str(error)

    kind = target["kind"]
    if not kind:
        # ⛔ Not an optimistic guess and not a silent skip: with no file of its own and no kind
        # passed for it, there is nothing to ask the port about, and that is a third answer.
        return None, False, "none written", (
            "no configuration of its own and no tracker kind passed for it, so the port has "
            "nothing to be probed with — pass `<path>:<kind>`"
        )
    example = os.path.join(PLUGIN_ROOT, "config", "examples", f"{kind}.yaml")
    if os.path.isfile(example):
        with open(example, encoding="utf-8") as handle:
            text = handle.read()
        where = f"none written — port probed through examples/{kind}.yaml"
        try:
            return config.load_text(text, project_dir, check_paths=False), False, where, None
        except config.ConfigError as error:
            return None, False, f"examples/{kind}.yaml", str(error)

    try:
        here = config.load(REPO_ROOT, check_paths=True)
    except config.ConfigError as error:
        return None, False, "this repository's own configuration", str(error)
    if here.tracker_kind == kind:
        return here, False, (
            "none written — port probed through this repository's own configuration, "
            "which runs the same kind"
        ), None
    return None, False, "none written", (
        f"no configuration exists to probe `tracker.kind: {kind}` with: the project has no "
        f"file, no candidate is written here, and the surface ships no example for this kind"
    )


def tracker(loaded) -> tuple[str, int, int, str]:
    """Ask the port what this configuration's tracker can do. Three states, never a boolean."""
    over = port.Port(loaded)
    described = over.to_dict()
    operations = described["operations"]
    available = sum(1 for entry in operations.values() if entry["available"])
    detail = {
        "registered": f"an adapter is registered for `{described['kind']}`",
        "trackerless": "the trackerless adapter — a stated configuration, not a gap",
        "absent": f"no adapter built yet for `{described['kind']}`",
    }[described["adapter"]]
    return described["adapter"], available, len(operations), detail


# --- the migration's critical path, from the host ---------------------------


def blocked_by_closure(repo: str, roots: list[int]) -> tuple[dict[int, str], list[str]]:
    """Walk `blocked_by` transitively. Relations, never a line in a body."""
    open_blockers: dict[int, str] = {}
    # ⛔ Asked-and-answered is tracked apart from found-as-a-blocker. Folding the two into one
    # set stops the walk one level past the roots, and a transitive closure that silently
    # reports only the first level is worse than no closure at all.
    asked: set[int] = set()
    notes: list[str] = []
    frontier = list(roots)
    while frontier:
        number = frontier.pop()
        if number in asked:
            continue
        asked.add(number)
        try:
            raw = subprocess.run(
                ["gh", "api", f"repos/{repo}/issues/{number}/dependencies/blocked_by",
                 "--jq", ".[] | [.number, .state, .title] | @tsv"],
                capture_output=True, text=True, timeout=30, check=True,
            ).stdout
        except FileNotFoundError:
            return open_blockers, ["`gh` is not on PATH, so the critical path was not read"]
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
            notes.append(f"#{number}: the host did not answer ({type(error).__name__})")
            continue
        for row in raw.strip().split("\n"):
            if not row:
                continue
            blocker, state, title = row.split("\t", 2)
            blocker = int(blocker)
            if state != "open":
                continue
            open_blockers.setdefault(blocker, title)
            frontier.append(blocker)
    # The roots are the migration itself; two of them block each other, and naming them as
    # their own blockers says nothing the header has not already said.
    for root in roots:
        open_blockers.pop(root, None)
    return open_blockers, notes


def issue(repo: str, number: int) -> tuple[str, str] | None:
    """One work item's state and title, read from the host rather than written down here."""
    try:
        raw = subprocess.run(
            ["gh", "api", f"repos/{repo}/issues/{number}",
             "--jq", "[.state, .title] | @tsv"],
            capture_output=True, text=True, timeout=30, check=True,
        ).stdout.strip()
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None
    state, title = raw.split("\t", 1)
    return state, title


# --- the report -------------------------------------------------------------


def line(label: str, value: str) -> str:
    return f"  {label:<26}{value}"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("projects", nargs="*", metavar="PATH[:KIND]",
                        help="a target's checkout, and its tracker kind where the project has "
                             "no configuration of its own to read one from")
    parser.add_argument("--adapter-item", action="append", default=[], metavar="KIND=N",
                        help="the work item that builds that kind's adapter; repeatable")
    parser.add_argument("--migration-items", default="", metavar="N,N",
                        help="the work items whose `blocked_by` closure is the critical path")
    parser.add_argument("--candidate", action="append", default=[], metavar="NAME=FILE",
                        help="a configuration drafted for that target, validated against its "
                             "own skills root and written nowhere; repeatable")
    parser.add_argument("--no-host", action="store_true",
                        help="skip the dependency closure, which is the only network read")
    args = parser.parse_args(argv)

    targets = [parse_project(argument) for argument in args.projects]
    adapter_items = {}
    for argument in args.adapter_item:
        kind_key, number = parse_pair(argument, "--adapter-item")
        if not number.isdigit():
            raise SystemExit(f"--adapter-item wants a work item number, and `{number}` is not one")
        adapter_items[kind_key] = int(number)
    candidates = dict(parse_pair(c, "--candidate") for c in args.candidate)
    migration_items = [int(n) for n in re.findall(r"\d+", args.migration_items)]

    with open(VOCABULARY, encoding="utf-8") as handle:
        declared = yaml.safe_load(handle)

    with open(os.path.join(PLUGIN_ROOT, "config", "schema.md"), encoding="utf-8") as handle:
        surface_text = handle.read()

    unestablished: list[str] = []

    # The surface against the declaration, before any project is read: a role list that no
    # longer matches the loop would make every count below wrong in the same direction.
    role_keys = declared["roles"]
    try:
        counted, listed = loop_role_count(surface_text)
        if not counted == listed == len(role_keys):
            unestablished.append(
                f"the loop's size disagrees three ways — heading says {counted}, the paragraph "
                f"lists {listed}, vocabulary.yaml declares {len(role_keys)} role keys"
            )
    except CannotEstablish as error:
        unestablished.append(str(error))

    # ⛔ And every `role:` value against that list, which nothing held. The file's own header
    # claims the role keys are held to the surface both ways, and that was true of the *count*
    # only: a misspelled `role:` was accepted silently, classified a shipped carrier under a role
    # that does not exist, and then reported the real role as unshipped — a wrong NOT READY with
    # no line anywhere saying why.
    #
    # ⚠️ One direction only, and the comment here claimed both. A declared entry that nothing
    # ships and no project carries is stale data, and nothing holds that — nor can anything hold
    # it on this population: the projects are the invocation's argument, so an entry would read
    # as stale whenever the one target carrying it is left off the list, a red keyed on the
    # caller's list rather than on any tree. The two entries for this repository's own carrier
    # root are the proof: nothing ships them and no adoption target carries them, so they would
    # read as stale while being exactly right.
    for name, entry in sorted(declared["carriers"].items()):
        role = entry.get("role")
        if role is not None and role not in role_keys:
            unestablished.append(
                f"vocabulary.yaml maps the carrier `{name}` to the role `{role}`, which is not "
                f"one of the {len(role_keys)} the loop declares. A role nothing declares reads "
                "as a role that does not exist, in both directions at once."
            )

    vocabulary = declared["carriers"]
    shipped = classify(shipped_carriers(), vocabulary)
    shipped_roles = set(shipped["roles"])

    print("mjolnir — adoption readiness\n")
    print(line("loop", f"{len(role_keys)} roles: {' · '.join(role_keys)}"))
    print(line("ships", ", ".join(
        f"{role} [{', '.join(shipped['roles'][role])}]" for role in sorted(shipped_roles)
    ) or "no role carrier at all"))
    for name, members in sorted(shipped["classes"].items()):
        print(line(f"ships ({name})", ", ".join(members)))
    if shipped["unclassified"]:
        print(line("ships (unclassified)", ", ".join(shipped["unclassified"])))
        unestablished.append(
            "the plugin ships a carrier vocabulary.yaml does not classify: "
            + ", ".join(shipped["unclassified"])
        )
    # ⛔ The sweep is asked for, not assumed to have run. Installation is the
    # module's presence in the port's adapters package and discovery is lazy, so
    # reading the registry before anything built a `Port` reported `none` while
    # an implementation was installed -- and three lines further down this same
    # report named it. One fact, two answers, the wrong one in the summary.
    #
    # ⛔ Once per port the surface declares, and never the one port this script
    # happens to care most about: a line naming a single port's implementations
    # reads as the whole of what is built, and a port whose package is empty is
    # exactly what a readiness answer has to carry.
    # ⚠️ Labelled by the **package** that was swept rather than by the port's
    # name: the label column is narrower than a dotted kind path, which ran the
    # value straight into the label with no space between them — and the package
    # is what the sweep actually read.
    for _name, spec in sorted(port.surface_ports().items()):
        installed = ", ".join(sorted(port.load_adapters(spec))) or "none"
        print(line(f"{spec.package} installed", installed))

    # ⛔ A list nobody passed is reported rather than resolved to nothing. An empty run that
    # printed a summary and exited 0 would read as "every target is ready". Answered before the
    # host is read, since there is nothing for a closure to be reported against.
    if not targets:
        print("\nno project was named, so nothing was measured. Pass each target's checkout, "
              "with\nits tracker kind after a colon where it has written no configuration of "
              "its own.")
        print(line("could not establish", "no target list was passed"))
        return 2

    # The host is read once, before the projects, so each project's own adapter item can be
    # reported against the closure rather than beside it.
    repo, closure, closure_notes = None, {}, []
    if not args.no_host:
        try:
            repo = config.load(REPO_ROOT, check_paths=True).get("host.repo")
        except config.ConfigError as error:
            unestablished.append(f"this repository's own configuration: {error}")
        if repo and migration_items:
            closure, closure_notes = blocked_by_closure(repo, migration_items)
            unestablished.extend(closure_notes)

    not_ready: list[str] = []
    ready: list[str] = []

    for target in targets:
        name = target["name"]
        print(f"\n{name}")

        project_dir = target["dir"]
        claude_dir = os.path.join(project_dir, ".claude")
        if not os.path.isdir(claude_dir):
            print(line("VERDICT", "CANNOT ESTABLISH — no .claude directory at "
                                  f"{project_dir}"))
            unestablished.append(f"{name}: no checkout at {project_dir}")
            continue

        resolves, why = resolution(claude_dir)
        print(line("resolution", ("yes — " if resolves else "NO — ") + why))

        loaded, own_config, source, error = configuration(
            target, project_dir, candidates.get(name))
        print(line("configuration", source))
        if error:
            print(line("", f"⛔ {error.splitlines()[0]}"))

        # The kind the invocation passed, or — where the project wrote its own file — the kind
        # the reader found in it, which is the stronger of the two and is never overwritten by
        # the argument. ⛔ Read off a probe it would be the probe's kind, so it is read off the
        # project's own configuration only.
        kind, from_own_file = target["kind"], False
        if own_config and loaded is not None and loaded.tracker_kind:
            kind, from_own_file = loaded.tracker_kind, True
        if kind:
            said = "the project's own file" if from_own_file else "passed on the invocation"
            print(line("tracker kind", f"{kind} — {said}"))
        elif own_config:
            print(line("tracker kind", "the project's own file states none, and none was passed"))
        else:
            print(line("tracker kind", "none passed, and the project wrote no file"))
        print(line("tracker in carriers", tracker_evidence(claude_dir)))

        adapter = None
        if loaded is not None:
            adapter, available, total, detail = tracker(loaded)
            print(line("tracker port", f"{detail} — {available} of {total} operations available"))

        # ⚠️ Four cases kept apart, because three of them are absences and an absence reported as
        # the wrong one is a false statement: no kind to look an item up by, no item passed for
        # the kind, an item nobody read the host for, and an item read.
        item = adapter_items.get(kind) if kind else None
        if not kind:
            pass                         # the line above already said why there is nothing to say
        elif item is None:
            print(line("adapter work item", f"none passed for `{kind}`"))
        elif not repo:
            print(line("adapter work item", f"#{item} — the host was not read"))
        else:
            found = issue(repo, item)
            if found is None:
                print(line("adapter work item", f"#{item} — the host did not answer"))
                unestablished.append(f"{name}: #{item}'s state was not read")
            else:
                state, title = found
                flag = ""
                if state == "open" and item not in closure:
                    flag = ("  ⚠️ open, and no migration item depends on it" if closure
                            else "  ⚠️ open; no closure was read to say what depends on it")
                print(line("adapter work item", f"#{item} {state} — {title}{flag}"))

        carried = classify(project_carriers(claude_dir), vocabulary)
        matchers = registered_hook_matchers(claude_dir)
        carried_roles = set(carried["roles"])
        covered = sorted(carried_roles & shipped_roles)
        missing = sorted(carried_roles - shipped_roles)

        print(line("roles carried", f"{len(carried_roles)} — " + ", ".join(
            f"{role} [{', '.join(carried['roles'][role])}]" for role in sorted(carried_roles)
        ) or "none"))
        print(line("replaceable now", f"{len(covered)} of {len(carried_roles)}"
                                      + (f" — {', '.join(covered)}" if covered else "")))
        if missing:
            print(line("unshipped", ", ".join(missing)))
        for role, caveat in sorted(carried["partial"].items()):
            print(line("partial carrier", f"{role}: {caveat}"))
        for cls, members in sorted(carried["classes"].items()):
            print(line(f"beside the loop ({cls})", ", ".join(members)))
        print(line("hooks registered", f"{matchers} matcher(s) in settings"))
        if carried["unclassified"]:
            print(line("unclassified", ", ".join(carried["unclassified"])))

        # A role is replaceable only with the facts it reads available. The day log is the one
        # shipped role, and its evidence script is a project-local path until #15 lands -- so a
        # configuration that leaves it null cannot run it, which the reader already reports.
        # ⛔ Read only off this project's own configuration: asked of a probe, this would report
        # whichever file the probe came from and attribute its absence here.
        caveats = []
        if own_config and loaded is not None and "day_log" in covered:
            if loaded.get("day_log.script") is None:
                caveats.append("day_log.script is null — the role stops rather than running (#15)")
        for caveat in caveats:
            print(line("blocked anyway", caveat))

        if carried["unclassified"]:
            verdict = "CANNOT ESTABLISH — a carrier nothing classifies, so the counts are floors"
            unestablished.append(f"{name}: unclassified carriers")
        elif not resolves:
            verdict = "NOT READY — the plugin does not resolve here"
        elif missing or caveats or adapter == "absent" or loaded is None or not own_config:
            parts = []
            if loaded is None:
                parts.append("no configuration can be validated")
            elif not own_config:
                parts.append("no configuration written")
            if adapter == "absent":
                parts.append("no tracker adapter")
            if missing:
                parts.append(f"{len(missing)} role(s) unshipped")
            if caveats:
                parts.append("a shipped role blocked by its own configuration")
            verdict = "NOT READY — " + "; ".join(parts)
        else:
            verdict = "READY"
        print(line("VERDICT", verdict))
        (ready if verdict == "READY" else not_ready).append(name)

    print("\nthe migration's critical path — open items, `blocked_by` walked transitively")
    if not migration_items:
        # ⚠️ Named rather than skipped. A section that vanished with its roots would leave the
        # report looking complete while the one transitive question went unasked.
        print(line("from", "no roots passed, so no closure was walked — `--migration-items N,N`"))
    elif not repo:
        print(line("from", f"{', '.join(f'#{n}' for n in migration_items)}, and the host was "
                           "not read"))
    else:
        print(line("from", f"{', '.join(f'#{n}' for n in migration_items)} in {repo}"))
        for number, title in sorted(closure.items()):
            print(line("", f"#{number}  {title}"))
        if not closure:
            print(line("", "nothing open blocks them"))
        for note in closure_notes:
            print(line("", f"⚠️ {note}"))

    print("\nsummary")
    print(line("ready", ", ".join(ready) or "none"))
    print(line("not ready", ", ".join(not_ready) or "none"))
    for item in unestablished:
        print(line("could not establish", item))

    if unestablished:
        return 2
    return 1 if not_ready else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
