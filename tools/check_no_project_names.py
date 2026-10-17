#!/usr/bin/env python3
"""Hold this repository to naming no other project.

The convention is that nothing here names another project -- no repository slug,
tracker identifier, host path or address -- and that nothing under a skills or
hooks root carries a *value* at all, where the procedure must read one from
configuration instead. The acceptance item for that convention says the **search
is the check**, rather than a reading of the procedure, so this script is the
search and the gate runs it.

Every check here is of the *forbidding* kind, which is sound only when the thing
forbidden has a stable form. Two rules keep that true, and they are what make
this script more than a grep:

1. **A stack token counts only inside a code span or a fenced block.** `make`,
   `go`, `task`, `just`, `stack`, `bundle`, `mix` and `pod` are ordinary English
   words in prose and unambiguous commands in a code span. Sweeping prose for
   them would redden on a reworded sentence, which is the failure the *quoting*
   kind of check has and the reason this one does not attempt it.
2. **A project's value counts only as a whole code span or a whole quoted
   string.** A value written as a value stands alone in its span -- `` `In
   Progress` ``, `"Todo"`. A phrase that merely contains the word does not, so
   "CI went green" quoted as an example of bad description wording is not a
   workflow name, and a status vocabulary of `open` and `closed` does not forbid
   the word "opening".

What it derives at run time, so that it is not one more copy of the rules:

* the one permitted repository slug, from this project's own configuration;
* the tracker names, from the surface's `kind` alternatives and every
  configuration's declared kind;
* the forbidden value set, from the configurations themselves -- which is why a
  new example configuration adds to what is forbidden under a skills root
  instead of tripping anything.

It hardcodes form only: the host-URL and address grammars, the tracker-identifier
grammars, the closed list of stack tool names, and which leaf keys of a
configuration carry a project's fact rather than the surface's own vocabulary.

Usage:
    check_no_project_names.py              sweep the tree
    check_no_project_names.py --self-test  assert every check reddens on each of
                                           its planted violations, then sweep
"""

from __future__ import annotations

import fnmatch
import os
import re
import subprocess
import sys

# --- what plays which role -------------------------------------------------

SURFACE = "plugins/mjolnir/config/schema.md"
OWN_CONFIG = ".claude/mjolnir.yaml"
EXAMPLES = "plugins/mjolnir/config/examples/"

# The strict set: a root that carries procedure. Nothing here may carry a value,
# name a tracker, or name a stack. A root that does not exist yet is declared
# anyway and reported as unswept rather than being silently absent -- the hooks
# that enforce the loop are #16 and land later, and a root nobody declared is a
# root nothing sweeps.
STRICT_ROOTS = [
    "plugins/*/skills/",
    "plugins/*/hooks/",
    "hooks/",
]

# ⛔ The strict set is a skills root and a hooks root, never the whole
# repository. `docs/` quotes the measurements this toolkit was derived from and
# has to keep naming the build tool that reported a cached pass as work done; a
# rule that forbade a tool name in a measurement would forbid the evidence.
# `config/examples/` is whole example configurations and is data rather than
# procedure -- it is the one place a concrete status word or label prefix is
# written down, and it is where this script reads the forbidden set *from*.
DATA_ROOTS = [EXAMPLES]

# This script and its sibling necessarily write down every token they forbid.
SELF = ["tools/"]

# A foreign slug permitted by name, with its reason. The convention forbids
# naming another *project*; a public artifact cited as prior art is not one, and
# the citation is load-bearing -- it is the independent confirmation of the
# status design. One entry, and adding a second means editing this table and
# saying why, which is the point of its being a table.
PRIOR_ART = {
    "nesquikm/dev-process-toolkit": "the public MIT plugin cited as prior art",
}

# --- the grammars ----------------------------------------------------------

HOST_URL = re.compile(
    r"\b(?:github|gitlab|bitbucket)\.(?:com|org)/(?P<slug>[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)"
)
# The install command's argument is the other place a slug is written bare.
MARKETPLACE_SLUG = re.compile(r"marketplace\s+add\s+(?P<slug>[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)")
CONFIG_SLUG = re.compile(r"^\s*repo:\s*[\"']?(?P<slug>[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)", re.M)

HOME_PATH = re.compile(r"(?:/Users/|/home/|\$HOME\b|\$\{HOME\}|(?<![\w.])~/[A-Za-z0-9_.])")
ADDRESS = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")

# Tracker-side identifiers. A Jira key is two or more capitals, a hyphen and a
# number; a Trello object id is 24 hex; both services name themselves in a URL.
TRACKER_IDS = [
    (re.compile(r"\b[A-Z][A-Z0-9]{1,9}-\d+\b"), "a Jira issue key"),
    (re.compile(r"\b[0-9a-f]{24}\b"), "a Trello object id"),
    (re.compile(r"\b[A-Za-z0-9-]+\.atlassian\.net\b"), "a Jira site"),
    (re.compile(r"\btrello\.com/[bc]/\S+"), "a Trello board or card"),
]

# A closed list, grouped by what each group is. Matched as a whole token inside a
# code span or a fenced block only, per rule 1 above.
STACK_TOKENS = {
    "a package manager": """
        npm npx yarn pnpm bun pip pip3 pipx poetry uv pdm pipenv conda
        gem bundle bundler composer cargo nuget pod cocoapods hex mix
        brew apt apt-get choco scoop
    """,
    "a task runner or build tool": """
        make cmake ninja bazel buck gradle gradlew mvn maven ant sbt lein
        leiningen rake grunt gulp just task nx turbo lerna rush melos
        webpack vite rollup esbuild parcel tsc tsup swc babel
        msbuild dotnet
    """,
    "a test runner or checker": """
        pytest tox nose jest vitest mocha karma cypress playwright
        eslint prettier ruff black flake8 pylint mypy isort
        rspec rubocop phpunit phpstan psalm
        detekt ktlint spotless clippy rustfmt gofmt golangci-lint
        svelte-check vue-tsc stylelint
    """,
    "a container or deployment tool": """
        docker docker-compose podman kubectl helm skaffold
        terraform ansible pulumi vagrant
        heroku flyctl vercel netlify wrangler eb gcloud aws az
    """,
    "a manifest or lockfile": """
        package.json package-lock.json yarn.lock pnpm-lock.yaml bun.lockb
        requirements.txt pyproject.toml poetry.lock Pipfile Pipfile.lock
        setup.py setup.cfg tox.ini
        Gemfile Gemfile.lock composer.json composer.lock
        Cargo.toml Cargo.lock go.mod go.sum
        pom.xml build.gradle build.gradle.kts settings.gradle settings.gradle.kts
        build.sbt project.clj Makefile CMakeLists.txt BUILD.bazel WORKSPACE
        pubspec.yaml pubspec.lock mix.exs Package.swift Podfile Podfile.lock
        tsconfig.json jsconfig.json Dockerfile docker-compose.yml .nvmrc
    """,
}

# ⚠️ A language interpreter is deliberately **not** on that list, and
# `python3 <day_log.script>` is the one live instance of one. Whether a
# configured script is a path the procedure prefixes with an interpreter or a
# command the procedure merely runs is #65's and #66's ruling about what
# configuration carries, not this check's to pre-empt by reddening on it. Until
# that lands, the interpreter named in a skill is a known, stated hole.

# `git` and `gh` are the shared procedure's own two commands -- the surface's § 1
# requires every invocation of them to name its root explicitly, which it could
# not require of a command it forbade.
PROCEDURE_COMMANDS = {"git", "gh"}

# A directory reaching a command, in the two forms the standing correction
# forbids outright: a change of directory prefixing it, and a flag carrying one.
DIRECTORY_CHANGE = re.compile(r"(?:^|[;&|]\s*)cd\s+\S")
DIRECTORY_FLAGS = re.compile(
    r"(?:^|\s)(?:-C|-w|--cwd|--prefix|--directory|--project-dir|--workspace|--chdir)(?:[=\s]|$)"
)
ABSOLUTE_PATH = re.compile(r"(?<![\w.$])/(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]+")

# Which leaf key of a configuration carries a project's fact. Grammar, because
# the surface does not mark its keys as project-supplied or procedure-supplied --
# it illustrates some with a placeholder and some with a default, and the two
# read alike. Each name below is asserted to occur in some configuration, so a
# renamed key is loud rather than a value set that quietly shrinks to nothing.
VALUE_KEYS = [
    "repo",          # the host's slug
    "workflow",      # a run's name on the host
    "mirrors",       # the local command a run duplicates
    "board",         # a Trello board
    "project_key",   # a Jira project
    "name",          # a status word, and a status field's own name
    "label_prefix",  # the prefix a label convention carries
    "unit",          # an estimate's unit
    "dir",           # where a project keeps its templates
    "outcome",       # a template's own heading, per semantic section
    "acceptance",
    "reproduction",
    "field",         # what a readiness check reads
    "label",
    "ref",
    "out_dir",       # where the day log is written
    "script",        # the evidence script's path
    "audience",      # who an artifact is written for
]

# A value that is a placeholder is not a value. The examples use these
# throughout, which is how they stay data rather than anyone's facts.
PLACEHOLDER = re.compile(r"^(?:<.*>|…|.*….*|\$\{?[A-Z_]+\}?.*|[A-Z][A-Z0-9_]*(?:/[A-Z][A-Z0-9_]*)?)$")

# A value is matched as a whole code span or a whole quoted string, per rule 2.
CODE_SPAN = re.compile(r"`([^`\n]+)`")
FENCE = re.compile(r"```[A-Za-z0-9]*\n(.*?)```", re.S)
QUOTED = re.compile(r"\"([^\"\n]*)\"|«([^»\n]*)»")

# Too short to be a value rather than a coincidence. One letter plus a colon is
# a real label prefix, so the floor is on bare words only.
MIN_VALUE_LEN = 3


def _tokens(groups: dict[str, str]) -> list[tuple[str, str]]:
    return [(token, label) for label, blob in groups.items() for token in blob.split()]


STACK = _tokens(STACK_TOKENS)


# --- the tree --------------------------------------------------------------


class Tree:
    """Every tracked text file, in memory, so a violation can be planted."""

    def __init__(self, root: str):
        self.root = root
        self.text: dict[str, str] = {}
        for path in self._tracked():
            body = self._read(path)
            if body is not None:
                self.text[path] = body
        self.unswept = [r for r in STRICT_ROOTS if not self._under(r)]

    def _tracked(self) -> list[str]:
        out = subprocess.run(
            ["git", "-C", self.root, "ls-files"],
            capture_output=True, text=True, check=True,
        ).stdout
        return [line for line in out.splitlines() if line]

    def _read(self, rel: str) -> str | None:
        try:
            with open(os.path.join(self.root, rel), encoding="utf-8") as handle:
                return handle.read()
        except (UnicodeDecodeError, OSError):
            return None  # not text; nothing here can read it anyway

    def copy(self) -> "Tree":
        clone = Tree.__new__(Tree)
        clone.root = self.root
        clone.text = dict(self.text)
        clone.unswept = list(self.unswept)
        return clone

    # --- scopes ----------------------------------------------------------

    def _under(self, root: str) -> list[str]:
        return [
            p for p in self.text
            if p.startswith(root) or fnmatch.fnmatch(p, root + "*")
        ]

    def everything(self) -> list[str]:
        return [p for p in sorted(self.text) if not self.inside(p, SELF)]

    def strict(self) -> list[str]:
        found = {p for root in STRICT_ROOTS for p in self._under(root)}
        return sorted(p for p in found if not self.inside(p, SELF))

    @staticmethod
    def inside(path: str, roots: list[str]) -> bool:
        return any(path.startswith(r) or fnmatch.fnmatch(path, r + "*") for r in roots)

    # --- code regions, per rule 1 ----------------------------------------

    def code(self, path: str) -> list[str]:
        """The regions of a file that are commands rather than prose.

        A non-markdown file in the strict set is a script: all of it is code.
        """
        body = self.text[path]
        if not path.endswith(".md"):
            return body.splitlines()
        regions = [m.group(1) for m in CODE_SPAN.finditer(body)]
        for match in FENCE.finditer(body):
            regions.extend(match.group(1).splitlines())
        return regions

    def value_contexts(self, path: str) -> list[str]:
        """Whole spans and whole quoted strings, per rule 2."""
        body = self.text[path]
        out = [m.group(1) for m in CODE_SPAN.finditer(body)]
        for match in QUOTED.finditer(body):
            out.append(match.group(1) if match.group(1) is not None else match.group(2))
        if not path.endswith(".md"):
            out.extend(line.strip() for line in body.splitlines())
        return out

    # --- what the configurations and the surface say ----------------------

    def configs(self) -> list[str]:
        return [OWN_CONFIG] + sorted(p for p in self.text if p.startswith(EXAMPLES))

    def own_slug(self) -> str | None:
        match = CONFIG_SLUG.search(self.text.get(OWN_CONFIG, ""))
        return match.group("slug") if match else None

    def tracker_names(self) -> set[str]:
        """The surface's `kind` alternatives, plus every configuration's own.

        `none` is dropped: it is the absent case and an ordinary English word,
        and a procedure that may not say "none" could not state an absent case.
        """
        names: set[str] = set()
        for match in re.finditer(r"^\s*kind:\s*(?P<alts>[a-z-]+(?:\s*\|\s*[a-z-]+)*)\s*$",
                                 self.text.get(SURFACE, ""), re.M):
            names.update(a.strip() for a in match.group("alts").split("|"))
        for path in self.configs():
            for match in re.finditer(r"^\s*kind:\s*(?P<kind>[a-z-]+)\s*$", self.text.get(path, ""), re.M):
                names.add(match.group("kind"))
        return {n for n in names if n not in {"none", "github"}}

    def forbidden_values(self) -> dict[str, str]:
        """value -> the configuration and key it was read from."""
        found: dict[str, str] = {}
        own = self.own_slug()
        for path in self.configs():
            for line in self.text.get(path, "").splitlines():
                for key in VALUE_KEYS:
                    for match in re.finditer(
                        r"(?:^|[\s{,])" + re.escape(key) + r":\s*(?P<value>\"[^\"]*\"|'[^']*'|[^,}#\n]+)",
                        line,
                    ):
                        value = match.group("value").strip().strip("\"'").strip()
                        if not value or value in {"null", "[]", "{}"}:
                            continue
                        if PLACEHOLDER.match(value) or value == own:
                            continue
                        if len(value) < MIN_VALUE_LEN and not value.endswith(":"):
                            continue
                        found.setdefault(value, f"{path} ({key})")
        return found

    def declared_keys_present(self) -> set[str]:
        blob = "\n".join(self.text.get(p, "") for p in self.configs())
        return {k for k in VALUE_KEYS if re.search(r"(?:^|[\s{,])" + re.escape(k) + r":", blob, re.M)}


# --- the checks ------------------------------------------------------------


def check_no_other_repository_is_named(tree: Tree) -> list[str]:
    own = tree.own_slug()
    problems = []
    if not own:
        return [
            f"{OWN_CONFIG}: states no `host.repo`, so this check has no permitted slug to "
            "measure against and would forbid every slug including this project's own."
        ]
    permitted = {own} | set(PRIOR_ART)
    for path in tree.everything():
        body = tree.text[path]
        found = [(m.group("slug"), "a code-host URL") for m in HOST_URL.finditer(body)]
        found += [(m.group("slug"), "an install command") for m in MARKETPLACE_SLUG.finditer(body)]
        if path in tree.configs():
            found += [(m.group("slug"), "a `repo:` value") for m in CONFIG_SLUG.finditer(body)]
        for slug, form in found:
            if slug in permitted:
                continue
            if tree.inside(path, DATA_ROOTS) and PLACEHOLDER.match(slug):
                continue
            problems.append(
                f"{path}: names the repository `{slug}` as {form}. This repository names no "
                f"other project's slug; the permitted ones are `{own}`, its own, and the "
                "prior-art table in this script."
            )
    return problems


def check_no_home_directory_is_named(tree: Tree) -> list[str]:
    problems = []
    for path in tree.everything():
        for match in HOME_PATH.finditer(tree.text[path]):
            line = tree.text[path].count("\n", 0, match.start()) + 1
            problems.append(
                f"{path}:{line}: names a path under a home directory "
                f"(`{match.group(0)}`). A path on whoever's machine wrote it is the one value "
                "with no absent case and no exception anywhere."
            )
    return problems


def check_no_address_is_named(tree: Tree) -> list[str]:
    problems = []
    for path in tree.everything():
        for match in ADDRESS.finditer(tree.text[path]):
            line = tree.text[path].count("\n", 0, match.start()) + 1
            problems.append(
                f"{path}:{line}: names the address `{match.group(0)}`. An address identifies a "
                "person or an account on a service, which is a project's fact wherever it is "
                "written."
            )
    return problems


def check_no_tracker_identifier_is_named(tree: Tree) -> list[str]:
    problems = []
    for path in tree.everything():
        for pattern, what in TRACKER_IDS:
            for match in pattern.finditer(tree.text[path]):
                token = match.group(0)
                if tree.inside(path, DATA_ROOTS) and PLACEHOLDER.match(token):
                    continue
                line = tree.text[path].count("\n", 0, match.start()) + 1
                problems.append(
                    f"{path}:{line}: `{token}` reads as {what}. An identifier that resolves on "
                    "someone's tracker is that project's fact; the examples carry placeholders "
                    "instead."
                )
    return problems


def check_no_tracker_is_named_in_the_strict_set(tree: Tree) -> list[str]:
    names = tree.tracker_names()
    problems = []
    if not names:
        return [
            f"{SURFACE}: no `kind:` alternatives were read from the surface and no "
            "configuration declares one, so this check holds nothing."
        ]
    for path in tree.strict():
        body = tree.text[path].lower()
        for name in sorted(names):
            if re.search(r"(?<![\w-])" + re.escape(name) + r"(?![\w-])", body):
                problems.append(
                    f"{path}: names the tracker `{name}`. The shared procedure names the port "
                    "and never a tracker, so a role's text may not carry one at all."
                )
    return problems


def check_no_stack_is_named_in_the_strict_set(tree: Tree) -> list[str]:
    problems = []
    for path in tree.strict():
        for region in tree.code(path):
            words = set(re.findall(r"[A-Za-z0-9_.-]+", region))
            for token, what in STACK:
                if token in words and token not in PROCEDURE_COMMANDS:
                    problems.append(
                        f"{path}: the command `{region.strip()[:70]}` names {what} "
                        f"(`{token}`). A role reads the command it runs from configuration; a "
                        "role that names one has learned what produced a verdict."
                    )
            if DIRECTORY_CHANGE.search(region):
                problems.append(
                    f"{path}: the command `{region.strip()[:70]}` is prefixed with a change of "
                    "directory. A directory is resolved through a configured command root, "
                    "which is precisely so that no role carries one."
                )
            if DIRECTORY_FLAGS.search(region):
                problems.append(
                    f"{path}: the command `{region.strip()[:70]}` carries a directory flag. "
                    "Same rule: the root is configuration, not an argument a role writes."
                )
            for match in ABSOLUTE_PATH.finditer(region):
                problems.append(
                    f"{path}: the command `{region.strip()[:70]}` names the absolute path "
                    f"`{match.group(0)}`. Every path a role uses is relative to a configured "
                    "root."
                )
    return problems


def check_no_value_is_carried_in_the_strict_set(tree: Tree) -> list[str]:
    values = tree.forbidden_values()
    problems = []
    missing = set(VALUE_KEYS) - tree.declared_keys_present()
    for key in sorted(missing):
        problems.append(
            f"`{key}` is declared here as a key that carries a project's fact and occurs in no "
            "configuration. Either it was renamed on the surface, in which case the value set "
            "this check sweeps for has quietly shrunk, or it should go."
        )
    if not values:
        problems.append(
            "No configuration supplies a concrete value, so this check holds nothing. The "
            "examples are placeholders by design, but at least one concrete status word, "
            "workflow name or heading is what gives the sweep something to look for."
        )
    for path in tree.strict():
        for context in tree.value_contexts(path):
            stripped = context.strip()
            if stripped in values:
                problems.append(
                    f"{path}: carries the value `{stripped}`, which "
                    f"{values[stripped]} supplies. No value in a configuration appears anywhere "
                    "under a skills or hooks root — the procedure reads it."
                )
    return problems


def check_the_strict_set_is_swept(tree: Tree) -> list[str]:
    problems = []
    if not tree.strict():
        problems.append(
            "No file is in the strict set, so every check scoped to it reports green while "
            "holding nothing. A check that holds nothing reports green."
        )
    return problems


CHECKS = [
    ("no other repository is named", check_no_other_repository_is_named),
    ("no home directory is named", check_no_home_directory_is_named),
    ("no address is named", check_no_address_is_named),
    ("no tracker identifier is named", check_no_tracker_identifier_is_named),
    ("the strict set is swept at all", check_the_strict_set_is_swept),
    ("no tracker is named in the strict set", check_no_tracker_is_named_in_the_strict_set),
    ("no stack is named in the strict set", check_no_stack_is_named_in_the_strict_set),
    ("no value is carried in the strict set", check_no_value_is_carried_in_the_strict_set),
]


# --- the planted violations ------------------------------------------------
#
# One per branch that does real work. A plant that reddens a check by the wrong
# route proves nothing about the branch it was written for.

A_SKILL = "plugins/mjolnir/skills/day-report/SKILL.md"


def _append(path: str, text: str):
    def apply(tree: Tree) -> Tree:
        tree.text[path] = tree.text.get(path, "") + text
        return tree

    return apply


def _plant_foreign_slug_as_url(tree: Tree) -> Tree:
    tree.text["README.md"] += "\nSee <https://github.com/planted-owner/planted-repo>.\n"
    return tree


def _plant_foreign_slug_in_install_command(tree: Tree) -> Tree:
    tree.text["README.md"] += "\n```\n/plugin marketplace add planted-owner/planted-repo\n```\n"
    return tree


def _plant_foreign_slug_as_config_value(tree: Tree) -> Tree:
    tree.text[OWN_CONFIG] += '\nhost:\n  repo: "planted-owner/planted-repo"\n'
    return tree


def _plant_own_slug_unstated(tree: Tree) -> Tree:
    """The permitted slug is derived, so its absence must not read as green."""
    tree.text[OWN_CONFIG] = CONFIG_SLUG.sub("", tree.text[OWN_CONFIG])
    return tree


def _plant_home_path(tree: Tree) -> Tree:
    tree.text["README.md"] += "\nIt lives at /Users/someone/Projects/thing.\n"
    return tree


def _plant_tilde_path(tree: Tree) -> Tree:
    tree.text["README.md"] += "\nIt lives under ~/Projects/thing.\n"
    return tree


def _plant_address(tree: Tree) -> Tree:
    tree.text["README.md"] += "\nAsk someone@example.com.\n"
    return tree


def _plant_jira_key(tree: Tree) -> Tree:
    tree.text["docs/configuration-surface.md"] += "\nMeasured on PROJ-1421.\n"
    return tree


def _plant_trello_id(tree: Tree) -> Tree:
    tree.text["docs/configuration-surface.md"] += "\nThe board is 5f2b1c9e4a7d8e3f0b6a1c2d.\n"
    return tree


def _plant_tracker_name_in_a_skill(tree: Tree) -> Tree:
    tree.text[A_SKILL] += "\nOn Trello the card moves separately.\n"
    return tree


def _plant_build_tool_in_a_skill(tree: Tree) -> Tree:
    tree.text[A_SKILL] += "\nRun `npm run build` first.\n"
    return tree


def _plant_manifest_name_in_a_skill(tree: Tree) -> Tree:
    tree.text[A_SKILL] += "\nRead the version out of `package.json`.\n"
    return tree


def _plant_directory_change_in_a_skill(tree: Tree) -> Tree:
    tree.text[A_SKILL] += "\nRun `cd frontend && ./run` from the root.\n"
    return tree


def _plant_directory_flag_in_a_skill(tree: Tree) -> Tree:
    tree.text[A_SKILL] += "\nRun `gh --prefix web issue list` instead.\n"
    return tree


def _plant_absolute_path_in_a_skill(tree: Tree) -> Tree:
    tree.text[A_SKILL] += "\nWrite it to `/var/log/day-report.txt`.\n"
    return tree


def _plant_status_word_in_a_skill(tree: Tree) -> Tree:
    tree.text[A_SKILL] += "\nMove the item to `In Progress` first.\n"
    return tree


def _plant_script_path_in_a_skill(tree: Tree) -> Tree:
    """The realistic break: a configured path written out rather than read."""
    tree.text[A_SKILL] += '\nRun "/.claude/skills/day-report/scripts/active_time.py".\n'.replace("/.", ".")
    return tree


def _plant_renamed_value_key(tree: Tree) -> Tree:
    for path in tree.configs():
        tree.text[path] = re.sub(r"(?m)^(\s*)out_dir:", r"\1output_dir:", tree.text[path])
    return tree


def _plant_empty_strict_set(tree: Tree) -> Tree:
    tree.text = {p: b for p, b in tree.text.items() if not Tree.inside(p, STRICT_ROOTS)}
    return tree


def _plant_surface_with_no_tracker_kinds(tree: Tree) -> Tree:
    tree.text[SURFACE] = re.sub(r"(?m)^\s*kind:.*$", "", tree.text[SURFACE])
    for path in tree.configs():
        tree.text[path] = re.sub(r"(?m)^\s*kind:.*$", "", tree.text[path])
    return tree


def _plant_configurations_with_no_concrete_value(tree: Tree) -> Tree:
    # Flow maps as well as block style: a status list is written inline, so a
    # line-anchored substitution would leave every status word in place and the
    # plant would prove nothing.
    keys = "|".join(VALUE_KEYS)
    for path in tree.configs():
        tree.text[path] = re.sub(
            r"((?:^|[\s{,])(?:" + keys + r"):)\s*(?:\"[^\"]*\"|'[^']*'|[^,}#\n]+)",
            r'\1 "<placeholder>"',
            tree.text[path],
        )
    return tree


VIOLATIONS = [
    ("no other repository is named", "a foreign slug in a URL", _plant_foreign_slug_as_url),
    ("no other repository is named", "a foreign slug in the install command", _plant_foreign_slug_in_install_command),
    ("no other repository is named", "a foreign slug as a config value", _plant_foreign_slug_as_config_value),
    ("no other repository is named", "this project's own slug unstated", _plant_own_slug_unstated),
    ("no home directory is named", "an absolute home path", _plant_home_path),
    ("no home directory is named", "a tilde path", _plant_tilde_path),
    ("no address is named", "an email address", _plant_address),
    ("no tracker identifier is named", "a Jira key", _plant_jira_key),
    ("no tracker identifier is named", "a Trello object id", _plant_trello_id),
    ("the strict set is swept at all", "a strict set with no files in it", _plant_empty_strict_set),
    ("no tracker is named in the strict set", "a tracker named in a skill", _plant_tracker_name_in_a_skill),
    ("no tracker is named in the strict set", "a surface declaring no tracker kinds", _plant_surface_with_no_tracker_kinds),
    ("no stack is named in the strict set", "a build tool invocation in a skill", _plant_build_tool_in_a_skill),
    ("no stack is named in the strict set", "a manifest name in a skill", _plant_manifest_name_in_a_skill),
    ("no stack is named in the strict set", "a directory change prefixing a command", _plant_directory_change_in_a_skill),
    ("no stack is named in the strict set", "a directory flag on a command", _plant_directory_flag_in_a_skill),
    ("no stack is named in the strict set", "an absolute path in a command", _plant_absolute_path_in_a_skill),
    ("no value is carried in the strict set", "a status word in a skill", _plant_status_word_in_a_skill),
    ("no value is carried in the strict set", "a configured script path in a skill", _plant_script_path_in_a_skill),
    ("no value is carried in the strict set", "a renamed value key", _plant_renamed_value_key),
    ("no value is carried in the strict set", "configurations with no concrete value left", _plant_configurations_with_no_concrete_value),
]


def run(tree: Tree) -> dict[str, list[str]]:
    return {name: check(tree) for name, check in CHECKS}


def self_test(tree: Tree) -> int:
    by_name = dict(CHECKS)
    uncovered = [name for name, _ in CHECKS if not any(n == name for n, _, _ in VIOLATIONS)]
    for name in uncovered:
        print(f"  NO PLANTED VIOLATION   {name}")
    failures = len(uncovered)
    for name, label, plant in VIOLATIONS:
        if by_name[name](plant(tree.copy())):
            print(f"  red on                 {name}: {label}")
        else:
            print(f"  STAYED GREEN           {name}: {label}")
            failures += 1
    if failures:
        print(f"\n{failures} assertion(s) did not hold. A check that cannot fail is not a check.")
    return 1 if failures else 0


def main(argv: list[str]) -> int:
    unknown = [a for a in argv if a != "--self-test"]
    if unknown:
        print(f"unrecognised argument(s): {' '.join(unknown)}\n\n{__doc__}")
        return 2

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tree = Tree(root)

    if "--self-test" in argv:
        print(f"Asserting each check reddens on its planted violations ({len(VIOLATIONS)}):")
        if self_test(tree):
            return 1
        print()

    results = run(tree)
    problems = [p for found in results.values() for p in found]
    for name, found in results.items():
        print(f"  {'FAIL' if found else 'ok  '}  {name}")
    for root_pattern in tree.unswept:
        print(f"  --    `{root_pattern}` matched no file and is unswept")
    if problems:
        print(f"\n{len(problems)} problem(s):\n")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print(
        "\nNo other project is named, and nothing under a skills or hooks root carries a "
        "value, a tracker or a stack."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
