#!/usr/bin/env python3
"""Hold this repository to naming no other project.

The convention is that nothing here names another project -- no repository slug,
tracker identifier, host path or address -- and that nothing under a carrier root
carries a *value*, where the procedure must read one from configuration instead.
The acceptance item for that convention says the **search is the check**, rather
than a reading of the procedure, so this script is the search and the gate runs
it.

Seven of the nine checks here are of the *forbidding* kind, which is sound only
when the thing forbidden has a stable form; the two computed ones exist to stop
the other seven holding nothing. Two rules keep the forbidding kind sound:

1. **A stack token counts only as code, never as prose.** In markdown that means
   inside a code span or a fenced block; in a script it means outside the
   comments. `make`, `go`, `task`, `just`, `stack`, `bundle`, `mix` and `pod` are
   ordinary English words in a sentence and unambiguous commands in a code span.
2. **A value counts only as a whole code span or a whole quoted string.** A value
   written as a value stands alone in its span, so a sentence that merely
   contains the word is not a value -- a status vocabulary of `open` and `closed`
   does not forbid the word "opening".

⚠️ **What this script checks, what it derives, and every limit it has are
recorded once, in `docs/single-source-of-truth.md` § The second sweep.** This
docstring deliberately does not restate them: two prose copies of a limit are the
defect this repository exists to delete, and nothing holds a docstring to a
document.

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

# A carrier's directory name. Grammar, from the surface's § 7 axis: a role's
# carrier is a skill, a command or a hook, and each kind lives in a directory
# named for it. Keying on the directory name rather than on one plugin's layout
# is what stops a sweep of skill directories undercounting a slash-command
# project by six roles, which § 7 records as measured.
CARRIERS = ["skills", "commands", "hooks"]

# Where a carrier directory can sit. A root that does not exist yet is still
# matched by shape rather than declared by hand, and `check_no_carrier_escapes`
# below is what catches one sitting somewhere these shapes do not reach.
STRICT_SHAPES = [f"plugins/*/{c}/" for c in CARRIERS] + [f"{c}/" for c in CARRIERS] + [
    f".claude/{c}/" for c in CARRIERS
]

# ⛔ The strict set is the carrier roots, never the whole repository. `docs/`
# quotes the measurements this toolkit was derived from and has to keep naming
# the build tool that reported a cached pass as work done; a rule that forbade a
# tool name in a measurement would forbid the evidence. `config/examples/` is
# whole example configurations and is data rather than procedure -- it is the one
# place a concrete status word or label prefix is written down, and it is where
# this script reads the forbidden set *from*.
DATA_ROOTS = [EXAMPLES]

# Everything under a plugin is a carrier, its configuration, its manifest, or the
# implementation a carrier calls. Anything else is unclassified and fails rather
# than being skipped: a carrier in a directory nobody anticipated is exactly what
# a shape-matched strict set misses, and a typo in a directory name is how one
# gets there.
#
# ⚠️ `scripts/` is classified rather than swept, and the distinction is not
# convenience. A carrier is instructions a role follows, and the strict rules
# hold those to naming no tracker and no stack because one role is shared across
# projects whose trackers and stacks differ. An implementation a carrier calls is
# the toolkit's own code: it is written in some language, and saying so names the
# toolkit's stack rather than any project's. A sweep that forbade it would forbid
# the shared reader telling a user which package to install.
PLUGIN_NON_CARRIER = [
    "plugins/*/config/",
    "plugins/*/.claude-plugin/",
    "plugins/*/scripts/",
]

# ⚠️ This file alone, not all of `tools/`. It necessarily writes down every token
# it forbids -- its own grammars and its planted violations contain home paths,
# addresses and foreign slugs. Its sibling needs no such exemption and is swept
# like any other file.
SELF_FILE = "tools/check_no_project_names.py"

# A foreign slug permitted by name, with its reason. The convention forbids
# naming another *project*; a public artifact cited as prior art is not one, and
# the citation is load-bearing -- it is the independent confirmation of the
# status design. One entry, and adding a second means editing this table and
# saying why, which is the point of its being a table.
PRIOR_ART = {
    "nesquikm/dev-process-toolkit": "the public MIT plugin cited as prior art",
    "humanlayer/advanced-context-engineering-for-coding-agents":
        "the published practice the window-as-a-resource measurements are drawn from",
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

# Tracker-side identifiers. A Jira key and a Trello object id are matched only in
# a *value* position -- a whole code span, a whole quoted string, or a URL path --
# for the same reason rule 2 exists: `UTF-8`, `SHA-256`, `ISO-8601` and `RFC-7231`
# have a Jira key's exact shape, and a check that reddened on a document naming
# an encoding would be the quoting failure one check over.
TRACKER_IDS_IN_VALUE = [
    (re.compile(r"^[A-Z][A-Z0-9]{1,9}-\d+$"), "a Jira issue key"),
    (re.compile(r"^[0-9a-f]{24}$"), "a Trello object id"),
]
TRACKER_IDS_ANYWHERE = [
    (re.compile(r"\b[A-Za-z0-9-]+\.atlassian\.net\b"), "a Jira site"),
    (re.compile(r"\btrello\.com/[bc]/\S+"), "a Trello board or card"),
]

# A closed list, grouped by what each group is. Matched as a whole token in code
# only, per rule 1.
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
        msbuild dotnet go stack cabal
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
# configuration carries, not this check's to pre-empt by reddening on it.

# `git` and `gh` are the shared procedure's own two commands. They are absent
# from the lists above, and a command *rooted* at one of them is exempt from the
# directory-flag rule as well -- because the surface's § 1 requires every
# invocation of them to name its root explicitly, and for git that naming form is
# `git -C <root>`. Forbidding the flag that discharges § 1 would leave a role no
# way to be correct: `cd <root> && git …` is forbidden too, and rightly.
PROCEDURE_COMMANDS = {"git", "gh"}

# A directory reaching a command, in the two forms the standing correction
# forbids outright: a change of directory prefixing it, and a flag carrying one.
# `-w` is not here: it is `gh`'s `--web` and git's ignore-whitespace, not a root.
DIRECTORY_CHANGE = re.compile(r"(?:^|[;&|]\s*)cd\s+\S")
DIRECTORY_FLAGS = re.compile(
    r"(?:^|\s)(?:-C|--cwd|--prefix|--directory|--project-dir|--workspace|--chdir)(?:[=\s]|$)"
)
# ⚠️ `}` is in the lookbehind because a path that follows a `${…}` expansion is
# rooted at that variable and is not absolute. The harness substitutes the
# plugin's own location into a carrier that way -- it is the only means a role
# has of naming a file the plugin ships -- and reading it as an absolute path
# forbids the one form the rule is satisfied by.
ABSOLUTE_PATH = re.compile(r"(?<![\w.$}])/(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]+")

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

# A placeholder is not a value. ⛔ The bare-capitals form counts as a placeholder
# **only inside the data root**, where `OWNER/REPO` and `KEY` are stand-ins. A
# configuration that is somebody's actual facts has no such licence, so `TODO`
# and `IN_PROGRESS` there are values -- which matters because those are the
# commonest status spellings and one tracker upper-cases its project keys.
PLACEHOLDER = re.compile(r"^(?:<.*>|[^\n]*[<…][^\n]*)$")
PLACEHOLDER_IN_DATA = re.compile(r"^[A-Z][A-Z0-9_]*(?:/[A-Z][A-Z0-9_]*)?$")

# A value is matched as a whole code span or a whole quoted string, per rule 2.
# Newlines are normalised away before matching, because this repository
# hard-wraps its prose and a value whose wrap falls inside it is still a value.
CODE_SPAN = re.compile(r"`([^`]+)`")
QUOTED_ANY = re.compile(r"\"([^\"]*)\"|«([^»]*)»|“([^”]*)”")
QUOTED_SINGLE = re.compile(r"'([^']*)'")

# Two characters is a real value -- a tracker's `CI`, a label prefix's `E:`.
MIN_VALUE_LEN = 2

SHEBANG = re.compile(r"^#!.*$", re.M)
TRAILING_COMMENT = re.compile(r"(?<!\\)#.*$")


def _tokens(groups: dict[str, str]) -> list[tuple[str, str]]:
    return [(token, label) for label, blob in groups.items() for token in blob.split()]


STACK = _tokens(STACK_TOKENS)


def rooted_at_procedure_command(region: str) -> bool:
    """Is this command's own name `git` or `gh`?"""
    head = region.strip().split()
    return bool(head) and head[0] in PROCEDURE_COMMANDS


def deslugged(name: str) -> re.Pattern[str]:
    """`github-projects` also written `GitHub Projects`, or `githubprojects`.

    A tracker's name reaches the surface as a `kind:` slug and reaches prose as
    words. Matching only the slug would certify the check on the one spelling
    nobody writes.
    """
    return re.compile(r"(?<![\w-])" + r"[-\s]?".join(map(re.escape, name.split("-"))) + r"(?![\w-])")


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
        return clone

    # --- scopes ----------------------------------------------------------

    @staticmethod
    def inside(path: str, roots: list[str]) -> bool:
        return any(path.startswith(r) or fnmatch.fnmatch(path, r + "*") for r in roots)

    def everything(self) -> list[str]:
        return [p for p in sorted(self.text) if p != SELF_FILE]

    def strict(self) -> list[str]:
        return [
            p for p in sorted(self.text)
            if self.inside(p, STRICT_SHAPES)
            and p != SELF_FILE
            and not self.inside(p, DATA_ROOTS)
        ]

    def unswept_shapes(self) -> list[str]:
        return [s for s in STRICT_SHAPES if not any(self.inside(p, [s]) for p in self.text)]

    # --- code and value regions ------------------------------------------

    def code(self, path: str) -> list[str]:
        """The regions of a file that are commands rather than prose.

        Markdown: code spans and fenced blocks, found by a line toggle rather
        than by a paired regex -- a trailing space after a fence's language tag
        is enough to make a paired regex match one block's closer against the
        next block's opener, which hides every command and sweeps the prose
        between them instead.

        A script: every line that is not a comment. A shebang names an absolute
        path and a comment is prose, so sweeping either would be the failure
        rule 1 exists to prevent.
        """
        body = self.text[path]
        if not path.endswith(".md"):
            body = SHEBANG.sub("", body)
            return [
                stripped for stripped in
                (TRAILING_COMMENT.sub("", line).strip() for line in body.splitlines())
                if stripped
            ]
        regions: list[str] = []
        fenced = False
        for line in body.splitlines():
            if line.lstrip().startswith("```"):
                fenced = not fenced
                continue
            if fenced:
                regions.append(line)
            else:
                regions.extend(CODE_SPAN.findall(line))
        return regions

    def value_contexts(self, path: str) -> list[str]:
        """Whole spans and whole quoted strings, per rule 2.

        ⛔ Fenced blocks come out first, by the same line toggle `code` uses. A
        fence's own backticks otherwise shift the pairing of every span after it,
        so a value written as a span lands inside a span the document never had.
        A line of a fence is a context in its own right.
        """
        body = self.text[path]
        if path.endswith(".md"):
            prose: list[str] = []
            out: list[str] = []
            fenced = False
            for line in body.splitlines():
                if line.lstrip().startswith("```"):
                    fenced = not fenced
                    continue
                (out if fenced else prose).append(line.strip() if fenced else line)
            # The wrap is not part of the value.
            flat = re.sub(r"\n\s*", " ", "\n".join(prose))
            out += CODE_SPAN.findall(flat)
            out += [g for match in QUOTED_ANY.finditer(flat) for g in match.groups() if g is not None]
            return out
        out = [line.strip() for line in body.splitlines()]
        out += CODE_SPAN.findall(body)
        for pattern in (QUOTED_ANY, QUOTED_SINGLE):
            out += [g for match in pattern.finditer(body) for g in match.groups() if g is not None]
        return out

    # --- what the configurations and the surface say ----------------------

    def configs(self) -> list[str]:
        return [OWN_CONFIG] + sorted(p for p in self.text if p.startswith(EXAMPLES))

    def own_slug(self) -> str | None:
        match = CONFIG_SLUG.search(self.text.get(OWN_CONFIG, ""))
        return match.group("slug") if match else None

    def tracker_names(self) -> set[str]:
        """The `kind` alternatives of the surface's tracker block, plus each
        configuration's own declared tracker kind.

        ⛔ Scoped to the `tracker:` block. A line-anchored read of every `kind:`
        cannot tell `host.kind: github` from `tracker.kind`, and subtracting the
        host's name afterwards would be an undeclared carve-out of content in a
        script that hardcodes form.
        """
        names: set[str] = set()
        for path in [SURFACE] + self.configs():
            for block in self._tracker_blocks(self.text.get(path, "")):
                for match in re.finditer(
                    r"^\s*kind:\s*(?P<alts>[a-z-]+(?:\s*\|\s*[a-z-]+)*)\s*$", block, re.M
                ):
                    names.update(a.strip() for a in match.group("alts").split("|"))
        # `none` is the absent case and an ordinary English word; a procedure
        # that may not say "none" could not state an absent case.
        return {n for n in names if n != "none"}

    @staticmethod
    def _tracker_blocks(body: str) -> list[str]:
        """Each `tracker:` block, by indentation, fences stripped of their tags."""
        blocks = []
        lines = [l for l in body.splitlines() if not l.lstrip().startswith("```")]
        for i, line in enumerate(lines):
            if not re.match(r"^tracker:\s*$", line):
                continue
            block = []
            for following in lines[i + 1:]:
                if following.strip() and not following.startswith((" ", "\t")):
                    break
                block.append(following)
            blocks.append("\n".join(block))
        return blocks

    def forbidden_values(self) -> dict[str, str]:
        """value -> the configuration and key it was read from."""
        found: dict[str, str] = {}
        own = self.own_slug()
        for path in self.configs():
            in_data = self.inside(path, DATA_ROOTS)
            for raw in self.text.get(path, "").splitlines():
                # A comment is not a value, and a block scalar's marker is not
                # the value it introduces.
                line = TRAILING_COMMENT.sub("", raw)
                for key in VALUE_KEYS:
                    for match in re.finditer(
                        r"(?:^|[\s{,])" + re.escape(key) + r":\s*(?P<value>\"[^\"]*\"|'[^']*'|[^,}\n]+)",
                        line,
                    ):
                        value = match.group("value").strip().strip("\"'").strip()
                        if not value or value in {"null", "[]", "{}", ">-", "|", ">", "|-"}:
                            continue
                        if PLACEHOLDER.match(value) or value == own:
                            continue
                        if in_data and PLACEHOLDER_IN_DATA.match(value):
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
            if tree.inside(path, DATA_ROOTS) and PLACEHOLDER_IN_DATA.match(slug):
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
                "with no absent case."
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
        for pattern, what in TRACKER_IDS_ANYWHERE:
            for match in pattern.finditer(tree.text[path]):
                line = tree.text[path].count("\n", 0, match.start()) + 1
                problems.append(
                    f"{path}:{line}: `{match.group(0)}` reads as {what}. An identifier that "
                    "resolves on someone's tracker is that project's fact; the examples carry "
                    "placeholders instead."
                )
        for context in tree.value_contexts(path):
            token = context.strip()
            for pattern, what in TRACKER_IDS_IN_VALUE:
                if pattern.match(token):
                    problems.append(
                        f"{path}: `{token}` is written as a value and reads as {what}. An "
                        "identifier that resolves on someone's tracker is that project's fact."
                    )
    return problems


def check_no_tracker_is_named_in_the_strict_set(tree: Tree) -> list[str]:
    names = tree.tracker_names()
    problems = []
    if not names:
        return [
            f"{SURFACE}: no `kind:` alternatives were read from a tracker block and no "
            "configuration declares one, so this check holds nothing."
        ]
    for path in tree.strict():
        body = tree.text[path].lower()
        for name in sorted(names):
            if deslugged(name).search(body):
                problems.append(
                    f"{path}: names the tracker `{name}`. The shared procedure names the port "
                    "and never a tracker, so a role's text may not carry one at all — in any "
                    "spelling, which is why the slug and its de-slugged form are both matched."
                )
    return problems


def check_no_stack_is_named_in_the_strict_set(tree: Tree) -> list[str]:
    problems = []
    swept = 0
    for path in tree.strict():
        for region in tree.code(path):
            swept += 1
            words = set(re.findall(r"[A-Za-z0-9_.-]+", region))
            for token, what in STACK:
                if token in words:
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
            if DIRECTORY_FLAGS.search(region) and not rooted_at_procedure_command(region):
                problems.append(
                    f"{path}: the command `{region.strip()[:70]}` carries a directory flag. "
                    "Same rule: the root is configuration, not an argument a role writes. "
                    "(`git` and `gh` are exempt — § 1 requires them to name their root.)"
                )
            for match in ABSOLUTE_PATH.finditer(region):
                problems.append(
                    f"{path}: the command `{region.strip()[:70]}` names the absolute path "
                    f"`{match.group(0)}`. Every path a role uses is relative to a configured "
                    "root."
                )
    if tree.strict() and not swept:
        problems.append(
            "The strict set has files and not one line of code in any of them, so this check "
            "holds nothing. A check that holds nothing reports green."
        )
    return problems


def check_no_value_is_carried_in_the_strict_set(tree: Tree) -> list[str]:
    values = tree.forbidden_values()
    problems = []
    for key in sorted(set(VALUE_KEYS) - tree.declared_keys_present()):
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
                    "under a carrier root — the procedure reads it."
                )
    return problems


def check_the_strict_set_is_swept(tree: Tree) -> list[str]:
    if not tree.strict():
        return [
            "No file is in the strict set, so every check scoped to it reports green while "
            "holding nothing. A check that holds nothing reports green."
        ]
    return []


def check_no_carrier_escapes(tree: Tree) -> list[str]:
    """Every file under a plugin is a carrier, a configuration or a manifest.

    The strict set is matched by shape, so a carrier in a directory the shapes do
    not reach would be swept by nothing *and* reported by nothing -- a typo in a
    directory name is the cheap way to get there. This runs in the other
    direction and makes that residue loud.
    """
    problems = []
    for path in tree.everything():
        if not path.startswith("plugins/"):
            continue
        if tree.inside(path, STRICT_SHAPES) or tree.inside(path, PLUGIN_NON_CARRIER):
            continue
        if len(path.split("/")) <= 3:  # a plugin's own top-level file
            continue
        problems.append(
            f"{path}: sits under a plugin in no carrier root and in no configuration root, so "
            f"the strict checks do not reach it. A carrier directory is one of {CARRIERS}; "
            "anything else is unclassified rather than exempt."
        )
    return problems


CHECKS = [
    ("no other repository is named", check_no_other_repository_is_named),
    ("no home directory is named", check_no_home_directory_is_named),
    ("no address is named", check_no_address_is_named),
    ("no tracker identifier is named", check_no_tracker_identifier_is_named),
    ("the strict set is swept at all", check_the_strict_set_is_swept),
    ("no carrier escapes the strict set", check_no_carrier_escapes),
    ("no tracker is named in the strict set", check_no_tracker_is_named_in_the_strict_set),
    ("no stack is named in the strict set", check_no_stack_is_named_in_the_strict_set),
    ("no value is carried in the strict set", check_no_value_is_carried_in_the_strict_set),
]


# --- the planted violations ------------------------------------------------
#
# One per branch that does real work. A plant that reddens a check by the wrong
# route proves nothing about the branch it was written for.


def a_strict_file(tree: Tree) -> str:
    """A file in the strict set to plant into, synthesised if there is none.

    ⛔ Never a hardcoded path. The self-test is what the workflow runs, so a
    moved or renamed carrier root must make a check go red rather than make this
    script die with a KeyError in place of a verdict.
    """
    existing = [p for p in tree.strict() if p.endswith(".md")]
    if existing:
        return existing[0]
    planted = f"plugins/mjolnir/{CARRIERS[0]}/planted/SKILL.md"
    tree.text.setdefault(planted, "# Planted\n")
    return planted


def _plant_in_a_carrier(text: str):
    def apply(tree: Tree) -> Tree:
        path = a_strict_file(tree)
        tree.text[path] = tree.text[path] + text
        return tree

    return apply


def _plant_in_a_hook(text: str):
    def apply(tree: Tree) -> Tree:
        tree.text["hooks/planted.sh"] = "#!/usr/bin/env bash\n" + text
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


def _plant_home_path_in_the_sibling_script(tree: Tree) -> Tree:
    """The exemption is this file, not all of `tools/`."""
    tree.text["tools/check_single_source.py"] += '\nFALLBACK = "/Users/someone/Projects/thing"\n'
    return tree


def _plant_address(tree: Tree) -> Tree:
    tree.text["README.md"] += "\nAsk someone@example.com.\n"
    return tree


def _plant_jira_key_as_a_value(tree: Tree) -> Tree:
    tree.text["docs/configuration-surface.md"] += "\nMeasured on `PROJ-1421`.\n"
    return tree


def _plant_trello_id_as_a_value(tree: Tree) -> Tree:
    tree.text["docs/configuration-surface.md"] += "\nThe board is `5f2b1c9e4a7d8e3f0b6a1c2d`.\n"
    return tree


def _plant_jira_site(tree: Tree) -> Tree:
    tree.text["docs/configuration-surface.md"] += "\nIt lives on planted.atlassian.net.\n"
    return tree


def _plant_trello_url(tree: Tree) -> Tree:
    tree.text["docs/configuration-surface.md"] += "\nSee trello.com/c/abcd1234.\n"
    return tree


def _plant_empty_strict_set(tree: Tree) -> Tree:
    tree.text = {p: b for p, b in tree.text.items() if not Tree.inside(p, STRICT_SHAPES)}
    return tree


def _plant_carrier_in_an_unreachable_root(tree: Tree) -> Tree:
    """A typo'd carrier directory: swept by no shape, so reported by this check."""
    tree.text["plugins/other/skils/review/SKILL.md"] = "# Review\n\nRun `npm test` on Trello.\n"
    return tree


def _plant_surface_with_no_tracker_kinds(tree: Tree) -> Tree:
    for path in [SURFACE] + tree.configs():
        tree.text[path] = re.sub(r"(?m)^\s*kind:.*$", "", tree.text[path])
    return tree


def _plant_configurations_with_no_concrete_value(tree: Tree) -> Tree:
    keys = "|".join(VALUE_KEYS)
    for path in tree.configs():
        tree.text[path] = re.sub(
            r"((?:^|[\s{,])(?:" + keys + r"):)\s*(?:\"[^\"]*\"|'[^']*'|[^,}#\n]+)",
            r'\1 "<placeholder>"',
            tree.text[path],
        )
    return tree


def _plant_renamed_value_key(tree: Tree) -> Tree:
    for path in tree.configs():
        tree.text[path] = re.sub(r"(?m)^(\s*)out_dir:", r"\1output_dir:", tree.text[path])
    return tree


VIOLATIONS = [
    ("no other repository is named", "a foreign slug in a URL", _plant_foreign_slug_as_url),
    ("no other repository is named", "a foreign slug in the install command", _plant_foreign_slug_in_install_command),
    ("no other repository is named", "a foreign slug as a config value", _plant_foreign_slug_as_config_value),
    ("no other repository is named", "this project's own slug unstated", _plant_own_slug_unstated),
    ("no home directory is named", "an absolute home path", _plant_home_path),
    ("no home directory is named", "a tilde path", _plant_tilde_path),
    ("no home directory is named", "a home path in the sibling script", _plant_home_path_in_the_sibling_script),
    ("no address is named", "an email address", _plant_address),
    ("no tracker identifier is named", "a Jira key written as a value", _plant_jira_key_as_a_value),
    ("no tracker identifier is named", "a Trello object id written as a value", _plant_trello_id_as_a_value),
    ("no tracker identifier is named", "a Jira site", _plant_jira_site),
    ("no tracker identifier is named", "a Trello card URL", _plant_trello_url),
    ("the strict set is swept at all", "a strict set with no files in it", _plant_empty_strict_set),
    ("no carrier escapes the strict set", "a carrier in a root no shape reaches", _plant_carrier_in_an_unreachable_root),
    ("no tracker is named in the strict set", "a tracker named in a carrier",
     _plant_in_a_carrier("\nOn Trello the card moves separately.\n")),
    ("no tracker is named in the strict set", "a tracker named in its de-slugged spelling",
     _plant_in_a_carrier("\nOn GitHub Projects the item moves separately.\n")),
    ("no tracker is named in the strict set", "a surface declaring no tracker kinds", _plant_surface_with_no_tracker_kinds),
    ("no stack is named in the strict set", "a build tool invocation in a carrier",
     _plant_in_a_carrier("\nRun `npm run build` first.\n")),
    ("no stack is named in the strict set", "a build tool inside a fenced block",
     _plant_in_a_carrier("\nThen:\n\n```sh \nnpm run build\n```\n")),
    ("no stack is named in the strict set", "a manifest name in a carrier",
     _plant_in_a_carrier("\nRead the version out of `package.json`.\n")),
    ("no stack is named in the strict set", "a token the rules cite by name",
     _plant_in_a_carrier("\nRun `go test ./...` and `stack build`.\n")),
    ("no stack is named in the strict set", "a directory change prefixing a command",
     _plant_in_a_carrier("\nRun `cd frontend && ./run` from the root.\n")),
    ("no stack is named in the strict set", "a directory flag on a command that is not git or gh",
     _plant_in_a_carrier("\nRun `npx --prefix web serve` instead.\n")),
    ("no stack is named in the strict set", "an absolute path in a command",
     _plant_in_a_carrier("\nWrite it to `/var/log/day-report.txt`.\n")),
    ("no stack is named in the strict set", "a build tool in a hook, outside its comments",
     _plant_in_a_hook("# Make sure the task is still assigned.\nnpm run build\n")),
    ("no value is carried in the strict set", "a status word in a carrier",
     _plant_in_a_carrier("\nMove the item to `In Progress` first.\n")),
    ("no value is carried in the strict set", "a status word whose wrap falls inside it",
     _plant_in_a_carrier("\nMove the item to `In\nProgress` first.\n")),
    ("no value is carried in the strict set", "an upper-case status word",
     lambda tree: _plant_in_a_carrier("\nMove the item to `IN_PROGRESS` first.\n")(
         _plant_upper_case_status(tree))),
    ("no value is carried in the strict set", "a single-quoted value in a hook",
     lambda tree: _plant_in_a_hook("status='In Progress'\n")(tree)),
    ("no value is carried in the strict set", "a renamed value key", _plant_renamed_value_key),
    ("no value is carried in the strict set", "configurations with no concrete value left", _plant_configurations_with_no_concrete_value),
]


def _plant_upper_case_status(tree: Tree) -> Tree:
    """An all-caps status in a real configuration is a value, not a placeholder."""
    tree.text[OWN_CONFIG] += '\nstatuses:\n  - { name: "IN_PROGRESS", role: in_flight }\n'
    return tree


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
    unswept = tree.unswept_shapes()
    if unswept:
        print(
            f"  --    {len(unswept)} carrier shape(s) match no file and sweep nothing; the run "
            "still exits 0. `no carrier escapes the strict set` is what covers a carrier "
            "outside every shape."
        )
    if problems:
        print(f"\n{len(problems)} problem(s):\n")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print(
        "\nNo other project is named, and nothing under a carrier root carries a value, a "
        "tracker or a stack."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
