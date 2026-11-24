#!/usr/bin/env python3
"""Can this procedure replace a target project's loop today, and what is missing where it cannot.

The answer is not one fact, so this prints four per project and never averages them:

  **Resolution** -- does the plugin resolve in that project at all. The registration is
  machine-wide at user scope, so this is one global fact plus a check for a local override that
  turns it off again.

  **Configuration** -- is there a `.claude/mjolnir.yaml` the shared reader accepts. A project
  with none is not configured; a candidate file named on the invocation is validated against the
  project's own skills root without writing anything into that project.

  **The tracker** -- asked through a `Port` rather than read off the registry, so the three
  states § 3 keeps apart stay apart: an adapter registered for this kind, the trackerless
  adapter, and an adapter nobody has built yet. ⛔ Every other tracker reading this check takes
  goes through the same port and names no tracker either -- the blocker closure and each adapter
  work item included.

  **The roles** -- what the project carries today against what this toolkit ships. Both sides are
  enumerated from the trees rather than declared, because a count maintained by hand is the thing
  that goes stale first. Carriers are skills, commands *and* hooks (§ 7): a sweep of skill
  directories alone undercounts one target by six roles.

⛔ Which projects to check is an **argument, never a value in this tree**, and so is everything
else about them -- the tracker kind, the adapter work item, the migration's roots, a drafted
configuration, and the map that says what a carrier on that project's disk is. So this file names
no project, no directory and no tracker, and a list nobody passed is reported as exactly that
rather than resolving to nothing and reading as ready.

  adoption.py <path>[:<kind>] ... [--carriers <file>] [--adapter-item <kind>=<n>]
              [--migration-items 1,2] [--candidate <name>=<file>] [--no-host]

⛔ What *this toolkit* ships is classified the other way round: each carrier declares its own
class beside itself, a skill in its own `SKILL.md` and a hook in its own script, so the change
that ships a carrier cannot ship it unclassified. Nothing in this directory lists them.

⛔ Nothing here writes to a target project, and nothing writes to this repository.

Exit status: 0 every target ready -- 1 at least one is not -- 2 something could not be
established, which is a different answer from "not ready" and is never folded into it.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN_ROOT = os.path.dirname(os.path.dirname(SKILL_DIR))
PLUGIN_SCRIPTS = os.path.join(PLUGIN_ROOT, "scripts")
VOCABULARY = os.path.join(SKILL_DIR, "vocabulary.yaml")

# The tree the plugin is served from, used for one label and nothing else. ⚠️ Not the project
# this role is running in: that is the skills root below, and the two are the same directory only
# when the check is run from the repository the plugin is served out of.
PLUGIN_TREE = os.path.dirname(os.path.dirname(PLUGIN_ROOT))

# § 1's skills root -- the project this role was invoked in, which is where its own configuration
# is read from. ⛔ Not derived from this file's path: a carrier under a plugin resolves the plugin
# wherever it is installed, and the project whose backlog carries the work items below is the one
# the person ran the check in.
SKILLS_ROOT = os.getcwd()

# The reader and the port are imported rather than reimplemented: this check must report what a
# role would actually get, and a second implementation of either would report what it believes.
sys.path.insert(0, PLUGIN_SCRIPTS)
try:
    import config  # noqa: E402
    import port  # noqa: E402
    import yaml  # noqa: E402
except ModuleNotFoundError as error:  # pragma: no cover - environment, not logic
    sys.exit(f"adoption.py cannot import what it measures with: {error}")

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

# ⛔ The heading states no count and this check reads none out of it. The surface rules that the
# role list carries no count anywhere -- not in its own heading, not on the front page, not in a
# document beside it -- so the paragraph under the heading is the only statement of the loop's size
# there is, and a word read out of the heading would be this check asking for the restatement the
# surface forbids. ⚠️ The heading is still what locates the paragraph, which is why it is matched
# at all.
LOOP_HEADING = re.compile(r"^##\s+The loop\s*$", re.MULTILINE)

# How a carrier declares what it is, in its own file.
#
# ⛔ The skill form is read **inside a fenced yaml block** and not anywhere in the file. At the
# start of a markdown line `# carrier: start` is a level-one heading, so a form matched loose
# would read a heading as a declaration and a declaration in prose as one too -- and the fence is
# the device the surface itself uses for the same purpose.
FENCE = re.compile(r"^```yaml\s*$(?P<body>.*?)^```\s*$", re.MULTILINE | re.DOTALL)
FENCED_CARRIER = re.compile(r"^#\s*carrier:\s*(?P<word>[A-Za-z_][\w-]*)\s*$", re.MULTILINE)
HOOK_CARRIER = re.compile(
    r"^CARRIER_CLASS\s*=\s*[\"'](?P<word>[A-Za-z_][\w-]*)[\"']\s*$", re.MULTILINE)


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


def read_carrier_map(path: str | None) -> dict:
    """The map that says what a carrier on a *target's* disk is, which arrives on the invocation.

    ⛔ Absent is not empty. With no map passed, nothing can say what any carrier a project holds
    is, so the role axis of every target is unestablished and says so -- never a project carrying
    no roles, which is § 2's absence-of-signal rule arriving where the permissive reading is a
    migration declared done.
    """
    if path is None:
        return {}
    if not os.path.isfile(path):
        raise SystemExit(f"--carriers names `{path}`, which is not a file")
    with open(path, encoding="utf-8") as handle:
        declared = yaml.safe_load(handle) or {}
    carriers = declared.get("carriers")
    if not isinstance(carriers, dict):
        raise SystemExit(
            f"--carriers wants a mapping under `carriers:`, and `{path}` carries none")
    return carriers


# --- the surface, held against the declaration ------------------------------


def loop_role_count(surface_text: str) -> int:
    """The loop's size as the surface states it: the phrases of the list under the heading.

    ⛔ One statement and not two, which is the surface's own rule rather than a reading dropped
    for convenience: the list carries no count, so the paragraph is the whole of what this list
    can be held against. ⚠️ A paragraph that no longer separates its roles with `·` reads as a
    loop of one and is refused here rather than being reported as a disagreement, which is the
    shape a reworded list arrives in.
    """
    match = LOOP_HEADING.search(surface_text)
    if not match:
        raise CannotEstablish(
            "schema.md no longer carries a `## The loop` heading, so the role vocabulary in "
            "vocabulary.yaml is held to nothing."
        )

    rest = surface_text[match.end():].lstrip("\n")
    paragraph = []
    for line in rest.split("\n"):
        if not line.strip():
            break
        paragraph.append(line.strip())
    phrases = " ".join(paragraph).split("·")
    if len(phrases) < 2:
        raise CannotEstablish(
            "the paragraph under schema.md's `## The loop` heading separates no roles with `·`, "
            "so the role vocabulary in vocabulary.yaml is held to nothing."
        )
    return len(phrases)


# --- what this toolkit ships, and what each shipped carrier says it is ------


def shipped_carriers(plugin_root: str = PLUGIN_ROOT) -> list[tuple[str, str]]:
    """Every carrier this toolkit ships, as `(kind, name)`, each one once.

    Enumerated from the plugin tree. A role is shipped when something here carries it, which is
    not the same question as whether its work item is closed.

    ⛔ Deduplicated, and the duplicates are the hooks: one script registered on five events is one
    carrier, and a list that repeated it named the same thing five times in the report and
    classified it five times over.
    """
    found = []
    skills = os.path.join(plugin_root, SKILLS_DIR)
    if os.path.isdir(skills):
        for name in sorted(os.listdir(skills)):
            if os.path.isfile(os.path.join(skills, name, "SKILL.md")):
                found.append(("skill", name))

    commands = os.path.join(plugin_root, COMMANDS_DIR)
    if os.path.isdir(commands):
        for name in sorted(os.listdir(commands)):
            if name.endswith(".md"):
                found.append(("command", name[:-3]))

    hooks = os.path.join(plugin_root, HOOKS_DIR, "hooks.json")
    if os.path.isfile(hooks):
        with open(hooks, encoding="utf-8") as handle:
            declared = json.load(handle)
        for event, matchers in (declared.get("hooks") or {}).items():
            for matcher in matchers:
                for entry in matcher.get("hooks") or []:
                    found.append(("hook", hook_stem(entry, event)))
    return sorted(set(found))


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


def declaration_file(kind: str, name: str, plugin_root: str) -> str:
    """Which of this toolkit's own files a shipped carrier declares itself in."""
    if kind == "skill":
        return os.path.join(plugin_root, SKILLS_DIR, name, "SKILL.md")
    if kind == "command":
        return os.path.join(plugin_root, COMMANDS_DIR, f"{name}.md")
    return os.path.join(plugin_root, "scripts", f"{name}.py")


def shipped_word(kind: str, name: str, plugin_root: str = PLUGIN_ROOT) -> str:
    """The one word a shipped carrier declares about itself, read from its own file.

    ⛔ Raises rather than returning a default. A carrier whose file says nothing is the state the
    central table used to hide: the role it carries would read as a role that does not exist, and
    that is the one error this check must not make.

    ⛔ And two declarations in one file raise as well. A file saying two things is not a file
    saying the first of them, and picking one would be this reader choosing which.
    """
    path = declaration_file(kind, name, plugin_root)
    if not os.path.isfile(path):
        raise CannotEstablish(
            f"`{name}` ({kind}) is shipped, and the file it would declare itself in is not "
            f"there: {os.path.relpath(path, plugin_root)}"
        )
    with open(path, encoding="utf-8") as handle:
        text = handle.read()

    if kind == "hook":
        words = [m.group("word") for m in HOOK_CARRIER.finditer(text)]
    else:
        words = [
            m.group("word")
            for fence in FENCE.finditer(text)
            for m in FENCED_CARRIER.finditer(fence.group("body"))
        ]

    if not words:
        raise CannotEstablish(
            f"`{name}` ({kind}) is shipped and declares no class in its own file. The change "
            "that ships a carrier declares it there, by schema.md § Whether a project can adopt "
            "this procedure at all → Which carriers are classified, and where."
        )
    if len(set(words)) > 1:
        raise CannotEstablish(
            f"`{name}` ({kind}) declares {len(set(words))} different classes in one file "
            f"({', '.join(sorted(set(words)))}), so nothing there says which it is."
        )
    return words[0]


def classify_shipped(carriers: list[tuple[str, str]], roles: list[str], classes: set[str],
                     plugin_root: str = PLUGIN_ROOT) -> dict:
    """Split what this toolkit ships into roles and non-role classes, by each carrier's own word.

    ⛔ There is no map here and no fallback. Every carrier answers for itself or is reported, and
    what cannot be read is a finding rather than a gap in the toolkit.
    """
    found: dict[str, list[str]] = {}
    other: dict[str, list[str]] = {}
    problems: list[str] = []
    for kind, name in carriers:
        label = f"{name} ({kind})"
        try:
            word = shipped_word(kind, name, plugin_root)
        except CannotEstablish as error:
            problems.append(str(error))
            continue
        if word in roles:
            found.setdefault(word, []).append(label)
        elif word in classes:
            other.setdefault(word, []).append(label)
        else:
            problems.append(
                f"`{name}` ({kind}) declares `{word}`, which is neither one of the "
                f"{len(roles)} roles the loop states nor one of the {len(classes)} classes "
                "vocabulary.yaml closes. A word nothing declares reads as a role that does not "
                "exist, in both directions at once."
            )
    return {"roles": found, "classes": other, "problems": problems}


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


def classify_carried(carriers: list[tuple[str, str]], carrier_map: dict) -> dict:
    """Split a target's carrier list into roles, non-role classes, and what nothing classifies.

    ⛔ An `ambiguous:` entry lands in neither of the first two. A basename covering several roles
    across the projects -- #14's three, measured over at least five copies -- is a name that
    answers nothing, and the two wrong readings are opposite and equally silent: counted as its
    first role, the report names the other two unshipped on a project that carries one of them;
    counted as all of them, it reports two roles covered that nothing there implements. So it is
    counted as none, and the caller turns it into "cannot establish" the way an unclassified
    carrier already is.
    """
    roles: dict[str, list[str]] = {}
    classes: dict[str, list[str]] = {}
    unclassified: list[str] = []
    ambiguous: dict[str, list[str]] = {}
    partial: dict[str, str] = {}
    for kind, name in carriers:
        entry = carrier_map.get(name)
        label = f"{name} ({kind})"
        if entry is None:
            unclassified.append(label)
        elif not isinstance(entry, dict) or not (
                entry.keys() & {"role", "class", "ambiguous"}):
            # ⛔ An entry that states none of the three is counted as no classification at all,
            # which is the same answer as no entry. ⚠️ Found by review on this change, reproduced:
            # the `else` arm read `entry["class"]` unconditionally, so a half-written entry --
            # `{}`, or one carrying only a `partial:` note -- came back as a `KeyError` traceback
            # and an exit status of 1, which every caller keying on the status reads as *not
            # ready*. ⛔ The map is a file a person maintains outside this repository, so a
            # half-written entry is the ordinary shape of its mistakes rather than an exotic one.
            unclassified.append(label)
        elif "ambiguous" in entry:
            ambiguous[label] = list(entry["ambiguous"])
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
        "ambiguous": ambiguous,
        "partial": partial,
    }


def hold_carrier_map(carrier_map: dict, roles: list[str], classes: set[str]) -> list[str]:
    """Every word the invocation's map uses, against the two sets the surface closes.

    ⛔ Held because nothing else does. A misspelled `role:` was accepted silently, classified a
    carrier under a role that does not exist, and then reported the real role as unshipped -- a
    wrong NOT READY with no line anywhere saying why.

    ⚠️ One direction only, and an earlier form of this comment claimed both. An entry nothing
    ships and no project carries is stale data, and nothing holds that -- nor can anything hold it
    on this population: the projects are the invocation's argument, so an entry would read as
    stale whenever the one target carrying it is left off the list, a red keyed on the caller's
    list rather than on any tree.

    ⚠️ `ambiguous:` is held the same way and for the same reason. Its values are never compared
    against a shipped carrier, so a misspelling in one is quieter than a misspelling in `role:`:
    it would print a role the loop does not have as one of the readings a carrier may be, and
    nothing downstream would ever ask about it.
    """
    problems = []
    for name, entry in sorted(carrier_map.items()):
        if not isinstance(entry, dict):
            problems.append(
                f"the carrier map entry for `{name}` is not a mapping, so it states neither a "
                "role nor a class")
            continue
        for key in ("role", "ambiguous"):
            value = entry.get(key)
            if value is None:
                continue
            for role in [value] if isinstance(value, str) else value:
                if role in roles:
                    continue
                problems.append(
                    f"the carrier map puts `{name}` under the role `{role}` in `{key}:`, which "
                    f"is not one of the {len(roles)} the loop declares. A role nothing declares "
                    "reads as a role that does not exist, in both directions at once."
                )
        word = entry.get("class")
        if word is not None and word not in classes:
            problems.append(
                f"the carrier map puts `{name}` in the class `{word}`, which is not one of the "
                f"{len(classes)} vocabulary.yaml closes."
            )
    return problems


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

    tree = "the tree this check is running out of" if served == PLUGIN_TREE else served
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

    Four sources, in the order that answers the question most truthfully first: the project's own
    file; a candidate named on the invocation for it; the shipped example for the kind the
    invocation gave; the configuration of the project this check is running in, where the kind
    matches.

    ⛔ Only the first two are **this project's facts**, which the returned flag says, because
    the other two are a probe of the port for a `kind` and carry nobody's values. Reading a
    project fact off an example or off another project's file is the mistake the flag exists to
    make impossible -- it would report one project's absence as another's.
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
        here = config.load(SKILLS_ROOT, check_paths=True)
    except config.ConfigError as error:
        return None, False, "the configuration of the project this check runs in", str(error)
    if here.tracker_kind == kind:
        return here, False, (
            "none written — port probed through the configuration of the project this check "
            "runs in, which states the same kind"
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
    # ⛔ Keyed on the port's own names for its three states and never on copies of
    # the words. ⚠️ Measured: this dict held `trackerless` as a literal, the port
    # renamed that state to `unconfigured`, and every configuration with no tracker
    # reached this line as `KeyError` — a traceback where an answer belongs, from a
    # script the same change was editing.
    detail = {
        port.STATE_REGISTERED: f"an adapter is registered for `{described['kind']}`",
        port.STATE_UNCONFIGURED: "the adapter that implements nothing — a stated "
        "configuration, not a gap",
        port.STATE_ABSENT: f"no adapter built yet for `{described['kind']}`",
    }[described["adapter"]]
    return described["adapter"], available, len(operations), detail


# --- the migration's critical path, through the tracker port ----------------
#
# ⛔ Both readings below go through the port and neither names a tracker. ⚠️ Found by review on
# this change: they shelled out to one host's own client, with that host's API path and a
# projection written out -- a second implementation of two operations § 3 already declares, in a
# file whose own header claims the port is imported rather than reimplemented. The claim was the
# defect; the code is what made it false. ⚠️ Neither the client's name nor the path form is
# written anywhere in this file, which a self-test arm holds: this is a carrier's implementation
# and the one lexical rule it is held to is naming no tracker.
#
# ⚠️ What the switch also buys, stated because it is the reason the port exists rather than a
# bonus: these read *this* project's tracker, whatever kind it is, instead of one host's issue
# API -- so a project whose backlog is not on the code host gets an answer or a stated absence
# rather than a silent failure to read anything.


def tracker_over(loaded) -> object:
    """The tracker port over this project's configuration, built once per run."""
    return port.Port(loaded)


def blocked_by_closure(over, roots: list[int]) -> tuple[dict[int, str], list[str]]:
    """Walk `read_blockers` transitively. Relations, never a line in a body."""
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
        outcome = over.invoke("read_blockers", str(number))
        if outcome.refused or not outcome.performed:
            # ⛔ Absent and did-not-answer are reported apart, the port holding them apart: the
            # first is a capability this tracker does not have and stops the walk entirely, the
            # second is one item nobody could ask about.
            if outcome.refused:
                return open_blockers, [
                    f"the tracker port cannot read blockers here: {outcome.detail}"]
            notes.append(f"#{number}: the tracker did not answer — {outcome.detail}")
            continue
        for blocker in (outcome.result or {}).get("blockers") or []:
            if str(blocker.get("state", "")).lower() != "open":
                continue
            found = int(blocker["number"])
            open_blockers.setdefault(found, blocker.get("title") or "")
            frontier.append(found)
    # The roots are the migration itself; two of them block each other, and naming them as
    # their own blockers says nothing the header has not already said.
    for root in roots:
        open_blockers.pop(root, None)
    return open_blockers, notes


def issue(over, number: int) -> tuple[str, str] | None:
    """One work item's state and title, read through the port rather than written down here."""
    outcome = over.invoke("read_item", str(number))
    if outcome.refused or not outcome.performed or not outcome.result:
        return None
    item = outcome.result
    state, title = item.get("state"), item.get("title")
    if state is None or title is None:
        return None
    return str(state).lower(), str(title)


# --- the report -------------------------------------------------------------


def line(label: str, value: str) -> str:
    return f"  {label:<26}{value}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("projects", nargs="*", metavar="PATH[:KIND]",
                        help="a target's checkout, and its tracker kind where the project has "
                             "no configuration of its own to read one from")
    parser.add_argument("--carriers", metavar="FILE",
                        help="the map saying what a carrier on a target's disk is, keyed by "
                             "basename; a target's facts, so it arrives here and is kept outside "
                             "this repository")
    parser.add_argument("--adapter-item", action="append", default=[], metavar="KIND=N",
                        help="the work item that builds that kind's adapter; repeatable")
    parser.add_argument("--migration-items", default="", metavar="N,N",
                        help="the work items whose blocker closure is the critical path")
    parser.add_argument("--candidate", action="append", default=[], metavar="NAME=FILE",
                        help="a configuration drafted for that target, validated against its "
                             "own skills root and written nowhere; repeatable")
    parser.add_argument("--no-host", action="store_true",
                        help="skip the dependency closure, which is the only network read")
    parser.add_argument("--self-test", action="store_true",
                        help="hold this check to the properties it claims, and to the surface")
    return parser


def main(argv: list[str]) -> int:
    args = build_parser().parse_args(argv)
    if args.self_test:
        return self_test()

    targets = [parse_project(argument) for argument in args.projects]
    adapter_items = {}
    for argument in args.adapter_item:
        kind_key, number = parse_pair(argument, "--adapter-item")
        if not number.isdigit():
            raise SystemExit(f"--adapter-item wants a work item number, and `{number}` is not one")
        adapter_items[kind_key] = int(number)
    candidates = dict(parse_pair(c, "--candidate") for c in args.candidate)
    migration_items = [int(n) for n in re.findall(r"\d+", args.migration_items)]
    carrier_map = read_carrier_map(args.carriers)

    with open(VOCABULARY, encoding="utf-8") as handle:
        declared = yaml.safe_load(handle)

    with open(os.path.join(PLUGIN_ROOT, "config", "schema.md"), encoding="utf-8") as handle:
        surface_text = handle.read()

    unestablished: list[str] = []

    role_keys = declared["roles"]
    class_words = set(declared["classes"])

    # ⛔ The two sets are asserted disjoint rather than assumed so. One word meaning both a role
    # and a class would make every carrier's declaration ambiguous, and the reader resolves roles
    # first -- so the collision would be silent in exactly the direction that reports a class as
    # a role of the loop.
    both = sorted(set(role_keys) & class_words)
    if both:
        unestablished.append(
            f"vocabulary.yaml uses {', '.join(both)} as both a role of the loop and a class, so "
            "a carrier declaring one of those words states two different things at once"
        )

    # The surface against the declaration, before any project is read: a role list that no
    # longer matches the loop would make every count below wrong in the same direction.
    try:
        listed = loop_role_count(surface_text)
        if listed != len(role_keys):
            unestablished.append(
                f"the loop's size disagrees — the surface's list carries {listed} roles, "
                f"vocabulary.yaml declares {len(role_keys)} role keys"
            )
    except CannotEstablish as error:
        unestablished.append(str(error))

    unestablished.extend(hold_carrier_map(carrier_map, role_keys, class_words))

    shipped = classify_shipped(shipped_carriers(), role_keys, class_words)
    shipped_roles = set(shipped["roles"])

    print("mjolnir — can this procedure replace a project's loop\n")
    print(line("loop", f"{len(role_keys)} roles: {' · '.join(role_keys)}"))
    print(line("ships", ", ".join(
        f"{role} [{', '.join(shipped['roles'][role])}]" for role in sorted(shipped_roles)
    ) or "no role carrier at all"))
    for name, members in sorted(shipped["classes"].items()):
        print(line(f"ships ({name})", ", ".join(members)))
    for problem in shipped["problems"]:
        print(line("ships (unestablished)", problem.split(". ")[0]))
        unestablished.append(problem)
    # ⛔ The sweep is asked for, not assumed to have run. Installation is the
    # module's presence in the port's adapters package and discovery is lazy, so
    # reading the registry before anything built a `Port` reported `none` while
    # an implementation was installed -- and three lines further down this same
    # report named it. One fact, two answers, the wrong one in the summary.
    #
    # ⛔ Once per port the surface declares, and never the one port this script
    # happens to care most about: a line naming a single port's implementations
    # reads as the whole of what is built, and a port whose package is empty is
    # exactly what an answer here has to carry.
    # ⚠️ Labelled by the **package** that was swept rather than by the port's
    # name: the label column is narrower than a dotted kind path, which ran the
    # value straight into the label with no space between them — and the package
    # is what the sweep actually read.
    # ⚠️ Ordered by what is printed. Sorting by the port's dotted name while
    # printing its package put these lines in an order keyed on something the
    # reader cannot see.
    for spec in sorted(port.surface_ports().values(), key=lambda one: one.package):
        installed = ", ".join(sorted(port.load_adapters(spec))) or "none"
        print(line(f"{spec.package} installed", installed))

    # ⛔ Absent is reported rather than read as empty, and before any target is measured: with no
    # map, nothing can say what a carrier any project holds is.
    if not carrier_map:
        unestablished.append(
            "no carrier map was passed, so what any target's own carriers are is unestablished "
            "and every role count below is a floor — `--carriers <file>`"
        )

    # ⛔ A list nobody passed is reported rather than resolved to nothing. An empty run that
    # printed a summary and exited 0 would read as "every target is ready". Answered before the
    # host is read, since there is nothing for a closure to be reported against.
    if not targets:
        print("\nno project was named, so nothing was measured. Pass each target's checkout, "
              "with\nits tracker kind after a colon where it has written no configuration of "
              "its own.")
        print(line("could not establish", "no target list was passed"))
        # ⛔ And everything established before the target list was read, which this return used
        # to drop. The findings above it are about the surface, the vocabulary and this toolkit's
        # own carriers -- none of them needs a target, all of them were already printed in part,
        # and the one line about the missing argument read as the only thing wrong. Measured on a
        # misspelled role key under `ambiguous:`: the hold fired, the entry was on this list, and
        # a run with no target reported green.
        for item in unestablished:
            print(line("could not establish", item))
        return 2

    # The tracker is read once, before the projects, so each project's own adapter item can be
    # reported against the closure rather than beside it. ⚠️ `repo` is read for the report alone
    # and is never what addresses a call: which repository or project the items live in is the
    # port's own business, read out of the same configuration it was built from.
    over, repo, closure, closure_notes = None, None, {}, []
    if not args.no_host:
        try:
            here = config.load(SKILLS_ROOT, check_paths=True)
            over, repo = tracker_over(here), here.get("host.repo")
        except config.ConfigError as error:
            unestablished.append(
                f"the configuration of the project this check runs in: {error}")
        if over and migration_items:
            closure, closure_notes = blocked_by_closure(over, migration_items)
            unestablished.extend(closure_notes)

    # ⛔ Three buckets and not two. ⚠️ Measured on this check's own first run after the promotion:
    # a target whose verdict was CANNOT ESTABLISH was appended to `not ready`, because the only
    # test was whether the verdict was READY -- so the summary folded the third answer into the
    # second in the one line a reader skims, while the verdict line three rows above said
    # otherwise. The exit status was right and the summary was wrong, which is the quieter half.
    ready: list[str] = []
    not_ready: list[str] = []
    unanswered: list[str] = []

    for target in targets:
        name = target["name"]
        print(f"\n{name}")

        project_dir = target["dir"]
        claude_dir = os.path.join(project_dir, ".claude")
        if not os.path.isdir(claude_dir):
            print(line("VERDICT", "CANNOT ESTABLISH — no .claude directory at "
                                  f"{project_dir}"))
            unestablished.append(f"{name}: no checkout at {project_dir}")
            # ⛔ Into the third bucket before the `continue`, not left out of all three.
            # ⚠️ Found by review on this change, reproduced: this arm returned to the loop
            # without placing the target anywhere, so the summary named it under `targets` and
            # then said `none` on every one of the three lines below it -- a target measured and
            # placed nowhere, which reads as a target that was not measured.
            unanswered.append(name)
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
        elif over is None:
            print(line("adapter work item", f"#{item} — the tracker was not read"))
        else:
            found = issue(over, item)
            if found is None:
                print(line("adapter work item", f"#{item} — the tracker did not answer"))
                unestablished.append(f"{name}: #{item}'s state was not read")
            else:
                state, title = found
                flag = ""
                if state == "open" and item not in closure:
                    flag = ("  ⚠️ open, and no migration item depends on it" if closure
                            else "  ⚠️ open; no closure was read to say what depends on it")
                print(line("adapter work item", f"#{item} {state} — {title}{flag}"))

        carried = classify_carried(project_carriers(claude_dir), carrier_map)
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
        for label, readings in sorted(carried["ambiguous"].items()):
            print(line("ambiguous carrier", f"{label} — may be {', '.join(readings)}; read this "
                                            "project's own carriers block"))

        # ⛔ No shipped role is blocked by its own configuration here, and the arm that used to
        # answer that question is gone rather than left standing. It read `day_log.script`, which
        # #15 retired: a configuration declaring that key is now refused by the reader, so the
        # test had one outcome for every project -- `None` always, and so a caveat and a
        # NOT READY verdict for every project that carried a `day_log` role. ⚠️ An unconditional
        # arm is worse than an absent one: it reads as a reading and answers nothing.
        # ⚠️ What a replacement would have to be: a reading taken off a key that is still live,
        # and off this project's own configuration rather than a probe's -- asked of a probe, it
        # would report whichever file the probe came from and attribute the absence here.

        if not carrier_map:
            # ⛔ Its own verdict, because the cause is the invocation and not the project: a
            # target measured with no map has nothing wrong with it, and reporting it as
            # unclassified would name the project for a missing argument.
            verdict = ("CANNOT ESTABLISH — no carrier map was passed, so the counts are floors")
        elif carried["unclassified"]:
            verdict = "CANNOT ESTABLISH — a carrier nothing classifies, so the counts are floors"
            unestablished.append(f"{name}: unclassified carriers")
        elif carried["ambiguous"]:
            # ⛔ Its own verdict and its own line, not folded into the one above. The remedy is
            # opposite: an unclassified carrier is answered by naming it in the map, and an
            # ambiguous one can never be -- the name is known and is several roles, so only this
            # project's own statement says which.
            verdict = ("CANNOT ESTABLISH — a carrier whose name covers several roles, so the "
                       "counts are floors")
            unestablished.append(
                f"{name}: " + "; ".join(
                    f"`{label}` may be {', '.join(readings)}"
                    for label, readings in sorted(carried["ambiguous"].items())
                )
            )
        elif not resolves:
            verdict = "NOT READY — the plugin does not resolve here"
        elif missing or adapter == "absent" or loaded is None or not own_config:
            parts = []
            if loaded is None:
                parts.append("no configuration can be validated")
            elif not own_config:
                parts.append("no configuration written")
            if adapter == "absent":
                parts.append("no tracker adapter")
            if missing:
                parts.append(f"{len(missing)} role(s) unshipped")
            verdict = "NOT READY — " + "; ".join(parts)
        else:
            verdict = "READY"
        print(line("VERDICT", verdict))
        if verdict == "READY":
            ready.append(name)
        elif verdict.startswith("CANNOT ESTABLISH"):
            unanswered.append(name)
        else:
            not_ready.append(name)

    print("\nthe migration's critical path — open items, blockers walked transitively")
    if not migration_items:
        # ⚠️ Named rather than skipped. A section that vanished with its roots would leave the
        # report looking complete while the one transitive question went unasked.
        print(line("from", "no roots passed, so no closure was walked — `--migration-items N,N`"))
    elif over is None:
        print(line("from", f"{', '.join(f'#{n}' for n in migration_items)}, and the tracker was "
                           "not read"))
    else:
        # ⚠️ The subject is named by what the port answers for, which is `host.repo` where that
        # is what this project's tracker is keyed on and nothing where it states none.
        where = f" in {repo}" if repo else ""
        print(line("from", f"{', '.join(f'#{n}' for n in migration_items)}{where}"))
        for number, title in sorted(closure.items()):
            print(line("", f"#{number}  {title}"))
        if not closure:
            print(line("", "nothing open blocks them"))
        for note in closure_notes:
            print(line("", f"⚠️ {note}"))

    print("\nsummary")
    print(line("targets", ", ".join(t["name"] for t in targets)))
    print(line("ready", ", ".join(ready) or "none"))
    print(line("not ready", ", ".join(not_ready) or "none"))
    print(line("no answer", ", ".join(unanswered) or "none"))
    for item in unestablished:
        print(line("could not establish", item))

    if unestablished:
        return 2
    return 1 if not_ready else 0


# --- what this check claims about itself ------------------------------------


def self_test() -> int:
    """Hold this check to the four properties it claims, and to the surface it reads.

    ⛔ Every arm stands its own trees up. A property asserted against the live adoption targets
    would be asserted against whatever those projects happen to hold today, which is a test that
    passes or fails for reasons outside this repository.
    """
    import shutil                                      # noqa: PLC0415 - the suite's own, not the
    import tempfile                                    # noqa: PLC0415 - check's
    import contextlib
    import io

    problems: list[str] = []

    def check(what: str, ok: bool) -> None:
        print(f"  {'ok  ' if ok else 'FAIL'}  {what}")
        if not ok:
            problems.append(what)

    def answers(what: str, how, expected) -> None:
        """An arm whose subject may *raise* rather than answer wrong.

        ⛔ A raise is reported as this arm failing and the suite continues. ⚠️ Found by review on
        this change's own fix commit: the arms written against the traceback defect called the
        function directly, so disabling the fix took the whole suite down at that line instead of
        reddening one arm -- and every arm after it never ran, which is one defect masking all of
        them. The arm has to survive exactly the failure it is written against.
        """
        try:
            produced = how()
        except Exception as error:                       # noqa: BLE001 - the arm's whole subject
            print(f"  FAIL  {what} — it raised {type(error).__name__}: {error}")
            problems.append(what)
            return
        check(what, produced == expected)

    with open(VOCABULARY, encoding="utf-8") as handle:
        declared = yaml.safe_load(handle)
    role_keys = declared["roles"]
    class_words = set(declared["classes"])

    # --- the two closed sets, and the surface they are held to ---------------
    check("the role keys and the class words are disjoint",
          not set(role_keys) & class_words)

    with open(os.path.join(PLUGIN_ROOT, "config", "schema.md"), encoding="utf-8") as handle:
        surface_text = handle.read()
    # ⛔ The agreement arm is read through the same guard as the plants below it, and for the same
    # reason: the reading raises where the surface it reads has moved, so an arm that let that out
    # would die here and take every arm after it -- which is the whole suite's own measurement
    # applied to its first use of this reading rather than only to the plants.
    try:
        agrees = loop_role_count(surface_text) == len(role_keys)
    except Exception:
        agrees = False
    check(f"the loop's size agrees with the surface's own list ({len(role_keys)})", agrees)

    # ⛔ Both refusals planted against the mechanism rather than asserted, the surface being the
    # only statement of the loop's size left: a heading this check cannot find, and a list whose
    # roles are no longer separated. ⚠️ Each is read for the sentence it refuses with, because the
    # two say different things to whoever has to fix them.
    for what, mutate, wanted in (
        ("a heading this check cannot find is a refusal, not a loop of nothing",
         lambda text: text.replace("\n## The loop\n", "\n## The loop of roles\n", 1),
         "no longer carries a `## The loop` heading"),
        # ⚠️ Every separator and not the mid-line ones: the list wraps, so a plant written as
        # `" · "` leaves the line-end separators standing and the count never falls to one --
        # measured, as a plant that reported green over an unchanged reading.
        ("a list with no separators left is a refusal, not a loop of one",
         lambda text: text.replace("·", ","),
         "separates no roles with `·`"),
    ):
        # ⛔ Every exception caught and not only the refusal, so the arm survives the defect it
        # tests: with the refusal removed the reading raises on the state it no longer rejects,
        # and an arm that let that out would kill the suite at this line and take every arm
        # below it with it -- measured, as a traceback in place of a verdict.
        try:
            loop_role_count(mutate(surface_text))
        except CannotEstablish as error:
            held = wanted in str(error)
        except Exception:
            held = False
        else:
            held = False
        check(what, held)

    # --- every carrier this toolkit ships declares itself -------------------
    live = shipped_carriers()
    live_shipped = classify_shipped(live, role_keys, class_words)
    check("every carrier this toolkit ships declares its own class",
          not live_shipped["problems"])
    check("one script on several events is one shipped carrier",
          len(live) == len(set(live)))

    # ⛔ Property: a shipped carrier nothing classifies refuses this check's own answer. Planted
    # against the mechanism rather than asserted -- a fake plugin tree with one undeclared skill.
    fake = tempfile.mkdtemp(prefix="adoption-shipped-")
    try:
        bare = os.path.join(fake, SKILLS_DIR, "declares-nothing")
        os.makedirs(bare)
        with open(os.path.join(bare, "SKILL.md"), "w", encoding="utf-8") as handle:
            handle.write("---\nname: declares-nothing\n---\n\n# A carrier with no declaration\n")
        planted = classify_shipped(
            shipped_carriers(fake), role_keys, class_words, plugin_root=fake)
        check("a shipped carrier declaring nothing is a finding, not a default",
              len(planted["problems"]) == 1 and "declares no class" in planted["problems"][0])

        # And a declaration that is a heading rather than a fenced marker is not read as one.
        with open(os.path.join(bare, "SKILL.md"), "w", encoding="utf-8") as handle:
            handle.write("---\nname: declares-nothing\n---\n\n# carrier: start\n")
        heading = classify_shipped(
            shipped_carriers(fake), role_keys, class_words, plugin_root=fake)
        check("a markdown heading is not read as a carrier declaration",
              len(heading["problems"]) == 1)

        # And a word in neither closed set is refused by name.
        with open(os.path.join(bare, "SKILL.md"), "w", encoding="utf-8") as handle:
            handle.write("---\nname: x\n---\n\n```yaml\n# carrier: not-a-word\n```\n")
        unknown = classify_shipped(
            shipped_carriers(fake), role_keys, class_words, plugin_root=fake)
        check("a declared word in neither closed set is refused by name",
              len(unknown["problems"]) == 1 and "not-a-word" in unknown["problems"][0])

        # And two declarations in one file say nothing rather than the first of them.
        with open(os.path.join(bare, "SKILL.md"), "w", encoding="utf-8") as handle:
            handle.write("---\nname: x\n---\n\n```yaml\n# carrier: start\n```\n"
                         "\n```yaml\n# carrier: finish\n```\n")
        twice = classify_shipped(
            shipped_carriers(fake), role_keys, class_words, plugin_root=fake)
        check("two declarations in one file are a finding, not the first of them",
              len(twice["problems"]) == 1 and "different classes" in twice["problems"][0])
    finally:
        shutil.rmtree(fake, ignore_errors=True)

    # --- the invocation's own map, held to the same two sets ----------------
    check("a misspelled role in the carrier map is refused by name",
          len(hold_carrier_map({"a": {"role": "stat"}}, role_keys, class_words)) == 1)
    check("a misspelled role under `ambiguous:` is refused too",
          len(hold_carrier_map(
              {"a": {"ambiguous": ["start", "stat"]}}, role_keys, class_words)) == 1)
    check("a class word in neither set is refused",
          len(hold_carrier_map({"a": {"class": "helpful"}}, role_keys, class_words)) == 1)
    check("a well-formed map is quiet",
          not hold_carrier_map(
              {"a": {"role": "start"}, "b": {"class": "utility"}}, role_keys, class_words))

    # --- an ambiguous name is counted as no role ----------------------------
    split = classify_carried(
        [("skill", "two-roles")], {"two-roles": {"ambiguous": ["billing_report", "day_log"]}})
    check("a basename covering several roles is counted as none of them",
          not split["roles"] and len(split["ambiguous"]) == 1)

    # ⛔ And a map entry stating none of the three. ⚠️ Found by review on this change: the arm
    # that reads a `class:` read it unconditionally, so a half-written entry raised `KeyError`
    # and exited 1 -- which every caller keying on the status reads as *not ready*. The map is a
    # file a person maintains outside this repository, so this is the ordinary shape of its
    # mistakes.
    for shape in ({}, {"partial": "only a note"}, "not a mapping at all"):
        answers(
            f"a map entry stating none of the three is unclassified, not a traceback "
            f"({shape if shape else 'empty'})",
            lambda one=shape: classify_carried(
                [("skill", "half-written")], {"half-written": one}),
            {"roles": {}, "classes": {}, "unclassified": ["half-written (skill)"],
             "ambiguous": {}, "partial": {}},
        )

    # --- the tracker readings go through the port, and name no tracker -------
    # ⛔ Held on the text rather than on a run, which is what this property is about: the two
    # readings were a host client with an API path written out, in a file whose header claims
    # the port is imported rather than reimplemented.
    # ⚠️ The needles are assembled from parts rather than written out, because this file is the
    # text being searched: the first form of this arm failed on its own assertion string, which
    # is the arm reaching the mechanism and also the arm being useless.
    with open(os.path.abspath(__file__), encoding="utf-8") as handle:
        own_text = handle.read()
    shelling = "sub" + "process"
    host_client = "g" + "h api"
    check("no host client and no shell-out is in this file at all",
          shelling not in own_text and host_client not in own_text)
    asked = [one for one in ("read_blockers", "read_item")
             if f'over.invoke("{one}"' in own_text]
    check("the blocker closure and the work-item read go through port operations",
          len(asked) == 2)

    # --- carriers are swept across all three kinds, and hooks come from settings
    sweep = tempfile.mkdtemp(prefix="adoption-sweep-")
    try:
        claude = os.path.join(sweep, ".claude")
        os.makedirs(os.path.join(claude, SKILLS_DIR, "a-skill"))
        with open(os.path.join(claude, SKILLS_DIR, "a-skill", "SKILL.md"), "w",
                  encoding="utf-8") as handle:
            handle.write("---\nname: a-skill\n---\n")
        os.makedirs(os.path.join(claude, COMMANDS_DIR))
        with open(os.path.join(claude, COMMANDS_DIR, "a-command.md"), "w",
                  encoding="utf-8") as handle:
            handle.write("a command\n")
        os.makedirs(os.path.join(claude, HOOKS_DIR))
        with open(os.path.join(claude, HOOKS_DIR, "a-hook.sh"), "w", encoding="utf-8") as handle:
            handle.write("#!/bin/sh\n")
        found = project_carriers(claude)
        check("a target's carriers are swept across skills, commands and hooks",
              sorted(found) == [("command", "a-command"), ("hook", "a-hook"),
                                ("skill", "a-skill")])

        # ⛔ Hooks counted from settings and not from the directory: one target registers five
        # matchers and keeps no hooks directory at all, so the listing is not the population.
        with open(os.path.join(claude, "settings.json"), "w", encoding="utf-8") as handle:
            json.dump({"hooks": {"PreToolUse": [{}, {}], "Stop": [{}]}}, handle)
        check("registered hooks are counted from settings, not from the directory",
              registered_hook_matchers(claude) == 3 and len(
                  [one for one in found if one[0] == "hook"]) == 1)
    finally:
        shutil.rmtree(sweep, ignore_errors=True)

    # --- a probe is never reported as a project's own fact ------------------
    probe = tempfile.mkdtemp(prefix="adoption-probe-")
    try:
        os.makedirs(os.path.join(probe, ".claude"))
        loaded, own, source, error = configuration(
            {"name": os.path.basename(probe), "dir": probe, "kind": "github-issues"},
            probe, None)
        check("a probed configuration is never flagged as the project's own",
              loaded is not None and own is False and "port probed" in source and error is None)
        _, no_kind_own, _, no_kind_error = configuration(
            {"name": "x", "dir": probe, "kind": None}, probe, None)
        check("no file and no kind is a third answer, not a guess",
              no_kind_own is False and no_kind_error is not None)
    finally:
        shutil.rmtree(probe, ignore_errors=True)

    # --- the three verdicts, out of one path --------------------------------
    stage = tempfile.mkdtemp(prefix="adoption-verdicts-")
    was = os.environ.get("CLAUDE_CONFIG_DIR")
    try:
        cfg = os.path.join(stage, "config")
        os.makedirs(os.path.join(cfg, "plugins"))
        with open(os.path.join(cfg, "plugins", "known_marketplaces.json"), "w",
                  encoding="utf-8") as handle:
            json.dump({"mjolnir": {"installLocation": PLUGIN_TREE}}, handle)
        with open(os.path.join(cfg, "settings.json"), "w", encoding="utf-8") as handle:
            json.dump({"enabledPlugins": {PLUGIN_ID: True}}, handle)
        os.environ["CLAUDE_CONFIG_DIR"] = cfg

        example = os.path.join(PLUGIN_ROOT, "config", "examples", "github-issues.yaml")
        with open(example, encoding="utf-8") as handle:
            example_text = handle.read()

        # A project this toolkit can fully serve: its own configuration, a registered adapter,
        # and every carrier it holds mapping to a role something here ships.
        served = os.path.join(stage, "fully-served")
        os.makedirs(os.path.join(served, ".claude", SKILLS_DIR, "its-filer"))
        with open(os.path.join(served, ".claude", SKILLS_DIR, "its-filer", "SKILL.md"), "w",
                  encoding="utf-8") as handle:
            handle.write("---\nname: its-filer\n---\n")
        with open(os.path.join(served, ".claude", "mjolnir.yaml"), "w",
                  encoding="utf-8") as handle:
            handle.write(example_text)

        # And one it cannot: no configuration of its own, and a carrier whose role nothing here
        # ships yet.
        short = os.path.join(stage, "not-served")
        os.makedirs(os.path.join(short, ".claude", SKILLS_DIR, "its-breakdown"))
        with open(os.path.join(short, ".claude", SKILLS_DIR, "its-breakdown", "SKILL.md"), "w",
                  encoding="utf-8") as handle:
            handle.write("---\nname: its-breakdown\n---\n")

        # And one nothing can be said about: a carrier the map does not name.
        opaque = os.path.join(stage, "unmapped")
        os.makedirs(os.path.join(opaque, ".claude", SKILLS_DIR, "nobody-named-this"))
        with open(os.path.join(opaque, ".claude", SKILLS_DIR, "nobody-named-this", "SKILL.md"),
                  "w", encoding="utf-8") as handle:
            handle.write("---\nname: nobody-named-this\n---\n")
        with open(os.path.join(opaque, ".claude", "mjolnir.yaml"), "w",
                  encoding="utf-8") as handle:
            handle.write(example_text)

        carriers_file = os.path.join(stage, "carriers.yaml")
        with open(carriers_file, "w", encoding="utf-8") as handle:
            handle.write("carriers:\n"
                         "  its-filer: { role: file }\n"
                         "  its-breakdown: { role: hours_breakdown }\n")

        def run(argv: list[str]) -> tuple[int, str]:
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                status = main(argv)
            return status, buffer.getvalue()

        code, text = run([served, "--carriers", carriers_file, "--no-host"])
        check("a project this toolkit can fully serve is READY, and the run exits 0",
              code == 0 and "VERDICT                   READY" in text)

        code, text = run([f"{short}:github-issues", "--carriers", carriers_file, "--no-host"])
        check("a project it cannot serve is NOT READY and every gap is named",
              code == 1 and "NOT READY" in text
              and "no configuration written" in text and "1 role(s) unshipped" in text
              and "hours_breakdown" in text)

        code, text = run([opaque, "--carriers", carriers_file, "--no-host"])
        check("a carrier nothing classifies is CANNOT ESTABLISH and exits 2, never NOT READY",
              code == 2 and "CANNOT ESTABLISH" in text and "NOT READY" not in text)
        # ⛔ And the summary's own buckets, which the line above does not reach: it tests the
        # words in the whole report, and the defect this arm was written against put the target
        # under `not ready` while the verdict line said CANNOT ESTABLISH. One fact, two answers.
        check("an unanswered target is in the summary's third bucket, not under not-ready",
              "no answer                 unmapped" in text
              and "not ready                 none" in text)

        # ⛔ And the two verdicts come out of one path: both targets in one run, each answered.
        code, text = run([served, f"{short}:github-issues",
                          "--carriers", carriers_file, "--no-host"])
        check("both verdicts come out of the same run, and not-ready decides the status",
              code == 1 and "READY" in text and "NOT READY" in text
              and "ready                     fully-served" in text
              and "not ready                 not-served" in text)

        # ⛔ No map is its own answer, and it names the invocation rather than the project.
        code, text = run([served, "--no-host"])
        check("no carrier map is unestablished and names the argument, not the project",
              code == 2 and "no carrier map was passed" in text)

        # ⛔ An empty target list measures nothing and says so.
        code, text = run(["--carriers", carriers_file, "--no-host"])
        check("an empty target list is reported, never resolved to nothing",
              code == 2 and "no target list was passed" in text
              and "no project was named" in text)

        # ⛔ And the targets measured are named, so no verdict reads as covering a project
        # nobody passed.
        code, text = run([served, "--carriers", carriers_file, "--no-host"])
        check("the report names which targets were measured",
              "targets                   fully-served" in text)

        # ⛔ A target with no checkout is placed too. ⚠️ Found by review on this change: that arm
        # returned to the loop without reaching any bucket, so the summary named the target under
        # `targets` and then said `none` on all three lines under it — a target measured and
        # placed nowhere, which reads exactly like a target nobody measured.
        gone = os.path.join(stage, "no-checkout-here")
        os.makedirs(gone)
        code, text = run([gone, "--carriers", carriers_file, "--no-host"])
        check("a target with no checkout is in the third bucket, not in none of them",
              code == 2
              and "no answer                 no-checkout-here" in text
              and "targets                   no-checkout-here" in text)
    finally:
        if was is None:
            os.environ.pop("CLAUDE_CONFIG_DIR", None)
        else:
            os.environ["CLAUDE_CONFIG_DIR"] = was
        shutil.rmtree(stage, ignore_errors=True)

    print()
    if problems:
        print(f"{len(problems)} propert{'y' if len(problems) == 1 else 'ies'} this check claims "
              "about itself does not hold.")
        return 1
    print("Every property this check claims about itself holds, and the loop's size agrees with "
          "the surface.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
